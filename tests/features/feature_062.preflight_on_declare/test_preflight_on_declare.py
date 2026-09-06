"""Wave 0/P0-1 preflight-on-declare — feature_062.

Contract:
- The omt_phase success response embeds the A4 preflight projection for the
  feature's own edit surfaces: tests-dir probe on Programming AND Testing,
  plus a src probe at Programming — ordered gates + clearing actions, the
  declared phase already visible (g.phase fires ✓), live session state
  (g.kb honest about consults), inert $ (dry net verdict).
- FAIL-OPEN: no feature / no edit phase (Analysis/Design/abandon/unspecified)
  → no embed; an embed error never fails the declare.
- Shared home: the projection core lives in lib/enforcer/preflight.ts,
  consumed by BOTH omt_status{op:"preflight"} (unchanged A4 op) and the
  declare embed; read-only, no ledger writes, no self think-gate literal.

Bun probes exercise the REAL TS modules (test_omt_q.py idiom): hermetic
ledger via OMT_LEDGER_PATH (process-level override — GOTCHA feature_051),
real IR + nav index via cwd=REPO_ROOT (REPO_ROOT → process.cwd() pre-init).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts"
SESSION_STATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "session_state.ts"
PREFLIGHT_LIB = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "preflight.ts"
STATUS_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts"

BUN = shutil.which("bun")

F = "feature_062.preflight_on_declare"


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


# --- declare-embed probe (createPhaseTools → omt_phase) ------------------------

_DECLARE_PROBE = """
import { writeFileSync } from "node:fs"
import { createPhaseTools } from "%PG%"
import { createSessionState } from "%SS%"
const env: any = { client: undefined, $: undefined, directory: process.cwd()!,
  state: createSessionState(), safeLog: () => {}, notify: async () => {} }
writeFileSync(process.env.OMT_LEDGER_PATH!, "")
const { omt_phase } = createPhaseTools(env)
const F = "%F%"
const r: Record<string, string> = {}
r.prog = String(await omt_phase.execute({ task_type: "minor_feature", phase: "Programming",
  scope: "s", feature: F }, { sessionID: "s1" }))
r.testing = String(await omt_phase.execute({ task_type: "minor_feature", phase: "Testing",
  scope: "s", feature: F }, { sessionID: "s1" }))
r.nofeature = String(await omt_phase.execute({ task_type: "minor_feature", phase: "Programming",
  scope: "s" }, { sessionID: "s1" }))
r.design = String(await omt_phase.execute({ task_type: "minor_feature", phase: "Design",
  scope: "s", feature: F }, { sessionID: "s1" }))
r.abandon = String(await omt_phase.execute({ task_type: "minor_feature", phase: "abandoned",
  scope: "abandon Design: done", feature: F }, { sessionID: "s1" }))
console.log(JSON.stringify(r))
"""


class TestDeclareEmbed:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_programming_embeds_both_probes(self, tmp_path: Path) -> None:
        out = _run_probe(tmp_path, _DECLARE_PROBE
                         .replace("%PG%", PHASE_GATE.as_posix())
                         .replace("%SS%", SESSION_STATE.as_posix())
                         .replace("%F%", F), cwd=REPO_ROOT)
        prog = out["prog"]
        # Baseline PROCESS CHECK + unlock line preserved.
        assert "📋 OMT++ PROCESS CHECK (recorded)" in prog
        assert "✅ src/ edits unlocked for this session" in prog
        # Test-dir probe: canary gate + clearing action.
        assert (f"🛫 OMT++ PREFLIGHT — edit tests/features/{F}/test_probe.py"
                in prog), prog
        assert "g.tests — WOULD BLOCK" in prog
        assert 'clear: omt_skip{reason:"approved canary test", scope:"tests"}' in prog
        # Src probe (Programming only): g.kb consult + phase already visible.
        assert "🛫 OMT++ PREFLIGHT — edit src/feature_probe.py" in prog
        assert "g.kb — WOULD BLOCK" in prog
        assert "omt_kb_nav" in prog
        assert "g.phase — fires ✓" in prog

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_phase_scoping_and_fail_open(self, tmp_path: Path) -> None:
        out = _run_probe(tmp_path, _DECLARE_PROBE
                         .replace("%PG%", PHASE_GATE.as_posix())
                         .replace("%SS%", SESSION_STATE.as_posix())
                         .replace("%F%", F), cwd=REPO_ROOT)
        # Testing: test-dir probe only, no src probe.
        t = out["testing"]
        assert f"🛫 OMT++ PREFLIGHT — edit tests/features/{F}/test_probe.py" in t
        assert "src/feature_probe.py" not in t
        # No feature → no embed.
        assert "🛫" not in out["nofeature"]
        # Non-edit phase (Design) → no embed.
        assert "🛫" not in out["design"]
        # Abandon tombstone early-return → no embed.
        assert "🛫" not in out["abandon"]


# --- parity probe: op=preflight still wired after the move ----------------------

_PARITY_PROBE = """
import { writeFileSync } from "node:fs"
writeFileSync(process.env.OMT_LEDGER_PATH!, "")
const plugin = await (await import("%STATUS%")).default({ directory: process.cwd(), worktree: process.cwd() })
const res = await plugin.tool.omt_status.execute({ op: "preflight", tool: "grep", path: ".meta/META_HARNESS.omt" }, { sessionID: "s2" })
console.log(JSON.stringify({ output: res.output ?? res }))
"""


class TestParity:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_op_preflight_still_wired(self, tmp_path: Path) -> None:
        out = _run_probe(tmp_path, _PARITY_PROBE
                         .replace("%STATUS%", STATUS_PLUGIN.as_posix()),
                         cwd=REPO_ROOT)
        text = out["output"] if isinstance(out["output"], str) else json.dumps(out)
        assert "🛫 OMT++ PREFLIGHT — grep .meta/META_HARNESS.omt" in text, text
        # grep on a doc path w/o nav → g.nav blocks (clearing action shown).
        assert "g.nav — WOULD BLOCK" in text, text


# --- static wiring pins --------------------------------------------------------

class TestStaticPins:
    def test_phase_gate_embed_wiring(self) -> None:
        src = PHASE_GATE.read_text(encoding="utf-8")
        assert 'await preflightProjection(t, "edit", session' in src
        assert "feature_062.preflight_on_declare" in src

    def test_preflight_lib_shared_home(self) -> None:
        src = PREFLIGHT_LIB.read_text(encoding="utf-8")
        assert "export async function preflightProjection" in src
        assert "export function preflightLines" in src
        assert "PREFLIGHT_DEFAULT_TOOL" in src
        # Read-only + no self think-gate literal (A4 posture inherited).
        assert "writeLedger" not in src and "appendLedger" not in src
        assert "TA:" not in src

    def test_omt_status_is_thin_consumer(self) -> None:
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        assert "lib/enforcer/preflight" in src, (
            "omt_status must import the shared projection core")
        assert 'op === "preflight"' in src, (
            "the op=preflight branch must remain in omt_status.ts")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])