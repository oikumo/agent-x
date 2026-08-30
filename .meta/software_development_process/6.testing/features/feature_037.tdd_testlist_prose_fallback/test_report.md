# Test report — feature_037.tdd_testlist_prose_fallback (meta_harness_4)

> Date: 2026-08-29 · minor_feature (declaration-only artifact; tests live in `tests/scripts/omt/test_tdd_check.py`) · Declared from `.sandbox/meta_harness_3_idea.md` proposal #10 · Resume: `.sandbox/pause_2026-08-29.md`

## Verdict

**COMPLETE — prose fallback shipped: `_parse_behaviors` in `scripts/omt/tdd/cli.py` accepts JSON array / JSON string / bullets / numbered lists; 11/11 parser smoke + CLI success criteria verified; `TestParseBehaviors` ×10 rows GREEN; full sentinel 1658 passed; harnessc build+check 0 errors; e2e receipt refreshed.**

## Scope recap (what was changed)

- `scripts/omt/tdd/cli.py` — `import re`, `_BULLET_RE`, `_parse_behaviors(raw)`; `cmd_testlist` calls `_parse_behaviors(args.behaviors)` (was `json.loads`). Purely additive: JSON-array callers unchanged.
- `tests/scripts/omt/test_tdd_check.py` — `TestParseBehaviors` ×10 parametrized rows (Before/After table + hardening). Existing JSON-array fixtures untouched.
- Doc sync (same session): `.meta/META_HARNESS.omt` ×3 records (`@hat tdd.testlist`, `@doc gotcha.testlist_json`, `@tool omt_tdd`), `.opencode/lib/enforcer/tdd_hats.ts:25` TS fallback seed (drift-pin), WORK.md scratchpad gotcha + 16→17 count fix.

## Before / After (CLI, `uv run scripts/omt/tdd_check.py testlist --behaviors <B> --feature feature_037.tdd_testlist_prose_fallback`)

| Input | Before | After |
|-------|--------|-------|
| `"Write a test"` (prose) | `{"ok": false, "error": "Expecting value: line 1 column 1 (char 0)"}` | `"ok": true, behaviors_count: 1` |
| `"- Write a test\n- Fix bug"` (bullets) | same JSON error | `behaviors_count: 2` |
| `"1. Write a test\n2. Fix bug"` (numbered) | same JSON error | `behaviors_count: 2` |
| `'["Write a test", "Fix bug"]'` (JSON array) | `behaviors_count: 2` | `behaviors_count: 2` (regression OK) |

## Parser matrix (`_parse_behaviors`, 11/11 smoke + unit table)

JSON array (unchanged) · JSON string → `[str]` (quotes stripped) · bullet `-`/`•`/`*` prose → split+strip · numbered `1.`/`2)` → split+strip · empty/omitted/`[]` → `[]` · empty-marker lines skipped (no phantom entries) · JSON scalar `123` → prose path `["123"]` · indented prose → stripped.

## Suite numbers

- `tests/scripts/omt/test_tdd_check.py`: **43 passed** (33 pre-existing + 10 new rows).
- `tests/scripts/omt/ -k "tdd"`: **51 passed**.
- `tests/scripts/omt/`: **250 passed** (harness suite).
- Full sentinel `uv run pytest`: **1658 passed, 0 failures** (KNOWN_SUITE_FAILURES allowlist path).
- `harnessc build` OK (251 records → 5 projections) · `harnessc check` **0 errors** · e2e receipt refreshed (`test_omt_harness_e2e.py` 1 passed).

## Note

- Receipt round-robin respected: 3 `.omt` records + WORK.md + TS seed were edited in ONE round at pause; this resume ran `harnessc build` → e2e refresh before any further harness-surface edits (none needed — housekeeping touched only project/FEATURE/PLAN/CURRENT_STATE artifacts).