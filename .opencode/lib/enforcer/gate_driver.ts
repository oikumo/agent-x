// OMT++ HDL-2 gate driver (improvement006/OPT-F).
//
// The before-hook gate chain is DATA-DRIVEN: .meta/META_HARNESS.omt @gate
// records (compiled into harness.ir.json gates[]) declare on/tools/when/
// requires/msg/hard/skip_ok/order per gate. This driver iterates the IR
// before-gates in ascending order=, matches tools=, evaluates when= through
// the closed @pred registry (HDL-1: data only; TS owns builtins), and delegates the gate-specific
// remainder the DSL does not yet express to the registered impl (IMPLS):
// design-artifact matrix, TDD-hat deferral, per-file consult, protected
// override, tests-stop.
//
// .omt-only operations (no TS edit, no receipt round-robin ×7):
//   • reorder gates (order=)      • retarget a gate's tool set (tools=)
//   • retarget when= path sets    • change ANY gate's block/warn text (@msg payload — R8/OPT-G)
//   • ADD a pred-composed before-gate (unregistered id → genericImpl)
// TS-required: new @pred builtins, new specialized impls (before IMPLS /
// after AFTER_IMPLS — improvement007 R7: after-gates are data-driven too).
//
// Fallback philosophy (isDocPath heritage): if the IR is missing/corrupt the
// chain must never die open — FALLBACK_GATES mirrors the .omt order/tools.

import { existsSync, readFileSync } from "node:fs"
import {
  loadIr, relOf, globToRegex, readLedger, readThoughtsIndex,
  omtHarnessE2eStatus, UNLOCK_WINDOW_MS, protectList, matchesProtect, gateMsg,
} from "../omt_shared"
import {
  OmtBlock, getActiveUnlock, hasNavUnlock, hasFastPathUnlock, type EnforcerEnv,
} from "./session_state"
import { getSearchPath, navGateDecision } from "./nav_gate"
import {
  guardProtectedPath, guardHarnessReceipt, guardTestsPath,
} from "./receipt_guard"
import { guardSrcPath } from "./phase_gate"
import { guardThoughts, fileThoughtsIn } from "./think_gate"
import { mvcAfterEdit } from "./mvc_after"
import { tddAfterEdit } from "./tdd_hats"

export interface GateCtx {
  env: EnforcerEnv
  session: string | undefined
  tool: string
  input: any
  output: any
  rel: string | null  // edit tools: target file; search tools: search scope
  abs: string | null
  memo: Map<string, boolean> // per-invocation pred cache (e.g. file_has greps)
}

// --- @pred builtins (HDL-1 closed vocabulary) --------------------------------

function pathEntries(spec: string, ir: any): string[] {
  const m = spec.match(/^@var\.([a-z0-9_]+)$/)
  const raw = m ? String(ir?.vars?.[m[1]] ?? "") : spec
  return raw.split(",").map((e) => e.trim()).filter(Boolean)
}

function pathIn(rel: string, spec: string, ir: any): boolean {
  if (spec === "@protect.*") {
    // improvement007 R6 (HDL-2 die-open fix): with the IR missing, ir?.protect
    // evaluates to [] and the when= pre-filter skipped g.protect entirely —
    // protected files were UNGUARDED on the fallback chain. Fall back to the
    // shared-lib accessor (FALLBACK_PROTECT literal) — never die open.
    const list = Array.isArray(ir?.protect) && ir.protect.length
      ? ir.protect : protectList()
    return list.some((p: any) => matchesProtect(rel, p))
  }
  return pathEntries(spec, ir).some((e) => {
    if (e.includes("*")) return globToRegex(e).test(rel)
    return e.endsWith("/") ? rel.startsWith(e) : rel === e
  })
}

// feature_054 C2: bug_fix/test phase record satisfies g.nav+g.kb in one
// write — session_state.hasFastPathUnlock is the single ledger-backed
// implementation (session-matched, window fallback; major/new_screen stay
// hard). The phase tool also flips the in-memory flags for immediacy.
const SESSION_FLAGS: Record<string, (ctx: GateCtx) => boolean> = {
  nav_used: (ctx) => {
    const s = ctx.session ? ctx.env.state.nav.get(ctx.session) : undefined
    return !!s?.usedNav || hasNavUnlock(ctx.session) || hasFastPathUnlock(ctx.session)
  },
  // feature_kb_akb: g.kb gate's `session_flag(kb_consulted)` predicate. Set by
  // kbTrack on any omt_kb_nav op call (nav_gate.ts); guards src/ edit-tools.
  kb_consulted: (ctx) => {
    const s = ctx.session ? ctx.env.state.kb.get(ctx.session) : undefined
    return !!s?.consulted || hasFastPathUnlock(ctx.session)
  },
}

