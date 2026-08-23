// @vitest-environment node
// TA: gotcha: @vitest-environment node is REQUIRED for engine/store tests: under jsdom, vitest rewrites import.meta.url to http://localhost and fs.readFileSync(new URL(...)) dies with 'The URL must be of scheme file'. UI component tests are the only ones that should use jsdom.
/**
 * io-layer tests — 1:1 TS port of `tests/model/petri_net/test_io.py`
 * (59 behaviors; design_001 §9.2). Covers: canonical serialization (D7/§8),
 * two-level validation (§6: level-1 shape + level-2 V1–V6), typed-error
 * precedence, layout verbatim round-trip (§5), M0-only serialization, the
 * shared examples as golden canonical bytes, and JSON Schema cross-checks
 * (ajv, dev-only).
 *
 * NOTE (integral floats): JS collapses 1.0 === 1, so the integral-float
 * normalization path is exercised at the JSON TEXT level (raw "1.0" literal),
 * mirroring what Python's json.dumps(1.0) -> "1.0" exercises.
 */

import { readFileSync } from "node:fs";

import Ajv2020 from "ajv/dist/2020.js";
import { describe, expect, it } from "vitest";

import { PetriNetError } from "../../src/engine/errors.js";
import {
  documentFromJson,
  FormatSyntaxError,
  netFromJson,
  netToJson,
  PetriNetFormatError,
  SchemaValidationError,
  SemanticValidationError,
  UnknownFormatError,
  UnsupportedVersionError,
  type JsonValue,
} from "../../src/engine/io.js";
import { PetriNet } from "../../src/engine/model.js";

const EXAMPLES = new URL("../../../../shared/petri-net/examples/", import.meta.url);
const SCHEMA = new URL("../../../../shared/petri-net/petri-net-json-v1.schema.json", import.meta.url);
const EXAMPLE_NAMES = ["hello.json", "producer_consumer.json", "weighted_reaction.json"] as const;

function readExample(name: string): string {
  return readFileSync(new URL(name, EXAMPLES), "utf-8");
}

function makeHello(): PetriNet {
  // FORMAT.md Appendix A net: p1 -t1-> p2, one token in p1.
  const net = new PetriNet();
  net.addPlace("p1", 1);
  net.addPlace("p2", 0);
  net.addTransition("t1");
  net.addInput({ place: "p1", transition: "t1" });
  net.addOutput({ transition: "t1", place: "p2" });
  return net;
}

const HELLO_JSON = `{
  "format": "petri-net-json",
  "version": 1,
  "places": [
    {
      "name": "p1",
      "tokens": 1
    },
    {
      "name": "p2",
      "tokens": 0
    }
  ],
  "transitions": [
    {
      "name": "t1"
    }
  ],
  "arcs": [
    {
      "source": "p1",
      "target": "t1",
      "weight": 1
    },
    {
      "source": "t1",
      "target": "p2",
      "weight": 1
    }
  ]
}
`;

// ---------------------------------------------------------------------------
// Behavior 1 — canonical dump (§8): bytes, ordering, escaping
// ---------------------------------------------------------------------------

