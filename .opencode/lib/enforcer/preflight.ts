// OMT++ gate preflight projection — the shared A4 core (feature_055).
//
// feature_062 P0-1 (meta_harness_7): this module is the SINGLE home of the
// preflight projection machinery, consumed by BOTH omt_status{op:"preflight"}
// (opt-in, unchanged) and the omt_phase declare-embed (new). The before-chain
// verdicts reuse the SAME dry-run sibling omt_q{op:plan} predicts with
// (runBeforeGatesDry on a synthetic GateCtx) — no second gate-evaluation
// engine to drift.
//
// Guardrails (feature_055 posture, inherited): READ-ONLY (no ledger writes)
// and no self think-gate literal — the preflight surface stays exempt from
// the thought gate on itself.
//
// Module-cycle note (feature_062): phase_gate imports this module, this
// module imports gate_driver, gate_driver imports phase_gate — a function-
// level-only cycle (every cross-reference is a hoisted function declaration
// resolved at call time, never at module-eval time). ESM live bindings make
// this safe; do NOT add module-level cross-references here.

import { relOf, loadIr, repoRoot, globToRegex } from "../omt_shared"
import { createSessionState, hasNavUnlock, type EnforcerEnv } from "./session_state"
import { type GateCtx, runBeforeGatesDry } from "./gate_driver"

// Distilled per-gate "what unblocks this". The .omt @msg records embed the
// same escapes as prose (meta_harness_5 #9) — this map is the concise
// actionable form, consistency-pinned by the feature tests. Deliberately NOT
// a new @gate clear= attribute: nav_index headroom is ~281B (Wave 3/B1).
const CLEARING_ACTIONS: Record<string, string> = {
  "g.nav": 'omt_nav{op:"nav"|"list_sections"|"quick_ref"} first (read + src/non-doc exempt); override omt_skip{scope:"nav"}; bug_fix/test phase auto-satisfies (C2)',
  "g.protect": '.env* is NEVER editable; README/uv.lock/LICENSE → ask the user, then omt_skip{scope:"all"}',
  "g.receipt": 'refresh the e2e receipt: uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q (one edit per harness file per round)',
  "g.tests": 'omt_skip{reason:"approved canary test", scope:"tests"}; own feature test dir auto-approved in RED (C2)',
  "g.net": 'omt_net{op:"fire", transition:"work_start"} (solo sessions auto-skip per C1); break-glass omt_skip{scope:"all"} — expiring, audited',
  "g.phase": 'omt_phase{task_type, scope} (bug_fix is enough for trivial fixes; major_feature/new_screen also need a design artifact); override omt_skip{reason:"..."}',
  "g.think": 'omt_think{op:"list", path:"<file>"} — NOT skip-bypassable',
  "g.kb": 'omt_kb_nav{op:"nav", query} (CLASS_/CONTRACT_/DEP_/LAYER_ or symbol id); bug_fix/test phase auto-satisfies (C2)',
  "g.mvc": 'after-edit: fix NEWLY introduced hard MVC++ violations forward (delta vs pre-edit snapshot)',
  "g.tdd_after": 'after-edit: REFACTOR auto-reverts breaking edits — keep the tests green',
}

// Gates whose dry-run verdict can diverge from the live enforcer path.
const DRY_CAVEATS: Record<string, string> = {
  "g.net": "dry-run cannot verify the live net verdict — under concurrency fire(work_start) first; solo auto-skips (C1)",
}

export const PREFLIGHT_DEFAULT_TOOL = "edit"

// feature_062 P0-1: the declare-embed passes the LIVE session state so the
// projection is honest about consults already paid (g.kb, nav); $ stays inert
// so the dry-run never shells out (g.net keeps its dry caveat).
export type PreflightEnvOverride = {
  state?: EnforcerEnv["state"]
  directory?: string
}

// Synthetic GateCtx mirroring the SDK before-hook shape (the omt_q plan
// idiom): input={tool}, output={args:{filePath}} — the BUG-A pin literal.
// env.$ stays a non-function so shell-out impls take their dry path.
function buildPreflightCtx(
  path: string, toolName: string, session?: string, envOverride?: PreflightEnvOverride,
): GateCtx {
  const { abs, rel } = relOf(path)
  const env: EnforcerEnv = {
    state: envOverride?.state ?? createSessionState(),
    directory: envOverride?.directory ?? repoRoot(),
    safeLog: () => {},
    notify: async () => {},
    client: {},
    $: {},
  }
  // Pre-seed nav from the ledger only for a FRESH state — an overridden live
  // state already knows what this session used (and must not be mutated).
  if (session && !envOverride?.state) {
    env.state.nav.set(session, { usedNav: !!hasNavUnlock(session) })
  }
  return {
    env,
    session,
    tool: toolName,
    input: { tool: toolName },
    output: { args: { filePath: path } },
    rel,
    abs,
    memo: new Map(),
  }
}

