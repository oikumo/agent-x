# Design 001: omt_q interrogative first ops (op:state, op:plan, op:drift)

> **Phase:** Design — `omt_agent_guide.md §2`, §5–§10
> **Feature:** feature_026.omt_q_interrogative_first_ops
> **Parent design source-of-truth:** `.projects/meta/meta_harness_2/PROJECT.md` (v1.5, 513 lines)
> **Analysis doc:** `3.analysis/features/feature_026.omt_q_interrogative_first_ops/analysis_001_substrate_rederivation_costs.md`

## Summary

Ship a new read-only `omt_q` TypeScript plugin at `.opencode/plugins/omt_q.ts` exposing **three fixed-shape ops** — `op:state{feature?, session?, as_of?}`, `op:plan{path, tool?, session?, as_of?}`, `op:drift{as_of?}` — on top of the existing v1 substrates (gate IR + rotated ledger + thoughts index + KB IR + e2e receipt status + `KNOWN_SUITE_FAILURES` literal). Every response envelope carries `as_of_commit:"<HEAD-sha>"` (Phase-A stub: always `HEAD`, parsed live via `git rev-parse HEAD`). Seven fold projections (U6/U7/U8/U9+`live_smoke_count`/U10/U13 on `op:state`, U11 on `op:plan`) collapse ~10 per-session re-derivation rituals into one deterministic read per question.

The single *mechanical* touch is a behaviour-preserving refactor of `gate_driver.runBeforeGates` that adds an orthogonal `dryRun:true` path: a synthetic `GateCtx` is built from `{path, tool, session}` inputs + live `env.state`, each before-gate's `impl` is wrapped in `try { await impl } catch (e) { if (e instanceof OmtBlock) capture }`, and the captured decisions `[{gate_id, blocked, msg, skip_ok}...]` are returned instead of `void`. **Real edits still throw `OmtBlock`** on the existing `await impl(gate, ctx)` path.

No new gates, no ledger semantics change, no enforcer relocate, no TDD engine rewrite — the v1 lock is preserved. The plugin mirrors `omt_nav.ts`'s factory structure exactly. Each call appends a `kind:"q"` ledger record (v1.3 schema + v1.4 `op_set`/`fold_used`/`latency_ms` + v1.5 `as_of:"HEAD"`).

## Problem Analysis

### Current behavior

The 8 existing `omt_*` tools are all *writes* or *single-substrate reads*. None cross-cuts substrates to answer resume questions:

