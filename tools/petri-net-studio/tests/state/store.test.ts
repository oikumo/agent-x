/**
 * Store smoke tests — design_001 §9.3 (manual red→green cycle 3, A11).
 *
 * Covers: document ops validity (auto-naming, rename collision → rejected,
 * cascade delete), mode transitions (simulate snapshots M0; edit discards),
 * fire updates marking + enabled set, reset, import-error integrity, and
 * export→import round-trip equality of the doc.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  NetDocument,
  addArc,
  addPlace,
  addTransition,
  emptyDocument,
  removeArc,
  removeNode,
  renameNode,
  setTokens,
  setWeight,
  toNet,
} from "../../src/state/document.js";
import {
  AUTO_LAYOUT_RADIUS,
  docFromNet,
  enabledTransitions,
  initialDataState,
  useStudioStore,
} from "../../src/state/store.js";
import { EXAMPLE_NAMES, EXAMPLE_TEXTS } from "../../src/examples.js";

const S = () => useStudioStore.getState();

/** p1(1) → t1 → p2(0), all weights 1 (pure-document hello net). */
function twoNodeDoc(): NetDocument {
  let doc = emptyDocument();
  doc = addPlace(doc); // p1
  doc = addPlace(doc); // p2
  doc = addTransition(doc); // t1
  doc = setTokens(doc, "p1", 1).doc;
  doc = addArc(doc, "p1", "t1").doc;
  doc = addArc(doc, "t1", "p2").doc;
  return doc;
}

/** Same net built through store actions, with integer positions. */
function buildHelloInStore(): void {
  S().addPlaceAt({ x: 0, y: 0 }); // p1
  S().addPlaceAt({ x: 200, y: 0 }); // p2
  S().addTransitionAt({ x: 100, y: 0 }); // t1
  S().setTokens("p1", 1);
  S().addArc("p1", "t1");
  S().addArc("t1", "p2");
}

beforeEach(() => {
  useStudioStore.setState(initialDataState());
});

// ---------------------------------------------------------------------------
// Document ops (design §9.3: ops validity)
// ---------------------------------------------------------------------------

