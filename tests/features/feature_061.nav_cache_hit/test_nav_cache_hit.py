"""Wave 0/P0-4 nav-cache-hit — feature_061.

Contract:
- The g.nav denial for a blocked doc-scoped grep/glob appends the top-3 nav
  index hits for the query stem (message-only: verdict, policy and the IR
  nav_required text are unchanged).
- Fail-open: no usable stem / no index hits → the block text is
  byte-identical to the pre-P0-4 denial (no 📎 line).
- Policy untouched: after a nav tool is used the same search is allowed.

Bun probes exercise the REAL TS modules (test_omt_q.py idiom): hermetic
ledger via OMT_LEDGER_PATH (process-level override — GOTCHA feature_051),
real nav index via cwd=REPO_ROOT (REPO_ROOT falls back to process.cwd()
pre-init, omt_shared.ts header).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
NAV_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "nav_gate.ts"
GATE_DRIVER = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "gate_driver.ts"
SESSION_STATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "session_state.ts"

BUN = shutil.which("bun")

# Index fixtures verified against .meta/.omt/nav.index.jsonl at authoring
# time: "dangling" 2 records, "budget" 2, "tdd" 26, "zzzqqqxxx" 0 (miss).
# Block-severity @msg records (e.g. receipt_stale) are NOT nav-indexed —
# only err_*/wrn_* severity are — so fixtures must use indexed words.


def _run_probe(tmp_path: Path, body: str, cwd: Path | None = None) -> dict:
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    ledger = tmp_path / "ledger.jsonl"
    probe = tmp_path / "probe.ts"
    probe.write_text(body, encoding="utf-8")
    env = {**os.environ, "OMT_LEDGER_PATH": str(ledger)}
    out = subprocess.run([BUN, str(probe)], capture_output=True, text=True,
                         timeout=90, cwd=str(cwd or tmp_path), env=env)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


# --- unit probe: searchQueryStem + navCacheHint (pure functions) ---------------

_UNIT_PROBE = """
import { searchQueryStem, navCacheHint } from "%NAV_GATE%"
const out = {
  stem_regex: searchQueryStem({ args: { pattern: "^##* SECTION:" } }),
  stem_ident: searchQueryStem({ args: { pattern: "receipt_stale" } }),
  stem_array: searchQueryStem({ args: { pattern: ["g.nav", 7] } }),
  stem_none: searchQueryStem({ args: { path: ".meta" } }),
  hint_full: navCacheHint({ args: { pattern: "dangling" } }),
  hint_word: navCacheHint({ args: { pattern: "budget ceremony meter" } }),
  hint_cap: navCacheHint({ args: { pattern: "tdd" } }),
  hint_miss: navCacheHint({ args: { pattern: "zzzqqqxxx_nothing" } }),
  hint_noargs: navCacheHint({}),
}
console.log(JSON.stringify(out))
"""


class TestUnitProbe:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_stem_extraction(self, tmp_path: Path) -> None:
        out = _run_probe(tmp_path, _UNIT_PROBE
                         .replace("%NAV_GATE%", NAV_GATE.as_posix()),
                         cwd=REPO_ROOT)
        # Regex noise stripped: anchors/classes/quantifiers become spaces.
        assert out["stem_regex"] == "section", out
        # Identifiers survive (underscores kept).
        assert out["stem_ident"] == "receipt_stale", out
        # Array args coerce to the first string (DEFECT B posture).
        assert out["stem_array"] == "g nav", out
        # No pattern-ish arg → null (hint stays absent).
        assert out["stem_none"] is None, out

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_hint_build(self, tmp_path: Path) -> None:
        out = _run_probe(tmp_path, _UNIT_PROBE
                         .replace("%NAV_GATE%", NAV_GATE.as_posix()),
                         cwd=REPO_ROOT)
        # Full-stem hit: header + ≤3 hit lines from the real index.
        full = out["hint_full"]
        assert full is not None, out
        assert full.startswith("📎 nav index hits for 'dangling':"), full
        lines = full.splitlines()
        assert 2 <= len(lines) <= 4, full  # header + 1..3 hits (index has 2)
        assert all(":" in ln and ln.startswith("  ") for ln in lines[1:]), full
        # Word fallback: full stem misses, longest word with hits wins —
        # "ceremony" has 0 index records, "budget" has 2.
        word = out["hint_word"]
        assert word is not None, out
        assert word.startswith("📎 nav index hits for 'budget ceremony meter':"), word
        # Top-3 cap: "tdd" has 26 index records — exactly 3 hit lines.
        cap = out["hint_cap"]
        assert cap is not None, out
        assert len(cap.splitlines()) == 4, cap
        # Fail-open: no hits / no args → null (byte-identical denial).
        assert out["hint_miss"] is None, out
        assert out["hint_noargs"] is None, out


# --- chain probe: the REAL before-chain (gate_driver runBeforeGates) ----------

_CHAIN_PROBE = """
import { writeFileSync } from "node:fs"
import { runBeforeGates } from "%DRIVER%"
import { navTrack } from "%NAV_GATE%"
import { createSessionState, OmtBlock } from "%SS%"
const env: any = { client: undefined, $: undefined, directory: process.cwd()!,
  state: createSessionState(), safeLog: () => {}, notify: async () => {} }
