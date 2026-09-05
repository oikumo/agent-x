"""omt_net behavioral mining — feature_044.mined_behavioral_net (IDEA-004 v2).

Ledger STORE → α-variant observed net + intended-vs-observed drift, proposal-only
(D4): read-only on the supervised net (no revision bump, like sync/synthesize),
ledger-audited (kind net_mine), draft artifacts beside the bundle (D14 runtime
state). Pool nets (D20) mine the same way — drift reports the level gap honestly.

Hermetic via OMT_NET_DIR / OMT_LEDGER_PATH (miner.store_files globs the ledger
parent, so the tmp ledger IS the whole store).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))


def _miner():
    from net import miner  # noqa: PLC0415

    return miner


def _state():
    from net import state  # noqa: PLC0415

    return state


def _cli():
    from net import cli  # noqa: PLC0415

    return cli


def _write_ledger(path: Path, records: list[dict]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def _phase(ts: str, phase: str, feature: str, session: str) -> dict:
    return {"ts": ts, "kind": "phase", "phase": phase, "feature": feature,
            "session": session}


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


class TestGoldenMinerCase:
    """10th golden case (IDEA-004 §8 #6): synthetic traces → known mined net."""

    TRACES = {
        "t1": ["a", "b", "c"],
        "t2": ["a", "b", "c"],
        "t3": ["a", "c", "b"],
        "t4": ["a", "c", "b"],
    }

    def test_causality_parallelism(self) -> None:
        miner = _miner()
        rel = miner.mine_relations(dict(self.TRACES), min_support=2)
        causal = {tuple(item["edge"]) for item in rel["causal"]}
        assert causal == {("a", "b"), ("a", "c")}
        assert rel["parallel"] == [["b", "c"]]
        assert rel["pruned"] == []

    def test_fragment_deterministic_and_namespaced(self) -> None:
        miner = _miner()
        rel = miner.mine_relations(dict(self.TRACES), min_support=2)
        first = json.dumps(miner.build_observed_fragment(rel, dict(self.TRACES)),
                           sort_keys=True)
        second = json.dumps(miner.build_observed_fragment(rel, dict(self.TRACES)),
                            sort_keys=True)
        assert first == second
        frag = json.loads(first)
        assert {t["name"] for t in frag["add_transitions"]} == {
            "m_do_a", "m_do_b", "m_do_c"}
        names = {p["name"] for p in frag["add_places"]}
        assert "m_start" in names and "m_end" in names
        assert not any(n.startswith("f") and n[1].isdigit() for n in names)

    def test_support_pruning_surfaced(self) -> None:
        miner = _miner()
        traces = {f"c{i}": ["a", "b"] for i in range(11)}
        traces["rare"] = ["a", "z"]
        rel = miner.mine_relations(traces, min_support=3)
        causal = {tuple(item["edge"]) for item in rel["causal"]}
        assert ("a", "b") in causal
        assert ("a", "z") not in causal
        assert {"edge": ["a", "z"], "support": 1} in rel["pruned"]


class TestAttribution:
    def test_session_attribution_flags_and_counts(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        ledger = tmp_path / "ledger.jsonl"
        monkeypatch.setenv("OMT_LEDGER_PATH", str(ledger))
        miner = _miner()
        records = [
            _phase("2026-09-01T10:00:00+00:00", "Analysis", "feature_044.x", "s1"),
            {"ts": "2026-09-01T10:05:00+00:00", "kind": "skip", "session": "s1",
             "reason": "x"},
            {"ts": "2026-09-01T10:06:00+00:00", "kind": "skip", "session": "s9",
             "reason": "y"},
        ]
        traces, stats = miner.extract_traces(records, case="feature",
                                             activity_view="phase-flow")
        assert traces["feature_044.x"] == ["phase[Analysis]", "skip"]
        assert stats["attributed_support"] == 1
        assert stats["skipped_reasons"].get("no_case_after_attribution") == 1

    def test_seed_ts_skipped_and_counted(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        miner = _miner()
        records = [
            {"ts": "2024-01-01T00:00:00.000000", "kind": "phase",
             "phase": "Analysis", "feature": "f", "session": "s"},
            _phase("2026-09-01T10:00:00+00:00", "Analysis", "f", "s"),
        ]
        traces, stats = miner.extract_traces(records)
        assert traces["f"] == ["phase[Analysis]"]
        assert stats["skipped_reasons"].get("seed_ts") == 1

    def test_window_last_n(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        miner = _miner()
        records = [
            _phase("2026-09-01T10:00:00+00:00", "Analysis", "old", "s"),
            _phase("2026-09-02T10:00:00+00:00", "Analysis", "new", "s"),
        ]
        traces, stats = miner.extract_traces(records)
        kept = miner.select_window(traces, stats, "last:1")
        assert list(kept) == ["new"]
        assert miner.select_window(traces, stats, "corpus") == traces
        with pytest.raises(ValueError):
            miner.select_window(traces, stats, "recent")


class TestProposalOnly:
    def test_pool_net_untouched_draft_written(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        ledger = tmp_path / "ledger.jsonl"
        monkeypatch.setenv("OMT_LEDGER_PATH", str(ledger))
        state = _state()
        base = tmp_path
        before = _make_pool(base)
        rev_before = before.revision
        marking_before = dict(before.live_marking)
        _write_ledger(ledger, [
            _phase("2026-09-01T10:00:00+00:00", "Analysis", "feature_044.x", "s1"),
            _phase("2026-09-01T11:00:00+00:00", "Design", "feature_044.x", "s1"),
            _phase("2026-09-01T12:00:00+00:00", "Programming", "feature_044.x", "s1"),
        ])
        st, info = state.mine(base, None, reasoning="044 test", session="s1",
                              feature="feature_044.x")
        assert info["applied"] is False
        assert info["pool_net"] is True
        assert info["prefix"] == "m_"
        assert info["would_exceed_cap"] is True  # 12 places + mined ≫ 15
        assert info["places_after"] > 15
        after = state.load(base)
        assert after.revision == rev_before
        assert after.live_marking == marking_before
        assert len(after.net.places) == 12
        # drift is honest about the pool/phase-flow level gap
        assert info["drift"]["intended_level"] == "pool"
        assert "phase[Analysis]" in info["drift"]["mined_only_activities"]
        assert info["empirical"]["place_invariant_count"] >= 1
        assert info["mining"]["cases"] == 1
        # draft artifacts beside the bundle (D14 runtime state)
        assert (base / "META_NET.mined.petri.json").exists()
        assert (base / "mine.draft.manifest.json").exists()
        manifest = json.loads((base / "mine.draft.manifest.json").read_text())
        assert manifest["case"] == "feature"
        assert manifest["records_used"] == 3
        kinds = [json.loads(line)["kind"] for line in
                 ledger.read_text().splitlines() if line.strip()]
        assert kinds[-1] == "net_mine"

    def test_empty_ledger_mines_empty(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        _make_pool(tmp_path)
        _, info = state.mine(tmp_path, {"window": "corpus"}, reasoning="044 test")
        assert info["mining"]["cases"] == 0
        assert info["drift"]["mined_activities"] == []
        assert info["fragment"]["add_transitions"] == []


class TestInvalidParams:
    @pytest.mark.parametrize("params", [
        {"window": "recent"},
        {"window": "last:0"},
        {"min_support": 0},
        {"min_support": "3"},
        {"case": "trace"},
        {"activity_view": "all"},
        {"unknown_key": 1},
        ["corpus"],
    ])
    def test_invalid_mine_params_rejected(
        self, tmp_path, monkeypatch, params
    ) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        state = _state()
        _make_pool(tmp_path)
        with pytest.raises(Exception) as exc:
            state.mine(tmp_path, params, reasoning="044 test")
        assert getattr(exc.value, "code", "") == "invalid_mine_params"


class TestCliDispatch:
    def test_mine_live(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        ledger = tmp_path / "ledger.jsonl"
        monkeypatch.setenv("OMT_LEDGER_PATH", str(ledger))
        cli = _cli()
        _make_pool(tmp_path)
        _write_ledger(ledger, [
            _phase("2026-09-01T10:00:00+00:00", "Analysis", "feature_044.x", "s1"),
            _phase("2026-09-01T11:00:00+00:00", "Design", "feature_044.x", "s1"),
        ])
        code = cli.main(["mine", "--reasoning", "044 cli test",
                         "--feature", "feature_044.x"])
        out = json.loads(capsys.readouterr().out)
        assert code == 0
        assert out["ok"] is True
        assert out["op"] == "mine"
        assert out["applied"] is False
        assert "drift" in out and "empirical" in out and "manifest" in out

    def test_mine_no_net_fails_clean(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
        cli = _cli()
        code = cli.main(["mine", "--reasoning", "044 cli test"])
        out = json.loads(capsys.readouterr().out)
        assert code == 1
        assert out["ok"] is False
        assert out["error"] == "net_not_bootstrapped"
