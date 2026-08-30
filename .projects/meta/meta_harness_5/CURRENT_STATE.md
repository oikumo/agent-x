# CURRENT_STATE: meta_harness_5

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-30 (auto — feature_038.tdd_toolchain_aware Done)

- shipped: minor_feature · test report @ 6.testing/features/feature_038.tdd_toolchain_aware/test_report.md
- logged by omt_complete; expand by hand if resume needs more.

---


## 2026-08-29 (iter 2 — feature_038 completed: OPEN ITEM fixed, tests, doc sync, complete)

### Done

- **Resumed from** `.sandbox/pause_2026-08-29f.md` (feature_038.tdd_toolchain_aware).
- **Fixed the OPEN ITEM** (vitest `cwd`): new `_find_vitest_root(test_path)` in `scripts/omt/tdd/state.py` walks up to the vitest project root (package.json-with-vitest-dep / vitest.config.* marker). Verified it resolves all real studio test files to `tools/petri-net-studio/`.
- **Design hardening:** vitest runs the WHOLE test file (dropped the `-t <name>` filter — vitest treats `-t` as regex and an unmatched name returns exit 0 = FALSE green/red; whole-file matches the studio A11/B11 precedent).
- **Live RED/GREEN verified:** `start` on a real studio file → "already passes" (exit 0); on a temp failing file → `ok:true,state:red,verified:true,exit_code:1`; `green` → exit 0. `.py` pytest path unchanged (exit 0 regression).
- **Unit tests:** `TestRunTestDispatch` ×6 added to `tests/scripts/omt/test_tdd_check.py` (mock subprocess for .py/.ts/.tsx/unknown + `_find_vitest_root` discovery); `test_after_edit_revert_branch_is_revert_on_driven` updated to patch `run_test` (gates.py renamed `run_pytest`→`run_test`).
- **Doc sync:** `.meta/META_HARNESS.omt` `@doc gotcha.tdd_toolchain` (new) + `@tool omt_tdd` desc; `.opencode/lib/enforcer/tdd_hats.ts` TS fallback seed (drift-pin); `test_omt_docs_drift_pins.py` `WORK_BUDGET` 5120→5632 synced to `.omt @budget work_md` (stale from pause); WORK.md gotcha count 17→18.
- **Verification:** `tests/scripts/omt/` 256 passed; full sentinel **1664 passed, 0 failures**; `harnessc build` 252 records; `harnessc check` 0 errors; e2e receipt refreshed.
- **Bookkeeping:** FEATURE.md + test_report.md + PLAN.md filled; `omt_phase` Programming→Testing→Done; `omt_complete`.

### In progress / Blocked

- _(none)_ — feature_038 DONE.

### Next

- Any new `meta_harness_5` work requires a **fresh** harness review (`_idea.md`) at the new HEAD — the prior review's single proposal is now shipped.

### Notes / context

- Aborted optional `-t` filter due to a real correctness bug (vitest `-t` = regex; unmatched name → exit 0 false-pass) — documented in GOTCHA_TDD_TOOLCHAIN.

---

## 2026-08-29 (iter 1 — executed forward scope: fresh review + feature_038 declared + core impl, PAUSED)

### Done

- **Wrote fresh harness review** `.sandbox/meta_harness_5_idea.md` @ HEAD `544b40285` (audited current metrics: 208 @-records, 247 nav-index, 17 gotchas, 11 budgets; confirmed all 6 prior shipped + 3 rejected + #10 prose fallback shipped in feature_037).
- **Identified the single NEW genuine DX win (Proposal A):** `omt_tdd` is pytest-only — TypeScript/Vitest features (034/035/036) are forced into the documented A11/B11 manual red→green workaround. Verified live: `omt_tdd{op:red}` on a Vitest node returns `exit_code: 4` ("file not found"). Fix = toolchain-aware dispatch (pytest `.py` / vitest `.ts/.tsx`).
- **Declared `feature_038.tdd_toolchain_aware`** (minor_feature) via `new_feature.py` → linked to meta_harness_5 (draft → active).
- **`omt_phase` Analysis declared**; **core impl** in `scripts/omt/tdd/`: `state.py::run_test` (suffix dispatch), `cli.py` cmd_start/green/refactor use `run_test` + `.py`-only AST guard, `gates.py` cmd_after_edit uses `run_test`.

### In progress / Blocked

- **PAUSED (workflow pause_dev_for_resume_later)** — see `.sandbox/pause_2026-08-29f.md`.
- OPEN: `run_test` vitest subprocess `cwd` should be the vitest project root, NOT `test_path.parent` (bogus exit 1). Unit tests, doc sync (gotcha count 17→18), build + e2e, sentinel, completion pending.

### Next

- Resume from `.sandbox/pause_2026-08-29f.md`: fix vitest cwd → re-verify RED/GREEN live → unit tests in `test_tdd_check.py` → `.omt`/WORK.md doc sync → `harnessc build` + e2e + sentinel → `omt_complete`. (Meets the D4-recommended forward scope: fresh review produced + top DX win declared as a feature.)

### Notes / context

- D4 (no open backlog entries) resolved by producing NEW proposals (a fresh `_idea.md` at current HEAD) as the project's own recommended scope, rather than re-running the old 10.

---

## 2026-08-29 (iter 0 — project created + requirements backlog written)

### Done

- Project home created (`project.py new`, state: draft) as **meta_harness_5**.
- PROJECT.md written as a **forward-looking requirements backlog** transcribed from `.sandbox/meta_harness_3_idea.md` — all 10 review proposals tagged `shipped`/`reject` with remaining value + next action; **#10 (prose fallback) marked shipped** with pointer to `meta_harness_4`/`feature_037` (never re-implement here).

### In progress / Blocked

- _(nothing)_ — project declared (draft), not executed.

### Next

- Fresh session: read PROJECT.md §Requirements backlog — currently **no open entries** (all 10 done or rejected). Recommended forward scope: produce a **new** harness review `_idea.md` at the current HEAD to surface new requirement ideas, then declare the top genuine DX win as a feature via `new_feature.py "<name>" --type <tt> --project meta_harness_5`.

### Notes / context

- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.
- Decision (user): this is a requirements backlog, not the re-execution of #10 (already shipped in `meta_harness_4`).
