# Design 001: DeepAgent Context Optimization for Coding Module

> **Phase:** Design — `omt_agent_guide.md §2`, §5–§10
> **Feature:** feature_025.coding_context_window_optimization
> **Parent context:** Console coding module (`feature_024` console parity) reaches the model's context window too quickly because every `file_read` / `file_search` / `file_list` result accumulates verbatim in the LangGraph checkpointer history with no compression or offloading.

## Summary

Replace the bare `create_agent` call in `CodingAgentService` with the **LangChain deepagents full stack** via `create_deep_agent`. The deepagent harness wires four middleware layers — `FilesystemMiddleware` (offload large tool outputs to a virtual filesystem, replacing them with a pointer + 10-line preview), `SummarizationMiddleware` (auto-compress older conversation turns when context crosses 85% of the model's `max_input_tokens`), `MemoryMiddleware` (always-loaded `AGENTS.md`-style guidelines), and `SkillsMiddleware` (on-demand `SKILL.md` progressive disclosure) — plus a `compact_conversation` tool the agent can call between tasks. Together these keep the console coding agent working inside a single context window across long, multi-file sessions without manual trimming.

## Problem Analysis

### Current behavior (`src/agentx/model/coding/coding_agent_service.py`)

```python
self._agent = create_agent(
    model=self._llm,
    tools=self._tools,            # 5 file tools — outputs stay in history
    system_prompt=self._system_prompt,
    checkpointer=self._checkpointer,
)
```

- **No middleware.** Every `file_read`, `file_search`, `file_list` result is added to the message history **in full** and never compressed.
- **Checkpointer grows monotonically.** `InMemorySaver` keeps every `ToolMessage` for the life of the thread. A 2000-line file read stays in context for every subsequent turn.
- **No offloading.** Big tool outputs (>20k tokens by default) are not written aside; they sit in the active window until it overflows.
- **No summarization.** When the window fills, the next model call raises `ContextOverflowError` and the run fails — there is no fallback.
- **Workflow symptom:** the user reads 3–4 files, the agent edits one, and by the next question the context is near the limit; further turns degrade or error out.

### DeepAgent techniques (from LangChain docs)

Per [`/oss/python/deepagents/context-engineering`](https://docs.langchain.com/oss/python/deepagents/context-engineering) and [`/oss/python/deepagents/overview`](https://docs.langchain.com/oss/python/deepagents/overview):

| Layer | What it does | Token impact |
|------|--------------|---------------|
| **FilesystemMiddleware** | When a tool call input or result exceeds 20k tokens, offload it to a configured backend and substitute a file-path pointer + 10-line preview in history. | Removes the single biggest source of bloat — full file contents. |
| **SummarizationMiddleware** | When context crosses 85% of `max_input_tokens` (and nothing more is eligible for offloading), an LLM summarizes older turn history into a structured summary; the original is written to the filesystem as a canonical record. | Compresses accumulated reasoning/tool chatter. Recovers from `ContextOverflowError` by retrying with the summary + recent messages. |
| **MemoryMiddleware** | Always loads `AGENTS.md`-style memory into the system prompt. | Static, minimal cost — keeps conventions in scope without per-turn reload. |
| **SkillsMiddleware** | Reads `SKILL.md` frontmatter at startup; loads full skill content only when relevant. | Progressive disclosure — detailed workflows enter context only when needed. |
| **`compact_conversation` tool** | (`create_summarization_tool_middleware`) Lets the agent trigger compaction on demand between tasks instead of waiting for 85%. | Agent-driven compaction reduces peaks. |

`create_deep_agent` assembles these in the correct order (Skills → Filesystem → Subagents → Summarization → Patch → caching → Memory) so each layer sees the messages the next layer expects.

## Components / Files Affected

| File | Layer | Change |
|------|-------|--------|
| `src/agentx/model/coding/coding_agent_service.py` | Model | Swap `create_agent` → `create_deep_agent`; wire middleware stack + `StateBackend`; add `compact_conversation` tool middleware; keep `thread_id`, `cancel`, `is_running`, `get_history`, `reset_conversation` API stable. |
| `src/agentx/model/coding/coding_agent_service.py` | Model | Accept optional `memory` / `skills` / `backend` ctor args (default: project `AGENTS.md` + `./skills/` if present). |
| `src/agentx/model/coding/coding_agent_service.py` | Model | Preserve `from langchain.agents import create_agent` import line (MVC pin `test_coding_mvc.py::test_coding_agent_service_model_layer` checks its presence) — kept as a guarded import for fallback/legacy paths; the live path uses `create_deep_agent`. |
| `pyproject.toml` | Deps | Add `deepagents` (>=0.7 for `FilesystemMiddleware` tools allowlist). |
| `src/agentx/model/coding/coding_skills/` (new) | Skills | One optional `SKILL.md` per coding workflow (e.g. refactor, read-before-edit) — progressive-disclosure placeholder. |
| `tests/features/feature_025.coding_context_window_optimization/` (new) | Tests | RED: middleware wiring, offload behavior, summarization trigger, compact tool registration, API stability. |

## Static Structure (Classes & Files)

```python
# src/agentx/model/coding/coding_agent_service.py  (after)
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.middleware import (
    FilesystemMiddleware,
    MemoryMiddleware,
    SkillsMiddleware,
)
from deepagents.middleware.summarization import create_summarization_tool_middleware
from langchain.agents import create_agent  # kept for MVC pin + fallback
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import SummarizationMiddleware

class CodingAgentService:
    def __init__(
        self,
        llm: BaseChatModel | None = None,
        tools: List[BaseTool] | None = None,
        system_prompt: str | None = None,
        *,
        backend: StateBackend | None = None,
        memory: list[str] | None = None,
        skills: list[str] | None = None,
    ) -> None:
        ...
        self._backend = backend or StateBackend()
        self._agent = create_deep_agent(
            model=self._llm,
            tools=self._tools,
            system_prompt=self._system_prompt,
            backend=self._backend,
            checkpointer=self._checkpointer,   # InMemorySaver kept for thread history
            memory=memory,                      # e.g. ["./AGENTS.md"] or None
            skills=skills,                      # e.g. ["./src/agentx/model/coding/coding_skills/"]
            middleware=[
                create_summarization_tool_middleware(self._llm, self._backend),
            ],
        )
```

## Functional Flow (Sequence)

```
User → ConsoleCodingView.show() → CodingController.send_message(msg)
   → CodingAgentService.stream_agent(msg, callbacks...)
      → create_deep_agent graph invoked with {"messages": [{user, msg}]}
         [SkillsMiddleware]      : frontmatter loaded; full skill deferred
         [FilesystemMiddleware]  : file tools registered; >20k outputs offloaded
         [SummarizationMiddleware]: watches context; at 85% → summarize older turns
                                    on ContextOverflowError → retry w/ summary + recent
         [compact_conversation]  : agent may call between tasks
      → agent.stream_events(version="v3") consumed by service
         → on_reasoning / on_tool_call / on_tool_result / on_answer / on_done / on_error
   → ConsoleCodingView.show_thinking()/show_tool_call()/... (unchanged UI)
```

## Operation Specifications (Service Methods)

| Method | Pre | Post | Exceptions |
|--------|-----|------|------------|
| `CodingAgentService(llm?, tools?, system_prompt?, backend?, memory?, skills?)` | — | `_agent` is a deepagent-compiled graph; `_tools`, `_checkpointer`, `_thread_id` set | `ImportError` if `deepagents` not installed (mitigated by pyproject dep) |
| `stream_agent(user_message, on_*)` | not running | runs; emits callbacks; calls `on_done` or `on_error` | caught internally → `on_error` |
| `cancel()` | — | `_cancel_event` set; next delta breaks | — |
| `reset_conversation()` | — | new `_thread_id`; checkpointer fresh | — |
| `get_history()` | — | returns `state.values["messages"]` from deepagent graph | swallowed → `[]` |

## Breaking-change risk

- **MVC pin** `test_coding_mvc.py::test_coding_agent_service_model_layer` asserts:
  - `"from langchain.agents import create_agent"` is present in the file ✅ (kept)
  - `"from langgraph.checkpoint.memory import InMemorySaver"` present ✅ (kept)
  - `"textual"` not in file ✅ (still true)
  → GREEN preserved.
- **Integration tests** `test_coding_integration.py` exercise `CodingAgentService()`, properties, `reset_conversation`, `stream_agent` callable — all kept stable via duck-typed API.
- **Console / TUI views** are unchanged — they consume the controller's `show_*` callbacks, which are downstream of the service. The middleware lives inside the agent graph, transparent to the View/Controller.

## Backwards compatibility

- `create_agent` is still imported (MVC pin + fallback).
- A thin fallback path: if `import deepagents` fails at runtime, log a warning and construct the bare `create_agent(...)` agent (current behavior). This keeps the service usable in a stripped environment but the optimization is the default path when `deepagents` is installed (declared in pyproject).
- The existing `system_prompt` (`DEFAULT_CODING_SYSTEM_PROMPT`) is reused; deepagents prepends it to the built-in base prompt.

## Testing strategy (TDD — major_feature)

RED tests (new file `tests/features/feature_025.coding_context_window_optimization/test_deepagent_context_optimization.py`):

1. `test_service_uses_create_deep_agent_when_available` — service ctor wires `_agent` from `create_deep_agent`.
2. `test_service_writes_state_backend_for_offloading` — `_backend` is a `StateBackend`.
3. `test_service_registers_compact_conversation_tool` — `compact_conversation` appears in the agent's tool surface.
4. `test_service_accepts_memory_paths` — ctor stores `_memory`; default is project `AGENTS.md` if present else None.
5. `test_service_accepts_skills_paths` — ctor stores `_skills`; default is the coding skills dir if present else None.
6. `test_service_falls_back_to_create_agent_without_deepagents` — monkeypatch `import deepagents` to raise; service still constructs a usable agent (legacy path).
7. `test_service_preserves_thread_id_cancel_history_api` — `thread_id`, `cancel`, `is_running`, `get_history`, `reset_conversation` behave compatibly.
8. `test_mvc_pin_still_passes` — pin file content for `create_agent` + `InMemorySaver` imports.

GREEN: implement the wiring per the static structure above.

REFACTOR: slim `DEFAULT_CODING_SYSTEM_PROMPT` (the deepagent base prompt already covers file-tool usage); ensure tool descriptions are concise.

## Open questions / risks

- **deepagents version pin**: need `deepagents>=0.7` for the `FilesystemMiddleware(tools=...)` allowlist. Pin to a tested version in pyproject.
- **Model profile availability**: `SummarizationMiddleware` trigger defaults to 85% of `max_input_tokens` from the model profile. For locally-served models (Ollama, llama.cpp) the profile may be absent — the harness falls back to a 170k-token trigger / 6 messages kept. Verify defaulting works for the AIService LLMs.
- **Streaming metadata**: per docs, `stream_events(version="v3")` tokens emitted by the summarization step carry `metadata["lc_source"] == "summarization"` — the service should filter these out of `on_answer`/`on_reasoning` so the console doesn't stream the summary text to the user. Add a filter in `stream_agent`.

## Links

- LangChain deepagents overview: https://docs.langchain.com/oss/python/deepagents/overview
- Context engineering: https://docs.langchain.com/oss/python/deepagents/context-engineering
- Customization (middleware stack order): https://docs.langchain.com/oss/python/deepagents/customization
- `SummarizationMiddleware` API: https://docs.langchain.com/oss/python/langchain/middleware/built-in#summarization
