#!/usr/bin/env python3
"""Golden tests for P1-2: cmd_done feature-suite split + R4 baseline_failures
regression guard (feature_028, meta_harness_3 v1.2).

R4/D5: a feature that breaks a prior feature's GREEN test still blocks done
(regressions = current − baseline − KNOWN_SUITE_FAILURES); drift (broken at
baseline AND still broken) is a repo-level triage note, not a block.
R10: hermetic — the feature's test dir is a tmp dir and the two pytest
runners are stubbed, so the golden never mutates (or waits on) the real suite.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

from tdd import cli, state  # noqa: E402

FEATURE = "feature_synth.done_split"
DRIFT_NODE = "tests/features/feature_001.old/test_old.py::test_drifts"
REGRESSION_NODE = "tests/features/feature_002.green/test_green.py::test_was_green"


@pytest.fixture()
def hermetic(tmp_path, monkeypatch):
    """Hermetic ledger + snapshot dir + tmp repo with a feature test dir
    (one well-named test, so the feature-suite run happens and naming_ok)."""
    monkeypatch.setattr(state, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(state, "SNAPSHOT_DIR", tmp_path / "snapshots")
    monkeypatch.setattr(state, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cli, "SNAPSHOT_DIR", tmp_path / "snapshots")
    test_dir = tmp_path / "tests" / "features" / FEATURE
    test_dir.mkdir(parents=True)
    (test_dir / "test_synth_done.py").write_text(
        "def test_synth_done_behavior():\n    assert True\n", encoding="utf-8")
    return tmp_path


def _write_phase(root: Path, baseline: list[str] | None) -> None:
    """The phase record as phase_gate.ts will write it (R4: baseline_failures
    captured at omt_phase{phase:Programming} entry)."""
    rec = {"kind": "phase", "session": "ses_golden", "feature": FEATURE,
           "phase": "Programming", "tdd_mode": True,
           "ts": "2026-08-16T09:00:00+00:00"}
    if baseline is not None:
        rec["baseline_failures"] = baseline
    with open(state.LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def _stub_runners(monkeypatch, suite_stdout: str, suite_exit: int,
                  feature_exit: int = 0):
    monkeypatch.setattr(cli, "run_full_suite",
                        lambda timeout=120: (suite_exit, suite_stdout, ""))
    monkeypatch.setattr(cli, "run_pytest",
                        lambda node, timeout=30: (feature_exit, "", ""))


class TestDoneBaselineRegressions:
    def test_regression_blocks_done(self, hermetic, monkeypatch):
        """R4: prior test GREEN at baseline → RED now → done BLOCKS (D5);
        the drift node is reported as tolerated, not as a blocker."""
        _write_phase(hermetic, [DRIFT_NODE])
        _stub_runners(monkeypatch,
                      f"FAILED {DRIFT_NODE} - assert x\n"
                      f"FAILED {REGRESSION_NODE} - assert y\n", 1)
        res = cli.cmd_done(SimpleNamespace(feature=FEATURE, session="ses_golden"))
        assert res["ok"] is False
        assert res["checklist"]["repo_hygiene_passes"] is False
        assert REGRESSION_NODE in res["message"]
        blocking = res["message"].split("drift")[0]
        assert DRIFT_NODE not in blocking

    def test_drift_does_not_block_done(self, hermetic, monkeypatch):
        """R10: broken at baseline AND still broken → done SUCCEEDS with a
        drift triage note (the P1-2 split)."""
        _write_phase(hermetic, [DRIFT_NODE])
        _stub_runners(monkeypatch, f"FAILED {DRIFT_NODE} - assert x\n", 1)
        res = cli.cmd_done(SimpleNamespace(feature=FEATURE, session="ses_golden"))
        assert res["ok"] is True
        assert res["checklist"]["feature_suite_passes"] is True
        assert res["checklist"]["repo_hygiene_passes"] is True
        assert "drift" in res["message"]
        assert DRIFT_NODE in res["message"]

    def test_no_baseline_keeps_legacy_blocking(self, hermetic, monkeypatch):
        """No baseline on the phase record → legacy semantics: ANY
        non-allowlisted failure blocks (D5 — no protection regression)."""
        _write_phase(hermetic, None)
        _stub_runners(monkeypatch, f"FAILED {DRIFT_NODE} - assert x\n", 1)
        res = cli.cmd_done(SimpleNamespace(feature=FEATURE, session="ses_golden"))
        assert res["ok"] is False

    def test_feature_suite_failure_blocks_even_when_repo_clean(
            self, hermetic, monkeypatch):
        """The split's new half: the feature's OWN suite must be green even
        when repo hygiene passes."""
        _write_phase(hermetic, [])
        _stub_runners(monkeypatch, "", 0, feature_exit=1)
        res = cli.cmd_done(SimpleNamespace(feature=FEATURE, session="ses_golden"))
        assert res["ok"] is False
        assert res["checklist"]["feature_suite_passes"] is False

    def test_cmd_start_captures_feature_baseline(self, hermetic, monkeypatch):
        """P1-3 producer (rides this cli.py round): cmd_start captures the
        feature-baseline snapshot for each existing target src at RED
        declaration — validate-exit's diff substrate (first-write-wins)."""
        root = hermetic
        src = root / "src" / "agentx" / "cap.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("def pre_existing():\n    return 1\n", encoding="utf-8")
        test_file = root / "tests" / "features" / FEATURE / "test_cap.py"
        test_file.write_text(
            "def test_cap_missing_behavior():\n    assert False\n",
            encoding="utf-8")
        monkeypatch.setattr(cli, "run_pytest",
                            lambda node, timeout=30: (1, "", ""))
        res = cli.cmd_start(SimpleNamespace(
            test_node=f"tests/features/{FEATURE}/test_cap.py::test_cap_missing_behavior",
            target_src="src/agentx/cap.py", feature=FEATURE, session="ses_golden"))
        assert res["ok"] is True
        baseline = state.load_feature_baseline(FEATURE, src)
        assert baseline is not None
        assert [m["method"] for m in baseline["methods"]] == ["pre_existing"]


class TestBaselineCapture:
    def test_cmd_baseline_returns_failing_node_ids(self, monkeypatch):
        """R4 producer: the baseline subcommand phase_gate.ts calls at
        Programming entry — raw failing node IDs of the current suite."""
        monkeypatch.setattr(
            cli, "run_full_suite",
            lambda timeout=120: (1, "FAILED a.py::t1 - x\nFAILED b.py::t2 - y\n", ""))
        res = cli.cmd_baseline(SimpleNamespace())
        assert res["ok"] is True
        assert res["exit_code"] == 1
        assert res["baseline_failures"] == ["a.py::t1", "b.py::t2"]

    def test_phase_gate_captures_baseline_at_programming_entry(self):
        """R4 TS pin (feature_016 enforcer-integration pattern): omt_phase
        snapshots baseline_failures onto the phase record at TDD Programming
        entry — scoped (not every phase call) and fail-open (D5: capture
        failure → no field → cmd_done legacy semantics)."""
        src = (REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts"
               ).read_text(encoding="utf-8")
        assert "tdd_check.py baseline" in src      # the producer call
        assert "baseline_failures" in src          # stored on the phase record
        assert '"Programming"' in src              # scoped to Programming entry
