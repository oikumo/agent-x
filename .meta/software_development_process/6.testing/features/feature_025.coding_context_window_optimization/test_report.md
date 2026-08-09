# Test Report — feature_025.coding_context_window_optimization

> **Phase:** Testing
> **Feature:** feature_025.coding_context_window_optimization
> **Test file:** `tests/features/feature_025.coding_context_window_optimization/test_deepagent_context_optimization.py`
> **Design:** `design_001_deepagent_context_optimization.md` §Testing strategy (tests 1-8)

## Test scope

8 behaviors covering the contract surface introduced by the deepagent wiring:

| # | Test node | Behavior | RED cause (pre-fix) | GREEN |
|---|-----------|----------|---------------------|-------|
| 1 | `TestDeepAgentWiring::test_service_uses_create_deep_agent_when_available` | ctor calls `create_deep_agent` when `deepagents` importable | ctor called bare `create_agent`; mock `create_deep_agent` never called | ✅ |
| 2 | `TestDeepAgentWiring::test_service_writes_state_backend_for_offloading` | ctor constructs a `StateBackend` for offloading | no `_backend` attribute + `backend=` kwarg not passed | ✅ |
| 3 | `TestDeepAgentWiring::test_service_registers_compact_conversation_tool` | ctor invokes `create_summarization_tool_middleware` | ctor did not call the tool-middleware factory | ✅ |
| 4 | `TestDeepAgentWiring::test_service_accepts_memory_paths` | ctor stores `_memory` kwarg | `TypeError: __init__() got an unexpected keyword argument 'memory'` | ✅ |
| 5 | `TestDeepAgentWiring::test_service_accepts_skills_paths` | ctor stores `_skills` kwarg | `TypeError: __init__() got an unexpected keyword argument 'skills'` | ✅ |
| 6 | `TestDeepAgentWiring::test_service_falls_back_to_create_agent_without_deepagents` | ctor uses legacy `create_agent` when `import deepagents` raises `ImportError` | already passed pre-fix (fallback path predates the feature — design preserved it) | ✅ |
| 7 | `TestDeepAgentWiring::test_service_preserves_thread_id_cancel_history_api` | `thread_id` / `cancel` / `is_running` / `get_history` / `reset_conversation` stay stable | already passed pre-fix (API unchanged); later required a mock-side fix to make `get_state` return `[]` | ✅ |
| 8 | `TestMVCPinStillPasses::test_mvc_pin_still_passes` | `create_agent` + `InMemorySaver` literal imports present; `textual` absent | already passed pre-fix (MVC pin preserved by design) | ✅ |

## Mock strategy

Tests inject a **fake `deepagents` package** into `sys.modules` (`deepagents`, `deepagents.backends`, `deepagents.middleware`, `deepagents.middleware.summarization`) so the module-under-test imports a wired mock graph — no LLM, no network. The fake graph returns a `MagicMock` agent whose `get_state().values` carries `{"messages": []}`, mirroring the live deepagent graph state shape so `get_history()` returns `[]`.

The fallback test (behavior 6) flushes `deepagents` from `sys.modules`, so the guarded `try: import deepagents` raises `ImportError` and the ctor takes the legacy `create_agent` path.

Each test imports `CodingAgentService` lazily (`importlib.import_module`) inside the test body so failures surface as test failures (exit 1) rather than collection errors (exit 2) — required by the OMT TDD RED-gate rule (META_HARNESS.omt:227).

## Test results

```
tests/features/feature_025.coding_context_window_optimization/test_deepagent_context_optimization.py
  TestDeepAgentWiring::test_service_uses_create_deep_agent_when_available      PASSED
  TestDeepAgentWiring::test_service_writes_state_backend_for_offloading       PASSED
  TestDeepAgentWiring::test_service_registers_compact_conversation_tool        PASSED
  TestDeepAgentWiring::test_service_accepts_memory_paths                       PASSED
  TestDeepAgentWiring::test_service_accepts_skills_paths                        PASSED
  TestDeepAgentWiring::test_service_falls_back_to_create_agent_without_deepagents PASSED
  TestDeepAgentWiring::test_service_preserves_thread_id_cancel_history_api     PASSED
  TestMVCPinStillPasses::test_mvc_pin_still_passes                             PASSED

================== 8 passed, 2 warnings in 4.36s ==================
```

## Regression sweep (existing test files)

| Suite | File | Result |
|-------|------|--------|
| MVC pin | `tests/features/feature_019.coding_agent_screen/test_coding_mvc.py` | ✅ all pass (incl. `test_coding_agent_service_model_layer`) |
| Coding integration | `tests/features/feature_019.coding_agent_screen/test_coding_integration.py` | ✅ all pass |
| Console parity | `tests/features/feature_024.no_tui_full_features/test_console_provider_and_views.py` + siblings | ✅ all pass |

The combined feature_019+feature_024+feature_025 run = 151 passed, 0 failed.

## Full-suite run

`uv run pytest` → **1196 passed, 3 failed, 5 warnings** (84s).

The 3 failures are the allowlisted `KNOWN_SUITE_FAILURES` (feature_018 react_screen×3 — environmental test-framework interaction; same root as the existing ledger window-flaky probes; passed in isolation):

- `test_react_screen_mounts_and_displays_welcome`
- `test_react_screen_escape_pops`
- `test_react_screen_input_and_send`

None caused by feature_025 scope.

## Side-effect: kb_compiler count drift

Adding the new test file's 2 test classes (`TestDeepAgentWiring`, `TestMVCPinStillPasses`) bumped the AKB record counts: `class=239 → 240`, `dep=104 → 105`, total `437 → 439 records`. Updated the actively-enforced pin in `tests/features/feature_kb_akb.application_knowledge_base/test_kb_feature_acceptance.py::test_kb_compiler_build_runs_clean` (with a comment explaining the drift source). No historical records (`.projects/`, `test_report.md`, `implementation_notes.md`, `WORK_ARCHIVE.md`, `README.md`) were retroactively rewritten — those are append-only.

## Side-effect: WORK.md budget

The new `[~] feature_025` line + the leftover 5 DONE entries pushed `WORK.md` to 6078B (over the 5120B budget pin). Resolved by rotating the 3 oldest inline DONE rows (the verbose `meta.workflows_*` + `meta.projects_*` entries) to `WORK_ARCHIVE.md` under a new "2026-08-08 rotation (feature_025 completion round)" section, and condensing the in-progress pointer. Final size: 3079B (well under budget). `harnessc check` returns 0 errors; projections fresh.

## TDD cycle ledger

- **testlist** recorded: 8 behaviors (via direct `tdd/cli.py` CLI — workaround for the `omt_tdd{op:testlist}` TS-tool bug noted in `.sandbox/pause_2026-08-08.md`).
- **red** at `…TestDeepAgentWiring::test_service_uses_create_deep_agent_when_available` → 5/8 RED, runnable (exit 1).
- **green** at the same node → 8/8 green.
- **refactor** → 8/8 still green.
- **done** → phase exit approved (KNOWN_SUITE_FAILURES allowlisted).
