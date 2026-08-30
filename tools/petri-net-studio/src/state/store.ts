/**
 * Zustand store for the Studio v1 editor (design §7, operation_spec §state).
 *
 * State: the editable `NetDocument` (M0 always), canvas `positions` (integers,
 * snapped on write), `mode` edit|simulate (A9), the live `marking` tuple over
 * `placeOrder` (simulate only), the current `selection`, and the last
 * `importError` string.
 *
 * Simulate mode locks ALL structure edits (A9: "structure locked") — the
 * doc/positions-mutating actions no-op unless `mode === "edit"`; only
 * setMode / resetMarking / fireTransition / setSelection stay live. Firing is
 * engine-pure: `marking := fireMarking(marking, t)` via the memoized net;
 * disabled or out-of-mode clicks are no-ops (UI guards by the enabled set).
 *
 * Import replaces doc+positions (layout.nodes → positions; nodes without a
 * layout position get a deterministic circle auto-layout, radius
 * AUTO_LAYOUT_RADIUS) and lands in edit mode; failure leaves ALL state
 * unchanged and records `importError = "<ErrorClass>: <message>"` (captured,
 * never thrown). Export is `netToJson(toNet(doc), {nodes})` — canonical bytes.
 */

import { create } from "zustand";
import { PetriNet, compareCodePoints } from "../engine/model.js";
import { JsonObject, JsonValue, documentFromJson, netToJson } from "../engine/io.js";
import { EXAMPLE_TEXTS } from "../examples.js";
import {
  NetDocument,
  addArc as docAddArc,
  addPlace as docAddPlace,
  addTransition as docAddTransition,
  emptyDocument,
  nodeNames,
  removeArc as docRemoveArc,
  removeNode as docRemoveNode,
  renameNode as docRenameNode,
  setTokens as docSetTokens,
  setWeight as docSetWeight,
  toNet,
} from "./document.js";

export type Mode = "edit" | "simulate";

export interface Point {
  x: number;
  y: number;
}

export type Selection =
  | { kind: "place" | "transition"; id: string }
  | { kind: "arc"; id: string }; // id = arcId(source, target)

/** Radius of the deterministic circle auto-layout for imports without positions (design §7). */
export const AUTO_LAYOUT_RADIUS = 120;

/** Data-only slice of the store (actions excluded) — also the test reset point. */
export interface StudioData {
  doc: NetDocument;
  positions: Record<string, Point>;
  mode: Mode;
  marking: number[] | null;
  selection: Selection | null;
  importError: string | null;
  /** Analysis UI state (B10/B12): max-states dial; default 1000, visible, never hidden. */
  maxStates: number | null;
  /** Analysis panel visibility; default hidden. */
  analysisVisible: boolean;
  /** Graph explorer visibility; default hidden (design_001 §6 — feature_036). */
  graphVisible: boolean;
}

export interface StudioState extends StudioData {
  addPlaceAt(pos: Point): void;
  addTransitionAt(pos: Point): void;
  removeNode(name: string): void;
  addArc(source: string, target: string): boolean;
  removeArc(source: string, target: string): boolean;
  renameNode(oldName: string, nextName: string): boolean;
  setTokens(place: string, n: number): boolean;
  setWeight(source: string, target: string, n: number): boolean;
  moveNode(name: string, pos: Point): void;
  setSelection(sel: Selection | null): void;
  setMode(mode: Mode): void;
  fireTransition(transition: string): void;
  resetMarking(): void;
  importJson(text: string): boolean;
  exportJson(): string;
  loadExample(name: string): boolean;
  setMaxStates(n: number | null): void;
  toggleAnalysis(): void;
  toggleGraph(): void;
}

export function initialDataState(): StudioData {
  return {
    doc: emptyDocument(),
    positions: {},
    mode: "edit",
    marking: null,
    selection: null,
    importError: null,
    maxStates: 1000,
    analysisVisible: false,
    graphVisible: false,
  };
}

