# CURRENT_STATE: rag_v2

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

> **Resume entry point:** read `PROJECT.md` §New Session Quick Start (the v1.2 block at the top of PROJECT.md), then run the three commands in it.
> The locked v1.1 project definition (Summary → Purpose → Vision → §Scope G1–G6 closure matrix → Decisions D1–D8 → References) sits below the Quick Start block in PROJECT.md — read once on first contact, then act.

---

## 2026-08-15 (iter 2 — Design phase complete; advanced to Programming)

### Done (this iter)

- **Design phase completed.** `design_001_retrieve_offload_delegate.md` + companion `operation_spec_001_rag_v2_service_and_tools.md` written to `4.design/features/feature_027.rag_v2/` (dir created this session — was MISSING at session start per pause_f.md).
  - **Think gate satisfied** before writing the design doc: 5 TA: thoughts at `PROJECT.md:272-276` consulted (:272 gotcha D5 pattern locked + coding_agent_service.py:159 grounding; :273 todo v1-cutover deferred to Design → THIS doc records the proof gate; :274 xref ANALYSIS-PARTIAL deepagents stack verified; :275 gotcha G1-G3 STALE → v2 mirrors for parity NOT net-new; :276 risk D5 rubric-composition boundary-vs-content).
  - **Substrate re-verification (the design doc consumed)**: `coding_agent_service.py:159-172` `create_deep_agent(...)` call site (parallel-service choice grounded); `coding_tools.py:18` `@tool`-wrapper pattern (the shape `rag_v2_tools.py` mirrors); `providers.py:103` `create_rag_view()` factory (the shape `create_rag_v2_view()` mirrors); `interfaces.py:53,274` `IRagView`/`IRagViewPartner` (the ABC pair v2 mirrors short-form); `main_controller.py:106` v1's buggy `.view = rag_view` vs `:244,266` `set_view()` (the Constraint d gate); `rag.py`/`rag_db.py`/`rag_controller.py` (the v2 model aggregates mirror); feature_024 `test_console_provider_and_views.py` (630 lines / 10 TestCase) + `test_console_commands_and_views.py` (250 lines) (the contract-test shapes the v2 test plan mirrors); feature_025 `design_001_deepagent_context_optimization.md` + `operation_spec_001_deepagent_service_methods.md` (the doc template shape this pair mirrors).
  - **Five design-doc ownership areas all closed:**
    1. **`RagV2AgentService` architecture** — decision taken: PARALLEL service (not tools-on-`CodingAgentService`). Four reasons documented (separation of concern + v1-is-already-a-separate-screen + subagent isolation + both-consume-the-stack). Same guarded-import + fallback pattern as `coding_agent_service.py:39-50`. NEW kwarg vs coding = `subagents=[chunk_analyst]` explicit.
    2. **`subagents=[chunk-analyst]` contract** — the `SubAgent` dict spec `{name, description, system_prompt, tools?, middleware?, skills?, response_format?, permissions?}` (per `docs.langchain.com/oss/python/deepagents/subagents`). Decision: keep `general-purpose` default auto-added by `create_deep_agent` (Constraint b — less surface-area change). `CHUNK_ANALYST` + `RAG_V2_SUBAGENTS` documented in `rag_v2_subagents.py`.
    3. **Persistence-strategy decision** (Constraint c) — KEEP `StateBackend` (ephemeral, per-turn); chunks are scratch, NOT state. The `backend=` is about agent-side chunk files for subagent `read_file`/`grep` access; the vector store itself stays ChromaDB (different concerns). `_rag_search_impl` uses explicit `backend.upload_files()` for deterministic chunk filenames (`chunk_0.txt`, …) so the chunk-analyst's `task(description="summarize chunk_0.txt")` references a stable path. Swap-to-FilesystemBackend is a future `meta_harness_2`-style reserved move, NOT v2 scope.
    4. **Cutover decision record** (D3) — DECISION: DEFER. v1 stays untouched in this iteration. Gate (locked): v2 surface MUST be proven against G1-G6 BEFORE any cutover. Audit requirement: grep downstream-consumers of v1's RAG (`from agentx.model.rag` / `from agentx.ui.screens.rag`, `RagShowCommand`, `IRagView`/`IRagViewPartner`, `create_rag_view()`) before remove-vs-fallback choice. Two acceptable post-proof choices documented (A remove / B keep as opt-in fallback); taken in a separate post-Testing iteration, NOT here.
    5. **Test plan** — G1-G6 closure matrix sharpened to 24 pytest node IDs across 5 test files: `test_rag_v2_mvc_contract.py` (~630 lines, mirrors feature_024 `test_console_provider_and_views.py`); `test_rag_v2_commands_and_views.py` (~250 lines, mirrors `test_console_commands_and_views.py`); `test_rag_v2_agent_service.py` (~264 lines, mirrors feature_025 `test_deepagent_context_optimization.py`); `test_rag_v2_retrieval_tool.py` (rag_search + backend.upload_files + chunk-analyst); `test_rag_v2_gaps_closure_matrix.py` (the G1-G6 rows).
  - **Architecture decision record**: new `RagV2AgentService` PARALLEL to `CodingAgentService` — reached via `RagV2ShowCommand` on `MainController` (additive; v1 `RagShowCommand` stays live; `show_rag_v2()` uses `set_view()` NOT `.view =` per Constraint d). Model layer `src/agentx/model/rag_v2/` (11 files: `rag_v2.py`/`rag_v2_db.py`/`rag_v2_repository.py`/`rag_v2_agent_service.py`/`rag_v2_tools.py`/`rag_v2_subagents.py`/`rag_v2_provider.py` + `pdf_ingestion/`/`md_ingestion/`/`web_ingestion/`/`query/`); UI layer `src/agentx/ui/screens/rag_v2/` (15 files: controller + view for outer + 4 ingestion sub-screens + create-repo + select-repo + constants); Integration: `interfaces.py` + `providers.py` + `main_controller.py` all additive.
