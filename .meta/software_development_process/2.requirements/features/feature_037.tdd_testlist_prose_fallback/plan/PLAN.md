# PLAN — feature_037: Tdd_Testlist_Prose_Fallback

> Task type: **minor_feature** · See `omt_agent_guide.md §12` for the required artifacts.

## Objective

`omt_tdd testlist` accepts prose behaviors (JSON array / JSON string / bullets / numbered lists via `_parse_behaviors` in `scripts/omt/tdd/cli.py`) with unit tests and same-session doc sync — all green, e2e receipt refreshed, feature `[x]` DONE.

## Steps

- [x] Analysis — idea doc `.sandbox/meta_harness_3_idea.md` proposal #10 (harness review)
- [x] Design — PROJECT.md declaration (D1 scope one improvement / D2 python-side-only)
- [x] Implementation — `_parse_behaviors` in `scripts/omt/tdd/cli.py` (11/11 parser smoke + CLI success criteria)
- [x] Testing — `TestParseBehaviors` ×10 rows in `tests/scripts/omt/test_tdd_check.py` (43/51 passed) + full sentinel + e2e receipt refresh

## Artifacts produced

- Requirements: `feature_037.tdd_testlist_prose_fallback/FEATURE.md`
- Analysis: `3.analysis/features/feature_037.tdd_testlist_prose_fallback/analysis_001_*.md`
- Design: `4.design/features/feature_037.tdd_testlist_prose_fallback/design_001_*.md`
- Testing: `6.testing/features/feature_037.tdd_testlist_prose_fallback/test_report.md`