function ledgerHas(ctx: GateCtx, arg: string, ir: any): boolean {
  // ledger_has(kind,k=v,window) — window may be a @var ref (numeric in IR vars)
  const [kind, kv, win] = arg.split(",").map((s) => s.trim())
  const winVar = (win || "").match(/^@var\.([a-z0-9_]+)$/)
  const windowMs = winVar ? Number(ir?.vars?.[winVar[1]]) : Number(win)
  const [k, v] = (kv || "").split("=").map((s) => s.trim())
  const now = Date.now()
  return readLedger().some((r) => {
    if (r.kind !== kind) return false
    if (k && String(r[k] ?? "") !== v) return false
    if (ctx.session && r.session === ctx.session) return true
    const t = Date.parse(r.ts || "")
    return !Number.isNaN(t) && now - t < (windowMs || UNLOCK_WINDOW_MS)
  })
}

function evalPred(call: string, ctx: GateCtx, ir: any): boolean {
  const m = call.match(/^(!?)\s*([a-z_][a-z0-9_]*)\s*\((.*)\)\s*$/)
  if (!m) return true // unevaluable → fail open (never brick a session)
  const [, neg, name, argStr] = m
  const arg = argStr.trim().replace(/^"(.*)"$/, "$1")
  let out: boolean
  switch (name) {
    case "path_in":
      out = ctx.rel !== null && pathIn(ctx.rel, argStr.trim(), ir)
      break
    case "file_has": {
      if (!ctx.abs || !existsSyncSafe(ctx.abs)) { out = false; break }
      out = arg === "TA:"
        ? memo(ctx, `file_has:TA:${ctx.abs}`, () => fileThoughtsIn(ctx.abs!).length > 0)
        : memo(ctx, `file_has:${arg}:${ctx.abs}`, () =>
            readFileSyncSafe(ctx.abs!).includes(arg))
      break
    }
    case "session_flag":
      out = SESSION_FLAGS[arg]?.(ctx) ?? false
      break
    case "ledger_has":
      out = ledgerHas(ctx, argStr, ir)
      break
    case "receipt_fresh":
      out = !!ctx.rel && !!ctx.abs && omtHarnessE2eStatus(ctx.rel, ctx.abs).ok
      break
    case "risk_high":
      out = !!ctx.rel && readThoughtsIndex().some((r) =>
        r.path === ctx.rel && r.category === "risk")
      break
    case "cmd_match": {
      const cmd = String(ctx.output?.args?.command ?? "")
      out = !!cmd && (ir?.deny ?? []).some((d: any) =>
        d.scope === "bash" && globToRegex(d.match).test(cmd))
      break
    }
    case "fsm_allows":
      // Generic-gate evaluation of the TDD hats is not supported — the
      // specialized impls (g.tests/g.phase) own TDD deferral. Fail open.
      ctx.env.safeLog("warn", `pred fsm_allows has no generic evaluator (gate ${call})`)
      out = true
      break
    default:
      ctx.env.safeLog("warn", `unknown @pred '${name}' — failing open`)
      out = true
  }
  return neg === "!" ? !out : out
}

function memo(ctx: GateCtx, key: string, fn: () => boolean): boolean {
  if (!ctx.memo.has(key)) ctx.memo.set(key, fn())
  return ctx.memo.get(key)!
}

function existsSyncSafe(p: string): boolean {
  try { return existsSync(p) } catch { return false }
}

function readFileSyncSafe(p: string): string {
  try { return readFileSync(p, "utf8") } catch { return "" }
}

function evalPredExpr(expr: string, ctx: GateCtx, ir: any): boolean {
  // when=/requires= are single pred calls in HDL-1 (optionally !-negated).
  return evalPred(expr, ctx, ir)
}

// --- specialized impls (the remainder the DSL does not express) --------------

type GateImpl = (gate: any, ctx: GateCtx) => Promise<void | "stop">

