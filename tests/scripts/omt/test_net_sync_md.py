"""omt_net sync md directions — feature_045.work_md_net_driven.

net_to_md render + md_to_net_propose (D4 proposal-only) + D19 menu block.
Hermetic via OMT_NET_DIR / OMT_LEDGER_PATH / OMT_NET_FEATURES_DIR /
OMT_NET_WORK_MD env overrides. RED-first: imports net.sync_md (not yet
implemented).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))


def _sync_md():
    from net import sync_md  # noqa: PLC0415 (lazy — runnable RED)

    return sync_md


def _cli():
    from net import cli  # noqa: PLC0415

    return cli


def _state():
    from net import state  # noqa: PLC0415

    return state


WORK_MD = """# WORK

## Tasks

- [ ] **feature_003.gamma** — pending row
- [~] **feature_001.alpha** — active row
- [x] **feature_002.beta** — done row

## Projects (synced)

| project | state | features |
|---|---|---|
| proj_a | active | feature_001.alpha, feature_002.beta |
"""


@pytest.fixture()
def env(tmp_path, monkeypatch):
    net_dir = tmp_path / "net"
    monkeypatch.setenv("OMT_NET_DIR", str(net_dir))
    monkeypatch.setenv("OMT_LEDGER_PATH", str(net_dir / "ledger.jsonl"))
    features = tmp_path / "features"
    features.mkdir()
    (features / "feature_001.alpha").mkdir()
    (features / "feature_002.beta").mkdir()
    work = tmp_path / "WORK.md"
    work.write_text(WORK_MD, encoding="utf-8")
    monkeypatch.setenv("OMT_NET_FEATURES_DIR", str(features))
    monkeypatch.setenv("OMT_NET_WORK_MD", str(work))
    return tmp_path


def _bootstrap(env):
    st_mod = _state()
    st, _ = st_mod.sync(env / "net", reasoning="bootstrap", session="s1")
    # apply pending add_subnets deterministically (test-only splice path)
    _, info = st_mod.sync(env / "net", reasoning="resync", session="s1")
    for entry in info["proposal"]["add_subnets"]:
        st_mod.splice(
            env / "net", "add", mutation=entry["mutation"],
            reasoning="test apply", session="s1", feature="feature_045",
        )
    return st_mod.load(env / "net")


class TestSyncMd:
    def test_round_trip_same_enabled(self, env) -> None:
        sync_md = _sync_md()
        st = _bootstrap(env)
        text = sync_md.render_tasks_block(
            st.net, st.live_marking, st.overlay,
            resources=[], conflicts=[], revision=st.revision,
        )
        desired = sync_md.parse_tasks_block(text)
        proposal = sync_md.propose_diff(st.net, st.live_marking, desired)
        assert proposal["fires"] == [] and proposal["blocked"] == []
        assert "net_rev" in text and "NEXT" in text

    def test_proposals_are_enabled(self, env) -> None:
        sync_md = _sync_md()
        st = _bootstrap(env)
        desired = {"01": "active", "02": "done", "03": "pending"}
        proposal = sync_md.propose_diff(st.net, st.live_marking, desired)
        live = tuple(st.live_marking[p] for p in st.net.place_order)
        for t in proposal["fires"]:
            assert st.net.is_enabled_at(live, t), t

    def test_hand_edit_blocked_logs_drift(self, env, capsys) -> None:
        cli = _cli()
        _bootstrap(env)
        work = Path(env / "WORK.md")
        text = work.read_text(encoding="utf-8")
        # activate 002 (done→active needs no valid fire: must block, not apply)
        text = text.replace(
            "- [x] **feature_002.beta**", "- [~] **feature_002.beta**"
        )
        work.write_text(text, encoding="utf-8")
        code = cli.main(["sync", "--direction", "md_to_net_propose",
                         "--session", "s1"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0, out
        assert out["ok"] is True
        assert out["proposals"]["blocked"], out

    def test_resource_block_over_capacity(self, env) -> None:
        sync_md = _sync_md()
        st = _bootstrap(env)
        # both 001 and 002 active: only one agent_attention claim can enable
        proposal = sync_md.propose_diff(
            st.net, st.live_marking, {"01": "active", "02": "active"})
        assert proposal["blocked"] or len(proposal["fires"]) <= 1

    def test_menu_order_next_resources(self, env) -> None:
        sync_md = _sync_md()
        st = _bootstrap(env)
        lines = sync_md.menu_lines(
            enabled=["f002_start", "f001_start"],
            resources=[{"place": "agent_attention", "capacity_ok": True}],
            conflicts=[], revision=st.revision,
        )
        blob = "\n".join(lines)
        assert "NEXT" in blob and "f001_start" in blob
        assert blob.index("f001_start") < blob.index("f002_start")

    def test_cli_net_to_md_dry_run(self, env, capsys) -> None:
        cli = _cli()
        _bootstrap(env)
        code = cli.main(["sync", "--direction", "net_to_md",
                         "--dry-run", "--session", "s1"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0, out
        assert out["ok"] is True and out.get("rendered"), out
