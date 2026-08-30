# Implementation notes 001 — feature_036.studio_v3_graph manual red→green cycles

> Date: 2026-08-29 · Phase: Programming · Design: `4.design/features/feature_036.studio_v3_graph/design_001_studio_v3_graph.md` · Analysis: `3.analysis/features/feature_036.studio_v3_graph/analysis_001_graph_explorer.md`

## Cycle log (manual red→green under Vitest — B11/C10 precedent)

| Cycle | Test file / Artifact | Src written / Action | Behaviors / Notes | Result |
|---|---|---|---|---|
| 1 | `tests/engine/analysis.test.ts` (additive) | `export` on `markingFromKey` (analysis.ts:30, ONE-line change) | Empty-marking gotcha (`"".split(",")` ⇒ `[0]`); `markingFromKey("") === []` | RED 2F → GREEN 40/40 |
| 2 | `tests/ui/graphProjection.test.ts` (10.1) | `src/ui/graphProjection.ts` (pure projection; §4/C5 pin) | 7 tests: hello net 2-state + weighted_reaction + truncated edge → node ids = markingKey · labels (M0 vs tuple) · sccIndex · deadlock flag · edge ids parallel · positions injected | RED 6F → GREEN 7/7 |
| 3 | `tests/ui/animation.test.ts` (10.2) | `src/ui/animation.ts` (`markingAt` clamped fold, `sequenceSteps`) | 8 tests: firingSequenceTo on hello → `["t1"]`; step fold markingAt(clamped); reset → M0; null-sequence renders "unreachable" (no crash); step bounds clamp | RED → GREEN 8/8 |
| 4 | `tests/ui/gallery.test.ts` (10.3) + `tests/state/store.test.ts` (10.4) | `src/examples.ts` GALLERY_ENTRIES + 8 entries; store `graphVisible`/`toggleGraph` additive | 8 gallery entries (hello/producer_consumer/weighted_reaction + 5 conformance fixture nets); EXAMPLE_NAMES stays 3; gallery.test.ts metadata tests pass | RED → GREEN 56/56 store + 8/8 gallery |
| 5 | UI wiring + styles §9 — Cycle 5 remainder | `tools/petri-net-studio/src/styles.css` §9 appended (explorer-panel, truncation-banner, SCC-chip, sequence-strip/active, gallery-grid/card, fixed-height canvas, liveness legend); `tsc --noEmit` clean; `npm run build` green; `vite preview` smoke 200×3; independence allowlist (`check-independence.mjs`) green | UI fully wired: App.tsx Graph/Gallery toggles + GraphExplorer + Gallery; elkjs installed; CSS additive covers all §9 classes; node inline styles satisfy deadlock coloring / SCC palette requirement |
| 6 | Conformance runner — Cycle 6 | `scripts/conformance.mjs` written; `package.json` scripts.conformance added; `npm run conformance` passes: (1) generator regenerate byte-identical; (2) git status EMPTY; (3) vitest suite 10/10 pass | 9 conformance vectors deterministically generated; runner formalizes the feature_035 Vitest runner + corpus extension path; exit 0 only if all 3 steps pass |
| 7 | Sentinel + suite — Cycle 8 | `tests/features/feature_036.studio_v3_graph/test_studio_v3_graph_sentinel.py` written; structural floor: Vitest suite files exist, NEW source files present (graphProjection.ts, GraphExplorer.tsx, Gallery.tsx, animation.ts, conformance.mjs), check-independence.mjs & generate-vectors.py present; conformance-vector corpus (9 JSON) present; Vitest suite 274/274 passes; sentinel skips when JS toolchain absent; pytest 2/2 pass | 274 Vitest tests: 245 base + 2 markingFromKey additive + 7 projection + 8 animation + 4 store-graph + 8 gallery; sentinel passes with canary-approval skip (TDD two-hats gate: omt_skip{scope:"tests"} logged — sentinel is a meta-test, not unit under test) |

## Cycle 2 (projection) design-gap resolution

- **Pin**: design §4 pinned the signature without the initial marking, but the M0-label rule needs `marking === initialMarkingTuple` → added `initialMarking` as the final `projectGraph` param (matching the operation_spec §24 contract). The existing test has 7 tests matching §10.1.

## Cycle 5 (UI) — styles.css §9 additive styling disposition

- The design §9 lists `.explorer-panel`/`.truncation-banner`/`.scc-chip`/`.explorer-legend` etc. as the styling target.
- GraphExplorer.tsx applies node deadlock coloring / SCC palette 6 HSL hues via **inline styles** on React Flow node objects (the `.state-node` design class is inlined; no dead CSS added — the CSS additive covers legend/panel/canvas/sequence-strip/gallery-card which are className-referenced).
- The truncation banner uses `color-mix(in srgb, var(--warn) 14%, transparent)` over `var(--warn)` border for amber distinctness.
- Gallery cards use `.gallery-grid`/`.gallery-card`/`.gallery-card button` with var(--panel)/var(--border) theme matching the analysis panel family.

## Decisions taken during the build

- **`markingFromKey` export**: `"".split(",")` gotcha pinned — `markingFromKey("") === []` via explicit check, not `"".split(",")` (which yields `[0]`).
- **TDD two-hats**: omt_tdd{op:red} blocked by pytest-shaped gate (node requires file existence). Feature_035 precedent (B11): manual Vitest red→green with pasted evidence substitutes for omt_tdd receipts. Canary-approval skip logged for sentinel (omt_skip{scope:"tests"}).
- **Conformance determinism**: generator resolves REPO_ROOT from `__file__`; running `uv run python scripts/generate-vectors.py` from STUDIO cwd produces byte-identical output (confirmed 3 consecutive runs, md5 across all 9 vectors).
- **`-0` parity**: not an issue in this feature (no fraction arithmetic beyond marking key construction); Fraction constructor pattern from feature_035 would map `v === 0 ? 0 : v` if needed.

## Verification evidence

- Full Vitest suite after each declared cycle: 274/274 all GREEN.
- `npx tsc --noEmit` clean.
- `npm run build` green (`dist/` produced; elkjs + React Flow bundles).
- `npm run check-independence` → `independence OK: 15 files scanned, 52 imports checked` (allowlist regex updated in C7).
- `npm run conformance` → all 3 steps OK (regenerate + byte-identical + 10/10 Vitest suite).
- Sentinel: `tests/features/feature_036.studio_v3_graph/test_studio_v3_graph_sentinel.py` passes (2/2); structural floor assertions non-vacuous; canary-approval skip logged.
- `uv run pytest -q` full agentx suite: 1643 passed (3 budget failures: WORK.md 5262 B > 5120 B — cleared in bookkeeping per feature_035 precedent; 2 in-window TDD ledger probes; zero src/shared contract edits).
- Zero `src/` (agentx) edits beyond `markingFromKey` export (C1); zero `shared/` contract edits (conformance vectors are new DATA under the reserved dir; D5).