- **`omt_phase` re-declared** (Design — the 2026-08-09 activation had expired at the 8h marker) → `omt_complete{advance_to:"Programming"}` passed cleanly. Feature health now 80% (R:1 A:1 D:1 I:1 T:0). TDD auto-activates at Programming (D7); close via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT skip.

### Test results

- _(none — Design phase; docs-only artifacts. No pytest run.)_

### Locked decisions (do not re-litigate without new evidence)

- **Parallel-service (not tools-on-coding)** — the architecture decision recorded in this design doc. `RagV2AgentService` is a sibling of `CodingAgentService`; NOT additional `@tool`s on the coding agent. Re-pick requires new evidence + a new DESIGN doc iteration, not a feature-phase re-litigation.
- **Keep `StateBackend` (ephemeral)** — the persistence-strategy decision (Constraint c). Re-pick to `FilesystemBackend`/`StoreBackend` is a future `meta_harness_2`-style reserved move, NOT v2 scope.
- **v1 cutover DEFERRED** — the gate (G1-G6 proof + downstream-consumer audit) is locked; the remove-vs-fallback CHOICE is NOT pre-decided. Both acceptable post-proof choices are documented but taken in a separate post-Testing iteration.
- **Keep `general-purpose` subagent** (Constraint b) — `subagents=[chunk_analyst]` coexists with the auto-added default; v2 does NOT disable it (`GeneralPurposeSubagentProfile(enabled=False)` is out of scope).
- **24 pytest node IDs in the test plan** — the G1-G6 closure matrix is sharpened; Programming may NOT drop a node. Adding a node is allowed (e.g., an emergent need surfaced during GREEN); removing one requires a design-doc amendment.

### Next

