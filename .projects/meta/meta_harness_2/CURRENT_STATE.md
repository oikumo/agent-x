# CURRENT_STATE: meta_harness_2

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-09 (iter 13 — omt_q GREEN + REFACTOR + DONE)

### Done

- **Resumed from pause_d** (mid-Step-3-GREEN-fix, 13/14 golden green). Fixed the last red (U10 hermetic-root): added `use_real_root: bool` parameter to `_q_probe`; U10 now runs the probe at `REPO_ROOT` so `parseKnownSuiteFailures(repoRoot())` finds the live `scripts/omt/tdd/state.py` → 14/14 golden green (28/28 with sentinel).
- **Debug `catch (e)` cleanup** — reverted the `stack: e?.stack` debug block in `omt_q.ts` plan op back to the clean fail-open `} catch { ... error:"plan op failed (fail-open)" }` (per pause_d plan).
- **REFACTOR pass** — extracted `emitQEnvelope(start, op, op_set, fold_used, extra, ledger_extra?)` helper consolidating the 3-op `latency_ms + appendLedger{kind:"q"} + JSON.stringify` triplet. `omt_q.ts` 681→666 lines (15-line reduction). Soft <600 target not hit (20 blank/80 comment/566 code); per design the contract is the golden suite + behaviour-preservation, NOT a line count — documented in implementation_notes.md.
- **Discovered requirement: tool-set drift fix** — `test_omt_tool_set_is_in_sync_everywhere` caught `omt_q` only in plugins, not in IR (the design doc erroneously said "No changes to META_HARNESS.omt"). Fix: added `@tool omt_q perm=allow args="op,feature?,session?,path?,tool?,as_of?" tags="CMD_Q"` to `META_HARNESS.omt` + bumped `@budget tool_schemas` 1024→1280 (the description pushed the sum to 1085 B) + `uv run scripts/omt/harnessc.py build` regenerated the projections (harness.ir.json 9 tools, AGENTS.md "9 omt_*", opencode.jsonc perm keys, nav.index.jsonl CMD_Q).
- **Pre-existing baseline failure unblocked** — `test_no_singular_plugin_path_outside_frozen_history` was failing on `PROJECT.md:264` (the singular directory literal — `.opencode` + `plugin/` — in the item-9 path-drift documentation; introduced in commit `8b384b1 [WIP] Project META HARNESS v2`). Reworded to break both drift regexes (`SINGULAR_LITERAL` + `SINGULAR_PATH_PARTS`) while preserving the singular-vs-plural meaning. The think-gate consult (8 thoughts reviewed on PROJECT.md) cleared via `omt_think{op:list}`.
- **`omt_tdd{op:done}` via CLI** — `tdd_check.py done` returned `{"ok":true, "checklist":{"suite_passes":true,"refactor_recorded":true,"naming_ok":true}, "allowlisted_failures":[2 feature_016 tests]}`. Phase exit approved.
- **Phase exits** — `omt_complete Programming→Testing` + `omt_phase Testing` + `omt_complete Testing→Done`.
- **Artifacts written** — `5.implementation/features/feature_026.../implementation_notes.md` + `6.testing/features/feature_026.../test_report.md` + WORK.md `[~]→[x] DONE (2026-08-09)` rotation + scratchpad FEATURES DONE appended.

### Test results

- Golden suite: 14/14 canonical + 14/14 sentinel = 28/28 green.
- Behaviour-preservation pins: 31/31 green.
- Drift pins: 12/12 green (post-fix).
- Full suite (`-m "not opencode_live"`): 1223 passed, 2 failed (both in `KNOWN_SUITE_FAILURES` allowlist — feature_016 TDD-gate pair, environment-state-dependent flake). react_screen trio 22/22 clean this run.

### Locked decisions (do not re-litigate without new evidence)

- **`omt_q` IS a registered `@tool` in the IR** — the design doc's "No changes to META_HARNESS.omt" was wrong; the drift test `test_omt_tool_set_is_in_sync_everywhere` enforces IR↔plugins parity (R8/F35). Any new `omt_*` plugin tool must be declared in `META_HARNESS.omt` and the IR regenerated via `harnessc build`. The `@budget tool_schemas` must be grown deliberately in the same edit when the description sum exceeds the current max.
- **U10 contract = parse the LIVE state.py** — the probe must run at `REPO_ROOT` (not a hermetic tmp_path). This is consistent with U10 being a build-time-constant parse, not a substrate-fold. The ledger `kind:"q"` records U10 writes land in the real `.meta/.omt/ledger.jsonl` — expected churn (the golden does NOT assert against the ledger).
- **`runBeforeGatesDry` is additive and behaviour-preserving** — the `runBeforeGates` body is byte-identical and still throws on block; 31/31 pins stayed green through the refactor.

