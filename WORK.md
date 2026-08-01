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
- [x] **feature_024.no_tui_full_features** — DONE (2026-08-01): console parity (IUIProvider + 5 console REPL views + streaming); cmd_done latest-per-node fix; coverage-gate skip override wired. Details: .meta/.../feature_024.* dirs + git log.
- [x] **improvement006.meta_harness_evolution (ALL OPT A–H)** — DONE (2026-08-01): schemas 1484→775 B + 18→7 tools (omt_tdd/omt_nav/omt_think op=) · WORK.md 5.9→3.3 KB DONE-rotation · seed-drift lint · @derive+nav/IR budgets · status compact+2 fixes · HDL-2 gate_driver (IR-ordered chain) · root-hygiene gate. Details: .sandbox/meta/improvement006/OUTCOME.md + git log.
- [x] **feature_tui_dark_mode** — TUI dark mode toggle + theme selector
- [x] **feature_023.production_hook_effects_test** — Test 6 MVC++ gate root-caused (after-hook args on `input`, SDK contract); tests green.
- [x] **feature_023.deep_harness_tests** <!-- id:T-023d prio:high agent:true --> — BUG-B live test redesigned (git-dirty-first); suite 105/105 ✓; dist/ deleted (proven unused); TA index reconciled.
- [x] **Evaluate META HARNESS DSL + verify implementation (fix if needed)** <!-- id:T-024 prio:high agent:true --> — DONE (2026-07-26): VERIFIED GREEN (harnessc 0 errors, live bun probe, jsonc splice); 4 fixes implemented (gate-order pin, IR-driven doc_paths, .omt-sourced numeric constants, harnessc @version robustness). Details: git log.

---

## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023.meta_harness_improvement (F14-F17) · feature_tui_dark_mode (default dark, `k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (react/coding/models/agent/fast-agent REPL + streaming via IUIProvider; 28 behaviors/37 tests).

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
