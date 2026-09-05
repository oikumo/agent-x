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

- [x] **feature_041.resource_places_concurrency** — DONE 2026-08-30: minor_feature (meta_harness_concurrent core 3/3 — CORE COMPLETE): R1–R8 resource places — 5-place catalog cap=1 (IDEA-002 v4 §2.2: agent_attention/src_edit_capacity/tests_capacity/harness_surface_round/e2e_receipt), R2 attention claim/release arcs, R3 ports.resources refinement, R4 resource_report + invariant-envelope resources[]/conflicts[], R5 resync ONE add_resource_places proposal, R6 lifecycle auto-sync hooks (project.py ×5 + new_feature.py link), R8 zero TS/budget churn; dogfood REAL SSOT rev 0→1 (sync→splice, invariant green); 27/27 canonical, sentinel 1756 passed, harnessc 0 err, pins 12/12. Finding: omt_net.ts --session proxy bug → feature_046? (user); D17 feature_045 promotion open (user). Details @ FEATURE.md + test_report.md.
- [x] **feature_046.omt_net_session_arg_whitelist** — DONE 2026-08-30: bug_fix (meta_harness_concurrent): omt_net.ts per-op `OP_ARGS` argv whitelist mirroring cli.py subparsers (no `--session` for probe/invariant/synthesize; `max_states` probe-gated) + TA gotcha→why-note + 6 cross-source pins; sentinel 1756→1762, harnessc 0 err, e2e refreshed; live plugin check on next-session reload (cached plugin ran pre-fix code). Details @ FEATURE.md.
- [x] **feature_045.work_md_net_driven** — DONE 2026-09-05: minor_feature (meta_harness_concurrent core 4/4 — CORE COMPLETE): `sync_md.py` render/parse/propose + `omt_net{op:sync}` md directions (`--direction/--dry-run/--work-md`, net_to_md/md_to_net_propose) + `_write_md_section` rev-stamped Tasks block (NEXT/Other/Blocked/Resources per D19) + 6 round-trip vectors; net 98 green, pins 6/6, e2e 1/1, dogfood SSOT rev 43 dry-run (NEXT f001_start, 6 pending, 5/5 free); sentinel 1767 passed +1 flake (`test_nav_reminder_deferred`, passes isolated), harnessc 0 err. Details @ FEATURE.md + test_report.md.
- [x] **feature_042.goal_net_synthesis** — DONE 2026-09-05: minor_feature (meta_harness_concurrent phase-2 1/3): `synthesize` template proposal (task→chain, dependency→arc, resource⇄borrow, acceptance→verified) + D4 proposal-only/D20 pool-aware (no revision bump, net_synthesize audit, would_exceed_cap) + zero-churn args reuse (tool_schemas +8, tool_args flat); test_net_synthesize.py×16; omt 386 green, sentinel 1800, harnessc 0 err, e2e ×2; live rev48→49 drift-free (4/0/3). Details @ FEATURE.md + test_report.md.
- [x] **feature_043.meta_net_dashboard** — DONE 2026-09-05: major_feature (meta_harness_concurrent phase-2 2/3): ledger-replay snapshot (`history.py` fold, 83 records→52 snaps, live-exact, 2 leaks skipped transparently) + read-only dashboard page (graph/deadlock-highlight/slider, studio reuse) + TDD testlist-red-green-refactor-done; pytest×12 + vitest×9 + bridge×3; omt 398, sentinel 1815, harnessc 0 err (zero budget churn), build+preview green; live rev50→51 drift-free (3/0/4). Details @ FEATURE.md + test_report.md.
- [x] **feature_044.mined_behavioral_net** — optional phase-2 (scaffolded).
- [x] **feature_048.wip_limited_pool** — DONE 2026-09-05: minor_feature (meta_harness_concurrent): pool-aware net (sync empty on pool + pool info, 15-cap guard, pool holders/conflicts, Pool render line) + test_net_pool.py×10 + tombstone 047 + budget 8192; omt 364 green, sentinel 1778, harnessc 0 err, live rev45 pool 12 places drift-free. Details @ FEATURE.md + test_report.md.
- [x] **feature_049.session_start_menu** — DONE 2026-09-05: minor_feature (meta_harness_concurrent D19 on pool net, rescaffolded — 047 tombstone): menu_lines pool-aware + render NEXT work_complete when active + fire --expected-revision stale guard + STARTUP Tasks-menu line (agents_md 2816→2944); test_net_menu.py×6; omt 370 green, sentinel 1784, harnessc 0 err, e2e ×2; live rev46→47 (5/0/2) drift-free. Details @ FEATURE.md + test_report.md.
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
---


## Projects (synced by `uv run scripts/omt/project.py sync` — do not hand-edit)

| project | state | features |
|---|---|---|
| feature_kb_akb | draft | — |
| meta_harness_2 | active | feature_020.meta_harness_navigation, feature_021.meta_harness_think_anywhere, feature_022.meta_harness_think_anywhere_v2, feature_023.meta_harness_improvement, feature_026.omt_q_interrogative_first_ops |
| meta_harness_3 | active | feature_028.feature_scoped_gating |
| meta_harness_4 | complete | feature_037.tdd_testlist_prose_fallback |
| meta_harness_5 | active | feature_038.tdd_toolchain_aware |
| meta_harness_concurrent | active | feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency, feature_042.goal_net_synthesis, feature_043.meta_net_dashboard, feature_044.mined_behavioral_net, feature_045.work_md_net_driven, feature_046.omt_net_session_arg_whitelist, feature_047.wip_limited_pool, feature_048.wip_limited_pool, feature_049.session_start_menu |
| petri_net_library | active | feature_031.petri_net_library |
| petri_net_studio | active | feature_032.petri_net_format, feature_033.petri_net_io, feature_034.studio_v1_editor, feature_035.studio_v2_analysis, feature_036.studio_v3_graph |
| project_lifecycle | active | feature_030.project_lifecycle |
| rag_v2 | active | feature_027.rag_v2, feature_029.rag_v2_slash_commands |
| workflows | draft | — |

---


## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md; pre-2026-08-23 rotated to WORK_ARCHIVE.md):
- feature_032..feature_036 (petri_net_format/io, studio_v1/2/3) — DONE 2026-08-23→29 · details @ Tasks [x] rows + FEATURE.md/test_report.md + git log.

RECURRING GOTCHAS — 18 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd testlist behaviors:** JSON array canonical; newline/bullet prose auto-split by tdd/cli.py `_parse_behaviors` — no re-format required.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```