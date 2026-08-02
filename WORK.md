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

- [~] **feature_kb_akb.application_knowledge_base** — IN PROGRESS (2026-08-02): Full migration of 6 `.meta/doc/omt++/*.md` → `.kb.omt` + `kb_compiler.py` + `omt_kb_nav.ts` plugin + `g.kb` gate. **PAUSED for resume.** Analysis complete, plan approved, ready to begin implementation. Resume: read `.projects/meta/feature_kb_akb/CURRENT_STATE.md` then `omt_phase{task_type:major_feature, scope:"AKB: compiler + 6 .kb.omt migrations + omt_kb_nav + g.kb gate + tests", feature:feature_kb_akb}`.
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
- [x] **improvement007.meta_harness_evolution (ALL OPT A–I)** — DONE (2026-08-01): R1–R11 ({@var.x} interpolation · grammar-vocab check · arg diet 1609→1285 B + tool_args budget · TS+py consume IR (7 mirrors deleted) · after-gates in gate_driver · IR gate msgs + orphan check · derive round 2 (14 hand → 13 derived + 2 pruned) · META_HARNESS/META diet · guide dedup 27.5→23.9 KB + §15 drift fix + @xref guide 6→16); 163/163 omt · full suite 1109+3 known · live smoke 2/2. Details: .sandbox/meta/improvement007/OUTCOME.md + git log.
- [!] **feature_024.no_tui_full_features** — BUG FIX ANALYSIS PAUSED (2026-08-02): feature_024 tests pass but runtime bugs found — console views violate IAgentViewPartner contract (missing show_memory_view), console partner ABCs declare wrong method (process_user_message vs send_message), ConsoleReactView/ConsoleCodingView missing 6 streaming callbacks (silent no-ops), AgentController not registered as virtual subclass of console partner ABCs. Analysis & fix alternatives documented in .sandbox/feature_024_console_parity_bugs.md. Awaiting user decision on fix alternative (A/B/C/D).
- [x] **improvement006.meta_harness_evolution (ALL OPT A–H)** — DONE (2026-08-01): schemas 1484→775 B + 18→7 tools (omt_tdd/omt_nav/omt_think op=) · WORK.md 5.9→3.3 KB DONE-rotation · seed-drift lint · @derive+nav/IR budgets · status compact+2 fixes · HDL-2 gate_driver (IR-ordered chain) · root-hygiene gate. Details: .sandbox/meta/improvement006/OUTCOME.md + git log.
- [x] **feature_tui_dark_mode** — TUI dark mode toggle + theme selector
- [x] **feature_023.production_hook_effects_test** — Test 6 MVC++ gate root-caused (after-hook args on `input`, SDK contract); tests green.
---

## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023.meta_harness_improvement (F14-F17) · feature_tui_dark_mode (default dark, `k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (react/coding/models/agent/fast-agent REPL + streaming via IUIProvider; 28 behaviors/37 tests) — **BUG FIX PAUSED 2026-08-02**.

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
