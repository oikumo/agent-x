"""omt_net WIP pool — feature_048.wip_limited_pool (D20 15-place cap).

Generic pool replaces per-feature partitions: 3 pool places + 5 resources +
3 boundary (+1 archive) = 11–12 places, 2 transitions. Hermetic via
OMT_NET_DIR / OMT_LEDGER_PATH / OMT_NET_FEATURES_DIR / OMT_NET_WORK_MD.
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


def _sync_md():
    from net import sync_md  # noqa: PLC0415

    return sync_md


WORK_MD = """# WORK

## Tasks

- [ ] **feature_001.alpha** — pending row
- [ ] **feature_002.beta** — pending row

## Projects (synced)

| project | state | features |
|---|---|---|
| proj_a | active | feature_001.alpha, feature_002.beta |
"""


def _make_env(tmp_path, monkeypatch):
    net_dir = tmp_path / "net"
    monkeypatch.setenv("OMT_NET_DIR", str(net_dir))
    monkeypatch.setenv("OMT_LEDGER_PATH", str(net_dir / "ledger.jsonl"))
    features = tmp_path / "features"
    features.mkdir(exist_ok=True)
    for d in ("feature_001.alpha", "feature_002.beta"):
        (features / d).mkdir(exist_ok=True)
    work = tmp_path / "WORK.md"
    work.write_text(WORK_MD, encoding="utf-8")
    monkeypatch.setenv("OMT_NET_FEATURES_DIR", str(features))
    monkeypatch.setenv("OMT_NET_WORK_MD", str(work))
    return tmp_path


def _make_pool(base: Path, pending: int = 2, active: int = 0, done: int = 0):
    """Minimal 12-place pool net (mirrors live rev45 structure)."""
    state = _state()
    st = state.init_empty(base)
    seed = {
        "feature_ready": 1, "resource_token": 1, "goal_satisfied": 0,
        "agent_attention": 1, "src_edit_capacity": 1, "tests_capacity": 1,
        "harness_surface_round": 1, "e2e_receipt": 1,
        "work_pending": pending, "work_active": active, "work_done": done,
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


class TestPoolDetect:
    def test_is_pool_true_on_pool_false_on_skeleton(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        state.sync(base, reasoning="bootstrap", session="s1")
        st = state.load(base)
        assert state.is_pool_net(st.net) is False
        _make_pool(base)
        assert state.is_pool_net(state.load(base).net) is True


class TestPoolSync:
    def test_sync_on_pool_emits_no_per_feature_adds(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        _make_pool(base)
        _, info = state.sync(base, reasoning="pool resync", session="s1")
        assert info["proposal"]["add_subnets"] == []
        assert info["proposal"]["disable_subnets"] == []
        assert info["proposal"]["add_resource_places"] == []
        pool = info["proposal"]["pool"]
        assert pool["pending"] == 2 and pool["places"] == 12 and pool["cap"] == 15

    def test_sync_on_skeleton_still_proposes_subnets(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        state.sync(base, reasoning="bootstrap", session="s1")
        _, info = state.sync(base, reasoning="resync", session="s1")
        assert {e["subnet"] for e in info["proposal"]["add_subnets"]} == {
            "feature_001", "feature_002",
        }
        assert "pool" not in info["proposal"]


class TestPlaceCap:
    def test_add_past_15_rejected(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        _make_pool(base)
        with pytest.raises(Exception) as exc:
            state.splice(
                base, "add",
                mutation={
                    "add_places": [{"name": f"q{i}"} for i in range(4)],
                    "add_transitions": [], "add_arcs": [],
                },
                reasoning="cap test", session="s1", feature="feature_048",
            )
        assert getattr(exc.value, "code", "") == "place_cap_exceeded"

    def test_add_at_15_edge_ok(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        _make_pool(base)
        st, _ = state.splice(
            base, "add",
            mutation={
                "add_places": [{"name": f"r{i}"} for i in range(3)],
                "add_transitions": [], "add_arcs": [],
            },
            reasoning="edge", session="s1", feature="feature_048",
        )
        assert len(st.net.places) == 15


class TestPoolResources:
    def test_idle_pool_free_no_conflict(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        st = _make_pool(base, pending=2, active=0)
        rep = state.resource_report(st)
        agent = next(r for r in rep["resources"] if r["place"] == "agent_attention")
        assert agent == {
            "place": "agent_attention", "capacity": 1, "live": 1,
            "capacity_ok": True, "holders": [],
        }
        assert rep["conflicts"] == []

    def test_active_pool_holds_attention(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        _make_pool(base, pending=1, active=0)
        state.fire(base, "work_start", reasoning="t", session="s1")
        rep = state.resource_report(state.load(base))
        agent = next(r for r in rep["resources"] if r["place"] == "agent_attention")
        assert agent["live"] == 0 and agent["holders"] == ["pool"]
        assert agent["capacity_ok"] is True

    def test_blocked_pool_reports_conflict(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        _make_pool(base, pending=1, active=0)
        state.fire(base, "work_start", reasoning="t", session="s1")
        st = state.load(base)
        st.live_marking["work_pending"] = 1  # new work arrives while attention held
        state.save(base, st)
        rep = state.resource_report(state.load(base))
        assert rep["conflicts"] == [{
            "subnet": "pool", "transition": "work_start",
            "blocked_by": ["agent_attention"],
        }]


class TestPoolRender:
    def test_render_includes_pool_counts(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        sync_md = _sync_md()
        base = tmp_path / "net"
        st = _make_pool(base, pending=6, active=0, done=1)
        rep = state.resource_report(st)
        text = sync_md.render_tasks_block(
            st.net, st.live_marking, st.overlay,
            rep["resources"], rep["conflicts"], st.revision,
        )
        assert "Pool: pending=6 active=0 done=1 (places 12/15)" in text
        assert "NEXT: work_start" in text

    def test_render_non_pool_has_no_pool_line(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        sync_md = _sync_md()
        base = tmp_path / "net"
        state.sync(base, reasoning="bootstrap", session="s1")
        st = state.load(base)
        rep = state.resource_report(st)
        text = sync_md.render_tasks_block(
            st.net, st.live_marking, st.overlay,
            rep["resources"], rep["conflicts"], st.revision,
        )
        assert "Pool:" not in text
