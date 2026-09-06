"""g.net gate — feature_050.net_as_gate (Alt A Net-as-Gate).

RED spec: net becomes permission-to-act. Gate helper `net.gate` does not
exist yet → all tests FAIL (RED). GREEN will implement gate.py + harden
fire/invariant + harnessc WORK.md canonical check.
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
    from net import gate  # noqa: PLC0415 — must exist in GREEN

    return gate


def _bundle(tmp_path, monkeypatch):
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
        "agent_attention": 1,
        "src_edit_capacity": 1,
        "work_pending": 1,
        "work_active": 0,
    }
    state.save(tmp_path, st)
    return tmp_path


def _make_concurrent(base) -> None:
    """Bump a test bundle to real concurrency (C1, feature_053: the gate's
    fire-receipt requirement engages only when net_marking(active>1))."""
    from net import state  # noqa: PLC0415

    st = state.load(base)
    st.live_marking = dict(st.live_marking)
    st.live_marking["work_active"] = 2
    state.save(base, st)


class TestNetGate:
    def test_blocks_without_fire_receipt(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch)
        _make_concurrent(base)  # C1: receipt required only when concurrent
        res = gate.check_edit_allowed(
            base, path="src/foo.py", has_fire_receipt=False
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_NOT_ENABLED"

    def test_stale_revision_refused(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch)
        res = gate.check_edit_allowed(
            base,
            path="src/foo.py",
            has_fire_receipt=True,
            expected_revision=999,
            live_revision=1,
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_STALE_REV"

    def test_drifted_blocks(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch)
        res = gate.check_edit_allowed(
            base, path="src/foo.py", has_fire_receipt=True, drifted=True
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_DRIFT_CONFLICT"

    def test_conflicts_block(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch)
        res = gate.check_edit_allowed(
            base,
            path="src/foo.py",
            has_fire_receipt=True,
            conflicts=[{"place": "agent_attention"}],
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_DRIFT_CONFLICT"

    def test_net_down_fail_closed(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        (tmp_path / "ledger.jsonl").write_text("")
        res = gate.check_edit_allowed(
            tmp_path, path="src/foo.py", has_fire_receipt=False, net_available=False
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_DOWN"

    def test_break_glass_allows_with_expiry(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch)
        res = gate.check_edit_allowed(
            base,
            path="src/foo.py",
            has_fire_receipt=False,
            net_available=False,
            break_glass_scope_all=True,
        )
        assert res["allowed"] is True
        assert res["break_glass"] is True


def _fire_record(transition: str, revision: int = 1) -> dict:
    """A recent (within the 8h window) net_fire ledger record."""
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "net_fire",
        "session": "ses_test",
        "transition": transition,
        "revision": revision,
        "reasoning": "test",
    }


class TestReceiptFilter:
    """feature_050 wrap-up: only _start-suffixed fires grant permission
    (AGENTS.md NEVER: fire(work_start) required)."""

    def test_work_complete_only_ledger_refused(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        base = _bundle(tmp_path, monkeypatch)
        _make_concurrent(base)  # C1: receipt requirement is concurrency-gated
        (tmp_path / "ledger.jsonl").write_text(
            json.dumps(_fire_record("work_complete")) + "\n", encoding="utf-8"
        )
        res = gate.check_edit_allowed(
            base, path="src/foo.py", has_fire_receipt=False
        )
        assert res["allowed"] is False
        assert res["code"] == "ERR_NET_NOT_ENABLED"

    def test_work_start_ledger_allowed(self, tmp_path, monkeypatch) -> None:
        gate = _gate()
        _bundle(tmp_path, monkeypatch)
        (tmp_path / "ledger.jsonl").write_text(
            json.dumps(_fire_record("work_start")) + "\n", encoding="utf-8"
        )
        res = gate.check_edit_allowed(
            tmp_path, path="src/foo.py", has_fire_receipt=False
        )
        assert res["allowed"] is True
        assert res["code"] == "OK"


class TestGateCliOp:
    """feature_050 wrap-up: live gate-op wiring — drift mirrors _invariant,
    fail-closed on load error (D3), expected_revision flows through."""

    def _run_gate(self, capsys, extra: list[str] | None = None):
        from net import cli  # noqa: PLC0415

        code = cli.main(
            ["gate", "--path", "src/foo.py", "--session", "ses_test", *(extra or [])]
        )
        out = json.loads(capsys.readouterr().out)
        return code, out

    def test_unbootstrapped_fails_closed_net_down(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        code, out = self._run_gate(capsys)
        assert code == 1
        assert out["allowed"] is False
        assert out["code"] == "ERR_NET_DOWN"

    def test_bootstrapped_with_work_start_receipt_ok(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        from net import state  # noqa: PLC0415

        _bundle(tmp_path, monkeypatch)
        st = state.load(tmp_path)
        (tmp_path / "ledger.jsonl").write_text(
            json.dumps(_fire_record("work_start", revision=st.revision)) + "\n",
            encoding="utf-8",
        )
        code, out = self._run_gate(capsys)
        assert code == 0
        assert out["allowed"] is True
        assert out["code"] == "OK"

    def test_ledger_revision_mismatch_blocks_drift(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        _bundle(tmp_path, monkeypatch)
        (tmp_path / "ledger.jsonl").write_text(
            json.dumps(_fire_record("work_start", revision=999)) + "\n",
            encoding="utf-8",
        )
        code, out = self._run_gate(capsys)
        assert code == 1
        assert out["allowed"] is False
        assert out["code"] == "ERR_NET_DRIFT_CONFLICT"
