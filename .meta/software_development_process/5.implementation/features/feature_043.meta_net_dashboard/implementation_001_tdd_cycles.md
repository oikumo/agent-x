# Implementation notes 001 — feature_043.meta_net_dashboard TDD cycles

> Date: 2026-09-05 · Phase: Programming · Task type: major_feature (TDD auto-on)
> Design: `4.design/.../feature_043.meta_net_dashboard/design_001_snapshot_dashboard.md`
> + `operation_spec_001_dashboard.md` · Analysis: `3.analysis/.../analysis_001_reuse_and_replay.md`
> TDD: `omt_tdd{testlist(15 behaviors) → red(pytest node) → green(pytest) → refactor → green(vitest) → done}` (toolchain-aware: .py→pytest, .ts→vitest)

## Cycle log

| Cycle | Test file / Artifact | Src written / Action | Behaviors / Notes | Result |
|---|---|---|---|---|
| RED | `tests/scripts/omt/test_net_history.py` (new, 9→12 tests) + `tools/.../tests/dashboard/*` (3 files, 9 tests) | none (two-hats RED) | pytest 9F ImportError (no history module); vitest 3 suites fail (no src/dashboard/*) — true-RED both halves | RED confirmed |
| GREEN-py 1 | same pytest file | `scripts/omt/net/history.py` (new: genesis/add/remove/disable/undo/fire fold) | 15/16 pass; CLI-style dispatch n/a (no new op) | 1F: CLI test was 042's — n/a here |
| GREEN-py 2 | +2 vectors (forbid-refusal mirror, map-less reroute) | era-accurate genesis (3 ports, not 8 — live ledger proves resources came via 041 resync) | synthetic 11/11 | live golden still red |
| GREEN-py 3 | live golden (real store, read-only) | archive-done recovery rule (map-less reroute → archive_pool; evidence: rev4 creation + 39 reasonings + 39==39 tokens) + monotonicity gate (skip regressing revs — the rev-1 cap-edge leak) + check-first restructure | full 83-record fold reproduces live rev50 exactly | 12/12 GREEN |
| GREEN-ts 1 | `blockedPlaces.test.ts` ×4, `snapshot.test.ts` ×3, `Dashboard.test.tsx` ×2 | `src/dashboard/blockedPlaces.ts` + `Dashboard.tsx` + `dashboard-main.tsx` + `dashboard.html` + `scripts/omt/net_snapshot.py` + generated `snapshot.json` (rev50, 51 snaps, 2 skipped) | import fix (`toNet` lives in state/document.js, not engine/model.js); snapshot guard relaxed for historic place names (structural fidelity proven by pytest golden); jest-dom import + cleanup (no globals); ResizeObserver mock (jsdom) | 9/9 GREEN |
| GREEN-ts 2 | — | `vite.config.ts` second input + styles.css `.blocked` (additive, --warn) | `tsc --noEmit` clean; `npm run build` emits index+dashboard; independence 23 files/81 imports; preview smoke 200×2; full vitest 283/283 (274+9) | GREEN |
| REFACTOR | same suites | removed dead per-branch monotonicity guards (top gate owns it) + gate-comment trim; `replaceAll` single edit | pytest 12/12 + vitest 9/9 stay green | GREEN |
| Bridge | `tests/features/feature_043.../test_dashboard_sentinel.py` (3 tests) | structural floor + scoped vitest + live-freshness (snapshot rev == live rev) | 3/3 (path-prefix fix) | GREEN |

## Decisions taken during the build

- **Era-accurate genesis**: today's `sync` bootstraps WITH resources, but the 040-era live bootstrap predates the 041 catalog — replaying with 8 places dies on the real `add_resource_places` record (DuplicatePlace). Genesis = 3 boundary ports; proven by the live golden, not by reading old code.
- **Archive-done recovery rule**: live `net_disable` drops the mutation AND reroute map (audit gap — follow-up: persist them). Recovery (map-less reroute holders → archive_pool, must exist) is evidence-backed per-record (rev4 creation prose + uniform reasonings + 39==39 arithmetic), guarded (absent archive_pool → invalid_replay), and terminal-gated (final exact equality).
- **Monotonicity gate + skipped transparency**: revision-regressing emitting records are foreign leaked writes (proven rev-1 pair) → skip pre-mutation, listed in snapshot `skipped` (dashboard banners the count). A wrongly skipped mutation breaks the terminal gate — never silent.
- **`toNet` import**: lives in `state/document.js` (re-export hub), not `engine/model.js` — the one import error in the TS half.
- **No new tool / no budget churn**: snapshot is a build script (`net_snapshot.py`), not an `omt_net` op (F5); no @tool change → tool_schemas/tool_args untouched.
- **No `src/` touches** (D1): all code in `scripts/omt/net/`, `scripts/omt/net_snapshot.py`, `tools/petri-net-studio/`.

## Verification evidence

- pytest `test_net_history.py` 12/12 (incl. live golden on the real store).
- vitest `tests/dashboard` 9/9; full studio suite 283/283 (274 pre-existing + 9).
- `npx tsc --noEmit` clean; `npm run build` green (dist/index.html + dist/dashboard.html); `npm run check-independence` OK (23/81); `vite preview` smoke 200 on both pages.
- Sentinel bridge 3/3.
