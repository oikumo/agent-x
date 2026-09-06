# PROJECT: meta_harness_7 — Meta Harness 7 — Work-Performance Improvement Program

> Status: **active** · **v0.2 (2026-09-06)** — created by `project.py new`, program definition filled same session (work-friction deep analysis). Iterate freely (non-gated); spawn features with `new_feature.py "<name>" --type <tt> --project meta_harness_7`; log sessions in CURRENT_STATE.md (newest on top).

---

## New Session Quick Start

> One line: `meta_harness_7` is the **11-item work-performance program distilled from the 2026-09-06 performing-work analysis** (evidence: `omt_status` + `omt_q state/plan/drift` this session) — 3 waves: quick-wins → structural → productization; **PROGRAM DEFINED, ZERO EXECUTED** (see CURRENT_STATE.md iter 1; verdicts D1–D3 below).

**Next:** read §Decision gates → §Execution rules → §Baseline, then scaffold Wave 0 / P0-2 (`dangling-active-only`, minor_feature) per Execution rule 1.

---

## Summary (one line)

**All 11 work-friction improvements from the 2026-09-06 performing-work analysis, sequenced into 3 waves (4 quick-wins + 4 structural + 3 productization), aimed at: fewer denials before real work, cheaper consults, quiet dangling/noise, headroom-safe budgets, and a workflow discovery path that doesn't tax tokens.**

---

## Purpose

### What this project is

- The **execution program** for every improvement option accepted in the 2026-09-06 performing-work analysis ("include all"): items P0-1–P0-4, P1-1–P1-4, P2-1–P2-3 (detail per item: evidence, mechanism, acceptance @ §The program + `.sandbox/` analysis thread 2026-09-06).
- **Self-contained**: a fresh session needs only this file + CURRENT_STATE.md iter 1 — no conversation history required.
- A **measured program**: the baseline (skips, dangling, ceremony, gates, budgets, drift, suite) is recorded in §Baseline so the end-of-program re-evaluation can compute deltas.

### What this project is **not**

- NOT executing anything now — this session only defined the program (features are scaffolded and executed in later sessions, one feature per item/group).
- NOT a re-litigation of `meta_harness_6` verdicts (D4–D6 + DG1–DG3 locked: suite 1979/0, KNOWN empty, net solo-only, Tier-3 excludes net) or of `meta_harness_5` backlog (check its backlog for overlap before each scaffold).
- NOT weakening `g.think` / `g.protect` semantics, NOT blanket `tests/` auto-unlock, NOT a new gate without a retirement (B1 net-zero holds).

---

## Scope & success criteria

**Scope:** all 11 items below, each shipped as its own feature through the full OMT++ process, in wave order (within a wave, order is the listed order). Grouped scaffolds allowed where noted (P0-2+P0-4 status/message-only may ride together only if receipt discipline allows — default is one feature per item).

**Success criteria (project-level):**

1. All 11 items shipped OR explicitly closed-with-verdict in Decisions log.
2. Suite stays **1979+ green / 0 failed** with KNOWN allowlist empty (shape-pinned); `harnessc check` 0 errors + `build` OK after every feature; all 12 byte budgets green.
3. Work-friction deltas vs §Baseline: `nav-escapes 53 → <20 /7d`; second-edit-in-same-feature `plan` passes without a new consult; `evasion` stays ≤3/7d with `warn>5/week` alarm armed.
4. Dangling section fits one screen: unexpired list ≤10 lines + `expired GC count` line (P0-2); `drift project_drift 11 → 0` (P1-3).
5. Zero `tdd_node` blocks at `done` for features shipped under this program (P1-2); zero `tests_canary_shadow` re-occurrences.
6. End-of-program re-evaluation vs §Baseline shows: ceremony medians still 0 with real `bug_fix` sessions measured; consults/session and denials/session trend down; no new gate without retirement (`@budget gates 10/12` held).

**Out of scope / guardrails:**

- `g.think` and `g.protect` semantics are NOT weakened by any item (P0-3/P1-1 explicitly exclude them; `risk:` stays per-file).
- No auto-unlock of the tests canary beyond C2's narrowed condition (own test dir, RED hat active only).
- No new gate may be added without retiring/merging one (B1 policy).
- Tier-3 template still excludes net (DG1/DG3 from meta_harness_6 stand); P2-3 receipt batching stays fail-closed outside its stage.

---

## The program — 11 items in 3 waves

> Per-item: what / why (evidence) / mechanism (HDL hook) / size (§12 task type). Evidence base: `omt_status` 2026-09-06 (Skips 82, Dangling 101/91-expired, Ceremony 0s, Gates 10/12), `omt_q state` (risky 101, live_smoke 46), `omt_q plan(edit,src)` (only `g.kb` blocks solo), `omt_q drift` (11 unlinked-project-backed), `.workflows/META §8` (deferred `omt_workflow` tool + `gates:` field).

