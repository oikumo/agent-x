// @vitest-environment node
/**
 * Analysis-layer tests — design_001 §10.2 (38 behaviors, 1:1 port of
 * `tests/model/petri_net/test_analysis.py`). Fixtures inlined from the Python
 * file. Assertions translate frozensets → sorted-array equality via
 * `compareMarkings`; `AnalysisResult` deep-equal incl. `reason`; truncated
 * reasons verbatim (B5/B6).
 */

import { describe, expect, it } from "vitest";

import { PetriNetAnalyzer, markingKey } from "../../src/engine/analysis.js";
import { PetriNet } from "../../src/engine/model.js";

// ---------------------------------------------------------------------------
// §30 fixtures (mirror of test_analysis.py make_net + net defns)
// ---------------------------------------------------------------------------

interface NetDefn {
  places: string[];
  transitions: string[];
  arcs: Array<[string, string, number]>;
}

function makeNet(defn: NetDefn, initialMarking: Record<string, number> = {}): PetriNet {
  const net = new PetriNet();
  for (const p of defn.places) net.addPlace(p, initialMarking[p] ?? 0);
  for (const t of defn.transitions) net.addTransition(t);
  for (const [src, dst, w] of defn.arcs) {
    if (defn.places.includes(src)) {
      net.addInput({ place: src, transition: dst, weight: w });
    } else {
      net.addOutput({ transition: src, place: dst, weight: w });
    }
  }
  return net;
}

const TWO_WAY_CYCLE: NetDefn = {
  places: ["p1", "p2"],
  transitions: ["t1", "t2"],
  arcs: [
    ["p1", "t1", 1],
    ["t1", "p2", 1],
    ["p2", "t2", 1],
    ["t2", "p1", 1],
  ],
};
const CONSERVATION_M0 = { p1: 1, p2: 1 };
const LIVE_BOUNDED_M0 = { p1: 1, p2: 0 };

const UNBOUNDED_NET: NetDefn = {
  places: ["p"],
  transitions: ["t"],
  arcs: [
    ["p", "t", 1],
    ["t", "p", 2],
  ],
};
const DEADLOCK_NET: NetDefn = {
  places: ["p"],
  transitions: ["t"],
  arcs: [["p", "t", 1]],
}; // M0 p=0 -> t never enabled
const TOKEN_DRAIN_NET: NetDefn = {
  // token flows to a deadlock (2 SCCs; t fires once then dead)
  places: ["p1", "p2"],
  transitions: ["t"],
  arcs: [
    ["p1", "t", 1],
    ["t", "p2", 1],
  ],
};
const TWO_DEADLOCKS_NET: NetDefn = {
  // (1,0) branches to two distinct deadlock markings
  places: ["p1", "p2"],
  transitions: ["t1", "t2"],
  arcs: [
    ["p1", "t1", 1],
    ["t1", "p2", 1],
    ["p1", "t2", 1],
  ],
};

const TRUNCATED_DEADLOCK_REASON =
  "State-space exploration was truncated; " +
  "listed deadlocks are only those among explored states.";
const TRUNCATED_BOUNDS_REASON =
  "State-space exploration was truncated; boundedness is unknown.";

// ---------------------------------------------------------------------------
// Behaviors 13–14 — reachable_markings (happy + truncated)
// ---------------------------------------------------------------------------