describe("TestCanonicalDump", () => {
  it("test_hello_serializes_to_expected_canonical_bytes", () => {
    expect(netToJson(makeHello())).toBe(HELLO_JSON);
  });

  it("test_places_transitions_arcs_sorted_code_point", () => {
    const net = new PetriNet();
    net.addPlace("z", 0);
    net.addPlace("a", 2);
    net.addTransition("t2");
    net.addTransition("t10"); // code-point: "t10" < "t2"
    net.addInput({ place: "z", transition: "t2", weight: 3 });
    net.addInput({ place: "a", transition: "t10" });
    net.addOutput({ transition: "t2", place: "a" });
    const doc = JSON.parse(netToJson(net));
    expect(doc.places.map((p: { name: string }) => p.name)).toEqual(["a", "z"]);
    expect(doc.transitions.map((t: { name: string }) => t.name)).toEqual(["t10", "t2"]);
    const arcs = doc.arcs.map((a: { source: string; target: string }) => [a.source, a.target]);
    const sorted = [...arcs].sort((x, y) => (x[0] + "x" < y[0] + "x" ? -1 : 1));
    expect(arcs).toEqual(sorted);
    expect(arcs).toEqual([
      ["a", "t10"],
      ["t2", "a"],
      ["z", "t2"],
    ]);
  });

  it("test_explicit_weights_and_tokens_always_emitted", () => {
    const doc = JSON.parse(netToJson(makeHello()));
    for (const p of doc.places) expect(Object.keys(p).sort()).toEqual(["name", "tokens"]);
    for (const a of doc.arcs) expect(Object.keys(a).sort()).toEqual(["source", "target", "weight"]);
  });

  it("test_non_ascii_names_written_raw_utf8", () => {
    const net = new PetriNet();
    net.addPlace("plätz", 1);
    net.addTransition("tü");
    net.addInput({ place: "plätz", transition: "tü" });
    const text = netToJson(net);
    expect(text).toContain("plätz");
    expect(text).toContain("tü");
    expect(text).not.toContain("\\u");
  });

  it("test_strings_minimally_escaped", () => {
    const net = new PetriNet();
    net.addPlace('quote"and\nnewline', 0);
    const text = netToJson(net);
    expect(text).toContain('\\"');
    expect(text).toContain("\\n");
  });

  it("test_empty_net_round_trips", () => {
    const text = netToJson(new PetriNet());
    expect(netToJson(netFromJson(text))).toBe(text);
  });

  it("test_dump_uses_initial_marking_not_live", () => {
    const net = makeHello();
    net.fire("t1"); // live marking now (0, 1); M0 stays (1, 0)
    expect(netToJson(net)).toBe(HELLO_JSON);
  });

  it("test_trailing_lf_and_indent", () => {
    const text = netToJson(makeHello());
    expect(text.endsWith("\n")).toBe(true);
    expect(text.endsWith("\n\n")).toBe(false);
    expect(text).toContain('\n  "version"');
  });
});

// ---------------------------------------------------------------------------
// Behavior 2 — load: happy path + document round-trip byte-identity (§5/§8)
// ---------------------------------------------------------------------------

describe("TestLoad", () => {
  it("test_hello_loads_to_equivalent_net", () => {
    const net = netFromJson(HELLO_JSON);
    expect(net.places).toEqual(new Set(["p1", "p2"]));
    expect(net.transitions).toEqual(new Set(["t1"]));
    expect(net.inputs).toEqual(new Map([["t1", new Map([["p1", 1]])]]));
    expect(net.outputs).toEqual(new Map([["t1", new Map([["p2", 1]])]]));
    expect(net.initialMarking).toEqual(
      new Map([
        ["p1", 1],
        ["p2", 0],
      ]),
    );
    expect(net.enabledTransitionsAt(net.currentMarking())).toEqual(["t1"]);
  });

  it("test_document_round_trip_byte_identical", () => {
    const doc = documentFromJson(HELLO_JSON);
    expect(doc.layout).toBeNull();
    expect(netToJson(doc.net, doc.layout)).toBe(HELLO_JSON);
  });

  it("test_net_to_json_accepts_layout_and_validates_it", () => {
    const layout = { nodes: { p1: { x: 1, y: 2 } } };
    const text = netToJson(makeHello(), layout);
    expect(JSON.parse(text).layout).toEqual(layout);
    expect(() => netToJson(makeHello(), { nodes: { p1: { x: 1.5, y: 2 } } })).toThrow(SchemaValidationError);
  });

  it.each(EXAMPLE_NAMES)("test_shared_examples_are_golden_canonical_bytes[%s]", (name) => {
    // The shipped examples round-trip byte-identically (D7).
    const text = readExample(name);
    const doc = documentFromJson(text);
    expect(netToJson(doc.net, doc.layout)).toBe(text);
  });

  it("test_layout_preserved_verbatim_including_extensions", () => {
    const text = readExample("producer_consumer.json");
    const docIn = JSON.parse(text);
    docIn.layout.viewport = { zoom: 1, x: 0, y: 0 }; // extension member
    const doc = documentFromJson(JSON.stringify(docIn));
    const out = JSON.parse(netToJson(doc.net, doc.layout));
    expect(out.layout.viewport).toEqual({ zoom: 1, x: 0, y: 0 });
  });

  it("test_layout_nodes_for_unknown_nodes_ignored_not_error", () => {
    const docIn = JSON.parse(HELLO_JSON);
    docIn.layout = { nodes: { ghost: { x: 0, y: 0 }, p1: { x: 1, y: 2 } } };
    const doc = documentFromJson(JSON.stringify(docIn)); // V6: ignored, not error
    const out = JSON.parse(netToJson(doc.net, doc.layout));
    expect(Object.keys(out.layout.nodes).sort()).toEqual(["ghost", "p1"]);
  });

  it("test_integral_floats_normalized_to_int", () => {
    // JSON text with a raw integral-float literal (JS collapses 1.0 === 1, so
    // this must be exercised at the text level — see module docstring).
    const withFloat = HELLO_JSON.replace('"tokens": 1', '"tokens": 1.0');
    expect(withFloat).toContain('"tokens": 1.0');
    const net = netFromJson(withFloat);
    expect(net.initialMarking.get("p1")).toBe(1);
    // …and re-serialization is canonical integer bytes.
    expect(netToJson(net)).toBe(HELLO_JSON);
  });

  it("test_non_canonical_input_loads_and_recanonicalizes", () => {
    const messy = JSON.stringify({
      arcs: [
        { weight: 1, target: "t1", source: "p1" },
        { weight: 1, target: "p2", source: "t1" },
      ],
      transitions: [{ name: "t1" }],
      places: [
        { tokens: 0, name: "p2" },
        { tokens: 1, name: "p1" },
      ],
      version: 1,
      format: "petri-net-json",
    });
    expect(netToJson(netFromJson(messy))).toBe(HELLO_JSON);
  });
});