const IMPLS: Record<string, GateImpl> = {
// TA: risk: risk (feature_050 wrap-up @ .sandbox/pause_2026-09-05c.md): (1) g.net impl carries a // DEBUG block writing /tmp/gate_debug.log — remove with its require("node:fs"); (2) .omt @gate g.net skip_ok=true contradicts TS fallback skip_ok:false + design_001 — IR is the functional source so ANY session skip bypasses the net gate; fix .omt to skip_ok=false (break-glass scope=all only, net_enforced_harness D3) + harnessc rebuild
  // feature_020: block doc-scoped searches until a nav tool was used.
  "g.nav": async (_gate, ctx) => {
    if (!ctx.session) return
    const state = ctx.env.state.nav.get(ctx.session)
    const decision = navGateDecision({
      tool: ctx.tool,
      targetRel: ctx.rel,
      usedNav: state?.usedNav ?? false,
      // feature_054 C2: a bug_fix/test phase record satisfies the nav gate
      // too (impl-owned — this impl never evaluates requires=).
      navUnlock: hasNavUnlock(ctx.session) || hasFastPathUnlock(ctx.session),
    })
    if (decision === "block") {
      ctx.env.safeLog("warn", `Session ${ctx.session}: blocked ${ctx.tool} (doc search '${ctx.rel || "repo"}') without prior navigation`)
      throw new OmtBlock(`⛔ OMT++ gate: ${gateMsg("nav_required")}`)
    }
  },
  // AGENTS.md NEVER paths; .env* hard, README/uv.lock/LICENSE via scope=all.
  "g.protect": async (_gate, ctx) =>
    (await guardProtectedPath(ctx.env, ctx.session, ctx.rel!)) ? "stop" : undefined,
  // Harness-surface second-edit guard (per-file git-dirty + mtime vs receipt).
  "g.receipt": async (_gate, ctx) => { await guardHarnessReceipt(ctx.rel!, ctx.abs!) },
  // tests/ canary (TDD-hat deferral inside); tests/ edits stop the chain.
  "g.tests": async (_gate, ctx) => {
    await guardTestsPath(ctx.env, ctx.session, ctx.rel!)
    return "stop"
  },
  // src/ phase + §12 artifact gate (+ TDD two-hats + snapshots inside).
  "g.phase": async (_gate, ctx) => { await guardSrcPath(ctx.env, ctx.session, ctx.rel!, ctx.abs!) },
  // Thought-carrying files need a per-file omt_think{op:list} consult (not skip-able).
  "g.think": async (_gate, ctx) => { await guardThoughts(ctx.env, ctx.session, ctx.rel!, ctx.abs!) },
  // KB consult gate: src/ edits need prior omt_kb_nav consult (genericImpl handles requires=).
  "g.kb": undefined,
  // feature_050.net_as_gate: net permission-to-act gate (Alt A Net-as-Gate).
  // Runs after g.tests:30, before g.phase:40. Calls Python net.gate helper.
  // feature_053 C1 @pred net_marking(active>1): solo sessions skip the shell
  // entirely and revert to phase-gate only — the gate engages only under real
  // concurrency (2+ active works). Unreadable bundle → engage (fail-closed;
  // solo must be proven, never assumed). Python net/gate.is_concurrent is the
  // authority for the shell path; this fs-read mirrors it for the fast path.
  "g.net": async (_gate, ctx) => {
    const abs = ctx.abs || ""
    const rel = ctx.rel || ""
    if (!abs || !rel) return
    // Only gate src/, tests/, and harness-surface paths.
    const isSrc = rel.startsWith("src/")
    const isTests = rel.startsWith("tests/")
    const isHarness = rel.startsWith(".opencode/") || rel.startsWith("scripts/omt/")
    if (!isSrc && !isTests && !isHarness) return
    // C1 solo fast-path (net_marking mirror).
    const soloBypass = ((): boolean => {
      try {
        const dir = (typeof process !== "undefined" && (process as any)?.env?.OMT_NET_DIR)
          || `${ctx.env.directory}/.meta/.omt`
        const sidecar = JSON.parse(readFileSync(`${dir}/net_state.sidecar.json`, "utf8"))
        const live: unknown = (sidecar as any)?.live_marking
        if (!Array.isArray(live)) return false
        let order: string[] = []
        try {
          const netJson = JSON.parse(readFileSync(`${dir}/META_NET.petri.json`, "utf8"))
          order = Array.isArray((netJson as any)?.places)
            ? (netJson as any).places.map((p: any) => String(p?.name ?? ""))
            : []
        } catch { return false }
        const marking: Record<string, number> = {}
        order.forEach((name, i) => { marking[name] = Number((live as any[])[i] ?? 0) })
        if ((marking["work_active"] ?? 0) > 1) return false
        const holders = Object.keys(marking).filter((k) => /^f\d+_active$/.test(k) && (marking[k] ?? 0) > 0)
        return holders.length <= 1
      } catch { return false }
    })()
    if (soloBypass) return
    // Dry-run / synthetic ctx (omt_q op:plan): no SDK shell on env.$ — the
    // gate still fires in the predicted chain, but its verdict needs the
    // live enforcer path (skip the shell-out instead of crashing the fold).
    if (typeof ctx.env.$ !== "function") return
    // Call net.gate to check permission.
    const res = await ctx.env.$`uv run scripts/omt/net_check.py gate --path ${rel} --session ${ctx.session || ""}`.cwd(ctx.env.directory).quiet().nothrow()
    const data = JSON.parse(res.stdout.toString() || '{"allowed":false,"code":"ERR_NET_NOT_ENABLED"}')
    if (!data.allowed) throw new OmtBlock(`⛔ OMT++ gate (g.net): ${data.message || data.code}`)
  },
}

