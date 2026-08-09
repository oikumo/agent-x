# Analysis 001: Context-window bloat in the Coding module

> **Phase:** Analysis — `omt_agent_guide.md §1`–§4
> **Feature:** feature_025.coding_context_window_optimization
> **Design doc:** `4.design/features/feature_025.coding_context_window_optimization/design_001_deepagent_context_optimization.md`

## Problem statement

The console coding module (delivered under feature_024 console parity) reaches the model's context window too quickly during realistic multi-file coding sessions. The user reports the coding agent "uses context window too quickly" — the session degrades or errors out after only a handful of file reads / searches.

## Current implementation

`src/agentx/model/coding/coding_agent_service.py` builds the agent with the **bare** LangChain agent factory:

```python
self._agent = create_agent(
    model=self._llm,
    tools=self._tools,            # 5 file tools
    system_prompt=self._system_prompt,
    checkpointer=self._checkpointer,   # InMemorySaver
)
```

No middleware is registered. The five tools (`file_search`, `file_read`, `file_edit`, `file_list`, `file_create`) each return dataclasses whose `str()` renderings are written into the LangGraph message history verbatim.

## Observed bloat sources

| Source | Why it bloats | Token cost per occurrence |
|--------|---------------|---------------------------|
| `file_read` result | Full requested range written into the ToolMessage; a 2000-line file read = ~all of it in history | thousands–tens of thousands |
| `file_search` result | First 5 lines of every matched file embedded as `context`; up to 100 matches | hundreds–thousands |
| `file_list(recursive=True)` | One DirectoryEntry per file in the tree | hundreds–thousands |
| `file_edit` / `file_create` | The unified diff (or new file body) in the ToolMessage + the same content in the ToolCall arguments | thousands |
| Checkpointer | `InMemorySaver` keeps every ToolMessage + AIMessage for the thread forever | monotonically growing |
| System prompt | `DEFAULT_CODING_SYSTEM_PROMPT` reiterates the file-tool workflow — duplicated guidance the deepagent base prompt already covers | ~250 tokens/turn |

With no compression or offloading, the active context equals the entire thread history. A typical session — read 3 files, search once, edit one — easily crosses low-context-window models' limits (e.g. 8k–32k).

## LangChain deepagents techniques available

Per the Docs-by-LangChain knowledge base (`/oss/python/deepagents/context-engineering`, `/oss/python/deepagents/overview`, `/oss/python/deepagents/customization`):

1. **FilesystemMiddleware (offloading)** — when a tool-call input or result exceeds 20k tokens, offload to a configured backend and substitute a file-path pointer + 10-line preview. When context crosses 85% of `max_input_tokens`, truncate older tool calls to a pointer. Removes the single biggest source of bloat: full file contents.
2. **SummarizationMiddleware** — when context crosses 85% of `max_input_tokens` (and nothing more is eligible for offloading), an LLM summarizes older messages into a structured summary; the original is written to the filesystem as a canonical record. On `ContextOverflowError`, the deepagent immediately retries with the summary + recent preserved messages.
3. **MemoryMiddleware** — always-loaded `AGENTS.md`-style memory injected into the system prompt. Static cost; persistent conventions.
4. **SkillsMiddleware** — reads `SKILL.md` frontmatter at startup; loads full skill content only when the agent judges it relevant (progressive disclosure). Detailed workflows enter context only on demand.
5. **`compact_conversation` tool** (`create_summarization_tool_middleware`) — gives the agent a tool to trigger compaction on demand between tasks, instead of waiting for 85%.

`create_deep_agent` assembles these in the correct order (Skills → Filesystem → Subagents → Summarization → Patch → caching → Memory) per `/oss/python/deepagents/customization#bare-stack`.

## Constraints discovered

- **`deepagents` not currently installed.** Only `langchain==1.3.14`, `langgraph==1.2.10`. `SummarizationMiddleware` is importable from `langchain.agents.middleware` without `deepagents`, but `FilesystemMiddleware`, `MemoryMiddleware`, `SkillsMiddleware`, `create_deep_agent`, and `create_summarization_tool_middleware` are in the separate `deepagents` package. **Decision:** add `deepagents>=0.7` to pyproject (user chose the full deepagent stack).
- **MVC pin** — `tests/features/feature_019.coding_agent_screen/test_coding_mvc.py::test_coding_agent_service_model_layer` asserts the literal strings `"from langchain.agents import create_agent"` and `"from langgraph.checkpoint.memory import InMemorySaver"` exist in the service file. Both must remain in the source (the create_agent import is kept for a fallback path; InMemorySaver is kept as the checkpointer).
- **Streaming metadata filter** — docs note `stream_events(version="v3")` emits tokens from the summarization step with `metadata["lc_source"] == "summarization"`. The service must filter these so the console view does not stream the summary text as user-facing answer/reasoning.
- **Model-profile availability** — `SummarizationMiddleware` trigger defaults to 85% of `max_input_tokens` from the model profile. Locally-served models (Ollama, llama.cpp) may lack profile data; the harness falls back to a 170k-token trigger / 6 messages kept. Verify defaulting is acceptable for the AIService LLMs.

## Non-goals

- Not re-architecting the View/Controller layers — the middleware lives inside the agent graph, transparent to the UI.
- Not changing the file tool implementations (`coding_tools.py`) — offloading wraps the tool results, it does not change tool inputs/outputs.
- Not introducing a persistent on-disk backend in this feature — `StateBackend` (in-memory) is sufficient for the console flow; a disk-backed backend is a future feature.

## Recommendation

Proceed to Design with the full deepagent stack per `design_001_deepagent_context_optimization.md`.
