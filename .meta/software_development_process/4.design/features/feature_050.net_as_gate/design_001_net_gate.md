# Design 001 — Net-as-Gate (g.net:35)

> feature_050.net_as_gate · major_feature · Design · 2026-09-05 · project net_enforced_harness

## Goal
Make `omt_net` rev 51 the permission-to-act: no `src/tests/harness-surface` edit without enabled-transition + successful `fire --expected-revision`, drift/conflict hard-block.

## Changes (minimal blast radius)
1. **Enforcer `g.net:35 BLOCK skip_ok=false`** (`lib/enforcer/*`, `omt_enforcer.ts`): pre-tool hook `probe` → must show `work_start` (or `f{N}_start`) enabled + caller holds `agent_attention/src_edit_capacity` token; then `fire` must succeed. Order between `g.tests:30` and `g.phase:40`. New `ERR_NET_NOT_ENABLED / ERR_NET_STALE_REV / ERR_NET_DRIFT_CONFLICT`. Ledger records `net_fire` receipt (like e2e receipt).
2. **omt_net proxy hardening** (`omt_net.ts`, `scripts/omt/net/cli.py`): stale-rev check on ALL ops (extend feat_046 whitelist fix); `fire` adds conformance regression (no cap exceed, invariants hold); fail-closed policy: net-down/unknown → BLOCK (with `fail_open=false` flag) + break-glass `omt_skip{scope:all, reason}` expiring 8h + audit to `harness.net.drift.jsonl`.
3. **WORK.md canonical** (`sync_md.py`, `harnessc check`): Tasks block writable only via `sync net_to_md`; hand-edit → `harnessc` error (like work_done_max). `menu_lines` already pool-aware (feat_049) becomes the ONLY menu source.
4. **Fail-open closures**: fix TS no-reload (GOTCHA_TS_NO_RELOAD) via version-hash reload check; close bash-evasion by moving receipt-round check into `harnessc check` post-pass (not just edit-hook).

## Invariants preserved
D2 add-only model, D4 proposal-only for splice/sync (fire is the only auto-applied mutator), D16 net-owns-state/gates-own-enforcement, D19 menu order, 15-place cap, cap=1 resources, budgets zero-churn (F32).

## Test plan (TDD Programming)
`test_net_gate.py`: fire-required blocks edit; stale-rev blocks; drift/conflict blocks; net-down blocks + break-glass passes with expiry; receipt-round + g.net interaction; WORK.md hand-edit fails harnessc. E2E: 2 rounds (clean edit + blocked edit), sentinel, dogfood rev+1 drift-free.

## Risks
Availability (net-down blocks all) → mitigated by break-glass + health probe. Token +1 call/edit → mitigated by windowed `net_fire` receipt (8h like unlock window). Cached plugin → mitigated by reload check.
