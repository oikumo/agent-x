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
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Tests redirect the ledger/snapshot dir to a temp path via these env vars so
# they NEVER wipe the real .meta/.omt/ledger.jsonl (clear_ledger is destructive).
_LEDGER_ENV = os.environ.get("OMT_LEDGER_PATH")
LEDGER_PATH = Path(_LEDGER_ENV) if _LEDGER_ENV else REPO_ROOT / ".meta" / ".omt" / "ledger.jsonl"
_SNAPSHOT_ENV = os.environ.get("OMT_SNAPSHOT_DIR")
SNAPSHOT_DIR = Path(_SNAPSHOT_ENV) if _SNAPSHOT_ENV else REPO_ROOT / ".meta" / ".omt" / "tdd_snapshots"
UNLOCK_WINDOW_MS = 8 * 60 * 60 * 1000  # 8 hours (keep in sync with .opencode/lib/omt_shared.ts — single TS source since meta_harness_dsl R1; pinned by tests/scripts/omt/test_thought_pattern_pin.py)

# Two-hats gate rules: {state: {src: bool, tests: bool}}
HAT_RULES: dict[str, dict[str, bool]] = {
    "testlist": {"src": False, "tests": False},
    "red": {"src": False, "tests": True},      # test hat
    "green": {"src": True, "tests": False},     # code hat
    "refactor": {"src": True, "tests": False},  # refactor hat
    "done": {"src": False, "tests": False},
    "none": {"src": True, "tests": True},       # TDD not active
}

# Built-in / common names to exclude from "missing references" check.
_BUILTINS = frozenset(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__)) | frozenset({
    "self", "cls", "True", "False", "None", "len", "str", "int", "list", "dict",
    "set", "tuple", "bool", "float", "type", "isinstance", "issubclass", "print",
    "range", "enumerate", "zip", "sorted", "reversed", "open", "Path", "pytest",
    "monkeypatch", "fixture", "mark", "parametrize", "skip", "xfail", "raises",
    "warns", "approx", "tmp_path", "capsys", "capfd", "caplog", "tmpdir",
    "MagicMock", "patch", "mock", "AsyncMock", "Any", "Optional", "Union",
    "dataclass", "field", "ABC", "abstractmethod", "property",
})


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_ledger() -> list[dict]:
    if not LEDGER_PATH.exists():
        return []
    records: list[dict] = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if not s:
            continue
        try:
            records.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return records


def write_ledger(record: dict) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now_iso(), **record}) + "\n")


def _within_window(record: dict, now_ms: float) -> bool:
    ts = record.get("ts", "")
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000
        return now_ms - t < UNLOCK_WINDOW_MS
    except (ValueError, OSError):
        return False


def get_session_records(session: str) -> list[dict]:
    """Get phase/skip/tdd/tdd_testlist records for this session."""
    records = read_ledger()
    relevant = [r for r in records
                if r.get("kind") in ("phase", "skip", "tdd", "tdd_testlist", "complete")]
    if not relevant:
        return []
    if session:
        mine = [r for r in relevant if r.get("session") == session]
        if mine:
            return mine
    now_ms = time.time() * 1000
    return [r for r in relevant if _within_window(r, now_ms)]


def get_tdd_mode(session: str) -> bool:
    """Check if TDD mode is active from the latest phase record."""
    records = get_session_records(session)
    phase_recs = [r for r in records if r.get("kind") == "phase"]
    if not phase_recs:
        return False
    return bool(phase_recs[-1].get("tdd_mode", False))


def get_tdd_state(session: str) -> str:
    """Current TDD state: testlist/red/green/refactor/done/none."""
    if not get_tdd_mode(session):
        return "none"
    records = get_session_records(session)
    tdd_recs = [r for r in records if r.get("kind") in ("tdd", "tdd_testlist")]
    if not tdd_recs:
        return "testlist"  # TDD active but no cycle started
    latest = tdd_recs[-1]
    if latest.get("kind") == "tdd_testlist":
        return "testlist"
    return latest.get("state", "none")


def get_current_test_node(session: str) -> str | None:
    records = get_session_records(session)
    tdd_recs = [r for r in records if r.get("kind") == "tdd"]
    if not tdd_recs:
        return None
    return tdd_recs[-1].get("test_node")


