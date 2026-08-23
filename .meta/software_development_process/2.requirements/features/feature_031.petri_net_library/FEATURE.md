# Feature 031: Petri Net Library

> **Status:** [x] Done (2026-08-23)
> **Created:** 2026-08-22
> **WORK.md task:** `- [~] **feature_031.petri_net_library**`
> **Project home:** `.projects/meta/petri_net_library/PROJECT.md` (scope LOCKED v1.1, 2026-08-22)

---

## Summary

A pure-Python, zero-dependency weighted Place/Transition Petri-net library in `src/agentx/model/petri_net/` with two separated layers: an execution/model layer (places, transitions, weighted arcs, canonical tuple markings, enabledness, atomic pure firing) and an analysis layer (BFS reachability, reachability graph, firing sequences, deadlocks, bounds, exact incidence matrix, P/T-invariants via pure-Python rational Gaussian elimination, transition liveness on complete finite graphs, Tarjan SCC) — all completeness-explicit (`complete`/`reason`, never overclaiming from truncated searches). It is the generic foundation that `feature_001.session_user_objectives_driven_by_Petri_Net` will later consume. Requirement anchor: `.meta/doc/petri_nets/petri_net_python_coding_agents.md` (v1 sections per project D-scope).

## Scope (one sentence — what "done" looks like)

Done when `src/agentx/model/petri_net/` (`model.py`, `analysis.py`, `coverability.py` stub, `errors.py`, `__init__.py`) plus real tests under `tests/model/petri_net/` (replacing the June placeholder stub) implement the v1 scope and pass the requirement doc's Definition of Done items 1–17 and 19 with the full suite green (§40-18 coverability = v2 stub).

## Task type

major_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_031.petri_net_library/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_031.petri_net_library/analysis_001_petri_net_library.md` | [x] |
| Design | Design doc | `4.design/features/feature_031.petri_net_library/design_001_petri_net_library.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_031.petri_net_library/implementation_001_tdd_cycles.md` | [x] |
| Testing | Test report | `6.testing/features/feature_031.petri_net_library/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
