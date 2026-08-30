# Feature 038: Tdd_Toolchain_Aware

> **Status:** [x] Complete (2026-08-29)
> **Created:** 2026-08-29
> **Project:** meta_harness_5 (forward scope, Proposal A)
> **WORK.md task:** feature_038.tdd_toolchain_aware — DONE 2026-08-29

---

## Summary

`omt_tdd` (the pytest-only two-hats engine) is now **toolchain-aware**: the test runner dispatches on the target test file's suffix — `.py` → pytest (unchanged), `.ts/.tsx` → `npx vitest run <file>` executed from the resolved vitest **project root**. This eliminates the documented A11/B11 manual red→green workaround that three consecutive TypeScript/Vitest features (petri_net_studio 034/035/036) were forced into, because `omt_tdd{op:red}` previously hard-failed with pytest exit-4 "file not found" on Vitest nodes. Real two-hats RED/GREEN/REFACTOR enforcement now works for polyglot (Python+TypeScript) features.

## Scope (one sentence)

`run_test` in `scripts/omt/tdd/state.py` + `cmd_start`/`cmd_green`/`cmd_refactor`/`cmd_after_edit` use toolchain-aware dispatch; new `GOTCHA_TDD_TOOLCHAIN` documents the whole-file vitest run (no `-t` filter, which vitest treats as regex and would false-pass), with unit tests for dispatch + project-root discovery.

## Task type

**minor_feature**

---

## Phase artifacts (traceability)

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_038.tdd_toolchain_aware/` | [x] |
| Analysis | _declaration only (minor_feature)_ | — | [x] |
| Design | _declaration only (minor_feature)_ | — | [x] |
| Implementation | `scripts/omt/tdd/{state,cli,gates}.py` | — | [x] |
| Testing | Test report | `6.testing/features/feature_038.tdd_toolchain_aware/test_report.md` | [x] |