describe("TestReachableMarkings", () => {
  it("reachable two-way cycle complete", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const result = new PetriNetAnalyzer(net).reachableMarkings(null);
    expect(result.markings).toEqual([
      [0, 1],
      [1, 0],
    ]);
    expect(result.complete).toBe(true);
    expect(result.exploredStates).toBe(2);
    expect(result.predecessors.get(markingKey([1, 0]))).toEqual({
      prev: null,
      transition: null,
    });
    expect(result.predecessors.get(markingKey([0, 1]))).toEqual({
      prev: [1, 0],
      transition: "t1",
    });
  });

  it("reachable truncated max_states 1", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const result = new PetriNetAnalyzer(net).reachableMarkings(1);
    expect(result.markings).toEqual([[1, 0]]);
    expect(result.complete).toBe(false);
    expect(result.exploredStates).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Behavior 15 — reachability_graph (happy + truncated)
// ---------------------------------------------------------------------------

describe("TestReachabilityGraph", () => {
  it("graph two-way cycle complete", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const graph = new PetriNetAnalyzer(net).reachabilityGraph(null);
    expect(graph.states).toEqual([
      [0, 1],
      [1, 0],
    ]);
    expect(graph.edges.get(markingKey([1, 0]))).toEqual([["t1", [0, 1]]]);
    expect(graph.edges.get(markingKey([0, 1]))).toEqual([["t2", [1, 0]]]);
    expect(graph.complete).toBe(true);
  });

  it("graph truncated records edges to unvisited", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const graph = new PetriNetAnalyzer(net).reachabilityGraph(1);
    expect(graph.states).toEqual([[1, 0]]);
    // edge to the unvisited (0,1) is still recorded; consumers check complete
    expect(graph.edges.get(markingKey([1, 0]))).toEqual([["t1", [0, 1]]]);
    expect(graph.complete).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Behavior 16 — firing_sequence_to
// ---------------------------------------------------------------------------

describe("TestFiringSequenceTo", () => {
  it("shortest sequence", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const result = analyzer.reachableMarkings(null);
    expect(analyzer.firingSequenceTo(result, [0, 1])).toEqual(["t1"]);
  });

  it("sequence to initial marking is empty", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const result = analyzer.reachableMarkings(null);
    expect(analyzer.firingSequenceTo(result, [1, 0])).toEqual([]);
  });

  it("absent target on complete result is null", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const result = analyzer.reachableMarkings(null);
    expect(result.complete).toBe(true);
    // null here IS a proof of unreachability (complete exploration).
    expect(analyzer.firingSequenceTo(result, [9, 9])).toBeNull();
  });

  it("absent target on truncated result is null not proof", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const result = analyzer.reachableMarkings(1);
    expect(result.complete).toBe(false);
    // (0,1) IS reachable, but the truncated search cannot prove anything.
    expect(analyzer.firingSequenceTo(result, [0, 1])).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Behavior 17 — deadlocks (happy + truncated; never "deadlock-free")
// ---------------------------------------------------------------------------

describe("TestDeadlocks", () => {
  it("deadlock net found complete", () => {
    const net = makeNet(DEADLOCK_NET); // M0 p=0
    const result = new PetriNetAnalyzer(net).deadlocks(null);
    expect(result.deadlocks).toEqual([[0]]);
    expect(result.complete).toBe(true);
    expect(result.reason).toBeNull();
  });

  it("truncated search never claims deadlock free", () => {
    const net = makeNet(UNBOUNDED_NET, { p: 1 });
    const result = new PetriNetAnalyzer(net).deadlocks(3);
    expect(result.deadlocks).toEqual([]); // none among explored — NOT a proof
    expect(result.complete).toBe(false);
    expect(result.reason).toBe(TRUNCATED_DEADLOCK_REASON);
  });
});

// ---------------------------------------------------------------------------
// Behavior 18 — bounds (happy + truncated; never bounded=True from truncation)
// ---------------------------------------------------------------------------

describe("TestBounds", () => {
  it("bounds complete finite", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const result = new PetriNetAnalyzer(net).bounds(null);
    expect(result.bounded).toBe(true);
    expect(result.bounds).toEqual([
      ["p1", 1],
      ["p2", 1],
    ]);
    expect(result.complete).toBe(true);
    expect(result.reason).toBeNull();
  });

  it("bounds truncated unbounded net", () => {
    const net = makeNet(UNBOUNDED_NET, { p: 1 });
    const result = new PetriNetAnalyzer(net).bounds(5);
    expect(result.bounded).toBeNull(); // unknown — never overclaimed (§16/§39)
    expect(result.complete).toBe(false);
    expect(result.reason).toBe(TRUNCATED_BOUNDS_REASON);
    expect(result.bounds).toEqual([["p", 5]]); // observed maxima only
  });
});

// ---------------------------------------------------------------------------
// Behavior 19 — incidence_matrix (exact; degenerate shapes)
// ---------------------------------------------------------------------------

describe("TestIncidenceMatrix", () => {
  it("two-way cycle matrix", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    expect(new PetriNetAnalyzer(net).incidenceMatrix()).toEqual([
      [-1, 1],
      [1, -1],
    ]);
  });

  it("unbounded net matrix", () => {
    const net = makeNet(UNBOUNDED_NET, { p: 1 });
    expect(new PetriNetAnalyzer(net).incidenceMatrix()).toEqual([[1]]);
  });

  it("places only matrix p-by-0", () => {
    const net = makeNet({ places: ["a", "b"], transitions: [], arcs: [] });
    expect(new PetriNetAnalyzer(net).incidenceMatrix()).toEqual([[], []]);
  });

  it("transitions only matrix 0 rows", () => {
    const net = makeNet({ places: [], transitions: ["ta", "tb"], arcs: [] });
    expect(new PetriNetAnalyzer(net).incidenceMatrix()).toEqual([]);
  });

  it("empty net matrix", () => {
    const net = makeNet({ places: [], transitions: [], arcs: [] });
    expect(new PetriNetAnalyzer(net).incidenceMatrix()).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 20 — place_invariants (exact; degenerate bases)
// ---------------------------------------------------------------------------

describe("TestPlaceInvariants", () => {
  it("two-way cycle conservation invariant", () => {
    const net = makeNet(TWO_WAY_CYCLE, CONSERVATION_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const invariants = analyzer.placeInvariants();
    expect(invariants).toEqual([[1, 1]]);
    // conservation: y · m constant across the reachable markings
    const result = analyzer.reachableMarkings(null);
    for (const m of result.markings) {
      let sum = 0;
      for (let i = 0; i < invariants[0].length; i++) {
        sum += invariants[0][i] * m[i];
      }
      expect(sum).toBe(2);
    }
  });

  it("places only identity basis", () => {
    const net = makeNet({ places: ["a", "b"], transitions: [], arcs: [] });
    expect(new PetriNetAnalyzer(net).placeInvariants()).toEqual([
      [1, 0],
      [0, 1],
    ]);
  });

  it("transitions only no place invariants", () => {
    const net = makeNet({ places: [], transitions: ["ta"], arcs: [] });
    expect(new PetriNetAnalyzer(net).placeInvariants()).toEqual([]);
  });

  it("empty net no place invariants", () => {
    const net = makeNet({ places: [], transitions: [], arcs: [] });
    expect(new PetriNetAnalyzer(net).placeInvariants()).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 21 — transition_invariants (exact; degenerate bases)
// ---------------------------------------------------------------------------

describe("TestTransitionInvariants", () => {
  it("two-way cycle t-invariant", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    expect(new PetriNetAnalyzer(net).transitionInvariants()).toEqual([[1, 1]]);
  });

  it("transitions only identity basis", () => {
    const net = makeNet({ places: [], transitions: ["ta", "tb"], arcs: [] });
    expect(new PetriNetAnalyzer(net).transitionInvariants()).toEqual([
      [1, 0],
      [0, 1],
    ]);
  });

  it("places only no transition invariants", () => {
    const net = makeNet({ places: ["a"], transitions: [], arcs: [] });
    expect(new PetriNetAnalyzer(net).transitionInvariants()).toEqual([]);
  });

  it("empty net no transition invariants", () => {
    const net = makeNet({ places: [], transitions: [], arcs: [] });
    expect(new PetriNetAnalyzer(net).transitionInvariants()).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 22 — transition_liveness (complete verdict + incomplete unknown)
// ---------------------------------------------------------------------------

describe("TestTransitionLiveness", () => {
  it("live net transitions live", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    expect(analyzer.transitionLiveness("t1", graph)).toEqual({
      value: true,
      complete: true,
      exploredStates: 2,
      reason: null,
    });
    expect(analyzer.transitionLiveness("t2", graph)).toEqual({
      value: true,
      complete: true,
      exploredStates: 2,
      reason: null,
    });
  });

  it("deadlock net transition not live", () => {
    const net = makeNet(DEADLOCK_NET);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    expect(analyzer.transitionLiveness("t", graph)).toEqual({
      value: false,
      complete: true,
      exploredStates: 1,
      reason: null,
    });
  });

  it("incomplete graph unknown", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(1);
    expect(analyzer.transitionLiveness("t1", graph)).toEqual({
      value: null,
      complete: false,
      exploredStates: 1,
      reason: "Reachability graph is incomplete; liveness is unknown.",
    });
  });
});

// ---------------------------------------------------------------------------
// Behavior 23 — is_live (incl. empty net F1)
// ---------------------------------------------------------------------------

describe("TestIsLive", () => {
  it("live net is live", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    expect(analyzer.isLive(graph)).toEqual({
      value: true,
      complete: true,
      exploredStates: 2,
      reason: null,
    });
  });

  it("fire once then dead not live", () => {
    const net = makeNet(TOKEN_DRAIN_NET, { p1: 1 });
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    expect(analyzer.isLive(graph)).toEqual({
      value: false,
      complete: true,
      exploredStates: 2,
      reason: null,
    });
  });

  it("incomplete graph unknown", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(1);
    expect(analyzer.isLive(graph)).toEqual({
      value: null,
      complete: false,
      exploredStates: 1,
      reason: "Reachability graph is incomplete; global liveness is unknown.",
    });
  });

  it("empty net is live f1", () => {
    const net = makeNet({ places: [], transitions: [], arcs: [] });
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    // F1: §31 uniform rule — explored_states == len(graph.states) == 1.
    expect(analyzer.isLive(graph)).toEqual({
      value: true,
      complete: true,
      exploredStates: 1,
      reason: null,
    });
  });
});

// ---------------------------------------------------------------------------
// Behavior 24 — strongly_connected_components
// ---------------------------------------------------------------------------

describe("TestStronglyConnectedComponents", () => {
  it("cycle single component", () => {
    const net = makeNet(TWO_WAY_CYCLE, LIVE_BOUNDED_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    const sccs = analyzer.stronglyConnectedComponents(graph);
    // component = sorted markings of the single SCC (B6)
    expect(sccs).toEqual([
      [
        [0, 1],
        [1, 0],
      ],
    ]);
  });

  it("deadlock net single state component", () => {
    const net = makeNet(DEADLOCK_NET);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    expect(analyzer.stronglyConnectedComponents(graph)).toEqual([[[0]]]);
  });

  it("token drain two components", () => {
    const net = makeNet(TOKEN_DRAIN_NET, { p1: 1 });
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    const sccs = analyzer.stronglyConnectedComponents(graph);
    expect(sccs).toHaveLength(2);
    expect(sccs).toContainEqual([[0, 1]]);
    expect(sccs).toContainEqual([[1, 0]]);
  });

  it("empty net single component", () => {
    const net = makeNet({ places: [], transitions: [], arcs: [] });
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(null);
    expect(analyzer.stronglyConnectedComponents(graph)).toEqual([[[]]]);
  });
});

// ---------------------------------------------------------------------------
// Behavior 25 — determinism (§29) + sorted deadlocks
// ---------------------------------------------------------------------------

describe("TestDeterminism", () => {
  it("repeated calls equal", () => {
    const net = makeNet(TWO_WAY_CYCLE, CONSERVATION_M0);
    const analyzer = new PetriNetAnalyzer(net);
    const first = analyzer.reachableMarkings(null);
    const second = analyzer.reachableMarkings(null);
    expect(first).toEqual(second);
    expect(analyzer.reachabilityGraph(null)).toEqual(
      analyzer.reachabilityGraph(null),
    );
  });

  it("deadlocks sorted", () => {
    const net = makeNet(TWO_DEADLOCKS_NET, { p1: 1 });
    const result = new PetriNetAnalyzer(net).deadlocks(null);
    expect(result.complete).toBe(true);
    expect(result.deadlocks).toEqual([
      [0, 0],
      [0, 1],
    ]); // sorted tuple (§29)
  });
});