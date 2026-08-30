// @vitest-environment node
/**
 * graphProjection tests — design_001 §10.1.
 *
 * Pure projection: `reachabilityGraph` + SCCs + deadlocks + positions →
 * React Flow nodes/edges. Node ids = markingKey; label "M0" for the initial
 * marking else "(m.join(","))"; sccIndex/deadlock/initial flags; positions
 * injected (missing → origin); edge ids unique under parallel transitions;
 * edge order = engine order; deterministic (deep-equal on identical inputs).
 *
 * NOTE (design-gap resolution, recorded in test report): design §4 pins the
 * signature without the initial marking, yet the label rule requires
 * `marking === initialMarkingTuple`. Resolution: the caller passes
 * `initialMarking` (the net's M0 tuple) as the final parameter.
 */

import { describe, expect, it } from "vitest";

import { PetriNetAnalyzer } from "../../src/engine/analysis.js";
import { PetriNet } from "../../src/engine/model.js";
import { projectGraph } from "../../src/ui/graphProjection.js";

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

const HELLO: NetDefn = { places: ["p"], transitions: ["t"], arcs: [["p", "t", 1]] };
const PARALLEL: NetDefn = {
  places: ["p1", "p2"],
  transitions: ["ta", "tb"],
  arcs: [
    ["p1", "ta", 1],
    ["ta", "p2", 1],
    ["p1", "tb", 1],
    ["tb", "p2", 1],
  ],
};
const UNBOUNDED: NetDefn = {
  places: ["p"],
  transitions: ["t"],
  arcs: [
    ["p", "t", 1],
    ["t", "p", 2],
  ],
};

function project(net: PetriNet, maxStates: number | null = null) {
  const analyzer = new PetriNetAnalyzer(net);
  const graph = analyzer.reachabilityGraph(maxStates);
  const args = [
    graph,
    analyzer.stronglyConnectedComponents(graph),
    analyzer.deadlocks(maxStates).deadlocks,
    {},
    net.placeOrder,
    net.initialMarkingTuple(),
  ] as const;
  return {
    graph,
    result: projectGraph(...args),
    withPositions: (positions: Record<string, { x: number; y: number }>) =>
      projectGraph(graph, args[1], args[2], positions, net.placeOrder, net.initialMarkingTuple()),
  };
}

describe("projectGraph — nodes", () => {
  const net = makeNet(HELLO, { p: 1 });
  const { result } = project(net);

  it("ids are markingKey values; labels M0 vs tuple text; flags set", () => {
    const byId = new Map(result.nodes.map((n) => [n.id, n]));
    expect([...byId.keys()].sort()).toEqual(["0", "1"]);
    expect(byId.get("1")?.data.label).toBe("M0");
    expect(byId.get("0")?.data.label).toBe("(0)");
    expect(byId.get("1")?.data.initial).toBe(true);
    expect(byId.get("0")?.data.initial).toBe(false);
    expect(byId.get("0")?.data.marking).toEqual([0]);
  });

  it("sccIndex is the component index; deadlock flag from the deadlock set", () => {
    const byId = new Map(result.nodes.map((n) => [n.id, n]));
    expect(byId.get("0")?.data.sccIndex).toBe(0);
    expect(byId.get("1")?.data.sccIndex).toBe(1);
    expect(byId.get("0")?.data.deadlock).toBe(true);
    expect(byId.get("1")?.data.deadlock).toBe(false);
  });

  it("positions injected; missing key falls back to origin", () => {
    const byId = new Map(
      project(net).withPositions({ "1": { x: 50, y: 80 } }).nodes.map((n) => [n.id, n]),
    );
    expect(byId.get("1")?.position).toEqual({ x: 50, y: 80 });
    expect(byId.get("0")?.position).toEqual({ x: 0, y: 0 });
  });
});

describe("projectGraph — edges", () => {
  it("hello: one edge with transition label + arrow marker", () => {
    const { result } = project(makeNet(HELLO, { p: 1 }));
    expect(result.edges).toHaveLength(1);
    expect(result.edges[0]).toMatchObject({
      id: "1::t::0",
      source: "1",
      target: "0",
      label: "t",
    });
    expect(result.edges[0].data?.transition).toBe("t");
    expect(result.edges[0].markerEnd).toBeDefined();
  });

  it("parallel transitions: distinct edge ids, engine edge order", () => {
    const net = makeNet(PARALLEL, { p1: 1 });
    const { graph, result } = project(net);
    expect(result.edges).toHaveLength(2);
    expect(new Set(result.edges.map((e) => e.id)).size).toBe(2);
    expect(result.edges.map((e) => e.id).sort()).toEqual(["1,0::ta::0,1", "1,0::tb::0,1"]);
    expect(result.edges.map((e) => e.data?.transition)).toEqual(
      graph.edges.get("1,0")!.map(([t]) => t),
    );
  });

  it("truncated graph: dangling edge to an absent node id still emitted", () => {
    const net = makeNet(UNBOUNDED, { p: 1 });
    const { graph, result } = project(net, 2);
    expect(graph.complete).toBe(false);
    expect(result.nodes.map((n) => n.id)).toEqual(["1", "2"]);
    const dangling = result.edges.find((e) => e.target === "3");
    expect(dangling).toBeDefined();
    expect(dangling?.source).toBe("2");
  });
});

describe("projectGraph — determinism", () => {
  it("same inputs produce deep-equal output", () => {
    const net = makeNet(PARALLEL, { p1: 1 });
    const { result } = project(net);
    expect(project(net).result).toEqual(result);
  });
});