# Refactor Plan: Live Opencode Tests + Source Pins Only

## Core Philosophy (from WORK.md lessons)
- **Runner fixtures fabricate shapes** that match buggy code → stay green while real runtime drifts (F14, BUG-A, BUG-B)
- **Only real-binary tests catch contract/path drift** - proven by `test_omt_live_opencode_guards.py`
- **Source pins** (static analysis of plugin .ts) catch regressions even when behavior tests skipped

## What to KEEP

### 1. Live Opencode Tests (Real Binary)
```
tests/scripts/omt/test_omt_live_opencode_guards.py    ← PRIMARY, expand this
```
- Drives REAL `opencode run --format json`
- Proves plugins auto-load, hooks fire, guards block
- Catches: BUG-A (before-hook contract), BUG-B (path drift), F14c (session.start never dispatched)

### 2. Source Pin Tests (Static Analysis of Plugin Source)
```
tests/scripts/omt/test_omt_enforcer_guard_source_pins.py   ← Static contract pins
tests/scripts/omt/test_opencode_sdk_contract.py            ← SDK hook shape pins
tests/scripts/omt/test_omt_harness_e2e.py                  ← Harness file coverage pins
```
- Check plugin source directly for: correct hook shapes, correct paths, sanctioned exports
- Fail immediately on source drift, no test runtime needed

### 3. MVC/TDD Unit Tests (Python script logic only)
```
tests/scripts/omt/test_mvc_check.py      ← Pure Python logic, no harness
tests/scripts/omt/test_tdd_check.py      ← Pure Python logic, no harness
```
- These test the Python linters/TDD engine, not the opencode plugin hooks

## What to REMOVE (All Node Runner Based)

### Feature 022 Tier Tests (4 files, 69 tests) - ALL REMOVE
```
tests/features/feature_022.meta_harness_think_anywhere_v2/
  test_omt_think_v2.py
  test_omt_think_v2_tier_bd.py
  test_omt_think_v2_tier_c.py
  test_omt_think_v2_tier_remainder.py
  _think_runner.mjs
  _think_gate_runner.mjs
```
- Use fabricated SDK shapes via node runners
- Didn't catch F14 before-hook bug (args on input vs output)
- Didn't catch BUG-B path drift (plugin vs plugins)

### Feature 023 Tests - REMOVE
```
tests/features/feature_023.meta_harness_improvement/
  test_omt_harness_improvement.py
  _plugin_surface_runner.mjs
```
- Behavior 3/4 (F14c live path) duplicate live opencode test
- Behavior 13 (hook wiring) duplicate source pin test
- Other behaviors: doc claims (keep if unique), export guards (source pins cover)

### Production Hook Effects - REMOVE
```
tests/scripts/omt/test_hook_effects_production.py      ← Just a pytest wrapper
tests/scripts/omt/test_hook_effects_production.ts      ← Node runner based
```

### Lifecycle E2E - REMOVE
```
tests/scripts/omt/test_omt_lifecycle_e2e.py            ← Isolated ledger, not real opencode
```

### Unified Runner Module - REMOVE (never completed)
```
tests/omt_runners/                                     ← Delete entirely
```

## New Test Structure

```
tests/scripts/omt/
├── test_omt_live_opencode_guards.py      # EXPAND - primary test suite
├── test_omt_enforcer_guard_source_pins.py # KEEP - static pins
├── test_opencode_sdk_contract.py          # KEEP - SDK contract pins
├── test_omt_harness_e2e.py                # KEEP - harness file pins
├── test_mvc_check.py                      # KEEP - Python unit tests
├── test_tdd_check.py                      # KEEP - Python unit tests
└── (remove all others)
```

## Expansion of test_omt_live_opencode_guards.py

Add tests for:
1. ✅ Plugin tool registration/callable (exists)
2. ✅ Plugin load no errors (exists)
3. ✅ Nav reminder + TA digest on first tool result (exists)
4. ✅ --pure disables plugin effects (exists)
5. ✅ Protected file edit blocked (exists - BUG-A)
6. ✅ Plugin file edit blocked by e2e receipt (exists - BUG-B)
7. ➕ **ADD**: think-gate blocks edit of thought-carrying file
8. ➕ **ADD**: omt_think_list consults clears think-gate
9. ➕ **ADD**: TDD two-hats gate (RED only tests/, GREEN only src/)
10. ➕ **ADD**: MVC++ post-edit gate blocks new hard errors
11. ➕ **ADD**: omt_phase/omt_complete phase transitions
12. ➕ **ADD**: omt_skip escape hatches (scope: src, tests, nav, all)
13. ➕ **ADD**: think-gate risk:-first weighting + STALE markers
14. ➕ **ADD**: Per-file consult granularity (C2)
15. ➕ **ADD**: Session isolation

## Migration Strategy

1. Delete all REMOVE files
2. Expand test_omt_live_opencode_guards.py with missing coverage
3. Verify source pin tests still pass
4. Run full suite: live tests + pin tests + mvc/tdd unit tests