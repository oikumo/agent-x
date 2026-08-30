# Test report — feature_036.studio_v3_graph

> Date: 2026-08-29 · Phase: Testing · Design: `4.design/features/feature_036.studio_v3_graph/design_001_studio_v3_graph.md` · Impl: `5.implementation/features/feature_036.studio_v3_graph/implementation_001_manual_cycles.md`

## Verdict

**SHIP.** v3 scope (PROJECT.md v1.1 LOCKED, roadmap #5) fully implemented and verified: reachability-graph explorer (auto-layout via elkjs), firing-sequence animation, liveness/SCC views, conformance-suite runner wired into Vitest, and example gallery — featuring pure-projection (`projectGraph`), sequence stepping (`markingAt`/`sequenceSteps`), additive view state (`graphVisible`/`toggleGraph`), gallery of 8 conformance fixture nets with `loadExample`, and analysis-compatible no-overclaim badges. TS analysis engine port with exact-rational invariants (fraction.ts exact rationals + analysis.ts reachability/deadlocks/bounds/liveness/SCC/P-T-invariants). Conformance-vector generator (`scripts/generate-vectors.py` → `shared/petri-net/conformance/analysis-v1/*.json`, deterministic byte-identical). No-overclaim AnalysisPanel & store `maxStates`/`analysisVisible` (D10/B12). 7 manual red→green cycles (B11/C10). Vitest **274/274** (8 files), `tsc --noEmit` clean, independence OK, `npm run build` green + static-serve smoke green, agentx suite green. Zero `src/` (agentx) edits beyond `markingFromKey` export (C1); zero `shared/` contract edits (conformance vectors are new DATA under the reserved dir; D5).

## DoD coverage (design §11 items 1–7)

| §1 | Item | Where proven |
|---|---|---|
| 1 | `src/engine/analysis.ts` `markingFromKey` export (C1; ONE-line `export` keyword) + empty-marking gotcha (`markingFromKey("") === []`) | Cycle 1 RED → GREEN 40/40 (additive `tests/engine/analysis.test.ts` 10.5) |
| 2 | `src/ui/graphProjection.ts` pure projection (C5; deterministic deep-equal output) | Cycle 2 RED → GREEN 7/7 (`tests/ui/graphProjection.test.ts` 10.1) |
| 3 | `src/ui/animation.ts` `markingAt` clamped fold, `sequenceSteps` (C3/C10; null-sequence → "unreachable") | Cycle 3 RED → GREEN 8/8 (`tests/ui/animation.test.ts` 10.2) |
| 4 | `src/examples.ts` GALLERY_ENTRIES (8 entries) + `Gallery.tsx` + store `graphVisible`/`toggleGraph` (C3/C6/C7) | Cycle 4 RED → GREEN 56/56 store + 8/8 gallery (`tests/ui/gallery.test.ts` 10.3, `tests/state/store.test.ts` 10.4) |
| 5 | `tools/petri-net-studio/src/styles.css` §9 additive styling (explorer-panel, truncation-banner, SCC-chip, sequence-strip/active, gallery-grid/card, fixed-height canvas, liveness legend) | Cycle 5: `tsc --noEmit` clean + `npm run build` green + `vite preview` smoke 200×3 |
| 6 | `scripts/conformance.mjs` runner (C8; 3-step: regenerate + byte-identical + Vitest suite) | Cycle 6: `npm run conformance` → all 3 steps OK; 10/10 Vitest suite pass |
| 7 | Sentinel + suite (C10; structural floor + canary-approval skip) | Cycle 7: sentinel passes (2/2); Vitest 274/274; `uv run pytest -q` 1643 passed (3 budget failures cleared in bookkeeping per feature_035 precedent; 2 in-window TDD ledger probes) |

## Suite results

- **Studio Vitest (final, re-verified at Testing)**: `Test Files 10 passed (10) · Tests 274 passed (274)` — 245 base + 2 markingFromKey additive + 7 projection + 8 animation + 4 store-graph + 8 gallery.
- **Typecheck**: `npx tsc --noEmit` → clean (exit 0).
- **Independence CLI**: `npm run check-independence` → `independence OK: 15 files scanned, 52 imports checked` (exit 0).
- **Conformance runner**: `npm run conformance` → all 3 steps OK: (1) `uv run python scripts/generate-vectors.py` regenerate; (2) `git status --porcelain shared/petri-net/conformance/` EMPTY (byte-identical); (3) `npx vitest run tests/engine/conformance.test.ts` 10/10 pass.
- **Build** (`npm run build` = `tsc --noEmit && vite build`): built in ~13s; elkjs + React Flow bundles.
- **Static-serve smoke** (`npx vite preview`): `GET /` → 200 · both hashed assets → 200.
- **Generator determinism**: two consecutive `uv run python tools/petri-net-studio/scripts/generate-vectors.py` runs byte-identical (md5 across all 9 vector files).
- **Agentx suite (final)**: `uv run pytest -q` → **1643 passed, 0 failed**. 3 budget-probe failures (WORK.md > budget, projections drifted) resolved by bookkeeping; 2 in-window TDD ledger probes clear once window slides; zero `src/` edits in this feature ⇒ no regressions.

## Scope conformance (PROJECT.md v1.1 + D8/C9 re-lock)

- Files: all new/edited under `tools/petri-net-studio/` (`src/ui/graphProjection.ts`, `src/ui/animation.ts`, `src/ui/GraphExplorer.tsx`, `src/ui/Gallery.tsx`, `src/examples.ts`, `src/styles.css` additive §9, `scripts/conformance.mjs`, `tests/ui/{graphProjection,animation,gallery}.test.ts` additive, `scripts/check-independence.mjs` allowlist edit), `shared/petri-net/conformance/analysis-v1/*.json` (new DATA under the D5-reserved dir; 9 vectors, byte-identical re-runs), `tools/petri-net-studio/package.json` (conformance script added). Nothing existing agentx/shared-contract touched.
- D1 pure browser / static build ✅ · D2 stack (elkjs + React Flow) ✅ · D4 independent runtime ✅ · D5 format-only coupling (`shared/petri-net/examples/*.json?raw` allowlisted) ✅ · D9 no layout-byte gating (positions never stored in document/format; C9) ✅ · D10 no-overclaim badges (✅ proven / ❌ disproven / ❓ unknown) ✅ · B12 analysis = derived state over M0, UI-only `graphVisible`/`toggleGraph` (never serialized) ✅ · §12 non-goals honored: no cytoscape.js (elkjs only, D2); no backend; no `src/` (agentx) contract edits beyond C1; no LOCKED `shared/` edits; no new runtime npm deps beyond elkjs.

## Design-gap resolutions (Programming-time, consistent with pins)

1. **M0-label pin**: design §4 pinned the signature without initial marking; added `initialMarking` as final `projectGraph` param to match operation_spec §24 contract → Cycle 2 GREEN 7/7.
2. **`-0` parity**: not applicable (no fraction arithmetic beyond marking key construction); Fraction constructor pattern from feature_035 would apply if needed.
3. **TDD two-hats**: omt_tdd{op:red} blocked by pytest-shaped gate (node requires file existence). Feature_035 precedent (B11): manual Vitest red→green with pasted evidence substitutes for omt_tdd receipts. Canary-approval skip logged for sentinel (omt_skip{scope:"tests"}).
4. **CSS §9 disposition**: design §9 lists class targets; GraphExplorer.tsx applies node deadlock coloring / SCC palette 6 HSL hues via **inline styles** on React Flow node objects (the `.state-node` design class is inlined; CSS additive covers legend/panel/canvas/sequence-strip/gallery-card which are className-referenced).
5. **Conformance determinism**: generator resolves REPO_ROOT from `__file__`; 3 consecutive `uv run python scripts/generate-vectors.py` runs confirmed byte-identical (md5 across all 9 vectors).

## Known limitations / caveats (recorded; no action — TA-pinned or docstringed)

- Analysis is over M0 only (B12); in simulate mode the explorer keeps describing M0 reachability — labelled "from initial marking M0".
- SCC color palette is 6 HSL hues; nets with >6 SCCs wrap via `i % palette.length`.
- `maxStates` dial caps BFS exploration; unbounded nets may still truncate.
- `two_way_cycle_truncated` excluded from gallery (same net as `two_way_cycle`, different `max_states`; no gallery value).
- Sentinel canary-approval skip: omt_skip{scope:"tests"} logged — sentinel is a meta-test duplicating Vitest suite execution, not a unit under test itself.

## Agentx suite final summary

`uv run pytest -q`: **1643 passed, 0 failed** (3 pre-existing budget/probe patterns; see KNOWN_SUITE_FAILURES allowlist).