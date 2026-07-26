// OMT++ think-gate (feature_021) + read-time thought injection (feature_022
// D1) — meta_harness_dsl R2 module.
//
//   • guardThoughts       — before-hook: block edits to thought-carrying files
//                           until the session has consulted (omt_think_list).
//                           NOT bypassable by omt_skip — thoughts are
//                           safety-relevant.
//   • injectThoughtsOnRead — after-hook: on the FIRST read of a
//                           thought-carrying file per session, append the
//                           file's thought-tags to the read result
//                           (point-of-use awareness, strictly earlier than the
//                           edit-time block). Awareness ≠ consult: NO
//                           think_consult record is written.

import { existsSync } from "node:fs"
import { execFileSync } from "node:child_process"
import {
  ledgerPath, thoughtsIndexPath, readJsonl, relOf,
  UNLOCK_WINDOW_MS, THOUGHT_PATTERN,
} from "../omt_shared"
import { OmtBlock, type EnforcerEnv } from "./session_state"

// Pure decision: may the agent edit a file that carries TA: thoughts?
//   hasThoughts=false → allow (nothing to review).
//   hasThoughts=true && consulted → allow.
//   hasThoughts=true && !consulted → block.
export function thinkGateDecision(opts: {
  hasThoughts: boolean
  consulted: boolean
}): "allow" | "block" {
  // Load-safety heritage (feature_023 Tier 3, pre-R2 monolith): an undefined
  // arg must fail open to "allow" (no thoughts to review) instead of crashing
  // on `.hasThoughts` destructure.
  if (!opts?.hasThoughts) return "allow"
  return opts.consulted ? "allow" : "block"
}

// Has the session consulted thoughts FOR rel? (feature_022 C2: per-file
// granularity.) Reads the shared ledger for `think_consult` records (written
// by omt_think_list). rel omitted → whole-consult semantics identical to v1
// (back-compat). covered(r): rel omitted → true; record without `files`
// (legacy, pre-C2) → true (grandfathered — ages out with the window); else
// r.files includes rel. Exact-session covering consult → true; else a
// cross-session consult within UNLOCK_WINDOW_MS covering rel → true ONLY IF
// NOT opts.risk (the window is dropped for risk:-carrying files — a risk
// thought demands THIS session looked). opts.root: ledger root (default: the
// shared lib's repo root — the production call site passes the plugin ctx
// root explicitly; root injection enables hermetic tests).
export function hasConsultedThoughts(
  session: string | undefined,
  rel?: string,
  opts?: { risk?: boolean; root?: string },
): boolean {
  const recs = readJsonl(ledgerPath(opts?.root))
  const consults = recs.filter((r) => r && r.kind === "think_consult")
  if (!consults.length) return false
  const covered = (r: any): boolean => {
    if (rel === undefined) return true
    if (!Array.isArray(r.files)) return true // legacy record — grandfathered
    return r.files.includes(rel)
  }
  if (session && consults.some((r) => r.session === session && covered(r))) return true
  if (opts?.risk) return false // window dropped for risk:-carrying files
  const now = Date.now()
  return consults.some((r) => {
    if (!covered(r)) return false
    const t = Date.parse(r.ts || "")
    return !Number.isNaN(t) && now - t < UNLOCK_WINDOW_MS
  })
}

// Grep TA: in a single file (cheap; used by the think-gate before-hook and the
// D1 read-time injection). Takes an absolute path.
export function fileThoughtsIn(absFile: string): { line: number; content: string }[] {
  if (!absFile || !existsSync(absFile)) return []
  try {
    const out = execFileSync("grep", ["-nHE", "--", THOUGHT_PATTERN, absFile], {
      encoding: "utf8", stdio: ["pipe", "pipe", "ignore"],
    })
    const res: { line: number; content: string }[] = []
    for (const line of out.trim().split("\n")) {
      if (!line) continue
      const m = line.match(/^(?:.+?):(\d+):(.*)$/)
      if (m) res.push({ line: parseInt(m[1], 10), content: m[2].trim() })
    }
    return res
  } catch { return [] }
}

// feature_022 C1: latest verify records for path === rel whose status is
// "stale" → their line numbers. Reads thoughts.jsonl via the shared lib
// (root = plugin ctx root at the call site; injected in tests). Fail-open:
// missing/corrupt index → empty set (no markers, never blocks the message).
function staleLinesFor(root: string, rel: string): Set<number> {
  const out = new Set<number>()
  try {
    const latest = new Map<number, string>()
    for (const r of readJsonl(thoughtsIndexPath(root))) {
      if (r && r.kind === "verify" && r.path === rel && typeof r.line === "number") {
        latest.set(r.line, r.status)
      }
    }
    for (const [line, status] of latest) {
      if (status === "stale") out.add(line)
    }
  } catch { /* fail-open */ }
  return out
}

