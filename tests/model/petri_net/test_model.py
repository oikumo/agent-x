"""Model-layer tests for the Petri-net library (design_001 §8; DoD items 1–6).

Imports are deferred inside helpers/test bodies for RED-collection safety
(design_001 §8: "imports deferred inside test bodies where RED-collection-
safety matters"): at cycle-1 RED ``src/agentx/model/petri_net/`` does not
exist yet, and a module-level import would abort collection (pytest exit 2)
instead of failing the tests (exit 1).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Deferred imports + builders
# ---------------------------------------------------------------------------

def _errors():
    from agentx.model.petri_net import errors
    return errors


def _new_net():
    from agentx.model.petri_net.model import PetriNet
    return PetriNet()


def make_two_way_cycle(m0: tuple[int, int] = (1, 0)):
    """§30 TWO_WAY_CYCLE: p1 -t1-> p2 -t2-> p1, unit weights."""
    net = _new_net()
    net.add_place("p1", tokens=m0[0])
    net.add_place("p2", tokens=m0[1])
    net.add_transition("t1")
    net.add_transition("t2")
    net.add_input("p1", "t1")
    net.add_output("t1", "p2")
    net.add_input("p2", "t2")
    net.add_output("t2", "p1")
    return net


@pytest.fixture
def net():
    return _new_net()


# ---------------------------------------------------------------------------
# Behavior 1 — build: places/transitions/weighted arcs in orders + markings
# ---------------------------------------------------------------------------

class TestBuild:
    def test_build_orders_and_markings(self):
        net = make_two_way_cycle((1, 0))
        assert net.place_order == ("p1", "p2")
        assert net.transition_order == ("t1", "t2")
        assert net.current_marking() == (1, 0)
        assert net.initial_marking_tuple() == (1, 0)
        assert net.inputs == {"t1": {"p1": 1}, "t2": {"p2": 1}}
        assert net.outputs == {"t1": {"p2": 1}, "t2": {"p1": 1}}

    def test_build_weighted_arcs(self):
        net = _new_net()
        net.add_place("p", tokens=3)
        net.add_transition("t")
        net.add_input("p", "t", weight=2)
        net.add_output("t", "p", weight=3)
        assert net.inputs["t"] == {"p": 2}
        assert net.outputs["t"] == {"p": 3}

    def test_build_default_tokens_zero(self):
        net = _new_net()
        net.add_place("p")
        assert net.current_marking() == (0,)
        assert net.initial_marking_tuple() == (0,)


# ---------------------------------------------------------------------------
# Behavior 2 — duplicate names (F4 asymmetry)
# ---------------------------------------------------------------------------

class TestDuplicateNames:
    def test_duplicate_place_raises_duplicate_place_error(self, net):
        errors = _errors()
        net.add_place("p")
        with pytest.raises(errors.DuplicatePlaceError):
            net.add_place("p")

    def test_duplicate_place_error_is_invalid_model_error(self, net):
        errors = _errors()
        net.add_place("p")
        with pytest.raises(errors.InvalidModelError):
            net.add_place("p")

    def test_duplicate_transition_raises_plain_value_error(self, net):
        # F4: duplicate transition is a plain ValueError, NOT a PetriNetError.
        errors = _errors()
        net.add_transition("t")
        with pytest.raises(ValueError) as exc_info:
            net.add_transition("t")
        assert not isinstance(exc_info.value, errors.PetriNetError)


# ---------------------------------------------------------------------------
# Behavior 3 — empty names / bad token counts
# ---------------------------------------------------------------------------

class TestAddValidation:
    def test_empty_place_name_raises(self, net):
        with pytest.raises(ValueError, match="Place name cannot be empty"):
            net.add_place("")

    def test_empty_transition_name_raises(self, net):
        with pytest.raises(ValueError, match="Transition name cannot be empty"):
            net.add_transition("")

    @pytest.mark.parametrize("tokens", [True, False, -1, 1.5, "2"])
    def test_bad_token_count_raises(self, net, tokens):
        with pytest.raises(ValueError, match="non-negative integer"):
            net.add_place("p", tokens=tokens)


# ---------------------------------------------------------------------------
# Behavior 4 — arc validation + duplicate arcs + arg-order pin
# ---------------------------------------------------------------------------

class TestArcs:
    def test_add_input_unknown_place_raises(self, net):
        errors = _errors()
        net.add_transition("t")
        with pytest.raises(errors.UnknownPlaceError):
            net.add_input("ghost", "t")

    def test_add_input_place_checked_before_transition(self, net):
        # Both unknown -> the place error wins (design §5.2 _validate_arc order).
        errors = _errors()
        with pytest.raises(errors.UnknownPlaceError):
            net.add_input("ghost", "ghost_t")

    def test_add_input_unknown_transition_raises(self, net):
        errors = _errors()
        net.add_place("p")
        with pytest.raises(errors.UnknownTransitionError):
            net.add_input("p", "ghost")

    def test_add_output_unknown_place_raises(self, net):
        errors = _errors()
        net.add_transition("t")
        with pytest.raises(errors.UnknownPlaceError):
            net.add_output("t", "ghost")

    def test_add_output_unknown_transition_raises(self, net):
        errors = _errors()
        net.add_place("p")
        with pytest.raises(errors.UnknownTransitionError):
            net.add_output("ghost", "p")

    @pytest.mark.parametrize("weight", [0, -1, True, 2.5])
    def test_add_input_bad_weight_raises(self, net, weight):
        net.add_place("p")
        net.add_transition("t")
        with pytest.raises(ValueError, match="positive integer"):
            net.add_input("p", "t", weight=weight)

    @pytest.mark.parametrize("weight", [0, -1, True, 2.5])
    def test_add_output_bad_weight_raises(self, net, weight):
        net.add_place("p")
        net.add_transition("t")
        with pytest.raises(ValueError, match="positive integer"):
            net.add_output("t", "p", weight=weight)

    def test_duplicate_input_arc_rejected_regardless_of_weight(self, net):
        errors = _errors()
        net.add_place("p")
        net.add_transition("t")
        net.add_input("p", "t", weight=1)
        with pytest.raises(errors.DuplicateArcError):
            net.add_input("p", "t", weight=3)

    def test_duplicate_output_arc_rejected(self, net):
        errors = _errors()
        net.add_place("p")
        net.add_transition("t")
        net.add_output("t", "p")
        with pytest.raises(errors.DuplicateArcError):
            net.add_output("t", "p")

    def test_add_output_keyword_call_pins_arg_order(self, net):
        # §9 gotcha: add_output is (transition, place) — swapped vs add_input.
        net.add_place("p")
        net.add_transition("t")
        net.add_output(transition="t", place="p", weight=2)
        assert net.outputs["t"] == {"p": 2}


# ---------------------------------------------------------------------------
# Behavior 5 — enabledness
# ---------------------------------------------------------------------------

class TestEnabledness:
    def test_and_across_inputs_all_sufficient(self):
        net = _new_net()
        net.add_place("p1", tokens=2)
        net.add_place("p2", tokens=1)
        net.add_transition("t")
        net.add_input("p1", "t", weight=2)
        net.add_input("p2", "t", weight=1)
        assert net.is_enabled_at(net.current_marking(), "t") is True

    def test_and_across_inputs_one_insufficient(self):
        net = _new_net()
        net.add_place("p1", tokens=1)  # needs 2
        net.add_place("p2", tokens=5)
        net.add_transition("t")
        net.add_input("p1", "t", weight=2)
        net.add_input("p2", "t", weight=1)
        assert net.is_enabled_at(net.current_marking(), "t") is False

    def test_no_input_transition_always_enabled(self, net):
        net.add_place("p")  # zero tokens, no arc
        net.add_transition("source")
        assert net.is_enabled_at(net.current_marking(), "source") is True

    def test_zero_token_place_blocks_weight1(self, net):
        net.add_place("p")  # 0 tokens
        net.add_transition("t")
        net.add_input("p", "t")
        assert net.is_enabled_at(net.current_marking(), "t") is False

    def test_is_enabled_unknown_transition_raises(self, net):
        errors = _errors()
        with pytest.raises(errors.UnknownTransitionError):
            net.is_enabled_at((), "ghost")

    def test_enabled_transitions_at_sorted(self):
        net = _new_net()
        net.add_place("p", tokens=1)
        net.add_transition("tb")  # added first on purpose
        net.add_transition("ta")
        net.add_input("p", "tb")
        net.add_input("p", "ta")
        assert net.enabled_transitions_at(net.current_marking()) == ["ta", "tb"]

    def test_enabled_transitions_at_transitions_only_net(self, net):
        net.add_transition("source")  # no places -> marking () is well-formed
        assert net.enabled_transitions_at(()) == ["source"]


# ---------------------------------------------------------------------------
# Behavior 6 — fire_marking: purity, errors, precedence
# ---------------------------------------------------------------------------

class TestFireMarking:
    def test_successor_and_purity(self):
        net = make_two_way_cycle((1, 0))
        m0 = net.current_marking()
        succ = net.fire_marking(m0, "t1")
        assert succ == (0, 1)
        assert net.current_marking() == (1, 0)  # net untouched (pure)
        assert m0 == (1, 0)  # input marking untouched

    def test_weighted_successor(self):
        net = _new_net()
        net.add_place("p1", tokens=3)
        net.add_place("p2", tokens=0)
        net.add_transition("t")
        net.add_input("p1", "t", weight=2)
        net.add_output("t", "p2", weight=1)
        assert net.fire_marking(net.current_marking(), "t") == (1, 1)

    def test_disabled_raises_transition_not_enabled(self):
        errors = _errors()
        net = make_two_way_cycle((1, 0))
        with pytest.raises(errors.TransitionNotEnabledError):
            net.fire_marking(net.current_marking(), "t2")

    def test_unknown_transition_checked_before_marking(self):
        errors = _errors()
        net = make_two_way_cycle()
        with pytest.raises(errors.UnknownTransitionError):
            net.fire_marking((1,), "ghost")  # malformed too — transition wins

    def test_malformed_marking_length_raises(self):
        net = make_two_way_cycle()
        with pytest.raises(ValueError, match="length"):
            net.fire_marking((1, 0, 0), "t1")

    def test_malformed_marking_negative_raises(self):
        net = make_two_way_cycle()
        with pytest.raises(ValueError, match="negative"):
            net.fire_marking((1, -1), "t1")

    def test_marking_value_error_precedes_not_enabled(self):
        # must-pin 3: ValueError (malformed) BEFORE TransitionNotEnabledError.
        net = make_two_way_cycle((0, 1))  # t1 disabled at this marking
        with pytest.raises(ValueError):
            net.fire_marking((0,), "t1")  # malformed AND disabled -> ValueError


# ---------------------------------------------------------------------------
# Behavior 7 — fire (mutable) + reset
# ---------------------------------------------------------------------------

class TestFireAndReset:
    def test_fire_mutates_live_marking(self):
        net = make_two_way_cycle((1, 0))
        net.fire("t1")
        assert net.current_marking() == (0, 1)

    def test_fire_error_leaves_live_marking_unchanged(self):
        errors = _errors()
        net = make_two_way_cycle((1, 0))
        with pytest.raises(errors.TransitionNotEnabledError):
            net.fire("t2")
        assert net.current_marking() == (1, 0)

    def test_reset_restores_initial_marking(self):
        net = make_two_way_cycle((1, 0))
        net.fire("t1")
        net.reset()
        assert net.current_marking() == (1, 0)
        assert net.initial_marking_tuple() == (1, 0)

    def test_reset_returns_a_copy(self):
        net = make_two_way_cycle((1, 0))
        net.fire("t1")
        net.reset()
        net.fire("t1")  # mutating live marking must not corrupt M0
        assert net.initial_marking_tuple() == (1, 0)
        assert net.current_marking() == (0, 1)


# ---------------------------------------------------------------------------
# Behavior 8 — self-loop: net effect M-1+1
# ---------------------------------------------------------------------------

class TestSelfLoop:
    def _self_loop_net(self):
        net = _new_net()
        net.add_place("counter", tokens=1)
        net.add_transition("process")
        net.add_input("counter", "process")
        net.add_output("process", "counter")
        return net

    def test_self_loop_enabled_and_neutral(self):
        net = self._self_loop_net()
        m = net.current_marking()
        assert net.is_enabled_at(m, "process") is True
        assert net.fire_marking(m, "process") == (1,)
        net.fire("process")
        assert net.current_marking() == (1,)
        assert net.is_enabled_at(net.current_marking(), "process") is True


# ---------------------------------------------------------------------------
# Behavior 9 — parallel transitions
# ---------------------------------------------------------------------------

class TestParallelTransitions:
    def test_both_enabled_distinct_successors(self):
        net = _new_net()
        net.add_place("p", tokens=1)
        net.add_place("pa", tokens=0)
        net.add_place("pb", tokens=0)
        net.add_transition("ta")
        net.add_transition("tb")
        net.add_input("p", "ta")
        net.add_output("ta", "pa")
        net.add_input("p", "tb")
        net.add_output("tb", "pb")
        m = net.current_marking()
        assert net.enabled_transitions_at(m) == ["ta", "tb"]
        assert net.fire_marking(m, "ta") == (0, 1, 0)
        assert net.fire_marking(m, "tb") == (0, 0, 1)


# ---------------------------------------------------------------------------
# Behavior 10 — marking accessors, orders, place_index
# ---------------------------------------------------------------------------

class TestMarkingAccessors:
    def test_sorted_orders(self):
        net = _new_net()
        net.add_place("z", tokens=1)
        net.add_place("a", tokens=2)
        net.add_transition("tz")
        net.add_transition("ta")
        assert net.place_order == ("a", "z")
        assert net.transition_order == ("ta", "tz")
        assert net.current_marking() == (2, 1)  # (a, z) order

    def test_place_index(self):
        net = _new_net()
        net.add_place("z")
        net.add_place("a")
        assert net.place_index == {"a": 0, "z": 1}

    def test_marking_round_trip(self):
        net = make_two_way_cycle((1, 0))
        assert net.marking_to_dict(net.current_marking()) == {"p1": 1, "p2": 0}
        assert net.marking_to_dict((0, 1)) == {"p1": 0, "p2": 1}

    def test_marking_to_dict_length_mismatch(self):
        net = make_two_way_cycle()
        with pytest.raises(ValueError, match="length"):
            net.marking_to_dict((1,))

    def test_marking_to_dict_negative(self):
        net = make_two_way_cycle()
        with pytest.raises(ValueError, match="negative"):
            net.marking_to_dict((1, -1))


# ---------------------------------------------------------------------------
# Behavior 11 — pre_set / post_set (F5)
# ---------------------------------------------------------------------------

class TestStructuralQueries:
    def test_transition_pre_post(self):
        net = make_two_way_cycle()
        assert net.pre_set("t1") == frozenset({"p1"})
        assert net.post_set("t1") == frozenset({"p2"})

    def test_place_pre_post(self):
        net = make_two_way_cycle()
        assert net.pre_set("p2") == frozenset({"t1"})   # producers
        assert net.post_set("p2") == frozenset({"t2"})  # consumers

    def test_unknown_node_raises(self, net):
        errors = _errors()
        with pytest.raises(errors.PetriNetError, match="Unknown node"):
            net.pre_set("ghost")

    def test_ambiguous_node_raises(self):
        errors = _errors()
        net = _new_net()
        net.add_place("x")
        net.add_transition("x")
        with pytest.raises(errors.InvalidModelError, match="Ambiguous"):
            net.post_set("x")


# ---------------------------------------------------------------------------
# Behavior 12 — empty net
# ---------------------------------------------------------------------------

class TestEmptyNet:
    def test_empty_net_semantics(self, net):
        assert net.current_marking() == ()
        assert net.initial_marking_tuple() == ()
        assert net.place_order == ()
        assert net.transition_order == ()
        assert net.place_index == {}
        assert net.enabled_transitions_at(()) == []
        net.reset()  # no-op
        assert net.current_marking() == ()

    def test_empty_net_unknown_transition_raises(self, net):
        errors = _errors()
        with pytest.raises(errors.UnknownTransitionError):
            net.is_enabled_at((), "t")
