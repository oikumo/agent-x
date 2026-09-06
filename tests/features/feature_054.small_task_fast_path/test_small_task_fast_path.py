"""Wave 2/C2 small_task_fast_path — feature_054.

Contract (GREEN pins the implementation):
- FAST PATH: a bug_fix/test omt_phase record satisfies g.nav+g.kb in ONE
  write (ledger record is the single mechanism — no in-memory flag flip);
  stays HARD for minor/major/new_screen (latest-phase-wins: a later
  non-fast-path declaration turns it off).
- NARROWED CANARY: tests/ canary auto-approves ONLY the declared feature's
  own test dir (tests/features/<feature>/, full slug or feature_NNN short
  form) while its feature-scoped TDD RED is active; bootstrap (testlist/no
  RED) and every other tests/ path still require the explicit canary skip.
- GUARDRAILS: g.think/g.protect untouched (pinned: their @gate lines carry
  no C2 change; receipt_guard gains no think/protect logic).

Bun probes exercise the REAL TS modules (test_omt_q.py idiom): hermetic
ledger via OMT_LEDGER_PATH (process-level override — GOTCHA from
feature_051), real IR + net sidecar for the full before-chain probe.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
OMT = REPO_ROOT / ".meta" / "META_HARNESS.omt"
SESSION_STATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "session_state.ts"
GATE_DRIVER = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "gate_driver.ts"
RECEIPT_GUARD = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "receipt_guard.ts"
PHASE_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts"

BUN = shutil.which("bun")

F = "feature_054.small_task_fast_path"


# --- ledger record builders ---------------------------------------------------

def _ts(hours_ago: float = 0.0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def _phase(tt: str, session: str = "s1", feature: str = "", tdd: bool = False,
           hours_ago: float = 0.0) -> dict:
    return {"ts": _ts(hours_ago), "kind": "phase", "session": session,
            "task_type": tt, "phase": "Programming", "scope": "c2 test",
            "feature": feature, "design_doc": "", "tdd_mode": tdd}


def _tdd(state: str, session: str = "s1", feature: str = F,
         hours_ago: float = 0.0) -> dict:
    return {"ts": _ts(hours_ago), "kind": "tdd", "session": session,
            "state": state, "test_node": "tests/features/x/test_x.py::T::t",
            "verified": True, "exit_code": 1, "feature": feature}


def _testlist(session: str = "s1", feature: str = F) -> dict:
    return {"ts": _ts(), "kind": "tdd_testlist", "session": session,
            "behaviors": ["b1"], "remaining": ["b1"], "feature": feature}


def _skip(scope: str = "tests", session: str = "s1") -> dict:
    return {"ts": _ts(), "kind": "skip", "session": session,
            "reason": "canary", "scope": scope,
            "tests_approved": scope in ("tests", "all")}


# --- bun probe plumbing -------------------------------------------------------

def _run_probe(tmp_path: Path, body: str, cwd: Path | None = None,
               extra_env: dict | None = None) -> dict:
    """Write body to tmp/probe.ts, run bun with a hermetic ledger env."""
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    ledger = tmp_path / "ledger.jsonl"
    probe = tmp_path / "probe.ts"
    probe.write_text(body, encoding="utf-8")
    env = {**os.environ, "OMT_LEDGER_PATH": str(ledger),
           **(extra_env or {})}
    out = subprocess.run([BUN, str(probe)], capture_output=True, text=True,
                         timeout=90, cwd=str(cwd or tmp_path), env=env)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


# --- static pins (guardrails + wiring) ----------------------------------------

class TestStaticPins:
    def test_static_omt_gate_notes_carry_c2(self) -> None:
        omt = OMT.read_text(encoding="utf-8")
        for line_id in ("g.nav", "g.kb"):
            line = next(ln for ln in omt.splitlines() if ln.startswith(f"@gate {line_id}"))
            assert "C2: bug_fix/test phase auto-satisfies" in line, (
                f"{line_id} must document the C2 fast path")
        tests_line = next(ln for ln in omt.splitlines()
                          if ln.startswith("@gate g.tests"))
        assert "C2: own test dir auto-approved in RED" in tests_line

    def test_static_think_protect_gates_untouched(self) -> None:
        """C2 MUST NOT touch g.think/g.protect — their @gate lines carry no
        C2 change and keep their original skip semantics."""
        omt = OMT.read_text(encoding="utf-8")
        think = next(ln for ln in omt.splitlines() if ln.startswith("@gate g.think"))
        protect = next(ln for ln in omt.splitlines() if ln.startswith("@gate g.protect"))
        assert "C2" not in think and "C2" not in protect
        assert "NOT skip-bypassable" in think  # original semantics intact
        assert "skip_ok=true" in protect

    def test_static_tdd_bootstrap_doc_narrowed(self) -> None:
        omt = OMT.read_text(encoding="utf-8")
        doc = next(ln for ln in omt.splitlines()
                   if ln.startswith("@doc tdd.bootstrap"))
        assert "narrowed C2 auto-unlock" in doc
        assert "blanket auto-unlock REJECTED" in doc

    def test_static_phase_gate_single_mechanism(self) -> None:
        """omt_phase documents the fast path but flips NO in-memory flags —
        the ledger record is the single mechanism (sticky flags would bypass
        g.kb after a later major_feature declaration)."""
        src = PHASE_GATE.read_text(encoding="utf-8")
        assert "feature_054 C2 small_task_fast_path" in src
        assert "state.nav.get(session)" not in src
        assert "state.kb.get(session)" not in src

    def test_static_session_state_fast_path_types(self) -> None:
        src = SESSION_STATE.read_text(encoding="utf-8")
        assert 'new Set(["bug_fix", "test"])' in src, (
            "FAST_PATH_TASK_TYPES must be exactly bug_fix+test")
        assert "export function hasFastPathUnlock" in src

    def test_static_gate_driver_wiring_pins(self) -> None:
        src = GATE_DRIVER.read_text(encoding="utf-8")
        # SESSION_FLAGS predicates (g.kb generic path) …
        assert "hasFastPathUnlock(ctx.session)" in src
        # … AND the g.nav impl (which bypasses requires=) must consult it too.
        assert "hasNavUnlock(ctx.session) || hasFastPathUnlock(ctx.session)" in src

    def test_static_receipt_guard_branch_pins(self) -> None:
        src = RECEIPT_GUARD.read_text(encoding="utf-8")
        for marker in ("isOwnTestDir", "isFeatureRedActive", "activeFeatureFor",
                       "C2 fast-path: own test dir"):
            assert marker in src, f"receipt_guard.ts missing {marker}"
        # C2 added no think/protect logic to the tests guard.
        assert "guardThoughts" not in src and "think_gate" not in src


# --- probe A: hasFastPathUnlock (session_state.ts, real module) ---------------

_A_PROBE = """
import { writeFileSync } from "node:fs"
import { hasFastPathUnlock } from "%SS%"
const ledger = process.env.OMT_LEDGER_PATH!
const cases: Record<string, any[]> = %CASES%
const out: Record<string, boolean> = {}
for (const [name, recs] of Object.entries(cases)) {
  writeFileSync(ledger, recs.map((r: any) => JSON.stringify(r)).join("\\n") + "\\n")
  out[name] = hasFastPathUnlock("s1")
}
console.log(JSON.stringify(out))
"""


class TestHasFastPathUnlockBun:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_unlock_latest_phase_wins_matrix(self, tmp_path) -> None:
        cases = {
            "bug_fix_mine": [_phase("bug_fix")],
            "test_mine": [_phase("test")],
            "minor_mine": [_phase("minor_feature")],
            "major_mine": [_phase("major_feature")],
            "refactor_mine": [_phase("refactor")],
            "docs_mine": [_phase("docs")],
            "empty_ledger": [],
            # window fallback: other session, fresh vs stale record
            "other_session_fresh": [_phase("bug_fix", session="s2")],
            "other_session_stale": [_phase("bug_fix", session="s2", hours_ago=9)],
            # latest-phase-wins: a later declaration shadows the fast path
            "later_minor_shadows": [_phase("bug_fix"), _phase("minor_feature")],
            "later_bug_fix_wins": [_phase("minor_feature"), _phase("bug_fix")],
            # skips are not the authority for the fast path
            "skip_not_authority": [_phase("bug_fix"), _skip("tests")],
        }
        out = _run_probe(tmp_path, _A_PROBE
                         .replace("%SS%", str(SESSION_STATE))
                         .replace("%CASES%", json.dumps(cases)))
        assert out == {
            "bug_fix_mine": True, "test_mine": True,
            "minor_mine": False, "major_mine": False,
            "refactor_mine": False, "docs_mine": False,
            "empty_ledger": False,
            "other_session_fresh": True, "other_session_stale": False,
            "later_minor_shadows": False, "later_bug_fix_wins": True,
            "skip_not_authority": True,
        }, f"hasFastPathUnlock matrix mismatch: {out}"


# --- probe B: guardTestsPath narrowed canary (receipt_guard.ts) ---------------

_B_PROBE = """
import { writeFileSync } from "node:fs"
import { guardTestsPath } from "%RG%"
import { createSessionState, OmtBlock } from "%SS%"
// Mock $: answers the tddGateCheck shell-out (testlist/green hats deny the
// tests/ edit — the real engine's verdict for those states).
const chain: any = { cwd: () => chain, quiet: () => chain, nothrow: () => chain,
  stdout: { toString: () => JSON.stringify({ allowed: false,
    reason: "⛔ TDD two-hats (mock): the current hat denies this tests/ edit" }) } }
