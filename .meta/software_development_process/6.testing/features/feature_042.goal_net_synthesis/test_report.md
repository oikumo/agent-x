# Test report: feature_042.goal_net_synthesis (IDEA-002 §4, F4-bounded)

> Type: minor_feature · Phases: Analysis → Design → Programming → Testing → Done
> Date: 2026-09-05 · Project: meta_harness_concurrent (optional phase-2, first of 042–044)

## Scope

Deterministic goal→net template synthesis via `omt_net{op:synthesize}`,
proposal-only (D4 — the agent applies the fragment via splice, which runs the
9-vector conformance gate + D20 cap check). Templates (§4.2): task→chain
(`{id}_ready → do_{id} → {id}_done`), dependency→arc (`{dep}_done → do_{id}`),
resource→capacity borrow arcs (`r ⇄ do_{id}` self-loop preserves the token),
acceptance→verified place (`do_{id} → {id}_verified`). Pool-aware (D20):
synthesize never mutates state (no revision bump, like sync resync),
ledger-audited (`kind: net_synthesize`), returns `would_exceed_cap` so pool
fragments stay proposals. Free-form synthesis explicitly out (F4).

## RED → GREEN (manual, tdd_mode:false)

- RED: new tests/scripts/omt/test_net_synthesize.py — 16 failed
  (no `build_goal_fragment`/`synthesize`, CLI subparser missing → SystemExit 2).
- GREEN round 1: state.py `build_goal_fragment` + `synthesize` → 15/16
  (CLI dispatch still SystemExit 2 — true-RED remainder).
- GREEN round 2: cli.py full-file rewrite in one Write (docstring + RESERVED_OPS
  emptied + `_synthesize` + subparser reusing `--mutation/--feature` zero-churn
  args + dispatch) → 16/16; old reserved pin in test_net_cli.py updated after
  e2e receipt (gate order) → 25/25 with test_net_cli.py.
- GREEN round 3 (harness surface, one edit per file + one e2e): omt_net.ts
  OP_ARGS synthesize whitelist + live description; .omt @tool description;
  plugin_args pins (synthesize moves to the --session group); harnessc build
  (projections) → omt suite 386/386, sentinel 1800/1800.

## Vectors

- test_net_synthesize.py ×16: single-task chain / resource self-loop /
  dependency arc / verified place / deterministic ordering / pool proposal-only
  (revision + marking + 12 places unchanged) / cap overflow flags
  (12+5=17>15) / skeleton no-overflow / 7 invalid goals (empty/bad-id/dup/
  ghost-after/unknown-resource) / CLI live dispatch.
- Regression: test_net_cli.py (synthesize-live pin), plugin_args cross-source
  pins, drift pins (tool_schemas 1551→1559 +8, tool_args unchanged 2148 —
  zero-churn as designed), e2e receipt, full omt 386, sentinel 1800.

## Numbers

- omt suite: 386 passed (370 @049 + 16 new), harnessc build+check 0 err
  (253 records, 5 projections).
- e2e: test_omt_harness_e2e 1/1 (two receipt refreshes, one per harness round).
- Live dogfood: synthesize 2-task fragment on live pool net rev48 → ok,
  applied=False, pool_net=True, places_after=17 would_exceed_cap=True;
  rev48 untouched, probe enabled=[work_complete] (042 active), invariant
  drift-free net48=ledger48, resources 5/5 capacity_ok (attention held by pool).

## Files (one edit per file per e2e round)

- scripts/omt/net/state.py (`build_goal_fragment` + `synthesize` + ledger audit)
- scripts/omt/net/cli.py (RESERVED_OPS emptied + `_synthesize` + subparser +
  dispatch; single full-file Write = one round)
- .opencode/plugins/omt_net.ts (OP_ARGS synthesize + live description)
- .meta/META_HARNESS.omt (@tool omt_net description) → harnessc build
  (harness.ir.json + nav.index.jsonl + AGENTS.md regenerated)
- tests/scripts/omt/test_net_synthesize.py (new, ×16)
- tests/scripts/omt/test_net_cli.py (reserved→live pin)
- tests/scripts/omt/test_omt_net_plugin_args.py (synthesize joins --session group)

## Deferred

- No `--apply` flag: synthesize is proposal-only on ALL nets (even pre-pool);
  materialization stays manual via splice (D4). A future apply path would need
  its own cap + conformance UX — out of scope for this minor_feature.
- Dependency arcs consume `{dep}_done` (sequential chains); diamond
  dependencies sharing one done-place need token duplication — noted limitation.
- 043/044 optionals still scaffolded-pending; 001/002 unscoped (D1 out-of-scope).