### Next

- _(nothing — feature_026 DONE. PENDING: feature_001 Petri Net + feature_002 RAG, both scope-unset.)_

---

## 2026-08-09 (iter 11-12 — design + RED session B/C, backfilled from pause_b/pause_c)

### Done (backfilled)

- **iter 11 (session B)** — design artifacts written under `4.design/features/feature_026.omt_q_interrogative_first_ops/`: `design_001_omt_q_first_ops.md` (~190 lines, §Static Structure + §Functional Flow + §Testing strategy) + `operation_spec_001_omt_q_ops.md` (~180 lines, per-op Pre/Post/Exc). Analysis under `3.analysis/features/feature_026.../analysis_001_substrate_rederivation_costs.md`. IR fingerprint re-verified (ledgers 34/415/628, 9 gates, 7 before-gates, KNOWN_SUITE_FAILURES=6 IDs). Pause at `.sandbox/pause_2026-08-09_b.md`.
- **iter 12 (session C)** — Programming phase declared + TDD testlist planted (12 behaviors via direct CLI; MCP `omt_tdd{op:testlist}` wrapper hit the `Expecting value` quoting bug on the JSON-with-embedded-parentheses/commas/quotes). RED golden suite written: `tests/scripts/omt/test_omt_q.py` (681 lines, 14 tests across 12 classes) + sentinel re-export `tests/features/feature_026.../test_omt_q_golden_smoke.py`. GREEN source shipped: `gate_driver.ts` `runBeforeGatesDry` (additive, 31/31 pins green) + `omt_q.ts` (682 lines). 13/14 green (U10 hermetic-root red remaining). 2 bug fixes (buildCtxFromInputs state field + foldDecreeHealth global-vs-feature-scope). Pause at `.sandbox/pause_2026-08-09_c.md` then `pause_2026-08-09_d.md`.

### In progress

