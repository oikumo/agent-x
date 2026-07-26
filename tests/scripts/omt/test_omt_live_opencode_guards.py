"""
LIVE smoke: drive the REAL opencode binary (`opencode run --format json`) and
assert the OMT harness is alive in the production runtime — the minimal check
that would have caught "plugins silently not loading" drift, which runner
fixtures cannot see (the F14 meta-lesson: fixtures fabricate the shapes the
code expects and stay green while the real runtime drifts).

What this proves, live, per the OpenCode plugin architecture
(.meta/doc/opencode_plugins/OpenCode Plugin Creation Guide.md):

  1. All 4 plugins auto-load from .opencode/plugins/ in a real run — one tool
     per plugin (omt_status / omt_list_sections / omt_think_list / omt_skip)
     registers and executes to completion. No npm distribution involved.
  2. tool.execute.after hooks fire: the FIRST tool result of the session
     carries the NAVIGATION TIP and the 💡 TA: digest (feature_023 F14c live
     path; post meta_harness_dsl R2 both are emitted from ONE sessionBootstrap
     in the enforcer composition root, digest machinery in omt_shared.ts,
     injected on the first result of ANY tool, no exclusions).

Scope history: this suite previously pinned 13 guard behaviors live (BUG-A/BUG-B
before-hook edit guards, think-gate, TDD two-hats, MVC++ gate, phase
transitions, omt_skip scopes, per-file consult granularity, session isolation)
across 17 tests / ~22 real opencode runs (several minutes). Reduced to the
minimal smoke ("plugins load and work") by directive: guard behavior is pinned
STATICALLY by test_omt_enforcer_guard_source_pins.py (before/after-hook source
contract) + test_opencode_sdk_contract.py (SDK d.ts contract), and the
real-binary probing recipes (BUG-B git-dirty-first receipt-guard probe,
--pure A/B control, --print-logs bootstrap audit) are preserved in the WORK.md
agent scratchpad should a full live guard pass ever be needed again.

Cost: ONE real LLM round-trip (~30–60 s). Marked `opencode_live`; skipped when
the opencode binary is absent. The prompt forbids edits, so the run is
side-effect free (omt_skip scope=nav affects only the throwaway session).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
OPENCODE = shutil.which("opencode")
OPENCODE_BIN = OPENCODE or "opencode"  # skipif guards the None case

pytestmark = [
    pytest.mark.skipif(not OPENCODE, reason="opencode binary not available"),
    pytest.mark.opencode_live,
]

TIMEOUT = 240

# One tool per plugin: omt_status / omt_nav / omt_think / omt_enforcer.
PLUGIN_TOOLS = ("omt_status", "omt_list_sections", "omt_think_list", "omt_skip")


def _run_opencode(prompt: str, *extra: str) -> tuple[int, list[dict], str]:
    """One real headless run; returns (exit, parsed json events, stderr)."""
    proc = subprocess.run(
        [OPENCODE_BIN, "run", "--format", "json", *extra, prompt],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=TIMEOUT,
    )
    events = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return proc.returncode, events, proc.stderr


def _tool_uses(events: list[dict]) -> list[dict]:
    return [e["part"] for e in events
            if e.get("type") == "tool_use" and isinstance(e.get("part"), dict)]


def _tool_output(part: dict) -> str:
    state = part.get("state") or {}
    return str(state.get("output") or state.get("error") or "")


def test_plugins_load_and_tools_execute():
    """Minimal live smoke: one real run calling one tool per plugin.

    Proves plugins auto-load and register their tools in the real runtime,
    the tools execute to completion, omt_status returns its real banner, and
    the tool.execute.after hooks inject the nav reminder + TA digest into the
    first tool result (F14c live path — injection is on the first result of
    ANY tool, so whatever the agent happens to call first carries both).
    """
    code, events, stderr = _run_opencode(
        "Call exactly these 4 tools in order, then reply DONE: "
        "1) omt_status 2) omt_list_sections 3) omt_think_list "
        "4) omt_skip with reason 'live smoke' and scope 'nav'. "
        "Do not edit any files. Do not call any other tool.")
    assert code == 0, f"opencode run failed (exit {code}): {stderr[-500:]!r}"

    uses = _tool_uses(events)
    seen = [p.get("tool") for p in uses]
    for name in PLUGIN_TOOLS:
        calls = [p for p in uses if p.get("tool") == name]
        assert calls, (
            f"{name} was never called — its plugin did not load/register in "
            f"the real runtime? tools seen: {seen}")
        state = calls[0].get("state") or {}
        assert state.get("status") == "completed", (
            f"{name} did not complete successfully: {state}")

    status_out = _tool_output(
        [p for p in uses if p.get("tool") == "omt_status"][0])
    assert "OMT++ STATUS" in status_out, (
        f"omt_status output wrong: {status_out[:200]!r}")

    # After-hooks fire (F14c): the first tool result carries both injections.
    assert uses, "no tool calls at all — plugins and built-ins both silent?"
    first_out = _tool_output(uses[0])
    assert "NAVIGATION TIP" in first_out, (
        "omt_enforcer after-hook nav reminder missing from the first tool "
        f"result ({uses[0].get('tool')}): {first_out[:300]!r}")
    assert "💡 TA:" in first_out, (
        "omt_think after-hook TA digest missing from the first tool "
        f"result ({uses[0].get('tool')}): {first_out[:300]!r}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
