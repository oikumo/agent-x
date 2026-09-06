# CURRENT_STATE: meta_harness_7

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-09-06 (iter 4 — P0-1 preflight-on-declare DONE, Wave 0 3/4)

### Done

- **feature_062.preflight_on_declare DONE (minor_feature, Programming→Testing→Done):** the `omt_phase` success response now embeds the A4 preflight projection for the feature's own edit surfaces — tests-dir probe on Programming AND Testing, plus a src probe at Programming — ordered gates + clearing actions, the just-declared phase already visible (g.phase fires ✓), live session state (g.kb honest about consults), inert `$` (dry net verdict). Fail-open: no feature / non-edit phase (Analysis/Design/abandon) → no embed; an embed error never fails the declare.
- **Refactor:** the A4 projection core (CLEARING_ACTIONS, DRY_CAVEATS, buildPreflightCtx, whenPathMatches, preflightProjection, preflightLines) moved from `omt_status.ts` into a new `lib/enforcer/preflight.ts` — the shared home for the `omt_status{op:"preflight"}` op AND the declare embed. `omt_status.ts` is now a thin consumer (imports PREFLIGHT_DEFAULT_TOOL/preflightProjection/preflightLines). buildPreflightCtx gains `envOverride` (live state, inert `$`); module cycle phase_gate→preflight→gate_driver→phase_gate is function-level-only (hoisted declarations), ESM-safe.
- Overlap check (Exec rule 5): meta_harness_5 all-shipped/reject; meta_harness_6 A4 built op=preflight — P0-1 REUSES it (the A4 core shared home, no second gate engine), no re-implementation.
- Receipt round-robin held (2 file transforms via one `uv run python` script + new-file Write, all within the fresh-receipt round); canary ordering held. feature_055's CLEARING_ACTIONS source pins repointed to preflight.ts (tests/ edit under canary).
- Evidence: new `tests/features/feature_062.preflight_on_declare/test_preflight_on_declare.py` (6 tests: declare-embed probes, phase-scoping + fail-open, op=preflight parity, static pins) + feature_055 pins updated + e2e check #21 + HARNESS_FILES entry; e2e 1/1; `harnessc check` 0 errors + `build` OK (budgets green, 263 records); full suite **1992/0**.

### In progress / Blocked

- _(nothing — P0-1 shipped; 3/4 Wave 0 done)_

### Next

1. Wave 0 remainder: P0-3 `kb-sticky-per-feature` (`uv run scripts/omt/new_feature.py "kb sticky per feature" --type minor_feature --project meta_harness_7`), then Wave 1 (P1-1 → P1-2 → P1-3 → P1-4).
2. Before each scaffold: overlap check vs meta_harness_5/6 backlogs (Exec rule 5).

### Notes / context

- The g.mvc after-note is absent from the src probe (when= path_in(src/**/*.py) + edit tool) — a pre-existing A4 parity detail, not a P0-1 regression (shared code path, byte-identical).
- The declare embed only fires for feature-scoped Programming/Testing declares; my own unframed Testing declare did not embed (correct).

---


## 2026-09-06 (iter 3 — P0-4 nav-cache-hit DONE, Wave 0 2/4)

### Done

