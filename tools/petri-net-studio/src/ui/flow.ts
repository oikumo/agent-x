/**
 * Pure projection: NetDocument + marking + positions → React Flow graph (design §7).
 *
 * Places become circular nodes showing the LIVE token count (edit mode: M0;
 * simulate mode: current marking). Transitions carry an `enabled` flag (simulate
 * only) the node styles on. Arcs become edges with an arrow marker and the
 * weight as an always-visible label (FORMAT explicit-always rule). Edge ids are
 * `arcId(source, target)` (injective JSON encoding) so removals decode back.
 */

import { MarkerType, type Edge, type Node } from "@xyflow/react";
import { arcId, toNet, type NetDocument } from "../state/document.js";
import type { Point } from "../state/store.js";

export interface FlowNodeData extends Record<string, unknown> {
  kind: "place" | "transition";
  name: string;
  tokens: number;
  enabled: boolean;
  simulate: boolean;
}

export type StudioFlowNode = Node<FlowNodeData, "place" | "transition">;

export interface FlowGraph {
  nodes: StudioFlowNode[];
  edges: Edge[];
}

export function toFlowGraph(
  doc: NetDocument,
  positions: Record<string, Point>,
  marking: number[] | null,
  enabled: string[],
): FlowGraph {
  const simulate = marking !== null;
  const enabledSet = new Set(enabled);
  const placeIndex = toNet(doc).placeIndex;

  const nodes: StudioFlowNode[] = [];
  for (const p of doc.places) {
    nodes.push({
      id: p.name,
      type: "place",
      position: positions[p.name] ?? { x: 0, y: 0 },
      data: {
        kind: "place",
        name: p.name,
        tokens: simulate ? marking[placeIndex.get(p.name)!] : p.tokens,
        enabled: false,
        simulate,
      },
    });
  }
  for (const t of doc.transitions) {
    nodes.push({
      id: t.name,
      type: "transition",
      position: positions[t.name] ?? { x: 0, y: 0 },
      data: {
        kind: "transition",
        name: t.name,
        tokens: 0,
        enabled: simulate && enabledSet.has(t.name),
        simulate,
      },
    });
  }

  const edges: Edge[] = doc.arcs.map((a) => ({
    id: arcId(a.source, a.target),
    source: a.source,
    target: a.target,
    label: String(a.weight),
    markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
  }));

  return { nodes, edges };
}
