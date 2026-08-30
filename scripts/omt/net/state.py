"""Net bundle state store — feature_039.adaptive_net_engine.

Three-file bundle (IDEA-002 §1.4/§7.2, PROJECT.md D16 — the SSOT state proper):

    META_NET.petri.json      v1 structure + M0 (format unchanged, D6)
    net_state.sidecar.json   {live_marking, revision, updated_at} — live state
    supervisor.overlay.json  composition view (subnets/ports/disabled; §1.4)

Guarantees: atomic three-file save with rollback (IDEA-003 §4 #1); the sidecar
tuple is rebound to place NAMES at load (place_order is derived/sorted —
IDEA-002 D12); a sidecar↔overlay revision mismatch refuses the load (repair:
splice{mode:"repair"}, feature_040); mutations append flat `kind:"net_*"`
ledger records (§3.3) and drift rows to `harness.net.drift.jsonl` (D7).

Runtime artifacts live in `.meta/.omt/` (git-ignored, D15); override with
OMT_NET_DIR / OMT_LEDGER_PATH (tests stay hermetic).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import PetriNetError
from .io import document_from_json, net_to_json
from .model import PetriNet

REPO_ROOT = Path(__file__).resolve().parents[3]

NET_FILENAME = "META_NET.petri.json"
SIDECAR_FILENAME = "net_state.sidecar.json"
OVERLAY_FILENAME = "supervisor.overlay.json"
DRIFT_FILENAME = "harness.net.drift.jsonl"


class NetNotBootstrappedError(PetriNetError):
    """The net bundle does not exist yet (IDEA-002 v4 §5.1 — sync is first-call)."""


class RevisionMismatchError(PetriNetError):
    """Sidecar/overlay revisions disagree, or sidecar length != place count."""


def net_dir() -> Path:
    """Bundle directory: OMT_NET_DIR env (tests) or `.meta/.omt/` (D15)."""
    env = os.environ.get("OMT_NET_DIR")
    return Path(env) if env else REPO_ROOT / ".meta" / ".omt"


def _ledger_path() -> Path:
    env = os.environ.get("OMT_LEDGER_PATH")
    return Path(env) if env else REPO_ROOT / ".meta" / ".omt" / "ledger.jsonl"


def bundle_paths(base: Path) -> tuple[Path, Path, Path]:
    return (base / NET_FILENAME, base / SIDECAR_FILENAME, base / OVERLAY_FILENAME)


def is_bootstrapped(base: Path) -> bool:
    net_path, sidecar_path, _ = bundle_paths(base)
    return net_path.exists() and sidecar_path.exists()


def default_overlay(revision: int = 0) -> dict[str, Any]:
    """Empty composition view (IDEA-002 §1.4) — populated by feature_040."""
    return {
        "net_file": NET_FILENAME,
        "revision": revision,
        "supervisor": {"places": [], "transitions": []},
        "subnets": {},
        "disabled": [],
    }


@dataclass
class NetState:
    """In-memory image of the bundle: structure + live marking + composition."""

    net: PetriNet
    layout: dict[str, Any] | None
    live_marking: dict[str, int]  # by place NAME (rebased at load, §11 #7)
    revision: int
    overlay: dict[str, Any]
    updated_at: str = ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(base: Path) -> NetState:
    """Load the bundle; rebind the sidecar tuple to place names (§11 #7)."""
    net_path, sidecar_path, overlay_path = bundle_paths(base)
    if not is_bootstrapped(base):
        raise NetNotBootstrappedError(
            f"net not bootstrapped in {base} — first call is omt_net{{op:sync}} "
            "(feature_040); IDEA-002 v4 §5.1"
        )
    doc = document_from_json(net_path.read_text(encoding="utf-8"))
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    order = doc.net.place_order
    live = sidecar["live_marking"]
    if len(live) != len(order):
        raise RevisionMismatchError(
            f"sidecar live_marking length {len(live)} != place count {len(order)}"
        )
    overlay = (
        json.loads(overlay_path.read_text(encoding="utf-8"))
        if overlay_path.exists()
        else default_overlay(sidecar["revision"])
    )
    if overlay.get("revision") != sidecar["revision"]:
        raise RevisionMismatchError(
            f"overlay revision {overlay.get('revision')} != sidecar revision "
            f"{sidecar['revision']} — repair via splice{{mode:'repair'}} (feature_040)"
        )
    return NetState(
        net=doc.net,
        layout=doc.layout,
        live_marking=dict(zip(order, live)),
        revision=sidecar["revision"],
        overlay=overlay,
        updated_at=sidecar.get("updated_at", ""),
    )


def save(base: Path, st: NetState) -> None:
    """Atomic three-file write with rollback (IDEA-003 §4 #1): any failure
    restores the previous bytes of every file already replaced."""
    base.mkdir(parents=True, exist_ok=True)
    net_path, sidecar_path, overlay_path = bundle_paths(base)
    sidecar = {
        "live_marking": [st.live_marking[p] for p in st.net.place_order],
        "revision": st.revision,
        "updated_at": st.updated_at or _utc_now(),
    }
    overlay = dict(st.overlay, revision=st.revision, net_file=NET_FILENAME)
    payloads = {
        net_path: net_to_json(st.net, layout=st.layout),
        sidecar_path: json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n",
        overlay_path: json.dumps(overlay, indent=2, ensure_ascii=False) + "\n",
    }
    previous: dict[Path, bytes | None] = {
        p: (p.read_bytes() if p.exists() else None) for p in payloads
    }
    replaced: list[Path] = []
    try:
        for path, text in payloads.items():
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(text, encoding="utf-8")
            try:
                os.replace(tmp, path)
            finally:
                tmp.unlink(missing_ok=True)
            replaced.append(path)
    except BaseException:
        for path in replaced:
            old = previous[path]
            if old is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(old)
        raise


def init_empty(base: Path) -> NetState:
    """Create an empty-net bundle at revision 0 (test/dev bootstrap — the real
    net is born via omt_net{op:sync}, feature_040; IDEA-002 v4 §5.1)."""
    st = NetState(
        net=PetriNet(),
        layout=None,
        live_marking={},
        revision=0,
        overlay=default_overlay(0),
        updated_at=_utc_now(),
    )
    save(base, st)
    return st


def rebase_marking(live_marking: dict[str, int], new_net: PetriNet) -> dict[str, int]:
# TA: xref: feature_040 design (resume @ .sandbox/pause_2026-08-30c.md): splice{mode:remove|disable} = REBUILD a new PetriNet via add_* copying survivors (model is add-only, D2 — never extend model.py), then rebase_marking; overlay = DERIVED at every save() from net (f{N}_ prefix membership, ports = unprefixed places touched by subnet transitions) + preserved disabled list — overlay↔net drift impossible by construction.
    """Name-based rebase across a structure change (IDEA-002 D12): surviving
    places keep their tokens; new places start at their M0; removed places
    drop out (token policy is the splice op's concern, feature_040)."""
    return {
        p: live_marking.get(p, new_net.initial_marking[p]) for p in new_net.place_order
    }


def append_ledger(record: dict[str, Any]) -> None:
    """Append one flat `kind:"net_*"` record (IDEA-002 §3.3 record style)."""
    path = _ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": _utc_now(), **record}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_drift(base: Path, record: dict[str, Any]) -> None:
    """Append a net-vs-ledger drift record (IDEA-002 §8.2; D7)."""
    record = {"ts": _utc_now(), "kind": "net_drift", **record}
    with open(base / DRIFT_FILENAME, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_ledger_net_records() -> list[dict[str, Any]]:
    """All `net_*` records across the ledger store (hot + latest archive —
    the mining-window convention, not the gate-truth window)."""
    path = _ledger_path()
    records: list[dict[str, Any]] = []
    archives = sorted(path.parent.glob("ledger-*.jsonl"))
    if archives:
        records.extend(_read_jsonl(archives[-1]))
    records.extend(_read_jsonl(path))
    return [r for r in records if str(r.get("kind", "")).startswith("net_")]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def fire(base: Path, transition: str, *, reasoning: str, session: str) -> NetState:
    """Validate enablement at the live marking, apply, persist atomically,
    ledger `kind:"net_fire"` (IDEA-002 §5.0 — marking-only; no conformance
    regression). Disabled/unknown transitions raise before any write."""
    st = load(base)
    successor = st.net.fire_marking(
        tuple(st.live_marking[p] for p in st.net.place_order), transition
    )  # TransitionNotEnabledError / UnknownTransitionError raised here, pre-write
    st.live_marking = dict(zip(st.net.place_order, successor))
    st.revision += 1
    st.updated_at = _utc_now()
    save(base, st)
    append_ledger({
        "kind": "net_fire",
        "session": session,
        "transition": transition,
        "revision": st.revision,
        "reasoning": reasoning,
    })
    return st
