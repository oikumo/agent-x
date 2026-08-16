"""TDD gates (meta_harness_dsl R3) — two-hats + validate-exit.

Extracted from the former monolithic scripts/omt/tdd_check.py:
  - HAT_RULES:     the two-hats edit matrix (spec: two_hats_never_same_time)
  - gate:          is this edit allowed in the current TDD state?
  - after-edit:    post-edit advisory / refactor revert check
  - validate-exit: phase-exit validation (dangling reds, coverage gaps)
"""
from __future__ import annotations

import json
import time

from .ast_checks import (
    extract_public_methods,
    extract_test_references,
    find_untested_methods,
    infer_target_src,
)
from .state import (
    REPO_ROOT,
    UNLOCK_WINDOW_MS,
    _resolve_src_path,
    _resolve_test_path,
    _within_window,
    diff_snapshots,
    get_current_test_node,
    get_tdd_cycles,
    get_tdd_state,
    load_feature_baseline,
    load_snapshot,
    read_ledger,
    run_pytest,
    snapshot_source,
)

# Two-hats gate rules: {state: {src: bool, tests: bool}}
# improvement007 R5/OPT-E: the .omt @hat records are the single source — when
# the compiled IR is present, HAT_RULES/HAT_REVERT_ON are DERIVED from ir.hats
# at module load (allow "tests/"→tests-only, "src/"→src-only, ""→no edits; the
# engine-local "none" state is appended). The literals stay as the no-IR
# fallback (pre-build checkout); pinned ≡ ir.hats-derived in test_tdd_check.py
# (mirror of the R4 TS FALLBACK_* pins; pattern precedent: state._ir_var_int).
_FALLBACK_HAT_RULES: dict[str, dict[str, bool]] = {
    "testlist": {"src": False, "tests": False},
    "red": {"src": False, "tests": True},      # test hat
    "green": {"src": True, "tests": False},     # code hat
    "refactor": {"src": True, "tests": False},  # refactor hat
    "done": {"src": False, "tests": False},
    "none": {"src": True, "tests": True},       # TDD not active
}

_FALLBACK_HAT_REVERT_ON: dict[str, str] = {
    "testlist": "",
    "red": "",
    "green": "",
    "refactor": "tests_break",
    "done": "",
}


def _ir_hats() -> dict[str, dict[str, str]] | None:
    """Best-effort read of ir.hats; None (missing/corrupt IR) → literals win."""
    try:
        ir = json.loads(
            (REPO_ROOT / ".meta" / ".omt" / "harness.ir.json").read_text(encoding="utf-8")
        )
        return ir.get("hats") or None
    except (OSError, ValueError):
        return None


def _derive_hat_rules(hats: dict[str, dict[str, str]]) -> dict[str, dict[str, bool]]:
    rules = {
        rid.split(".", 1)[-1]: {
            "src": hat.get("allow", "") == "src/",
            "tests": hat.get("allow", "") == "tests/",
        }
        for rid, hat in hats.items()
    }
    rules["none"] = {"src": True, "tests": True}  # engine-local, not in IR
    return rules


_IR_HATS = _ir_hats()
HAT_RULES: dict[str, dict[str, bool]] = (
    _derive_hat_rules(_IR_HATS) if _IR_HATS else _FALLBACK_HAT_RULES
)
HAT_REVERT_ON: dict[str, str] = (
    {rid.split(".", 1)[-1]: hat.get("revert_on", "") for rid, hat in _IR_HATS.items()}
    if _IR_HATS else _FALLBACK_HAT_REVERT_ON
)


def cmd_gate(args) -> dict:
    state = get_tdd_state(args.session)
    is_tests = args.is_tests or args.path.startswith("tests/")
    rules = HAT_RULES.get(state, HAT_RULES["none"])
    allowed = rules["tests"] if is_tests else rules["src"]
    if not allowed:
        hat = {"red": "test", "green": "code", "refactor": "refactor",
               "testlist": "planning", "done": "complete"}.get(state, "")
        # P3-8 (feature_028, R6): branch on the IR-derived allow-set, NOT the
        # state name — a both-blocked state (any hat with allow="") says
        # "nothing editable", whatever the hat is called.
        if not rules["src"] and not rules["tests"]:
            which = ("nothing editable — declare omt_tdd{op:red} at a failing "
                     "test to enter the test hat.")
        elif rules["tests"]:
            which = "Only tests/ edits allowed."
        else:
            which = "Only src/ edits allowed."
        return {
            "allowed": False,
            "reason": f"⛔ TDD two-hats: wearing the {hat} hat. {which} "
                      f"(spec: two_hats_never_same_time)",
            "state": state, "tdd_mode": state != "none",
        }
    return {"allowed": True, "reason": "", "state": state, "tdd_mode": state != "none"}


def cmd_after_edit(args) -> dict:
    state = get_tdd_state(args.session)

    if HAT_REVERT_ON.get(state) == "tests_break":
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

    # feature_024 skip override (works around the latent phase_gate.ts bug
    # where the advertised "call omt_skip to override" never consulted the
    # skip ledger): honor an active omt_skip{scope:"all"} here. This Python
    # side is shelled out to LIVE on every omt_complete, so the override
    # takes effect in-session. Window-fallback semantics (no --session is
    # threaded through validate-exit; mirrors TS hasNavUnlock).
    now_ms = time.time() * 1000
    skip_override = any(
        r.get("kind") == "skip"
        and r.get("scope") == "all"
        and _within_window(r, now_ms)
        for r in read_ledger()
    )

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
                # P1-3 (feature_028, R5): scope the gap to methods ADDED by
                # THIS feature's diff — diff against the feature-baseline
                # snapshot (captured at first RED). No baseline (legacy
                # feature) → every current method counts as added → the
                # legacy full-file scan applies unchanged (D5).
                baseline = load_feature_baseline(feature, src_path)
                added = diff_snapshots(
                    baseline, {"methods": extract_public_methods(src_path)})
                added_keys = {(m["class"], m["method"]) for m in added}
                scoped = [m for m in untested
                          if (m["class"], m["method"]) in added_keys]
                if scoped:
                    coverage_gaps.append({"file": target, "untested": scoped})

    all_ok = len(dangling) == 0 and len(coverage_gaps) == 0
    summary = {
        "test_files": len(test_files), "src_files": len(all_targets),
        "untested_methods": sum(len(g["untested"]) for g in coverage_gaps),
    }
    if skip_override and not all_ok:
        return {
            "ok": True, "dangling_reds": [], "coverage_gaps": [],
            "summary": {**summary, "skip_override": True},
        }
    return {
        "ok": all_ok, "dangling_reds": dangling, "coverage_gaps": coverage_gaps,
        "summary": summary,
    }