const env: any = { client: undefined, $: (s: any, ...v: any[]) => chain,
  directory: ".", state: createSessionState(), safeLog: () => {}, notify: async () => {} }
const ledger = process.env.OMT_LEDGER_PATH!
const scenarios: Record<string, { recs: any[]; rels: string[] }> = %SCENARIOS%
const out: Record<string, Record<string, string>> = {}
for (const [name, sc] of Object.entries(scenarios)) {
  writeFileSync(ledger, sc.recs.map((r: any) => JSON.stringify(r)).join("\\n") + "\\n")
  const verdicts: Record<string, string> = {}
  for (const rel of sc.rels) {
    try { await guardTestsPath(env, "s1", rel); verdicts[rel] = "allow" }
    catch (e) { verdicts[rel] = e instanceof OmtBlock ? "block" : "error:" + String(e) }
  }
  out[name] = verdicts
}
console.log(JSON.stringify(out))
"""

_OWN = f"tests/features/{F}/test_a.py"
_OWN_SHORT = "tests/features/feature_054/test_d.py"
_OTHER = "tests/features/feature_999.other/test_b.py"
_HARNESS = "tests/scripts/omt/test_c.py"
_EVIL = "tests/features/feature_054evil/test_e.py"


class TestNarrowedCanaryBun:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_canary_scenarios(self, tmp_path) -> None:
        advance = [_phase("minor_feature", feature=F, tdd=True), _tdd("red"),
                   _phase("Testing", feature=F)]  # tdd-less advance record
        scenarios = {
            # THE value case: mid-TDD Programming→Testing advance (tdd-less
            # phase record) must not strand own-dir test edits during RED.
            "advance_red_allows_own_dir": {
                "recs": advance,
                "rels": [_OWN, _OWN_SHORT, _OTHER, _HARNESS, _EVIL]},
            "testlist_no_red_blocks": {
                "recs": [_phase("minor_feature", feature=F, tdd=True), _testlist()],
                "rels": [_OWN]},
            "green_supersedes_red_blocks": {
                "recs": [_phase("minor_feature", feature=F, tdd=True),
                         _tdd("red"), _tdd("green")],
                "rels": [_OWN]},
            "no_feature_context_blocks": {
                "recs": [_phase("bug_fix")],  # feature "" → no C2 scope
                "rels": [_OWN]},
            "empty_ledger_blocks": {"recs": [], "rels": [_OWN]},
            # legacy path intact: an explicit tests-canary skip still allows.
            "skip_tests_still_allows": {
                "recs": [_phase("minor_feature", feature=F, tdd=True),
                         _tdd("red"), _skip("tests")],
                "rels": [_OWN]},
        }
        out = _run_probe(tmp_path, _B_PROBE
                         .replace("%RG%", str(RECEIPT_GUARD))
                         .replace("%SS%", str(SESSION_STATE))
                         .replace("%SCENARIOS%", json.dumps(scenarios)))
        assert out["advance_red_allows_own_dir"] == {
            _OWN: "allow", _OWN_SHORT: "allow",
            _OTHER: "block", _HARNESS: "block", _EVIL: "block"}, out
        assert out["testlist_no_red_blocks"][_OWN] == "block"
        assert out["green_supersedes_red_blocks"][_OWN] == "block"
        assert out["no_feature_context_blocks"][_OWN] == "block"
        assert out["empty_ledger_blocks"][_OWN] == "block"
        assert out["skip_tests_still_allows"][_OWN] == "allow"


# --- probe C: full before-chain (gate_driver.ts runBeforeGates) ---------------

_C_PROBE = """
import { writeFileSync } from "node:fs"
import { runBeforeGates } from "%GD%"
import { createSessionState, OmtBlock } from "%SS%"
const env: any = { client: undefined, $: undefined, directory: process.env.C2_REPO_ROOT!,
  state: createSessionState(), safeLog: () => {}, notify: async () => {} }
