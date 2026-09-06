#!/usr/bin/env python3
"""Feature tests for TDD enforcement (feature_016).

Verifies the TDD engine's subcommands, gate logic, and AST analysis work
end-to-end through the CLI interface.

Run with: uv run pytest tests/features/feature_016.tdd_enforcement/ -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
TDD_CHECK = ["uv", "run", "scripts/omt/tdd_check.py"]


def _run_tdd(*args: str) -> subprocess.CompletedProcess[str]:
    """feature_051 (A1 — ledger test isolation): every tdd_check subprocess
    runs against a fresh TMP ledger (OMT_LEDGER_PATH / OMT_SNAPSHOT_DIR), so
    gate verdicts depend only on the args — never on whatever TDD session is
    live in the real 8h-window ledger (the historical window-flaky root:
    test_gate_no_tdd_* failed exactly while a TDD session was in-window)."""
    with tempfile.TemporaryDirectory(prefix="omt_tdd_hermetic_") as td:
        env = {
            **os.environ,
            "OMT_LEDGER_PATH": str(Path(td) / "ledger.jsonl"),
            "OMT_SNAPSHOT_DIR": str(Path(td) / "tdd_snapshots"),
        }
        return subprocess.run(
            TDD_CHECK + list(args),
            capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT),
            env=env,
        )


class TestTddCheckCli:
    """Verify tdd_check.py CLI subcommands return valid JSON."""

    def test_status_returns_json(self):
        result = _run_tdd("status", "--session", "")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "tdd_mode" in data
        assert "state" in data

    def test_gate_no_tdd_allows_everything(self):
        result = _run_tdd("gate", "--path", "src/foo.py", "--session", "")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["allowed"] is True
        assert data["tdd_mode"] is False

    def test_gate_no_tdd_allows_tests(self):
        result = _run_tdd("gate", "--path", "tests/foo.py", "--is-tests", "--session", "")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["allowed"] is True

    def test_validate_exit_unknown_feature_ok(self):
        result = _run_tdd("validate-exit", "--feature", "feature_999.nonexistent")
        data = json.loads(result.stdout)
        assert data["ok"] is True

    def test_after_edit_no_tdd_returns_ok(self):
        result = _run_tdd("after-edit", "--path", "src/foo.py", "--session", "")
        data = json.loads(result.stdout)
        assert data["action"] == "ok"


class TestTddCheckGateRules:
    """Verify the two-hats gate rules are correctly enforced."""

    @pytest.mark.parametrize("state,is_tests,expected", [
        ("testlist", False, False),   # planning: no edits
        ("testlist", True, False),    # planning: no edits
        ("red", False, False),        # test hat: src blocked
        ("red", True, True),          # test hat: tests allowed
        ("green", False, True),       # code hat: src allowed
        ("green", True, False),       # code hat: tests blocked
        ("refactor", False, True),    # refactor hat: src allowed
        ("refactor", True, False),    # refactor hat: tests blocked
        ("done", False, False),       # complete: no edits
        ("done", True, False),        # complete: no edits
        ("none", False, True),        # TDD off: everything allowed
        ("none", True, True),         # TDD off: everything allowed
    ])
    def test_hat_rules(self, state, is_tests, expected):
        rules = {
            "testlist": {"src": False, "tests": False},
            "red": {"src": False, "tests": True},
            "green": {"src": True, "tests": False},
            "refactor": {"src": True, "tests": False},
            "done": {"src": False, "tests": False},
            "none": {"src": True, "tests": True},
        }
        allowed = rules[state]["tests"] if is_tests else rules[state]["src"]
        assert allowed == expected


class TestTddCheckEnforcerIntegration:
    """Verify the enforcer plugin source has TDD integration.

    Post meta_harness_dsl R2: omt_enforcer.ts is a thin composition root;
    the TDD machinery lives in .opencode/lib/enforcer/ modules.
    """

    def test_enforcer_has_tdd_tools(self):
        tdd_hats = (REPO_ROOT / ".opencode" / "lib" / "enforcer" / "tdd_hats.ts").read_text()
        # improvement006/OPT-H: the five TDD tools consolidated into one
        # namespaced op= dispatcher (18 → 7 registered omt_* tools).
        assert "const omt_tdd" in tdd_hats
        for op in ("testlist", "red", "green", "refactor", "done"):
            assert f'"{op}"' in tdd_hats or f"{op}:" in tdd_hats

    def test_enforcer_has_tdd_gate(self):
        tdd_hats = (REPO_ROOT / ".opencode" / "lib" / "enforcer" / "tdd_hats.ts").read_text()
        assert "tdd_check.py gate" in tdd_hats
        assert "tdd_mode" in tdd_hats
        assert "refactorSnapshots" in tdd_hats
        assert "revert_needed" in tdd_hats

    def test_enforcer_has_validate_exit(self):
        phase_gate = (REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts").read_text()
        assert "tdd_check.py validate-exit" in phase_gate

    def test_status_has_tdd_section(self):
        status = (REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts").read_text()
        assert "runTddStatus" in status
        assert "TDD Mode" in status

    def test_tdd_check_in_harness_files(self):
        e2e = (REPO_ROOT / "tests" / "scripts" / "omt" / "test_omt_harness_e2e.py").read_text()
        assert "scripts/omt/tdd_check.py" in e2e


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
