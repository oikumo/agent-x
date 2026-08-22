# WORK_ARCHIVE — rotated DONE tasks

> Rotated out of WORK.md per CONV_WORK_ROTATE (improvement006/OPT-B): WORK.md
> keeps pending + last 5 DONE inline; older DONE lands here. NEVER auto-read
> (not in startup, not nav-indexed); consult only when archaeology is needed.

## 2026-08-22 rotation (feature_030.project_lifecycle kickoff round)

- [x] **feature_025.coding_context_window_optimization** — DONE (2026-08-08): deepagents full stack (`create_deep_agent` + middleware) — rotated to WORK_ARCHIVE.md.
- [x] **feature_026.omt_q_interrogative_first_ops** — DONE (2026-08-09): read-only `omt_q` plugin (3 ops `state|plan|drift`, `as_of_commit` envelope); 14/14 golden + 14/14 sentinel + suite 1223 passed (2 allowlisted). Report @ `6.testing/features/feature_026.omt_q_interrogative_first_ops/test_report.md`.
- [x] **feature_027.rag_v2** — DONE (2026-08-15): v2 console retrieve-offload-delegate RAG (deepagents + chunk-analyst subagent); 31/31 tests GREEN. Report @ `.meta/software_development_process/6.testing/features/feature_027.rag_v2/test_report.md`.
- [x] **feature_028.feature_scoped_gating** — DONE 2026-08-16 (meta_harness_3 Phase-A): P1-1 feature-scoped TDD state · P1-3 coverage-on-diff · P1-2 done split · T1 op=state summary 44KB→2.7KB; 10/10 GREEN; 217/217 omt. Report @ `6.testing/features/feature_028.feature_scoped_gating/test_report.md`.

## 2026-08-08 rotation (feature_025 completion round)

- [x] **meta.workflows_definition_layer** — DONE (2026-08-08): `.workflows/` catalog definition layer — root `META.md` (8 sections) + 3 subject META.md (`agentx` 2 loops, `meta_harness` 2 loops + 1 one-shot, `app_knowledge_base` future/reserved). 3 open gaps fixed (empty loops stub declared future; `consitency_enforcement` typo fixed; pause workflow brought to full schema). S5 dry-run verified. Details: `.projects/meta/workflows/PROJECT.md` + git log.
- [x] **meta.workflows_harness_surface** — DONE (2026-08-08): Declared the workflows project intent in the META HARNESS. `.omt` — fixed `@var root_allowlist` (`workflows`→`.workflows`, clearing repo-root hygiene) + added `@doc workflows`/`comp.workflows`/`pth.workflows` (nav-indexed). `harnessc.py` — `render_agents()` now emits an explicit `**Workflows (.workflows/):**` line in GENERATED AGENTS.md (243 records). `README.md` — Workflows Catalog subsection + Components row + record-count refresh (234→243). Build regenerated projections; drift-test 0 errors. Pre-existing `work_md` overage resolved by rotating verbose DONE → WORK_ARCHIVE.md. No `src/` changes. Details: git diff + PROJECT.md.
- [x] **meta.projects_harness_surface** — DONE (2026-08-08): Declared `.projects/` as a first-class META HARNESS component (mirrors `.workflows/` precedent). `.omt` — added `@doc comp.projects`/`pth.projects`/`projects_home` (nav-indexed); bumped `@budget agents_md 2560→2816` for `## Process` line. `harnessc.py` — `render_agents()` template emits `**Projects home (.projects/):**`. `README.md` — Components row + `### Projects Home` subsection; record-count 243→246. `test_omt_docs_drift_pins.py` — `AGENTS_BUDGET=2816`. Drift-test 0 errors; 184/184 omt green; 1187 passed (4 pre-existing baseline). No `src/` changes. Details: git diff + AGENTS.md L25.

## 2026-08-08 rotation (workflows contract surfacing round)

