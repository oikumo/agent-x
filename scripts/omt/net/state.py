"""Net bundle state store — feature_039.adaptive_net_engine (+ feature_040).

Three-file bundle (IDEA-002 §1.4/§7.2, PROJECT.md D16 — the SSOT state proper):

    META_NET.petri.json      v1 structure + M0 (format unchanged, D6)
    net_state.sidecar.json   {live_marking, revision, updated_at} — live state
    supervisor.overlay.json  composition view (subnets/ports/disabled; §1.4)

Guarantees: atomic three-file save with rollback (IDEA-003 §4 #1); the sidecar
tuple is rebound to place NAMES at load (place_order is derived/sorted —
IDEA-002 D12); a sidecar↔overlay revision mismatch refuses the load (repair:
splice{mode:"repair"}); mutations append flat `kind:"net_*"` ledger records
(§3.3) and drift rows to `harness.net.drift.jsonl` (D7).

feature_040.net_composition_supervisor adds: the splice engine (modes
add|remove|disable|undo|repair; token policies forbid|reroute|drain; the model
is add-only so removal REBUILDS a new PetriNet from survivors, D2), the sync
op (§5.1 first-call supervisor skeleton + deterministic proposal scan, never
auto-applied — D4), the 9-vector conformance gate on every structure-changing
op (P8), and the DERIVED overlay recomputed at every save (P10 — overlay↔net
drift impossible by construction; the disabled list is preserved across
derivation).

Runtime artifacts live in `.meta/.omt/` (git-ignored, D15); override with
OMT_NET_DIR / OMT_LEDGER_PATH (tests stay hermetic). feature_040 adds
OMT_NET_FEATURES_DIR / OMT_NET_WORK_MD overrides for the sync reality scan.
"""
from __future__ import annotations

import copy
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import PetriNetError, TransitionNotEnabledError
from .io import document_from_json, net_to_json
from .model import PetriNet

REPO_ROOT = Path(__file__).resolve().parents[3]

NET_FILENAME = "META_NET.petri.json"
SIDECAR_FILENAME = "net_state.sidecar.json"
OVERLAY_FILENAME = "supervisor.overlay.json"
DRIFT_FILENAME = "harness.net.drift.jsonl"

CONFORMANCE_DIR = REPO_ROOT / "shared" / "petri-net" / "conformance" / "analysis-v1"

SUBNET_PREFIX_RE = re.compile(r"^f(\d+)_")
_FEATURE_DIR_RE = re.compile(r"^feature_(\d+)(?:\.|$)")
_TASK_ROW_RE = re.compile(r"^- \[([ xX~!])\] \*\*feature_(\d+)")
_CHECKBOX_M0 = {" ": "pending", "~": "active", "!": "active", "x": "done", "X": "done"}

BOUNDARY_PORTS = ("feature_ready", "resource_token", "goal_satisfied")
# TA: xref: feature_041 design (resume @ .sandbox/pause_2026-08-30d.md R1-R8): RESOURCE_PLACES catalog (agent_attention/src_edit_capacity/tests_capacity/harness_surface_round/e2e_receipt, ALL cap=1 per IDEA-002 v4 §2.2 — the IDEA-005 example's 2/3 is a sketch, not canonical) joins the sync() bootstrap skeleton + resync emits ONE add_resource_places proposal entry (missing places + retrofit arcs for existing subnets, D4 never auto-applied); _subnet_mutation wires agent_attention (f{N}_start claims, f{N}_complete releases → serial-mirror conflict trap, §2.3); derive_overlay ports.resources = sorted((entry∪exit) ∩ RESOURCE_PLACES) — stays a pure function of the net (P10).


RESOURCE_PLACES = (
    "agent_attention",
    "src_edit_capacity",
    "tests_capacity",
    "harness_surface_round",
    "e2e_receipt",
)


class NetNotBootstrappedError(PetriNetError):
    """The net bundle does not exist yet (IDEA-002 v4 §5.1 — sync is first-call)."""


class RevisionMismatchError(PetriNetError):
    """Sidecar/overlay revisions disagree, or sidecar length != place count."""


