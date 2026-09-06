# Implementation 001 — Net-as-Gate (g.net:35)

> feature_050.net_as_gate · major_feature · Programming · 2026-09-05 → 2026-09-06 · project net_enforced_harness
> Companion: `design_001_net_gate.md` + `operation_spec_001_net_gate.md` (4.design) · `test_report.md` (6.testing)

## What was built (file map)

| Component | File | Role |
|---|---|---|
| Gate helper | `scripts/omt/net/gate.py` | Pure-Python permission check: break-glass → availability → drift/conflicts → stale-rev → fire-receipt; `_start`-suffix receipt filter (8h window, any session) |
| CLI op | `scripts/omt/net/cli.py` (`gate` op) | Live wiring: drift mirrors `_invariant` (net rev vs last ledger net-record rev), fail-closed on load error (D3), `expected_revision` pass-through; `invariant` gains `--expected-revision` (OP_ARGS mirror) |
| Entry shim | `scripts/omt/net_check.py` | `uv run scripts/omt/net_check.py gate …` — the enforcer call site |
| Enforcer hook | `.opencode/lib/enforcer/gate_driver.ts` (`g.net` impl) | Shells `net_check.py gate --path --session`; dry-run guard for omt_q plan (synthetic ctx has no SDK shell) |
| Spec | `.meta/META_HARNESS.omt` (`@gate g.net … order=35 skip_ok=false`) | IR source of truth; break-glass = `omt_skip{scope:all}` only |
| Replay | `scripts/omt/net/history.py` | `net_mine` added to the no-mutation skip branch (draft-only, D4) |
| Proxy seed | `.opencode/plugins/omt_net.ts` | TS fallback description byte-matches the .omt payload (`gate(path,session?)`); OP_ARGS whitelist for all ops |
| Tests | `tests/features/feature_050.net_as_gate/test_net_gate.py` | ×11: 6 original + 5 wrap-up (receipt filter ×2, CLI gate op ×3) |

## Key decisions made during implementation

- **skip_ok=false in the .omt** (not just the TS fallback): the IR is the functional source —
  with `skip_ok=true` ANY session skip (scope=nav/tests) bypassed the net gate; only
  `omt_skip{scope:all}` (break-glass, 8h expiry, ledger-audited) may bypass (D3).
- **Receipt filter = transition suffix, not name**: any `*_start`-suffixed transition grants
  permission (future `f{N}_start` transitions qualify automatically); `work_complete` etc. do not.
- **Drift-before-receipt ordering** (operation_spec): an empty/corrupt ledger is DRIFT
  (`ERR_NET_DRIFT_CONFLICT`), not merely "no receipt" — a healthy bundle always has ≥1 net record.
- **Fail-closed on ANY load error** in the gate op (not just `NetNotBootstrappedError`) — net-down,
  unbootstrapped, and IO errors all BLOCK (D3).
- **Dry-run guard instead of a synthetic shell**: omt_q's `op:plan` builds `env.$ = {}`; the g.net
  impl returns early (gate still fires in the predicted chain; verdict needs the live path) rather
  than emulating the SDK shell API.

## Wrap-up session (2026-09-06) — applied `.sandbox/pause_2026-09-05c.md` runbook

All 5 specced test-failure root causes + 5 code defects fixed, +1 new defect found & fixed
(omt_q plan fail-open on net_paths — see test report §Wrap-up fixes). Edit rounds respected the
receipt round-robin (2-site files via uv-run transform; e2e receipt refreshed ×3).

## Known limitations (Phase B — feature_051, user-deferred)

Any-session receipt (no session→work binding), no flock on the bundle RMW, WIP=1,
`@var.net_paths` excludes compile-time spec files (g.receipt only), WORK.md render not
auto-refreshed after fire.
