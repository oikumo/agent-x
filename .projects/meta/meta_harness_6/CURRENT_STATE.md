# CURRENT_STATE: meta_harness_6

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-09-06 (iter 2 — Wave 1/F1 EXECUTED: feature_052.opencode_version_canary DONE; Wave 1 COMPLETE)

### Done

- **Resumed per `.sandbox/pause_2026-09-06.md`**: Quick Start + pause file read, tree verified CLEAN (user committed A1: `ec7bc5b`), overlap re-check clean (meta_harness_5 backlog all shipped/rejected, nothing on version canary), work_start fired (net rev 55→56).
- **F1 `feature_052.opencode_version_canary` SHIPPED** (minor_feature, Programming→Testing→Done):
  - `.omt`: `@var opencode_version_range : >=1.18.29,<1.19` (floor = live 1.18.29) + `@msg wrn_opencode_version sev=warn` (range baked via OPT-C; `{rel}` renders observed version) — 258 records, check 0 errors, orphan-wired via TS gateMsg.
  - `.opencode/lib/enforcer/nav_gate.ts`: `liveBinaryVersion()` + `versionInRange()` (exported, fail-open nulls) + WRN appended in `sessionBootstrap` firstEver branch (warn-only, zero steady-state token cost).
  - Canary suite `tests/features/feature_052.opencode_version_canary/test_version_canary.py` (17 tests: wiring pins, 14-case grammar matrix, live `opencode --version` fail-loud canary) + `test_version_range_fallback_matches_ir` source pin.
  - R6 bun probes: real impl matrix 9/9 + in-range silence w/ digest intact; fake 9.9.9 binary → exact WRN text end-to-end. Bun quirk found: execFileSync ignores runtime PATH mutation (set PATH at launch).
  - **Evidence: full suite 1866 passed / 0 failed (empty allowlist); build OK, all 12 budgets green (nav_index 63582/64000 — tight, Wave 3/B1 owns it); e2e receipt refreshed (round 1, 3 files).**
  - One mechanical failure fixed, not a regression: dashboard snapshot rev drift (work_start 55→56) → `net_snapshot.py` regen.
  - Artifacts: `5.implementation/.../implementation_notes.md` + `6.testing/.../test_report.md`.
- **Wave 1 COMPLETE (A1 + F1).** Re-baseline contract on future WRN/canary red: live smoke + full suite on the new binary → bump @var → rebuild → commit.

### In progress / Blocked

- _(nothing in-flight — feature_052 fully closed)_

### Next

1. **Wave 2 / C1 `net_gate_concurrency_predicate`** (minor_feature): overlap-check meta_harness_5 backlog → scaffold (takes number **053**) → work_start (if new session) → omt_phase → `@pred net_marking()` per evaluation §5 C1.
2. Then Wave 2 (C2, A4) — PROJECT.md §The program.

### Notes / context

- Working tree UNCOMMITTED (agent cannot git-commit): feature_052 changes (2 harness files + pins test + new test dir + 2 feature artifact dirs + project docs + net bundle rev 56 + snapshot regen) await user `git commit`.
- Net: rev 56, pool pending=0/active=1/done=6 — close with `work_complete` before pausing, or continue straight into C1.

---


## 2026-09-06 (iter 1 — Wave 1/A1 EXECUTED: feature_051.ledger_test_isolation DONE; session paused before F1)

### Done

- **Program execution started** (first session of the execution phase): work_start fired (net rev 53→54), meta_harness_5 backlog overlap-checked (clean — all its items shipped/rejected, no overlap with A1/F1), feature_051 scaffolded (`new_feature.py`, linked → project flipped draft→active), DG2 same-session obligation done (WORK.md prose reworded: deferred concurrency concept now "multi_session_concurrency (deferred, unnumbered)", number 051 reassigned to this program).
- **A1 `feature_051.ledger_test_isolation` SHIPPED** (minor_feature, Programming→Testing→Done):
  - `OMT_LEDGER_PATH` honored by BOTH ledger clients: `.opencode/lib/omt_shared.ts` `ledgerPath()` (process-level override, beats injected root) + `scripts/omt/tdd/state.py` (already honored; now pinned in both directions by tests).
  - Window-flaky gate probes hermetic: feature_016 `_run_tdd` + `TestTddCheckSubprocess` subprocesses run on fresh tmp ledgers (`OMT_LEDGER_PATH`/`OMT_SNAPSHOT_DIR`); the feature_016 pair is now deterministic; the test_tdd_check gate probe re-tightened to `allowed is True / tdd_mode is False`.
  - `KNOWN_SUITE_FAILURES` **permanently empty** (`frozenset({})` — literal shape kept for the U10 regex) + shape-pinned empty by `test_ledger_rotation.py`; omt_q U10 regex `[^}]*` → `known_suite_failures: []` is now a live invariant probe.
  - .omt: 4 records updated (`tdd.done_allowlist` zero-tolerance, `gotcha.done_reachable`, `gotcha.tdd_env_flaky` → **demoted** to `tdd.env_flaky_fixed` (root-caused; nav gotchas 18→17), `gotcha.tdd_node` teaching flipped to "do NOT grow").
  - react_screen trio verified stably green (×3 isolated + full suite) — un-tolerated with no code change.
  - **Evidence: full suite 1846 passed / 0 failed with an EMPTY allowlist; harnessc check 0 errors (256 records); build OK, all 12 budgets green; e2e receipt refreshed (round 1, one edit per file).**
  - Artifacts: `5.implementation/features/feature_051.../implementation_notes.md` + `6.testing/features/feature_051.../test_report.md` + `tests/features/feature_051.ledger_test_isolation/test_ledger_isolation.py` (4 tests).
