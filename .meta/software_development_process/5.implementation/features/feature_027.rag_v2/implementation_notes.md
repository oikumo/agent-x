# Implementation Notes — feature_027.rag_v2

> **Phase:** Programming → Testing
> **Feature:** feature_027.rag_v2 (major_feature; TDD auto-on at Programming)
> **Design:** `design_001_retrieve_offload_delegate.md`
> **Operation spec:** `operation_spec_001_rag_v2_service_and_tools.md`
> **Parent design:** `.projects/meta/rag_v2/PROJECT.md` (v1.1; D5 locks the retrieve-offload-delegate pattern)
> **Branch point:** no v2 surface → v2 console-only RAG with the retrieve-offload-delegate deepagents-RAG pattern + chunk-analyst subagent.
> **Resume anchor:** `.sandbox/pause_2026-08-15_l.md` (iter-g Design baseline → `.sandbox/pause_2026-08-15_g.md`).

## Scope locked (user decisions)

1. **v2 is console-only** — no TUI screens for v2; v1 RAG stays untouched for the TUI path.
2. **Console `rag` command repoints → `show_rag_v2`** via new `RagV2ShowCommand` (NOT a new key; v1 `RagShowCommand` stays registered for the TUI path only).

## What shipped

### New — `src/agentx/model/rag_v2/` (12 files)
- `__init__.py`, `rag_v2.py` (aggregate; mirrors v1 `Rag`), `rag_v2_db.py` (SQLite journal), `rag_v2_repository.py` (value object).
- `rag_v2_agent_service.py` — DeepAgents orchestrator; parallels `CodingAgentService` (feature_025). Wires `create_deep_agent(model, tools, system_prompt, backend|StateBackend(), checkpointer|InMemorySaver(), memory, skills, subagents=[CHUNK_ANALYST], middleware=[create_summarization_tool_middleware(llm, backend)])`. **Fallback path:** if `import deepagents` raises, warn + use legacy `create_agent(...)` (no subagents; chunk-analyst unavailable; `_backend=None`). Public API surface mirrors `CodingAgentService` (stream_agent / cancel / reset_conversation / get_history / is_running / thread_id) so the v2 controller's `show_*` callbacks wire identically.
- `rag_v2_tools.py` — `@tool rag_search(query, repository_path, k=5)` → `RagSearchResult`; offload step writes chunks to backend via `backend.upload_files()` (deterministic `chunk_{i}.txt` paths for the chunk-analyst's `task(description="summarize chunk_0.txt")`). `@tool rag_ingest_status(repository_path)` → dict (database_exists / documents_exist / ingested_url). DI-seam `_rag_search_impl(backend=, _retriever=)` lets tests inject fakes without a live ChromaDB. Dataclasses `RagSearchHit` (chunk_id/content/score/source_path/page/line) + `RagSearchResult` (hits/chunks_uploaded/truncated/error) carry the citation metadata the orchestrator threads to the synthesizer.
- `rag_v2_subagents.py` — `CHUNK_ANALYST` dict spec + `RAG_V2_SUBAGENTS` list (read/grep/summarize individual files in parallel via the deepagents built-in `task({subagentType, description})`).
- `rag_v2_provider.py` — factory.
- `pdf_ingestion/` (`__init__.py` + `pdf_ingest.py` — `PyPDFLoader`), `md_ingestion/` (`__init__.py` + `md_ingest.py` — `TextLoader`), `web_ingestion/` (`__init__.py` + `web_ingest.py` — `WebBaseLoader`). Loader sources from `langchain_community` (sunset package; DeprecationWarning at import — fine for v2 day-1; future iteration may swap to standalone integration packages).
- `query/rag_v2_retriever.py` — `build_retriever(repository_path)` builds the real retriever against the repository's ChromaDB store (lazily imported so the `@tool` import stays light).

### New — `src/agentx/ui/screens/rag_v2/` (10 files)
- `__init__.py`, `rag_v2_controller.py` (`RagV2MainController` + `RagV2State`; `set_view()`-based wrapper — Constraint d; G1/G2/G3/G5/G6 partners), `rag_v2_view.py` (console REPL; mirrors `ConsoleReactView`).
- 4 controller/view pairs: `rag_v2_create_repository_controller.py` + `rag_v2_create_repository_view.py`, `rag_v2_repository_selection_controller.py` + `rag_v2_repository_selection_view.py`, `rag_v2_web_ingestion_controller.py` + `rag_v2_web_ingestion_view.py`, `rag_v2_pdf_ingestion_controller.py` + `rag_v2_pdf_ingestion_view.py`, `rag_v2_md_ingestion_controller.py` + `rag_v2_md_ingestion_view.py`.
- `constants.py`.

### Existing (additive — no existing ABC/code touched)
- `src/agentx/ui/interfaces.py` — +8 ABC pairs: `IRagV2View`/`IRagV2ViewPartner` (outer) + 6 inner pairs (create-repo / repo-selection / web/pdf/md-ingestion). +6 `create_rag_v2_*` factories on `IUIProvider`.
- `src/agentx/ui/providers.py` — +6 factories on `ConsoleProvider` + TYPE_CHECKING `IRagV2*` imports.
- `src/agentx/ui/tui/provider.py` — +6 `NotImplementedError("RAG v2 is console-only; use the console provider.")` stubs on `TUIProvider` (+ typed return annotations `IRagV2*` + TYPE_CHECKING imports). v1 untouched (D3 defer honored; v1 stays for TUI).
- `src/agentx/ui/screens/main/main_controller.py` — +`_rag_v2_controller`/`_rag_v2_view` attrs, +`show_rag_v2()` (uses `set_view(view)` — Constraint d; NOT the legacy `.view =` assignment), +`get_rag_v2_controller()`, +lazy runtime `from agentx.ui.providers import ConsoleProvider` inside `load_commands` (circular-safe; distinguishes the real ConsoleProvider class from a TUIProvider/mock by class identity), +console-repoint: registers `RagV2ShowCommand("rag", self)` when `isinstance(self._provider, ConsoleProvider)`, else v1 `RagShowCommand` for the TUI path.
- `src/agentx/ui/screens/main/commands/commands.py` — +`RagV2ShowCommand` (console `rag`→v2; calls `show_rag_v2()` then `_rag_v2_view.show()` to enter the REPL — feature_024 console parity pattern).

## TDD cycle (auto-on)

`testlist(25 behaviors)` → `red` at 5 file-level nodes → `green` at 5 file-level nodes → `refactor` at `test_rag_v2_mvc_contract.py` (1 DRY tighten of `RagSearchResult` docstring) → `done` ✅. Cycle count: 12; `stranded_red: []`. Node IDs:
- `tests/features/feature_027.rag_v2/test_rag_v2_mvc_contract.py`
- `tests/features/feature_027.rag_v2/test_rag_v2_commands_and_views.py`
- `tests/features/feature_027.rag_v2/test_rag_v2_agent_service.py`
- `tests/features/feature_027.rag_v2/test_rag_v2_retrieval_tool.py`
- `tests/features/feature_027.rag_v2/test_rag_v2_gaps_closure_matrix.py`

## Fixes applied (from iter- `.sandbox/pause_2026-08-15_l.md` §"Exact fixes for the 6 failing tests")

1. **TUIProvider v2 stubs** (src, GREEN) — adding the 6 `create_rag_v2_*` abstract factories to `IUIProvider` made `TUIProvider` uninstantiable (doesn't implement them; v2 console-only). Added 6 `NotImplementedError` stubs (+ typed return annotations + TYPE_CHECKING `IRagV2*` imports so the stubs satisfy the ABC and typecheck).
2. **Lazy ConsoleProvider import in `load_commands`** (src, GREEN) — `main_controller.py:85` `isinstance(self._provider, ConsoleProvider)` was a `NameError` at runtime (ConsoleProvider imported only under `TYPE_CHECKING`). Added a lazy runtime `from agentx.ui.providers import ConsoleProvider` inside `load_commands`. Chose option A (runtime import) over option B (`hasattr` capability check) because a mock or TUIProvider might expose `create_rag_v2_view` as an ABC attr even though it's not a console provider — the class-identity isinstance check keeps the routing correct.
3. **`sys.modules` poison in fallback test** (tests, RED) — `test_service_falls_back_to_create_agent_without_deepagents` false-took the deepagents path (deepagents is importable) → `TypeError: 'expects model to be a BaseChatModel'`. Poisoned `sys.modules["deepagents"]=None` (and 2 submodules) before `_fresh_service_module()` to force `ImportError` (CPython contract: a None entry makes `import <name>` raise), asserted `svc._backend is None`.
4. **Source-pin slice defect** (tests, RED + src, GREEN) — `test_show_rag_v2_calls_set_view_not_dot_view` sliced the `show_rag_v2` body by `\ndef ` (top-level col-0) but MainController methods are 4-space-indented → over-captured into `show_models`'s legacy `models_controller.view = models_view` (matched the `.view = ` literal). Fixed the slice to `\n    def ` (4-space-indented method def). Also reworded the TA: comment in `show_rag_v2` to drop the `.view = view` literal (the TA: comment-trips-source-pin gotcha — idempotency note).

## REFACTOR

- `testlist → red → green → refactor → done` declared at the SAME file-level node IDs (node-granularity gotcha honored — red/green/refactor at the SAME test_node).
- 1 substantive tightening: `RagSearchResult` docstring collapsed to a one-line summary (the offload note duplicated module-header + `rag_search` docstring). System prompt (8 lines) + `@tool` docstrings (Google-style, descriptive) were already concise from the RED-phase author; no further slim needed. Tests stayed green (refactor auto-revert guard satisfied).

## Collateral infrastructure fixes (pre-existing hygiene that blocked `omt_tdd{op:done}`)

The `done` checklist gates on `suite_passes`. Three pre-existing infra failures blocked it — fixed this session (full detail in `6.testing/features/feature_027.rag_v2/test_report.md`):

1. **Stray `sandbox/` directory** (empty, untracked, Aug-9) not in `@var root_allowlist` → deleted (`rmdir`).
2. **WORK.md budget breach** 6507 B > 5120 B → slimmed verbose feature_027 `[~]` row + two feature_025/026 DONE rows to terse one-liners + `test_report.md` pointer (CONV_WORK_DONE). **WORK.md 4540 B < 5120 B**; `harnessc check` clean.
3. **KB compiler count pin drift** (`test_kb_compiler_build_runs_clean` pinned `class=240/contract=32/dep=105`) — volatile AST-scraped counts drift on every feature ship. Per user direction, replaced the brittle count pins with a **structural pin**: build exits 0 + reports ALL seven record kinds (class/contract/dep/doc/feature/flow/xref) + writes index/IR. No future feature owes a re-pin.
4. **`test_u13_op_state_consult_dedup` date-drift** (x2: test + golden-smoke re-export) — hardcoded `fresh_ts="2026-08-09T18:00:00Z"` went stale past the 8h window → `recent_consults=[]`. Replaced with dynamic `datetime.now(timezone.utc) - timedelta(hours=1)`. (feature_026 test flaw — out of feature_027's content scope; user approved the small dynamic-date fix; harness-surface receipt-refresh obeyed.)

`omt_tdd{op:done}` ✅ — all checklist items verified (2 KNOWN_SUITE_FAILURES tolerated: 3× `TestReactScreenPilot` + 3× `test_tdd_enforcement`/`test_tdd_check`).

## Open follow-ups (non-blocking, out of feature_027's content scope)

- **`langchain_community` sunset** — the PDF/MD/web loaders emit a `DeprecationWarning`. Fine for v2 day-1; a future iteration may swap to standalone integration packages.
- **LSP type noise** — `main_controller.py:201/246/270/271` (AgentController→IConsoleAgentViewPartner / ModelsController→IModelsViewPartner unassignable; `models_controller.view` unknown) and `tui/provider.py` adapter imports unresolved. All pre-existing feature_024 virtual-subclass issues / runtime-lazy TUI imports (TA: thoughts record the gotchas); NOT regressed by feature_027; NOT runtime failures (v2 suite is fully green).
- **v1 RAG deferral** — v1's `RagShowCommand`/`src/agentx/model/rag/`/`src/agentx/ui/screens/rag/` stay untouched for the TUI path. Whether to cut over (remove v1) or keep as opt-in fallback is a deferred design decision requiring a downstream-consumer audit of v1 (per `.projects/meta/rag_v2/PROJECT.md` D-lock + the analysis_001 G1–G3 STALE note). The gate for EITHER choice is met here: v2 surface proven GREEN against the G1–G6 closure matrix.
