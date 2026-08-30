/**
 * GraphExplorer — reachability-graph view (design_001 §5; feature_036).
 *
 * Derived state only (B12): `useMemo` over `toNet(doc)` + `maxStates` — the
 * SAME graph the dashboard would show (never a second explore pass). The
 * explorer is read-only over M0: nodes = reachable markings, edges =
 * transitions, elkjs auto-layout (D2/C9, positions never stored), SCC coloring,
 * deadlock highlight, truncation banner (D10), liveness legend.
 *
 * Animation (design 3.2): clicking a state runs `firingSequenceTo`; Play/Step/
 * Reset step through a preview strip via `markingAt`/`sequenceSteps` (pure
 * engine folds) — the strip NEVER touches store marking/doc (C3).
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ReactFlow } from "@xyflow/react";
import ELK from "elkjs";

import { PetriNetAnalyzer } from "../engine/analysis.js";
import { toNet } from "../state/document.js";
import { useStudioStore, type Point } from "../state/store.js";
import { markingAt, sequenceSteps } from "./animation.js";
import { projectGraph, type ExplorerNode } from "./graphProjection.js";

const PLAY_INTERVAL_MS = 700;
// TA: gotcha: Pause mid-Cycle 5 gotcha: styles.css §9 styles NOT yet appended (explorer-panel/sequence-strip/gallery-grid/etc.) — App.tsx + GraphExplorer + Gallery are written and tsc-clean + 274/274 Vitest green, but the UI will look unstyled until the CSS additive section lands; also npm run build + preview smoke still pending (Cycle 5 remainder).
// TA: why: layout is a SEPARATE memoized step: projectGraph() is called twice (once with {} positions for the layout dependency, once with elkjs positions for render) — positions never stored in the document/format (C9); ELK is deterministic for identical input but layout bytes are NOT conformance-gated (visual-only determinism).
/** Deterministic 6-hue SCC palette (design §9). */
const SCC_PALETTE = ["hsl(210, 70%, 55%)", "hsl(120, 55%, 45%)", "hsl(30, 80%, 55%)", "hsl(280, 55%, 55%)", "hsl(350, 70%, 55%)", "hsl(190, 60%, 45%)"];

/** ELK layered layout → positions keyed by markingKey (design C9). */
async function layoutGraph(
  nodes: ExplorerNode[],
  edges: { id: string; source: string; target: string }[],
): Promise<Record<string, Point>> {
  const elk = new ELK();
  const graph = await elk.layout({
    id: "root",
    children: nodes.map((n) => ({ id: n.id, width: 60, height: 44 })),
    edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  });
  const positions: Record<string, Point> = {};
  for (const child of graph.children ?? []) {
    positions[child.id] = { x: child.x ?? 0, y: child.y ?? 0 };
  }
  return positions;
}

function StatusBadge(props: { value: boolean | null; complete: boolean }) {
  const unknown = !props.complete || props.value === null;
  const glyph = unknown ? "❓" : props.value ? "✅" : "❌";
  const cls = unknown ? "status-unknown" : props.value ? "status-ok" : "status-no";
  return <span className={`status-badge ${cls}`} aria-label={glyph}>{glyph}</span>;
}

