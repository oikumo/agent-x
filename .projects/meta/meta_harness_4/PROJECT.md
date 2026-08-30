# PROJECT: meta_harness_4 — TDD testlist prose fallback (Meta Harness 3 single improvement)

> Status: **complete** · **v0.1 (2026-08-29)** — declared from the analysis `.sandbox/meta_harness_3_idea.md` (review of META HARNESS @ HEAD `5789125`). **DECLARATION ONLY — not executed.** Created by `project.py new`. Iterate freely (non-gated); spawn features with `new_feature.py "<name>" --type <tt> --project meta_harness_4`; log sessions in CURRENT_STATE.md (newest on top).

---

## New Session Quick Start

> One line: Meta Harness 4 ships the single, low-risk improvement that survived a 10-proposal harness review — a prose fallback for `omt_tdd testlist` behavior parsing (`scripts/omt/tdd/cli.py:68`) that also accepts JSON strings and numbered-list prose. Declared, not yet executed.

**Next:** execute the single improvement as a feature: `_parse_behaviors` in `scripts/omt/tdd/cli.py` (JSON array / JSON string / bullets / numbered lists) + unit tests in `tests/scripts/omt/test_tdd_check.py` + same-session doc sync (`.omt` gotcha/testlist hat records, `WORK.md` gotcha + 16→17 count fix) + `harnessc.py build` + e2e receipt refresh.

---

## Summary (one line)

**The single surviving improvement from the Meta Harness 3 review** — add a hardened prose fallback (`_parse_behaviors`) to `omt_tdd testlist` behavior parsing so agents can pass behaviors as JSON array, JSON string, bullets, or numbered lists instead of failing with `Expecting value: line 1 column 1 (char 0)`.

---

## Purpose

### What this project is

- The **declaration** of the one genuine DX win identified by the 10-proposal harness review (`.sandbox/meta_harness_3_idea.md`): proposal **#10 — prose fallback for `omt_tdd testlist`**.
- The change is a **Python-script edit only** (`scripts/omt/tdd/cli.py:68`), purely additive: JSON-array syntax keeps working unchanged; prose becomes a graceful input form. No opencode plugin edits, no gate changes, no `.ts` edits.
- It removes a **top-3 recurring agent failure mode** (`GOTCHA_TESTLIST_JSON`, named inline in `WORK.md`), which fires at least once per TDD session (every `major_feature`/`new_screen` auto-activates `omt_tdd{op:testlist}` at Programming).

### What this project is **not**

