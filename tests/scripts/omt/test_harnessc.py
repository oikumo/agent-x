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
8. Grammar vocab hardening (improvement007/OPT-D): fsm state closure, hat
   allow/revert_on + inject on= closed vocab, @gate when= pred-call arity
   + no '|' in args, @gate order uniqueness per on= group.
9. tool_args budget: live dispatcher arg describes measured from TS
   (irToolDescription region), per-op helpers excluded (OPT-A).

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


# --- 10. grammar vocab hardening (improvement007/OPT-D) ------------------------


def test_grammar_vocab_fsm_state_closure() -> None:
    c = _corpus(
        '@fsm bad states="A,B" initial="Z" transitions="A>B;B>Q" : t\n')
    harnessc.check_grammar_vocab(c)
    assert any("initial 'Z' not in states" in e for e in c.errors), c.errors
    assert any("transition endpoint 'Q' not in states" in e
               for e in c.errors), c.errors


def test_grammar_vocab_hat_vocab() -> None:
    c = _corpus('@hat tdd.x allow="src/*.py" revert_on="boom" : t\n')
    harnessc.check_grammar_vocab(c)
    assert any("revert_on" in e for e in c.errors), c.errors
    assert any("allow entry 'src/*.py'" in e for e in c.errors), c.errors


def test_grammar_vocab_inject_on_closed() -> None:
    c = _corpus("@inject i on=every_tool budget=10 : t\n")
    harnessc.check_grammar_vocab(c)
    assert any("@inject i" in e and "closed" in e for e in c.errors), c.errors


def test_grammar_vocab_gate_when_arity_and_pipe() -> None:
    c = _corpus(
        "@gate g.a on=before tools=edit when=receipt_fresh(x) msg=@msg.m "
        "hard=true skip_ok=false order=1 : t\n"
        "@gate g.b on=before tools=edit when=ledger_has(phase|skip) msg=@msg.m "
        "hard=true skip_ok=false order=2 : t\n"
        "@msg m sev=block : m\n"
    )
    harnessc.check_grammar_vocab(c)
    assert any("receipt_fresh() takes 0 arg(s), got 1" in e
               for e in c.errors), c.errors
    assert any("reject '|' alternation" in e for e in c.errors), c.errors


def test_grammar_vocab_gate_order_unique_per_on_group() -> None:
    c = _corpus(
        "@gate g.a on=before tools=edit when=risk_high() msg=@msg.m hard=true "
        "skip_ok=false order=10 : t\n"
        "@gate g.b on=before tools=edit when=risk_high() msg=@msg.m hard=true "
        "skip_ok=false order=10 : t\n"
        "@gate g.c on=after tools=edit when=risk_high() msg=@msg.m hard=false "
        "skip_ok=false order=10 : t\n"
        "@msg m sev=block : m\n"
    )
    harnessc.check_grammar_vocab(c)
    dups = [e for e in c.errors if "order=10 duplicates" in e]
    assert len(dups) == 1 and "g.b" in dups[0], (
        f"exactly the same-group duplicate must be flagged: {c.errors}")


def test_grammar_vocab_accepts_valid_shapes() -> None:
    c = _corpus(
        '@fsm ok states="A,B" initial="A" transitions="A>B;B>A" : t\n'
        '@hat tdd.a allow="src/" revert_on="tests_break" : t\n'
        "@inject i on=file_read budget=10 : t\n"
        "@gate g.a on=before tools=edit when=fsm_allows(@fsm.ok,path) msg=@msg.m "
        "hard=true skip_ok=false order=1 : t\n"
        "@msg m sev=block : m\n"
    )
    harnessc.check_grammar_vocab(c)
    assert c.errors == [], f"valid shapes falsely rejected: {c.errors}"


# --- 11. tool_args budget measures live TS arg describes (OPT-A) ---------------


def test_ts_arg_describes_region_and_unescape() -> None:
    src = (
        'const t = tool({ description: irToolDescription("omt_x", "d"), '
        'args: { a: tool.schema.string().describe("alpha"), '
        'b: tool.schema.string().optional().describe(\n'
        '  "be \\"ta\\"") }, '
        'async execute(args) { return "x" } })\n'
        'const u = tool({ description: "other", args: { '
        'c: tool.schema.string().describe("not-counted") } })\n'
    )
    assert harnessc._ts_arg_describes(src, "omt_x") == ["alpha", 'be "ta"']