- [x] **feature_kb_akb.application_knowledge_base** — DONE (2026-08-08): UNIFIED concept-altitude index 437 records (239 class/32 contract/104 dep + 62 curated) via `kb_ast_extract.py` + `kb_compiler.py build` (curated+overlay merge, unbounded) + `omt_kb_nav.ts` cap=25+truncate; g.kb gate + kb_bootstrap inject wired; B7 Agent facade overlay; 21/21 test_kb_* green. Details: `.projects/meta/feature_kb_akb/PROJECT.md` v2.1 + git log + test_report.md under `6.testing/features/feature_kb_akb.application_knowledge_base/`.
- [x] **feature_024.no_tui_full_features** — DONE (2026-08-08): All 5 console-parity bug categories (Alt A) resolved (missing show_memory_view · wrong ABC method name · 6 streaming callbacks · is_running · virtual subclass registration). `agent_controller.py` 350→284 LOC via `DemoController` extraction (delegation pattern, public surface unchanged), clearing the 300-LOC god-controller gate (`test_controllers_under_300_loc`). 80/80 mvc+parity+demo tests green; 329/329 agent-feature sweep green; 4 pre-existing failures unrelated (feature_kb count drift · textual react_screen). Details: .sandbox/feature_024_console_parity_bugs.md + git log.
- [x] **feature_024.react_empty_input_reprompt** — DONE (2026-08-08): Bug fix — react module empty string (bare Enter) quit to agentx main menu instead of re-prompting. Root cause: `ConsoleReactView.show()` used `if not user_input: return` so empty exited; `UIConsole.capture_input()` returned `None` for empty/interrupt alike. Fix: `capture_input` now returns `""` for empty Enter and `None` only for Ctrl+C/Ctrl+D; `show()` re-prompts on `""`, exits on `None` or quit tokens `q/quit/exit` (mirrors TUI `ReactTUIScreen.action_send`). Banner changed "empty input to exit" → "q/quit/exit to return". Tests updated: renamed exit-on-empty → exit-on-interrupt; added empty-reprompts + quit-token-exits. 115/115 react+main sweep green; full suite 1186 passed (2 pre-existing unrelated kb/harness failures; 3 textual-pilot flaky deselected).
- [x] **improvement007.meta_harness_evolution (ALL OPT A–I)** — DONE (2026-08-01): R1–R11 ({@var.x} interpolation · grammar-vocab check · arg diet 1609→1285 B + tool_args budget · TS+py consume IR (7 mirrors deleted) · after-gates in gate_driver · IR gate msgs + orphan check · derive round 2 (14 hand → 13 derived + 2 pruned) · META_HARNESS/META diet · guide dedup 27.5→23.9 KB + §15 drift fix + @xref guide 6→16); 163/163 omt · full suite 1109+3 known · live smoke 2/2. Details: .sandbox/meta/improvement007/OUTCOME.md + git log.
- [x] **improvement006.meta_harness_evolution (ALL OPT A–H)** — DONE (2026-08-01): schemas 1484→775 B + 18→7 tools (omt_tdd/omt_nav/omt_think op=) · WORK.md 5.9→3.3 KB DONE-rotation · seed-drift lint · @derive+nav/IR budgets · status compact+2 fixes · HDL-2 gate_driver (IR-ordered chain) · root-hygiene gate. Details: .sandbox/meta/improvement006/OUTCOME.md + git log.
- [x] **feature_tui_dark_mode** — TUI dark mode toggle + theme selector (k toggles, Ctrl+Shift+T 21 themes).
- [x] **feature_023.production_hook_effects_test** — Test 6 MVC++ gate root-caused (after-hook args on `input`, SDK contract); tests green.

## 2026-08-01 rotation (improvement006/OPT-B)

