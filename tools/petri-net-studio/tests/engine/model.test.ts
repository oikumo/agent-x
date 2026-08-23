// @vitest-environment node
/**
 * Model-layer tests — 1:1 TS port of `tests/model/petri_net/test_model.py`
 * (60 behaviors; design_001 §9.1). Error-class assertions use instanceof;
 * message assertions use substrings (same pins as the Python matrix).
 */

import { describe, expect, it } from "vitest";

import {
  DuplicateArcError,
  DuplicatePlaceError,
  InvalidModelError,
  PetriNetError,
  TransitionNotEnabledError,
  UnknownPlaceError,
  UnknownTransitionError,
  ValueError,
} from "../../src/engine/errors.js";
import { PetriNet } from "../../src/engine/model.js";

// ---------------------------------------------------------------------------
// Builders (mirror the Python helpers)
// ---------------------------------------------------------------------------

function makeTwoWayCycle(m0: readonly [number, number] = [1, 0]): PetriNet {
  // p1 -t1-> p2 -t2-> p1, unit weights.
  const net = new PetriNet();
  net.addPlace("p1", m0[0]);
  net.addPlace("p2", m0[1]);
  net.addTransition("t1");
  net.addTransition("t2");
  net.addInput({ place: "p1", transition: "t1" });
  net.addOutput({ transition: "t1", place: "p2" });
  net.addInput({ place: "p2", transition: "t2" });
  net.addOutput({ transition: "t2", place: "p1" });
  return net;
}

// ---------------------------------------------------------------------------
// Behavior 1 — build: places/transitions/weighted arcs in orders + markings
// ---------------------------------------------------------------------------

