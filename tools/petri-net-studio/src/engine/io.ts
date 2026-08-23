/**
 * petri-net-json v1 io — TS port of `src/agentx/model/petri_net/io.py`
 * (shared/petri-net/FORMAT.md; executable spec; 59-test matrix in
 * `tests/engine/io.test.ts` + golden bytes in `shared/petri-net/examples/`).
 *
 * The format is the ONLY coupling to the Python library (D5); semantics stay
 * with model.ts — this module translates documents to nets and back.
 *
 * - Load (documentFromJson / netFromJson): JSON syntax with duplicate-key
 *   rejection (parseJsonStrict — JSON.parse cannot detect duplicates, A1),
 *   then level-1 shape/types/domains, then level-2 semantic rules V1–V6
 *   (FORMAT.md §6), then net construction per §7.
 *   Error precedence: FormatSyntaxError → UnknownFormatError →
 *   UnsupportedVersionError → SchemaValidationError → SemanticValidationError.
 * - Dump (netToJson): canonical bytes per FORMAT.md §8 — pinned member order,
 *   code-point-sorted arrays (A3 comparator — NOT JS default sort), integer-only
 *   numbers, minimal escaping, trailing LF. Round-trip byte-identity is a
 *   tested property (D7).
 * - tokens is the initial marking M0 (initialMarking), never the live marking;
 *   v1 has no current-marking snapshots. layout is UI-namespaced: ignored for
 *   computation, preserved verbatim on document round-trips (§5).
 *
 * Documented cross-implementation caveats (outside the pinned test matrix):
 * - A2: integer-like object keys inside layout EXTENSION values enumerate in
 *   numeric-first order in JS vs pure insertion order in Python — byte
 *   divergence possible for such exotic extension values only; the v1-pinned
 *   surface (and all golden examples) is unaffected.
 * - Numbers are JS doubles: an integral-float literal (e.g. `"version": 1.0`)
 *   is accepted and normalized everywhere, including `version` — Python io.py
 *   rejects a float-typed version under its strict isinstance check. Schema
 *   regards 1.0 as integer; TS follows the schema, Python is stricter.
 */

import { PetriNetError } from "./errors.js";
import { PetriNet, compareCodePoints } from "./model.js";

export const FORMAT_ID = "petri-net-json";
export const FORMAT_VERSION = 1;

// ---------------------------------------------------------------------------
// Typed errors (all subclass the engine base, mirroring io.py)
// ---------------------------------------------------------------------------

/** Base class for petri-net-json load/dump failures. */
export class PetriNetFormatError extends PetriNetError {
  constructor(message: string) {
    super(message);
    this.name = "PetriNetFormatError";
  }
}

/** Not well-formed JSON, or a duplicate object key (FORMAT.md §6). */
export class FormatSyntaxError extends PetriNetFormatError {
  constructor(message: string) {
    super(message);
    this.name = "FormatSyntaxError";
  }
}

/** Top-level `format` is not "petri-net-json". */
export class UnknownFormatError extends PetriNetFormatError {
  constructor(message: string) {
    super(message);
    this.name = "UnknownFormatError";
  }
}

/** `version` is not implemented here (this implementation speaks v1). */
export class UnsupportedVersionError extends PetriNetFormatError {
  constructor(message: string) {
    super(message);
    this.name = "UnsupportedVersionError";
  }
}

/** Level-1 violation: document shape, types, or integer domains (§6). */
export class SchemaValidationError extends PetriNetFormatError {
  constructor(message: string) {
    super(message);
    this.name = "SchemaValidationError";
  }
}

/** Level-2 violation: semantic rules V1–V6 (§6); message carries the rule id. */
export class SemanticValidationError extends PetriNetFormatError {
  constructor(message: string) {
    super(message);
    this.name = "SemanticValidationError";
  }
}

// ---------------------------------------------------------------------------
// JSON value model + document
// ---------------------------------------------------------------------------

