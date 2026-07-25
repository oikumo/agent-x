"""
Harness-level contract pin: opencode plugin SDK tool.execute hook shapes
(feature_023 Tier 2 — mechanize the F14 meta-lesson).

F14 (analysis_001_f14_contract_pinning.md): the enforcer's tool.execute.after
read `output.args` — a key that NEVER existed in ANY SDK version (1.1.12 …
1.17.11) — so the read-injection AND the MVC++ post-edit gate were dead since
shipment, while runner fixtures fabricated the same wrong shape and kept every
test green. This module pins the two links that must never drift apart again:

  1. Shape pin   — the INSTALLED SDK d.ts declares:
                     tool.execute.before: input={tool,sessionID,callID} (NO args),
                                          output={args}
                     tool.execute.after:  input={tool,sessionID,callID,args},
                                          output={title,output,metadata} (NO args)
  2. Version pin — .opencode/package.json's declared @opencode-ai/plugin
                   version == the installed node_modules version (drift alarm
                   on SDK upgrade).

The F14 meta-lesson (feature_023.test_refactor_live_only / REFACTOR_PLAN_v2):
runner fixtures fabricate the SDK shapes the buggy code expects and stay green
while the real runtime drifts. The deleted feature_022 fixture-pinning class
(TestFixturePin) pinned the fixtures themselves; with the fixtures removed by
the v2 refactor, that 3rd pin is obsolete. The after-hook contract is now
pinned LIVE by test_omt_live_opencode_guards.py::test_nav_reminder_and_think_digest_on_first_tool_result
(F14c live path — real opencode binary drives the hook). The before-hook
contract is pinned LIVE by test_omt_live_opencode_guards.py::test_protected_file_edit_blocked_without_unlock
(BUG-A regression). Both live tests fail on the real buggy runtime — the
mechanization the fixture pins failed to provide.

Runtime truth (ground the d.ts pin proxies): binary audit of the installed
opencode-linux-x64 1.18.3 (`grep -ao 'trigger("[a-z._]*"'`) yields exactly 16
dispatched hook names — chat.message, chat.params, chat.headers,
command.execute.before, tool.execute.before (×7 call sites),
tool.execute.after (×7), shell.env, tool.definition, file.open (×2), tab.new,
and 5 experimental.* — and `session.start` is NOT among them. After-hook call
sites dispatch trigger("tool.execute.after", {tool,sessionID,callID,args},
{title,metadata,output}) — args on INPUT, exactly as the d.ts types say
(analysis_001 addendum, F14c).

skipif: the whole module skips when node_modules is absent (CI without npm i)
— the pin targets the installed environment, not a vendored snapshot.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
DTS = REPO_ROOT / ".opencode" / "node_modules" / "@opencode-ai" / "plugin" / "dist" / "index.d.ts"
PKG = REPO_ROOT / ".opencode" / "package.json"
INSTALLED_PKG = REPO_ROOT / ".opencode" / "node_modules" / "@opencode-ai" / "plugin" / "package.json"

pytestmark = pytest.mark.skipif(not DTS.exists(), reason="plugin SDK not installed (npm i not run)")


def _hook_blocks(hook: str) -> tuple[str, str]:
    """Extract the (input, output) type blocks of a Hooks entry from the d.ts."""
    dts = DTS.read_text(encoding="utf-8")
    m = re.search(
        r'"' + re.escape(hook) + r'"\?:\s*\(input:\s*\{(?P<input>[^}]*)\},\s*'
        r'output:\s*\{(?P<output>[^}]*)\}\)\s*=>',
        dts, re.DOTALL)
    assert m, f'"{hook}" not found in installed d.ts — Hooks interface drifted?'
    return m.group("input"), m.group("output")


class TestHookShapePin:
    def test_before_hook_args_on_output(self):
        """tool.execute.before: input carries NO args; output carries args."""
        inp, out = _hook_blocks("tool.execute.before")
        assert not re.search(r"\bargs\b", inp), (
            f"before-hook input must NOT carry args (contract drift): {inp!r}")
        assert re.search(r"\bargs\b", out), (
            f"before-hook output MUST carry args (contract drift): {out!r}")

    def test_after_hook_args_on_input(self):
        """tool.execute.after: input carries args; output is exactly
        {title, output, metadata} with NO args (the F14 contract)."""
        inp, out = _hook_blocks("tool.execute.after")
        assert re.search(r"\bargs\b", inp), (
            f"after-hook input MUST carry args (contract drift): {inp!r}")
        assert not re.search(r"\bargs\b", out), (
            f"after-hook output must NOT carry args (the F14 defect class): {out!r}")
        for key in ("title", "output", "metadata"):
            assert re.search(r"\b" + key + r"\b", out), (
                f"after-hook output missing {key!r} (contract drift): {out!r}")


class TestVersionPin:
    def test_declared_version_matches_installed(self):
        """Drift alarm: .opencode/package.json's declared SDK version must
        equal the installed node_modules version. On SDK upgrade this fails
        until the contract is re-reviewed (F14 lesson)."""
        declared = json.loads(PKG.read_text(encoding="utf-8"))["dependencies"]["@opencode-ai/plugin"]
        installed = json.loads(INSTALLED_PKG.read_text(encoding="utf-8"))["version"]
        assert declared == installed, (
            f"SDK drift: package.json declares {declared}, node_modules has {installed} — "
            "re-review the tool.execute contract before bumping")


# Note: TestFixturePin removed in feature_023.test_refactor_live_only (v2 refactor).
# It pinned the deleted feature_022 fixture files (test_omt_think_v2_tier_{bd,c}.py)
# which fabricated SDK hook shapes — exactly the F14 meta-lesson: runner fixtures
# stay green while the real runtime drifts. The after/before-hook contracts are
# now pinned LIVE by test_omt_live_opencode_guards.py (F14c + BUG-A tests).


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