def test_tool_args_budget_measures_live_describes_only() -> None:
    """improvement007/OPT-A: tool_args counts describe() bytes of the 7 LIVE
    dispatcher tools (irToolDescription region); unregistered per-op helper
    describes in the same files never reach the model and are excluded."""
    c = harnessc.Corpus(harnessc.parse(
        harnessc.OMT_PATH.read_text(encoding="utf-8"), []))
    sizes = harnessc.measure_budgets(c, "")
    size, cap = sizes["tool_args"]
    assert cap is not None and 0 < size <= cap, f"tool_args={size}/{cap}"
    nav = (harnessc.REPO_ROOT / ".opencode/plugins/omt_nav.ts").read_text(
        encoding="utf-8")
    live = harnessc._ts_arg_describes(nav, "omt_nav")
    all_desc = harnessc.re.findall(r'describe\(\s*"((?:[^"\\]|\\.)*)"', nav,
                                   harnessc.re.DOTALL)
    assert len(live) < len(all_desc), (
        "per-op helper describes must be excluded from the live measure")



# --- 12. orphan-@msg check (improvement007 R8/OPT-G) ---------------------------


def test_msg_orphans_flags_unwired_msg() -> None:
    c = _corpus(
        "@gate g.t on=before tools=edit when=risk_high() msg=@msg.used "
        "hard=true skip_ok=false order=1 : t\n"
        "@msg used sev=block : used\n"
        "@msg dead_weight sev=warn : nobody references me\n"
    )
    harnessc.check_msg_orphans(c)
    assert any("@msg dead_weight: orphan" in e for e in c.errors), c.errors
    assert not any("@msg used" in e for e in c.errors), c.errors


def test_msg_orphans_payload_and_deny_refs_count() -> None:
    c = _corpus(
        '@deny bash.x scope=bash match="x *" msg=@msg.deny_x : d\n'
        "@msg deny_x sev=block : denied\n"
        "@msg catalog_entry sev=block : rule text\n"
        '@xref cat tags="X" : catalog: @msg.catalog_entry\n'
        "@msg self_only sev=info : see @msg.self_only — self-refs don't count\n"
    )
    harnessc.check_msg_orphans(c)
    assert not any("@msg deny_x" in e for e in c.errors), c.errors
    assert not any("@msg catalog_entry" in e for e in c.errors), c.errors
    assert any("@msg self_only: orphan" in e for e in c.errors), c.errors


def test_msg_orphans_repo_corpus_fully_wired() -> None:
    """The real corpus passes with zero orphans: gate/deny/protect msg= attrs,
    the @xref mvc catalog enumeration, and the TS gateMsg("<id>") consumers
    (artifact/mvc_warn/protect_env have no in-corpus msg= — TS-wired, R8)."""
    c = harnessc.Corpus(harnessc.parse(
        harnessc.OMT_PATH.read_text(encoding="utf-8"), []))
    harnessc.check_msg_orphans(c)
    assert c.errors == [], f"repo corpus has orphan @msg: {c.errors}"
    ts = (harnessc.REPO_ROOT / ".opencode/lib/enforcer/phase_gate.ts").read_text(
        encoding="utf-8")
    assert 'gateMsg("artifact"' in ts, "artifact must be TS-consumed (OPT-G)"


# --- 13. derive round 2: flows/trees/prot/esc from single sources (R9/OPT-I) --


def _repo_corpus_derived() -> harnessc.Corpus:
    text = harnessc.OMT_PATH.read_text(encoding="utf-8")
    c = harnessc.Corpus(harnessc.parse(text, []))
    harnessc.interpolate(c)
    harnessc.derive_records(c, text)
    assert c.errors == [], f"repo derive errors: {c.errors}"
    return c


def test_derive_start_flows_from_phase_fsm_scaffold() -> None:
    c = _repo_corpus_derived()
    flows = {r.rid: r for r in c.of("flow")}
    major = flows["start_major"].payload
    assert major.startswith('omt_phase{tt:major_feature,ph:Analysis'), major
    assert "design doc (uv run scripts/omt/new_feature.py)" in major, (
        "design leg from @phase requires=decl,design + @var scaffold")
    assert "TDD auto-on" in major, "@fsm tdd auto_on leg missing"
    assert flows["start_major"].attrs["tags"] == "QUICK_START_MAJOR"
    minor = flows["start_minor"].payload
    assert minor.startswith('omt_phase{tt:minor_feature,ph:Design'), minor
    bug = flows["start_bug"].payload
    assert bug.startswith('omt_phase{tt:bug_fix,ph:Programming'), bug
    assert "omt_complete{advance_to:Testing}" in bug


def test_derive_tdd_flows_cover_fsm_states_and_hat_attrs() -> None:
    c = _repo_corpus_derived()
    flows = {r.rid: r for r in c.of("flow")}
    fsm = c.get("fsm", "tdd")
    assert fsm is not None
    states = [s.strip().lower() for s in fsm.attrs["states"].split(",")]
    for s in states:
        rec = flows.get(f"tdd_{s}")
        assert rec is not None, f"no derived flow for @fsm tdd state {s}"
        assert rec.attrs["tags"] == f"QUICK_TDD_{s.upper()}"
        assert f"omt_tdd{{op:{s}}}" in rec.payload
    assert "allow: tests/" in flows["tdd_red"].payload  # @hat tdd.red allow=
    assert "allow: src/" in flows["tdd_refactor"].payload
    assert "auto-revert on tests_break" in flows["tdd_refactor"].payload, (
        "revert_on=tests_break must surface in the derived flow")


