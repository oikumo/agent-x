# Feature 042: Goal Net Synthesis

> **Status:** [x] Done 2026-09-05 (minor_feature, meta_harness_concurrent phase-2 1/3)
> **Created:** 2026-08-30
> **WORK.md task:** `feature_042.goal_net_synthesis` row (net-rendered Tasks block)

---

## Summary

Deterministic goal→net template synthesis (IDEA-002 §4, bounded F4): structured
goal bullets compose into a splice-ready fragment (task→chain, dependency→arc,
resource→capacity arc, acceptance→verified place) via `omt_net{op:synthesize}`,
proposal-only on pool nets (D4/D20 15-cap), never auto-applied.

## Scope (one sentence — what "done" looks like)

`synthesize --mutation '<goal-json>'` returns a deterministic splice fragment + cap analysis, read-only on pool nets, live on pre-pool nets behind the conformance gate.

## Task type

minor_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_042.goal_net_synthesis/` | [x] |
| Analysis | Analysis doc | minor_feature declaration only (§12) — scope locked in Design | [x] |
| Design | Design doc | minor_feature declaration only (§12) — pool-aware proposal design in test_report | [x] |
| Implementation | Impl notes | `scripts/omt/net/state.py` (`build_goal_fragment` + `synthesize`) + `cli.py` | [x] |
| Testing | Test report | `6.testing/features/feature_042.goal_net_synthesis/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
