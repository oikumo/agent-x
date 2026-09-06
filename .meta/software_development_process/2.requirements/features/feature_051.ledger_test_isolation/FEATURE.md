# Feature 051: Ledger Test Isolation

> **Status:** [x] Done (2026-09-06 — full suite 1846 passed / 0 failed, allowlist empty)
> **Created:** 2026-09-05
> **WORK.md task:** meta_harness_6 Wave 1 / A1 (`.projects/meta/meta_harness_6/PROJECT.md`)

---

## Summary

The harness ledger (append-only audit of think/phase/skip/q/complete records) is global mutable state shared between harness self-tests and live opencode sessions. This breaks test isolation: 6 suite failures are currently tolerated in a `KNOWN_SUITE_FAILURES` allowlist (3× feature_018 react_screen + 3× ledger-window flaky). A "tests must pass" system that ships with a known-failing suite is the biggest credibility hole in the harness. This feature threads an env override (`OMT_LEDGER_PATH`, backed by `@var ledger_path`) through both ledger clients (`.opencode/lib/omt_shared.ts` + `scripts/omt/tdd/state.py`), points harness self-tests at tmp ledgers, and DELETES the allowlist — suite green means green.

## Scope (one sentence — what "done" looks like)

Full test suite green with zero KNOWN_SUITE_FAILURES entries: both ledger clients honor `OMT_LEDGER_PATH`; harness tests that touch the ledger run on tmp copies (no cross-test/live-session interference); the allowlist is deleted; GOTCHA_TDD_ENV_FLAKY is demoted to an ordinary doc note.

## Task type

minor_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_051.ledger_test_isolation/` | [x] |
| Analysis | Analysis doc | (n/a — evidence base @ `.sandbox/meta_harness_6_evaluation.md` §5 A1) | [x] |
| Design | Design doc | (n/a — minor_feature, declaration only per §12) | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_051.ledger_test_isolation/implementation_notes.md` | [x] |
| Testing | Test report | `6.testing/features/feature_051.ledger_test_isolation/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
