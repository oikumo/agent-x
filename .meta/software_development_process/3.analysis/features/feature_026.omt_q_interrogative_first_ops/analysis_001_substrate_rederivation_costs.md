# Analysis 001: Per-session substrate re-derivation costs the interrogative layer targets

> **Phase:** Analysis — `omt_agent_guide.md §1`–§4
> **Feature:** feature_026.omt_q_interrogative_first_ops
> **Design doc:** `4.design/features/feature_026.omt_q_interrogative_first_ops/design_001_omt_q_first_ops.md`

## Problem statement

Every OMT session re-derives ~2–4 KB of prose the agent already wrote in a prior
session. The harness *writes* the answer to most resume questions to the ledger
anyway — but provides no single read to get it back. A fresh session today reads
`WORK.md` + scratchpad + `.projects/<feat>/CURRENT_STATE.md` (only 2 of 25
features have one) + ledger tail-greps + thoughts + fsm + nav queries for
gotchas, then runs `git stash`+suite+re-derive to verify the `KNOWN_SUITE_FAILURES`
allowlist is intact, then discovers the gate chain by *being blocked*.

`feature_026.omt_q_interrogative_first_ops` adds a **9th `omt_*` tool — `omt_q`**,
read-only above v1 mechanics, that collapses the re-derivation ritual into
three fixed-shape ops: `op:state`, `op:plan`, `op:drift`. Every response carries
an `as_of_commit` envelope field (the v1.5 characteristic stub — always `HEAD`
in Phase-A). The single *mechanical* touch is one behavior-preserving refactor
of `gate_driver.runBeforeGates` to accept a synthetic `GateCtx` and return
decisions rather than throw.

## Current implementation

The agent has 8 `omt_*` tools (`omt_phase`, `omt_skip`, `omt_complete`,
`omt_tdd`, `omt_status`, `omt_think`, `omt_kb_nav`, `omt_nav`). All 8 are
*writes* or *single-substrate reads* — none cross-cuts the agent's substrates
to answer the actual resume questions:

- "What is the state of feature_X?" — re-derived by tail-grepping 3–5 ledger
  files + reading thoughts + scanning `CURRENT_STATE.md` + reasoning.
- "Will this edit hit a gate I don't know about?" — discovered by being blocked
  (`OmtBlock` from `IMPLS[gate.id]` propagates to the root before-hook).
- "Which AKB records have drifted?" — no way to ask at all (silent drift is a
  known state; see WORK_ARCHIVE L16).

The 16 nav-indexed gotchas exist precisely because these questions re-trip every
session — 3 of 16 are kept **inline in WORK.md's scratchpad** because they keep
recurring (TDD node-granularity, testlist JSON, receipt round-robin), and **0
`omt_nav{query:"GOTCHA_"}` calls** appear in any ledger — the gotchas are
*live-smoke skips*, not consults.

## Observed re-derivation costs (grounded in evidence)

The 15 re-derivation costs catalogued in the parent
`.projects/meta/meta_harness_2/PROJECT.md` collapse into 3 op-driver groups:

| Cost | Today's ritual | Token / wall-clock | `omt_q` op that collapses it |
|------|----------------|---------------------|------------------------------|
| #1 feature resume | 5 reads (WORK + scratchpad + projects + ledger tail + thoughts + fsm) | ~2.0–3.5 KB tokens / 5 reasoning turns | `op:state` (U1) |
| #2 gate blocks | Learn the gate chain by being blocked | ~1.2 KB per block→recover cycle | `op:plan` (U2) |
| #3 AKB drift | No way to ask — silent drift is known | (unknowable today) | `op:drift` (U3) |
| #4 TDD stranded reds | tail-grep `kind:"tdd"` + re-run pytest to verify | ~1.5 KB + ~30 s | `op:state` fold (U6) |
| #5 TDD closed-via-skip | Trust WORK.md DONE marker — silently loses hygiene | (silent loss) | `op:state` fold (U7) |
| #6 phase decree health | grep slug variants + eyeball FSM validity | ~1 KB / 3–5 turns | `op:state` fold (U8) |
| #7 skip reasons + live-smoke | per-feature skip grep + manual tally | ~12 KB archived | `op:state` fold (U9) |
| #8 `KNOWN_SUITE_FAILURES` | `git stash` + suite run + re-derive | MOST-CITED friction: "30 s saves hours" | `op:state` (no feature) (U10) |
| #9 receipt freshness | read `omt_harness_e2e_last_run.json` + mtime | ~0.6 KB × 19 mentions | `op:plan` fold (U11) |
| #10 think_consult dedup | re-`omt_think{op:list}` the same 14 files | ~2.4 KB per repeat | `op:state` fold (U13) |