describe("TestDocumentOps", () => {
  it("addPlace auto-names p1, p2 (first free)", () => {
    let doc = emptyDocument();
    doc = addPlace(doc);
    doc = addPlace(doc);
    expect(doc.places.map((p) => p.name)).toEqual(["p1", "p2"]);
  });

  it("addPlace reuses the first free index after removal", () => {
    let doc = addPlace(addPlace(emptyDocument())); // p1 p2
    doc = removeNode(doc, "p1");
    doc = addPlace(doc);
    expect(doc.places.map((p) => p.name)).toEqual(["p2", "p1"]);
  });

  it("addTransition auto-names t1, t2 independent of places", () => {
    let doc = addPlace(emptyDocument());
    doc = addTransition(doc);
    doc = addTransition(doc);
    expect(doc.transitions.map((t) => t.name)).toEqual(["t1", "t2"]);
  });

  it("auto-naming is V1-safe across places ∪ transitions", () => {
    let doc = addTransition(emptyDocument()); // t1
    doc = renameNode(doc, "t1", "p1").doc; // transition named "p1"
    doc = addPlace(doc);
    expect(doc.places.map((p) => p.name)).toEqual(["p2"]);
  });

  it("removeNode cascades incident arcs in both directions", () => {
    const doc = removeNode(twoNodeDoc(), "t1");
    expect(doc.transitions).toEqual([]);
    expect(doc.arcs).toEqual([]);
    expect(doc.places.map((p) => p.name)).toEqual(["p1", "p2"]);
  });

  it("removeArc removes exactly that arc; unknown arc rejected unchanged", () => {
    const doc = twoNodeDoc();
    const res = removeArc(doc, "p1", "t1");
    expect(res.ok).toBe(true);
    expect(res.doc.arcs).toEqual([{ source: "t1", target: "p2", weight: 1 }]);
    const miss = removeArc(doc, "p1", "p2");
    expect(miss.ok).toBe(false);
    expect(miss.doc).toBe(doc);
  });

  it("renameNode rewires arcs (source and target)", () => {
    const res = renameNode(twoNodeDoc(), "t1", "fire");
    expect(res.ok).toBe(true);
    expect(res.doc.transitions).toEqual([{ name: "fire" }]);
    expect(res.doc.arcs).toEqual([
      { source: "p1", target: "fire", weight: 1 },
      { source: "fire", target: "p2", weight: 1 },
    ]);
  });

  it("renameNode rejects collisions with places and transitions (V1)", () => {
    const doc = twoNodeDoc();
    const ontoPlace = renameNode(doc, "t1", "p1");
    expect(ontoPlace.ok).toBe(false);
    expect(ontoPlace.doc).toBe(doc);
    expect(renameNode(doc, "p1", "p2").ok).toBe(false);
  });

  it("renameNode rejects empty names; renaming to itself is a no-op success", () => {
    const doc = twoNodeDoc();
    expect(renameNode(doc, "p1", "").ok).toBe(false);
    const same = renameNode(doc, "p1", "p1");
    expect(same.ok).toBe(true);
    expect(same.doc).toBe(doc);
  });

  it("renameNode of an unknown node is rejected unchanged", () => {
    const doc = twoNodeDoc();
    const res = renameNode(doc, "nope", "x");
    expect(res.ok).toBe(false);
    expect(res.doc).toBe(doc);
  });

  it("setTokens sets M0 tokens; rejects negative / non-integer / unknown", () => {
    const doc = twoNodeDoc();
    const res = setTokens(doc, "p1", 5);
    expect(res.ok).toBe(true);
    expect(res.doc.places[0].tokens).toBe(5);
    expect(setTokens(doc, "p1", -1).ok).toBe(false);
    expect(setTokens(doc, "p1", 1.5).ok).toBe(false);
    expect(setTokens(doc, "nope", 1).ok).toBe(false);
  });

  it("setWeight updates weight; rejects < 1 and unknown arcs", () => {
    const doc = twoNodeDoc();
    const res = setWeight(doc, "p1", "t1", 3);
    expect(res.ok).toBe(true);
    expect(res.doc.arcs[0].weight).toBe(3);
    expect(setWeight(doc, "p1", "t1", 0).ok).toBe(false);
    expect(setWeight(doc, "p1", "p2", 2).ok).toBe(false);
  });

  it("addArc creates a weight-1 arc", () => {
    const doc = addTransition(addPlace(emptyDocument()));
    const res = addArc(doc, "p1", "t1");
    expect(res.ok).toBe(true);
    expect(res.doc.arcs).toEqual([{ source: "p1", target: "t1", weight: 1 }]);
  });

  it.each([
    ["p1", "p2", /V3/], // place → place
    ["t1", "t2", /V3/], // transition → transition
    ["p1", "ghost", /V2/], // unknown target
    ["ghost", "t1", /V2/], // unknown source
  ])("addArc rejects %s → %s", (source, target, re) => {
    const doc = addPlace(addPlace(addTransition(addTransition(emptyDocument()))));
    const res = addArc(doc, source, target);
    expect(res.ok).toBe(false);
    expect(res.reason).toMatch(re);
    expect(res.doc).toBe(doc);
  });

  it("addArc rejects duplicates (V4)", () => {
    const doc = twoNodeDoc();
    const res = addArc(doc, "p1", "t1");
    expect(res.ok).toBe(false);
    expect(res.reason).toMatch(/V4/);
  });

  it("ops never mutate the input document", () => {
    const doc = twoNodeDoc();
    const snapshot = JSON.parse(JSON.stringify(doc));
    addPlace(doc);
    removeNode(doc, "p1");
    renameNode(doc, "p1", "x");
    setTokens(doc, "p1", 9);
    setWeight(doc, "p1", "t1", 9);
    addArc(doc, "p2", "t1");
    expect(doc).toEqual(snapshot);
  });

  it("toNet derives a working net (enabled set at M0)", () => {
    const net = toNet(twoNodeDoc());
    expect(net.enabledTransitionsAt(net.initialMarkingTuple())).toEqual(["t1"]);
  });

  it("toNet is memoized by document identity", () => {
    const doc = twoNodeDoc();
    expect(toNet(doc)).toBe(toNet(doc));
    expect(toNet(addPlace(doc))).not.toBe(toNet(doc));
  });
});