export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };
export type JsonObject = { [key: string]: JsonValue };

/** A loaded document: the net plus the verbatim `layout` member (§5). */
export interface PetriNetDocument {
  net: PetriNet;
  layout: JsonValue | null;
}

function isObject(v: JsonValue): v is JsonObject {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

/** Python-repr-ish rendering for error messages (single-quoted strings). */
function pyrepr(v: unknown): string {
  if (typeof v === "string") return `'${v.replace(/\\/g, "\\\\").replace(/'/g, "\\'")}'`;
  if (typeof v === "boolean") return v ? "True" : "False";
  if (v === null) return "None";
  if (Array.isArray(v)) return `[${v.map(pyrepr).join(", ")}]`;
  if (typeof v === "object" && v !== null) return `{${Object.entries(v as JsonObject).map(([k, val]) => `${pyrepr(k)}: ${pyrepr(val)}`).join(", ")}}`;
  return String(v);
}

// ---------------------------------------------------------------------------
// parseJsonStrict — full JSON grammar with duplicate-key rejection (A1)
// ---------------------------------------------------------------------------

class Parser {
  private i = 0;

  constructor(private readonly text: string) {}

  parse(): JsonValue {
    this.ws();
    const value = this.value();
    this.ws();
    if (this.i !== this.text.length) {
      throw new FormatSyntaxError(`Invalid JSON: trailing data at offset ${this.i}`);
    }
    return value;
  }

  private ws(): void {
    while (this.i < this.text.length && " \t\n\r".includes(this.text[this.i])) this.i++;
  }

  private fail(what: string): never {
    throw new FormatSyntaxError(`Invalid JSON: ${what} at offset ${this.i}`);
  }

  private value(): JsonValue {
    if (this.i >= this.text.length) this.fail("Expecting value");
    const c = this.text[this.i];
    if (c === "{") return this.object();
    if (c === "[") return this.array();
    if (c === '"') return this.string();
    if (c === "t") return this.literal("true", true);
    if (c === "f") return this.literal("false", false);
    if (c === "n") return this.literal("null", null);
    if (c === "-" || (c >= "0" && c <= "9")) return this.number();
    this.fail(`Unexpected character ${pyrepr(c)}`);
  }

  private literal(word: string, value: JsonValue): JsonValue {
    if (this.text.startsWith(word, this.i)) {
      this.i += word.length;
      return value;
    }
    this.fail("Expecting value");
  }

  private object(): JsonObject {
    this.i++; // '{'
    const obj: JsonObject = {};
    this.ws();
    if (this.text[this.i] === "}") {
      this.i++;
      return obj;
    }
    for (;;) {
      this.ws();
      if (this.text[this.i] !== '"') this.fail("Expecting property name enclosed in double quotes");
      const key = this.string();
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        throw new FormatSyntaxError(`Duplicate object key: ${pyrepr(key)}`);
      }
      this.ws();
      if (this.text[this.i] !== ":") this.fail("Expecting ':' delimiter");
      this.i++;
      this.ws();
      obj[key] = this.value();
      this.ws();
      const c = this.text[this.i];
      if (c === ",") {
        this.i++;
        continue;
      }
      if (c === "}") {
        this.i++;
        return obj;
      }
      this.fail("Expecting ',' delimiter");
    }
  }

  private array(): JsonValue[] {
    this.i++; // '['
    const arr: JsonValue[] = [];
    this.ws();
    if (this.text[this.i] === "]") {
      this.i++;
      return arr;
    }
    for (;;) {
      this.ws();
      arr.push(this.value());
      this.ws();
      const c = this.text[this.i];
      if (c === ",") {
        this.i++;
        continue;
      }
      if (c === "]") {
        this.i++;
        return arr;
      }
      this.fail("Expecting ',' delimiter");
    }
  }

  private string(): string {
    this.i++; // opening '"'
    let out = "";
    for (;;) {
      if (this.i >= this.text.length) this.fail("Unterminated string");
      const c = this.text[this.i];
      if (c === '"') {
        this.i++;
        return out;
      }
      if (c === "\\") {
        this.i++;
        if (this.i >= this.text.length) this.fail("Unterminated string escape");
        const e = this.text[this.i];
        this.i++;
        switch (e) {
          case '"': out += '"'; break;
          case "\\": out += "\\"; break;
          case "/": out += "/"; break;
          case "b": out += "\b"; break;
          case "f": out += "\f"; break;
          case "n": out += "\n"; break;
          case "r": out += "\r"; break;
          case "t": out += "\t"; break;
          case "u": {
            const first = this.hex4();
            if (first >= 0xd800 && first <= 0xdbff && this.text.startsWith("\\u", this.i)) {
              const save = this.i;
              this.i += 2;
              const second = this.hex4();
              if (second >= 0xdc00 && second <= 0xdfff) {
                out += String.fromCodePoint(0x10000 + ((first - 0xd800) << 10) + (second - 0xdc00));
              } else {
                // Lone high surrogate + non-low escape: keep both (Python parity).
                this.i = save;
                out += String.fromCharCode(first);
              }
            } else {
              out += String.fromCharCode(first); // lone surrogates kept (Python parity)
            }
            break;
          }
          default:
            this.fail(`Invalid \\escape: ${pyrepr(e)}`);
        }
      } else if (c < " ") {
        this.fail("Invalid control character");
      } else {
        out += c;
        this.i++;
      }
    }
  }

  private hex4(): number {
    const s = this.text.slice(this.i, this.i + 4);
    if (s.length !== 4 || !/^[0-9a-fA-F]{4}$/.test(s)) this.fail("Invalid \\uXXXX escape");
    this.i += 4;
    return parseInt(s, 16);
  }

  private number(): number {
    const start = this.i;
    if (this.text[this.i] === "-") this.i++;
    if (this.text[this.i] === "0") {
      this.i++;
    } else if (this.text[this.i] >= "1" && this.text[this.i] <= "9") {
      while (this.i < this.text.length && this.text[this.i] >= "0" && this.text[this.i] <= "9") this.i++;
    } else {
      this.fail("Expecting value");
    }
    if (this.text[this.i] === ".") {
      this.i++;
      const fracStart = this.i;
      while (this.i < this.text.length && this.text[this.i] >= "0" && this.text[this.i] <= "9") this.i++;
      if (this.i === fracStart) this.fail("Expecting fraction digits");
    }
    if (this.text[this.i] === "e" || this.text[this.i] === "E") {
      this.i++;
      if (this.text[this.i] === "+" || this.text[this.i] === "-") this.i++;
      const expStart = this.i;
      while (this.i < this.text.length && this.text[this.i] >= "0" && this.text[this.i] <= "9") this.i++;
      if (this.i === expStart) this.fail("Expecting exponent digits");
    }
    return Number(this.text.slice(start, this.i));
  }
}

