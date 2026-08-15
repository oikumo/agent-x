# Operation Spec 001: RagV2AgentService + retrieval tools (deepagents-grounded)

> **Phase:** Design — `omt_agent_guide.md §10`
> **Feature:** feature_027.rag_v2
> **Design doc:** `design_001_retrieve_offload_delegate.md`

---

## `RagV2AgentService.__init__`

```python
def __init__(
    self,
    repository_path: str,
    llm: BaseChatModel | None = None,
    tools: List[BaseTool] | None = None,
    system_prompt: str | None = None,
    *,
    backend: Any | None = None,
    memory: "list[str] | None" = None,
    skills: "list[str] | None" = None,
    subagents: "list[dict] | None" = None,
) -> None
```

**Pre:** `repository_path` is a non-empty string pointing at an existing (or to-be-created) repository directory. `AIService` provides a default LLM on no `llm` arg.

**Post:**
- `_llm`, `_repository_path`, `_tools` (default `RAG_V2_TOOLS`), `_system_prompt` (default `DEFAULT_RAG_V2_SYSTEM_PROMPT`), `_checkpointer` (`InMemorySaver`), `_thread_id` (UUID), `_cancel_event`, `_is_running` set (API stable; mirrors `CodingAgentService`).
- `_backend` = `backend or StateBackend()`.
- `_memory` = `memory` or `["./AGENTS.md"]` if the file exists, else `None`.
- `_skills` = `skills` (no auto-detect on day-1; v2 has no skills dir yet).
- `_subagents` = `subagents or [CHUNK_ANALYST]` (NEW vs `CodingAgentService` — explicit v2 subagent; the create_deep_agent kwarg is the surface v2 adds).
- `_agent` = result of `create_deep_agent(model, tools, system_prompt, backend, checkpointer, memory, skills, subagents, middleware=[create_summarization_tool_middleware(model, backend)])`.
- On `ImportError` of `deepagents` at runtime (degraded environment): warn + fall back to the legacy `create_agent(model, tools, system_prompt, checkpointer)` path. **Fallback has NO subagents support** — `rag_search` still works; parallel `chunk-analyst` does not.

**Exc:** swallowed inside `__init__` — never raises (fallback guaranteed; mirrors `coding_agent_service.py:173-184`)

---

## `RagV2AgentService.stream_agent`

```python
def stream_agent(
    self,
    user_message: str,
    on_reasoning: OnReasoning,
    on_tool_call: OnToolCall,
    on_tool_result: OnToolResult,
    on_answer: OnAnswer,
    on_done: OnDone,
    on_error: OnError,
) -> None
```

**Pre:** not currently running (`is_running == False`).
**Post:**
- `is_running == True` for the duration; `_cancel_event.clear()` at start.
- Runs `self._agent.stream_events({"messages": [{"role":"user","content":user_message}]}, config={"configurable":{"thread_id":self._thread_id}}, version="v3")`.
- For each message in `stream.messages`:
  - Skip deltas where `metadata["lc_source"] == "summarization"` (same filter as `coding_agent_service.py:268` — summaries are not user-facing answer/reasoning).
  - Emit `on_reasoning(delta)` for each reasoning delta.
  - Emit `on_answer(delta)` for each text delta.
  - Emit `on_tool_call(name, args_str)` for each finalized tool call.
- For each call in `stream.tool_calls`: emit `on_tool_result(name, str(output))` (or `f"Error: {call.error}"` on failure).
- If `_cancel_event` is NOT set when the stream ends: emit `on_done()`.
- `is_running == False`, `_cancel_event.clear()` in `finally`.

**Exc:** any exception caught → `on_error(str(exc))`. `is_running` always restored in `finally`.

**Cancel:** checked between every delta — `_cancel_event.is_set()` breaks the inner loop at the next token (within one delta of cancellation; mirrors `coding_agent_service.py:259-291`).

---

## `RagV2AgentService.cancel`

```python
def cancel(self) -> None
```

**Pre:** none.
**Post:** `_cancel_event.set()`. The next delta check in `stream_agent` breaks the loop.

---

## `RagV2AgentService.reset_conversation`

```python
def reset_conversation(self) -> None
```

**Pre:** none.
**Post:** `_cancel_event.set()` (halts any pending stream), `_thread_id` = new UUID, `_cancel_event.clear()`. The StateBackend's scratch chunks from the prior thread are NOT carried over (ephemeral per Persistence-strategy decision).

---

## `RagV2AgentService.get_history`

```python
def get_history(self) -> list
```

**Pre:** none.
**Post:** Returns `state.values.get("messages", [])` from `self._agent.get_state({"configurable":{"thread_id":self._thread_id}})`. On any exception: returns `[]` (swallowed; mirrors `coding_agent_service.py:325-338`).

---

## `rag_search` `@tool`

```python
@tool
def rag_search(query: str, repository_path: str, k: int = 5) -> RagSearchResult
```

