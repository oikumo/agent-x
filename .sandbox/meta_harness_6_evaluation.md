# Meta Harness Evaluation — 2026-09-05 (session analysis, evidence base for meta_harness_6)

> Deep evaluation of the META HARNESS as a whole: usage gains with vs without it, for a
> user running opencode on future projects. Performed at net rev 53 (post feature_050),
> WORK.md pool pending=2 active=0 done=5, e2e receipt fresh. This file is the durable
> record of that evaluation; `.projects/meta/meta_harness_6/PROJECT.md` is the actionable
> program distilled from it.

---

## 1. Verdict summary

| Dimension | Grade | One-liner |
|---|---|---|
| Architectural coherence | **A** | SSOT + compiler + closed predicate vocabulary — policy-as-code done right |
| Self-consistency / dogfooding | **A−** | Built under itself; every projection derived, every override logged |
| Demonstrated quality payoff | **B+** | Petri-net studio sprint (6 major features / 8 days, 1577-test suite) |
| Runtime friction | **C+** | 266 skips vs 327 phases — escape hatch nearly as used as the front door |
| Portability to a future project | **C** | Coupled to repo layout, uv, Python/MVC++, opencode plugin API internals |
| Self-hosting tax | **D+** | ~50% of feature work since July went into the harness itself |

**Bottom line:** for the same user on long-lived projects with opencode: clear net positive
(mechanically solves amnesia, drift, unenforced discipline). For a different user or a short
project: negative ROI unless shipped as a trimmed template. Value is real but concentrated;
cost is front-loaded and ongoing.

## 2. Measured evidence (the field trial)

Cumulative ledger (archives + current, as of 2026-09-05):

| Record | Count | Interpretation |
|---|---|---|
| think_consult | 696 | Most-hit gate; 40 TA:-carrying files pay a consult toll every editing session |
| phase | 327 | Front-door usage |
| skip | 266 | Escape hatch — large share is procedural (tests canary per TDD_BOOTSTRAP), not evasion |
| q | 191 | Interrogative layer in real use |
| complete | 173 | ~53% of declared phases completed |

Size / effort split:

- App src 22,794 LOC vs harness ~14,000 LOC (scripts/omt 8,991 + .opencode TS 5,008) = 61% of app size.
- 115 test files: ~20 direct app unit tests, 62 per-feature TDD-gate artifacts, 33 harness-self tests.
- ~27 of ~55 features since July were harness-internal; buildout Jul 11 → Sep 5 (~8 weeks).
- Budget creep history (documented in `@budget` comments): work_md 4096→8192B over 8 features;
  tool_schemas ~760→1792B; tool_args 1536→2304B. Corrections were manual diets (improvement002–007),
  not structural.
- KNOWN_SUITE_FAILURES: 6 tolerated failures (3× feature_018 react_screen + 3× ledger-window flaky)
  — the harness ships with a known-failing suite, caused by global ledger state shared with live sessions.
- 18 nav-indexed gotchas, clustering into: SDK-contract class (4), test-isolation class (3),
  receipt-discipline class (4), TDD-toolchain class (3), misc (4).
- g.net:35 is fail-closed on ALL of src/, tests/, .opencode/, scripts/omt/ — but its justification
  (multi-session concurrency, feature_051) is DEFERRED. Single-session work pays full net ceremony
  for zero current benefit.
- All 12 projections/budgets green at evaluation time (harness.report, AGENTS.md 2918/2944 B).

Peak-throughput proof point: features 031–036 (petri lib → format → io → studio v1/2/3), 6 majors in
8 days, each 99–274 tests, golden byte-parity conformance, 1577-test suite green, zero regressions.
The harness did not slow peak throughput; it made peak throughput safe.

## 3. Architecture assessment

**Wins:** SSOT→compiler→projections (docs/config/enforcement cannot drift); gates as data with a
closed `@pred` vocabulary (12 readable `@gate` lines = the whole posture); compile-enforced token
budgets with an active self-dieting loop; logged escape hatch (friction without suppression) with
two non-bypassable safety gates (g.think, g.net); append-only ledger audit.

**Weaknesses:** opencode plugin-API coupling (GOTCHA_SDK_CONTRACT / LOADER_EXPORTS / TS_NO_RELOAD —
an opencode upgrade can silently disable every gate: the quiet-failure mode); global mutable ledger
breaks harness test isolation (→ KNOWN_SUITE_FAILURES); gate proliferation trend with no structural
brake; net layer live but single-session; no onboarding path (646-line guide presumes OMT++ fluency);
no packaging/portability story despite `@var` parametrization.

## 4. Economic model

Value ≈ (sessions × continuity) + (repo size × knowledge-layer) + (risk × prevention) + (discipline × quality).
Cost ≈ adaptation + learning curve + per-edit ceremony + maintenance.