/** json.loads with duplicate-key rejection (FORMAT.md §6 level 1). */
export function parseJsonStrict(text: string): JsonValue {
  return new Parser(text).parse();
}

// ---------------------------------------------------------------------------
// Validation — levels 1+2 (line-by-line port of io.py _validate)
// ---------------------------------------------------------------------------

interface PlaceItem {
  name: string;
  tokens: number;
}
interface TransitionItem {
  name: string;
}
interface ArcItem {
  source: string;
  target: string;
  weight: number;
}

const TOP_LEVEL_KEYS = new Set(["format", "version", "places", "transitions", "arcs", "layout"]);

function requireSchema(cond: boolean, message: string): void {
  if (!cond) throw new SchemaValidationError(message);
}

/** Schema-`integer` semantics: number (never boolean) and integral. */
function asInt(value: JsonValue, what: string, minimum: number): number {
  if (typeof value === "boolean") {
    throw new SchemaValidationError(`${what} must be an integer, got boolean ${value}`);
  }
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throw new SchemaValidationError(`${what} must be an integer, got ${pyrepr(value)}`);
  }
  if (value < minimum) {
    throw new SchemaValidationError(`${what} must be >= ${minimum}, got ${value}`);
  }
  return value;
}

function asName(value: JsonValue, what: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new SchemaValidationError(`${what} must be a non-empty string, got ${pyrepr(value)}`);
  }
  return value;
}

