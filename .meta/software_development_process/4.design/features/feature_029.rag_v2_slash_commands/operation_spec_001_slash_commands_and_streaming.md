# Operation Spec 001: Slash-Command Surface + Tool-Activity Streaming

> **Feature:** feature_029.rag_v2_slash_commands
> **Parent design:** `design_001_slash_command_grammar.md`
> **Conventions:** pre/post per operation; errors via `print_message_error`; no LLM on the slash path except `/search`.

## View operations — `RagV2View`

### `show()` (reworked dispatch)
- **Pre:** banner + hint printed once at entry.
- **Post:** every iteration consumes exactly one input; loop exits only on `None` (interrupt), exit tokens, or `/quit`.
- Dispatch (total, in order): `None` → return · `""` (bare Enter) → re-prompt · exit tokens → return · `/…` → `_dispatch_command` · else → `send_message` + `_wait_for_agent`.

### `_dispatch_command(text: str) -> bool`
- **Input:** raw input starting with `/`. **Returns** True to continue the loop, False to exit.
- Parse: `cmd = text[1:].split(maxsplit=1)` → `(name, args)`; `name.lower()`.
- Routes: `help` → print `RAG_V2_HELP` · `search` → args non-empty ? `send_message(args)` + wait : usage error · `repos|use|create|ingest|status|reset` → same-named controller method (arg or None) · `quit` → False · unknown → error + `/help` hint.
- **Post:** no path reaches `send_message` except `search`; no path raises on missing args.

### `show_menu()` (re-purposed)
- Prints `RAG_V2_BANNER` + hint line (`RAG_V2_MENU` rewritten to the hint); the command table lives in `RAG_V2_HELP` and prints only on `/help`.

## Controller operations — `RagV2MainController` (all NEW unless noted)

### `list_repositories() -> None`
- **Pre:** none (works with zero repos). **Post:** `self.repositories` refreshed from `RagV2Provider(self.rag_working_directory).get_repositories()`; each repo printed, active one marked; empty → "no repositories" hint.

### `use_repository(repo_id: str | None) -> None`
- `None`/empty → `select_repository()` (interactive picker, unchanged).
- Registry hit → swap + `_agent_service = None` + confirm.
- Else `RagV2Provider.get_repository(repo_id)` → register + swap + invalidate + confirm.
- Else → `print_message_error(f"Unknown repository: {repo_id}")`.

### `create_repository_named(name: str | None) -> RagV2Repository | None`
- `None`/empty → existing prompt flow `create_repository()`.
- Else `_create_repository(name)` (same validation); success → active + registry + invalidate + confirm; invalid → error, `None`.

### `ingest(kind: str | None, target: str | None) -> None`
- **Guards (in order):** no active repo → error hint; kind not in `{web, pdf, md}` → usage line; target empty → usage line.
- **Post:** calls `ingest_web(url, repository_path=…)` / `ingest_pdf(path, …)` / `ingest_md(path, …)` exactly as the sub-controllers do; prints the returned chunk count; exceptions → `print_message_error`, REPL survives.

### `show_status() -> None`
- No active repo → hint (`/use` or `/create` first).
- Else prints: repo id, path, `get_rag_state()` fields (url / db location / documents location, `<none>` when absent), and the agent thread id when the service is built.

### `reset_chat() -> None`
- Service built → `reset_conversation()` + "conversation reset"; not built → "no active conversation" (still returns cleanly).

### `_run_agent()` (extended wiring)
- Adds `on_tool_call=lambda name, args: view.print_message(f"» {_TOOL_LABELS.get(name, name)}: {args}")` and `on_tool_result=lambda name, preview: view.print_message(f"« {_TOOL_LABELS.get(name, name)}: {preview}")`.
- `_TOOL_LABELS = {"search_documents": "search", "ingestion_status": "status", "task": "analyst"}`.

### `show_chat()` — REMOVED
- From `RagV2MainController` and `IRagV2ViewPartner`; contract test updated in the same cycle.

## Service operations — `rag_v2_agent_service.py`

### `_dispatch_stream_delta(...)` (extended)
- AI message with non-empty `tool_calls` → `on_tool_call(tc.name, str(tc.args)[:120])` per call; existing `on_answer(content)` route unchanged (guarded on non-empty content).
- Message of type `tool` → `on_tool_result(msg.name or "tool", str(msg.content)[:120])`.
- `lc_source == "summarization"` filter applies before all routing (unchanged).

## Tool renames — `rag_v2_tools.py`

| Old | New |
|---|---|
| `rag_search` (@tool name + fn) | `search_documents` |
| `_rag_search_impl` | `_search_documents_impl` |
| `RagSearchResult` | `SearchDocumentsResult` |
| `rag_ingest_status` (@tool name + fn) | `ingestion_status` |
| (its impl/result mirrors) | `_ingestion_status_impl` / `IngestionStatusResult` (or existing names mirroring the same pattern) |

- `RAG_V2_TOOLS` + `build_rag_v2_tools` `@tool("…")` decorators use the new names; schemas still expose no `repository_path`.
- Prompts (`DEFAULT_RAG_V2_SYSTEM_PROMPT` + path-binding suffix) reference new names; `rag_v2_retriever.py` docstring updated.
- **Totality postcondition:** `rg "rag_search|rag_ingest_status" src/ tests/` → 0 hits (historical `.meta/` docs excluded — immutable records).
