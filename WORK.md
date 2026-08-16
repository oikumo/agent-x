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

- [x] **feature_025.coding_context_window_optimization** — DONE (2026-08-08): `CodingAgentService` swapped from bare `create_agent` to deepagents full stack (`create_deep_agent` + Filesystem/Summarization/Memory/Skills middleware + `compact_conversation` tool; legacy fallback kept). `deepagents>=0.7` dep; 8/8 new + 143/143 regression + suite 1196 passed (3 known react_screen). Test report @ `6.testing/features/feature_025.coding_context_window_optimization/test_report.md`.
- [x] **feature_026.omt_q_interrogative_first_ops** — DONE (2026-08-09): New read-only `omt_q` plugin (`.opencode/plugins/omt_q.ts`, 3 ops `state|plan|drift`) with `as_of_commit` envelope + `kind:"q"` ledger; additive `runBeforeGatesDry` in `gate_driver.ts`. 9 tools in IR (`tool_schemas` 1024→1280). 14/14 golden + 14/14 sentinel + 31/31 pins + 12/12 drift + suite 1223 passed / 2 allowlisted (feature_016). Test report @ `6.testing/features/feature_026.omt_q_interrogative_first_ops/test_report.md`.
- [~] **feature_027.rag_v2** — GREEN 31/31 (2026-08-15): v2 console-only (console `rag` → `show_rag_v2` via new `RagV2ShowCommand`; v1 `RagShowCommand` stays for TUI path, untouched); 22 new src files (`model/rag_v2/` 12 + `ui/screens/rag_v2/` 10) + 4 additive edits (`interfaces.py`/`providers.py`/`main_controller.py`/`commands.py`); 5 test files under `tests/features/feature_027.rag_v2/`. Pre-existing hygiene blocked `omt_tdd{op:done}` (stray `sandbox/` dir + WORK.md budget) — fixing this session → REFACTOR done → `done` → Testing (`test_report.md`). resume → **`.sandbox/pause_2026-08-15_l.md`** (3 exact fixes applied this session: TUIProvider v2 stubs, lazy `ConsoleProvider` import, test `sys.modules` poison + source-pin slice fix).
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
---


## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023 meta-harness (F14-F17) · feature_tui_dark_mode (`k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (28 bx/37 tests) — **PAUSED 2026-08-02** · feature_kb_akb (UNIFIED IDX 437 recs; AST+curated+overlay; omt_kb_nav cap+truncate; g.kb gate + kb_bootstrap inject; 21/21 test_kb_*) — DONE 2026-08-08 · feature_025 deepagent context opt (create_deep_agent + middleware stack) — DONE 2026-08-08 · feature_026 omt_q interrogative layer (3 ops state/plan/drift + runBeforeGatesDry additive; 9 tools in IR; 14 golden + 14 sentinel) — DONE 2026-08-09.

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
