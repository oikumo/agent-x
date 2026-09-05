"""Ledger replay → dashboard snapshots — feature_043.meta_net_dashboard.

A pure fold over the ledger store (ALL `ledger-*.jsonl` sorted + hot, append
order = time order) into per-revision marking snapshots. Reuses the engine
appliers from `state.py` — `_apply_add`, `_apply_token_policy`,
`_rebuild_without`, `rebase_marking`, `fire_marking` — so replay carries NO
new net semantics (D2). Deliberately NOT reused: the conformance gate (it
tests the engine, not net content, and was enforced at mutation time) and
disk I/O (replay is in-memory; nothing is written).

Fail-closed (D16): unknown kinds/modes, pre-genesis structure ops, applier
failures, and fire of disabled/unknown transitions all raise
`SpliceError("invalid_replay")`; `build_snapshot` additionally refuses
`SpliceError("replay_mismatch")` unless the fold reproduces the live bundle
exactly (revision + full marking).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import TransitionNotEnabledError, UnknownTransitionError
from .model import PetriNet
from .state import (
    BOUNDARY_PORTS,
    POOL_PLACES,
    RESOURCE_PLACES,
    NetState,
    SpliceError,
    _apply_add,
    _apply_token_policy,
    _rebuild_without,
    _utc_now,
    _validate_add_mutation,
    _validate_remove_mutation,
    load,
    pool_counts,
    rebase_marking,
    resource_report,
)

SNAPSHOT_FORMAT = "meta-net-dashboard-snapshot"
SNAPSHOT_VERSION = 1

SKIP_MODES = ("repair",)


def _genesis() -> tuple[PetriNet, dict[str, int]]:
    """Era-accurate genesis: the 040-era bootstrap laid 3 boundary ports only
    (feature_ready=1, resource_token=1, goal_satisfied=0) — the RESOURCE_PLACES
    catalog arrived later via feature_041's add_resource_places resync (the
    live ledger proves it: that record adds all five). Today's sync code
    bootstraps WITH resources; replay must NOT (DuplicatePlace otherwise)."""
    net = PetriNet()
    live: dict[str, int] = {}
    for name, tokens in (
        ("feature_ready", 1),
        ("resource_token", 1),
        ("goal_satisfied", 0),
    ):
        net.add_place(name, tokens)
        live[name] = tokens
    return net, live


def read_store(store: Path) -> list[dict[str, Any]]:
    """All `net_*` records across the full store (archives sorted + hot)."""
    files = sorted(store.glob("ledger-*.jsonl"))
    hot = store / "ledger.jsonl"
    if hot.is_file():
        files.append(hot)
    records: list[dict[str, Any]] = []
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if str(rec.get("kind", "")).startswith("net_"):
                records.append(rec)
    return records


def _label(rec: dict[str, Any]) -> str:
    kind = rec.get("kind", "")
    if kind == "net_fire":
        return str(rec.get("transition", ""))
    if kind in ("net_splice", "net_disable"):
        mode = rec.get("mode", "")
        if mode == "add":
            return f"add {rec.get('feature', '')}".strip()
        if mode == "remove":
            return f"remove {rec.get('feature', '')}".strip()
        if mode == "disable":
            return f"disable {rec.get('subnet', '')}".strip()
        if mode == "undo":
            return f"undo rev {rec.get('undoes', '')}".strip()
        return str(mode)
    if kind == "net_sync":
        return "bootstrap" if rec.get("bootstrap") else "resync"
    return str(kind)


def _need_revision(rec: dict[str, Any]) -> int:
    rev = rec.get("revision")
    if not isinstance(rev, int):
        raise SpliceError("invalid_replay", f"record missing integer revision: {rec!r}")
    return rev


def _remove_like(
    net: PetriNet,
    live: dict[str, int],
    removed_places: set[str],
    removed_transitions: set[str],
    policy: str,
    reroute: dict[str, str],
) -> tuple[PetriNet, dict[str, int]]:
    """The `_remove_nodes` state transition minus record/gate (see module doc)."""
    for name in sorted(removed_places):
        if name not in net.places:
            raise SpliceError("invalid_replay", f"replay remove of unknown place: {name!r}")
    for name in sorted(removed_transitions):
        if name not in net.transitions:
            raise SpliceError("invalid_replay", f"replay remove of unknown transition: {name!r}")
    live_after = _apply_token_policy(net, live, removed_places, policy, reroute)
    new_net = _rebuild_without(net, removed_places, removed_transitions)
    return new_net, rebase_marking(live_after, new_net)


def _archive_recovery_map(
    net: PetriNet, live: dict[str, int], removed_places: set[str]
) -> dict[str, str]:
    """Archive-done recovery rule: the 39 rev5-43 disables persist
    policy=reroute but NOT the reroute map (live splice-disable drops the
    mutation — audit gap, see test report). Evidence chain: rev4 creates
    archive_pool 'to collect rerouted tokens'; all 39 reasonings read
    'reroute historic f{N} ... to archive_pool'; 39 removed live tokens ==
    live archive_pool (39). So map-less reroute holders go to archive_pool
    (must exist — else fail-closed invalid_replay)."""
    holders = [p for p in sorted(removed_places) if live.get(p, 0) > 0]
    if not holders:
        return {}
    if 'archive_pool' not in net.places:
        raise SpliceError(
            'invalid_replay',
            'reroute policy without a persisted map and no archive_pool to recover to',
        )
    return {holder: 'archive_pool' for holder in holders}


def _readd_recorded(
    net: PetriNet, live: dict[str, int], removed: dict[str, Any]
) -> tuple[PetriNet, dict[str, int]]:
    """Inverse of a recorded remove/disable (mirrors `_splice_undo` re-add)."""
    if not isinstance(removed, dict):
        raise SpliceError("invalid_replay", f"undo target has no removed structure: {removed!r}")
    mutation = {
        "add_places": [
            {"name": p["name"], "tokens": p["tokens"]} for p in removed.get("places", [])
        ],
        "add_transitions": list(removed.get("transitions", [])),
        "add_arcs": list(removed.get("arcs", [])),
    }
    places, transitions, arcs = _validate_add_mutation(mutation)
    candidate = PetriNet()
    # rebuild survivor net first (add-only model), then apply the recorded add
    for name in sorted(net.places):
        candidate.add_place(name, net.initial_marking[name])
    for name in sorted(net.transitions):
        candidate.add_transition(name)
    for trans in sorted(net.transitions):
        for place, weight in sorted(net.inputs[trans].items()):
            candidate.add_input(place, trans, weight)
        for place, weight in sorted(net.outputs[trans].items()):
            candidate.add_output(transition=trans, place=place, weight=weight)
    _apply_add(candidate, places, transitions, arcs)
    live_after = rebase_marking(live, candidate)
    for place in removed.get("places", []):
        live_after[place["name"]] = place.get("live", place["tokens"])
    return candidate, live_after


def replay_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fold ledger records into snapshots (see module doc for the contract)."""
    snaps, _ = replay_full(records)
    return snaps


