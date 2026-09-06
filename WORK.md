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
<!-- net_rev:57 -->
NEXT: none
Other enabled: none
Blocked: none
Resources: 5/5 free
Pool: pending=0 active=0 done=7 (places 12/15)
## Projects (synced by `uv run scripts/omt/project.py sync` — do not hand-edit)

| project | state | features |
|---|---|---|
| feature_kb_akb | draft | — |
| meta_harness_2 | active | feature_020.meta_harness_navigation, feature_021.meta_harness_think_anywhere, feature_022.meta_harness_think_anywhere_v2, feature_023.meta_harness_improvement, feature_026.omt_q_interrogative_first_ops |
| meta_harness_3 | active | feature_028.feature_scoped_gating |
| meta_harness_4 | complete | feature_037.tdd_testlist_prose_fallback |
| meta_harness_5 | active | feature_038.tdd_toolchain_aware |
| meta_harness_6 | active | feature_051.ledger_test_isolation, feature_052.opencode_version_canary, feature_053.net_gate_concurrency_predicate, feature_054.small_task_fast_path, feature_055.gate_preflight |
| meta_harness_concurrent | active | feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency, feature_042.goal_net_synthesis, feature_043.meta_net_dashboard, feature_044.mined_behavioral_net, feature_045.work_md_net_driven, feature_046.omt_net_session_arg_whitelist, feature_047.wip_limited_pool, feature_048.wip_limited_pool, feature_049.session_start_menu |
| net_enforced_harness | active | feature_050.net_as_gate |
| petri_net_library | active | feature_031.petri_net_library |
| petri_net_studio | active | feature_032.petri_net_format, feature_033.petri_net_io, feature_034.studio_v1_editor, feature_035.studio_v2_analysis, feature_036.studio_v3_graph |
| project_lifecycle | active | feature_030.project_lifecycle |
| rag_v2 | active | feature_027.rag_v2, feature_029.rag_v2_slash_commands |
| workflows | draft | — |

---


## Paused (resumable)

- [~] **meta_harness_6 program execution** — Wave 2 COMPLETE `feature_055.gate_preflight` DONE 2026-09-06 (A1+F1+C1+C2+A4 shipped → feature_051..055; suite 1902/0; net rev 57, pool done=7). NEXT: Wave 3/A2+A3 `skip_taxonomy_phase_hygiene` (takes number 056; then B1+B2 takes 057 — owns the tight budgets: tool_args 13B, nav_index 174B headroom). Resume @ `.projects/meta/meta_harness_6/CURRENT_STATE.md` (2026-09-06 iter 5 entry). ⚠ Working tree uncommitted — user commit pending.

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
