# CURRENT_STATE: meta_harness_4

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-29 (iter 0 — project created)

### Done

- Project home created (`project.py new`, state: draft) as **meta_harness_4** (meta_harness_3 slug already taken by `feature_028.feature_scoped_gating`).
- PROJECT.md written — **declaration only** of the single improvement from `.sandbox/meta_harness_3_idea.md` (proposal #10: prose fallback `_parse_behaviors` for `omt_tdd testlist` at `scripts/omt/tdd/cli.py:68`). No implementation executed (per user instruction).

### In progress / Blocked

- _(nothing)_ — project declared, not executed.

### Next

- Execute the improvement: declare the feature (`new_feature.py "tdd_testlist_prose_fallback" --type minor_feature --project meta_harness_4`), implement `_parse_behaviors` in `scripts/omt/tdd/cli.py`, extend `tests/scripts/omt/test_tdd_check.py`, same-session doc sync (`.omt` ×2 records + `WORK.md` gotcha + 16→17 count fix), `harnessc.py build` + e2e receipt.

### Notes / context

- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.
- Key evidence: failure repro `uv run scripts/omt/tdd_check.py testlist --behaviors "Write a test" --feature test.xyz` → `{"ok": false, "error": "Expecting value: line 1 column 1 (char 0)"}`; `--feature` is required (`cli.py:412`).