describe("TestBuild", () => {
  it("test_build_orders_and_markings", () => {
    const net = makeTwoWayCycle([1, 0]);
    expect(net.placeOrder).toEqual(["p1", "p2"]);
    expect(net.transitionOrder).toEqual(["t1", "t2"]);
    expect(net.currentMarking()).toEqual([1, 0]);
    expect(net.initialMarkingTuple()).toEqual([1, 0]);
    expect(net.inputs).toEqual(
      new Map([
        ["t1", new Map([["p1", 1]])],
        ["t2", new Map([["p2", 1]])],
      ]),
    );
    expect(net.outputs).toEqual(
      new Map([
        ["t1", new Map([["p2", 1]])],
        ["t2", new Map([["p1", 1]])],
      ]),
    );
  });

  it("test_build_weighted_arcs", () => {
    const net = new PetriNet();
    net.addPlace("p", 3);
    net.addTransition("t");
    net.addInput({ place: "p", transition: "t", weight: 2 });
    net.addOutput({ transition: "t", place: "p", weight: 3 });
    expect(net.inputs.get("t")).toEqual(new Map([["p", 2]]));
    expect(net.outputs.get("t")).toEqual(new Map([["p", 3]]));
  });

  it("test_build_default_tokens_zero", () => {
    const net = new PetriNet();
    net.addPlace("p");
    expect(net.currentMarking()).toEqual([0]);
    expect(net.initialMarkingTuple()).toEqual([0]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 2 — duplicate names (F4 asymmetry)
// ---------------------------------------------------------------------------

describe("TestDuplicateNames", () => {
  it("test_duplicate_place_raises_duplicate_place_error", () => {
    const net = new PetriNet();
    net.addPlace("p");
    expect(() => net.addPlace("p")).toThrow(DuplicatePlaceError);
  });

  it("test_duplicate_place_error_is_invalid_model_error", () => {
    const net = new PetriNet();
    net.addPlace("p");
    expect(() => net.addPlace("p")).toThrow(InvalidModelError);
  });

  it("test_duplicate_transition_raises_plain_value_error", () => {
    // F4: duplicate transition is a plain ValueError, NOT a PetriNetError.
    const net = new PetriNet();
    net.addTransition("t");
    let caught: unknown;
    try {
      net.addTransition("t");
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(ValueError);
    expect(caught).not.toBeInstanceOf(PetriNetError);
  });
});

// ---------------------------------------------------------------------------
// Behavior 3 — empty names / bad token counts
// ---------------------------------------------------------------------------

describe("TestAddValidation", () => {
  it("test_empty_place_name_raises", () => {
    const net = new PetriNet();
    expect(() => net.addPlace("")).toThrow(/Place name cannot be empty/);
  });

  it("test_empty_transition_name_raises", () => {
    const net = new PetriNet();
    expect(() => net.addTransition("")).toThrow(/Transition name cannot be empty/);
  });

  it.each([true, false, -1, 1.5, "2"] as const)("test_bad_token_count_raises[%s]", (tokens) => {
    const net = new PetriNet();
    expect(() => net.addPlace("p", tokens as unknown as number)).toThrow(/non-negative integer/);
  });
});

// ---------------------------------------------------------------------------
// Behavior 4 — arc validation + duplicate arcs + arg-order pin
// ---------------------------------------------------------------------------

describe("TestArcs", () => {
  it("test_add_input_unknown_place_raises", () => {
    const net = new PetriNet();
    net.addTransition("t");
    expect(() => net.addInput({ place: "ghost", transition: "t" })).toThrow(UnknownPlaceError);
  });

  it("test_add_input_place_checked_before_transition", () => {
    // Both unknown -> the place error wins (validateArc order).
    const net = new PetriNet();
    expect(() => net.addInput({ place: "ghost", transition: "ghost_t" })).toThrow(UnknownPlaceError);
  });

  it("test_add_input_unknown_transition_raises", () => {
    const net = new PetriNet();
    net.addPlace("p");
    expect(() => net.addInput({ place: "p", transition: "ghost" })).toThrow(UnknownTransitionError);
  });

  it("test_add_output_unknown_place_raises", () => {
    const net = new PetriNet();
    net.addTransition("t");
    expect(() => net.addOutput({ transition: "t", place: "ghost" })).toThrow(UnknownPlaceError);
  });

  it("test_add_output_unknown_transition_raises", () => {
    const net = new PetriNet();
    net.addPlace("p");
    expect(() => net.addOutput({ transition: "ghost", place: "p" })).toThrow(UnknownTransitionError);
  });

  it.each([0, -1, true, 2.5] as const)("test_add_input_bad_weight_raises[%s]", (weight) => {
    const net = new PetriNet();
    net.addPlace("p");
    net.addTransition("t");
    expect(() => net.addInput({ place: "p", transition: "t", weight: weight as unknown as number })).toThrow(
      /positive integer/,
    );
  });

  it.each([0, -1, true, 2.5] as const)("test_add_output_bad_weight_raises[%s]", (weight) => {
    const net = new PetriNet();
    net.addPlace("p");
    net.addTransition("t");
    expect(() => net.addOutput({ transition: "t", place: "p", weight: weight as unknown as number })).toThrow(
      /positive integer/,
    );
  });

  it("test_duplicate_input_arc_rejected_regardless_of_weight", () => {
    const net = new PetriNet();
    net.addPlace("p");
    net.addTransition("t");
    net.addInput({ place: "p", transition: "t", weight: 1 });
    expect(() => net.addInput({ place: "p", transition: "t", weight: 3 })).toThrow(DuplicateArcError);
  });

  it("test_duplicate_output_arc_rejected", () => {
    const net = new PetriNet();
    net.addPlace("p");
    net.addTransition("t");
    net.addOutput({ transition: "t", place: "p" });
    expect(() => net.addOutput({ transition: "t", place: "p" })).toThrow(DuplicateArcError);
  });

  it("test_add_output_keyword_call_pins_arg_order", () => {
    // §9 gotcha neutralized by object args (A5).
    const net = new PetriNet();
    net.addPlace("p");
    net.addTransition("t");
    net.addOutput({ transition: "t", place: "p", weight: 2 });
    expect(net.outputs.get("t")).toEqual(new Map([["p", 2]]));
  });
});

// ---------------------------------------------------------------------------
// Behavior 5 — enabledness
// ---------------------------------------------------------------------------

describe("TestEnabledness", () => {
  it("test_and_across_inputs_all_sufficient", () => {
    const net = new PetriNet();
    net.addPlace("p1", 2);
    net.addPlace("p2", 1);
    net.addTransition("t");
    net.addInput({ place: "p1", transition: "t", weight: 2 });
    net.addInput({ place: "p2", transition: "t", weight: 1 });
    expect(net.isEnabledAt(net.currentMarking(), "t")).toBe(true);
  });

  it("test_and_across_inputs_one_insufficient", () => {
    const net = new PetriNet();
    net.addPlace("p1", 1); // needs 2
    net.addPlace("p2", 5);
    net.addTransition("t");
    net.addInput({ place: "p1", transition: "t", weight: 2 });
    net.addInput({ place: "p2", transition: "t", weight: 1 });
    expect(net.isEnabledAt(net.currentMarking(), "t")).toBe(false);
  });

  it("test_no_input_transition_always_enabled", () => {
    const net = new PetriNet();
    net.addPlace("p"); // zero tokens, no arc
    net.addTransition("source");
    expect(net.isEnabledAt(net.currentMarking(), "source")).toBe(true);
  });

  it("test_zero_token_place_blocks_weight1", () => {
    const net = new PetriNet();
    net.addPlace("p"); // 0 tokens
    net.addTransition("t");
    net.addInput({ place: "p", transition: "t" });
    expect(net.isEnabledAt(net.currentMarking(), "t")).toBe(false);
  });

  it("test_is_enabled_unknown_transition_raises", () => {
    const net = new PetriNet();
    expect(() => net.isEnabledAt([], "ghost")).toThrow(UnknownTransitionError);
  });

  it("test_enabled_transitions_at_sorted", () => {
    const net = new PetriNet();
    net.addPlace("p", 1);
    net.addTransition("tb"); // added first on purpose
    net.addTransition("ta");
    net.addInput({ place: "p", transition: "tb" });
    net.addInput({ place: "p", transition: "ta" });
    expect(net.enabledTransitionsAt(net.currentMarking())).toEqual(["ta", "tb"]);
  });

  it("test_enabled_transitions_at_transitions_only_net", () => {
    const net = new PetriNet();
    net.addTransition("source"); // no places -> marking [] is well-formed
    expect(net.enabledTransitionsAt([])).toEqual(["source"]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 6 — fire_marking: purity, errors, precedence
// ---------------------------------------------------------------------------

describe("TestFireMarking", () => {
  it("test_successor_and_purity", () => {
    const net = makeTwoWayCycle([1, 0]);
    const m0 = net.currentMarking();
    const succ = net.fireMarking(m0, "t1");
    expect(succ).toEqual([0, 1]);
    expect(net.currentMarking()).toEqual([1, 0]); // net untouched (pure)
    expect(m0).toEqual([1, 0]); // input marking untouched
  });

  it("test_weighted_successor", () => {
    const net = new PetriNet();
    net.addPlace("p1", 3);
    net.addPlace("p2", 0);
    net.addTransition("t");
    net.addInput({ place: "p1", transition: "t", weight: 2 });
    net.addOutput({ transition: "t", place: "p2", weight: 1 });
    expect(net.fireMarking(net.currentMarking(), "t")).toEqual([1, 1]);
  });

  it("test_disabled_raises_transition_not_enabled", () => {
    const net = makeTwoWayCycle([1, 0]);
    expect(() => net.fireMarking(net.currentMarking(), "t2")).toThrow(TransitionNotEnabledError);
  });

  it("test_unknown_transition_checked_before_marking", () => {
    const net = makeTwoWayCycle();
    expect(() => net.fireMarking([1], "ghost")).toThrow(UnknownTransitionError); // malformed too — transition wins
  });

  it("test_malformed_marking_length_raises", () => {
    const net = makeTwoWayCycle();
    expect(() => net.fireMarking([1, 0, 0], "t1")).toThrow(/length/);
  });

  it("test_malformed_marking_negative_raises", () => {
    const net = makeTwoWayCycle();
    expect(() => net.fireMarking([1, -1], "t1")).toThrow(/negative/);
  });

  it("test_marking_value_error_precedes_not_enabled", () => {
    // must-pin: ValueError (malformed) BEFORE TransitionNotEnabledError.
    const net = makeTwoWayCycle([0, 1]); // t1 disabled at this marking
    expect(() => net.fireMarking([0], "t1")).toThrow(ValueError); // malformed AND disabled -> ValueError
  });
});

// ---------------------------------------------------------------------------
// Behavior 7 — fire (mutable) + reset
// ---------------------------------------------------------------------------

describe("TestFireAndReset", () => {
  it("test_fire_mutates_live_marking", () => {
    const net = makeTwoWayCycle([1, 0]);
    net.fire("t1");
    expect(net.currentMarking()).toEqual([0, 1]);
  });

  it("test_fire_error_leaves_live_marking_unchanged", () => {
    const net = makeTwoWayCycle([1, 0]);
    expect(() => net.fire("t2")).toThrow(TransitionNotEnabledError);
    expect(net.currentMarking()).toEqual([1, 0]);
  });

  it("test_reset_restores_initial_marking", () => {
    const net = makeTwoWayCycle([1, 0]);
    net.fire("t1");
    net.reset();
    expect(net.currentMarking()).toEqual([1, 0]);
    expect(net.initialMarkingTuple()).toEqual([1, 0]);
  });

  it("test_reset_returns_a_copy", () => {
    const net = makeTwoWayCycle([1, 0]);
    net.fire("t1");
    net.reset();
    net.fire("t1"); // mutating live marking must not corrupt M0
    expect(net.initialMarkingTuple()).toEqual([1, 0]);
    expect(net.currentMarking()).toEqual([0, 1]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 8 — self-loop: net effect M-1+1
// ---------------------------------------------------------------------------

describe("TestSelfLoop", () => {
  function selfLoopNet(): PetriNet {
    const net = new PetriNet();
    net.addPlace("counter", 1);
    net.addTransition("process");
    net.addInput({ place: "counter", transition: "process" });
    net.addOutput({ transition: "process", place: "counter" });
    return net;
  }

  it("test_self_loop_enabled_and_neutral", () => {
    const net = selfLoopNet();
    const m = net.currentMarking();
    expect(net.isEnabledAt(m, "process")).toBe(true);
    expect(net.fireMarking(m, "process")).toEqual([1]);
    net.fire("process");
    expect(net.currentMarking()).toEqual([1]);
    expect(net.isEnabledAt(net.currentMarking(), "process")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Behavior 9 — parallel transitions
// ---------------------------------------------------------------------------

describe("TestParallelTransitions", () => {
  it("test_both_enabled_distinct_successors", () => {
    const net = new PetriNet();
    net.addPlace("p", 1);
    net.addPlace("pa", 0);
    net.addPlace("pb", 0);
    net.addTransition("ta");
    net.addTransition("tb");
    net.addInput({ place: "p", transition: "ta" });
    net.addOutput({ transition: "ta", place: "pa" });
    net.addInput({ place: "p", transition: "tb" });
    net.addOutput({ transition: "tb", place: "pb" });
    const m = net.currentMarking();
    expect(net.enabledTransitionsAt(m)).toEqual(["ta", "tb"]);
    expect(net.fireMarking(m, "ta")).toEqual([0, 1, 0]);
    expect(net.fireMarking(m, "tb")).toEqual([0, 0, 1]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 10 — marking accessors, orders, place_index
// ---------------------------------------------------------------------------

describe("TestMarkingAccessors", () => {
  it("test_sorted_orders", () => {
    const net = new PetriNet();
    net.addPlace("z", 1);
    net.addPlace("a", 2);
    net.addTransition("tz");
    net.addTransition("ta");
    expect(net.placeOrder).toEqual(["a", "z"]);
    expect(net.transitionOrder).toEqual(["ta", "tz"]);
    expect(net.currentMarking()).toEqual([2, 1]); // (a, z) order
  });

  it("test_place_index", () => {
    const net = new PetriNet();
    net.addPlace("z");
    net.addPlace("a");
    expect(net.placeIndex).toEqual(
      new Map([
        ["a", 0],
        ["z", 1],
      ]),
    );
  });

  it("test_marking_round_trip", () => {
    const net = makeTwoWayCycle([1, 0]);
    expect(net.markingToDict(net.currentMarking())).toEqual(
      new Map([
        ["p1", 1],
        ["p2", 0],
      ]),
    );
    expect(net.markingToDict([0, 1])).toEqual(
      new Map([
        ["p1", 0],
        ["p2", 1],
      ]),
    );
  });

  it("test_marking_to_dict_length_mismatch", () => {
    const net = makeTwoWayCycle();
    expect(() => net.markingToDict([1])).toThrow(/length/);
  });

  it("test_marking_to_dict_negative", () => {
    const net = makeTwoWayCycle();
    expect(() => net.markingToDict([1, -1])).toThrow(/negative/);
  });
});

// ---------------------------------------------------------------------------
// Behavior 11 — pre_set / post_set (F5)
// ---------------------------------------------------------------------------

describe("TestStructuralQueries", () => {
  it("test_transition_pre_post", () => {
    const net = makeTwoWayCycle();
    expect(net.preSet("t1")).toEqual(new Set(["p1"]));
    expect(net.postSet("t1")).toEqual(new Set(["p2"]));
  });

  it("test_place_pre_post", () => {
    const net = makeTwoWayCycle();
    expect(net.preSet("p2")).toEqual(new Set(["t1"])); // producers
    expect(net.postSet("p2")).toEqual(new Set(["t2"])); // consumers
  });

  it("test_unknown_node_raises", () => {
    const net = new PetriNet();
    expect(() => net.preSet("ghost")).toThrow(/Unknown node/);
    expect(() => net.preSet("ghost")).toThrow(PetriNetError);
  });

  it("test_ambiguous_node_raises", () => {
    const net = new PetriNet();
    net.addPlace("x");
    net.addTransition("x");
    expect(() => net.postSet("x")).toThrow(InvalidModelError);
    expect(() => net.postSet("x")).toThrow(/Ambiguous/);
  });
});

// ---------------------------------------------------------------------------
// Behavior 12 — empty net
// ---------------------------------------------------------------------------

describe("TestEmptyNet", () => {
  it("test_empty_net_semantics", () => {
    const net = new PetriNet();
    expect(net.currentMarking()).toEqual([]);
    expect(net.initialMarkingTuple()).toEqual([]);
    expect(net.placeOrder).toEqual([]);
    expect(net.transitionOrder).toEqual([]);
    expect(net.placeIndex).toEqual(new Map());
    expect(net.enabledTransitionsAt([])).toEqual([]);
    net.reset(); // no-op
    expect(net.currentMarking()).toEqual([]);
  });

  it("test_empty_net_unknown_transition_raises", () => {
    const net = new PetriNet();
    expect(() => net.isEnabledAt([], "t")).toThrow(UnknownTransitionError);
  });
});
