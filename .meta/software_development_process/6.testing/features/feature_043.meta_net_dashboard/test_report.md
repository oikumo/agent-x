# Test report: feature_043.meta_net_dashboard (IDEA-002 §6 war-room)

> Type: major_feature · Phases: Analysis → Design → Programming → Testing → Done
> Date: 2026-09-05 · Project: meta_harness_concurrent (optional phase-2, 2/3)
> TDD: `omt_tdd{testlist(15) → red → green → refactor → done}` (toolchain-aware)

## Scope

Static-build dashboard reusing studio graph rendering over a ledger-replay
snapshot: live net graph (`toFlowGraph` + PlaceNode/TransitionNode reuse),
deadlock/blocked-place highlight, revision slider over replayed markings,
pool/resource status — no live server, no editor changes, no new tool, no
`src/` touches (D1), zero budget churn (F5).

## RED → GREEN (TDD receipts)

- RED: pytest `test_net_history.py` 9F (no history module); vitest 3 suites
  fail (no src/dashboard/*) — true-RED both halves, `omt_tdd{op:red}` recorded.
- GREEN-py: `scripts/omt/net/history.py` (genesis/add/remove/disable/undo/fire
  fold reusing engine appliers) — synthetics pass; live golden drove 3
  discoveries, each with a vector: era-accurate genesis (3 ports — resources
  came via the 041 resync), archive-done recovery rule (map-less reroute →
  archive_pool, 39==39 evidence), monotonicity gate (rev-1 cap-edge leak
  skipped pre-mutation, `skipped` transparency). 12/12.
- GREEN-ts: `blockedPlaces.ts` + `Dashboard.tsx` + `dashboard-main.tsx` +
  `dashboard.html` + `net_snapshot.py` + generated `snapshot.json` (rev50,
  51 snaps, 2 skipped). Fixes: `toNet` imports from state/document.js;
  snapshot guard scoped to final marking (historic place names); jest-dom
  import + cleanup (no globals); ResizeObserver mock (jsdom). 9/9.
- GREEN-surface: vite second input + styles.css `.blocked` (--warn, additive).
  `tsc` clean; `npm run build` emits index+dashboard; independence 23/81;
  preview smoke 200×2; full vitest 283/283 (274+9).
- REFACTOR (`omt_tdd{op:refactor}`): dead per-branch monotonicity guards
  removed (top gate owns it) — 12/12 + 9/9 stay green.
- Bridge `test_dashboard_sentinel.py` ×3 (structural + scoped vitest + live
  freshness) — 3/3. `omt_tdd{op:done}` recorded.

## Vectors

- pytest ×12: genesis/add/fire, remove-reroute, undo-add, undo-add-refusal
  mirror, undo-remove live-restore, map-less recovery ±archive, skip-kinds,
  unknown-kind, LIVE golden (real store ⇒ rev50 + exact marking), schema keys,
  mismatch fail-closed.
- vitest ×9: blockage single/dedupe/empty-net/live-pool, snapshot
  version/final-coverage/positions, Dashboard pool/slider/step/blocked.
- Regression: omt 398/398 (386+12), sentinel 1815/1815 (1800+12+3),
  harnessc 0 err (253 records, no .omt change — budgets flat).

## Numbers

- Live replay: 83 net records → 51 snapshots (rev 0→50), 2 foreign skipped,
  final == live bundle exactly (marking + revision).
- Snapshot: 12 places / 2 transitions / pool 3/1/3 @rev50 (043 active).
- Live dogfood: `net_snapshot.py` → rev50 envelope ok; rev50 untouched by reads.

## Files

- `scripts/omt/net/history.py` (new: replay_records/replay_full/replay/
  build_snapshot + archive recovery + monotonicity gate + grid positions)
- `scripts/omt/net_snapshot.py` (new thin shim, default out dashboard snapshot)
- `tools/petri-net-studio/src/dashboard/` (blockedPlaces.ts, Dashboard.tsx,
  dashboard-main.tsx, snapshot.json committed rev50)
- `tools/petri-net-studio/dashboard.html` (new) + `vite.config.ts` (2nd input)
  + `src/styles.css` (.blocked additive)
- `tools/petri-net-studio/tests/dashboard/` (3 files, 9 tests)
- `tests/scripts/omt/test_net_history.py` (×12)
- `tests/features/feature_043.meta_net_dashboard/test_dashboard_sentinel.py`
- `.meta/.../feature_043.*/` analysis/design/operation-spec/implementation docs

## Deferred / follow-ups

- Live audit gap: `net_disable` persists policy but NOT the mutation/reroute
  map (state.py `_splice_disable` ledger block) — replay recovers via the
  archive-done rule; persisting the map would remove the special case.
- Ledger hygiene: the rev-1 cap-edge add + work_start fire (19:42 2026-09-05,
  leaked hermetic-test writes) stay in the store, skipped transparently —
  left untouched (audit immutability).
- GraphExplorer reachability reuse + animation-ride for slider steps: evaluated,
  deferred (elkjs runtime cost; slider already steps markings).
- Snapshot staleness: committed rev50; regen = one script run (bridge enforces
  freshness — fails when live moves on).
- 044 optional still scaffolded-pending; 001/002 unscoped (D1 out-of-scope).
