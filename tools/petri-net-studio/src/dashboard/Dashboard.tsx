/**
 * Dashboard — read-only harness-net view (feature_043, operation_spec_001).
 *
 * Own React root, no zustand: a `useState` slider index over the committed
 * snapshot's revision list. Per index: marking dict → tuple → shared
 * `toFlowGraph` + shared `PlaceNode`/`TransitionNode` (editor reuse, zero
 * editor changes) + `blockedPlaces` highlight. Never writes store/doc/net.
 */

import { useMemo, useState } from "react";
import { ReactFlow, type NodeProps } from "@xyflow/react";
import { toNet } from "../state/document.js";
import { toFlowGraph, type StudioFlowNode } from "../ui/flow.js";
import { PlaceNode } from "../ui/PlaceNode.js";
import { TransitionNode } from "../ui/TransitionNode.js";
import type { NetDocument } from "../state/document.js";
import { blockedPlaces } from "./blockedPlaces.js";
import committed from "./snapshot.json";

export interface DashboardSnapshotMarking {
  revision: number;
  kind: string;
  label: string;
  marking: Record<string, number>;
}

export interface DashboardSnapshot {
  format: string;
  version: number;
  net_revision: number;
  built_at: string;
  place_order: string[];
  net: NetDocument;
  positions: Record<string, { x: number; y: number }>;
  pool: { pending: number; active: number; done: number };
  snapshots: DashboardSnapshotMarking[];
  skipped: { ts: string; kind: string; revision: number | null }[];
}

function assertSnapshot(raw: unknown): DashboardSnapshot {
  const snap = raw as DashboardSnapshot;
  if (snap?.format !== "meta-net-dashboard-snapshot" || snap?.version !== 1) {
    throw new Error(
      `Dashboard: unsupported snapshot (want meta-net-dashboard-snapshot v1, got ${
        (snap as { format?: unknown })?.format ?? "none"
      } v${(snap as { version?: unknown })?.version ?? "?"}) — regenerate via uv run scripts/omt/net_snapshot.py`,
    );
  }
  return snap;
}

function DashboardPlaceNode(props: NodeProps<StudioFlowNode>) {
  const blocked = (props.data as { blocked?: boolean }).blocked === true;
  return (
    <div
      data-testid={`place-${props.data.name}`}
      className={blocked ? "blocked" : undefined}
    >
      <PlaceNode {...props} />
    </div>
  );
}

const dashboardNodeTypes = { place: DashboardPlaceNode, transition: TransitionNode };

export function Dashboard(props: { snapshot?: DashboardSnapshot }) {
  const snapshot = useMemo(
    () => (props.snapshot ? (props.snapshot as DashboardSnapshot) : assertSnapshot(committed)),
    [props.snapshot],
  );
  const [index, setIndex] = useState(snapshot.snapshots.length - 1);
  const current = snapshot.snapshots[Math.min(index, snapshot.snapshots.length - 1)];

  const view = useMemo(() => {
    const doc = snapshot.net;
    const net = toNet(doc);
    const tuple = snapshot.place_order.map((p) => current.marking[p] ?? 0);
    const enabled = net.enabledTransitionsAt(tuple);
    const blockage = blockedPlaces(doc, tuple);
    const blockedSet = new Set(blockage.blocked);
    const graph = toFlowGraph(doc, snapshot.positions, tuple, enabled);
    const nodes = graph.nodes.map((node) =>
      node.data.kind === "place" && blockedSet.has(node.id)
        ? { ...node, data: { ...node.data, blocked: true } }
        : node,
    );
    return { tuple, enabled, blockage, nodes, edges: graph.edges };
  }, [snapshot, current]);

  return (
    <div className="app">
      <header className="toolbar">
        <span className="brand">Meta Net Dashboard</span>
        <span data-testid="revision-label">
          rev {current.revision} ({current.label})
        </span>
        <input
          data-testid="revision-slider"
          type="range"
          min={0}
          max={snapshot.snapshots.length - 1}
          value={Math.min(index, snapshot.snapshots.length - 1)}
          onChange={(e) => setIndex(Number(e.target.value))}
          aria-label="revision"
        />
        <span data-testid="pool-line">
          Pool: pending={snapshot.pool.pending} active={snapshot.pool.active} done=
          {snapshot.pool.done}
        </span>
        <span>
          snapshot rev {snapshot.net_revision}
          {view.blockage.deadlocked ? " · DEADLOCKED" : ""}
          {(snapshot.skipped ?? []).length > 0
            ? ` · ${snapshot.skipped.length} foreign record(s) skipped`
            : ""}
        </span>
      </header>
      <div className="canvas">
        <ReactFlow
          nodes={view.nodes}
          edges={view.edges}
          nodeTypes={dashboardNodeTypes}
          nodesDraggable={false}
          nodesConnectable={false}
          deleteKeyCode={null}
          fitView
          proOptions={{ hideAttribution: false }}
        />
      </div>
    </div>
  );
}
