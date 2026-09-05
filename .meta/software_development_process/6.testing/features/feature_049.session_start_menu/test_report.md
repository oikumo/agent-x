# Test report: feature_049.session_start_menu (D19 on pool net)

> Type: minor_feature · Phases: Analysis → Design → Programming → Testing → Done
> Date: 2026-09-05 · Project: meta_harness_concurrent (D19 session-start menu, rescaffolded from 047 tombstone → 049)

## Scope

D19 menu = 045 render, rev-stamped (NEXT + Other + Blocked + Resources + Pool, net rev R).
STARTUP reads WORK.md Tasks only, presents options in order. Fire verifies R == probe
revision else refuses + re-renders (D4 proposal-only). Pool-net gaps closed: menu_lines
pool-aware, render NEXT work_complete when active, fire --expected-revision guard,
STARTUP Tasks-menu instruction in META_HARNESS.omt + AGENTS.md (+agents_md 2816→2944).

## RED → GREEN (manual, tdd_mode:false)

- RED: new tests/scripts/omt/test_net_menu.py — 3 failed / 1 passed (menu_lines pool
  kwarg + state.fire expected_revision TypeErrors — true-RED, missing behavior).
- GREEN round 1: sync_md.menu_lines(pool=None) + state.fire(expected_revision) +
  cli --expected-revision/--expected_revision + omt_net.ts OP_ARGS + STARTUP line +
  agents_md budget 2944 + drift pin 2944 → 4 passed.
- GREEN round 2 (acceptance gap): render_tasks_block NEXT none on active pool →
  pool-aware enabled filter (work_complete) + 2 render vectors → 6 passed.

## Vectors

- test_net_menu.py ×6: menu pool line / menu no-pool / fire stale refuses
  (stale_revision) / fire fresh ok / render active NEXT work_complete + Blocked
  work_start + Pool / render idle NEXT work_start.
- Regression: test_net_pool.py ×10, test_net_sync_md.py ×6, plugin_args pins,
  drift pins (AGENTS_BUDGET 2944), e2e receipt — all green.

## Numbers

- omt suite: 370 passed (364 @048 + 6 new), harnessc build+check 0 err (253 records).
- e2e: test_omt_harness_e2e 1/1 (two receipt refreshes, one per harness round).
- Live dogfood: rev45 → fire work_start (user-approved) → rev46 (5/1/1, attention
  held by pool); probe enabled=[work_complete]; invariant drift-free net46=ledger46;
  stale fire rev45 refused (stale_revision, no mutation); sync net_to_md dry-run
  renders NEXT work_complete + Pool 5/1/1 (places 12/15), proposal empty + pool info.

## Files (one edit per file per e2e round; cli.py remainder + budget via uv-run script)

- scripts/omt/net/sync_md.py (menu_lines pool + render pool work_complete)
- scripts/omt/net/state.py (fire expected_revision → SpliceError stale_revision)
- scripts/omt/net/cli.py (_fire + --expected-revision/--expected_revision)
- .opencode/plugins/omt_net.ts (OP_ARGS fire + expected_revision)
- .meta/META_HARNESS.omt (STARTUP menu line + agents_md 2944) → harnessc build
- tests/scripts/omt/test_net_menu.py (new, ×6)
- tests/scripts/omt/test_omt_docs_drift_pins.py (AGENTS_BUDGET 2944)
- AGENTS.md + opencode.jsonc (GENERATED via build)

## Deferred

- test_omt_docs_drift_pins.py:22 docstring still cites 2816 (comment only, unenforced;
  left to respect one-edit-per-file round — fold into next harness round).
- WORK.md Tasks not re-rendered from pool net (D4): pool render omits per-feature rows
  (identity in overlay+ledger per D20) — re-render would wipe the pending list; menu is
  served from probe + dry-run render instead.
- 042/043/044 optionals still scaffolded-pending; 001/002 unscoped (D1 out-of-scope).
