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

- [x] **feature_035.studio_v2_analysis** — DONE 2026-08-29: `tools/petri-net-studio/` v2 (petri_net_studio #4): TS analysis port — fraction.ts exact rationals + analysis.ts (reachability/deadlocks/bounds/liveness/SCC/P-T-invariants; B2/B3 exact parity, B6 deterministic ordering) + conformance-vector generator (9 vectors @ `shared/petri-net/conformance/analysis-v1/`, byte-identical re-runs; D8 re-lock) + no-overclaim AnalysisPanel & store maxStates/analysisVisible (D10/B12); 4 manual red→green cycles (B11). Vitest 245/245, tsc clean, build + independence OK (15 files/43 imports) + preview smoke 200s; sentinel + pytest 1638 passed (2 known). Details @ FEATURE.md + test_report.md.
- [x] **feature_036.studio_v3_graph** — DONE 2026-08-29: major_feature studio v3 graph completed (7 cycles: markingFromKey export + analysis additive, projection 7/7, animation 8/8, store+gallery 56/56+8/8, UI styles.css §9 + build + preview smoke 200×3, conformance runner regenerate+byte-identical+10/10 Vitest suite, sentinel green); Vitest 274/274, tsc clean, build green, independence OK.
- [x] **feature_034.studio_v1_editor** — DONE 2026-08-23: `tools/petri-net-studio/` (petri_net_studio #3): Vite+React+TS studio — TS engine port (model+io, golden byte-parity), zustand store, React Flow edit/simulate UI, import/export, independence lint, static build; Vitest 170/170 + tsc clean; 4 manual red→green cycles (A11) + pytest sentinel. Details @ FEATURE.md + test_report.md.
- [x] **feature_037.tdd_testlist_prose_fallback** — DONE 2026-08-29: minor_feature (meta_harness_4): `_parse_behaviors` prose fallback in tdd/cli.py (JSON array/string/bullets/numbered) + TestParseBehaviors ×10; sentinel 1658 passed, harnessc 0 err, e2e refreshed. Details @ FEATURE.md.
- [x] **feature_038.tdd_toolchain_aware** — DONE 2026-08-29: minor_feature (meta_harness_5): omt_tdd toolchain-aware dispatch — `run_test` routes `.py`→pytest `.ts/.tsx`→vitest from resolved project root (`_find_vitest_root`; whole-file supersedes A11/B11 workaround) + `TestRunTestDispatch`×6 + GOTCHA_TDD_TOOLCHAIN; sentinel 1664 passed, harnessc 0 err. Details @ FEATURE.md + test_report.md.
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