- NOT the other 9 proposals: 6 are already implemented (#1 receipt, #2 think, #3 kb, #6 tdd_after, #8 two-hats, #9 gate-message escapes) and 3 were correctly rejected as safety/complexity losses (#4 nav soft/hard, #5 budget removal, #7 tighten-to-actual). **Do not** soften `g.receipt`, remove TS-pinned budgets, tighten budgets, or re-add escape hints.
- NOT a gate change or a harness-surface redesign — the fix lands only in the Python parser (the agent-facing call chain `omt_tdd` TS tool → `tdd_check.py` shim → `tdd/cli.py:68` passes prose through verbatim, so the parser is the only place that can accept it).

---

## Scope & success criteria

**Scope (declared, not executed):**

1. `scripts/omt/tdd/cli.py` — add `_parse_behaviors(raw)` replacing `json.loads(args.behaviors)` in `cmd_testlist` (line 68):
   - JSON array → list (unchanged behavior)
   - JSON string (`"Write a test"`) → `["Write a test"]` (naive fallbacks would keep the quotes)
   - Bullet prose (`- `, `• `, `* `) → split lines, strip markers
   - Numbered prose (`1. `, `2) `) → split lines, strip markers (the format agents actually emit)
   - Empty/omitted/`[]` → `[]` unchanged (argparse default `"[]"` stays)
   - Empty behavior lines skipped (no phantom entries); JSON scalar falls to prose
2. `tests/scripts/omt/test_tdd_check.py` — unit tests covering the Before/After table in the idea doc (§ "Before vs After"); keep existing JSON-array fixtures untouched (regression).
3. Same-session doc sync (harness-surface round-robin, one edit per file per receipt):
   - `.meta/META_HARNESS.omt` `@doc gotcha.testlist_json` (L221) + `@hat tdd.testlist` (L89) rewording
   - `WORK.md` Agent Scratchpad gotcha line + stale "16 nav-indexed" → 17 count fix
   - `@tool omt_tdd` description (L264) can note "JSON array or prose" (propagates to tool-level description only)
4. `uv run scripts/omt/harnessc.py build` + e2e receipt refresh.

**Success criteria:**

- `uv run scripts/omt/tdd_check.py testlist --behaviors "Write a test" --feature <slug>` returns `"ok": true, "behaviors_count": 1` (previously `{"ok": false, "error": "Expecting value: line 1 column 1 (char 0)"}`).
- `omt_tdd{op:"testlist", behaviors:"- Write a test\n- Fix bug", feature:"<slug>"}` returns `behaviors_count=2`.
- JSON-array calls in tests/ledger fixtures pass unchanged; `uv run pytest tests/scripts/omt/ -k "tdd"` green.

**Explicitly out of scope (do NOT do):** soften `g.receipt` to warn, remove TS-pinned budgets, tighten budgets to actual+5%, soft/hard nav strikes, re-add escape hints to `@msg` records, or any arg-level hint edit in `tdd_hats.ts:28` (plugin edit out of scope — the hint describes the canonical JSON form; prose is a graceful fallback).

---

## Status

- [x] First linked feature (header flips draft → active mechanically) — `feature_037.tdd_testlist_prose_fallback` linked via `new_feature.py` (draft → active)
- [x] Implementation executed — `_parse_behaviors` prose fallback in `scripts/omt/tdd/cli.py` + `TestParseBehaviors` unit tests (43 file / 51 tdd-filtered passed) + doc sync (`.omt` ×3 records, TS fallback seed, WORK.md) — completed 2026-08-29, e2e receipt refreshed, full sentinel green, WORK.md row `[x]` DONE

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — Scope is exactly ONE improvement (#10):** the review verified 6 already implemented + 3 correctly rejected; re-litigating rejected items or expanding scope adds complexity for no quality gain. Evidence: `.sandbox/meta_harness_3_idea.md` §Proposal-by-Proposal Verdicts + executed repro of the failure (`{"ok": false, "error": "Expecting value: line 1 column 1 (char 0)"}`).
- **D2 — Python-side fix only:** the agent-facing chain passes prose verbatim (SDK array-coercion guard `tdd_hats.ts:44-47` only re-serializes JSON arrays); `cli.py:68` is the only place a fix can land. No `.ts`/plugin edits (arg-level hint stays JSON-only — acceptable).
- **D3 — Project slug `meta_harness_4`:** `meta_harness_3` already exists (active, `feature_028.feature_scoped_gating`); per user instruction the new project is named `meta_harness_4`.

---

## References

- `.sandbox/meta_harness_3_idea.md` — the analysis document (source of this declaration; non-gated)
- `.sandbox/meta_harness_3_plan.petri.json` — plan artifact (non-gated)
- `scripts/omt/tdd/cli.py:68` — the only runtime file the improvement modifies (`behaviors = json.loads(args.behaviors) if args.behaviors else []`)
- `scripts/omt/tdd_check.py` — compat shim (no modification needed)
- `.opencode/lib/enforcer/tdd_hats.ts:44-47` — SDK array-coercion guard (no modification needed)
- `tests/scripts/omt/test_tdd_check.py` — existing TDD-check suite (unit tests to extend)
- `.meta/META_HARNESS.omt` L89 `@hat tdd.testlist`, L221 `@doc gotcha.testlist_json`, L264 `@tool omt_tdd` — doc-sync records