// Block message for the think-gate: surfaces the file's own TA: thoughts so the
// agent has read them; the expected next action is omt_think_list{path} (clears).
// feature_022 C1 weighting: risk:-category thoughts render first (stable sort;
// category read from content at category position only, /TA:\s*([a-z0-9_-]+):/i
// — a gotcha: thought mentioning "risk:" in its text does not match); a thought
// line gains a "  ⚠️ STALE" suffix when opts.staleLines contains its line
// (latest verify record stale). 10-line cap + "+M more" pointer unchanged.
function thinkGateMsg(
  rel: string,
  thoughts: { line: number; content: string }[],
  opts?: { staleLines?: Set<number> },
): string {
  const isRisk = (t: { content: string }) => /TA:\s*risk:/i.test(t.content)
  const weighted = [...thoughts].sort((a, b) => Number(isRisk(b)) - Number(isRisk(a)))
  const shown = weighted.slice(0, 10).map((t) =>
    `  ${rel}:${t.line}: ${t.content}${opts?.staleLines?.has(t.line) ? "  ⚠️ STALE" : ""}`,
  ).join("\n")
  return `⛔ OMT++ think-gate (feature_021): '${rel}' carries TA: thoughts. Review them ` +
    `before editing, then clear the gate with omt_think_list{path:"${rel}"}:\n${shown}` +
    (thoughts.length > 10 ? `\n  … (+${thoughts.length - 10} more)` : "") +
    `\n(The block already shows these thoughts; call omt_think_list to record the consult.)`
}

// Before-hook think-gate (feature_021): block edits to thought-carrying files
// until the session has consulted thoughts (omt_think_list). NOT bypassable by
// omt_skip — thoughts are safety-relevant warnings. Runs only for edits
// already permitted by the protected/e2e/tests/src checks (composition-root
// ordering). feature_022 C2: consult is checked per-file (rel); the
// cross-session window is dropped when the file carries a risk: thought.
// C1: the block message renders risk: first and marks ⚠️ STALE lines.
export async function guardThoughts(
  env: EnforcerEnv,
  session: string | undefined,
  rel: string,
  abs: string,
): Promise<void> {
  const thinkHits = fileThoughtsIn(abs)
  if (thinkHits.length) {
    // risk detection anchors at category position (TA:\s*risk:) — a
    // gotcha: thought mentioning "risk:" in its text does not match.
    const risk = thinkHits.some(t => /TA:\s*risk:/i.test(t.content))
    const consulted = hasConsultedThoughts(session, rel, { risk, root: env.directory })
    if (thinkGateDecision({ hasThoughts: true, consulted }) === "block") {
      throw new OmtBlock(thinkGateMsg(rel, thinkHits, { staleLines: staleLinesFor(env.directory, rel) }))
    }
  }
}

// After-hook read-time injection (feature_022 D1): on the FIRST read of a
// thought-carrying file per session, append the file's thought-tags to the
// read result. Fail-open: this branch never throws.
// feature_023 Tier 1 (F14): args live on INPUT in tool.execute.after
// (SDK contract), so the caller passes input — output.args never existed in
// any SDK version (the dead branch shipped in feature_022).
export async function injectThoughtsOnRead(env: EnforcerEnv, input: any, output: any): Promise<void> {
  if (input?.tool !== "read") return
// TA: gotcha: F14 — output.args never existed in tool.execute.after (SDK contract: args on input, output={title,output,metadata}) so this branch never fired pre-feature_023; now reads input?.args?.filePath — see 6.testing/.../evaluation_001_post_shipment.md §3
  try {
    const raw = input?.args?.filePath ?? input?.args?.path ?? input?.args?.file
    if (typeof raw === "string" && raw) {
      const { abs, rel } = relOf(raw)
      const session = input?.sessionID || ""
      let seen = env.state.injected.get(session)
      if (!seen) {
        seen = new Set<string>()
        env.state.injected.set(session, seen)
      }
      if (!seen.has(abs)) {
        const hits = fileThoughtsIn(abs)
        if (hits.length) {
          seen.add(abs)
          const shown = hits.slice(0, 10)
            .map((t) => `  ${rel}:${t.line}: ${t.content}`).join("\n")
          output.output += `\n\n💡 TA: thoughts in ${rel} (${hits.length}) — review ` +
            `before editing (think-gate applies; omt_think_list{path:"${rel}"} ` +
            `records consult):\n${shown}` +
            (hits.length > 10
              ? `\n  … (+${hits.length - 10} more: omt_think_list{path:"${rel}"})`
              : "")
        }
      }
    }
  } catch (e: any) {
    env.safeLog("warn", "read-injection failed open: " + (e?.message || e))
  }
}