- **Programming phase — feature_016 TDD cycle**:
  1. `omt_tdd{op:"testlist", behaviors:"[...]", feature:"feature_027.rag_v2"}` — declare the behaviors (the 24 test nodes above; optional grouping). **Behaviors MUST be a JSON array** (gotcha: prose fails `json.loads`).
  2. **RED** (tests/ only) — write the 5 test files under `tests/features/feature_027.rag_v2/` with the pytest node IDs from the matrix; all RED (no v2 src yet). Two-hats: RED touches tests/ only.
  3. **GREEN** (src only) — implement `src/agentx/model/rag_v2/` + `src/agentx/ui/screens/rag_v2/` + extend `interfaces.py`/`providers.py`/`main_controller.py` per the design doc Static Structure. Two-hats: GREEN touches `src/` only.
  4. **REFACTOR** (src only) — slim `DEFAULT_RAG_V2_SYSTEM_PROMPT`; ensure `rag_v2_tools.py` `@tool` descriptions are concise.
  5. `omt_tdd{op:"done", feature:"feature_027.rag_v2"}` with `checklist.suite_passes:true`. NOT via `omt_skip` (D7).
- **TDD node-granularity gotcha** (per WORK.md Agent Scratchpad top-3): declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → `omt_tdd{op:done}` blocked (recovery: `omt_tdd{op:green}` at the exact red node).
- **Think gate for src/ edits**: before any `src/` edit at Programming, consult `omt_think{op:list}` on the file under test. The PROJECT.md:274-275 TA: thoughts (deepagents stack verified + G1-G3 stale) are still anchor references; new thoughts can be deposited during Programming via `omt_think{op:add}` to carry forward-going gotchas (e.g., the `set_view()` consequence on `show_rag_v2()`, the `backend.upload_files()` deterministic-naming concern, the `subagents=` SubAgent dict-vs-dataclass re-verification against deepagents>=0.7 in GREEN).
- **`set_view()` `show_rag()` v1 bug (NOT fixed in v1)**: `main_controller.py:106` still uses `rag_controller.view = rag_view`. v2's `show_rag_v2()` uses `set_view()` (the fixed pattern at `:244,266`). The two coexist; v2 does NOT touch v1's line. A future v1 cutover (post-Testing) may take a `set_view` fix on v1 as a pre-cutover audit step — out of scope for v2's Programming phase.
- **Then Testing phase** — the `test_report.md` artifact (Feature Health 100% R:1 A:1 D:1 I:1 T:1).
- **Then post-Testing cutover decision** — the remove-vs-fallback choice taken after v2 passes G1-G6 in Testing + the downstream-consumer audit is run against the proven surface.

### Pause notes

- Design-doc name is `design_001_retrieve_offload_delegate.md` (matches the D5 pattern lock from the suggested names in pause_f.md; no ad-hoc `*_PROOF.md`). Companion is `operation_spec_001_rag_v2_service_and_tools.md` (mirrors the feature_025 design dir convention which shipped BOTH design_001 + operation_spec_001).
- The 5 TA: thoughts at `PROJECT.md:272-276` are still anchor references — the design doc supersedes the analysis-level verifications as the freshest anchor, but the analysis verifications remain accurate pointers to file:line. Leave them tagged `ANALYSIS-PARTIAL` until the v2 source ships at Programming (theProgramming-phase thoughts will supersede; the analysis ones stay as historical anchor).

---



### Done (this iter)