def replay_full(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fold + report foreign leaked writes (see module doc).

    Revision monotonicity: every snapshot-emitting record bumps the bundle
    revision, so an emitting record with revision <= the last emitted one
    cannot belong to this bundle's chain — it is a leaked hermetic-test write
    (proven case: rev-1 cap-edge add + work_start fire sitting in the live
    store at 19:42 2026-09-05 while live was rev 45). Such records are
    SKIPPED (no state change, listed in `skipped` with ts/kind/revision for
    transparency). Soundness rests on the terminal exact-equality gate in
    `build_snapshot`: a wrongly skipped mutation breaks the fold and refuses
    the build — never silent (D16).
    """
    net: PetriNet | None = None
    live: dict[str, int] = {}
    snaps: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    structural: dict[int, dict[str, Any]] = {}
    last_rev: int | None = None

    def emit(rec: dict[str, Any], rev: int) -> None:
        assert net is not None
        snaps.append({
            "revision": rev,
            "kind": rec.get("kind", ""),
            "label": _label(rec),
            "marking": dict(live),
        })

    for rec in records:
        kind = rec.get("kind", "")
        try:
            if kind == "net_sync" and rec.get("bootstrap"):
                if net is not None:
                    raise SpliceError("invalid_replay", "second bootstrap in one store")
                net, live = _genesis()
                rev = _need_revision(rec)
                last_rev = rev
                emit(rec, rev)
                continue
            if net is None:
                raise SpliceError("invalid_replay", f"structure op before genesis: {kind}")
            _mode = rec.get("mode", "")
            if kind == "net_fire" or (
                kind in ("net_splice", "net_disable")
                and _mode in ("add", "remove", "disable", "undo")
            ):
                    # Monotonicity gate FIRST (before any state change): emitting
                    # records bump the bundle revision, so rev <= last is a foreign
                    # leaked write → skip with no state change. Soundness rests
                    # on the terminal exact-equality gate in build_snapshot —
                    # never silent (D16).
                gate_rev = _need_revision(rec)
                if last_rev is not None and gate_rev <= last_rev:
                    skipped.append(_skip_info(rec))
                    continue
                last_rev = gate_rev
            if kind == "net_splice" and rec.get("mode") == "add":
                mutation = rec.get("mutation")
                places, transitions, arcs = _validate_add_mutation(mutation)
                _apply_add(net, places, transitions, arcs)
                live = rebase_marking(live, net)
                rev = _need_revision(rec)
                structural[rev] = rec
                emit(rec, rev)
            elif (kind == "net_splice" and rec.get("mode") == "remove") or (
                kind == "net_disable"
            ):
                mutation = rec.get("mutation")
                if kind == "net_disable":
                    sub = rec.get("subnet", "")
                    if not sub:
                        raise SpliceError("invalid_replay", "net_disable without subnet")
                    from .state import _subnet_key_prefix  # noqa: PLC0415 (lazy, same package)

                    _key, prefix = _subnet_key_prefix(sub)
                    removed_places = {p for p in net.places if p.startswith(prefix)}
                    removed_transitions = {t for t in net.transitions if t.startswith(prefix)}
                    # policy is top-level on disable records (the mutation,
                    # when passed, is NOT persisted — audit gap); the map
                    # never is → archive recovery rule applies
                    policy = rec.get("token_policy", "forbid")
                    reroute: dict[str, str] = {}
                    if isinstance(mutation, dict):
                        policy = mutation.get("token_policy", policy)
                        reroute = mutation.get("reroute", {})
                    if policy == "reroute" and not reroute:
                        reroute = _archive_recovery_map(net, live, removed_places)
                else:
                    removed_places, removed_transitions, policy, reroute = (
                        _validate_remove_mutation(mutation)
                    )
                    if policy == 'reroute' and not reroute:
                        reroute = _archive_recovery_map(net, live, removed_places)
                net, live = _remove_like(
                    net, live, removed_places, removed_transitions, policy, reroute)
                rev = _need_revision(rec)
                structural[rev] = rec
                emit(rec, rev)
            elif kind == "net_splice" and rec.get("mode") == "undo":
                undoes = rec.get("undoes")
                orig = structural.get(undoes) if isinstance(undoes, int) else None
                if orig is None:
                    raise SpliceError(
                        "invalid_replay", f"undo of unknown revision: {undoes!r}")
                if orig.get("mode") == "add":
                    mutation = orig.get("mutation", {})
                    places = {p["name"] for p in mutation.get("add_places", [])}
                    transitions = {t["name"] for t in mutation.get("add_transitions", [])}
                    if not places and not transitions:
                        raise SpliceError(
                            "invalid_replay", "undo target added no nodes")
                    net, live = _remove_like(net, live, places, transitions, "forbid", {})
                else:
                    net, live = _readd_recorded(net, live, orig.get("removed", {}))
                rev = _need_revision(rec)
                structural[rev] = rec
                emit(rec, rev)
            elif kind == "net_fire":
                transition = rec.get("transition", "")
                successor = net.fire_marking(
                    tuple(live[p] for p in net.place_order), transition)
                live = dict(zip(net.place_order, successor))
                rev = _need_revision(rec)
                emit(rec, rev)
            elif (kind == "net_splice" and rec.get("mode") in SKIP_MODES) or (
                kind == "net_sync"
            ) or (kind == "net_synthesize"):
                continue  # no state mutation → no snapshot (design §1)
            else:
                raise SpliceError("invalid_replay", f"unknown ledger record: {kind}")
        except (SpliceError, TransitionNotEnabledError, UnknownTransitionError) as exc:
            if isinstance(exc, SpliceError) and exc.code == "invalid_replay":
                raise
            raise SpliceError("invalid_replay", f"replay failed on {kind}: {exc}") from exc
    return snaps, skipped


def _skip_info(rec):
    return {
        'ts': rec.get('ts', ''),
        'kind': rec.get('kind', ''),
        'mode': rec.get('mode', ''),
        'revision': rec.get('revision'),
        'reasoning': str(rec.get('reasoning', '') or '')[:80],
    }


def replay(store: Path) -> list[dict[str, Any]]:
    """Replay a ledger store directory (archives + hot)."""
    return replay_records(read_store(store))


def grid_positions(place_order: list[str]) -> dict[str, dict[str, int]]:
    """Deterministic grid layout by role (design §4 — no runtime elkjs)."""
    ordered = list(place_order)
    pools = [p for p in POOL_PLACES if p in ordered]
    resources = [p for p in RESOURCE_PLACES if p in ordered]
    boundary = [p for p in BOUNDARY_PORTS if p in ordered]
    rest = sorted(set(ordered) - set(pools) - set(resources) - set(boundary))
    positions: dict[str, dict[str, int]] = {}
    for row, names in ((0, pools), (140, resources), (280, boundary), (420, rest)):
        for i, name in enumerate(names):
            positions[name] = {"x": i * 180, "y": row}
    return positions


def transition_positions(net: PetriNet, base_y: int = 560) -> dict[str, dict[str, int]]:
    """Alphabetical transition row below the place rows (design §4)."""
    return {
        name: {"x": i * 180 + 90, "y": base_y}
        for i, name in enumerate(sorted(net.transitions))
    }


def build_snapshot(base: Path, store: Path | None = None) -> dict[str, Any]:
    """Fold the store, gate against the live bundle, emit the §2 schema."""
    from .state import _ledger_path  # noqa: PLC0415 (lazy, same package)

    st: NetState = load(base)
    ledger_dir = store if store is not None else _ledger_path().parent
    snaps, skipped = replay_full(read_store(ledger_dir))
    if (
        not snaps
        or snaps[-1]["revision"] != st.revision
        or snaps[-1]["marking"] != st.live_marking
    ):
        have_rev = snaps[-1]["revision"] if snaps else None
        raise SpliceError(
            "replay_mismatch",
            f"ledger replay (rev {have_rev}) does not reproduce live rev "
            f"{st.revision} — regenerate after sync/fire, never ship stale",
        )
    order = list(st.net.place_order)
    arcs: list[dict[str, Any]] = []
    for trans in st.net.transition_order:
        for place, weight in st.net.inputs[trans].items():
            arcs.append({"source": place, "target": trans, "weight": weight})
        for place, weight in st.net.outputs[trans].items():
            arcs.append({"source": trans, "target": place, "weight": weight})
    arcs.sort(key=lambda a: (a["source"], a["target"]))
    positions = grid_positions(order)
    positions.update(transition_positions(st.net))
    counts = pool_counts(st.live_marking)
    return {
        "format": SNAPSHOT_FORMAT,
        "version": SNAPSHOT_VERSION,
        "net_revision": st.revision,
        "built_at": _utc_now(),
        "place_order": order,
        "net": {
            "places": [
                {"name": p, "tokens": st.net.initial_marking[p]} for p in order
            ],
            "transitions": [{"name": t} for t in st.net.transition_order],
            "arcs": arcs,
        },
        "positions": positions,
        "pool": {
            "pending": counts.get("work_pending", 0),
            "active": counts.get("work_active", 0),
            "done": counts.get("work_done", 0),
        },
        "snapshots": snaps,
        "skipped": skipped,
    }
