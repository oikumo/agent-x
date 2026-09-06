# Test Report — feature_053.net_gate_concurrency_predicate (C1)

> meta_harness_6 Wave 2 / C1 · Testing 2026-09-06

## Acceptance criteria → results

| Criterion (evaluation §5 C1) | Result |
|---|---|
| New `@pred net_marking()` wraps the probe marking | ✅ `.omt @pred net_marking : net_marking(active>1)`; `PREDS` extended; `harnessc check` OK (259 records, 0 errors); e2e check 13 pins `@pred`, the threshold literal, `is_concurrent`, `live_marking` forwarding, and the TS mirror |
| g.net engages only when `active>1` | ✅ concurrent (`work_active=2`, or 2× `f{N}_active`) without receipt → `ERR_NET_NOT_ENABLED`; with `work_start` receipt → `OK`; live CLI op mirrors both |
| Solo reverts to phase-gate only | ✅ solo/idle (`work_active ∈ {0,1}`) without receipt → `OK solo`; single subnet holder stays solo; live solo bundle + empty ledger via CLI → `OK` |
| Fail-closed preserved | ✅ unreadable bundle → engage; drift / net-down / stale-rev still BLOCK even when solo (checked before the predicate) |
| feature_051 stays deferred | ✅ no multi-session machinery touched; predicate sleeps the gate until concurrency is real |
| Full suite green, budgets green, receipt fresh | ✅ **1879 passed, 0 failed** (1866 + 13 new, empty allowlist); build OK, all 12 budgets green; e2e receipt refreshed |

## Runs

| Command | Result |
|---|---|
| `uv run pytest tests/features/feature_053... tests/features/feature_050... -q` | 24 passed (13 new + 11) |
| `uv run pytest tests/scripts/omt/test_harnessc.py .../feature_050/... .../feature_053/... test_omt_net_plugin_args.py -q` | 64 passed |
| `bun build --target=bun plugins/omt_enforcer.ts` (TS graph incl. gate_driver) | bundled 82 modules, no errors |
| `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` (receipt refresh, round 1) | 1 passed |
| `uv run scripts/omt/harnessc.py check` | OK — 259 records, 0 errors |
| `uv run scripts/omt/harnessc.py build` | OK — 5 projections, all 12 budgets green |
| `uv run pytest -q` (full) | **1879 passed, 0 failed** |

## Notes

- Solo-session ceremony after C1: no `fire(work_start)` required, no
  rev advance, no drift risk from the gate path — the net goes dormant until
  a second active work appears. `work_complete` before pausing stays valid
  (pool `done` accounting), just no longer gate-mandated for solo.
- Compiler lesson: `@pred` payloads must start with a closed-vocabulary
  builtin (`harnessc` errored on the new pred until `PREDS` gained
  `net_marking`) — new preds are a two-site change (`.omt` + `PREDS`).