/** Enabled transitions for the current doc+marking (empty outside simulate). */
export function enabledTransitions(doc: NetDocument, marking: number[] | null): string[] {
  if (marking === null) return [];
  return toNet(doc).enabledTransitionsAt(marking);
}

/** Build an editable document from an engine net (canonical ordering, mirrors netToJson). */
export function docFromNet(net: PetriNet): NetDocument {
  const places = net.placeOrder.map((name) => ({
    name,
    tokens: net.initialMarking.get(name)!,
  }));
  const transitions = net.transitionOrder.map((name) => ({ name }));
  const arcs: { source: string; target: string; weight: number }[] = [];
  for (const t of net.transitionOrder) {
    for (const [p, w] of net.inputs.get(t)!) arcs.push({ source: p, target: t, weight: w });
    for (const [p, w] of net.outputs.get(t)!) arcs.push({ source: t, target: p, weight: w });
  }
  arcs.sort(
    (a, b) => compareCodePoints(a.source, b.source) || compareCodePoints(a.target, b.target),
  );
  return { places, transitions, arcs };
}

/** Deterministic circle auto-layout (radius AUTO_LAYOUT_RADIUS) for the given node order. */
function circlePositions(names: string[]): Record<string, Point> {
  const out: Record<string, Point> = {};
  const n = names.length;
  names.forEach((name, i) => {
    const angle = (2 * Math.PI * i) / Math.max(n, 1);
    out[name] = {
      x: Math.round(AUTO_LAYOUT_RADIUS * Math.cos(angle)),
      y: Math.round(AUTO_LAYOUT_RADIUS * Math.sin(angle)),
    };
  });
  return out;
}

/** Positions from layout.nodes where present (V6: unknown names ignored), circle otherwise. */
function positionsFromLayout(layout: JsonValue | null, names: string[]): Record<string, Point> {
  const positions = circlePositions(names);
  const known = new Set(names);
  if (typeof layout === "object" && layout !== null && !Array.isArray(layout)) {
    const nodes = layout["nodes"];
    if (typeof nodes === "object" && nodes !== null && !Array.isArray(nodes)) {
      for (const [name, pos] of Object.entries(nodes)) {
        if (!known.has(name)) continue;
        if (typeof pos === "object" && pos !== null && !Array.isArray(pos)) {
          const { x, y } = pos as JsonObject;
          if (typeof x === "number" && typeof y === "number") {
            positions[name] = { x, y };
          }
        }
      }
    }
  }
  return positions;
}

/** Integer snap — positions are always integers in the store (design §7 drag rule). */
function snap(pos: Point): Point {
  return { x: Math.round(pos.x), y: Math.round(pos.y) };
}

