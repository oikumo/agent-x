#!/usr/bin/env python3
"""Feature-acceptance tests for feature_kb_akb.application_knowledge_base.

Run with: uv run pytest tests/features/feature_kb_akb.application_knowledge_base/ -v

These tests pin the feature-level contracts of the Application Knowledge Base:
- The unified index builds (AST skeleton + curated overlay) with 0 errors.
- The g.kb consult-gate is WIRED (SESSION_FLAGS impl + kbTrack + state.kb Map).
- omt_kb_nav plugin exposes the four ops (nav | list_sections | cross_ref | quick_ref)
  with the per-query MAX_RECORDS cap + truncated marker.

The contract tests live alongside the existing unit tests
(`tests/scripts/omt/test_kb_*.py` — 21 tests for AST extraction + compiler) and
the structural e2e tests (`tests/scripts/omt/test_omt_harness_e2e.py`); this
file fills the feature-acceptance layer required by the §12 phase-exit matrix
(phase_gate.ts PHASE_EXIT_REQUIREMENTS["Programming"] → Testing).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _run(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


class TestKbFeatureAcceptance:
    """Feature-level acceptance for feature_kb_akb.application_knowledge_base."""

    def test_kb_compiler_build_runs_clean(self) -> None:
        """`uv run scripts/omt/kb_compiler.py build` produces a unified index
        with the expected record distribution and 0 errors."""
        result = _run(["uv", "run", "scripts/omt/kb_compiler.py", "build"])
        assert result.returncode == 0, result.stdout + result.stderr
        # 439 records (240 class + 32 contract + 105 dep + 39 doc + 12 feature + 9 flow + 2 xref)
        # 437→439 drift introduced by feature_025 (added 2 test classes under
        # tests/features/feature_025.coding_context_window_optimization/). Re-pin
        # update is mechanical — bumps class=239→240, dep=104→105.
        assert "class=240" in result.stdout, result.stdout
        assert "contract=32" in result.stdout, result.stdout
        assert "dep=105" in result.stdout, result.stdout
        # Index written
        assert (REPO_ROOT / ".meta/.omt/kb.index.jsonl").exists()
        assert (REPO_ROOT / ".meta/.omt/kb.ir.json").exists()

    def test_kb_index_jsonl_well_formed_and_comprehensive(self) -> None:
        """The unified index is JSONL + covers all expected kinds."""
        idx_path = REPO_ROOT / ".meta/.omt/kb.index.jsonl"
        records = []
        for line in idx_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        # Total ≥ 400 (skeleton + curated + overlay)
        assert len(records) >= 400, f"expected ≥400 records, got {len(records)}"
        # All expected kinds present
        kinds = {r["kind"] for r in records}
        for kind in ("class", "contract", "dep", "doc", "feature", "flow", "xref"):
            assert kind in kinds, f"kind '{kind}' missing from index"
        # All records have required fields
        for r in records:
            assert "id" in r and "kind" in r and "tags" in r and "tier" in r

    def test_overlay_wins_for_agent_facade_class(self) -> None:
        """B7 acceptance: class.Agent's text is the curated overlay (not the
        AST auto-text `Agent(IAgentModelPartner)`)."""
        idx_path = REPO_ROOT / ".meta/.omt/kb.index.jsonl"
        agent_rec = None
        for line in idx_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["id"] == "class.Agent":
                agent_rec = r
                break
        assert agent_rec is not None, "class.Agent not in index"
        # Auto-text is just `Agent(IAgentModelPartner)`; overlay text is the
        # curated facade description.
        assert "facade orchestrating" in agent_rec["text"], (
            f"Agent overlay text not present (got: {agent_rec['text']!r})")

    def test_overlay_wins_for_tool_registry(self) -> None:
        """class.ToolRegistry's text is the curated overlay."""
        idx_path = REPO_ROOT / ".meta/.omt/kb.index.jsonl"
        for line in idx_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["id"] == "class.ToolRegistry":
                assert "Model-layer tool catalog" in r["text"]
                return
        pytest.fail("class.ToolRegistry not in index")


