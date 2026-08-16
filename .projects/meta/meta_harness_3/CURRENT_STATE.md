# CURRENT_STATE: meta_harness_3

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-16 (iter 3 — Phase-A BUILD COMPLETE: 10/10 behaviors GREEN, done gate ✅)

### Done

- **Resumed from `.sandbox/pause_2026-08-16.md` and built all 5 R9 rounds** in one session (refactor + TDD, feature_028.feature_scoped_gating):
  1. `state.py` P1-1 — `_active_feature` + `_tdd_records` feature-scoped derivation (R11 two-session golden: `testlist`→`green` preserved on resume).
  2. `gates.py` P1-3 + P3-8 — validate-exit scopes coverage to feature-added methods (feature-baseline snapshot tier in state.py: `snapshot_feature_baseline`/`load_feature_baseline`, first-write-wins, no-baseline→legacy full scan D5); two-hats both-blocked message config-driven via HAT_RULES (R6).
  3. `cli.py` P1-2 — cmd_done split `feature_suite_passes` + `repo_hygiene_passes` (suite_passes kept = conjunction, omt_q U7-compatible); R4 `regressions = current − baseline − KNOWN_SUITE_FAILURES` block, drift noted; `_feature_baseline_failures` + `cmd_baseline`; cmd_start captures the P1-3 baseline at RED.
  4. `phase_gate.ts` R4 — omt_phase{TDD Programming} shells `tdd_check.py baseline`, stores `baseline_failures` on the phase record (fail-open), response line surfaces the count.
  5. `omt_q.ts` T1 — default op=state projects decree_health/risky_thoughts/recent_consults to counts+top-N; `verbose:true` byte-identical full dump; `.omt` @tool desc updated (harnessc build+check 0 errors, budgets OK). Live: **44,181B → 2,706B**.