- **Analysis phase completed.**
  - **4 substrate reads re-verified against the working tree** at HEAD commit `7ce6913` (the pause note flagged this as a 5-minute grep, not a full re-read). All anchors confirmed: (a) v1 RAG `rag_create_repository_controller.py:96-126` `_create_repository` + `rag_repository_selection_controller.py:57-76` `get_selected_repository` + `rag_controller.py:66-107` `get_rag_state` → G1/G2/G3 RESOLVED in tree (not placeholders); (b) `coding_agent_service.py:11` hits for `create_deep_agent|@tool|StateBackend` → deepagents stack live; (c) `interfaces.py:53,274` `IRagView`/`IRagViewPartner` + `providers.py:103` `create_rag_view()` → outer parity confirmed, BUT zero `IRagCreateRepositoryView`/`IRagRepositorySelectionView`/`IRagWebIngestionView`/`IRagChatView` classes exist → inner-view parity gap (G6(a)) PARTIALLY-CONFIRMED confirmed; (d) `model/rag/`+`ui/screens/rag/` zero deepagents refs → G6(b) CONFIRMED.
  - **`analysis_001_v1_gaps_and_deepagents_grounding.md` written** to `3.analysis/features/feature_027.rag_v2/` — 6-section template (Problem → Current → Observations → LangChain techniques → Constraints → Non-goals + Recommendation). Cites file:line evidence for every verdict. Key finding recorded: the G1–G3 STALE-vs-working-tree finding (TA: thought @ PROJECT.md:275) — v2 mirrors G1–G3 for parity per feature_024 MVC++, NOT reimplements them as net-new. Eight additional v1 surface surprises captured (pprint stdout pollution, dead `show_partial_text()`, constants drift, filename typo `[sic]`, async-in-ingestion-only topology, non-UIConsole streaming, RagController constructor dep, current_rag_repository local field).
  - **Think gate satisfied**: TA: thoughts at `.projects/meta/rag_v2/PROJECT.md:272-276` consulted before writing the analysis doc (5 thoughts: gotcha D5 pattern locked + coding_agent_service.py:159 grounding; todo v1-cutover deferred to Design; xref ANALYSIS-PARTIAL deepagents stack verified; gotcha G1-G3 STALE; risk D5 rubric composition boundary-vs-content).
- **`omt_phase` re-declared** (Analysis) — phase had expired (8h) between pause and resume; re-declared with "Analysis complete: ... advancing to Design" scope, then `omt_complete{advance_to:"Design"}` advanced cleanly. Feature health 40% (R:1 A:1 D:0 I:0 T:0); 1 artifact still required (Design: `design_*.md`).

### Test results

- _(none — Analysis phase; docs-only artifact. No pytest run.)_

### Locked decisions (do not re-litigate without new evidence)

- **The G1–G3 RESOLVED-in-v1 finding is now recorded in `analysis_001_*.md`** — the closure matrix at PROJECT.md:178-187 still lists G1/G2/G3 as constraints v2 "owns", but v2's TRUE scope per current code = G4 + G5 + G6(b) + narrow G6(a). v2 ships `RagV2CreateRepositoryController`/`RagV2RepositorySelectionController`/`RagV2MainController.get_rag_state()` **for parity with feature_024's MVC++ contract**, NOT because v1 didn't have them. Design-phase Architecture/Tasks must reflect this (don't propose reimplementing G1–G3 as net-new capability work; each is "mirror v1's impl, with the new ABC pair + `set_view()`").
- **The Design-phase decision set is named in the analysis Constraints (a-g):** (a) G1–G3 mirror-for-parity; (b) `subagents=[chunk-analyst]` coexists with auto-added `general-purpose` (keep by default); (c) `StateBackend` ephemeral → persistence choice at design time (chunk files vs vector store — the chunk files are the design decision, not ChromaDB); (d) `set_view()` usage in `show_rag_v2()` (the feature_024 bug pin); (e) `IRagV2ViewPartner` short-form naming (no clash); (f) D1-D8 locks unchanged; (g) v1-cutover decision (remove-vs-fallback) deferred to Design with G1–G6 proof gate explicit.

### Next

