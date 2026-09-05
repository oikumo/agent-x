# Feature 045: Work Md Net Driven

> **Status:** [x] Done (2026-09-05)
> **Created:** 2026-08-30
> **WORK.md task:** feature_045.work_md_net_driven

---

## Summary

WORK.md Tasks/Projects become a deterministic projection of the single-net
SSOT (rev-stamped render of probe/invariant) plus a proposal surface for
hand edits (md→net proposals through splice, D4) — completing the D16 SSOT
loop and serving as the D19 session-start menu.

## Scope (one sentence — what "done" looks like)

`sync.py` render/parse/propose + `omt_net{op:sync}` md directions ship with
round-trip conformance vectors green and WORK.md blocks rendering rev 43 deterministically.

## Task type

minor_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_045.work_md_net_driven/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_045.work_md_net_driven/analysis_001_net_md_contract.md` | [x] |
| Design | Design doc | `4.design/features/feature_045.work_md_net_driven/design_001_sync_md_spec.md` | [x] |
| Implementation | Impl notes | `scripts/omt/net/sync_md.py` + `state.py`/`cli.py` md branches (minor_feature, declaration only) | [x] |
| Testing | Test report | `6.testing/features/feature_045.work_md_net_driven/test_report.md` (6 sync_md vectors; net 98 green) | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
