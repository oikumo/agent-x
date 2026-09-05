"""omt_net goal synthesis — feature_042.goal_net_synthesis (IDEA-002 §4, F4-bounded).

Deterministic template composition → splice-ready fragment, proposal-only (D4):
task→chain, dependency→arc, resource→capacity arcs, acceptance→verified place.
Pool nets (D20 15-cap) never auto-apply — synthesize returns the fragment for
the agent to apply via splice (which enforces the cap + conformance gate).

Hermetic via OMT_NET_DIR / OMT_LEDGER_PATH.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))


def _state():
    from net import state  # noqa: PLC0415

    return state


def _cli():
    from net import cli  # noqa: PLC0415

    return cli


def _make_pool(base: Path):
    """Minimal 12-place pool net (mirrors live rev45 structure)."""
    state = _state()
    st = state.init_empty(base)
    seed = {
        "feature_ready": 1, "resource_token": 1, "goal_satisfied": 0,
        "agent_attention": 1, "src_edit_capacity": 1, "tests_capacity": 1,
        "harness_surface_round": 1, "e2e_receipt": 1,
        "work_pending": 2, "work_active": 0, "work_done": 0,
        "archive_pool": 0,
    }
    for pl, tok in seed.items():
        st.net.add_place(pl, tok)
    st.net.add_transition("work_start")
    st.net.add_transition("work_complete")
    st.net.add_input("agent_attention", "work_start")
    st.net.add_input("feature_ready", "work_start")
    st.net.add_input("work_pending", "work_start")
    st.net.add_output("work_start", "feature_ready")
    st.net.add_output("work_start", "work_active")
    st.net.add_input("work_active", "work_complete")
    st.net.add_output("work_complete", "agent_attention")
    st.net.add_output("work_complete", "goal_satisfied")
    st.net.add_output("work_complete", "work_done")
    st.live_marking = dict(seed)
    state.save(base, st)
    return state.load(base)


def _make_skeleton(base: Path):
    """Pre-pool skeleton net (sync bootstrap, no pool places)."""
    state = _state()
    state.sync(base, reasoning="bootstrap", session="s1")
    return state.load(base)


GOAL_SINGLE = {"tasks": [{"id": "X"}]}

GOAL_RICH = {"tasks": [
    {"id": "A", "needs": ["src_edit_capacity"], "acceptance": "A works"},
    {"id": "B", "after": ["A"], "needs": ["tests_capacity"]},
]}


class TestTemplateMapping:
    def test_single_task_chain(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        frag = state.build_goal_fragment(GOAL_SINGLE, "f042_")
        names = {p["name"] for p in frag["add_places"]}
        assert names == {"f042_X_ready", "f042_X_done"}
        assert [t["name"] for t in frag["add_transitions"]] == ["f042_do_X"]
        arcs = {(a["source"], a["target"]) for a in frag["add_arcs"]}
        assert ("f042_X_ready", "f042_do_X") in arcs
        assert ("f042_do_X", "f042_X_done") in arcs

    def test_resource_need_wires_capacity_self_loop(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        frag = state.build_goal_fragment(
            {"tasks": [{"id": "A", "needs": ["src_edit_capacity"]}]}, "f042_")
        arcs = {(a["source"], a["target"]) for a in frag["add_arcs"]}
        # borrow modeling: claim + release (self-loop preserves the token)
        assert ("src_edit_capacity", "f042_do_A") in arcs
        assert ("f042_do_A", "src_edit_capacity") in arcs

    def test_dependency_arc_done_to_do(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        frag = state.build_goal_fragment(
            {"tasks": [{"id": "A"}, {"id": "B", "after": ["A"]}]}, "f042_")
        arcs = {(a["source"], a["target"]) for a in frag["add_arcs"]}
        assert ("f042_A_done", "f042_do_B") in arcs

    def test_acceptance_adds_verified_place(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        frag = state.build_goal_fragment(
            {"tasks": [{"id": "A", "acceptance": "A works"}]}, "f042_")
        names = {p["name"] for p in frag["add_places"]}
        assert "f042_A_verified" in names
        arcs = {(a["source"], a["target"]) for a in frag["add_arcs"]}
        assert ("f042_do_A", "f042_A_verified") in arcs

    def test_deterministic_ordering(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        goal = {"tasks": [
            {"id": "B", "after": ["A"], "needs": ["tests_capacity"]},
            {"id": "A", "needs": ["src_edit_capacity"], "acceptance": "A works"},
        ]}
        first = json.dumps(state.build_goal_fragment(goal, "f042_"), sort_keys=True)
        second = json.dumps(state.build_goal_fragment(goal, "f042_"), sort_keys=True)
        assert first == second


class TestProposalOnly:
    def test_pool_net_returns_proposal_without_mutation(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        base = tmp_path
        before = _make_pool(base)
        rev_before = before.revision
        marking_before = dict(before.live_marking)
        st, info = state.synthesize(
            base, GOAL_SINGLE,
            reasoning="042 test", session="s1", feature="feature_042.x",
        )
        assert info["applied"] is False
        assert info["pool_net"] is True
        assert "fragment" in info and "add_places" in info["fragment"]
        after = state.load(base)
        assert after.revision == rev_before
        assert after.live_marking == marking_before
        assert len(after.net.places) == 12

    def test_cap_analysis_flags_overflow(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        base = tmp_path
        _make_pool(base)  # 12 places; 2-task rich fragment adds ≥4 new places
        _, info = state.synthesize(
            base, GOAL_RICH,
            reasoning="042 test", session="s1", feature="feature_042.x",
        )
        assert info["would_exceed_cap"] is True
        assert info["places_after"] > 15

    def test_skeleton_net_reports_no_cap_overflow_for_single(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        base = tmp_path
        _make_skeleton(base)
        _, info = state.synthesize(
            base, GOAL_SINGLE,
            reasoning="042 test", session="s1", feature="feature_042.x",
        )
        assert info["pool_net"] is False
        assert info["applied"] is False
        assert info["would_exceed_cap"] is False


class TestInvalidGoals:
    @pytest.mark.parametrize("goal", [
        {},
        {"tasks": []},
        {"tasks": [{"id": ""}]},
        {"tasks": [{"id": "has space"}]},
        {"tasks": [{"id": "A"}, {"id": "A"}]},
        {"tasks": [{"id": "B", "after": ["GHOST"]}]},
        {"tasks": [{"id": "A", "needs": ["no_such_place"]}]},
    ])
    def test_invalid_goal_rejected(self, tmp_path, monkeypatch, goal) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        base = tmp_path
        _make_pool(base)
        with pytest.raises(Exception) as exc:
            state.synthesize(
                base, goal, reasoning="042 test",
                session="s1", feature="feature_042.x",
            )
        assert getattr(exc.value, "code", "") == "invalid_goal"


class TestCliDispatch:
    def test_synthesize_live_not_reserved(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        cli = _cli()
        _make_pool(tmp_path)
        code = cli.main([
            "synthesize", "--mutation", json.dumps(GOAL_SINGLE),
            "--feature", "feature_042.x", "--reasoning", "042 cli test",
        ])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["ok"] is True
        assert out["op"] == "synthesize"
        assert out["applied"] is False
        assert "fragment" in out
