# Feature 037: Tdd_Testlist_Prose_Fallback

> **Status:** [x] Done (2026-08-29)
> **Created:** 2026-08-29
> **WORK.md task:** `- [x] feature_037.tdd_testlist_prose_fallback` (DONE 2026-08-29; resume was `.sandbox/pause_2026-08-29.md`)

---

## Summary

The agent-facing `omt_tdd{op:"testlist"}` call passes `behaviors` prose through verbatim to
`scripts/omt/tdd/cli.py`, where `cmd_testlist` (line 68) previously did `json.loads(args.behaviors)`
and failed on any non-JSON input with `Expecting value: line 1 column 1 (char 0)` — a top-3 recurring
agent failure mode fired at least once per TDD session (`GOTCHA_TESTLIST_JSON`). This feature adds a
hardened `_parse_behaviors(raw)` prose fallback: JSON arrays keep working unchanged, while JSON
strings, bullet prose (`-` / `•` / `*`) and numbered lists (`1.` / `2)`) are split and stripped,
empty/`[]` input stays `[]`, and JSON scalars fall through to the prose path. One of the 10 proposals
from the harness review (`.sandbox/meta_harness_3_idea.md` #10); shipped via project `meta_harness_4`.

## Scope (one sentence — what "done" looks like)

`omt_tdd testlist` accepts JSON array, JSON string, bullet prose, or numbered lists via
`_parse_behaviors` in `scripts/omt/tdd/cli.py` (existing JSON-array fixtures unchanged), with unit
tests in `tests/scripts/omt/test_tdd_check.py` and same-session doc sync (`.omt` ×3 records +
WORK.md + TS fallback seed) — all green and e2e receipt refreshed.

## Task type

minor_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case (declaration) | `2.requirements/.../feature_037.tdd_testlist_prose_fallback/` | [x] |
| Analysis | Analysis doc | — n/a (minor_feature: declaration only per §12) | — |
| Design | Design doc | — n/a (minor_feature: declaration only per §12) | — |
| Implementation | Impl | `scripts/omt/tdd/cli.py:68-102` (`_BULLET_RE` + `_parse_behaviors` + `cmd_testlist` call) | [x] |
| Testing | Test report | `6.testing/features/feature_037.tdd_testlist_prose_fallback/test_report.md` (+ unit tests: `tests/scripts/omt/test_tdd_check.py` `TestParseBehaviors` ×10 rows; file 43, tdd-filtered 51, harness suite 250, sentinel 1658 passed) | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.