// After-gate when= projection: path_in(...) forms only (both live after-gates
// are path_in); anything else fires conservatively — a false "will fire"
// costs a hint, a miss would cost a surprise.
function whenPathMatches(when: string, rel: string | null, ir: any): boolean {
  const spec = String(when || "").trim()
  const m = spec.match(/^(!?)\s*path_in\((.+)\)$/)
  if (!m) return true
  const varRef = m[2].trim().match(/^@var\.([a-z0-9_]+)$/)
  const raw = varRef ? String(ir?.vars?.[varRef[1]] ?? "") : m[2].trim()
  const hit = raw.split(",").map((e) => e.trim()).filter(Boolean).some((e) =>
    e.includes("*") ? globToRegex(e).test(rel || "")
      : e.endsWith("/") ? (rel || "").startsWith(e) : rel === e)
  return m[1] === "!" ? !hit : hit
}

export async function preflightProjection(
  path: string, toolName: string, session?: string, envOverride?: PreflightEnvOverride,
): Promise<Record<string, any>> {
  const ir = loadIr()
  const ctx = buildPreflightCtx(path, toolName, session, envOverride)
  const decisions = await runBeforeGatesDry(ctx)
  const irGates: any[] = Array.isArray(ir?.gates) ? ir.gates : []
  const orderOf = new Map<string, number>(
    irGates.map((g: any) => [String(g.id), Number(g.order ?? 0)]))
  const before = decisions.map((d) => ({
    gate_id: d.gate_id,
    order: orderOf.get(d.gate_id) ?? -1,
    fired: d.fired !== false,
    blocked: d.blocked,
    halts_chain: d.stop === true,
    skip_ok: d.skip_ok,
    clearing_action: CLEARING_ACTIONS[d.gate_id] ?? "",
  }))
  // After-gates are NOTES, not predictions: g.mvc/g.tdd_after verdicts depend
  // on the edit content that does not exist yet.
  const after = irGates
    .filter((g: any) => g.on === "after")
    .filter((g: any) => String(g.tools ?? "").split("|").filter(Boolean).includes(toolName))
    .filter((g: any) => whenPathMatches(String(g.when ?? ""), ctx.rel, ir))
    .sort((a: any, b: any) => a.order - b.order)
    .map((g: any) => ({
      gate_id: String(g.id),
      order: Number(g.order ?? 0),
      note: CLEARING_ACTIONS[String(g.id)] ?? "",
    }))
  const firedRows = before.filter((r) => r.fired)
  const blockers = firedRows.filter((r) => r.blocked)
  return {
    op: "preflight",
    path,
    tool: toolName,
    rel: ctx.rel,
    before,
    after,
    summary: {
      before_total: before.length,
      before_fired: firedRows.length,
      would_block: blockers.length,
      first_blocker: blockers[0]?.gate_id ?? null,
      not_applicable: before.length - firedRows.length,
    },
  }
}

export function preflightLines(p: Record<string, any>): string[] {
  const lines = [
    `🛫 OMT++ PREFLIGHT — ${p.tool} ${p.path}`,
    `   before-chain: ${p.summary.before_fired} of ${p.summary.before_total} fire` +
      `${p.summary.would_block ? ` · ${p.summary.would_block} WOULD BLOCK (first: ${p.summary.first_blocker})` : " · all clear"}` +
      `${p.summary.not_applicable ? ` · ${p.summary.not_applicable} n/a` : ""}`,
  ]
  let n = 0
  for (const row of p.before) {
    if (!row.fired) continue
    n += 1
    if (row.blocked) {
      lines.push(`   ${n}. [${row.order}] ${row.gate_id} — WOULD BLOCK`)
      lines.push(`      clear: ${row.clearing_action}`)
    } else if (row.halts_chain) {
      lines.push(`   ${n}. [${row.order}] ${row.gate_id} — fires, halts the chain here`)
      if (row.clearing_action) lines.push(`      (${row.clearing_action})`)
    } else {
      const caveat = DRY_CAVEATS[row.gate_id]
      lines.push(`   ${n}. [${row.order}] ${row.gate_id} — fires ✓${caveat ? ` (${caveat})` : ""}`)
    }
  }
  for (const row of p.after) {
    lines.push(`   after [${row.order}] ${row.gate_id} — ${row.note}`)
  }
  return lines
}
