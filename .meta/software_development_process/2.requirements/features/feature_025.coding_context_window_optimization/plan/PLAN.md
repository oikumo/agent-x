# PLAN — feature_025: Coding Context Window Optimization

> Task type: **major_feature** · See `omt_agent_guide.md §12` for the required artifacts.
> Phase: **Programming** (TDD auto-on — `omt_tdd` testlist → red → green → refactor → done).

## Objective

`CodingAgentService` uses `create_deep_agent` with the full middleware stack (FilesystemMiddleware + SummarizationMiddleware + MemoryMiddleware + SkillsMiddleware + compact_conversation tool) so multi-file coding sessions no longer overflow the context window, while keeping all existing public methods API-compatible and the existing MVC pin green.

## Steps

- [x] Analysis (folded into design_001 — context-engineering analysis on the current `create_agent` bloat problem)
- [x] Design — `4.design/features/feature_025.coding_context_window_optimization/design_001_deepagent_context_optimization.md`
- [ ] Programming (TDD)
  - [ ] `omt_tdd{op:testlist}` — behaviors list
  - [ ] `omt_tdd{op:red}` — failing tests in `tests/features/feature_025.../`
  - [ ] `omt_tdd{op:green}` — wire `create_deep_agent` + middleware stack in `coding_agent_service.py`
  - [ ] `omt_tdd{op:refactor}` — slim default system prompt + tool descriptions
  - [ ] `omt_tdd{op:done}` — collapse green record
- [ ] Testing — full pytest suite + harness drift check
- [ ] WORK.md DONE entry + rotate

## Artifacts produced

- Requirements: `feature_025.coding_context_window_optimization/FEATURE.md` ✅
- Design: `4.design/features/feature_025.coding_context_window_optimization/design_001_deepagent_context_optimization.md` ✅
- Implementation: `src/agentx/model/coding/coding_agent_service.py` (modified) + `pyproject.toml` (deepagents dep)
- Testing: `6.testing/features/feature_025.coding_context_window_optimization/test_report.md`

## Dependency change

Add `deepagents>=0.7` to `pyproject.toml` dependencies.