const ledger = process.env.OMT_LEDGER_PATH!
const scenarios: Record<string, any[]> = %SCENARIOS%
const out: Record<string, Record<string, string>> = {}
for (const [name, recs] of Object.entries(scenarios)) {
  writeFileSync(ledger, recs.map((r: any) => JSON.stringify(r)).join("\\n") + "\\n")
  const verdicts: Record<string, string> = {}
  for (const call of [
    ["nav", { tool: "grep" }, { args: { path: ".meta/META_HARNESS.omt" } }, null],
    ["kb", { tool: "edit" }, { args: { filePath: "src/agentx/__init__.py" } },
      "src/agentx/__init__.py"],
  ] as const) {
    const [tag, input, output, raw] = call as any
    try {
      await runBeforeGates(env, "s1", input, output, raw)
      verdicts[tag] = "allow"
    } catch (e) {
      verdicts[tag] = e instanceof OmtBlock ? "block:" + e.message.slice(0, 200) : "error:" + String(e)
    }
  }
  out[name] = verdicts
}
console.log(JSON.stringify(out))
"""


class TestGateChainBun:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_before_chain_fast_path(self, tmp_path) -> None:
        scenarios = {
            "bug_fix_phase": [_phase("bug_fix")],
            "minor_feature_phase": [_phase("minor_feature")],
            "empty_ledger": [],
        }
        out = _run_probe(tmp_path, _C_PROBE
                         .replace("%GD%", str(GATE_DRIVER))
                         .replace("%SS%", str(SESSION_STATE))
                         .replace("%SCENARIOS%", json.dumps(scenarios)),
                         cwd=REPO_ROOT,
                         extra_env={"C2_REPO_ROOT": str(REPO_ROOT)})
        # bug_fix: ONE phase write satisfies g.nav (doc search) AND g.kb
        # (src edit) through the REAL gate chain.
        assert out["bug_fix_phase"]["nav"] == "allow", out
        assert out["bug_fix_phase"]["kb"] == "allow", out
        # minor_feature stays hard on both gates.
        assert out["minor_feature_phase"]["nav"].startswith("block"), out
        assert "omt_nav" in out["minor_feature_phase"]["nav"], out
        assert out["minor_feature_phase"]["kb"].startswith("block"), out
        assert "g.kb" in out["minor_feature_phase"]["kb"], out
        # no phase at all: g.nav blocks the doc search, g.phase blocks src.
        assert out["empty_ledger"]["nav"].startswith("block"), out
        assert out["empty_ledger"]["kb"].startswith("block"), out
        assert "omt_phase" in out["empty_ledger"]["kb"], out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
