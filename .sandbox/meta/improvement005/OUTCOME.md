# OUTCOME — improvement005 / OPT-A: per-turn injection diet

Executed 2026-08-01. Fresh-start loop (no prior-iteration input); user-selected from IMPROVEMENT_OPTIONS.md.

## Changes (4 files, one edit each per receipt round-robin)

| File | Change | Saving |
|---|---|---|
| .opencode/lib/enforcer/nav_gate.ts | navReminderMsg 8-segment block → one-liner (kept "NAVIGATION TIP" literal for live-guard pin) | 489→155 B (−334/turn) |
| .opencode/lib/omt_shared.ts | thinkDigest tail folded into line 1; kept "omt_think_list" + "think-gate" tokens | 101→52 B (−49/turn) |
| scripts/omt/harnessc.py | AGENTS.md GENERATED header template (drift cmd dropped; lives in .omt header comment) | −93 B/turn |
| .meta/META_HARNESS.omt | @doc enforcement payload compressed (single source → AGENTS.md ENF line) | −42 B/turn |

**Total: −518 B per LLM turn** (≈26 KB over a 50-turn session). AGENTS.md 2097→1962 B (budget 2560 OK).

## Verification

- `harnessc check` 0 errors · `build` 5 projections · `check --verify-projections` OK (243 records)
- e2e `test_omt_harness_e2e.py` ✓ (receipt refreshed)
- `tests/scripts/omt/` 116/116 ✓ (incl. nav-tip budget pin 155≤512, digest cap pin, live opencode guards: "NAVIGATION TIP" + TA digest presence)
- Full suite: 1062 passed, 3 failed = KNOWN_SUITE_FAILURES (feature_018 react_screen ×3, allowlisted) → expected green

## Notes

- No behavior change: gate logic, budgets (nav_tip ≤512, digest ≤1024, agents_md ≤2560), and live-test contract literals all preserved.
- Step-6 interpretation: `./meta/META_HARNESS.md` does not exist; state file = `.meta/META_HARNESS.omt` (updated, projections regenerated — AGENTS.md is generated, never hand-edited).
- Next-loop candidates (unchosen options): OPT-B tool-schema diet (~400 B/turn), OPT-C WORK.md diet (~3 KB/session), OPT-D @derive pass, OPT-E integrity pack.
