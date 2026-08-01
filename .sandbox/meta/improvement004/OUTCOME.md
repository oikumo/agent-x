# improvement004 — OUTCOME (2026-08-01)

**Selected:** OPT-A — AGENTS.md diet round 2 (tables → nav pointers).
**Feature slug:** improvement004.opt_a_agentsmd_diet · phase lifecycle Done.

## Changes
- `scripts/omt/harnessc.py` render_agents: §12 table / TDD / Tools / NAV / THINK /
  QuickRef sections → 4-bullet "Process (full rules on demand via nav)" block
  (§12 line data-driven from @phase; TDD cycle from @fsm tdd).
- `.meta/META_HARNESS.omt`: @budget agents_md 5120 → 2560.
- `tests/scripts/omt/test_omt_docs_drift_pins.py`: AGENTS_BUDGET 5120 → 2560;
  docstring budgets fixed (also stale WORK/scratchpad KiB from 002/003).
- `tests/scripts/omt/test_omt_harness_e2e.py`: assertion retargeted to surviving
  "Think gate" pointer.
- `.meta/META_HARNESS.md`: stub state note appended (loop step 7).
- Regenerated: AGENTS.md, harness.ir.json, nav.index.jsonl, opencode.jsonc blocks,
  harness.report.

## Result
- **AGENTS.md 2941 → 2097 B (−844 B ≈ ~210 tok saved EVERY TURN)**; budget 2097/2560.
- Verified: harnessc check 0 err · build + --verify-projections no drift · e2e receipt
  refreshed · tests/scripts/omt 116/116 · full suite 1062 passed + 3 known feature_018.

## Next-loop candidates (from IMPROVEMENT_OPTIONS.md, unselected)
OPT-B tool consolidation 18→8 (biggest per-turn win, high effort) · OPT-C WORK.md DONE
rotation · OPT-D HDL-2 data-driven gates · OPT-E token telemetry · OPT-F compact status ·
OPT-G omt_start bootstrap.
