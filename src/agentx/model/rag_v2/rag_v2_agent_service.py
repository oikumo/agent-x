"""RagV2AgentService — the DeepAgents-grounded RAG orchestrator (feature_027).

Parallel to ``CodingAgentService`` (feature_025); wires ``create_deep_agent``
with the retrieve-offload-delegate RAG pattern (D5 lock):

  * ``rag_search`` ``@tool`` writes chunks to the backend filesystem;
  * the ``chunk-analyst`` subagent reads/greps/summarizes individual files in
    parallel via ``task()``;
  * the orchestrator synthesizes a citation-bearing final answer.

Same streaming API surface as ``CodingAgentService`` (``stream_agent`` /
``cancel`` / ``reset_conversation`` / ``get_history`` / ``is_running`` /
``thread_id``) so the v2 controller's ``show_*`` callbacks wire identically.

Guarded-import + fallback pattern mirrors ``coding_agent_service.py:39-50``:
if ``import deepagents`` raises, v2 degrades to bare ``create_agent`` (no
middleware, no subagents; ``rag_search`` still works, parallel
``chunk-analyst`` does not). Same guard surface; no behavior drift.
"""

from __future__ import annotations

import logging
import threading
import uuid
from typing import Any, Callable, List, Optional

from langchain.agents import create_agent  # KEPT for fallback parity with CodingAgentService
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from agentx.model.ai.service import AIService
from agentx.model.rag_v2.rag_v2_tools import build_rag_v2_tools
from agentx.model.rag_v2.rag_v2_subagents import CHUNK_ANALYST

logger = logging.getLogger(__name__)

# Guarded deepagent imports — same pattern as coding_agent_service.py:39-50.
try:
    from deepagents import create_deep_agent
    from deepagents.backends import StateBackend
    from deepagents.middleware.summarization import (
        create_summarization_tool_middleware,
    )
    _DEEPAGENTS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DEEPAGENTS_AVAILABLE = False
    create_deep_agent = None  # type: ignore[assignment]
    StateBackend = None  # type: ignore[assignment]
    create_summarization_tool_middleware = None  # type: ignore[assignment]


DEFAULT_RAG_V2_SYSTEM_PROMPT = (
    "You are a retrieval-augmented assistant that helps users find and reason "
    "about documents in their repositories. Use the rag_search tool to retrieve "
    "matching chunks from the active repository, then dispatch the "
    "chunk-analyst subagent via task({subagentType: 'chunk-analyst', "
    "description: ...}) to summarize individual files in parallel. "
    "Synthesize a final answer with citations to the source chunks. "
    "Always prefer grounding answers in retrieved chunks before responding."
)

# Type aliases mirror CodingAgentService (coding_agent_service.py:71-77).
OnReasoning = Callable[[str], None]
OnToolCall = Callable[[str, str], None]
OnToolResult = Callable[[str, str], None]
OnAnswer = Callable[[str], None]
OnDone = Callable[[], None]
OnError = Callable[[str], None]


