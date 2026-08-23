# Operation Spec 001 — feature_034.studio_v1_editor: public operation contracts

> Phase: Design companion to design_001. Each operation: signature · pre · post/effects · errors. Semantics = the Python sources (`model.py`/`io.py`) exactly; this spec is the caller-facing TS contract. `M` = marking (`readonly number[]`) over `placeOrder`.

## engine/errors.ts

| Op | Contract |
|---|---|
| `PetriNetError` → `InvalidModelError` → `DuplicatePlaceError`, `DuplicateArcError`; `PetriNetError` → `UnknownPlaceError`, `UnknownTransitionError`, `TransitionNotEnabledError` | class hierarchy mirrors `errors.py`; each sets `name` to its class name |
| `ValueError extends Error` | NOT a `PetriNetError` (Python parity, A7) |

## engine/model.ts — `class PetriNet`

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `addPlace(name, tokens=0)` | — | place added; `marking`/`initialMarking` set | `ValueError` empty name / bad tokens (bool, non-integer, <0); `DuplicatePlaceError` |
| `addTransition(name)` | — | transition added; empty input/output maps | `ValueError` empty name / duplicate (F4 asymmetry) |
| `addInput({place, transition, weight=1})` | place, transition exist | `inputs[transition][place]=weight` | `UnknownPlaceError` (checked first), `UnknownTransitionError`, `ValueError` weight non-int/bool/≤0, `DuplicateArcError` |
| `addOutput({transition, place, weight=1})` | place, transition exist | `outputs[transition][place]=weight` | same set (object args — A5) |
| `isEnabledAt(M, t) → boolean` | t exists; M well-formed | AND over inputs (vacuous true if none) | `UnknownTransitionError`, `ValueError` malformed M |
| `enabledTransitionsAt(M) → string[]` | M well-formed | enabled transitions, code-point sorted | `ValueError` malformed M |
| `fireMarking(M, t) → number[]` | t exists; M well-formed | successor marking; PURE (net + M untouched); atomic | precedence: `UnknownTransitionError` → `ValueError` → `TransitionNotEnabledError` |
| `fire(t) → void` | t enabled at live marking | live marking := fireMarking result (re-validated) | same set; live marking unchanged on error |
| `reset() → void` | — | live marking := copy of M0 | — |
| `currentMarking() / initialMarkingTuple() → number[]` | — | tuple over `placeOrder` (code-point sorted, A3) | — |
| `markingToDict(M) → Map<string,number>` | len(M)=|places|, all ≥0 | dict view of M | `ValueError` length (first) / negative |
| `placeOrder / transitionOrder / placeIndex` | — | code-point sorted arrays / index map (recomputed getters) | — |
| `preSet(node) / postSet(node) → Set<string>` | node is place XOR transition | neighbors (place: producers/consumers; transition: inputs/outputs) | `InvalidModelError` ambiguous; `PetriNetError` unknown |

## engine/io.ts

| Op | Pre | Post / returns | Errors (precedence pinned) |
|---|---|---|---|
| `documentFromJson(text) → {net, layout}` | text is string | parsed + validated doc; net built per FORMAT §7; `layout` verbatim parsed value or `null` | `FormatSyntaxError` (non-string, bad JSON, duplicate key, non-object doc) → `UnknownFormatError` → `UnsupportedVersionError` → `SchemaValidationError` (shape/types/domains) → `SemanticValidationError` (V1→V2/V3→V4, ids in messages; V6 no-op) |
| `netFromJson(text) → PetriNet` | as above | net only (layout dropped) | as above |
| `netToJson(net, layout?) → string` | valid net; layout shape-valid if given | **canonical §8 bytes**: pinned member order, code-point-sorted arrays, `tokens` from M0, minimal escaping, single trailing LF | `SchemaValidationError` bad layout shape |
| `buildNet(places, transitions, arcs) → PetriNet` | validated item lists | net per FORMAT §7 (arc direction by source membership) | model errors propagate (shouldn't occur post-validation) |
| `parseJsonStrict(text) → JsonValue` (internal) | — | full JSON grammar; duplicate object keys rejected | `FormatSyntaxError` all syntax/duplicate failures |
| `FORMAT_ID` / `FORMAT_VERSION` | — | `"petri-net-json"` / `1` | — |

## state/document.ts + store.ts (UI-internal)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `addPlace(doc) / addTransition(doc)` | — | new doc; auto-name `p<n>`/`t<n>` first free index (V1-safe) | — |
| `removeNode(doc, name)` | name exists | node + incident arcs removed | — |
| `removeArc(doc, source, target)` | arc exists | arc removed | — |
| `renameNode(doc, old, next)` | old exists; next non-empty, not colliding (V1) | node renamed; arcs rewired | rejected (returns unchanged + flag) on collision |
| `setTokens(doc, place, n)` / `setWeight(doc, arc, n)` | n ≥ 0 / n ≥ 1 | M0 tokens / arc weight updated | rejected otherwise |
| `toNet(doc) → PetriNet` | doc valid | memoized `buildNet` (A8) | — |
| `store.setMode("edit"\|"simulate")` | — | simulate: `marking := initialMarkingTuple()`; edit: `marking := null` | — |
| `store.fireTransition(t)` | simulate mode; t enabled | `marking := fireMarking(marking, t)`; disabled click = no-op | engine errors propagate (UI guards by enabled set) |
| `store.resetMarking()` | simulate mode | marking := M0 | — |
| `store.importJson(text)` | — | success: doc+positions replaced (layout.nodes → positions; missing → circle auto-layout); failure: state unchanged, `importError` = `<ErrorClass>: <message>` | captured, not thrown |
| `store.exportJson() → string` | — | `netToJson(toNet(doc), {nodes: integer positions})` — canonical bytes | — |
| `store.loadExample(name)` | name ∈ {hello, producer_consumer, weighted_reaction} | as importJson (shared example bytes) | — |

**Global invariants:** engine imports nothing but its own errors; io imports engine only; store/UI never bypass the engine for semantics (enabled sets, firing); all sorts code-point (A3); zero agentx/harness imports anywhere under `tools/petri-net-studio/src` (checked by `scripts/check-independence.mjs`).
