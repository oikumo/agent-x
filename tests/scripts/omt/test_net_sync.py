"""omt_net sync op — feature_040.net_composition_supervisor.

net↔reality bootstrap + resync (IDEA-002 v4 §5.1/§11 #6; consolidated design
P6–P8 @ .sandbox/pause_2026-08-30c.md): first call materializes the supervisor
skeleton (boundary ports feature_ready=1 / resource_token=1 / goal_satisfied=0
+ the feature_041 resource catalog: agent_attention / src_edit_capacity /
tests_capacity / harness_surface_round / e2e_receipt, all M0=1 — NO supervisor
transitions in v1) behind the 9-vector conformance gate; every
call then scans reality (feature dirs + WORK.md tasks/projects) and emits a
deterministic PROPOSAL — never auto-applied (D4; the agent applies via splice).
Hermetic via OMT_NET_DIR / OMT_LEDGER_PATH / OMT_NET_FEATURES_DIR /
OMT_NET_WORK_MD env overrides.
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
    """Hermetic reality: 2 feature dirs + a WORK.md (001 active, 002 done)."""
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


def _run(cli, argv, capsys):
    code = cli.main(argv)
    out = json.loads(capsys.readouterr().out)
    return code, out


def _sync(cli, capsys):
    return _run(cli, ["sync", "--session", "s1"], capsys)


def _ledger_records(base: Path) -> list[dict]:
    path = base / "ledger.jsonl"
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class TestSyncBootstrap:
    def test_first_call_materializes_skeleton(self, env, capsys) -> None:
        cli = _cli()
        code, out = _sync(cli, capsys)
        assert code == 0, out
        assert out["ok"] is True
        assert out["op"] == "sync"
        assert out["bootstrap"] is True
        assert out["revision"] == 0
        assert out["conformance"] == {"vectors": 9, "ok": True}
        st = _state().load(env / "net")
        assert st.net.places == {
            "feature_ready",
            "resource_token",
            "goal_satisfied",
            # feature_041 R1: resource catalog (all M0=1, IDEA-002 v4 §2.2)
            "agent_attention",
            "src_edit_capacity",
            "tests_capacity",
            "harness_surface_round",
            "e2e_receipt",
        }
        assert st.net.transitions == set()  # NO supervisor transitions in v1
        assert st.live_marking == {
            "feature_ready": 1,
            "resource_token": 1,
            "goal_satisfied": 0,
            "agent_attention": 1,
            "src_edit_capacity": 1,
            "tests_capacity": 1,
            "harness_surface_round": 1,
            "e2e_receipt": 1,
        }
        assert st.overlay["supervisor"]["places"] == [
            "agent_attention",
            "e2e_receipt",
            "feature_ready",
            "goal_satisfied",
            "harness_surface_round",
            "resource_token",
            "src_edit_capacity",
            "tests_capacity",
        ]
        rec = _ledger_records(env / "net")[-1]
        assert rec["kind"] == "net_sync"
        assert rec["bootstrap"] is True
        assert rec["conformance"] == {"vectors": 9, "ok": True}

    def test_bootstrap_then_probe_works(self, env, capsys) -> None:
        cli = _cli()
        _sync(cli, capsys)
        code, out = _run(cli, ["probe"], capsys)
        assert code == 0
        assert out["ok"] is True

    def test_bootstrap_conformance_failure_blocks_write(self, env, capsys, monkeypatch) -> None:
        from net import conformance  # noqa: PLC0415

        monkeypatch.setattr(
            conformance,
            "run_vectors",
            lambda _dir: [{"id": "v1", "ok": False, "mismatches": ["bounds"]}],
        )
        cli = _cli()
        code, out = _sync(cli, capsys)
        assert code == 1
        assert out["error"] == "conformance_failed"
        assert not _state().is_bootstrapped(env / "net")


class TestSyncScan:
    def test_scan_proposes_subnets_with_checkbox_m0(self, env, capsys) -> None:
        cli = _cli()
        code, out = _sync(cli, capsys)
        assert code == 0, out
        proposal = out["proposal"]
        adds = {e["subnet"]: e for e in proposal["add_subnets"]}
        assert set(adds) == {"feature_001", "feature_002"}
        assert proposal["disable_subnets"] == []
        a1 = adds["feature_001"]
        assert a1["slug"] == "feature_001.alpha"
        assert a1["project"] == "proj_a"
        assert a1["m0"] == "active"
        places = {p["name"]: p["tokens"] for p in a1["mutation"]["add_places"]}
        assert places == {"f001_pending": 0, "f001_active": 1, "f001_done": 0}
        a2 = adds["feature_002"]
        assert a2["m0"] == "done"
        places2 = {p["name"]: p["tokens"] for p in a2["mutation"]["add_places"]}
        assert places2 == {"f002_pending": 0, "f002_active": 0, "f002_done": 1}

    def test_proposal_mutation_uses_subnet_template(self, env, capsys) -> None:
        """P7 lifecycle chain (feature_041 R2 adds the agent_attention
        claim/release): start(pending+feature_ready+agent_attention ->
        active+feature_ready), complete(active -> done+goal_satisfied+agent_attention)."""
        cli = _cli()
        _, out = _sync(cli, capsys)
        mutation = out["proposal"]["add_subnets"][0]["mutation"]
        arcs = {(a["source"], a["target"]) for a in mutation["add_arcs"]}
        assert arcs == {
            ("f001_pending", "f001_start"),
            ("feature_ready", "f001_start"),
            ("agent_attention", "f001_start"),  # feature_041 R2: claim
            ("f001_start", "f001_active"),
            ("f001_start", "feature_ready"),
            ("f001_active", "f001_complete"),
            ("f001_complete", "f001_done"),
            ("f001_complete", "goal_satisfied"),
            ("f001_complete", "agent_attention"),  # feature_041 R2: release
        }
        names = {t["name"] for t in mutation["add_transitions"]}
        assert names == {"f001_start", "f001_complete"}

    def test_scan_skips_existing_subnets(self, env, capsys) -> None:
        cli = _cli()
        _sync(cli, capsys)
        # apply the feature_001 proposal by hand (the D4 path)
        _, out = _run(cli, ["sync"], capsys)
        mutation = out["proposal"]["add_subnets"][0]["mutation"]
        _run(
            cli,
            ["splice", "--mode", "add", "--mutation", json.dumps(mutation),
             "--reasoning", "apply proposal"],
            capsys,
        )
        code, out2 = _sync(cli, capsys)
        assert code == 0
        adds = {e["subnet"] for e in out2["proposal"]["add_subnets"]}
        assert adds == {"feature_002"}  # feature_001 already materialized

    def test_scan_proposes_disable_for_missing_dirs(self, env, capsys) -> None:
        cli = _cli()
        _sync(cli, capsys)
        # hand-materialize a subnet with no feature dir behind it
        mutation = {
            "add_places": [{"name": "f009_pending", "tokens": 1}],
            "add_transitions": [{"name": "f009_start"}],
            "add_arcs": [
                {"source": "f009_pending", "target": "f009_start", "weight": 1}
            ],
        }
        _run(
            cli,
            ["splice", "--mode", "add", "--mutation", json.dumps(mutation),
             "--reasoning", "orphan subnet"],
            capsys,
        )
        code, out = _sync(cli, capsys)
        assert code == 0
        disables = {e["subnet"] for e in out["proposal"]["disable_subnets"]}
        assert "feature_009" in disables

    def test_resync_is_proposal_only_no_revision_bump(self, env, capsys) -> None:
        cli = _cli()
        _sync(cli, capsys)
        code, out = _sync(cli, capsys)
        assert code == 0
        assert out["bootstrap"] is False
        assert out["revision"] == 0  # unchanged
        assert "conformance" not in out  # read-only: no gate run (P8)
        recs = _ledger_records(env / "net")
        assert recs[-1]["kind"] == "net_sync"  # audit never silent (D4)
        assert recs[-1]["bootstrap"] is False

    def test_sync_applies_nothing_d4(self, env, capsys) -> None:
        """The proposal is NEVER auto-applied; the agent applies via splice."""
        cli = _cli()
        code, out = _sync(cli, capsys)
        assert code == 0
        st = _state().load(env / "net")
        assert st.net.places == {
            "feature_ready",
            "resource_token",
            "goal_satisfied",
            "agent_attention",  # feature_041 R1 catalog (all M0=1)
            "src_edit_capacity",
            "tests_capacity",
            "harness_surface_round",
            "e2e_receipt",
        }
        assert st.overlay["subnets"] == {}
        # agent approves + applies the proposal through the splice path
        mutation = out["proposal"]["add_subnets"][0]["mutation"]
        code2, out2 = _run(
            cli,
            ["splice", "--mode", "add", "--mutation", json.dumps(mutation),
             "--reasoning", "approve sync proposal"],
            capsys,
        )
        assert code2 == 0, out2
        st = _state().load(env / "net")
        assert "f001_active" in st.net.places
        subnet = st.overlay["subnets"]["feature_001"]
        assert subnet["ports"]["entry"] == ["agent_attention", "feature_ready"]
        assert subnet["ports"]["exit"] == [
            "agent_attention",
            "feature_ready",
            "goal_satisfied",
        ]
        # feature_041 R3: ports.resources = (entry ∪ exit) ∩ RESOURCE_PLACES
        assert subnet["ports"]["resources"] == ["agent_attention"]
