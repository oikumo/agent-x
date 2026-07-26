// OMT++ enforcer session state (meta_harness_dsl R2; audit P5/F20).
//
// The FIVE process-lifetime state containers extracted from the enforcer
// monolith behind one factory, plus the ledger-derived session state
// (active unlock / nav unlock / per-feature phase) and the OmtBlock gate
// signal shared by every gate module:
//   • nav               — feature_020 per-session nav-vs-search tracking
//   • injected          — feature_022 D1 read-time thought-injection dedup
//   • bootstrapped      — R6 S6: ONE session-bootstrap Set (consolidates the
//                         old navRemindedSessions + omt_think's digestSessions;
//                         single emission site in the enforcer after-hook)
//   • hardSnapshot      — MVC++ pre-edit hard-error counts (delta gate)
//   • refactorSnapshots — TDD REFACTOR pre-edit file contents (revert)
//
// The ledger helpers are pure functions over the shared lib's lazy state
// paths (initOmtShared has run by the time any hook calls them).

import { ledgerPath, readJsonl, appendJsonl, UNLOCK_WINDOW_MS } from "../omt_shared"

// Intentional gate block: the only error a hook may propagate (everything
// else fails OPEN — never brick a working session).
export class OmtBlock extends Error {}

export function createSessionState() {
  return {
    // feature_020: sessionID -> nav/search usage
    nav: new Map<string, { usedNav: boolean; usedSearch: boolean; searchCount: number }>(),
    // feature_022 D1: sessionID -> absPaths already thought-injected (sessionless → "" bucket)
    injected: new Map<string, Set<string>>(),
    // R6 S6: sessions that already received the bootstrap injection (nav tip + TA digest)
    bootstrapped: new Set<string>(),
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

// --- ledger helpers (shared lib: append adds ts; reads fail-open) ---------
export function writeLedger(record: any): void {
  appendJsonl(ledgerPath(), record)
}

export function readLedger(): any[] {
  return readJsonl(ledgerPath())
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
