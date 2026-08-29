/**
 * App — toolbar + React Flow canvas + inspector (design §7 walking skeleton).
 *
 * Toolbar: mode toggle (edit|simulate), palette (+ Place / + Transition — arms
 * placement, the next canvas click drops the node), Examples menu, Import /
 * Export dialogs, Reset (simulate only). Edit gestures: drag moves (integer
 * snapped by the store), connect-drag creates a weight-1 arc (V2–V4 rejections
 * flash a transient hint), Delete/Backspace removes the selected element, click
 * selects into the Inspector. Simulate gestures: click an enabled transition to
 * fire it; everything structural is locked (store-enforced, A9).
 */

import { useCallback, useMemo, useState, type MouseEvent } from "react";
import {
  ReactFlow,
  useReactFlow,
  type Connection,
  type EdgeChange,
  type NodeChange,
} from "@xyflow/react";
import { EXAMPLE_NAMES } from "../examples.js";
import { enabledTransitions, useStudioStore } from "../state/store.js";
import { toFlowGraph, type StudioFlowNode } from "./flow.js";
import { PlaceNode } from "./PlaceNode.js";
import { TransitionNode } from "./TransitionNode.js";
import { Inspector } from "./Inspector.js";
import { AnalysisPanel } from "./AnalysisPanel.js";

const nodeTypes = { place: PlaceNode, transition: TransitionNode };

const HINT_TTL_MS = 2500;

