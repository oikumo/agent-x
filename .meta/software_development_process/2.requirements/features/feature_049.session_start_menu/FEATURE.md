# Feature 049: Session Start Menu (D19, rescaffolded from 047 — 047 is tombstone)

> **Status:** [x] Done 2026-09-05 — minor_feature (meta_harness_concurrent D19)
> **Created:** 2026-09-05
> **WORK.md task:** done (pool rev46 active; close via work_complete after omt_complete)

---

## Summary

Session-start actionable menu = the 045 WORK.md render, rev-stamped (D19). The net tracks global state (pool rev46: pending 5/active 1/done 1); nothing turns it into user action at session start. This feature makes the 045 Tasks block (NEXT + Other enabled + Blocked + Resources + Pool, net rev R) the menu: STARTUP reads WORK.md Tasks only, presents options in order, fire verifies R == probe revision else re-renders first (D4 proposal-only).

## Scope (one sentence — what "done" looks like)

DONE = pool-aware menu_lines + stale-rev fire guard + STARTUP instruction presents Tasks menu + round-trip pool vector green, net 98+ green, sentinel green, harnessc 0 err, live rev46+ drift-free.

## Task type

minor_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_049.session_start_menu/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_049.session_start_menu/analysis_001_*.md` | [x] — scope in FEATURE.md (minor_feature declaration-only, §12) |
| Design | Design doc | `4.design/features/feature_049.session_start_menu/design_001_*.md` | [x] — D19-on-pool deltas (menu pool line, NEXT work_complete, stale guard, STARTUP) |
| Implementation | Impl notes | `5.implementation/features/feature_049.session_start_menu/` | [x] — sync_md/state/cli/ts/omt edits (see test report) |
| Testing | Test report | `6.testing/features/feature_049.session_start_menu/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
