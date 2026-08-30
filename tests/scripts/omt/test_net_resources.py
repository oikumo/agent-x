"""omt_net resource places & concurrency — feature_041.resource_places_concurrency.

Core 3/3 of meta_harness_concurrent (D16 SSOT; design R1–R8 @
.sandbox/pause_2026-08-30d.md; canonical semantics IDEA-002 v4 §2 — ALL five
catalog capacities are 1 per §2.2, the IDEA-005 example's 2/3 is a sketch):

- R1: sync() bootstrap materializes the resource catalog
  (agent_attention / src_edit_capacity / tests_capacity /
  harness_surface_round / e2e_receipt — all M0=1).
- R2: _subnet_mutation wires agent_attention — f{N}_start claims (input),
  f{N}_complete releases (output) → serial-mirror conflict trap (§2.3).
- R3: derive_overlay ports.resources = sorted((entry ∪ exit) ∩ RESOURCE_PLACES)
  — stays a pure function of the net (P10 intact).
- R4: state.resource_report(st) + ADDITIVE invariant-envelope keys
  resources[] (capacity/live/capacity_ok/holders) + conflicts[] (pending
  subnets whose f{N}_start is not enabled; blocked_by = empty unprefixed
  input places).
- R5: resync of pre-041 bundles emits ONE add_resource_places proposal entry
  (missing places + retrofit arcs for unwired subnets; D4 — never
  auto-applied; apply BEFORE any pending add_subnets entry).
- R6: state.lifecycle_sync_hook(event) — fail-open, skip silently when
  unbootstrapped, proposal-only, one-line stdout; wired into project.py
  cmd_new/link/close/archive/reopen + new_feature.py --project link.

Hermetic via OMT_NET_DIR / OMT_LEDGER_PATH / OMT_NET_FEATURES_DIR /
OMT_NET_WORK_MD (+ OMT_PROJECTS_ROOT / OMT_PROJECTS_ARCHIVE / OMT_WORK_PATH
for the lifecycle-hook integration tests).
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


RESOURCE_PLACES = (
# TA: xref: xref: feature_041 design R1-R8 (resume @ .sandbox/pause_2026-08-30e.md): TestBootstrapResourceCatalog=R1 · TestSubnetAgentAttentionWiring=R2 (+R4 envelope/conflict pins) · TestResyncResourceProposal=R5 (+R3 ports.resources) · TestLifecycleSyncHook=R6 · R7=this file + sentinel bridge · R8=no op/budget churn. RED baseline at pause: 21 failed (18 here + 3 evolved pins in test_net_sync.py) / 6 passed; GREEN touches scripts/omt/net/state.py + net/cli.py + project.py + new_feature.py only.
    "agent_attention",
    "src_edit_capacity",
    "tests_capacity",
    "harness_surface_round",
    "e2e_receipt",
)
BOUNDARY = {"feature_ready", "resource_token", "goal_satisfied"}

WORK_MD = """# WORK

## Tasks

- [ ] **feature_001.alpha** — pending row
- [ ] **feature_002.beta** — pending row

## Projects (synced)

| project | state | features |
|---|---|---|
| proj_a | active | feature_001.alpha, feature_002.beta |
"""


def _make_env(tmp_path, monkeypatch, work_md: str = WORK_MD, dirs=("feature_001.alpha", "feature_002.beta")):
    """Hermetic reality: feature dirs + a WORK.md (checkbox M0 per row)."""
    net_dir = tmp_path / "net"
    monkeypatch.setenv("OMT_NET_DIR", str(net_dir))
    monkeypatch.setenv("OMT_LEDGER_PATH", str(net_dir / "ledger.jsonl"))
    features = tmp_path / "features"
    features.mkdir(exist_ok=True)
    for d in dirs:
        (features / d).mkdir(exist_ok=True)
    work = tmp_path / "WORK.md"
    work.write_text(work_md, encoding="utf-8")
    monkeypatch.setenv("OMT_NET_FEATURES_DIR", str(features))
    monkeypatch.setenv("OMT_NET_WORK_MD", str(work))
    return tmp_path


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Default reality: feature_001 + feature_002 both PENDING."""
    return _make_env(tmp_path, monkeypatch)


