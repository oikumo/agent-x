# EXECUTION — improvement003 / OPT-M (2026-08-01)

## Selected
OPT-M — Compact WORK.md DONE narratives (startup token diet); user-selected via the loop's
step-5 question.

## Changes
- `WORK.md`: 4 DONE narratives (L24 R4=406 B, L33 feature_024=619 B, L59 DSL=634 B,
  L61 T-024=1657 B — 3316 B total) compacted to one-liners + pointers (feature dirs /
  .sandbox plan / git log). Convention section gained: "DONE entries — one line + pointer;
  narrative is paid every session startup (CONV_WORK_DONE)".
- `.meta/META_HARNESS.omt` (ONE edit, harness-surface): new `@doc conv.work_done`
  (tags `CONV_WORK_DONE`, nav-indexed) + `@budget work_md` max 14336 → 8192 (payload
  documents the shrink). Corpus 242 → 243 records.
- `tests/scripts/omt/test_omt_docs_drift_pins.py`: `WORK_BUDGET` 14*1024 → 8*1024
  (deliberate budget change, same session as the .omt @budget change per `_budget_fail`
  guidance; canary via `omt_skip{scope:tests}`, precedent improvement002/OPT-B).
- Projections REGENERATED via `harnessc.py build` (never hand-edited).
- `.meta/META_HARNESS.md`: dated state note appended (loop step 7; stub is not compiled).

## Result
| Metric | Before | After |
|---|---|---|
| WORK.md (every session startup) | 7767 B | **5899 B (−1868 B ≈ −470 tok)** |
| `@budget work_md` | 14336 (54% used) | **8192 (72% used)** — future DONE bloat = compile error |
| .omt corpus | 242 records | 243 records (+1 @doc conv.*) |
| DONE-entry convention | none (narratives grew unbounded) | CONV_WORK_DONE in WORK.md Convention + nav-indexed @doc |

## Verification
- `harnessc.py check` — 243 records, 0 errors ✓
- `harnessc.py build` + `check --verify-projections` — no drift ✓
- `test_omt_harness_e2e.py` — pass (receipt refreshed after the harness-surface edit) ✓
- `tests/scripts/omt` — 116/116 ✓
- Full suite — 1062 passed + 3 failed (all 3 = allowlisted feature_018 KNOWN_SUITE_FAILURES) ✓
- `omt_nav "CONV_WORK_DONE"` — live after build (record in nav.index.jsonl, 252 records) ✓

## Process notes
- Phase: `omt_phase{task_type:refactor, phase:Programming, feature:improvement003.opt_m_workmd_diet}`.
- Round-robin recipe: .omt edited ONCE (both changes combined in a single contiguous edit),
  test pin edited once (different file, same round); ONE e2e receipt refresh afterwards.
  No second edit to any guarded file → no extra receipt cycles.
- WORK.md is not harness-surface (not in @var harness_paths) → no receipt friction there;
  its size IS compile-enforced via @budget work_md.
- Savings model: −1868 B now; the tightened budget (8192) prevents regression — the pre-OPT-M
  trajectory (WORK.md grew 12117 B → narratives accumulating) would have hit the old cap.
- No-commit-without-request honored: all changes left uncommitted for user review.

## Loop-step-7 reconciliation
As in improvement001/002: the loop's "update ./meta/META_HARNESS.md" predates R8 (retired stub;
truth = `.meta/META_HARNESS.omt` + projections). Honored by the dated note on the stub; the
machine-consumed state lives in the rebuilt projections. (OPT-I — fixing the loop prompt
itself — remains OPEN and was re-verified stale on this run.)
