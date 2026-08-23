/**
 * NetDocument — the editor's editable, format-shaped document model (design A8).
 *
 * The document mirrors the petri-net-json v1 pinned surface exactly
 * (places/transitions/arcs with explicit tokens/weight); the engine `PetriNet`
 * is DERIVED from it via a memoized `toNet` (buildNet — FORMAT.md §7). All ops
 * are pure: they never mutate `doc`, and return a fresh document on success.
 * Fallible ops return `{ doc, ok, reason? }`; on rejection `doc` is the INPUT
 * document (identity unchanged), so callers can bail without re-render.
 *
 * Ops keep the document always-valid by construction (V1–V4 enforced on
 * mutation): auto-naming is first-free across places ∪ transitions (V1-safe),
 * rename is collision-checked (V1), arc creation rejects unknown endpoints
 * (V2), same-kind connections (V3) and duplicates (V4). Rejection reasons
 * carry the rule id, mirroring the io.ts message convention.
 */

import { PetriNet } from "../engine/model.js";
import { buildNet } from "../engine/io.js";

export interface PlaceItem {
  name: string;
  tokens: number;
}
export interface TransitionItem {
  name: string;
}
export interface ArcItem {
  source: string;
  target: string;
  weight: number;
}

/** Editable petri-net-json v1 document (M0 tokens; no layout — positions live in the store). */
export interface NetDocument {
  places: PlaceItem[];
  transitions: TransitionItem[];
  arcs: ArcItem[];
}

/** Result of a fallible op: `ok` false ⇒ `doc` is the unchanged input document. */
export interface OpResult {
  doc: NetDocument;
  ok: boolean;
  reason?: string;
}

/** Injective arc identifier (no separator collisions) for selection/state keys. */
export function arcId(source: string, target: string): string {
  return JSON.stringify([source, target]);
}

export function emptyDocument(): NetDocument {
  return { places: [], transitions: [], arcs: [] };
}

/** All node names (places ∪ transitions) in document order. */
export function nodeNames(doc: NetDocument): string[] {
  return [...doc.places.map((p) => p.name), ...doc.transitions.map((t) => t.name)];
}

function nameSet(doc: NetDocument): Set<string> {
  return new Set(nodeNames(doc));
}

/** First `p<n>`/`t<n>` (n ≥ 1) not used by ANY node — V1-safe across places ∪ transitions. */
function firstFreeName(doc: NetDocument, prefix: "p" | "t"): string {
  const used = nameSet(doc);
  let n = 1;
  while (used.has(`${prefix}${n}`)) n++;
  return `${prefix}${n}`;
}

/** Add a place auto-named `p<n>` (first free index across P ∪ T, V1-safe). */
export function addPlace(doc: NetDocument): NetDocument {
  return { ...doc, places: [...doc.places, { name: firstFreeName(doc, "p"), tokens: 0 }] };
}

/** Add a transition auto-named `t<n>` (first free index across P ∪ T, V1-safe). */
export function addTransition(doc: NetDocument): NetDocument {
  return { ...doc, transitions: [...doc.transitions, { name: firstFreeName(doc, "t") }] };
}

/** Remove a place or transition and cascade-delete its incident arcs. Unknown name ⇒ unchanged. */
export function removeNode(doc: NetDocument, name: string): NetDocument {
  if (!nameSet(doc).has(name)) return doc;
  return {
    places: doc.places.filter((p) => p.name !== name),
    transitions: doc.transitions.filter((t) => t.name !== name),
    arcs: doc.arcs.filter((a) => a.source !== name && a.target !== name),
  };
}