class SpliceError(PetriNetError):
    """Clean splice/sync failure carrying a stable envelope error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def net_dir() -> Path:
    """Bundle directory: OMT_NET_DIR env (tests) or `.meta/.omt/` (D15)."""
    env = os.environ.get("OMT_NET_DIR")
    return Path(env) if env else REPO_ROOT / ".meta" / ".omt"


def _ledger_path() -> Path:
    env = os.environ.get("OMT_LEDGER_PATH")
    return Path(env) if env else REPO_ROOT / ".meta" / ".omt" / "ledger.jsonl"


def _features_dir() -> Path:
    env = os.environ.get("OMT_NET_FEATURES_DIR")
    return (
        Path(env)
        if env
        else REPO_ROOT / ".meta" / "software_development_process" / "2.requirements" / "features"
    )


def _work_md_path() -> Path:
    env = os.environ.get("OMT_NET_WORK_MD")
    return Path(env) if env else REPO_ROOT / "WORK.md"


def bundle_paths(base: Path) -> tuple[Path, Path, Path]:
    return (base / NET_FILENAME, base / SIDECAR_FILENAME, base / OVERLAY_FILENAME)


def is_bootstrapped(base: Path) -> bool:
    net_path, sidecar_path, _ = bundle_paths(base)
    return net_path.exists() and sidecar_path.exists()


def default_overlay(revision: int = 0) -> dict[str, Any]:
    """Empty composition view (IDEA-002 §1.4) — seed for init/repair."""
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


def derive_overlay(net: PetriNet, disabled: list[str] | None = None) -> dict[str, Any]:
    """P10: the composition view is a pure function of the flat union net
    (+ the preserved disabled list) — overlay↔net drift impossible by
    construction. Subnets are keyed `feature_{N}` from the `f{N}_` prefix;
    supervisor nodes are the unprefixed rest; per-subnet ports are the
    unprefixed places the subnet's transitions input from (entry) / output
    to (exit). `resources` = the (entry ∪ exit) ∩ RESOURCE_PLACES subset
    (feature_041 R3 — still a pure function of the net, P10)."""
    supervisor_places: list[str] = []
    supervisor_transitions: list[str] = []
    subnets: dict[str, dict[str, Any]] = {}

    def _subnet_for(node: str) -> dict[str, Any] | None:
        m = SUBNET_PREFIX_RE.match(node)
        if not m:
            return None
        return subnets.setdefault(
            f"feature_{m.group(1)}",
            {
                "prefix": f"f{m.group(1)}_",
                "places": [],
                "transitions": [],
                "ports": {"entry": [], "exit": [], "resources": []},
            },
        )

    for p in net.place_order:
        sub = _subnet_for(p)
        (sub["places"] if sub is not None else supervisor_places).append(p)
    for t in net.transition_order:
        sub = _subnet_for(t)
        (sub["transitions"] if sub is not None else supervisor_transitions).append(t)
    for sub in subnets.values():
        entry: set[str] = set()
        exit_: set[str] = set()
        for t in sub["transitions"]:
            for p in net.inputs[t]:
                if not SUBNET_PREFIX_RE.match(p):
                    entry.add(p)
            for p in net.outputs[t]:
                if not SUBNET_PREFIX_RE.match(p):
                    exit_.add(p)
        sub["ports"] = {
            "entry": sorted(entry),
            "exit": sorted(exit_),
            "resources": sorted((entry | exit_) & set(RESOURCE_PLACES)),
        }
    return {
        "net_file": NET_FILENAME,
        "revision": 0,  # stamped by save()
        "supervisor": {"places": supervisor_places, "transitions": supervisor_transitions},
        "subnets": subnets,
        "disabled": list(disabled or []),
    }


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
    restores the previous bytes of every file already replaced. The overlay
    is RE-DERIVED from the net here (P10) — callers mutate the net and the
    disabled list, never the membership sections."""
    base.mkdir(parents=True, exist_ok=True)
    net_path, sidecar_path, overlay_path = bundle_paths(base)
    st.overlay = derive_overlay(st.net, disabled=st.overlay.get("disabled", []))
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
    net is born via omt_net{op:sync}; IDEA-002 v4 §5.1)."""
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
    drop out (token policy is the splice op's concern)."""
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


# ---------------------------------------------------------------------------
# Conformance gate (P8 — IDEA-002 v4 §5.0 trigger matrix)
# ---------------------------------------------------------------------------

def _conformance_gate() -> dict[str, Any]:
    """Re-run the 9 shared conformance vectors; failure raises pre-save."""
    from . import conformance  # noqa: PLC0415 (call-time lookup — tests patch)

    results = conformance.run_vectors(CONFORMANCE_DIR)
    failures = [r["id"] for r in results if not r["ok"]]
    if failures:
        raise SpliceError(
            "conformance_failed",
            f"conformance regression on vectors: {failures}",
        )
    return {"vectors": len(results), "ok": True}


# ---------------------------------------------------------------------------
# Splice engine (P1–P5 — IDEA-002 v4 §3; the model is add-only, D2)
# ---------------------------------------------------------------------------

