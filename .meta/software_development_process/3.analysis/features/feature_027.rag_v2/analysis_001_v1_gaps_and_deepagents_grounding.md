<!-- NAVIGATION: sibling analysis doc to feature_025's analysis_001_context_window_bloat.md · follows the 6-section template (Problem → Current → Observations → LangChain techniques → Constraints → Non-goals). -->
<!-- THINK GATE: TA: thoughts consulted at .projects/meta/rag_v2/PROJECT.md:272-276 (gotcha: D5 pattern locked + coding_agent_service.py:159 grounding; todo: v1-cutover deferred to design; xref: ANALYSIS-PARTIAL deepagents stack verified graph.py:268-893; gotcha: ANALYSIS-PARTIAL G1-G3 STALE vs closure matrix lines 178-187; risk: D5 rubric-composition boundary-vs-content). -->

# Analysis 001: v1 gaps and deepagents grounding for `rag_v2`

> **Phase:** Analysis — `omt_agent_guide.md §1`–§4
> **Feature:** feature_027.rag_v2
> **Design doc:** `4.design/features/feature_027.rag_v2/design_001_*.md` (pending — owned by the Design phase this Analysis advances to)
> **Project home:** `.projects/meta/rag_v2/PROJECT.md` (locked v1.2 — scope/Vision/Decisions D1–D8;ilestone: Analysis sharpening belongs here, NOT re-negotiation there)

## Problem statement

