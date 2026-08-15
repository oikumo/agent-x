# Design 001: Retrieve, Offload, and Delegate — RAG v2 Module

> **Phase:** Design — `omt_agent_guide.md §2`, §5–§10
> **Feature:** feature_027.rag_v2
> **Parent context:** `3.analysis/features/feature_027.rag_v2/analysis_001_v1_gaps_and_deepagents_grounding.md` (6-section Analysis; source-of-truth for the design-phase decision set Constraints a–g + the eight v1 surface surprises + the G1–G3 RESOLVED-in-v1 finding).
> **Project home:** `.projects/meta/rag_v2/PROJECT.md` (locked v1.2 — Scope/Vision/Decisions D1–D8; this doc does NOT re-negotiate any locked axis).
> **Sibling design dir:** `4.design/features/feature_025.coding_context_window_optimization/` (`design_001_deepagent_context_optimization.md` + `operation_spec_001_deepagent_service_methods.md`) — the template shape this doc mirrors (Summary → Problem → Components → Static Structure → Flow → Operation Specs → Risks → Test plan).

<!-- THINK GATE: 5 TA: thoughts consulted at .projects/meta/rag_v2/PROJECT.md:272-276 before writing this design doc:
  - :272 gotcha — D5 pattern locked (retrieve-offload-delegate grounded in coding_agent_service.py:159)
  - :273 todo — v1-cutover deferred to Design (THIS doc records the proof gate — Constraint g)
  - :274 xref ANALYSIS-PARTIAL — deepagents stack verified (graph.py:268-893, middleware auto-assembly order)
  - :275 gotcha ANALYSIS-PARTIAL — G1-G3 STALE vs closure matrix lines 178-187 (v2 mirrors for parity, NOT net-new)
  - :276 risk — D5 rubric-composition boundary-vs-content (composition = §Standing extension, NOT D5 re-pick)
-->

## Summary