### Wave 0 — Quick wins (status/message/flag only, execute first)

| # | Item | What | Why (evidence) | Mechanism | Size |
|---|---|---|---|---|---|
| P0-1 | `preflight-on-declare` | `omt_phase` success response embeds `preflight(edit, <feature own dirs>)` projection (ordered gates + clearing actions) | A4 exists but opt-in; first-denial still costs a turn | `phase_gate.ts` reuses `runBeforeGatesDry` read-only, no schema growth | minor |
| P0-2 | `dangling-active-only` | `omt_status` lists ≤10 *unexpired* dangling + `expired GC count` line; expired auto-hide (+1 session grace) with existing one-call abandon/resume | 101 shown, 91 expired — noise hides 9 real resumes | status-only filter in `session_state.ts` | minor |
| P0-3 | `kb-sticky-per-feature` | `kb_consulted` scoped to `feature+session`: first `kb_nav` satisfies later `src/` edits for same feature/session; majors re-consult on scope change | `plan` demo: 6/7 pass, only `g.kb` blocks solo | C2-precedent ledger flag + `gate_driver` OR; think/protect untouched | minor |
| P0-4 | `nav-cache-hit` | Blocked-`grep` denial appends top-3 nav index hits for the query stem | 53/82 skips are `scope:nav` — relevance miss, not defiance | `nav_gate.ts` message only, no policy change | minor |

### Wave 1 — Structural (one `minor_feature` each)

| # | Item | What | Why | Mechanism | Size |
|---|---|---|---|---|---|
| P1-1 | `think-batch-consult` | `omt_think{op:list, path:[...]}` or `query:`-scoped consult clears gate for matched files; `risk:` stays per-file | 101 risky / 40 files re-pay per file per session | `think_gate.hasConsultedThoughts` set-semantics + ledger `files[]` | minor |
| P1-2 | `tdd-same-node-lint` | `omt_tdd{op:green/refactor}` warns when `test_node` ≠ latest `red` node for same feature before running toolchain | `GOTCHA_TDD_NODE` blocks `done` late | `tdd/state.py` latest-wins check + message | minor |
| P1-3 | `project-autolink` | `drift` detail gains exact `project.py link --infer` command; `check_projects` fix-it for hand-added design docs | 11 unlinked-backed (`feature_kb_akb` x10 + `workflows` x1) | status/drift-only | minor |
| P1-4 | `budget-diet-bot` | `build` warns with `suggest -N bytes: longest @tool describes` when within 64B of any byte cap | tightest `tool_args -26B, schemas -22B, nav_index -77B` — surprise diets today | `harnessc.py` report hint only | minor |

### Wave 2 — Productization (needs design; only after Waves 0–1)

| # | Item | What | Why | Mechanism | Size |
|---|---|---|---|---|---|
| P2-1 | `omt-workflow-index` | `omt_workflow` tool: `list(subject?) + plan(workflow)` from subject manifests; machine `gates:` frontmatter (`follow\|override`) | `.workflows/META §8` deferred: two-level manual read costs tokens, stance is prose | new tool + compiler, net-zero gate aware | minor (+ design note) |
| P2-2 | `subagent-fanout-recipe` | One loop recipe: `explore (read-only) → propose → approval → execute` with ledger-session scoping so parallel probes don't shadow canary | `.agents/agents/` empty, invariant says "prefer sub-agents" with no recipe | docs + 1 workflow file | minor |
| P2-3 | `receipt-batch-mode` | `harnessc.py stage --feature N` snapshots mtimes, allows N files, single `e2e` at end if `check` green; fail-closed outside stage | receipt round-robin (`ONE edit/file/round + refresh`) dominates harness work turns | `receipt_guard` stage mode + F1-style live canary | minor |

---

## Baseline (2026-09-06, for end-of-program delta)

- Ledger 7d: skips **82 (friction 26 · nav-escapes 53 · evasion 3, warn>5/week)** · dangling **101 (91 expired)** · ceremony medians **bug_fix 0 · minor 0 · docs 0 · test 0 · major 0 · refactor 0 (alarm bug_fix>3)** · gates **10/12 net-zero** · tools **10**.
- Cumulative (meta_harness_6 close iter 10): think_consult **759** · phase **368** · skip **309** · q **267** · complete **195** · tdd **179** + testlist **32** · net **rev 57 dormant solo** · pool **pending=0/active=0/done=7, places 12/15**.
- Suite **1979/0**, KNOWN empty shape-pinned · lint **0 err / 36 warn** · budgets 12 green (tightest: tool_args −26B, schemas −22B, nav_index −77B) · records **263** · app src **22794 (zero drift)**.
- Knowledge: risky_thoughts **101** · recent_consults 31 · live_smoke 46 · drift records **0** + project_drift **11 unlinked-backed** · gotchas **18 clustered**.

