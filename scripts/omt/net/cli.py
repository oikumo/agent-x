"""omt_net CLI — feature_039.adaptive_net_engine + feature_040.net_composition_supervisor.

Single tool, closed op enum (IDEA-002 v4 §5.0, PROJECT.md D10):

    probe|fire|invariant   feature_039 (observe / marking-only fire / drift)
    splice|sync            feature_040 (structural transactions + net↔reality)
    synthesize             reserved → clean not_implemented (feature_042)

Contract (tests/scripts/omt/test_net_{cli,splice,sync}.py ARE the spec): one
JSON envelope on stdout, exit 0 ok / 1 error; bootstrap ordering §5.1 —
probe/fire/invariant fail clean with net_not_bootstrapped until the bundle
exists (sync is the first-call entry point). `fire` is marking-only (no
conformance regression, §5.0 matrix); splice (all modes) + sync bootstrap run
the 9-vector conformance gate pre-save; proposal-only sync stays read-only
(D4 — the agent applies proposals via splice). `invariant` folds the old
`drift` op — net-vs-ledger revision drift is surfaced (exit stays 0) and
logged to harness.net.drift.jsonl (D7).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import state
from .analysis import PetriNetAnalyzer
from .errors import (
    PetriNetError,
    TransitionNotEnabledError,
    UnknownTransitionError,
)

RESERVED_OPS = ("synthesize",)
# TA: xref: feature_041 (pause_2026-08-30d.md R4): _invariant envelope gains ADDITIVE resources[] (per catalog place: capacity/live/capacity_ok/holders — holders for agent_attention = subnets with f{N}_active marked) + conflicts[] (pending subnets whose f{N}_start is not enabled, blocked_by = empty unprefixed input places) via state.resource_report(st) — the D7 omt_complete exit hook then surfaces capacity conflicts mechanically; additive keys only (test_net_cli.py exact-shape risk), RESERVED_OPS stays ("synthesize",) → feature_042.
# TA: xref: feature_040 (pause_2026-08-30c.md): splice args --mode add|remove|disable|undo|repair --mutation '<json>' --subnet --reasoning; sync bootstraps supervisor skeleton (feature_ready=1, resource_token=1, goal_satisfied=0, NO supervisor transitions v1) then emits PROPOSAL only (D4 — agent applies via splice); RESERVED_OPS shrinks to ("synthesize",) → feature_042.
DEFAULT_MAX_STATES = 1000


def _emit(envelope: dict[str, Any], code: int) -> int:
    print(json.dumps(envelope, ensure_ascii=False))
    return code


def _error(code_str: str, op: str, message: str = "") -> tuple[dict[str, Any], int]:
    envelope: dict[str, Any] = {"ok": False, "error": code_str, "op": op}
    if message:
        envelope["message"] = message
    return envelope, 1


def _probe(base: Path, max_states: int) -> tuple[dict[str, Any], int]:
    st = state.load(base)
    analyzer = PetriNetAnalyzer(st.net)
    live_tuple = tuple(st.live_marking[p] for p in st.net.place_order)
    deadlocks = analyzer.deadlocks(max_states=max_states)
    bounds = analyzer.bounds(max_states=max_states)
    envelope = {
        "ok": True,
        "op": "probe",
        "revision": st.revision,
        "marking": st.live_marking,
        "enabled": st.net.enabled_transitions_at(live_tuple),
        "advice": {
            "deadlocks": [list(m) for m in deadlocks.deadlocks],
            "deadlocks_complete": deadlocks.complete,
            "bounded": bounds.bounded,
            "bounds": bounds.bounds,
            "place_invariants": [list(v) for v in analyzer.place_invariants()],
            "transition_invariants": [
                list(v) for v in analyzer.transition_invariants()
            ],
            "max_states": max_states,
        },
    }
    return envelope, 0


def _fire(base: Path, transition: str, reasoning: str, session: str) -> tuple[dict[str, Any], int]:
    st = state.fire(base, transition, reasoning=reasoning, session=session)
    envelope = {
        "ok": True,
        "op": "fire",
        "revision": st.revision,
        "marking": st.live_marking,
    }
    return envelope, 0


def _splice(base: Path, args: argparse.Namespace, mutation: Any) -> tuple[dict[str, Any], int]:
    st, info = state.splice(
        base,
        args.mode,
        mutation=mutation,
        subnet=args.subnet,
        reasoning=args.reasoning,
        session=args.session,
        feature=args.feature,
    )
    envelope = {
        "ok": True,
        "op": "splice",
        "mode": args.mode,
        "revision": st.revision,
        "marking": st.live_marking,
        **info,
    }
    return envelope, 0


def _sync(base: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    st, info = state.sync(base, reasoning=args.reasoning, session=args.session)
    envelope: dict[str, Any] = {
        "ok": True,
        "op": "sync",
        "bootstrap": info["bootstrap"],
        "revision": st.revision,
        "proposal": info["proposal"],
    }
    if info.get("conformance") is not None:
        envelope["conformance"] = info["conformance"]
    return envelope, 0


def _invariant(base: Path) -> tuple[dict[str, Any], int]:
    st = state.load(base)
    analyzer = PetriNetAnalyzer(st.net)
    place_invariants = analyzer.place_invariants()
    live_tuple = tuple(st.live_marking[p] for p in st.net.place_order)
    initial = st.net.initial_marking_tuple()
    hold = all(
        sum(y[i] * live_tuple[i] for i in range(len(y)))
        == sum(y[i] * initial[i] for i in range(len(y)))
        for y in place_invariants
    )
    records = state.read_ledger_net_records()
    ledger_revision = records[-1].get("revision", 0) if records else 0
    drifted = st.revision != ledger_revision
    drift = {
        "drifted": drifted,
        "net_revision": st.revision,
        "ledger_revision": ledger_revision,
    }
    if drifted:
        state.append_drift(base, {
            "op": "invariant",
            "net_revision": st.revision,
            "ledger_revision": ledger_revision,
        })
    envelope = {
        "ok": True,
        "op": "invariant",
        "place_invariants": [list(v) for v in place_invariants],
        "transition_invariants": [
            list(v) for v in analyzer.transition_invariants()
        ],
        "live_marking_invariants_hold": hold,
        "drift": drift,
    }
    return envelope, 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omt_net",
        description="Meta-harness concurrency net (IDEA-002 v4 §5.0 closed op enum).",
    )
    sub = parser.add_subparsers(dest="op", required=True)

    p_probe = sub.add_parser("probe", help="Observe marking + enabled + analyzer advice.")
    p_probe.add_argument("--max-states", type=int, default=DEFAULT_MAX_STATES)

    p_fire = sub.add_parser("fire", help="Fire an enabled transition (marking-only).")
    p_fire.add_argument("--transition", required=True)
    p_fire.add_argument("--reasoning", required=True)
    p_fire.add_argument("--session", default="")

    p_splice = sub.add_parser(
        "splice", help="Atomic structural transaction (conformance-gated, §3)."
    )
    p_splice.add_argument(
        "--mode", required=True, choices=["add", "remove", "disable", "undo", "repair"]
    )
    p_splice.add_argument("--mutation", default="", help="JSON mutation object.")
    p_splice.add_argument("--subnet", default="", help="Subnet key (disable mode).")
    p_splice.add_argument("--reasoning", required=True)
    p_splice.add_argument("--session", default="")
    p_splice.add_argument("--feature", default="")

    p_sync = sub.add_parser(
        "sync", help="net↔reality bootstrap + resync (proposal-only, D4)."
    )
    p_sync.add_argument("--reasoning", default="")
    p_sync.add_argument("--session", default="")

    sub.add_parser("invariant", help="Invariants + net-vs-ledger drift (D7).")

    for op in RESERVED_OPS:
        sub.add_parser(op, help="Reserved — feature_042+.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    op: str = args.op

    if op in RESERVED_OPS:
        return _emit(*_error(
            "not_implemented",
            op,
            f"omt_net{{op:{op}}} is reserved for feature_042 "
            "(goal_net_synthesis) — IDEA-002 v4 §5.0",
        ))

    base = state.net_dir()
    try:
        if op == "probe":
            return _emit(*_probe(base, args.max_states))
        if op == "fire":
            return _emit(*_fire(base, args.transition, args.reasoning, args.session))
        if op == "splice":
            mutation = None
            if args.mutation:
                try:
                    mutation = json.loads(args.mutation)
                except json.JSONDecodeError as exc:
                    return _emit(*_error(
                        "invalid_mutation", op, f"--mutation is not valid JSON: {exc}"
                    ))
            return _emit(*_splice(base, args, mutation))
        if op == "sync":
            return _emit(*_sync(base, args))
        if op == "invariant":
            return _emit(*_invariant(base))
    except state.SpliceError as exc:
        return _emit(*_error(exc.code, op, str(exc)))
    except state.NetNotBootstrappedError as exc:
        return _emit(*_error("net_not_bootstrapped", op, str(exc)))
    except state.RevisionMismatchError as exc:
        return _emit(*_error("revision_mismatch", op, str(exc)))
    except TransitionNotEnabledError:
        return _emit(*_error("transition_not_enabled", op))
    except UnknownTransitionError:
        return _emit(*_error("unknown_transition", op))
    except PetriNetError as exc:
        return _emit(*_error("petri_net_error", op, str(exc)))
    raise AssertionError(f"unreachable op dispatch: {op}")


if __name__ == "__main__":
    sys.exit(main())
