# Analysis 001 — feature_034.studio_v1_editor: port sources & reference matrices

> Date: 2026-08-23 · Phase: Analysis · Sources: `.sandbox/pause_2026-08-23.md` (resume doc), `shared/petri-net/FORMAT.md` (LOCKED v1), `src/agentx/model/petri_net/{model,io,errors}.py`, `tests/model/petri_net/{test_model,test_io}.py`, PROJECT.md scope LOCKED v1.1 (roadmap #3, D1–D10).
> Purpose: inventory what the TypeScript port must reproduce, with the traps that diverge silently. Design doc resolves each finding into a PIN.

---

## 1. Scope anchor (locked)

Roadmap #3 (PROJECT.md, LOCKED v1.1): `tools/petri-net-studio/` scaffold (Vite+React+TS+React Flow+Vitest per D2) — visual editor, token/weight editing, **TS model-layer port**, click-to-fire simulation, JSON import/export with validation, static build, independence lint check. Depends on #1 (format) ✅. Feature #2 (io.py) ✅ also shipped — its 59 tests are the io-port reference matrix.

v1 does **NOT** include: analysis (feature #4), reachability graph (feature #5), conformance vectors (feature #5 runner), exact-rational invariants (feature #4 — fraction arithmetic, TA gotcha in PROJECT.md).

## 2. Port sources (executable specifications)

| TS artifact | Python source | Reference test matrix | Behaviors |
|---|---|---|---|
| `src/engine/errors.ts` | `errors.py` (7 classes) | via model/io tests | hierarchy only |
| `src/engine/model.ts` | `model.py` (200 LOC) | `test_model.py` — **60 tests** | full model layer |
| `src/engine/io.ts` | `io.py` (326 LOC) | `test_io.py` — **59 tests** + golden bytes: `shared/petri-net/examples/*.json` | full io layer |

Golden-bytes contract (feature_032, FORMAT.md §8): TS `serialize(load(example))` must reproduce the 3 example files byte-exactly — cross-impl test without Python: `fs.readFile` + string compare in Vitest.

## 3. Model-layer behaviors to port (60 tests, from `test_model.py` collect)

- **Build**: sorted orders/markings; weighted arcs; default tokens 0.
- **Duplicate names**: duplicate place → `DuplicatePlaceError` (⊂ `InvalidModelError`); duplicate transition → **plain `ValueError`** (F4 asymmetry, pinned by test).
- **Add validation**: empty place/transition name → ValueError; bad token count rejected: `True`, `False` (bool before int!), `-1`, `1.5`; `[2]`-style non-number rejected.
- **Arcs**: unknown place/transition (place checked **before** transition); bad weight `0/-1/True/2.5` both directions; duplicate input/output arc rejected regardless of weight; `add_output` keyword-call pins arg order (§9 gotcha: `add_output(transition, place)` — swapped vs `add_input(place, transition)`).
- **Enabledness**: AND across inputs; no-input transition always enabled; zero-token place blocks weight-1; unknown transition raises; enabled list sorted; transitions-only net.
- **fire_marking**: successor + purity (input marking untouched); weighted successor; disabled → `TransitionNotEnabledError`; precedence: `UnknownTransitionError` → marking ValueError (length, then negative) → not-enabled.
- **fire/reset**: fire mutates live marking; fire error leaves live marking unchanged; reset restores M0; reset returns a copy (later `add_place` doesn't alias).
- **Edge cases**: self-loop enabled & neutral; parallel transitions distinct successors; empty net semantics; empty net unknown transition raises.
- **Marking accessors**: sorted orders; `place_index`; marking↔dict round-trip; length-mismatch/negative ValueErrors.
- **Structural queries** (`pre_set`/`post_set`): transition pre/post; place pre (producers)/post (consumers); unknown node → base error; ambiguous node (name in both) → `InvalidModelError`. *(Model permits place∩transition overlap; the format forbids it — but the TS engine ports the model, so the ambiguity path is ported too.)*

## 4. io-layer behaviors to port (59 tests, from `test_io.py`)

- **Load pipeline order** (typed-error precedence, module docstring): `FormatSyntaxError` (bad JSON / duplicate object key / non-object doc / non-str input) → L1 format family: missing/non-string `format` = Schema, wrong value = `UnknownFormatError` → version: missing/non-int = Schema, wrong value = `UnsupportedVersionError` → unknown top-level members = Schema → missing/non-array `places|transitions|arcs` = Schema → per-item shape (exact key sets, required members, name non-empty string, int domains) → L2: **V1** name uniqueness across P∪T → **V2** arc endpoints exist → **V3** arc connects P↔T (V2 before V3 per arc, in arc order) → **V4** duplicate (source,target) pairs → (V6: no check — unknown layout node names ignored). Rule ids `V1`–`V4` appear in messages.
- **Schema-`integer` semantics**: bool rejected before int; integral floats (`1.0`) normalized to int; non-integral rejected; domains: tokens ≥ 0, weight ≥ 1, version int, layout x/y int (wide min −10¹⁵).
- **Layout (§5)**: must be object; `nodes` maps names → strict `{x, y}` int pairs; **unknown layout members allowed + preserved verbatim** (extensions within a version); V6 non-node keys ignored; round-trip keeps layout byte-identical.
- **Dump (canonical §8)**: pinned member order (top: format, version, places, transitions, arcs, layout · Place: name, tokens · Transition: name · Arc: source, target, weight · position: x, y); arrays sorted code-point (places/transitions by name; arcs by (source, target)); layout members sorted code-point, nodes sorted by name, extension values verbatim; `tokens` from `initial_marking` (M0, never live marking); ends with exactly one LF; UTF-8 no BOM; minimal escaping (non-ASCII raw).
- **Document**: `document_from_json` returns `{net, layout}` (layout = parsed value verbatim or None); `net_from_json` drops layout.
- **Golden bytes**: 3 shared examples load → construct real nets with expected enabled sets → dump = file bytes.

## 5. Findings (traps the design must pin)

- **A1 — Duplicate JSON keys.** Python rejects via `object_pairs_hook`; JS `JSON.parse` is silent last-wins. TS needs its own parser path (hand-rolled minimal JSON parser with per-object key-set rejection → `FormatSyntaxError`). Also gives syntax-error control without depending on engine error strings.
- **A2 — Integer-like object keys reorder in JS.** JS own-key order = integer-like keys ascending, then string keys insertion order; Python preserves pure insertion order. Affects verbatim passthrough of `layout` *extension values* with keys like `"2"`. v1-pinned members never have such keys. Design pins plain JS objects + documented caveat (full parity would need pairs-preserving structures — deferred; irrelevant to the pinned surface and the 3 golden examples).
- **A3 — Code-point sort ≠ JS default sort for astral-plane strings.** FORMAT.md §8.5 declares "UTF-16 code-unit ≡ code-point for well-formed strings" — true for BMP, **false for supplementary characters** (U+10000+ start with high surrogate D800–DBFF < U+FFFF, so UTF-16 sorts them before U+FFFF; code points sort them after). Python `sorted()` = code points. Design pins a code-point comparator in TS (spec's primary rule wins; the UTF-16 equivalence note is a spec erratum candidate — surfaced to user, no spec edit without re-lock).
- **A4 — Canonical serialization equivalence.** `JSON.stringify(doc, null, 2) + "\n"` ≡ `json.dumps(doc, indent=2, ensure_ascii=False) + "\n"` for the pinned integer/string surface (verified by feature_032's 32 checks on the Python side). Numbers: v1 integers only → no float-format divergence; extension floats are the A2-class caveat. Lone surrogates: both escape (ES2019 well-formed stringify) — non-issue for well-formed strings.
- **A5 — `add_output` argument order.** Python: `add_input(place, transition)` vs `add_output(transition, place)` — swapped (§9 gotcha; test pins keyword call). TS API pins **object args** for both: `addInput({place, transition, weight?})`, `addOutput({transition, place, weight?})` — order trap structurally impossible.
- **A6 — Bool rejection.** Python `isinstance(x, bool)` before `int`. TS: `typeof x === "boolean"` rejects naturally when checking `typeof x === "number" && Number.isInteger(x)` — but error *types* must stay distinct (Schema vs ValueError class) and messages should carry the same rule content.
- **A7 — Error-type parity across a language gap.** Python `ValueError` is NOT a `PetriNetError`; typed errors are. TS pins a `ValueError` class extending `Error` (not `PetriNetError`) so catch-by-type parity holds in the ported tests.
- **A8 — Mutability/React impedance.** Engine `PetriNet` is mutable add-only (no remove/rename). An editor needs delete/rename. Design resolves: **document-model-first** — the editor edits a format-shaped document model; the engine net is *derived* (memoized buildNet per FORMAT §7) for semantics (enabled sets, firing). Engine stays a pure port.
- **A9 — M0 vs live marking in the UI.** Format is M0-only; simulation needs a live marking. Design pins Edit/Simulate modes: Edit mutates structure + M0; Simulate holds live marking (starts at M0), click-to-fire + reset; switching back discards live marking.
- **A10 — Harness root hygiene.** `@var root_allowlist` does NOT include `tools` → creating `tools/petri-net-studio/` trips `harnessc check` (cf. feature_027 stray-`sandbox/` error). Programming must first add `tools` to `META_HARNESS.omt` root_allowlist + `harnessc.py build` (harness-surface receipt discipline: one edit per file per e2e receipt).
- **A11 — TDD driver mismatch.** `omt_tdd` takes pytest node ids; this feature's runner is Vitest (`npx vitest`). Resolution (recorded at pause): manual red→green discipline — engine behaviors first, watch fail, implement, watch pass; outputs pasted as evidence into the test report; if `omt_tdd` auto-activation blocks Programming, declare the mismatch in the phase scope / `omt_skip{scope:"tests"}`.
- **A12 — Reading `shared/` from Vite.** Examples are data coupling (allowed, D5). Dev/build loading via Vite `?raw` imports requires `server.fs.allow` to include the repo root; tests read via `fs.readFile` relative to repo root. Independence check = static import-specifier scan (no `agentx`, `src/`, `scripts/`, `.meta/` imports in the app's `src/`), not a bundler rule.

## 6. v1 UI capability → implementation map (for design)

| Capability (locked scope) | Implementation |
|---|---|
| Add place/transition | palette buttons → node at canvas center/click; auto-names `p1..`, `t1..` (format V1 keeps uniqueness) |
| Drag nodes | React Flow `onNodesChange` → positions map (integer-snapped) |
| Arcs with weight | React Flow connect → document arc (weight 1 default); inspector edits weight ≥ 1; edge label shows weight |
| Token editing | Edit mode: place inspector edits M0 tokens; Simulate mode: read-only counts |
| Click-to-fire + enabled highlight | Simulate mode: `enabledTransitionsAt(marking)` styled; click fires `fireMarking`; reset button restores M0 |
| Import JSON | paste/upload → `documentFromJson` → document model + positions from `layout.nodes` (missing → simple auto-layout); typed error display (class + V-rule id) |
| Export JSON | canonical bytes from derived net + `layout.nodes` (editor always knows positions) → download/copy |
| Load shared examples | `?raw` imports of the 3 examples |
| Static build | `vite build` → `dist/`; no backend (D1) |
| Independence | `scripts/check-independence.mjs` scan + engine has zero React imports |
