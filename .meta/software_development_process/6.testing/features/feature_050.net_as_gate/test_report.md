# Test report: feature_050.net_as_gate (Alt A Net-as-Gate)

> Type: major_feature · Phases: Analysis → Design → Programming → Testing → Done
> Date: 2026-09-05 → 2026-09-06 · Project: net_enforced_harness (D1–D3 locked)
> Wrap-up session resumed from `.sandbox/pause_2026-09-05c.md` (Phase A diagnosis → fixes applied here)

## Scope (what shipped)

- **g.net:35 BLOCK live** in IR (order 35, between g.tests:30 and g.phase:40), `skip_ok=false`
  — break-glass = `omt_skip{scope:all}` only (D3); scope=nav/tests skips can no longer bypass the net gate.
- Enforcer `g.net` impl calls `uv run scripts/omt/net_check.py gate --path … --session …`
  (fail-closed); dry-run-safe for `omt_q op:plan` (synthetic ctx has no SDK shell).
- `net/gate.py` permission helper, decision order per operation_spec_001:
  break-glass → availability → drift/conflicts → stale-rev → fire-receipt.
- Receipt filter: **only `_start`-suffixed `net_fire` records grant permission**
  (AGENTS.md NEVER: "fire(work_start) required"); 8h window, any session (identity = Phase B).
- `cli.py` gate op live wiring: drift mirrors `_invariant` (net rev vs last ledger net-record rev),
  fail-closed on load error (D3), `expected_revision` flows through → ERR_NET_DRIFT_CONFLICT /
  ERR_NET_STALE_REV / ERR_NET_DOWN reachable in the LIVE enforcer path.

## Wrap-up fixes applied (all specced at pause)

| # | Fix | File(s) |
|---|-----|---------|
| 1 | `invariant` subparser `--expected-revision` (mirror OP_ARGS whitelist) | cli.py |
| 2 | WORK.md Pool line rev52→53 render (fixed at pause via sync net_to_md) | WORK.md |
| 3 | TS fallback seed byte-match `gate(path,session?)` | omt_net.ts |
| 4 | replay: `net_mine` no-mutation skip branch | history.py |
| 5 | `@gate g.net skip_ok=true → false` + harnessc rebuild | META_HARNESS.omt |
| 6 | gate.py DEBUG log block removed (+ `rm .meta/.omt/gate_debug.log`) | gate.py |
| 7 | gate_driver.ts DEBUG block removed (`/tmp/gate_debug.log`) | gate_driver.ts |
| 8 | `_has_recent_fire_receipt` filters `_start`-suffix transitions | gate.py |
| 9 | gate op live wiring (drift + fail-closed + expected_revision) | cli.py |
| 10 | **NEW (found this session):** g.net impl crashed `omt_q op:plan` — synthetic
    GateCtx has `env.$ = {}` → TypeError propagated → fail-open on every
    `@var.net_paths` path. Fixed: dry-run guard (`typeof ctx.env.$ !== "function"` → return). | gate_driver.ts |
| 11 | 043 dashboard snapshot stale (rev 51 vs live 53) → regenerated (rev 53, 54 snaps) | tools/petri-net-studio/src/dashboard/snapshot.json |
| 12 | **POST-DONE (user-directed):** live guard test order-flaky — the live LLM
    occasionally reorders the requested calls (omt_nav first) and R7 T3 defers the
    nav reminder off nav-tool results; assertions made order-agnostic per the
    sessionBootstrap contract (digest → first result; reminder → first non-nav) | tests/scripts/omt/test_omt_live_opencode_guards.py |

## Vectors

- `test_net_gate.py` ×11: 6 original (block-no-receipt / stale-rev / drift / conflicts /
  net-down / break-glass) + 5 new — receipt filter (work_complete-only ledger → ERR_NET_NOT_ENABLED;
  work_start ledger → OK) + CLI gate op (unbootstrapped → ERR_NET_DOWN; bootstrapped + work_start
  receipt → OK; ledger revision mismatch → ERR_NET_DRIFT_CONFLICT). Fixes landed before the new
  tests per pause runbook order (tests are the regression contract — green-on-arrival).
- Regression (all 10 remaining baseline failures green): plugin_args whitelist pin, harnessc
  ×2 (WORK.md canonical + projections fresh + seed byte-match), net_history TestLiveGolden,
  043 dashboard sentinel, fallback-gates IR pin (skip_ok=false alignment), omt_q U2/U11 in both
  `test_omt_q.py` and feature_026 golden smoke.
- **Live gate verification** (env-controlled, real net rev 53): empty ledger →
  `ERR_NET_DRIFT_CONFLICT` (drift precedes receipt per operation_spec — the pause doc's
  `ERR_NET_NOT_ENABLED` expectation described pre-fix code); work_start-only ledger → OK;
  **work_complete-only ledger → ERR_NET_NOT_ENABLED** (receipt filter proven live); real repo → OK.
- **g.net exercised LIVE** by this session's own edit-tool calls on net_paths (work_start receipt
  22:34Z in-window, drift-free rev 53) — the gate ran its own fixed code on every subsequent edit.

## Numbers

- omt suite + feature_043: **430 passed, 0 failed**.
- Full suite (final): **1844 passed, 0 failed** — including the allowlisted-known feature_016
  TestTddCheckCli pair (green in the final run once the TDD window state resolved; they remain
  red-by-design WHILE a tdd-mode phase record is in-window — allowlisted in KNOWN_SUITE_FAILURES)
  and both live opencode guard tests.
- e2e receipt refreshed ×3 this session (round discipline: one edit per file per receipt);
  harnessc build + check → **0 errors** (256 records, budgets OK).

## Files (2-site files via uv-run transform per GOTCHA receipt-round-robin)

- scripts/omt/net/gate.py (receipt filter + DEBUG removal — transform)
- scripts/omt/net/cli.py (invariant flag + gate rewire — transform)
- scripts/omt/net/history.py (net_mine skip)
- .opencode/lib/enforcer/gate_driver.ts (DEBUG removal + dry-run guard — two receipt rounds)
- .opencode/plugins/omt_net.ts (seed `?`)
- .meta/META_HARNESS.omt (skip_ok=false) → harnessc build
- tests/features/feature_050.net_as_gate/test_net_gate.py (+5 tests; moved from
  tests/scripts/omt/ to satisfy the §12 artifact matrix — 11/11 green at the new path)
- tools/petri-net-studio/src/dashboard/snapshot.json (regenerated, rev 53)
- AGENTS.md / opencode.jsonc / harness.ir.json / nav.index.jsonl (GENERATED via build)

## Known limitations (Phase B scope — feature_051.multi_session_concurrency, user-deferred 2026-09-05)

- Receipt is any-session (no session→work binding; D20 overlay map unimplemented, overlay.subnets={}).
- No flock: concurrent sessions race the 3-file bundle read-modify-write.
- WIP=1: agent_attention held start→complete (attention+active=1 invariant).
- `@var.net_paths` (src/, tests/, .opencode/, scripts/omt/) excludes META_HARNESS.omt /
  AGENTS.md / opencode.jsonc — compile-time spec edits gated only by g.receipt.
- WORK.md render not auto-refreshed after fire (staleness class rev52→53 seen 2026-09-05).