Introduce a **console-only new module** — `src/agentx/model/rag_v2/` (model) + `src/agentx/ui/screens/rag_v2/` (UI) — that grounds RAG retrieval as a `@tool` on the deepagents stack feature_025 already ships. The v2 orchestrator is a new `RagV2AgentService` parallel to `CodingAgentService`: it calls `create_deep_agent(model=, tools=[rag_search, …], subagents=[chunk-analyst], backend=StateBackend(), checkpointer=InMemorySaver, memory=, skills=, middleware=[create_summarization_tool_middleware(...)])`, exposing retrieval as a tool the agent invokes rather than a parallel agent system (the v2 Vision's defining inversion). The retrieval `@tool` writes relevant chunks to the agent's backend filesystem via `backend.upload_files()`; a `chunk-analyst` subagent reads/greps/summarizes individual chunk files in parallel via the deepagents built-in `task({subagentType, description})` tool; the orchestrator synthesizes a citation-bearing final answer. This is the LangChain-deepagents **retrieve, offload, and delegate** pattern (D5 lock), grounded in feature_025's actual ship.

The UI surface is a new `RagV2MainController` + `IRagV2View`/`IRagV2ViewPartner` ABC pair + `ConsoleProvider.create_rag_v2_view()` factory + `RagV2ShowCommand` registration on `MainController` — matching feature_024's console MVC++ contract (the 9-point pattern the rest of `src/agentx/ui/screens/` follows). Three inner sub-screens (create-repository, select-repository, ingestion) each get their own ABC pair + factory, closing the narrow G6(a) inner-view parity gap. The v1 RAG tree (`src/agentx/model/rag/` + `src/agentx/ui/screens/rag/`) stays **untouched** until the G1–G6 proof gate passes (cutover decision record in §Cutover below).

## Problem Analysis

### Why a new module, not a patch on v1

v1 (`src/agentx/model/rag/` + `src/agentx/ui/screens/rag/`, shipped under `feature_002`) is a **parallel agent system** — `RagController` builds its own LangChain agent for chat, owns its own ingestion pipeline + SQLite journal + ChromaDB store, and runs side-by-side with the coding agent as a peer, not as a capability. That shape is why v1 "core functional then stalled" (feature_002 §Status): every cross-cutting improvement (context-window management, summarization, memory, skill discovery) would have to be re-implemented inside the RAG agent separately from the coding agent. v2 inverts the topology — **retrieval is a `@tool` the deepagents orchestrator invokes** (the v2 Vision's standing principle), so the four middleware layers feature_025 already ships (`FilesystemMiddleware`, `SummarizationMiddleware`, `MemoryMiddleware`, `SkillsMiddleware`) benefit retrieval for free. Patching v1 in place would mean re-implementing feature_025 inside v1 — the wrong direction.

### The six v1 gaps — closure matrix vs current code

Per `analysis_001_*.md` (re-verified against HEAD commit `90b6bd5`): the closure matrix at `PROJECT.md:178-187` lists G1/G2/G3 as constraints v2 owns, **but v1 already ships them** in the working tree. The three `feature_002` design docs describe PRE-implementation state; commit `cdeb15f` shipped both the designs AND the code the same day (2026-06-21); `FEATURE.md §Status` was never refreshed. v2's **TRUE scope per current code** = G4 + G5 + G6(b) + narrow G6(a). G1–G3 are mirrored in v2 **for parity with feature_024's MVC++ contract**, NOT reimplemented as net-new capability work.

| Gap | verdict (per analysis_001) | File:line evidence | v2 scope |
|---|---|---|---|
| **G1** — repo creation placeholder | RESOLVED in v1 | `rag_create_repository_controller.py:96-126` `_create_repository()` fully implemented | v2 mirrors for parity (new ABC pair + factory + `set_view()`); NOT net-new |
| **G2** — `get_selected_repository()` returns None | RESOLVED in v1 | `rag_repository_selection_controller.py:57-76` returns cached `RagRepository` w/ bounds check | v2 mirrors for parity |
| **G3** — `get_rag_state()` returns None | RESOLVED in v1 | `rag_controller.py:66-107` returns populated `RagState` | v2 mirrors for parity |
| **G4** — PDF/MD ingestion missing | **CONFIRMED** | `model/rag/` has `web_ingestion/` only; no `pdf_ingestion`/`md_ingestion` sibling | **v2 owns closure** (PDF + MD + web ported) |
| **G5** — multi-repo session switch incomplete | **CONFIRMED** | `rag_controller.py:35` holds `current_rag_repository` as a local field; no switch command; no peer-agent propagation | **v2 owns closure** |
| **G6(a)** — console parity (inner) | PARTIALLY CONFIRMED | Outer integration IS parity (`IRagView`/`IRagViewPartner`/`create_rag_view()`); inner views are bare classes w/o `I<X>View` ABC pairs + zero `create_*_view` factories | **v2 owns narrow closure** (3 inner ABC pairs + factories + `set_view()`) |
| **G6(b)** — deepagents grounding | **CONFIRMED** | `rg "deepagents\|create_deep_agent\|@tool\|StateBackend" model/rag/ ui/screens/rag/` = 0 hits | **v2 owns closure** |

### Eight v1 surface surprises carried from analysis_001 (design-time consumption)

1. `rag_query.py:40` — `pprint.pprint(doc)` stdout pollution **in the model layer** → v2 keeps `pprint` out of `model/rag_v2/`.
2. `rag_chat_view.py.show_partial_text()` is **dead** → v2 omits it.
3. `constants.py` vs `FEATURE.md` extract-preset drift → v2 keeps constants as a single source of truth.
4. v1 filename typo `rag_repostitory_selection_view.py` `[sic]` → v2 names cleanly (`rag_v2_repository_selection_view.py`).
5. v1 `web_ingestion/` is the one real asyncio surface; the rest is sync (D6 invariant v2 preserves).
6. v1 `RagChatView` streams via own callbacks, NOT via `UIConsole.stream_write()` → v2 wires streaming through `UIConsole.stream_write()` per feature_024.
7. v1 `RagController.__init__` consumes `repository_selection` tightly → v2's `RagV2MainController` follows the D5 tool-on-orchestrator shape, not a peer-controller dep.
8. v1 holds `current_rag_repository` as a plain attribute (line 35) → v2's session is `RagV2MainController.current_repository` + `repositories` state (G5 closure).

## Components / Files Affected

> All paths are **new siblings** of v1 (`src/agentx/model/rag_v2/`, `src/agentx/ui/screens/rag_v2/`) — v1 (`src/agentx/model/rag/`, `src/agentx/ui/screens/rag/`) is untouched (D3 lock).

### Model layer — `src/agentx/model/rag_v2/`

| File | Layer | Responsibility |
|------|-------|----------------|
| `rag_v2.py` | Model | `RagV2` aggregate — owns the active repository's DB + docs + ingestion-URL state queries (mirrors v1 `rag.py` shape; `pprint`-free). |
| `rag_v2_db.py` | Model | `RagV2Database` — SQLite journal of ingestion entries (mirrors v1 `rag_db.py` schema). |
| `rag_v2_repository.py` | Model | `RagV2Repository` value object (name + path). |
| `rag_v2_agent_service.py` | Model | **`RagV2AgentService`** — the deepagents orchestrator. Parallel to `CodingAgentService`; wires `create_deep_agent(model=, tools=RAG_V2_TOOLS, subagents=[chunk_analyst], backend=StateBackend(), checkpointer=InMemorySaver, memory=, skills=, middleware=[create_summarization_tool_middleware(...)]`)`. Same streaming API surface as `CodingAgentService` (`stream_agent`, `cancel`, `reset_conversation`, `get_history`, `is_running`, `thread_id`). |
| `rag_v2_tools.py` | Model | The `@tool`-wrapped retrieval surface. `rag_search` (similarity search → `backend.upload_files()` chunk files) + `rag_ingest_status` (read-only state probe). `@tool` pattern from `coding_tools.py:18`; dataclass return types. |
| `rag_v2_subagents.py` | Model | The `chunk_analyst` `SubAgent` dict spec — `{name, description, system_prompt, tools?, middleware?, skills?, response_format?, permissions?}`. Dispatched via the built-in `task({subagentType, description})`. |
| `pdf_ingestion/` | Model | PDF loader (async, D6-scoped). New. |
| `md_ingestion/` | Model | MD loader (async, D6-scoped). New. |
| `web_ingestion/` | Model | Web loader ported from v1 (async, D6-scoped). Cleansed of stdout pollution. |
| `query/` | Model | Query helpers (similarity search + history-aware retriever). Reuses LangChain primitives; NO bespoke DSL. |
| `rag_v2_provider.py` | Model | `RagV2Provider` factory (constructs the `RagV2` aggregate). |

### UI layer — `src/agentx/ui/screens/rag_v2/`

| File | Layer | Responsibility |
|------|-------|----------------|
| `rag_v2_controller.py` | UI | **`RagV2MainController`** — implements `IRagV2ViewPartner`; holds `current_repository` + `repositories` state (G5 closure); routes to sub-screens via `set_view()`. |
| `rag_v2_view.py` | UI | **`RagV2View`** — implements `IRagV2View`; the outer composite view. Wires streaming through `UIConsole.stream_write()`. |
| `rag_v2_create_repository_controller.py` + `rag_v2_create_repository_view.py` | UI | Repo-creation sub-screen (G1 mirror for parity). |
| `rag_v2_repository_selection_controller.py` + `rag_v2_repository_selection_view.py` | UI | Repo-selection sub-screen (G2 mirror for parity; clean filename — no `[sic]` typo). |
| `rag_v2_web_ingestion_controller.py` + `rag_v2_web_ingestion_view.py` | UI | Web-ingestion sub-screen (G4 web path). |
| `rag_v2_pdf_ingestion_controller.py` + `rag_v2_pdf_ingestion_view.py` | UI | PDF-ingestion sub-screen (G4 new). |
| `rag_v2_md_ingestion_controller.py` + `rag_v2_md_ingestion_view.py` | UI | MD-ingestion sub-screen (G4 new). |
| `constants.py` | UI | Display constants — single source of truth (fixes v1 constants drift). |

### Integration layer — `src/agentx/ui/`

| File | Layer | Change |
|------|-------|--------|
| `interfaces.py` | Interface | **New ABC pairs**: `IRagV2View`/`IRagV2ViewPartner` (outer) + `IRagV2CreateRepositoryView`/`IRagV2CreateRepositoryViewPartner` + `IRagV2RepositorySelectionView`/`IRagV2RepositorySelectionViewPartner` + `IRagV2WebIngestionView`/`IRagV2WebIngestionViewPartner` + `IRagV2PdfIngestionView`/`IRagV2PdfIngestionViewPartner` + `IRagV2MdIngestionView`/`IRagV2MdIngestionViewPartner` (inner — G6(a) narrow closure). |
| `providers.py` | Provider | New `ConsoleProvider.create_rag_v2_view(...)` factory (outer) + 3 inner `create_*_view(...)` factories. |
| `screens/main/main_controller.py` | Controller | New `show_rag_v2()` method using **`set_view(view)`** NOT `.view = view` (the feature_024 bug-pin Constraint d). New `RagV2ShowCommand` registration. |

### Test layer — `tests/features/feature_027.rag_v2/`

| File | Scope |
|------|-------|
| `test_rag_v2_mvc_contract.py` | MVC++ contract pins (mirrors `test_console_provider_and_views.py` 630-line/10-TestCase shape). |
| `test_rag_v2_commands_and_views.py` | Command registration + view rendering (mirrors `test_console_commands_and_views.py` 250-line shape). |
| `test_rag_v2_agent_service.py` | Deepagents wiring (mirrors `test_deepagent_context_optimization.py` 264-line shape). |
| `test_rag_v2_retrieval_tool.py` | The `rag_search` `@tool` + `backend.upload_files()` + `chunk-analyst` subagent dispatch. |
| `test_rag_v2_gaps_closure_matrix.py` | The G1–G6 closure matrix sharpened to pytest node IDs (this doc's Test plan). |

## Architecture decision — `RagV2AgentService` is a parallel service, NOT tools registered on `CodingAgentService`

> Per `analysis_001_*.md` Recommendation (i): a `RagV2AgentService` parallel to `CodingAgentService`, OR additional `@tool`s registered on `CodingAgentService` itself — a design-phase decision. **This doc takes: a parallel service.**

**Decision: new `RagV2AgentService`**, parallel to `CodingAgentService`. The v2 RAG is a **separate console screen** with its own controller, its own service, its own system prompt, and its own `chunk-analyst` subagent set — reached from the main menu via `RagV2ShowCommand`, the same way `RagShowCommand` reaches v1 RAG today.

**Why parallel, not tools-on-coding:**

1. **Separation of concern.** The coding agent's system prompt (`DEFAULT_CODING_SYSTEM_PROMPT` at `coding_agent_service.py:53-69`) is about file search/read/edit/Create; injecting RAG retrieval tools onto it would blur the coding agent's contract (a maintenance burden for the 5-file-tool MVC pin at `test_coding_mvc.py`). The v2 RAG screen has a different prompt (citation-bearing retrieval + synthesis) and a different subagent set (`chunk-analyst`, not the coding default).
2. **The v1 RAG is already a separate screen.** v1 is reached via `RagShowCommand` on `MainController` (line 73). v2 replacing it with a same-shape sibling (different implementation, same menu position) is the minimal-surprise cutover; folding v2's tools onto the coding screen would move RAG's entry point — a UX change, not just an impl change.
3. **Subagent isolation.** The `chunk-analyst` is a v2-only subagent profile; adding `subagents=[chunk_analyst]` to `CodingAgentService` would change the coding stack's behavior (the `task()` surface gains a new `subagentType`). Keeping v2 parallel means the coding stack's subagent set stays as-feature_025-shipped (D4 consume-don't-modify honored at the composition boundary too).
4. **Both options consume the same stack.** Whichever shape wins, the agent is built via `create_deep_agent(...)` with the same middleware auto-assembly order (Skills → Filesystem → Subagents → Summarization → Patch → [user middleware] → ToolExclusion → PromptCaching → Memory). The parallel-service choice isolates the v2 subagents/tools/middleware kwargs from the coding stack.

## Static Structure (Classes & Files)

### `RagV2AgentService` — the deepagents orchestrator

```python
# src/agentx/model/rag_v2/rag_v2_agent_service.py  (new)
from __future__ import annotations

import threading
import uuid
import logging
from pathlib import Path
from typing import Any, Callable, List, Optional

from langchain.agents import create_agent  # KEPT for fallback parity with CodingAgentService
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from agentx.model.ai.service import AIService
from agentx.model.rag_v2.rag_v2_tools import RAG_V2_TOOLS
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
    "description: ...}) to summarize individual files in parallel. Synthesize "
    "a final answer with citations to the source chunks.\n\n"
    "Always prefer grounding answers in retrieved chunks before responding. "
    "Show reasoning before each tool call. Between user tasks you MAY call "
    "compact_conversation to compress older conversation history."
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

    Wires `create_deep_agent` with the retrieve-offload-delegate RAG pattern
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
        self._tools: List[BaseTool] = list(tools) if tools is not None else list(RAG_V2_TOOLS)
        self._system_prompt: str = system_prompt or DEFAULT_RAG_V2_SYSTEM_PROMPT
        self._checkpointer = InMemorySaver()
        self._thread_id: str = str(uuid.uuid4())
        self._cancel_event = threading.Event()
        self._is_running: bool = False

        self._memory: Optional[list[str]] = memory
        if self._memory is None and Path("AGENTS.md").exists():
            self._memory = ["./AGENTS.md"]
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
```

### `rag_v2_tools.py` — the retrieve-offload `@tool` surface

```python
# src/agentx/model/rag_v2/rag_v2_tools.py  (new) — mirrors coding_tools.py:18 @tool pattern
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from langchain.tools import tool


@dataclass
class RagSearchHit:
    """A single retrieval hit with citation metadata."""
    chunk_id: str
    content: str
    score: float
    source_path: Optional[str] = None
    page: Optional[int] = None       # for PDF sources
    line: Optional[int] = None       # for MD sources


@dataclass
class RagSearchResult:
    """Result of the rag_search tool.

    Under create_deep_agent the FilesystemMiddleware auto-offloads results
    exceeding 20k tokens to a StateBackend (pointer + 10-line preview in
    history). Tool inputs/outputs themselves UNCHANGED — only the in-history
    representation is compressed. (Mirrors coding_tools.py:18 TA: note.)
    """
    hits: List[RagSearchHit]
    chunks_uploaded: int             # how many chunk files landed in backend
    truncated: bool
    error: Optional[str] = None


@tool
def rag_search(query: str, repository_path: str, k: int = 5) -> RagSearchResult:
    """Search the active RAG repository for chunks matching the query.

    Writes retrieved chunks to the agent backend filesystem via
    backend.upload_files() so the chunk-analyst subagent can read/grep
    them in parallel. Returns a pointer-and-preview result; the full
    chunks live in the backend (retrieve-offload-delegate pattern, D5).

    Args:
        query: The similarity-search query string.
        repository_path: The active repository's working directory (G5 switch swaps this).
        k: Top-k chunks to retrieve (default 5).
    """
    return _rag_search_impl(query, repository_path, k)


def _rag_search_impl(query: str, repository_path: str, k: int) -> RagSearchResult:
    """Thin impl wrapper — similarity search + backend.upload_files()."""
    # ... LangChain similarity search against the repository's ChromaDB ...
    # ... backend.upload_files([(f"chunk_{i}.txt", hit.content.encode())]) ...
    # ... return RagSearchResult(hits=..., chunks_uploaded=..., truncated=...) ...
    raise NotImplementedError  # GREEN-phase impl


@tool
def rag_ingest_status(repository_path: str) -> dict:
    """Probe the active repository's ingestion state (read-only).

    Returns a dict with database_exists / documents_exist / ingested_url
    fields — mirrors Rag.database_exists / documents_exist / get_ingested_url
    (rag.py:69-92) but as a @tool the deepagents stack can invoke.
    """
    return _rag_ingest_status_impl(repository_path)


def _rag_ingest_status_impl(repository_path: str) -> dict:
    raise NotImplementedError  # GREEN-phase impl


RAG_V2_TOOLS = [rag_search, rag_ingest_status]
```

### `rag_v2_subagents.py` — the `chunk-analyst` SubAgent dict spec

> Per `analysis_001_*.md` Constraint (b): `subagents=[chunk-analyst]` coexists with the `general-purpose` default. `create_deep_agent` auto-adds the default `general-purpose` subagent (`graph.py:750-814`) UNLESS v2 disables it (`GeneralPurposeSubagentProfile(enabled=False)`). **Decision: keep `general-purpose`** (less surface-area change; the v2 orchestrator can peer-delegate to it for non-chunk tasks).

```python
# src/agentx/model/rag_v2/rag_v2_subagents.py  (new)
from __future__ import annotations

# The chunk-analyst subagent — one-file summarize, dispatched via the
# deepagents built-in task({subagentType, description}) tool. Per the
# LangChain subagents doc (docs.langchain.com/oss/python/deepagents/subagents)
# the SubAgent dict spec is {name, description, system_prompt, tools?,
# middleware?, skills?, response_format?, permissions?}.
CHUNK_ANALYST: dict = {
    "name": "chunk-analyst",
    "description": (
        "Reads a single retrieved chunk file from the agent backend and "
        "returns a concise structured summary: the chunk's key claims, "
        "the source citation, and any named entities. One chunk per call."
    ),
    "system_prompt": (
        "You are a chunk-analyst subagent. You are given a single chunk "
        "file path in the agent backend filesystem. Read it with read_file, "
        "then return a JSON object with keys: summary (str, 1-3 sentences), "
        "citation (str, the source path + page/line), entities (list of "
        "str). Do NOT read multiple files; do NOT search. Be concise."
    ),
    # tools omitted → inherits the deepagents built-in read_file/grep/glob.
    # response_format omitted → returns free text (the orchestrator parses).
    # permissions omitted → default.
}

# The full subagent list passed to create_deep_agent(subagents=...).
# create_deep_agent AUTO-ADDS the general-purpose default alongside this
# list UNLESS v2 disables it (GeneralPurposeSubagentProfile(enabled=False)).
# v2 KEEPS general-purpose (Constraint b) — less surface-area change.
RAG_V2_SUBAGENTS: list[dict] = [CHUNK_ANALYST]
```

### `interfaces.py` additions — the ABC pairs (G6(a) narrow closure)

```python
# src/agentx/ui/interfaces.py  (extend) — new ABC pairs mirror IRagView/IRagViewPartner
# at lines 53 + 274 (short-form naming per Constraint e — no clash).

class IRagV2View(ABC):
    """Abstract interface for RAG v2 Screen View (outer composite)."""
    @abstractmethod
    def show(self) -> None: ...
    @abstractmethod
    def print_message(self, message: str) -> None: ...
    @abstractmethod
    def print_message_error(self, message: str) -> None: ...
    @abstractmethod
    def show_repository_state(self, state: object) -> None: ...
    @abstractmethod
    def show_menu(self) -> None: ...

class IRagV2ViewPartner(ABC):
    """Abstract partner for RAG v2 View (implemented by RagV2MainController)."""
    @abstractmethod
    def select_repository(self) -> None: ...
    @abstractmethod
    def create_repository(self) -> None: ...
    @abstractmethod
    def show_chat(self) -> None: ...
    @abstractmethod
    def show_web_ingestion(self) -> None: ...
    @abstractmethod
    def show_pdf_ingestion(self) -> None: ...      # NEW (G4)
    @abstractmethod
    def show_md_ingestion(self) -> None: ...        # NEW (G4)
    @abstractmethod
    def switch_repository(self) -> None: ...        # NEW (G5)
    @abstractmethod
    def close(self) -> None: ...
    @abstractmethod
    def get_rag_state(self) -> object: ...

# Inner ABC pairs (G6(a) narrow closure — 3 new):
class IRagV2CreateRepositoryView(ABC): ...
class IRagV2CreateRepositoryViewPartner(ABC): ...
class IRagV2RepositorySelectionView(ABC): ...
class IRagV2RepositorySelectionViewPartner(ABC): ...
class IRagV2WebIngestionView(ABC): ...
class IRagV2WebIngestionViewPartner(ABC): ...
# PDF + MD ingestion views (G4) — also ABC pairs:
class IRagV2PdfIngestionView(ABC): ...
class IRagV2PdfIngestionViewPartner(ABC): ...
class IRagV2MdIngestionView(ABC): ...
class IRagV2MdIngestionViewPartner(ABC): ...
```

### `providers.py` additions + `MainController.show_rag_v2()` — the `set_view()` wiring

```python
# src/agentx/ui/providers.py  (extend ConsoleProvider) — mirror create_rag_view at :103
class ConsoleProvider(IUIProvider):
    # ... existing factories ...

    def create_rag_v2_view(self, controller: "IRagV2ViewPartner") -> "IRagV2View":
        """Create console-based RAG v2 view."""
        from agentx.ui.screens.rag_v2.rag_v2_view import RagV2View
        return RagV2View(controller)  # type: ignore

    def create_rag_v2_create_repository_view(self, controller):
        from agentx.ui.screens.rag_v2.rag_v2_create_repository_view import RagV2CreateRepositoryView
        return RagV2CreateRepositoryView(controller)

    def create_rag_v2_repository_selection_view(self, controller):
        from agentx.ui.screens.rag_v2.rag_v2_repository_selection_view import RagV2RepositorySelectionView
        return RagV2RepositorySelectionView(controller)

    def create_rag_v2_web_ingestion_view(self, controller):
        from agentx.ui.screens.rag_v2.rag_v2_web_ingestion_view import RagV2WebIngestionView
        return RagV2WebIngestionView(controller)

    def create_rag_v2_pdf_ingestion_view(self, controller):
        from agentx.ui.screens.rag_v2.rag_v2_pdf_ingestion_view import RagV2PdfIngestionView
        return RagV2PdfIngestionView(controller)

    def create_rag_v2_md_ingestion_view(self, controller):
        from agentx.ui.screens.rag_v2.rag_v2_md_ingestion_view import RagV2MdIngestionView
        return RagV2MdIngestionView(controller)
```

```python
# src/agentx/ui/screens/main/main_controller.py  (extend) — set_view() NOT .view (Constraint d)
class MainController:
    # ...
    def show_rag_v2(self):
        """Create and wire a RagV2MainController — uses set_view() per feature_024 bug-pin."""
        if self._rag_v2_controller is not None:
            return
        from agentx.ui.screens.rag_v2.rag_v2_controller import RagV2MainController
        rag_v2_controller = RagV2MainController()
        if self._provider is not None:
            rag_v2_view = self._provider.create_rag_v2_view(rag_v2_controller)
            rag_v2_controller.set_view(rag_v2_view)   # <— set_view, NOT .view = (Constraint d)
            self._rag_v2_view = rag_v2_view
        self._rag_v2_controller = rag_v2_controller
```

> **Critical `set_view()` note (Constraint d, per feature_024 TA: gotcha @ `main_controller.py:251,273`):** v1's `show_rag` at `main_controller.py:99-110` still uses the **buggy** `rag_controller.view = rag_view` (line 106) — the streaming callbacks the v2 agent emits would silently no-op if v2 copied this pattern. v2's `show_rag_v2()` MUST use `set_view(view)` (the fixed pattern at `show_react`/`show_coding` lines 244/266). This is the single most consequential wiring detail in v2.

## Functional Flow (Sequence)

```
User → RagV2View.show() → RagV2MainController.show_chat()
   → RagV2AgentService(repository_path=current_repository.path).stream_agent(msg, callbacks...)
      → create_deep_agent graph invoked with {"messages": [{user, msg}]}
         [SkillsMiddleware]        : frontmatter loaded (v2 skills=None on day-1 → no-op)
         [FilesystemMiddleware]    : rag_search results >20k tokens offloaded to StateBackend
         [SubAgentMiddleware]      : chunk-analyst + general-purpose subagents registered
                                     → task() tool available to the orchestrator
         [SummarizationMiddleware] : watches context; at 85% → summarize older turns
         [compact_conversation]    : agent may call between tasks
      → orchestrator calls rag_search(query, repository_path)
         → _rag_search_impl similarity-searches the repository's ChromaDB
         → backend.upload_files([(chunk_i.txt, hit.content.encode())])
         → returns RagSearchResult(hits=..., chunks_uploaded=N, ...)
      → orchestrator dispatches task({subagentType: 'chunk-analyst', description: 'summarize chunk_i.txt'})
         → chunk-analyst reads chunk_i.txt via built-in read_file
         → returns {summary, citation, entities}
         → (parallel fan-out: one task() per chunk)
      → orchestrator synthesizes a citation-bearing final answer
      → agent.stream_events(version="v3") consumed by service
         → on_reasoning / on_tool_call / on_tool_result / on_answer / on_done / on_error
         → lc_source=="summarization" deltas filtered out (same filter as coding_agent_service.py:268)
   → RagV2View.show_thinking()/show_tool_call()/... (via UIConsole.stream_write())
```

## Persistence-strategy decision (Constraint c)

> **Decision: keep `StateBackend` (ephemeral, per-turn).**

**Reasoning.** The retrieve-offload-delegate pattern (D5) is **per-turn**: the orchestrator retrieves chunks, the chunk-analyst subagents read them in parallel, the orchestrator synthesizes, then the turn ends. The chunks are **scratch, not state** — they are the *intermediate representation* between retrieval and synthesis, not a durable store. `StateBackend` is thread-scoped (verified at `deepagents/backends/state.py:308`); chunks uploaded this turn do NOT survive `reset_conversation()`. This is the correct behavior for v2: the chunks for this query are irrelevant to the next query against the same repository.

**What `StateBackend` is NOT.** It is **not** the vector store. The vector store is ChromaDB (unchanged from v1; `AIService.rag_chromadb(vector_db_path)` at `service.py:59`). The `backend.upload_files()` call writes agent-side scratch chunk files for subagent `read_file`/`grep` access — NOT a second vector store. These are different concerns; the `backend=` choice is about agent-side chunk files only.

**When v2 would revisit.** Swap to `FilesystemBackend`/`StoreBackend`/`CompositeBackend` (persistent) ONLY if a future iteration needs chunks to survive across turns (e.g., "ask a follow-up question against the same chunks without re-retrieving"). That is `meta_harness_2`-style reserved moves (§Out of scope); v2 ships ephemeral and that decision is recorded here, not deferred further.

**Explicit non-revisit:** the `FilesystemMiddleware` auto-offload of >20k-token results is **already live** in `StateBackend` (verified at `coding_tools.py:18` TA: note + `graph.py:816-870`). v2 does NOT need explicit `backend.upload_files()` for the auto-offload path — only for *deterministic* subagent `read_file`/`grep` access where v2 wants a stable chunk filename across calls. `_rag_search_impl` uses explicit `upload_files()` to give each chunk a deterministic name (`chunk_0.txt`, `chunk_1.txt`, …) so the chunk-analyst's `task(description="summarize chunk_0.txt")` references a known path.

## Cutover decision record (D3, deferred to Design per TA: todo @ PROJECT.md:273)

> **Decision: DEFER — do NOT remove or modify v1 in this iteration. Prove v2 against G1–G6 first.**

**The gate (locked, non-negotiable).** The v2 surface must be **proven against the G1–G6 closure matrix** (the Test plan below) BEFORE any cutover is taken. Both the remove-v1 and keep-v1-as-fallback choices require this proof; the gate does not choose between them, it gates both.

**Audit requirement.** Before any cutover (remove OR fallback), v2 must audit downstream consumers of v1's RAG:
- `RagShowCommand` on `MainController` (registered at `main_controller.py:73`) — the v1 entry point; v2 coexists by adding `RagV2ShowCommand` alongside (NOT replacing).
- `interfaces.py:53` `IRagView` + `:274` `IRagViewPartner` + `providers.py:103` `create_rag_view()` — the v1 outer ABC pair + factory; v2 adds `IRagV2View`/`IRagV2ViewPartner` + `create_rag_v2_view()` alongside (NOT replacing).
- `src/agentx/model/rag/` — the v1 model tree; v2 does NOT import from it; the v2 ChromaDB path is independent.
- Any other import of `agentx.model.rag.*` or `agentx.ui.screens.rag.*` in the working tree — a `grep -rn "from agentx.model.rag\|from agentx.ui.screens.rag" src/ tests/` audit before the cutover choice is taken.

**Decision.** v2 ships as a **sibling alongside v1** in this iteration. The cutover choice (remove v1 OR keep as opt-in fallback) is a **post-Testing-phase decision** made AFTER v2 passes G1–G6 in the Testing phase and the audit is run against the proven surface. This doc does NOT pre-decide remove-vs-fallback; it records the gate.

**The two acceptable post-proof choices (taken later, not now):**
- **(A) Remove v1.** Delete `src/agentx/model/rag/` + `src/agentx/ui/screens/rag/` + `IRagView`/`IRagViewPartner` + `create_rag_view()` + `RagShowCommand`. Requires the downstream-consumer audit to confirm no live importer breaks silently.
- **(B) Keep v1 as opt-in fallback.** v2 is the default (`RagV2ShowCommand`); v1 stays reachable via a `--rag-v1` flag or an env var. v1 stays frozen (no new features); v2 is the active surface.

Either choice is a separate `.meta/.../feature_027.rag_v2/` iteration post-Testing; this doc records the gate, not the choice.

## Breaking-change risk

- **v1 untouched (D3).** Zero edits to `src/agentx/model/rag/` + `src/agentx/ui/screens/rag/`. The v2 sibling coexists.
- **`interfaces.py` additive.** New ABC pairs, no existing ABC removed/renamed.
- **`providers.py` additive.** New `create_rag_v2_view()` + inner factories; existing `create_rag_view()` unchanged.
- **`main_controller.py` additive.** New `show_rag_v2()` + `RagV2ShowCommand` registration; `show_rag()` (v1) unchanged — v1 entry point stays live.
- **Deepagents stack (D4).** v2 consumes `create_deep_agent` + middleware; it does NOT modify them. Same import-guarded pattern as `coding_agent_service.py:39-50`.
- **MVC pin (`test_coding_mvc.py`).** No impact — v2 is separate files. The v2 service's guarded-import + fallback pattern mirrors the coding one; a v2 MVC pin test is part of the Test plan.
- **Test suite.** New `tests/features/feature_027.rag_v2/` test files; no existing test modified. Known baseline: the 3 `TestReactScreenPilot` + 3 `test_tdd_enforcement`/`test_tdd_check` allowlisted failures (per `omt_q` known_suite_failures) are independent of v2.

## Backwards compatibility

- v1 RAG stays fully functional; `RagShowCommand` still routes to v1.
- v2 is opt-in via `RagV2ShowCommand` (the menu gains a second RAG entry — temporary, until the post-Testing cutover decision collapses the two).
- `deepagents` not installed → v2 degrades to bare `create_agent` (no middleware, no subagents; `rag_search` still works, parallel `chunk-analyst` does not). Same guard as `coding_agent_service.py:46-50`.

## Testing strategy (TDD — major_feature, D7)

> feature_016 TDD auto-activates at Programming. RED in tests/ only → GREEN/REFACTOR in src/ only. Close via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT skip.

### Test files (5 new under `tests/features/feature_027.rag_v2/`)

1. `test_rag_v2_mvc_contract.py` — MVC++ provider/view/controller contract pins (~630 lines, 10 TestCase classes; mirrors `test_console_provider_and_views.py` shape from feature_024).
2. `test_rag_v2_commands_and_views.py` — command registration + view rendering (~250 lines; mirrors `test_console_commands_and_views.py` shape).
3. `test_rag_v2_agent_service.py` — deepagents wiring (~264 lines; mirrors `test_deepagent_context_optimization.py` shape from feature_025).
4. `test_rag_v2_retrieval_tool.py` — the `rag_search` `@tool` + `backend.upload_files()` + `chunk-analyst` dispatch.
5. `test_rag_v2_gaps_closure_matrix.py` — the G1–G6 closure matrix as pytest node IDs (this doc's Test plan).

### G1–G6 closure matrix — sharpened to pytest node IDs

| Gap | pytest node ID | Verification shape |
|---|---|---|
| **G1** (mirror for parity) | `test_rag_v2_mvc_contract.py::TestRagV2CreateRepositoryContract::test_create_command_returns_repository_not_none` | Invoke `RagV2MainController` "create" command → assert `IRagV2CreateRepositoryView`/`IViewPartner` exchange consoles out a name prompt → validate-and-create → return a `RagV2Repository` (not `None`) on success. |
| **G1** | `test_rag_v2_mvc_contract.py::TestRagV2CreateRepositoryContract::test_create_repository_view_factory_present` | `ConsoleProvider.create_rag_v2_create_repository_view(...)` exists + returns an `IRagV2CreateRepositoryView` instance. |
| **G2** (mirror for parity) | `test_rag_v2_mvc_contract.py::TestRagV2RepositorySelectionContract::test_get_selected_repository_returns_candidate_on_valid_index` | Set up N repositories → mock view's `get_selected_index()=i` → `controller.get_selected_repository()` returns `candidates[i-1]`, not `None`. |
| **G2** | `test_rag_v2_mvc_contract.py::TestRagV2RepositorySelectionContract::test_get_selected_repository_returns_none_on_out_of_bounds` | Out-of-bounds index → returns `None` (the documented graceful case). |
| **G3** (mirror for parity) | `test_rag_v2_gaps_closure_matrix.py::TestRagV2StateHygiene::test_get_rag_state_returns_populated_state_with_repository_and_artifacts` | Selected repository + artifacts present on disk → `get_rag_state()` returns a populated `RagV2State` (path fields non-None). |
| **G3** | `test_rag_v2_gaps_closure_matrix.py::TestRagV2StateHygiene::test_get_rag_state_returns_none_when_no_repository_selected` | No repository selected → `None` (the documented graceful case). |
| **G4** PDF | `test_rag_v2_gaps_closure_matrix.py::TestRagV2PdfIngestion::test_pdf_fixture_lands_in_vector_store` | Feed a PDF fixture → assert vectors land in the v2 store + the ingestion record exists. |
| **G4** MD | `test_rag_v2_gaps_closure_matrix.py::TestRagV2MdIngestion::test_md_fixture_lands_in_vector_store` | Same for an MD fixture. |
| **G4** web | `test_rag_v2_gaps_closure_matrix.py::TestRagV2WebIngestion::test_web_url_fixture_lands_in_vector_store` | Same for a web-URL fixture (the v1 asyncio path ported). |
| **G5** switch | `test_rag_v2_gaps_closure_matrix.py::TestRagV2SessionSwitch::test_switch_between_two_repositories_no_leak` | Create repo_A + repo_B → select A → assert state reflects A → switch to B → assert state reflects B → switch back to A → assert state reflects A again (no leak). |
| **G5** switch | `test_rag_v2_mvc_contract.py::TestRagV2MainController::test_switch_repository_command_present` | `RagV2MainController.switch_repository()` exists + swaps the active repository + refreshes state. |
| **G6(a)** outer | `test_rag_v2_mvc_contract.py::TestRagV2OuterParity::test_irag_v2_view_and_partner_abc_pair_present` | `IRagV2View` + `IRagV2ViewPartner` classes present in `interfaces.py`. |
| **G6(a)** outer | `test_rag_v2_mvc_contract.py::TestRagV2OuterParity::test_create_rag_v2_view_factory_present` | `ConsoleProvider.create_rag_v2_view(...)` returns an `IRagV2View` instance. |
| **G6(a)** inner (3) | `test_rag_v2_mvc_contract.py::TestRagV2InnerParity::test_three_inner_abc_pairs_present` | `IRagV2CreateRepositoryView`/`Partner` + `IRagV2RepositorySelectionView`/`Partner` + `IRagV2WebIngestionView`/`Partner` all present. |
| **G6(a)** inner (3) | `test_rag_v2_mvc_contract.py::TestRagV2InnerParity::test_three_inner_factories_present` | `ConsoleProvider.create_rag_v2_create_repository_view` + `.create_rag_v2_repository_selection_view` + `.create_rag_v2_web_ingestion_view` all present. |
| **G6(a)** set_view | `test_rag_v2_mvc_contract.py::TestRagV2MainControllerWiringUsesSetView::test_show_rag_v2_calls_set_view_not_dot_view` | `show_rag_v2()` calls `set_view(view)` NOT `.view = view` (the feature_024 bug-pin Constraint d). |
| **G6(b)** deepagents | `test_rag_v2_agent_service.py::TestRagV2AgentService::test_service_uses_create_deep_agent_when_available` | Service ctor wires `_agent` from `create_deep_agent` (not bare `create_agent`). |
| **G6(b)** deepagents | `test_rag_v2_agent_service.py::TestRagV2AgentService::test_service_registers_chunk_analyst_subagent` | `CHUNK_ANALYST` appears in the agent's `subagents=` kwarg. |
| **G6(b)** deepagents | `test_rag_v2_agent_service.py::TestRagV2AgentService::test_service_writes_state_backend_for_offloading` | `_backend` is a `StateBackend`. |
| **G6(b)** deepagents | `test_rag_v2_agent_service.py::TestRagV2AgentService::test_service_falls_back_to_create_agent_without_deepagents` | Monkeypatch `import deepagents` to raise; service still constructs a usable agent (legacy path, no subagents). |
| **G6(b)** deepagents | `test_rag_v2_agent_service.py::TestRagV2AgentService::test_service_preserves_thread_id_cancel_history_api` | `thread_id`, `cancel`, `is_running`, `get_history`, `reset_conversation` behave compatibly (same API surface as `CodingAgentService`). |
| **G6(b)** tool | `test_rag_v2_retrieval_tool.py::TestRagSearchTool::test_rag_search_uploads_chunks_to_backend` | `rag_search(...)` calls `backend.upload_files(...)` with the retrieved chunks. |
| **G6(b)** tool | `test_rag_v2_retrieval_tool.py::TestRagSearchTool::test_rag_search_returns_pointer_result_with_citation_metadata` | Returns `RagSearchResult` with `hits[i].source_path` + `page`/`line` populated. |
| **G6(b)** subagent | `test_rag_v2_retrieval_tool.py::TestChunkAnalystSubagent::test_chunk_analyst_spec_has_required_fields` | `CHUNK_ANALYST` dict has `name`/`description`/`system_prompt`. |
| **G6(b)** subagent | `test_rag_v2_retrieval_tool.py::TestChunkAnalystSubagent::test_chunk_analyst_in_rag_v2_subagents_list` | `CHUNK_ANALYST` in `RAG_V2_SUBAGENTS`. |

### RED → GREEN → REFACTOR cycle (D7 TDD)

- **RED** (tests/ only): write the 5 test files above with `pytest` node IDs from the matrix; all RED (no v2 src yet).
- **GREEN** (src only): implement `src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/` + extend `interfaces.py`/`providers.py`/`main_controller.py` per the Static Structure above. Two-hats: GREEN touches `src/` only.
- **REFACTOR** (src only): slim `DEFAULT_RAG_V2_SYSTEM_PROMPT` (the deepagent base prompt already covers tool usage); ensure `rag_v2_tools.py` `@tool` descriptions are concise (the docstring = the tool description the model sees).
- **DONE** via `omt_tdd{op:done, faeture:"feature_027.rag_v2"}` with `checklist.suite_passes:true`. NOT via `omt_skip`.

## Open questions / risks

- **deepagents `subagents=` API shape.** The `SubAgent` dict spec `{name, description, system_prompt, …}` is the documented shape (`docs.langchain.com/oss/python/deepagents/subagents`); the exact set of optional keys (`tools?`, `middleware?`, `skills?`, `response_format?`, `permissions?`) should be re-verified against the installed `deepagents>=0.7` version in the GREEN phase. If the installed API accepts a `SubAgent` dataclass instead of a dict, swap — the contract is the same.
- **`backend.upload_files()` deterministic naming.** `_rag_search_impl` names chunks `chunk_0.txt`, `chunk_1.txt`, … so the chunk-analyst's `task(description="summarize chunk_0.txt")` references a stable path. If the orchestrator re-runs `rag_search` before the previous turn's `task()` calls finish, the names collide. Mitigation: prefix with `thread_id` (`f"{thread_id}/chunk_{i}.txt"`) OR accept that within a single turn the names are stable (the turn's lifecycle bounds the scratch space).
- **v1 `show_rag` still uses buggy `.view =` (Constraint d evidence).** v1's `main_controller.py:106` uses `rag_controller.view = rag_view` — the unfixed pattern. v2's `show_rag_v2()` uses `set_view()` (the fixed pattern). The two coexist; v2 does NOT touch v1's line. A future v1 cutover (post-Testing) may take a `set_view` fix on v1 as a pre-cutover audit step, but that's out of scope for v2's Design.
- **No skills dir on day-1.** `CodingAgentService` auto-detects `src/agentx/model/coding/coding_skills/`; v2 has no skills dir yet. `RagV2AgentService` allows `skills=None` (the deepagents stack handles `skills=None`/missing → `SkillsMiddleware` no-op). v2 may grow a `rag_v2_skills/` dir in a later iteration (§Out of scope for this Design).
- **Rubric-checked grounding composition (TA: risk @ PROJECT.md:276).** If the chunk-analyst's one-file summary proves insufficient (chunks need rubric grading to be useful), v2 may compose rubric-checked grounding ON TOP of retrieve-offload-delegate as a **§Standing principle extension**, NOT a D5 replacement. Surface as a new PROJECT.md iteration if it ships, not as a silent D5 retirement. This Design ships retrieve-offload-delegate only.

## Links

- Analysis: `3.analysis/features/feature_027.rag_v2/analysis_001_v1_gaps_and_deepagents_grounding.md`
- Project home: `.projects/meta/rag_v2/PROJECT.md` (locked v1.2)
- Sibling design dir (template shape): `4.design/features/feature_025.coding_context_window_optimization/`
- Sibling console contract: `4.design/features/feature_024.no_tui_full_features/design_001_console_parity.md`
- Deepagents RAG (D5 pattern): https://docs.langchain.com/oss/python/deepagents/rag
- Deepagents subagents (chunk-analyst contract): https://docs.langchain.com/oss/python/deepagents/subagents
- Deepagents backends (StateBackend ephemeral): https://docs.langchain.com/oss/python/deepagents/backends
- Operation specs (companion): `operation_spec_001_rag_v2_service_and_tools.md`