export const useStudioStore = create<StudioState>()((set, get) => {
// TA: why: why: simulate-lock is STORE-level (A9 "structure locked") — every mutating action guards mode!=="edit", so UI slips can't corrupt; tests reset via setState(initialDataState()) partial-merge — replace=true would wipe the actions.
  /** Simulate mode locks all structure edits (A9) — single guard for mutating actions. */
  const editLocked = (): boolean => get().mode !== "edit";

  return {
    ...initialDataState(),

    addPlaceAt(pos: Point): void {
      if (editLocked()) return;
      const doc = docAddPlace(get().doc);
      const name = doc.places[doc.places.length - 1].name;
      set({ doc, positions: { ...get().positions, [name]: snap(pos) } });
    },

    addTransitionAt(pos: Point): void {
      if (editLocked()) return;
      const doc = docAddTransition(get().doc);
      const name = doc.transitions[doc.transitions.length - 1].name;
      set({ doc, positions: { ...get().positions, [name]: snap(pos) } });
    },

    removeNode(name: string): void {
      if (editLocked()) return;
      const positions = { ...get().positions };
      delete positions[name];
      set({ doc: docRemoveNode(get().doc, name), positions, selection: null });
    },

    addArc(source: string, target: string): boolean {
      if (editLocked()) return false;
      const res = docAddArc(get().doc, source, target);
      if (res.ok) set({ doc: res.doc });
      return res.ok;
    },

    removeArc(source: string, target: string): boolean {
      if (editLocked()) return false;
      const res = docRemoveArc(get().doc, source, target);
      if (res.ok) set({ doc: res.doc, selection: null });
      return res.ok;
    },

    renameNode(oldName: string, nextName: string): boolean {
      if (editLocked()) return false;
      const res = docRenameNode(get().doc, oldName, nextName);
      if (res.ok) {
        const positions = { ...get().positions };
        if (oldName !== nextName && positions[oldName] !== undefined) {
          positions[nextName] = positions[oldName];
          delete positions[oldName];
        }
        set({ doc: res.doc, positions });
      }
      return res.ok;
    },

    setTokens(place: string, n: number): boolean {
      if (editLocked()) return false;
      const res = docSetTokens(get().doc, place, n);
      if (res.ok) set({ doc: res.doc });
      return res.ok;
    },

    setWeight(source: string, target: string, n: number): boolean {
      if (editLocked()) return false;
      const res = docSetWeight(get().doc, source, target, n);
      if (res.ok) set({ doc: res.doc });
      return res.ok;
    },

    moveNode(name: string, pos: Point): void {
      if (editLocked()) return;
      if (get().positions[name] === undefined) return;
      set({ positions: { ...get().positions, [name]: snap(pos) } });
    },

    setSelection(sel: Selection | null): void {
      set({ selection: sel });
    },

    setMode(mode: Mode): void {
      if (mode === get().mode) return;
      if (mode === "simulate") {
        // A9: entering simulate snapshots M0 as the live marking.
        set({ mode, marking: toNet(get().doc).initialMarkingTuple(), selection: null });
      } else {
        set({ mode, marking: null, selection: null });
      }
    },

    fireTransition(transition: string): void {
      const { mode, marking, doc } = get();
      if (mode !== "simulate" || marking === null) return;
      const net = toNet(doc);
      if (!net.isEnabledAt(marking, transition)) return; // disabled click = no-op
      set({ marking: net.fireMarking(marking, transition) });
    },

    resetMarking(): void {
      if (get().mode !== "simulate") return;
      set({ marking: toNet(get().doc).initialMarkingTuple() });
    },

    importJson(text: string): boolean {
      try {
        const { net, layout } = documentFromJson(text);
        const doc = docFromNet(net);
        const positions = positionsFromLayout(layout, nodeNames(doc));
        set({ doc, positions, mode: "edit", marking: null, selection: null, importError: null });
        return true;
      } catch (e) {
        const err = e as Error;
        set({ importError: `${err.name}: ${err.message}` });
        return false;
      }
    },

    exportJson(): string {
      const { doc, positions } = get();
      const nodes: JsonObject = {};
      for (const name of nodeNames(doc)) {
        const p = snap(positions[name] ?? { x: 0, y: 0 });
        nodes[name] = { x: p.x, y: p.y }; // fresh literal: Point lacks an index signature (JsonObject)
      }
      return netToJson(toNet(doc), { nodes });
    },

    loadExample(name: string): boolean {
      const text = EXAMPLE_TEXTS[name];
      if (text === undefined) {
        set({ importError: `Error: unknown example '${name}'` });
        return false;
      }
      return get().importJson(text);
    },

    // ------------------------------------------------------------------
    // Analysis UI state (B12: UI-only; NOT edit-locked — view over M0 in
    // both modes; never written into the document/format).
    // ------------------------------------------------------------------

    setMaxStates(n: number | null): void {
      set({ maxStates: n });
    },

    toggleAnalysis(): void {
      set({ analysisVisible: !get().analysisVisible });
    },

    toggleGraph(): void {
      set({ graphVisible: !get().graphVisible });
    },
  };
});
