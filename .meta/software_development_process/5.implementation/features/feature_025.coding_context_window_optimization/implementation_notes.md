# Implementation Notes — feature_025.coding_context_window_optimization

> **Phase:** Programming → Testing
> **Feature:** feature_025.coding_context_window_optimization
> **Design:** `design_001_deepagent_context_optimization.md`
> **Operation spec:** `operation_spec_001_deepagent_service_methods.md`
> **Branch point:** bare `create_agent` → Deep Agents full stack via `create_deep_agent`.

## What changed

### `src/agentx/model/coding/coding_agent_service.py`
- **Guarded deepagent import block** (lines 36-50): `try: from deepagents import create_deep_agent / from deepagents.backends import StateBackend / from deepagents.middleware.summarization import create_summarization_tool_middleware` with `_DEEPAGENTS_AVAILABLE = True`; `except ImportError` falls back to `None`-typed sentinels and `_DEEPAGENTS_AVAILABLE = False`. The guarded import is below (not in place of) the `from langchain.agents import create_agent` import literal, preserving the MVC pin (`test_coding_mvc.py::test_coding_agent_service_model_layer`).
- **Ctor signature** — added keyword-only kwargs `backend`, `memory`, `skills` (all default `None`); pre-existing positional `llm`/`tools`/`system_prompt` unchanged, so existing callers (`CodingController`) are unaffected.
- **Memory/skills defaulting** — `memory` defaults to `["./AGENTS.md"]` when the file exists at the cwd (typical project layout), else `None`; `skills` defaults to `["./src/agentx/model/coding/coding_skills/"]` when that dir exists, else `None`. Both can be overridden explicitly.
- **Deep path branch** (when `_DEEPAGENTS_AVAILABLE`):
  - `self._backend = backend or StateBackend()` — a real `StateBackend` for `FilesystemMiddleware` to offload large tool outputs to.
  - `self._agent = create_deep_agent(model, tools, system_prompt, backend, checkpointer, memory, skills, middleware=[create_summarization_tool_middleware(model, backend)])` — the Deep Agents bare stack (FilesystemMiddleware + SummarizationMiddleware + MemoryMiddleware + SkillsMiddleware) is auto-wired by `create_deep_agent`; the on-demand `compact_conversation` tool comes from the `create_summarization_tool_middleware` we pass via `middleware=`.
  - Defensive `try/except` around `create_deep_agent` — on any unexpected failure, log a warning and fall back to the legacy `create_agent(...)` build so the service is never left unusable.