- [x] **META HARNESS DSL** (refactor.meta_harness_dsl; supersedes refactor.meta_harness) — DONE (2026-07-26): workstreams R0–R8 ALL DONE (ledger rotation · enforcer split ×7 · tdd/ package · docs single-source · think index append-only · budget pins · OMT-HDL-1 .omt+harnessc → IR/nav.index/AGENTS.md/jsonc projections; AGENTS.md user-adopted). Details: .sandbox/meta_harness_refactor_plan.md (anchor a7163df) + git log.
- [x] **R4 (meta_harness_dsl): state hygiene + latent bugs** — DONE (2026-07-26): ledger 64 KB rotation, omt_done reachable, TDD tests/ bootstrap doc. Details: git log + .sandbox/meta_harness_refactor_plan.md.
- [x] **feature_007.agentx_intelligent_agent_behaviour**
- [x] **Fix feature_007 bugs per BUG_FIX_PLAN.md**
- [x] **feature_004.modern_ui**
- [x] **Update README.md with feature_006 and agentic workflow**
- [x] **Update application design overview in .meta/.../4.design/**
- [x] **feature_006.opencode_process_enforcement**
- [x] **feature_012.tui_framework**
- [x] **feature_010.agent_demo_screen**
- [x] **feature_011.fast_agent**
- [x] **feature_013.ai_model_provider_selector**
- [x] **feature_014.tui_nonblocking_runner**
- [x] **Fix feature_011.fast_agent UI freeze**
- [x] **feature_016.tdd_enforcement**
- [x] **Fix feature_017.chat_screen_conversation_history_bug**
- [x] **feature_017.improve_chat_screen**
- [x] **feature_018.chat_screen_improvements**
- [x] **Fix chat screen "no assistant message" bug**
- [x] **Fix chat screen "no conversation history" bug**
- [x] **feature_018.react_screen**
- [x] **feature_019.coding_agent_screen**
- [x] **feature_020.meta_harness_navigation** <!-- id:T-020 prio:high agent:true -->
- [x] **feature_020.e2e_tests_opencode_driven** <!-- id:T-020e2e prio:high agent:true -->
- [x] **feature_021.meta_harness_think_anywhere** <!-- id:T-021 prio:high agent:true -->
- [x] **feature_022.meta_harness_think_anywhere_v2 — Tier A: correctness hotfixes A1–A4** <!-- id:T-022 prio:medium agent:true -->
- [x] **think_anywhere_v2 Tier B1+D1: anchor-based insertion + read-time thought injection** <!-- id:T-022BD prio:medium agent:true -->
- [x] **think_anywhere_v2 Tier C: verify/stale lifecycle C1 + per-file consult C2** <!-- id:T-022C prio:low agent:true -->
- [x] **think_anywhere_v2 Tier remainder: B2 suggest + E1 index strategy + E2 theory-doc fixes** <!-- id:T-022E prio:low agent:true -->
- [x] **feature_023.meta_harness_improvement** <!-- id:T-023 prio:high agent:true -->
- [x] **feature_023.test_refactor_live_only** — consolidated suite: Node-runner fixtures removed; source-pins + live-opencode-binary tests kept (13 verification points); 68 static + e2e ✓.
- [x] **Evaluate META HARNESS DSL + verify implementation (fix if needed)** <!-- id:T-024 prio:high agent:true --> — DONE (2026-07-26): VERIFIED GREEN (harnessc 0 errors, live bun probe, jsonc splice); 4 fixes implemented (gate-order pin, IR-driven doc_paths, .omt-sourced numeric constants, harnessc @version robustness). Details: git log.
- [x] **feature_023.deep_harness_tests** <!-- id:T-023d prio:high agent:true --> — BUG-B live test redesigned (git-dirty-first); suite 105/105 ✓; dist/ deleted (proven unused); TA index reconciled.

## 2026-08-16 rotation (ingestion bug_fix completion round)

- [x] **feature_025.coding_context_window_optimization** — DONE (2026-08-08): `CodingAgentService` swapped from bare `create_agent` to deepagents full stack (`create_deep_agent` + Filesystem/Summarization/Memory/Skills middleware + `compact_conversation` tool; legacy fallback kept). `deepagents>=0.7` dep; 8/8 new + 143/143 regression + suite 1196 passed (3 known react_screen). Test report @ `6.testing/features/feature_025.coding_context_window_optimization/test_report.md`.
