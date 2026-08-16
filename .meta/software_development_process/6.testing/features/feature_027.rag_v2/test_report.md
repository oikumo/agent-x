# Test Report — feature_027.rag_v2

> RAG v2 (console-only): retrieve-offload-delegate with LangChain deepagents + chunk-analyst subagent.
> Resume anchor: `.sandbox/pause_2026-08-15_l.md` (iter-g Design baseline → `.sandbox/pause_2026-08-15_g.md`).
> Design source-of-truth: `4.design/features/feature_027.rag_v2/design_001_retrieve_offload_delegate.md` (Static Structure + the 25-pytest-node-ID G1–G6 closure matrix).

---

## Scope locked (user decisions)

1. **v2 is console-only** — no TUI screens for v2; v1 RAG stays untouched for the TUI path.
2. **Console `rag` command repoints → `show_rag_v2`** via new `RagV2ShowCommand` (NOT a new key). v1 `RagShowCommand` stays registered for the TUI path.

## Test surface (31 v2 tests, 5 files)

- `test_rag_v2_mvc_contract.py` — 10 nodes (G6(a) outer/inner parity, G1 create-repo, G2 select-repo, G5 switch, `set_view` Constraint-d pin).
- `test_rag_v2_commands_and_views.py` — 6 nodes (console `rag`→v2 routing via `RagV2ShowCommand`, REPL loop, streaming).
- `test_rag_v2_agent_service.py` — 5 nodes (deepagents wiring: `create_deep_agent`, chunk-analyst, StateBackend, fallback to legacy `create_agent` when deepagents unavailable, public API stability).
- `test_rag_v2_retrieval_tool.py` — 4 nodes (`rag_search` offload + citation metadata + `chunk_analyst` subagent spec; `rag_ingest_status`).
- `test_rag_v2_gaps_closure_matrix.py` — 6 nodes (G3 state hygiene, G4 PDF/MD/web ingestion, G5 no-leak switch).
- Fixtures: `tests/features/feature_027.rag_v2/fixtures/sample.pdf` (pypdf blank) + `sample.md` (2-paragraph content).

## TDD cycle (major_feature @ Programming → auto-on)

`testlist(25 behaviors)` → `red` at 5 file-level nodes → `green` at 5 file-level nodes → `refactor` at `test_rag_v2_mvc_contract.py` (1 DRY tighten of `RagSearchResult` docstring) → `done` ✅ (cycle count: 12; `stranded_red: []`).

## Final result — GREEN 31/31

```
$ uv run pytest tests/features/feature_027.rag_v2/ -q
31 passed, 2 warnings in 3.31s
```
- 2 warnings: (1) `chromadb.telemetry` `DeprecationWarning: asyncio.iscoroutinefunction` (lib noise; harmless); (2) `langchain_community` sunset `DeprecationWarning` from `pdf_ingest.py:24` (fine for v2 day-1; future iteration may swap to standalone integration packages).

## Fixes this applied session (from iter- .sandbox/pause_2026-08-15_l.md §"Exact fixes")

| # | Fix | Files | Hat |
|---|-----|-------|-----|
| 1 | TUIProvider uninstantiable under 6 new `IUIProvider.create_rag_v2_*` abstract factories → added 6 `NotImplementedError("RAG v2 is console-only; use the console provider.")` stubs (+ typed return annotations + TYPE_CHECKING imports of `IRagV2*` view ABCs) | `src/agentx/ui/tui/provider.py` | GREEN (src) |
| 2 | `main_controller.py:85` `isinstance(self._provider, ConsoleProvider)` → `NameError` at runtime (ConsoleProvider imported only under `TYPE_CHECKING`) → lazy runtime import inside `load_commands` (circular-safe; chosen over a `hasattr` capability check to keep class-identity distinction from a TUIProvider/mock) | `src/agentx/ui/screens/main/main_controller.py` | GREEN (src) |
| 3 | `test_service_falls_back_to_create_agent_without_deepagents` false-took the deepagents path (installed importable) → poisoned `sys.modules["deepagents"]=None` (and 2 submodules) before `_fresh_service_module()` to force `ImportError`, asserted `svc._backend is None` | `tests/features/feature_027.rag_v2/test_rag_v2_agent_service.py` | RED (tests) |
| 4 | `test_show_rag_v2_calls_set_view_not_dot_view` source-pin sliced `show_rag_v2` by `\ndef ` (col-0) but MainController methods are 4-space-indented → over-captured into `show_models`'s legacy `models_controller.view = models_view` (matched `.view = ` literal) → fixed slice to `\n    def ` (4-space-indented method def). Also reworded the `show_rag_v2` TA: comment to remove the `.view = view` literal (the TA: comment-trips-source-pin gotcha). | `tests/.../test_rag_v2_mvc_contract.py` + `src/.../main_controller.py` | RED (tests) + GREEN (src) |

