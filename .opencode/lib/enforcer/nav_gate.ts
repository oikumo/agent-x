// OMT++ navigation gate (feature_020) + session bootstrap (meta_harness_dsl
// R6 S6, rides R2).
//
// Two exports for the composition root:
//   • navGateBefore   — before-hook branch: track nav-vs-search usage and
//                       block doc-scoped grep/glob until a nav tool was used.
//   • sessionBootstrap — after-hook branch: ONE emission site per session for
//                       the nav reminder + the TA digest (S6 consolidation:
//                       replaces the enforcer's navRemindedSessions AND
//                       omt_think's digestSessions Tier-1c hook — load-order
//                       independent, single Set in session_state).

import { loadIr, relOf, thinkDigest } from "../omt_shared"
import { type EnforcerEnv } from "./session_state"

const NAV_TOOLS = new Set(["omt_nav"])  // improvement006/OPT-H: consolidated
// improvement007/OPT-E: .omt @var search_tools is the FUNCTIONAL source; the
// literal is the pinned IR-missing fallback. "read" was dropped from the old
// hand set — it is gate-exempt (navGateDecision) and not a conceptual search.
const FALLBACK_SEARCH_TOOLS = "grep|glob|rg|find"
function searchTools(): Set<string> {
  const v = loadIr()?.vars?.search_tools
  return new Set(String(typeof v === "string" && v ? v : FALLBACK_SEARCH_TOOLS).split("|").filter(Boolean))
}

// Whether a repo-relative path is a META HARNESS *documentation* path. The nav
// tools index docs only, so the "try nav first" expectation applies solely to
// doc-scoped searches.
// Defensive (DEFECT B): opencode's real tool-call shape can pass arrays/objects
// here, not just strings; guard so a non-string never reaches .startsWith.
// meta_harness_dsl R8 follow-up (F9 class, the @var harness_paths sibling):
// the compiled IR is the FUNCTIONAL source (.omt @var doc_paths — comma
// string, trailing "/" = prefix else exact); the literal below is only the
// fallback when the projection is missing/corrupt — the gate must never die
// open. The two are pinned in sync by test_omt_enforcer_guard_source_pins.py.
export function isDocPath(rel: string): boolean {
  if (typeof rel !== "string") return false
  const dp = loadIr()?.vars?.doc_paths
  if (typeof dp === "string" && dp) {
    return dp.split(",").some((e) => {
      const entry = e.trim()
      return entry.endsWith("/") ? rel.startsWith(entry) : rel === entry
    })
  }
  return rel === "AGENTS.md" || rel === "WORK.md" || rel.startsWith(".meta/")
}

// Decide whether a search-tool call must be blocked until navigation is used.
// Returns "allow" | "block". Pure (no I/O) so it can be unit-tested directly.
//   - `read` is never gated (M1: targeted file access is not a conceptual
//     search — e.g. reading WORK.md at startup or a file the user named).
//   - grep/glob/rg/find scoped to src/ or other non-doc paths are never gated
//     (M2: nav indexes docs, not code). A path-less search is treated as
//     doc-capable (conservative — it may hit docs).
export function navGateDecision(opts: {
  tool: string
  targetRel: string | null
  usedNav: boolean
  navUnlock: boolean
}): "allow" | "block" {
  // Load-safety heritage (feature_023 Tier 3, from the pre-R2 monolith where
  // the loader invoked every named export): destructure from {}-default so a
  // non-object arg fails open to "block" rather than crashing.
  const { tool, targetRel, usedNav, navUnlock } = opts ?? {}
  if (tool === "read") return "allow"
  // Defensive (DEFECT B): a non-string targetRel (array/object from opencode's
  // real tool-call shape) is treated as null (whole-repo / unknown scope).
  const rel = typeof targetRel === "string" ? targetRel : null
  const docScoped = !rel || isDocPath(rel)
  if (docScoped && !usedNav && !navUnlock) return "block"
  return "allow"
}

// feature_020: extract the repo-relative search target from a grep/glob call
// (the `path` arg). Returns null when no path is supplied (whole-repo search).
// Defensive (DEFECT B): opencode's real tool-call shape can pass arrays or
// objects for path/filePath/file (not just strings). Without coercion,
// relOf() calls isAbsolute/join on a non-string and the plugin crashes at
// bootstrap ("rel.startsWith is not a function"). Coerce: arrays -> first
// string element; non-string -> null.
export function getSearchPath(output: any): string | null {
  const raw = output?.args?.path ?? output?.args?.filePath ?? output?.args?.file
  if (!raw) return null
  const rawStr = Array.isArray(raw)
    ? (raw.find((v) => typeof v === "string") ?? null)
    : (typeof raw === "string" ? raw : null)
  if (!rawStr) return null
  return relOf(rawStr).rel
}

// improvement007 R8/OPT-G: the block text moved to the IR (@msg nav_required)
// — gate_driver's g.nav impl renders it via gateMsg.
const navReminderMsg = () =>
  `💡 NAVIGATION TIP: docs search → omt_nav (op=nav|list_sections|cross_ref|quick_ref) BEFORE grep/glob (read+src exempt; skip: omt_skip{scope:"nav"}).`

// Before-hook instrumentation (feature_020): track nav-vs-search usage for
// every tool. HDL-2 (improvement006/OPT-F): the BLOCK decision moved to the
// data-driven gate chain — lib/enforcer/gate_driver.ts IMPLS["g.nav"].
export async function navTrack(
  env: EnforcerEnv,
  session: string | undefined,
  input: any,
): Promise<void> {
  if (!session) return
  const toolName = input?.tool
  if (!env.state.nav.has(session)) {
    env.state.nav.set(session, { usedNav: false })
  }
  const state = env.state.nav.get(session)!
  if (NAV_TOOLS.has(toolName)) {
    state.usedNav = true
    env.safeLog("info", `Session ${session}: navigation tool ${toolName} used`)
  }
  // improvement007 R6: usedSearch/searchCount write-only counters deleted
  // (zero readers); searchTools() above stays — IR-accessor pin target.
}

// After-hook branch (R6 S6): the session bootstrap — compact TA digest
// appended ONCE per session to the FIRST tool result (any tool; the
// guaranteed agent-visible channel, headless or not — the F14c Tier-1c path,
// kept as the R6 S3 fallback because no agent-visible delivery channel from
// event hooks is verified on 1.18.5). Fail-open — never blocks a tool result.
// R7 T3 (F31): if the session's FIRST tool is already a nav tool, the agent is
// demonstrably compliant — skip the reminder WITHOUT marking navReminded, so
// it lands on the first NON-nav tool result instead (stops teaching the
// already-taught; saves ~120 tok × N turns in nav-first sessions). The digest
// still fires on the very first result regardless.
export async function sessionBootstrap(env: EnforcerEnv, input: any, output: any): Promise<void> {
  try {
    const session = input?.sessionID || ""
    const firstEver = !env.state.bootstrapped.has(session)
    const sendReminder = !NAV_TOOLS.has(input?.tool) && !env.state.navReminded.has(session)
    if (!firstEver && !sendReminder) return
    if (firstEver) env.state.bootstrapped.add(session)
    if (sendReminder) env.state.navReminded.add(session)
    if (typeof output?.output === "string") {
      const parts: string[] = []
      if (sendReminder) parts.push(navReminderMsg())
      if (firstEver) parts.push(thinkDigest())
      if (parts.length) output.output += "\n\n" + parts.join("\n\n")
    }
  } catch (e: any) {
    env.safeLog("warn", "session bootstrap failed open: " + (e?.message || e))
  }
}
