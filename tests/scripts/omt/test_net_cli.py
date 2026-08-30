"""omt_net CLI ops — feature_039.adaptive_net_engine.

Canonical op enum (IDEA-002 v4 §5.0, closed set): probe|fire|splice|sync|
synthesize|invariant. feature_039 ships probe/fire/invariant; the rest are
reserved → clean not_implemented envelopes (bootstrap ordering §5.1).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))


def _cli():
    from net import cli  # noqa: PLC0415  (lazy — runnable RED)

    return cli


@pytest.fixture()
def bundle(tmp_path, monkeypatch):
    from net import state  # noqa: PLC0415

    monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
    monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    state.init_empty(tmp_path)
    st = state.load(tmp_path)
    st.net.add_place("p1", tokens=1)
    st.net.add_place("p2", tokens=0)
    st.net.add_transition("t1")
    st.net.add_input("p1", "t1")
    st.net.add_output("t1", "p2")
    st.live_marking = {"p1": 1, "p2": 0}
    state.save(tmp_path, st)
    return tmp_path


def _run(cli, argv, capsys):
    code = cli.main(argv)
    out = json.loads(capsys.readouterr().out)
    return code, out


class TestBootstrapOrdering:
    def test_probe_no_net_fails_clean(self, tmp_path, monkeypatch, capsys) -> None:
        cli = _cli()
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        code, out = _run(cli, ["probe"], capsys)
        assert code == 1
        assert out["ok"] is False
        assert out["error"] == "net_not_bootstrapped"

    def test_invariant_no_net_fails_clean(self, tmp_path, monkeypatch, capsys) -> None:
        cli = _cli()
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        code, out = _run(cli, ["invariant"], capsys)
        assert code == 1
        assert out["ok"] is False
        assert out["error"] == "net_not_bootstrapped"


class TestProbe:
    def test_probe_reports_marking_enabled_advice(self, bundle, capsys) -> None:
        cli = _cli()
        code, out = _run(cli, ["probe"], capsys)
        assert code == 0
        assert out["ok"] is True
        assert out["op"] == "probe"
        assert out["revision"] == 0
        assert out["marking"] == {"p1": 1, "p2": 0}
        assert out["enabled"] == ["t1"]
        advice = out["advice"]
        assert advice["deadlocks"] == [[0, 1]]
        assert advice["bounded"] is True
        assert advice["place_invariants"] == [[1, 1]]


class TestFireOp:
    def test_fire_updates_marking_and_ledgers(self, bundle, capsys) -> None:
        cli = _cli()
        code, out = _run(
            cli, ["fire", "--transition", "t1", "--reasoning", "cli test", "--session", "s9"],
            capsys,
        )
        assert code == 0
        assert out["ok"] is True
        assert out["op"] == "fire"
        assert out["revision"] == 1
        assert out["marking"] == {"p1": 0, "p2": 1}
        code2, out2 = _run(cli, ["probe"], capsys)
        assert out2["marking"] == {"p1": 0, "p2": 1}
        ledger = (bundle / "ledger.jsonl").read_text(encoding="utf-8")
        assert json.loads(ledger.strip().splitlines()[-1])["kind"] == "net_fire"

    def test_fire_disabled_fails_clean(self, bundle, capsys) -> None:
        cli = _cli()
        _run(cli, ["fire", "--transition", "t1", "--reasoning", "x"], capsys)
        code, out = _run(cli, ["fire", "--transition", "t1", "--reasoning", "x"], capsys)
        assert code == 1
        assert out["ok"] is False
        assert out["error"] == "transition_not_enabled"


class TestInvariantOp:
    def test_invariant_reports_invariants_and_no_drift(self, bundle, capsys) -> None:
        cli = _cli()
        _run(cli, ["fire", "--transition", "t1", "--reasoning", "x"], capsys)
        code, out = _run(cli, ["invariant"], capsys)
        assert code == 0
        assert out["ok"] is True
        assert out["op"] == "invariant"
        assert out["place_invariants"] == [[1, 1]]
        assert out["live_marking_invariants_hold"] is True
        assert out["drift"]["drifted"] is False
        assert out["drift"]["net_revision"] == 1
        assert out["drift"]["ledger_revision"] == 1

    def test_invariant_surfaces_drift_and_logs(self, bundle, capsys) -> None:
        cli = _cli()
        from net import state  # noqa: PLC0415

        st = state.load(bundle)
        st.revision = 7  # hand-mutation behind the ledger's back
        state.save(bundle, st)
        code, out = _run(cli, ["invariant"], capsys)
        assert code == 0
        assert out["drift"]["drifted"] is True
        assert out["drift"]["net_revision"] == 7
        drift_log = bundle / "harness.net.drift.jsonl"
        assert drift_log.exists()
        rec = json.loads(drift_log.read_text(encoding="utf-8").strip().splitlines()[-1])
        assert rec["kind"] == "net_drift"
        assert rec["net_revision"] == 7


class TestReservedOps:
    @pytest.mark.parametrize("op", ["splice", "sync", "synthesize"])
    def test_reserved_ops_not_implemented(self, bundle, capsys, op) -> None:
        cli = _cli()
        code, out = _run(cli, [op], capsys)
        assert code == 1
        assert out["ok"] is False
        assert out["error"] == "not_implemented"
        assert out["op"] == op
        assert "feature_040" in out["message"]

    def test_unknown_op_rejected(self, bundle, capsys) -> None:
        cli = _cli()
        with pytest.raises(SystemExit):
            cli.main(["frobnicate"])  # argparse choices= reject, exit 2
