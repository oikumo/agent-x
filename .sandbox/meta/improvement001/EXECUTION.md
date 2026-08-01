# EXECUTION — improvement001 / OPT-A (2026-08-01)

## Selected
OPT-A — Slim the AGENTS.md projection (user-selected via the loop's step-5 question).

## Changes
- `scripts/omt/harnessc.py` (`render_agents`): removed the 18-row `## Tools` table
  (`tools`/`tool_rows`/`short()` helper deleted), replaced with a one-line pointer:
  `18 omt_* tools — descriptions ride the system-prompt schemas; catalog: omt_nav{query:"CMD_", tag_type:"CMD"}`.
- `AGENTS.md`: REGENERATED via `harnessc.py build` (never hand-edited).
- `.meta/META_HARNESS.md`: dated state note appended (loop step 7; stub is not compiled).

## Result
| Metric | Before | After |
|---|---|---|
| AGENTS.md | 4273 B (83% of 5120 budget) | **2941 B (57%)** |
| Per-turn saving | — | **−1332 B ≈ −330 tokens every turn** |

## Verification
- `harnessc.py check` — 226 records, 0 errors ✓
- `harnessc.py check --verify-projections` — no drift ✓
- `tests/scripts/omt/test_omt_harness_e2e.py` — pass (receipt refreshed ×2) ✓
- `tests/scripts/omt` — 116/116 ✓
- Full suite — 1062 passed + 3 failed (all 3 = allowlisted feature_018 KNOWN_SUITE_FAILURES) ✓
- Budget report: agents_md 2941/5120 OK; all other budgets OK ✓

## Process notes
- Phase: `omt_phase{task_type:refactor, phase:Programming}` (declaration-only artifact class).
- Receipt-guard round-robin observed exactly as documented (one edit per e2e receipt):
  2 receipt refreshes needed for 3 sequential edits to harnessc.py. This validates
  IMPROVEMENT_OPTIONS OPT-G (harness-edit session mode) as the next high-ROI candidate.
- No-commit-without-request honored: changes left uncommitted for user review.

## Loop-step-7 reconciliation
The loop's "update ./meta/META_HARNESS.md" predates R8 (the file is now a retired,
non-compiled stub; truth = `.meta/META_HARNESS.omt` + projections). Honored by a dated
state note on the stub; the machine-consumed state lives in the rebuilt projections.