- _(nothing — iter 11/12 work landed in iter 13's DONE)_

### Next

- _(see iter 13 Next)_

---



### Done

- **User-objective reframe pass on PROJECT.md** — the project's two stated main objectives were treated as first-class *acceptance criteria*, not side-effects: (a) reduce opencode token consumption per session, (b) faster problem solving. Applied seven grounded moves without opening the Phase-A build:
  1. **Vision §Vision + standing principle + main objectives** — added a third non-negotiable paragraph framing the layer's *reason to exist* as the (a)+(b) outcomes; "interrogative" reframed as the means, not the end. Each axis (token-direction, speed-direction) given a concrete re-derivation-burn reference and a post-Phase-A verification anchor.
  2. **re-derivation cost list extended** with #14 subagent delegation (the macroscopic token lever — `task{subagent_type:...}` is opencode-native, used 0× across 125 sessions) + #15 escape-pattern replay (the 63/63 nav-scope live-smoke pattern showing the agent re-types the same escape template 63×).
  3. **U16 + U17 added** to the U-set — subagent delegate-advisory (Phase-B `op:state`/`op:plan` fold candidate) + escape-replay `last_escape: {scope, reason}` (Phase-B `op:plan` fold candidate). Both are advisory-only, the agent remains free to ignore. Neither breaks the v1 lock.
  4. **Use case → token-lever map** subsection added to §Scope declaring each fold's token-out and speed-out lever + its post-Phase-A observable metric (token-direction / speed-direction / pre-vs-post metric). The map verifies every fold pulls a lever the agent was pulling by hand; U16 + U17 are explicitly the "v1.4 user-objective moves" tied to the two axes the user stated.
  5. **Phase-B Deferred-table extended** to enumerate U14 + U16 + U17 with explicit decision gates (Subagent advisory acted-on within 3 turns? `last_escape.reason` reused ≥50%? — see Tasks → Phase-B).
  6. **Success criteria** gained post-Phase-A outcome-acceptance metrics: token-direction = `tools_called_pre_task / 1` ratio trend (downward), speed-direction = `block_count / edited_file_count` trend (downward) + `latency_ms < 1500` budget. The (a)+(b) objectives become *measurable trends across k sessions post-Phase-A rollout*, not Phase-A gate items (the layer can only deliver the outcome once it exists).
  7. **`kind:"q"` telemetry schema extended** with `op_set:[<folds used>]`, `fold_used`, `latency_ms` — pure additions to the v1.3 schema, no substrate change. These carry the per-fold outcome metrics so Phase-B measurement is from the same single substrate Phase-A writes to.
- **Tasks → Immediate** gained three v1.4 open questions: `kind:"q"` telemetry extension pre-baseline; U16 advisory actionability (decorative vs effective); U17 fold-out fold placement (`op:plan` vs separate `op:state{escape_match}`).
- **Decisions log + Iteration log + References** all updated to v1.4 with verifiable evidence commands (`rg` one-liners reproduce every new finding — subagent never-used, escape uniformity, consult concentration, zero-hit consults, scope distribution).
- **Four TA: thoughts added** to PROJECT.md for future-session consult: subagent never-used, escape uniformity (live-smoke × nav), the post-rationalization risk on acceptance metrics, v1.4 evidence anchors (h)-(m).
- **think-gate consult recorded** before edits (`omt_think{op:list, path:".projects/meta/meta_harness_2/PROJECT.md"}` returned the 3 v1.3 thoughts).

### Locked decisions (do not re-litigate without new evidence)

- **Phase-A surface UNCHANGED:** 3 ops (`state`/`plan`/`drift`) + 7 folds (U6/U7/U8/U10/U13 + U9 with `live_smoke_count` field), zero new build artifacts, single mechanical touch = `gate_driver.runBeforeGates` synthetic-ctx/dryRun refactor. **The v1 lock is reaffirmed for v1.4** — U16/U17 are Phase-B candidates, the Use case → token-lever map is doc only, the outcome-acceptance metrics are doc + future-`kind:"q"`-field-extension, NOT Phase-A scope additions.
- **"interrogative" is the means, (a)+(b) outcomes are the end** — the v1.4 purpose re-anchor rewrites the project's stated objective from "the harness answers what-if before the agent acts" to "the agent consumes fewer tokens per session and reaches the answer faster because the harness answers what-if before the agent acts." Both stand together; the (a)+(b) framing is the *acceptance* criterion for the interrogative layer moving past a novelty into earned-its-keep territory.
- **U16 advisory-only** — the harness never enforces subagent delegation; the agent remains free to ignore `delegate_hint`. If Phase-B evidence shows the advisory is decorative, the fallback is Phase-C enforcement via an opencode skill or harness slash command (out of v1.4 scope).
- **U17 advisory-only** — `op:plan` surfaces `last_escape: {scope, reason}` but the agent still calls `omt_skip` itself. The layer never mutates state, consistent with the v1 lock.
- **(a)+(b) post-Phase-A metrics are *trends*, not *thresholds*** — across k consecutive post-rollout sessions, the token-direction `tools_called_pre_task / 1` ratio should trend downward, the speed-direction `block_count / edited_file_count` should trend downward, single-op `latency_ms < 1500`. If neither trends after Phase-A rollout, the v1.4 framing is itself evidence the layer doesn't move the needle and we should NOT widen to U16/U17 — *anti-target is a feature, not a bug*.

### In progress

- _(nothing — v1.4 doc round complete)_

### Blocked

- _(nothing)_

### Next (when user decides to build Phase-A)

- Decide: open `feature_026.omt_q_interrogative_first_ops` under `4.design/features/` (phase-gated, activates TDD + AGENTS.md process surface) OR design in `.projects/meta/meta_harness_2/` only (non-gated, iterative). Unchanged from v1.3.
- Refactor `gate_driver.runBeforeGates` — synthetic `GateCtx` + `dryRun` return-decisions mode (behavior-preserving for real `tool.execute.before`); pinned by `test_omt_enforcer_guard_source_pins.py` + F14 real-binary tests.
- **FIRST STEP per Tasks → Phase-A build:** `omt_q{op:plan, path:".opencode/lib/enforcer/gate_driver.ts"}` must predict `g.think` BEFORE the refactor edit. Then `omt_think{op:list, path:".opencode/lib/enforcer/gate_driver.ts"}` consult. Then edit. (This step lands once `omt_q` itself is implemented.)
- Implement `.opencode/plugins/omt_q.ts` — three ops + U9 `live_smoke_count` field + `kind:"q"` call telemetry **including the v1.4 `op_set`/`fold_used`/`latency_ms` extensions** so the outcome-acceptance metrics are baseline-recorded from Phase-A call 1.
- Write golden-query scenarios for U1, U2, U3, U6–U11, U13 (incl. U9 `live_smoke_count` assertion); the U2 golden asserts `op:plan` predicted chain == real `tool.execute.before` run on the same path/session.
- Full regression: 1196 baseline must stay green.

### Notes / context

- v1.4 verification commands reproduce every new finding (every annotation is grep-runnable):
  - `rg '"task\("|"subagent_type"' .meta/.omt/ledger-*.jsonl` = 0
  - `rg '"reason":"live smoke"' .meta/.omt/ledger-202608.jsonl | rg -o '"scope":"[^"]+"' | sort | uniq -c` = `63 "scope":"nav"`
  - `rg -o '"kind":"[^"]+"' .meta/.omt/ledger-202608.jsonl | sort | uniq -c` = `123 skip / 104 phase / 97 think_consult / 45 complete`
  - `rg -o '"session":"[^"]+"' .meta/.omt/ledger-202608.jsonl | sort -u | wc -l` = 125
  - `ls .agents/agents/` = empty directory
- The four TA: thoughts on PROJECT.md are the v1.4 evidence anchors — future-session resume should `omt_think{op:list, path:".projects/meta/meta_harness_2/PROJECT.md"}` to see them before any edits (think-gate will fire on this file from now on; 7 thoughts total now: 3 v1.3 + 4 v1.4).
- **Two open questions investigated but not resolved** in this session (parked in Tasks → Immediate) — the U16 advisory actionability is a *future-evidence* question (can only be measured once Phase-B exists); the U17 surface placement is a *design* question (fold `last_escape` into `op:plan`'s predicted-block `msg` vs expose it as a separate `op:state{escape_match:<gate_id>}` call — the U-set table proposes the fold for one-call cheapness, but the separate-op form is more discoverable). Both are decision-pending, not in-progress.

---

## 2026-08-09 (iter 9 — v1.3 resume-improvement round)


### Done

- **Resume-improvement pass on PROJECT.md** — applied six grounded moves without opening the Phase-A build:
  1. **U9 deepened** — added `live_smoke_count` as a named field (≥63/162 skip records in 202608, the dominant stem — larger than receipt+baseline+gotcha combined). Updated re-derivation cost list item #12 + U9 row + `op:state` spec.
  2. **U14 added** — design↔testing schema consistency (`4.design/features` × `6.testing/features` dir diff; 5 known closure gaps). Filed as Phase-B `op:audit` candidate; out-of-scope for Phase-A locked-surface.
  3. **U15 added** — opencode-capability surface (`.agents/agents/` empty, `.agents/skills/` 1 local, MCP langchain-only, 0 slash commands). Filed as Phase-C `op:state` candidate; **inverts the layer's direction to proactive** (capability → ask). First forward-looking use case in the U-set.
  4. **Phase-A build sequence bootstrapped** — added a first-step task that `omt_q{op:plan, path:"gate_driver.ts"}` predicts `g.think` *before* the refactor edit. Converts edge case #2 from risk narrative to concrete build order; sharpens Risk #4 framing from "could feel paradoxical" to "is the build order".
  5. **Phase-A call telemetry criterion + U9 golden added** — `kind:"q"` ledger record per `omt_q` call is the gated-on-usage Phase-B evidence. U9 golden asserts `live_smoke_count` is surfaced as a named field, not just a generic top-3 stem.
  6. **Split-option ambiguity resolved** in Tasks → Immediate — ship all 7 Phase-A folds (evidence: U10+U13 sub-trivial, U7 needs one FP guard, splitting saves no risk and loses the closed U-set story). Demoted the split option to a single inline "RESOLVED" note.
- **Header / Summary / Decisions / Iteration log + References** all updated to v1.3 with verifiable evidence commands (`rg`/`comm`/`ls` one-liners reproduce every new finding).
- **Three TA: thoughts added** to PROJECT.md for future-session consult (live-smoke stem, design↔testing gap, opencode-capability surface); think-gate consult recorded before edits.

### Locked decisions (do not re-litigate without new evidence)

- **Phase-A surface UNCHANGED:** 3 ops (`state`/`plan`/`drift`) + 7 folds (U6/U7/U8/U10/U13 + U9 with `live_smoke_count` field), zero new build artifacts, single mechanical touch = `gate_driver.runBeforeGates` synthetic-ctx/dryRun refactor. The v1 lock holds — U14 + U15 are Phase-B/C candidates, not Phase-A scope.
- **Build sequence is the thesis' demonstration** — `op:plan` predicting its own `g.think` trigger on `gate_driver.ts` is the first Phase-A build step, not a paradox to mitigate.
- **Phase-B evidence gate is now measurable** — `kind:"q"` ledger records (zero today) → non-zero across k sessions = green-light for U4/U12/U14 audit ops. Without telemetry the gate was a vibe check; now it's a count.
- **Single-developer realism** — U14 widens substrate (filesystem dir pairs, not just ledger rows) but stays read-only + no gate added; U15 reads opencode config + skills dirs, also read-only. Neither breaks the "above-mechanics, not into them" principle.

### In progress

- _(nothing — v1.3 doc round complete)_

### Blocked

- _(nothing)_

### Next (when user decides to build Phase-A)

- Decide: open `feature_026.omt_q_interrogative_first_ops` under `4.design/features/` (phase-gated, activates TDD + AGENTS.md process surface) OR design in `.projects/meta/meta_harness_2/` only (non-gated, iterative). Same as v1.2 — no new evidence changes this question yet.
- Refactor `gate_driver.runBeforeGates` — synthetic `GateCtx` + `dryRun` return-decisions mode (behavior-preserving for real `tool.execute.before`); pinned by `test_omt_enforcer_guard_source_pins.py` + F14 real-binary tests.
- **FIRST STEP per Tasks → Phase-A build:** `omt_q{op:plan, path:".opencode/lib/enforcer/gate_driver.ts"}` must predict `g.think` BEFORE the refactor edit. Then `omt_think{op:list, path:".opencode/lib/enforcer/gate_driver.ts"}` consult. Then edit. (This step lands once `omt_q` itself is implemented — chicken-and-egg resolved by writing the plugin first, the plan-prediction as the first `omt_q` call against the freshly-implemented tool.)
- Implement `.opencode/plugins/omt_q.ts` — three ops + U9 `live_smoke_count` field + `kind:"q"` call telemetry.
- Write golden-query scenarios for U1, U2, U3, U6–U11, U13 (incl. U9 `live_smoke_count` assertion); the U2 golden asserts `op:plan` predicted chain == real `tool.execute.before` run on the same path/session.
- Full regression: 1196 baseline must stay green (3 known react_screen failures + KNOWN_SUITE_FAILURES allowlist unchanged).

### Notes / context

- v1.3 verification commands reproduce every new finding: `rg -o '"reason":"live smoke' .meta/.omt/ledger-202608.jsonl | wc -l` = 63; `comm -23 <(ls .meta/software_development_process/4.design/features/ | sort) <(ls .meta/software_development_process/6.testing/features/ | sort)` = 5 slugs; `ls .agents/agents/` empty; `head -30 opencode.jsonc` = 2 agents.
- The three TA: thoughts on PROJECT.md are the v1.3 evidence anchors — future-session resume should `omt_think{op:list, path:".projects/meta/meta_harness_2/PROJECT.md"}` to see them before any edits (think-gate will fire on this file from now on).

---

## 2026-08-09 (iter 1-6 — scope lock round)

### Done

- Created project directory `.projects/meta/meta_harness_2/`.
- **6 iteration rounds with user** — explored & locked v2 scope:
  1. Stub → "next-gen v2 harness redesign" (too broad — implied v1 rewrite).
  2. → "intelligent harness" with query language above mechanics (HQL idea).
  3. → HQL drafted; axes maxed (structured+raw+regex content, persisted+session+transcript state, workspace+git+no-external); commit-anchoring R1/R2/R3 phased.
  4. → Read WORK.md + WORK_ARCHIVE.md + ledger + 16 GOTCHA_* to ground use cases in real agent pain (not theoretical queries).
  5. → Critical re-examination: 4 of 5 canonical use cases (U1/U2/U3/U4) are **fixed-shape** parameterized by slug/path/session — they don't need a grammar. Only U5 (graph traversal with depth) has combinatorial structure that justifies HQL. → Grammar deferred.
  6. → Locked: **Phase-A ships `omt_q` with three ops (state/plan/drift); grammar & U4/U5 deferred to Phase-B/C gated on Phase-A usage evidence.**
- Wrote `PROJECT.md` v1 (locked scope): Summary / Vision + standing principle ("above the mechanics, not into them") / Purpose with U1–U5 canonical table / Scope (Phase-A in/out + deferred phases) / Success criteria (golden queries U1–U3 + U2 pre-flight=true-real assertion) / Architecture (TS plugin + synthetic GateCtx refactor) / Risks / Tasks / Decisions log (6 entries) / Iteration log / References.
- This `CURRENT_STATE.md` updated.

### Locked decisions (do not re-litigate without new evidence)

- **Above-mechanics principle** — v1's 9 gates + enforcer + TDD engine + IR compiler stay unchanged; single mechanical touch is `gate_driver.runBeforeGates` synthetic-ctx refactor (behavior-preserving).
- **Phase-A = three ops on `omt_q`:** `op:state` (U1 resume) / `op:plan` (U2 pre-flight, the thesis payoff) / `op:drift` (U3 AKB/source drift, reads kb.ir.json skeleton — zero new extractor).
- **U1–U5 canonical use case set** — Phase-A covers U1/U2/U3; U4 (audit) → Phase-B candidate; U5 (transitive risk / graph traversal) → Phase-C candidate + HQL gate.
- **Axes collapsed for Phase-A** (relaxed from earlier "maxed" state): structured-only (no raw-file-regex), persisted + session-state only (no transcript), workspace only (no AS OF git-tracked). Transcript/AS OF/raw-files/graph traversal ALL deferred to Phase-B/C.
- **src table = `kb.ir.json` skeleton** (zero new extractor).
- **Test bar = golden queries U1–U5** (Phase-A suite covers U1/U2/U3; U4/U5 golden reserved for later).
- **HQL grammar is a Phase-C bet**, gated on Phase-A+B ops gathering evidence the agent asks novel questions. Realistic failure mode: language never ships, 3–4 ops suffice. This is a feature of the plan.

### In progress

- _(nothing — scope lock complete)_

### Blocked

- _(nothing)_

### Next (when user decides to build Phase-A)

- Decide: open `feature_026.omt_q_interrogative_first_ops` under `4.design/features/` (phase-gated, activates TDD + AGENTS.md process surface) OR design in `.projects/meta/meta_harness_2/` only (non-gated, iterative).
- Refactor `gate_driver.runBeforeGates` — synthetic `GateCtx` + `dryRun` return-decisions mode (behavior-preserving for real `tool.execute.before`); pinned by test_omt_enforcer_guard_source_pins.py + F14 real-binary tests.
- Implement `.opencode/plugins/omt_q.ts` — three ops.
- Write golden-query scenarios for U1, U2, U3; the U2 golden asserts `op:plan` predicted chain == real `tool.execute.before` run on the same path/session.
- Full regression: 1196 baseline must stay green (3 known react_screen failures + KNOWN_SUITE_FAILURES allowlist unchanged).

### Notes / context

- Project slug: **`meta_harness_2`** (matches `.projects/meta/feature_kb_akb` + `.projects/meta/workflows` underscore convention, not `meta_harness_2.0`).
- Non-gated project: `.projects/` not in `harness_paths` — no `omt_phase` for the PROJECT.md edits in this session (per `.meta/META_HARNESS.omt:184`).
- Evidence base for U-set (start here when re-validating): `WORK.md` last 5 done + scratchpad gotcha top-3, `WORK_ARCHIVE.md` 50+ rotated completions, `.meta/.omt/ledger.jsonl` recent window fingerprint (54 phase / 48 skip / 42 think_consult / 21 complete).
- The "intelligent harness" vision is **fully delivered by `op:plan` alone** — the agent asks "if I edit this file, what fires?" and the harness answers with the gate chain evaluated against live state, before the block. Grammar is a 2nd-order value, not the thesis.
- Costliest gotchas the project targets: `GOTCHA_THINK_GATED` (op:plan pre-flight) / `GOTCHA_RECEIPT_ROUND_ROBIN` (op:plan says whether 2nd-edit is receipt-clean) / `GOTCHA_TESTLIST_JSON` (op:plan surfaces tdd-hat requirements). The 16 nav-indexed gotchas exist because they re-tripped enough to burn budget every session — op:plan converts them from post-block discovery to pre-flight intelligence.
