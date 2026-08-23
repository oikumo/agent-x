"""Analysis-layer tests for the Petri-net library (design_001 §8; DoD 7–17, 19).

Imports are deferred inside helpers/test bodies for RED-collection safety
(design_001 §8): at cycle-2 RED ``analysis.py`` does not exist yet, and a
module-level import would abort collection (pytest exit 2) instead of failing
the tests (exit 1). Every exploration API gets a happy test AND a truncated /
"unknown" test (per-function matrix, §40-19 — no overclaiming).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Deferred imports + §30 fixtures
# ---------------------------------------------------------------------------

def _analysis():
    from agentx.model.petri_net import analysis
    return analysis


def _analyzer(net):
    from agentx.model.petri_net.analysis import PetriNetAnalyzer
    return PetriNetAnalyzer(net)


def make_net(defn, initial_marking=None):
    """Mirror of doc §30 make_net: defn = places/transitions/arcs (src,dst,w)."""
    from agentx.model.petri_net.model import PetriNet
    net = PetriNet()
    m0 = initial_marking or {}
    for p in defn["places"]:
        net.add_place(p, tokens=m0.get(p, 0))
    for t in defn["transitions"]:
        net.add_transition(t)
    for src, dst, w in defn["arcs"]:
        if src in defn["places"]:
            net.add_input(src, dst, weight=w)
        else:
            net.add_output(src, dst, weight=w)
    return net


TWO_WAY_CYCLE = {
    "places": ["p1", "p2"],
    "transitions": ["t1", "t2"],
    "arcs": [("p1", "t1", 1), ("t1", "p2", 1), ("p2", "t2", 1), ("t2", "p1", 1)],
}
CONSERVATION_M0 = {"p1": 1, "p2": 1}
LIVE_BOUNDED_M0 = {"p1": 1, "p2": 0}

UNBOUNDED_NET = {
    "places": ["p"],
    "transitions": ["t"],
    "arcs": [("p", "t", 1), ("t", "p", 2)],
}
DEADLOCK_NET = {
    "places": ["p"],
    "transitions": ["t"],
    "arcs": [("p", "t", 1)],
}  # M0 p=0 -> t never enabled
TOKEN_DRAIN_NET = {  # token flows to a deadlock (2 SCCs; t fires once then dead)
    "places": ["p1", "p2"],
    "transitions": ["t"],
    "arcs": [("p1", "t", 1), ("t", "p2", 1)],
}
TWO_DEADLOCKS_NET = {  # (1,0) branches to two distinct deadlock markings
    "places": ["p1", "p2"],
    "transitions": ["t1", "t2"],
    "arcs": [("p1", "t1", 1), ("t1", "p2", 1), ("p1", "t2", 1)],
}

TRUNCATED_DEADLOCK_REASON = (
    "State-space exploration was truncated; "
    "listed deadlocks are only those among explored states."
)
TRUNCATED_BOUNDS_REASON = (
    "State-space exploration was truncated; boundedness is unknown."
)


# ---------------------------------------------------------------------------
# Behaviors 13–14 — reachable_markings (happy + truncated)
# ---------------------------------------------------------------------------

class TestReachableMarkings:
    def test_reachable_two_way_cycle_complete(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        result = _analyzer(net).reachable_markings(max_states=None)
        assert result.markings == frozenset({(1, 0), (0, 1)})
        assert result.complete is True
        assert result.explored_states == 2
        assert result.predecessors[(1, 0)] == (None, None)
        assert result.predecessors[(0, 1)] == ((1, 0), "t1")

    def test_reachable_truncated_max_states_1(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        result = _analyzer(net).reachable_markings(max_states=1)
        assert result.markings == frozenset({(1, 0)})
        assert result.complete is False
        assert result.explored_states == 1


# ---------------------------------------------------------------------------
# Behavior 15 — reachability_graph (happy + truncated)
# ---------------------------------------------------------------------------

class TestReachabilityGraph:
    def test_graph_two_way_cycle_complete(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        graph = _analyzer(net).reachability_graph(max_states=None)
        assert graph.states == frozenset({(1, 0), (0, 1)})
        assert graph.edges == {
            (1, 0): (("t1", (0, 1)),),
            (0, 1): (("t2", (1, 0)),),
        }
        assert graph.complete is True

    def test_graph_truncated_records_edges_to_unvisited(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        graph = _analyzer(net).reachability_graph(max_states=1)
        assert graph.states == frozenset({(1, 0)})
        # edge to the unvisited (0,1) is still recorded; consumers check complete
        assert graph.edges == {(1, 0): (("t1", (0, 1)),)}
        assert graph.complete is False


# ---------------------------------------------------------------------------
# Behavior 16 — firing_sequence_to
# ---------------------------------------------------------------------------

class TestFiringSequenceTo:
    def test_shortest_sequence(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        result = analyzer.reachable_markings(max_states=None)
        assert analyzer.firing_sequence_to(result, (0, 1)) == ["t1"]

    def test_sequence_to_initial_marking_is_empty(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        result = analyzer.reachable_markings(max_states=None)
        assert analyzer.firing_sequence_to(result, (1, 0)) == []

    def test_absent_target_on_complete_result_is_none(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        result = analyzer.reachable_markings(max_states=None)
        assert result.complete is True
        # None here IS a proof of unreachability (complete exploration).
        assert analyzer.firing_sequence_to(result, (9, 9)) is None

    def test_absent_target_on_truncated_result_is_none_not_proof(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        result = analyzer.reachable_markings(max_states=1)
        assert result.complete is False
        # (0,1) IS reachable, but the truncated search cannot prove anything.
        assert analyzer.firing_sequence_to(result, (0, 1)) is None


# ---------------------------------------------------------------------------
# Behavior 17 — deadlocks (happy + truncated; never "deadlock-free")
# ---------------------------------------------------------------------------

class TestDeadlocks:
    def test_deadlock_net_found_complete(self):
        net = make_net(DEADLOCK_NET)  # M0 p=0
        result = _analyzer(net).deadlocks(max_states=None)
        assert result.deadlocks == ((0,),)
        assert result.complete is True
        assert result.reason is None

    def test_truncated_search_never_claims_deadlock_free(self):
        net = make_net(UNBOUNDED_NET, {"p": 1})
        result = _analyzer(net).deadlocks(max_states=3)
        assert result.deadlocks == ()  # none among explored — NOT a proof
        assert result.complete is False
        assert result.reason == TRUNCATED_DEADLOCK_REASON


# ---------------------------------------------------------------------------
# Behavior 18 — bounds (happy + truncated; never bounded=True from truncation)
# ---------------------------------------------------------------------------

class TestBounds:
    def test_bounds_complete_finite(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        result = _analyzer(net).bounds(max_states=None)
        assert result.bounded is True
        assert result.bounds == {"p1": 1, "p2": 1}
        assert result.complete is True
        assert result.reason is None

    def test_bounds_truncated_unbounded_net(self):
        net = make_net(UNBOUNDED_NET, {"p": 1})
        result = _analyzer(net).bounds(max_states=5)
        assert result.bounded is None  # unknown — never overclaimed (§16/§39)
        assert result.complete is False
        assert result.reason == TRUNCATED_BOUNDS_REASON
        assert result.bounds == {"p": 5}  # observed maxima only


# ---------------------------------------------------------------------------
# Behavior 19 — incidence_matrix (exact; degenerate shapes)
# ---------------------------------------------------------------------------

class TestIncidenceMatrix:
    def test_two_way_cycle_matrix(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        assert _analyzer(net).incidence_matrix() == [[-1, 1], [1, -1]]

    def test_unbounded_net_matrix(self):
        net = make_net(UNBOUNDED_NET, {"p": 1})
        assert _analyzer(net).incidence_matrix() == [[1]]

    def test_places_only_matrix_p_by_0(self):
        net = make_net({"places": ["a", "b"], "transitions": [], "arcs": []})
        assert _analyzer(net).incidence_matrix() == [[], []]

    def test_transitions_only_matrix_0_rows(self):
        net = make_net({"places": [], "transitions": ["ta", "tb"], "arcs": []})
        assert _analyzer(net).incidence_matrix() == []

    def test_empty_net_matrix(self):
        net = make_net({"places": [], "transitions": [], "arcs": []})
        assert _analyzer(net).incidence_matrix() == []


# ---------------------------------------------------------------------------
# Behavior 20 — place_invariants (exact; degenerate bases)
# ---------------------------------------------------------------------------

class TestPlaceInvariants:
    def test_two_way_cycle_conservation_invariant(self):
        net = make_net(TWO_WAY_CYCLE, CONSERVATION_M0)
        analyzer = _analyzer(net)
        invariants = analyzer.place_invariants()
        assert invariants == [(1, 1)]
        # conservation: y · m constant across the reachable markings
        result = analyzer.reachable_markings(max_states=None)
        for m in result.markings:
            assert sum(y * x for y, x in zip(invariants[0], m)) == 2

    def test_places_only_identity_basis(self):
        net = make_net({"places": ["a", "b"], "transitions": [], "arcs": []})
        assert _analyzer(net).place_invariants() == [(1, 0), (0, 1)]

    def test_transitions_only_no_place_invariants(self):
        net = make_net({"places": [], "transitions": ["ta"], "arcs": []})
        assert _analyzer(net).place_invariants() == []

    def test_empty_net_no_place_invariants(self):
        net = make_net({"places": [], "transitions": [], "arcs": []})
        assert _analyzer(net).place_invariants() == []


# ---------------------------------------------------------------------------
# Behavior 21 — transition_invariants (exact; degenerate bases)
# ---------------------------------------------------------------------------

class TestTransitionInvariants:
    def test_two_way_cycle_t_invariant(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        assert _analyzer(net).transition_invariants() == [(1, 1)]

    def test_transitions_only_identity_basis(self):
        net = make_net({"places": [], "transitions": ["ta", "tb"], "arcs": []})
        assert _analyzer(net).transition_invariants() == [(1, 0), (0, 1)]

    def test_places_only_no_transition_invariants(self):
        net = make_net({"places": ["a"], "transitions": [], "arcs": []})
        assert _analyzer(net).transition_invariants() == []

    def test_empty_net_no_transition_invariants(self):
        net = make_net({"places": [], "transitions": [], "arcs": []})
        assert _analyzer(net).transition_invariants() == []


# ---------------------------------------------------------------------------
# Behavior 22 — transition_liveness (complete verdict + incomplete unknown)
# ---------------------------------------------------------------------------

class TestTransitionLiveness:
    def test_live_net_transitions_live(self):
        analysis = _analysis()
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        assert analyzer.transition_liveness("t1", graph) == analysis.AnalysisResult(
            True, True, 2)
        assert analyzer.transition_liveness("t2", graph) == analysis.AnalysisResult(
            True, True, 2)

    def test_deadlock_net_transition_not_live(self):
        analysis = _analysis()
        net = make_net(DEADLOCK_NET)
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        assert analyzer.transition_liveness("t", graph) == analysis.AnalysisResult(
            False, True, 1)

    def test_incomplete_graph_unknown(self):
        analysis = _analysis()
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=1)
        result = analyzer.transition_liveness("t1", graph)
        assert result == analysis.AnalysisResult(
            None, False, 1,
            "Reachability graph is incomplete; liveness is unknown.")


# ---------------------------------------------------------------------------
# Behavior 23 — is_live (incl. empty net F1)
# ---------------------------------------------------------------------------

class TestIsLive:
    def test_live_net_is_live(self):
        analysis = _analysis()
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        assert analyzer.is_live(graph) == analysis.AnalysisResult(True, True, 2)

    def test_fire_once_then_dead_not_live(self):
        analysis = _analysis()
        net = make_net(TOKEN_DRAIN_NET, {"p1": 1})
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        assert analyzer.is_live(graph) == analysis.AnalysisResult(False, True, 2)

    def test_incomplete_graph_unknown(self):
        analysis = _analysis()
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=1)
        result = analyzer.is_live(graph)
        assert result == analysis.AnalysisResult(
            None, False, 1,
            "Reachability graph is incomplete; global liveness is unknown.")

    def test_empty_net_is_live_f1(self):
        analysis = _analysis()
        net = make_net({"places": [], "transitions": [], "arcs": []})
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        # F1: §31 uniform rule — explored_states == len(graph.states) == 1.
        assert analyzer.is_live(graph) == analysis.AnalysisResult(True, True, 1)


# ---------------------------------------------------------------------------
# Behavior 24 — strongly_connected_components
# ---------------------------------------------------------------------------

class TestStronglyConnectedComponents:
    def test_cycle_single_component(self):
        net = make_net(TWO_WAY_CYCLE, LIVE_BOUNDED_M0)
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        sccs = analyzer.strongly_connected_components(graph)
        assert sccs == [frozenset({(1, 0), (0, 1)})]

    def test_deadlock_net_single_state_component(self):
        net = make_net(DEADLOCK_NET)
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        assert analyzer.strongly_connected_components(graph) == [frozenset({(0,)})]

    def test_token_drain_two_components(self):
        net = make_net(TOKEN_DRAIN_NET, {"p1": 1})
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        sccs = analyzer.strongly_connected_components(graph)
        assert len(sccs) == 2
        assert frozenset({(0, 1)}) in sccs
        assert frozenset({(1, 0)}) in sccs

    def test_empty_net_single_component(self):
        net = make_net({"places": [], "transitions": [], "arcs": []})
        analyzer = _analyzer(net)
        graph = analyzer.reachability_graph(max_states=None)
        assert analyzer.strongly_connected_components(graph) == [frozenset({()})]


# ---------------------------------------------------------------------------
# Behavior 25 — determinism (§29) + sorted deadlocks
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_repeated_calls_equal(self):
        net = make_net(TWO_WAY_CYCLE, CONSERVATION_M0)
        analyzer = _analyzer(net)
        first = analyzer.reachable_markings(max_states=None)
        second = analyzer.reachable_markings(max_states=None)
        assert first == second  # frozen dataclass equality
        assert analyzer.reachability_graph(max_states=None) == (
            analyzer.reachability_graph(max_states=None))

    def test_deadlocks_sorted(self):
        net = make_net(TWO_DEADLOCKS_NET, {"p1": 1})
        result = _analyzer(net).deadlocks(max_states=None)
        assert result.complete is True
        assert result.deadlocks == ((0, 0), (0, 1))  # sorted tuple (§29)
