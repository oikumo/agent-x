#!/usr/bin/env python3
"""TDD enforcement engine — Kent Beck TDD spec implementation.

Follows the mvc_check.py pattern: stdlib-only Python script that does analysis
and returns JSON, called by the TypeScript enforcer plugin via:
    $`uv run scripts/omt/tdd_check.py <subcommand> ...`

Spec: .meta/doc/tdd/tdd-agent-spec.md (Kent Beck TDD v5)

Subcommands:
    testlist        Record behaviors to implement
    start           TDD Red: verify test fails
    green           TDD Green: verify test passes
    refactor        TDD Refactor: verify tests stay green
    done            TDD Done: full checklist verification
    gate            Check if a file edit is allowed (two-hats principle)
    after-edit      Post-edit advisory / revert check
    status          Current TDD state + cycle history
    validate-exit   Phase exit validation (coverage gaps, dangling reds)

meta_harness_dsl R3: the implementation is split across this package
(state / ast_checks / gates / cli); scripts/omt/tdd_check.py remains as a
thin compat shim — every call site keeps working unchanged.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys

from .ast_checks import (
    _parse_file,
    detect_red_anti_patterns,
    extract_test_summary,
    infer_target_src,
    verify_true_red,
)
from .gates import cmd_after_edit, cmd_gate, cmd_validate_exit
from .state import (
    KNOWN_SUITE_FAILURES,
    REPO_ROOT,
    SNAPSHOT_DIR,
    _resolve_src_path,
    _resolve_test_path,
    get_current_test_node,
    get_session_records,
    get_tdd_cycles,
    get_tdd_mode,
    get_tdd_state,
    run_full_suite,
    run_pytest,
    snapshot_source,
    suite_failures,
    write_ledger,
)


# ---------------------------------------------------------------------------
# Subcommand implementations (cycle verbs; gate verbs live in gates.py)
# ---------------------------------------------------------------------------

def cmd_testlist(args) -> dict:
    behaviors = json.loads(args.behaviors) if args.behaviors else []
    write_ledger({
        "kind": "tdd_testlist", "session": args.session,
        "behaviors": behaviors, "remaining": behaviors, "feature": args.feature,
    })
    return {
        "ok": True, "state": "testlist",
        "behaviors_count": len(behaviors),
        "message": (f"✅ Test list recorded ({len(behaviors)} behaviors). State=TESTLIST.\n"
                    f"Write a test for the first behavior, then:\n"
                    f"  omt_red{{test_node: \"...\"}}"),
    }


def cmd_start(args) -> dict:
    test_node = args.test_node
    test_name = test_node.split("::")[-1]
    test_path = _resolve_test_path(test_node)

    # Infer target source
    targets: list[str] = []
    if args.target_src:
        targets = [args.target_src]
    elif test_path.exists():
        targets = infer_target_src(test_path)

    # Run pytest
    exit_code, _stdout, stderr = run_pytest(test_node, timeout=30)

    if exit_code == 0:
        write_ledger({
            "kind": "tdd", "session": args.session, "state": "red",
            "test_node": test_node, "target_src": targets,
            "verified": False, "exit_code": exit_code, "feature": args.feature,
        })
        return {
            "ok": False, "state": "red", "verified": False, "exit_code": exit_code,
            "message": (f"⚠️ Test '{test_node}' already passes. "
                        f"Fix the test to fail, or remove this cycle."),
        }

    if exit_code in (2, 3, 4):
        return {
            "ok": False, "state": "red", "verified": False, "exit_code": exit_code,
            "message": f"❌ pytest error (exit {exit_code}). Check the test node ID.\n{stderr[:500]}",
        }

    # RED verified (exit 1 = fail, exit 5 = no tests collected, -1 = timeout)
    true_red = None
    test_summary = None
    warnings: list[str] = []

    if test_path.exists():
        src_paths = [_resolve_src_path(t) for t in targets if _resolve_src_path(t).exists()]
        if src_paths:
            true_red = verify_true_red(test_path, test_name, src_paths)
        test_summary = extract_test_summary(test_path, test_name)
        warnings = detect_red_anti_patterns(test_path)

    write_ledger({
        "kind": "tdd", "session": args.session, "state": "red",
        "test_node": test_node, "target_src": targets,
        "verified": True, "exit_code": exit_code, "feature": args.feature,
    })

    lines = [f"✅ RED — test '{test_node}' fails (exit {exit_code})."]
    if true_red and true_red["is_true_red"]:
        lines.append(f"  TRUE RED — references missing: {true_red['missing']}")
    elif true_red and not true_red["is_true_red"]:
        lines.append("  Test references existing code — likely a bug fix (valid RED).")
    if targets:
        lines.append(f"  Inferred targets: {', '.join(targets)}")
    if test_summary and test_summary["assertions"]:
        lines.append("  Test checks:")
        for a in test_summary["assertions"]:
            lines.append(f"    {a['line']}: {a['test']}")
    if warnings:
        lines.append("  ⚠️ Warnings:")
        for w in warnings:
            lines.append(f"    {w}")
    lines.append("  src/ BLOCKED (test hat). Call omt_green when ready to write code.")

    return {
        "ok": True, "state": "red", "verified": True, "exit_code": exit_code,
        "is_true_red": true_red["is_true_red"] if true_red else None,
        "missing": true_red["missing"] if true_red else [],
        "test_summary": test_summary, "warnings": warnings,
        "message": "\n".join(lines),
    }


def cmd_green(args) -> dict:
    test_node = args.test_node
    exit_code, _stdout, stderr = run_pytest(test_node, timeout=30)

    if exit_code != 0:
        details = "\n".join(stderr.strip().split("\n")[-10:]) if stderr else ""
        return {
            "ok": False, "state": "green", "verified": False, "exit_code": exit_code,
            "message": (f"⛔ Test still fails (exit {exit_code}). "
                        f"Write more production code (L3: min-to-pass).\n{details}"),
        }

    # Save source snapshot
    test_path = _resolve_test_path(test_node)
    targets = infer_target_src(test_path) if test_path.exists() else []
    snapshots: list[str] = []
    for t in targets:
        src_path = _resolve_src_path(t)
        if src_path.exists():
            snapshot_source(src_path)
            snapshots.append(t)

    write_ledger({
        "kind": "tdd", "session": args.session, "state": "green",
        "test_node": test_node, "verified": True, "exit_code": exit_code,
        "feature": args.feature,
    })

    return {
        "ok": True, "state": "green", "verified": True, "exit_code": exit_code,
        "snapshots": snapshots,
        "message": (f"✅ GREEN — test '{test_node}' passes. Source snapshot saved.\n"
                    f"  src/ ALLOWED (code hat), tests/ BLOCKED.\n"
                    f"  Next: omt_refactor{{...}} or omt_red{{...}} for next behavior."),
    }


def cmd_refactor(args) -> dict:
    test_node = args.test_node
    exit_code, _stdout, stderr = run_pytest(test_node, timeout=30)

    if exit_code != 0:
        return {
            "ok": False, "state": "refactor", "verified": False, "exit_code": exit_code,
            "message": "⛔ Tests are failing. Fix before refactoring "
                       "(spec: courage_enabled_by_safety_net).",
        }

    write_ledger({
        "kind": "tdd", "session": args.session, "state": "refactor",
        "test_node": test_node, "verified": True, "exit_code": exit_code,
        "feature": args.feature,
    })

    return {
        "ok": True, "state": "refactor", "verified": True, "exit_code": exit_code,
        "message": (f"✅ REFACTOR — tests green. src/ unlocked for refactoring.\n"
                    f"  Each src/ edit will be verified: tests must stay green or edit is reverted.\n"
                    f"  Call omt_green{{...}} when done, or omt_red{{...}} for next behavior."),
    }


def cycles_refactor_recorded(cycles: list[dict]) -> bool:
    """Latest record per test_node decides: the ledger is append-only, so a
    cycle's red is superseded only by a green/refactor at the SAME node. A
    lingering latest=red means an unfinished cycle and blocks omt_done.
    (R4 follow-up, feature_024: the previous all-records check could never
    pass for honest red-first TDD within one ledger window — historical reds
    never leave the scanned window.)"""
    if not cycles:
        return True
    latest_by_node: dict[str, dict] = {}
    for c in cycles:
        latest_by_node[c.get("test_node") or ""] = c
    return all(c.get("state") in ("green", "refactor", "done")
               for c in latest_by_node.values())


def cmd_done(args) -> dict:
    exit_code, stdout, stderr = run_full_suite(timeout=120)
    failures = suite_failures(stdout)
    unexpected = [f for f in failures if f not in KNOWN_SUITE_FAILURES]
    allowlisted = [f for f in failures if f in KNOWN_SUITE_FAILURES]
    # R4 (audit F6/F7): the suite counts as clean when every failure is a
    # known, pre-existing one (feature_018 react_screen trio + the
    # window-flaky gate probe that reads the real 8 h ledger). A failure
    # OUTSIDE the allowlist — or a non-test failure (collection error,
    # timeout: no FAILED lines to parse) — still blocks.
    suite_clean = exit_code == 0 or (bool(failures) and not unexpected)

    cycles = get_tdd_cycles(args.feature)
    refactor_recorded = cycles_refactor_recorded(cycles)

    # Naming check
    test_dir = REPO_ROOT / "tests" / "features" / args.feature
    test_files = list(test_dir.rglob("test_*.py")) if test_dir.exists() else []
    naming_ok = True
    for tf in test_files:
        tree = _parse_file(tf)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                if len(node.name.split("_")) < 3:
                    naming_ok = False

    checklist = {
        "suite_passes": suite_clean,
        "refactor_recorded": refactor_recorded,
        "naming_ok": naming_ok,
    }

    write_ledger({
        "kind": "tdd", "session": args.session, "state": "done",
        "feature": args.feature, "checklist": checklist,
    })

    all_ok = suite_clean and refactor_recorded and naming_ok

    # Clean up TDD snapshots for this feature's source files
    if all_ok:
        try:
            test_dir = REPO_ROOT / "tests" / "features" / args.feature
            test_files = list(test_dir.rglob("test_*.py")) if test_dir.exists() else []
            all_targets: set[str] = set()
            for tf in test_files:
                all_targets.update(infer_target_src(tf))
            for target in all_targets:
                src_path = _resolve_src_path(target)
                if src_path.exists():
                    snap_file = SNAPSHOT_DIR / f"{src_path.stem}.json"
                    if snap_file.exists():
                        snap_file.unlink()
        except Exception:
            pass  # cleanup is best-effort
    if all_ok:
        note = (f"  ({len(allowlisted)} known pre-existing failure(s) tolerated — "
                f"KNOWN_SUITE_FAILURES in scripts/omt/tdd/state.py)\n") if allowlisted else ""
        return {
            "ok": True, "checklist": checklist, "coverage_gaps": [],
            "allowlisted_failures": allowlisted,
            "message": "✅ DONE — all checklist items verified.\n" + note +
                       "  Phase exit approved. Call omt_complete to advance to Testing.",
        }
    lines = ["⛔ DONE checklist incomplete:"]
    if not suite_clean:
        lines.append(f"  ❌ Full suite has failures (exit {exit_code})")
        for f in unexpected[:10]:
            lines.append(f"     - {f}")
    if not refactor_recorded:
        lines.append("  ❌ Refactor not recorded for some cycles")
    if not naming_ok:
        lines.append("  ❌ Some tests don't follow test_<subject>_<behavior> naming")
    return {"ok": False, "checklist": checklist, "coverage_gaps": [], "message": "\n".join(lines)}


def cmd_status(args) -> dict:
    session = args.session
    tdd_mode = get_tdd_mode(session)
    state = get_tdd_state(session) if tdd_mode else "none"
    test_node = get_current_test_node(session) if tdd_mode else None
    records = get_session_records(session)
    cycles = [r for r in records if r.get("kind") == "tdd"]
    testlists = [r for r in records if r.get("kind") == "tdd_testlist"]
    return {
        "tdd_mode": tdd_mode, "state": state, "test_node": test_node,
        "cycles_count": len(cycles),
        "testlist": testlists[-1] if testlists else None,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TDD enforcement engine")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("testlist")
    p.add_argument("--behaviors", default="[]")
    p.add_argument("--feature", required=True)
    p.add_argument("--session", default="")

    p = sub.add_parser("start")
    p.add_argument("--test-node", required=True)
    p.add_argument("--target-src", default="")
    p.add_argument("--feature", default="")
    p.add_argument("--session", default="")

    p = sub.add_parser("green")
    p.add_argument("--test-node", required=True)
    p.add_argument("--feature", default="")
    p.add_argument("--session", default="")

    p = sub.add_parser("refactor")
    p.add_argument("--test-node", required=True)
    p.add_argument("--feature", default="")
    p.add_argument("--session", default="")

    p = sub.add_parser("done")
    p.add_argument("--feature", required=True)
    p.add_argument("--session", default="")

    p = sub.add_parser("gate")
    p.add_argument("--path", required=True)
    p.add_argument("--session", default="")
    p.add_argument("--is-tests", action="store_true")

    p = sub.add_parser("after-edit")
    p.add_argument("--path", required=True)
    p.add_argument("--session", default="")

    p = sub.add_parser("status")
    p.add_argument("--session", default="")

    p = sub.add_parser("validate-exit")
    p.add_argument("--feature", required=True)

    args = parser.parse_args(argv)

    commands = {
        "testlist": cmd_testlist, "start": cmd_start, "green": cmd_green,
        "refactor": cmd_refactor, "done": cmd_done, "gate": cmd_gate,
        "after-edit": cmd_after_edit, "status": cmd_status,
        "validate-exit": cmd_validate_exit,
    }
    handler = commands.get(args.command)
    if not handler:
        print(json.dumps({"ok": False, "error": f"unknown command: {args.command}"}))
        return 1

    try:
        result = handler(args)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("ok", True) else 1
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
