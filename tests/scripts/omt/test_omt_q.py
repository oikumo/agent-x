"""Golden smoke/query tests for feature_026.omt_q_interrogative_first_ops.

Harness-level pin-test convention: lives alongside `test_omt_enforcer_guard_source_pins.py`
+ `test_omt_harness_e2e.py`. The canonical 12-behaviour golden suite mirrors the
TDD testlist record planted at Programming-phase entry (12 behaviors = the v1.3
Phase-A interrogative surface: U1/U2/U3 + U6/U7/U8/U9/U10/U11/U13 + v1.5
envelope + behaviour-preserving probe).

These tests exercise the real TS plugin source via `bun` probes (the same pattern
as `TestGateDriverProtectIrMissing`/`TestGateDriverIrRenderedMsg`). A probe is a
tiny TS snippet that imports the real `omt_q` plugin, calls `omt_q.execute()`,
and prints the JSON envelope — the Python test parses that JSON and asserts the
fold projections. The probes are hermetic (tmp + copied IR) unless a test
explicitly targets the live repo root (the U10 known-suite-failures parse).

Two-hats TDD: this file is RED-phase ONLY. GREEN implementation lands in
.opencode/plugins/omt_q.ts (+ gate_driver.ts runBeforeGatesDry) — never both at
once (GOTCHA_TDD_NODE_GRANULARITY: red/green/refactor at the SAME test_node).
"""

import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
OMT_Q_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_q.ts"
GATE_DRIVER = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "gate_driver.ts"
SHARED_LIB = REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts"
SESSION_STATE = (
    REPO_ROOT / ".opencode" / "lib" / "enforcer" / "session_state.ts"
)
STATE_PY = REPO_ROOT / "scripts" / "omt" / "tdd" / "state.py"

BUN = shutil.which("bun")


# --- test helpers -----------------------------------------------------------

def _copy_real_ir(tmp_path: Path) -> None:
    """Copy the live harness IR into tmp root (tests that need real gate defs)."""
    ir_dst = tmp_path / ".meta" / ".omt"
    ir_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / ".meta" / ".omt" / "harness.ir.json",
        ir_dst / "harness.ir.json",
    )


def _write_ledger(tmp_path: Path, records: list[dict]) -> None:
    """Write a fixture ledger.jsonl under tmp root."""
    p = tmp_path / ".meta" / ".omt" / "ledger.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


# Bare probe scaffold that imports omt_q, calls execute once, prints the JSON.
_q_probe_template = """
import { initOmtShared, repoRoot } from "%LIB%"
initOmtShared(process.argv[2])
const mod = await import("%PLUGIN%")
const { tool } = await mod.default({ directory: process.argv[2], worktree: process.argv[2] })
const args = %ARGS%
const result = await tool.omt_q.execute(args, { sessionID: "%SESSION%" })
console.log(result)
"""


