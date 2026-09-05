# Feature 043: Meta Net Dashboard

> **Status:** [x] Done 2026-09-05 (major_feature, meta_harness_concurrent phase-2 2/3)
> **Created:** 2026-08-30
> **WORK.md task:** `feature_043.meta_net_dashboard` row (net-rendered Tasks block)

---

## Summary

Static-build war-room dashboard for the harness concurrency net (IDEA-002 §6,
PROJECT.md roadmap #5): a read-only studio view over a build-time snapshot
(live net graph via `toFlowGraph` reuse, deadlock/blocked-place highlight,
revision slider over ledger-replayed markings, pool/resource status) —
no live server, no editor changes, no new tool.

## Scope (one sentence — what "done" looks like)

`npm run build` in petri-net-studio emits a standalone dashboard page from a
ledger-replay snapshot (fail-closed on replay mismatch) with graph + deadlock
highlight + revision slider green in vitest and the sentinel bridge.

## Task type

major_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_043.meta_net_dashboard/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_043.meta_net_dashboard/analysis_001_reuse_and_replay.md` | [x] |
| Design | Design doc | `4.design/features/feature_043.meta_net_dashboard/design_001_snapshot_dashboard.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_043.meta_net_dashboard/implementation_001_tdd_cycles.md` | [x] |
| Testing | Test report | `6.testing/features/feature_043.meta_net_dashboard/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