def get_tdd_cycles(feature: str) -> list[dict]:
    records = read_ledger()
    return [r for r in records if r.get("kind") == "tdd" and r.get("feature") == feature]


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _parse_file(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return None


def infer_target_src(test_file: Path) -> list[str]:
    """Parse test file imports → source file paths under src/."""
    tree = _parse_file(test_file)
    if not tree:
        return []
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("agentx"):
                p = "src/" + node.module.replace(".", "/") + ".py"
                if p not in targets:
                    targets.append(p)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("agentx"):
                    p = "src/" + alias.name.replace(".", "/") + ".py"
                    if p not in targets:
                        targets.append(p)
    return targets


def extract_test_references(test_file: Path, test_name: str) -> set[str]:
    """Find all method calls (ast.Call with ast.Attribute func) in a test function."""
    tree = _parse_file(test_file)
    if not tree:
        return set()
    refs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == test_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    refs.add(child.func.attr)
    return refs


def extract_defined_names(src_file: Path) -> set[str]:
    """Find all class names and public method/function names in source."""
    tree = _parse_file(src_file)
    if not tree:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_"):
                        names.add(item.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
    return names


def extract_public_methods(src_file: Path) -> list[dict]:
    """Extract public methods from a source file (module-level + class methods)."""
    tree = _parse_file(src_file)
    if not tree:
        return []
    methods: list[dict] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("_"):
                        continue
                    is_abstract = any(
                        "abstractmethod" in ast.unparse(d) for d in item.decorator_list
                    )
                    methods.append({
                        "class": node.name, "method": item.name,
                        "line": item.lineno, "is_abstract": is_abstract,
                    })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                methods.append({
                    "class": "", "method": node.name,
                    "line": node.lineno, "is_abstract": False,
                })
    return methods


def find_untested_methods(src_file: Path, test_files: list[Path]) -> list[dict]:
    """Find public methods not referenced by any test file."""
    src_methods = extract_public_methods(src_file)
    if not src_methods:
        return []
    tested_names: set[str] = set()
    for tf in test_files:
        tree = _parse_file(tf)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                tested_names.add(node.attr)
    return [m for m in src_methods if m["method"] not in tested_names]


def verify_true_red(test_file: Path, test_name: str, src_files: list[Path]) -> dict:
    """Check if test references code that doesn't exist in source yet."""
    test_refs = extract_test_references(test_file, test_name)
    all_defined: set[str] = set()
    for sf in src_files:
        all_defined |= extract_defined_names(sf)
    missing = sorted(r for r in test_refs if r not in all_defined and r not in _BUILTINS)
    return {"is_true_red": len(missing) > 0, "missing": missing}


def extract_test_summary(test_file: Path, test_name: str) -> dict:
    """Extract assertions and method calls from a test function."""
    tree = _parse_file(test_file)
    if not tree:
        return {"assertions": [], "calls": []}
    assertions: list[dict] = []
    calls: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == test_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    try:
                        assertions.append({"line": child.lineno, "test": ast.unparse(child.test)})
                    except Exception:
                        assertions.append({"line": child.lineno, "test": "<unparseable>"})
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    try:
                        calls.append({"line": child.lineno, "call": ast.unparse(child.func)})
                    except Exception:
                        pass
    return {"assertions": assertions, "calls": calls}


def detect_red_anti_patterns(test_file: Path) -> list[str]:
    """Detect anti-patterns in a test file during RED state."""
    warnings: list[str] = []
    tree = _parse_file(test_file)
    if not tree:
        return warnings
    test_fns = [n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    if len(test_fns) > 1:
        warnings.append(
            f"batch-N-tests: {len(test_fns)} test functions in file. "
            f"TDD requires 1 test:1 min impl loop. (spec anti-pattern)"
        )
    for fn in test_fns:
        has_assert = any(isinstance(c, ast.Assert) for c in ast.walk(fn))
        if not has_assert:
            for c in ast.walk(fn):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute):
                    if c.func.attr.startswith("assert"):
                        has_assert = True
                        break
        if not has_assert:
            warnings.append(f"test '{fn.name}' has no assertions.")
        parts = fn.name.split("_")
        if len(parts) < 3:
            warnings.append(
                f"test '{fn.name}' doesn't follow test_<subject>_<behavior> naming."
            )
        for dec in fn.decorator_list:
            try:
                dec_str = ast.unparse(dec)
            except Exception:
                dec_str = ""
            if "skip" in dec_str or "xfail" in dec_str:
                warnings.append(
                    f"test '{fn.name}' has skip/xfail — forbidden. (spec anti-pattern)"
                )
    return warnings


# ---------------------------------------------------------------------------
# Snapshot management
# ---------------------------------------------------------------------------

def snapshot_source(src_file: Path) -> dict:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    methods = extract_public_methods(src_file)
    snapshot = {"file": str(src_file), "methods": methods, "ts": _now_iso()}
    (SNAPSHOT_DIR / f"{src_file.stem}.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )
    return snapshot


def load_snapshot(src_file: Path) -> dict | None:
    p = SNAPSHOT_DIR / f"{src_file.stem}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def diff_snapshots(before: dict | None, after: dict | None) -> list[dict]:
    if not before:
        return after.get("methods", []) if after else []
    before_set = {(m["class"], m["method"]) for m in before.get("methods", [])}
    after_methods = after.get("methods", []) if after else []
    return [m for m in after_methods if (m["class"], m["method"]) not in before_set]


# ---------------------------------------------------------------------------
# Pytest runner
# ---------------------------------------------------------------------------

def run_pytest(test_node: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_node, "-x", "-q", "--no-header", "--tb=short"],
            capture_output=True, text=True, timeout=timeout, cwd=str(REPO_ROOT),
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"pytest timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def run_full_suite(timeout: int = 120) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "--tb=short"],
            capture_output=True, text=True, timeout=timeout, cwd=str(REPO_ROOT),
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"pytest timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


# ---------------------------------------------------------------------------
# Subcommand implementations
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


def _resolve_test_path(test_node: str) -> Path:
    test_file = test_node.split("::")[0]
    p = Path(test_file)
    if not p.is_absolute():
        p = REPO_ROOT / test_file
    return p


def _resolve_src_path(target: str) -> Path:
    p = Path(target)
    if not p.is_absolute():
        p = REPO_ROOT / target
    return p


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


def cmd_done(args) -> dict:
    exit_code, _stdout, stderr = run_full_suite(timeout=120)
    suite_clean = exit_code == 0

    cycles = get_tdd_cycles(args.feature)
    refactor_recorded = all(
        c.get("state") in ("green", "refactor", "done") for c in cycles
    ) if cycles else True

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
        return {
            "ok": True, "checklist": checklist, "coverage_gaps": [],
            "message": "✅ DONE — all checklist items verified.\n"
                       "  Phase exit approved. Call omt_complete to advance to Testing.",
        }
    lines = ["⛔ DONE checklist incomplete:"]
    if not suite_clean:
        lines.append(f"  ❌ Full suite has failures (exit {exit_code})")
    if not refactor_recorded:
        lines.append("  ❌ Refactor not recorded for some cycles")
    if not naming_ok:
        lines.append("  ❌ Some tests don't follow test_<subject>_<behavior> naming")
    return {"ok": False, "checklist": checklist, "coverage_gaps": [], "message": "\n".join(lines)}


def cmd_gate(args) -> dict:
    state = get_tdd_state(args.session)
    is_tests = args.is_tests or args.path.startswith("tests/")
    rules = HAT_RULES.get(state, HAT_RULES["none"])
    allowed = rules["tests"] if is_tests else rules["src"]
    if not allowed:
        hat = {"red": "test", "green": "code", "refactor": "refactor",
               "testlist": "planning", "done": "complete"}.get(state, "")
        which = "Only tests/ edits allowed." if hat == "test" else "Only src/ edits allowed."
        return {
            "allowed": False,
            "reason": f"⛔ TDD two-hats: wearing the {hat} hat. {which} "
                      f"(spec: two_hats_never_same_time)",
            "state": state, "tdd_mode": state != "none",
        }
    return {"allowed": True, "reason": "", "state": state, "tdd_mode": state != "none"}


def cmd_after_edit(args) -> dict:
    state = get_tdd_state(args.session)

    if state == "refactor":
        test_node = get_current_test_node(args.session)
        if test_node:
            exit_code, _stdout, stderr = run_pytest(test_node, timeout=30)
            if exit_code != 0:
                return {
                    "action": "revert_needed",
                    "reason": ("⛔ REFACTOR broke tests. Reverting to last GREEN state. "
                               "(spec: REFACTOR breaks suite -> git checkout -- f)"),
                }
        return {"action": "ok"}

    if state == "green":
        src_path = _resolve_src_path(args.path)
        if src_path.exists() and src_path.suffix == ".py":
            prev = load_snapshot(src_path)
            current = snapshot_source(src_path)
            new_methods = diff_snapshots(prev, current)
            if new_methods:
                test_node = get_current_test_node(args.session)
                test_refs: set[str] = set()
                if test_node:
                    tp = _resolve_test_path(test_node)
                    tn = test_node.split("::")[-1]
                    if tp.exists():
                        test_refs = extract_test_references(tp, tn)
                untested_new = [m for m in new_methods if m["method"] not in test_refs]
                if untested_new:
                    names = [f"{m['class']}.{m['method']}" if m["class"] else m["method"]
                             for m in untested_new]
                    return {
                        "action": "warning",
                        "advisories": [
                            f"⚠️ TDD law 3: new method(s) {names} not referenced by "
                            f"the current test. Write no more code than sufficient to pass."
                        ],
                    }
        return {"action": "ok"}

    return {"action": "ok"}


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


def cmd_validate_exit(args) -> dict:
    feature = args.feature
    cycles = get_tdd_cycles(feature)
    dangling: list[str] = []
    for i, c in enumerate(cycles):
        if c.get("state") == "red" and c.get("verified"):
            found_green = any(
                c2.get("state") == "green"
                and c2.get("test_node") == c.get("test_node")
                for c2 in cycles[i + 1:]
            )
            if not found_green:
                dangling.append(c.get("test_node", "?"))

    test_dir = REPO_ROOT / "tests" / "features" / feature
    test_files = list(test_dir.rglob("test_*.py")) if test_dir.exists() else []
    all_targets: set[str] = set()
    for tf in test_files:
        all_targets.update(infer_target_src(tf))

    coverage_gaps: list[dict] = []
    for target in all_targets:
        src_path = _resolve_src_path(target)
        if src_path.exists():
            untested = find_untested_methods(src_path, test_files)
            if untested:
                coverage_gaps.append({"file": target, "untested": untested})

    all_ok = len(dangling) == 0 and len(coverage_gaps) == 0
    return {
        "ok": all_ok, "dangling_reds": dangling, "coverage_gaps": coverage_gaps,
        "summary": {
            "test_files": len(test_files), "src_files": len(all_targets),
            "untested_methods": sum(len(g["untested"]) for g in coverage_gaps),
        },
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
