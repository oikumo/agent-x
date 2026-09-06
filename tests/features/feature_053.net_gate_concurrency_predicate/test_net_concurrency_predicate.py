"""C1 net_gate_concurrency_predicate — feature_053.

g.net engages only under real concurrency (net_marking(active>1)); solo
sessions revert to phase-gate only (no fire receipt required).

Contract (GREEN pins the Round-1 implementation):
- solo (work_active<=1, <=1 f{N}_active holder) + no receipt → ALLOW solo
- concurrent (work_active>1 or 2+ holders) + no receipt → BLOCK NOT_ENABLED
- concurrent + work_start receipt → ALLOW
- unreadable bundle (no marking, no base) → fail-closed (BLOCK)
- drift / net-down / stale-rev still BLOCK even when solo (fail-closed first)
- live CLI gate op on a solo bundle with an empty ledger → ALLOW solo
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))


def _gate():
    from net import gate  # noqa: PLC0415

    return gate


def _bundle(tmp_path, monkeypatch, work_active: int = 1):
    """Hermetic pool bundle with a chosen work_active level (default solo)."""
    from net import state  # noqa: PLC0415

    monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
    monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    state.init_empty(tmp_path)
    st = state.load(tmp_path)
    st.net.add_place("agent_attention", tokens=1)
    st.net.add_place("src_edit_capacity", tokens=1)
    st.net.add_place("work_pending", tokens=1)
    st.net.add_place("work_active", tokens=0)
    st.net.add_transition("work_start")
    st.net.add_input("work_pending", "work_start")
    st.net.add_input("agent_attention", "work_start")
    st.net.add_output("work_start", "work_active")
    st.live_marking = {
        "agent_attention": 0,
        "src_edit_capacity": 1,
        "work_pending": 0,
        "work_active": work_active,
    }
    state.save(tmp_path, st)
    return tmp_path


def _fire_record(transition: str, revision: int = 1) -> dict:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "net_fire",
        "session": "ses_test",
        "transition": transition,
        "revision": revision,
        "reasoning": "test",
    }


class TestSoloBypass:
    def test_solo_allows_without_receipt(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=1)
        res = gate.check_edit_allowed(base, path="src/foo.py")
        assert res["allowed"] is True
        assert res["code"] == "OK"
        assert res.get("solo") is True

    def test_idle_allows_without_receipt(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=0)
        res = gate.check_edit_allowed(base, path="src/foo.py")
        assert res["allowed"] is True
        assert res.get("solo") is True

    def test_explicit_solo_marking_allows(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        _bundle(tmp_path, monkeypatch, work_active=1)
        res = gate.check_edit_allowed(
            tmp_path, path="src/foo.py", live_marking={"work_active": 1}
        )
        assert res["allowed"] is True
        assert res.get("solo") is True


class TestConcurrentEngages:
    def test_work_active_two_blocks_without_receipt(
        self, tmp_path, monkeypatch
    ) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=2)
        res = gate.check_edit_allowed(base, path="src/foo.py")
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_NOT_ENABLED"

    def test_two_subnet_holders_block_without_receipt(
        self, tmp_path, monkeypatch
    ) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=1)
        res = gate.check_edit_allowed(
            base,
            path="src/foo.py",
            live_marking={
                "work_active": 1,
                "f039_active": 1,
                "f040_active": 1,
            },
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_NOT_ENABLED"

    def test_single_subnet_holder_stays_solo(
        self, tmp_path, monkeypatch
    ) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=1)
        res = gate.check_edit_allowed(
            base,
            path="src/foo.py",
            live_marking={"work_active": 1, "f039_active": 1},
        )
        assert res["allowed"] is True
        assert res.get("solo") is True

    def test_concurrent_with_work_start_receipt_allows(
        self, tmp_path, monkeypatch
    ) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=2)
        (tmp_path / "ledger.jsonl").write_text(
            json.dumps(_fire_record("work_start")) + "\n", encoding="utf-8"
        )
        res = gate.check_edit_allowed(base, path="src/foo.py")
        assert res["allowed"] is True
        assert res["code"] == "OK"
        assert res.get("solo") is not True


class TestFailClosedFirst:
    def test_unreadable_bundle_blocks(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        (tmp_path / "ledger.jsonl").write_text("")
        missing = tmp_path / "no-such-bundle"
        res = gate.check_edit_allowed(missing, path="src/foo.py")
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_NOT_ENABLED"

    def test_drift_blocks_even_when_solo(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=1)
        res = gate.check_edit_allowed(base, path="src/foo.py", drifted=True)
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_DRIFT_CONFLICT"

    def test_net_down_blocks_even_when_solo(
        self, tmp_path, monkeypatch
    ) -> None:
        gate = _gate()
        _bundle(tmp_path, monkeypatch, work_active=1)
        res = gate.check_edit_allowed(
            tmp_path,
            path="src/foo.py",
            net_available=False,
            live_marking={"work_active": 1},
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_DOWN"

    def test_stale_rev_blocks_even_when_solo(
        self, tmp_path, monkeypatch
    ) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch, work_active=1)
        res = gate.check_edit_allowed(
            base,
            path="src/foo.py",
            expected_revision=999,
            live_revision=1,
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_STALE_REV"


class TestGateCliSolo:
    def test_cli_solo_bundle_empty_ledger_allows(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        from net import cli  # noqa: PLC0415

        _bundle(tmp_path, monkeypatch, work_active=1)
        (tmp_path / "ledger.jsonl").write_text("")
        code = cli.main(["gate", "--path", "src/foo.py", "--session", "ses"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["allowed"] is True
        assert out["code"] == "OK"

    def test_cli_concurrent_bundle_empty_ledger_blocks(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        from net import cli  # noqa: PLC0415

        _bundle(tmp_path, monkeypatch, work_active=2)
        (tmp_path / "ledger.jsonl").write_text("")
        code = cli.main(["gate", "--path", "src/foo.py", "--session", "ses"])
        out = json.loads(capsys.readouterr().out)
        assert code == 1
        assert out["allowed"] is False
        assert out["code"] == "ERR_NET_NOT_ENABLED"
