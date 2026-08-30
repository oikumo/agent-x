// @vitest-environment node
/**
 * animation helpers tests — design_001 §10.2.
 *
 * `markingAt(net, m0, seq, step)` folds `net.fireMarking` over `seq.slice(0, k)`,
 * clamped to [0, seq.length]; returns a NEW array. `sequenceSteps` returns
 * `[m0, …, final]` (length seq.length + 1). Both pure + deterministic.
 * Null sequences (`firingSequenceTo` → null) are a CALLER case — the UI
 * renders "unreachable"; the helpers are never called with null (op spec).
 */

import { describe, expect, it } from "vitest";

import { PetriNetAnalyzer } from "../../src/engine/analysis.js";
import { PetriNet } from "../../src/engine/model.js";
import { markingAt, sequenceSteps } from "../../src/ui/animation.js";

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

const CHAIN: NetDefn = {
  places: ["p1", "p2", "p3"],
  transitions: ["a", "b"],
  arcs: [
    ["p1", "a", 1],
    ["a", "p2", 1],
    ["p2", "b", 1],
    ["b", "p3", 1],
  ],
}; // M0=[1,0,0] -> a -> [0,1,0] -> b -> [0,0,1]

describe("markingAt", () => {
  const net = makeNet(CHAIN, { p1: 1 });
  const m0 = net.initialMarkingTuple();
  const seq = ["a", "b"];

  it("step 0 returns a copy of M0", () => {
    const out = markingAt(net, m0, seq, 0);
    expect(out).toEqual([1, 0, 0]);
    expect(out).not.toBe(m0); // new array, never aliases
  });

  it("step k folds fireMarking over seq.slice(0, k)", () => {
    expect(markingAt(net, m0, seq, 1)).toEqual([0, 1, 0]);
    expect(markingAt(net, m0, seq, 2)).toEqual([0, 0, 1]);
  });

  it("matches reachableMarkings successors at each step", () => {
    const analyzer = new PetriNetAnalyzer(net);
    const reach = analyzer.reachableMarkings(null);
    const seqTo = analyzer.firingSequenceTo(reach, [0, 0, 1])!;
    expect(seqTo).toEqual(seq);
    const steps = sequenceSteps(net, m0, seqTo);
    // every prefix marking is reachable from M0 along the engine's sequence
    expect(steps[0]).toEqual([1, 0, 0]);
    expect(steps[1]).toEqual([0, 1, 0]);
    expect(steps[2]).toEqual([0, 0, 1]);
  });

  it("clamps step beyond seq.length to the final marking", () => {
    expect(markingAt(net, m0, seq, 10)).toEqual([0, 0, 1]);
    expect(markingAt(net, m0, seq, -1)).toEqual([1, 0, 0]);
  });

  it("deterministic + fresh array each call", () => {
    const a = markingAt(net, m0, seq, 1);
    const b = markingAt(net, m0, seq, 1);
    expect(a).toEqual(b);
    expect(a).not.toBe(b);
  });
});

describe("sequenceSteps", () => {
  it("length seq.length + 1, first = M0, last = target", () => {
    const net = makeNet(CHAIN, { p1: 1 });
    const m0 = net.initialMarkingTuple();
    const steps = sequenceSteps(net, m0, ["a", "b"]);
    expect(steps).toHaveLength(3);
    expect(steps[0]).toEqual([1, 0, 0]);
    expect(steps[2]).toEqual([0, 0, 1]);
  });

  it("single-transition sequence", () => {
    const net = makeNet(CHAIN, { p1: 1 });
    const steps = sequenceSteps(net, net.initialMarkingTuple(), ["a"]);
    expect(steps).toEqual([
      [1, 0, 0],
      [0, 1, 0],
    ]);
  });

  it("deterministic", () => {
    const net = makeNet(CHAIN, { p1: 1 });
    const m0 = net.initialMarkingTuple();
    expect(sequenceSteps(net, m0, ["a", "b"])).toEqual(
      sequenceSteps(net, m0, ["a", "b"]),
    );
  });
});