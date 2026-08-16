#!/usr/bin/env python3
"""Golden tests for P3-8: two-hats message for both-blocked states
(feature_028, meta_harness_3 v1.2).

R6: the fix must branch on the IR-derived HAT_RULES (rules["src"]/rules["tests"]
both False), NOT on hardcoded state names — so it stays correct if the .omt
@hat config changes a state's allow-set. The synthetic-config golden proves
the message is config-driven.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

from tdd import gates  # noqa: E402


def _args(path: str = "src/foo.py", is_tests: bool = False, session: str = "s"):
    return SimpleNamespace(path=path, is_tests=is_tests, session=session)


class TestTwoHatsMessage:
    def test_both_blocked_states_say_nothing_editable(self, monkeypatch):
        """P3-8: testlist/done block BOTH src+tests — the message must say so
        (today it misleadingly says 'Only src/ edits allowed', eval §3.3)."""
        for state_name in ("testlist", "done"):
            monkeypatch.setattr(
                gates, "get_tdd_state", lambda _s, _n=state_name: _n)
            res = gates.cmd_gate(_args())
            assert res["allowed"] is False
            assert "nothing editable" in res["reason"], state_name
            assert "Only src/ edits allowed" not in res["reason"], state_name
            assert "omt_tdd{op:red}" in res["reason"], state_name

    def test_message_is_config_driven_not_state_name(self, monkeypatch):
        """R6: a SYNTHETIC hat config (state names the hat map never heard of)
        drives the same message purely from the allow-set."""
        synthetic = gates._derive_hat_rules({
            "tdd.frozen": {"allow": ""},       # both blocked, unknown state name
            "tdd.srconly": {"allow": "src/"},  # src-only, unknown state name
        })
        monkeypatch.setattr(gates, "HAT_RULES", synthetic)
        monkeypatch.setattr(gates, "get_tdd_state", lambda _s: "frozen")
        res = gates.cmd_gate(_args())
        assert res["allowed"] is False
        assert "nothing editable" in res["reason"]
        monkeypatch.setattr(gates, "get_tdd_state", lambda _s: "srconly")
        blocked_tests = gates.cmd_gate(_args(path="tests/foo.py", is_tests=True))
        assert blocked_tests["allowed"] is False
        assert "Only src/ edits allowed" in blocked_tests["reason"]
        assert "nothing editable" not in blocked_tests["reason"]

    def test_single_allow_states_keep_their_messages(self, monkeypatch):
        """Characterization guard: red says tests-only, green says src-only
        (unchanged by the P3-8 fix)."""
        monkeypatch.setattr(gates, "get_tdd_state", lambda _s: "red")
        res = gates.cmd_gate(_args())
        assert "Only tests/ edits allowed" in res["reason"]
        monkeypatch.setattr(gates, "get_tdd_state", lambda _s: "green")
        res = gates.cmd_gate(_args(path="tests/foo.py", is_tests=True))
        assert "Only src/ edits allowed" in res["reason"]
