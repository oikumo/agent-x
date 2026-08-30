# Test report — feature_038.tdd_toolchain_aware (meta_harness_5)

> Date: 2026-08-29 · minor_feature (declaration-only artifact; tests live in `tests/scripts/omt/test_tdd_check.py`) · Declared from `.sandbox/meta_harness_5_idea.md` Proposal A · Resume: `.sandbox/pause_2026-08-29f.md`

## Verdict

**COMPLETED.** `omt_tdd` is now toolchain-aware — `.py` → pytest, `.ts/.tsx` → `npx vitest run <file>` from the resolved vitest project root. The pause's OPEN ITEM (wrong vitest `cwd`) is fixed and verified live; real RED (exit 1) and GREEN (exit 0) round-trips confirmed on real studio files; 6 new dispatch/project-root unit tests GREEN; full sentinel 1664 passed; harnessc build+check 0 errors; e2e receipt refreshed.

## OPEN ITEM resolution (vitest cwd)

- **Before:** `run_test` ran vitest with `cwd=str(test_path.parent)` → for `tools/petri-net-studio/tests/engine/analysis.test.ts` that was `tests/engine/`, which is NOT the vitest project root → bogus exit 1 / "no tests matched" that broke RED/GREEN truth.
- **Fix:** new `_find_vitest_root(test_path)` walks up from the test file toward an ancestor with a `package.json` declaring a `vitest` dependency (or a `vitest.config.*` marker), falling back to `test_path.parent`. Verified it resolves all real studio test files to `tools/petri-net-studio/`.
- **Design hardening:** vitest runs the **whole file** (dropped the `-t <name>` filter). Vitest treats `-t` as a regex — an unmatched name (regex-special chars, or unknown `::Class::method` that doesn't exist in vitest) returns exit 0 ("N skipped") = FALSE green/red. The established studio RED/GREEN practice (features 034/035/036, A11/B11/C10) already ran the whole file, so this is both safer and backward-compatible.

## Live verification (real studio files, `uv run scripts/omt/tdd_check.py`)

| Command | Result |
|---------|--------|
| `start --test-node "tools/petri-net-studio/tests/engine/model.test.ts"` (passing) | `ok:false, state:red, verified:false, exit_code:0` — "already passes" branch (was pytest exit-4 "file not found") |
| `start` on a temp failing vitest file | `ok:true, state:red, verified:true, exit_code:1` — genuine RED, no false AST rejection (`.py`-only guard) |
| `green --test-node "tools/petri-net-studio/tests/engine/model.test.ts"` | `ok:true, state:green, verified:true, exit_code:0` |
| `run_test` on `.py` node (regression) | `exit_code:0` (pytest path unchanged) |

`_find_vitest_root` resolves: `analysis.test.ts`, `model.test.ts`, `gallery.test.ts` → all `tools/petri-net-studio`.

## Scope recap (what was changed)

- `scripts/omt/tdd/state.py` — `_find_vitest_root(test_path)` + `run_test(test_node, timeout)`; the vitest branch runs the WHOLE file from the resolved project root (no `-t`). `.ts/.tsx` → vitest, everything else → `run_pytest(...)` (unchanged).
- `scripts/omt/tdd/cli.py` — `cmd_start`/`cmd_green`/`cmd_refactor` call `run_test` (was `run_pytest`); Python-AST true-red/summary/anti-pattern block in `cmd_start` guarded to `.py` suffix only (Vitest targets skip AST → non-zero exit = valid RED); error wording "❌ pytest error" → "❌ test error".
- `scripts/omt/tdd/gates.py` — `cmd_after_edit` REFACTOR-revert check calls `run_test`; `run_pytest` import removed.
- `tests/scripts/omt/test_tdd_check.py` — `TestRunTestDispatch` ×6 (py→pytest, ts→vitest-from-root, tsx→vitest, unknown→pytest, root-discovery skips non-vitest package, root-fallback-to-parent) + `test_after_edit_revert_branch_is_revert_on_driven` updated to patch `run_test` (gates.py renamed `run_pytest`→`run_test`).
- Doc sync (same session): `.meta/META_HARNESS.omt` ×2 records (`@doc gotcha.tdd_toolchain` new, `@tool omt_tdd` desc), `.opencode/lib/enforcer/tdd_hats.ts` TS fallback seed (drift-pin), `tests/scripts/omt/test_omt_docs_drift_pins.py` `WORK_BUDGET` 5120→5632 synced to `.omt @budget work_md` (stale from pause), WORK.md gotcha count 17→18.

## Suite numbers

- `tests/scripts/omt/test_tdd_check.py`: **49 passed** (43 prior + 6 new dispatch rows).
- `tests/scripts/omt/`: **256 passed** (harness suite, incl. drift-pins 12/12).
- Full sentinel `uv run pytest`: **1664 passed, 0 failures**.
- `harnessc build` OK (252 records → 5 projections) · `harnessc check` **0 errors** · e2e receipt refreshed (`test_omt_harness_e2e.py` 1 passed).

## Note

- Receipt round-robin respected across all harness-surface edits (state.py, test_tdd_check.py, META_HARNESS.omt, tdd_hats.ts, WORK.md, drift-pins) — one edit per file per e2e receipt, e2e refreshed between edits.
- `git status` at completion: uncommitted (user commits separately, per repo convention).
