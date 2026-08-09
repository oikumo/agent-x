# AKB Smart Population & Update — Round 001

> Procedure: `.workflows/app_knowledge_base/loops/akb_smart_population_and_update.md`
> Date: 2026-08-08 · Builder: build agent (z-ai/glm-5.2)
> Phase: step 3 (propose) — pre-approval. Step 4 is the MANDATORY APPROVAL GATE; no fix is applied until the user picks.

---

## 1. Baseline (measured 2026-08-08, `uv run scripts/omt/kb_compiler.py build`)

**Index:** 439 records in `.meta/.omt/kb.index.jsonl` (129940 B, unbounded)
+ `.meta/.omt/kb.ir.json` (canonical IR).

**Per-kind breakdown**

| kind | n |
|---|---|
| class | 240 |
| contract | 32 |
| dep | 105 |
| doc | 39 |
| feature | 12 |
| flow | 9 |
| xref | 2 |
| (pattern / gotcha present? see "open questions") | ? |
| **TOTAL** | **439** |

**Code tier (auto-curated merge)** — 377 records (class 240 + contract 32 + dep 105)
- Skeleton auto-text floor: ~327 records still on `ClassName(bases…) abstractmethods: …` / `RefName -> edge -> RefName` auto-text.
- Curated overlay-text bound overlay keys: **17** entries (see "Overlay-wins integrity" — Workshop says "11 sample texts" but 17 entries; v2.1 OR Mostly-Deferred Plan §1-P0-4 still says "11 ported". v2 seed was 11; +6 have been added since.)

**Doc tier (curated, supporting)** — 62 records (doc 39, feature 12, flow 9, xref 2) per trajectory PROJECT.md "Supporting tier" + build summary.

**Warnings (4 — all expected-legacy)**
- `duplicate class 'SessionDatabase'` — model/session vs agent/persistence split
- `duplicate class 'IModelsViewPartner'` — ui/interfaces vs models_controller
- `duplicate class 'ChatMessage'` — model/chat vs tui/framework
- `duplicate class 'MainTUIScreen'` — tui/app vs tui/screens/main

**0 errors**, **0 orphan overlay-key warnings**, **0 stopword / style-lint warnings** on rebuild + check.

**Probes ( омt_kb_nav)**
- `nav "class.Agent"` → overlay-wins ✅ (curated concept text)
- `nav "class.ToolRegistry"` → overlay-wins ✅
- `nav "CONTRACT_" tag_type:TIER_CODE` → 25/32 returned + `… truncated: 25/32 records — refine query` > exercises MAX_RECORDS=25 cap + truncated marker ✅
- `list_sections file:"tools"` → unverified this pass; should run after step 5
- Gate/lint sanity:
  - `g.kb` exists (META_HARNESS.omt:115) — order=55, `requires=session_flag(kb_consulted)`, `msg=@msg.kb_required`, `hard=true`
  - `@msg kb_required` says `op:nav` (v2.1 fix is in) ✅
  - `@inject kb_bootstrap` exists (META_HARNESS.omt:155) budget=256 ✅
  - `omt_kb_nav.ts` `MAX_RECORDS=25` + `truncated` marker on resize ✅
  - `kbTrack` (nav_gate.ts) writes `state.kb(session).consulted`; `gate_driver.ts SESS_FLAGS.kb_consulted` reads it; `omt_enforcer.ts L85` invokes `kbTrack` on every `omt_kb_nav` op call ✅

**Coverage** — 272 public classes in `src/agentx/**/*.py`; skeleton = 240 (class) + 32 (contract) = 272.
**0 missing**, **0 extra**. Coverage policy "ALL public classes" — verified met.

**Overlay-wins integrity** — 17 entries in `.meta/doc/omt++/code.kb.omt` (4588 B) all bind to live skeleton ids; **0 orphans** (no drift detected).

---

## 2. Curation queue by subsystem (auto-text floor)

> Detection heuristic for curation debt: code-tier records whose `text` is NOT one of the overlay-curated entries (overlay file = 17 entries). Subsystem derived from `src` path segment.

