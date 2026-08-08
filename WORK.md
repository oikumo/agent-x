# WORK

> Single-developer + coding-agent roadmap. Machine-parseable, minimal friction, git-friendly.

---

## Convention

| Symbol | Meaning |
|--------|---------|
| `[ ]`  | Pending |
| `[~]`  | In progress (agent working on it) |
| `[x]`  | Done |
| `[!]`  | Blocked / needs decision |

**Hierarchy** - top-level task -> optional subtasks (indented 4 spaces).
**Metadata** - optional inline comment: `<!-- id:T-123 prio:medium agent:true -->`
**Thoughts** - separate `---` line then bullet list; tools can strip it.
**DONE entries** - one line + pointer (feature dir / git log); narrative is paid every session startup (CONV_WORK_DONE).
**DONE rotation** - keep pending + last 5 DONE inline; older rotate to `WORK_ARCHIVE.md` (never auto-read) — CONV_WORK_ROTATE; `harnessc check` errors past @var work_done_max.

---

## Tasks

- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
- [x] **feature_kb_akb.application_knowledge_base** — DONE (2026-08-08): UNIFIED concept-altitude index 437 records (239 class/32 contract/104 dep + 62 curated) via `kb_ast_extract.py` + `kb_compiler.py build` (curated+overlay merge, unbounded) + `omt_kb_nav.ts` cap=25+truncate; g.kb gate + kb_bootstrap inject wired; B7 Agent facade overlay; 21/21 test_kb_* green. Details: `.projects/meta/feature_kb_akb/PROJECT.md` v2.1 + git log + test_report.md under `6.testing/features/feature_kb_akb.application_knowledge_base/`.
- [x] **improvement007.meta_harness_evolution (ALL OPT A–I)** — DONE (2026-08-01): R1–R11 ({@var.x} interpolation · grammar-vocab check · arg diet 1609→1285 B + tool_args budget · TS+py consume IR (7 mirrors deleted) · after-gates in gate_driver · IR gate msgs + orphan check · derive round 2 (14 hand → 13 derived + 2 pruned) · META_HARNESS/META diet · guide dedup 27.5→23.9 KB + §15 drift fix + @xref guide 6→16); 163/163 omt · full suite 1109+3 known · live smoke 2/2. Details: .sandbox/meta/improvement007/OUTCOME.md + git log.
- [x] **feature_024.no_tui_full_features** — DONE (2026-08-08): All 5 console-parity bug categories (Alt A) resolved (missing show_memory_view · wrong ABC method name · 6 streaming callbacks · is_running · virtual subclass registration). `agent_controller.py` 350→284 LOC via `DemoController` extraction (delegation pattern, public surface unchanged), clearing the 300-LOC god-controller gate (`test_controllers_under_300_loc`). 80/80 mvc+parity+demo tests green; 329/329 agent-feature sweep green; 4 pre-existing failures unrelated (feature_kb count drift · textual react_screen). Details: .sandbox/feature_024_console_parity_bugs.md + git log.
  - [x] **feature_024.react_empty_input_reprompt** — DONE (2026-08-08): Bug fix — react module empty string (bare Enter) quit to agentx main menu instead of re-prompting. Root cause: `ConsoleReactView.show()` used `if not user_input: return` so empty exited; `UIConsole.capture_input()` returned `None` for empty/interrupt alike. Fix: `capture_input` now returns `""` for empty Enter and `None` only for Ctrl+C/Ctrl+D; `show()` re-prompts on `""`, exits on `None` or quit tokens `q/quit/exit` (mirrors TUI `ReactTUIScreen.action_send`). Banner changed "empty input to exit" → "q/quit/exit to return". Tests updated: renamed exit-on-empty → exit-on-interrupt; added empty-reprompts + quit-token-exits. 115/115 react+main sweep green; full suite 1186 passed (2 pre-existing unrelated kb/harness failures; 3 textual-pilot flaky deselected).
- [x] **improvement006.meta_harness_evolution (ALL OPT A–H)** — DONE (2026-08-01): schemas 1484→775 B + 18→7 tools (omt_tdd/omt_nav/omt_think op=) · WORK.md 5.9→3.3 KB DONE-rotation · seed-drift lint · @derive+nav/IR budgets · status compact+2 fixes · HDL-2 gate_driver (IR-ordered chain) · root-hygiene gate. Details: .sandbox/meta/improvement006/OUTCOME.md + git log.
- [x] **feature_tui_dark_mode** — TUI dark mode toggle + theme selector
- [x] **feature_023.production_hook_effects_test** — Test 6 MVC++ gate root-caused (after-hook args on `input`, SDK contract); tests green.
- [x] **meta.workflows_definition_layer** — DONE (2026-08-08): `.workflows/` catalog definition layer — root `META.md` (8 sections: catalog purpose, subject namespaces, `loops/` vs top-level split, file schema, discovery & trigger contract read-order, output-path declaration, authoring template, recurring invariants) + 3 subject META.md (`agentx` 2 loops, `meta_harness` 2 loops + 1 one-shot, `app_knowledge_base` future/reserved). 3 open gaps fixed: empty `app_knowledge_base/loops/` stub declared future; `consitency_enforcement` typo corrected (grep zero hits); `pause_dev_for_resume_later.md` brought to full schema (# Rules + # Pause strategy). S5 dry-run verified — two distinct triggers matched without filename paste. S6 `git diff --stat` confirms only `.workflows/` touched. Details: `.projects/meta/workflows/PROJECT.md` Tasks + git log.
---

## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023 meta-harness (F14-F17) · feature_tui_dark_mode (`k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (28 bx/37 tests) — **PAUSED 2026-08-02** · feature_kb_akb (UNIFIED IDX 437 recs; AST+curated+overlay; omt_kb_nav cap+truncate; g.kb gate + kb_bootstrap inject; 21/21 test_kb_*) — DONE 2026-08-08.

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
