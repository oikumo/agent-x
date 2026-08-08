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
- [x] **feature_kb_akb.application_knowledge_base** — DONE (2026-08-08): UNIFIED concept-altitude index 437 records via `kb_compiler.py build`; g.kb gate + kb_bootstrap inject wired; 21/21 test_kb_* green. Details: `.projects/meta/feature_kb_akb/PROJECT.md` + git log. (Full narrative rotated 2026-08-08 → WORK_ARCHIVE.md.)
- [x] **improvement007.meta_harness_evolution (ALL OPT A–I)** — DONE (2026-08-01): R1–R11 (HDL-2/deriver/diet/dedup); 163/163 omt. Details: .sandbox/meta/improvement007/OUTCOME.md + git log.
- [x] **feature_024.no_tui_full_features** — DONE (2026-08-08): 5 console-parity bug cats resolved; `agent_controller.py` 350→284 LOC via `DemoController` extraction (god-controller gate cleared); 80/80 + 329/329 green. Subtask `feature_024.react_empty_input_reprompt` — empty Enter re-prompts (was quit). Details: .sandbox/feature_024_console_parity_bugs.md + git log. (Full narratives rotated 2026-08-08 → WORK_ARCHIVE.md.)
- [x] **improvement006.meta_harness_evolution (ALL OPT A–H)** — DONE (2026-08-01): schemas 1484→775 B + 18→7 tools; HDL-2 gate_driver; root-hygiene gate. Details: .sandbox/meta/improvement006/OUTCOME.md + git log.
- [x] **feature_tui_dark_mode** — dark mode toggle + theme selector (rotated 2026-08-08).
- [x] **feature_023.production_hook_effects_test** — MVC++ gate root-caused; tests green (rotated 2026-08-08).
- [x] **meta.workflows_definition_layer** — DONE (2026-08-08): `.workflows/` catalog definition layer — root `META.md` (8 sections) + 3 subject META.md (`agentx` 2 loops, `meta_harness` 2 loops + 1 one-shot, `app_knowledge_base` future/reserved). 3 open gaps fixed (empty loops stub declared future; `consitency_enforcement` typo fixed; pause workflow brought to full schema). S5 dry-run verified. Details: `.projects/meta/workflows/PROJECT.md` + git log.
- [x] **meta.workflows_harness_surface** — DONE (2026-08-08): Declared the workflows project intent in the META HARNESS. `.omt` — fixed `@var root_allowlist` (`workflows`→`.workflows`, clearing repo-root hygiene) + added `@doc workflows`/`comp.workflows`/`pth.workflows` (nav-indexed). `harnessc.py` — `render_agents()` now emits an explicit `**Workflows (.workflows/):**` line in GENERATED AGENTS.md (243 records). `README.md` — Workflows Catalog subsection + Components row + record-count refresh (234→243). Build regenerated projections; drift-test 0 errors. Pre-existing `work_md` overage resolved by rotating verbose DONE → WORK_ARCHIVE.md. No `src/` changes. Details: git diff + PROJECT.md.
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
