# PROJECT: meta_harness_6 — Meta Harness 6 — Evaluation-Driven Improvement Program

> Status: **active** · **v0.2 (2026-09-05)** — created by `project.py new`, program definition filled same session (deep evaluation). Iterate freely (non-gated); spawn features with `new_feature.py "<name>" --type <tt> --project meta_harness_6`; log sessions in CURRENT_STATE.md (newest on top).

---

## New Session Quick Start

> One line: `meta_harness_6` is the **13-item improvement program distilled from the 2026-09-05 deep evaluation** of the META HARNESS (evidence + full option detail @ `.sandbox/meta_harness_6_evaluation.md`) — 5 waves: integrity → friction → signal → knowledge → productization; Wave 1/A1 SHIPPED as feature_051 (2026-09-06, suite 1846/0, allowlist permanently empty); next = Wave 1/F1.

**Next:** Wave 2 opens with **C1 `net_gate_concurrency_predicate`** — resume from `.projects/meta/meta_harness_6/CURRENT_STATE.md` §Next (2026-09-06 iter 2 entry). Scaffold: `uv run scripts/omt/new_feature.py "net gate concurrency predicate" --type minor_feature --project meta_harness_6` (takes number 053), then `omt_phase{task_type:minor_feature, phase:Programming, scope:"..."}` and execute per §Execution rules. Read §Decision gates + §Execution rules FIRST (net/receipt discipline; DG2 numbering note is RESOLVED — 051 taken by A1, 052 by F1).

---

## Summary (one line)

**All 13 improvement options from the 2026-09-05 harness evaluation, sequenced into 5 waves (10 minor features + 1 major + 2 riding minors + 1 analysis pass), aimed at: suite integrity, opencode-upgrade survivability, ceremony reduction, anti-creep brakes, and a tiered template that makes the harness reusable on future projects.**

---

## Purpose

### What this project is

- The **execution program** for every improvement option accepted in the 2026-09-05 evaluation ("include all"): items A1–A4, B1–B2, C1–C2, D1–D3, E1–E2, F1 (detail per item: evidence, mechanism, acceptance @ `.sandbox/meta_harness_6_evaluation.md` §5).
- **Self-contained**: a fresh session needs only this file + the evaluation doc — no conversation history required.
- A **measured program**: the evaluation's baseline (ledger counts, suite failures, gate count, budgets, gotcha clusters) is recorded in §Baseline so the end-of-program re-evaluation can compute deltas.

### What this project is **not**

- NOT executing anything now — this session only defined the program (features are scaffolded and executed in later sessions, one feature per item/group).
- NOT a re-litigation of the evaluation verdicts (grades, economic model) or of `meta_harness_5`'s locked verdicts (shipped/reject statuses stand — check its backlog for overlap before spawning each feature).
- NOT feature_051.multi_session_concurrency — that stays DEFERRED (user decision 2026-09-05); this program ships the C1 net-gate **predicate** instead (DG1).

---

## Scope & success criteria

**Scope:** all 13 items below, each shipped as its own feature through the full OMT++ process, in wave order (within a wave, order is the listed order). Grouped scaffolds allowed where noted (A2+A3, B1+B2, E2+E1).

**Success criteria (project-level):**

1. All 13 items shipped OR explicitly closed-with-verdict in Decisions log.
2. KNOWN_SUITE_FAILURES = **0** and stays 0 (A1) — suite green means green.
3. g.net engages only under real concurrency (C1); solo-session ceremony measurably reduced (B2 report: bug_fix median ≤ 3 process calls before first src edit).
4. `@budget gates` enforced at ≤ 12 with net-zero policy (B1); all byte budgets stay green after every feature (harnessc build → report).
5. `harnessc init --tier 1` produces a WORKING Tier-1 harness in a fresh tmp repo (deny/protect/phase/TDD/ledger live; e2e of the template passes) (D1–D3).
6. End-of-program re-evaluation vs §Baseline shows: skip purpose report live (friction vs evasion distinguishable), dangling-phase count ≤ 5, gotcha count reduced by ≥ 5 (root-caused, not deleted), thought staleness pruned.

**Out of scope / guardrails:**

