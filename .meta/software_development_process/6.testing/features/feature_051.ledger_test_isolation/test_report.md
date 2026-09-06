# Test Report — feature_051.ledger_test_isolation (A1)

> meta_harness_6 Wave 1 / A1 · Testing 2026-09-06 · HEAD = feature_051 WIP (uncommitted)

## Acceptance criteria → results

| Criterion (PROJECT.md A1) | Result |
|---|---|
| `OMT_LEDGER_PATH` honored by TS shared lib | ✅ `.opencode/lib/omt_shared.ts` `ledgerPath()`; pinned by `TestTsClientHonorsEnvOverride::test_ledger_path_and_append_follow_env` (bun probe: path + append follow env; repo default untouched) |
| `OMT_LEDGER_PATH` honored by `tdd/state.py` | ✅ already honored (import-time read); pinned in BOTH directions by `TestPythonClientHonorsEnvOverride` (empty tmp ledger → `allowed:true`; fabricated tdd-active ledger at env path → `allowed:false`) |
| Harness tests run on tmp ledger | ✅ feature_016 `_run_tdd` + `TestTddCheckSubprocess` subprocesses run with `OMT_LEDGER_PATH`/`OMT_SNAPSHOT_DIR` → fresh tmp ledger per call |
| KNOWN_SUITE_FAILURES deleted | ✅ `frozenset({})` — permanently empty; shape-pinned by `test_ledger_rotation.py::test_known_suite_failures_documented_shape` (len == 0) + `TestAllowlistPermanentlyEmpty` |
| Full suite green with zero allowlist entries | ✅ **1846 passed, 0 failed** (2 deselected opencode_live) — 64.7s |
| GOTCHA_TDD_ENV_FLAKY demoted to ordinary doc | ✅ `@doc tdd.env_flaky_fixed` (tag `TDD_ENV_FLAKY_FIXED`); nav-indexed gotchas 18 → 17 |
| omt_q U10 surface intact | ✅ `known_suite_failures: []`, `parse_failed: false` (regex `[^}]*`); `TestOpStateKnownSuiteFailuresParse` green |

## Runs

| Command | Result |
|---|---|
| `uv run pytest tests/features/feature_051.ledger_test_isolation/ tests/scripts/omt/test_ledger_rotation.py tests/scripts/omt/test_tdd_check.py::TestTddCheckSubprocess tests/features/feature_016.tdd_enforcement/test_tdd_enforcement.py::TestTddCheckCli -q` | 25 passed |
| `uv run pytest tests/scripts/omt/test_omt_q.py -q` | 14 passed |
| `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` (receipt refresh, round 1) | 1 passed |
| `uv run scripts/omt/harnessc.py check` | OK — 256 records, 0 errors |
| `uv run scripts/omt/harnessc.py build` | OK — 5 projections, all 12 budgets green |
| `uv run pytest -q -m "not opencode_live"` | **1846 passed, 0 failed** |
| react_screen trio stability (pre-change) | 3 passed × 3 repeats + isolated + full-suite runs |

## Previously-allowlisted tests — now un-tolerated and green

- `feature_018.react_screen::TestReactScreenPilot` ×3 — stably green (mock-leak fix); verified ×3 isolated + full suite.
- `test_tdd_check.py::TestTddCheckSubprocess::test_gate_returns_allowed_when_no_tdd` — hermetic; re-tightened to assert `allowed is True`/`tdd_mode is False` (deterministic).
- `feature_016::TestTddCheckCli::test_gate_no_tdd_allows_{everything,tests}` — hermetic; deterministic green even while a live TDD session is in-window (the historical failure trigger).

## Notes

- RED evidence: pre-change, the new TS-env test could not pass (`ledgerPath()` ignored env — the implementation gap this feature closes) and the emptiness pins asserted against a 6-member set; both flipped green only after the src edits in the same round.
- Non-goal honored: g.think / g.protect untouched; no gate added; net ceremony unchanged.