function exactKeys(obj: JsonValue, keys: Set<string>, what: string): JsonObject {
  if (!isObject(obj)) {
    throw new SchemaValidationError(`${what} must be an object, got ${pyrepr(obj)}`);
  }
  const unknown = Object.keys(obj).filter((k) => !keys.has(k)).sort(compareCodePoints);
  requireSchema(unknown.length === 0, `${what} has unknown member(s): ${pyrepr(unknown)}`);
  return obj;
}

/** §5: layout is an object; `nodes` maps names to strict {x, y} int pairs. */
function validateLayoutShape(layout: JsonValue): JsonObject {
// TA: gotcha: JS forbids unary minus before ** (Python allows -10**15) — port as -1e15; first GREEN run 2026-08-23 failed collection on this (esbuild Unexpected '**'). Also: JS collapses 1.0===1, so integral-float acceptance (version/tokens) differs from Python io.py strict-int version check — documented in module docstring caveats (A2-class, outside pinned matrix).
  if (!isObject(layout)) {
    throw new SchemaValidationError(`'layout' must be an object, got ${pyrepr(layout)}`);
  }
  const nodes = layout["nodes"];
  if (nodes !== undefined) {
    if (!isObject(nodes)) {
      throw new SchemaValidationError(`'layout.nodes' must be an object, got ${pyrepr(nodes)}`);
    }
    for (const [nodeName, pos] of Object.entries(nodes)) {
      const p = exactKeys(pos, new Set(["x", "y"]), `layout.nodes[${pyrepr(nodeName)}]`);
      requireSchema("x" in p && "y" in p, `layout.nodes[${pyrepr(nodeName)}] requires members 'x' and 'y'`);
      asInt(p["x"], `layout.nodes[${pyrepr(nodeName)}].x`, -1e15);
      asInt(p["y"], `layout.nodes[${pyrepr(nodeName)}].y`, -1e15);
    }
  }
  return layout;
}

function sortedCodePoint(items: string[]): string[] {
  return [...items].sort(compareCodePoints);
}