- **Gates:** 6 RED→GREEN cycles (node-granularity honored) → `omt_tdd{op:done}` ✅ (2 KNOWN_SUITE_FAILURES tolerated; the feature's own phase records predate round 4 → legacy fallback exercised live). 217/217 `tests/scripts/omt/`. E2E receipt refreshed per round (one guard-prescribed mid-round refresh for a test-file fix).
- **TA cleanup:** the 5 `feature_028` fix-site todos tombstoned after shipping.
- **Test report:** `.meta/software_development_process/6.testing/features/feature_028.feature_scoped_gating/test_report.md` (per-round evidence + design decisions).

### Locked decisions (do not re-litigate without new evidence)

- (carried) D1–D9 hold.
- **(new) First-RED capture** chosen for the P1-3 baseline tier (R5's allowed alternative to Programming-entry): Python-local, exactly pre-first-touch.
- **(new) Two-hats is src/-scoped by construction** (g.phase `path_in(src/)`); harness-surface TDD cycles run on ledger-ops + receipt-guard discipline. Skip-shadows-phase mute of the TDD deferral = candidate finding for the evaluation doc, NOT a v1.2 fix.

### In progress / Blocked

- _(nothing)_

### Next

- `omt_complete` Programming→Testing→Done for feature_028; WORK.md row → DONE.
- Phase-B (P2 items + T2 nav caps) untouched — separate feature/round per the v1.2 surface.

### Notes / context

- The bootstrap friction the pause doc flagged (testlist state allows zero edits → omt_skip{tests} required to create the first RED file) is real and recurring (hit again this session); candidate finding for the evaluation.
- op=state live envelope 2,706B vs ~2KB target: the delta is actionable per-session scalars (stranded_red IDs, KNOWN_SUITE_FAILURES); structural ≤2048B pinned hermetically.

---

## 2026-08-16 (iter 2 — token deep analysis + v1.2 unified re-scope, user-approved)

### Done

- **Ran the measured token deep analysis the user asked for** (improve operation, remove friction, cut token consumption, no new features): read-only aggregate SQL over `~/.local/share/opencode/opencode.db` (1009 agentx sessions, 2026-04-19→2026-08-16: 494M input / 8.4M output / 1.07B cache-read tokens, $294.54, 26.2 turns/session avg) + static byte audit of the harness surface. No session content read — sizes/counts only.
- **Verified what's already lean** (no action): ceremony tools 257–369B/call; bootstrap tips ~690B once-per-session (S6 single-emission confirmed working); AGENTS.md 2,626/2,816B; tool schemas 1,094/1,280B; gate-block messages ~350B × 887.
- **Isolated 3 measured token leaks + 1 policy:** T1 `omt_q{op:state}` 24–36KB/call avg 29KB (`decree_health` unconditional, `omt_q.ts:494-528` — root-caused in code); T2 `omt_nav` uncapped 4.5KB avg × 302 calls (1.37MB); T3 duplicate re-reads (same file up to 29× in one session; read = 66% of all tool bytes; root cause = compaction eviction); T4 schema budget at cap → standing policy.
- **Wrote PROJECT.md v1.2:** §Token evidence section (full audit trail), T1/T2/T3 rows in the §Purpose table + §Scope items (phase-tagged T1./T2./T3. to avoid renumbering 1–12), token success targets, D7 (unified re-scope) / D8 (slimming ≠ removal) / D9 (schema budget zero-sum), D6 annotated as superseded-by-R2 (stale decision caught), iter v1.2 log, References updated.

### Locked decisions (do not re-litigate without new evidence)

- (unchanged) v3 = feature-scoped-gating refactor; no gate removals; feature-dir + phase declaration deferred until approved.
- **(new, user-approved 2026-08-16) D7 unified re-scope:** two axes (friction 12 + token T1–T3), one surface, scale × cost.
- **(new, user-approved) D8:** output/schema slimming allowed when protection semantics provably unchanged; D5 still governs gates.
- **(new, user-approved) T1 shape:** `omt_q{op:state}` summary default (counts + top-N, ≤ ~2KB) + `verbose:true` full dump byte-identical.
- **(new) D9:** `tool_schemas` budget is zero-sum — new tools displace, not raise (OPT-H precedent).
- **(new) Sequencing:** the v1.2 analysis GATES the Phase-A build — Phase-A starts from the v1.2 surface (12 + T1), not the v1.1 surface.

### In progress

- _(nothing — v1.2 doc round complete; awaiting user go for feature_028 scaffold + Phase-A)_

### Blocked

- _(nothing)_

### Next (when user approves the v1.2 build surface)

- **Scaffold feature_028** (`uv run scripts/omt/new_feature.py "feature scoped gating" --type <refactor|major_feature>` — type still open) + declare `omt_phase`.
- **Phase-A build order (R9 + T1):** state.py (P1-1) → gates.py (P1-3 + P3-8) → cli.py (P1-2 + R4 baseline) → phase_gate.ts (baseline capture) → **omt_q.ts (T1: summary projection + `verbose` flag; independent 5th round)**. Each round: edit → `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` → refresh receipt.
- **Mandatory Phase-A exit goldens:** R4 regression (P1-2), R11 two-session ledger (P1-1), R10 hermetic-test-dir (P1-2), R6 config-driven two-hats (P3-8), **T1 token golden (default ≤ ~2KB + verbose byte-identical)**.

### Notes / context

- The token problem is NOT the standing surface (the @budget system + 5 prior diet rounds did their job) — it's three output-shape leaks, and the biggest (T1) is in the NEWEST tool (feature_026's omt_q shipped without an output budget). Meta-lesson now in D9's orbit: new tools need an output-size budget at design time, not just a schema-description budget at compile time.
- T3's root cause is context compaction (agent re-reads after eviction) — harness leverage is indirect; the Phase-C design round picks the cheapest mechanism (candidate: `omt_status` resume-digest ≤ ~2KB).
- Resume entry point: PROJECT.md §Summary → §Token evidence (v1.2) → §Plan review R1–R11 → this entry → §Next.

---

## 2026-08-16 (iter 1 — plan review v1.1: pre-build verification)

### Done

- **Re-verified v1.0's anchors against the working tree** by reading the actual gate code end-to-end: `scripts/omt/tdd/gates.py` (212 lines), `state.py` (291), `cli.py` (397), `ast_checks.py` (203), `.opencode/lib/enforcer/phase_gate.ts` (396), `gate_driver.ts` (g.kb predicate), `session_state.ts` (kb session-boolean), `omt_q.ts` (recent_consults fold). Found 11 findings (R1–R11), applied inline corrections to PROJECT.md §Purpose table + §Scope items, added a §Plan review (v1.1) section + iter v1.1 log entry.
- **Two factual anchor corrections:**
  - **R1 (P1-2):** the evaluation §3.6 says `cmd_validate_exit` (gates.py:156) runs the full suite — WRONG. Verified `cmd_validate_exit` checks ONLY dangling reds + coverage gaps; the full-suite run is in `cmd_done` (cli.py:234). `omt_tdd{op:done}` and `omt_complete`→validate-exit are TWO DISTINCT exit gates; P1-2 targets the former, P1-3 the latter.
  - **R2 (P3-9):** v1.0 said "mirror `recent_consults`" — imprecise. `recent_consults` (omt_q.ts:251) folds `think_consult` records (g.think's substrate), not KB/Read. The KB gate (`g.kb`) uses `session_flag(kb_consulted)` — a session-boolean. The fix needs a NEW per-file Read-recency substrate.
- **One safety-critical gap (R4, the big one):** v1.0's P1-2 split would let a feature that breaks a prior feature's GREEN test (real regression) ship green — violating D5. Added the mandatory `baseline_failures` mechanism: snapshot failing node IDs at `omt_phase{phase:Programming}` entry; at `cmd_done`, `regressions = current − baseline − KNOWN_SUITE_FAILURES`. Regressions block; drift doesn't. Regression golden is now a Phase-A exit criterion.
- **P1-1 reframe (R3):** from "omt_phase idempotency" (symptom) to "feature-scoped TDD state derivation" (v3-consistent thesis); `get_tdd_cycles(feature)` is the existing precedent.
- **P1-3 sharpen (R5):** `diff_snapshots` does added-methods only (not modified); per-edit baseline is rolling, not feature-baselined. Specified the feature-baseline snapshot tier as a real substrate extension. Recommendation: ship "added" in Phase-A, defer "modified."
- **P3-8 fold (R7) + robustness (R6):** committed to Phase-A's gates.py round (saves a receipt round); fix must consult IR-derived `HAT_RULES` (both-blocked), not hardcode state names.
- **P2-4 location (R8):** `omt_tdd{op:sync}` is a new `cli.py` subcommand (not gates.py); sync writes a `green` record so it must require test-passes (no fabricated GREEN).
- **Phase-A sequencing (R9) + hermetic fixtures (R10/R11):** receipt-round order state.py → gates.py(+P3-8) → cli.py → phase_gate.ts; hermetic-test-dir for P1-2, two-session ledger for P1-1.

### Locked decisions (do not re-litigate without new evidence)

- (unchanged from iter 0) v3 = feature-scoped-gating refactor; no gate removals; feature-dir + phase declaration deferred until approved.
- **(new) D5 reinforced (R4):** P1-2 MUST ship the `baseline_failures` regression guard; the regression golden is a mandatory Phase-A exit criterion. A feature-suite-only split without it is a protection regression and is NOT shippable.
- **(new) P3-8 reclassified C→A** (folded into Phase-A's gates.py round per D3).

### In progress

- _(nothing — v1.1 review round complete; plan is build-ready pending approval)_

### Blocked

- _(nothing)_

### Next (when user approves the project definition)

- **Decide the Phase-A entry shape + scaffold feature_028** (same fork as iter 0: open `feature_028.*` under `4.design/features/` phase-gated, OR continue in `.projects/` non-gated). `uv run scripts/omt/new_feature.py "feature scoped gating" --type <refactor|major_feature>`.
- **Phase-A build per R9 receipt-round order:** state.py (P1-1) → gates.py (P1-3 + P3-8) → cli.py (P1-2 + R4 baseline) → phase_gate.ts (baseline capture + done envelope). Each round: edit → `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` → refresh `.meta/.omt/omt_harness_e2e_last_run.json`.
- **Mandatory Phase-A exit goldens:** R4 regression golden (P1-2), R11 two-session ledger (P1-1), R10 hermetic-test-dir drift+regression (P1-2), R6 config-driven two-hats (P3-8).

### Notes / context

- The v1.1 round did NOT change the v3 thesis or the P1/P2/P3 priority ordering — it made the build surface honest about what the existing mechanisms actually do (added-only diff, rolling snapshot, session-boolean KB gate, two distinct exit gates) so Phase-A designs the right substrate extensions instead of assuming "promote the existing mechanism" suffices.
- v1.0 trusted the evaluation's line numbers; v1.1 re-derived every anchor from the code. The two errors caught (R1, R2) were inherited from the evaluation (§3.6, §3.4) — the evaluation was written from inside the loop with a bias disclaimer; v1.1 is the outside-the-loop verification pass.
- Resume entry point: read PROJECT.md §Summary + §Plan review (v1.1) R1–R11 first, then this entry, then the §Next block.

---

## 2026-08-16 (iter 0 — project home created from feature_027 evaluation)

### Done

- **Created the v3 project home** — `.projects/meta/meta_harness_3/` with `PROJECT.md` v1.0 + this `CURRENT_STATE.md`. The directory already existed (empty) from the feature_027 session.
- **Read the evidence base** — `.sandbox/session_2026-08-15_feature_027_completion.md` (179 lines) end-to-end: §2 (8 protections that earned their keep), §3 (12 friction items classified COMPOUNDS/FIXED/LOCAL), §4 (7 workflow-evolution patterns), §5 (12-item P1/P2/P3 improvement table), §6 (verdict: feature-scoped gating beats repo-scoped gating).
- **Re-verified every code anchor against the current working tree** before writing the doc (the evaluation's line numbers are from the session; the working tree is the current truth):
  - `scripts/omt/tdd/gates.py:99-107` — the two-hats message bug (§3.3): `hat` map has `testlist: "planning"`, `done: "complete"`; line 101 ternary flips the noun but says "Only src/ edits allowed" when BOTH src+tests are blocked.
  - `gates.py:129-131` — `diff_snapshots` is ALREADY used in the GREEN-hat after-edit to detect new methods; the P1-3 coverage-on-diff fix promotes this same mechanism to `validate-exit` (which today scans ALL public methods of full files at `gates.py:185-197`).
  - `gates.py:156-212` — `cmd_validate_exit`: dangling-red derivation (173-183) + full-file coverage scan (185-197) + `skip_override` honoring ONLY `scope:"all"` (161-171).
  - `scripts/omt/tdd/state.py:132` — `KNOWN_SUITE_FAILURES` (6 allowlisted node IDs).
  - `state.py:157-169` — `get_session_records`: **the §3.1 phase-reset root cause**. A new session's `omt_phase` record makes `mine` non-empty for the new session id → the prior session's TDD records are shadowed → `get_tdd_state` (`state.py:181-192`) falls through to `testlist`.
  - `state.py:232` — `diff_snapshots` implementation.
  - `state.py:257-272` — `run_full_suite` (the full-suite run that makes `omt_tdd{op:done}` a worldwide-drift triage, §3.6).
  - `.opencode/lib/enforcer/phase_gate.ts:203-208` — `omt_phase` writes a phase record with `tdd_mode`; no in-flight-feature preservation branch exists.
  - `.opencode/lib/enforcer/receipt_guard.ts` + `.meta/.omt/omt_harness_e2e_last_run.json` — the receipt guard (§3.5).
  - Confirmed next free feature slot: **feature_028** (`2.requirements/features/` lists 027 = rag_v2 as the last).
- **Locked the improvement surface** in `PROJECT.md` §Purpose: the P1/P2/P3 table (12 items) with verified anchors + per-item Success shapes in §Scope.
- **Locked 6 decisions** (D1–D6) — v3 = feature-scoped-gating refactor (not a rewrite); slug `meta_harness_3` + feature_028; Phase-A=P1 / Phase-B=P2 / Phase-C=P3; hermetic-ledger golden-test verification; no gate removals; g.kb recent-read mirrors `recent_consults`.

### Locked decisions (do not re-litigate without new evidence)

- **v3 is the "feature-scoped gating" refactor — the evaluation's §5 headline.** The phase lifecycle should gate on the FEATURE's content + hygiene, not the union of all prior features' drift. Phase-A ships the three P1 fixes (`omt_phase` idempotent, `suite_passes` split, coverage-on-diff).
- **No gate removals; §2 protections stay byte-identical.** Their existing pin tests are the regression guard.
- **Feature-dir scaffolding + phase declaration deferred** (per the rag_v2/meta_harness_2 convention) until this project definition is approved by the user.
- **Verification = hermetic-ledger + golden-test** (`OMT_LEDGER_PATH` / `OMT_SNAPSHOT_DIR` redirects per `state.py:34-37`), full-suite regression at phase exit.

### In progress

- _(nothing — iter 0 doc round complete)_

### Blocked

- _(nothing)_

### Next (when user approves the project definition)

- **Decide the Phase-A entry shape**: open `feature_028.*` under `4.design/features/` (phase-gated, activates TDD + AGENTS.md process surface) OR continue designing in `.projects/meta/meta_harness_3/` only (non-gated, iterative). Same fork meta_harness_2/rag_v2 faced.
- **Scaffold the feature dir** when the fork is decided:
  ```bash
  uv run scripts/omt/new_feature.py "feature scoped gating" --type <task_type>
  ```
  (major_feature or refactor — decided with the user; feature_028 confirmed free.)
- **Phase-A build order** (per PROJECT.md §Scope P1 items):
  1. `omt_phase` idempotency — fix the `get_session_records` session-scoping shadow + add an in-flight-feature preservation branch in `state.py`/`phase_gate.ts`; golden = the §3.1 scenario (TDD state preserved, not reset to `testlist`).
  2. `suite_passes` split — `feature_suite_passes` + `repo_hygiene_passes` in the done-checklist envelope; golden = done succeeds with synthetic prior-feature drift present.
  3. Coverage-on-diff — promote `diff_snapshots` to `validate-exit`; golden = additive edit to a file with prior untested methods exits Testing without `scope:all` skip; a NEW untested method still blocks.
- **Each Phase-A edit is harness-surface** (`scripts/omt/`, `.opencode/`) → receipt round-robin discipline applies: ONE edit per file per e2e receipt, run `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` + refresh `.meta/.omt/omt_harness_e2e_last_run.json` between rounds (WORK.md scratchpad gotcha).

### Notes / context

- The evaluation's bias disclaimer (it was written from inside the loop it critiques) is carried into PROJECT.md D1 — v3's thesis is the session's OWN headline finding, labeled as such, not re-derived independently.
- Two P2 items were ALREADY fixed as feature_027 collateral (WORK.md 2026-08-15: kb count pins → structural kind-pin; u13 hardcoded date → dynamic now-1h). v3's P2-5/P2-6 bake the *conventions + lints* (GOTCHA_ entries + date lint) so the classes don't recur — they do NOT re-fix the tests. Verified: `test_kb_compiler_build_runs_clean` and the u13 test are in the current tree in their fixed forms.
- Feature_027's session left `git status` clean; the only workspace change from this iter is the two new project-home files.
- Resume entry point: read `PROJECT.md` §Summary + §Scope P1 items first, then the latest `CURRENT_STATE.md` entry, then the §Next block above.