// ---------------------------------------------------------------------------
// Store modes (design §9.3: mode transitions)
// ---------------------------------------------------------------------------

describe("TestStoreModes", () => {
  it("initial state: edit mode, empty doc, no marking/error", () => {
    const s = S();
    expect(s.mode).toBe("edit");
    expect(s.doc).toEqual({ places: [], transitions: [], arcs: [] });
    expect(s.positions).toEqual({});
    expect(s.marking).toBeNull();
    expect(s.selection).toBeNull();
    expect(s.importError).toBeNull();
  });

  it("addPlaceAt/addTransitionAt add nodes with integer-snapped positions", () => {
    S().addPlaceAt({ x: 10.4, y: 20.6 });
    S().addTransitionAt({ x: -3.6, y: 7.2 });
    const s = S();
    expect(s.doc.places.map((p) => p.name)).toEqual(["p1"]);
    expect(s.doc.transitions.map((t) => t.name)).toEqual(["t1"]);
    expect(s.positions["p1"]).toEqual({ x: 10, y: 21 });
    expect(s.positions["t1"]).toEqual({ x: -4, y: 7 });
  });

  it("setMode simulate snapshots M0 over placeOrder; edit discards it", () => {
    buildHelloInStore();
    S().setMode("simulate");
    expect(S().mode).toBe("simulate");
    expect(S().marking).toEqual([1, 0]); // placeOrder [p1, p2]
    S().setMode("edit");
    expect(S().marking).toBeNull();
  });

  it("setMode to the current mode is a no-op", () => {
    S().setMode("edit");
    expect(S().mode).toBe("edit");
    expect(S().marking).toBeNull();
  });

  it("simulate mode locks all structure edits", () => {
    buildHelloInStore();
    const docBefore = S().doc;
    const posBefore = S().positions;
    S().setMode("simulate");
    S().addPlaceAt({ x: 9, y: 9 });
    S().addTransitionAt({ x: 9, y: 9 });
    S().removeNode("p1");
    S().moveNode("p1", { x: 500, y: 500 });
    expect(S().addArc("p2", "t1")).toBe(false);
    expect(S().removeArc("p1", "t1")).toBe(false);
    expect(S().renameNode("p1", "zz")).toBe(false);
    expect(S().setTokens("p1", 7)).toBe(false);
    expect(S().setWeight("p1", "t1", 7)).toBe(false);
    expect(S().doc).toBe(docBefore);
    expect(S().positions).toBe(posBefore);
  });

  it("returning to edit re-enables structure edits", () => {
    buildHelloInStore();
    S().setMode("simulate");
    S().setMode("edit");
    S().addPlaceAt({ x: 1, y: 1 });
    expect(S().doc.places.map((p) => p.name)).toEqual(["p1", "p2", "p3"]);
  });
});

// ---------------------------------------------------------------------------
// Fire & reset (design §9.3: fire updates marking + enabled set, reset)
// ---------------------------------------------------------------------------

