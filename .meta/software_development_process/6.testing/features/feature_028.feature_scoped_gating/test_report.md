# Test report — feature_028.feature_scoped_gating (meta_harness_3 v1.2, Phase-A)

> Date: 2026-08-16 · TDD refactor (5 R9 receipt rounds) · Plan: `.projects/meta/meta_harness_3/PROJECT.md` (R1–R11, T1) · Resume anchor: `.sandbox/pause_2026-08-16.md`

## Verdict

**Phase-A build COMPLETE — 10/10 testlist behaviors GREEN; `omt_tdd{op:done}` ✅ (full suite, 2 KNOWN_SUITE_FAILURES tolerated); 217/217 `tests/scripts/omt/`; harnessc build+check 0 errors; e2e receipt fresh.**

## Rounds (R9 order, one receipt round per file)

| # | File | Items | Golden (RED→GREEN node) | Result |
|---|------|-------|--------------------------|--------|
| 1 | `scripts/omt/tdd/state.py` | P1-1 (R3/R11) feature-scoped TDD state | `test_tdd_feature_scoped_state.py::…::test_two_session_resume_preserves_tdd_state` | ✅ RED `'testlist'=='green'` → GREEN |
| 2 | `scripts/omt/tdd/gates.py` (+ state.py baseline tier) | P1-3 (R5) coverage-on-diff + P3-8 (R6) two-hats message | `test_validate_exit_coverage_on_diff.py::…::test_additive_edit_with_preexisting_untested_exits_clean` + `test_gate_two_hats_message.py::…::test_both_blocked_states_say_nothing_editable` | ✅ 2 REDs → 2 GREENs |
| 3 | `scripts/omt/tdd/cli.py` | P1-2 (R4/R10) done split + regression guard + P1-3 producer (cmd_start capture) + `baseline` subcommand | `test_done_baseline_regressions.py::…::test_regression_blocks_done` | ✅ RED (KeyError pre-split) → GREEN |
| 4 | `.opencode/lib/enforcer/phase_gate.ts` | R4 baseline capture at TDD Programming entry (fail-open) | `test_done_baseline_regressions.py::TestBaselineCapture::test_phase_gate_captures_baseline_at_programming_entry` (structural pin, feature_016 pattern) | ✅ RED → GREEN |
| 5 | `.opencode/plugins/omt_q.ts` (+ `.meta/META_HARNESS.omt` @tool desc) | T1 summary projection + `verbose` flag | `test_omt_q_state_summary.py::…::test_default_state_envelope_is_compact_summary` | ✅ RED (5KB+ default) → GREEN |

## The 10 behaviors → evidence

1. **P1-1 R11 two-session resume** — hermetic ledger, prior red+green + new-session phase-only → `get_tdd_state=="green"`, node preserved, `cycles==2` (was `testlist`/0 pre-fix). `test_tdd_feature_scoped_state.py` (3 tests).
2. **P1-1 mode/node feature-scoped** — same golden asserts `get_current_test_node`; `get_tdd_mode` intentionally session-phase-based (approved sketch); isolation + legacy-scope guards included.
3. **P1-3 additive edit exits clean** — synthetic repo: pre-existing untested `old_helper`/`legacy_render` + feature-added tested `new_featured` → `validate-exit` ok, `coverage_gaps==[]`.
4. **P1-3 protection preserved** — feature-added UNTESTED `new_featured` still blocks; gap names only the added method. Plus no-baseline → legacy full scan (D5 fallback pin).
5. **P3-8 R6 config-driven message** — testlist/done → "nothing editable — declare omt_tdd{op:red}…"; synthetic IR hat (`allow:""`) proves the branch reads HAT_RULES, not state names; red/green single-allow messages unchanged (characterization).
6. **P1-2 R4 regression blocks** — baseline `[DRIFT]`, current `[DRIFT, REGRESSION]` → done blocked, `repo_hygiene_passes:false`, regression named, drift not a blocker.
7. **P1-2 R10 drift tolerated** — baseline `[DRIFT]`, current `[DRIFT]` → done ok with drift triage note (node named).
8. **R4 baseline capture** — `cmd_baseline` returns failing node IDs (stubbed suite, hermetic); phase_gate.ts pin: capture call + `baseline_failures` on the phase record + scoped to `"Programming"` + fail-open.
9. **T1 default ≤2KB** — wide hermetic substrate (25 slugs, 12×300-char scopes, 4 invalid, 2 consults ×10 files, 10×400-char thoughts): envelope ≤ 2048B, counts+samples asserted. Live on this repo: **44,181B → 2,706B (−94%)**.
10. **T1 verbose byte-identical** — full dump restored (25 slugs, untruncated scopes, consult list, thought list); existing U8/U13 goldens migrated to `verbose:true` and pass with assertions UNCHANGED (byte-identity through the verbose path).

## Suite numbers

- `tests/scripts/omt/`: **217/217** (198 pre-feature + 19 new: 3 state + 4 coverage + 3 message + 7 done/baseline + 2 T1).
- Full suite via `omt_tdd{op:done}`: green, 2 KNOWN_SUITE_FAILURES tolerated (legacy path — this feature's own phase records predate the round-4 capture, exercising the D5 no-baseline fallback live).
- `harnessc build` OK (247 records → 5 projections) · `harnessc check` 0 errors · e2e receipt refreshed after every round (5 rounds + 1 guard-prescribed mid-round refresh).

## Design decisions taken in-build

- **Two-hats gate is `src/`-scoped** (g.phase `path_in(src/)`): harness-surface TDD cycles (this feature) are disciplined by the ledger ops + receipt guard, not the edit hats. The skip-shadows-phase observation (active skip unlock mutes the TDD deferral in guardSrcPath/guardTestsPath) is logged as a candidate finding for the evaluation — NOT fixed (out of the locked v1.2 surface).
- **First-RED capture** for the feature-baseline tier (R5 allowed Programming-entry OR first-RED; first-RED is Python-local and exactly pre-first-touch). Producer = `cmd_start`; consumer = `validate-exit`; storage `SNAPSHOT_DIR/feature_baseline/<feature>/<stem>.json`; first-write-wins.
- **`suite_passes` kept** in the done checklist as the conjunction of the two new halves — `omt_q.ts` U7 (`foldClosedViaSkip`) consumer byte-compatible; split fields additive.
- **T1 projects 3 collections** (decree_health + risky_thoughts + recent_consults) — measured live driver ranked risky_thoughts 31.6KB > recent_consults 5.9KB > decree_health 5.2KB; ≤2KB target impossible projecting decree_health alone.
- **Live default envelope 2,706B** (vs ~2KB target): the delta is actionable per-session scalars (stranded_red node IDs, KNOWN_SUITE_FAILURES list) — kept by design; the structural ≤2048B guarantee is pinned on the controlled substrate.

## Known limitations / deferred

- `modified`-method detection deferred (needs body-hash in `extract_public_methods`) — R5 recommendation, Phase-A ships added-only.
- feature_028's own validate-exit will full-scan (no baselines captured before round 3 shipped) — legacy strict path, safe.
- `.sandbox/pause_2026-08-16.md` bootstrap gap (testlist state allows no edits; omt_skip{tests} required) — candidate finding for the evaluation doc, only its message is in the v1.2 surface (P3-8 shipped).