// Generic impl: a before-gate with NO registered impl is fully pred-composed —
// requires= fails → block (or warn) with the IR msg text. skip_ok honors a
// logged omt_skip (any scope) as the escape hatch.
async function genericImpl(gate: any, ctx: GateCtx): Promise<void> {
  const ir = loadIr()
  if (gate.requires && evalPredExpr(gate.requires, ctx, ir)) return
  if (gate.skip_ok && getActiveUnlock(ctx.session)?.type === "skip") return
  const text = gateMsg(String(gate.msg ?? gate.id), { rel: ctx.rel })
  if (!gate.hard) {
    await ctx.env.notify(`⚠️ OMT++ gate (${gate.id}): ${text}`)
    return
  }
  throw new OmtBlock(`⛔ OMT++ gate (${gate.id}): ${text}`)
}

// IR-missing fallback (never die open): mirrors .meta/META_HARNESS.omt @gate
// order/tools — keep in sync; verify-projections + the IR pins make drift a
// build error long before this path runs.
const FALLBACK_GATES = [
  { id: "g.nav", on: "before", tools: "grep|glob|rg|find", when: "path_in(@var.doc_paths)", requires: "", msg: "nav_required", hard: true, skip_ok: true, order: 0 },
  { id: "g.protect", on: "before", tools: "edit|write|patch|multiedit", when: "path_in(@protect.*)", requires: "", msg: "protect_file", hard: true, skip_ok: true, order: 10 },
  { id: "g.receipt", on: "before", tools: "edit|write|patch|multiedit", when: "path_in(@var.harness_paths)", requires: "receipt_fresh()", msg: "receipt_stale", hard: true, skip_ok: false, order: 20 },
  { id: "g.tests", on: "before", tools: "edit|write|patch|multiedit", when: "path_in(tests/)", requires: "", msg: "tests_canary", hard: true, skip_ok: true, order: 30 },
  { id: "g.net", on: "before", tools: "edit|write|patch|multiedit", when: "path_in(@var.net_paths)", requires: "", msg: "net_required", hard: true, skip_ok: false, order: 35 },
  { id: "g.phase", on: "before", tools: "edit|write|patch|multiedit", when: "path_in(src/)", requires: "", msg: "no_phase", hard: true, skip_ok: true, order: 40 },
  { id: "g.think", on: "before", tools: "edit|write|patch|multiedit", when: 'file_has("TA:")', requires: "", msg: "think_gate", hard: true, skip_ok: false, order: 50 },
  { id: "g.kb", on: "before", tools: "edit|write|patch|multiedit", when: "path_in(src/)", requires: "session_flag(kb_consulted)", msg: "kb_required", hard: true, skip_ok: false, order: 55 },
]

// Composition-root entry point (HDL-2): run every IR before-gate in order=.
// rawEditPath: the before-hook filePath (output.args per the SDK contract —
// the caller keeps the BUG-A pin literal); search tools get their scope from
// getSearchPath instead.
export async function runBeforeGates(
  env: EnforcerEnv,
  session: string | undefined,
  input: any,
  output: any,
  rawEditPath: string | null,
): Promise<void> {
  const ir = loadIr()
  const gates = (Array.isArray(ir?.gates) && ir.gates.length ? ir.gates : FALLBACK_GATES)
    .filter((g: any) => g.on === "before")
    .sort((a: any, b: any) => a.order - b.order)
  const tool = input?.tool ?? ""
  let rel: string | null = null
  let abs: string | null = null
  if (rawEditPath) {
    ({ abs, rel } = relOf(rawEditPath))
  } else {
    rel = getSearchPath(output)
  }
  const ctx: GateCtx = { env, session, tool, input, output, rel, abs, memo: new Map() }
  for (const gate of gates) {
    const tools = String(gate.tools ?? "").split("|").filter(Boolean)
    if (tools.length && !tools.includes(tool)) continue
    // when= pre-filter: decisive only for a known non-null target (a null/whole-
    // repo target stays with the impl, matching the pre-HDL-2 semantics).
    if (rel !== null && gate.when && !evalPredExpr(gate.when, ctx, ir)) continue
    const impl = IMPLS[gate.id] ?? genericImpl
    if ((await impl(gate, ctx)) === "stop") return
  }
}

