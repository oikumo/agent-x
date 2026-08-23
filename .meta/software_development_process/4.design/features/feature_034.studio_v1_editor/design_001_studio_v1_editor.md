# Design 001 — feature_034.studio_v1_editor: v1 implementation blueprint

> Date: 2026-08-23 · Phase: Design · Sources: PROJECT.md scope LOCKED v1.1 (roadmap #3, D1–D10) + analysis_001 (port matrices, findings A1–A12) + `shared/petri-net/FORMAT.md` (LOCKED v1) + `src/agentx/model/petri_net/{model,io,errors}.py` (executable specs).
> Rule: Programming copies this doc; anything ambiguous here is resolved HERE, not in code.

---

## 1. Deliverable & definition of done

`tools/petri-net-studio/` — standalone Vite+React+TS app, pure browser (D1), zero agentx/harness imports (D4/D5). Done when:

1. `npm run build` produces static `dist/`;
2. Vitest green: engine model port (60 behaviors), io port (59 behaviors + 3 golden-bytes examples), store smoke tests;
3. walking skeleton in-browser: draw → edit tokens/weights → Simulate: click-to-fire with enabled highlighting → export → re-import identical canonical JSON;
4. `node scripts/check-independence.mjs` passes;
5. `harnessc check` clean with `tools` in root_allowlist; full agentx pytest suite untouched/green (no `src/` edits in this feature at all).

## 2. A-findings dispositions (analysis_001 → design PINs)

| # | PIN |
|---|---|
| A1 | Hand-rolled minimal JSON parser `parseJsonStrict(text)` inside `io.ts`: full JSON grammar (objects/arrays/strings+escapes/numbers incl. frac+exp/literals), per-object duplicate-key rejection → `FormatSyntaxError`, syntax errors → `FormatSyntaxError`. `JSON.parse` is never used by the loader. |
| A2 | Parsed objects = plain JS objects; **documented caveat**: integer-like keys inside layout *extension values* reorder vs Python (deferred; v1-pinned surface + golden examples unaffected). Noted in `io.ts` docstring. |
| A3 | All sorts use a **code-point comparator** `compareCodePoints(a,b)` (compare via `[...str]` code-point sequences), never JS default sort. Used for: placeOrder/transitionOrder, enabled list, dump arrays, layout member/node ordering. Spec §8.5 UTF-16-equivalence note = erratum candidate, surfaced to user (no spec edit — LOCKED). |
| A4 | Dump = `canonicalStringify` built on `JSON.stringify(value, null, 2)` applied to an object constructed in pinned member order, + `"\n"`. Integers only on the pinned surface; extension floats = A2 caveat. |
| A5 | TS arc API uses **named object args**: `addInput({place, transition, weight?})`, `addOutput({transition, place, weight?})`. The Python positional-order trap is structurally impossible. |
| A6 | Integer validation helper `asInt(value, what, min)`: `typeof === "boolean"` → Schema error; `typeof === "number" && Number.isInteger` → ok (integral floats normalize via `1.0` being `=== 1` in JS — no separate float class exists); else Schema error; then `< min` check. Model-side same shape → `ValueError`. |
| A7 | `errors.ts`: `class PetriNetError extends Error`; `InvalidModelError`, `UnknownPlaceError`, `UnknownTransitionError`, `TransitionNotEnabledError` extend it; `DuplicatePlaceError`, `DuplicateArcError` extend `InvalidModelError`; **`class ValueError extends Error` — NOT a PetriNetError** (parity with Python). io errors in `io.ts`: `PetriNetFormatError extends PetriNetError` + 5 subclasses. `error.name` set to class name in each constructor (minification-safe discrimination via `instanceof`). |
| A8 | **Document-model-first UI**: editor state = `NetDocument` (format-shaped, editable: add/remove/rename); engine `PetriNet` derived via memoized `buildNet` (FORMAT §7 algorithm, shared with io.ts). Engine stays a pure add-only port. |
| A9 | **Two modes**: `edit` (structure + M0 token editing; simulation off) / `simulate` (structure locked; live `marking: number[]` from M0; click-to-fire; reset). Entering simulate snapshots `initialMarkingTuple()`; entering edit discards it. |
| A10 | Before any `tools/` file exists: add `tools` to `@var root_allowlist` in `.meta/META_HARNESS.omt` + `uv run scripts/omt/harnessc.py build` (harness-surface: one edit per file per e2e receipt; the allowlist line is the single edit). |
| A11 | **TDD = manual red→green under Vitest.** Two cycles (model, io): write the full behavior spec file → `npx vitest run` → paste RED summary into test report → implement → GREEN summary. `omt_tdd` is pytest-shaped; the mismatch is declared in the Programming phase scope. |
| A12 | Shared examples load via `import doc from "../../../shared/petri-net/examples/<name>.json?raw"` with `server.fs.allow: ["../.."]` in `vite.config.ts`; Vitest reads them via `fs.readFileSync(new URL(...))`. Independence check = specifier scan (§8). |

## 3. Repository layout (all new; nothing existing touched)

```
tools/petri-net-studio/
├── package.json            # scripts: dev/build/test/check-independence; no publish
├── tsconfig.json           # strict, bundler moduleResolution, DOM libs
├── vite.config.ts          # @vitejs/plugin-react, server.fs.allow, vitest config (environment jsdom for ui tests)
├── index.html
├── src/
│   ├── engine/
│   │   ├── errors.ts       # §4 — pure TS, no imports
│   │   ├── model.ts        # §5 — imports errors.ts only
│   │   └── io.ts           # §6 — imports errors.ts, model.ts only
│   ├── state/
│   │   ├── document.ts     # NetDocument type + ops (add/remove/rename/set tokens/weight), pure functions
│   │   └── store.ts        # zustand store (§7)
│   ├── ui/
│   │   ├── App.tsx         # toolbar (mode toggle, import/export, examples, reset) + canvas + inspector
│   │   ├── flow.ts         # NetDocument+marking+positions → React Flow nodes/edges (pure)
│   │   ├── PlaceNode.tsx   # circle, name, token count
│   │   ├── TransitionNode.tsx  # bar/rect, name; enabled style in simulate mode
│   │   └── Inspector.tsx   # selection panel: place tokens (edit mode), arc weight, node names
│   ├── examples.ts         # ?raw imports of the 3 shared examples + loader map
│   ├── main.tsx
│   └── styles.css
├── tests/
│   ├── engine/model.test.ts    # 62 behaviors (§9.1)
│   ├── engine/io.test.ts       # 59 behaviors + golden bytes (§9.2)
│   ├── engine/examples.test.ts # 3 examples: load → enabled sets → canonical bytes round-trip
│   └── state/store.test.ts     # document ops + mode transitions + fire/reset smoke
└── scripts/
    └── check-independence.mjs  # §8
```

## 4. `errors.ts` — full content pin

```ts
export class PetriNetError extends Error { constructor(m: string){ super(m); this.name="PetriNetError"; } }
export class InvalidModelError extends PetriNetError { /* name */ }
export class DuplicatePlaceError extends InvalidModelError { /* name */ }
export class DuplicateArcError extends InvalidModelError { /* name */ }
export class UnknownPlaceError extends PetriNetError { /* name */ }
export class UnknownTransitionError extends PetriNetError { /* name */ }
export class TransitionNotEnabledError extends PetriNetError { /* name */ }
export class ValueError extends Error { /* name="ValueError"; NOT PetriNetError (A7) */ }
```

## 5. `model.ts` — API pin (semantics = `model.py` exactly)

```ts
import { DuplicateArcError, DuplicatePlaceError, PetriNetError, InvalidModelError,
         TransitionNotEnabledError, UnknownPlaceError, UnknownTransitionError, ValueError }
  from "./errors.js";

export type Marking = readonly number[];   // tuple[int, ...] equivalent (immutable by convention)

export class PetriNet {
  readonly places: Set<string>;
  readonly transitions: Set<string>;
  readonly inputs: Map<string, Map<string, number>>;    // transition -> {place: weight}
  readonly outputs: Map<string, Map<string, number>>;
  marking: Map<string, number>;                          // live
  readonly initialMarking: Map<string, number>;          // M0

  addPlace(name: string, tokens = 0): void       // empty name→ValueError; bad tokens→ValueError (bool/non-int/<0); dup→DuplicatePlaceError
  addTransition(name: string): void              // empty→ValueError; dup→ValueError (F4 asymmetry pinned)
  addInput({place, transition, weight = 1}): void    // A5 object args
  addOutput({transition, place, weight = 1}): void   // validation: place before transition (test pins), weight pos-int
  get placeOrder(): string[]                     // sorted code-point (A3 comparator)
  get transitionOrder(): string[]
  get placeIndex(): Map<string, number>
  currentMarking(): number[]                     // tuple over placeOrder
  initialMarkingTuple(): number[]
  markingToDict(m: Marking): Map<string, number> // length→ValueError, negative→ValueError (order pinned)
  isEnabledAt(m: Marking, t: string): boolean    // unknown t → UnknownTransitionError; marking validation propagates
  enabledTransitionsAt(m: Marking): string[]     // transitionOrder filtered
  fireMarking(m: Marking, t: string): number[]   // PURE; precedence: UnknownTransition → marking ValueError → TransitionNotEnabled; inputs then outputs
  fire(t: string): void                          // live = markingToDict(fireMarking(current, t)); unchanged on error
  reset(): void                                  // marking = copy of initialMarking
  preSet(node: string): Set<string>              // transition→inputs keys; place→producers; ambiguous→InvalidModelError; unknown→PetriNetError
  postSet(node: string): Set<string>             // transition→outputs keys; place→consumers; same dispatch
}
```

Integer check helper (model-side): `isInt(x): x is number ⇔ typeof x === "number" && Number.isInteger(x)`; boolean values fail `typeof` → `ValueError` (A6). Messages copied from Python strings ("Place name cannot be empty", "Token count must be a non-negative integer", "Arc weight must be a positive integer", "Marking length does not match place count", "Marking contains a negative token count", error-class constructors carry the offending name like Python).

## 6. `io.ts` — API pin (semantics = `io.py` exactly)

```ts
export const FORMAT_ID = "petri-net-json";
export const FORMAT_VERSION = 1;

export class PetriNetFormatError extends PetriNetError { }
export class FormatSyntaxError extends PetriNetFormatError { }
export class UnknownFormatError extends PetriNetFormatError { }
export class UnsupportedVersionError extends PetriNetFormatError { }
export class SchemaValidationError extends PetriNetFormatError { }
export class SemanticValidationError extends PetriNetFormatError { }

export type JsonValue = null | boolean | number | string | JsonValue[] | { [k: string]: JsonValue };
export interface PetriNetDocument { net: PetriNet; layout: JsonValue | null }  // layout verbatim (A2 caveat)

export function documentFromJson(text: string): PetriNetDocument
export function netFromJson(text: string): PetriNet
export function netToJson(net: PetriNet, layout?: JsonValue | null): string   // canonical §8 bytes
export function buildNet(places, transitions, arcs): PetriNet                 // §7 algorithm; exported for the store (A8)
```

- **Loader**: `parseJsonStrict` (A1) → `_validate(doc)` mirroring io.py line-for-line: doc-is-object (else FormatSyntaxError) → format present/string/value → version present/int/value → unknown top-level members → required arrays → per-item exact-keys + required members + `asName`/`asInt` → layout shape (object; `nodes` object; positions exact `{x,y}` ints; unknown layout members kept) → **V1** (dup places / dup transitions / P∩T, message lists each) → per-arc **V2** (endpoints exist) then **V3** (P↔T), in arc order → **V4** duplicate (source,target) pairs (message lists dupes) → V6 no-op. Error class precedence per analysis §4. Messages ported verbatim incl. `V1:`–`V4:` prefixes.
- **Non-string input** to `documentFromJson` → `FormatSyntaxError` (parity with Python type check).
- **Dumper**: doc built in pinned literal order `{format, version, places, transitions, arcs[, layout]}`; places/transitions sorted by name (A3 comparator); arcs collected from inputs/outputs maps then sorted by (source, target); layout canonicalized (own members sorted code-point; `nodes` sorted by name; positions re-emitted `{x, y}`; extension values verbatim); tokens from `initialMarking`; `JSON.stringify(doc, null, 2) + "\n"`.
- `parseJsonStrict` implementation: recursive-descent, ~120 LOC, single-pass; rejects trailing garbage, leading zeros (`01`), `+1`, `.5`, `NaN`/`Infinity`, single quotes, trailing commas, unescaped control chars in strings, bad `\u` escapes → all `FormatSyntaxError`. Numbers → JS `number` (frac/exp allowed at JSON level; domain checks reject non-integers later — parity with Python accepting `1.0` then normalizing). Objects built with duplicate-key rejection (A1). Surrogate pair escapes joined; **lone surrogates accepted** (Python `json.loads` accepts them; parity) — canonical dump re-escapes them (ES2019 stringify) so writer output stays well-formed.

## 7. Store & UI pin (v1 walking skeleton)

```ts
// state/document.ts — editable, format-shaped (A8)
interface NetDocument {
  places: { name: string; tokens: number }[];
  transitions: { name: string }[];
  arcs: { source: string; target: string; weight: number }[];
}
// pure ops: addPlace(doc,pos)/addTransition → auto-name p1,p2,…/t1,t2,… (first free index)
// removeNode (cascades arcs), removeArc, renameNode (rewires arcs; V1-checked against collision),
// setTokens(place,n≥0), setWeight(arc,n≥1), toNet(doc) = buildNet(...)  [memoized by doc identity]

// state/store.ts (zustand)
{
  doc: NetDocument; positions: Record<string,{x:number;y:number}>; mode: "edit"|"simulate";
  marking: number[] | null;            // simulate only, tuple over placeOrder
  selection: {kind:"place"|"transition"|"arc", id:string} | null;
  importError: string | null;
  // actions: node/arc ops (delegating to document.ts), setMode, fireTransition(t),
  // resetMarking(), importJson(text) (documentFromJson → doc+positions from layout.nodes,
  //   missing positions → circle auto-layout radius 120; error → importError string, state unchanged),
  // exportJson(): string (netToJson(toNet(doc), {nodes: integer positions})), loadExample(name)
}
```

- **flow.ts** (pure): places → circular `PlaceNode` (name + live token count — edit mode shows M0, simulate shows marking tokens); transitions → `TransitionNode` (enabled in simulate ⇒ distinct style: green border + shadow; disabled ⇒ muted); arcs → edges with arrow marker + weight label (always shown, FORMAT explicit-always). Click transition in simulate ⇒ `fireTransition`; click disabled ⇒ no-op.
- **Edit gestures**: palette buttons "＋ Place" / "＋ Transition" (next click on canvas places it — or at center if dropped via button); drag moves (positions snapped to integers); connect drag creates arc weight 1 (reject place→place / transition→transition with a transient hint — V3); select opens Inspector: rename (V1 collision check), place tokens (edit mode), arc weight ≥ 1, delete buttons. Simulate mode locks all structure edits (toolbar toggle only + reset + fire).
- **Import/Export**: textarea dialog (paste) + file picker; export shows canonical text with copy + download (`net.json`). "Examples" menu loads the 3 shared examples (A12).
- Styling: plain CSS, dark-neutral minimal; no UI kit (v1).

## 8. Independence check — `scripts/check-independence.mjs`

Node script (no deps): walks `src/**/*.ts(x)`, regexes `import … from "<spec>"` / `import("<spec>")`; FAILS if a specifier: starts with `.` and resolves outside `tools/petri-net-studio/src` (exception: none — shared examples enter ONLY via `src/examples.ts` `?raw` imports, which the script allowlists by exact specifier substring `shared/petri-net/examples/`), or matches `agentx|scripts/|\.meta/|\.projects/|tests/`. Exit 1 with offending list. Wired as `npm run check-independence`; also asserted by a Vitest test spawning it (so CI-less `npm test` covers it).

## 9. Test plan (Vitest; manual red→green per A11)

### 9.1 `tests/engine/model.test.ts` — 60 behaviors (1:1 port of `test_model.py` classes)

TestBuild (3) · TestDuplicateNames (3) · TestAddValidation (2 + 5 params) · TestArcs (8 + 8 params) · TestEnabledness (7) · TestFireMarking (7) · TestFireAndReset (4) · TestSelfLoop (1) · TestParallelTransitions (1) · TestMarkingAccessors (5) · TestStructuralQueries (4) · TestEmptyNet (2). Params via `it.each`. Assertions on error **class via instanceof** + message substrings.

### 9.2 `tests/engine/io.test.ts` — 59 behaviors (1:1 port of `test_io.py`)

canonical dump shape · byte-identity round-trips · typed-error matrix (class + precedence + rule ids) · integral-float normalization · bool rejection · layout verbatim/extensions/V6 · duplicate-key rejection · schema cross-checks. `tests/engine/examples.test.ts`: for each of the 3 shared examples — file bytes load cleanly → enabled set at M0 equals expected (hello: [t1]; producer_consumer: [produce]; weighted_reaction: [consume_h2_o2] — verify against io.py behavior at Programming time) → `netToJson(doc.net, doc.layout)` === file bytes.

### 9.3 `tests/state/store.test.ts` — smoke

document ops validity (auto-naming, rename collision → rejected, cascade delete), mode transitions (simulate snapshots M0; edit discards), fire updates marking + enabled set, reset, import error leaves state untouched, export→import round-trip equality of doc.

### 9.4 Evidence protocol

RED: `npx vitest run tests/engine/model.test.ts` after writing spec against stub → summary pasted into test report. GREEN: full `npx vitest run` output. Same for io cycle. (Substitute for `omt_tdd` receipts — A11.)

## 10. Programming sequence (copy order)

1. **A10 first**: `.meta/META_HARNESS.omt` root_allowlist `+ tools` → `uv run scripts/omt/harnessc.py build` → `harnessc check` clean.
2. `omt_phase{task_type:"major_feature", phase:"Programming", …}` — scope declares the Vitest/omt_tdd mismatch.
3. Scaffold `tools/petri-net-studio/` (hand-written package.json etc. — `npm create vite` is interactive): deps `react react-dom @xyflow/react zustand`; dev `typescript vite @vitejs/plugin-react vitest jsdom @testing-library/react @testing-library/jest-dom @types/react @types/react-dom`. `npm install` (network confirmed OK 2026-08-23: npm 11.11.0, node v24.14.1). `.gitignore` for `node_modules/ dist/`.
4. RED cycle 1: `errors.ts` (full) + `model.ts` stub + `tests/engine/model.test.ts` full spec → RED evidence → implement `model.ts` → GREEN.
5. RED cycle 2: `io.ts` stub + io/examples tests → RED evidence → implement (incl. `parseJsonStrict`) → GREEN.
6. UI: document.ts + store.ts (+ store tests green) → flow.ts + nodes + Inspector + App + styles → manual smoke via `npm run dev` (user-verifiable) — UI covered by store tests + build, no component-test mandate in v1.
7. `check-independence.mjs` → `npm run check-independence` green → `npm run build` → `dist/` exists, `index.html` + assets; smoke-serve `dist/` statically.
8. Test report `6.testing/features/feature_034.studio_v1_editor/test_report.md` (RED/GREEN evidence, build output, independence output) → FEATURE.md/PLAN.md checkboxes → `omt_complete`.

## 11. Explicit non-goals (locked scope reminders)

No analysis dashboard (#4), no reachability explorer (#5), no conformance runner (#5), no coverability, no current-marking snapshot in exports, no backend, no npm publish, no `src/` edits whatsoever, no changes to `shared/` (contract LOCKED), no rename of the A3 spec erratum (surface only).