**Critical path today:** the agent can only know *that* `KNOWN_SUITE_FAILURES`
exists by knowing the path `scripts/omt/tdd/state.py:132`. There is no surface
to ask "what's allowlisted?" — exactly the interrogation gap.

## Substrate inventory (verified live, 2026-08-09)

All atoms `omt_q` consumes already exist in v1:

| Substrate | Path | Current helpers that already read it |
|-----------|------|--------------------------------------|
| gate IR (7 before-gates, 2 after-gates) | `.meta/.omt/harness.ir.json` | `loadIr()` — `gate_driver.ts` iterates `gates[]` |
| ledger (phase, skip, think_consult, tdd, tdd_testlist, complete) | `.meta/.omt/ledger{,-YYYYMMDD}.jsonl` | `readLedger()` — hot + archive |
| thoughts index | `.meta/.omt/thoughts.jsonl` | `readThoughtsIndex()` — already used by `risk_high` pred |
| KB skeleton (records: id, kind, src, line, refs, tags, text, tier) | `.meta/.omt/kb.ir.json` | `loadKbIr()` — built by `kb_ast_extract.py` |
| receipt status | `.meta/.omt/omt_harness_e2e_last_run.json` | `omtHarnessE2eStatus(rel, abs)` — `receipt_guard.ts:53` |
| `KNOWN_SUITE_FAILURES` literal (Python `frozenset`, 6 node IDs) | `scripts/omt/tdd/state.py:132` | (none — pure parse target) |
| active feature phase | derived in `session_state.ts` | `getActiveFeaturePhase(feature, session)` — exact-match then 8 h-window |
| env.state maps (nav, kb, unlocked) | `env.state` in live TS | `getActiveUnlock(session)`, `hasNavUnlock(session)` |

**Cell counts (v1.5-reconciled, re-verified live 2026-08-09 17:55):**
- ledgers: `ledger.jsonl` 23 + `ledger-202608.jsonl` 415 + `ledger-202607.jsonl` 628 = **1066 records** (a new
  ledger.jsonl record since the v1.5 snapshot brings the live total to 1067 — within churn tolerance)
- kinds cross-ledger: think_consult 517 / phase 192 / skip 164 / complete 101 / tdd 80 / tdd_testlist 12
- 21 `feature:""` phase records (3 hot + 10 in 202608 + 8 in 202607)
- 12 `phase:""` records (2 hot + 9 in 202608 + 1 in 202607)
- 12 `tdd` `done`-with-false-checklist records across 4 features (U7 corpus)
- 63 of 123 skip records in 202608 are `"reason":"live smoke"` — uniformly `scope:"nav"`
- **0** `task(`/`subagent_type` hits across all ledgers — opencode's parallel-research affordance never used

## Live IR fingerprint correction (one item the parent doc got wrong)

The parent PROJECT.md repeatedly says "the 9 gates with `on:"before"`" (§Summary,
§Scope, §Architecture, §Phase-A build). The live IR today has **7 before-gates**
and **2 after-gates**:

| before (order) | id | when= | requires= | skip_ok |
|----------------|----|------|-----------|---------|
| 0  | `g.nav`     | `path_in(@var.doc_paths)`     | `session_flag(nav_used)`                       | true  |
| 10 | `g.protect` | `path_in(@protect.*)`         | (none — impl-owned)                            | true  |
| 20 | `g.receipt` | `path_in(@var.harness_paths)` | `receipt_fresh()`                              | false |
| 30 | `g.tests`   | `path_in(tests/)`             | `ledger_has(skip,tests_approved=true,@var.unlock_window_ms)` | true  |
| 40 | `g.phase`   | `path_in(src/)`               | `ledger_has(phase|skip)`                        | true  |
| 50 | `g.think`   | `file_has("TA:")`             | `ledger_has(think_consult)`                     | false |
| 55 | `g.kb`      | `path_in(src/)`               | `session_flag(kb_consulted)`                    | false |

