# Operation Spec 001: omt_q ops (state, plan, drift)

> **Phase:** Design — `omt_agent_guide.md §10`
> **Feature:** feature_026.omt_q_interrogative_first_ops
> **Design doc:** `design_001_omt_q_first_ops.md`

---

## `omt_q` (registered single-tool dispatch)

```typescript
const omt_q = tool({
  description: irToolDescription("omt_q", "Interrogative layer — read-only."),
  args: {
    op: tool.schema.string().describe("state|plan|drift"),
    feature: tool.schema.string().optional(),
    session: tool.schema.string().optional(),
    path: tool.schema.string().optional(),
    tool: tool.schema.string().optional(),
    as_of: tool.schema.string().optional(),
  },
  async execute(args, context): Promise<string> { … },
})
```

**Pre:** none (plugin factory already called `initOmtShared(worktree ?? directory)`).
**Post:**
- Dispatches by `op` to one of `omt_state` / `omt_plan` / `omt_drift` (unregistered impl tools, built inside `createQTools`).
- Each op wraps its return in `envelope: {as_of_commit:"<HEAD-sha>", op, ...}` and appends a `kind:"q"` ledger record.
- Unknown `op` → returns `"⛔ omt_q: unknown op — want state|plan|drift"` (no ledger append).
**Exc:** none — all op impls swallow internal errors and return a fail-open envelope (so a malformed state file never blocks a session resume).

---

## `omt_state` (op=state impl)

```typescript
const omt_state = tool({
  args: { feature: tool.schema.string().optional(),
          session: tool.schema.string().optional(),
          as_of:  tool.schema.string().optional() },
  async execute(args, context): Promise<string>
})
```

**Pre:** `initOmtShared` already called (factory); `repoRoot()` resolves to the real root.
**Post:** returns a JSON-string envelope `{as_of_commit, op:"state", feature?, session?, ...}` containing the fold projections:

