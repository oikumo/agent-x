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
- [~] **feature_036.studio_v3_graph** — PAUSED 2026-08-29 @ Programming (TDD cycle 0): scaffolded (petri_net_studio #5, major_feature); Analysis+Design DONE + operation_spec_001 written (gate unblocked) + omt_phase Programming accepted (TDD A11 — Vitest/omt_tdd mismatch declared in test report). Next: TDD Cycle 1 — markingFromKey export + analysis.test.ts additive → RED → GREEN. Resume: `.sandbox/pause_2026-08-29d.md`.
- [x] **feature_034.studio_v1_editor** — DONE 2026-08-23: `tools/petri-net-studio/` (petri_net_studio #3): Vite+React+TS studio — TS engine port (model+io, golden byte-parity), zustand store, React Flow edit/simulate UI, import/export, independence lint, static build; Vitest 170/170 + tsc clean; 4 manual red→green cycles (A11) + pytest sentinel. Details @ FEATURE.md + test_report.md.
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
---


## Projects (synced by `uv run scripts/omt/project.py sync` — do not hand-edit)

| project | state | features |
|---|---|---|
| feature_kb_akb | draft | — |
| meta_harness_2 | active | feature_020.meta_harness_navigation, feature_021.meta_harness_think_anywhere, feature_022.meta_harness_think_anywhere_v2, feature_023.meta_harness_improvement, feature_026.omt_q_interrogative_first_ops |
| meta_harness_3 | active | feature_028.feature_scoped_gating |
| petri_net_library | active | feature_031.petri_net_library |
| petri_net_studio | active | feature_032.petri_net_format, feature_033.petri_net_io, feature_034.studio_v1_editor, feature_035.studio_v2_analysis, feature_036.studio_v3_graph |
| project_lifecycle | active | feature_030.project_lifecycle |
| rag_v2 | active | feature_027.rag_v2, feature_029.rag_v2_slash_commands |
| workflows | draft | — |

---


## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md; pre-2026-08-23 rotated to WORK_ARCHIVE.md):
- feature_032 petri_net_format (shared/petri-net/ FORMAT v1 + schema + 3 examples; 32/32 checks) — DONE 2026-08-23 · feature_033 petri_net_io (io.py L1+V1–V6, canonical bytes; 59 tests) — DONE 2026-08-23 · feature_034 studio_v1_editor (TS engine port + store + React Flow UI, golden byte-parity, independence lint; Vitest 170/170) — DONE 2026-08-23 · feature_035 studio_v2_analysis (fraction.ts+analysis.ts exact port, 9 conformance vectors, no-overclaim AnalysisPanel; Vitest 245/245) — DONE 2026-08-29.

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```