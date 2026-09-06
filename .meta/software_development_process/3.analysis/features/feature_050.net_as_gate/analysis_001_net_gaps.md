# Analysis 001 — Net enforcement gaps

> feature_050 · 2026-09-05 · summarizes sandbox deep analysis for traceability

## Evidence
- probe rev51 enabled=[work_start] pending:3/active:0/done:4; invariant drift:false 51==51 5/5 ok conflicts:[] bounded:true.
- Enforcer `gate_driver.ts:227-350` order g.nav:0/g.protect:10/g.receipt:20/g.tests:30/g.phase:40/g.think:50/g.kb:55/g.mvc:60/g.tdd_after:70; DENY in opencode.jsonc.
- Net CLI `scripts/omt/net/cli.py`: probe/fire/splice/sync/synthesize/mine/invariant; D4 proposal-only for splice/sync/synthesize/mine; fire marking-only + stale-rev refuse.
- Bypasses: omt_skip logged; read+src exempt silent; docs/.projects ungated; bash-evasion; cached-TS; fail-open 105/147/380; drift kb:515.

## Gap
Enforcer blocks without net; net advises without blocking. No fire-required, no drift-block, WORK.md hand-editable, splice voluntary.

## Decision
Alt A Net-as-Gate: add g.net:35 BLOCK skip_ok=false querying net; fail-closed + break-glass expiring; WORK.md canonical via sync; TS-reload fix.
Full detail: `sandbox/meta/improvement001_net_enforcement/IMPROVEMENT_OPTIONS.md`.
