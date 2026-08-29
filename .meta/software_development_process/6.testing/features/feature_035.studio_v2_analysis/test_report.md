# Test report — feature_035.studio_v2_analysis

> Date: 2026-08-29 · Phase: Testing · Design: `4.design/features/feature_035.studio_v2_analysis/design_001_studio_v2_analysis.md` · Impl: `5.implementation/features/feature_035.studio_v2_analysis/implementation_001_manual_cycles.md`

## Verdict

**SHIP.** v2 scope (PROJECT.md v1.1 LOCKED, roadmap #4, D8 re-lock) implemented and verified: TS analysis engine port (`fraction.ts` + `analysis.ts` — exact parity with `analysis.py`, B2/B3), conformance-vector generator (`scripts/generate-vectors.py` → `shared/petri-net/conformance/analysis-v1/*.json`, deterministic byte-identical), no-overclaim analysis dashboard (`AnalysisPanel.tsx` + store `maxStates`/`analysisVisible`, D10). Vitest **245/245** (8 files), `tsc --noEmit` clean, independence OK, `vite build` + static-serve smoke green, agentx suite green (2 known allowlisted failures only). Zero `src/` (agentx) edits; zero `shared/` contract edits.

## DoD coverage (design §1 items 1–5)

| §1 | Item | Where proven |
|---|---|---|
| 1 | `src/engine/fraction.ts` + `src/engine/analysis.ts` port the analysis layer with exact parity (B2/B3) | Cycles 1–2 evidence below; 1:1 loop/algebra ports pinned in implementation_001 (§B3 explore, B2 nullspace/_coprimeIntVector, B6 ordering, B7 Tarjan) |
| 2 | Vitest green: fraction + 38 analysis + conformance-vector suite | Final suite **245/245** below: 22 fraction + 38 analysis + 10 conformance + 175 v1 (model/io/examples/store) + 1 independence |
| 3 | Generator emits canonical, deterministic vectors TS reads via fs | 9 vectors (`analysis-v1/*.json`); two consecutive generator runs byte-identical (md5 across all files); `tests/engine/conformance.test.ts` deep-equals every API against `expected` |
| 4 | Dashboard renders ✅/❌/❓ + `complete` + `reason` + `max_states` dial (D10); `npm run build` green | `AnalysisPanel.tsx` (badge component, verbatim reasons, M0 label, dial min 1 + unlimited) + store defaults `maxStates:1000`; build output below |
| 5 | Independence lint passes; agentx pytest untouched/green | `independence OK: 15 files scanned, 43 imports checked`; agentx suite below — zero `src/` edits in this feature |

## Manual red→green evidence (design §10.5 protocol — substitute for `omt_tdd` receipts, B11)

- **Cycle 1 (fraction) RED**: `npx vitest run tests/engine/fraction.test.ts` → `Test Files 1 failed (1) · Tests 22 failed (22)` (stub "not implemented (RED stub)").
- **Cycle 1 GREEN**: same cmd → `Test Files 1 passed (1) · Tests 22 passed (22)`.
- **Cycle 2 (analysis) RED**: `npx vitest run tests/engine/analysis.test.ts` → `Test Files 1 failed (1) · Tests 38 failed (38)` (stub).
- **Cycle 2 GREEN (full suite)**: `npx vitest run` → `Test Files 7 passed (7) · Tests 230 passed (230)`.
- **Cycle 3 (conformance) RED**: `npx vitest run tests/engine/conformance.test.ts` (vectors not yet generated) → `Test Files 1 failed (1) · Tests 1 failed (1)` ("generator has produced at least one vector").
- **Cycle 3 GREEN (full suite)**: `npx vitest run` → `Test Files 8 passed (8) · Tests 240 passed (240)` — 240 = 230 + 9 vectors + the non-empty guard.
- **Cycle 4 (store) GREEN**: `TestAnalysisUIState` (5 additive cases) green within the final suite — written alongside the store additions; the RED receipt for these additive cases predates the resume (not captured before the pause; the pause doc had mis-stated the cycle position — see implementation_001).
- **Cycle 4 (UI wiring) RED → GREEN (build-level)**: at resume the panel import was unused (`src/ui/App.tsx(27,1): error TS6133: 'AnalysisPanel' is declared but its value is never read`) and `styles.css` lacked the §9 analysis styles → fixed (render `{analysisVisible && <AnalysisPanel />}` below the canvas + CSS section) → `tsc --noEmit` clean, `npm run build` green, preview smoke 200/200/200.

## Suite results

- **Studio Vitest (final, re-verified at Testing)**: `Test Files 8 passed (8) · Tests 245 passed (245)` — 60 model + 59 io + 3 golden-examples + 22 fraction + 38 analysis + 10 conformance + 52 store + 1 independence.
- **Typecheck**: `npx tsc --noEmit` → clean (exit 0).
- **Independence CLI**: `node scripts/check-independence.mjs` → `independence OK: 15 files scanned, 43 imports checked` (exit 0).
- **Build** (`npm run build` = `tsc --noEmit && vite build`):

  ```
  dist/index.html                   0.40 kB │ gzip:   0.27 kB
  dist/assets/index-BZawRaL4.css   21.32 kB │ gzip:   4.00 kB
  dist/assets/index-eWqW8yp7.js   368.92 kB │ gzip: 117.61 kB
  ✓ built in 2.31s
  ```

- **Static-serve smoke** (`npx vite preview`): `GET /` → 200 · `GET /assets/index-eWqW8yp7.js` → 200 · `GET /assets/index-BZawRaL4.css` → 200.
- **Generator determinism**: two consecutive `uv run python tools/petri-net-studio/scripts/generate-vectors.py` runs byte-identical (md5 across all 9 vector files; re-verified after the TS `-0` fix).
- **Agentx suite (final)**: `uv run pytest -q` → **1643 passed, 0 failed**. During the wrap-up one run showed 5 failures: the 2 `test_gate_no_tdd_allows_*` are in `KNOWN_SUITE_FAILURES` (`scripts/omt/tdd/state.py`) — TDD-gate probes reading the live 8h ledger (feature_031/034 precedent — pass once the window clears); the other 3 (`test_repo_omt_check_has_zero_errors`, `test_repo_projections_are_fresh`, `test_work_md_within_budget`) were ONE root cause — WORK.md 5644 B > 5120 B budget — cleared by DONE-rotation to `WORK_ARCHIVE.md` in the wrap-up (feature_031 precedent). The final run passed everything including the formerly in-window probes. Zero `src/` edits in this feature ⇒ no regressions.

## Scope conformance (PROJECT.md v1.1 + D8 re-lock)

- Files: all new/edited under `tools/petri-net-studio/` (`src/engine/{fraction,analysis}.ts`, `src/state/store.ts` additive, `src/ui/{AnalysisPanel.tsx,App.tsx,styles.css}`, `scripts/generate-vectors.py`, `tests/engine/{fraction,analysis,conformance}.test.ts`, `tests/state/store.test.ts` additive) + `shared/petri-net/conformance/analysis-v1/*.json` (new DATA under the D5-reserved dir; no FORMAT/schema/examples edits). Nothing existing agentx/shared-contract touched.
- D1 pure browser / static build ✅ · D2 stack ✅ · D4 independent runtime ✅ · D5 format-only coupling (only cross-boundary imports = `shared/petri-net/examples/*.json?raw` allowlisted) ✅ · D8 generator shipped HERE (re-lock) ✅ · D10 no-overclaim dashboard ✅ · B12 analysis = derived state over M0, UI-only `maxStates`/`analysisVisible` (never serialized — pinned by test).
- §12 non-goals honored: no reachability explorer UI / animation / conformance RUNNER (#5), no coverability, no current-marking snapshot in analysis, no backend, no npm publish, no `src/` (agentx) edits, no LOCKED `shared/` edits, no new runtime npm deps (fraction.ts hand-rolled, B2).

## Design-gap resolutions (Programming-time, consistent with pins — also in implementation_001)

1. **9th conformance vector**: design §6 lists `two_way_cycle` at `max_states: null` AND `max_states: 1` while §3 shows 8 files — emitted **9 vectors** (`two_way_cycle.json` + `two_way_cycle_truncated.json`), a strict superset strengthening the no-overclaim corpus (bounded net truncated still reports unknown). TA-pinned in the generator docstring.
2. **`-0` parity bug**: `weighted_reaction.json` place_invariants diverged `[1,-0,-2]` (TS) vs `[1,0,-2]` (Python) — JS `-x` of `0` yields `-0`, Python `int()` canonicalizes `-0.0 → 0`, vitest `toEqual` distinguishes via `Object.is`. Fixed in `Fraction` constructor AND `_coprimeIntVector` final `map(v => v === 0 ? 0 : v)`. TA-pinned both sites.
3. **`markingFromKey`**: `markingKey([]) = ""` and `"".split(",")` would yield `[""] → [0]` — special-cased `key === "" ? [] : …` (empty net's single SCC must be `[[]]` not `[[0]]`). TA-pinned.
4. **Panel render + CSS missing at resume**: `AnalysisPanel` imported but never rendered (TS6133) and no §9 styles — completed in the wrap-up (gap was a pause-bookkeeping omission, not a design gap).

## Known limitations / caveats (recorded; no action — TA-pinned or docstringed)

- `omt_tdd` not used (B11 declared in the Programming scope): manual Vitest red→green with the pasted evidence above substitutes for receipts.
- Analysis is over M0 only (B12); in simulate mode the panel keeps describing M0 reachability — labelled "from initial marking M0".
- Tarjan SCC is recursive (depth fine for v1 nets); `maxStates` dial caps BFS exploration, not recursion.
- Cycle 4 store RED receipt not captured (additive tests + implementation landed before the pause; GREEN verified in the resume suite).