def test_derive_trees_prot_esc_from_gates_protects_tool() -> None:
    c = _repo_corpus_derived()
    docs = {r.rid: r for r in c.of("doc")}
    src_tree = docs["tree.src"].payload
    assert "g.phase" in src_tree and "g.mvc" in src_tree
    assert "g.tdd_after" in src_tree
    assert "g.tests" in docs["tree.tst"].payload
    assert "tdd.red" in docs["tree.tst"].payload  # @hat allows tests/
    assert "no phase required" in docs["tree.doc"].payload  # @phase docs_none
    prot = docs["prot.files"].payload
    assert ".env" in prot and "README.md" in prot and "uv.lock" in prot
    esc = docs["esc"].payload
    assert "scope:src|tests|nav|all" in esc  # from @tool omt_skip payload
    assert "everything except .env" in esc  # hard @protect exclusion


def test_derive_tdd_flow_state_without_hat_is_an_error() -> None:
    c = _corpus(
        '@fsm tdd states="RED,BLUE" initial="RED" : t\n'
        '@hat tdd.red allow="tests/" : t\n'
    )
    harnessc.derive_records(c, "")
    assert any("state 'blue' has no @hat tdd.blue" in e for e in c.errors), (
        f"missing-hat derive source not flagged: {c.errors}")


def test_derive_tdd_flow_state_without_gloss_is_an_error() -> None:
    c = _corpus(
        '@fsm tdd states="PURPLE" initial="PURPLE" : t\n'
        '@hat tdd.purple allow="" : t\n'
    )
    harnessc.derive_records(c, "")
    assert any("no TDD_FLOW_GLOSS entry" in e for e in c.errors), (
        f"missing-gloss not flagged: {c.errors}")


def test_hand_record_under_derived_id_is_duplicate_error() -> None:
    c = _corpus(
        '@fsm tdd states="RED" initial="RED" : t\n'
        '@hat tdd.red allow="tests/" : t\n'
        '@flow tdd_red tags="QUICK_TDD_RED" : hand-written drift bait\n'
    )
    harnessc.derive_records(c, "")
    harnessc.check_ids(c)
    assert any("duplicate id flow.tdd_red" in e for e in c.errors), (
        f"hand re-add under a derived id not flagged: {c.errors}")


def test_r9_pruned_nav_dups_stay_absent() -> None:
    """doc.nav.tools (dup of @tool omt_nav + comp.nav) and doc.nav.workflow
    (dup of flow.nav_docs) were pruned as dead weight — keep them out."""
    c = _repo_corpus_derived()
    ids = {r.full_id for r in c.records}
    assert "doc.nav.tools" not in ids and "doc.nav.workflow" not in ids
    nav = harnessc.render_nav_index(c)
    assert "doc.nav.tools" not in nav and "doc.nav.workflow" not in nav


# --- 14. on-demand doc budgets: META_HARNESS.md stub + META.md (R10/OPT-B) ----


def test_meta_doc_budget_ids_are_measurable() -> None:
    assert {"meta_harness_md", "meta_md"} <= harnessc.MEASURABLE_BUDGETS


def test_meta_doc_budgets_measured_and_within_cap() -> None:
    text = harnessc.OMT_PATH.read_text(encoding="utf-8")
    c = harnessc.Corpus(harnessc.parse(text, []))
    sizes = harnessc.measure_budgets(c, "", "", "")
    for rid in ("meta_harness_md", "meta_md"):
        size, cap = sizes[rid]
        assert size > 0 and cap is not None and size <= cap, (
            f"{rid}: {size} B vs cap {cap} B — grow the budget deliberately "
            "in the same .omt edit")


def test_meta_harness_stub_rotates_state_notes() -> None:
    mh = harnessc.META_HARNESS_MD_PATH.read_text(encoding="utf-8")
    assert "GENERATED" in mh and ".meta/META_HARNESS.omt" in mh  # e2e contract
    assert "improvement001" not in mh and "improvement005" not in mh, (
        "rotated state notes live in git history, not inline")
    assert "ROTATION" in mh, "the rotation rule must travel with the stub"


def test_meta_md_has_no_stale_read_first_directive() -> None:
    md = harnessc.META_MD_PATH.read_text(encoding="utf-8")
    assert "READ FIRST" not in md, (
        "stale directive misroutes agents to the retired .md stub")
    assert ".meta/META_HARNESS.omt" in md, "must route to the live corpus"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
