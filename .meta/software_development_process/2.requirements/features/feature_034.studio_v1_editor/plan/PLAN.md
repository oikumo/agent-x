# PLAN — feature_034: Studio V1 Editor

> Task type: **major_feature** · See `omt_agent_guide.md §12` for the required artifacts.
> **DONE 2026-08-23** — SHIP; evidence @ `6.testing/features/feature_034.studio_v1_editor/test_report.md`.

## Objective

Static-building React+TS app in `tools/petri-net-studio/`: draw → edit → click-to-fire → export/import byte-identical canonical petri-net-json, engine semantics ported exactly from `model.py`, zero agentx/harness imports, Vitest green.

## Steps

- [x] Analysis — port sources: `src/agentx/model/petri_net/model.py` + `io.py`; reference test matrix: `tests/model/petri_net/test_io.py` (59 tests); contract: `shared/petri-net/FORMAT.md` §6–§8
- [x] Design — `4.design/features/feature_034.studio_v1_editor/design_001_studio_v1_editor.md` (then `omt_phase{phase:"Design", design_doc:…}`)
- [x] Implementation — npm scaffold (network OK: npm 11.11.0/node 24.14.1) → `src/engine/model.ts` → `src/engine/io.ts` → React Flow editor UI → import/export → `vite build`
- [x] Testing — Vitest (engine + io golden-bytes vs `shared/petri-net/examples/`), independence lint check, static build verified

## Artifacts produced

- Requirements: `feature_034.studio_v1_editor/FEATURE.md`
- Analysis: `3.analysis/features/feature_034.studio_v1_editor/analysis_001_port_sources.md`
- Design: `4.design/features/feature_034.studio_v1_editor/design_001_studio_v1_editor.md` (+ `operation_spec_001_studio_v1_editor_ops.md`)
- Implementation: `5.implementation/features/feature_034.studio_v1_editor/implementation_001_manual_cycles.md`
- Testing: `6.testing/features/feature_034.studio_v1_editor/test_report.md`