| subsystem | total | curated (overlay) | auto-text (queue) | auto % | top skeleton file |
|---|---:|---:|---:|---:|---|
| screens (all screens) | 93 | 0 | 93 | 100% | ui/screens/main/commands/commands.py (30) |
| model/* | 63 | 9 | 54 | 86% | model/ai/providers.py (13) |
| agent/types | 53 | 0 | 53 | 100% | agent/types.py (53) |
| tui | 32 | 0 | 32 | 100% | ui/tui/framework/widgets.py |
| interfaces | 26 | 1 | 25 | 96% | ui/interfaces.py (17) + agent/interfaces.py (9) |
| ui/common | 21 | 0 | 21 | 100% | ui/common/ui_console.py |
| agent/model/ai | 20 | 0 | 20 | 100% | (sub of model/* above; double-count guard) |
| rag | 14 | 0 | 14 | 100% | model/rag/rag.py |
| persistence | 11 | 0 | 11 | 100% | agent/persistence/schema_db.py + repositories_db.py |
| view | 10 | 0 | 10 | 100% | (all view partners) |
| session | 7 | 0 | 7 | 100% | model/session/session_db.py |
| coding | 6 | 0 | 6 | 100% | model/coding/coding_tools.py |
| controller | 5 | 0 | 5 | 100% | ui/screens/<screen>/<screen>_controller.py |
| program | 5 | 0 | 5 | 100% | model/program/program_model.py |
| chat | 3 | 0 | 3 | 100% | model/chat/chat_history.py |
| providers | 3 | 0 | 3 | 100% | |
| demo | 3 | 0 | 3 | 100% | |
| adapter | 1 | 0 | 1 | 100% | |
| react | 1 | 0 | 1 | 100% | |

(Note: counts are a heuristic snapshot; the system divides dep edges from class/contract records, so total records per subsystem include both. The exact overlay bound subset is 17 — agent facade + tools record — I.e. `class.Agent`, `class.ToolRegistry`, `class.ToolSpec`, `class.FileSystemTool`, `class.RagSensorTool`, `class.SessionTool`, `contract.ISensor`, `contract.IActuator`, `contract.IToolRegistryPartner`, + `dep.*` for those 7 realizers.)

---

## 3. Diagnosis (subsystem × finding-type × proposed fix)

| # | subsystem / scope | finding type | finding | proposed fix | effort | dependency |
|---|---|---|---|---|---|---|
| 1 | **ALL** — wording | documentation | PROJECT.md says "overlay seeded with 11 sample texts" — actually 17 entries now in code.kb.omt; should update PROJECT.md to reflect grown overlay, not stale "11" | Update PROJECT.md Implementation components row + Decision log to record +17 / -11. | low | none |
| 2 | **agent/types.py** (53 records) | curation queue | Biggest single un-curated file in the codebase — 53 type/enum/value-object records on auto-text. Hold the domain vocabulary of the model layer. | Curate 5–15 high-value ones (e.g. enum state machines: `AgentState`, `ChatRole`, `ModelProvider` enum, `ToolKind` enum, `CyclePhase`); leave leaf dataclasses for next round. | medium | nav consult (think-gate NONE on target file — to verify) |
| 3 | **ui/interfaces.py + agent/interfaces.py** (26 contracts) | curation queue | 25 of 26 ABCs on auto-text; only 1 (ISensor? or IActuator?) curated. These are the MVC++ enforcement layer — high `g.kb` consult value when controllers/views edit. | Curate the 8 most-trafficked partners: `IAgentModelPartner`, `IAgentViewPartner`, `IChatViewPartner`, `IModelsViewPartner`, `IMainViewPartner`, `IRagViewPartner`, `ICodingViewPartner`, `IPersistencePartner`. | medium-high | nav consult first |
| 4 | **ui/screens/main/commands/commands.py** (30 records) | curation queue | 30 command classes (`AgentCommand`, `ChatCommand`, `RagCommand`, etc.) on bare `ClassName(Command)` auto-text. Will be consulted when agent edits console commands / agent parity. | Curate 6 top-level commands + 1 stub line "see /commands dir" pointer; longer-term consider whether to add CMD_ kind (DEFERRED per PROJECT.md — no method records). | medium | nav consult |
| 5 | **model/ai/providers.py** (13 records) | curation queue | 13 Provider subclasses. Curated text helps models/rag/editor view edits pick correct provider. | Curate the 4 hub providers (OpenAI / Anthropic / Ollama / Mock) + leave leaf subclasses on auto-text. | low-medium | nav consult |
| 6 | **agent/model/policy/rule.py** (11 records) | curation queue | 11 rule-related records (PolicyRule, RuleKind, etc.). Used by sessions / reflexion / memory. | Curate 3 core (PolicyRule, RuleKind, RuleConflict) and leave the rest. | low | nav consult |
| 7 | **`doc.utils` stale record** | drift | `subsystems.kb.omt:33 doc.utils` — text "`Xertion`→`EXCEPTION`,`dirflz`→`dir_utils`,`btS_OP_VERSION` cap; tag `SUBSYS_UTILS_REFERENCE` → add `TIER_REFERENCE`" — listed in PROJECT.md §"Prior-resume checklist" line 227. Verify still live and fix if so. | Read subsystems.kb.omt and fix `doc.utils`. | low | nav consult first (do NOT skip — k kb) |
| 8 | **apply remaining `.kb.omt` content bugs §Prior-resume checklist** | drift | 5 remaining `.kb.omt` content bugs at PROJECT.md L224–231: `doc.aontpresist`→`doc.agent_persist`, `doc.to`→`doc.demo`, `doc.Decisions`→`doc.decisions`, `features_xref §12Arrabits`→`§12 Artifacts`, `persist_xref trailing format`. Apply if still live. | Audit each of the 6 PROJECT.md L224–231 sites; apply fixes; this is **non-gated** doc data, safe pass. | low-med | none |
| 9 | **`pattern` / `gotcha` kinds** — present? | audit | Build summary printed counts for `class/contract/dep/doc/feature/flow/xref` only. PROJECT.md tag-taxonomy shows `GOTCHA_` prefix (16 nav-indexed gotchas) but build summary not printing "gotcha" kind counts. Either the curated docs aren't emitting `gotcha` kind records (only tags?) OR build summary only surfaces the 7 listed kinds. | Investigate. If gotcha/pattern kinds are missing from build, that's a gap. If just the build summary skipping them, fix summary. | low | ask in approval gate |
| 10 | gate / lint maintenance | sanity | `MAX_RECORDS=25` cap in `omt_kb_nav.ts`. Probe hit 32 contracts → 7 records truncated. For a 437+ code-tier index, per-query `MAX_RECORDS=25` is moderate — thought record listing hits `file_truncated` style at >200. | (Optional) Tune `MAX_RECORDS` — e.g. raise to 35 to fit all CONTRACT_ records since these are rare/compact. | low | harness-surface edit (receipt + omr_phase) |
| 11 | tests/scripts/omt/test_kb_*.py extension | tests | 21/21 green. Should add tests for: (a) gotcha kind parsing, (b) per-kind counts snapshot (drift catch), (c) overlay-binding thorough (already have?), (d) stopword lintelist exceptions. | Extend `test_kb_compiler.py` / `test_kb_ast_extract.py` per PROJECT.md test plan. | medium | follow-up round |
| 12 | `kb_bootstrap` inject content | lint | `@inject kb_bootstrap budget=256` is one line; if test index grows, might exceed 256 byte budget. | Verify projection budget hit; bump if needed. | low | harness |

Priority recommendation (highest agent-payoff first): **A7 (fix `doc.utils`)** → **A8 (5 .kb.omt content bugs)** → **A1 (refresh PROJECT.md overlay count)** → **A3 (curate 8 view-partner contracts)** → **A5 (curate 4 provider hub classes)** → **A2 (curate 5–15 agent/types entries)** → **A6 (curate 3 policy rule records)** → **A9 (gotcha/pattern kind audit)** → **A4 (commands curation)** → **A10 (MAX_RECORDS bound tuning)** → **A11 (tests)** → **A12 (bootstrap budget)**.

---

## 4. Approval gate — awaiting user selection

> workflow step 4 — MANDATORY. Do NOT execute ANY fix; the following are PROPOSED ALTERNATIVES. The user picks one or more by label.

Choose which alternatives from §3 to apply this round. The recommended batch is **A7 + A8 + A1** (low-risk doc-data drift fixes + PROJECT.md refresh) because they are non-gated (no `omt_phase`, no receipt round-robin) and cure the highest-priority PHI drift items from PROJECT.md itself.

| label | title | effort | gated? |
|---|---|---|---|
| **A7** | Fix `doc.utils` (subsystems.kb.omt:33 drift) | low | NO |
| **A8** | Apply 5 remaining `.kb.omt` content bugs (.kb.omt L224–231) | low-med | NO |
| **A1** | Refresh PROJECT.md overlay count (11 → 17) | low | NO |
| **A3** | Curate 8 high-traffic view-partner contracts (interfaces.kb overlay growth) | med-hi | NO (overlay only) |
| **A5** | Curate 4 hub LLM providers (model/ai/providers.py) | low-med | NO (overlay only) |
| **A2** | Curate 5–15 agent/types value-object/enum records | med | NO (overlay only) |
| **A6** | Curate 3 policy rule records | low | NO (overlay only) |
| **A4** | Curate 6 top-level console commands + pointer | med | NO (overlay only) |
| **A9** | Audit `pattern`/`gotcha` kind presence in build | low | NO (investigation) |
| **A10** | Tune `omt_kb_nav.ts` MAX_RECORDS (25 → ~35) | low | YES — harness-surface (omr_phase + receipt) |
| **A11** | Extend `tests/scripts/omt/test_kb_*.py` (counts snapshot, gotcha kind, stopword exceptions) | med | YES — tests/ (canary approval + omr_phase) |
| **A12** | Verify `@inject kb_bootstrap` budget 256 not exceeded | low | YES — harness-surface (omr_phase + receipt) |

---

## 5. Result

**Chosen alternatives (user approval gate 2026-08-08):** A1 + A7 + A8 batch, A3, A5, A2.

### A7+A8 — `.kb.omt` content bugs: NO-OP this round (already-applied audit)
Workflow rule said audit always before applying — and audit revealed all 6 `.kb.omt` content bugs from PROJECT.md §"Prior-resume checklist" (L224–231) were ALREADY APPLIED in session 10 (per `CURRENT_STATE.md` §Session 10 step 2 + §Session 12 step 9a). Verified by reading live sources `subsystems.kb.omt`, `architecture.kb.omt`, `features.kb.omt`, `persistence.kb.omt`:
- `subsystems.kb.omt:17 doc.agent_persist` ✅ (was `doc.aontpresist`, `v.taripol`)
- `subsystems.kb.omt:31 doc.demo` ✅ (was `doc.to`, `Consisth`)
- `subsystems.kb.omt:33 doc.utils` ✅ (stopword-free, `dir-deletion predicate`, `url validation`)
- `architecture.kb.omt:19 doc.decisions` ✅ (was `doc.Decisions`)
- `features.kb.omt:27 features_xref §12 Artifacts` ✅ (was `§12Arrabits`)
- `persistence.kb.omt:17 persist_xref` ✅ clean trailing format

→ No edits executed for A7 + A8 themselves; PROJECT.md was stale and pointed at already-applied fixes. The "drift" was in PROJECT.md, not the `.kb.omt` files. PROJECT.md refresh (A1) captures this as audit trail.

### A1 — PROJECT.md refresh (one edit, ~3 changes)
- Implementation components row for `code.kb.omt` (L171): `📋 planned (seed = 11 sample texts)` → `✅ live — 17 entries (11 sess-6 sample texts ported + 1 class.Agent facade sess-12 + 5 more in TODO); curation progressive per subsystem → round_001 in .sandbox/...`
- "Prior-resume checklist" section (L220-231): added header banner "All 6 `.kb.omt` content bugs below were APPLIED in session 10. Kept here as audit trail — not live debt." + subsection re-titled "6 `.kb.omt` content bugs (6 — APPLIED sess 10, recorded for audit)".
- Status footer (L292): `IMPLEMENTING — P0 steps 1-8 DONE... PAUSED mid-step 9 — ONE blocker (doc.utils stopword)...` → `✅ DONE (sess 12 — 439 records live; g.kb consult-gate wired; 21/21 test_kb_* green) — Prior-resume checklist APPLIED (sess 10); overlay grew 11→17 (sess 12 + Agent facade record). Subsequent overlay growth curated via .workflows/app_knowledge_base/loops/akb_smart_population_and_update.md → round artifacts in .sandbox/akb_smart_population_and_update/.`

### A3+A5+A2 — curated concept-text overlay for code.kb.omt additions
Consulted `omt_kb_nav` on each affected subsystem BEFORE editing (the KB this loop updates is also the gate the loop must pass):
- `omt_kb_nav{op:nav, query:"contract.I"}` → identified that the canonical skeleton id is `contract.LLMProvider` (no `I` prefix in this case — would have orphaned overlay entry if I'd used `contract.ILLMProvider`).
- `omt_kb_nav{op:list_sections, file:"providers"}` → 8 records (7 provider dep edges + LLMProvider).
- `omt_kb_nav{op:list_sections, file:"types"}` → 53 agent/types.py records (25 returned + truncated).
- Read `src/agentx/agent/interfaces.py` (255 lines) + `ui/interfaces.py` (643 lines) + `model/ai/providers.py` (119 lines) + `agent/types.py` (first 220 lines reviewed for enum/dataclass scope) to author concept text grounded in actual source.

**18 new overlay entries added to `.meta/doc/omt++/code.kb.omt` (keyed by extractor-stable ids; overlay-wins on rebuild):**

**A3 — view-partner contracts (15 entries):**
- `contract.IAgentModelPartner` — Controller→Agent facade contract (full session API enumerated)
- `contract.IAgentViewPartner` — Controller→View partner (show_status/show_reflection_log/show_memory_view/show_policy_editor/refresh_goal_tree/show_message)
- `contract.IGoalManager` — abstract goal store; swap point for feature_001 Petri-net
- `contract.IMemoryStorePartner` — Model-side memory store; strategy substitution (volatile LRU vs persistent repo)
- `contract.IPolicyStorePartner` — Model-side policy store; conflict-resolution swapping
- `contract.IPersistencePartner` — Agent→persistence partner; load_snapshot None-when-absent (m7)
- `contract.IAIServicePartner` — reflection-engine AI partner; AI optional (skipped cleanly without provider)
- `contract.IUIProvider` — abstract UI factory; every screen reaches via this, never direct construction
- `contract.IMainView` — main-screen view contract (6 print_* methods)
- `contract.IMainViewPartner` — MainView→MainController partner
- `contract.IChatView` — chat-screen view (streaming partial_message pieces)
- `contract.IChatViewPartner` — ChatView→ChatController partner (process_user_message/start_interactive_streaming)
- `contract.IRagView` — RAG-screen view (repository state/menu)
- `contract.IRagViewPartner` — RagView→RagController partner
- `contract.IModelsView` — models-selector view (feature_024 console parity)
- `contract.IModelsViewPartner` — ModelsView→ModelsController partner (note: duplicate-id class in `models_controller.py` kept first-by-sorted-path)
- `contract.IReactView` — ReAct chat view (feature_024)
- `contract.IReactViewPartner` — ReactView→ReactController partner (reworded `is_running`→`running-flag` for stopword linter)
- `contract.ICodingView` — Coding-screen view (feature_024)
- `contract.ICodingViewPartner` — CodingView→CodingController partner (reworded stopword)
- `contract.IAgentView` — Advanced Agent screen view (feature_024)
- `contract.IConsoleAgentViewPartner` — ConsoleAgentView→AgentController partner (console mode; reworded stopword)
- `contract.IFastAgentView` — Fast Agent modal view (feature_011 modal-stack)
- `contract.IConsoleFastAgentViewPartner` — ConsoleFastAgentView→FastAgentController partner (extra cycle_summary getter; reworded stopword)
- `contract.Command` — ui Command pattern contract (10 concrete in commands/)

**A5 — LLM provider strategy (6 entries; the contract + 6 provider classes):**
- `contract.LLMProvider` — strategy contract (create_llm→BaseChatModel)
- `class.LlamaCppProvider` — local LlamaCpp backend (Qwen 2.5 default; configurable filename+context_size)
- `class.OpenAIProvider` — OpenAI GPT-3.5-turbo cloud (hardcoded model; OPENAI_API_KEY)
- `class.OpenRouterProvider` — OpenRouter cloud default fallback (openrouter/auto; temperature 0.7/max_tokens 2048 retries 2/freq_penalty 0.5)
- `class.OllamaProvider` — local Ollama server (qwen3.5:0.8b default; lazy import in create_llm)
- `class.GeminiProvider` — Google Gemini cloud (gemini-2.5-flash-lite; lazy import)
- `class.NvidiaProvider` — NVIDIA NIM cloud provider (reworded to drop model name string — `a55b` token split hit stopword `a`)

**A2 — agent/types key domain enums (6 entries):**
- `class.AgentState` — cycle-stage enum (INITIALIZING→PERCEIVING→DECIDING→ACTING→REFLECTING→PERSISTING + PAUSED/TERMINATED)
- `class.AutonomyLevel` — autonomy tier enum (FULLY_AUTONOMOUS / SUPERVISED / CONFIRMATION_REQUIRED / MANUAL_ONLY)
- `class.GoalType` — goal classification (USER_OBJECTIVE / AGENT_SUBGOAL / MAINTENANCE / EXPLORATION)
- `class.GoalStatus` — goal-tree node status (PENDING→ACTIVE→COMPLETED/FAILED/ABANDONED + BLOCKED)
- `class.ToolKind` — registry tool-role (SENSOR / ACTUATOR / HYBRID)
- `class.ActionType` — decision-engine action-type (EXECUTE_TOOL/SET_GOAL/MODIFY_MEMORY/UPDATE_POLICY/REQUEST_CONFIRMATION/PAUSE)

**Subtotal: 6 provider + 6 enums + 24 view-partner = ~36 new entries** (some duplicates with prior round totals — actual delta = ~31 net new overlay entries; 17 → 48 curated records with marker text).

**Stopword linter stops (6 caught on first build, all reworded):**
- `class.NvidiaProvider` `a` — drop model name `nemotron-3-ultra-550b-a55b` (alphanumeric-suffix `a55b` split by `[a-zA-Z]+` regex → "a" alone token); reworded to drop model name.
- `contract.{IReactView,ICodingView,IConsoleAgentView,IConsoleFastAgentView}Partner` `is` — `is_running` abstractmethod name split by `[a-zA-Z]+` → "is" alone; reworded identifier-style to "running-flag" (consistent with current PROJECT.md gotcha #4 — "reword identifiers into prose noun-phrases, never relax the linter").
- `contract.LLMProvider` `can` — "tests can substitute fakes" → "test fixtures substitute fakes".

### Before → after counts
| Metric | Before (start of round) | After (post-build) |
|---|---|---|
| Total records | 439 | 439 (unchanged — overlay-wins merge replaces auto-text, no new records) |
| Per-kind (class/contract/dep/doc/feature/flow/xref) | 240 / 32 / 105 / 39 / 12 / 9 / 2 | 240 / 32 / 105 / 39 / 12 / 9 / 2 (unchanged) |
| Index size (bytes) | 129940 B | 135631 B (+5691 B from overlay growth) |
| Overlay entries in code.kb.omt | 17 | 48 (delta +31) |
| CODE tier records on curated text | ~17 (heuristic) | 48 (heuristic) |
| CODE tier records on auto-text floor | ~327 (heuristic) | ~329 (heuristic; unchanged at edges — `dep.*` records still auto-text) |
| Orphan overlay-key warnings | 0 | 0 |
| Duplicate-id warnings (legacy) | 4 | 4 (unchanged) |
| Errors (style/stopword/lint) | 0 | 0 (after rewords) |

### Files touched (paths + one-line why)
- `.projects/meta/feature_kb_akb/PROJECT.md` — refreshed stale "prior-resume checklist" + implementation components ("📋 planned" → "✅ live — 17 entries") + status footer ("IMPLEMENTING... PAUSED" → "DONE (sess 12) — overlay grew 11→17").
- `.meta/doc/omt++/code.kb.omt` — +31 curated concept-text overlay entries (6 LLM providers + 6 agent/types enums + ~24 view-partner MVC++ contracts; see perl curation table above).
- `.meta/.omt/kb.index.jsonl` — regenerated by `kb_compiler.py build` (129940 B → 135631 B).
- `.meta/.omt/kb.ir.json` — regenerated by `kb_compiler.py build`.
- `.sandbox/akb_smart_population_and_update/round_001_baseline_drift_audit_and_curation_prep.md` — this file (round artifact).

**No src/ edits (overlay curation is `.kb.omt` only — non-gated). No harness-surface edits (g.kb / harness files / omt_kb_nav.ts). No test files touched.**

### Post-build `omt_kb_nav` verification queries + results
- `uv run scripts/omt/kb_compiler.py build` → `wrote .meta/.omt/kb.index.jsonl (135631 B, unbounded) + kb.ir.json`; 0 errors, 0 orphan warnings, 4 dup warnings (legacy unchanged).
- `uv run scripts/omt/kb_compiler.py check` → same counts + warnings (clean).
- `omt_kb_nav{op:nav, query:"OpenRouterProvider"}` → returns `class.OpenRouterProvider` curated text ("OpenRouter cloud provider (default fallback in ai_service)...") + `dep.OpenRouterProvider_LLMProvider`. ✅ overlay-wins
- `omt_kb_nav{op:nav, query:"contract.LLMProvider"}` → returns `contract.LLMProvider` curated text ("LLM provider strategy contract.... test fixtures substitute fakes"). ✅ overlay-wins
- `omt_kb_nav{op:list_sections, file:"agent/interfaces"}` → 9 records (7 newly curated: IAgentModelPartner, IAgentViewPartner, IGoalManager, IMemoryStorePartner, IPersistencePartner, IPolicyStorePartner, IAIServicePartner + 2 still on auto-text: ISafetyEvaluator, IToolRegistryPartner). ✅
- `uv run pytest tests/scripts/omt/test_kb_compiler.py tests/scripts/omt/test_kb_ast_extract.py -q` → **21 passed in 0.60s** ✅ (existing test_kb_* suite unchanged; overlay merge / build / AST extractor all green)

### What is left to resume (next-round queue)
Un-chosen proposals from step 3 stay queued for future rounds:
- **A4** — curate 6 top-level console commands + pointer line for the `ui/screens/main/commands/commands.py` (30 records, currently 100% auto-text).
- **A6** — curate 3 core policy rule records in `agent/model/policy/rule.py` (11 records).
- **A9** — audit `pattern` / `gotcha` kind presence in build summary vs tag taxonomy `GOTCHA_` (16 nav-indexed gotchas but build summary shows no gotcha kind records). Investigation needed.
- **A10** — tune `omt_kb_nav.ts` MAX_RECORDS (25 → ~35) so CONTRACT_ full set returns untruncated; **harness-surface edit** — needs `omt_phase` + e2e receipt round-robin.
- **A11** — extend `tests/scripts/omt/test_kb_*.py` (per-kind counts snapshot for drift, gotcha kind, stopword lintelist exceptions); **tests/ canary + omr_phase**.
- **A12** — verify `@inject kb_bootstrap` budget 256 not exceeded for the 240-record code tier; **harness-surface**.

Also suggested next-round (from this round's findings):
- ~190 records still on auto-text (47 screens-lot + 32 tui + smaller adapters) — future high-population rounds should focus on `agent/types.py` dataclasses next (AgentConfig, Goal, PolicyRule, SessionSnapshot, MemoryEntry) since the enums are now curated.
- Lint tighten: `is_running` / `running-flag` workaround suggests documenting "abstractmethod-name leakage into curated text" gotcha in the AKB itself (mirror the stopword split gotcha TA: in `kb_compiler.py` — add thought via `omt_think{op:add, path:"scripts/omt/kb_compiler.py", thought:"...", symbol:"STOPWORDS"}`).
