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

import { relOf, thinkDigest } from "../omt_shared"
import { OmtBlock, hasNavUnlock, type EnforcerEnv } from "./session_state"

const NAV_TOOLS = new Set(["omt_nav", "omt_list_sections", "omt_cross_ref", "omt_quick_ref"])
const SEARCH_TOOLS = new Set(["grep", "glob", "read", "rg", "find"])

// Whether a repo-relative path is a META HARNESS *documentation* path. The nav
// tools index docs only, so the "try nav first" expectation applies solely to
// doc-scoped searches.
// Defensive (DEFECT B): opencode's real tool-call shape can pass arrays/objects
// here, not just strings; guard so a non-string never reaches .startsWith.
export function isDocPath(rel: string): boolean {
  if (typeof rel !== "string") return false
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
function getSearchPath(output: any): string | null {
  const raw = output?.args?.path ?? output?.args?.filePath ?? output?.args?.file
  if (!raw) return null
  const rawStr = Array.isArray(raw)
    ? (raw.find((v) => typeof v === "string") ?? null)
    : (typeof raw === "string" ? raw : null)
  if (!rawStr) return null
  return relOf(rawStr).rel
}

const navRequiredMsg = () =>
  `⛔ OMT++ gate (feature_020): before grep/glob on META HARNESS docs, use ` +
  `omt_nav / omt_list_sections / omt_cross_ref / omt_quick_ref first (AGENTS.md MANDATORY). ` +
  `Only fall back to grep/glob if navigation returns nothing. ` +
  `\`read\` and src/non-doc searches are exempt. To override: omt_skip{reason:"...", scope:"nav"}.\n` +
  `Navigation tools: omt_nav{query:"SECTION:"}, omt_list_sections, omt_cross_ref{xref:"..."}, omt_quick_ref{workflow:"..."}`

const navReminderMsg = () =>
  `💡 NAVIGATION TIP (feature_020): Before searching META HARNESS *docs* with grep/glob, ` +
  `try the navigation tools first:\n` +
  `  • omt_nav{query:"SECTION:", tag_type:"CMD"} — find commands\n` +
  `  • omt_list_sections — list all documentation sections\n` +
  `  • omt_cross_ref{xref:"XREF_GUIDE"} — resolve cross-references\n` +
  `  • omt_quick_ref{workflow:"START_MAJOR"} — get workflow patterns\n` +
  `Note: \`read\` and src/code searches are exempt. To skip the nav gate: omt_skip{reason:"...", scope:"nav"}.`

// Before-hook branch (feature_020): track navigation vs search tool usage and
// gate doc-scoped searches behind prior nav usage. Runs for every tool;
// returns quickly for non-search tools.
export async function navGateBefore(
  env: EnforcerEnv,
  session: string | undefined,
  input: any,
  output: any,
): Promise<void> {
  if (!session) return
  const toolName = input?.tool
  if (!env.state.nav.has(session)) {
    env.state.nav.set(session, { usedNav: false, usedSearch: false, searchCount: 0 })
  }
  const state = env.state.nav.get(session)!

  // Track navigation tool usage
  if (NAV_TOOLS.has(toolName)) {
    state.usedNav = true
    env.safeLog("info", `Session ${session}: navigation tool ${toolName} used`)
  }

  // Nav-gate search tools — but only for documentation-scoped searches.
  if (SEARCH_TOOLS.has(toolName)) {
    state.usedSearch = true
    state.searchCount++

    // M1: `read` is never gated (targeted file access).
    // M2: grep/glob scoped to src/ or non-doc paths are never gated
    //     (nav indexes docs, not code). No path = doc-capable.
    const targetRel = toolName === "read" ? null : getSearchPath(output)
    const decision = navGateDecision({
      tool: toolName,
      targetRel,
      usedNav: state.usedNav,
      navUnlock: hasNavUnlock(session),
    })
    if (decision === "block") {
      env.safeLog("warn", `Session ${session}: blocked ${toolName} (doc search '${targetRel || "repo"}') without prior navigation`)
      throw new OmtBlock(navRequiredMsg())
    }
    env.safeLog("info", `Session ${session}: ${toolName} allowed (nav-gate passed)`)
  }
}

// After-hook branch (R6 S6): the session bootstrap — nav reminder + compact TA
// digest appended ONCE per session to the FIRST tool result (any tool; the
// guaranteed agent-visible channel, headless or not — the F14c Tier-1c path,
// kept as the R6 S3 fallback because no agent-visible delivery channel from
// event hooks is verified on 1.18.5). Fail-open — never blocks a tool result.
export async function sessionBootstrap(env: EnforcerEnv, input: any, output: any): Promise<void> {
  try {
    const session = input?.sessionID || ""
    if (!env.state.bootstrapped.has(session)) {
      env.state.bootstrapped.add(session)
      if (typeof output?.output === "string") {
        output.output += "\n\n" + navReminderMsg() + "\n\n" + thinkDigest()
      }
    }
  } catch (e: any) {
    env.safeLog("warn", "session bootstrap failed open: " + (e?.message || e))
  }
}
