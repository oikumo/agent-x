# Implementation Notes — feature_057.gate_budget_ceremony_meter (Wave 3/B1+B2)

> meta_harness_6 · minor_feature · 2026-09-06 · Programming→Testing→Done

## What shipped

**B1 gate_budget** — `@budget gates max=12` (the count is 10 now; the eval
counted 12 at review time) rides the generic budget loop: past max is a build
error (message speaks counts — `13 gates > 12 gates` — not bytes). Net-zero
policy: reaching the cap warns (never errors) with skip-frequency retirement
advice — the most-skipped gate is the toll-booth candidate (merge/simplify),
bypassable (`skip_ok`) zero-skip gates are dead-weight watch. Attribution via
`SKIP_SCOPE_TO_GATES` (tests→g.tests, nav→g.nav, src→g.phase, all→g.net).

**B2 ceremony_meter** — per-task_type median of agent-issued ledger records
(`q|think_consult|skip|tdd|tdd_testlist`; system `net_*|project_*|complete`
records are session noise, not ceremony) before the session's first phase
record. Sessions without a session id or without a phase carry no attributable
ceremony. Alarm (warning, never error) when the bug_fix median > 3.

Both checks mirror in `omt_status.ts` (`gateBudget()` / `ceremonyMeter()`,
exported for probes) as two default-output lines + `gate_budget` / `ceremony`
metadata. NO new @tool/@doc/@msg, NO schema growth on `omt_status`.

## Surface (3 harness files + e2e, receipt round-robin; tests via canary skip)

1. **`.meta/META_HARNESS.omt`** (round 1, one edit): `@budget gates max=12`
   after `tool_args`. Cost analysis up front: `@budget` records are NOT
   nav-indexed (`render_nav_index` only takes doc/flow/xref/tool/msg), so the
   new record is nav-free — nav_index stayed 63900/64000; ir_json +17 B.
2. **`scripts/omt/harnessc.py`** (rounds 1–2, one bash transform each):
   `"gates"` joins `MEASURABLE_BUDGETS` (the closed set — the unknown-id test
   still passes); `measure_budgets` counts `c.of("gate")`; B1+B2 section
   (`gate_skip_counts`, `gate_retirement_candidates`, `ceremony_stats` pure;
   `_read_repo_ledger_records` follows the A2 audit-the-repo precedent —
   deliberately NOT `OMT_LEDGER_PATH`-aware; `check_gate_retirement` +
   `check_ceremony_alarm` warnings-only, wired into `run_all_checks`).
3. **`.opencode/plugins/omt_status.ts`** (round 1, one bash transform):
   `SKIP_SCOPE_TO_GATES` / `CEREMONY_KINDS` / `CEREMONY_BUG_FIX_ALARM`
   mirrors + exported helpers + two status lines. The A4 ledger-write-free pin
   holds (helpers only read).
4. **`tests/scripts/omt/test_omt_harness_e2e.py`** (check 17, receipt-exempt):
   pins `@budget gates max=12`, the measurable id, the three Python helpers,
   the exported TS helpers and the ceremony line literal.

## Rounds & incidents

- **R1**: .omt + harnessc.py + omt_status.ts + e2e + new test dir →
  check green (`gates: 10/12 OK`) → 15/17 new tests → e2e refresh.
- **R2** (after refresh): two catches from the feature's own tests —
  (1) `check_gate_retirement` read the cap from `.payload`, but `@budget`
  carries its value in `attrs["max"]` (`@var` uses payload — the mixed
  convention is now pinned by `test_over_max…` + `test_at_cap…`);
  (2) `×` vs `x` in toll-booth rendering, normalized to ASCII `x`
  everywhere. → 17/17 → check/build green → full suite → e2e refresh.
- **Live-status note** (GOTCHA_TS_NO_RELOAD class): the MCP `omt_status`
  surface loads the plugin at session start, so this session's own status
  calls cannot show the new lines; the bun full-plugin probe (fresh process,
  hermetic ledger + fixture IR) asserts the exact rendered lines instead.
- **Dogfood note**: live ledger right now — gates 10/12 (no warning),
  no bug_fix sessions (alarm silent), toll-booth g.nav, watch g.phase/g.protect.
  This session's own ceremony (4 pre-phase think consults? 0 — phase declared
  first, consults were `omt_nav`/`omt_kb_nav`/reads which are not ledger
  consults) classifies cleanly under the new meter.