- g.think and g.protect semantics are NOT weakened by any item (C2 explicitly excluded from touching them).
- No auto-unlock of the tests canary beyond the narrowed condition in C2 (declared feature's own test dir, RED hat active only).
- No new gate may be added without retiring/merging one (B1 policy starts with the Wave 3 feature, applies from then on).
- feature_051.multi_session_concurrency remains deferred; reviving it is a NEW decision requiring user re-ask (see pause runbook note).

---

## The program — 13 items in 5 waves

> Per-item: what / why (evidence) / mechanism (HDL hook) / size (§12 task type). Full detail + acceptance criteria per item @ `.sandbox/meta_harness_6_evaluation.md` §5. Suggested feature slugs are indicative; `new_feature.py` assigns numbers mechanically (see DG2).

### Wave 1 — Integrity (execute first)

| # | Item | What | Why (evidence) | Mechanism | Size |
|---|---|---|---|---|---|
| A1 | `ledger_test_isolation` | env override (`OMT_LEDGER_PATH`) honored by TS shared lib + `tdd/state.py`; harness tests on tmp ledger; **delete KNOWN_SUITE_FAILURES allowlist** | 6 tolerated failures; "tests must pass" system ships red | `@var ledger_path` threading | minor |
| F1 | `opencode_version_canary` | `@var opencode_version_range` + startup WRN out-of-range + live-binary probes (GOTCHA_LIVE_BINARY recipe) as fail-loud canary suite | SDK-contract gotchas (4); opencode upgrade can silently kill every gate — quiet failure is worst case | new `@var` + WRN msg + probe tests | minor |

### Wave 2 — Friction

| # | Item | What | Why | Mechanism | Size |
|---|---|---|---|---|---|
| C1 | `net_gate_concurrency_predicate` | new `@pred net_marking()`; g.net engages only when `active>1` — solo sessions revert to phase-gate only | g.net fail-closed on ALL net_paths for zero current benefit (051 deferred) | `@pred` closed vocab + `omt_net{op:probe}` wrap | minor |
| C2 | `small_task_fast_path` | for `bug_fix`/`test`: the `omt_phase` record satisfies g.nav+g.kb flags in ONE write (stays hard for major/new_screen); narrowed canary auto-unlock (own test dir, RED hat only) | worst case 6 process calls before real work; canary-shadow ordering trap | compound ledger record / session flags | minor |
| A4 | `gate_preflight` | `omt_status{op:preflight, tool, path}` → ordered gates-that-will-fire + clearing action each | deny-learn-retry costs a turn per gate hit | read-only projection of `@gate` table | minor |

### Wave 3 — Signal & brakes

| # | Item | What | Why | Mechanism | Size |
|---|---|---|---|---|---|
| A2+A3 | `skip_taxonomy_phase_hygiene` | `purpose:` arg on omt_skip (canary/emergency/break_glass/override) + friction:evasion report; auto-expire phase records past unlock window + dangling list with abandon/resume | 266 skips opaque; 327 declared vs 173 completed; stale records shadow later approvals (GOTCHA_TESTS_CANARY_SHADOW) | `@tool omt_skip` args + `@state` fields + status report | minor (one feature, two behaviors) |
| B1+B2 | `gate_budget_ceremony_meter` | `@budget gates max=12` net-zero policy + retirement candidates from skip-frequency; ceremony meter (calls before first src edit, per task_type; alarm bug_fix > 3) | gate proliferation is the dominant failure trend; ceremony cost invisible today | `@budget` line + harnessc check + report | minor (one feature, two behaviors) |

### Wave 4 — Knowledge

| # | Item | What | Why | Mechanism | Size |
|---|---|---|---|---|---|
| E2+E1 | `thought_review_gotcha_root_cause` | batch `omt_think{op:review}` (>90d untouched → one-call archive); gotcha cluster tagging (SDK/isolation/receipt/toolchain/misc) + root-cause fixes (A1/F1 kill 2 clusters) + demote survivors to docs | 696 consults lifetime — toll never decays; 18 gotchas are patches on surprises, clustered causes | omt_think op + `@doc gotcha.*` category tags | minor + analysis (docs) |

### Wave 5 — Productization (the future-project payoff; only after Waves 1–4)

| # | Item | What | Why | Mechanism | Size |
|---|---|---|---|---|---|
| D1 | `harness_tiered_template` | `harnessc init --tier 1|2|3`: T1 deny/protect/phase(decl-only)/TDD-majors/ledger; T2 +nav/thoughts/KB/budgets/projects/workflows; T3 +net/receipt/think-hard/MVC | portability grade C — adoption currently means copying a repo-entangled 14K-LOC harness | `@var` re-pointing + state reset + budget re-baseline | **major** (design doc + TDD auto-on) |
| D2 | `stack_profiles` | `@profile mvc_py|mvc_ts|none` (mvc_check TS mode or disabled) | MVC++ rules are Python/TUI-specific | new `@profile` kind or var | minor (rides D1) |
| D3 | `generated_onboarding` | `harnessc build` emits GETTING_STARTED.md per tier from @gate/@tool/@flow | no onboarding path today; 646-line guide presumes fluency | compiler emission | minor (rides D1) |

---

## Baseline (2026-09-05, for end-of-program delta)

- Ledger cumulative: think_consult 696 · phase 327 · skip 266 · q 191 · complete 173.
- Harness ~14,000 LOC (scripts/omt 8,991 + .opencode TS 5,008) vs app src 22,794.
- Gates: 12 · tools: 10 · gotchas: 18 · KNOWN_SUITE_FAILURES: 6 · TDD allowlist shape-pinned.
- All 12 byte budgets green (AGENTS.md 2918/2944 B); net rev 53, places 12/15.
- Full current numbers @ `.sandbox/meta_harness_6_evaluation.md` §2.

---

## Decision gates (resolved at program definition)

- **DG1 — net layer:** ship C1 predicate; feature_051.multi_session_concurrency stays DEFERRED (user 2026-09-05). Template Tier-3 EXCLUDES net until multi-session is proven (DG3 default).
- **DG2 — feature numbering:** `next_feature_number()` is dirs-based; next scaffold = **feature_051**, which collides with the deferred concept's name (no dirs exist, only WORK.md prose). Resolution: this program's first feature TAKES 051; update the WORK.md prose reference from "feature_051.multi_session_concurrency" to "multi_session_concurrency (deferred, unnumbered)" in the same session. Renumbering the deferred concept if revived is mechanical (it has no artifacts).
- **DG3 — template scope:** Tier 3 is opt-in and excludes net (per DG1); receipt-guard + think-hard included as experimental flags.

---

## Execution rules (per session, per feature)

1. **Scaffold:** `uv run scripts/omt/new_feature.py "<name>" --type <tt> --project meta_harness_6` → declare phase → work → `omt_complete`. Waves 1–4 items are `minor_feature` (§12 decl-only); D1 is `major_feature` (design doc + TDD auto-on); E1's analysis pass may run as `docs` (no phase).
2. **Harness-surface discipline (every wave touches it):** fire `omt_net{op:fire, transition:"work_start"}` FIRST (g.net:35 live, fail-closed, skip_ok=false); receipt round-robin — ONE edit per harness file per round, parallel OK, ONE e2e refresh per round (`uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`); the e2e test file itself is receipt-EXEMPT (update its source pins first, shape-agnostic).
3. **Canary ordering:** declare `omt_phase` BEFORE `omt_skip{scope:tests}` and issue the skip immediately before the tests/ edit (GOTCHA_TESTS_CANARY_SHADOW). New test files need the canary (TDD_BOOTSTRAP) until/unless C2's narrowed auto-unlock ships.
4. **After each feature:** `uv run scripts/omt/harnessc.py check && build` (budgets must stay green — tool_args/tool_schemas have little headroom: 2226/2304 and 1612/1792), full suite green, e2e receipt refreshed, WORK.md synced by omt_complete, CURRENT_STATE.md entry (this project) logged.
5. **Overlap check before each scaffold:** scan `meta_harness_5` PROJECT.md backlog — its shipped/reject verdicts stand; do not re-implement shipped items (e.g. its #10 = feature_037).
6. **Wave 5 precondition:** D1 starts only after Waves 1–4 are complete or closed-with-verdict; its design doc should reuse `.sandbox/meta_harness_6_evaluation.md` §5 D1–D3 + this file's tier table.

---

## Status

- [x] Wave 1 — A1 ✅ DONE (feature_051.ledger_test_isolation, 2026-09-06) · F1 ✅ DONE (feature_052.opencode_version_canary, 2026-09-06: @var opencode_version_range >=1.18.29,<1.19 + session-start WRN + fail-loud canary suite, suite 1866/0) — **Wave 1 COMPLETE**
- [ ] Wave 2 — C1 net_gate_concurrency_predicate (= NEXT, takes number 053), C2 small_task_fast_path, A4 gate_preflight
- [ ] Wave 3 — A2+A3 skip_taxonomy_phase_hygiene, B1+B2 gate_budget_ceremony_meter
- [ ] Wave 4 — E2+E1 thought_review_gotcha_root_cause
- [ ] Wave 5 — D1 harness_tiered_template (+ D2 stack_profiles, D3 generated_onboarding)
- [ ] End-of-program re-evaluation vs §Baseline (delta report → Decisions log)
- [x] First linked feature flips this project draft → active (feature_051 linked 2026-09-06)

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — include all 13 items:** user decision 2026-09-05 ("include all") — every evaluation option is in scope; none dropped at definition time.
- **D2 — execution deferred to next sessions:** this session defines the program only; zero features scaffolded/executed (user: "to be executed in a next opencode session").
- **D3 — DG1/DG2/DG3 defaults locked:** net predicate over 051 (051 stays deferred); program takes feature number 051 (WORK.md prose reworded in the scaffold session); Tier-3 template excludes net.

---

## References

- Evidence base + full option detail: `.sandbox/meta_harness_6_evaluation.md` (same session, self-contained).
- Lineage: `.projects/meta/meta_harness_5/PROJECT.md` (prior review backlog from `.sandbox/meta_harness_3_idea.md` — overlap check per Execution rule 5).
- Operational state at definition: `.sandbox/pause_2026-09-05c.md` (feature_050 wrap-up; net rev 53; receipt/time-window discipline).
- Harness SSOT: `.meta/META_HARNESS.omt` (gates @GATE, budgets @BUDGET, tools @TOOL, vars @VAR).
- WORK.md Projects table row (synced by `uv run scripts/omt/project.py sync`).
