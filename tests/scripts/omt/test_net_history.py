"""Ledger replay + dashboard snapshot — feature_043.meta_net_dashboard (design §1).

`history.replay` folds the ledger store (ALL archives + hot, append order)
into per-revision marking snapshots reusing the engine appliers; no new
semantics. `build_snapshot` gates the fold against the live bundle
(fail-closed replay_mismatch). Hermetic via tmp stores except the LIVE golden
(read-only on the real runtime bundle; skips when unbootstrapped).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))

REPO_ROOT = Path(__file__).resolve().parents[3]
LIVE_BASE = REPO_ROOT / ".meta" / ".omt"


def _history():
    from net import history  # noqa: PLC0415  (lazy — runnable RED)

    return history


def _state():
    from net import state  # noqa: PLC0415

    return state


def _write_store(store: Path, files: dict[str, list[dict]]) -> Path:
    store.mkdir(parents=True, exist_ok=True)
    for name, records in files.items():
        with open(store / name, "a", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
    return store


GENESIS = {
    "kind": "net_sync", "bootstrap": True, "revision": 0,
    "reasoning": "t", "session": "s",
}

ADD_AB = {
    "kind": "net_splice", "mode": "add", "revision": 1,
    "mutation": {
        "add_places": [{"name": "p_ready", "tokens": 1}, {"name": "p_done", "tokens": 0}],
        "add_transitions": [{"name": "do_p"}],
        "add_arcs": [
            {"source": "p_ready", "target": "do_p", "weight": 1},
            {"source": "do_p", "target": "p_done", "weight": 1},
        ],
    },
    "reasoning": "t", "session": "s", "feature": "feature_043.x",
}

FIRE_P = {
    "kind": "net_fire", "transition": "do_p", "revision": 2,
    "reasoning": "t", "session": "s",
}

# Zero-token fragment: undo-add with forbid succeeds on it (live code refuses
# token-holding removes — the replay mirrors that refusal exactly).
ADD_ZERO = {
    "kind": "net_splice", "mode": "add", "revision": 1,
    "mutation": {
        "add_places": [{"name": "z_ready", "tokens": 0}, {"name": "z_done", "tokens": 0}],
        "add_transitions": [{"name": "do_z"}],
        "add_arcs": [
            {"source": "z_ready", "target": "do_z", "weight": 1},
            {"source": "do_z", "target": "z_done", "weight": 1},
        ],
    },
    "reasoning": "t", "session": "s", "feature": "feature_043.x",
}


class TestReplayVectors:
    def test_genesis_add_fire(self, tmp_path) -> None:
        history = _history()
        store = _write_store(tmp_path / "store", {"ledger.jsonl": [GENESIS, ADD_AB, FIRE_P]})
        snaps = history.replay(store)
        assert [s["revision"] for s in snaps] == [0, 1, 2]
        assert snaps[0]["marking"]["feature_ready"] == 1
        assert snaps[1]["marking"]["p_ready"] == 1
        assert snaps[2]["marking"]["p_ready"] == 0
        assert snaps[2]["marking"]["p_done"] == 1

    def test_remove_with_reroute(self, tmp_path) -> None:
        history = _history()
        remove = {
            "kind": "net_splice", "mode": "remove", "revision": 3,
            "mutation": {
                "remove_places": ["p_ready"], "remove_transitions": [],
                "token_policy": "reroute", "reroute": {"p_ready": "p_done"},
            },
            "removed": {"places": [], "transitions": [], "arcs": []},
            "token_policy": "reroute",
            "reasoning": "t", "session": "s", "feature": "f",
        }
        store = _write_store(
            tmp_path / "store", {"ledger.jsonl": [GENESIS, ADD_AB, FIRE_P, remove]})
        snaps = history.replay(store)
        assert snaps[-1]["revision"] == 3
        assert "p_ready" not in snaps[-1]["marking"]
        # p_done held 1 (fired) + rerouted 0 → still 1
        assert snaps[-1]["marking"]["p_done"] == 1

    def test_mapless_reroute_recovers_to_archive_pool(self, tmp_path) -> None:
        """Archive-done recovery rule: a reroute policy WITHOUT a persisted
        map (live disable drops it) sends holders to archive_pool."""
        history = _history()
        add_archive = {
            "kind": "net_splice", "mode": "add", "revision": 1,
            "mutation": {"add_places": [{"name": "archive_pool", "tokens": 0}],
                         "add_transitions": [], "add_arcs": []},
            "reasoning": "t", "session": "s", "feature": "f",
        }
        add_frag = {
            "kind": "net_splice", "mode": "add", "revision": 2,
            "mutation": {
                "add_places": [{"name": "q_ready", "tokens": 1}],
                "add_transitions": [], "add_arcs": []},
            "reasoning": "t", "session": "s", "feature": "f",
        }
        remove = {
            "kind": "net_splice", "mode": "remove", "revision": 3,
            "mutation": {"remove_places": ["q_ready"], "remove_transitions": [],
                         "token_policy": "reroute"},
            "removed": {"places": [], "transitions": [], "arcs": []},
            "token_policy": "reroute",
            "reasoning": "t", "session": "s", "feature": "f",
        }
        store = _write_store(tmp_path / "store", {
            "ledger.jsonl": [GENESIS, add_archive, add_frag, remove]})
        snaps = history.replay(store)
        assert snaps[-1]["marking"]["archive_pool"] == 1
        assert "q_ready" not in snaps[-1]["marking"]

    def test_mapless_reroute_without_archive_fails(self, tmp_path) -> None:
        history = _history()
        remove = {
            "kind": "net_splice", "mode": "remove", "revision": 2,
            "mutation": {"remove_places": ["p_ready"], "remove_transitions": [],
                         "token_policy": "reroute"},
            "removed": {"places": [], "transitions": [], "arcs": []},
            "token_policy": "reroute",
            "reasoning": "t", "session": "s", "feature": "f",
        }
        store = _write_store(tmp_path / "store", {
            "ledger.jsonl": [GENESIS, ADD_AB, remove]})
        with pytest.raises(Exception) as exc:
            history.replay(store)
        assert getattr(exc.value, "code", "") == "invalid_replay"

    def test_undo_of_add_forbid_removes(self, tmp_path) -> None:
        history = _history()
        undo = {
            "kind": "net_splice", "mode": "undo", "undoes": 1, "revision": 2,
            "reasoning": "t", "session": "s", "feature": "f",
        }
        store = _write_store(
            tmp_path / "store", {"ledger.jsonl": [GENESIS, ADD_ZERO, undo]})
        snaps = history.replay(store)
        assert snaps[-1]["revision"] == 2
        assert "z_ready" not in snaps[-1]["marking"]

    def test_undo_add_refuses_token_holders_like_live(self, tmp_path) -> None:
        """Forbid-remove of a token-holding place refuses in live code
        (`_remove_nodes` → token_policy_violation); replay mirrors it."""
        history = _history()
        state = _state()
        undo = {
            "kind": "net_splice", "mode": "undo", "undoes": 1, "revision": 2,
            "reasoning": "t", "session": "s", "feature": "f",
        }
        store = _write_store(
            tmp_path / "store", {"ledger.jsonl": [GENESIS, ADD_AB, undo]})
        with pytest.raises(Exception) as exc:
            history.replay(store)
        assert getattr(exc.value, "code", "") == "invalid_replay"

    def test_undo_of_remove_restores_live_tokens(self, tmp_path) -> None:
        history = _history()
        remove = {
            "kind": "net_splice", "mode": "remove", "revision": 3,
            "mutation": {
                "remove_places": ["p_done"], "remove_transitions": [],
                "token_policy": "reroute", "reroute": {"p_done": "p_ready"},
            },
            "removed": {
                "places": [{"name": "p_done", "tokens": 0, "live": 1}],
                "transitions": [],
                "arcs": [{"source": "do_p", "target": "p_done", "weight": 1}],
            },
            "token_policy": "reroute",
            "reasoning": "t", "session": "s", "feature": "f",
        }
        undo = {
            "kind": "net_splice", "mode": "undo", "undoes": 3, "revision": 4,
            "reasoning": "t", "session": "s", "feature": "f",
        }
        store = _write_store(
            tmp_path / "store",
            {"ledger.jsonl": [GENESIS, ADD_AB, FIRE_P, remove, undo]})
        snaps = history.replay(store)
        assert snaps[-1]["revision"] == 4
        # recorded live tokens restored (not M0); the reroute residue on
        # p_ready stays — exactly like live `_splice_undo`
        assert snaps[-1]["marking"]["p_done"] == 1
        assert snaps[-1]["marking"]["p_ready"] == 1

    def test_skip_kinds_emit_no_snapshots(self, tmp_path) -> None:
        history = _history()
        records = [
            GENESIS, ADD_AB,
            {"kind": "net_splice", "mode": "repair", "revision": 1,
             "reasoning": "t", "session": "s", "feature": "f"},
            {"kind": "net_sync", "bootstrap": False, "revision": 1,
             "reasoning": "t", "session": "s"},
            {"kind": "net_synthesize", "revision": 1, "applied": False,
             "reasoning": "t", "session": "s", "feature": "f"},
        ]
        store = _write_store(tmp_path / "store", {"ledger.jsonl": records})
        snaps = history.replay(store)
        assert [s["revision"] for s in snaps] == [0, 1]

    def test_unknown_kind_fails_closed(self, tmp_path) -> None:
        history = _history()
        store = _write_store(tmp_path / "store", {
            "ledger.jsonl": [GENESIS, {"kind": "net_frobnicate", "revision": 9}]})
        with pytest.raises(Exception) as exc:
            history.replay(store)
        assert getattr(exc.value, "code", "") == "invalid_replay"


class TestLiveGolden:
    @pytest.mark.skipif(
        not (LIVE_BASE / "META_NET.petri.json").is_file(),
        reason="harness net not bootstrapped — no live runtime to replay",
    )
    def test_replay_matches_live_bundle(self) -> None:
        history = _history()
        state = _state()
        snaps = history.replay(LIVE_BASE)
        st = state.load(LIVE_BASE)
        assert snaps, "live store replayed zero snapshots"
        assert snaps[-1]["revision"] == st.revision
        assert snaps[-1]["marking"] == st.live_marking


class TestBuildSnapshot:
    def _bundle(self, tmp_path, monkeypatch):
        """Hermetic bundle matching the replay final state exactly
        (genesis 3 ports + ADD_AB + FIRE_P at revision 2)."""
        state = _state()
        base = tmp_path / "net"
        monkeypatch.setenv("OMT_NET_DIR", str(base))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(base / "ledger.jsonl"))
        st = state.init_empty(base)
        for pl, tok in (("feature_ready", 1), ("resource_token", 1),
                        ("goal_satisfied", 0)):
            st.net.add_place(pl, tok)
        st.net.add_place("p_ready", 1)
        st.net.add_place("p_done", 0)
        st.net.add_transition("do_p")
        st.net.add_input("p_ready", "do_p")
        st.net.add_output(transition="do_p", place="p_done")
        live = {"feature_ready": 1, "resource_token": 1, "goal_satisfied": 0,
                "p_ready": 0, "p_done": 1}
        st.live_marking = dict(live)
        st.revision = 2
        state.save(base, st)
        return base

    def test_schema_keys(self, tmp_path, monkeypatch) -> None:
        history = _history()
        base = self._bundle(tmp_path, monkeypatch)
        store = _write_store(tmp_path / "store", {"ledger.jsonl": [GENESIS, ADD_AB, FIRE_P]})
        snap = history.build_snapshot(base, store=store)
        assert snap["format"] == "meta-net-dashboard-snapshot"
        assert snap["version"] == 1
        assert snap["net_revision"] == 2
        assert set(snap["place_order"]) == {
            "feature_ready", "resource_token", "goal_satisfied", "p_ready", "p_done"}
        assert snap["net"]["places"] and snap["net"]["transitions"] and snap["net"]["arcs"]
        assert snap["positions"]["p_ready"] != snap["positions"]["p_done"]
        assert [s["revision"] for s in snap["snapshots"]] == [0, 1, 2]
        # markings track structure per revision: genesis has no p_* places
        assert "p_ready" not in snap["snapshots"][0]["marking"]
        assert snap["snapshots"][1]["marking"]["p_ready"] == 1
        assert snap["snapshots"][2]["marking"]["p_done"] == 1

    def test_mismatch_fails_closed(self, tmp_path, monkeypatch) -> None:
        history = _history()
        state = _state()
        base = self._bundle(tmp_path, monkeypatch)
        store = _write_store(tmp_path / "store", {"ledger.jsonl": [GENESIS, ADD_AB, FIRE_P]})
        st = state.load(base)
        st.live_marking["p_done"] = 0  # hand-mutation behind the replay's back
        state.save(base, st)
        with pytest.raises(Exception) as exc:
            history.build_snapshot(base, store=store)
        assert getattr(exc.value, "code", "") == "replay_mismatch"