writeFileSync(process.env.OMT_LEDGER_PATH!, "")
async function call(tool: string, args: any): Promise<string> {
  try {
    await runBeforeGates(env, "s1", { tool }, { args }, null)
    return "allow"
  } catch (e) {
    return e instanceof OmtBlock ? "block:" + e.message : "error:" + String(e)
  }
}
const out: Record<string, string> = {}
out.blocked_with_hint = await call("grep", { pattern: "dangling", path: ".meta/META_HARNESS.omt" })
out.blocked_no_hint = await call("grep", { pattern: "zzzqqqxxx_nothing", path: ".meta/META_HARNESS.omt" })
await navTrack(env, "s1", { tool: "omt_nav" })
out.allowed_after_nav = await call("grep", { pattern: "dangling", path: ".meta/META_HARNESS.omt" })
console.log(JSON.stringify(out))
"""


class TestChainProbe:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_before_chain_message_only(self, tmp_path: Path) -> None:
        out = _run_probe_p4(tmp_path)
        # Blocked doc search WITH index hits: denial + appended hint.
        with_hint = out["blocked_with_hint"]
        assert with_hint.startswith("block:"), out
        assert "omt_nav" in with_hint, out          # IR nav_required text intact
        assert "📎 nav index hits for 'dangling':" in with_hint, with_hint
        # Blocked doc search with NO hits: byte-identical pre-P0-4 denial.
        no_hint = out["blocked_no_hint"]
        assert no_hint.startswith("block:"), out
        assert "omt_nav" in no_hint, out
        assert "📎" not in no_hint, no_hint
        # Policy untouched: nav use still allows the same search.
        assert out["allowed_after_nav"] == "allow", out


def _run_probe_p4(tmp_path: Path) -> dict:
    body = (_CHAIN_PROBE
            .replace("%DRIVER%", GATE_DRIVER.as_posix())
            .replace("%NAV_GATE%", NAV_GATE.as_posix())
            .replace("%SS%", SESSION_STATE.as_posix()))
    return _run_probe(tmp_path, body, cwd=REPO_ROOT)


# --- static wiring pins --------------------------------------------------------

class TestStaticPins:
    def test_gate_driver_appends_hint(self) -> None:
        src = GATE_DRIVER.read_text(encoding="utf-8")
        assert "navCacheHint(ctx.output)" in src, (
            "g.nav impl must append navCacheHint (P0-4 wiring)")
        assert 'gateMsg("nav_required")' in src, (
            "the IR @msg text stays the denial source (P0-4 is message-only)")

    def test_nav_gate_exports(self) -> None:
        src = NAV_GATE.read_text(encoding="utf-8")
        assert "export function searchQueryStem" in src
        assert "export function navCacheHint" in src
        assert "loadNavIndex" in src, "hint reads the compiled nav index"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
