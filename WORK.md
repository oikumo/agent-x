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

- [x] **feature_025.coding_context_window_optimization** — DONE (2026-08-08): deepagents full stack (`create_deep_agent` + middleware) — rotated to WORK_ARCHIVE.md.
- [x] **feature_026.omt_q_interrogative_first_ops** — DONE (2026-08-09): read-only `omt_q` plugin (3 ops `state|plan|drift`, `as_of_commit` envelope); 14/14 golden + 14/14 sentinel + suite 1223 passed (2 allowlisted). Report @ `6.testing/features/feature_026.omt_q_interrogative_first_ops/test_report.md`.
- [x] **feature_027.rag_v2** — DONE (2026-08-15): v2 console retrieve-offload-delegate RAG (deepagents + chunk-analyst subagent); 31/31 tests GREEN. Report @ `.meta/software_development_process/6.testing/features/feature_027.rag_v2/test_report.md`.
- [x] **feature_028.feature_scoped_gating** — DONE 2026-08-16 (meta_harness_3 Phase-A): P1-1 feature-scoped TDD state · P1-3 coverage-on-diff · P1-2 done split · T1 op=state summary 44KB→2.7KB; 10/10 GREEN; 217/217 omt. Report @ `6.testing/features/feature_028.feature_scoped_gating/test_report.md`.
- [x] **feature_029.rag_v2_slash_commands** — DONE 2026-08-16: rag_v2 REPL → hybrid slash grammar (`/help /search /repos /use /create /ingest /status /reset /quit`); streamed tool activity (`» search:` / `» analyst:`); tools renamed `search_documents`/`ingestion_status`; 51 new tests; suite 1335 passed. Report @ `6.testing/features/feature_029.rag_v2_slash_commands/test_report.md`.
- [x] **bug_fix.rag_v2_ingestion_persist** — DONE 2026-08-16: `_persist` (web/md/pdf) built `RagV2` which has no `add_texts` → silent no-op (chunks never stored). Now persists via `AIService().rag_chromadb("<repo>/chroma_db")` per operation_spec_001; `/chroma` drift removed (one Chroma per repo; empty skeleton dirs deleted from session); web journal record added; 6 regression tests pin production path. Suite 1338 passed (3 harness budget tests fixed).
- [x] **bug_fix.help_command_deepcopy_thread** — DONE 2026-08-16: console `help` crashed `TypeError: cannot pickle '_thread.lock' object` after a RAG v2 chat. `get_commands()` deepcopied every Command; each holds a MainController back-ref whose graph contains the rag_v2 worker thread. Now shallow list copy (`list(self.commands.values())`); 2 regression tests; suite 1343 passed.
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
---


## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023 meta-harness (F14-F17) · feature_tui_dark_mode (`k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (28 bx/37 tests) — **PAUSED 2026-08-02** · feature_kb_akb (UNIFIED IDX 437 recs; AST+curated+overlay; omt_kb_nav cap+truncate; g.kb gate + kb_bootstrap inject; 21/21 test_kb_*) — DONE 2026-08-08 · feature_025 deepagent context opt (create_deep_agent + middleware stack) — DONE 2026-08-08 · feature_026 omt_q interrogative layer (3 ops state/plan/drift + runBeforeGatesDry additive; 9 tools in IR; 14 golden + 14 sentinel) — DONE 2026-08-09 · feature_028 feature-scoped gating (meta_harness_3 Phase-A: P1-1/P1-2/P1-3/P3-8/T1; op=state 44KB→2.7KB) — DONE 2026-08-16 · feature_029 rag_v2 slash commands (hybrid grammar; streamed tool activity; tool rename) — DONE 2026-08-16 · bug_fix.rag_v2_ingestion_persist (_persist silent no-op → real Chroma via AIService().rag_chromadb(chroma_db); /chroma drift removed; web journal record; 6 regression tests) — DONE 2026-08-16 · bug_fix.help_command_deepcopy_thread (help crash after rag_v2 chat: get_commands deepcopied Command→MainController→worker thread → unpicklable _thread.lock; now shallow copy; 2 regression tests) — DONE 2026-08-16.

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
