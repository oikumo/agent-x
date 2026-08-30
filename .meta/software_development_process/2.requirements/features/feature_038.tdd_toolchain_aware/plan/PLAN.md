# PLAN — feature_038: Tdd_Toolchain_Aware

> Task type: **minor_feature** · See `omt_agent_guide.md §12` for the required artifacts.

## Objective

<!-- one sentence: what done looks like -->
`omt_tdd` red/green/refactor/after-edit dispatch toolchain-aware (`.py` → pytest, `.ts/.tsx` → vitest from the vitest project root), eliminating the A11/B11 manual red→green workaround for TypeScript/Vitest features. DONE 2026-08-29 (see FEATURE.md + test_report.md).

## Steps

- [x] Analysis (declaration only — minor_feature)
- [x] Design (declaration only — minor_feature)
- [x] Implementation — `scripts/omt/tdd/{state,cli,gates}.py`
- [x] Testing — `TestRunTestDispatch` ×6 + sentinel 1664 passed

## Artifacts produced

- Requirements: `feature_038.tdd_toolchain_aware/FEATURE.md`
- Analysis: _declaration only (overridden in `omt_phase` scope; no separate doc for minor_feature)_
- Design: _declaration only (overridden in `omt_phase` scope; no separate doc for minor_feature)_
- Testing: `6.testing/features/feature_038.tdd_toolchain_aware/test_report.md`