export function GraphExplorer() {
  const doc = useStudioStore((s) => s.doc);
  const maxStates = useStudioStore((s) => s.maxStates);

  const analysis = useMemo(() => {
    const net = toNet(doc);
    const analyzer = new PetriNetAnalyzer(net);
    const graph = analyzer.reachabilityGraph(maxStates);
    return {
      net,
      analyzer,
      graph,
      reach: analyzer.reachableMarkings(maxStates),
      deadlocks: analyzer.deadlocks(maxStates).deadlocks,
      sccs: analyzer.stronglyConnectedComponents(graph),
      transitions: net.transitionOrder.map((t) => ({
        name: t,
        result: analyzer.transitionLiveness(t, graph),
      })),
    };
  }, [doc, maxStates]);

  const m0 = analysis.net.initialMarkingTuple();

  // Projection (pure, positions injected later) — memoized on graph identity.
  const projected = useMemo(
    () => projectGraph(analysis.graph, analysis.sccs, analysis.deadlocks, {}, analysis.net.placeOrder, m0),
    [analysis.graph, analysis.sccs, analysis.deadlocks, analysis.net.placeOrder, m0],
  );

  // Layout — separate pure-ish step (elkjs), memoized on the projection.
  const [positions, setPositions] = useState<Record<string, Point>>({});
  useEffect(() => {
    let cancelled = false;
    void layoutGraph(projected.nodes, projected.edges).then((pos) => {
      if (!cancelled) setPositions(pos);
    });
    return () => {
      cancelled = true;
    };
  }, [projected]);

  const { nodes, edges } = useMemo(
    () => projectGraph(analysis.graph, analysis.sccs, analysis.deadlocks, positions, analysis.net.placeOrder, m0),
    [analysis.graph, analysis.sccs, analysis.deadlocks, positions, analysis.net.placeOrder, m0],
  );

  // ------------------------------------------------------------------
  // Animation strip (C3: component-local, never touches the store)
  // ------------------------------------------------------------------
  const [selected, setSelected] = useState<number[] | null>(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef<number | null>(null);

  const sequence = useMemo(() => {
    if (selected === null) return null;
    return analysis.analyzer.firingSequenceTo(analysis.reach, selected);
  }, [analysis.analyzer, analysis.reach, selected]);

  const stopTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setPlaying(false);
  }, []);

  useEffect(() => stopTimer, [stopTimer]);

  const play = useCallback(() => {
    if (sequence === null || sequence.length === 0) return;
    stopTimer();
    setPlaying(true);
    timerRef.current = window.setInterval(() => {
      setStep((s) => {
        const next = Math.min(s + 1, sequence.length);
        if (next >= sequence.length) stopTimer();
        return next;
      });
    }, PLAY_INTERVAL_MS);
  }, [sequence, stopTimer]);

  useEffect(() => {
    if (step >= (sequence?.length ?? 0) && sequence !== null && sequence.length > 0) {
      stopTimer();
    }
  }, [step, sequence, stopTimer]);

  const steps = useMemo(
    () => (sequence === null ? null : sequenceSteps(analysis.net, m0, sequence)),
    [analysis.net, m0, sequence],
  );

  const onNodeClick = useCallback((_: unknown, node: ExplorerNode) => {
    setSelected(node.data.marking);
    setStep(0);
    stopTimer();
  }, [stopTimer]);

  const placeOrder = analysis.net.placeOrder;

  return (
    <section className="explorer-panel">
      <h2>
        Reachability graph <span className="analysis-sub">from initial marking M0</span>
      </h2>

      {!analysis.graph.complete && (
        <p className="truncation-banner">
          State-space exploration was truncated — graph shows explored states only;
          liveness/SCC verdicts are unknown.
        </p>
      )}

      <div className="explorer-legend">
        <span className="explorer-legend-label">SCC:</span>
        {analysis.sccs.map((comp, i) => (
          <span key={i} className="scc-chip" style={{ background: SCC_PALETTE[i % SCC_PALETTE.length] }}>
            {comp.length}
          </span>
        ))}
        <span className="explorer-legend-label">liveness:</span>
        {analysis.transitions.map(({ name, result }) => (
          <span key={name} className="explorer-liveness">
            <StatusBadge value={result.value} complete={result.complete} /> {name}
          </span>
        ))}
      </div>

      <div className="explorer-canvas">
        <ReactFlow
          nodes={nodes.map((n) => ({
            ...n,
            style: {
              background: SCC_PALETTE[n.data.sccIndex % SCC_PALETTE.length],
              border: n.data.deadlock
                ? "2px solid var(--danger)"
                : n.data.initial
                  ? "2px solid var(--text)"
                  : "1px solid var(--border)",
              borderRadius: "50%",
              width: 44,
              height: 44,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            },
            label: n.data.label,
          }))}
          edges={edges}
          onNodeClick={onNodeClick}
          nodesDraggable={false}
          nodesConnectable={false}
          deleteKeyCode={null}
          fitView
          proOptions={{ hideAttribution: false }}
        />
      </div>

      {sequence === null ? (
        <p className="analysis-count">
          {selected === null
            ? "Click a state to show a firing sequence to it."
            : "Target unreachable from M0 in the explored graph."}
        </p>
      ) : (
        <div className="sequence-strip">
          <button onClick={() => { setStep(0); stopTimer(); }}>Reset</button>
          <button onClick={playing ? stopTimer : play}>{playing ? "Pause" : "Play"}</button>
          <button onClick={() => { setStep((s) => Math.min(s + 1, sequence.length)); stopTimer(); }}>
            Step
          </button>
          {steps!.map((marking, i) => (
            <span key={i} className={`sequence-cell${i === step ? " active" : ""}`}>
              {i === 0 ? "M0" : `(${marking.join(",")})`}
            </span>
          ))}
          <span className="sequence-step-label">
            step {step}/{sequence.length} · target ({selected!.join(",")})
          </span>
          <span className="sequence-marking">
            marking at step: ({markingAt(analysis.net, m0, sequence, step).join(",")})
          </span>
        </div>
      )}

      <p className="analysis-count">
        {analysis.graph.states.length} state(s) · {edges.length} edge(s) ·{" "}
        {analysis.graph.complete ? "complete" : "truncated"} ·{" "}
        {placeOrder.map((p) => p).join(", ")} places
      </p>
      <p className="explorer-tip">Edges labeled with transition names; deadlock states have a red ring.</p>
    </section>
  );
}