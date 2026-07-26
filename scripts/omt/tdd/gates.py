"""TDD gates (meta_harness_dsl R3) — two-hats + validate-exit.

Extracted from the former monolithic scripts/omt/tdd_check.py:
  - HAT_RULES:     the two-hats edit matrix (spec: two_hats_never_same_time)
  - gate:          is this edit allowed in the current TDD state?
  - after-edit:    post-edit advisory / refactor revert check
  - validate-exit: phase-exit validation (dangling reds, coverage gaps)
"""
from __future__ import annotations

from .ast_checks import (
    extract_test_references,
    find_untested_methods,
    infer_target_src,
)
from .state import (
    REPO_ROOT,
    _resolve_src_path,
    _resolve_test_path,
    diff_snapshots,
    get_current_test_node,
    get_tdd_cycles,
    get_tdd_state,
    load_snapshot,
    run_pytest,
    snapshot_source,
)

# Two-hats gate rules: {state: {src: bool, tests: bool}}
HAT_RULES: dict[str, dict[str, bool]] = {
    "testlist": {"src": False, "tests": False},
    "red": {"src": False, "tests": True},      # test hat
    "green": {"src": True, "tests": False},     # code hat
    "refactor": {"src": True, "tests": False},  # refactor hat
    "done": {"src": False, "tests": False},
    "none": {"src": True, "tests": True},       # TDD not active
}


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