def _run(cli, argv, capsys):
    code = cli.main(argv)
    out = json.loads(capsys.readouterr().out)
    return code, out


def _sync(cli, capsys):
    return _run(cli, ["sync", "--session", "s1"], capsys)


def _apply(cli, capsys, mutation, reasoning="apply proposal"):
    return _run(
        cli,
        ["splice", "--mode", "add", "--mutation", json.dumps(mutation),
         "--reasoning", reasoning],
        capsys,
    )


def _fire(cli, capsys, transition):
    return _run(
        cli, ["fire", "--transition", transition, "--reasoning", "t"], capsys
    )


def _ledger_records(base: Path) -> list[dict]:
    path = base / "ledger.jsonl"
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _legacy_bundle(base: Path) -> None:
    """A pre-041 bundle: 3 boundary ports only (feature_040 skeleton), rev 0."""
    state = _state()
    st = state.init_empty(base)
    st.net.add_place("feature_ready", 1)
    st.net.add_place("resource_token", 1)
    st.net.add_place("goal_satisfied", 0)
    st.live_marking = {"feature_ready": 1, "resource_token": 1, "goal_satisfied": 0}
    state.save(base, st)


def _legacy_subnet_mutation(n: str) -> dict:
    """Pre-041 lifecycle chain template: NO agent_attention wiring."""
    pending, active, done = f"f{n}_pending", f"f{n}_active", f"f{n}_done"
    start, complete = f"f{n}_start", f"f{n}_complete"
    return {
        "add_places": [
            {"name": pending, "tokens": 1},
            {"name": active, "tokens": 0},
            {"name": done, "tokens": 0},
        ],
        "add_transitions": [{"name": start}, {"name": complete}],
        "add_arcs": [
            {"source": pending, "target": start, "weight": 1},
            {"source": "feature_ready", "target": start, "weight": 1},
            {"source": start, "target": active, "weight": 1},
            {"source": start, "target": "feature_ready", "weight": 1},
            {"source": active, "target": complete, "weight": 1},
            {"source": complete, "target": done, "weight": 1},
            {"source": complete, "target": "goal_satisfied", "weight": 1},
        ],
    }


class TestBootstrapResourceCatalog:
    """R1: the 5-place capacity catalog joins the bootstrap skeleton (§2.2)."""

    def test_bootstrap_materializes_resource_catalog(self, env, capsys) -> None:
        cli = _cli()
        code, out = _sync(cli, capsys)
        assert code == 0, out
        assert out["bootstrap"] is True
        st = _state().load(env / "net")
        assert st.net.places == BOUNDARY | set(RESOURCE_PLACES)
        assert st.net.transitions == set()  # still NO supervisor transitions
        m0 = dict(zip(st.net.place_order, st.net.initial_marking_tuple()))
        for name in RESOURCE_PLACES:
            assert m0[name] == 1, f"{name} M0 must be 1 (IDEA-002 v4 §2.2)"
            assert st.live_marking[name] == 1
        assert st.live_marking == {
            "feature_ready": 1,
            "resource_token": 1,
            "goal_satisfied": 0,
            **{name: 1 for name in RESOURCE_PLACES},
        }
        assert st.overlay["supervisor"]["places"] == sorted(
            BOUNDARY | set(RESOURCE_PLACES)
        )


