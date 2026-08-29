# Implementation notes 001 — feature_035.studio_v2_analysis manual red→green cycles

> Date: 2026-08-29 · Phase: Programming · Design: `4.design/features/feature_035.studio_v2_analysis/design_001_studio_v2_analysis.md` · Analysis: `3.analysis/features/feature_035.studio_v2_analysis/analysis_001_analysis_port.md`

## Cycle log (manual red→green under Vitest — B11/A11 precedent)

| Cycle | Test file | Src written | Behaviors | Result |
|---|---|---|---|---|
| 1 | `tests/engine/fraction.test.ts` | `src/engine/fraction.ts` | 22 fraction behaviors (design §10.1: gcd/lcm math-gcd semantics, Fraction normalize + exact arithmetic) | RED 22F → GREEN 22/22 |
| 2 | `tests/engine/analysis.test.ts` | `src/engine/analysis.ts` | 38 analysis behaviors (1:1 port of `test_analysis.py` classes TestReachableMarkings→TestDeterminism) | RED 38F → GREEN 38/38 |
| 3 | `tests/engine/conformance.test.ts` | `scripts/generate-vectors.py` + `shared/petri-net/conformance/analysis-v1/*.json` | 8 vectors × all analysis APIs (deep-equal vs `expected`) | RED 1F (0 vectors) → GREEN 10/10 |
| 4 | `tests/state/store.test.ts` (additive) + UI | `src/state/store.ts` (additive) + `src/ui/AnalysisPanel.tsx` + `src/ui/App.tsx` + `src/styles.css` | maxStates/analysisVisible defaults + setters + mode independence (design §10.4) | RED → GREEN 52/52 (5 additive) · UI verified by tsc + build + preview smoke |

Runner: `npx vitest` — **`omt_tdd` NOT used** (pytest-shaped vs Vitest runner; mismatch declared in the Programming phase scope, design B11). RED/GREEN command outputs pasted into `test_report.md` as the substitute receipts (design §10.5 evidence protocol).

## Cycle 2 (analysis) details

- **RED**: `npx vitest run tests/engine/analysis.test.ts` → `Test Files 1 failed (1) · Tests 38 failed (38)` (stub "not implemented (RED stub)").
- **GREEN**: same cmd → `Test Files 1 passed (1) · Tests 38 passed (38)` (Duration ~0.6s).
- **Typecheck**: `npx tsc --noEmit` → clean (one unused-import fix in the test file: `type Marking` not needed).
- **Full suite after cycle**: `npx vitest run` → `Test Files 7 passed (7) · Tests 230 passed (230)` — 60 model + 59 io + 3 golden + 47 store + 22 fraction + 38 analysis.
- Port fidelity notes (per design §5):
  - `explore` copies Python `_explore` 1:1 (B3): FIFO via index-advanced array queue; truncation records edges to unvisited successors without enqueueing, finishes the current state's edges, then `break`.
  - `nullspace` + `_coprimeIntVector` are line-for-line Fraction ports (B2): Gauss–Jordan to FULL RREF; LCM-scale → gcd-content divide → negate-first-nonzero. Zero floats in the algebra path.
  - Deterministic ordering (B6): `markings`/`states`/`deadlocks`/SCC inner arrays sorted by `compareMarkings`; edges in `enabledTransitionsAt` order; SCC start nodes sorted; reverse-liveness stack sorted.
  - Tarjan skips edge targets outside `graph.states` (B7 — truncation-only dangling edges).
  - `reason` is always present (`null` when Python defaults None) so result deep-equality is exact (B5).

## Cycle 3 (conformance vectors) details

- **RED**: `npx vitest run tests/engine/conformance.test.ts` (vectors not yet generated) → `Test Files 1 failed (1) · Tests 1 failed (1)` ("generator has produced at least one vector").
- **GREEN**: `npx vitest run` → `Test Files 8 passed (8) · Tests 240 passed (240)` — 240 = 230 + 10 conformance (9 vectors + the non-empty guard).
- **Generator determinism**: two consecutive `uv run python tools/petri-net-studio/scripts/generate-vectors.py` runs are **byte-identical** (md5 across all 9 files; verified twice incl. after the TS `-0` fix).
- **`-0` parity bug (fixed)**: `weighted_reaction.json` place_invariants diverged `[1,-0,-2]` (TS) vs `[1,0,-2]` (Python). JS `-x` of `0` yields `-0`; Python `int()` canonicalizes `-0.0 → 0`; vitest `toEqual` distinguishes via `Object.is`. Fixed in `Fraction` constructor (`num / d === 0 ? 0 : num / d`) AND `_coprimeIntVector` final `map(v => v === 0 ? 0 : v)`. TA-pinned both sites.
- **Design-gap resolution (9th vector)**: design §6 lists `two_way_cycle` at `max_states: null` AND `max_states: 1` while §3 shows 8 files; §7 example pins `two_way_cycle` complete. Emitted **9 vectors**: `two_way_cycle.json` (null, complete) + `two_way_cycle_truncated.json` (1, truncated) — strict superset of the §3 plan; strengthens the no-overclaim corpus (bounded net truncated still reports unknown). Recorded in the generator docstring; TA-pinned.
- Vector corpus (9): two_way_cycle (null), two_way_cycle_truncated (1), unbounded_net (5), deadlock_net (null), token_drain_net (null), two_deadlocks_net (null), weighted_reaction / producer_consumer / hello (null, shared canonical examples).