- "What is the state of feature_X?" → today a fresh session runs ~5 reads (`WORK.md` + scratchpad + `.projects/<feat>/CURRENT_STATE.md` + ledger tail-grep + thoughts + fsm), then re-reasons over them (= ~2.0–3.5 KB tokens / 5 reasoning turns).
- "Will this edit hit a gate I don't know about?" → discovered by *being blocked* (`OmtBlock` propagates from the matched gate's impl through `runBeforeGates` to the before-hook); the agent then recovers one gate per cycle (= ~1.2 KB per block→recover cycle, ~7 before-gates potentially).
- "Which AKB records have drifted?" → no surface today (silent drift is a known state).

### Substrate inventory (verified live 2026-08-09)

All atoms `omt_q` consumes already exist in v1; this feature is a pure composition layer:

| Substrate | Path | Existing helpers |
|-----------|------|------------------|
| gate IR (7 before-gates, 2 after-gates) | `.meta/.omt/harness.ir.json` | `loadIr()` — `gate_driver.ts` iterates `gates[]` |
| ledger (phase, skip, think_consult, tdd, tdd_testlist, complete) | `.meta/.omt/ledger{,-YYYYMM}.jsonl` | `readLedger()` — rotation-aware (latest archive + hot) |
| thoughts index | `.meta/.omt/thoughts.jsonl` | `readThoughtsIndex()` — already consumed by `risk_high` pred |
| KB skeleton | `.meta/.omt/kb.ir.json` | `loadKbIr()` — built by `kb_ast_extract.py` |
| receipt status | `.meta/.omt/omt_harness_e2e_last_run.json` | `omtHarnessE2eStatus(rel, abs)` |
| `KNOWN_SUITE_FAILURES` literal | `scripts/omt/tdd/state.py:132` | **none** — the single NEW read this feature adds (regex extract, parse-not-import) |
| active feature phase | derived in `session_state.ts` | `getActiveFeaturePhase(feature, session)` + `getActiveUnlock(session)` + `hasNavUnlock(session)` |

### Live IR fingerprint correction (carried from Analysis doc)

The parent `PROJECT.md` repeatedly says "9 before-gates"; live `harness.ir.json` has **7 before-gates** + 2 after-gates today. The count comes from the IR (not a hardcoded literal) — `op:plan` filters `gates.filter(on==="before")` dynamically, so this is a doc-count correction only. The 7 before-gates in order: `g.nav(0)`, `g.protect(10)`, `g.receipt(20)`, `g.tests(30)`, `g.phase(40)`, `g.think(50)`, `g.kb(55)`.

## Components / Files Affected

| File | Layer | Change |
|------|-------|--------|
| `.opencode/plugins/omt_q.ts` (new) | Plugin | The 3-op read-only interrogative plugin. Mirrors `omt_nav.ts` factory: `import { initOmtShared, repoRoot, ... } from "../lib/omt_shared"`; `export default async ({directory, worktree}) => { initOmtShared(worktree ?? directory); const {omt_q} = createQTools(); return {tool:{omt_q}} }`. |
| `.opencode/lib/enforcer/gate_driver.ts` | Enforcer | **Single mechanical touch.** Add `runBeforeGates(..., dryRun?: true)` overload (or sibling `runBeforeGatesDry(ctx)`). When `dryRun===true`, the existing loop wraps `await impl(gate, ctx)` in `try { await impl } catch (e) { if (e instanceof OmtBlock) capture }` and returns `[{gate_id, blocked, msg, skip_ok}...]` instead of `void`. The existing throw-path is unchanged (real edits still throw — pinned by `test_omt_enforcer_guard_source_pins.py` + `test_omt_harness_e2e.py`). |
| `tests/scripts/omt/test_omt_q.py` (new) | Tests | Golden queries for U1/U2/U3 + U6–U11 + U13 (+ U9 `live_smoke_count` named field + U7 cross-feature FP guard + U8 near-collision slugs + U2 predict==real chain on `gate_driver.ts` self-trigger + U3 count-drift direction-b only + v1.5 `as_of_commit` envelope assertion on every golden). Lives alongside `test_omt_enforcer_guard_source_pins.py` (harness-level pin-test convention). |
| `tests/features/feature_026.omt_q_interrogative_first_ops/test_omt_q_golden_smoke.py` (new, sentinel) | Tests | Sentinel re-export of the harness-level golden suite, to satisfy `omt_complete{Programming→Testing}` pattern matcher `tests/features/<feature>/test_*.py`. Thin wrapper (imports + re-runs `test_omt_q.py` cases) — NOT the canonical test location. |

**No changes to:** `.opencode/lib/omt_shared.ts` (substate helpers already sufficient — omt_q composes them), `omt_enforcer.ts` (composition root delegates to `runBeforeGates` as today), `.meta/META_HARNESS.omt` (no new gates/vars), `pyproject.toml` (TS-only feature — no Python deps), any src/agentx/ code.

## Static Structure

### `omt_q.ts` plugin (after)

```typescript
// .opencode/plugins/omt_q.ts  (after)
import { tool } from "@opencode-ai/plugin"
import { execFileSync } from "node:child_process"
import { existsSync, readFileSync, statSync } from "node:fs"
import { join, isAbsolute } from "node:path"
import {
  initOmtShared, repoRoot, loadIr, readLedger, appendLedger,
  readThoughtsIndex, loadKbIr, omtHarnessE2eStatus, gateMsg,
  THOUGHT_PATTERN, UNLOCK_WINDOW_MS,
} from "../lib/omt_shared"
import {
  getActiveFeaturePhase, getActiveUnlock, hasNavUnlock,
  type EnforcerEnv,
} from "../lib/enforcer/session_state"
import {
  OmtBlock, runBeforeGates, type GateCtx,
} from "../lib/enforcer/gate_driver"
import { createSessionState } from "../lib/enforcer/session_state"
import { relOf, toAbs } from "../lib/omt_shared"

// KNOWN_SUITE_FAILURES regex extractor (the single new read).
function parseKnownSuiteFailures(root: string): {
  nodeIds: string[];
  parse_failed: boolean;
} {
  try {
    const p = join(root, "scripts", "omt", "tdd", "state.py")
    if (!existsSync(p)) return { nodeIds: [], parse_failed: true }
    const src = readFileSync(p, "utf8")
    const m = src.match(/KNOWN_SUITE_FAILURES\s*=\s*frozenset\(\{([^}]+)\}\)/)
    if (!m) return { nodeIds: [], parse_failed: true }
    const ids = (m[1].match(/'([^']+)'/g) || [])
      .map(s => s.slice(1, -1))
    return { nodeIds: ids, parse_failed: false }
  } catch {
    return { nodeIds: [], parse_failed: true }
  }
}

function headSha(): string {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: repoRoot(), encoding: "utf8", stdio: ["ignore", "pipe", "ignore"],
    }).trim()
  } catch { return "HEAD" }
}

// --- createQTools: built post-init (mirrors omt_nav's createNavTools) --------
function createQTools() {
  const omt_state = tool({ /* … */ async execute(args, ctx) { … } })
  const omt_plan  = tool({ /* … */ async execute(args, ctx) { … } })
  const omt_drift = tool({ /* … */ async execute(args, ctx) { … } })

  const omt_q = tool({
    description: irToolDescription("omt_q", "…"),
    args: {
      op: tool.schema.string().describe("state|plan|drift"),
      feature: tool.schema.string().optional(),
      session: tool.schema.string().optional(),
      path: tool.schema.string().optional(),
      tool: tool.schema.string().optional(),
      as_of: tool.schema.string().optional(),
    },
    async execute(args, context) {
      const start = Date.now()
      const t0 = context?.sessionID
      switch (args?.op ?? "") {
        case "state": { const r = await omt_state.execute(args, context); /* envelope+ledger */ return r }
        case "plan":  { const r = await omt_plan.execute(args, context);  return r }
        case "drift": { const r = await omt_drift.execute(args, context); return r }
        default: return "⛔ omt_q: unknown op — want state|plan|drift"
      }
    },
  })
  return { omt_q }
}

export default async ({ directory, worktree }) => {
  initOmtShared(worktree ?? directory)
  const { omt_q } = createQTools()
  return { tool: { omt_q } }
}
```

### `gate_driver.runBeforeGates` refactor (after)

```typescript
// .opencode/lib/enforcer/gate_driver.ts  (additive — existing path unchanged)

export type GateDecision = { gate_id: string; blocked: boolean; msg: string; skip_ok: boolean }

// Existing export kept byte-identical (real edit path throws OmtBlock).
export async function runBeforeGates(
  env, session, input, output, rawEditPath,
): Promise<void> { /* … existing L241-270 unchanged … */ }

// NEW: dryRun variant for omt_q{op:plan}. Takes a PRE-BUILT GateCtx (omt_q
// builds it from {path, tool, session} + a synthetic env whose state mirrors
// ctx.session). Catches OmtBlock per-gate and returns decision rows; never
// throws — real edits still go through runBeforeGates (the throw path).
export async function runBeforeGatesDry(ctx: GateCtx): Promise<GateDecision[]> {
  const ir = loadIr()
  const gates = (Array.isArray(ir?.gates) && ir.gates.length ? ir.gates : FALLBACK_GATES)
    .filter((g: any) => g.on === "before")
    .sort((a: any, b: any) => a.order - b.order)
  const decisions: GateDecision[] = []
  const tool = ctx.tool
  for (const gate of gates) {
    const tools = String(gate.tools ?? "").split("|").filter(Boolean)
    if (tools.length && !tools.includes(tool)) continue
    if (ctx.rel !== null && gate.when && !evalPredExpr(gate.when, ctx, ir)) {
      decisions.push({ gate_id: gate.id, blocked: false, msg: "", skip_ok: !!gate.skip_ok })
      continue
    }
    const impl = IMPLS[gate.id] ?? genericImpl
    try {
      const r = await impl(gate, ctx)
      decisions.push({ gate_id: gate.id, blocked: false, msg: "", skip_ok: !!gate.skip_ok })
      if (r === "stop") break
    } catch (e) {
      if (e instanceof OmtBlock) {
        decisions.push({
          gate_id: gate.id,
          blocked: true,
          msg: e.message,
          skip_ok: !!gate.skip_ok,
        })
        // dryRun never propagates — capture and continue (so the agent sees
        // ALL before-gates that would fire, not just the first blocker).
        continue
      }
      throw e   // non-OmtBlock errors are real failures — propagate
    }
  }
  return decisions
}
```

###Behaviour-preservation invariants (the refactor doesn't break):

- The existing `runBeforeGates(env, session, input, output, rawEditPath)` has the SAME byte body — real edits go through it and throw `OmtBlock` as today (the first blocking gate wins, `"stop"` aborts the chain).
- `runBeforeGatesDry(ctx)` is a sibling function that catches `OmtBlock` per-gate. The impls themselves are NOT modified — `OmtBlock` propagation behavior inside each impl is identical whether the caller is `runBeforeGates` or `runBeforeGatesDry`.
- `test_omt_enforcer_guard_source_pins.py::TestGateDriverIrPin::test_impls_cover_exactly_the_ir_before_gates` — the `IMPLS` registry is NOT touched (the dryRun path reads the same registry), so the covers-exactly pin stays green.
- The `g.think` self-trigger: `gate_driver.ts` still contains the literal `"TA:"` and the impls still call `guardThoughts` that fires `file_has("TA:")` — so the same file still trips `g.think` whether via real `runBeforeGates` or `runBeforeGatesDry`.

## Functional Flow

### `op:state{feature?, session?, as_of?}`

```
omt_q{op:"state", feature:"feature_026…", session:"abc"}
  → headSha() → envelope.as_of_commit = "<sha>"
  → loadIr() → fsm.phase.states  // ["Analysis","Design","Programming","Testing","Done"]
  → readLedger()                  // rotation-aware
  → getActiveFeaturePhase(feature, session)       // U1 pipe-through
  → fold U6 stranded_reds         // per-test_node latest-state=="red" with NO later green at SAME test_node
  → fold U7 closed_via_skip       // latest done with any checklist.{suite_passes,refactor_recorded,naming_ok}==false
  │                               //   + later skip within same feature + 1h window, reason ⊇
  │                               //   {"Override permits"|"pre-existing baseline"}
  │                               //   CROSS-FEATURE FP GUARD: skip must be scoped to SAME feature within the 1h window
  → fold U8 decree_health         // slug_variants[], empty_slug_records[], invalid_phase_records[], phase_cycle_count
  │                               //   NEAR-COLLISION GUARD: feature_004 ≠ feature_04 (exact-prefix match only)
  → fold U9 skip_reason_tally     // top-3 stems + counts; SEPARATE named field `live_smoke_count`
  → fold U10 known_suite_failures // parse state.py:132 frozenset → 6 node IDs; fail-open `KNOWN_SUITE_FAILURES_parse_failed`
  → fold U13 think_consults       // recent_consults[{files[], ts, session}] within UNLOCK_WINDOW_MS (8h)
  │                               //   + consult_needed[] = files referenced-by-active-feature-but-NOT-recent-consult
  → last_activity_ts              // max ts across ledger records scoped to feature (or hot max if no feature)
  → risky_thoughts                // thoughts on files touched under this feature with line_drift flag (re-scan source)
  → appendLedger({kind:"q", op:"state", feature, session, ts,
                   op_set:[…folds used…], fold_used:"U1,U6,U7,…", latency_ms, as_of:"HEAD"})
  → return JSON-string envelope
```

### `op:plan{path, tool?, session?, as_of?}`

```
omt_q{op:"plan", path:".opencode/lib/enforcer/gate_driver.ts", tool:"edit", session:"abc"}
  → headSha() → envelope.as_of_commit
  → relOf(path) → {abs, rel}
  → tool = args.tool ?? "edit"
  → synthetic env (createSessionState(); mirror ctx.session into env.state.nav/kb maps if session given)
  → GateCtx = {env, session, tool, input:{tool}, output:{args:{filePath:path}}, rel, abs, memo:new Map()}
  → runBeforeGatesDry(ctx) → GateDecision[]   // the 7 before-gates, order-sorted
  → for each decision: project {gate_id, blocked, msg, skip_ok, when_eval, requires_eval}
  → fold U11 receipt_detail         // if rel ∈ @var.harness_paths (g.receipt would fire):
  │                                 //   {receipt_required:true,
  │                                 //    file_mtime: <statSync>,
  │                                 //    receipt_passed_at: <omt_harness_e2e_last_run.json passed_at>,
  │                                 //    stale: targetMtime > lastPassed,
  │                                 //    refresh_tests:["tests/scripts/omt/test_omt_harness_e2e.py"],
  │                                 //    refresh_cmd:"uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q"}
  → appendLedger({kind:"q", op:"plan", path, tool, session, ts,
                   op_set:["U2","U11"], fold_used:"U2,U11", latency_ms, as_of:"HEAD"})
  → return JSON-string envelope
```

### `op:drift{as_of?}`

```
omt_q{op:"drift"}
  → headSha() → envelope.as_of_commit
  → loadKbIr() → records[]: {id, kind, src, line, refs, tags, text, tier}
  → for each record:
  │     - source_scan: readFileSync(record.src, "utf8").split("\n")[record.line-1]
  │     - line_still_thought_line: does line match THOUGHT_PATTERN-based skeleton marker? (or symbol idToPoint match)
  │     - GONE: !existsSync(src)
  │     - MOVED: the skeleton marker at record.line no longer matches (line drifted up/down)
  │     - UNTRACKED: src exists + line points to a non-TA: line that no longer matches the KB record
  → count_drift direction-b: len(kb.ir records) vs len(source skeleton count) — ONLY KB>skeleton IS drift
  │                      (KB<skeleton is just "not-yet-curated" — not drift per edge case #5)
  → appendLedger({kind:"q", op:"drift", ts,
                   op_set:["U3"], fold_used:"U3", latency_ms, as_of:"HEAD"})
  → return JSON-string envelope {as_of_commit, op:"drift", drift_records[], count_drift:{kb, skeleton, direction_b_only}}
```

## Operation Specifications

See `operation_spec_001_omt_q_ops.md` (sibling file) for the per-op Pre/Post/Exc contracts on `omt_state`, `omt_plan`, `omt_drift`, the synthetic-env builder, and the `runBeforeGatesDry` invariant.

## Breaking-change risk

- **MVC pin** — none. The TS plugin layer doesn't touch any `src/agentx/*.py`; `test_coding_mvc.py` etc. are entirely outside the blast radius.
- **`runBeforeGates` behavior pin** — `test_omt_enforcer_guard_source_pins.py::TestGateDriverIrPin` asserts `IMPLS` covers exactly IR before-gates and that the composition root delegates. The refactor ADDS `runBeforeGatesDry` WITHOUT touching `IMPLS` or `runBeforeGates` body → all those pins stay green as-is.
- **`FALLBACK_GATES` pin** — `TestFallbackGatesIrSyncPin` asserts the literal mirrors IR before-gates. The refactor doesn't touch `FALLBACK_GATES` (the dryRun path uses the same `(ir?.gates.length ? ir.gates : FALLBACK_GATES).filter(on==="before").sort(order)` source as `runBeforeGates`) → green.
- **e2e (`test_omt_harness_e2e.py`) behaves** — since `runBeforeGates` is byte-identical, real-binary edit scenarios throw-on-block exactly as before.
- **`omt_q.ts` is itself in `@var.harness_paths`** → editing `omt_q.ts` triggers `g.receipt` (the second-edit guard). Each multi-edit round on the plugin needs one fresh `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` run BEFORE the second edit (GOTCHA_RECEIPT_ROUND_ROBIN). The build-sequence bootstrap step `omt_q{op:plan, path:".opencode/lib/enforcer/gate_driver.ts"}` *predicts* `g.think` and *is itself predicting the very receipt gate* — the v1.3 thesis demonstration.

## Backwards compatibility

- **No public API removal.** The new `omt_q` plugin is additive — registered alongside the 8 existing `omt_*` tools (now 9).
- **`runBeforeGates` contract preserved.** Same `(env, session, input, output, rawEditPath)` signature, same `Promise<void>` return, same throw-on-block semantics. The dryRun variant is an ADDITIONAL export (`runBeforeGatesDry(ctx): Promise<GateDecision[]>`); no caller is forced to migrate.
- **`kind:"q"` ledger records** are a pure addition to the ledger schema (new `kind` value) — existing readers filter by `kind` and never see q records; `test_ledger_*` pins don't cross-contaminate.
- **`KNOWN_SUITE_FAILURES` parsing** reads `scripts/omt/tdd/state.py` and regex-extracts; if the literal moves/renames, the parser fails open with `KNOWN_SUITE_FAILURES_parse_failed:true` (and the constant move surfaces immediately to the agent at the next `op:state` call — exactly the interrogative contract).

## Testing strategy (TDD — major_feature)

RED tests land under `tests/scripts/omt/test_omt_q.py` (harness-level pin-test convention, alongside `test_omt_enforcer_guard_source_pins.py` + `test_omt_harness_e2e.py`). A sentinel re-export at `tests/features/feature_026.omt_q_interrogative_first_ops/test_omt_q_golden_smoke.py` satisfies the `omt_complete{Programming→Testing}` pattern matcher `tests/features/<feature>/test_*.py`.

1. **U1** `test_op_state_resume_returns_5_read_snapshot` — hand-craft a feature with phase + tdd + skip + think_consult + thoughts + fsm state; assert snapshot matches the documented expected answer.
2. **U2** `test_op_plan_predicts_real_before_chain_on_gate_driver` — **THE HIGHEST-RISK CANARY** — assert `omt_q{op:plan, path:".opencode/lib/enforcer/gate_driver.ts"}` predicted chain == real `tool.execute.before` chain on the same path/session/tool (or a unit-level probe that mirrors the F14 bun-probe pattern). Includes the `gate_driver.ts` self-trigger scenario (predicts `g.think`).
3. **U3** `test_op_drift_reports_count_drift_direction_b_only` — assert `count_drift > 0` (direction-b); the known `feature_kb` count drift pre-existing failure must surface. Assert `direction_b_only: true` (KB > skeleton is drift; KB < skeleton is un-curated, NOT drift).
4. **U6** `test_op_state_reports_stranded_red` — hand-craft a stranded red (`state:"red"` at `test_node=A` with no later green at `test_node=A`) → assert `op:state` returns `stranded_red:["A"]`.
5. **U7** `test_op_state_reports_closed_via_skip` + `test_op_state_cross_feature_fp_guard` — hand-craft `done{checklist.suite_passes:false}` + later `skip{reason:"Override permits..."}` scoped to feature_X → assert `op:state{feature:X}` returns `closed_via_skip:true`; THEN hand-craft a same-window `skip` for feature_Y → assert `op:state{feature:X}` does NOT mark X as closed_via_skip.
6. **U8** `test_op_state_reports_decree_health_with_near_collision_guard` — hand-craft (i) `phase` record with `feature:""` whose `scope` text contains "feature_024", (ii) `phase:""` literal record, (iii) 3 `phase` records under 3 distinct slug variants of feature_024 → assert `slug_variants:[…]` length ≥ 3, `empty_slug_records` length 1, `invalid_phase_records` length 1. NEAR-COLLISION GUARD: hand-craft `feature_004` vs `feature_04` (bare) → assert they do NOT match.
7. **U9** `test_op_state_skip_reason_tally_with_live_smoke_named_field` — hand-craft 4 skips with reason stems `live smoke`×2, `TDD bootstrap`×1, `Override permits pre-existing baseline`×1 → assert `op:state` returns `live_smoke_count:2` (named) PLUS the generic top-3 stem tally (`live smoke:2`, `TDD bootstrap:1`, `Override permits…:1`).
8. **U10** `test_op_state_known_suite_failures_from_state_py` — assert `op:state` returns EXACTLY the 6 node IDs in `state.py:132` `KNOWN_SUITE_FAILURES` (parsed from the constant via regex, NOT hardcoded in the test).
9. **U11** `test_op_plan_receipt_detail_stale_path` — hand-craft a path in `@var.harness_paths` whose mtime > `omt_harness_e2e_last_run.json`'s `passed_at` → assert `op:plan.receipt_detail.stale === true` + `refresh_tests === ["tests/scripts/omt/test_omt_harness_e2e.py"]` + `refresh_cmd === "uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q"`.
10. **U13** `test_op_state_consult_dedup` — hand-craft a `think_consult` within the 8h window for file X → assert X ∈ `recent_consults` and X ∉ `consult_needed`.
11. **v1.5 envelope** `test_envelope_as_of_commit_in_every_golden` — every golden asserts `as_of_commit === <HEAD-sha>` (parsed live via `git rev-parse HEAD` at call time); two consecutive calls against an unchanged commit return byte-identical `as_of_commit` values.
12. **behaviour-preservation** `test_run_before_gates_dry_does_not_break_real_path` — assert that after the refactor, the existing `runBeforeGates` still throws `OmtBlock` on a protect-path (the bun-probe pattern, hermetic tmp root). Repeat the existing `TestGateDriverProtectIrMissing` test plus a new assertion: `runBeforeGatesDry` on the same path returns a non-empty `decisions[]` with `blocked:true` (no throw).

GREEN: implement the wiring per the static structure above.

REFACTOR: extract the synthetic-env builder (`buildCtxFromInputs(path, tool, session)`) + the ledger folding primitives (`foldStrandedReds`, `foldClosedViaSkip`, `foldDecreeHealth`, …) into local helpers; ensure `omt_q.ts` stays < 600 lines.

## Open questions / risks

- **`runBeforeGatesDry` evaluation of `impl`-side effects** — some impls (`guardThoughts`, `guardSrcPath`) call `env.notify` to warn (not throw) on non-hard gates. The dryRun path must distinguish blocked (caught `OmtBlock`) from advisory (returned `undefined`, gate was `!hard`). Decision: `blocked:false` if the impl returned normally; `blocked:true` only if `OmtBlock` was thrown. Advisory warnings drop out of the dryRun result (they're not blockers — `op:plan` only reports what would actually block).
- **`op:drift` line-still-matches heuristic** — the KB record's `line` is fragile (source code shifts). The fold should re-scan the source file's `record.line` and check it still matches the recorded thought/marker; a drift δ is reported but the record is NOT auto-migrated (KB migration is the v1 AKS process, out of scope).
- **`tdd_testlist` session-bleed** — the most recent `tdd_testlist` record (feature_025, 2026-08-09T00:46:55) has `session:""`. `op:state`'s TDD-position derivation joins `tdd_testlist` to `tdd` records by `feature` (NOT session) so an empty session string still works.
- **`omt_q` -> `omt_q` recursion** — `op:plan{path:".opencode/plugins/omt_q.ts"}` would predict `g.think` (the file contains `"TA:"` in the думка pattern string at the top, plus `g.receipt` on second edit). This is the build-order's own self-demonstration (analysis doc edge case #2). No recursion risk: `op:plan` doesn't call `omt_q`; it calls `runBeforeGatesDry` once.
- **Bun runtime dependency in tests** — the U2 golden uses the bun-probe pattern from `TestGateDriverProtectIrMissing`. `bun` is already a test-time dependency of `test_omt_enforcer_guard_source_pins.py` (skipif if missing). Keep the same skipif on the U2 golden.

## Links

- Parent design source-of-truth: `.projects/meta/meta_harness_2/PROJECT.md` (v1.5, 513 lines)
- Analysis doc: `3.analysis/features/feature_026.omt_q_interrogative_first_ops/analysis_001_substrate_rederivation_costs.md`
- Operation spec: `4.design/features/feature_026.omt_q_interrogative_first_ops/operation_spec_001_omt_q_ops.md`
- Mirror plugin: `.opencode/plugins/omt_nav.ts`
- Refactor target: `.opencode/lib/enforcer/gate_driver.ts` (L241-270 `runBeforeGates`, L175-207 `IMPLS`, L39-48 `GateCtx`)
- Behaviour-preservation pins: `tests/scripts/omt/test_omt_enforcer_guard_source_pins.py` (BUG-A before-hook + IR-sync pins stay green through the dryRun refactor)
- Existing major-feature templates: `feature_025.coding_context_window_optimization/design_001_deepagent_context_optimization.md` + `operation_spec_001_deepagent_service_methods.md`