- **Fallback path** (when `_DEEPAGENTS_AVAILABLE` is False): `_backend = None`; `_agent = create_agent(model, tools, system_prompt, checkpointer)` — identical to the pre-feature_025 behavior, with one warning log explaining how to install `deepagents>=0.7` for full middleware.
- **`stream_agent` filter** — added a metadata inspection in the messages loop: deltas whose metadata carries `lc_source == "summarization"` (token produced by the `SummarizationMiddleware` step) are skipped before forwarding to `on_reasoning`/`on_answer`, so the console doesn't stream summary-chatter to the user. Defensive `getattr(message, "metadata", None) or {}` keeps the path safe on mock agents in tests.
- **REFACTOR:** `DEFAULT_CODING_SYSTEM_PROMPT` slimmed — removed the per-tool bullet list (deepagent's base prompt already documents file-tool usage) and added a "between user tasks you MAY call `compact_conversation`" line so the agent is aware of the new on-demand compaction tool.

### `pyproject.toml`
- Added `deepagents>=0.7` to `dependencies` (resolves to 0.7.5 at write time). The `>=0.7` floor matches the design constraint for the `FilesystemMiddleware(tools=...)` allowlist (per LangChain docs `/oss/python/deepagents/customization#examples`). Not yet used (the deepagent bare stack offloads by default, no allowlist override needed), but covering for future restricted-tool configs.

### `src/agentx/model/coding/coding_tools.py`
- No code changes. The TA: XREF note at line 18 (describing how `FilesystemMiddleware` will offload tool results >20k tokens) stays as a contract record — the tool I/O contract is unchanged; only the in-history representation is compressed by the deepagent stack.

## Public API surface (post-change)

| Symbol | Before | After | Breaking? |
|--------|--------|-------|-----------|
| `CodingAgentService(llm?, tools?, system_prompt?)` | 3 positional args | + 3 keyword-only (`backend/memory/skills`, all defaulting to safe values) | No — existing positional callers unchanged |
| `stream_agent(user_message, on_*)` | unchanged | adds `lc_source == "summarization"` filter | No — pure addition |
| `cancel` / `reset_conversation` / `get_history` / `thread_id` / `is_running` | unchanged | unchanged | No |
| `from langchain.agents import create_agent` literal in source | present | present (kept for fallback + MVC pin) | No |
| `from langgraph.checkpoint.memory import InMemorySaver` literal in source | present | present (checkpointer reused via `checkpointer=` kwarg to `create_deep_agent`) | No |

## Fallback semantics

When `import deepagents` raises (`_DEEPAGENTS_AVAILABLE = False`), the service warns once and builds the legacy agent via `create_agent(...)` — identical to the pre-feature_025 behavior. No middleware, no offloading, no `compact_conversation` tool, no `lc_source` filter noop (the messages loop's `getattr(message, "metadata", None) or {}` returns `{}` so the summarization-check `get("lc_source")` is None → branch skipped; deltas flow through unchanged).

This preserves the project's run-anywhere guarantee: `pyproject.toml` declares `deepagents>=0.7` for the optimization, but stripping the dep still yields a working coding agent.

## What did NOT change

- `coding_tools.py` — file tool implementations and `@tool` wrappers untouched.
- The console + TUI views (`ConsoleCodingView`, `CodingTUIScreen`), `CodingController`, and `ICodingViewPartner` — they consume callbacks from `stream_agent` whose contract is unchanged (the new metadata filter is invisible to them).
- The `InMemorySaver` checkpointer is still the per-thread history backend (`create_deep_agent` reuses it via `checkpointer=`).
- `AIService` and the model-profile plumbing — `CodingAgentService` still defaults to `AIService().get_current_llm()` when `llm=None`. The `SummarizationMiddleware` falls back to its 170k-token / 6-message defaulting when no model profile is available (per LangChain docs).

## Risks followed up

- **deepagents version pin**: pinned to `>=0.7`; resolved to 0.7.5. The `FilesystemMiddleware(tools=[...])` allowlist requires this floor — not used today but reserved.
- **Model profile**: `SummarizationMiddleware` defaulting (170k / 6-msg fallback when profile absent) is owned by the deepagent stack; tested indirectly via the wiring tests (mock LLM, no profile).
- **Streaming metadata**: `lc_source == "summarization"` filter added per the operation spec §stream_agent filter. The filter is defensive (`getattr(message, "metadata", None) or {}`) so it's a no-op on mock agents in tests, and live runs see the metadata produced by the real middleware.

## TDD evidence

- **testlist recorded** (8 behaviors) via `uv run python -m scripts.omt.tdd.cli testlist` (TS wrapper bug workaround — `omt_tdd{op:testlist}` tool fails with `Expecting value: line 1 column 1` for any payload). Ledger: `.meta/.omt/ledger.jsonl`.
- **RED** at `test_deepagent_context_optimization.py::TestDeepAgentWiring::test_service_uses_create_deep_agent_when_available` — 5 of 8 tests failed cleanly (runnable exit 1, not collection error); 3 already-passing tests verified the unchanged parts of the design (fallback, API stability, MVC pin).
- **GREEN** — implemented the wiring; all 8 tests green.
- **REFACTOR** — slimmed `DEFAULT_CODING_SYSTEM_PROMPT`; all 8 still green.
- **done** — phase exit approved.
