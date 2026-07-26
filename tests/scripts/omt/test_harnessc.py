#!/usr/bin/env python3
"""harnessc compiler regression + contract tests (meta_harness_dsl R8 / OMT-HDL-1).

The compiler (scripts/omt/harnessc.py) is the single source of truth behind the
META HARNESS: .meta/META_HARNESS.omt → IR / AGENTS.md / nav.index / opencode.jsonc
splice / budget report. These tests pin:

1. The L161 parse regression: `@var x : 123` must yield payload "123" with
   EMPTY attrs (the payload separator ' : ' must not be swallowed into attrs).
2. The repo .omt passes `check` with 0 errors (incl. budgets).
3. `--verify-projections` is green: committed projections == recompiled.
4. Ref closure catches an unresolved `@kind.id` reference.
5. The pred vocabulary is a closed set (@pred payloads AND @gate when=/requires=).
6. An unknown @budget id is an error (closed budget set, Appendix C).
7. splice_config marker round-trip is idempotent, and a missing end marker
   raises SystemExit (never silently half-splices the live config).

Run with:
    uv run pytest tests/scripts/omt/test_harnessc.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

import harnessc  # noqa: E402


def _corpus(text: str) -> harnessc.Corpus:
    errors: list[str] = []
    records = harnessc.parse(text, errors)
    assert not errors, f"fixture .omt failed to parse: {errors}"
    return harnessc.Corpus(records)


# --- 1. L161 parse regression -------------------------------------------------


def test_parse_var_with_numeric_payload_has_empty_attrs() -> None:
    errors: list[str] = []
    records = harnessc.parse("@var x : 123\n", errors)
    assert errors == []
    assert len(records) == 1
    rec = records[0]
    assert rec.kind == "var" and rec.rid == "x"
    assert rec.payload == "123", (
        "L161 regression: ' : ' payload separator swallowed into attrs/rest")
    assert rec.attrs == {}, (
        f"L161 regression: payload leaked into attrs: {rec.attrs}")


# --- 2. repo .omt checks clean ------------------------------------------------


def test_repo_omt_check_has_zero_errors() -> None:
    assert harnessc.main(["harnessc.py", "check"]) == 0


# --- 3. committed projections match the .omt ----------------------------------


def test_repo_projections_are_fresh() -> None:
    assert harnessc.main(["harnessc.py", "check", "--verify-projections"]) == 0, (
        "committed projections drifted from .meta/META_HARNESS.omt — "
        "run `uv run scripts/omt/harnessc.py build` in the same .omt edit")


# --- 4. ref closure ------------------------------------------------------------


def test_check_refs_catches_unresolved_kind_id() -> None:
    c = _corpus("@msg m sev=info : see @doc.bogus for details\n")
    harnessc.check_refs(c)
    assert any("unresolved ref '@doc.bogus'" in e for e in c.errors), (
        f"ref closure missed @doc.bogus: {c.errors}")


# --- 5. pred vocabulary is closed ----------------------------------------------


def test_check_preds_rejects_unknown_builtins() -> None:
    c = _corpus(
        "@pred p.ok : path_in(\"src/\")\n"
        "@pred p.bad : made_up(x)\n"
        "@gate g.t on=before tools=edit when=!nope(x) msg=@msg.m hard=true "
        "skip_ok=false order=1 : t\n"
        "@msg m sev=block : m\n"
    )
    harnessc.check_preds(c)
    assert any("@pred p.bad" in e and "closed-vocabulary builtin" in e
               for e in c.errors), f"@pred unknown builtin missed: {c.errors}"
    assert any("@gate g.t" in e and "unknown pred 'nope'" in e
               for e in c.errors), f"@gate when= unknown pred missed: {c.errors}"
    assert not any("p.ok" in e for e in c.errors), (
        f"known builtin path_in falsely rejected: {c.errors}")


# --- 6. unknown @budget id is an error -----------------------------------------


def test_unknown_budget_id_is_an_error() -> None:
    c = _corpus("@budget bogus max=100\n")
    harnessc.measure_budgets(c, "")
    assert any("@budget bogus: unknown budget id" in e for e in c.errors), (
        f"closed budget set not enforced: {c.errors}")


# --- 7. splice_config round-trip + missing end marker --------------------------

_CONFIG_FIXTURE = (
    "{\n"
    "  // harnessc:begin read\n"
    "  // harnessc:end read\n"
    "  // harnessc:begin bash\n"
    "  // harnessc:end bash\n"
    "  // harnessc:begin perm\n"
    "  // harnessc:end perm\n"
    "}\n"
)
_BLOCKS = {"read": ['"*.env": "deny"'], "bash": ['"pip *": "deny"'],
           "perm": ['"omt_x": "allow"']}


def test_splice_config_round_trip_is_idempotent() -> None:
    once = harnessc.splice_config(_CONFIG_FIXTURE, _BLOCKS)
    twice = harnessc.splice_config(once, _BLOCKS)
    assert once == twice, "splice is not idempotent (round-trip drift)"
    for entry in ('"*.env": "deny"', '"pip *": "deny"', '"omt_x": "allow"'):
        assert entry in once
    assert once.count("// harnessc:begin read") == 1


def test_splice_config_missing_end_marker_raises() -> None:
    bad = "{\n  // harnessc:begin read\n  \"x\": 1\n}\n"
    with pytest.raises(SystemExit, match="no end marker"):
        harnessc.splice_config(bad, _BLOCKS)


# --- 8. harness_paths classification + stale-entry compile check -------------


def test_ir_harness_paths_classification_and_coverage() -> None:
    c = harnessc.Corpus(harnessc.parse(
        harnessc.OMT_PATH.read_text(encoding="utf-8"), []))
    lists = harnessc.harness_path_lists(c)
    assert "AGENTS.md" in lists["exact"], "files classify as exact"
    assert ".opencode/plugins/omt_" in lists["prefix"], "non-existent → prefix"
    assert any(e.startswith(".meta/software_development_process/2.requirements/"
                           "features/feature_006") for e in lists["prefix"]), (
        "feature_006 requirements dir must stay receipt-guarded")
    harnessc.check_harness_paths(c)
    assert c.errors == [], f"stale harness_paths entries: {c.errors}"


def test_check_harness_paths_flags_stale_entry() -> None:
    c = _corpus("@var harness_paths : AGENTS.md,no/such/dir/\n")
    harnessc.check_harness_paths(c)
    assert any("no/such/dir/" in e and "matches no real repo path" in e
               for e in c.errors), f"stale entry not flagged: {c.errors}"


# --- 9. missing/invalid @version is a clean error, never a traceback ---------


def test_build_ir_missing_version_is_clean_error() -> None:
    """T-024 fix 4: build_ir runs before the checks in main() and used to
    index c.of("version")[0] — a missing @version record crashed with an
    IndexError traceback. It now exits with a clean harnessc error (the
    render_agents/splice_config SystemExit style)."""
    c = _corpus("@var x : 1\n")
    with pytest.raises(SystemExit, match="@version"):
        harnessc.build_ir(c)


def test_build_ir_non_integer_version_is_clean_error() -> None:
    c = _corpus("@version omt_hdl n=abc\n")
    with pytest.raises(SystemExit, match="@version"):
        harnessc.build_ir(c)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
