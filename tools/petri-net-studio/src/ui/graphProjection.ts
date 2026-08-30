/**
 * Pure projection: reachability graph + SCCs + deadlocks + positions →
 * React Flow nodes/edges (design §4, C5). Layout is a separate step — the
 * projection never computes positions (testable without elkjs).
 *
 * Pure/DOM-free module: only TYPE imports from @xyflow/react (the value
 * bundle would pull React DOM into node-env tests); the arrow marker uses
 * the `"arrowclosed"` string literal (MarkerType.ArrowClosed, design §4).
 *
 * NOTE (design-gap resolution, recorded in the test report): design §4 pins
 * the signature without the initial marking, yet the label rule requires
 * `marking === initialMarkingTuple`. Resolution: the caller passes
 * `initialMarking` (the net's M0 tuple) as the final parameter.
 */

import type { Edge, Node } from "@xyflow/react";
import { markingKey, type ReachabilityGraph } from "../engine/analysis.js";
import type { Point } from "../state/store.js";

export interface GraphNodeData extends Record<string, unknown> {
  kind: "state";
  marking: number[];
  label: string;
  sccIndex: number;
  deadlock: boolean;
  initial: boolean;
}
export type ExplorerNode = Node<GraphNodeData, "state">;

export interface ExplorerEdgeData extends Record<string, unknown> {
  transition: string;
}
export type ExplorerEdge = Edge<ExplorerEdgeData>;

/** Arrow marker (MarkerType.ArrowClosed) — string literal keeps this module DOM-free. */
const ARROW = { type: "arrowclosed" as const, width: 18, height: 18 };

function sameMarking(a: number[], b: number[]): boolean {
  return a.length === b.length && a.every((v, i) => v === b[i]);
}

export function projectGraph(
  graph: ReachabilityGraph,
  sccs: number[][][],
  deadlocks: number[][],
  positions: Record<string, Point>,
  placeOrder: string[],
  initialMarking: number[],
): { nodes: ExplorerNode[]; edges: ExplorerEdge[] } {
  void placeOrder; // reserved for named tooltips (design §4)
  // sccIndex lookup: markingKey -> index of the component in `sccs`.
  const sccIndexOf = new Map<string, number>();
  sccs.forEach((component, index) => {
    for (const marking of component) {
      sccIndexOf.set(markingKey(marking), index);
    }
  });
  const deadlockKeys = new Set(deadlocks.map(markingKey));

  const nodes: ExplorerNode[] = graph.states.map((marking) => {
    const key = markingKey(marking);
    const initial = sameMarking(marking, initialMarking);
    return {
      id: key,
      type: "state",
      position: positions[key] ?? { x: 0, y: 0 },
      data: {
        kind: "state",
        marking,
        label: initial ? "M0" : `(${marking.join(",")})`,
        sccIndex: sccIndexOf.get(key) ?? -1,
        deadlock: deadlockKeys.has(key),
        initial,
      },
    };
  });

  const edges: ExplorerEdge[] = [];
  for (const [sourceKey, outgoing] of graph.edges) {
    for (const [transition, successor] of outgoing) {
      const targetKey = markingKey(successor);
      edges.push({
        id: `${sourceKey}::${transition}::${targetKey}`,
        source: sourceKey,
        target: targetKey,
        label: transition,
        markerEnd: ARROW,
        data: { transition },
      });
    }
  }

  return { nodes, edges };
}