## REFACTOR

- `testlist → red → green → refactor → done` at the SAME file-level node IDs (node-granularity gotcha honored).
- 1 substantive tightening: `RagSearchResult` docstring collapsed to a one-line summary (the offload note duplicated module-header + `rag_search` docstring).
- System prompt + `@tool` docstrings were already concise from the RED-phase author; no further slim needed (tests stayed green; refactor auto-revert guard satisfied).

## Collateral infrastructure fixes (pre-existing hygiene blockers of `omt_tdd{op:done}`)

The `done` checklist gates on `suite_passes`. Three pre-existing infra failures blocked it — fixed this session:

1. **Stray `sandbox/` directory** (empty, untracked, Aug 9) not in `@var root_allowlist` → `harnessc check` hygiene error → **deleted** (`rmdir sandbox`).
2. **WORK.md budget breach** 6507 B > 5120 B (verbose `feature_027` `[~]` row + two verbose DONE rows) → slimmed feature_027 in-progress row + two feature_025/026 DONE rows to terse one-liners + `test_report.md` pointer (CONV_WORK_DONE: "one line + pointer"). **WORK.md 4540 B < 5120 B**; `harnessc check` now clean.
3. **KB compiler count pin drift** `test_kb_compiler_build_runs_clean` pinned exact `class=240 / contract=32 / dep=105` — these volatile AST-scraped counts drift on every feature ship (feature_025 → +2, feature_027 → +55). Per user direction ("it does not make sense") **replaced the brittle count pins with a structural-pin**: build exits 0 + reports ALL seven record kinds (class/contract/dep/doc/feature/flow/xref) + writes index/IR artifacts. Well-formedness + record-field coverage stays pinned in `test_kb_index_jsonl_well_formed_and_comprehensive`. No future feature owes a re-pin.
4. **`test_u13_op_state_consult_dedup` date-drift** (x2 — re-exported by `test_omt_q_golden_smoke.py`): hardcoded `fresh_ts = "2026-08-09T18:00:00Z"` with a comment "today is 2026-08-09"; consult went stale past the 8h UNLOCK_WINDOW_MS window → `recent_consults=[]` false-fail. **Replaced with dynamic timestamp** `datetime.now(timezone.utc) - timedelta(hours=1)` so the consult stays within the 8h window regardless of today's date. (feature_026 test flaw — out of feature_027's content scope; user approved the small dynamic-date fix.)

`omt_tdd{op:done}` ✅ — all checklist items verified (2 KNOWN_SUITE_FAILURES tolerated: 3× `TestReactScreenPilot` + 3× `test_tdd_enforcement`/`test_tdd_check`).

## Regression verification (touched suites)

```
$ uv run pytest tests/features/feature_027.rag_v2/ \
                   tests/features/feature_kb_akb.application_knowledge_base/ \
                   tests/features/feature_026.omt_q_interrogative_first_ops/ \
                   tests/scripts/omt/test_omt_q.py \
                   tests/scripts/omt/test_harnessc.py \
                   tests/scripts/omt/test_omt_docs_drift_pins.py -q
117 passed in 3.49s
```

