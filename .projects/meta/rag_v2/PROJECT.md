# PROJECT: rag_v2 — RAG v2 (console-only, new module, deepagents grounding)

> Status: **v1.2 (2026-08-09)** — v1.1 scope locked + Vision written; v1.2 adds the §New Session Quick Start block (this header) + `CURRENT_STATE.md` iter-0 entry so a fresh session lands on the three exact next commands without re-reading 210 lines. Definition body (Summary → Purpose → Vision → Scope → Decisions → References) unchanged from v1.1.

---

## New Session Quick Start

> Read this block first. The v1.1 *definition* below (Summary → Purpose → Vision → §Scope G1–G6 closure matrix → Decisions log) is **locked** — do **not** re-derive scope, re-pick the RAG pattern, or re-litigate D1–D8 (see Decisions log). Architecture + Tasks + feature dir + phase declaration are all **intentionally PENDING** (§Status below) — they are design-phase and feature-dir work, not project-home work. This block names the three exact next commands a fresh session needs.

**Where this project is, in one line:** a *console-only new module* (`src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/`) that grounds RAG retrieval as a `@tool` on the deepagents stack (feature_025's `create_deep_agent` + `StateBackend`), ships the feature_024 console MVC++ contract, and closes all six v1 gaps (G1–G6). v1 RAG stays untouched until a cutover decision (D3, deferred to the v2 design phase).

### What's locked (read once, then act — do NOT re-negotiate)

| § locked section | Anchor | What a fresh session needs from it |
|---|---|---|
| §Summary | one line | RAG v2 = greenfield rewrite as `feature_027.rag_v2`, console-only new module, deepagents-grounded retrieval, v1 untouched → legacy. |
| §Purpose / v1 current state | the six v1 gaps | G1 creation placeholder, G2 selection None, G3 state None, G4 no PDF/MD, G5 multi-repo incomplete, G6 predates console parity + deepagents. v2 owns the closure of all six. |
| §Vision + standing principle | "retrieval is a tool, not a parallel agent" | v2 inverts the v1 parallel-agent topology — retrieval becomes a `@tool` on the deepagents orchestrator (the *retrieve, offload, and delegate* pattern, D5). Main objectives (a) closed gaps, (b) architectural consistency, (c) proven cutover. |
| §Scope & success criteria | G1–G6 closure matrix + in-scope axis→verification map | Boundary locked; exact pytest node IDs sharpen at design time. |
| §Decisions log D1–D8 | slug `feature_027.rag_v2`, console-only, new module, deepagents-grounded, retrieve-offload-delegate RAG pattern, async=ingestion-only, TDD mandatory, G1–G6 verification anchor | All eight locked. Do NOT re-pick the RAG base pattern (D5) without new evidence + a new PROJECT.md iteration. |

### The three exact next commands (run in this order)

> These are the **only** blocked-on-feature-dir items blocking actual code work. Architecture, Tasks, and `design_001_*.md` are owned by the Analysis → Design phases the second command declares — not by this document.

1. **Scaffold the feature dir.** Confirmed free slot: feature_027 (025=coding context window, 026=omt_q per current `2.requirements/features/` listing).
   ```bash
   uv run scripts/omt/new_feature.py "rag v2" --type major_feature
   ```
   Creates `.meta/software_development_process/{2.requirements,...}/features/feature_027.rag_v2/`. Per the v1.1 lock: the feature dir owns Architecture, Tasks, the `design_001_*.md` test plan, and the cutover decision record (D3) — the PROJECT.md home intentionally does *not*.

2. **Declare the major_feature phase (Analysis).** Triggers feature_016 TDD enforcement auto-activation at Programming; Analysis itself is TDD-free.
   ```
   omt_phase{task_type:"major_feature", scope:"rag v2 — Analysis: scaffold substrate reads (v1 RAG surface, feature_025 deepagents stack, feature_024 console MVC++ contract, LangChain deepagents-RAG docs) and write analysis_001_*.md; v1 untouched.", feature:"feature_027.rag_v2"}
   ```

3. **Run the Analysis substrate reads.** Four sources, parallelizable — Vision v1.1 added each one as grounded evidence; Analysis re-verifies each against the *current* working tree before the design doc commits to a shape:
   - **v1 RAG surface (the six gaps)** — read `src/agentx/model/rag/` + `src/agentx/ui/screens/rag/` + `feature_002.rag_retrieval_augmented_generation/FEATURE.md` §Status; confirm G1–G5 still hold; gap #6 (console parity + deepagents) confirmed by absence.
   - **feature_025 deepagents stack (the grounding)** — read `src/agentx/model/coding/coding_agent_service.py` `create_deep_agent(...)` call + `coding_tools.py:18` `@tool` offload note; confirm the `tools=[...]` array is the surface v2 adds the retrieval `@tool` to.
   - **feature_024 console MVC++ contract (the UI shape)** — read `design_001_console_parity.md` + `operation_spec_001_console_commands.md` + `use_case.md`; confirm `ConsoleProvider` factory + `IRagV2View`/`IRagV2ViewPartner` ABC pair + `RagV2MainController` command registration match.
   - **LangChain deepagents-RAG docs (the pattern)** — re-read [docs.langchain.com/oss/python/deepagents/rag](https://docs.langchain.com/oss/python/deepagents/rag) (the *retrieve, offload, and delegate* pattern D5 locks) + the [subagents](https://docs.langchain.com/oss/python/deepagents/subagents) + [backends](https://docs.langchain.com/oss/python/deepagents/backends) companion docs. Confirm `backend.upload_files()` + `task({subagentType, description})` are the primitives v2's retrieval `@tool` + chunk-analyst subagent consume.
   Write `analysis_001_*.md` to `3.analysis/features/feature_027.rag_v2/` citing all four sources.

### What NOT to do (the v1.1 deferred-in-this-document list — re-read before overriding)

- ❌ **Do NOT scaffold the feature dir from this document.** Step 1 above is the *first run-in-a-new-session* action; the v1.1 doc defers it deliberately. (§Out-of-scope-reminders point 1.)
- ❌ **Do NOT edit v1 RAG (`src/agentx/model/rag/`, `src/agentx/ui/screens/rag/`) — D3 lock.** v2 is a sibling, not an edit. The cutover *decision* (remove v1 OR keep as opt-in fallback) is open at design time; the *gate* is fixed (v2 surface proven against G1–G6 → then a decision, with downstream-consumer audit).
- ❌ **Do NOT pick a different RAG base pattern — D5 lock.** v2 implements *retrieve, offload, and delegate*. If the design phase finds rubric-checked grounding needs to compose on top, surface it as a §Standing principle extension, not a D5 replacement — see TA: risk at line ~210.
- ❌ **Do NOT introduce a TUI variant / `TUIProvider` adapter / `React*` screen — D2 lock.** v2 is console-only from the start.
- ❌ **Do NOT modify the deepagents stack — D4 lock.** v2 *consumes* `create_deep_agent` + middleware + `StateBackend`; it does not modify them.
- ❌ **Do NOT introduce a new vector store or a bespoke retrieval DSL — §Out of scope.** Reuse ChromaDB under a `VectorStore` interface; LangChain primitives only.
- ❌ **Do NOT declare TDD via `omt_skip` at Programming — D7 lock.** `feature_027.rag_v2` is `major_feature`; feature_016 TDD auto-activates at Programming; close via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT via skip.

### Resume entry point

A fresh session that needs more than the Quick Start (e.g., prior session context, prior decisions still in-flight, prior TA: thought consults) reads `.projects/meta/rag_v2/CURRENT_STATE.md` next — newest entry on top, one `## <date>` block per session. The iter-0 entry there points back here.

---

> Status: **v1.1 (2026-08-09)** — scope locked, Vision written. v1 had Summary + Purpose + draft scope; v1.1 (i) promotes the draft scope to a locked scope with a v1-gap→v2 closure matrix, (ii) adds the **Vision + standing principle + main objectives** section that the v1 doc deferred — grounded in (a) the canonical LangChain-deepagents "retrieve, offload, and delegate" RAG pattern documented at docs.langchain.com/oss/python/deepagents/rag, (b) feature_025's actual deepagents ship (`create_deep_agent` + `FilesystemMiddleware` + `SummarizationMiddleware` + `MemoryMiddleware` + `SkillsMiddleware` + `StateBackend` — verified in `src/agentx/model/coding/coding_agent_service.py`), (c) feature_024's console MVC++ contract (`ConsoleProvider` + `I<X>View`/`I<X>ViewPartner` ABC pair + `MainController` command registration), and (d) feature_002's three v1 design docs (creation / selection / state) confirming v1's intended MVC++-with-ChromaDB-and-SQLite architecture that nonetheless predates console parity and deepagents grounding. Architecture, Tasks, feature-dir scaffolding, and phase declaration remain deferred (Status checklist below).

> Scope anchor (user-pinned, 2026-08-09): **console-only** (no TUI variant, no TUI↔console adapter parity) · **new module** (`src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/`, v1 untouched) · **deepagents-grounded retrieval** (consumes `create_deep_agent`).

---

## Summary (one line)

**Greenfield rewrite of the RAG system as `feature_027.rag_v2`** — a **console-only new module** that fixes every v1 gap (placeholder repo creation, broken selection return, broken state management, no file ingestion, broken multi-repo session switching), adds the originally-spec'd PDF/MD ingestion, and grounds RAG retrieval as a `@tool` on the deepagents stack (consistent with feature_025's `create_deep_agent` + `StateBackend` + parallel-subagent pattern), matching the feature_024 console MVC++ contract — the v1 code stays in place untouched and becomes legacy, with a cutover decision deferred to a proven v2 surface.

---

## Purpose

### What this project is

A **full rewrite** of AgentX's Retrieval Augmented Generation system as a **console-only new module**. The existing RAG (`src/agentx/model/rag/` + `src/agentx/ui/screens/rag/`, shipped under `feature_002.rag_retrieval_augmented_generation`) reached "core functional with incomplete features" and then stalled: 5 of its 6 closing items are placeholders or broken (see **v1 current state** below). Rather than patch v1 in place, `rag_v2` introduces a clean new module (`src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/`) that folds the v1 design intent (multi-repo, web ingestion, context-aware chat) into a system that matches the console MVC++ contract the codebase has standardized on (feature_024) and grounds RAG retrieval as a `@tool` on the deepagents stack (feature_025) — rather than a parallel agent system.

**Console-only** means: no TUI variant, no `TUIProvider` adapter for RAG v2, no `React*` screen for RAG v2. The new module is console-native from the start, matching the `ConsoleProvider` factory + `I<X>View`/`I<X>ViewPartner` ABC pair + `MainController` command registration pattern that feature_024 established. The v1 module (`src/agentx/model/rag/`, `src/agentx/ui/screens/rag/`) is **untouched** by this project — a cutover decision (remove v1, or keep as opt-in fallback) is deferred to a proven v2 surface.

The project home is this `PROJECT.md`. The companion feature dir (`.meta/software_development_process/2.requirements/features/feature_027.rag_v2/`) and the phase declaration (`omt_phase{task_type:"major_feature"}`) are **deferred** until the scope/vision here is locked — this document is the project's *purpose*, before any artifact scaffolding.

### What this project is **not**

- **Not a patch on v1.** The v1 RAG code (`src/agentx/model/rag/`, `src/agentx/ui/screens/rag/`) stays in place untouched; `rag_v2` is a **new module** (`src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/` — exact path confirmed at design time, but a sibling, not an edit). v1 is **not** edited in place and is **not** kept as a live fallback path the v2 controller reaches into — it's legacy, and stays frozen until a final cutover decision.
- **Not a TUI feature.** v2 is console-only; no Textual screen, no `TUIProvider` wiring for v2, no `React*`/TUI adapter. The v1 TUI-tested surface (if any exists) is irrelevant to v2 — v2 does not parity-match it, and v2 does not introduce a TUI variant.
- **Not a new vector store.** v1 uses ChromaDB; v2 will likely reuse it under a `VectorStore` interface, but the store choice is a design decision, not the project's purpose. A new store is out of scope; a clean store *interface* is in scope.
- **Not a query-language or a custom retrieval DSL.** v2 uses LangChain's retrieval primitives (`create_retrieval_chain`, history-aware retriever, `@tool`-wrapped similarity search) and grounds via deepagents — no bespoke query grammar ships in this project.
- **Not a new screen framework.** v2 rides the console architecture feature_024 delivered (`ConsoleProvider`, `I<X>View`/`I<X>ViewPartner` ABCs, `MainController` command registration, `UIConsole` streaming); no framework work.
- **Not a deepagents replacement or modification.** v2 *consumes* `create_deep_agent` + `StateBackend` from feature_025's stack (the documented LangChain-deepagents RAG pattern: a `@tool` that similarity-searches and writes chunks to the backend filesystem, then a `create_deep_agent(backend=..., tools=[search_*], subagents=[chunk-analyst])` orchestrator with parallel `task()` delegation); it does not modify `create_deep_agent` or the middleware stack.

### v1 current state (the gaps v2 owns)

From `feature_002.rag_retrieval_augmented_generation/FEATURE.md` §Status, six documented gaps:

1. **`RagCreateRepositoryController` is a placeholder** — repository creation UI is unimplemented.
2. **`get_selected_repository()` returns `None`** — repository selection is broken.
3. **`get_rag_state()` returns `None`** — RAG state management is commented out.
4. **PDF/MD ingestion not implemented** — v1 spec listed PDF/MD; only web ingestion shipped.
5. **Multi-repo session switching is incomplete** — the architecture declared multi-repo; the wiring never shipped.
6. **(implicit)** The v1 code predates feature_024's console parity and feature_025's deepagents context-window work — it is neither console-parity nor deepagents-grounded.

`rag_v2` owns the closure of all six — either by implementing them in the new architecture, or by declaring v1 legacy and rendering them moot (design decision).

### Recurring principles (invariants v2 preserves)

- **MVC++ pattern** — model / view / controller + provider, the convention the rest of `src/agentx/ui/screens/` follows.
- **No new screen framework** — v2 rides the console architecture feature_024 delivered.
- **deepagents as the grounding path** — consistent with feature_025's middleware stack, not a parallel abstraction.
- **Async for ingestion only** — v1 used asyncio for the web pipeline; v2 keeps async scoped to ingestion, not to retrieval/chat.
- **TDD** — `rag_v2` is `task_type:"major_feature"`, so feature_016's TDD enforcement auto-activates at Programming (red → green → refactor at the same test_node).

---

## Vision + standing principle + main objectives

**Standing principle (non-negotiable): the retrieval is a tool the agent invokes, not a parallel agent system.**

The v1 RAG was a *parallel agent system* — `RagController` built its own LangChain agent for chat, owned its own ingestion pipeline + DB + ChromaDB store, and ran side-by-side with the coding agent (feature_007) and the fast-agent (feature_011) as a peer, not as a capability of any of them. That shape is why v1 "core functional then stalled" (feature_002 §Status): every cross-cutting improvement (context-window management, summarization, memory, skill discovery) had to be re-implemented inside the RAG agent separately from the main coding agent. v2 inverts the topology — RAG retrieval is a **`@tool` exposed on the same deepagents stack** feature_025 already ships in `CodingAgentService` (`create_deep_agent` + `FilesystemMiddleware` + `SummarizationMiddleware` + `MemoryMiddleware` + `SkillsMiddleware` + `StateBackend`). The orchestrator already knows how to call tools; RAG becomes one of them. The six v1 gaps (creation / selection / state / PDF-MD / multi-repo / no-deepagents) become *natural consequences* of the new shape rather than six separate fixes — e.g. multi-repo session switching (G5) is just "which store does the search-`@tool` bind to this turn," not a parallel agent switching problem.

This is consistent with the canonical LangChain-deepagents RAG pattern documented at [docs.langchain.com/oss/python/deepagents/rag](https://docs.langchain.com/oss/python/deepagents/rag): the harness ships four named RAG patterns — **skills-guided retrieval**, **rubric-checked grounding**, **todo-driven investigation**, and **retrieve, offload, and delegate** — of which the fourth is the one v2 implements. In its words: *"The agent retrieves matching chunks and writes them to the filesystem backend rather than keeping full text in the orchestrator context. Subagents read, search, and summarize individual files in parallel."* The pattern's primitives are exactly the feature_025 surface:

- `create_deep_agent(model=..., tools=[search_*], subagents=[chunk-analyst, ...])` — the orchestrator.
- A `@tool`-wrapped similarity-search that calls `backend.upload_files()` to write retrieved chunks to the agent backend filesystem (so `read_file`/`grep` built-ins can page through them).
- `subagents=[{name, description, system_prompt}]` declaring a `chunk-analyst` (or similar) that reads one file and summarizes it — dispatched via the deepagents built-in `task({subagentType, description, responseSchema})` for parallel fan-out + context quarantine.
- A citation-bearing final answer synthesized back in the main agent's context.

feature_025's coding agent stack already wires every middleware above (verified: `src/agentx/model/coding/coding_agent_service.py:159`'s `create_deep_agent(...)` call). v2 does **not** modify that stack — it **consumes** it. The retrieval `@tool` is the only new deepagents surface v2 introduces; it is added to the `tools=[...]` array of whichever agent surface v2 wires into the v2 console (almost certainly a new `RagV2AgentService` parallel to `CodingAgentService`, OR additional tools registered onto `CodingAgentService` itself — a design-phase decision, NOT a project-definition one).

**The console shape is feature_024's, not invented.** v2's UI surfaces (`RagV2MainController` + `IRagV2View`/`IRagV2ViewPartner` ABC pair + `RagV2Provider` factory + command registration via the `MainController` pattern) match the contract feature_024 established for the rest of `src/agentx/ui/screens/`. v2 is **console-native from the start** — no TUI variant, no `TUIProvider` adapter, no `React*` screen. This is why "console parity" is a *locked-axis* in scope (it's a contract the rest of the codebase already enforces), not an open design question.

**Main objectives — the project is justified by three outcomes, not by the rewrite itself:**

- **(a) Closure of the v1 gap surface — every documented gap closes OR renders moot.** feature_002 shipped six documented gaps (creation placeholder, selection return None, state-management commented out, PDF/MD missing, multi-repo session switching incomplete, and the implicit "predates console parity + deepagents context-window work" gap). v2 owns all six. Closure is *verified* by the v1-gap→v2-closure matrix in §Scope — each row maps to a test scenario, not a prose claim. The success state is "v2 passes G1–G6"; the v1 cutover decision (remove v1 OR keep v1 as opt-in fallback) is downstream — gated on that proof.

- **(b) Architectural consistency with the rest of the agent surface — v2 is not a special case.** feature_024 standardized the console MVC++ contract; feature_025 standardized the deepagents grounding path. The v1 RAG predates both and is the *last* screen in `src/agentx/ui/screens/` that is neither console-parity nor deepagents-grounded. v2 makes the agent's retrieval capability architecturally identical to its coding capability: same MVC++, same middleware stack, same `@tool`-on-the-orchestrator shape. After v2 ships, there is no "RAG screen" in the codebase that requires a reader to know a special-case architecture; "the agent has a retrieval tool" reads like "the agent has a coding tool."

- **(c) A proven cutover decision — v1 either exits cleanly or stays gated behind a proven v2 fallback.** The v1 code stays **untouched** by v2 work (a scope-axis: no in-place edits). The cutover *decision* — remove v1, or keep v1 as an opt-in fallback — is deferred to the v2 design phase, but the **gate** for either choice is fixed here: the v2 surface must be **proven against G1–G6** (the matrix) before any cutover is taken. This gates a real risk the project absorbs: if v2 surfaces a problem that v1 happened to handle by accident (e.g. some downstream consumer of v1's RAG), the cutover decision must visible-examine that, not silently break it.

**Verification anchor:** (a) is verifiable directly on the matrix (each row a test scenario that passes or doesn't); (b) is verifiable by the feature_024 console-parity contract tests passing against v2 + the feature_025 deepagents-grounding test passing; (c) is verifiable by the cutover decision being *recorded* in `feature_027.rag_v2/design_001_*.md` with the proof gate explicit. None of the three is a vibe check. The rewrite-in-itself is the means, not the end; the end is (a) closed gaps, (b) architectural consistency, (c) a proven cutover.

**What is NOT the vision:**
- **Not "novel retrieval"** — v2 uses LangChain primitives (`create_retrieval_chain` or the deepagents retrieve-offload-delegate pattern; `@tool`-wrapped similarity search), not a bespoke retrieval DSL. A retrieval DSL is an explicitly out-of-scope non-goal.
- **Not "novel storage"** — v2 likely reuses ChromaDB under a `VectorStore` interface; a new vector store is an explicitly out-of-scope non-goal.
- **Not "novel screen framework"** — v2 rides feature_024; no framework work.
- **Not "deepagents stack modification"** — v2 consumes `create_deep_agent` + middleware; it does not modify them.

The version's through-line is consistency, not novelty — v2 wins by making retrieval look like the rest of the agent, not by inventing a new kind of retrieval.

---

## Scope & success criteria (locked)

> Locked v1.1 (2026-08-09). The user picked all four scope axes (fix v1 gaps, console parity + deepagents grounding, full rewrite, and "defer scope sharpening to the design doc" — meaning the **architecture** and **tasks** sharpen further at design time; the scope *boundary* itself is locked here). The naming of these axes is the locked scope the project definition approves. Changing the boundary (adding/removing an axis) requires a new PROJECT.md iteration; sharpening within an axis belongs to `feature_027.rag_v2/design_001_*.md`.

### In scope (locked)

1. **v1 gap closure** — repository creation, selection return, state management, multi-repo session switching, all implemented in the v2 architecture (not patched into v1).
2. **File ingestion (PDF/MD)** — the originally-spec'd ingestion that v1 never shipped, plus the existing web ingestion path ported to the v2 pipeline.
3. **Console parity** — v2 RAG screen(s) match the feature_024 console architecture (MVC++, providers, provider contract, view contract); no TUI/nonconsole split.
4. **deepagents grounding** — RAG retrieval surfaces as a tool the deepagents stack can invoke (consistent with feature_025's `create_deep_agent` + middleware); the v2 RAG is not a parallel agent system.
5. **Legacy cutover** — v1 RAG either removed (clean cutover) or kept as opt-in fallback (decision at design time); the v2 surface must be proven first.

### Out of scope (explicit non-goals)

- **No new vector store** — reuse ChromaDB or wrap it; do not introduce a new store as a project goal.
- **No bespoke retrieval DSL / query language** — LangChain primitives + deepagents grounding only.
- **No TUI / nonconsole split** — v2 is console-only (feature_024 parity).
- **No edits to v1 in place** — v1 stays untouched until a proven v2 surface and a final cutover decision.
- **No deepagents stack modifications** — v2 consumes `create_deep_agent` + middleware; it does not change them.
- **No new screen framework** — v2 rides the console (`feature_024`); no framework work.
- **No Phase-B/C surface here** — graph traversal, cross-commit drift, capability inventory, etc. (those are `meta_harness_2`-style reserved moves; v2 ships a focused first iteration only).

### Success criteria (verified on phase work, locked at the boundary — test scenarios sharpened at design time)

The boundary is locked here: every v1 gap must close **or** render moot in v2, every in-scope axis must verify through a test, and TDD must close cleanly. The exact pytest node IDs / golden scenarios belong to `feature_027.rag_v2/design_001_*.md` (the v2 design phase owns the test plan), but the closure structure is locked below — every gap maps to a verifiable scenario, not a vibe check.

#### v1 gap → v2 closure matrix (locked — each row maps to a test scenario)

| # | v1 gap (from feature_002 §Status) | v2 closure | Verification shape (test scenario, not implementation) |
|---|---|---|---|
| **G1** | `RagCreateRepositoryController` is a placeholder — repo creation UI unimplemented | v2 ships working repo creation in `rag_v2/` following the feature_024 MVC++ contract (new `IRagV2CreateRepositoryView`/`IViewPartner` + `RagV2CreateRepositoryController` wired into `RagV2MainController` command registration). v1 is **untouched**; v2 implements its own creation pipeline. | Console-parity MVC++ contract test: invoke `RagV2MainController` "create" command → assert the `IView`/`IViewPartner` exchange consoles out a name prompt → validate-and-create → return a `RagV2Repository` (not `None`) on success. |
| **G2** | `get_selected_repository()` returns `None` — selection broken | v2 ships working selection in `rag_v2/`: selection view stores index internally, controller caches the candidate list, `get_selected_repository()` returns the actual `RagV2Repository` (not `None`) on a valid index. | Selection return-path test: set up N repositories → mock view's `get_selected_index()=i` → assert `controller.get_selected_repository()` returns `candidates[i-1]`, not `None`. |
| **G3** | `get_rag_state()` returns `None` — state management commented out | v2 ships working state retrieval in `rag_v2/`: the `RagV2MainController` holds the active repository, calls the v2 `Rag` (or equivalent) to read DB+docs+ingestion-URL existence, returns a `RagV2State` (not `None`) for a selected repository with on-disk artifacts. | State hygiene test: with a selected repository + artifacts present on disk → assert `get_rag_state()` returns a populated `RagV2State` (path fields non-None); with no repository selected → assert it returns `None` (the documented graceful case). |
| **G4** | PDF/MD ingestion not implemented — v1 spec listed PDF/MD; only web shipped | v2 ships PDF + MD ingestion in the v2 pipeline (in addition to the web ingestion ported from v1's asyncio pipeline). Async stays scoped to ingestion only (a v1 invariant v2 preserves); retrieval/chat stays sync. | Ingestion test: feed a PDF fixture → assert vectors land in the v2 store + the ingestion record exists; same for an MD fixture; same for a web-URL fixture (the v1 path ported). |
| **G5** | Multi-repo session switching incomplete — architecture declared multi-repo, wiring never shipped | v2 ships multi-repo session switching: the `RagV2MainController` keeps a `current_repository` and an enumerated `repositories` state; a "switch repository" command swaps the active repo and refreshes state. | Session-switch test: create repo_A + repo_B → select A → assert state reflects A → switch to B → assert state reflects B → switch back to A → assert state reflects A again (no leak across switches). |
| **G6** | (implicit) v1 predates feature_024 console parity AND feature_025 deepagents context-window work — v1 is neither console-parity nor deepagents-grounded | v2 ships console-native from the start (feature_024 contract; no TUI/nonconsole split) AND deepagents-grounded retrieval (feature_025 stack consumed; v2 is not a parallel agent system). | (a) Console-parity test: assert v2 controller/view/provider satisfy the feature_024-style MVC++ contract pins (provider factory + IVIew/IVIewPartner ABC pair + MainController registration). (b) Deepagents-grounding test: assert v2 retrieval surfaces as a `@tool` the deepagents stack invokes — a deepagents invocation returning grounded docs (citations). |

#### In-scope axis → verification map (locked)

- **v1 gap closure** — verified by the G1–G6 matrix above (each row = a test scenario, no "TODO-revisit").
- **File ingestion (PDF/MD/web)** — covered by G4 (one scenario per source).
- **Console parity** — verified by G6(a) (feature_024-style MVC++ contract tests: provider / view / controller each, mirroring the feature_024-pattern `test_console_provider_and_views.py` test shape).
- **deepagents grounding** — verified by G6(b) (a deepagents invocation test asserting RAG `@tool` returns grounded docs).
- **Legacy cutover** — recorded as a project decision in the v2 design doc (`feature_027.rag_v2/design_001_*.md`): the v2 surface must be **proven** before cutover; the cutover choice (remove v1 OR keep v1 as opt-in fallback) is a design-phase decision, but the **gate** for either choice is "v2 surface proven against G1–G6 above."
- **Full suite green; TDD closed cleanly** — `feature_027.rag_v2` is `task_type:"major_feature"`, so feature_016's TDD enforcement auto-activates at Programming (red → green → refactor at the same `test_node`); TDD close is via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT via `omt_skip` (per feature_016).

### Boundaries (one line each)

- **What changes (will change):** new feature dir `feature_027.rag_v2/` + new `src/agentx/model/rag_v2/` + new `src/agentx/ui/screens/rag_v2/` (exact paths refined at design time, but siblings of v1 — NOT edits to v1); eventual v1 removal/fallback (design-phase decision, gated on a proven v2 surface).
- **What does not change:** `feature_025` deepagents stack, `feature_024` console architecture, the harness, the enforcer, `META_HARNESS.omt`, `AGENTS.md`, and the v1 RAG code (`src/agentx/model/rag/` + `src/agentx/ui/screens/rag/`) — all untouched by v2.
- **What is deferred (future, not this project):** retrieval DSL, new vector store, TUI variant, graph-grounded retrieval, capability inventory — all explicitly out of scope (above).

---

## Status

- [x] Summary (one line)
- [x] Purpose (what it is / what it isn't / v1 gaps / principles)
- [x] Scope & success criteria (locked v1.1 — v1-gap→v2 closure matrix, in-scope axis→verification map, locked boundaries)
- [x] Vision / standing principle / main objectives (locked v1.1 — "retrieval is a tool, not a parallel agent," grounded in the deepagents retrieve-offload-delegate pattern; main objectives (a)-(c))
- [x] **New Session Quick Start block (v1.2 — prepends the locked v1.1 definition with the three exact next commands: scaffold feature_027, declare major_feature Analysis, run substrate reads)**
- [ ] Architecture — pending (deferred to the feature_027 design phase; `feature_027.rag_v2/design_001_*.md` will own it)
- [ ] Tasks — pending (no tasks until the feature dir is scaffolded and the first phase is declared)
- [ ] Feature dir scaffolded — pending (Quick Start step 1; `uv run scripts/omt/new_feature.py "rag v2" --type major_feature`, deferred until this project definition is approved)
- [ ] Phase declared — pending (Quick Start step 2; `omt_phase{task_type:"major_feature", ...}`, deferred until feature dir exists and scope is locked)

---

## Out-of-scope reminders (deferred, not done by this document)

- Feature dir scaffolding — `.meta/software_development_process/2.requirements/features/feature_027.rag_v2/` is **not** created by this document; creation awaits project-definition approval.
- Phase declaration — no `omt_phase` is invoked by this document; the major_feature phase awaits the feature dir.
- `src/` edits — none; this document is project-home markdown only.
- Any design/analysis/test artifacts — owned by the feature_027 phases (Analysis → Design → Programming → Testing), not by this project home.

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — Project slug is `feature_027.rag_v2`** (sibling to `feature_002.rag_retrieval_augmented_generation`, NOT a continuation — v2 is a new module under `src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/`, v1 stays in place untouched). Verified feature dir number: 025=coding context window, 026=omt_q, so 027 is the next free slot.
- **D2 — Console-only (locked scope axis)** — no TUI variant, no `TUIProvider` adapter for v2, no `React*` screen for v2. v2 is console-native from the start, matching the feature_024 contract.
- **D3 — New module, NOT an edit to v1 (locked scope axis)** — `src/agentx/model/rag/` and `src/agentx/ui/screens/rag/` (v1) are untouched by v2 work. v2 is a sibling, not an edit. The cutover *decision* (remove v1 OR keep as opt-in fallback) is deferred to the v2 design phase, but the *gate* for either choice is fixed: v2 surface proven against the G1–G6 matrix.
- **D4 — deepagents grounding via `create_deep_agent` + middleware (locked scope axis)** — v2 consumes the feature_025 stack (`create_deep_agent` + `FilesystemMiddleware` + `SummarizationMiddleware` + `MemoryMiddleware` + `SkillsMiddleware` + `StateBackend`); it does NOT modify them. The retrieval surface is a `@tool` added to the orchestrator's `tools=[...]`, not a parallel agent system. Verified that the deepagents stack is actually shipped (feature_025 DONE 2026-08-08 per WORK.md).
- **D5 — RAG pattern is "retrieve, offload, and delegate"** — of the four LangChain-deepagents RAG patterns (skills-guided retrieval, rubric-checked grounding, todo-driven investigation, retrieve-offload-delegate), v2 implements the fourth: the retrieval `@tool` writes chunks to the agent backend filesystem via `backend.upload_files()`, subagents read/grep/summarize individual files in parallel via the deepagents built-in `task({subagentType, description})`, the orchestrator synthesizes a citation-bearing answer. Source: docs.langchain.com/oss/python/deepagents/rag (the canonical tutorial).
- **D6 — Async scoped to ingestion only (invariant preserved from v1)** — v1 used asyncio for the web pipeline; v2 keeps async scoped to ingestion (PDF/MD/web loaders), NOT to retrieval/chat (which is sync via the deepagents orchestrator).
- **D7 — TDD is mandatory, closes via `omt_tdd{op:done}` not via skip** — `rag_v2` is `task_type:"major_feature"`, so feature_016's TDD enforcement auto-activates at Programming (red → green → refactor at the same test_node). The full suite must close green; TDD closes via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT via `omt_skip` (per feature_016).
- **D8 — Verification anchor is the v1-gap→v2 closure matrix (G1–G6)** — none of the three main objectives ((a) closed gaps, (b) architectural consistency, (c) proven cutover) is a vibe check. (a) is the matrix; (b) is the feature_024 console-parity contract tests + the deepagents-grounding test (G6(a) + G6(b)); (c) is the cutover decision recorded in the v2 design doc with the G1–G6 proof gate explicit.

---

## Iteration log

- **iter 1 (2026-08-08)** — project home `.projects/meta/rag_v2/` created. PROJECT.md v1 (draft) shipped: Summary, Purpose (what it is / what it isn't / v1 gaps / principles), draft scope, Status checklist with Vision/Architecture/Tasks/feature-dir/phase all marked pending. Scope axes (console-only, new module, deepagents-grounded, full rewrite) recorded from the user-pinned scope anchor.
- **iter v1.1 (2026-08-09)** — **scope locked + Vision written** (this round). Six grounded moves:
  1. Header status line rewritten from "draft v2 — project definition only" to "v1.1" with a one-paragraph changelog naming the four evidence sources for the Vision (LangChain deepagents-RAG docs, feature_025 actual ship in `coding_agent_service.py`, feature_024 console MVC++ contract, feature_002's three v1 design docs).
  2. Scope section promoted from draft to **locked**: in-scope, out-of-scope, and boundaries sections all renamed from "draft" to their final form; the section-level framing note records that the *boundary* is locked here but the *architecture/tasks within the boundary* sharpen at design time.
  3. Success criteria sharpened from a prose bullet list to a **v1-gap → v2 closure matrix (G1–G6)** — every row maps a documented v1 gap to its v2 closure AND a verification scenario (test shape, not implementation). Added an **in-scope axis → verification map** subsection that ties each locked axis to its verification path. Replaced "to be sharpened at design time" with "test scenarios sharpened at design time" — the boundary is locked here, the exact pytest node IDs belong to `feature_027.rag_v2/design_001_*.md`.
  4. **Vision + standing principle + main objectives** section added between Purpose and Scope ("retrieval is a tool the agent invokes, not a parallel agent system" — v2's defining inversion from the v1 parallel-agent topology). Cites the LangChain-deepagents retrieve-offload-delegate pattern verbatim, names the three main objectives ((a) closed gaps, (b) architectural consistency, (c) proven cutover) and their verification anchors, and declares "not the vision" (no novel retrieval, no novel storage, no novel screen framework, no deepagents modification).
  5. Status checklist updated: Scope → `[x] locked v1.1`, Vision → `[x] locked v1.1`. Architecture and Tasks remain pending (deferred to feature dir phases).
  6. Decisions log + this iteration log + References sections added (mirroring the meta_harness_2 PROJECT.md convention).
- Gestalt: the v1.1 round was grounded by reading four sources in parallel before writing — the LangChain-deepagents RAG docs (via MCP), feature_025's actual ship (via grep of `src/agentx/model/coding/`), feature_024's design dir, and feature_002's three v1 design docs (creation / selection / state). The Vision's claim that v2 is "backed by existing deepagents code, not aspirational" is the grounded payoff.
- **iter v1.2 (2026-08-09)** — **Quick Start block + CURRENT_STATE.md iter-0** (this round). Three moves, all in the project home (no src/ edit, no feature dir scaffold — deferred items stay deferred per the v1.1 lock):
  1. **§New Session Quick Start** block prepended to the document (between the H1 + v1.2 status line and the v1.1 Status preamble). The block has five named sub-sections — *What's locked* (a 5-row table mapping each locked v1.1 section to what a fresh session needs from it: Summary / Purpose-v1-gaps / Vision-standing-principle / Scope-G1-G6-matrix / Decisions-D1-D8), *The three exact next commands* (verbatim runnable: (1) `uv run scripts/omt/new_feature.py "rag v2" --type major_feature`, (2) `omt_phase{task_type:"major_feature", ..., feature:"feature_027.rag_v2"}` declaring Analysis, (3) run the four Analysis substrate reads + write `analysis_001_*.md`), *What NOT to do* (seven ❌ items: don't scaffold from this doc / don't edit v1 / don't pick a different RAG pattern / don't add TUI / don't modify the deepagents stack / don't add a new vector store / don't close TDD via skip), each citing the locked decision it would re-litigate, and *Resume entry point* (pointing to CURRENT_STATE.md). The block is **navigational**, not re-definitional — no scope axis is changed; the Quick Start block writes the *path to start* over the *definition of the project* (which is still the locked v1.1 body below it).
  2. **Status checklist bumped**: header status line promoted v1.1→v1.2 with a one-sentence changelog naming the Quick Start block + CURRENT_STATE.md; the checklist itself gained a new `[x] New Session Quick Start block (v1.2 — ...)` row between the four v1.1-locked items and the four design-phase-pending items. Architecture, Tasks, feature dir scaffold, phase declared stay `[ ]` (their deferral is part of the v1.1 lock — Quick Start *names* the three commands that will flip them; it does not run them).
  3. **`CURRENT_STATE.md` iter-0 created** (the companion session-log + resume-point file). Its iter-0 entry is the v1.2 Quick Start block's resume pointer — a fresh session reading CURRENT_STATE.md first lands on the iter-0 entry which says "read PROJECT.md §New Session Quick Start, then run the three commands" — closing the meta_harness_2-defined two-file convention (PROJECT = canonical design_doc, CURRENT_STATE = session log + resume point) so the project is *resumeable*, not just *defined*.
- Gestalt: the v1.2 round was driven by the user's "refine to be start in a new session" request — interpreted as *navigational* (Quick Start + CURRENT_STATE), not *definitional* (Architecture/Tasks still deferred to the feature dir per the v1.1 lock). Verified the next free feature slot is 027 (025=coding context window, 026=omt_q per current `2.requirements/features/` listing — confirms the D1 slug `feature_027.rag_v2`). Verified feature_027 dir does NOT yet exist (only 025 + 026 dirs under `2.requirements/features/`). Did NOT re-read the four v1.1 evidence sources (LangChain docs, feature_025 ship, feature_024 contract, feature_002 designs) — v1.1 already grounded them and v1.2 is navigational. The three next-commands the Quick Start names are the v1.1-pending items the new session opens with; Quick Start just *makes them the explicit landing surface*, so a fresh session doesn't re-derive "what's blocked first" by re-reading 210 lines.

---

## References

- **LangChain deepagents RAG docs** (the canonical pattern v2 implements) — [docs.langchain.com/oss/python/deepagents/rag](https://docs.langchain.com/oss/python/deepagents/rag). Four named patterns surface: *skills-guided retrieval*, *rubric-checked grounding*, *todo-driven investigation*, *retrieve, offload, and delegate* — v2 implements the fourth.
- **LangChain deepagents subagents doc** — [docs.langchain.com/oss/python/deepagents/subagents](https://docs.langchain.com/oss/python/deepagents/subagents). Documents the `subagents=[{name, description, system_prompt}]` parameter and the built-in `task({subagentType, description, responseSchema})` tool for parallel fan-out with context quarantine.
- **LangChain deepagents backends doc** — [docs.langchain.com/oss/python/deepagents/backends](https://docs.langchain.com/oss/python/deepagents/backends). Documents `StateBackend` (thread-scoped, default for deepagents), `FilesystemBackend` (local disk with `virtual_mode=True`), `CompositeBackend` (route different paths to different backends), `StoreBackend` (cross-thread persistence). v2's chunk-offload `@tool` calls `backend.upload_files()` — the same backend the main agent reads/writes.
- **feature_025 design doc** — `.meta/software_development_process/4.design/features/feature_025.coding_context_window_optimization/design_001_deepagent_context_optimization.md` + `operation_spec_001_deepagent_service_methods.md`. The deepagents-grounding path v2 consumes; documents the `create_deep_agent` + middleware stack choice, the `@tool` wrapping pattern (the offload-to-backend behavior), and the `StateBackend` choice.
- **feature_025 actual ship** — `src/agentx/model/coding/coding_agent_service.py:159`'s `create_deep_agent(...)` call + `src/agentx/model/coding/coding_tools.py:18`'s TA: note that `@tool` wrappers offload results >20k tokens to a `StateBackend`. Verifies the v2 Vision's claim that the deepagents stack is **backed by existing code, not aspirational**.
- **feature_024 design doc** — `.meta/software_development_process/4.design/features/feature_024.no_tui_full_features/design_001_console_parity.md` + `operation_spec_001_console_commands.md` + `use_case.md`. The console MVC++ contract v2 matches (`ConsoleProvider` factory + `I<X>View`/`I<X>ViewPartner` ABC pair + `MainController` command registration + `UIConsole` streaming).
- **feature_002 design docs** — `.meta/software_development_process/4.design/features/feature_002/design_001_repository_creation.md` (creation placeholder × v1), `design_002_repository_selection.md` (`get_selected_repository()` returns `None`), `design_003_state_management.md` (`get_rag_state()` returns `None` + commented implementation). Confirms v1's intended MVC++-with-ChromaDB-and-SQLite architecture that nonetheless predates console parity and deepagents grounding — the *six gaps* v2 owns (G1–G6).
- **Harness project-home convention** — `.meta/META_HARNESS.omt:184-185` + `:208`. Documents that `.projects/meta/<feature>/{PROJECT.md, CURRENT_STATE.md}` is non-gated (NOT in `harness_paths`); PROJECT.md is the canonical design doc, CURRENT_STATE.md is the session log + resume point. Companion to the phase-gated design doc (@phase `design_req` auto-detected under `4.design/features/feature_<n>/` OR accepts `design_doc=` pointing here).
- **Sibling project for convention** — `.projects/meta/meta_harness_2/PROJECT.md` + `CURRENT_STATE.md` (the project that defined the PROJECT.md + Decisions log + Iteration log + References convention rag_v2 adopts here).
<!-- TA: gotcha: v1.1 evidence: v2 implements the "retrieve, offload, and delegate" deepagents-RAG pattern — the retrieval @tool writes chunks to the agent backend filesystem via backend.upload_files(), subagents (chunk-analyst) read/grep individual files in parallel via the deepagents built-in task({subagentType, description}) tool, the orchestrator synthesizes a citation-bearing answer. Verified against docs.langchain.com/oss/python/deepagents/rag (the canonical tutorial) AND feature_025's actual ship (src/agentx/model/coding/coding_agent_service.py:159's create_deep_agent(...) call + coding_tools.py:18 TA: note that @tool wrappers offload results >20k tokens to a StateBackend). The v2 Vision's claim that deepagents grounding is "backed by existing code, not aspirational" is grounded in coding_agent_service.py — NOT a v1-of-the-PROJECT.md claim to verify later. -->
<!-- TA: todo: v1.1 deferred decision (PROJECT.md does NOT take it): v1 cutover — remove v1 (src/agentx/model/rag/ + src/agentx/ui/screens/rag/) OR keep as opt-in fallback — is a feature_027.rag_v2 design-phase decision. The gate for EITHER choice is fixed here: the v2 surface must be proven against the G1–G6 closure matrix first. Do not re-litigate "the gate" (it's locked); only the remove-vs-fallback choice is open at design time, and it requires evidence the v2 surface is green against G1–G6 AND an audit of any downstream consumer of v1's RAG (could break silently if cutover is taken without audit). Record in feature_027.rag_v2/design_001_*.md with the proof gate explicit. -->
<!-- TA: risk: v1.1 risk: the LangChain deepagents doc surfaces FOUR named RAG patterns — skills-guided retrieval, rubric-checked grounding, todo-driven investigation, and retrieve-offload-delegate. PROJECT.md D5 LOCKS retrieve-offload-delegate as THE pattern v2 implements. Risk: a v2 design phase working on, e.g., the chunk-analyst subagent's "summarize one file" contract might discover the chunks need rubric grading (the second pattern) to be useful — the rubric-checked grounding pattern has a grader sub-agent (RubricMiddleware) iterate-answer-until-grounded, while the retrieve-offload-delegate pattern does not. The two patterns compose (rubric grading CAN wrap retrieve-offload-delegate per the LangChain doc), but D5's lock says "v2 implements the fourth" — if the design phase wants to compose it with rubric grading, the boundary-vs-content distinction matters: composition is design-phase sharpening (allowed), re-picking the base pattern is re-litigating the boundary (forbidden without new evidence + a new PROJECT.md iteration). Do not silently retire D5 in the design phase; if rubric-checked grounding needs to ship, surface it as a §Standing principle extension, not a D5 replacement. -->
