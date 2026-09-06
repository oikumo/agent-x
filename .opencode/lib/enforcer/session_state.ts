// OMT++ enforcer session state (meta_harness_dsl R2; audit P5/F20).
//
// The process-lifetime state containers extracted from the enforcer monolith
// behind one factory, plus the ledger-derived session state (active unlock /
// nav unlock / per-feature phase) and the OmtBlock gate signal shared by every
// gate module:
//   • nav               — feature_020 per-session nav-vs-search tracking
//   • injected          — feature_022 D1 read-time thought-injection dedup
//   • bootstrapped      — R6 S6: ONE session-bootstrap Set (consolidates the
//                         old navRemindedSessions + omt_think's digestSessions;
//                         single emission site in the enforcer after-hook)
//   • navReminded       — R7 T3 (F31): nav-reminder delivery, tracked apart
//                         from bootstrapped so a nav-first session gets the
//                         reminder on its first NON-nav tool result instead
//   • hardSnapshot      — MVC++ pre-edit hard-error counts (delta gate)
//   • refactorSnapshots — TDD REFACTOR pre-edit file contents (revert)
//
// The ledger helpers are pure functions over the shared lib's lazy state
// paths (initOmtShared has run by the time any hook calls them).

import { readLedger as sharedReadLedger, appendLedger, UNLOCK_WINDOW_MS } from "../omt_shared"

// Intentional gate block: the only error a hook may propagate (everything
// else fails OPEN — never brick a working session).
export class OmtBlock extends Error {}

export function createSessionState() {
  return {
    // feature_020: sessionID -> nav usage (improvement007 R6: the write-only
    // usedSearch/searchCount instrumentation counters deleted — zero readers)
    nav: new Map<string, { usedNav: boolean }>(),
    // feature_kb_akb: sessionID -> KB-consult flag; consulted=true after any
    // omt_kb_nav op call in the session. Read by the g.kb gate predicate
    // `session_flag(kb_consulted)` (gate_driver.ts SESSION_FLAGS).
    kb: new Map<string, { consulted: boolean }>(),
    // feature_022 D1: sessionID -> absPaths already thought-injected (sessionless → "" bucket)
    injected: new Map<string, Set<string>>(),
    // R6 S6: sessions that already received the bootstrap injection (nav tip + TA digest)
    bootstrapped: new Set<string>(),
    // R7 T3 (F31): sessions already shown the nav reminder — tracked apart from
    // bootstrapped so a nav-first session gets it on its first NON-nav result
    navReminded: new Set<string>(),
    // MVC++ delta gate: abs path -> {rule: errorCount} captured pre-edit
    hardSnapshot: new Map<string, Record<string, number>>(),
    // TDD REFACTOR: abs path -> file content captured pre-edit (revert source)
    refactorSnapshots: new Map<string, string>(),
  }
}
export type SessionState = ReturnType<typeof createSessionState>

export type SafeLog = (level: string, message: string) => void
export type Notify = (message: string) => Promise<void>

// The ambient context every gate module receives (assembled once by the
// composition root).
export interface EnforcerEnv {
  client: any
  $: any
  directory: string
  state: SessionState
  safeLog: SafeLog
  notify: Notify
}

export function makeSafeLog(client: any): SafeLog {
  return (level, message) => {
    try { client?.app?.log?.({ service: "omt-enforcer", level, message }) }
    catch { /* logging is best-effort */ }
  }
}

export function makeNotify(client: any, safeLog: SafeLog): Notify {
  // Non-blocking surfacing: try a toast, always fall back to the log.
  return async (message) => {
    try { await client?.tui?.showToast?.({ message, variant: "warning" }) } catch { /* ignore */ }
    safeLog("warn", message)
  }
}

// --- ledger helpers (shared lib: append adds ts + rotates at cap (R4); reads
// scan the latest archive + hot file and fail-open) --------------------------
export function writeLedger(record: any): void {
  appendLedger(record)
}

export function readLedger(): any[] {
  return sharedReadLedger()
}