class TestSubnetAgentAttentionWiring:
    """R2: start claims / complete releases agent_attention (§2.3 serial mirror)."""

    def test_subnet_template_wires_agent_attention(self, env, capsys) -> None:
        cli = _cli()
        _, out = _sync(cli, capsys)
        mutation = out["proposal"]["add_subnets"][0]["mutation"]
        arcs = {(a["source"], a["target"]) for a in mutation["add_arcs"]}
        assert ("agent_attention", "f001_start") in arcs  # claim
        assert ("f001_complete", "agent_attention") in arcs  # release
        assert len(mutation["add_arcs"]) == 9  # 7 lifecycle + claim + release

    def test_two_feature_conflict_blocks_second_start(self, env, capsys) -> None:
        """§2.3: agent_attention=1 mirrors the single-threaded agent — the
        second feature's start is structurally blocked while the first holds
        attention; completion releases it."""
        cli = _cli()
        _, out = _sync(cli, capsys)
        for entry in out["proposal"]["add_subnets"]:
            _apply(cli, capsys, entry["mutation"])
        code, _ = _fire(cli, capsys, "f001_start")
        assert code == 0
        st = _state().load(env / "net")
        assert st.live_marking["agent_attention"] == 0
        assert st.live_marking["f001_active"] == 1
        live = tuple(st.live_marking[p] for p in st.net.place_order)
        assert not st.net.is_enabled_at(live, "f002_start")
        # completion releases attention → the second feature may start
        code, _ = _fire(cli, capsys, "f001_complete")
        assert code == 0
        st = _state().load(env / "net")
        assert st.live_marking["agent_attention"] == 1
        live = tuple(st.live_marking[p] for p in st.net.place_order)
        assert st.net.is_enabled_at(live, "f002_start")

    def test_conservation_law_agent_attention_plus_actives(self, env, capsys) -> None:
        """place_invariants conservation law: agent_attention + Σ f{N}_active = 1
        at every reachable marking of the claim/release cycle."""
        cli = _cli()
        _, out = _sync(cli, capsys)
        for entry in out["proposal"]["add_subnets"]:
            _apply(cli, capsys, entry["mutation"])

        def law(st) -> int:
            return st.live_marking["agent_attention"] + sum(
                st.live_marking[f"f{n}_active"] for n in ("001", "002")
            )

        st = _state().load(env / "net")
        assert law(st) == 1
        # the law is structural: some place invariant covers agent_attention
        from net.analysis import PetriNetAnalyzer  # noqa: PLC0415

        analyzer = PetriNetAnalyzer(st.net)
        idx = st.net.place_order.index("agent_attention")
        assert any(y[idx] != 0 for y in analyzer.place_invariants())
        for t in ("f001_start", "f001_complete", "f002_start", "f002_complete"):
            code, _ = _fire(cli, capsys, t)
            assert code == 0
            st = _state().load(env / "net")
            assert law(st) == 1, f"conservation broken after firing {t}"

    def test_invariant_envelope_reports_conflict_and_holder(self, env, capsys) -> None:
        """R4: additive envelope keys — resources[] (capacity/live/capacity_ok/
        holders) + conflicts[] (pending subnet blocked on empty agent_attention)."""
        cli = _cli()
        _, out = _sync(cli, capsys)
        for entry in out["proposal"]["add_subnets"]:
            _apply(cli, capsys, entry["mutation"])
        _fire(cli, capsys, "f001_start")
        code, out = _run(cli, ["invariant"], capsys)
        assert code == 0, out
        resources = {r["place"]: r for r in out["resources"]}
        agent = resources["agent_attention"]
        assert agent["capacity"] == 1
        assert agent["live"] == 0
        assert agent["capacity_ok"] is True  # 0 live + 1 held == capacity
        assert agent["holders"] == ["feature_001"]
        for name in RESOURCE_PLACES[1:]:  # unwired in v1: nothing can consume them
            assert resources[name] == {
                "place": name,
                "capacity": 1,
                "live": 1,
                "capacity_ok": True,
                "holders": [],
            }
        assert out["conflicts"] == [
            {
                "subnet": "feature_002",
                "transition": "f002_start",
                "blocked_by": ["agent_attention"],
            }
        ]
        # release → the conflict clears
        _fire(cli, capsys, "f001_complete")
        code, out = _run(cli, ["invariant"], capsys)
        assert code == 0
        assert out["conflicts"] == []
        resources = {r["place"]: r for r in out["resources"]}
        assert resources["agent_attention"]["live"] == 1
        assert resources["agent_attention"]["holders"] == []

    def test_invariant_envelope_legacy_bundle_empty_report(self, env, capsys) -> None:
        """Pre-041 bundles (no catalog places) report empty resources/conflicts —
        additive keys never break the legacy envelope."""
        _legacy_bundle(env / "net")
        cli = _cli()
        code, out = _run(cli, ["invariant"], capsys)
        assert code == 0, out
        assert out["resources"] == []
        assert out["conflicts"] == []
        assert "place_invariants" in out and "drift" in out  # pre-existing keys

    def test_seeded_active_without_claim_surfaces_violation(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        """A checkbox-seeded active subnet never claimed agent_attention — the
        report surfaces the conservation violation (capacity_ok=False). State
        drift is visible, never silent (D16)."""
        work = WORK_MD.replace("- [ ] **feature_001.alpha**", "- [~] **feature_001.alpha**")
        _make_env(tmp_path, monkeypatch, work_md=work)
        cli = _cli()
        _, out = _sync(cli, capsys)
        _apply(cli, capsys, out["proposal"]["add_subnets"][0]["mutation"])
        code, out = _run(cli, ["invariant"], capsys)
        assert code == 0, out
        resources = {r["place"]: r for r in out["resources"]}
        agent = resources["agent_attention"]
        assert agent["holders"] == ["feature_001"]
        assert agent["live"] == 1
        assert agent["capacity_ok"] is False  # 1 live + 1 held > capacity 1

    def test_multi_resource_fire_conserves_each_pair(self, env, capsys) -> None:
        """§2.3.2: a transition claiming agent_attention + src_edit_capacity in
        ONE fire conserves each complement pair independently."""
        cli = _cli()
        _sync(cli, capsys)
        mutation = {
            "add_places": [
                {"name": "f009_ready", "tokens": 1},
                {"name": "f009_doing", "tokens": 0},
                {"name": "f009_editing", "tokens": 0},
            ],
            "add_transitions": [{"name": "f009_begin"}],
            "add_arcs": [
                {"source": "f009_ready", "target": "f009_begin", "weight": 1},
                {"source": "agent_attention", "target": "f009_begin", "weight": 1},
                {"source": "src_edit_capacity", "target": "f009_begin", "weight": 1},
                {"source": "f009_begin", "target": "f009_doing", "weight": 1},
                {"source": "f009_begin", "target": "f009_editing", "weight": 1},
            ],
        }
        code, out = _apply(cli, capsys, mutation, "multi-resource transition")
        assert code == 0, out
        st = _state().load(env / "net")
        assert st.live_marking["agent_attention"] + st.live_marking["f009_doing"] == 1
        assert st.live_marking["src_edit_capacity"] + st.live_marking["f009_editing"] == 1
        code, _ = _fire(cli, capsys, "f009_begin")
        assert code == 0
        st = _state().load(env / "net")
        assert st.live_marking["agent_attention"] == 0
        assert st.live_marking["src_edit_capacity"] == 0
        assert st.live_marking["f009_doing"] == 1
        assert st.live_marking["f009_editing"] == 1
        # each pair conserved independently after the multi-resource fire
        assert st.live_marking["agent_attention"] + st.live_marking["f009_doing"] == 1
        assert st.live_marking["src_edit_capacity"] + st.live_marking["f009_editing"] == 1


class TestResyncResourceProposal:
    """R5: resync of pre-041 bundles emits ONE add_resource_places entry (D4)."""

    def test_resync_proposes_add_resource_places(self, env, capsys) -> None:
        _legacy_bundle(env / "net")
        cli = _cli()
        code, out = _sync(cli, capsys)
        assert code == 0, out
        assert out["bootstrap"] is False
        entries = out["proposal"]["add_resource_places"]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["places"] == list(RESOURCE_PLACES)  # catalog order
        assert entry["mutation"]["add_places"] == [
            {"name": name, "tokens": 1} for name in RESOURCE_PLACES
        ]
        assert entry["mutation"]["add_transitions"] == []
        assert entry["mutation"]["add_arcs"] == []  # no subnets → no retrofit
        # proposal-only (D4): state untouched
        st = _state().load(env / "net")
        assert st.revision == 0
        assert st.net.places == BOUNDARY
        # audit never silent
        rec = _ledger_records(env / "net")[-1]
        assert rec["kind"] == "net_sync"
        assert rec["add_resource_places"] == list(RESOURCE_PLACES)
        assert rec["retrofit_arcs"] == 0

    def test_resync_retrofit_arcs_for_unwired_subnets(self, env, capsys) -> None:
        _legacy_bundle(env / "net")
        cli = _cli()
        code, out = _apply(  # hand-apply a pre-041 (unwired) subnet
            cli, capsys, _legacy_subnet_mutation("009"), "legacy subnet"
        )
        assert code == 0, out
        code, out = _sync(cli, capsys)
        assert code == 0
        entries = out["proposal"]["add_resource_places"]
        assert len(entries) == 1
        arcs = [(a["source"], a["target"]) for a in entries[0]["mutation"]["add_arcs"]]
        assert arcs == [
            ("agent_attention", "f009_start"),      # claim retrofit
            ("f009_complete", "agent_attention"),   # release retrofit
        ]

    def test_resync_no_entry_when_catalog_present(self, env, capsys) -> None:
        cli = _cli()
        _sync(cli, capsys)  # bootstrap WITH the catalog
        code, out = _run(cli, ["sync", "--session", "s1"], capsys)
        assert code == 0
        assert out["proposal"]["add_resource_places"] == []

    def test_apply_resource_places_then_ports_resources_refined(self, env, capsys) -> None:
        """R3: after applying add_resource_places + a wired subnet, the overlay
        refines ports.resources = (entry ∪ exit) ∩ RESOURCE_PLACES (P10 pure).
        Also pins the apply order: resources BEFORE pending add_subnets."""
        _legacy_bundle(env / "net")
        cli = _cli()
        _, out = _sync(cli, capsys)
        resource_mutation = out["proposal"]["add_resource_places"][0]["mutation"]
        code, out2 = _apply(cli, capsys, resource_mutation, "apply resource catalog")
        assert code == 0, out2
        # the wired subnet template now applies cleanly (agent_attention exists)
        subnet_mutation = out["proposal"]["add_subnets"][0]["mutation"]
        code, out3 = _apply(cli, capsys, subnet_mutation, "apply subnet")
        assert code == 0, out3
        st = _state().load(env / "net")
        subnet = st.overlay["subnets"]["feature_001"]
        assert subnet["ports"]["entry"] == ["agent_attention", "feature_ready"]
        assert subnet["ports"]["exit"] == [
            "agent_attention",
            "feature_ready",
            "goal_satisfied",
        ]
        assert subnet["ports"]["resources"] == ["agent_attention"]


class TestLifecycleSyncHook:
    """R6: lifecycle events auto-trigger net sync — fail-open, silent skip when
    unbootstrapped, proposal-only (D4), one-line stdout."""

    def test_hook_calls_sync_and_prints_one_line(self, env, capsys, monkeypatch) -> None:
        state = _state()
        state.init_empty(env / "net")  # bootstrapped (empty net suffices)
        calls = []

        def spy(base, *, reasoning="", session=""):
            calls.append((base, reasoning))
            return None, {
                "proposal": {
                    "add_subnets": [{}],
                    "disable_subnets": [],
                    "add_resource_places": [],
                }
            }

        monkeypatch.setattr(state, "sync", spy)
        state.lifecycle_sync_hook("create")
        assert len(calls) == 1
        assert calls[0][0] == env / "net"
        assert "create" in calls[0][1]
        line = capsys.readouterr().out.strip()
        assert line and "\n" not in line  # exactly one line
        assert "create" in line and "1" in line

    def test_hook_silent_when_proposal_empty(self, env, capsys, monkeypatch) -> None:
        state = _state()
        state.init_empty(env / "net")
        monkeypatch.setattr(
            state,
            "sync",
            lambda base, **kw: (
                None,
                {"proposal": {"add_subnets": [], "disable_subnets": [], "add_resource_places": []}},
            ),
        )
        state.lifecycle_sync_hook("link")
        assert capsys.readouterr().out == ""

    def test_hook_fail_open_on_net_error(self, env, monkeypatch) -> None:
        state = _state()
        state.init_empty(env / "net")

        def boom(base, **kw):
            raise RuntimeError("net exploded")

        monkeypatch.setattr(state, "sync", boom)
        state.lifecycle_sync_hook("close")  # must NOT raise (fail-open)

    def test_hook_skips_when_unbootstrapped(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setenv("OMT_NET_DIR", str(tmp_path / "net"))
        monkeypatch.setenv("OMT_LEDGER_PATH", str(tmp_path / "net" / "ledger.jsonl"))
        state = _state()
        called = []
        monkeypatch.setattr(state, "sync", lambda *a, **kw: called.append(1))
        state.lifecycle_sync_hook("create")
        assert called == []  # bootstrap stays an explicit agent action (§5.1)
        assert capsys.readouterr().out == ""

    def test_project_new_triggers_hook_net_sync_record(self, env, monkeypatch, capsys) -> None:
        """project.py cmd_new wires the hook after the lifecycle ledger append —
        the net_sync audit record lands in the same (hermetic) ledger."""
        import project as project_cli  # noqa: PLC0415

        proots = env / ".projects" / "meta"
        proots.mkdir(parents=True)
        monkeypatch.setenv("OMT_PROJECTS_ROOT", str(proots))
        monkeypatch.setenv("OMT_PROJECTS_ARCHIVE", str(env / ".projects" / "archive"))
        monkeypatch.setenv("OMT_WORK_PATH", str(env / "PROJ_WORK.md"))
        cli = _cli()
        _sync(cli, capsys)  # bootstrap WITH catalog (reality: features 001/002)
        rc = project_cli.main(["new", "hook proj"])
        assert rc == 0
        recs = [r for r in _ledger_records(env / "net") if r["kind"] == "net_sync"]
        assert any("create" in r.get("reasoning", "") for r in recs)
        out = capsys.readouterr().out
        assert "auto-sync" in out  # one-line hook stdout (001/002 unapplied)

    def test_new_feature_link_triggers_hook(self, env, monkeypatch, capsys) -> None:
        """new_feature.py --project link fires the same hook with the
        new_feature_link event, AFTER the link ledger append."""
        import new_feature  # noqa: PLC0415

        proots = env / ".projects" / "meta"
        (proots / "proj_x").mkdir(parents=True)
        monkeypatch.setenv("OMT_PROJECTS_ROOT", str(proots))
        monkeypatch.setenv("OMT_PROJECTS_ARCHIVE", str(env / ".projects" / "archive"))
        monkeypatch.setenv("OMT_WORK_PATH", str(env / "PROJ_WORK.md"))
        monkeypatch.setattr(new_feature, "FEATURES_DIR", env / "features")
        cli = _cli()
        _sync(cli, capsys)
        rc = new_feature.main(["zeta work", "--project", "proj_x"])
        assert rc == 0
        recs = [r for r in _ledger_records(env / "net") if r["kind"] == "net_sync"]
        assert any("new_feature_link" in r.get("reasoning", "") for r in recs)
