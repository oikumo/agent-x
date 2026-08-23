# Feature 034: Studio V1 Editor

> **Status:** [x] Testing complete 2026-08-23 — SHIP (Vitest 170/170, tsc clean, independence OK, static build + preview smoke green, agentx suite 1637+2 KNOWN_SUITE_FAILURES tolerated); evidence @ `6.testing/features/feature_034.studio_v1_editor/test_report.md`
> **Created:** 2026-08-23
> **WORK.md task:** `- [x] **feature_034.studio_v1_editor**` (WORK.md §Tasks)
> **Project:** `.projects/meta/petri_net_studio/PROJECT.md` — roadmap feature #3 (scope LOCKED v1.1); depends on #1 ✅

---

## Summary

Scaffold + ship `tools/petri-net-studio/` — the standalone browser app: Vite +
React + TypeScript + React Flow (@xyflow/react) + Zustand + Vitest (D2). v1 =
visual editor (places/transitions/weighted arcs, token/weight editing), a
TypeScript port of the library's model layer (`model.py` semantics exactly),
click-to-fire simulation with enabled-transition highlighting, and petri-net-json
v1 import/export with full L1+V1–V6 validation and canonical §8 serialization
(byte-identical with Python `io.py`). Pure browser, static build (D1); zero
agentx/harness imports (independence enforced by a lint/test check).

## Scope (one sentence — what "done" looks like)

Done when the app builds as static files and the walking skeleton works in-browser:
draw → edit tokens/weights → fire enabled transitions by click → export → re-import
the identical canonical JSON — with Vitest green on the engine + io ports (shared
examples as golden canonical bytes) and the independence check passing.

## Task type

major_feature (design doc required §12; TDD pipeline at Programming — NOTE: `omt_tdd`
is pytest-shaped, this feature's runner is Vitest; manual red→green with evidence
recorded here, see pause doc "Open decision")

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_034.studio_v1_editor/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_034.studio_v1_editor/analysis_001_port_sources.md` | [x] |
| Design | Design doc | `4.design/features/feature_034.studio_v1_editor/design_001_studio_v1_editor.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_034.studio_v1_editor/implementation_001_manual_cycles.md` | [x] |
| Testing | Test report | `6.testing/features/feature_034.studio_v1_editor/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
