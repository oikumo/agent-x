# Test report — feature_030.project_lifecycle

> Date: 2026-08-22 · Phase: Testing · Design: `4.design/.../design_001_project_lifecycle.md` + `operation_spec_001_project_lifecycle_ops.md` · Canonical design: `.projects/meta/project_lifecycle/PROJECT.md` (D1–D8)

## Verdict

**GREEN.** 20/20 feature goldens · 232 passed / 0 failed in `tests/scripts/omt/` (3 live-binary deselected) · full suite via `omt_tdd{op:done}` ✅ (2 KNOWN_SUITE_FAILURES tolerated, **0 regressions** vs the Programming-entry baseline) · `harnessc check` 0 errors (250 records) · `harnessc build` OK (5 projections) · e2e receipt fresh.

## Behaviors (testlist ❶–⓰ → goldens)

| # | Behavior | Golden |
|---|---|---|
| ❶–❻ | project.py new/link/log/close/sync + derive FSM | `TestProjectPy` (6) |
| ❼–⓫ | harnessc checks: structure · links · resume-block · status · manifest | `TestHarnesscChecks` (5) |
| — | new_feature.py --project (dry-run announces link) | `TestScaffoldLink` (1) |
| ⓰ | backfill create-record idempotent + header normalization | `TestBackfill` (1) |
| ⓬ | omt_phase design_doc → project_link origin:inferred, exactly once | `TestPhaseGateProjectHooks` (bun probes) |
| ⓭ | omt_complete ship-sync auto-block, idempotent; unlinked → note | same (4 probes total) |
| ⓮ | op=drift additive `project_drift` (stale-log, phantom-link, unlinked-project-backed, aging-draft); U3 pins intact | `TestOmtQProjectDrift` |
| ⓯ | omt_status Project line present/absent | `TestOmtStatusProject` (2) |

Sentinel: `tests/features/feature_030.project_lifecycle/test_project_lifecycle_goldens.py` re-exports the suite (20/20 via the sentinel; `conftest.py` carries the `env` fixture registration).

## TDD evidence

4 red→green cycles, node-consistent (GOTCHA_TDD_NODE honored): `TestProjectPy` (R1) → file node (R2) → `TestPhaseGateProjectHooks` (R3) → file node (R4+sentinel semantics). Genuine-RED verified per cycle (exit 1, runnable reds with lazy importlib). Harness-surface discipline: one edit per file per e2e receipt; multi-site TS insertions via sanctioned bash transforms; receipt refreshed per round.

## Live verification (real repo)

- Backfill executed: 7 homes adopted (`origin:backfill` create records), 9 feature links (meta_harness_2↔020–023/026, meta_harness_3↔028, rag_v2↔027/029, project_lifecycle↔030), 7 baseline log blocks, manifest `.projects/meta/META.md` generated, `feature_kb_akb` stray `.bak` removed, `workflows/` CURRENT_STATE.md stub created.
- All 6 investigation drift instances now mechanically caught: structure (workflows/ pair), `.bak`, stale-log (rag_v2's 3 missing ships → baseline blocks), status (meta_harness_3 iter-4 class → header==derived check), unlinked (027 class → inference), manifest (now GENERATED + checked).
- `harnessc check` on the real tree: **0 errors** post-backfill (before: 8 project errors by design).

## Post-done fix (correctness, goldens re-verified)

The ship-sync call site initially fired on **every** omt_complete — an Analysis-complete would write a premature "(auto — feature Done)" block. Guarded to terminal completions (`Testing`/`Done`) in phase_gate.ts; aligned the stale-log fold (omt_q.ts) + close guard (project.py) to terminal-phase semantics (legacy phase-less completes count as terminal). 20/20 re-run green; full omt dir 232/0 re-run green.

## Known limitations (accepted, v1.1 candidates)

- **No hot-reload (GOTCHA_TS_NO_RELOAD):** this session's loaded plugins predate R3/R4 — live omt_q/omt_status/omt_complete surfaces activate next session. The feature's own ship-block in the project_lifecycle log is therefore written via `project.py log` (same content, manual trigger).
- **iteration-log drift** requires git in the probe root (fail-open, omitted hermetically); covered by construction, not by golden.
- **link-after-close check** forgives links written during a closed period that was later reopened (documented fold simplification).
- **LSP noise** harnessc.py:420 is the pre-existing documented cluster (meta_harness_3 P3-11 deferral), untouched.
- `new_feature.py --project` real-path link is pinned via dry-run structural golden only (new_feature's module-level paths predate env-redirectability).
