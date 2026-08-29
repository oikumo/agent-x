# Feature 035: Studio V2 Analysis

> **Status:** [x] Done — 2026-08-29
> **Created:** 2026-08-23
> **WORK.md task:** `- [x] **feature_035.studio_v2_analysis**` (petri_net_studio roadmap #4)

---

## Summary

Studio v2: TS analysis engine port (reachability, deadlocks, bounds, liveness, SCCs, exact P/T-invariants — exact-parity with `src/agentx/model/petri_net/analysis.py`), deterministic conformance-vector generator (D8 re-lock), and a no-overclaim analysis dashboard (D10). Scope LOCKED v1.1; design_001 blueprint; B11 manual red→green under Vitest (A11 precedent).

## Scope (one sentence — what "done" looks like)

`tools/petri-net-studio/` v2 — exact TS analysis port + conformance vectors in `shared/petri-net/conformance/analysis-v1/` + no-overclaim AnalysisPanel with max_states dial; Vitest green, build + independence + agentx suite green, zero `src/`/`shared`-contract edits.

## Task type

major_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_035.studio_v2_analysis/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_035.studio_v2_analysis/analysis_001_analysis_port.md` | [x] |
| Design | Design doc | `4.design/features/feature_035.studio_v2_analysis/design_001_studio_v2_analysis.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_035.studio_v2_analysis/implementation_001_manual_cycles.md` | [x] |
| Testing | Test report | `6.testing/features/feature_035.studio_v2_analysis/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
