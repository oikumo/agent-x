"""Wave 5/D1 init + D3 onboarding RED — feature_059.

Contract (GREEN pins per design_001 §3.2–3.3 + operation_spec_001):
- cmd_init(tier, dest): missing-or-empty dir → writes .meta/META_HARNESS.omt
  (tier-filtered source records), WORK.md skeleton, .meta/.omt ledger+thoughts,
  GETTING_STARTED.md, opencode.jsonc (harnessc blocks), runtime copies
  (scripts/omt, .opencode w/o node_modules, .meta/templates, guide, f006 dir,
  .workflows at T2+), tests/scripts/omt/test_template_e2e.py, .projects
  manifest + WORK.md Projects section; self-validates via check_tree (fail-closed).
- init refuses non-empty dir even with --force (never clobber).
- render_getting_started: Tier-1 names core gates, contains no nav/think/kb/net
  tokens; Tier-3-full lists all 10 gates.
- Target tree validates: emitted .omt parses + run_all_checks green in-process.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

import harnessc


def test_init_tier1_builds_working_tree(tmp_path):
    dest = tmp_path / "t1repo"
    rc = harnessc.cmd_init(["--tier", "1", str(dest)])
    assert rc == 0
    omt = dest / ".meta" / "META_HARNESS.omt"
    assert omt.exists()
    assert (dest / "WORK.md").exists()
    assert (dest / "GETTING_STARTED.md").exists()
    assert (dest / "opencode.jsonc").exists()
    assert (dest / "tests" / "scripts" / "omt" / "test_template_e2e.py").exists()
    assert (dest / "AGENTS.md").exists()
    # tier purity of the emitted policy
    text = omt.read_text(encoding="utf-8")
    assert "@gate g.nav " not in text and "@gate g.think " not in text
    assert "@gate g.net " not in text and "@gate g.receipt " not in text
    assert "@gate g.phase " in text and "@gate g.tests " in text
    # self-validation: the emitted tree checks green
    errors = harnessc.check_tree(dest)
    assert errors == []


def test_init_refuses_non_empty_dir(tmp_path):
    dest = tmp_path / "lived"
    dest.mkdir()
    (dest / "precious.txt").write_text("do not clobber", encoding="utf-8")
    assert harnessc.cmd_init(["--tier", "1", str(dest)]) == 1
    assert harnessc.cmd_init(["--tier", "1", "--force", str(dest)]) == 1
    assert (dest / "precious.txt").read_text(encoding="utf-8") == "do not clobber"
    assert not (dest / ".meta").exists()


def test_init_tier3_net_gating(tmp_path):
    plain = tmp_path / "t3"
    assert harnessc.cmd_init(["--tier", "3", str(plain)]) == 0
    text = (plain / ".meta" / "META_HARNESS.omt").read_text(encoding="utf-8")
    assert "@gate g.receipt " in text and "@gate g.net " not in text
    assert harnessc.check_tree(plain) == []
    with_net = tmp_path / "t3n"
    assert harnessc.cmd_init(["--tier", "3", "--with-net", str(with_net)]) == 0
    text_n = (with_net / ".meta" / "META_HARNESS.omt").read_text(encoding="utf-8")
    assert "@gate g.net " in text_n
    assert harnessc.check_tree(with_net) == []


def test_getting_started_tier_content():
    omt_text = (REPO_ROOT / ".meta" / "META_HARNESS.omt").read_text(encoding="utf-8")
    c = harnessc.Corpus(harnessc.parse(omt_text, []))
    harnessc.interpolate(c)
    t1 = harnessc.filter_corpus_for_tier(c, 1)
    g1 = harnessc.render_getting_started(t1, 1)
    assert "Tier 1" in g1
    for tok in ("omt_nav", "omt_think", "omt_kb_nav", "omt_net", "g.net"):
        assert tok not in g1, f"Tier-1 onboarding must not mention {tok}"
    for g in ("g.phase", "g.tests", "g.protect"):
        assert g in g1
    t3 = harnessc.filter_corpus_for_tier(c, 3, with_net=True)
    g3 = harnessc.render_getting_started(t3, 3)
    assert len([ln for ln in g3.splitlines() if ln.startswith("- `g.")]) == 10
