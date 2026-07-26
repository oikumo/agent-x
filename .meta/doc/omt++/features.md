# features.md — Feature Catalog (compressed) (grep:FEATURES_)

**SCOPE:** Every feature — status, summary, code + artifact locations.
**Status:** ✅ done · 🔨 in progress · ⏳ pending · 🅿️ placeholder

# SECTION:CATALOG — Feature Catalog Table (grep:FEATURES_CATALOG_)
| # | Feature | Status | Summary |
|---|---------|--------|---------|
| 001 | session_user_objectives_driven_by_Petri_Net | ⏳ | Petri-net-driven session objectives (will swap into agent's `IGoalManager`) |
| 002 | rag_retrieval_augmented_generation | ⏳ | RAG retrieval + generation (partially implemented; needs design scaffold) |
| 004 | modern_ui | ✅ | Textual TUI with full screen navigation (Main/Chat/RAG) |
| 005 | agentx_file_system_agentic_tools | ✅ | Agentic filesystem tools (folded into feature_007's tool registry) |
| 006 | opencode_process_enforcement | ✅ | OMT++ process gate: `mvc_check.py`, `new_feature.py`, `omt_enforcer.ts` |
| 007 | agentx_intelligent_agent_behaviour | ✅ | Intelligent agent: goals, policy DSL, memory, reflection, tools |
| 010 | agent_demo_screen | ✅ | One-trigger demo screen showcasing agent cycle (scenarios A/B) |
| 011 | fast_agent | ✅ | Modal-dialog-driven agent UX (Goal → Running → Reflection → Result) |
| 020 | meta_harness_navigation | ✅ | Grep-optimized docs + opencode plugin tools (omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref) |
| 021 | meta_harness_think_anywhere | ✅ | Persistent inline `TA:` thought-tags (omt_think/_list/_remove) + think-gate + session digest |
| 022 | meta_harness_think_anywhere_v2 | ✅ | Tier A ✅ (anchored THOUGHT_PATTERN + excludes, explicit ext map, string-context guard, filters/dedup/EOL); Tier B1+D1 ✅ (after:/symbol: anchor insertion + index anchor field; read-time thought injection, once/session, no consult); Tier C ✅ (omt_think_verify verified/stale lifecycle + digest stale count + risk-first/⚠️STALE gate weighting; per-file consult records + cross-session window dropped for risk:); Tier remainder ✅ (B2 omt_think_suggest AST-ranked site advisor via uv-run python end_lineno-splice-safe; E1 omt_think_reindex index drift-repair keep/repair/drop + verify prune, idempotent; E2 theory-doc F10–F13 fixes: pass@k unbiased estimator, per-block prefix attribution, strip-safety + sandbox warning, dead stub removed) |

> `feature_008.agent_framework` and `feature_009.feature_007_agentx_intelligent_agent_behaviour` = empty placeholder dirs (only `FEATURE.md` + `plan/`).

---

# SECTION:F001 — feature_001 — Session Objectives (Petri Net) ⏳ (grep:FEATURE_001_)
**Goal:** Drive session objectives through Petri-net model. Provides concrete `IGoalManager` impl replacing current stub (`agent/model/goal/manager.py`). Agent facade depends on `IGoalManager` abstraction → swaps at runtime.
- **Status:** Scope & success criteria not yet defined (`WORK.md`).
- **Integration point:** `agent/model/goal/manager.py` → `IGoalManager`.

# SECTION:F002 — feature_002 — RAG (Retrieval Augmented Generation) ⏳ (grep:FEATURE_002_)
**Goal:** Ingest documents (web + local) into vector store, answer questions with retrieval-augmented LLM responses. `Rag` orchestrator and `RagQuery` pipeline exist and wired into RAG screen; needs design scaffold.
- **Status:** Partially implemented (see subsystems.md §RAG); design doc pending.
- **Key code:** `src/agentx/model/rag/`.

# SECTION:F004 — feature_004 — Modern UI ✅ (grep:FEATURE_004_)
**Goal:** Rich Textual TUI replacing legacy console-only flow, with full screen navigation (Main → Chat → RAG → Agent), streaming chat, non-blocking RAG repository selection.
- **Key code:** `src/agentx/ui/tui/` (app, screens, adapters, provider).
- **Highlights:** `MainTUIScreen` pushes sub-screens directly AND calls `controller.show_*()` for wiring (dual-path fix for navigation freezes); `TUIChatAdapter` streams chunks into single growing widget; RAG screens use TUI modal screens instead of blocking console input.
- **Artifacts:** `.meta/.../features/feature_004.modern_ui/`.

# SECTION:F005 — feature_005 — Agentic File System Tools ✅ (grep:FEATURE_005_)
**Goal:** Agentic filesystem tools. Folded into feature_007's tool registry as `FileSystemTool` (hybrid sensor/actuator).
- **Key code:** `src/agentx/agent/model/tools/filesystem_tool.py`.

# SECTION:F006 — feature_006 — Opencode Process Enforcement ✅ (grep:FEATURE_006_)
**Goal:** Mechanically enforce OMT++ methodology via opencode. Provides MVC++ linter, feature scaffolder, live permissions, process gate plugin with phase-exit validation.
- **Key code:** `scripts/omt/mvc_check.py`, `scripts/omt/new_feature.py`, `.opencode/plugins/omt_enforcer.ts`, `.opencode/plugins/omt_status.ts`, `opencode.jsonc`.
- **Artifacts:** `.meta/.../features/feature_006.opencode_process_enforcement/`.

# SECTION:F007 — feature_007 — Intelligent Agent Behaviour ✅ (grep:FEATURE_007_)
**Goal:** Complete intelligent-agent subsystem running perceive → decide → act → reflect cycle driven by goals, policy condition DSL, tool registry, volatile/persistent memory, reflection engine with self-improvement proposals.
- **Key code:** `src/agentx/agent/` (model, controller, view, persistence, interfaces, types).
- **Subsystems:** Agent facade, GoalManager, PolicyEngine (condition DSL + conflict resolver), MemoryManager, ReflectionEngine (critique parser + safety evaluator + proposal router), ToolRegistry (FileSystemTool, RagSensorTool, SessionTool), `agent_session.db`.
- **Bug-fix pass:** All bugs in `BUG_FIX_PLAN.md` resolved (P0–P3); 169 tests pass; MVC++ 0/0.
- **Artifacts:** `.meta/.../features/feature_007.agentx_intelligent_agent_behaviour/` (8 analysis docs + design + operation specs + impl notes + test report).

# SECTION:F010 — feature_010 — Agent Demo Screen ✅ (grep:FEATURE_010_)
**Goal:** Dedicated Textual screen demonstrating feature_007 with one trigger. From Agent screen, press `d` (or type `demo [a|b]`) — seeds goal + rules + sandbox file, auto-runs cycle, offers Run/Reset/Back buttons.
- **Key code:** `src/agentx/agent/view/tui/demo_screen.py`, `src/agentx/agent/demo/scenarios.py`, `AgentController.load_demo_scenario_by_name()` / `reset_state()` / `Agent.clear_state()`.
- **Scenarios:** A = File Reader (1 cycle); B = Knowledge Assistant (read notes → write summary, multi-step, condition DSL showcase).
- **Side effect:** Fixed latent feature_007 bug (tools reading `command.parameters` instead of `command.action`) breaking runtime `EXECUTE_TOOL` create/query/update actions.
- **Artifacts:** `.meta/.../features/feature_010.agent_demo_screen/`.

# SECTION:F011 — feature_011 — Fast Agent ✅ (grep:FEATURE_011_)
**Goal:** Streamlined, modal-dialog-driven agent UX reusing existing feature_007 `Agent` engine through stack of Textual `ModalScreen` dialogs. Existing `🤖 Agent` button relabeled `⚙️ Advanced Agent`; new `⚡ Fast Agent` (`f` key) offers simpler UX.
- **Flow:** Goal → Running (auto-runs cycles) → Reflection (on proposal) → Result
- **Simplicity:** One goal at a time, natural-language input, no raw policy authoring, auto-runs cycles pausing only on reflection proposals, auto-resumes latest snapshot
- **First `ModalScreen` use** in codebase; Textual `ModalScreen` stack with `dismiss(value)` + callbacks
- **Key code:** `src/agentx/agent/view/tui/fast_agent_screen.py`, `fast_agent_modals.py`, `fast_agent_view.py`, `src/agentx/agent/controller/agent_controller.py` (+ `get_cycle_summary()`), `src/agentx/agent/adapter.py` (+ `create_fast()`), `src/agentx/ui/screens/main/main_controller.py` (+ `show_fast_agent()`), `src/agentx/ui/tui/screens/main_screen.py` (+ `f` binding, `⚡ Fast Agent` button, grid `3 2`, relabel "Advanced Agent")
- **MVC++ clean:** View-only addition; no Model-layer changes; `FastAgentTUIView` = no-op `IAgentViewPartner` virtual subclass; `get_cycle_summary()` returns plain dicts for display
- **Tests:** 44 new tests (unit + integration + MVC), 0 regressions
- **Artifacts:** `.meta/.../features/feature_011.fast_agent/` (design, impl notes, test report)

---

# SECTION:F020 — feature_020 — Meta Harness Navigation ✅ (grep:FEATURE_020_)
**Goal:** Structured, grep-based navigation of META HARNESS documentation using tag prefixes (`SECTION:`, `RULE_`, `ERR_`, `WRN_`, `CMD_`, `QUICK_`, `XREF_`, `TT_`, `PHASE_`, `FEAT_`). Agents must consult docs via nav tools before answering project questions; a mechanical gate blocks `grep`/`glob` on doc paths until a nav tool is used.
- **Key code:** `.opencode/plugins/omt_nav.ts` (4 tools: `omt_nav`, `omt_list_sections`, `omt_cross_ref`, `omt_quick_ref`), `.opencode/plugins/omt_enforcer.ts` (nav-gate), `opencode.jsonc` (tool permissions), `AGENTS.md` (MANDATORY section).
- **Defects fixed (e2e):** DEFECT-A (named tool-object exports not functions → "Plugin export is not a function"; fixed: only `export default`), DEFECT-B (`getSearchPath` passed non-string to `relOf` causing crash; fixed: defensive `typeof` guards), DEFECT-C (`input:{type,properties}` ignored by opencode → tools registered with no params; fixed: `args`/`tool.schema`), DEFECT-D (tools returned raw objects → opencode `.split()` crash; fixed: return plain strings).
- **Tests:** 54 tests (structural, behavioral via node runner, pure decider, enforcer integration, docs/config, plugin health). Serve e2e verified zero plugin-load errors.
- **Artifacts:** `.meta/.../features/feature_020.meta_harness_navigation/` (analysis, design, impl notes, test report).

# SECTION:F021 — feature_021 — Meta Harness Think Anywhere ✅ (grep:FEATURE_021_)
**Goal:** Persistent, grep-friendly inline `TA:` thought-tag layer adapting the Think-Anywhere paper's on-demand reasoning to a cross-session annotation/memory mechanism. Agents drop compact `TA:` comments inline in non-protected files; retrieval is grep-backed (O(hits) tokens); a per-session digest surfaces accumulated thoughts; a blocking think-gate refuses to edit thought-carrying files until consulted.
- **Key code:** `.opencode/plugins/omt_think.ts` (5 tools: `omt_think`, `omt_think_list`, `omt_think_remove`, `omt_think_verify`, `omt_think_suggest` + Tier 1c digest on first tool result; `omt_think_reindex` deleted in meta_harness_dsl R6), `.opencode/plugins/omt_enforcer.ts` (`thinkGateDecision`, `hasConsultedThoughts`, `fileThoughtsIn`, before-hook integration), `.meta/.omt/thoughts.jsonl` (append-only index sidecar), `opencode.jsonc` (tool permissions), `AGENTS.md` (MANDATORY section), `.meta/META_HARNESS.md` (`SECTION:THINK`).
- **Defect fixed:** DEFECT-A load crash — `omt_think.ts` named-exported `commentSyntaxFor` + `fileThoughts`; opencode's loader calls every named export at load with a non-string arg → `(ext||"").toLowerCase` crash → plugin never registered in real opencode. Fix: un-exported both (only `export default`); added deterministic `test_no_named_exports_except_default` structural guard.
- **Guardrails:** Hard-deny on `.env*`, `README.md`, `uv.lock`, `LICENSE`, `.json`; never creates files; bypasses phase/canary gates (annotation, not code); think-gate NOT bypassable by `omt_skip`; digest capped at 30 lines, list capped at 50.
- **Tests:** 30 tests across 5 classes (plugin structure incl. no-named-exports guard, real-tool behavioral, pure think-gate decider, enforcer integration/docs/config, plugin health).
- **Artifacts:** `.meta/.../features/feature_021.meta_harness_think_anywhere/` (FEATURE.md, analysis, design, operation specs, impl notes, test report).

---

# SECTION:CROSSCUT — Cross-Cutting Characteristics (grep:FEATURES_CROSSCUT_)
- **Persistence:** stdlib `sqlite3`, no ORM, idempotent DDL — three databases (`session.db`, `rag.db`, `agent_session.db`). See persistence.md.
- **AI-optional:** Agent cycle runs offline; reflection skipped when no AI service wired. Chat/RAG require LLM provider (OpenRouter default).
- **Two UIs, one controller layer:** Console and TUI share controllers via provider pattern — see architecture.md §3.
- **Test coverage:** ~1060 tests including Textual pilot e2e; feature tests under `tests/features/<feature_slug>/`.

---

# SECTION:XREF — Cross-References (grep:FEATURES_XREF_)
XREF_HARNESS: `.meta/META_HARNESS.md` — SECTION:RULES, SECTION:TDD, SECTION:RIGOR
XREF_GUIDE: `omt_agent_guide.md` — §12(Artifacts), §13(Checklist)
XREF_SUBSYSTEMS: `subsystems.md` — Agent, RAG, Session, AI, UI, Demo, Utils
XREF_DOC: `.meta/doc/` — architecture.md, features.md, subsystems.md, data_flow.md, persistence.md, extending.md
XREF_SDP: `.meta/software_development_process/` — phase artifacts per feature