// Phase-A interrogative layer (feature_026.omt_q_interrogative_first_ops):
// a dryRun variant of the before-chain that captures OmtBlock per-gate and
// returns decision rows instead of throwing. The existing runBeforeGates is
// byte-identical — real edits still throw OmtBlock as today; this sibling is
// omt_q{op:plan}'s "predict what would block" path. NEVER used by the real
// composition root (runBeforeGates remains the throw path).
export type GateDecision = {
  gate_id: string
  blocked: boolean
  msg: string
  skip_ok: boolean
}

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
      throw e // non-OmtBlock errors are real failures — propagate
    }
  }
  return decisions
}

// --- after-gates (improvement007 R7 / OPT-F): data-driven like the before-chain
//
// The root's after-hook keeps composition-only concerns (session bootstrap,
// read-time thought injection, the raw/null path guard); the edit-tools and
// src/**.py filters that used to live there are exactly the gates' tools=/
// when= attrs. g.mvc's "lint failed ⇒ skip the TDD after-edit" sequencing
// falls out of order= 60<70 plus the before-chain's "stop" adapter contract.
// OmtBlock (mvc hard violation, tdd revert) propagates to the root un-caught
// — the pre-R7 root's posture.

type AfterImpl = (gate: any, ctx: GateCtx) => Promise<void | "stop">

const AFTER_IMPLS: Record<string, AfterImpl> = {
  // MVC++ delta gate: throws on NEW hard violations; false ⇒ the lint itself
  // failed → stop the chain (skip g.tdd_after), the monolith's early return.
  "g.mvc": async (_gate, ctx) =>
    (await mvcAfterEdit(ctx.env, ctx.abs!, ctx.rel!)) === false ? "stop" : undefined,
  // TDD after-edit: advisory + REFACTOR revert check (ir.hats via R5).
  "g.tdd_after": async (_gate, ctx) => {
    await tddAfterEdit(ctx.env, ctx.input, ctx.abs!, ctx.rel!)
  },
}

// IR-missing fallback (never die open): mirrors the .omt after-gates on the
// FIELDS the driver consumes; requires=/run= stay impl-owned (excluded).
const FALLBACK_AFTER_GATES = [
  { id: "g.mvc", on: "after", tools: "edit|write|patch|multiedit", when: "path_in(src/**/*.py)", msg: "mvc_new_hard", hard: true, skip_ok: false, order: 60 },
  { id: "g.tdd_after", on: "after", tools: "edit|write|patch|multiedit", when: "path_in(src/)", msg: "tdd_revert", hard: false, skip_ok: false, order: 70 },
]

// Composition-root entry point: run every IR after-gate in order=. Every
// after-gate is edit-targeted — a null rawEditPath means nothing to do (the
// root keeps the raw/null guard; this is belt-and-braces for direct calls).
export async function runAfterGates(
  env: EnforcerEnv,
  session: string | undefined,
  input: any,
  output: any,
  rawEditPath: string | null,
): Promise<void> {
  if (!rawEditPath) return
  const ir = loadIr()
  const gates = (Array.isArray(ir?.gates) && ir.gates.length ? ir.gates : FALLBACK_AFTER_GATES)
    .filter((g: any) => g.on === "after")
    .sort((a: any, b: any) => a.order - b.order)
  const tool = input?.tool ?? ""
  const { abs, rel } = relOf(rawEditPath)
  const ctx: GateCtx = { env, session, tool, input, output, rel, abs, memo: new Map() }
  for (const gate of gates) {
    const tools = String(gate.tools ?? "").split("|").filter(Boolean)
    if (tools.length && !tools.includes(tool)) continue
    // when= pre-filter: same semantics as the before-chain (always decisive
    // here — rel is non-null past the rawEditPath guard above).
    if (gate.when && !evalPredExpr(gate.when, ctx, ir)) continue
    const impl = AFTER_IMPLS[gate.id]
    if (!impl) {
      // No generic after-impl: after semantics (run= deltas, fsm reverts) are
      // impl-owned by definition — fail open, never brick the after-hook.
      env.safeLog("warn", `after-gate ${gate.id} has no registered impl — skipped (fail open)`)
      continue
    }
    if ((await impl(gate, ctx)) === "stop") return
  }
}
