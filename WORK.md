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

- [x] **feature_025.coding_context_window_optimization** — DONE (2026-08-08): Swapped bare `create_agent` in `CodingAgentService` for the LangChain deepagents full stack (`create_deep_agent` + `FilesystemMiddleware` + `SummarizationMiddleware` + `MemoryMiddleware` + `SkillsMiddleware` + on-demand `compact_conversation` tool via `create_summarization_tool_middleware`); `stream_agent` filters `lc_source=="summarization"` deltas out of `on_answer`/`on_reasoning`; `deepagents>=0.7` dep added; legacy `create_agent` fallback kept for stripped environments. MVC pin preserved; 8/8 new tests + 143/143 regression sweep green; full suite 1196 passed (3 known react_screen baseline).
- [~] **feature_026.omt_q_interrogative_first_ops** — **PAUSED 2026-08-09 (session D)** mid-Step-3-GREEN-fix: 13/14 golden tests green, 1 red remaining (U10 `test_u10_known_suite_failures_from_state_py` — hermetic-root fix: use `REPO_ROOT` not `tmp_path` for the U10 probe since `parseKnownSuiteFailures(repoRoot())` reads the live `scripts/omt/tdd/state.py`). GREEN source shipped this session: `.opencode/lib/enforcer/gate_driver.ts` additive `runBeforeGatesDry` + `GateDecision` (31/31 behaviour-preservation pins stayed green; `runBeforeGates` body byte-identical) + `.opencode/plugins/omt_q.ts` (682 lines, 3 ops `op:state|plan|drift` + `as_of_commit` envelope + `kind:"q"` ledger + 8 fold helpers). RED source shipped: `tests/scripts/omt/test_omt_q.py` (681 lines, 14 tests across 12 classes) + `tests/features/feature_026.omt_q_interrogative_first_ops/test_omt_q_golden_smoke.py` (sentinel re-export). Bugs fixed this session: (1) `buildCtxFromInputs` was spreading `createSessionState()` at top-level instead of `state: createSessionState()` — caused `env.state.nav` TypeError; (2) `foldDecreeHealth` was feature-filtering the empty-slug record out of view — now health scans are GLOBAL, only `phase_cycle_count` narrows. Next = fix U10 + cleanup debug `catch (e)` block in plan op (revert to clean fail-open) + REFACTOR (674→<600 lines) + `omt_tdd{op:done}` + regression + phase exits. Parent design source-of-truth `.projects/meta/meta_harness_2/PROJECT.md` (v1.5, 513 lines). Resume by reading `.sandbox/pause_2026-08-09_d.md`.
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
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
