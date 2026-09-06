# Test Report — feature_057.gate_budget_ceremony_meter (Wave 3/B1+B2)

> meta_harness_6 · minor_feature · 2026-09-06 · Tester: build agent (same session)

## Scope

`@budget gates max=12` net-zero policy + skip-frequency retirement candidates
(B1); pre-unlock ceremony medians per task_type + bug_fix>3 alarm (B2);
mirrored Python/TS surfaces with no schema growth and all byte budgets green.

## Evidence

- **New suite** `tests/features/feature_057.gate_budget_ceremony_meter/
  test_gate_budget_ceremony.py`: **17 passed / 0 failed** —
  4 B1 static pins (record exists, count 10/12, over-max errors with gate
  unit, at-cap warns / under-cap silent), 4 retirement matrices (attribution,
  stale-window exclusion, unknown-scope/ts ignored, toll + dead-weight,
  no-skip case), 4 ceremony matrices (odd/even medians, system kinds
  excluded, missing session/ts skipped, alarm fires past 3 / silent at 3),
  1 TS-mirror bun probe on the REAL status plugin (hermetic ledger + fixture
  IR: exact `Gates 4/12 …` / `Ceremony median … ⚠ over alarm` lines +
  metadata), 3 static pins (helpers present/synced, read-only, no arg growth).
- **Full suite: 1951 passed / 0 failed** (868 core + 1083 features; 1934
  pre-existing + 17 new), empty allowlist (`KNOWN_SUITE_FAILURES` still `{}`).
- **`harnessc check` 0 errors, 261 records, all 12 budgets green**
  (`gates: 10/12 OK`; nav_index 63900/64000, tool_args 2271/2304,
  tool_schemas 1750/1792 — untouched); **build OK** (5 projections).
- **e2e receipt refreshed twice** (round 1 after transforms, round 2 after
  fixes — check 17 pins the wiring); live `omt_status` preflight green.
- **No live-ledger warnings introduced**: gates 10 < 12, no bug_fix ceremony
  data, skip-override alarm unchanged.

## Deviations

- Tests/ writes via `omt_skip{scope:"tests", purpose:"canary"}` (this
  surface exposes the tool — no bash-path workaround needed); one skip
  covered all tests/ edits (no re-declare, so no shadow).
- Round-2 fix round after the round-1 e2e refresh (receipt round-robin —
  one transform per harness file per round, kept manually for the bash path).
- Live `omt_status` output cannot show the new lines in-session
  (TS no-reload); covered by the bun full-plugin probe instead (see notes).
