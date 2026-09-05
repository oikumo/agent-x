"""omt_net session-start menu — feature_049.session_start_menu (D19 on pool net).

D19: the 045 Tasks render IS the menu (NEXT + Other + Blocked + Resources +
Pool, rev-stamped). STARTUP reads WORK.md Tasks only, presents options in
order. Fire verifies R == probe revision else refuses + re-renders (D4).

Hermetic via OMT_NET_DIR / OMT_LEDGER_PATH / OMT_NET_FEATURES_DIR /
OMT_NET_WORK_MD. RED-first: menu_lines pool kwarg + fire expected_revision
(not yet implemented).
"""
from __future__ import annotations

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


def _cli():
    from net import cli  # noqa: PLC0415

    return cli


WORK_MD = """# WORK

## Tasks

- [ ] **feature_001.alpha** — pending row

## Projects (synced)

| project | state | features |
|---|---|---|
| proj_a | active | feature_001.alpha |
"""


def _make_env(tmp_path, monkeypatch):
    net_dir = tmp_path / "net"
    monkeypatch.setenv("OMT_NET_DIR", str(net_dir))
    monkeypatch.setenv("OMT_LEDGER_PATH", str(net_dir / "ledger.jsonl"))
    features = tmp_path / "features"
    features.mkdir(exist_ok=True)
    (features / "feature_001.alpha").mkdir(exist_ok=True)
    work = tmp_path / "WORK.md"
    work.write_text(WORK_MD, encoding="utf-8")
    monkeypatch.setenv("OMT_NET_FEATURES_DIR", str(features))
    monkeypatch.setenv("OMT_NET_WORK_MD", str(work))
    return tmp_path


def _make_pool(base: Path, pending: int = 5, active: int = 1, done: int = 1):
    """Minimal 12-place pool net at rev0 (mirrors live rev46 shape)."""
    state = _state()
    st = state.init_empty(base)
    seed = {
        "feature_ready": 1, "resource_token": 1, "goal_satisfied": 0,
        "agent_attention": 0 if active else 1, "src_edit_capacity": 1,
        "tests_capacity": 1, "harness_surface_round": 1, "e2e_receipt": 1,
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


class TestPoolMenu:
    def test_menu_lines_includes_pool_when_provided(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        sync_md = _sync_md()
        lines = sync_md.menu_lines(
            enabled=["work_complete"],
            resources=[{"place": "agent_attention", "capacity_ok": True}],
            conflicts=[], revision=46,
            pool={"pending": 5, "active": 1, "done": 1, "places": 12, "cap": 15},
        )
        blob = "\n".join(lines)
        assert "NEXT: work_complete" in blob
        assert "Pool: pending=5 active=1 done=1 (places 12/15)" in blob
        assert "(net rev 46)" in blob

    def test_menu_lines_without_pool_has_no_pool_line(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        sync_md = _sync_md()
        lines = sync_md.menu_lines(
            enabled=["f001_start"], resources=[], conflicts=[], revision=0,
        )
        assert not any("Pool:" in ln for ln in lines)


class TestPoolRenderNext:
    def test_active_pool_render_next_is_work_complete(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        sync_md = _sync_md()
        base = tmp_path / "net"
        st = _make_pool(base, pending=5, active=1, done=1)
        rep = state.resource_report(st)
        text = sync_md.render_tasks_block(
            st.net, st.live_marking, st.overlay,
            rep["resources"], rep["conflicts"], st.revision,
        )
        assert "NEXT: work_complete (recommended)" in text
        assert "Blocked: work_start" in text
        assert "Pool: pending=5 active=1 done=1 (places 12/15)" in text

    def test_idle_pool_render_next_is_work_start(self, tmp_path, monkeypatch) -> None:
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
        assert "NEXT: work_start (recommended)" in text
class TestStaleRevGuard:
    def test_fire_stale_expected_revision_refuses(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        st = _make_pool(base)
        with pytest.raises(Exception) as exc:
            state.fire(
                base, "work_complete", reasoning="stale test", session="s1",
                expected_revision=st.revision - 1,
            )
        assert getattr(exc.value, "code", "") == "stale_revision"

    def test_fire_matching_expected_revision_ok(self, tmp_path, monkeypatch) -> None:
        _make_env(tmp_path, monkeypatch)
        state = _state()
        base = tmp_path / "net"
        st = _make_pool(base)
        st2 = state.fire(
            base, "work_complete", reasoning="fresh", session="s1",
            expected_revision=st.revision,
        )
        assert st2.revision == st.revision + 1