| field | source | fold |
|-------|--------|------|
| `phase` | `getActiveFeaturePhase(feature, session)` (pipe-through; "Unknown" if feature absent) | U1 |
| `tdd_position` | latest `kind:"tdd"` record for `feature` (joined to `tdd_testlist` by feature, not session) — `{state, test_node, target_src[], verified, exit_code}` | U1 |
| `stranded_red` | per `test_node`, latest `state:"red"` with no later `green` at the SAME `test_node` | U6 |
| `closed_via_skip` | latest `done` with any false in `checklist.{suite_passes, refactor_recorded, naming_ok}` + later `skip` scoped to the SAME feature within 1h window whose `reason` contains "Override permits" OR "pre-existing baseline" | U7 |
| `decree_health` | `{slug_variants[], empty_slug_records[{ts,scope}], invalid_phase_records[{ts,phase}], phase_cycle_count}` validated against `fsm.phase.states = "Analysis,Design,Programming,Testing,Done"` | U8 |
| `skip_reason_tally` | top-3 reason stems + counts; CROSS-FEATURE FP guard ensures skips scoped to a DIFFERENT feature within the 1h window do NOT count toward this feature's `closed_via_skip` | U7 |
| `live_smoke_count` | named SEPARATE field (count of `skip` records whose reason stem is `live smoke`, scoped to `nav`); NOT part of the generic top-3 tally | U9 |
| `known_suite_failures` | 6 node IDs parsed from `scripts/omt/tdd/state.py:132` `frozenset({...})` via `KNOWN_SUITE_FAILURES\s*=\s*frozenset\(\{([^}]+)\}\)` regex then split on quotes | U10 |
| `known_suite_failures_parse_failed` | boolean flag set true if the regex misses or the file is unreadable | U10 |
| `recent_consults` | `think_consult` records within `UNLOCK_WINDOW_MS` (8h) — `[{files[], ts, session}]` | U13 |
| `consult_needed[]` | files referenced by active feature (e.g. listed in feature's THINK-consult gate evidence or `feature`-scoped activity) NOT present in `recent_consults` within the 8h window | U13 |
| `last_activity_ts` | max `ts` across the ledger records scoped to `feature` (or hot max if `feature` absent) | — |
| `risky_thoughts[]` | thoughts on files touched under `feature` — re-scan source for `TA:` marker via `thoughtPattern()`; each carries `line_drift:bool` (true if the source line no longer starts with a thought marker at the recorded `line`) | edge case #3 |

**Exc:** none — all folds are fail-open (missing ledger rec / missing IR / missing thoughts index → empty array / `phase:"Unknown"` / `[]`).

**NEAR-COLLISION GUARD (U8):** `feature_004` and `feature_04` (bare) must NOT match. Implementation: prefix-match on `feature_NNN.` (with the dot) or `feature_NNN_` (with the underscore) only — bare `feature_NNN` is an exact-match case.

**CROSS-FEATURE FP GUARD (U7):** a `skip` for feature_Y within 1h of feature_X's not-done should NOT flip feature_X's `closed_via_skip:true`. The skip's `scope` text or feature-field must explicitly mention feature_X (per existing `omt_skip.feature` semantics).

---

## `omt_plan` (op=plan impl)

```typescript
const omt_plan = tool({
  args: { path:      tool.schema.string().describe("repo-relative or absolute target path"),
          tool:      tool.schema.string().optional().describe("edit|write|patch|multiedit|grep|glob|rg|find (default edit)"),
          session:   tool.schema.string().optional(),
          as_of:     tool.schema.string().optional() },
  async execute(args, context): Promise<string>
})
```

**Pre:** `initOmtShared` already called; `path` is a non-empty string.
**Post:** returns a JSON-string envelope `{as_of_commit, op:"plan", path, tool, ...}` containing:

| field | source | fold |
|-------|--------|------|
| `predicted_chain` | ordered (by IR `order=`) before-gate decisions `[{gate_id, blocked, msg, skip_ok, when_eval, requires_eval}]` produced by `runBeforeGatesDry(ctx)` (the new sibling of `runBeforeGates`) | U2 |
| `receipt_detail` | populated only when `path ∈ @var.harness_paths` — `{receipt_required:true, file_mtime:<ms>, receipt_passed_at:<ms>, stale:bool, refresh_tests:["tests/scripts/omt/test_omt_harness_e2e.py"], refresh_cmd:"uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q"}` | U11 |
| `first_blocker` | the FIRST decision in `predicted_chain` whose `blocked:true` (or null) — convenience field | U2 |

**Synthetic GateCtx construction (in `omt_plan` impl body):**

```typescript
const { abs, rel } = relOf(args.path)
const toolName = args.tool ?? "edit"
const session = args.session
const env: EnforcerEnv = {
  ...createSessionState(),          // fresh state maps (nav, kb, unlocked)
  directory: repoRoot(),
  safeLog: () => {},
  notify: async () => {},           // advisory warns drop out (dryRun captures only hard blocks)
  client: {}, $: {},
}
if (session) {
  // mirror session flags from the latest live env by replaying recent ledger
  if (hasNavUnlock(session))        env.state.nav.set(session, { usedNav: true })
  // (...) kb_consulted mirrored from recent think_consult records if needed
}
const ctx: GateCtx = {
  env, session, tool: toolName,
  input:   { tool: toolName },
  output:  { args: { filePath: args.path } },   // hack: SDK shape — see BUG-A pin
  rel, abs,
  memo: new Map(),
}
const decisions = await runBeforeGatesDry(ctx)
```

**IMPORTANT:** the `output.args.filePath` literal MUST stay (BUG-A pin). SDK contract: before-hook `output` carries `args`; the dryRun `GateCtx` mirrors the exact same shape so the impls see no difference.

**Exc:** none — `runBeforeGatesDry` catches `OmtBlock` per-gate; non-`OmtBlock` errors are propagated (still rare — only on a corrupt env).

---

## `omt_drift` (op=drift impl)

```typescript
const omt_drift = tool({
  args: { as_of: tool.schema.string().optional() },
  async execute(args, context): Promise<string>
})
```

**Pre:** `initOmtShared` already called.
**Post:** returns a JSON-string envelope `{as_of_commit, op:"drift", ...}` containing:

| field | source | fold |
|-------|--------|------|
| `drift_records[]` | for each KB record: re-scan `records[].src` file at `records[].line`; classify GONE (`!existsSync(src)`), MOVED (line no longer a thought marker — `line_drift`), UNTRACKED (src line ≠ KB record's thought-text) | U3 |
| `count_drift` | `{kb: <int len(kb.records)>, skeleton: <int len(source skeleton markers)>, direction_b_only: true}` | U3 |
| `direction_b_only` | **always `true`** — KB > skeleton IS drift; KB < skeleton is "not-yet-tracked" (NOT drift per edge case #5 + the v1 "new = not-yet-tracked is NOT drift" rule) | U3 |

**Exc:** none — missing KB IR → empty `drift_records[]`, `count_drift.kb = 0`.

---

## Synthetic-env builder (shared by `omt_plan`)

```typescript
function buildCtxFromInputs(args: {path, tool?, session?}): GateCtx
```

**Pre:** `initOmtShared` already called; `args.path` non-empty.
**Post:** returns a `GateCtx` with:
- `env`: a fresh `createSessionState()` + repoRoot + no-op `safeLog` / `notify` (advisory warns drop out; dryRun captures only `OmtBlock`-thrown hard blocks).
- `session`: the caller's `args.session` (or undefined).
- `tool`: `args.tool ?? "edit"`.
- `input`: `{tool: <toolName>}` (mirrors SDK before-hook shape).
- `output`: `{args:{filePath: args.path}}` (BUG-A pin literal — before-hook args live on `output`, not `input`).
- `rel`, `abs`: from `relOf(args.path)`.
- `memo`: fresh `new Map()`.

**Exc:** none.

---

## `runBeforeGatesDry(ctx: GateCtx): Promise<GateDecision[]>`

```typescript
export type GateDecision = { gate_id: string; blocked: boolean; msg: string; skip_ok: boolean }

export async function runBeforeGatesDry(ctx: GateCtx): Promise<GateDecision[]>
```

**Pre:** `ctx` is a fully-populated `GateCtx` (the caller built it via `buildCtxFromInputs`).
**Post:**
- Iterates the SAME before-gates as `runBeforeGates` (the `(ir?.gates.length ? ir.gates : FALLBACK_GATES).filter(on==="before").sort(order)` source), in ascending `order=`.
- For each gate whose `tools=` excludes `ctx.tool`, the gate is skipped (decision recorded with `blocked:false`, blank `msg`).
- For each gate whose `when=` pre-filter fails (gate doesn't apply to `ctx.rel`), `blocked:false` is recorded (matches `runBeforeGates`'s skip path).
- For each gate whose `when=` passes (or whose `ctx.rel === null`): call `impl = IMPLS[gate.id] ?? genericImpl`, wrap in:

  ```typescript
  try {
    const r = await impl(gate, ctx)
    decisions.push({gate_id: gate.id, blocked: false, msg: "", skip_ok: !!gate.skip_ok})
    if (r === "stop") break
  } catch (e) {
    if (e instanceof OmtBlock) {
      decisions.push({gate_id: gate.id, blocked: true, msg: e.message, skip_ok: !!gate.skip_ok})
      continue            // dryRun NEVER propagates — capture and continue
    }
    throw e                // non-OmtBlock errors are real failures — propagate
  }
  ```

- Returns the captured `decisions[]`. NEVER throws on an `OmtBlock`.

**Exc:** non-`OmtBlock` errors from `impl` propagate (e.g. if `loadIr()` itself raises an unhandled exception — currently impossible, `loadIr` is fail-open).

---

## Behaviour-preservation matrix

| Existing public API / pin | Behavior change | Risk |
|---------------------------|-----------------|------|
| `runBeforeGates(env, session, input, output, rawEditPath): Promise<void>` | NONE — body byte-identical | none |
| `IMPLS` registry coverage (`TestGateDriverIrPin::test_impls_cover_exactly_the_ir_before_gates`) | NONE — dryRun reads the same registry | none |
| `FALLBACK_GATES` IR sync (`TestFallbackGatesIrSyncPin::test_fallback_gates_mirror_ir_before_gates`) | NONE — `FALLBACK_GATES` literal untouched | none |
| `g.think` self-trigger on `gate_driver.ts` (`test_no_false_f14_comment_in_before_hook`, behaviour probe) | NONE — `g.think` impl body unchanged; `runBeforeGatesDry` on `gate_driver.ts` will still detect the `"TA:"` literal | none |
| `test_omt_harness_e2e.py` real-binary probe | UNCHANGED — `runBeforeGates` throw-on-block preserved | none |
| 8 existing `omt_*` plugin tools | NONE — additive new `omt_q` registration doesn't touch them | none |
| ledger API (`appendLedger`, `readLedger`) | NONE — new `kind:"q"` records use the same append API; no new read path | none |
| `KNOWN_SUITE_FAILURES` literal in `state.py` | NONE — read-only regex parse; **fail-open** if regex misses | none — the parse-failed flag surfaces the change |

## MVC pin test impact

No MVC pin is touched (this is a TS-only feature touching `.opencode/` + harness tests). The `src/agentx/` MVC pins (`test_coding_mvc.py`, `test_fast_agent_mvc.py`, etc.) are entirely outside the blast radius.
