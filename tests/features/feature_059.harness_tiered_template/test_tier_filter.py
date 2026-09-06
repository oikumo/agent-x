"""Wave 5/D1+D2+D3 harness_tiered_template — feature_059 RED.

Contract (GREEN pins the implementation per design_001 + operation_spec_001):
- filter_corpus_for_tier: T1 core gates/tools, drops nav/think/kb/net/receipt;
  T2 adds nav/think/kb/q; T3 adds receipt, net excluded default / included
  with with_net flag (DG3).
- check_template_vars: bad default_tier / bad stack_profile = check error.
- init --tier 1: files in empty tmp dir, emitted .omt parses + checks green.
- init refuses non-empty dir even with --force (never clobber).
- render_getting_started: Tier-1 has no nav/think/kb/net tokens; Tier-3 lists gates.
- mvc_check --profile none exits 0 clean; mvc_ts flags TS view-creates-controller.
- budget pins: nav_index/tool_args/tool_schemas/agents_md unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

import harnessc


def _load_full_corpus():
    omt_text = (REPO_ROOT / ".meta" / "META_HARNESS.omt").read_text(encoding="utf-8")
    c = harnessc.Corpus(harnessc.parse(omt_text, []))
    harnessc.interpolate(c)
    harnessc.derive_records(c, omt_text)
    return c


def test_tier1_keeps_core_drops_knowledge_net():
    c = _load_full_corpus()
    t1 = harnessc.filter_corpus_for_tier(c, 1)
    gates = {g.rid for g in t1.of("gate")}
    tools = {t.rid for t in t1.of("tool")}
    assert "g.protect" in gates and "g.phase" in gates and "g.tests" in gates
    for dropped in ("g.nav", "g.think", "g.kb", "g.net", "g.receipt"):
        assert dropped not in gates, f"T1 must drop {dropped}"
    for kept in ("omt_phase", "omt_skip", "omt_tdd", "omt_complete", "omt_status"):
        assert kept in tools, f"T1 must keep {kept}"
    for dropped_t in ("omt_nav", "omt_think", "omt_kb_nav", "omt_net", "omt_q"):
        assert dropped_t not in tools, f"T1 must drop tool {dropped_t}"


def test_tier2_adds_knowledge_over_t1():
    c = _load_full_corpus()
    t2 = harnessc.filter_corpus_for_tier(c, 2)
    gates = {g.rid for g in t2.of("gate")}
    tools = {t.rid for t in t2.of("tool")}
    for added in ("g.nav", "g.think", "g.kb"):
        assert added in gates, f"T2 must add {added}"
    for added_t in ("omt_nav", "omt_think", "omt_kb_nav", "omt_q"):
        assert added_t in tools, f"T2 must add tool {added_t}"
    assert "g.net" not in gates and "g.receipt" not in gates


def test_tier3_receipt_net_gating():
    c = _load_full_corpus()
    t3 = harnessc.filter_corpus_for_tier(c, 3)
    gates = {g.rid for g in t3.of("gate")}
    assert "g.receipt" in gates
    assert "g.net" not in gates, "T3 excludes net by default (DG3)"
    t3n = harnessc.filter_corpus_for_tier(c, 3, with_net=True)
    gates_n = {g.rid for g in t3n.of("gate")}
    assert "g.net" in gates_n


def test_template_vars_reject_bad_values():
    c = _load_full_corpus()
    # mutate copies: bad tier
    import copy
    c2 = copy.deepcopy(c)
    var = c2.get("var", "template_default_tier")
    assert var is not None
    var.payload = "5"
    n_before = len(c2.errors)
    harnessc.check_template_vars(c2)
    assert len(c2.errors) > n_before
    # bad profile
    c3 = copy.deepcopy(c)
    var3 = c3.get("var", "stack_profile")
    assert var3 is not None
    var3.payload = "rails"
    n3 = len(c3.errors)
    harnessc.check_template_vars(c3)
    assert len(c3.errors) > n3
