"""omt_net splice op — feature_040.net_composition_supervisor.

Atomic structural transactions (IDEA-002 v4 §3/§5.0; consolidated design
P1–P5/P8/P10 @ .sandbox/pause_2026-08-30c.md): modes add|remove|disable|
undo|repair; token policies forbid|reroute|drain; validate-all-then-apply;
9-vector conformance gate pre-save; derived overlay (f{N}_ prefix membership
+ boundary ports); net_splice/net_disable ledger records.
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


def _state():
    from net import state  # noqa: PLC0415  (lazy — runnable RED)

    return state


@pytest.fixture()
def bundle(tmp_path, monkeypatch):
    """p1=1 ->t1-> p2 bundle at revision 0 (feature_039 fixture pattern)."""
    state = _state()
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


def _splice(cli, capsys, mode, mutation=None, subnet=None, feature=""):
    argv = ["splice", "--mode", mode, "--reasoning", "test", "--session", "s1"]
    if mutation is not None:
        argv += ["--mutation", json.dumps(mutation)]
    if subnet is not None:
        argv += ["--subnet", subnet]
    if feature:
        argv += ["--feature", feature]
    return _run(cli, argv, capsys)


def _ledger_records(base: Path) -> list[dict]:
    path = base / "ledger.jsonl"
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _add_f1_subnet(base: Path, *, pending_tokens: int = 0) -> None:
    """Direct state edit: a minimal f1_ subnet (pending ->start-> active)."""
    state = _state()
    st = state.load(base)
    st.net.add_place("f1_pending", tokens=pending_tokens)
    st.net.add_place("f1_active", tokens=0)
    st.net.add_transition("f1_start")
    st.net.add_input("f1_pending", "f1_start")
    st.net.add_output(transition="f1_start", place="f1_active")
    st.live_marking = {**st.live_marking, "f1_pending": pending_tokens, "f1_active": 0}
    state.save(base, st)


class TestSpliceAdd:
    def test_add_updates_net_marking_and_ledger(self, bundle, capsys) -> None:
        cli = _cli()
        mutation = {
            "add_places": [{"name": "f1_pending", "tokens": 1}],
            "add_transitions": [{"name": "f1_start"}],
            "add_arcs": [{"source": "f1_pending", "target": "f1_start", "weight": 1}],
        }
        code, out = _splice(cli, capsys, "add", mutation, feature="feature_040.x")
        assert code == 0
        assert out["ok"] is True
        assert out["op"] == "splice"
        assert out["mode"] == "add"
        assert out["revision"] == 1
        assert out["marking"] == {"p1": 1, "p2": 0, "f1_pending": 1}
        assert out["conformance"] == {"vectors": 9, "ok": True}
        st = _state().load(bundle)
        assert "f1_pending" in st.net.places
        assert "f1_start" in st.net.transitions
        rec = _ledger_records(bundle)[-1]
        assert rec["kind"] == "net_splice"
        assert rec["mode"] == "add"
        assert rec["mutation"] == mutation
        assert rec["reasoning"] == "test"
        assert rec["session"] == "s1"
        assert rec["feature"] == "feature_040.x"
        assert rec["revision"] == 1
        assert rec["conformance"] == {"vectors": 9, "ok": True}

    def test_add_arc_direction_by_node_kinds(self, bundle, capsys) -> None:
        cli = _cli()
        mutation = {
            "add_places": [{"name": "p3", "tokens": 0}],
            "add_transitions": [{"name": "t2"}],
            "add_arcs": [
                {"source": "p2", "target": "t2", "weight": 2},  # place->transition = input
                {"source": "t2", "target": "p3", "weight": 1},  # transition->place = output
            ],
        }
        code, out = _splice(cli, capsys, "add", mutation)
        assert code == 0, out
        st = _state().load(bundle)
        assert st.net.inputs["t2"] == {"p2": 2}
        assert st.net.outputs["t2"] == {"p3": 1}

    def test_add_validate_all_then_apply(self, bundle, capsys) -> None:
        cli = _cli()
        before = {p.name: p.read_bytes() for p in bundle.glob("*.json")}
        mutation = {
            "add_places": [
                {"name": "ok_place", "tokens": 0},
                {"name": "p1", "tokens": 0},  # duplicate -> whole mutation rejected
            ]
        }
        code, out = _splice(cli, capsys, "add", mutation)
        assert code == 1
        assert out["ok"] is False
        assert out["error"] == "invalid_mutation"
        assert {p.name: p.read_bytes() for p in bundle.glob("*.json")} == before
        assert _ledger_records(bundle) == []

    def test_add_unknown_arc_endpoint_fails(self, bundle, capsys) -> None:
        cli = _cli()
        mutation = {"add_arcs": [{"source": "p1", "target": "nope", "weight": 1}]}
        code, out = _splice(cli, capsys, "add", mutation)
        assert code == 1
        assert out["error"] == "invalid_mutation"

    def test_add_derives_overlay_subnets_and_ports(self, bundle, capsys) -> None:
        """P10: overlay recomputed at save — f{N}_ membership + boundary ports."""
        cli = _cli()
        mutation = {
            "add_places": [
                {"name": "f1_pending", "tokens": 1},
                {"name": "f1_active", "tokens": 0},
            ],
            "add_transitions": [{"name": "f1_start"}],
            "add_arcs": [
                {"source": "p2", "target": "f1_start", "weight": 1},
                {"source": "f1_pending", "target": "f1_start", "weight": 1},
                {"source": "f1_start", "target": "f1_active", "weight": 1},
            ],
        }
        code, out = _splice(cli, capsys, "add", mutation)
        assert code == 0, out
        st = _state().load(bundle)
        overlay = st.overlay
        assert overlay["supervisor"] == {"places": ["p1", "p2"], "transitions": ["t1"]}
        assert overlay["subnets"]["feature_1"] == {
            "prefix": "f1_",
            "places": ["f1_active", "f1_pending"],
            "transitions": ["f1_start"],
            "ports": {"entry": ["p2"], "exit": [], "resources": []},
        }
        assert overlay["disabled"] == []


class TestSpliceConformanceGate:
    def test_conformance_failure_blocks_write(self, bundle, capsys, monkeypatch) -> None:
        from net import conformance  # noqa: PLC0415

        monkeypatch.setattr(
            conformance,
            "run_vectors",
            lambda _dir: [{"id": "v1", "ok": False, "mismatches": ["deadlocks"]}],
        )
        cli = _cli()
        before = {p.name: p.read_bytes() for p in bundle.glob("*.json")}
        code, out = _splice(
            cli, capsys, "add", {"add_places": [{"name": "px", "tokens": 0}]}
        )
        assert code == 1
        assert out["ok"] is False
        assert out["error"] == "conformance_failed"
        assert {p.name: p.read_bytes() for p in bundle.glob("*.json")} == before
        assert _ledger_records(bundle) == []


class TestSpliceRemove:
    def test_remove_forbid_refuses_live_tokens(self, bundle, capsys) -> None:
        cli = _cli()
        before = {p.name: p.read_bytes() for p in bundle.glob("*.json")}
        code, out = _splice(cli, capsys, "remove", {"remove_places": ["p1"]})
        assert code == 1
        assert out["error"] == "token_policy_violation"
        assert {p.name: p.read_bytes() for p in bundle.glob("*.json")} == before
        assert _ledger_records(bundle) == []

    def test_remove_forbid_emptied_place_ok(self, bundle, capsys) -> None:
        cli = _cli()
        _run(cli, ["fire", "--transition", "t1", "--reasoning", "empty p1"], capsys)
        code, out = _splice(cli, capsys, "remove", {"remove_places": ["p1"]})
        assert code == 0, out
        assert out["marking"] == {"p2": 1}
        st = _state().load(bundle)
        assert st.net.places == {"p2"}
        assert st.net.inputs["t1"] == {}  # arcs touching p1 filtered by rebuild
        rec = _ledger_records(bundle)[-1]
        assert rec["kind"] == "net_splice"
        assert rec["mode"] == "remove"
        assert rec["removed"]["places"] == [{"name": "p1", "tokens": 1, "live": 0}]
        assert {a["source"] for a in rec["removed"]["arcs"]} <= {"p1", "t1"}

    def test_remove_reroute_moves_tokens(self, bundle, capsys) -> None:
        cli = _cli()
        mutation = {
            "remove_places": ["p1"],
            "token_policy": "reroute",
            "reroute": {"p1": "p2"},
        }
        code, out = _splice(cli, capsys, "remove", mutation)
        assert code == 0, out
        assert out["marking"] == {"p2": 1}  # p1's live token moved to p2

    def test_remove_reroute_requires_target_for_tokens(self, bundle, capsys) -> None:
        cli = _cli()
        mutation = {"remove_places": ["p1"], "token_policy": "reroute", "reroute": {}}
        code, out = _splice(cli, capsys, "remove", mutation)
        assert code == 1
        assert out["error"] == "token_policy_violation"

    def test_remove_drain_consumes_then_removes(self, bundle, capsys) -> None:
        cli = _cli()
        code, out = _splice(
            cli, capsys, "remove", {"remove_places": ["p1"], "token_policy": "drain"}
        )
        assert code == 0, out
        assert out["marking"] == {"p2": 1}  # t1 fired during drain

    def test_remove_drain_no_progress_fails(self, bundle, capsys) -> None:
        state = _state()
        st = state.load(bundle)
        st.net.add_place("p3", tokens=2)  # no transition consumes from p3
        st.live_marking = {**st.live_marking, "p3": 2}
        state.save(bundle, st)
        cli = _cli()
        code, out = _splice(
            cli, capsys, "remove", {"remove_places": ["p3"], "token_policy": "drain"}
        )
        assert code == 1
        assert out["error"] == "drain_no_progress"


class TestSpliceDisable:
    def test_disable_removes_prefixed_nodes_and_archives(self, bundle, capsys) -> None:
        _add_f1_subnet(bundle, pending_tokens=1)
        cli = _cli()
        mutation = {"token_policy": "reroute", "reroute": {"f1_pending": "p1"}}
        code, out = _splice(cli, capsys, "disable", mutation, subnet="feature_1")
        assert code == 0, out
        st = _state().load(bundle)
        assert st.net.places == {"p1", "p2"}
        assert st.net.transitions == {"t1"}
        assert st.live_marking["p1"] == 2  # rerouted token
        overlay = st.overlay
        assert "feature_1" not in overlay["subnets"]
        assert overlay["disabled"] == ["feature_1"]
        rec = _ledger_records(bundle)[-1]
        assert rec["kind"] == "net_disable"
        assert rec["subnet"] == "feature_1"
        removed = rec["removed"]
        assert {p["name"] for p in removed["places"]} == {"f1_pending", "f1_active"}
        assert removed["places"][0]["live"] in (0, 1)  # live tokens recorded
        assert {t["name"] for t in removed["transitions"]} == {"f1_start"}
        assert len(removed["arcs"]) == 2

    def test_disable_forbid_refuses_live_tokens(self, bundle, capsys) -> None:
        _add_f1_subnet(bundle, pending_tokens=1)
        cli = _cli()
        code, out = _splice(cli, capsys, "disable", subnet="feature_1")
        assert code == 1
        assert out["error"] == "token_policy_violation"

    def test_disable_unknown_subnet_fails(self, bundle, capsys) -> None:
        cli = _cli()
        code, out = _splice(cli, capsys, "disable", subnet="feature_9")
        assert code == 1
        assert out["error"] == "unknown_subnet"


class TestSpliceUndo:
    def test_undo_add_removes_added_nodes(self, bundle, capsys) -> None:
        cli = _cli()
        mutation = {
            "add_places": [{"name": "f2_pending", "tokens": 0}],
            "add_transitions": [{"name": "f2_start"}],
        }
        code, _ = _splice(cli, capsys, "add", mutation)
        assert code == 0
        code, out = _splice(cli, capsys, "undo")
        assert code == 0, out
        assert out["mode"] == "undo"
        assert out["undoes"] == 1
        assert out["marking"] == {"p1": 1, "p2": 0}
        st = _state().load(bundle)
        assert "f2_pending" not in st.net.places
        rec = _ledger_records(bundle)[-1]
        assert rec["kind"] == "net_splice"
        assert rec["mode"] == "undo"
        assert rec["undoes"] == 1

    def test_undo_remove_readds_structure_and_live_tokens(self, bundle, capsys) -> None:
        state = _state()
        st = state.load(bundle)
        st.net.add_place("q1", tokens=2)
        st.live_marking = {**st.live_marking, "q1": 2}
        state.save(bundle, st)
        cli = _cli()
        mutation = {
            "remove_places": ["q1"],
            "token_policy": "reroute",
            "reroute": {"q1": "p1"},
        }
        code, _ = _splice(cli, capsys, "remove", mutation)
        assert code == 0
        code, out = _splice(cli, capsys, "undo")
        assert code == 0, out
        st = _state().load(bundle)
        assert "q1" in st.net.places
        assert st.net.initial_marking["q1"] == 2
        assert st.live_marking["q1"] == 2  # recorded live tokens restored

    def test_undo_disable_restores_subnet_and_disabled_list(self, bundle, capsys) -> None:
        _add_f1_subnet(bundle, pending_tokens=0)
        cli = _cli()
        code, _ = _splice(cli, capsys, "disable", subnet="feature_1")
        assert code == 0
        code, out = _splice(cli, capsys, "undo")
        assert code == 0, out
        st = _state().load(bundle)
        assert {"f1_pending", "f1_active"} <= st.net.places
        assert "f1_start" in st.net.transitions
        assert st.overlay["disabled"] == []
        assert "feature_1" in st.overlay["subnets"]

    def test_undo_nothing_to_undo(self, bundle, capsys) -> None:
        cli = _cli()
        code, out = _splice(cli, capsys, "undo")
        assert code == 1
        assert out["error"] == "nothing_to_undo"


class TestSpliceRepair:
    def test_repair_realigns_overlay_revision(self, bundle, capsys) -> None:
        overlay_path = bundle / "supervisor.overlay.json"
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        overlay["revision"] = 42
        overlay_path.write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(_state().RevisionMismatchError):
            _state().load(bundle)
        cli = _cli()
        code, out = _splice(cli, capsys, "repair")
        assert code == 0, out
        assert out["mode"] == "repair"
        assert out["revision"] == 0
        st = _state().load(bundle)  # load no longer refuses
        assert st.overlay["revision"] == st.revision
        rec = _ledger_records(bundle)[-1]
        assert rec["kind"] == "net_splice"
        assert rec["mode"] == "repair"

    def test_repair_missing_overlay_nodes_fails(self, bundle, capsys) -> None:
        overlay_path = bundle / "supervisor.overlay.json"
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        overlay["subnets"]["feature_7"] = {
            "prefix": "f7_",
            "places": ["f7_nope"],
            "transitions": [],
            "ports": {"entry": [], "exit": [], "resources": []},
        }
        overlay_path.write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
        cli = _cli()
        code, out = _splice(cli, capsys, "repair")
        assert code == 1
        assert out["error"] == "overlay_nodes_missing"
        assert "f7_nope" in out["message"]


class TestSpliceArgs:
    def test_splice_requires_mode(self, bundle, capsys) -> None:
        cli = _cli()
        with pytest.raises(SystemExit):
            cli.main(["splice", "--reasoning", "x"])

    def test_splice_invalid_mutation_json(self, bundle, capsys) -> None:
        cli = _cli()
        code, out = _run(
            cli, ["splice", "--mode", "add", "--mutation", "not json", "--reasoning", "x"],
            capsys,
        )
        assert code == 1
        assert out["error"] == "invalid_mutation"

    def test_disable_requires_subnet(self, bundle, capsys) -> None:
        cli = _cli()
        code, out = _run(
            cli, ["splice", "--mode", "disable", "--reasoning", "x"], capsys
        )
        assert code == 1
        assert out["error"] == "invalid_mutation"
