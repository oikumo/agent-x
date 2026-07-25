# Test Refactor Plan: feature_022 + feature_023 + tests/scripts/omt/

## Current State Analysis

### feature_022 Tests (4 files, 69 tests total)
- `test_omt_think_v2.py` - Tier A: 14 tests (A1-A4)
- `test_omt_think_v2_tier_bd.py` - Tier B1+D1: 17 tests
- `test_omt_think_v2_tier_c.py` - Tier C: 22 tests
- `test_omt_think_v2_tier_remainder.py` - Tier B2+E1+E2: 16 tests

### feature_023 Tests (1 file, 13 behaviors)
- `test_omt_harness_improvement.py` - Behaviors 2-5, 8-13

### tests/scripts/omt/ (8 files)
- `test_omt_live_opencode_guards.py` - 6 LIVE tests (slow, opencode_live marker)
- `test_opencode_sdk_contract.py` - 4 contract pin tests
- `test_omt_hook_effects_production.py` - Wrapper for TS production suite
- `test_omt_harness_e2e.py` - E2E receipt test
- `test_omt_lifecycle_e2e.py` - Full lifecycle test (12 tests)
- `test_mvc_check.py` - MVC linter unit tests (12 tests)
- `test_omt_enforcer_guard_source_pins.py` - Static source pins (7 tests)
- `test_tdd_check.py` - TDD engine unit tests (18 tests)

### Test Runners (3 separate files)
- `_think_runner.mjs` - omt_think tools + session-start + after-hook
- `_think_gate_runner.mjs` - think-gate helpers + after-hook/before-hook modes
- `_plugin_surface_runner.mjs` - export/hook surface inspection

---

## Problems to Fix

### 1. Redundant Tests
- **feature_023 behavior 13** (hook wiring) duplicates `test_omt_enforcer_guard_source_pins.py`
- **feature_023 behaviors 3/4** (F14c nav reminder + TA digest) duplicate what `test_hook_effects_production.ts` tests
- **test_omt_harness_e2e.py** and **test_omt_lifecycle_e2e.py** overlap in lifecycle coverage
- **test_omt_hook_effects_production.py** is just a pytest wrapper for a TS file

### 2. Fragmented Runner Files
- 3 runner files with overlapping responsibilities
- Each test file re-imports the same patterns
- Hard to maintain consistent SDK contract fixtures

### 3. Mixed Test Categories
- Unit tests (fast) mixed with LIVE tests (slow, real opencode)
- No clear separation in tests/scripts/omt/

### 4. feature_022 Tier Structure
- 4 separate files is fine for organization, but shared fixtures would reduce duplication
- Each test file has its own `_run_tool`, `_marker`, `_write_tmp` helpers

---

## Refactor Design

### Phase 1: Consolidate Test Runners
Create a **single unified test runner** at:
```
tests/omt_runners/
  __init__.py
  plugin_runner.py      # Unified node runner for all plugin tools
  mjs/
    think_runner.mjs    # omt_think tools (existing _think_runner.mjs)
    gate_runner.mjs     # think-gate helpers (existing _think_gate_runner.mjs)
    surface_runner.mjs  # plugin surface (existing _plugin_surface_runner.mjs)
```

### Phase 2: Reorganize tests/scripts/omt/
```
tests/scripts/omt/
  unit/                      # Fast unit tests (no opencode binary)
    test_mvc_check.py        # Keep as-is
    test_tdd_check.py        # Keep as-is
    test_opencode_sdk_contract.py  # Keep as-is
    test_omt_enforcer_guard_source_pins.py  # Keep as-is
    test_omt_harness_e2e.py  # Keep as-is (fast static checks)
  live/                      # Slow LIVE tests (real opencode binary)
    test_omt_live_opencode_guards.py  # Move here
    test_omt_lifecycle_e2e.py         # Move here (slow tests)
  production/                # Production hook effects (node/tsx)
    test_hook_effects_production.ts   # Move from wrapper
    test_hook_effects_production.py   # Keep as pytest entry
```

### Phase 3: Consolidate feature_022 Tests
- Keep 4 tier files (good organization by feature)
- Extract shared fixtures to `tests/features/feature_022.meta_harness_think_anywhere_v2/conftest.py`
- Shared helpers: `_run_tool`, `_marker`, `_write_tmp`, `_after_hook_batch`, etc.

### Phase 4: Prune feature_023 Tests
Remove from `test_omt_harness_improvement.py`:
- Behavior 13 (hook wiring) → covered by test_omt_enforcer_guard_source_pins.py
- Behaviors 3/4 (F14c live path) → covered by production hook effects tests
- Behavior 5 (doc claims) → keep (doc validation is unique)
- Keep behaviors 2, 8-12 (unique to feature_023)

### Phase 5: Remove test_omt_hook_effects_production.py wrapper
- The TS file `test_hook_effects_production.ts` is the real test
- The .py wrapper adds no value - remove it
- Update test_omt_harness_improvement.py to reference the TS suite directly if needed

---

## Test Count Impact

| Before | After | Change |
|--------|-------|--------|
| 69 feature_022 tests | 69 (same, better fixtures) | 0 |
| 13 feature_023 behaviors | ~8 unique behaviors | -5 removed |
| 8 tests/scripts/omt/ files | 8 (reorganized) | 0 moved |
| 3 runner files | 1 unified Python module + 3 .mjs | -2 Python wrappers |

---

## Migration Steps

1. **Create unified runner module** (tests/omt_runners/)
2. **Reorganize tests/scripts/omt/ directory structure**
3. **Extract feature_022 shared fixtures to conftest.py**
4. **Prune feature_023 test file**
5. **Remove test_omt_hook_effects_production.py**
6. **Update imports and paths in all affected tests**
7. **Run full test suite to verify nothing broken**

---

## Success Criteria

- [ ] All existing tests pass (105+ tests)
- [ ] No duplicate test coverage
- [ ] Clear separation: unit/ vs live/ vs production/
- [ ] Single shared fixture module for feature_022
- [ ] feature_023 tests only cover unique behaviors
- [ ] No wrapper test files that just call other test files