def _validate_add_mutation(mutation: Any) -> tuple[list[dict], list[dict], list[dict]]:
    if not isinstance(mutation, dict):
        raise SpliceError(
            "invalid_mutation",
            f"mutation must be a JSON object, got {type(mutation).__name__}",
        )
    unknown = set(mutation) - {"add_places", "add_transitions", "add_arcs"}
    if unknown:
        raise SpliceError(
            "invalid_mutation", f"add mutation has unknown member(s): {sorted(unknown)}"
        )
    places = mutation.get("add_places", [])
    transitions = mutation.get("add_transitions", [])
    arcs = mutation.get("add_arcs", [])
    if not all(isinstance(x, list) for x in (places, transitions, arcs)):
        raise SpliceError(
            "invalid_mutation", "add_places/add_transitions/add_arcs must be arrays"
        )
    for p in places:
        if not isinstance(p, dict) or not isinstance(p.get("name"), str) or not p["name"]:
            raise SpliceError(
                "invalid_mutation", f"add_places entries need a non-empty name: {p!r}"
            )
        tokens = p.get("tokens", 0)
        if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
            raise SpliceError(
                "invalid_mutation",
                f"add_places tokens must be a non-negative int: {p!r}",
            )
    for t in transitions:
        if not isinstance(t, dict) or not isinstance(t.get("name"), str) or not t["name"]:
            raise SpliceError(
                "invalid_mutation",
                f"add_transitions entries need a non-empty name: {t!r}",
            )
    for a in arcs:
        if (
            not isinstance(a, dict)
            or not isinstance(a.get("source"), str)
            or not isinstance(a.get("target"), str)
        ):
            raise SpliceError(
                "invalid_mutation", f"add_arcs entries need source/target strings: {a!r}"
            )
        weight = a.get("weight", 1)
        if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
            raise SpliceError(
                "invalid_mutation", f"add_arcs weight must be a positive int: {a!r}"
            )
    return places, transitions, arcs


def _apply_add(net: PetriNet, places: list[dict], transitions: list[dict], arcs: list[dict]) -> None:
    """Apply an add-mutation; arc direction is resolved by node kinds
    (place→transition = add_input; transition→place = add_output BY KEYWORD —
    model §9 arg-order gotcha). Runs on a deepcopy (validate-all-then-apply)."""
    try:
        for p in places:
            net.add_place(p["name"], p.get("tokens", 0))
        for t in transitions:
            net.add_transition(t["name"])
        for a in arcs:
            source, target, weight = a["source"], a["target"], a.get("weight", 1)
            if source in net.places:
                net.add_input(source, target, weight)
            else:
                net.add_output(transition=source, place=target, weight=weight)
    except (PetriNetError, ValueError) as exc:
        raise SpliceError("invalid_mutation", str(exc)) from exc


def _validate_remove_mutation(
    mutation: Any,
) -> tuple[set[str], set[str], str, dict[str, str]]:
    if not isinstance(mutation, dict):
        raise SpliceError(
            "invalid_mutation",
            f"mutation must be a JSON object, got {type(mutation).__name__}",
        )
    unknown = set(mutation) - {"remove_places", "remove_transitions", "token_policy", "reroute"}
    if unknown:
        raise SpliceError(
            "invalid_mutation",
            f"remove mutation has unknown member(s): {sorted(unknown)}",
        )
    removed_places = mutation.get("remove_places", [])
    removed_transitions = mutation.get("remove_transitions", [])
    policy = mutation.get("token_policy", "forbid")
    reroute = mutation.get("reroute", {})
    if not isinstance(removed_places, list) or not all(
        isinstance(p, str) for p in removed_places
    ):
        raise SpliceError("invalid_mutation", "remove_places must be an array of names")
    if not isinstance(removed_transitions, list) or not all(
        isinstance(t, str) for t in removed_transitions
    ):
        raise SpliceError("invalid_mutation", "remove_transitions must be an array of names")
    if policy not in ("forbid", "reroute", "drain"):
        raise SpliceError("invalid_mutation", f"unknown token_policy: {policy!r}")
    if not isinstance(reroute, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in reroute.items()
    ):
        raise SpliceError("invalid_mutation", "reroute must be an object place->place")
    if not removed_places and not removed_transitions:
        raise SpliceError("invalid_mutation", "remove mutation names no nodes")
    return set(removed_places), set(removed_transitions), policy, reroute


def _removed_record(
    net: PetriNet,
    live_marking: dict[str, int],
    removed_places: set[str],
    removed_transitions: set[str],
) -> dict[str, Any]:
    """Full removed structure (places+M0, transitions, arcs, live tokens) —
    sufficient for inverse replay (splice{mode:'undo'}, IDEA-002 §11 #8)."""
    arcs = []
    for t in net.transition_order:
        for p, w in net.inputs[t].items():
            if p in removed_places or t in removed_transitions:
                arcs.append({"source": p, "target": t, "weight": w})
        for p, w in net.outputs[t].items():
            if p in removed_places or t in removed_transitions:
                arcs.append({"source": t, "target": p, "weight": w})
    arcs.sort(key=lambda a: (a["source"], a["target"]))
    return {
        "places": [
            {"name": p, "tokens": net.initial_marking[p], "live": live_marking.get(p, 0)}
            for p in sorted(removed_places)
        ],
        "transitions": [{"name": t} for t in sorted(removed_transitions)],
        "arcs": arcs,
    }


