# feature_054.small_task_fast_path — Implementation Notes

**Wave 2 / C2 of meta_harness_6** · minor_feature · 2026-09-06 · Programming phase.

## What shipped

C2 cuts small-task ceremony to ONE process call without weakening the hard
gates (evaluation §5 C2; `.sandbox/meta_harness_6_evaluation.md`):

1. **Fast path** — a `bug_fix`/`test` `omt_phase` record satisfies g.nav +
   g.kb in that ONE ledger write. Minor/major/new_screen stay hard
   (latest-phase-wins: a later non-fast-path declaration turns it off).
2. **Narrowed tests-canary auto-unlock** — the declared feature's OWN test
   dir (`tests/features/<feature>/`, full slug or `feature_NNN` short form)
   is auto-approved while its feature-scoped TDD RED is active. Bootstrap
   (testlist / no RED), other features' dirs, and `tests/scripts/` still
   require the explicit `omt_skip{scope:"tests"}` canary.
3. **Guardrails** — g.think / g.protect untouched (pinned by tests).

## Mechanism (single mechanism by design)

- `session_state.ts` — `FAST_PATH_TASK_TYPES = {bug_fix, test}` +
  exported `hasFastPathUnlock(session)`: latest-PHASE-wins selection
  (session-matched preferred, else window-recent — mirrors
  `getActiveUnlock`'s shape but ignores skips), then task-type membership.
- `gate_driver.ts` — `SESSION_FLAGS.nav_used`/`kb_consulted` OR in
  `hasFastPathUnlock(ctx.session)`; the specialized `g.nav` impl (which
  bypasses `requires=`/SESSION_FLAGS) feeds it into the `navUnlock` slot of
  `navGateDecision`.
- `receipt_guard.ts` — `guardTestsPath` gains the narrowed branch after the
  TDD first branch: `activeFeatureFor` (unlock feature, else latest
  session/window phase-with-feature) + `isOwnTestDir` (slug / short-form
  prefix match; `feature_054evil` does NOT match — the separator matters)
  + `isFeatureRedActive` (feature-scoped tdd records: latest is `red`).
- `phase_gate.ts` — comment-only at the ledger write. **Deliberately NO
  in-memory flag flip**: the ledger record is the single mechanism (ledger
  reads are fresh per gate call, so the write is immediately visible), and
  sticky in-memory flags would keep `kb_consulted=true` after a later
  `major_feature` declaration — a guardrail violation.

## Design decisions

- **RED granularity is feature-scoped, not session-tdd_mode-scoped**
  (`isFeatureRedActive`): `omt_complete`'s Programming→Testing advance
  writes a tdd-less phase record, which would strand own-dir test edits
  mid-TDD if the fast path required session `tdd_mode`. Feature-scoped RED
  (mirrors `tdd/state.py _tdd_records`) keeps the value scenario working;
  the narrowed guardrails (own dir + RED only) are intact.
- **Skips are not the fast-path authority** — phase records are; a
  `omt_skip{scope:"tests"}` after a bug_fix phase neither grants nor
  revokes the fast path (it keeps its own legacy `tests_approved`
  semantics).
- **g.nav impl** needed the explicit fix: specialized impls never evaluate
  `requires=`, so a SESSION_FLAGS-only change would have been dead code
  for g.nav (round-2 catch).

## Files (3 receipt rounds, one edit per harness file per round)

- `.opencode/lib/enforcer/session_state.ts` — FAST_PATH_TASK_TYPES + hasFastPathUnlock (r1, rewritten r3)
- `.opencode/lib/enforcer/gate_driver.ts` — SESSION_FLAGS fast path + g.nav impl (r1, r2)
- `.opencode/lib/enforcer/phase_gate.ts` — fast-path note, no flag flip (r1, reverted r3)
- `.opencode/lib/enforcer/receipt_guard.ts` — narrowed canary (r1, tightened r2)
- `.meta/META_HARNESS.omt` — C2 notes on g.nav/g.kb/g.tests + narrowed TDD_BOOTSTRAP doc (r1)
- `tests/scripts/omt/test_omt_harness_e2e.py` — check 14 (receipt-exempt)
- `tests/features/feature_054.small_task_fast_path/test_small_task_fast_path.py` — 10 tests (new dir, canary skip logged)

Multi-site transforms ran as sanctioned bash scripts (GOTCHA_RECEIPT_ROUND_ROBIN);
harnessc check 0 errors (259 records), build OK, all 12 budgets green
(nav_index 63719/64000 — tight, Wave 3/B1 owns it).

## Evidence

- Feature suite: 10/10 (static pins + 3 bun probes against the real TS
  modules — hasFastPathUnlock matrix, guardTestsPath scenarios,
  runBeforeGates full-chain nav+kb).
- Full suite: **1887 passed / 0 failed** (empty allowlist), e2e green.
- bun build clean for all touched enforcer modules.
