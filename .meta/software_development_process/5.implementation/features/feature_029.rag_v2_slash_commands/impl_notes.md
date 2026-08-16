# Implementation Notes — feature_029.rag_v2_slash_commands

> **Phase:** Implementation · **Date:** 2026-08-16 · TDD cycle detail: folded into
> `6.testing/features/feature_029.rag_v2_slash_commands/test_report.md` (13/13 behaviors).

## Files changed (src)

| File | Change |
|---|---|
| `ui/screens/rag_v2/rag_v2_view.py` | REPL rework: `_MENU_ACTIONS` digit map deleted; `_dispatch_command()` slash router (`help`/`quit` view-local, `search` → `send_message`, `repos`/`use`/`create`/`ingest`/`status`/`reset` → controller); `show_menu()` = banner + hint |
| `ui/screens/rag_v2/constants.py` | `RAG_V2_MENU` rewritten to the hint line; `RAG_V2_HELP` command table added (single source of truth rule kept) |
| `ui/screens/rag_v2/rag_v2_controller.py` | +`list_repositories` `use_repository` `create_repository_named` `ingest` `show_status` `reset_chat`; `show_chat` **removed** (fake mode); `_run_agent` wires `on_tool_call`/`on_tool_result` with `_TOOL_LABELS`; `RagV2Provider` imported at top |
| `ui/interfaces.py` | `IRagV2ViewPartner`: −`show_chat`, +6 command abstracts, `create_repository` return widened to `object`; `IRagV2View`: +`capture_repository_name`/`get_selected_repository_id` |
| `model/rag_v2/rag_v2_agent_service.py` | `_dispatch_stream_delta`: AI `tool_calls` → `on_tool_call(name, args[:120])`; tool msgs → `on_tool_result(name, preview[:120])`; summarization filter precedes routing; prompts use new tool names |
| `model/rag_v2/rag_v2_tools.py` | rename: `search_documents`/`_search_documents_impl`/`SearchDocumentsResult`, `ingestion_status`/`_ingestion_status_impl`; bound factory `@tool("…")` names; `RagSearchHit` kept (citation record) |
| `model/rag_v2/query/rag_v2_retriever.py` | docstring reference updated |

## Files changed (tests)

- NEW `tests/features/feature_029.rag_v2_slash_commands/test_rag_v2_slash_commands.py` — 51 tests, 13 classes, deferred-import style (feature_027 pattern).
- `tests/features/feature_027.rag_v2/test_rag_v2_retrieval_tool.py` + `test_rag_v2_console_repl_regression.py` — 19 rename pins updated; 38/38 still green.

## Design decisions taken during implementation

1. **Full view dispatch in cycle b1's green** — the command table is one code path; b2/b3+b4 recorded as already-green rather than re-red (harness-verified).
2. **`/use` and `/create` bare-arg fallbacks** route to the existing interactive picker/prompt (`use_repository(None)` → `select_repository()`), so no sub-screen code was duplicated.
3. **`/ingest` dispatch table** (`_INGEST_KINDS`) lazy-imports the same `ingest_web/pdf/md` functions the sub-controllers use — one ingestion implementation, two entry surfaces.
4. **Totality pin self-trip** — the first rename green failed because the new module docstring *mentioned* the old names; the rename note moved to the design doc + test headers, src stays literal-free (the totality test enforces it permanently).
5. **`RagSearchHit` not renamed** — internal citation record, never surfaces in prompts/traces/console; renaming it would churn feature_027 pins for zero UX gain.
