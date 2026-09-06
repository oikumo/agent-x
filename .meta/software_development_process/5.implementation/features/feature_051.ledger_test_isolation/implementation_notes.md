# Implementation Notes — feature_051.ledger_test_isolation (A1)

> meta_harness_6 Wave 1 / A1 · task_type minor_feature · Programming 2026-09-06

## What changed (9 files, one edit each — receipt round-robin round 1)

| File | Change |
|---|---|
| `.opencode/lib/omt_shared.ts` | `ledgerPath()` honors `process.env.OMT_LEDGER_PATH` (process-level override, beats injected root; empty/unset → repo default). All ledger IO (`readLedger`/`appendLedger`/`readLedgerAll`/`rotateLedgerIfNeeded`) flows through it — TS/Python client parity. |
| `scripts/omt/tdd/state.py` | `KNOWN_SUITE_FAILURES = frozenset({})` — permanently empty. Literal kept as `frozenset({})` (not `frozenset()`) because the omt_q U10 regex pins the `frozenset({...})` shape. Comment documents the A1 decision + root causes. |
| `.opencode/plugins/omt_q.ts` | U10 extractor regex `[^}]+` → `[^}]*` so the empty literal parses (no `parse_failed` noise); `known_suite_failures` is now a live invariant probe. |
| `.meta/META_HARNESS.omt` | 4 records: `tdd.done_allowlist` rewritten (zero tolerance); `gotcha.done_reachable` allowlist mention updated; `gotcha.tdd_env_flaky` → `tdd.env_flaky_fixed` (DEMOTED from gotcha — root-caused); `gotcha.tdd_node` teaching flipped from "grow it + pin" to "pinned EMPTY — do NOT grow". |
| `tests/features/feature_016.tdd_enforcement/test_tdd_enforcement.py` | `_run_tdd` subprocesses run with `OMT_LEDGER_PATH`/`OMT_SNAPSHOT_DIR` → fresh tmp ledger (the window-flaky pair is now deterministic). |
| `tests/scripts/omt/test_tdd_check.py` | `TestTddCheckSubprocess` hermetic env for all 3 subprocess calls; the gate probe re-tightened to `allowed is True / tdd_mode is False` (deterministic now — was softened to shape-only while it depended on the real ledger). |
| `tests/scripts/omt/test_ledger_rotation.py` | shape-pin: `len(KNOWN_SUITE_FAILURES) == 0` (was `== 6` with 3+2 split) — mechanically enforces "and stays 0". |
| `tests/scripts/omt/test_omt_q.py` | U10 mirror-parse `[^}]*` + asserts `expected_ids == []` (A1 invariant). |
| `tests/features/feature_051.ledger_test_isolation/test_ledger_isolation.py` | NEW — 4 tests: Python client env override (both directions: empty tmp ledger → allowed; fabricated tdd-active ledger at env path → blocked), TS client env override (bun probe: `ledgerPath()` + `appendLedger` follow env, repo default untouched), allowlist empty. |

## Root causes of the 6 historical failures

- **Window-flaky trio** (test_tdd_check subprocess + feature_016 `test_gate_no_tdd_*` pair): the subprocesses read the REAL ledger with `--session ""` → 8h-window fallback → any live TDD session's `tdd_mode:true` phase record flipped the verdict. Fix: hermetic env redirect (above). The feature_051 test `test_fabricated_tdd_ledger_at_env_path_blocks` pins the mechanism in both directions.
- **feature_018 react_screen trio**: Textual/mock failures predating the harness; stably green since the scoped-`patch.object` mock-leak fix (documented in that file). Verified green isolated ×4 + full-suite ×2 this session. No code change needed — removed from tolerance.

## Evidence

- Targeted: 25 + 14 passed (changed files + omt_q).
- e2e receipt refreshed (round 1): 1 passed.
- `harnessc check` 0 errors / 256 records; `build` OK — all 12 budgets green (AGENTS.md unchanged; nav_index within budget).
- Full suite: **1846 passed, 0 failed** (2 deselected opencode_live) — with `KNOWN_SUITE_FAILURES` EMPTY.
- Gotchas: 18 → 17 nav-indexed (`GOTCHA_TDD_ENV_FLAKY` demoted to `TDD_ENV_FLAKY_FIXED`, root-caused).

## Deliberate non-changes

- `tdd/cli.py` untouched: with an empty set, `allowlisted` is always `[]` — the classification path is inert but harmless; removing it would spend a second edit round for zero behavior.
- `@var ledger_path` (.omt) unchanged: value is the default (non-overridden) path; the override contract is documented at both client implementations.
