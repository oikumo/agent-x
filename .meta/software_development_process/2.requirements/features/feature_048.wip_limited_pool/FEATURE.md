# Feature 048: Wip Limited Pool

> **Status:** [x] Done 2026-09-05
> **Created:** 2026-09-05
> **WORK.md task:** `feature_048.wip_limited_pool` (D20 15-place cap, generic WIP pool)

---

## Summary

Generic WIP pool replaces per-feature partitions to enforce META_NET ≤15 places: 3 pool places (`work_pending/active/done`) + 5 resources + 3 boundary (+1 archive) = 11–12 places, 2 transitions (`work_start/complete`); identity in overlay+ledger.

## Scope (one sentence — what "done" looks like)

Live net stays ≤15 places with pool-aware sync (no per-feature adds on pool net), pool-aware resource_report and sync_md render, cap enforced, sentinel green.

## Task type

minor_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_048.wip_limited_pool/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_048.wip_limited_pool/analysis_001_*.md` | [ ] |
| Design | Design doc | `4.design/features/feature_048.wip_limited_pool/design_001_*.md` | [ ] |
| Implementation | Impl notes | `5.implementation/features/feature_048.wip_limited_pool/` | [x] (`scripts/omt/net/state.py` + `sync_md.py` pool-aware) |
| Testing | Test report | `6.testing/features/feature_048.wip_limited_pool/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
