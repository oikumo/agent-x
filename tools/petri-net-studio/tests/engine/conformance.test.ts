// @vitest-environment node
/**
 * Conformance-vector suite — design_001 §10.3. Reads the generator-produced
 * vectors under `shared/petri-net/conformance/analysis-v1/*.json`, builds
 * each net via `documentFromJson`, runs ALL analysis APIs with the vector's
 * `max_states`, and deep-compares against `expected` (B9: sorted arrays;
 * maps re-keyed by markingKey). Failures name the vector id + API.
 */

import { readdirSync, readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { PetriNetAnalyzer, markingKey } from "../../src/engine/analysis.js";
import { documentFromJson } from "../../src/engine/io.js";
import type { ReachabilityResult } from "../../src/engine/analysis.js";

const VECTORS_DIR = new URL(
  "../../../../shared/petri-net/conformance/analysis-v1/",
  import.meta.url,
);

let vectorFiles: string[] = [];
try {
  vectorFiles = readdirSync(VECTORS_DIR)
    .filter((f) => f.endsWith(".json"))
    .sort();
} catch {
  vectorFiles = [];
}

/** Serialized firing_sequences: sorted [marking, seq] pairs + [target, null]. */
function computeFiringSequences(
  reach: ReachabilityResult,
  analyzer: PetriNetAnalyzer,
): Array<[number[], string[] | null]> {
  const items: Array<[number[], string[] | null]> = [];
  for (const m of reach.markings) {
    items.push([m, analyzer.firingSequenceTo(reach, m)]);
  }
  // one provably-unreachable (or, on truncation, absent) target -> null:
  // per-place max token count over explored states, +1.
  const maxTokens: number[] = [];
  for (const m of reach.markings) {
    for (let i = 0; i < m.length; i++) {
      if (i >= maxTokens.length) maxTokens.push(0);
      if (m[i] > maxTokens[i]) maxTokens[i] = m[i];
    }
  }
  const target = maxTokens.map((x) => x + 1);
  items.push([target, analyzer.firingSequenceTo(reach, target)]);
  return items;
}

describe("TestConformanceVectors", () => {
  it("generator has produced at least one vector", () => {
    expect(vectorFiles.length).toBeGreaterThan(0);
  });

  it.each(vectorFiles)("%s matches expected analysis results", (file) => {
    const text = readFileSync(new URL(file, VECTORS_DIR), "utf-8");
    const vector = JSON.parse(text);
    const doc = documentFromJson(JSON.stringify(vector.net));
    const analyzer = new PetriNetAnalyzer(doc.net);
    const maxStates = vector.max_states as number | null;
    const exp = vector.expected;

    // reachable_markings
    const reach = analyzer.reachableMarkings(maxStates);
    expect(reach.markings).toEqual(exp.reachable_markings.markings);
    expect(reach.complete).toBe(exp.reachable_markings.complete);
    expect(reach.exploredStates).toBe(exp.reachable_markings.explored_states);
    expect(reach.predecessors.size).toBe(exp.reachable_markings.predecessors.length);
    for (const [marking, prev, transition] of exp.reachable_markings.predecessors) {
      expect(reach.predecessors.get(markingKey(marking))).toEqual({ prev, transition });
    }

    // reachability_graph
    const graph = analyzer.reachabilityGraph(maxStates);
    expect(graph.states).toEqual(exp.reachability_graph.states);
    expect(graph.complete).toBe(exp.reachability_graph.complete);
    expect(graph.edges.size).toBe(exp.reachability_graph.edges.length);
    for (const [key, edges] of exp.reachability_graph.edges) {
      expect(graph.edges.get(key)).toEqual(edges);
    }

    // deadlocks
    const deadlocks = analyzer.deadlocks(maxStates);
    expect(deadlocks.deadlocks).toEqual(exp.deadlocks.deadlocks);
    expect(deadlocks.complete).toBe(exp.deadlocks.complete);
    expect(deadlocks.exploredStates).toBe(exp.deadlocks.explored_states);
    expect(deadlocks.reason).toBe(exp.deadlocks.reason);

    // bounds
    const bounds = analyzer.bounds(maxStates);
    expect(bounds.bounded).toBe(exp.bounds.bounded);
    expect(bounds.bounds).toEqual(exp.bounds.bounds);
    expect(bounds.complete).toBe(exp.bounds.complete);
    expect(bounds.reason).toBe(exp.bounds.reason);

    // incidence + invariants
    expect(analyzer.incidenceMatrix()).toEqual(exp.incidence_matrix);
    expect(analyzer.placeInvariants()).toEqual(exp.place_invariants);
    expect(analyzer.transitionInvariants()).toEqual(exp.transition_invariants);

    // firing_sequences
    expect(computeFiringSequences(reach, analyzer)).toEqual(exp.firing_sequences);

    // liveness (is_live + per-transition on the SAME graph)
    const isLive = analyzer.isLive(graph);
    expect([
      isLive.value,
      isLive.complete,
      isLive.exploredStates,
      isLive.reason ?? null,
    ]).toEqual(exp.liveness.is_live);
    const transitions = analyzer.net.transitionOrder.map((t) => {
      const r = analyzer.transitionLiveness(t, graph);
      return [t, r.value, r.complete, r.exploredStates, r.reason ?? null];
    });
    expect(transitions).toEqual(exp.liveness.transitions);

    // sccs
    expect(analyzer.stronglyConnectedComponents(graph)).toEqual(exp.sccs);
  });
});