**Pre:** `repository_path` points at a repository with a ChromaDB vector store (populated by ingestion). `query` is a non-empty string.
**Post:**
- Internally `_rag_search_impl(query, repository_path, k)` performs a similarity search against the repository's ChromaDB (`AIService.rag_chromadb(f"{repository_path}/chroma_db")` — mirrors `rag.py:32-35`).
- For each retrieved hit: writes a chunk file to the agent backend via `backend.upload_files([(f"chunk_{i}.txt", hit.content.encode())])` (the deterministic-naming concern in Open questions; per-turn stable).
- Returns `RagSearchResult(hits=[RagSearchHit(...)], chunks_uploaded=N, truncated=..., error=...)`. The `hits` carry citation metadata (`source_path`, `page`/`line`).
- Under `create_deep_agent`: if `RagSearchResult` exceeds 20k tokens serialized, `FilesystemMiddleware` auto-offloads it to a pointer + 10-line preview in history (the auto-offload is NOT the same as the explicit `upload_files` for deterministic subagent access — both happen).

**Exc:** swallowed inside `_rag_search_impl` — returns `RagSearchResult(hits=[], chunks_uploaded=0, truncated=False, error=str(exc))` on any internal failure (the orchestrator gets a clean error result, not an exception).

---

## `rag_ingest_status` `@tool`

```python
@tool
def rag_ingest_status(repository_path: str) -> dict
```

**Pre:** `repository_path` is a non-empty string.
**Post:** Returns `{"database_exists": bool, "documents_exist": bool, "ingested_url": str | None}` — reads from `RagV2` (mirrors v1 `rag.py:69-92` `database_exists` / `documents_exist` / `get_ingested_url`).
**Exc:** swallowed — returns `{"error": str(exc)}` on failure.

---

## `chunk-analyst` SubAgent (dispatched via built-in `task`)

```python
# dispatched by the orchestrator via:
task({"subagentType": "chunk-analyst", "description": "Summarize chunk_0.txt"})
```

**Pre:** a chunk file (`chunk_0.txt`, …) exists in the agent backend (uploaded by a prior `rag_search` call this turn).
**Post:** the chunk-analyst subagent runs with `CHUNK_ANALYST["system_prompt"]` as its system prompt, reads the named chunk file via the built-in `read_file`, and returns a structured summary (free text — the orchestrator parses). One chunk per call; the orchestrator dispatches one `task()` per chunk in parallel (context quarantine per deepagents design).
**Exc:** the deepagents `task()` propagates subagent exceptions back to the orchestrator as tool-call errors; the orchestrator's own `on_tool_result` handler surfaces them (or the `on_error` path if the orchestrator run fails).

---

## `RagV2MainController.show_rag_v2` (the `set_view()` gate)

> Per Constraint (d) + feature_024 TA: gotcha @ `main_controller.py:251,273`.

```python
def show_rag_v2(self) -> None
```

**Pre:** `self._rag_v2_controller is None` (C5 reuse — idempotent; if already wired, no-op).
**Post:**
- Constructs `RagV2MainController()`.
- If `self._provider is not None`: calls `self._provider.create_rag_v2_view(rag_v2_controller)` → returns `rag_v2_view`.
- **Calls `rag_v2_controller.set_view(rag_v2_view)`** (NOT `rag_v2_controller.view = rag_v2_view` — the bug-pin). This is the wiring that flips the v2 streaming callbacks on; the buggy `.view =` path leaves `_view=None` → `_run_agent` silent-no-ops all streaming.
- Stores `self._rag_v2_view = rag_v2_view` (for screen connection; the TUI path pushes a screen, the console command enters the REPL via `view.show()` afterwards — feature_024 parity).
- Stores `self._rag_v2_controller = rag_v2_controller`.

**Exc:** none (no `raise` in the body; downstream wiring errors surface at `view.show()` time).

---

## G5 multi-repo session switch

```python
# RagV2MainController
def switch_repository(self) -> None
```

**Pre:** at least one repository exists in the repositories list.
**Post:** invokes `RagV2RepositorySelectionController.show()` → caches the selected `RagV2Repository` into `self.current_repository` → refreshes `self.get_rag_state()` → calls `self.view.show_repository_state(state)`. The next `show_chat()` constructs `RagV2AgentService(repository_path=self.current_repository.path)` — the active repository's path binds at agent construction (NOT a hot-swap; the agent is per-repository).

**Idempotency:** switching to the currently-selected repository is a no-op (the selection controller returns the same `RagV2Repository`; the agent is NOT re-constructed).

**Exc:** swallowed — a selection failure prints a view error and leaves the prior `current_repository` unchanged (no partial state).

---

## Ingestion sub-screens (G4 — PDF/MD/web)

> The three ingestion controllers all follow the same operation shape; the only difference is the loader the controller invokes.

```python
# RagV2PdfIngestionController / RagV2MdIngestionController / RagV2WebIngestionController
def ingest(self, source: str) -> bool
```

**Pre:** `source` is a valid path (PDF/MD) or URL (web). `current_repository` is set on the parent `RagV2MainController`.
**Post:**
- Runs the async loader under `asyncio.run(...)` (D6 invariant — async scoped to ingestion only; NOT to retrieval/chat).
- The loader writes chunks to the repository's ChromaDB (`AIService.rag_chromadb(f"{repository_path}/chroma_db")`).
- The loader writes an ingestion record to the SQLite journal (`RagV2Database.insert_ingestion_entry`).
- Returns `True` on success; `False` on validation or loader failure (swallowed — view prints the error).

**Exc:** swallowed inside `ingest` — returns `False`; the view surfaces the error string.

**Async boundary:** `asyncio.run(...)` is the ONLY async surface (mirrors v1 `rag.py:62`); retrieval/chat/streaming stays sync via the deepagents orchestrator.