class TestKbConsultGateWiring:
    """Session-12 follow-up: the g.kb consult-gate must be WIRED in the
    harness-source — `SESSION_FLAGS[kb_consulted]` impl, `kbTrack` tracker
    callable, `state.kb` Map in session_state, `KB_TOOLS` set in nav_gate.

    The runtime gate executes in the opencode host process (TS plugins loaded
    at session start); these structural pins guard the contract independently
    of session reload.
    """

    def test_session_flags_kb_consulted_in_gate_driver(self) -> None:
        """`SESSION_FLAGS["kb_consulted"]` impl present in gate_driver.ts."""
        gate_driver = _read(".opencode/lib/enforcer/gate_driver.ts")
        assert re.search(r"kb_consulted:\s*\(ctx\)", gate_driver), (
            "kb_consulted SESSION_FLAGS impl missing from gate_driver.ts")
        assert "env.state.kb.get(ctx.session)" in gate_driver, (
            "kb_consulted predicate does not read env.state.kb Map")

    def test_kb_track_exported_by_nav_gate(self) -> None:
        """nav_gate.ts exports `kbTrack` and declares `KB_TOOLS` set."""
        nav_gate = _read(".opencode/lib/enforcer/nav_gate.ts")
        assert 'const KB_TOOLS = new Set(["omt_kb_nav"])' in nav_gate, (
            "KB_TOOLS set missing from nav_gate.ts")
        assert "export async function kbTrack" in nav_gate, (
            "kbTrack not exported by nav_gate.ts")

    def test_state_kb_in_session_state(self) -> None:
        """session_state.ts declares the per-session kb consult Map."""
        session_state = _read(".opencode/lib/enforcer/session_state.ts")
        assert "kb: new Map<string, { consulted: boolean }>()" in session_state, (
            "state.kb Map missing from session_state.ts")

    def test_kb_track_wired_into_enforcer(self) -> None:
        """omt_enforcer.ts imports + invokes kbTrack in the before-hook."""
        enforcer = _read(".opencode/plugins/omt_enforcer.ts")
        assert 'kbTrack' in enforcer, (
            "kbTrack not referenced by omt_enforcer.ts")
        assert "await kbTrack(env, session, input)" in enforcer, (
            "kbTrack not awaited in omt_enforcer.ts before-hook")

    def test_omt_kb_nav_in_harness_files_list(self) -> None:
        """omt_kb_nav.ts is in the e2e HARNESS_FILES list (receipt-guard
        coverage)."""
        e2e = _read("tests/scripts/omt/test_omt_harness_e2e.py")
        assert '".opencode/plugins/omt_kb_nav.ts"' in e2e, (
            "omt_kb_nav.ts missing from HARNESS_FILES in e2e test")


class TestKbNavPluginContract:
    """omt_kb_nav.ts plugin contract pinning."""

    def test_plugin_default_export_and_tool_dispatch(self) -> None:
        """omt_kb_nav.ts is a single-plugin default export with op= dispatch."""
        plugin = _read(".opencode/plugins/omt_kb_nav.ts")
        assert "export default async" in plugin
        assert "tool: { omt_kb_nav }" in plugin
        # Op dispatch covers all 4 ops
        for op in ("nav", "list_sections", "cross_ref", "quick_ref"):
            assert f'case "{op}"' in plugin, f"op dispatch missing '{op}'"

    def test_max_records_cap_constant(self) -> None:
        """MAX_RECORDS per-query cap is defined (per-query token bound)."""
        plugin = _read(".opencode/plugins/omt_kb_nav.ts")
        m = re.search(r"const MAX_RECORDS = (\d+)", plugin)
        assert m, "MAX_RECORDS constant missing from omt_kb_nav.ts"
        # P0 with 437-record index — cap MUST be set (24 < cap <= 100 sensible)
        cap = int(m.group(1))
        assert 10 <= cap <= 200, f"MAX_RECORDS={cap} expects a sane per-query bound"

    def test_truncated_marker_when_over_limit(self) -> None:
        """capRecords() emits a `truncated: N/M records — refine query` marker
        when the hit count exceeds MAX_RECORDS."""
        plugin = _read(".opencode/plugins/omt_kb_nav.ts")
        assert "truncated:" in plugin, "truncated marker text missing"
        assert "refine query" in plugin, "refine-query hint missing from truncated marker"
