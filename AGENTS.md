# AGENTS.md — System Rules

> GENERATED from .meta/META_HARNESS.omt — DO NOT EDIT; edit the source, then `uv run scripts/omt/harnessc.py build`.

> **STARTUP:** Read `WORK.md` (only) at session start; summarize current state in ≤ 15 lines (in-progress / blocked / next). All other docs on demand via `omt_nav` (op=nav|list_sections|cross_ref|quick_ref).
> **RUNTIME:** `uv` only (no bare `python`/`pip`/`pytest`). `src/` edits → `omt_phase` first.

## Enforcement
**ENF:** mechanical via .opencode/plugins/omt_enforcer.ts + lib/enforcer ×7 + opencode.jsonc; reference = .meta/META_HARNESS.omt (query: omt_nav)

## NEVER (blocked by gate)
- bash deny: `git commit *` `git push *` `python *` `python3 *` `pip *` `pip3 *` `pytest *`
- read deny: `*.env` `*.env.*`; toplevel deny: `webfetch`
- protected: `.env` `.env.*` (hard — no override) · `README.md` `uv.lock` `LICENSE` (`omt_skip{scope:"all"}` only)
- edit gates: harness-surface 2nd edit w/o fresh e2e receipt · `tests/` w/o canary approval · `src/` w/o `omt_phase` · TA:-carrying files w/o `omt_think_list` consult

## ALWAYS
`git status` → `META.md` per dir → `omt_phase` → `omt_complete` → `uv run pytest`

## Process (full rules on demand via nav)
- **§12 artifacts:** `bug_fix` `minor_feature` `refactor` `test` → declaration only · `major_feature` `new_screen` → + design doc on disk (`new_feature.py`) · `docs` → none
- **TDD (feature_016):** `major_feature`/`new_screen` @Programming auto-activates `omt_tdd{op: testlist → red → green → refactor → done}` — two-hats: RED tests/ only · GREEN/REFACTOR src/ only (auto-revert on break)
- **Tools:** 7 `omt_*` — catalog `omt_nav{query:"CMD_", tag_type:"CMD"}` · workflows `omt_quick_ref`
- **Nav gate (feature_020):** nav tools before grep/glob on docs (read + src/non-doc exempt) · **Think gate (feature_021):** TA: files need `omt_think{op:list}` consult (NOT skip-bypassable)