- Short/toy project: strongly negative (fixed costs dominate).
- Solo+agent, months, >100 sessions: positive (this repo's trajectory).
- Repo docs beyond context windows (>50–100KB): strongly positive (nav/KB/thoughts scale past the window).
- Multi-agent concurrency: potentially transformative but unproven (feature_051 deferred).

## 5. Improvement options (all 13 — full detail)

### A. Integrity fixes

**A1 ledger_test_isolation** — env override (e.g. `OMT_LEDGER_PATH`) honored by `.opencode/lib/omt_shared.ts`
+ `scripts/omt/tdd/state.py`; harness tests run on tmp ledger; DELETE the KNOWN_SUITE_FAILURES allowlist.
Size: minor_feature. Mechanism: `@var ledger_path` already exists — thread it. Acceptance: full suite
green with zero allowlist entries; GOTCHA_TDD_ENV_FLAKY demoted to ordinary doc. Cheapest fix of the
biggest credibility hole ("tests must pass" system with known-failing tests).

**A2 skip_purpose_taxonomy** — add `purpose: canary|emergency|break_glass|override` to `omt_skip`;
`omt_status` reports friction:evasion split; `harnessc check` alarms when `override` crosses a
threshold per week. Size: minor. Turns 266 opaque skips into signal.

**A3 phase_hygiene** — auto-expire phase records after `@var unlock_window_ms`; `omt_status` lists
dangling phases (327 declared vs 173 completed) with one-call abandon/resume; kills the
GOTCHA_TESTS_CANARY_SHADOW bug class (stale phase record shadows a later tests-approval).
Size: minor.

**A4 gate_preflight** — `omt_status{op:preflight, tool, path}` returns the ordered list of gates that
will fire + the clearing action for each (read-only projection of the `@gate` table). Kills the
deny-learn-retry loop (one call instead of N denials). Size: minor.

### B. Anti-creep

**B1 gate_budget** — compile-enforced `@budget gates max=12` (currently exactly 12); net-zero gate
policy (adding one requires retiring/merging one); retirement candidates auto-flagged from
skip-frequency data (never-fires gate = dead weight; always-fires-with-canary gate = toll booth).
Size: minor.

**B2 ceremony_meter** — ledger timestamps already exist: measure process calls between session start
and first src edit, per task_type; `harnessc report` median; alarm if bug_fix > 3. Makes the
"up to 6 calls before real work" cost visible and trendable. Size: minor.

### C. Friction reduction

**C1 net_gate_concurrency_predicate** — new `@pred net_marking()` (wraps `omt_net{op:probe}`);
g.net engages only when `net_marking(active>1)` — solo sessions revert to phase-gate only.
Size: minor. DECISION: this implements the predicate path; feature_051 (multi-session) stays
DEFERRED per user decision 2026-09-05. Re-evaluate only if multi-session becomes real.

**C2 small_task_fast_path** — for `bug_fix`/`test` task types, the `omt_phase` ledger record
auto-satisfies g.nav + g.kb session flags in one write (they stay hard for major_feature/new_screen).
Revisit TDD_BOOTSTRAP's rejected auto-unlock with a NARROWER condition: canary auto-approved only
for the declared feature's own test dir while RED hat is active. MUST NOT touch g.think/g.protect.
Size: minor.

### D. Portability / productization (the future-project payoff)

**D1 harness_tiered_template** — `harnessc init --tier 1|2|3` scaffolding:
Tier 1 = deny/protect/phase-gate(decl-only)/TDD-for-majors/ledger+skip (stack-agnostic, ~80% of value);
Tier 2 = +nav/thoughts/KB/budgets/projects/workflows (long-lived repos);
Tier 3 = +net/receipt/think-hard/MVC (experimental or proven-concurrency only).
Init = `@var` re-pointing + state reset + fresh budget baseline. Size: major_feature (design doc + TDD auto-on).

**D2 stack_profiles** — `@profile mvc_py|mvc_ts|none`; mvc_check gains a TS mode or ships disabled
under `none` (current rules are Python/TUI-specific). Size: minor. Rides with D1.

**D3 generated_onboarding** — `harnessc build` emits GETTING_STARTED.md per tier from the active
@gate/@tool/@flow set (the compiler already has everything needed). Size: minor. Rides with D1.

### E. Knowledge layer

**E1 gotcha_root_cause_pass** — tag the 18 gotchas by cluster (SDK-contract / test-isolation /
receipt-discipline / TDD-toolchain / misc); fix root causes (A1 kills the isolation class, F1 the
SDK class); demote survivors to ordinary docs. Size: analysis (docs task type) + fixes folded into A1/F1.

**E2 thought_review** — batch `omt_think{op:review}`: list thoughts untouched >90 days with one-call
archive; digest already flags staleness. Prunes the 696-consult toll (74 thoughts / 40 files, some
certainly stale). Size: minor.

### F. Survival against opencode churn

**F1 opencode_version_canary** — declare `@var opencode_version_range`; session start emits WRN when
out of range; the live-binary probes (GOTCHA_LIVE_BINARY recipe: `opencode run --format json` + jq
tool_use events, byte-identical file-state asserts) become a canary suite that FAILS LOUDLY on
version change. A gate that stops firing without notice is worse than no gate. Size: minor.

## 6. Recommended sequence

| Order | Option | Type |
|---|---|---|
| 1 | A1 ledger isolation | minor |
| 2 | F1 version pin + canary | minor |
| 3 | C1 net-gate predicate | minor |
| 4 | A2 + A3 skip taxonomy + phase expiry | minor |
| 5 | B1 + B2 gate budget + ceremony meter | minor |
| 6 | E2 thought review (+ E1 pass) | minor |
| 7 | D1–D3 tiered template | major + minors |

Steps 1–6 are ~6–8 minor features; step 7 only after the net question is settled (it is: C1 ships,
051 stays deferred). End-of-program re-evaluation should compare against the §2 baseline.