describe("TestStoreFireReset", () => {
  it("fireTransition advances the marking; enabled set tracks it", () => {
    buildHelloInStore();
    S().setMode("simulate");
    expect(enabledTransitions(S().doc, S().marking)).toEqual(["t1"]);
    S().fireTransition("t1");
    expect(S().marking).toEqual([0, 1]);
    expect(enabledTransitions(S().doc, S().marking)).toEqual([]);
  });

  it("fireTransition on a disabled transition is a no-op", () => {
    buildHelloInStore();
    S().setMode("simulate");
    S().fireTransition("t1");
    const marking = S().marking;
    S().fireTransition("t1"); // now disabled
    expect(S().marking).toBe(marking);
    expect(S().marking).toEqual([0, 1]);
  });

  it("fireTransition in edit mode is a no-op", () => {
    buildHelloInStore();
    S().fireTransition("t1");
    expect(S().marking).toBeNull();
  });

  it("resetMarking restores M0; no-op in edit mode", () => {
    buildHelloInStore();
    S().setMode("simulate");
    S().fireTransition("t1");
    S().resetMarking();
    expect(S().marking).toEqual([1, 0]);
    S().setMode("edit");
    S().resetMarking();
    expect(S().marking).toBeNull();
  });

  it("enabledTransitions returns [] outside simulate (null marking)", () => {
    buildHelloInStore();
    expect(enabledTransitions(S().doc, S().marking)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Import / export (design §9.3: import-error integrity, round-trip)
// ---------------------------------------------------------------------------

describe("TestStoreImportExport", () => {
  it("importJson loads a document with layout positions verbatim", () => {
    expect(S().importJson(EXAMPLE_TEXTS["producer_consumer"])).toBe(true);
    const s = S();
    expect(s.doc.places).toEqual([
      { name: "buffer", tokens: 0 },
      { name: "consumer_ready", tokens: 1 },
      { name: "free_slots", tokens: 3 },
      { name: "producer_ready", tokens: 1 },
    ]);
    expect(s.doc.transitions).toEqual([{ name: "consume" }, { name: "produce" }]);
    expect(s.doc.arcs).toHaveLength(7);
    expect(s.positions["buffer"]).toEqual({ x: 260, y: 60 });
    expect(s.positions["produce"]).toEqual({ x: 100, y: 60 });
    expect(s.positions["consume"]).toEqual({ x: 260, y: 220 });
    expect(s.importError).toBeNull();
    expect(s.mode).toBe("edit");
  });

  it("importJson without layout assigns circle auto-layout positions", () => {
    const text = JSON.stringify({
      format: "petri-net-json",
      version: 1,
      places: [
        { name: "a", tokens: 0 },
        { name: "b", tokens: 0 },
      ],
      transitions: [{ name: "t" }],
      arcs: [],
    });
    expect(S().importJson(text)).toBe(true);
    const positions = S().positions;
    expect(Object.keys(positions).sort()).toEqual(["a", "b", "t"]);
    for (const p of Object.values(positions)) {
      expect(Number.isInteger(p.x)).toBe(true);
      expect(Number.isInteger(p.y)).toBe(true);
      expect(Math.hypot(p.x, p.y)).toBeGreaterThanOrEqual(AUTO_LAYOUT_RADIUS - 1);
      expect(Math.hypot(p.x, p.y)).toBeLessThanOrEqual(AUTO_LAYOUT_RADIUS + 1);
    }
  });

  it("failed import records '<Class>: <message>' and leaves state untouched", () => {
    buildHelloInStore();
    S().setMode("simulate");
    const before = { doc: S().doc, positions: S().positions, mode: S().mode, marking: S().marking };
    expect(S().importJson("{ not json")).toBe(false);
    expect(S().importError).toMatch(/^[A-Za-z]+Error: .+/);
    expect(S().doc).toBe(before.doc);
    expect(S().positions).toBe(before.positions);
    expect(S().mode).toBe(before.mode);
    expect(S().marking).toBe(before.marking);
  });

  it("semantic failures (V1–V4) surface as importError carrying the rule id", () => {
    const dup = JSON.stringify({
      format: "petri-net-json",
      version: 1,
      places: [
        { name: "a", tokens: 0 },
        { name: "a", tokens: 0 },
      ],
      transitions: [],
      arcs: [],
    });
    expect(S().importJson(dup)).toBe(false);
    expect(S().importError).toMatch(/^SemanticValidationError: V1:/);
  });

  it("a successful import clears a previous importError", () => {
    expect(S().importJson("{ not json")).toBe(false);
    expect(S().importError).not.toBeNull();
    expect(S().importJson(EXAMPLE_TEXTS["hello"])).toBe(true);
    expect(S().importError).toBeNull();
  });

  it("import lands in edit mode with marking cleared (even from simulate)", () => {
    buildHelloInStore();
    S().setMode("simulate");
    expect(S().importJson(EXAMPLE_TEXTS["hello"])).toBe(true);
    expect(S().mode).toBe("edit");
    expect(S().marking).toBeNull();
  });

  it("export → import round-trip: doc + positions equal, re-export byte-identical", () => {
    buildHelloInStore();
    S().setTokens("p1", 2);
    S().setWeight("t1", "p2", 3);
    const text = S().exportJson();
    const docBefore = S().doc;
    const posBefore = S().positions;
    expect(S().importJson(text)).toBe(true);
    expect(S().doc).toEqual(docBefore);
    expect(S().positions).toEqual(posBefore);
    expect(S().exportJson()).toBe(text);
  });

  it("exportJson emits canonical bytes with integer layout nodes", () => {
    buildHelloInStore();
    const text = S().exportJson();
    expect(text.endsWith("\n")).toBe(true);
    const parsed = JSON.parse(text);
    expect(parsed.format).toBe("petri-net-json");
    expect(Object.keys(parsed.layout.nodes).sort()).toEqual(["p1", "p2", "t1"]);
    for (const pos of Object.values(parsed.layout.nodes) as { x: number; y: number }[]) {
      expect(Number.isInteger(pos.x)).toBe(true);
      expect(Number.isInteger(pos.y)).toBe(true);
    }
  });

  it("export after importing the laid-out example reproduces its file bytes", () => {
    expect(S().importJson(EXAMPLE_TEXTS["producer_consumer"])).toBe(true);
    expect(S().exportJson()).toBe(EXAMPLE_TEXTS["producer_consumer"]);
  });
});

// ---------------------------------------------------------------------------
// Examples menu + docFromNet helper
// ---------------------------------------------------------------------------

describe("TestLoadExample", () => {
  it.each(EXAMPLE_NAMES)("loadExample(%s) loads cleanly", (name) => {
    expect(S().loadExample(name)).toBe(true);
    expect(S().importError).toBeNull();
    expect(S().doc.places.length).toBeGreaterThan(0);
  });

  it("loadExample(hello) gives the hello net, simulatable", () => {
    S().loadExample("hello");
    expect(S().doc.places).toEqual([
      { name: "p1", tokens: 1 },
      { name: "p2", tokens: 0 },
    ]);
    expect(Object.keys(S().positions).sort()).toEqual(["p1", "p2", "t1"]);
    S().setMode("simulate");
    expect(S().marking).toEqual([1, 0]);
    expect(enabledTransitions(S().doc, S().marking)).toEqual(["t1"]);
  });

  it("loadExample with an unknown name fails without touching the doc", () => {
    buildHelloInStore();
    const before = S().doc;
    expect(S().loadExample("nope")).toBe(false);
    expect(S().importError).toMatch(/unknown example/i);
    expect(S().doc).toBe(before);
  });
});

describe("TestDocFromNet", () => {
  it("mirrors net content in canonical order", () => {
    S().loadExample("weighted_reaction");
    const doc = S().doc;
    expect(docFromNet(toNet(doc))).toEqual(doc);
    expect(doc.arcs).toEqual([
      { source: "h2", target: "react", weight: 2 },
      { source: "o2", target: "react", weight: 1 },
      { source: "react", target: "h2o", weight: 2 },
    ]);
  });
});
