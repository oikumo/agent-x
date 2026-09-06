# Feature 054: Small Task Fast Path

> **Status:** [x] Done (2026-09-06)
> **Created:** 2026-09-06
> **WORK.md task:** meta_harness_6 Wave 2 / C2 (`.projects/meta/meta_harness_6/`)

---

## Summary

Wave 2/C2 of the meta_harness_6 improvement program: for `bug_fix`/`test`
task types, the `omt_phase` ledger record satisfies g.nav + g.kb in ONE
write (stays hard for minor/major/new_screen), and the tests canary
auto-unlocks ONLY the declared feature's own test dir while its
feature-scoped TDD RED is active. g.think/g.protect untouched.

## Scope (one sentence — what "done" looks like)

A bug_fix/test phase declaration + (during RED) edits to the feature's own
test dir require no extra ceremony calls (nav/kb consult, tests canary),
while all other gate semantics — including g.think, g.protect, bootstrap
canary for new test files, and hard nav/kb for major work — are provably
unchanged (pinned by tests).

## Task type

minor_feature

---

## Phase artifacts (traceability)

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_054.small_task_fast_path/` | [x] |
| Analysis | (decl-only task type — evaluation §5 C2 is the analysis) | — | n/a |
| Design | (decl-only task type) | — | n/a |
| Implementation | Impl notes | `5.implementation/features/feature_054.small_task_fast_path/implementation_notes.md` | [x] |
| Testing | Test report | `6.testing/features/feature_054.small_task_fast_path/test_report.md` | [x] |

Evidence: feature suite 10/10; full suite 1887/0 (empty allowlist);
harnessc check 0 errors (259 records), build OK, all 12 budgets green;
e2e receipt refreshed.
