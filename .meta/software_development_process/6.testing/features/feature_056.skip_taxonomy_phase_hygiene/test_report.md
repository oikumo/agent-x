# Test Report — feature_056.skip_taxonomy_phase_hygiene (Wave 3/A2+A3)

> meta_harness_6 · minor_feature · 2026-09-06 · full suite **1934 passed / 0 failed**

## Evidence

- **New suite** `tests/features/feature_056.skip_taxonomy_phase_hygiene/`: **32 passed**
  - `test_skip_taxonomy.py` (18): effective-purpose matrix (explicit/default/unknown/
    non-string), 7-day split incl. window edge + corrupt-ts fail-open, warning
    boundary (=5 quiet / 6 warns / zero never warns), wrapper hermeticity
    (warning-not-error, quiet week, missing ledger, zero-threshold disable),
    static pins (tool record taxonomy+args, @var value, @state semantics, TS seed
    sync, vocab+default, diet trims).
  - `test_phase_hygiene.py` (14): bun expiry matrix (6 asserts), C2 fast-path
    guardrail probe, shadow-kill pair (expired allows / in-window still blocks via
    the real `guardTestsPath`), tool behavior (validation/defaults/ledger fields/
    tombstone content), full status-plugin probe (counts + lines + one-calls),
    static pins (helpers, abandon branch, report markers, status read-only, no
    omt_status schema growth).
- **Pre-formal probes**: 19/19 green (12 smoke + 7 round-2 X/Y/resume incl. the
  resurrection catch that forced the retired-rule).
- **E2E**: check 16 added and green (`test_omt_harness_e2e.py` passed after every
  round; receipt refreshed: R1 → R2 → fixture-fix).
- **Full suite**: 1934 passed / 0 failed (1902 baseline + 32 new), empty allowlist.
- **TDD validate-exit** for the feature: `ok:true`, 0 dangling reds, 0 coverage gaps.
- **Budgets**: `harnessc check` 0 errors, all 12 green (tool_args 2271/2304,
  tool_schemas 1750/1792, nav_index 63900/64000 — the three tight ones held).
- **Build**: `harnessc build` OK, 260 records → 5 projections (incl. regenerated
  AGENTS.md/opencode.jsonc/ir/nav-index); `--verify-projections` green via
  `test_repo_projections_are_fresh`.
- **Bun syntax gates**: all three touched TS files bundle clean.

## Incidents during the run (all closed)

1. **U1 snapshot red** (`test_omt_q` + golden re-export): fixture's absolute
   2026-08-09 phase record went `Unknown` under the new expiry — correct new
   behavior, stale fixture. Refreshed to in-window relative timestamps (intent
   preserved). No other time-frozen fixture depends on timeless matching.
2. **Live guards red once, green on rerun** (`test_plugins_load_and_tools_execute`,
   ~200 s live-binary test): flaky, not a regression (no code changed between runs;
   final full suite green includes it).
3. **Round-2 resurrection catch**: abandoning the session's current phase resurrected
   the retired record as unlock → added `isRetiredByTombstone` (one retirement
   semantic for unlock/feature-phase/dangling/abandon-target) + X/Y/resume probes.

## Residual notes (not blockers)

- Live-ledger hygiene state after this session: 7-day evasion 0 (no check warning);
  dangling-expired count is nonzero (months of history) — the end-of-program ≤5
  target is Wave-4/5 remediation work, now visible per phase via `omt_status`.
- `hasFastPathUnlock`/`hasNavUnlock` keep session-matched timelessness (C2 owns
  those semantics — documented, probed unchanged).
- Tool-surface parity gap: see implementation_notes.md (no `omt_skip` in this
  session's tool surface; tests/ writes via the sanctioned bash path, fully logged).
