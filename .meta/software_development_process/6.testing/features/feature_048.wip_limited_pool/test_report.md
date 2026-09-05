# Test report — feature_048.wip_limited_pool (D20 15-place cap)

> Type: minor_feature · Phases: Programming → Testing → Done (declaration only, §12)
> Date: 2026-09-05 · Live net: rev 45 (12 places, pool pending=6/active=0/done=1)

## Scope

Generic WIP pool (3 pool places + 5 resources + 3 boundary +1 archive = 11–12 places,
2 transitions) replaces per-feature partitions. Code follow-up after the rev44–45
dogfood migration: `state.py` pool-aware (`is_pool_net`, sync empty per-feature
proposals on pool nets, pool-aware `resource_report` holders/conflicts, 15-place
cap guard in splice add/undo), `sync_md.py` render reads `work_*` counts
(`Pool: pending=… active=… done=… (places N/15)`).

## Vectors

- New `tests/scripts/omt/test_net_pool.py` ×10: pool detect (pool vs skeleton),
  sync empty on pool (+pool info pending/places/cap) vs per-feature proposes on
  skeleton, cap reject at 16 (`place_cap_exceeded`) vs edge-15 ok, idle free /
  active `holders:["pool"]` / blocked `conflicts:[pool/work_start←agent_attention]`,
  render pool line vs non-pool absent — **10/10 green**.
- Existing net suite (sync/sync_md/resources/splice/state/cli/engine/conformance):
  **92 pre-existing green** (33 sync+sync_md+resources, 59 splice+state+cli+engine+conformance),
  full `tests/scripts/omt/` **364/364 green** (was 361+3 budget/link failures → fixed).
- Full sentinel: **1778 passed** (was 1767 +10 pool +1 budget-pin refresh), 0 failed.
- Harnessc: `build OK — 253 records → 5 projections`, `check OK — 0 errors`
  (fixes: 047 mis-scaffold tombstone `feature_047.wip_limited_pool/FEATURE.md`,
  `@budget work_md 7680→8192` + `WORK_BUDGET 7168→8192` in the same round).

## Live dogfood (read-only + sync proposal, D4 — never applied)

- `probe` rev 45: 12 places, marking pending=6/active=0/done=1, enabled `[work_start]`.
- `invariant`: drift-free 45=45, resources 5/5 free, conflicts [].
  (`live_marking_invariants_hold=false` pre-existing since rev 43, not introduced.)
- `sync proposal`: `add_subnets:[] disable:[] resources:[]` + `pool:{pending:6
  active:0 done:1 places:12 cap:15 reality:47 features pending:5 active:1 done:6}`
  (was 7–8 stale per-feature adds pre-fix — MUST NOT apply, breaks ≤15 cap).
- `sync_md` render (dry-run only — do NOT write to WORK.md, would wipe feature rows
  until 047 menu lands): `NEXT: work_start`, `Resources: 5/5 free`,
  `Pool: pending=6 active=0 done=1 (places 12/15)`.

## Notes

- Scaffold collision: `new_feature.py` auto-assigned `047` (planned D19 number free on
  disk) → renamed to `048` per locked D20; stale `047` ledger link kept green via
  tombstone dir (no unlink primitive, append-only ledger). Planned `047.session_start_menu`
  keeps its number in the roadmap; its scaffold takes the next free number.
- WORK.md Tasks stays hand-maintained (net_to_md dry-run only on pool nets).
  Pool counts trail reality by one fire (pending 6 vs 5+1) — fire `work_start` to align.