- **Design phase: write `design_001_*.md`** to `4.design/features/feature_027.rag_v2/` (the dir exists — mkdir'd during iter 1 but empty). Per `analysis_001_*.md`'s Recommendation, the design doc owns:
  1. **`RagV2AgentService` architecture** — parallel to `CodingAgentService`, OR additional `@tool`s on `CodingAgentService` itself (a design-phase decision; both follow the `create_deep_agent(model=, tools=[search_*], subagents=[chunk-analyst])` shape + `@tool`-pattern from `coding_tools.py:18`).
  2. **`subagents=[chunk-analyst]` contract** — one-file summarize, dispatched via `task({subagentType, description})`; the `SubAgent` dict spec `{name, description, system_prompt, tools?, middleware?, skills?, response_format?, permissions?}`.
  3. **Persistence-strategy decision** (Constraint (c)) — keep `StateBackend` (ephemeral, per-turn) vs swap to `FilesystemBackend`/`StoreBackend`/`CompositeBackend` (persistent chunk files). Default hypothesis: keep StateBackend (the pattern is per-turn; the agent's chunks are scratch, not state).
  4. **Cutover decision record** (D3, deferred to Design per TA: todo @ PROJECT.md:273) — remove v1 OR keep as opt-in fallback; the gate for EITHER choice is "v2 surface proven against G1–G6" first + downstream-consumer audit. Don't pre-decide it; record the proof gate explicitly.
  5. **Test plan** — sharpen the G1–G6 matrix rows (PROJECT.md:182-187) to actual pytest node IDs; mirror the feature_024 MVC++ contract-test shapes (`test_console_provider_and_views.py` 630 lines / 10 TestCase classes; `test_console_commands_and_views.py` 250 lines).
- **Then Programming** — feature_016 TDD auto-activates: `omt_tdd{op:testlist → red → green → refactor → done}`, two-hats (red = tests/ only, green/refactor = src/ only; closes via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT skip — D7 lock).
- **Then Testing** — the third artifact the Feature Health bar tracks (`test_report.md`).

### Pause notes

- The design_001_*.md name is `design_001_<topic>.md` (no ad-hoc `*_PROOF.md` per the new_feature.py output). Suggested: `design_001_deepagents_rag_v2_module.md` OR `design_001_retrieve_offload_delegate.md` — final name owned by the Design phase.
- The two TA: thoughts at PROJECT.md:274-275 (`xref: ANALYSIS-PARTIAL deepagents stack verified` + `gotcha: ANALYSIS-PARTIAL G1-G3 STALE`) can stay as anchor references now that `analysis_001_*.md` ships — their pointers to file:line don't rot easily. Leave tagged `ANALYSIS-PARTIAL` until the design doc commits (the design doc supersedes them, but the analysis verifications remain accurate references).

---

## 2026-08-09 (iter 0 — project definition locked + Quick Start block)

### Done (this iter)

- **`PROJECT.md` v1.1 → v1.2** (this round's only project-home edit, no `src/` edit, no feature dir scaffold — both intentionally deferred per the v1.1 lock).
  - **§New Session Quick Start** block prepended to the document (between the H1+v1.2 status line and the v1.1 Status preamble). The block has five named sub-sections:
    1. **What's locked** — a 5-row table mapping each locked v1.1 § to what a fresh session needs from it (Summary / Purpose-v1-gaps / Vision-standing-principle "retrieval is a tool" / Scope G1–G6 closure matrix / Decisions D1–D8).
    2. **The three exact next commands** (verbatim, runnable, in order):
       - `uv run scripts/omt/new_feature.py "rag v2" --type major_feature`  →  scaffolds `.meta/software_development_process/.../features/feature_027.rag_v2/` (free slot confirmed: 025=coding context window, 026=omt_q per `2.requirements/features/` listing).
       - `omt_phase{task_type:"major_feature", scope:"rag v2 — Analysis: ...", feature:"feature_027.rag_v2"}`  →  declares the Analysis phase (feature_016 TDD enforces at *Programming*, Analysis is TDD-free).
       - Run the four Analysis substrate reads in parallel + write `analysis_001_*.md` under `3.analysis/features/feature_027.rag_v2/` (sources: v1 RAG surface, feature_025 deepagents stack, feature_024 console MVC++ contract, LangChain deepagents-RAG docs).
    3. **What NOT to do** — seven ❌ items, each citing the locked decision it would re-litigate: don't scaffold from PROJECT.md / don't edit v1 (D3) / don't pick a different RAG pattern (D5) / don't add a TUI (D2) / don't modify the deepagents stack (D4) / don't add a new vector store / don't close TDD via skip (D7).
    4. **Resume entry point** — points back here to CURRENT_STATE.md.
  - **Status checklist bumped**: header status → v1.2; new row `[x] New Session Quick Start block (v1.2 — ...)` between the four v1.1-locked items and the four design-phase-pending items. Architecture, Tasks, feature dir scaffold, phase declared stay `[ ]`.
  - **Iteration log** appended with the v1.2 entry naming all three moves + gestalt. Three TA: thoughts from v1.1 preserved unchanged (the gotcha / todo / risk on retrieve-offload-delegate + v1 cutover + D5 lock — all still valid).
- **`CURRENT_STATE.md` iter-0** (this file) created per the meta_harness_2 convention (`PROJECT.md` = canonical design_doc, `CURRENT_STATE.md` = session log + resume point; sibling reference: `.projects/meta/meta_harness_2/{PROJECT.md,CURRENT_STATE.md}`).

### Test results

- _(none — project-home markdown only; no pytest run for docs work per `task_type:"docs"` convention.)_
- Sanity: `2.requirements/features/` listing re-verified (only up to feature_026) + no existing `feature_027` dir → step 1 of Quick Start is safe to run.

### Locked decisions (do not re-litigate without new evidence)

- **Quick Start block is navigational, not definitional** — no scope axis was changed by v1.2. The block writes the *path to start* over the *definition of the project* (which remains the locked v1.1 body in PROJECT.md). Editing the Quick Start block (e.g., renaming commands, re-ordering steps) is allowed without a new iteration; editing the v1.1 locked sections (Summary / Purpose / Vision / Scope / Decisions D1–D8) requires the v1.1 boundary-vs-content rules (changing an axis boundary = new iteration; sharpening within an axis = design-phase work).

- **CURRENT_STATE.md iter-0 is the resume anchor** — a fresh session reads CURRENT_STATE.md first, lands on iter-0, follows the resume_entry_point to PROJECT.md §New Session Quick Start, runs the three commands. Subsequent sessions add iter-1, iter-2, … blocks above iter-0; iter-0 stays as the historical origin point (do NOT rotation-delete iter-0 — it's the only entry that documents the pre-feature-dir definition state). Older iter blocks follow the WORK.md rotation rule (last N inline, older rotated to a future `CURRENT_STATE_ARCHIVE.md` if one is ever needed; N follows the same default as WORK.md, 5).

### Next

- **Run the three commands.** (iter 1 = Analysis phase begin)
  1. `uv run scripts/omt/new_feature.py "rag v2" --type major_feature`
  2. `omt_phase{task_type:"major_feature", scope:"rag v2 — Analysis: scaffold substrate reads + write analysis_001_*.md", feature:"feature_027.rag_v2"}`
  3. Parallel substrate reads → `analysis_001_*.md` under `3.analysis/features/feature_027.rag_v2/`.

- **After Analysis → Design phase**, write the deferred Architecture + Tasks into PROJECT.md (or, more likely, into `feature_027.rag_v2/design_001_*.md` per the feature dir's ownership of design-phase sharpening — the v1.1 PROJECT.md body explicitly defers both to the feature dir, so the next iter of THIS file's Status checklist only flips Architecture `[x]` once `design_001_*.md` is committed; the PROJECT.md may not need editing at design time at all, unless a §Standing principle extension arises (e.g., composing rubric-checked grounding on top of retrieve-offload-delegate per the TA: risk note at line ~210)).
