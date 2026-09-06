# Feature 059: Harness Tiered Template

> **Status:** [ ] Not started
> **Created:** 2026-09-06
> **WORK.md task:** <!-- link the matching line in WORK.md -->

---

## Summary

Wave 5 (D1+D2+D3) of meta_harness_6: `harnessc init --tier 1|2|3` scaffolds a
working tiered harness (policy filtered, runtime copied), `@var
stack_profile` drives `mvc_check --profile`, and `harnessc build` emits
per-tier `GETTING_STARTED.md`. The future-project payoff of the program.

## Scope (one sentence — what "done" looks like)

Tier-1 init produces a working harness in a fresh tmp repo (deny/protect/
phase/TDD/ledger live, check green, onboarding clean) with T2/T3 supersets,
stack profiles, and onboarding emission — full suite green, budgets green.

## Task type

major_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_059.harness_tiered_template/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_059.harness_tiered_template/analysis_001_tiered_template.md` | [x] |
| Design | Design doc | `4.design/features/feature_059.harness_tiered_template/design_001_tiered_template.md` + `operation_spec_001_init_ops.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_059.harness_tiered_template/implementation_notes.md` | [x] |
| Testing | Test report | `6.testing/features/feature_059.harness_tiered_template/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
