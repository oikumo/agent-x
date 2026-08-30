# Feature 036: Studio V3 Graph

> **Status:** [ ] Not started
> **Created:** 2026-08-29
> **WORK.md task:** <!-- link the matching line in WORK.md -->

---

## Summary

Standalone browser-based reachability-graph explorer (auto-layout via elkjs), firing-sequence animation, liveness/SCC views, conformance-suite runner wired into Vitest, and example gallery — featuring pure-projection (`projectGraph`), sequence stepping (`markingAt`/`sequenceSteps`), additive view state (`graphVisible`/`toggleGraph`), gallery of 8 conformance fixture nets with `loadExample`, and analysis-compatible no-overclaim badges. Typescript port of the weighted P/T Petri-net engine semantics. Built as an independent web app (`tools/petri-net-studio/`) sharing only the versioned JSON format (`shared/petri-net/`).

## Scope (one sentence — what "done" looks like)

All design_001 §11 cycles complete (1–7): engine `markingFromKey` export + analysis additive, projection GREEN 7/7, animation GREEN 8/8, store+gallery GREEN 56/56+8/8, UI (styles.css §9 → build + preview smoke 200×3), conformance runner (`npm run conformance` 3-step OK: regenerate + byte-identical + 10/10 Vitest suite), sentinel green; 274/274 Vitest; `tsc --noEmit` clean; `npm run build` green; preview smoke 200×3; `npm run check-independence` green; sentinel passes with canary-approval skip logged.

## Task type

major_feature

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/features/feature_036.studio_v3_graph/FEATURE.md` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_036.studio_v3_graph/analysis_001_graph_explorer.md` | [x] |
| Design | Design doc | `4.design/features/feature_036.studio_v3_graph/design_001_studio_v3_graph.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_036.studio_v3_graph/implementation_001_manual_cycles.md` | [x] |
| Testing | Test report | `6.testing/features/feature_036.studio_v3_graph/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
