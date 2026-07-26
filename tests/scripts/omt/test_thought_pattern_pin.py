#!/usr/bin/env python3
"""Shared-lib single-source pins (meta_harness_dsl R1).

Pre-R1 the enforcer and the think plugin each defined their own
THOUGHT_PATTERN (byte-identical pair, drifting unprotected after the
structural test was deleted in a7163df — audit F10; the R0 interim pin
asserted that byte-identity). R1 moved the pattern — plus UNLOCK_WINDOW_MS,
state paths, JSONL IO and repo-root — into the shared lib
`.opencode/lib/omt_shared.ts`. These pins assert the single-source contract:

1. exactly ONE THOUGHT_PATTERN definition repo-wide, in the lib; both
   consuming plugins import it (no local redefinition);
2. UNLOCK_WINDOW_MS agrees across the TS/Python language boundary
   (tdd_check.py keeps its own copy — cross-language, comment-pinned both
   sides per plan R1).

Grep-based (no hard-coded line numbers) so it survives refactors that shift
lines but not the definitions themselves.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

LIB = ".opencode/lib/omt_shared.ts"
ENFORCER = ".opencode/plugins/omt_enforcer.ts"
THINK = ".opencode/plugins/omt_think.ts"
TDD_CHECK = "scripts/omt/tdd_check.py"


def _definition_lines(rel: str) -> list[str]:
    """Lines that carry the THOUGHT_PATTERN definition (contain both the name
    and the TA: literal), whitespace-normalized for comparison."""
    return [
        line.strip()
        for line in (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
        if "THOUGHT_PATTERN" in line and "TA:" in line
    ]


def test_thought_pattern_single_source_in_shared_lib() -> None:
    lib_defs = _definition_lines(LIB)
    assert len(lib_defs) == 1, (
        f"exactly one THOUGHT_PATTERN definition expected in {LIB}: {lib_defs}")
    for plugin in (ENFORCER, THINK):
        plugin_defs = _definition_lines(plugin)
        assert not plugin_defs, (
            f"THOUGHT_PATTERN redefined in {plugin} (R1: single source is "
            f"{LIB}): {plugin_defs}")
        src = (REPO_ROOT / plugin).read_text(encoding="utf-8")
        assert re.search(
            r'import\s*\{[^}]*\bTHOUGHT_PATTERN\b[^}]*\}\s*from\s*"\.\./lib/omt_shared"',
            src, re.DOTALL,
        ), f"{plugin} must import THOUGHT_PATTERN from {LIB}"


def _eval_int_expr(expr: str) -> int:
    """Evaluate a pure-integer arithmetic literal (e.g. '8 * 60 * 60 * 1000')."""
    assert re.fullmatch(r"[\d\s*]+", expr), f"not a pure int expr: {expr!r}"
    return int(eval(expr))  # input regex-pinned to digits, spaces and '*'


def test_unlock_window_ms_agrees_across_languages() -> None:
    """Plan R1: UNLOCK_WINDOW_MS deduped across the TS plugins into the lib;
    tdd_check.py keeps its own copy (cross-language) — the two must agree."""
    lib_src = (REPO_ROOT / LIB).read_text(encoding="utf-8")
    py_src = (REPO_ROOT / TDD_CHECK).read_text(encoding="utf-8")
    m_ts = re.search(r"UNLOCK_WINDOW_MS\s*=\s*([0-9 *]+)", lib_src)
    m_py = re.search(r"UNLOCK_WINDOW_MS\s*=\s*([0-9 *]+)", py_src)
    assert m_ts, f"UNLOCK_WINDOW_MS definition not found in {LIB}"
    assert m_py, f"UNLOCK_WINDOW_MS definition not found in {TDD_CHECK}"
    ts_val, py_val = _eval_int_expr(m_ts.group(1)), _eval_int_expr(m_py.group(1))
    assert ts_val == py_val == 8 * 60 * 60 * 1000, (
        f"UNLOCK_WINDOW_MS drift: {LIB}={ts_val} {TDD_CHECK}={py_val}")


# --- meta_harness_dsl R6 S1 pins: the index rewrite class is DELETED ---------


def _think_source() -> str:
    return (REPO_ROOT / THINK).read_text(encoding="utf-8")


def test_think_index_never_rewritten() -> None:
    """F29-corrected no-rewrite pin: writeFileSync(THOUGHTS_INDEX must appear 0
    times (omt_think/omt_think_remove legitimately writeFileSync the TARGET
    file — that IS the tool's function — so a bare writeFileSync count would be
    false-red forever)."""
    src = _think_source()
    count = src.count("writeFileSync(THOUGHTS_INDEX")
    assert count == 0, (
        f"the thoughts index must be append-only (R6 S1); found "
        f"writeFileSync(THOUGHTS_INDEX ×{count} — the rewrite class is deleted"
    )


def test_reindex_and_reconcile_deleted() -> None:
    """R6 S1: omt_think_reindex + reconcileIndex are gone for good."""
    src = _think_source()
    assert "const omt_think_reindex" not in src
    assert "reconcileIndex" not in src


def test_remove_appends_tombstone() -> None:
    """R6 S1: omt_think_remove appends a remove-tombstone instead of rewriting."""
    src = _think_source()
    assert 'appendIndex({ kind: "remove"' in src


def test_digest_stale_join_is_text_keyed() -> None:
    """F28: the digest's stale-join matches verify verdicts to live hits by
    normalized thought TEXT (identity), never path:line (line drift must not
    re-attach a verdict to the wrong thought)."""
    src = _think_source()
    assert "latestVerifyByText.get(p.text)" in src
    assert "latestAddTsByText.get(p.text)" in src
