#!/usr/bin/env python3
"""Golden tests for P1-1: feature-scoped TDD state derivation (feature_028).

R11 (meta_harness_3 v1.2): the TDD cycle belongs to the FEATURE, not the
session. A new session declaring omt_phase must NOT shadow the prior
session's red/green records (eval §3.1 root cause: get_session_records is
session-scoped — a new session's phase record makes `mine` non-empty and the
prior session's TDD records fall out of view → get_tdd_state → 'testlist').
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

from tdd import state  # noqa: E402

FEATURE = "feature_028.feature_scoped_gating"


@pytest.fixture()
def ledger(tmp_path, monkeypatch):
    """Hermetic ledger redirect (pattern: test_ledger_rotation.py)."""
    path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(state, "LEDGER_PATH", path)
    return path


def _write(path: Path, records: list[dict]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


class TestFeatureScopedTddState:
    def test_two_session_resume_preserves_tdd_state(self, ledger):
        """R11: prior session red+green; new session phase-only → preserved."""
        _write(ledger, [
            {"kind": "phase", "session": "ses_prior", "feature": FEATURE,
             "tdd_mode": True, "ts": "2026-08-15T10:00:00+00:00"},
            {"kind": "tdd_testlist", "session": "ses_prior", "feature": FEATURE,
             "behaviors": ["b1"], "ts": "2026-08-15T10:01:00+00:00"},
            {"kind": "tdd", "session": "ses_prior", "feature": FEATURE,
             "state": "red", "test_node": "t.py::test_a", "verified": True,
             "ts": "2026-08-15T10:02:00+00:00"},
            {"kind": "tdd", "session": "ses_prior", "feature": FEATURE,
             "state": "green", "test_node": "t.py::test_a",
             "ts": "2026-08-15T10:03:00+00:00"},
            # New session: ONLY a phase record (the §3.1 resume scenario).
            {"kind": "phase", "session": "ses_new", "feature": FEATURE,
             "tdd_mode": True, "ts": "2026-08-16T09:00:00+00:00"},
        ])
        assert state.get_tdd_state("ses_new") == "green"          # NOT testlist
        assert state.get_current_test_node("ses_new") == "t.py::test_a"
        assert len(state.get_tdd_cycles(FEATURE)) == 2

    def test_feature_scope_isolates_other_features(self, ledger):
        """A session whose feature has no TDD records stays at testlist."""
        _write(ledger, [
            {"kind": "phase", "session": "ses_a", "feature": "feature_other.x",
             "tdd_mode": True, "ts": "2026-08-15T10:00:00+00:00"},
            {"kind": "tdd", "session": "ses_a", "feature": "feature_other.x",
             "state": "green", "test_node": "t.py::test_b",
             "ts": "2026-08-15T10:02:00+00:00"},
            {"kind": "phase", "session": "ses_b", "feature": FEATURE,
             "tdd_mode": True, "ts": "2026-08-16T09:00:00+00:00"},
        ])
        assert state.get_tdd_state("ses_b") == "testlist"
        assert state.get_current_test_node("ses_b") is None

    def test_phase_without_feature_keeps_legacy_session_scope(self, ledger):
        """feature='' phase record → legacy session-scoped derivation."""
        _write(ledger, [
            {"kind": "phase", "session": "ses_c", "feature": "",
             "tdd_mode": True, "ts": "2026-08-16T09:00:00+00:00"},
            {"kind": "tdd", "session": "ses_other", "feature": FEATURE,
             "state": "green", "test_node": "t.py::test_c",
             "ts": "2026-08-16T09:01:00+00:00"},
        ])
        assert state.get_tdd_state("ses_c") == "testlist"
