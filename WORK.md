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

- [x] **feature_031.petri_net_library** — DONE 2026-08-23: weighted P/T Petri-net library in `src/agentx/model/petri_net/` (model layer: weighted arcs, canonical tuple markings, pure `fire_marking`, typed errors; analysis layer: BFS reachability/graph/firing-sequences/deadlocks/bounds, exact incidence + P/T-invariants via pure-Python rational nullspace (D4, zero deps), liveness + Tarjan SCC on complete graphs; completeness-explicit `complete`/`reason`, `max_states` required kw-only; coverability = v2 stub). 3 TDD cycles; 99 tests; placeholder stub deleted; full suite 1577 passed, 0 regressions. Report @ `6.testing/features/feature_031.petri_net_library/test_report.md`.
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
- [x] **feature_030.project_lifecycle** — DONE 2026-08-22: mechanical .projects/ lifecycle (project.py CLI 9 cmds · 5 harnessc checks · design_doc inference + omt_complete ship-sync · omt_q project_drift + omt_status line · GENERATED manifest); 7 homes backfilled (9 origin:backfill links); 20/20 goldens, 232/0 omt. Report @ `6.testing/features/feature_030.project_lifecycle/test_report.md`.
---


## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023 meta-harness (F14-F17) · feature_tui_dark_mode (`k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (28 bx/37 tests) — **PAUSED 2026-08-02** · feature_kb_akb (UNIFIED IDX 437 recs; AST+curated+overlay; omt_kb_nav cap+truncate; g.kb gate + kb_bootstrap inject; 21/21 test_kb_*) — DONE 2026-08-08 · feature_025 deepagent context opt (create_deep_agent + middleware stack) — DONE 2026-08-08 · feature_026 omt_q interrogative layer (3 ops state/plan/drift + runBeforeGatesDry additive; 9 tools in IR; 14 golden + 14 sentinel) — DONE 2026-08-09 · feature_028 feature-scoped gating (meta_harness_3 Phase-A: P1-1/P1-2/P1-3/P3-8/T1; op=state 44KB→2.7KB) — DONE 2026-08-16 · feature_029 rag_v2 slash commands (hybrid grammar; streamed tool activity; tool rename) — DONE 2026-08-16 · bug_fix.rag_v2_ingestion_persist (_persist silent no-op → real Chroma via AIService().rag_chromadb(chroma_db); /chroma drift removed; web journal record; 6 regression tests) — DONE 2026-08-16 · bug_fix.help_command_deepcopy_thread (help crash after rag_v2 chat: get_commands deepcopied Command→MainController→worker thread → unpicklable _thread.lock; now shallow copy; 2 regression tests) — DONE 2026-08-16 · feature_031 petri_net_library (src/agentx/model/petri_net/: model + analysis layers, exact rational invariants, completeness-explicit, coverability v2 stub; 3 TDD cycles node-consistent; 99 tests; suite 1577; deferred-import REDs — top-level import of a nonexistent module = pytest exit 2, rejected by cmd_start) — DONE 2026-08-23.

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