- **Session closed cleanly**: net work_complete fired (rev 55, work_done=6), net_to_md synced, harnessc check green.
- Session-discovered gotchas embedded as TA: thoughts: omt_shared.ts (env-override-beats-root semantics) + net/sync_md.py (net_to_md sync consumes hand-added rows between `Pool:` and `## Projects` — durable pointers go after the Projects section; feature_050's DONE row was lost to this).

### In progress / Blocked

- _(nothing in-flight — clean pause; feature_051 fully closed)_

### Next

1. Read `PROJECT.md` §New Session Quick Start (updated → F1) + `.sandbox/pause_2026-09-06.md`.
2. **Wave 1 / F1 `opencode_version_canary`**: overlap-check meta_harness_5 backlog → scaffold `uv run scripts/omt/new_feature.py "opencode version canary" --type minor_feature --project meta_harness_6` (takes number **052**) → work_start → omt_phase → implement `@var opencode_version_range` + startup WRN + live-binary probe canary suite (GOTCHA_LIVE_BINARY recipe) per `.sandbox/meta_harness_6_evaluation.md` §5 F1.
3. Then Wave 2 (C1, C2, A4) — PROJECT.md §The program.

### Notes / context

- **Working tree is UNCOMMITTED** (agent cannot git-commit): all feature_051 changes + project docs + pause artifacts await user commit.
- The 3 baseline full-suite failures seen at session start were mechanical (net pool drift after work_start + dashboard snapshot rev 53→54) — fixed via net_to_md sync + `net_snapshot.py` regen; not regressions.
- Receipt round-robin honored: 9 files, ONE edit each, single e2e refresh (the .omt 4-record update ran as one sanctioned multi-site bash transform).

---


## 2026-09-05 (iter 1 — deep evaluation performed + program defined; ZERO execution)

### Done

- **Deep evaluation of the META HARNESS as a whole** (usage gains with vs without, for future opencode projects): architecture scorecard, ledger/archive metrics (327 phase / 266 skip / 173 complete / 696 think_consult), size split (~14K harness LOC vs ~23K app LOC), gotcha clustering (18 → 5 classes), economic model, tiered adoption recommendation (Tier 1/2/3).
- **Improvement options menu produced** (13 items: A1–A4, B1–B2, C1–C2, D1–D3, E1–E2, F1) with impact/cost/mechanism/sequencing.
- **Program created** (user: "create the new meta_harness_6 project … include all"): `project.py new` + PROJECT.md filled (waves, baseline, decision gates DG1–DG3, execution rules, success criteria) + this entry.
- **Evidence record saved:** `.sandbox/meta_harness_6_evaluation.md` (self-contained; PROJECT.md is the actionable distillation).

### In progress / Blocked

- _(nothing — program defined, nothing executed; next session starts Wave 1)_

### Next

1. Read `PROJECT.md` §New Session Quick Start → §Decision gates → §Execution rules.
2. Scaffold Wave 1 / A1: `uv run scripts/omt/new_feature.py "ledger test isolation" --type minor_feature --project meta_harness_6` — **this takes feature number 051** (DG2: reword the deferred "feature_051.multi_session_concurrency" WORK.md prose to "multi_session_concurrency (deferred, unnumbered)" in the same session).
3. `omt_phase{task_type:minor_feature, phase:Programming, scope:"harness tests run on isolated tmp ledger; KNOWN_SUITE_FAILURES deleted; full suite green"}` → execute per Execution rules (net work_start FIRST — g.net:35 live; receipt round-robin; canary ordering).

### Notes / context

- All Wave 1–4 items are `minor_feature`; Wave 5 D1 is `major_feature` (TDD auto-on, design doc). E1 analysis pass may be `docs`.
- Harness-surface discipline applies to every feature here (harness_paths + net_paths): fire work_start, ONE edit per file per receipt round, e2e refresh per round, harnessc check+build with budgets green.
- Check `meta_harness_5` backlog before each scaffold (Execution rule 5 — no re-implementation of its shipped items).
- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.

---

## 2026-09-05 (iter 0 — project created)

### Done

- Project home created (`project.py new`, state: draft).

### In progress / Blocked

- _(nothing)_

### Next

- <!-- superseded by iter 1 above -->

### Notes / context

- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.