def _drain(net: PetriNet, live_marking: dict[str, int], removed_places: set[str]) -> dict[str, int]:
    """Drain policy: fire enabled transitions (transition_order — deterministic)
    while they strictly decrease the tokens held in removed places; a full
    pass with no such fire is an error (P2)."""
    live = dict(live_marking)

    def held(marking: dict[str, int]) -> int:
        return sum(marking.get(p, 0) for p in removed_places)

    while held(live) > 0:
        progress = False
        for t in net.transition_order:
            try:
                successor = net.fire_marking(
                    tuple(live[p] for p in net.place_order), t
                )
            except TransitionNotEnabledError:
                continue
            after = dict(zip(net.place_order, successor))
            if held(after) < held(live):
                live = after
                progress = True
                break
        if not progress:
            stuck = sorted(p for p in removed_places if live.get(p, 0) > 0)
            raise SpliceError(
                "drain_no_progress",
                f"drain: no enabled transition consumes from {stuck}",
            )
    return live


def _apply_token_policy(
    net: PetriNet,
    live_marking: dict[str, int],
    removed_places: set[str],
    policy: str,
    reroute: dict[str, str],
) -> dict[str, int]:
    live = dict(live_marking)
    holders = [p for p in sorted(removed_places) if live.get(p, 0) > 0]
    if policy == "forbid":
        if holders:
            raise SpliceError(
                "token_policy_violation",
                f"forbid: removed place(s) hold live tokens: {holders}",
            )
    elif policy == "reroute":
        for p in holders:
            target = reroute.get(p)
            if target is None:
                raise SpliceError(
                    "token_policy_violation",
                    f"reroute: no target named for token-holding place {p!r}",
                )
            if target not in net.places or target in removed_places:
                raise SpliceError(
                    "invalid_mutation",
                    f"reroute target must be a surviving place: {target!r}",
                )
            live[target] = live.get(target, 0) + live[p]
    elif policy == "drain":
        live = _drain(net, live, removed_places)
    return live


def _rebuild_without(
    net: PetriNet, removed_places: set[str], removed_transitions: set[str]
) -> PetriNet:
    """P2: the model is add-only (D2) — removal REBUILDS a new PetriNet via
    add_* copying survivors (places keep their M0; arcs touching removed
    nodes are filtered)."""
    new = PetriNet()
    keep_p = sorted(p for p in net.places if p not in removed_places)
    keep_t = sorted(t for t in net.transitions if t not in removed_transitions)
    for p in keep_p:
        new.add_place(p, net.initial_marking[p])
    for t in keep_t:
        new.add_transition(t)
    for t in keep_t:
        for p, w in net.inputs[t].items():
            if p not in removed_places:
                new.add_input(p, t, w)
        for p, w in net.outputs[t].items():
            if p not in removed_places:
                new.add_output(transition=t, place=p, weight=w)
    return new


