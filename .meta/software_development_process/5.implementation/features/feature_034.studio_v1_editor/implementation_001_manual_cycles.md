# Implementation notes 001 — feature_034.studio_v1_editor manual red→green cycles

> Date: 2026-08-23 · Phase: Programming · Design: `4.design/features/feature_034.studio_v1_editor/design_001_studio_v1_editor.md` (+ `operation_spec_001`) · Analysis: `3.analysis/features/feature_034.studio_v1_editor/analysis_001_port_sources.md`

## Cycle log (4 cycles, manual red→green under Vitest — A11)

| Cycle | Test file | Src written | Behaviors | Result |
|---|---|---|---|---|
| 1 | `tests/engine/model.test.ts` | `src/engine/errors.ts` (full) + `src/engine/model.ts` | 60 model behaviors (1:1 port of `test_model.py` classes; params via `it.each`) | RED 60F → GREEN 60/60 |
| 2 | `tests/engine/io.test.ts` + `tests/engine/examples.test.ts` | `src/engine/io.ts` (incl. `parseJsonStrict`, A1) | 59 io behaviors (1:1 port of `test_io.py`) + 3 golden-bytes examples | RED 58F/4P → GREEN 122/122 (full suite) |
| 3 | `tests/state/store.test.ts` | `src/state/document.ts` + `src/state/store.ts` (+ `src/examples.ts`) | 47 store smoke behaviors (design §9.3) | RED 46F/1P → GREEN 169/169 (full suite) |
| 4 | `tests/independence.test.ts` | `scripts/check-independence.mjs` | 1 (independence script exists + passes via spawn) | RED 1F → GREEN 170/170 (full suite) |

Runner: `npx vitest` — **`omt_tdd` NOT used** (pytest-shaped; mismatch declared in the Programming phase scope per design A11). RED/GREEN command outputs pasted into `test_report.md` as the substitute receipts (design §9.4 evidence protocol).

## Decisions taken during the build

- **Design-gap: `addArc` op added to document.ts.** operation_spec_001's document.ts table omits an arc-creation op, but design §7 pins the connect-drag gesture → `addArc(doc, source, target)` (V2/V3/V4-checked, weight 1) so ALL doc mutation stays in pure ops (A8). TA-pinned in document.ts.
- **Design-gap: import ⇒ edit mode.** Op spec silent on mode after import → import lands in `edit` with marking cleared (fresh import = editing); store-level simulate lock (A9 "structure locked") implemented as a guard in EVERY mutating action (a toolbar hint alone is insufficient). TA-pinned in store.ts.
- **Build breakers fixed at the first-ever `tsc --noEmit`** (pending as part of `npm run build` until late-Programming): io.ts `validateLayoutShape` return widened to `JsonObject` (TA-consulted); store.ts `Point`→`JsonObject` fresh literal in `exportJson`; `@types/node` devDep + tsconfig `types: ["vite/client", "node"]` (engine tests used `node:fs` since cycle 2 — tsc had never run); check-independence.mjs docstring contained `src/**/*.ts` whose `**/` closed the block comment → SyntaxError (TA-pinned).
- **jsdom rewrites `import.meta.url`** → `// @vitest-environment node` docblock required atop the 3 engine test files AND `tests/independence.test.ts` (TA-pinned both places; discovered cycle 2 RED).
- **First cycle-2 GREEN attempt failed collection**: `-10 ** 15` (Python-ism; JS forbids unary minus before `**`) → `-1e15` (TA-pinned in io.ts). Never skip the GREEN run.
- **Minor pins**: positions snap to integers on WRITE (add/move; design §7); selection cleared on mode switch + node/arc removal; `loadExample` unknown name → `importError`, returns false.
- **No component tests** (design §10 step 6): UI layer covered by store tests + `tsc` + `vite build`; manual in-browser smoke remains user-verifiable (not mandated in v1).
- **TA thoughts pinned (8 total)**: io.ts (unary-`**` + integral-float caveats), model.ts (code-point sort rationale), io.test.ts (node-env), check-independence.mjs (`**/`-in-comment), document.ts (addArc design-gap why), store.ts (store-level lock + partial-merge reset why), independence.test.ts (node-env), App.tsx (controlled-through-store why).

## Verification evidence

- Full Vitest suite after every cycle; final: **170 passed (5 files)** — 122 engine (60 model + 59 io + 3 golden) + 47 store + 1 independence.
- Golden byte-identity: TS `netToJson(documentFromJson(example))` === file bytes for all 3 `shared/petri-net/examples/` — cross-impl byte parity WITHOUT Python.
- ajv Draft-2020-12 cross-checks: 3 examples schema-valid; 5 bad docs rejected by both schema and io.
- `npx tsc --noEmit` clean · `node scripts/check-independence.mjs` → `independence OK: 12 files scanned, 36 imports checked`.
- Zero `src/` (agentx) edits at any point; zero `shared/` edits (contract LOCKED).