function ImportDialog(props: { onClose: () => void }) {
  const importJson = useStudioStore((s) => s.importJson);
  const importError = useStudioStore((s) => s.importError);
  const [text, setText] = useState("");
  return (
    <div className="dialog-backdrop" onClick={props.onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>Import petri-net-json</h2>
        <textarea
          rows={12}
          value={text}
          placeholder='{"format": "petri-net-json", "version": 1, ...}'
          onChange={(e) => setText(e.target.value)}
        />
        <div className="dialog-row">
          <input
            type="file"
            accept=".json,application/json"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void file.text().then(setText);
            }}
          />
        </div>
        {importError && <p className="error-banner">{importError}</p>}
        <div className="dialog-row">
          <button
            className="primary"
            onClick={() => {
              if (importJson(text)) props.onClose();
            }}
          >
            Import
          </button>
          <button onClick={props.onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

function ExportDialog(props: { text: string; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const download = () => {
    const blob = new Blob([props.text], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "net.json";
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="dialog-backdrop" onClick={props.onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>Export petri-net-json (canonical)</h2>
        <textarea rows={12} readOnly value={props.text} />
        <div className="dialog-row">
          <button
            className="primary"
            onClick={() => {
              void navigator.clipboard.writeText(props.text).then(() => setCopied(true));
            }}
          >
            {copied ? "Copied" : "Copy"}
          </button>
          <button onClick={download}>Download net.json</button>
          <button onClick={props.onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export function App() {
  const doc = useStudioStore((s) => s.doc);
  const positions = useStudioStore((s) => s.positions);
  const mode = useStudioStore((s) => s.mode);
  const marking = useStudioStore((s) => s.marking);
  const importError = useStudioStore((s) => s.importError);
  const setMode = useStudioStore((s) => s.setMode);
  const resetMarking = useStudioStore((s) => s.resetMarking);
  const fireTransition = useStudioStore((s) => s.fireTransition);
  const addPlaceAt = useStudioStore((s) => s.addPlaceAt);
  const addTransitionAt = useStudioStore((s) => s.addTransitionAt);
  const moveNode = useStudioStore((s) => s.moveNode);
  const removeNode = useStudioStore((s) => s.removeNode);
  const addArc = useStudioStore((s) => s.addArc);
  const removeArc = useStudioStore((s) => s.removeArc);
  const setSelection = useStudioStore((s) => s.setSelection);
  const loadExample = useStudioStore((s) => s.loadExample);
  const exportJson = useStudioStore((s) => s.exportJson);
  const analysisVisible = useStudioStore((s) => s.analysisVisible);
  const toggleAnalysis = useStudioStore((s) => s.toggleAnalysis);

  const [adding, setAdding] = useState<"place" | "transition" | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [exportText, setExportText] = useState<string | null>(null);
  const { screenToFlowPosition } = useReactFlow();

  const flashHint = (message: string) => {
    setHint(message);
    window.setTimeout(() => setHint(null), HINT_TTL_MS);
  };

  const enabled = useMemo(() => enabledTransitions(doc, marking), [doc, marking]);
  const graph = useMemo(
    () => toFlowGraph(doc, positions, marking, enabled),
    [doc, positions, marking, enabled],
  );

  const onNodesChange = useCallback(
    (changes: NodeChange<StudioFlowNode>[]) => {
      for (const ch of changes) {
        if (ch.type === "position" && ch.position) moveNode(ch.id, ch.position);
        else if (ch.type === "remove") removeNode(ch.id);
      }
    },
    [moveNode, removeNode],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      for (const ch of changes) {
        if (ch.type === "remove") {
          const [source, target] = JSON.parse(ch.id) as [string, string];
          removeArc(source, target);
        }
      }
    },
    [removeArc],
  );

  const onConnect = useCallback(
    (conn: Connection) => {
      if (!conn.source || !conn.target) return;
      if (!addArc(conn.source, conn.target)) {
        flashHint("Arc rejected: connect a place ↔ a transition, no duplicates (V2–V4)");
      }
    },
    [addArc],
  );

  const onNodeClick = useCallback(
    (_: MouseEvent, node: StudioFlowNode) => {
      if (mode === "simulate") {
        if (node.data.kind === "transition") fireTransition(node.id);
      } else {
        setSelection({ kind: node.data.kind, id: node.id });
      }
    },
    [mode, fireTransition, setSelection],
  );

  const onEdgeClick = useCallback(
    (_: MouseEvent, edge: { id: string }) => {
      if (mode === "edit") setSelection({ kind: "arc", id: edge.id });
    },
    [mode, setSelection],
  );

  const onPaneClick = useCallback(
    (e: MouseEvent) => {
      if (adding !== null) {
        const pos = screenToFlowPosition({ x: e.clientX, y: e.clientY });
        if (adding === "place") addPlaceAt(pos);
        else addTransitionAt(pos);
        setAdding(null);
      } else {
        setSelection(null);
      }
    },
    [adding, screenToFlowPosition, addPlaceAt, addTransitionAt, setSelection],
  );

  const editing = mode === "edit";

  return (
    <div className="app">
      <header className="toolbar">
        <span className="brand">Petri Net Studio</span>
        <div className="mode-toggle" role="group" aria-label="mode">
          <button className={editing ? "active" : ""} onClick={() => setMode("edit")}>
            Edit
          </button>
          <button className={!editing ? "active" : ""} onClick={() => setMode("simulate")}>
            Simulate
          </button>
        </div>
        <button
          disabled={!editing}
          className={adding === "place" ? "armed" : ""}
          onClick={() => setAdding(adding === "place" ? null : "place")}
        >
          + Place
        </button>
        <button
          disabled={!editing}
          className={adding === "transition" ? "armed" : ""}
          onClick={() => setAdding(adding === "transition" ? null : "transition")}
        >
          + Transition
        </button>
        <select
          value=""
          disabled={!editing}
          onChange={(e) => {
            if (e.target.value) loadExample(e.target.value);
          }}
        >
          <option value="">Examples…</option>
          {EXAMPLE_NAMES.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        <button disabled={!editing} onClick={() => setImportOpen(true)}>
          Import
        </button>
        <button onClick={() => setExportText(exportJson())}>Export</button>
        <button
          className={analysisVisible ? "active" : ""}
          onClick={toggleAnalysis}
          title="Analyze the net from its initial marking M0"
        >
          Analyze
        </button>
        <button disabled={editing} onClick={resetMarking}>
          Reset marking
        </button>
      </header>
      {importError && !importOpen && <p className="error-banner">{importError}</p>}
      {hint && <p className="hint-banner">{hint}</p>}
      {adding && <p className="hint-banner">Click on the canvas to place the {adding} (button again to cancel)</p>}
      <div className="canvas">
        <ReactFlow
          nodes={graph.nodes}
          edges={graph.edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          nodesDraggable={editing}
          nodesConnectable={editing}
          deleteKeyCode={editing ? ["Backspace", "Delete"] : null}
          fitView
          proOptions={{ hideAttribution: false }}
        />
        <Inspector />
      </div>
      {analysisVisible && <AnalysisPanel />}
      {importOpen && <ImportDialog onClose={() => setImportOpen(false)} />}
      {exportText !== null && <ExportDialog text={exportText} onClose={() => setExportText(null)} />}
    </div>
  );
}
// TA: why: why: React Flow is controlled THROUGH the store — position/remove changes route back into store actions (integer snap on write, design §7) and nodes re-derive via useMemo; no local flow state to drift out of sync.