## Source surface shipped (22 new + 4 additive existing)

### New (untracked)
- `src/agentx/model/rag_v2/` (12 files): `__init__.py`, `rag_v2.py` (aggregate), `rag_v2_db.py` (SQLite journal), `rag_v2_repository.py` (value object), `rag_v2_agent_service.py` (DeepAgents orchestrator; mirrors `CodingAgentService`), `rag_v2_tools.py` (`rag_search` + `rag_ingest_status` @tool + `RagSearchHit`/`RagSearchResult` dataclasses + DI-seam `_rag_search_impl`), `rag_v2_subagents.py` (`CHUNK_ANALYST` + `RAG_V2_SUBAGENTS`), `rag_v2_provider.py` (factory), `pdf_ingestion/`, `md_ingestion/`, `web_ingestion/`, `query/rag_v2_retriever.py`.
- `src/agentx/ui/screens/rag_v2/` (10 files): `__init__.py`, `rag_v2_controller.py` (`RagV2MainController` + `RagV2State`; `set_view()`-based; G1/G2/G3/G5/G6 partners), `rag_v2_view.py` (console REPL; mirrors `ConsoleReactView`), create-repository + repository-selection + web/pdf/md-ingestion controller/view pairs (8 files), `constants.py`.

### Existing (additive, no existing ABC/code touched)
- `src/agentx/ui/interfaces.py` — +8 ABC pairs (`IRagV2View`/`IRagV2ViewPartner` + 6 inner) + +6 `create_rag_v2_*` factories on `IUIProvider`.
- `src/agentx/ui/providers.py` — +6 factories on `ConsoleProvider` + TYPE_CHECKING `IRagV2*` imports.
- `src/agentx/ui/tui/provider.py` — +6 `NotImplementedError("RAG v2 is console-only")` stubs on `TUIProvider` (+ typed return annotations + TYPE_CHECKING `IRagV2*` imports). v1 untouched (Constraint D3 defer honored; v1 stays for TUI).
- `src/agentx/ui/screens/main/main_controller.py` — +`_rag_v2_controller`/`_rag_v2_view` attrs, +`show_rag_v2()` (uses `set_view()` — Constraint d), +`get_rag_v2_controller()`, +lazy `ConsoleProvider` import + console-repoint in `load_commands` (registers `RagV2ShowCommand` when provider is `ConsoleProvider`, else v1 `RagShowCommand` for TUI).
- `src/agentx/ui/screens/main/commands/commands.py` — +`RagV2ShowCommand` (console `rag`→v2; calls `show_rag_v2()` then `_rag_v2_view.show()`).

## Open follow-ups (non-blocking — out of feature_027's content scope)

- **`langchain_community` sunset** — the PDF/MD/web loaders (`PyPDFLoader`/`TextLoader`/`WebBaseLoader`) emit a `DeprecationWarning`. Fine for v2 day-1; a future iteration may swap to standalone integration packages.
- **LSP type noise** — `main_controller.py:201/246/270/271` (AgentController→IConsoleAgentViewPartner / ModelsController→IModelsViewPartner unassignable; `models_controller.view` unknown attr) and `tui/provider.py` adapter imports unresolved. All pre-existing feature_024 virtual-subclass issues / runtime-lazy TUI imports (TA: thoughts record the gotchas); NOT regressed by feature_027 and NOT runtime failures (the v2 test suite is fully green).
- **v1 RAG deferral** — v1's `RagShowCommand`/`src/agentx/model/rag/`/`src/agentx/ui/screens/rag/` stay untouched for the TUI path. Whether to cut over (remove v1) or keep as opt-in fallback is a deferred design decision requiring a downstream-consumer audit of v1 (per `.projects/meta/rag_v2/PROJECT.md` D-lock + the analysis_001 G1–G3 STALE note). The gate for EITHER choice is met here: v2 surface proven GREEN against the G1–G6 closure matrix.
