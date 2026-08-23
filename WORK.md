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

- [x] **feature_034.studio_v1_editor** — DONE 2026-08-23: `tools/petri-net-studio/` (petri_net_studio #3): Vite+React+TS studio — TS engine port (model+io, golden byte-parity), zustand store, React Flow edit/simulate UI, import/export, independence lint, static build; Vitest 170/170 + tsc clean; 4 manual red→green cycles (A11) + pytest sentinel. Details @ FEATURE.md + test_report.md.
- [x] **feature_033.petri_net_io** — DONE 2026-08-23: `src/agentx/model/petri_net/io.py` (petri_net_studio #2): net_to_json/net_from_json/document_from_json — L1+V1–V6 validation, typed errors, canonical bytes, layout verbatim; stdlib-only, library untouched. 59 tests @ `tests/model/petri_net/test_io.py`.
- [x] **feature_032.petri_net_format** — DONE 2026-08-23: `petri-net-json` v1 in `shared/petri-net/` (petri_net_studio #1): FORMAT.md spec (V1–V6 validation, semantics by reference, canonical §8, versioning §9), JSON Schema 2020-12, 3 canonical examples, `shared/META.md`; 32/32 validation checks. Details @ FEATURE.md.
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [ ] **feature_002.rag_retrieval_augmented_generation**
---


## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023 meta-harness (F14-F17) · feature_tui_dark_mode (`k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (28 bx/37 tests) — **PAUSED 2026-08-02** · feature_kb_akb (UNIFIED IDX 437 recs; AST+curated+overlay; omt_kb_nav cap+truncate; g.kb gate + kb_bootstrap inject; 21/21 test_kb_*) — DONE 2026-08-08 · feature_025 deepagent context opt (create_deep_agent + middleware stack) — DONE 2026-08-08 · feature_026 omt_q interrogative layer (3 ops state/plan/drift + runBeforeGatesDry additive; 9 tools in IR; 14 golden + 14 sentinel) — DONE 2026-08-09 · feature_028 feature-scoped gating (meta_harness_3 Phase-A: P1-1/P1-2/P1-3/P3-8/T1; op=state 44KB→2.7KB) — DONE 2026-08-16 · feature_029 rag_v2 slash commands (hybrid grammar; streamed tool activity; tool rename) — DONE 2026-08-16 · bug_fix.rag_v2_ingestion_persist (_persist no-op → real Chroma; /chroma drift removed; 6 tests) — DONE 2026-08-16 · bug_fix.help_command_deepcopy_thread (help crash: get_commands deepcopy hit unpicklable _thread.lock; now shallow copy; 2 tests) — DONE 2026-08-16 · feature_031 petri_net_library (model+analysis, exact rational invariants, coverability v2 stub; 99 tests) — DONE 2026-08-23 · feature_032 petri_net_format (petri_net_studio #1; shared/petri-net/: FORMAT.md V1–V6+canonical §8, JSON Schema, 3 examples; 32/32 checks) — DONE 2026-08-23 · feature_033 petri_net_io (io.py: loads/dumps petri-net-json v1, L1+V1–V6 typed errors, canonical bytes, layout verbatim; 59 tests; suite 1639) — DONE 2026-08-23 · feature_034 studio_v1_editor (tools/petri-net-studio/: TS engine port + store + React Flow UI, golden byte-parity, independence lint, static build; Vitest 170/170; manual red→green A11 + pytest sentinel) — DONE 2026-08-23.

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{op:nav, query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_tdd{op:done} blocked (recovery: omt_tdd{op:green} at the exact red node).
- **omt_tdd{op:testlist} behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT. Multi-site transforms: uv-run python script via bash (guards hook edit-tools only) — keep the same round discipline manually.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