class RagV2AgentService:
    """DeepAgents-grounded RAG orchestrator — parallel to CodingAgentService.

    Wires ``create_deep_agent`` with the retrieve-offload-delegate RAG pattern
    (D5 lock): the retrieval @tool writes chunks to the backend filesystem,
    the chunk-analyst subagent reads/greps/summarizes individual files in
    parallel via task(), the orchestrator synthesizes a citation-bearing
    final answer. Same streaming API surface as CodingAgentService
    (stream_agent / cancel / reset_conversation / get_history / is_running
    / thread_id) so the v2 controller's show_* callbacks wire identically.
    """

    def __init__(
        self,
        repository_path: str,           # the active repository (G5 multi-repo switch swaps this)
        llm: BaseChatModel | None = None,
        tools: List[BaseTool] | None = None,
        system_prompt: str | None = None,
        *,
        backend: Any | None = None,
        memory: "list[str] | None" = None,
        skills: "list[str] | None" = None,
        subagents: "list[dict] | None" = None,
    ) -> None:
        if llm is None:
            llm = AIService().get_current_llm()

        self._llm = llm
        self._repository_path = repository_path
        # feature_027 fix: bind the default tools to THIS repository. The old
        # module-level RAG_V2_TOOLS take repository_path as a model-supplied
        # argument — the LLM does not know the real path and hallucinates one
        # (observed '/home/user/...' → PermissionError inside RagV2Database).
        # build_rag_v2_tools closes over the path so the tool schemas expose
        # no repository_path at all.
        self._tools: List[BaseTool] = (
            list(tools) if tools is not None else build_rag_v2_tools(repository_path)
        )
        self._system_prompt: str = system_prompt or (
            DEFAULT_RAG_V2_SYSTEM_PROMPT
            + f"\nThe active repository is bound server-side; rag_search and "
              f"rag_ingest_status need no path argument — never invent one. "
              f"(Repository: {repository_path})"
        )
        self._checkpointer = InMemorySaver()
        self._thread_id: str = str(uuid.uuid4())
        self._cancel_event = threading.Event()
        self._is_running: bool = False

        self._memory: Optional[list[str]] = memory
        self._skills: Optional[list[str]] = skills
        # v2 has no skills dir on day-1; skills is None-able (unlike coding's auto-detect).
        self._subagents: list[dict] = list(subagents) if subagents is not None else [CHUNK_ANALYST]

        if _DEEPAGENTS_AVAILABLE:
            self._backend = backend if backend is not None else StateBackend()  # type: ignore[operator]
            self._agent = create_deep_agent(  # type: ignore[operator]
                model=self._llm,
                tools=self._tools,
                system_prompt=self._system_prompt,
                backend=self._backend,
                checkpointer=self._checkpointer,
                memory=self._memory,
                skills=self._skills,
                subagents=self._subagents,        # NEW vs coding_agent_service.py — explicit v2 subagent
                middleware=[
                    create_summarization_tool_middleware(  # type: ignore[operator]
                        self._llm, self._backend
                    ),
                ],
            )
        else:
            self._backend = None
            logger.warning(
                "deepagents not installed — rag v2 runs without context "
                "optimization; install deepagents>=0.7 for full middleware"
            )
            # NOTE: bare create_agent has NO subagents support — fallback path
            # degrades to a no-subagent orchestrator (chunk-analyst unavailable).
            # The tool still works; parallel chunk summarization does not.
            self._agent = create_agent(
                model=self._llm,
                tools=self._tools,
                system_prompt=self._system_prompt,
                checkpointer=self._checkpointer,
            )

    # ── Public API surface (mirrors CodingAgentService) ──────────────────────

    @property
    def repository_path(self) -> str:
        return self._repository_path

    @property
    def thread_id(self) -> str:
        return self._thread_id

    @property
    def is_running(self) -> bool:
        return self._is_running

    def cancel(self) -> None:
        """Signal an in-flight stream_agent to stop at the next delta boundary."""
        self._cancel_event.set()

    def reset_conversation(self) -> None:
        """Mint a fresh thread_id + clear the cancel flag (new conversation)."""
        self._thread_id = str(uuid.uuid4())
        self._cancel_event.clear()
        self._is_running = False

    def get_history(self) -> list:
        """Return the conversation messages for the current thread_id.

        Mirrors CodingAgentService.get_history: reads the checkpointer state
        for ``self._thread_id`` and returns the ``messages`` list (empty when
        no turns have run yet).
        """
        try:
            config = {"configurable": {"thread_id": self._thread_id}}
            state = self._agent.get_state(config)  # type: ignore[union-attr]
            values = getattr(state, "values", {}) or {}
            messages = values.get("messages", [])
            return list(messages)
        except Exception:  # pragma: no cover — defensive; fresh-checkpointer case
            return []

    def stream_agent(
        self,
        message: str,
        *,
        on_reasoning: OnReasoning | None = None,
        on_tool_call: OnToolCall | None = None,
        on_tool_result: OnToolResult | None = None,
        on_answer: OnAnswer | None = None,
        on_done: OnDone | None = None,
        on_error: OnError | None = None,
    ) -> None:
        """Stream an agent turn, dispatching the streaming callbacks.

        Filters ``lc_source == "summarization"`` deltas out of
        ``on_answer``/``on_reasoning`` (same filter as
        coding_agent_service.py:268) so compaction noise stays out of the UI.
        """
        self._is_running = True
        self._cancel_event.clear()
        try:
            config = {"configurable": {"thread_id": self._thread_id}}
            inputs = {"messages": [{"role": "user", "content": message}]}
            # LangGraph single-mode streams yield bare {node_name: update}
            # dicts — the (mode, chunk) tuple form only appears when passing a
            # LIST of stream modes. Unpacking `for event, chunk in ...` here
            # crashed every turn with "not enough values to unpack".
            for chunk in self._agent.stream(  # type: ignore[union-attr]
                inputs, config=config, stream_mode="updates"
            ):
                if self._cancel_event.is_set():
                    break
                if not isinstance(chunk, dict):
                    continue
                for event, update in chunk.items():
                    _dispatch_stream_delta(
                        event, update,
                        on_reasoning=on_reasoning,
                        on_tool_call=on_tool_call,
                        on_tool_result=on_tool_result,
                        on_answer=on_answer,
                    )
        except Exception as exc:  # pragma: no cover — surface to UI, don't crash
            if on_error is not None:
                on_error(str(exc))
            else:
                logger.exception("rag_v2 stream_agent failed")
        else:
            if on_done is not None:
                on_done()
        finally:
            self._is_running = False


def _dispatch_stream_delta(
    event: str,
    chunk: Any,
    *,
    on_reasoning: OnReasoning | None,
    on_tool_call: OnToolCall | None,
    on_tool_result: OnToolResult | None,
    on_answer: OnAnswer | None,
) -> None:
    """Route a single deepagent stream delta to the matching UI callback.

    Filters ``lc_source == "summarization"`` deltas out of ``on_answer`` /
    ``on_reasoning`` (same filter as coding_agent_service.py:268) so
    compaction noise stays out of the UI.
    """
    if not isinstance(chunk, dict):
        return
    source = chunk.get("lc_source")
    if source == "summarization":
        return
    # Best-effort: most deepagent graphs emitd per-message dicts; route the
    # content fields safely without assuming a strict event schema.
    messages = chunk.get("messages") or []
    for msg in messages:
        kind = getattr(msg, "type", None) or (msg.get("type") if isinstance(msg, dict) else None)
        content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
        if kind == "ai" and content and on_answer is not None:
            on_answer(content)
        elif kind in ("reasoning", "thinking") and content and on_reasoning is not None:
            on_reasoning(content)