## Decisions taken during the build

- **`markingFromKey`**: SCC Tarjan stack stores marking KEYS; the marking arrays are reconstructed with `key === "" ? [] : key.split(",").map(Number)` — the empty marking's key is `""`, and `"".split(",")` would otherwise yield `[""]` → `[0]` (wrong). TA-pinned in analysis.ts.
- **FIFO queue via index pointer** instead of `Array.shift()` (O(n) per pop): `let qi = 0; while (qi < queue.length) { const marking = queue[qi++]; ... }` — same BFS order as Python `deque.popleft`, linear cost.
- **`visited` is a `Map<string, number[]>`** (B1 markingKey): preserves key uniqueness and lets results re-materialize arrays; sorted at result construction, so insertion order never leaks.
- Cycle 2 spec was written from the Python test file directly (38 behaviors in the same class layout); fixtures inlined (TWO_WAY_CYCLE, UNBOUNDED_NET, DEADLOCK_NET, TOKEN_DRAIN_NET, TWO_DEADLOCKS_NET + M0 dicts).

## Cycle 4 (dashboard) details

- **Store additions** (design §8, B10/B12): `maxStates: number | null` default 1000 + `analysisVisible` default false + `setMaxStates`/`toggleAnalysis` — pure UI state, never written into the document (B12 pinned by the "survives import/export" test asserting `parsed.maxStates === undefined`).
- **5 additive store tests** (`TestAnalysisUIState`): defaults · setMaxStates(number|null) · toggleAnalysis · mode transitions leave both untouched (available in edit AND simulate) · import/export never persists them.
- **`AnalysisPanel.tsx`** (design §9): derived-only `useMemo(() => new PetriNetAnalyzer(toNet(doc)).<all APIs>(maxStates), [doc, maxStates])` — simulate-mode firing changes the live marking, NOT `doc`, so analysis always describes M0 (labelled "from initial marking M0"). Sections: Reachability (M0-first table + explored count + complete badge), Deadlocks, Bounds (per-place maxima + bounded badge), Liveness (is_live + per-transition), SCCs, P/T-invariants (column-labelled tables), Incidence (places × transitions). Verdict badge component: ✅ proven / ❌ disproven / ❓ unknown (`complete === false || value === null`), reason verbatim. `max_states` dial: number input (min 1) + unlimited checkbox, current value always visible (B10).
- **App wiring**: toolbar "Analyze" toggle button (active class when visible) + `{analysisVisible && <AnalysisPanel />}` rendered below the canvas.
- **CSS**: analysis-panel section added to `styles.css` (design §9 — badges colored green/red/amber via `--enabled`/`--danger`/`--warn`; dial, tables, verdict-reason styling consistent with v1).
- **Gap found at resume**: the panel was imported but NOT rendered (TS6133) and `styles.css` lacked the analysis styles — completed in this wrap-up.

## Verification evidence

- Full Vitest suite after every cycle; after Cycle 2: **230 passed (7 files)** — 60 model + 59 io + 3 golden + 47 store + 22 fraction + 38 analysis.
- Final suite (all 4 cycles): **245 passed (8 files)** — +10 conformance +5 store additive.
- `npx tsc --noEmit` clean.
- `npm run build` green (`dist/index.html` + hashed js/css; built in ~2.3s).
- `npm run check-independence` → `independence OK: 15 files scanned, 43 imports checked`.
- `npx vite preview` smoke: `GET /` + both hashed assets → 200/200/200.
- Sentinel: `tests/features/feature_035.studio_v2_analysis/test_studio_v2_analysis_sentinel.py` (canary-approval skip logged) executes `npx vitest run`; agentx `uv run pytest -q` (final, post-wrap-up) → **1643 passed, 0 failed** — 3 budget/projection failures (WORK.md 5644 B > 5120 B) were cleared by WORK.md DONE-rotation; the 2 in-window TDD-ledger probes cleared before the final run.
- Zero `src/` (agentx) edits; zero `shared/` contract edits (conformance vectors are new DATA under the reserved dir).