- **feature_061.nav_cache_hit DONE (minor_feature, Programming→Testing→Done):** the g.nav denial for a blocked doc-scoped grep/glob now appends `📎 nav index hits for '<stem>':` + top-3 compiled-index records — message-only (verdict, policy and the IR `nav_required` text unchanged; fail-open returns the byte-identical pre-P0-4 denial when no stem / no index / no hits).
- Implementation: `nav_gate.ts` gains `searchQueryStem` (longest pattern-ish arg; regex noise → spaces; identifiers keep underscores) + `navCacheHint` (full-stem match, then longest-word fallback ≥3 chars; top-3 in index order; 96-char line cap); `gate_driver.ts` g.nav impl appends the hint after `gateMsg("nav_required")`.
- Overlap check (Exec rule 5): meta_harness_5 all-shipped/reject; meta_harness_6 A4 built preflight (opt-in projection) — P0-4 is denial-time, complementary, no re-implementation. Gotcha found: block-severity @msg records are NOT nav-indexed (only err_/wrn_*) — hint fixtures must use indexed words (dangling/budget/tdd).
- Receipt round-robin held across 3 rounds (the import edit consumed nav_gate.ts's round-2 slot → e2e refresh → function-block edit + gate_driver multi-site transform via `uv run python` = one file-edit each); canary ordering held (phase before skip, skip immediately before the tests/ write).
- Evidence: new `tests/features/feature_061.nav_cache_hit/test_nav_cache_hit.py` (5 tests: stem extraction, hint build incl. top-3 cap + word fallback + fail-open nulls, real before-chain message-only probe, static wiring pins) + e2e check #20; e2e 1/1; `harnessc check` 0 errors + `build` OK (budgets green, gates 10/12, 263 records); full suite **1986/0**.
- No `.omt` edits → nav_index/ir_json/tool_args/schemas budgets untouched (tightest caps preserved for P1-4).

### In progress / Blocked

- _(nothing — P0-4 shipped)_

### Next

1. Wave 0 remainder in listed order: P0-1 `preflight-on-declare` (`uv run scripts/omt/new_feature.py "preflight on declare" --type minor_feature --project meta_harness_7`), then P0-3 `kb-sticky-per-feature`.
2. Before each scaffold: overlap check vs meta_harness_5/6 backlogs (Exec rule 5). P0-1 sits on the feature_055 A4 surface (phase_gate.ts reusing runBeforeGatesDry read-only) — read feature_055's test first.

### Notes / context

- Live in-session g.nav denials still lack the hint (TS plugins don't hot-reload — restart picks it up; bun probes + pytest prove the behavior).
- Receipt round-robin reaffirmed: a second edit to the same harness file needs its e2e refresh BEFORE the edit lands, not after.

---


## 2026-09-06 (iter 2 — P0-2 dangling-active-only DONE, Wave 0 started)

### Done

- **feature_060.dangling_active_only DONE (minor_feature, Design→Programming→Testing→Done):** `omt_status` dangling list now shows ≤10 *unexpired* active oldest-first + `… N expired auto-hidden (GC: …)` line; header `Dangling phases: N (M expired)` unchanged (e2e shape pin); summary gains `dangling_active`. 8h UNLOCK_WINDOW is the one-session grace — hidden expired stay resumable via re-declare/abandon.
- Overlap check (Exec rule 5): meta_harness_5 all-shipped/reject (no open), meta_harness_6 A2+A3 built the dangling list — P0-2 is incremental active-filter, no re-implementation.
- Receipt round-robin held (ONE harness edit + tests edits, ONE e2e refresh); canary ordering held (phase before skip, skip immediately before tests/ edits).
- Evidence: new `tests/features/feature_060.dangling_active_only/test_dangling_active_only.py` (cap 12→10 + GC + empty) + updated `feature_056/test_phase_hygiene.py` (active-listed, expired-hidden); e2e 1/1; `harnessc check` 0 errors + `build` OK (budgets green, gates 10/12); full suite **1981/0**.
- Project flips draft → active (first linked feature; WORK.md + META.md auto-synced).

### In progress / Blocked

- _(nothing — P0-2 shipped)_

### Next

1. Wave 0 next per CURRENT_STATE iter 1: P0-4 `nav-cache-hit` (`new_feature.py "nav cache hit" --type minor_feature --project meta_harness_7`), then P0-1 → P0-3 in listed order.
2. Before each scaffold: overlap check vs meta_harness_5/6 backlogs (Exec rule 5).

### Notes / context

- Live `omt_status` in-session still shows expired list (TS plugins don't hot-reload — fresh `bun` probes + pytest show the new behavior; restart picks it up).
- Tightest budgets after build: tool_args 2278/2304, schemas 1770/1792, nav_index 63923/64000 — P1-4 owns the warning.

---


## 2026-09-06 (iter 1 — program defined; ZERO execution)

### Done

- **Program defined per `loops/meta_harness_project.md` steps 1–3**: toolbox reads (`omt_status`, `omt_q state/plan/drift`, `omt_nav QUICK_/PROJECT`, `omt_think{op:list, query:risk}`, `.workflows/META.md` → `meta_harness/META.md` → `loops/meta_harness_project.md`), `project.py new "meta harness 7" --slug meta_harness_7`, PROJECT.md filled (v0.2, 11 items in 3 waves, baseline, DG1–DG3, execution rules, success criteria).
- **Evidence record:** this session's performing-work analysis thread (friction map W1–W10 + P0/P1/P2 options); PROJECT.md §Baseline + §References are the durable pointers.
- **Scope locked:** P0-1..P0-4, P1-1..P1-4, P2-1..P2-3 — user "include all" (D1). Next session starts Wave 0.

### In progress / Blocked

- _(nothing — program defined, nothing executed; next session starts Wave 0)_

### Next

1. Read `PROJECT.md` §New Session Quick Start → §Decision gates → §Execution rules → §Baseline.
2. Scaffold Wave 0 / P0-2: `uv run scripts/omt/new_feature.py "dangling active only" --type minor_feature --project meta_harness_7` → `omt_phase{task_type:minor_feature, phase:Programming, scope:"..."}` → execute per Execution rules (receipt round-robin; canary ordering; overlap check).
3. Then Wave 0 remainder in listed order (P0-4 → P0-1 → P0-3) — PROJECT.md §The program.

### Notes / context

- All 11 items are `minor_feature` (+ short design note for P2-1 only); no §12 major gate, no TDD auto-on by default.
- Harness-surface discipline applies to every feature here (harness_paths + net_paths where touched): ONE edit per file per receipt round, e2e refresh per round, harnessc check+build with budgets green (tightest: tool_args −26B, schemas −22B, nav_index −77B — P1-4 owns the warning).
- Check `meta_harness_5` + `meta_harness_6` backlogs before each scaffold (Execution rule 5 — no re-implementation of C2/A4/B1/E2 etc.).
- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.

---

## 2026-09-06 (iter 0 — project created)

### Done

- Project home created (`project.py new`, state: draft).

### In progress / Blocked

- _(nothing)_

### Next

- <!-- superseded by iter 1 above -->

### Notes / context

- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.