function validate(doc: JsonValue): [PlaceItem[], TransitionItem[], ArcItem[], JsonValue | null] {
  if (!isObject(doc)) {
    throw new FormatSyntaxError(`Document must be a JSON object, got ${pyrepr(doc)}`);
  }

  // format family first, then version (error precedence per module docstring).
  if (!("format" in doc)) throw new SchemaValidationError("Missing required member 'format'");
  if (typeof doc["format"] !== "string") {
    throw new SchemaValidationError(`'format' must be a string, got ${pyrepr(doc["format"])}`);
  }
  if (doc["format"] !== FORMAT_ID) {
    throw new UnknownFormatError(`Unknown format: ${pyrepr(doc["format"])} (expected ${pyrepr(FORMAT_ID)})`);
  }
  if (!("version" in doc)) throw new SchemaValidationError("Missing required member 'version'");
  const version = doc["version"];
  if (typeof version === "boolean" || typeof version !== "number" || !Number.isInteger(version)) {
    throw new SchemaValidationError(`'version' must be an integer, got ${pyrepr(version)}`);
  }
  if (version !== FORMAT_VERSION) {
    throw new UnsupportedVersionError(`Unsupported version: ${version} (this loader speaks v${FORMAT_VERSION})`);
  }

  const unknown = Object.keys(doc).filter((k) => !TOP_LEVEL_KEYS.has(k)).sort(compareCodePoints);
  requireSchema(unknown.length === 0, `Unknown top-level member(s): ${pyrepr(unknown)}`);
  for (const key of ["places", "transitions", "arcs"] as const) {
    requireSchema(key in doc, `Missing required member ${pyrepr(key)}`);
    requireSchema(Array.isArray(doc[key]), `${pyrepr(key)} must be an array, got ${pyrepr(doc[key])}`);
  }

  const places: PlaceItem[] = [];
  (doc["places"] as JsonValue[]).forEach((raw, i) => {
    const p = exactKeys(raw, new Set(["name", "tokens"]), `places[${i}]`);
    requireSchema("name" in p && "tokens" in p, `places[${i}] requires members 'name' and 'tokens'`);
    places.push({
      name: asName(p["name"], `places[${i}].name`),
      tokens: asInt(p["tokens"], `places[${i}].tokens`, 0),
    });
  });
  const transitions: TransitionItem[] = [];
  (doc["transitions"] as JsonValue[]).forEach((raw, i) => {
    const t = exactKeys(raw, new Set(["name"]), `transitions[${i}]`);
    requireSchema("name" in t, `transitions[${i}] requires member 'name'`);
    transitions.push({ name: asName(t["name"], `transitions[${i}].name`) });
  });
  const arcs: ArcItem[] = [];
  (doc["arcs"] as JsonValue[]).forEach((raw, i) => {
    const a = exactKeys(raw, new Set(["source", "target", "weight"]), `arcs[${i}]`);
    requireSchema(
      "source" in a && "target" in a && "weight" in a,
      `arcs[${i}] requires members 'source', 'target', 'weight'`,
    );
    arcs.push({
      source: asName(a["source"], `arcs[${i}].source`),
      target: asName(a["target"], `arcs[${i}].target`),
      weight: asInt(a["weight"], `arcs[${i}].weight`, 1),
    });
  });
  const layout = "layout" in doc ? validateLayoutShape(doc["layout"]) : null;

  const placeNames = places.map((p) => p.name);
  const transitionNames = transitions.map((t) => t.name);
  const pset = new Set(placeNames);
  const tset = new Set(transitionNames);
  const dupPlaces = sortedCodePoint([...pset].filter((n) => placeNames.filter((x) => x === n).length > 1));
  const dupTransitions = sortedCodePoint([...tset].filter((n) => transitionNames.filter((x) => x === n).length > 1));
  const inBoth = sortedCodePoint([...pset].filter((n) => tset.has(n)));
  if (placeNames.length !== pset.size || transitionNames.length !== tset.size || inBoth.length > 0) {
    throw new SemanticValidationError(
      "V1: names must be unique across places ∪ transitions" +
        ` (duplicate place(s): ${pyrepr(dupPlaces)},` +
        ` duplicate transition(s): ${pyrepr(dupTransitions)},` +
        ` in both: ${pyrepr(inBoth)})`,
    );
  }
  const allNames = new Set([...pset, ...tset]);
  arcs.forEach((a, i) => {
    if (!allNames.has(a.source) || !allNames.has(a.target)) {
      throw new SemanticValidationError(
        `V2: arcs[${i}] endpoint(s) do not name an existing node: ${pyrepr(a.source)} -> ${pyrepr(a.target)}`,
      );
    }
    const sIsP = pset.has(a.source);
    const tIsP = pset.has(a.target);
    const sIsT = tset.has(a.source);
    const tIsT = tset.has(a.target);
    if (!((sIsP && tIsT) || (sIsT && tIsP))) {
      throw new SemanticValidationError(
        `V3: arcs[${i}] must connect a place and a transition: ${pyrepr(a.source)} -> ${pyrepr(a.target)}`,
      );
    }
  });
  // Pair identity via JSON encoding (injective for string pairs — no separator collisions).
  const pairs = arcs.map((a) => JSON.stringify([a.source, a.target]));
  const dupes = sortedCodePoint([...new Set(pairs.filter((p, idx) => pairs.indexOf(p) !== idx))]);
  if (pairs.length !== new Set(pairs).size) {
    throw new SemanticValidationError(`V4: duplicate arc(s) (source, target): ${pyrepr(dupes)}`);
  }
  // V6: unknown layout.nodes names are ignored, not errors (no check).
  return [places, transitions, arcs, layout];
}

