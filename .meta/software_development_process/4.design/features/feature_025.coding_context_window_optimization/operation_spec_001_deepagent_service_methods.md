# Operation Spec 001: DeepAgent-wired CodingAgentService methods

> **Phase:** Design — `omt_agent_guide.md §10`
> **Feature:** feature_025.coding_context_window_optimization
> **Design doc:** `design_001_deepagent_context_optimization.md`

---

## `CodingAgentService.__init__`

```python
def __init__(
    self,
    llm: BaseChatModel | None = None,
    tools: List[BaseTool] | None = None,
    system_prompt: str | None = None,
    *,
    backend: StateBackend | None = None,
    memory: list[str] | None = None,
    skills: list[str] | None = None,
) -> None
```

**Pre:** none (AIService provides a default LLM on no arg).
**Post:**
- `_llm`, `_tools`, `_system_prompt`, `_checkpointer` (InMemorySaver), `_thread_id`, `_cancel_event`, `_is_running` set as before (API stable).
- `_backend` = `backend or StateBackend()`.
- `_memory` stores the memory path list (or None).
- `_skills` stores the skills path list (or None).
- `_agent` = result of `create_deep_agent(model, tools, system_prompt, backend, checkpointer, memory, skills, middleware=[create_summarization_tool_middleware(model, backend)])`.
- On `ImportError` of `deepagents` at runtime (degraded environment): warn and fall back to the legacy `create_agent(...)` path (current behavior).

**Exc:** swallowed inside `__init__` — never raises (fallback guaranteed).

---

## `CodingAgentService.stream_agent`

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

**Pre:** `_is_running` is False.
**Post:**
- Sets `_is_running = True`; invokes `_agent.stream_events({"messages": [{user,user_message}]}, config={thread_id}, version="v3")`.
- Consumes `stream.messages` projection: emits `on_reasoning` per reasoning delta, `on_answer` per text delta, `on_tool_call` per finalized tool call.
- **Filter:** deltas whose metadata carries `lc_source == "summarization"` are NOT forwarded to `on_reasoning`/`on_answer` (so the console does not stream the LLM-generated summary text to the user).
- Consumes `stream.tool_calls` projection: emits `on_tool_result` per completed tool.
- Checks `_cancel_event` between every delta (cancellation within one token).
- On success → `on_done()`. On exception → `on_error(str(exc))`. Finally → `_is_running = False`, `_cancel_event.clear()`.

**Exc:** caught internally — surfaces via `on_error`.

---

## `CodingAgentService.cancel`

```python
def cancel(self) -> None
```

**Pre:** none.
**Post:** `_cancel_event.set()` — the next delta in `stream_agent` breaks the consumption loop.
**Exc:** none.

---

## `CodingAgentService.reset_conversation`

```python
def reset_conversation(self) -> None
```

**Pre:** none.
**Post:** `_cancel_event` set (interrupts any in-flight run), `_thread_id` replaced with a fresh `uuid4()`, `_cancel_event` cleared.
**Exc:** none.

---

## `CodingAgentService.get_history`

```python
def get_history(self) -> list
```

**Pre:** none.
**Post:** returns `state.values.get("messages", [])` from `_agent.get_state({"configurable":{"thread_id": _thread_id}})`. On exception or empty state → `[]`.
**Exc:** swallowed → `[]`.

---

## `CodingAgentService.thread_id` (property)

**Post:** returns `_thread_id` (str). Stable across the conversation until `reset_conversation`.

## `CodingAgentService.is_running` (property)

**Post:** returns `_is_running` (bool).

---

## Fallback path (no `deepagents` installed)

If `import deepagents` raises `ImportError` at `__init__` time:
- Log a warning ("deepagents not installed — coding agent runs without context optimization; install deepagents>=0.7 for full middleware").
- Construct the legacy `_agent = create_agent(model, tools, system_prompt, checkpointer)`.
- All other methods behave exactly as the current implementation (no offloading, no summarization, no `compact_conversation`).

This preserves the project's run-anywhere guarantee (bare `langchain` is sufficient) while making the optimization the default when `deepagents` is present (declared in pyproject so `uv sync` installs it).

---

## Backwards-compatibility matrix

| Existing public API | Behavior change | Risk |
|---------------------|-----------------|------|
| `CodingAgentService(...)` ctor (no new kwargs) | kwargs `backend/memory/skills` are keyword-only with defaults → old callers unaffected | none |
| `stream_agent(msg, on_*)` signature + semantics | Identical contract; new behavior is which messages get forwarded (summarization tokens filtered) | filtered tokens only — callers see the same surface |
| `cancel` / `reset_conversation` / `get_history` / `thread_id` / `is_running` | unchanged | none |
| `from langchain.agents import create_agent` literal in source | kept (fallback path + MVC pin) | MVC pin green |
| `from langgraph.checkpoint.memory import InMemorySaver` literal in source | kept (checkpointer reused by `create_deep_agent` via `checkpointer=` kwarg) | MVC pin green |

## MVC pin test impact

`tests/features/feature_019.coding_agent_screen/test_coding_mvc.py::test_coding_agent_service_model_layer` asserts:
- `"from langchain.agents import create_agent" in content` ✅ (kept)
- `"from langgraph.checkpoint.memory import InMemorySaver" in content` ✅ (kept)
- `"textual" not in content` ✅ (still true — no UI imports added)

No existing test in `tests/features/feature_019.coding_agent_screen/` or `tests/features/feature_024.no_tui_full_features/` breaks.