| after  | id          | when=                |
|--------|-------------|----------------------|
| 60 | `g.mvc`      | `path_in(src/**/*.py)` |
| 70 | `g.tdd_after` | `path_in(src/)`        |

**Design implication:** the `op:plan` doc text "9 before-gates" becomes
"7 before-gates" in the implementation. The change is a doc-count correction,
not a behaviour change — `op:plan` filters `gates.filter(on==="before")`
dynamically, so the count comes from the IR, not a hardcoded literal.

## The TA: self-trigger recursion (edge case #2 — concrete build step)

`gate_driver.ts` itself contains the literal string `"TA:"` (the `file_has("TA:")`
predicate implementation, plus the FALLBACK_GATES `g.think` stub at line 233
`'file_has("TA:")'`). `g.think`'s `when=` is `file_has("TA:")` — so editing
`gate_driver.ts` triggers `g.think` on the very file that implements think-gate
prediction.

This is **the build order, not a paradox**: the build-sequence bootstrap makes
`omt_q{op:plan, path:".opencode/lib/enforcer/gate_driver.ts"}` the first call
against the freshly-implemented plugin — predicting `g.think` *before* the
refactor edit, then `omt_think{op:list, path:"…"} consult → edit. The
interrogative layer constructs itself through its own prediction; the highest-risk
canary (Risks #1) is also the v1.3 thesis demonstration.

## Constraints discovered

- **v1 lock** (`AGENTS.md` + parent PROJECT.md §Vision "above the mechanics,
  not into them") — no new gates, no ledger semantics change, no enforcer
  relocate, no TDD engine rewrite. The single *mechanical* touch is the
  `gate_driver.runBeforeGates` synthetic-`GateCtx` + `dryRun` refactor
  (catch-and-capture instead of throw).
- **Behaviour-preservation pin** — `tests/scripts/omt/test_omt_enforcer_guard_source_pins.py`
  pins the before-hook edit path to `output?.args?.filePath`, the after-hook to
  `input?.args?.filePath`, and the `g.think` self-trigger must keep firing on
  `gate_driver.ts`. The refactor must keep real edits throwing `OmtBlock`; only
  the `dryRun:true` variant catches and captures.
- **`omt_q.ts` is in `@var.harness_paths`** — `.opencode/plugins/omt_` is a
  listed harness path → editing `omt_q.ts` will trigger `g.receipt` (the v1
  second-edit guard). This is *the very receipt-round-robin* the layer is built
  to interrogate (U11); each harness-file edit needs one fresh
  `tests/scripts/omt/test_omt_harness_e2e.py` run.
- **`KNOWN_SUITE_FAILURES` parse-not-import** — importing
  `scripts/omt/tdd/state.py` from a TS plugin pulls in `subprocess`/`pytest`
  machinery. `op:state` reads the file and regex-extracts the `frozenset({...})`
  literal with one regex. Fail-open with `KNOWN_SUITE_FAILURES_parse_failed`
  flag if the regex misses (the constant is a build-time literal — a move/rename
  surfaces immediately to the agent).
- **Slug drift is reported, not fixed** — `feature_024`'s work appears under 5
  distinct slug variants (`feature_024`, `feature_024.x`,
  `feature_024.no_tui_full_features`,
  `feature_024.context_window_optimization`,
  `feature_024.no_tui_react_sync`). `op:state`'s U8 fold canoncialises by
  scanning phase records whose `scope` text contains the feature token (after
  stripping `feature_024.`→ `feature_024`), aggregating across variants. The
  canonical slug is the most-recently-used one. *Canonicalization is a
  v1-process change (make `omt_phase.feature` required) — out of scope.*
- **`tdd_testlist` session-bleed** — the most recent `tdd_testlist` record
  (feature_025, 2026-08-09T00:46:55) has `session:""`. `op:state`'s TDD-position
  derivation joins `tdd_testlist` to `tdd` records by `feature` (not session).
- **Phase-A `as_of_commit` is always `HEAD`** — Phase-A parses `git rev-parse
  HEAD` at call time and stamps every response envelope. The `as_of:"<commit>"`
  *reconstruction* parameter is Phase-B U18 (out of scope) — but the envelope
  field ships in Phase-A so two calls against the same commit return byte-identical
  `as_of_commit` values (proving the stub is a deterministic field).

## Phase-A last-build additions vs parent doc

The v1.4 doc adds three telemetry fields to the `kind:"q"` ledger record (the
Phase-B evidence gate substrate):

- `op_set:[<folds used>]` — which folds were invoked on this `omt_q` call
- `fold_used:"<comma-separated U#>"` — quick-red on the use-case coverage
- `latency_ms:<int>` — single-op wall-clock budget (target < 1500 ms per
  Success criteria §(b))

These are pure additions to the v1.3 schema: `op` / `feature?` / `session` /
`ts` already there + `op_set` / `fold_used` / `latency_ms` + v1.5 `as_of:"HEAD"`.

## Non-goals (explicit out-of-scope)

- **No HQL grammar** — all 18 use cases ship as fixed-shape op-parameters
  (`op === "state" | "plan" | "drift"`, parameterised by `feature` / `path` /
  `session` / `as_of`). Grammar is a Phase-C+ bet gated on Phase-A+B evidence
  the agent asks questions not expressible as fixed-shape ops.
- **No `as_of:"<commit>"` temporal traversal in Phase-A** — the envelope ships
  (`as_of_commit:"HEAD"` per call); the *reconstruction* machinery
  (`git show <commit>:<path>` over IR + ledger tail + thoughts + kb + state.py)
  is Phase-B U18.
- **No slug-normalization fix** — U8 reports the 21 `feature:""` + 12 `phase:""`
  records; *fixing* them is a v1-process change (`omt_phase.feature` required,
  `phase` validated against FSM enum). The fix is out of scope.
- **No after-gates in `op:plan`** — the 2 after-gates (`g.mvc`, `g.tdd_after`)
  consume a *post-edit* snapshot. `op:plan` projects the 7 before-gates only.
- **No `op:audit`, `op:graph`, `op:plan_after`** — U4 (ordered skips across a
  feature), U5 (transitive risk with `depth`), `op:plan_after` (MVC delta
  predict) all deferred to Phase-B/C.
- **No subagent enforcement** — U16 (Phase-B candidate) is advisory-only; the
  harness never *forces* a `task{subagent_type:explore|general}` delegate-out.
  The v1 lock preserves agent autonomy.

## Recommendation

Proceed to Design with the Phase-A locked surface:

- **3 ops:** `op:state{feature?, session?, as_of?}`, `op:plan{path, tool?, session?, as_of?}`,
  `op:drift{as_of?}`.
- **7 folded ledger/IR projections:** U6 / U7 / U8 / U9 (+`live_smoke_count`
  named field) / U10 / U13 on `op:state`; U11 on `op:plan`.
- **`as_of_commit:"HEAD"` envelope on every response** — parsed live via
  `git rev-parse HEAD`.
- **Single mechanical touch:** `gate_driver.runBeforeGates` gains a
  synthetic-`GateCtx` / `dryRun:true` return-decisions variant (catches
  `OmtBlock` from `IMPLS[gate.id]`, captures `{gate_id, blocked, msg, skip_ok}`
  instead of propagating; real edits still throw on the existing path).
- **Single new read:** `KNOWN_SUITE_FAILURES` regex extractor over
  `scripts/omt/tdd/state.py`.
- **Call telemetry:** a `kind:"q"` ledger record per `omt_q` call (`op`,
  `feature?`, `session`, `ts`, `op_set`, `fold_used`, `latency_ms`, `as_of:"HEAD"`).

Test bar = golden queries for U1/U2/U3 + U6–U11 + U13 (+ U9 `live_smoke_count`
assertion + U7 cross-feature FP guard + U8 near-collision slugs + U2
pre-flight == real `tool.execute.before` chain, including the `gate_driver.ts`
self-trigger + U3 count-drift direction-b only + v1.5 `as_of_commit` envelope
assertion on every golden). Full regression must stay green (1196+ baseline,
`KNOWN_SUITE_FAILURES` allowlist of 6 IDs unchanged).
