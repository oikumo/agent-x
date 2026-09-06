# Feature 050: Net As Gate

> **Status:** [x] Done 2026-09-06 — major_feature (net_enforced_harness, Alt A)
> **Created:** 2026-09-05
> **WORK.md task:** done (work_complete fired rev53 23:24Z; wrap-up completed per `.sandbox/pause_2026-09-05c.md` runbook)

---

## Summary

Net-as-Gate makes omt_net rev 51 the permission-to-act for harness usage: fire-required before src/tests/harness edits, stale-rev + drift/conflict hard-block, WORK.md canonical via sync.

## Scope (one sentence — what "done" looks like)

Done = g.net:35 BLOCK live, fire-required enforced, drift/conflict block (not log), WORK.md check green, e2e + sentinel + dogfood rev+1 drift-free.

## Task type

major_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_050.net_as_gate/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_050.net_as_gate/analysis_001_net_gaps.md` | [x] |
| Design | Design doc | `4.design/features/feature_050.net_as_gate/design_001_net_gate.md` + `operation_spec_001_net_gate.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_050.net_as_gate/` | [x] — gate.py/gate_driver.ts/cli.py/history.py/omt_net.ts/.omt edits (see test report §Files) |
| Testing | Test report | `6.testing/features/feature_050.net_as_gate/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