/** Add an arc of weight 1. Rejects unknown endpoints (V2), same-kind links (V3), duplicates (V4). */
export function addArc(doc: NetDocument, source: string, target: string): OpResult {
// TA: why: why: addArc is NOT in operation_spec_001's op table (design omission) — §7 pins the connect-drag gesture, so the op was added to keep ALL doc mutation in pure ops (document-model-first A8); recorded in pause_2026-08-23c/test report.
  const names = nameSet(doc);
  if (!names.has(source) || !names.has(target)) {
    return {
      doc,
      ok: false,
      reason: `V2: arc endpoint(s) do not name an existing node: '${source}' -> '${target}'`,
    };
  }
  const placeNames = new Set(doc.places.map((p) => p.name));
  const sourceIsPlace = placeNames.has(source);
  const targetIsPlace = placeNames.has(target);
  if (sourceIsPlace === targetIsPlace) {
    return {
      doc,
      ok: false,
      reason: `V3: arcs must connect a place and a transition: '${source}' -> '${target}'`,
    };
  }
  if (doc.arcs.some((a) => a.source === source && a.target === target)) {
    return {
      doc,
      ok: false,
      reason: `V4: duplicate arc (source, target): '${source}' -> '${target}'`,
    };
  }
  return { doc: { ...doc, arcs: [...doc.arcs, { source, target, weight: 1 }] }, ok: true };
}

/** Remove the arc (source, target). */
export function removeArc(doc: NetDocument, source: string, target: string): OpResult {
  if (!doc.arcs.some((a) => a.source === source && a.target === target)) {
    return { doc, ok: false, reason: `no such arc: '${source}' -> '${target}'` };
  }
  return {
    doc: { ...doc, arcs: doc.arcs.filter((a) => !(a.source === source && a.target === target)) },
    ok: true,
  };
}

/** Rename a node and rewire arcs. Rejects empty/colliding names (V1 across P ∪ T). */
export function renameNode(doc: NetDocument, oldName: string, nextName: string): OpResult {
  const names = nameSet(doc);
  if (!names.has(oldName)) {
    return { doc, ok: false, reason: `unknown node: '${oldName}'` };
  }
  if (nextName.length === 0) {
    return { doc, ok: false, reason: "name must be a non-empty string" };
  }
  if (nextName === oldName) {
    return { doc, ok: true };
  }
  if (names.has(nextName)) {
    return {
      doc,
      ok: false,
      reason: `V1: names must be unique across places ∪ transitions: '${nextName}' is taken`,
    };
  }
  return {
    doc: {
      places: doc.places.map((p) => (p.name === oldName ? { ...p, name: nextName } : p)),
      transitions: doc.transitions.map((t) => (t.name === oldName ? { ...t, name: nextName } : t)),
      arcs: doc.arcs.map((a) => ({
        ...a,
        source: a.source === oldName ? nextName : a.source,
        target: a.target === oldName ? nextName : a.target,
      })),
    },
    ok: true,
  };
}

/** Set a place's M0 token count (integer ≥ 0). */
export function setTokens(doc: NetDocument, place: string, n: number): OpResult {
  if (!doc.places.some((p) => p.name === place)) {
    return { doc, ok: false, reason: `unknown place: '${place}'` };
  }
  if (typeof n !== "number" || !Number.isInteger(n) || n < 0) {
    return { doc, ok: false, reason: `token count must be a non-negative integer, got ${n}` };
  }
  return {
    doc: {
      ...doc,
      places: doc.places.map((p) => (p.name === place ? { ...p, tokens: n } : p)),
    },
    ok: true,
  };
}

/** Set an arc's weight (integer ≥ 1). */
export function setWeight(doc: NetDocument, source: string, target: string, n: number): OpResult {
  if (!doc.arcs.some((a) => a.source === source && a.target === target)) {
    return { doc, ok: false, reason: `no such arc: '${source}' -> '${target}'` };
  }
  if (typeof n !== "number" || !Number.isInteger(n) || n < 1) {
    return { doc, ok: false, reason: `arc weight must be a positive integer, got ${n}` };
  }
  return {
    doc: {
      ...doc,
      arcs: doc.arcs.map((a) =>
        a.source === source && a.target === target ? { ...a, weight: n } : a,
      ),
    },
    ok: true,
  };
}

const netCache = new WeakMap<NetDocument, PetriNet>();

/** Derive the engine net (memoized by document identity — pure docs make this safe, A8). */
export function toNet(doc: NetDocument): PetriNet {
  let net = netCache.get(doc);
  if (net === undefined) {
    net = buildNet(doc.places, doc.transitions, doc.arcs);
    netCache.set(doc, net);
  }
  return net;
}