---

## Decision gates (resolved at program definition)

- **DG1 — include all 11:** user decision 2026-09-06 ("include all the improvements") — every performing-work option is in scope; none dropped at definition time.
- **DG2 — execution deferred:** this session defines the program only; zero features scaffolded/executed (features ship in later sessions per Execution rules).
- **DG3 — inherited locks stand:** meta_harness_6 D1–D6 + DG1–DG3 (net solo-only, Tier-3 excludes net, KNOWN stays empty, gates net-zero) — do not re-litigate without new evidence.

---

## Execution rules (per session, per feature)

1. **Scaffold:** `uv run scripts/omt/new_feature.py "<name>" --type minor_feature --project meta_harness_7` → declare phase → work → `omt_complete`. P2-1 gets a short design note (not a §12 major gate); all others are `minor_feature` (§12 decl-only). Grouped scaffolds allowed only where noted.
2. **Harness-surface discipline (every wave touches it):** receipt round-robin — ONE edit per harness file per round, parallel OK, ONE e2e refresh per round (`uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`); the e2e test file itself is receipt-EXEMPT (update its source pins first, shape-agnostic). P2-3 builds the stage mode; until it ships, manual discipline holds.
3. **Canary ordering:** declare `omt_phase` BEFORE `omt_skip{scope:tests}` and issue the skip immediately before the tests/ edit (GOTCHA_TESTS_CANARY_SHADOW). New test files need the canary (TDD_BOOTSTRAP) unless C2's narrowed auto-unlock (own dir + RED) applies.
4. **After each feature:** `uv run scripts/omt/harnessc.py check && build` (budgets must stay green — tool_args/schemas/nav_index have ~20–70B headroom; P1-4 owns the warning), full suite green, e2e receipt refreshed, WORK.md synced by omt_complete, CURRENT_STATE.md entry (this project) logged.
5. **Overlap check before each scaffold:** scan `meta_harness_5` + `meta_harness_6` PROJECT.md backlogs — shipped/reject verdicts stand; do not re-implement (e.g. C2 fast-path, A4 preflight, B1 budget, E2 review).
6. **Wave 2 precondition:** P2 items start only after Waves 0–1 are complete or closed-with-verdict; P2-1's `gates:` design must reuse `.workflows/META.md` §4 + §8 + this file's P2-1 row.

---

## Status

- [ ] Wave 0 — P0-1 `preflight-on-declare` · P0-2 `dangling-active-only` ✅ DONE (feature_060, 2026-09-06: active-only ≤10 + expired GC, suite 1981/0) · P0-3 `kb-sticky-per-feature` · P0-4 `nav-cache-hit`
- [ ] Wave 1 — P1-1 `think-batch-consult` · P1-2 `tdd-same-node-lint` · P1-3 `project-autolink` · P1-4 `budget-diet-bot`
- [ ] Wave 2 — P2-1 `omt-workflow-index` · P2-2 `subagent-fanout-recipe` · P2-3 `receipt-batch-mode`
- [ ] End-of-program re-evaluation vs §Baseline (delta report → Decisions log → close program)
- [x] First linked feature flips this project draft → active (feature_060 linked 2026-09-06)

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — include all 11 items:** user decision 2026-09-06 ("include all the improvements") — every performing-work option is in scope; none dropped at definition time.
- **D2 — execution deferred to next sessions:** this session defines the program only; zero features scaffolded/executed.
- **D3 — DG1/DG2/DG3 + meta_harness_6 locks stand:** net solo-only with Tier-3 excluding net; KNOWN empty; gates net-zero; think/protect not weakened; tests canary narrowed-only.

---

## References

- Evidence base this session: `omt_status` (Skips 82, Dangling 101, Ceremony 0s, Gates 10/12) + `omt_q state/plan/drift` + `omt_think{op:list, query:risk}` + `.workflows/META.md` + `.workflows/meta_harness/META.md` + `loops/meta_harness_project.md`.
- Lineage: `.projects/meta/meta_harness_6/PROJECT.md` (prior program, closed 2026-09-06, suite 1979/0) + `.sandbox/meta_harness_6_evaluation.md` (architecture scorecard + economic model) + `.projects/meta/meta_harness_5/PROJECT.md` (overlap check per Execution rule 5).
- Harness SSOT: `.meta/META_HARNESS.omt` (gates @GATE, budgets @BUDGET, tools @TOOL, vars @VAR).
- WORK.md Projects table row (synced by `uv run scripts/omt/project.py sync`).
