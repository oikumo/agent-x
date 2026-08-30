"""Net bundle state store — feature_039.adaptive_net_engine.

Three-file bundle (IDEA-002 §1.4/§7.2): META_NET.petri.json (v1 structure+M0)
+ net_state.sidecar.json (live marking+revision) + supervisor.overlay.json
(composition view); atomic saves with rollback; name-based rebase; revision
guard. Hermetic via OMT_NET_DIR / OMT_LEDGER_PATH env (tmp_path).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))


def _state():
    from net import state  # noqa: PLC0415  (lazy — runnable RED)

    return state


def _hello_bundle(base: Path, state) -> None:
    """p1=1 ->t1-> p2 bundle at revision 0 (via init + splice-free build)."""
    state.init_empty(base)
    st = state.load(base)
    st.net.add_place("p1", tokens=1)
    st.net.add_place("p2", tokens=0)
    st.net.add_transition("t1")
    st.net.add_input("p1", "t1")
    st.net.add_output("t1", "p2")
    st.live_marking = {"p1": 1, "p2": 0}
    state.save(base, st)


@pytest.fixture()
def bundle(tmp_path, monkeypatch):
    state = _state()
    monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
    monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    _hello_bundle(tmp_path, state)
    return tmp_path


class TestBootstrap:
    def test_load_missing_net_raises(self, tmp_path, monkeypatch) -> None:
        state = _state()
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        with pytest.raises(state.NetNotBootstrappedError):
            state.load(tmp_path)

    def test_init_empty_round_trip(self, tmp_path, monkeypatch) -> None:
        state = _state()
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path))
        state.init_empty(tmp_path)
        st = state.load(tmp_path)
        assert st.revision == 0
        assert st.net.places == set()
        assert st.overlay["subnets"] == {}
        assert st.overlay["disabled"] == []


class TestFire:
    def test_fire_applies_persists_and_ledgers(self, bundle) -> None:
        state = _state()
        st = state.fire(bundle, "t1", reasoning="cycle test", session="s1")
        assert st.live_marking == {"p1": 0, "p2": 1}
        assert st.revision == 1
        reloaded = state.load(bundle)
        assert reloaded.live_marking == {"p1": 0, "p2": 1}
        assert reloaded.revision == 1
        assert reloaded.overlay["revision"] == 1
        ledger = (bundle / "ledger.jsonl").read_text(encoding="utf-8")
        rec = json.loads(ledger.strip().splitlines()[-1])
        assert rec["kind"] == "net_fire"
        assert rec["transition"] == "t1"
        assert rec["revision"] == 1
        assert rec["reasoning"] == "cycle test"

    def test_fire_disabled_raises_and_writes_nothing(self, bundle) -> None:
        state = _state()
        from net import errors  # noqa: PLC0415

        state.fire(bundle, "t1", reasoning="drain", session="s1")  # p1 now empty
        before = {p.name: p.read_bytes() for p in bundle.glob("*.json")}
        ledger_before = (bundle / "ledger.jsonl").read_text(encoding="utf-8")
        with pytest.raises(errors.TransitionNotEnabledError):
            state.fire(bundle, "t1", reasoning="x", session="s1")
        after = {p.name: p.read_bytes() for p in bundle.glob("*.json")}
        assert before == after
        assert (bundle / "ledger.jsonl").read_text(encoding="utf-8") == ledger_before


class TestAtomicSave:
    def test_rollback_restores_all_files(self, bundle, monkeypatch) -> None:
        state = _state()
        before = {p.name: p.read_bytes() for p in bundle.glob("*.json")}
        st = state.load(bundle)
        st.live_marking = {"p1": 0, "p2": 1}
        st.revision = 99
        orig_replace = state.os.replace

        def boom(src, dst):
            if str(dst).endswith("supervisor.overlay.json"):
                raise OSError("simulated write failure")
            return orig_replace(src, dst)

        monkeypatch.setattr(state.os, "replace", boom)
        with pytest.raises(OSError):
            state.save(bundle, st)
        after = {p.name: p.read_bytes() for p in bundle.glob("*.json")}
        assert before == after


class TestRebase:
    def test_rebase_by_name_keeps_tokens_new_places_get_m0(self, bundle) -> None:
        state = _state()
        st = state.load(bundle)
        st.live_marking = {"p1": 0, "p2": 5}
        new_net = st.net
        new_net.add_place("p3", tokens=2)
        rebased = state.rebase_marking(st.live_marking, new_net)
        assert rebased == {"p1": 0, "p2": 5, "p3": 2}

    def test_revision_mismatch_refused(self, bundle) -> None:
        state = _state()
        overlay_path = bundle / "supervisor.overlay.json"
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        overlay["revision"] = 42
        overlay_path.write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(state.RevisionMismatchError):
            state.load(bundle)