/** FORMAT.md §7 construction algorithm. */
export function buildNet(places: PlaceItem[], transitions: TransitionItem[], arcs: ArcItem[]): PetriNet {
  const net = new PetriNet();
  for (const p of places) net.addPlace(p.name, p.tokens);
  for (const t of transitions) net.addTransition(t.name);
  for (const a of arcs) {
    if (net.places.has(a.source)) {
      net.addInput({ place: a.source, transition: a.target, weight: a.weight });
    } else {
      net.addOutput({ transition: a.source, place: a.target, weight: a.weight });
    }
  }
  return net;
}

// ---------------------------------------------------------------------------
// Public load API
// ---------------------------------------------------------------------------

/** Parse + validate a petri-net-json v1 document (levels 1–2, §6). */
export function documentFromJson(text: string): PetriNetDocument {
  if (typeof text !== "string") {
    throw new FormatSyntaxError(`Expected JSON text (string), got ${typeof text}`);
  }
  const [places, transitions, arcs, layout] = validate(parseJsonStrict(text));
  return { net: buildNet(places, transitions, arcs), layout };
}

/** Like documentFromJson but returns only the net (layout dropped). */
export function netFromJson(text: string): PetriNet {
  return documentFromJson(text).net;
}

// ---------------------------------------------------------------------------
// Dump (canonical serialization, FORMAT.md §8)
// ---------------------------------------------------------------------------

/** §8.4: layout members sorted (code point); nodes sorted by name; x,y order. */
function canonicalLayout(layout: JsonObject): JsonObject {
  const out: JsonObject = {};
  for (const key of Object.keys(layout).sort(compareCodePoints)) {
    const value = layout[key];
    if (key === "nodes" && isObject(value)) {
      const nodes: JsonObject = {};
      for (const name of Object.keys(value).sort(compareCodePoints)) {
        const pos = value[name];
        nodes[name] = isObject(pos) && "x" in pos && "y" in pos ? { x: pos["x"], y: pos["y"] } : pos;
      }
      out[key] = nodes;
    } else {
      out[key] = value; // extension members: verbatim parsed value
    }
  }
  return out;
}

/** Serialize `net` (+ optional `layout`) to canonical bytes (§8). */
export function netToJson(net: PetriNet, layout?: JsonValue | null): string {
  const doc: JsonObject = {};
  doc["format"] = FORMAT_ID;
  doc["version"] = FORMAT_VERSION;
  doc["places"] = [...net.places].sort(compareCodePoints).map((p) => ({
    name: p,
    tokens: net.initialMarking.get(p)!,
  }));
  doc["transitions"] = [...net.transitions].sort(compareCodePoints).map((t) => ({ name: t }));
  const arcs: JsonObject[] = [];
  for (const t of net.transitions) {
    for (const [p, w] of net.inputs.get(t)!) arcs.push({ source: p, target: t, weight: w });
    for (const [p, w] of net.outputs.get(t)!) arcs.push({ source: t, target: p, weight: w });
  }
  arcs.sort((a, b) => compareCodePoints(a["source"] as string, b["source"] as string) || compareCodePoints(a["target"] as string, b["target"] as string));
  doc["arcs"] = arcs;
  if (layout !== undefined && layout !== null) {
    doc["layout"] = canonicalLayout(validateLayoutShape(layout));
  }
  return JSON.stringify(doc, null, 2) + "\n";
}
