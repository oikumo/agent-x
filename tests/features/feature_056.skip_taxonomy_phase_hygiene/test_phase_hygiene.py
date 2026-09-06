"""Wave 3/A3 phase_hygiene (+ A2.1 tool behavior) — feature_056.

Contract (GREEN pins the implementation):
- A3.1 AUTO-EXPIRE: getActiveUnlock/getActiveFeaturePhase ignore records older
  than @var unlock_window_ms — INCLUDING session-matched ones (the shadow hole:
  a stale session phase no longer shadows a later tests-approval, and stale
  scope=all no longer opens protected paths). All-expired sessions resolve to
  no-unlock (fail-closed); sessions owning no records keep the window fallback.
- A3.2 ABANDON: omt_phase{phase:"abandoned"} tombstones the feature's latest
  dangling phase; tombstones never unlock; a tombstone retires earlier
  same-feature same-phase records (other features/phases unaffected); resume
  is a plain re-declare.
- A2.1 TOOL: purpose validated (closed vocab), scope-aware default, ledger echo.
- GUARDRAIL: hasFastPathUnlock (C2) semantics preserved.

Bun probes exercise the REAL TS modules (feature_054 idiom): hermetic ledger
via OMT_LEDGER_PATH. Same process note as test_skip_taxonomy.py re: canary.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SESSION_STATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "session_state.ts"
RECEIPT_GUARD = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "receipt_guard.ts"
PHASE_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts"
STATUS_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts"
OMT = REPO_ROOT / ".meta" / "META_HARNESS.omt"

BUN = shutil.which("bun")

F = "feature_056.skip_taxonomy_phase_hygiene"


def _run_probe(tmp_path: Path, body: str) -> dict:
    """Write body to tmp/probe.ts, run bun with a hermetic ledger env."""
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    probe = tmp_path / "probe.ts"
    probe.write_text(body, encoding="utf-8")
    env = {**os.environ, "OMT_LEDGER_PATH": str(tmp_path / "ledger.jsonl")}
    out = subprocess.run([BUN, str(probe)], capture_output=True, text=True,
                         timeout=90, cwd=str(tmp_path), env=env)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


# --- A3.1 expiry matrix ----------------------------------------------------------

EXPIRY_PROBE = """import { writeFileSync } from "node:fs";
const LEDGER = process.env.OMT_LEDGER_PATH;
const H = 3600 * 1000, now = Date.now();
const iso = (ms) => new Date(ms).toISOString();
const recs = [
  { ts: iso(now - 9 * H), kind: "phase", session: "old", task_type: "minor_feature", phase: "Programming", scope: "s", feature: "feature_001.a" },
  { ts: iso(now - 30 * 60 * 1000), kind: "phase", session: "live", task_type: "minor_feature", phase: "Design", scope: "s", feature: "feature_002.b" },
  { ts: iso(now - 9 * H), kind: "skip", session: "oldskip", reason: "x", scope: "all" },
];
writeFileSync(LEDGER, recs.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
const m = await import("SESSION_STATE_ABS");
const out = {};
out.expired_session_null = m.getActiveUnlock("old") === null;
out.live_session_kept = m.getActiveUnlock("live")?.record?.feature === "feature_002.b";
out.no_session_window_fallback = m.getActiveUnlock(undefined)?.record?.feature === "feature_002.b";
out.expired_feature_phase_null = m.getActiveFeaturePhase("feature_001.a", "old") === null;
out.live_feature_phase_kept = m.getActiveFeaturePhase("feature_002.b", "live")?.phase === "Design";
out.unknown_session_falls_back = m.getActiveUnlock("nobody")?.record?.feature === "feature_002.b";
console.log(JSON.stringify(out));
"""


class TestExpiry:
    def test_expiry_matrix(self, tmp_path: Path) -> None:
        body = EXPIRY_PROBE.replace("SESSION_STATE_ABS", SESSION_STATE.as_posix())
        out = _run_probe(tmp_path, body)
        assert out == {k: True for k in out}, f"expiry matrix failed: {out}"

    def test_fast_path_guardrail_preserved(self, tmp_path: Path) -> None:
        """C2 owns hasFastPathUnlock — the new expiry code must not change it."""
        body = """import { writeFileSync } from "node:fs";
const LEDGER = process.env.OMT_LEDGER_PATH;
const recs = [{ ts: new Date().toISOString(), kind: "phase", session: "s",
  task_type: "bug_fix", phase: "Programming", scope: "s", feature: "f" }];
writeFileSync(LEDGER, recs.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
const m = await import("SESSION_STATE_ABS");
console.log(JSON.stringify({ fast: m.hasFastPathUnlock("s") === true }));
""".replace("SESSION_STATE_ABS", SESSION_STATE.as_posix())
        assert _run_probe(tmp_path, body) == {"fast": True}


# --- A3.1 shadow kill via the real canary guard -----------------------------------

SHADOW_PROBE = """import { writeFileSync } from "node:fs";
const LEDGER = process.env.OMT_LEDGER_PATH;
const H = 3600 * 1000, now = Date.now();
const iso = (ms) => new Date(ms).toISOString();
// ledger order: canary skip FIRST, shadowing phase SECOND (the gotcha shape)
const recs = [
  { ts: iso(now - SHADOW_SKIP_MIN * 60 * 1000), kind: "skip", session: "s", reason: "canary", scope: "tests", purpose: "canary", tests_approved: true },
  { ts: iso(now - SHADOW_PHASE_H * H), kind: "phase", session: "s", task_type: "minor_feature", phase: "Programming", scope: "s", feature: "feature_007.g" },
];
writeFileSync(LEDGER, recs.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
const g = await import("RECEIPT_GUARD_ABS");
const env = { directory: "/tmp", state: (await import("SESSION_STATE_ABS")).createSessionState(), safeLog: () => {}, notify: async () => {}, client: {}, $: {} };
let threw = "";
try { await g.guardTestsPath(env, "s", "tests/features/other/x.py"); }
catch (e) { threw = String((e && e.message) || e); }
console.log(JSON.stringify({ threw }));
"""


class TestShadowKill:
    def test_expired_phase_no_longer_shadows(self, tmp_path: Path) -> None:
        body = (SHADOW_PROBE.replace("RECEIPT_GUARD_ABS", RECEIPT_GUARD.as_posix())
                .replace("SESSION_STATE_ABS", SESSION_STATE.as_posix())
                .replace("SHADOW_SKIP_MIN", "60").replace("SHADOW_PHASE_H", "9"))
        assert _run_probe(tmp_path, body) == {"threw": ""}

    def test_in_window_phase_still_shadows(self, tmp_path: Path) -> None:
        """The ordering rule stands within the window (gotcha still true there)."""
        body = (SHADOW_PROBE.replace("RECEIPT_GUARD_ABS", RECEIPT_GUARD.as_posix())
                .replace("SESSION_STATE_ABS", SESSION_STATE.as_posix())
                .replace("SHADOW_SKIP_MIN", "60").replace("SHADOW_PHASE_H", "0.5"))
        out = _run_probe(tmp_path, body)
        assert "tests_canary" in out["threw"], f"expected canary block, got: {out}"


# --- A2.1 + A3.2 tool behavior ------------------------------------------------------

TOOL_PROBE = """import { writeFileSync, readFileSync } from "node:fs";
const LEDGER = process.env.OMT_LEDGER_PATH;
const H = 3600 * 1000, now = Date.now();
const iso = (ms) => new Date(ms).toISOString();
writeFileSync(LEDGER, [{ ts: iso(now - 30 * 60 * 1000), kind: "phase", session: "s",
  task_type: "minor_feature", phase: "Design", scope: "half", feature: "feature_009.q" }
].map((r) => JSON.stringify(r)).join("\\n") + "\\n");
const ss = await import("SESSION_STATE_ABS");
const pg = await import("PHASE_GATE_ABS");
const env = { directory: "/tmp", state: ss.createSessionState(), safeLog: () => {}, notify: async () => {}, client: {}, $: {} };
const tools = pg.createPhaseTools(env);
const out = {};
out.bad_purpose = String(await tools.omt_skip.execute({ reason: "x", purpose: "bogus" }, { sessionID: "s" }));
out.def_tests = String(await tools.omt_skip.execute({ reason: "c", scope: "tests" }, { sessionID: "s" }));
out.def_src = String(await tools.omt_skip.execute({ reason: "q", scope: "src" }, { sessionID: "s" }));
out.explicit = String(await tools.omt_skip.execute({ reason: "u", scope: "all", purpose: "emergency" }, { sessionID: "s" }));
out.abandon = String(await tools.omt_phase.execute({ task_type: "minor_feature", phase: "abandoned", feature: "feature_009.q", scope: "pivot" }, { sessionID: "s" }));
out.ledger = readFileSync(LEDGER, "utf8").trim().split("\\n").map((l) => JSON.parse(l));
console.log(JSON.stringify(out));
"""


class TestToolBehavior:
    def test_purpose_and_abandon(self, tmp_path: Path) -> None:
        body = (TOOL_PROBE.replace("SESSION_STATE_ABS", SESSION_STATE.as_posix())
                .replace("PHASE_GATE_ABS", PHASE_GATE.as_posix()))
        out = _run_probe(tmp_path, body)
        assert out["bad_purpose"].startswith("❌ invalid purpose")
        assert "purpose=canary" in out["def_tests"]
        assert "purpose=override" in out["def_src"]
        assert "purpose=emergency" in out["explicit"]
        assert "feature_009.q Design retired" in out["abandon"]
        skips = [r for r in out["ledger"] if r["kind"] == "skip"]
        assert [r["purpose"] for r in skips] == ["canary", "override", "emergency"], skips
        tomb = out["ledger"][-1]
        assert tomb["phase"] == "abandoned" and tomb["abandons"] == "Design"
        assert tomb["feature"] == "feature_009.q"


# --- A2.2 + A3.3 status report ---------------------------------------------------------

STATUS_PROBE = """import { writeFileSync } from "node:fs";
const LEDGER = process.env.OMT_LEDGER_PATH;
const H = 3600 * 1000, D = 24 * H, now = Date.now();
const iso = (ms) => new Date(ms).toISOString();
const recs = [
  { ts: iso(now - H), kind: "skip", session: "p", reason: "c", scope: "tests", purpose: "canary", tests_approved: true },
  { ts: iso(now - H), kind: "skip", session: "p", reason: "n", scope: "nav", purpose: "override" },
  { ts: iso(now - H), kind: "skip", session: "p", reason: "s", scope: "src" },
  { ts: iso(now - H), kind: "skip", session: "p", reason: "b", scope: "src", purpose: "bogus" },
  { ts: iso(now - 8 * D), kind: "skip", session: "p", reason: "e", scope: "all", purpose: "emergency" },
  { ts: iso(now - 30 * 60 * 1000), kind: "phase", session: "p", task_type: "minor_feature", phase: "Programming", scope: "live", feature: "feature_FA.a" },
  { ts: iso(now - 9 * H), kind: "phase", session: "p", task_type: "minor_feature", phase: "Design", scope: "stale", feature: "feature_FB.b" },
  { ts: iso(now - H), kind: "phase", session: "p", task_type: "minor_feature", phase: "Testing", scope: "done", feature: "feature_FC.c" },
  { ts: iso(now - 30 * 60 * 1000), kind: "complete", session: "p", feature: "feature_FC.c", phase: "Testing" },
  { ts: iso(now - 10 * H), kind: "phase", session: "p", task_type: "minor_feature", phase: "Analysis", scope: "old", feature: "feature_FD.d" },
  { ts: iso(now - 30 * 60 * 1000), kind: "phase", session: "p", task_type: "minor_feature", phase: "abandoned", abandons: "Analysis", scope: "x", feature: "feature_FD.d" },
];
writeFileSync(LEDGER, recs.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
const plugin = await (await import("STATUS_ABS")).default({ directory: "TMP_ABS", worktree: "TMP_ABS" });
const res = await plugin.tool.omt_status.execute({}, {});
console.log(JSON.stringify({ output: res.output, hygiene: res.metadata.skip_hygiene }));
"""


class TestStatusReport:
    def test_hygiene_section(self, tmp_path: Path) -> None:
        body = (STATUS_PROBE.replace("STATUS_ABS", STATUS_PLUGIN.as_posix())
                .replace("TMP_ABS", tmp_path.as_posix()))
        out = _run_probe(tmp_path, body)
        h = out["hygiene"]
        assert h == {"week_total": 4, "friction": 1, "nav_escapes": 1,
                     "evasion": 2, "warn_at": 5, "dangling_total": 2,
                     "dangling_expired": 1}, h
        text = out["output"]
        assert "Skips 7d: 4 (friction 1 · nav-escapes 1 · evasion 2, warn>5/week)" in text
        assert "Dangling phases: 2 (1 expired)" in text
        assert "feature_FB.b Design" in text and 'phase:"abandoned"' in text
        assert "resume: omt_phase{" in text and "abandon: omt_phase{" in text
        assert "feature_FA.a" not in text.split("Dangling phases")[1].split("resume:")[0]


# --- static pins --------------------------------------------------------------------------

class TestStaticPins:
    def test_expiry_and_tombstone_helpers(self) -> None:
        src = SESSION_STATE.read_text(encoding="utf-8")
        for token in ("isAliveUnlockRecord", "isRetiredByTombstone",
                      "abandons === r.phase", "fail-closed"):
            assert token in src

    def test_abandon_branch(self) -> None:
        src = PHASE_GATE.read_text(encoding="utf-8")
        assert 'if (newPhase === "abandoned")' in src
        assert "abandonDanglingPhase(env, session, tt," in src

    def test_hygiene_report_markers(self) -> None:
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        for token in ("skipHygiene()", "Skips 7d:", "Dangling phases:",
                      "DANGLING_LIST_CAP", "result.skip_hygiene"):
            assert token in src

    def test_status_stays_read_only(self) -> None:
        """A4 pin: omt_status never writes the ledger (its hygiene section reads)."""
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        assert "appendLedger" not in src and "writeLedger" not in src

    def test_no_new_tool_args_on_status(self) -> None:
        """A2+A3 ride the default status output — no schema growth on omt_status."""
        omt = OMT.read_text(encoding="utf-8")
        line = next(ln for ln in omt.splitlines() if ln.startswith("@tool omt_status"))
        assert 'args="op?,tool?,path?,include_ledger?"' in line
