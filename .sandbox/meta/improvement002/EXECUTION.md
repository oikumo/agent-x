# EXECUTION — improvement002 / OPT-B (2026-08-01)

## Selected
OPT-B — Relocate WORK.md scratchpad gotchas into nav-indexed `@doc gotcha.*` records
(user-selected via the loop's step-5 question).

## Changes
- `.meta/META_HARNESS.omt`: new GOTCHA section — 16 `@doc gotcha.*` records
  (tags `GOTCHA_<NAME>`, queryable via `omt_nav "GOTCHA_"`); `@budget work_scratchpad`
  max 6144 → 3072 (payload documents the shrink).
- `WORK.md`: 3 gotcha blocks (16 bullets, ~4.3 KB) replaced by a pointer + top-3 inline
  (TDD node-granularity, testlist-JSON, receipt round-robin). Also removed the STALE
  "UNCOMMITTED HARNESS WIP" line — those files were committed in e4233ce; git tree clean.
- `tests/scripts/omt/test_omt_docs_drift_pins.py`: `SCRATCHPAD_BUDGET` 6*1024 → 3*1024
  (deliberate budget change, same session as the .omt change, per `_budget_fail` guidance);
  canary via `omt_skip{scope:tests}`.
- Projections REGENERATED via `harnessc.py build` (never hand-edited).
- `.meta/META_HARNESS.md`: dated state note appended (loop step 7; stub is not compiled).

## Result
| Metric | Before | After |
|---|---|---|
| WORK.md (every session startup) | 12117 B | **7767 B (−4350 B ≈ −1100 tok)** |
| Scratchpad | 5692/6144 B (93%) | **1342/3072 B (44%)** |
| .omt corpus | 226 records | 242 records (+16 @doc) |
| Gotcha access | auto-paid every session | on-demand `omt_nav "GOTCHA_"` (16/16 live, verified) |

## Verification
- `harnessc.py check` — 242 records, 0 errors ✓
- `harnessc.py build` + `check --verify-projections` — no drift ✓
- `test_omt_harness_e2e.py` — pass (receipt refreshed after the harness-surface edits) ✓
- `tests/scripts/omt` — 116/116 ✓
- Full suite — 1062 passed + 3 failed (all 3 = allowlisted feature_018 KNOWN_SUITE_FAILURES) ✓
- `omt_nav "GOTCHA_"` — returns all 16 records ✓

## Process notes
- Phase: `omt_phase{task_type:refactor, phase:Programming, feature:improvement002.opt_b_gotchas_to_nav}`.
- Round-robin recipe followed: 3 harness-surface files (.omt, WORK.md n/a — not harness-surface,
  test pin) edited one-edit-per-file in round 1; ONE e2e receipt refresh afterwards. No second
  edit to any guarded file was needed → no extra receipt cycles.
- Budget-failure risk retired: scratchpad was at 93% of a compile-enforced budget on an
  agent-edited file; headroom now 56%.
- Trade-off accepted (per OPT-B risk note): gotchas are no longer auto-seen each session;
  mitigation = top-3 inline + the pointer line + the standing nav tip in session bootstrap.
- No-commit-without-request honored: all changes left uncommitted for user review.

## Loop-step-7 reconciliation
As in improvement001: the loop's "update ./meta/META_HARNESS.md" predates R8 (retired stub;
truth = `.meta/META_HARNESS.omt` + projections). Honored by the dated note on the stub; the
machine-consumed state lives in the rebuilt projections. (improvement002 OPT-I proposes fixing
the loop prompt itself.)