The user asked for a **greenfield rewrite of the RAG system** as `feature_027.rag_v2` — a **console-only new module** (`src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/`) that grounds RAG retrieval as a `@tool` on the deepagents stack (feature_025's `create_deep_agent` + `StateBackend`), matches the feature_024 console MVC++ contract, and closes the six documented v1 gaps (G1–G6). The v1 RAG code (`src/agentx/model/rag/` + `src/agentx/ui/screens/rag/`, shipped under `feature_002.rag_retrieval_augmented_generation`) stays **untouched** until a proven v2 surface + a design-phase cutover decision (D3 lock). This Analysis re-verifies the six gaps against the *current* working tree (the four PROJECT.md v1.1 evidence sources re-read at HEAD) and distills the deepagents + console-parity grounding the design phase will consume. It does **not** re-pick scope (locked v1.1), re-pick the RAG pattern (D5 lock), or sharpen pytest node IDs (Design-phase work).

## Current implementation (v1 RAG)

v1 ships RAG as a **parallel agent system** in two layers, verified at HEAD commit `7ce6913` (2026-08-09):

**Model layer** — `src/agentx/model/rag/`:

| File | Role |
|------|------|
| `rag.py` | the `Rag` aggregate; owns DB + docs + ingestion-URL state queries |
| `rag_db.py` | `RagDatabase` + ChromaDB `PersistentClient` store wiring |
| `rag_repository.py` | `RagRepository` value object (name + path) |
| `rag_provider.py` | `RagProvider` factory (constructs the `Rag` aggregate) |
| `rag_query.py` | query helpers; `rag_query.py:40` `pprint.pprint(doc)` is stdout pollution in the model layer |
| `web_ingestion/` | asyncio web-ingestion subpackage (Tavily fetch → chunk → embed) |
| `query/` | query-pipeline subpackage |

**UI layer** — `src/agentx/ui/screens/rag/`:

| File | Role |
|------|------|
| `rag_controller.py` | `RagController` (holds `current_rag_repository`, `get_rag_state()` at `:66-107` returns populated `RagState`) |
| `rag_chat_controller.py`, `rag_chat_view.py` | chat sub-screen (`RagChatView.show_partial_text()` is **dead** per the v1 surface read) |
| `rag_create_repository_controller.py`, `rag_create_repository_view.py` | repo creation sub-screen (`_create_repository()` fully implemented at `:96-126`) |
| `rag_repository_selection_controller.py`, `rag_repostitory_selection_view.py` (`[sic]` typo in v1 filename) | repo selection sub-screen (`get_selected_repository()` at `:57-76` — returns cached `RagRepository` with 1-based→0-based index map + bounds check, NOT `None`) |
| `rag_web_ingestion_controller.py`, `rag_web_ingestion_view.py` | web-ingestion sub-screen |
| `rag_view.py` | the outer composite view implementing `IRagView` (`interfaces.py:53`) |
| `constants.py` | display constants (drift from FEATURE.md extract presets noted) |

**Outer integration** (the parity-aware surface): `interfaces.py:53` `IRagView(ABC)` + `interfaces.py:274` `IRagViewPartner(ABC)` + `providers.py:103` `create_rag_view()` factory + `RagShowCommand` registration on `MainController`.

## Observations — v1 gap → v2 closure matrix vs current code

> **Key finding (per TA: thought @ PROJECT.md:275):** the v1-gap→v2 closure matrix at `PROJECT.md:178-187` lists G1/G2/G3 as constraints v2 owns, **but v1 already ships them** in the working tree. The three `feature_002` design docs (`design_001-003`) describe PRE-implementation state; commit `cdeb15f` shipped both designs AND the code on 2026-06-21; `FEATURE.md §Status` was never refreshed. v2's **TRUE scope per current code** = G4 + G5 + G6(b) + narrow G6(a). G1–G3 are mirrored in v2 for **parity**, not reimplemented as net-new.

| Gap | verdict | File:line evidence |
|---|---|---|
| **G1** — repo creation placeholder | **RESOLVED in v1** | `rag_create_repository_controller.py:96-126` `_create_repository()` fully implemented (~30 lines: mkdir + `RagDatabase.create_if_not_exists`). The design_001 from feature_002 describes PRE-implementation state; code shipped same commit. v2 mirrors, doesn't close. |
| **G2** — `get_selected_repository()` returns None | **RESOLVED in v1** | `rag_repository_selection_controller.py:57-76` returns cached `RagRepository` with a 1-based→0-based index map + bounds check (NOT `None`). The design_002 describes the None-returning placeholder; code shipped same commit. v2 mirrors, doesn't close. |
| **G3** — `get_rag_state()` returns None | **RESOLVED in v1** | `rag_controller.py:66-107` returns populated `RagState` (NOT commented; consumes `Rag.database_exists`/`documents_exist`/`get_ingested_url`). The design_003 describes the commented placeholder; code shipped same commit. v2 mirrors, doesn't close. |
| **G4** — PDF/MD ingestion missing | **CONFIRMED** | `src/agentx/model/rag/` has a `web_ingestion/` subpackage only; no `pdf_ingestion`/`md_ingestion` sibling. v2 owns the closure (PDF + MD + web ported). |
| **G5** — multi-repo session switch incomplete | **CONFIRMED** | `rag_controller.py:35` holds `self.current_rag_repository = repository_selection.get_selected_repository()` — a local field on the controller, not a session object; no "switch repository" command exists in `MainController`; no propagation to peer agents (coding/fast-agent) when the active repo changes. v2 owns the closure. |
| **G6(a)** — console parity (inner) | **PARTIALLY CONFIRMED** | The OUTER integration IS parity (`IRagView`/`IRagViewPartner`/`create_rag_view()`/`RagShowCommand` exist in `interfaces.py:53,274` + `providers.py:103`). The INNER views are **bare classes**: `RagChatView`, `RagCreateRepositoryView`, `RagRepositorySelectionView`, `RagWebIngestionView` each have **no** `I<X>View`/`I<X>ViewPartner` ABC pair in `interfaces.py` and **no** `create_*_view(...)` factory in `providers.py:ConsoleProvider`. Zero parity for inner views. v2 owns the closure (3 inner ABC pairs + 3 factories + `set_view()` usage in `show_rag_v2()` — see Constraint (d)). |
| **G6(b)** — deepagents grounding | **CONFIRMED** | `rg "deepagents\|create_deep_agent\|@tool\|StateBackend" src/agentx/model/rag/ src/agentx/ui/screens/rag/` returns 0 hits. The v1 RAG tree has zero deepagents references — it is a parallel agent system built on bare `create_agent` (the surface feature_025 migrated away from). v2 owns the closure. |

**Eight additional v1 surface surprises (carry to Design):**

1. `rag_query.py:40` — `pprint.pprint(doc)` stdout pollution **in the model layer** (a model-layer → console coupling G6(a) inheres in; v2 must keep `pprint` out of `model/rag_v2/`).
2. `rag_chat_view.py.show_partial_text()` is **dead** (defined, never called). v2 omits it.
3. `constants.py` vs `FEATURE.md` extract-preset drift (chunk size/overlap) — v2 keeps constants as a single source of truth.
4. v1 filename typo `rag_repostitory_selection_view.py` (`[sic]`) — v2 names cleanly.
5. v1 `web_ingestion/` is the one real asyncio surface; the rest of v1 RAG is sync (consistent with the D6 async-scoped-to-ingestion invariant v2 preserves).
6. v1 `RagChatView` streams via its own callbacks, NOT via `ConsoleProvider.create_chat_view` or the UIConsole streaming bus — v2 wires streaming through `UIConsole.stream_write()` per feature_024.
7. v1 `RagController.__init__` consumes `repository_selection` tightly (a constructor dep) — v2's `RagV2MainController` follows the D5 *tool-on-orchestrator* shape, not a peer-controller dep.
8. v1 holds `current_rag_repository` as a plain attribute on `RagController` (line 35) — no session object, no broadcast. v2's session is the `RagV2MainController`'s `current_repository` + `repositories` state (G5 closure).

## LangChain deepagents techniques available

> Per TA: thought @ PROJECT.md:274 — verified from feature_025's ship + library source (`deepagents/graph.py:268-893`, `backends/state.py`, `middleware/subagents.py`) and the LangChain-deepagents RAG docs (`/oss/python/deepagents/{rag,subagents,backends,retrieval}.mdx`).

**The pattern v2 implements (D5 lock): *retrieve, offload, and delegate*.** Of the four named deepagents-RAG patterns (skills-guided retrieval, rubric-checked grounding, todo-driven investigation, retrieve-offload-delegate), v2 implements the fourth: the retrieval `@tool` writes retrieved chunks to the agent backend filesystem via `backend.upload_files()`, subagents read/grep/summarize individual files in parallel via the built-in `task({subagentType, description, responseSchema})`, the orchestrator synthesizes a citation-bearing final answer.

**Primitives confirmed live in feature_025's actual ship:**

- `create_deep_agent(model=, tools=[search_*], subagents=[chunk-analyst])` — the orchestrator. Verified at `src/agentx/model/coding/coding_agent_service.py:159-172` (the agentx call site; passes `model`/`tools`/`system_prompt`/`backend=StateBackend()`/`checkpointer=InMemorySaver`/`memory=default["./AGENTS.md"]`/`skills=default["./src/agentx/model/coding/coding_skills/"]`/`middleware=[create_summarization_tool_middleware(llm,backend)]`). `subagents=` is **absent** from the agentx call, but `create_deep_agent` auto-adds a default `general-purpose` subagent (`graph.py:750-814`) — the `task()` tool + `SubAgentMiddleware` are already live in the coding stack.
- The `@tool`-wrapper pattern — `from langchain.tools import tool`; a dataclass return type; a Google-style docstring serves as the tool description; the function body is a thin wrapper over an `_*_impl` method. Verified at `src/agentx/model/coding/coding_tools.py:18` (TA: note) + the five `@tool` functions (`file_search`/`file_read`/`file_edit`/`file_list`/`file_create`) + the `CODING_TOOLS` registry at line 453. **v2's retrieval `@tool` follows this exact pattern.**
- `backend.upload_files(files: list[tuple[str, bytes]])` — the primitive a `@tool` calls to write retrieved chunks to the agent backend (so `read_file`/`grep` built-ins can page through them). Verified at `deepagents/backends/state.py:308` (`StateBackend.upload_files()`).
- Built-in `task({subagentType, description, responseSchema?})` tool — auto-wired by `SubAgentMiddleware` (`graph.py:816-870`). v2's `chunk-analyst` subagent is invoked through this.
- `FilesystemMiddleware` (auto-assembled by `graph.py:816-870`) offloads `>20k`-token tool-call results to the backend automatically — v2 **may not** need explicit `backend.upload_files()` for large retrieval results, depending on whether it wants *deterministic* subagent `read_file`/`grep` access (then explicit `upload_files()` is required).

**Middleware auto-assembly order** (verified `graph.py:816-870`): `Skills → Filesystem → SubAgents → Summarization → Patch → [user middleware splices here] → ToolExclusion → PromptCaching → Memory`. PROJECT.md Vision names four middleware (Filesystem/Summarization/Memory/Skills); they are **auto-assembled** based on the `memory=`/`skills=`/`subagents=`/`permissions=` kwargs of `create_deep_agent`, NOT visible in the `coding_agent_service.py` body. v2 splices any custom middleware at the `[user middleware splices here]` slot.

**Backends reference** (D4 lock — v2 consumes, doesn't modify): `StateBackend` (default, **ephemeral** — thread-scoped; chunks do NOT survive `reset_conversation()`), `FilesystemBackend` (local disk, `virtual_mode=True`), `CompositeBackend` (router: different paths → different backends), `StoreBackend` (cross-thread persistence). v2's persistence strategy is a **design-phase decision** (see Constraint (c)).

**The UI shape is feature_024's, not invented** (per TA: thought @ PROJECT.md:274 inline): `ConsoleProvider` factory at `providers.py:81` + `I<X>View`/`I<X>ViewPartner` ABC pair in `interfaces.py` + `MainController` command registration + `UIConsole.stream_write()` streaming (`ui_console.py:46`). v2's `IRagV2View`/`IRagV2ViewPartner` + `RagV2MainController` + `RagV2Provider.create_rag_v2_view()` match this contract. The console-MVC++ test mirror recipe is the 9-point pattern from feature_024's design (`test_console_provider_and_views.py` 630 lines / 10 TestCase classes; `test_console_commands_and_views.py` 250 lines).

## Constraints discovered

- **(a) G1–G3 already ship; v2 mirrors for parity, not for closure.** The closure matrix at `PROJECT.md:178-187` lists G1/G2/G3 as constraints v2 owns; the *current code* ships them. v2 implements its own `RagV2CreateRepositoryController`/`RagV2RepositorySelectionController`/`RagV2MainController.get_rag_state()` **following the feature_024 MVC++ contract** (new `IRagV2CreateRepositoryView`/`IViewPartner` ABC pair + `RagV2Provider.create_*_view()` factories + `set_view()` usage), NOT as net-new because v1 didn't have them. The design doc must record the STALE-vs-working-tree finding so a future reader doesn't waste time "closing" resolved gaps.
- **(b) `subagents=` is new surface; `general-purpose` auto-coexists.** v2 adding `subagents=[chunk-analyst]` is the agent's first explicit subagent declaration. `create_deep_agent` auto-adds the default `general-purpose` subagent (`graph.py:750-814`) UNLESS v2 disables it (`GeneralPurposeSubagentProfile(enabled=False)`). Design decision: keep `general-purpose` (the coding stack's peer) or disable it (a v2-only subagent set). Default: keep (less surface-area change; the coding stack benefits from it too).
- **(c) `StateBackend` is ephemeral — v2 needs a persistence strategy.** `StateBackend` is thread-scoped — chunks uploaded this turn do NOT survive `reset_conversation()`. v2's chunk store (the thing the `search_*` `@tool` writes via `backend.upload_files()`) is ephemeral if v2 reuses the coding stack's `StateBackend`; persistent if v2 swaps to `FilesystemBackend`/`StoreBackend`/`CompositeBackend`. Note: this `backend=` is the **agent's** backend (for subagent `read_file`/`grep` access); the vectors themselves live in ChromaDB (unchanged). **The design decision is about agent-side chunk files, not the vector store.** Default hypothesis: keep `StateBackend` (ephemeral; the retrieve-offload-delegate pattern is per-turn) — the chunks the agent offloads are scratch, not state.
- **(d) `set_view()` vs `.view = ...` — v2 MUST use `set_view()`.** Per feature_024's `TestMainControllerWiringUsesSetView` pin: streaming callbacks are silent no-op if the controller assigns `.view = ...` directly; **`set_view()` is the wiring that flips streaming on.** v2's `show_rag_v2()` command must call `MainController.set_view(provider.create_rag_v2_view(self))`, else the `UIConsole.stream_write()` callbacks the agent emits go nowhere.
- **(e) `IRagV2ViewPartner` short-form naming (no clash).** The `IAgentView` vs `IConsoleAgentViewPartner` naming clash in `feature_024` (the `agent` screen) doesn't apply to v2 — `model/rag_v2/` has no parallel ABC clashing on `IRagV2View`. v2 follows the short-form majority: `IRagV2View` + `IRagV2ViewPartner` (mirroring `IRagView`/`IRagViewPartner` at `interfaces.py:53,274`).
- **(f) Locks unchanged from PROJECT.md:** D1 (slug `feature_027.rag_v2`), D2 (console-only, no TUI variant), D3 (new module, v1 untouched; cutover decision deferred to Design with the G1–G6 proof gate explicit), D4 (consume `create_deep_agent`+middleware; don't modify), D5 (retrieve-offload-delegate; rubric composition is §Standing-principle extension, NOT D5 re-pick per TA: risk @ PROJECT.md:276), D6 (async scoped to ingestion only), D7 (TDD mandatory; close via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT skip), D8 (G1–G6 closure matrix is the verification anchor).
- **(g) The v1-cutover decision (remove v1 OR keep as fallback) is **deferred to the Design phase**, NOT Analysis.** Per TA: todo @ PROJECT.md:273: the gate for EITHER choice is fixed — v2 surface proven against G1–G6 first, then a cutover decision with a downstream-consumer audit. The design doc records the proof gate explicitly; Analysis only flags it as a constraint, doesn't pre-decide it.

## Non-goals

- **No v1 edits** (D3 lock) — `src/agentx/model/rag/` and `src/agentx/ui/screens/rag/` stay untouched; v2 is a sibling, not an edit.
- **No TUI variant** (D2 lock) — no Textual screen, no `TUIProvider` adapter for v2, no `React*` screen for v2.
- **No deepagents stack modification** (D4 lock) — v2 consumes `create_deep_agent` + middleware + `StateBackend`; it does not change them.
- **No new vector store** — reuse ChromaDB under a `VectorStore` interface; a new store is out of scope (the `backend=` decision in Constraint (c) is about agent-side chunk files, NOT the vector store).
- **No bespoke retrieval DSL** — LangChain primitives (`create_retrieval_chain`, history-aware retriever, `@tool`-wrapped similarity search) only; no query grammar.
- **No new screen framework** — v2 rides feature_024's `ConsoleProvider`/`I<X>View`/`I<X>ViewPartner`/`MainController` command registration.
- **No Phase-B/C surface** — graph traversal, cross-commit drift, capability inventory are `meta_harness_2` territory, not v2.
- **No rubric-checked-grounding replacement of D5** — composition (rubric grading wrapping retrieve-offload-delegate) is a §Standing-principle extension at Design time; re-picking the base pattern is forbidden without new evidence + a new PROJECT.md iteration (per TA: risk @ PROJECT.md:276).
- **No re-negotiation of the locked scope axes** — the v1.1 lock on Summary/Purpose/Vision/Scope/Decisions stands; Analysis sharpens within the lock, it does not re-pick the axes.

## Recommendation

Proceed to **Design** with the deepagents retrieve-offload-delegate pattern + feature_024 console MVC++ contract + the G1–G6 closure matrix sharpened to pytest node IDs. The design doc owns: (i) the `RagV2AgentService` architecture (parallel to `CodingAgentService`, OR additional `@tool`s on `CodingAgentService` itself — a design-phase decision), (ii) the `subagents=[chunk-analyst]` contract (one-file summarize, dispatched via `task()`), (iii) the persistence-strategy decision (Constraint (c)), (iv) the cutover decision record (D3, with the G1–G6 proof gate explicit per TA: todo @ PROJECT.md:273), (v) the test plan sharpening the G1–G6 matrix to pytest node IDs. TDD auto-activates at Programming (D7); close via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT skip.