// Latest phase/skip unlocking edits for this session (exact match preferred,
// else any record within the time window — keeps the gate usable if sessionID
// is not threaded through on this opencode version).
export function getActiveUnlock(session: string | undefined): { type: string; record: any } | null {
  const recs = readLedger().filter((r) => r.kind === "phase" || r.kind === "skip")
  if (!recs.length) return null
  const mine = session ? recs.filter((r) => r.session === session) : []
  let chosen = mine.length ? mine[mine.length - 1] : null
  if (!chosen) {
    const now = Date.now()
    const recent = recs.filter((r) => {
      const t = Date.parse(r.ts || "")
      return !Number.isNaN(t) && now - t < UNLOCK_WINDOW_MS
    })
    chosen = recent.length ? recent[recent.length - 1] : null
  }
  return chosen ? { type: chosen.kind, record: chosen } : null
}

// feature_020 nav escape: is there an active omt_skip{scope:"nav"|"all"} for
// this session (or, fallback, within the unlock window)? Unlike
// getActiveUnlock(), this ignores phase records so a later phase declaration
// does not shadow a nav skip. (M1 escape hatch.)
export function hasNavUnlock(session: string | undefined): boolean {
  const recs = readLedger().filter(
    (r) => r.kind === "skip" && (r.scope === "nav" || r.scope === "all"),
  )
  if (!recs.length) return false
  const mine = session ? recs.filter((r) => r.session === session) : []
  let chosen = mine.length ? mine[mine.length - 1] : null
  if (!chosen) {
    const now = Date.now()
    const recent = recs.filter((r) => {
      const t = Date.parse(r.ts || "")
      return !Number.isNaN(t) && now - t < UNLOCK_WINDOW_MS
    })
    chosen = recent.length ? recent[recent.length - 1] : null
  }
  return !!chosen
}

// feature_054 C2 small_task_fast_path: bug_fix/test phases auto-satisfy
// g.nav+g.kb. The phase tool flips the in-memory flags immediately; this
// ledger-backed check keeps the fast path durable across plugin reloads and
// session-ID drift (window fallback mirrors getActiveUnlock). Major/new_screen
// stay hard — only bug_fix/test qualify. MUST NOT extend to g.think/g.protect.
export const FAST_PATH_TASK_TYPES: ReadonlySet<string> = new Set(["bug_fix", "test"])

export function hasFastPathUnlock(session: string | undefined): boolean {
  // Latest-PHASE-wins (skips are not the authority): the session's latest
  // phase record decides — a later minor/major declaration turns the fast
  // path OFF again. Mirrors getActiveUnlock's selection shape (session-matched
  // preferred, else window-recent) but reads only phase records.
  const phases = readLedger().filter((r) => r.kind === "phase")
  if (!phases.length) return false
  const mine = session ? phases.filter((r) => r.session === session) : []
  let chosen = mine.length ? mine[mine.length - 1] : null
  if (!chosen) {
    const now = Date.now()
    const recent = phases.filter((r) => {
      const t = Date.parse(r.ts || "")
      return !Number.isNaN(t) && now - t < UNLOCK_WINDOW_MS
    })
    chosen = recent.length ? recent[recent.length - 1] : null
  }
  return FAST_PATH_TASK_TYPES.has(String(chosen?.task_type || ""))
}

// Latest phase record for a specific feature. Exact session match is preferred,
// then we fall back to the recent single-user window. Unlike getActiveUnlock(),
// this ignores skip records and unrelated features so omt_complete cannot be
// shadowed by a later skip or another task's phase declaration.
export function getActiveFeaturePhase(feature: string, session: string | undefined): any | null {
  const recs = readLedger().filter((r) => r.kind === "phase" && r.feature === feature)
  if (!recs.length) return null
  const mine = session ? recs.filter((r) => r.session === session) : []
  let chosen = mine.length ? mine[mine.length - 1] : null
  if (!chosen) {
    const now = Date.now()
    const recent = recs.filter((r) => {
      const t = Date.parse(r.ts || "")
      return !Number.isNaN(t) && now - t < UNLOCK_WINDOW_MS
    })
    chosen = recent.length ? recent[recent.length - 1] : null
  }
  return chosen
}