// ---------------------------------------------------------------------------
// Behavior 3 — typed errors, precedence (syntax → format → version → L1 → L2)
// ---------------------------------------------------------------------------

function doc(overrides: Record<string, JsonValue> = {}): Record<string, JsonValue> {
  return { ...JSON.parse(HELLO_JSON), ...overrides };
}

describe("TestTypedErrors", () => {
  it("test_syntax_error_on_malformed_json", () => {
    expect(() => netFromJson("{not json")).toThrow(FormatSyntaxError);
  });

  it("test_syntax_error_on_duplicate_keys", () => {
    expect(() => netFromJson('{"format": "petri-net-json", "format": "petri-net-json"}')).toThrow(
      /Duplicate object key/,
    );
    expect(() => netFromJson('{"format": "petri-net-json", "format": "petri-net-json"}')).toThrow(FormatSyntaxError);
  });

  it("test_document_must_be_object", () => {
    expect(() => netFromJson("[1, 2]")).toThrow(FormatSyntaxError);
  });

  it("test_unknown_format", () => {
    expect(() => netFromJson(JSON.stringify(doc({ format: "other" })))).toThrow(UnknownFormatError);
  });

  it("test_format_checked_before_version", () => {
    expect(() => netFromJson(JSON.stringify(doc({ format: "other", version: 99 })))).toThrow(UnknownFormatError);
  });

  it("test_unsupported_version", () => {
    expect(() => netFromJson(JSON.stringify(doc({ version: 99 })))).toThrow(/99/);
    expect(() => netFromJson(JSON.stringify(doc({ version: 99 })))).toThrow(UnsupportedVersionError);
  });

  it.each([
    ["format=1", doc({ format: 1 })],
    ["version='1'", doc({ version: "1" })],
    ["places=null", doc({ places: null })],
    ["arcs={}", doc({ arcs: {} })],
    ["extra=1", doc({ extra: 1 })],
  ])("test_schema_level_violations[%s]", (_label, bad) => {
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(SchemaValidationError);
  });

  it.each(["version", "places", "transitions", "arcs"] as const)("test_missing_required_members[%s]", (member) => {
    const bad = JSON.parse(HELLO_JSON);
    delete bad[member];
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(SchemaValidationError);
  });

  it("test_missing_format_member", () => {
    const bad = JSON.parse(HELLO_JSON);
    delete bad.format;
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(/format/);
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(SchemaValidationError);
  });

  it.each([
    [{ name: "", tokens: 0 }, "non-empty"],
    [{ name: "p", tokens: -1 }, ">= 0"],
    [{ name: "p", tokens: true }, "boolean"],
    [{ name: "p", tokens: 0.5 }, "integer"],
    [{ name: "p" }, "requires"],
    [{ name: "p", tokens: 0, extra: 1 }, "unknown"],
  ])("test_bad_places[%s]", (place, frag) => {
    const bad = doc({ places: [place as JsonValue] });
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(frag as unknown as RegExp);
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(SchemaValidationError);
  });

  it.each([
    [{ source: "p1", target: "t1", weight: 0 }, ">= 1"],
    [{ source: "p1", target: "t1", weight: 1.5 }, "integer"],
    [{ source: "", target: "t1", weight: 1 }, "non-empty"],
    [{ source: "p1", target: "t1" }, "requires"],
  ])("test_bad_arcs[%s]", (arc, frag) => {
    const bad = doc({ arcs: [arc as JsonValue] });
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(frag as unknown as RegExp);
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(SchemaValidationError);
  });

  it.each([
    ["layout='not-an-object'", "not-an-object"],
    ["nodes=array", { nodes: ["not-an-object"] }],
    ["x=1.5", { nodes: { p1: { x: 1.5, y: 0 } } }],
    ["missing y", { nodes: { p1: { x: 0 } } }],
    ["extra z", { nodes: { p1: { x: 0, y: 0, z: 0 } } }],
  ])("test_bad_layouts[%s]", (_label, layout) => {
    const bad = doc({ layout: layout as JsonValue });
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(SchemaValidationError);
  });

  it.each([
    ["dup places", doc({ places: [{ name: "p1", tokens: 0 }, { name: "p1", tokens: 1 }] }), "V1"],
    ["name in both P and T", doc({ transitions: [{ name: "p1" }] }), "V1"],
    ["arc to ghost", doc({ arcs: [{ source: "p1", target: "ghost", weight: 1 }] }), "V2"],
    ["place-to-place arc", doc({ arcs: [{ source: "p1", target: "p2", weight: 1 }] }), "V3"],
    [
      "duplicate arc",
      doc({
        arcs: [
          { source: "p1", target: "t1", weight: 1 },
          { source: "p1", target: "t1", weight: 2 },
        ],
      }),
      "V4",
    ],
  ])("test_semantic_violations_carry_rule_id[%s]", (_label, bad, rule) => {
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(rule as unknown as RegExp);
    expect(() => netFromJson(JSON.stringify(bad))).toThrow(SemanticValidationError);
  });

  it("test_errors_subclass_library_base", () => {
    for (const cls of [
      FormatSyntaxError,
      UnknownFormatError,
      UnsupportedVersionError,
      SchemaValidationError,
      SemanticValidationError,
    ]) {
      expect(new cls("x")).toBeInstanceOf(PetriNetError);
    }
  });
});

// ---------------------------------------------------------------------------
// Behavior 4 — cross-checks against the JSON Schema (ajv, dev-only)
// ---------------------------------------------------------------------------

describe("TestSchemaCrossCheck", () => {
  const ajv = new Ajv2020({ strict: false, allErrors: true });
  const schema = JSON.parse(readFileSync(SCHEMA, "utf-8"));
  const validate = ajv.compile(schema);

  it.each(EXAMPLE_NAMES)("test_examples_validate_against_schema[%s]", (name) => {
    const ok = validate(JSON.parse(readExample(name)));
    expect(validate.errors ?? []).toEqual([]);
    expect(ok).toBe(true);
  });

  it("test_io_rejects_what_schema_rejects", () => {
    const bads = [
      doc({ format: "other" }),
      doc({ version: 2 }),
      doc({ extra: 1 }),
      doc({ places: [{ name: "p", tokens: -1 }] }),
      doc({ arcs: [{ source: "p1", target: "t1", weight: 0 }] }),
    ];
    for (const bad of bads) {
      expect(validate(bad)).toBe(false);
      expect(() => netFromJson(JSON.stringify(bad))).toThrow(PetriNetFormatError);
    }
  });
});
