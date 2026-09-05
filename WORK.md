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

- [x] **feature_038.tdd_toolchain_aware** — DONE 2026-08-29: minor_feature (meta_harness_5): omt_tdd toolchain-aware dispatch — `run_test` routes `.py`→pytest `.ts/.tsx`→vitest from resolved project root (`_find_vitest_root`; whole-file supersedes A11/B11 workaround) + `TestRunTestDispatch`×6 + GOTCHA_TDD_TOOLCHAIN; sentinel 1664 passed, harnessc 0 err. Details @ FEATURE.md + test_report.md.
- [x] **feature_039.adaptive_net_engine** — DONE 2026-08-30: minor_feature (meta_harness_concurrent core 1/3): harness-owned net engine `scripts/omt/net/` (parity clones, D2 no-src-import, 9-vector conformance byte-parity) + `state.py` three-file bundle (sidecar+overlay, atomic saves w/ rollback, name rebase, `net_fire` ledger) + `cli.py` omt_net ops probe/fire/invariant (IDEA-002 v4 §5.0 closed enum; splice/sync/synthesize reserved→feature_040; §5.1 bootstrap ordering) + `net_check.py` shim + `@tool omt_net` registered (budgets 1536/2048) + `omt_net.ts` proxy; 37 net tests + 2 sentinel, full sentinel 1703 passed, harnessc 0 err, drift pins 12/12. Details @ FEATURE.md + test_report.md.
- [x] **feature_040.net_composition_supervisor** — DONE 2026-08-30: minor_feature (meta_harness_concurrent core 2/3): omt_net splice (add validate-all-then-apply · remove REBUILD + forbid/reroute/drain token policies · disable≡prefix-remove + overlay archive · undo ledger inverse-replay · repair realign) + sync (§5.1 bootstrap skeleton + deterministic proposal, never auto-applied D4) + derived overlay at every save (P10) + 9-vector conformance gate + omt_complete D7 fail-open drift hook; synthesize reserved→feature_042; budgets 1536→1792/2048→2304; REAL SSOT bootstrapped (rev 0, drift-free). 42 splice/sync/CLI + 68 net suite, sentinel 1736 passed, harnessc 0 err, pins 12/12. Details @ FEATURE.md + test_report.md.
- [x] **feature_041.resource_places_concurrency** — DONE 2026-08-30: minor_feature (meta_harness_concurrent core 3/3 — CORE COMPLETE): R1–R8 resource places — 5-place catalog cap=1 (IDEA-002 v4 §2.2: agent_attention/src_edit_capacity/tests_capacity/harness_surface_round/e2e_receipt), R2 attention claim/release arcs, R3 ports.resources refinement, R4 resource_report + invariant-envelope resources[]/conflicts[], R5 resync ONE add_resource_places proposal, R6 lifecycle auto-sync hooks (project.py ×5 + new_feature.py link), R8 zero TS/budget churn; dogfood REAL SSOT rev 0→1 (sync→splice, invariant green); 27/27 canonical, sentinel 1756 passed, harnessc 0 err, pins 12/12. Finding: omt_net.ts --session proxy bug → feature_046? (user); D17 feature_045 promotion open (user). Details @ FEATURE.md + test_report.md.
- [x] **feature_046.omt_net_session_arg_whitelist** — DONE 2026-08-30: bug_fix (meta_harness_concurrent): omt_net.ts per-op `OP_ARGS` argv whitelist mirroring cli.py subparsers (no `--session` for probe/invariant/synthesize; `max_states` probe-gated) + TA gotcha→why-note + 6 cross-source pins; sentinel 1756→1762, harnessc 0 err, e2e refreshed; live plugin check on next-session reload (cached plugin ran pre-fix code). Details @ FEATURE.md.
- [x] **feature_045.work_md_net_driven** — DONE 2026-09-05: minor_feature (meta_harness_concurrent core 4/4 — CORE COMPLETE): `sync_md.py` render/parse/propose + `omt_net{op:sync}` md directions (`--direction/--dry-run/--work-md`, net_to_md/md_to_net_propose) + `_write_md_section` rev-stamped Tasks block (NEXT/Other/Blocked/Resources per D19) + 6 round-trip vectors; net 98 green, pins 6/6, e2e 1/1, dogfood SSOT rev 43 dry-run (NEXT f001_start, 6 pending, 5/5 free); sentinel 1767 passed +1 flake (`test_nav_reminder_deferred`, passes isolated), harnessc 0 err. Details @ FEATURE.md + test_report.md.
- [ ] **feature_042.goal_net_synthesis** — optional phase-2 (scaffolded).
- [ ] **feature_043.meta_net_dashboard** — optional phase-2 (scaffolded).
- [ ] **feature_044.mined_behavioral_net** — optional phase-2 (scaffolded).
- [x] **feature_048.wip_limited_pool** — DONE 2026-09-05: minor_feature (meta_harness_concurrent): pool-aware net (sync empty on pool + pool info, 15-cap guard, pool holders/conflicts, Pool render line) + test_net_pool.py×10 + tombstone 047 + budget 8192; omt 364 green, sentinel 1778, harnessc 0 err, live rev45 pool 12 places drift-free. Details @ FEATURE.md + test_report.md.
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
| meta_harness_concurrent | active | feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency, feature_042.goal_net_synthesis, feature_043.meta_net_dashboard, feature_044.mined_behavioral_net, feature_045.work_md_net_driven, feature_046.omt_net_session_arg_whitelist, feature_047.wip_limited_pool, feature_048.wip_limited_pool |
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