def _remove_nodes(
    st: NetState,
    removed_places: set[str],
    removed_transitions: set[str],
    policy: str,
    reroute: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Shared remove/disable path: validate → record → token policy →
    conformance gate → rebuild + rebase (revision bump is the caller's)."""
    for p in sorted(removed_places):
        if p not in st.net.places:
            raise SpliceError("invalid_mutation", f"unknown place: {p!r}")
    for t in sorted(removed_transitions):
        if t not in st.net.transitions:
            raise SpliceError("invalid_mutation", f"unknown transition: {t!r}")
    record = _removed_record(st.net, st.live_marking, removed_places, removed_transitions)
    live = _apply_token_policy(st.net, st.live_marking, removed_places, policy, reroute)
    gate = _conformance_gate()
    new_net = _rebuild_without(st.net, removed_places, removed_transitions)
    st.net = new_net
    st.live_marking = rebase_marking(live, new_net)
    return record, gate


def _bump(st: NetState) -> None:
    st.revision += 1
    st.updated_at = _utc_now()


def _splice_add(
    base: Path, mutation: Any, *, reasoning: str, session: str, feature: str
) -> tuple[NetState, dict[str, Any]]:
    st = load(base)
    places, transitions, arcs = _validate_add_mutation(mutation)
    candidate = copy.deepcopy(st.net)
    _apply_add(candidate, places, transitions, arcs)
    gate = _conformance_gate()
    st.net = candidate
    st.live_marking = rebase_marking(st.live_marking, candidate)
    _bump(st)
    save(base, st)
    append_ledger({
        "kind": "net_splice",
        "mode": "add",
        "mutation": mutation,
        "reasoning": reasoning,
        "session": session,
        "feature": feature,
        "revision": st.revision,
        "conformance": gate,
    })
    return st, {"conformance": gate}


def _splice_remove(
    base: Path, mutation: Any, *, reasoning: str, session: str, feature: str
) -> tuple[NetState, dict[str, Any]]:
    st = load(base)
    removed_places, removed_transitions, policy, reroute = _validate_remove_mutation(mutation)
    record, gate = _remove_nodes(st, removed_places, removed_transitions, policy, reroute)
    _bump(st)
    save(base, st)
    append_ledger({
        "kind": "net_splice",
        "mode": "remove",
        "mutation": mutation,
        "removed": record,
        "token_policy": policy,
        "reasoning": reasoning,
        "session": session,
        "feature": feature,
        "revision": st.revision,
        "conformance": gate,
    })
    return st, {"conformance": gate, "removed": record}


def _subnet_key_prefix(subnet: str) -> tuple[str, str]:
    """--subnet accepts feature_039 | f039_ | f039 | 039 → (overlay key, prefix)."""
    s = subnet.strip()
    if s.startswith("feature_"):
        n = s[len("feature_"):]
    elif s.startswith("f"):
        n = s[1:].rstrip("_")
    else:
        n = s
    if not n.isdigit():
        raise SpliceError("unknown_subnet", f"cannot parse subnet: {subnet!r}")
    return f"feature_{n}", f"f{n}_"


def _splice_disable(
    base: Path, mutation: Any, subnet: str, *, reasoning: str, session: str, feature: str
) -> tuple[NetState, dict[str, Any]]:
    """P3: disable ≡ remove-with-policy scoped by subnet prefix + ledger
    kind:"net_disable" (full structure for inverse replay) + overlay.disabled
    append (archive visibility, IDEA-002 §1.4/§11 #8)."""
    if not subnet:
        raise SpliceError("invalid_mutation", "mode disable requires --subnet")
    st = load(base)
    key, prefix = _subnet_key_prefix(subnet)
    removed_places = {p for p in st.net.places if p.startswith(prefix)}
    removed_transitions = {t for t in st.net.transitions if t.startswith(prefix)}
    if not removed_places and not removed_transitions:
        raise SpliceError("unknown_subnet", f"no nodes with prefix {prefix!r}")
    policy, reroute = "forbid", {}
    if mutation is not None:
        if not isinstance(mutation, dict):
            raise SpliceError("invalid_mutation", "disable mutation must be an object")
        unknown = set(mutation) - {"token_policy", "reroute"}
        if unknown:
            raise SpliceError(
                "invalid_mutation",
                f"disable mutation has unknown member(s): {sorted(unknown)}",
            )
        policy = mutation.get("token_policy", "forbid")
        reroute = mutation.get("reroute", {})
        if policy not in ("forbid", "reroute", "drain"):
            raise SpliceError("invalid_mutation", f"unknown token_policy: {policy!r}")
        if not isinstance(reroute, dict):
            raise SpliceError("invalid_mutation", "reroute must be an object place->place")
    record, gate = _remove_nodes(st, removed_places, removed_transitions, policy, reroute)
    disabled = list(st.overlay.get("disabled", []))
    if key not in disabled:
        disabled.append(key)
    st.overlay["disabled"] = disabled
    _bump(st)
    save(base, st)
    append_ledger({
        "kind": "net_disable",
        "mode": "disable",
        "subnet": key,
        "removed": record,
        "token_policy": policy,
        "reasoning": reasoning,
        "session": session,
        "feature": feature,
        "revision": st.revision,
        "conformance": gate,
    })
    return st, {"conformance": gate, "removed": record, "subnet": key}


def _splice_undo(
    base: Path, *, reasoning: str, session: str, feature: str
) -> tuple[NetState, dict[str, Any]]:
    """P4: inverse-replay the LATEST structural ledger record (add → remove
    those nodes forbid; remove/disable → re-add the recorded structure incl.
    recorded live tokens). undo/repair records are not themselves undoable."""
    records = [
        r
        for r in read_ledger_net_records()
        if r.get("kind") in ("net_splice", "net_disable")
        and r.get("mode") in ("add", "remove", "disable")
    ]
    if not records:
        raise SpliceError("nothing_to_undo", "no structural ledger record to undo")
    last = records[-1]
    undoes = last.get("revision", 0)
    st = load(base)
    if last["mode"] == "add":
        mutation = last.get("mutation", {})
        places = {p["name"] for p in mutation.get("add_places", [])}
        transitions = {t["name"] for t in mutation.get("add_transitions", [])}
        if not places and not transitions:
            raise SpliceError(
                "nothing_to_undo", f"latest structural record (rev {undoes}) added no nodes"
            )
        _record, gate = _remove_nodes(st, places, transitions, "forbid", {})
    else:  # remove | disable → re-add the recorded structure
        removed = last.get("removed", {})
        mutation = {
            "add_places": [
                {"name": p["name"], "tokens": p["tokens"]}
                for p in removed.get("places", [])
            ],
            "add_transitions": list(removed.get("transitions", [])),
            "add_arcs": list(removed.get("arcs", [])),
        }
        places, transitions, arcs = _validate_add_mutation(mutation)
        candidate = copy.deepcopy(st.net)
        _apply_add(candidate, places, transitions, arcs)
        gate = _conformance_gate()
        st.net = candidate
        st.live_marking = rebase_marking(st.live_marking, candidate)
        for p in removed.get("places", []):
            st.live_marking[p["name"]] = p.get("live", p["tokens"])
        if last["mode"] == "disable":
            key = last.get("subnet", "")
            st.overlay["disabled"] = [
                d for d in st.overlay.get("disabled", []) if d != key
            ]
    _bump(st)
    save(base, st)
    append_ledger({
        "kind": "net_splice",
        "mode": "undo",
        "undoes": undoes,
        "reasoning": reasoning,
        "session": session,
        "feature": feature,
        "revision": st.revision,
        "conformance": gate,
    })
    return st, {"conformance": gate, "undoes": undoes}


def _overlay_missing_nodes(net: PetriNet, overlay: dict[str, Any]) -> list[str]:
    missing: set[str] = set()
    supervisor = overlay.get("supervisor", {})
    for name in supervisor.get("places", []):
        if name not in net.places:
            missing.add(name)
    for name in supervisor.get("transitions", []):
        if name not in net.transitions:
            missing.add(name)
    for sub in overlay.get("subnets", {}).values():
        for name in sub.get("places", []):
            if name not in net.places:
                missing.add(name)
        for name in sub.get("transitions", []):
            if name not in net.transitions:
                missing.add(name)
        ports = sub.get("ports", {})
        for name in ports.get("entry", []) + ports.get("exit", []):
            if name not in net.places:
                missing.add(name)
    return sorted(missing)


def _splice_repair(
    base: Path, *, reasoning: str, session: str, feature: str
) -> tuple[NetState, dict[str, Any]]:
    """P5: the load() refusal recovery path (D12) — read the raw files WITHOUT
    the revision check, validate every overlay-referenced node exists in the
    net, then realign by re-saving (the derived overlay carries the sidecar
    revision by construction). Revision is NOT bumped (no state mutation)."""
    net_path, sidecar_path, overlay_path = bundle_paths(base)
    if not is_bootstrapped(base):
        raise NetNotBootstrappedError(
            f"net not bootstrapped in {base} — first call is omt_net{{op:sync}}"
        )
    doc = document_from_json(net_path.read_text(encoding="utf-8"))
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    overlay = (
        json.loads(overlay_path.read_text(encoding="utf-8"))
        if overlay_path.exists()
        else default_overlay(sidecar["revision"])
    )
    missing = _overlay_missing_nodes(doc.net, overlay)
    if missing:
        raise SpliceError(
            "overlay_nodes_missing",
            f"overlay references nodes not in the net: {missing}",
        )
    live = sidecar["live_marking"]
    if len(live) != len(doc.net.place_order):
        raise RevisionMismatchError(
            f"sidecar live_marking length {len(live)} != place count "
            f"{len(doc.net.place_order)} — not repairable by realignment"
        )
    gate = _conformance_gate()
    st = NetState(
        net=doc.net,
        layout=doc.layout,
        live_marking=dict(zip(doc.net.place_order, live)),
        revision=sidecar["revision"],
        overlay=overlay,
        updated_at=_utc_now(),
    )
    save(base, st)
    append_ledger({
        "kind": "net_splice",
        "mode": "repair",
        "reasoning": reasoning,
        "session": session,
        "feature": feature,
        "revision": st.revision,
        "conformance": gate,
    })
    return st, {"conformance": gate}


def splice(
    base: Path,
    mode: str,
    *,
    mutation: Any = None,
    subnet: str = "",
    reasoning: str,
    session: str,
    feature: str = "",
) -> tuple[NetState, dict[str, Any]]:
    """Atomic structural transaction (IDEA-002 v4 §3/§5.0). Modes:
    add|remove|disable|undo|repair. Returns (state, info) — info carries the
    conformance record + mode extras (removed/subnet/undoes)."""
    if mode == "add":
        if mutation is None:
            raise SpliceError("invalid_mutation", "mode add requires --mutation")
        return _splice_add(base, mutation, reasoning=reasoning, session=session, feature=feature)
    if mode == "remove":
        if mutation is None:
            raise SpliceError("invalid_mutation", "mode remove requires --mutation")
        return _splice_remove(base, mutation, reasoning=reasoning, session=session, feature=feature)
    if mode == "disable":
        return _splice_disable(
            base, mutation, subnet, reasoning=reasoning, session=session, feature=feature
        )
    if mode == "undo":
        return _splice_undo(base, reasoning=reasoning, session=session, feature=feature)
    if mode == "repair":
        return _splice_repair(base, reasoning=reasoning, session=session, feature=feature)
    raise SpliceError("invalid_mutation", f"unknown splice mode: {mode!r}")


# ---------------------------------------------------------------------------
# Sync (P6/P7 — IDEA-002 v4 §5.1 bootstrap + §11 #6 net↔reality scan)
# ---------------------------------------------------------------------------

def _md_section(text: str, header: str) -> str:
    """One `## ` section's body (header matched by prefix — real headers may
    carry suffixes, e.g. '## Projects (synced by ...)')."""
    lines, out, capturing = text.splitlines(), [], False
    for line in lines:
        if line.startswith("## "):
            if capturing:
                break
            capturing = line.strip().startswith(header)
            continue
        if capturing:
            out.append(line)
    return "\n".join(out)


def _scan_reality() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Reality scan (P6): feature dirs → {N: slug}; WORK.md ## Tasks
    checkboxes → {N: pending|active|done}; ## Projects table → {N: project}."""
    features: dict[str, str] = {}
    fdir = _features_dir()
    if fdir.is_dir():
        for child in sorted(fdir.iterdir()):
            m = _FEATURE_DIR_RE.match(child.name)
            if m and child.is_dir():
                features[m.group(1)] = child.name
    checkboxes: dict[str, str] = {}
    projects: dict[str, str] = {}
    work = _work_md_path()
    if work.is_file():
        text = work.read_text(encoding="utf-8")
        for line in _md_section(text, "## Tasks").splitlines():
            m = _TASK_ROW_RE.match(line)
            if m:
                checkboxes[m.group(2)] = _CHECKBOX_M0[m.group(1)]
        for line in _md_section(text, "## Projects").splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3 or cells[0] in ("project", "") or set(cells[0]) <= set("-: "):
                continue
            for slug in cells[-1].split(","):
                sm = re.match(r"feature_(\d+)", slug.strip())
                if sm:
                    projects[sm.group(1)] = cells[0]
    return features, checkboxes, projects


def _subnet_mutation(n: str, m0: str) -> dict[str, Any]:
    """P7 deterministic lifecycle chain for feature N:
    start(pending + feature_ready + agent_attention → active + feature_ready),
    complete(active → done + goal_satisfied + agent_attention) — feature_041
    R2: start claims agent_attention, complete releases it (IDEA-002 §2.3
    serial-mirror conflict trap; claim/release appended last, 9 arcs)."""
    pending, active, done = f"f{n}_pending", f"f{n}_active", f"f{n}_done"
    start, complete = f"f{n}_start", f"f{n}_complete"
    return {
        "add_places": [
            {"name": pending, "tokens": 1 if m0 == "pending" else 0},
            {"name": active, "tokens": 1 if m0 == "active" else 0},
            {"name": done, "tokens": 1 if m0 == "done" else 0},
        ],
        "add_transitions": [{"name": start}, {"name": complete}],
        "add_arcs": [
            {"source": pending, "target": start, "weight": 1},
            {"source": "feature_ready", "target": start, "weight": 1},
            {"source": start, "target": active, "weight": 1},
            {"source": start, "target": "feature_ready", "weight": 1},
            {"source": active, "target": complete, "weight": 1},
            {"source": complete, "target": done, "weight": 1},
            {"source": complete, "target": "goal_satisfied", "weight": 1},
            # feature_041 R2: agent_attention claim (start) / release (complete)
            {"source": "agent_attention", "target": start, "weight": 1},
            {"source": complete, "target": "agent_attention", "weight": 1},
        ],
    }


def sync(base: Path, *, reasoning: str = "", session: str = "") -> tuple[NetState, dict[str, Any]]:
    """net↔reality bootstrap + resync (IDEA-002 v4 §5.1/§11 #6). First call
    materializes the supervisor skeleton (boundary ports, NO supervisor
    transitions in v1) behind the conformance gate; every call then scans
    reality and emits a deterministic PROPOSAL — never auto-applied (D4; the
    agent applies it via splice). Resyncs bump nothing (read-only on state;
    the ledger record is the audit, never silent)."""
    bootstrap = not is_bootstrapped(base)
    gate = None
    if bootstrap:
        net = PetriNet()
        net.add_place("feature_ready", 1)
        net.add_place("resource_token", 1)
        net.add_place("goal_satisfied", 0)
        for resource in RESOURCE_PLACES:  # feature_041 R1 catalog (all M0=1)
            net.add_place(resource, 1)
        st = NetState(
            net=net,
            layout=None,
            live_marking={
                "feature_ready": 1,
                "resource_token": 1,
                "goal_satisfied": 0,
                **{resource: 1 for resource in RESOURCE_PLACES},
            },
            revision=0,
            overlay=default_overlay(0),
            updated_at=_utc_now(),
        )
        gate = _conformance_gate()
        save(base, st)
    else:
        st = load(base)
    features, checkboxes, projects = _scan_reality()
    existing = set(st.overlay.get("subnets", {}))
    archived = set(st.overlay.get("disabled", []))
    add_subnets = []
    for n in sorted(features):
        key = f"feature_{n}"
        if key in existing or key in archived:
            continue
        m0 = checkboxes.get(n, "pending")
        add_subnets.append({
            "subnet": key,
            "slug": features[n],
            "project": projects.get(n),
            "m0": m0,
            "mutation": _subnet_mutation(n, m0),
        })
    disable_subnets = [
        {"subnet": key, "reason": "feature_dir_missing"}
        for key in sorted(existing)
        if key[len("feature_"):] not in features
    ]
    # feature_041 R5: resync of pre-041 bundles proposes ONE
    # add_resource_places entry (missing catalog places in catalog order +
    # agent_attention retrofit arcs for existing subnets lacking the wiring)
    # — D4: never auto-applied; apply BEFORE any pending add_subnets entry
    # (the subnet template references agent_attention).
    missing_resources = [p for p in RESOURCE_PLACES if p not in st.net.places]
    retrofit_arcs: list[dict[str, Any]] = []
    for key in sorted(existing):
        prefix = f"f{key[len('feature_') :]}_"
        start, complete = f"{prefix}start", f"{prefix}complete"
        if start in st.net.transitions and "agent_attention" not in st.net.inputs.get(
            start, {}
        ):
            retrofit_arcs.append(
                {"source": "agent_attention", "target": start, "weight": 1}
            )
        if complete in st.net.transitions and "agent_attention" not in st.net.outputs.get(
            complete, {}
        ):
            retrofit_arcs.append(
                {"source": complete, "target": "agent_attention", "weight": 1}
            )
    add_resource_places = []
    if missing_resources or retrofit_arcs:
        add_resource_places.append({
            "places": missing_resources,
            "mutation": {
                "add_places": [{"name": p, "tokens": 1} for p in missing_resources],
                "add_transitions": [],
                "add_arcs": retrofit_arcs,
            },
        })
    proposal = {
        "add_subnets": add_subnets,
        "disable_subnets": disable_subnets,
        "add_resource_places": add_resource_places,
    }
    record: dict[str, Any] = {
        "kind": "net_sync",
        "bootstrap": bootstrap,
        "revision": st.revision,
        "reasoning": reasoning,
        "session": session,
        "add_subnets": [e["subnet"] for e in add_subnets],
        "disable_subnets": [e["subnet"] for e in disable_subnets],
        "add_resource_places": missing_resources,
        "retrofit_arcs": len(retrofit_arcs),
    }
    if gate is not None:
        record["conformance"] = gate
    append_ledger(record)
    return st, {"bootstrap": bootstrap, "proposal": proposal, "conformance": gate}


# ---------------------------------------------------------------------------
# Resource reporting + lifecycle hook (feature_041 R4/R6 — IDEA-002 v4 §2.3)
# ---------------------------------------------------------------------------

def resource_report(st: NetState) -> dict[str, Any]:
    """R4: per-catalog-place capacity view + structural conflicts.

    resources[]: {place, capacity, live, capacity_ok, holders} for each
    RESOURCE_PLACES member present in the net (capacity = M0; holders — for
    agent_attention only — = subnets with f{N}_active marked; capacity_ok =
    live + held == capacity, so a checkbox-seeded active that never claimed
    surfaces as a violation — D16: drift visible, never silent).
    conflicts[]: pending subnets (f{N}_pending marked) whose f{N}_start is
    NOT enabled at the live marking; blocked_by = the empty UNPREFIXED input
    places of start (sorted). Legacy bundles (no catalog) report []/[].
    """
    resources: list[dict[str, Any]] = []
    for name in RESOURCE_PLACES:
        if name not in st.net.places:
            continue
        capacity = st.net.initial_marking[name]
        live = st.live_marking.get(name, 0)
        holders: list[str] = []
        if name == "agent_attention":
            holders = sorted(
                f"feature_{m.group(1)}"
                for p in st.net.places
                if (m := SUBNET_PREFIX_RE.match(p))
                and p.endswith("_active")
                and st.live_marking.get(p, 0) > 0
            )
        resources.append({
            "place": name,
            "capacity": capacity,
            "live": live,
            "capacity_ok": live + len(holders) == capacity,
            "holders": holders,
        })
    live_tuple = tuple(st.live_marking.get(p, 0) for p in st.net.place_order)
    conflicts: list[dict[str, Any]] = []
    for key in sorted(st.overlay.get("subnets", {})):
        prefix = f"f{key[len('feature_') :]}_"
        pending, start = f"{prefix}pending", f"{prefix}start"
        if pending not in st.net.places or start not in st.net.transitions:
            continue
        if st.live_marking.get(pending, 0) <= 0:
            continue
        if st.net.is_enabled_at(live_tuple, start):
            continue
        blocked_by = sorted(
            p
            for p in st.net.inputs.get(start, {})
            if not SUBNET_PREFIX_RE.match(p) and st.live_marking.get(p, 0) == 0
        )
        conflicts.append({
            "subnet": key,
            "transition": start,
            "blocked_by": blocked_by,
        })
    return {"resources": resources, "conflicts": conflicts}


def lifecycle_sync_hook(event: str) -> None:
    """R6: lifecycle auto-sync — re-sync the net on harness lifecycle events
    (project create/link/close/archive/reopen, new_feature --project link).

    Proposal-only (D4 — the agent applies via splice), ledger-audited by
    sync() itself, FAIL-OPEN (net errors never block the lifecycle op), and
    SILENT when the bundle is unbootstrapped (bootstrap stays an explicit
    agent action — IDEA-002 v4 §5.1) or when the proposal is empty. Prints
    exactly ONE stdout line when proposals are pending."""
    base = net_dir()
    if not is_bootstrapped(base):
        return
    try:
        _, info = sync(base, reasoning=f"lifecycle auto-sync ({event})")
    except Exception:  # noqa: BLE001 — fail-open by design (R6)
        return
    proposal = info.get("proposal", {})
    pending = sum(
        len(proposal.get(k, []))
        for k in ("add_subnets", "disable_subnets", "add_resource_places")
    )
    if pending:
        print(
            f"omt_net auto-sync ({event}): {pending} proposal(s) pending — "
            "apply via splice (D4)"
        )
