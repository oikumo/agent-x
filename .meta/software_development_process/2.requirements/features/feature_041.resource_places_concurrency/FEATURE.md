# Feature 041: Resource Places Concurrency

> **Status:** [~] In progress
> **Created:** 2026-08-30
> **WORK.md task:** core 3/3 of `meta_harness_concurrent` (see `.projects/meta/meta_harness_concurrent/PROJECT.md` roadmap)

---

## Summary

Core 3/3 of the `meta_harness_concurrent` project (D16 SSOT). Makes concurrency
conflicts **structurally visible** in the single supervisor net: resource capacities
(`agent_attention`=1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`,
`e2e_receipt`) are modeled as complement/resource places whose token-conservation
invariants are verified mechanically via `place_invariants()`; the overlay's
`ports.resources` refinement wires feature subnets to those shared resource places;
and `project.py` / `new_feature.py` lifecycle events auto-trigger `omt_net{op:sync}`
so the net never silently lags reality (D12, proposal-only per D4). Builds on the
feature_040 splice/sync machinery (shipped); no gate/FSM change (D3), no `src/`
edits (D1), no runtime import of the library (D2).

## Scope (one sentence — what "done" looks like)

`omt_net{op:sync}` bootstrap materializes the five capacity resource places wired through `ports.resources`, `place_invariants()`-backed capacity verification surfaces conflicts/deadlocks on a ≥2-concurrent-feature scenario, lifecycle events auto-propose re-sync, and the full sentinel stays green.

**Deferred:** `synthesize` op → feature_042; WORK.md net projection → feature_045 (D17 promote-to-core decision at this feature's exit review); mined behavioral net → feature_044; dashboard → feature_043.

## Task type

minor_feature (declaration-only per §12; manual red→green, tdd_mode:false — same convention as feature_039/040)

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_041.resource_places_concurrency/` | [ ] |
| Analysis | Analysis doc | `3.analysis/features/feature_041.resource_places_concurrency/analysis_001_*.md` | [ ] |
| Design | Design doc | `4.design/features/feature_041.resource_places_concurrency/design_001_*.md` | [ ] |
| Implementation | Impl notes | `5.implementation/features/feature_041.resource_places_concurrency/` | [ ] |
| Testing | Test report | `6.testing/features/feature_041.resource_places_concurrency/` | [ ] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