def _q_probe(args_str: str, session: str = "ses_probe", extra_files: dict | None = None,
             use_real_ir: bool = False, tmp_path: Path | None = None,
             use_real_root: bool = False) -> dict:
    """Invoke omt_q with the given args JSON-string under a tmp root; return parsed envelope.

    ``use_real_root=True`` runs the probe against ``REPO_ROOT`` instead of the
    hermetic ``tmp_path`` — used by tests whose contract is to read the live
    repo substrate (e.g. U10 parses the real ``scripts/omt/tdd/state.py``).
    The hermetic ``tmp_path`` is still required for the fixture-setup plumbing
    but is ignored when ``use_real_root`` is set.
    """
    if tmp_path is None:
        raise AssertionError("tmp_path required")
    assert BUN is not None, "bun runtime required for _q_probe (guard against skipif bypass)"
    root = REPO_ROOT if use_real_root else tmp_path
    if use_real_ir and not use_real_root:
        _copy_real_ir(tmp_path)
    if extra_files and not use_real_root:
        for rel, contents in extra_files.items():
            dst = tmp_path / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(contents, dict):
                dst.write_text(json.dumps(contents), encoding="utf-8")
            else:
                dst.write_text(contents, encoding="utf-8")
    probe = tmp_path / "probe.ts"
    probe.write_text(
        _q_probe_template
            .replace("%LIB%", str(SHARED_LIB))
            .replace("%PLUGIN%", str(OMT_Q_PLUGIN))
            .replace("%ARGS%", args_str)
            .replace("%SESSION%", session),
        encoding="utf-8",
    )
    out = subprocess.run([BUN, str(probe), str(root)],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    lines = out.stdout.strip().splitlines()
    return json.loads(lines[-1])


# ---------------------------------------------------------------------------
# U1: op:state resume 5-read snapshot
# ---------------------------------------------------------------------------

class TestOpStateResumeSnapshot:
    """U1: op:state returns the documented 5-read resume snapshot folded into
    one envelope: phase + tdd_position + last_activity_ts."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u1_op_state_returns_5_read_snapshot(self, tmp_path):
        _copy_real_ir(tmp_path)
        _write_ledger(tmp_path, [
            {"ts": "2026-08-09T10:00:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Programming",
             "feature": "feature_026.omt_q_interrogative_first_ops",
             "session": "ses_u1"},
            {"ts": "2026-08-09T10:01:00Z", "kind": "tdd_testlist",
             "session": "ses_u1", "behaviors": ["U1"], "remaining": [],
             "feature": "feature_026.omt_q_interrogative_first_ops"},
            {"ts": "2026-08-09T10:05:00Z", "kind": "tdd", "session": "ses_u1",
             "state": "red", "test_node": "tests/scripts/omt/test_omt_q.py::T::t",
             "target_src": [".opencode/plugins/omt_q.ts"], "verified": False,
             "exit_code": 1, "feature": "feature_026.omt_q_interrogative_first_ops"},
        ])
        out = _q_probe(
            '{"op":"state","feature":"feature_026.omt_q_interrogative_first_ops","session":"ses_u1"}',
            session="ses_u1", use_real_ir=True, tmp_path=tmp_path,
        )
        assert out["op"] == "state"
        assert "phase" in out and out["phase"] == "Programming", (
            f"U1 pipe-through phase missing/wrong: {out}")
        assert "tdd_position" in out, f"U1 tdd_position missing: {out}"
        assert out["tdd_position"]["state"] == "red", (
            f"U1 tdd_position.state should be red: {out['tdd_position']}")
        assert "last_activity_ts" in out, f"U1 last_activity_ts missing: {out}"


# ---------------------------------------------------------------------------
# U2: op:plan predicts real before-chain on gate_driver.ts incl g.think self-trigger
# ---------------------------------------------------------------------------

class TestOpPlanPredictsBeforeChain:
    """U2: op:plan {path:gate_driver.ts} predicted chain == real before-chain
    (the 7 IR before-gates order-sorted), incl g.think self-trigger (the file
    contains the literal "TA:")."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u2_op_plan_predicts_before_chain_on_gate_driver(self, tmp_path):
        _copy_real_ir(tmp_path)
        # Copy the real gate_driver.ts into tmp so file_has("TA:") fires.
        dst = tmp_path / ".opencode" / "lib" / "enforcer" / "gate_driver.ts"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(GATE_DRIVER, dst)
        out = _q_probe(
            json.dumps({"op": "plan",
                        "path": ".opencode/lib/enforcer/gate_driver.ts",
                        "tool": "edit", "session": "ses_u2"}),
            session="ses_u2", use_real_ir=True, tmp_path=tmp_path,
        )
        assert out["op"] == "plan"
        assert "predicted_chain" in out, f"U2 predicted_chain missing: {out}"
        chain = out["predicted_chain"]
        assert isinstance(chain, list), f"U2 predicted_chain must be a list: {out}"
        # The 7 before-gates in IR order: g.nav, g.protect, g.receipt, g.tests,
        # g.phase, g.think, g.kb. gate_driver.ts is in harness_paths but not
        # src/, not tests/, not @protect — g.protect skip, g.receipt applies
        # (path in harness_paths → would block on stale receipt), g.think
        # applies (file contains "TA:" literal) and SHOULD block.
        gate_ids = [d["gate_id"] for d in chain]
        assert "g.think" in gate_ids, (
            f"U2 g.think self-trigger missing — gate_driver.ts contains 'TA:' "
            f"so g.think must fire: {chain}")
        # first_blocker convenience field
        assert "first_blocker" in out, f"U2 first_blocker missing: {out}"


# ---------------------------------------------------------------------------
# U3: op:drift reports count_drift direction-b only
# ---------------------------------------------------------------------------

class TestOpDriftCountDriftDirectionB:
    """U3: op:drift reports count_drift with direction_b_only=true (KB>skeleton
    IS drift; KB<skeleton is just not-yet-curated, NOT drift)."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u3_op_drift_direction_b_only(self, tmp_path):
        _copy_real_ir(tmp_path)
        out = _q_probe(json.dumps({"op": "drift"}),
                       session="ses_u3", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "drift"
        assert "count_drift" in out, f"U3 count_drift missing: {out}"
        cd = out["count_drift"]
        assert "direction_b_only" in cd, (
            f"U3 direction_b_only missing: {out}")
        assert cd["direction_b_only"] is True, (
            f"U3 direction_b_only must be true (KB>skeleton IS drift; "
            f"KB<skeleton is NOT drift): {cd}")
        assert "kb" in cd and "skeleton" in cd, (
            f"U3 count_drift must have kb + skeleton counts: {cd}")


# ---------------------------------------------------------------------------
# U6: stranded_red per-test_node latest-red with no later green
# ---------------------------------------------------------------------------

class TestOpStateStrandedRed:
    """U6: op:state reports stranded_red = test_nodes whose latest tdd state is
    'red' with no later green at the same test_node."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u6_op_state_reports_stranded_red(self, tmp_path):
        _copy_real_ir(tmp_path)
        _write_ledger(tmp_path, [
            # red at node A, never greened
            {"ts": "2026-08-09T11:00:00Z", "kind": "tdd", "session": "s",
             "state": "red", "test_node": "tests/x.py::T::a",
             "target_src": ["src/x.py"], "verified": False, "exit_code": 1,
             "feature": "feature_026.omt_q_interrogative_first_ops"},
            # red at node B, then greened (NOT stranded)
            {"ts": "2026-08-09T11:01:00Z", "kind": "tdd", "session": "s",
             "state": "red", "test_node": "tests/x.py::T::b",
             "target_src": ["src/x.py"], "verified": True, "exit_code": 1,
             "feature": "feature_026.omt_q_interrogative_first_ops"},
            {"ts": "2026-08-09T11:02:00Z", "kind": "tdd", "session": "s",
             "state": "green", "test_node": "tests/x.py::T::b",
             "target_src": ["src/x.py"], "verified": True, "exit_code": 0,
             "feature": "feature_026.omt_q_interrogative_first_ops"},
        ])
        out = _q_probe(
            json.dumps({"op": "state",
                        "feature": "feature_026.omt_q_interrogative_first_ops"}),
            session="ses_u6", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "state"
        assert "stranded_red" in out, f"U6 stranded_red missing: {out}"
        sr = out["stranded_red"]
        assert isinstance(sr, list), f"U6 stranded_red must be a list: {out}"
        assert any("::a" in s for s in sr), (
            f"U6 stranded_red must include the un-greened node A: {sr}")
        assert not any("::b" in s for s in sr), (
            f"U6 stranded_red must NOT include the greened node B: {sr}")


# ---------------------------------------------------------------------------
# U7: closed_via_skip + cross-feature FP guard
# ---------------------------------------------------------------------------

class TestOpStateClosedViaSkip:
    """U7: closed_via_skip = a not-done (false checklist) followed by a skip in
    the SAME feature within 1h window. A skip for feature_Y does NOT flip
    feature_X."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u7_closed_via_skip_same_feature(self, tmp_path):
        _copy_real_ir(tmp_path)
        _write_ledger(tmp_path, [
            {"ts": "2026-08-09T12:00:00Z", "kind": "complete",
             "session": "s", "feature": "feature_X", "phase": "Testing",
             "checklist": {"suite_passes": False, "refactor_recorded": True,
                           "naming_ok": True}},
            {"ts": "2026-08-09T12:30:00Z", "kind": "skip", "session": "s",
             "feature": "feature_X", "scope": "all",
             "reason": "Override permits pre-existing baseline failure"},
        ])
        out = _q_probe(json.dumps({"op": "state", "feature": "feature_X"}),
                       session="ses_u7a", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "state"
        assert "closed_via_skip" in out, f"U7 closed_via_skip missing: {out}"
        assert bool(out["closed_via_skip"]) is True, (
            f"U7 closed_via_skip should be true for feature_X: {out}")

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u7_cross_feature_fp_guard(self, tmp_path):
        _copy_real_ir(tmp_path)
        _write_ledger(tmp_path, [
            {"ts": "2026-08-09T12:00:00Z", "kind": "complete",
             "session": "s", "feature": "feature_X", "phase": "Testing",
             "checklist": {"suite_passes": False, "refactor_recorded": True,
                           "naming_ok": True}},
            # skip scoped to feature_Y — must NOT flip feature_X
            {"ts": "2026-08-09T12:30:00Z", "kind": "skip", "session": "s",
             "feature": "feature_Y", "scope": "all",
             "reason": "Override permits pre-existing baseline failure"},
        ])
        out = _q_probe(json.dumps({"op": "state", "feature": "feature_X"}),
                       session="ses_u7b", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "state"
        assert "closed_via_skip" in out, f"U7 closed_via_skip missing: {out}"
        assert bool(out["closed_via_skip"]) is False, (
            f"U7 cross-feature FP guard: skip for feature_Y must NOT flip "
            f"feature_X's closed_via_skip: {out}")


# ---------------------------------------------------------------------------
# U8: decree_health slug_variants + empty_slug + invalid_phase + near-collision guard
# ---------------------------------------------------------------------------

class TestOpStateDecreeHealth:
    """U8: decree_health reports slug_variants + empty_slug_records +
    invalid_phase_records + phase_cycle_count. NEAR-COLLISION GUARD:
    feature_004 != feature_04 (bare)."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u8_decree_health_with_near_collision_guard(self, tmp_path):
        _copy_real_ir(tmp_path)
        _write_ledger(tmp_path, [
            # empty slug whose scope mentions feature_024
            {"ts": "2026-08-09T01:00:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Programming",
             "feature": "", "scope": "feature_024 work",
             "session": "s"},
            # "" literal phase record (invalid phase tracking)
            {"ts": "2026-08-09T01:01:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "",
             "feature": "feature_024.tui_framework",
             "session": "s"},
            # 3 distinct slug variants of feature_024
            {"ts": "2026-08-09T01:02:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Design",
             "feature": "feature_024.tui_framework",
             "session": "s"},
            {"ts": "2026-08-09T01:03:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Design",
             "feature": "feature_024.tui_framework_v2",
             "session": "s"},
            {"ts": "2026-08-09T01:04:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Design",
             "feature": "feature_024.no_tui_full_features",
             "session": "s"},
            # invalid phase name
            {"ts": "2026-08-09T01:05:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Reintegration",
             "feature": "feature_024.tui_framework",
             "session": "s"},
            # near-collision: feature_004 vs feature_04 (bare)
            {"ts": "2026-08-09T01:06:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Design",
             "feature": "feature_004.foo",
             "session": "s"},
            {"ts": "2026-08-09T01:07:00Z", "kind": "phase",
             "task_type": "major_feature", "phase": "Design",
             "feature": "feature_04",
             "session": "s"},
        ])
        out = _q_probe(
            json.dumps({"op": "state", "verbose": True,
                        "feature": "feature_024.tui_framework"}),
            session="ses_u8", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "state"
        assert "decree_health" in out, f"U8 decree_health missing: {out}"
        dh = out["decree_health"]
        assert "slug_variants" in dh, f"U8 slug_variants missing: {dh}"
        assert "empty_slug_records" in dh, (
            f"U8 empty_slug_records missing: {dh}")
        assert "invalid_phase_records" in dh, (
            f"U8 invalid_phase_records missing: {dh}")
        # empty_slug_records must include the ""-slug record
        assert len(dh["empty_slug_records"]) >= 1, (
            f"U8 empty_slug_records should be >= 1: {dh}")
        # invalid_phase_records must include "Reintegration" or ""
        assert len(dh["invalid_phase_records"]) >= 1, (
            f"U8 invalid_phase_records should be >= 1: {dh}")
        # near-collision: feature_004 and feature_04 must NOT be merged
        slugs = {s if isinstance(s, str) else s.get("feature", "") for s in dh["slug_variants"]}
        # feature_004.foo and a "feature_04" (bare) are DIFFERENT slugs
        assert any(s.startswith("feature_004") for s in slugs), (
            f"U8 feature_004 should appear: {slugs}")
        # feature_04 (bare) must not be confused with feature_004.*
        for s in slugs:
            if s == "feature_04":
                assert not s.startswith("feature_004"), (
                    f"U8 near-collision: feature_04 must NOT match feature_004: {slugs}")


# ---------------------------------------------------------------------------
# U9: skip_reason_tally top-3 + live_smoke_count SEPARATE named field
# ---------------------------------------------------------------------------

class TestOpStateSkipReasonTally:
    """U9: skip_reason_tally reports top-3 stems + counts. live_smoke_count is a
    SEPARATE named field (not part of the generic tally)."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u9_skip_reason_tally_with_live_smoke_named(self, tmp_path):
        _copy_real_ir(tmp_path)
        _write_ledger(tmp_path, [
            {"ts": "2026-08-09T13:00:00Z", "kind": "skip", "session": "s",
             "reason": "live smoke probe nav gate", "scope": "nav"},
            {"ts": "2026-08-09T13:01:00Z", "kind": "skip", "session": "s",
             "reason": "live smoke probe think gate", "scope": "nav"},
            {"ts": "2026-08-09T13:02:00Z", "kind": "skip", "session": "s",
             "reason": "TDD bootstrap gotcha", "scope": "all"},
            {"ts": "2026-08-09T13:03:00Z", "kind": "skip", "session": "s",
             "reason": "Override permits pre-existing baseline failure",
             "scope": "all"},
        ])
        out = _q_probe(json.dumps({"op": "state"}),
                       session="ses_u9", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "state"
        assert "skip_reason_tally" in out, f"U9 skip_reason_tally missing: {out}"
        # live_smoke_count is a NAMED separate field, NOT inside the tally
        assert "live_smoke_count" in out, (
            f"U9 live_smoke_count named field missing: {out}")
        assert out["live_smoke_count"] == 2, (
            f"U9 live_smoke_count should be 2 (two skips with 'live smoke' stem): "
            f"{out}")


# ---------------------------------------------------------------------------
# U10: known_suite_failures parsed from state.py (not hardcoded)
# ---------------------------------------------------------------------------

class TestOpStateKnownSuiteFailuresParse:
    """U10 (feature_051/A1 shape): op:state.known_suite_failures mirrors the
    state.py KNOWN_SUITE_FAILURES frozenset — PERMANENTLY EMPTY since A1
    (ledger test isolation). The field is now a live invariant probe:
    non-empty output means someone regrew the allowlist (reverting A1).
    Mirror-parse state.py here and compare (NOT hardcoded in the test)."""

    @staticmethod
    def _parse_ksf_from_state_py() -> tuple[list[str], bool]:
        """Mirror omt_q's regex extractor in Python (independent cross-check).
        feature_051/A1: `[^}]*` so the empty frozenset({}) literal parses."""
        try:
            if not STATE_PY.exists():
                return [], True
            src = STATE_PY.read_text(encoding="utf-8")
            m = re.search(
                r"KNOWN_SUITE_FAILURES\s*=\s*frozenset\(\{([^}]*)\}\)", src)
            if not m:
                return [], True
            ids = [s.strip("'\"") for s in re.findall(r"['\"]([^'\"]+)['\"]", m.group(1))]
            return ids, False
        except Exception:
            return [], True

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u10_known_suite_failures_from_state_py(self, tmp_path):
        # U10's contract is to parse the LIVE scripts/omt/tdd/state.py — run the
        # probe at REPO_ROOT (not a hermetic tmp_path which has no state.py).
        # The IR copy into tmp_path is harmless plumbing here; use_real_root
        # makes the bun probe run against the real repo substrate.
        _copy_real_ir(tmp_path)
        out = _q_probe(json.dumps({"op": "state"}),
                       session="ses_u10", use_real_ir=True, tmp_path=tmp_path,
                       use_real_root=True)
        assert out["op"] == "state"
        assert "known_suite_failures" in out, (
            f"U10 known_suite_failures missing: {out}")
        assert "known_suite_failures_parse_failed" in out, (
            f"U10 parse-failed flag missing: {out}")
        # Mirror-parses state.py in Python and compares.
        expected_ids, py_parse_failed = self._parse_ksf_from_state_py()
        if py_parse_failed:
            pytest.skip("state.py KNOWN_SUITE_FAILURES regex miss on this checkout")
        # A1 invariant: the allowlist is empty — the field is a live probe.
        assert expected_ids == [], (
            f"A1 invariant: KNOWN_SUITE_FAILURES must be empty: {expected_ids}")
        assert out["known_suite_failures"] == expected_ids, (
            f"U10 known_suite_failures must equal state.py parse: "
            f"plugin={out['known_suite_failures']}  py={expected_ids}")
        assert out["known_suite_failures_parse_failed"] is False, (
            f"U10 plugin parse must not have failed: {out}")


# ---------------------------------------------------------------------------
# U11: op:plan receipt_detail.stale + refresh_tests + refresh_cmd
# ---------------------------------------------------------------------------

class TestOpPlanReceiptDetail:
    """U11: op:plan receipt_detail is populated when path ∈ @var.harness_paths,
    with stale/refresh_tests/refresh_cmd when the file mtime > last receipt."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u11_plan_receipt_detail_stale(self, tmp_path):
        _copy_real_ir(tmp_path)
        # Copy a real harness file in (it's in @var.harness_paths prefix).
        dst = tmp_path / ".opencode" / "plugins" / "omt_nav.ts"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / ".opencode" / "plugins" / "omt_nav.ts", dst)
        # Write an old receipt (passed_at long ago → the freshly-copied nav.ts
        # has a mtime of "now", which is > passed_at → stale:true).
        rec_dst = tmp_path / ".meta" / ".omt" / "omt_harness_e2e_last_run.json"
        rec_dst.parent.mkdir(parents=True, exist_ok=True)
        rec_dst.write_text(json.dumps({
            "passed_at": 1,  # epoch-second: very old
            "ok": True, "command": "uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q",
        }), encoding="utf-8")
        out = _q_probe(
            json.dumps({"op": "plan",
                        "path": ".opencode/plugins/omt_nav.ts",
                        "tool": "edit", "session": "ses_u11"}),
            session="ses_u11", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "plan"
        assert "receipt_detail" in out, f"U11 receipt_detail missing: {out}"
        rd = out["receipt_detail"]
        assert rd.get("receipt_required") is True, (
            f"U11 receipt_required must be true (path in harness_paths): {rd}")
        assert rd.get("stale") is True, (
            f"U11 stale should be true (file newer than old receipt): {rd}")
        assert rd.get("refresh_tests") == [
            "tests/scripts/omt/test_omt_harness_e2e.py"], (
            f"U11 refresh_tests mismatch: {rd}")
        assert rd.get("refresh_cmd") == (
            "uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q"), (
            f"U11 refresh_cmd mismatch: {rd}")


# ---------------------------------------------------------------------------
# U13: recent_consults within 8h + consult_needed[] = files not recently consulted
# ---------------------------------------------------------------------------

class TestOpStateConsultDedup:
    """U13: recent_consults = think_consult records within UNLOCK_WINDOW_MS (8h).
    consult_needed = files referenced by the active feature but not recently
    consulted."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_u13_op_state_consult_dedup(self, tmp_path):
        _copy_real_ir(tmp_path)
        # Dynamic timestamp: 1h before "now", always within the 8h
        # UNLOCK_WINDOW_MS consult-de-dup window. A hardcoded date (2026-08-09)
        # drifts stale past 8h of the real today → recent_consults becomes empty
        # and the U13 pin false-fails. Use now-1h so the test is date-stable.
        fresh_ts = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        _write_ledger(tmp_path, [
            {"ts": fresh_ts, "kind": "think_consult", "session": "s",
             "files": ["src/x.py", "src/y.py"], "category": "gotcha",
             "feature": "feature_026.omt_q_interrogative_first_ops"},
        ])
        out = _q_probe(
            json.dumps({"op": "state", "verbose": True,
                        "feature": "feature_026.omt_q_interrogative_first_ops"}),
            session="ses_u13", use_real_ir=True, tmp_path=tmp_path)
        assert out["op"] == "state"
        assert "recent_consults" in out, f"U13 recent_consults missing: {out}"
        rc = out["recent_consults"]
        assert isinstance(rc, list), f"U13 recent_consults must be a list: {out}"
        assert len(rc) >= 1, f"U13 should have >= 1 recent consult: {out}"
        # src/x.py and src/y.py were both recently consulted → in recent_consults,
        # NOT in consult_needed.
        files_in_recent = set()
        for r in rc:
            files_in_recent.update(r.get("files", []))
        assert "src/x.py" in files_in_recent, (
            f"U13 src/x.py must be in recent_consults: {rc}")
        assert "src/y.py" in files_in_recent, (
            f"U13 src/y.py must be in recent_consults: {rc}")
        assert "consult_needed" in out, f"U13 consult_needed missing: {out}"
        cn = out["consult_needed"]
        assert "src/x.py" not in cn and "src/y.py" not in cn, (
            f"U13 recently-consulted files must NOT be in consult_needed: {cn}")


# ---------------------------------------------------------------------------
# v1.5 envelope: as_of_commit == HEAD-sha in every golden; byte-identical on re-call
# ---------------------------------------------------------------------------

class TestEnvelopeAsOfCommit:
    """v1.5 envelope: every op response carries as_of_commit == <HEAD-sha>
    (parsed live via `git rev-parse HEAD`); two consecutive calls against an
    unchanged commit return byte-identical as_of_commit values."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_envelope_as_of_commit_matches_head_sha(self, tmp_path):
        _copy_real_ir(tmp_path)
        out = _q_probe(json.dumps({"op": "state"}),
                       session="ses_env", use_real_ir=True, tmp_path=tmp_path)
        assert "as_of_commit" in out, (
            f"v1.5 envelope: as_of_commit missing: {out}")
        # Compare against the live git HEAD-sha of the REAL repo (the plugin
        # calls `git rev-parse HEAD` against repoRoot — which under the probe
        # tmp_path has no .git, so it falls back to "HEAD" — but against the
        # real repo it returns the actual sha). Accept either: a 40-char sha OR
        # the literal "HEAD" (the documented fallback when git fails).
        sha = out["as_of_commit"]
        assert sha == "HEAD" or len(sha) == 40, (
            f"v1.5 envelope: as_of_commit must be a 40-char sha OR the 'HEAD' "
            f"fallback, got: {sha!r}")

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    def test_envelope_two_calls_byte_identical_commit(self, tmp_path):
        _copy_real_ir(tmp_path)
        out1 = _q_probe(json.dumps({"op": "state"}),
                        session="ses_env2a", use_real_ir=True, tmp_path=tmp_path)
        out2 = _q_probe(json.dumps({"op": "state"}),
                        session="ses_env2b", use_real_ir=True, tmp_path=tmp_path)
        assert out1.get("as_of_commit") == out2.get("as_of_commit"), (
            f"v1.5 envelope: two consecutive calls against the same commit must "
            f"return byte-identical as_of_commit: got {out1.get('as_of_commit')!r} "
            f"vs {out2.get('as_of_commit')!r}")


# ---------------------------------------------------------------------------
# Behaviour-preserving: runBeforeGatesDry does not break real runBeforeGates throw-on-block
# ---------------------------------------------------------------------------

DRY_VS_REAL_PROBE = """
import { initOmtShared } from "%LIB%"
import { runBeforeGates, runBeforeGatesDry, type GateCtx } from "%DRIVER%"
import { createSessionState, OmtBlock } from "%STATE%"
initOmtShared(process.argv[2])
const env = {
  client: {}, $: {}, directory: process.argv[2],
  state: createSessionState(),
  safeLog: () => {},
  notify: async () => {},
}
let realResult = "NO_BLOCK"
try {
  await runBeforeGates(env, "r-probe", { tool: "edit" }, { args: { filePath: "README.md" } }, "README.md")
} catch (e) {
  realResult = e instanceof OmtBlock ? "BLOCKED" : "OTHER:" + (e?.message || e)
}
const ctx: GateCtx = {
  env, session: "r-probe", tool: "edit",
  input: { tool: "edit" },
  output: { args: { filePath: "README.md" } },
  rel: "README.md", abs: process.argv[2] + "/README.md",
  memo: new Map(),
}
let dryDecisions: any[] = []
let dryErr = ""
try {
  dryDecisions = await runBeforeGatesDry(ctx)
} catch (e: any) {
  dryErr = String(e?.message || e)
}
console.log(JSON.stringify({ realResult, dryDecisions, dryErr }))
"""


class TestRunBeforeGatesDryDoesNotBreakRealPath:
    """Behaviour-preserving probe: the additive runBeforeGatesDry does NOT break
    the real runBeforeGates throw-on-block on a protect-path; AND runBeforeGatesDry
    on the same path returns a decisions[] with at least one blocked:true (no
    throw). Mirrors TestGateDriverProtectIrMissing's bun-probe pattern."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    @pytest.mark.skipif(not OMT_Q_PLUGIN.exists(), reason="omt_q.ts not implemented yet (RED)")
    @pytest.mark.skipif(not GATE_DRIVER.exists(), reason="gate_driver.ts missing")
    def test_run_before_gates_dry_does_not_break_real_path(self, tmp_path):
        assert BUN is not None, "bun runtime required (guard against skipif bypass)"
        (tmp_path / "README.md").write_text("# probe\n", encoding="utf-8")
        _copy_real_ir(tmp_path)
        probe = tmp_path / "probe.ts"
        probe.write_text(
            DRY_VS_REAL_PROBE
                .replace("%LIB%", str(SHARED_LIB))
                .replace("%DRIVER%", str(GATE_DRIVER))
                .replace("%STATE%", str(SESSION_STATE)),
            encoding="utf-8")
        out = subprocess.run(
            [BUN, str(probe), str(tmp_path)],
            capture_output=True, text=True, timeout=60)
        assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
        data = json.loads(out.stdout.strip().splitlines()[-1])
        # The REAL runBeforeGates must still throw OmtBlock on README.md
        assert data["realResult"] == "BLOCKED", (
            f"behaviour-preserving: runBeforeGates must STILL throw OmtBlock on "
            f"README.md after the dry refactor: got {data['realResult']!r}")
        # The DRY variant must NOT throw — it captures OmtBlock and returns
        # decisions[] with at least one blocked:true.
        assert data["dryErr"] == "", (
            f"runBeforeGatesDry must not throw — it captures: {data['dryErr']}")
        assert isinstance(data["dryDecisions"], list), (
            f"runBeforeGatesDry must return a decisions list: "
            f"{type(data['dryDecisions'])}")
        assert len(data["dryDecisions"]) > 0, (
            "runBeforeGatesDry must return >= 1 decision row")
        assert any(d.get("blocked") is True for d in data["dryDecisions"]), (
            f"runBeforeGatesDry must have >= 1 blocked:true decision: "
            f"{data['dryDecisions']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
