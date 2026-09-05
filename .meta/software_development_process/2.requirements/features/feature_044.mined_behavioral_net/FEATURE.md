# Feature 044: Mined Behavioral Net

> **Status:** [x] Done 2026-09-05 (minor_feature, meta_harness_concurrent phase-2 3/3)
> **Created:** 2026-08-30
> **WORK.md task:** <!-- link the matching line in WORK.md -->

---

## Summary

Ledger-mined behavioral net (IDEA-004 v2, the upward complement to synthesis):
the ledger STORE (hot + all rotated archives) is read as an event log and an
observed P/T net is discovered with a simplified α-variant (`miner.py`, stdlib-only)
via `omt_net{op:mine}` — the single D7-gated extension of the closed op enum —
so intended-vs-observed behavioral drift, empirical invariants, and next-event
frequencies are mechanical reports, proposal-only (D4), never auto-applied.

## Scope (one sentence — what "done" looks like)

`mine` returns an observed-net draft (fragment + drift + empirical invariants +
manifest) over 61 live cases, read-only on the pool net, ledger-audited.

## Task type

minor_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_044.mined_behavioral_net/` | [ ] |
| Analysis | Analysis doc | `3.analysis/features/feature_044.mined_behavioral_net/analysis_001_*.md` | [ ] |
| Design | Design doc | `4.design/features/feature_044.mined_behavioral_net/design_001_*.md` | [ ] |
| Implementation | Impl notes | `5.implementation/features/feature_044.mined_behavioral_net/` | [ ] |
| Testing | Test report | `6.testing/features/feature_044.mined_behavioral_net/` | [ ] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
