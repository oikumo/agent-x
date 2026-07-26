// OMT++ Process Enforcer — opencode plugin (feature_006).
//
// Turns AGENTS.md's *voluntary* process checkpoints into a *real* gate, tuned for a
// solo-dev learning scaffold: it blocks the edit that would skip a phase, but every block
// is a teaching message that names the OMT++ rule and the exact next command. Internal
// errors fail OPEN (never brick a working session); only genuine process violations block.
//
// Mechanics:
//   • omt_phase  custom tool → agent declares task_type/phase/scope; recorded in the ledger.
//   • omt_skip   custom tool → logged escape hatch that unlocks edits for the session.
//   • tool.execute.before → gate edits to src/ (needs a phase), tests/ (needs approval),
//     and hard-deny README/.env/uv.lock/LICENSE.
//   • tool.execute.after  → run the MVC++ linter on touched src/*.py, surface warnings.
//
// Ledger: .meta/.omt/ledger.jsonl  (gitignored runtime state, one JSON record per line)
//
// API note (verify on opencode 1.17.x via the Step-0 probe): assumes `input.sessionID`
// on tool.execute.before and `context.sessionID` on custom-tool execute. If absent, the
// gate falls back to an 8-hour time window so it still functions for a single user.

import { tool } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs"
import { join } from "node:path"
import { execFileSync } from "node:child_process"
// Single source (meta_harness_dsl R1): cross-plugin constants, state paths,
// JSONL IO, repo-root and the e2e-receipt guard live in the shared lib.
import {
  initOmtShared, ledgerPath, thoughtsIndexPath, relOf, readJsonl, appendJsonl,
  resolveFeatureDir, globToRegex, UNLOCK_WINDOW_MS, THOUGHT_PATTERN,
  omtHarnessE2eStatus,
} from "../lib/omt_shared"


const EDIT_TOOLS = new Set(["edit", "write", "patch", "multiedit"])
const NAV_TOOLS = new Set(["omt_nav", "omt_list_sections", "omt_cross_ref", "omt_quick_ref"])
const SEARCH_TOOLS = new Set(["grep", "glob", "read", "rg", "find"])
const VALID_TASK_TYPES = new Set([
  "bug_fix", "minor_feature", "major_feature", "new_screen", "refactor", "test", "docs",
])
// Task types that may not touch src/ until a design artifact exists on disk (guide §12).
const ARTIFACT_REQUIRED = new Set(["major_feature", "new_screen"])
// OMT_HARNESS_E2E_COMMAND / _RECEIPT / _TEST constants: single source is the
// shared lib (meta_harness_dsl R1).

// Valid phase transitions per guide §12
const VALID_TRANSITIONS: Record<string, string[]> = {
  Analysis: ["Design", "Testing"],
  Design: ["Programming", "Analysis"],
  Programming: ["Testing", "Design", "Analysis"],
  Testing: ["Analysis", "Design", "Programming", "Done"],
}

// 8-hour unlock window: single source is the shared lib (R1); tdd_check.py
// keeps a cross-language copy (pinned to agree).

// Phase exit requirements per guide §12 — only enforced for ARTIFACT_REQUIRED task types
const PHASE_EXIT_REQUIREMENTS: Record<string, { phase: string; patterns: string[]; description: string }[]> = {
  // Analysis → Design requires: Use case, Operation list, Analysis artifacts
  Analysis: [
    { phase: "Requirements", patterns: ["FEATURE.md"], description: "Use case / FEATURE.md" },
    { phase: "Analysis", patterns: ["analysis_001_*.md"], description: "Analysis docs (analysis_001_*.md)" },
  ],
  // Design → Programming requires: Design class diagram, Operation specs
  Design: [
    { phase: "Design", patterns: ["design_001_*.md"], description: "Design doc (design_001_*.md)" },
    { phase: "Operations", patterns: ["operation_spec_*.md", "operations.md"], description: "Operation specifications (operation_spec_*.md or operations.md)" },
  ],
  // Programming → Testing requires: Unit tests, Integration tests
  Programming: [
    { phase: "Implementation", patterns: ["*.md"], description: "Implementation notes (5.implementation/features/...)" },
    { phase: "Unit tests", patterns: ["test_*.py", "*_test.py"], description: "Unit tests (tests/features/<feature>/...)" },
  ],
  // Testing → Done requires: System tests
  Testing: [
    { phase: "System tests", patterns: ["test_report.md"], description: "System test report (6.testing/features/...)" },
  ],
}

// resolveFeatureDir + globToRegex: single source is the shared lib (R1) —
// imported above.

// Check if required artifacts for a phase exist for a feature
function checkPhaseExitArtifacts(repoRoot: string, feature: string, fromPhase: string): { ok: boolean; missing: string[] } {
  if (!feature) return { ok: true, missing: [] }
  const requirements = PHASE_EXIT_REQUIREMENTS[fromPhase]
  if (!requirements) return { ok: true, missing: [] }

  const featureNum = feature.match(/feature_(\d+)/)?.[0] || feature
  const PROCESS_ROOT = ".meta/software_development_process"
  const missing: string[] = []

  for (const req of requirements) {
    let exists = false
    for (const pattern of req.patterns) {
      let dir: string | null = null
      if (req.phase === "Requirements") {
        dir = resolveFeatureDir(join(repoRoot, PROCESS_ROOT, "2.requirements", "features"), feature, featureNum)
      } else if (req.phase.startsWith("Analysis")) {
        dir = resolveFeatureDir(join(repoRoot, PROCESS_ROOT, "3.analysis", "features"), feature, featureNum)
      } else if (req.phase === "Design" || req.phase === "Operations") {
        dir = resolveFeatureDir(join(repoRoot, PROCESS_ROOT, "4.design", "features"), feature, featureNum)
      } else if (req.phase === "Implementation") {
        dir = resolveFeatureDir(join(repoRoot, PROCESS_ROOT, "5.implementation", "features"), feature, featureNum)
      } else if (req.phase.startsWith("Unit tests")) {
        dir = resolveFeatureDir(join(repoRoot, "tests", "features"), feature, featureNum)
      } else if (req.phase.startsWith("System tests")) {
        dir = resolveFeatureDir(join(repoRoot, PROCESS_ROOT, "6.testing", "features"), feature, featureNum)
      } else {
        continue
      }

      try {
        if (dir) {
          const files = readdirSync(dir, { recursive: true })
          const regex = globToRegex(pattern)
          exists = files.some(f => regex.test(f))
          if (exists) break
        }
      } catch { /* ignore */ }
    }
    if (!exists) missing.push(req.description)
  }
  return { ok: missing.length === 0, missing }
}

class OmtBlock extends Error {}

// --- feature_020 navigation gate (module-level, pure, unit-testable) --------
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
  // feature_023 Tier 3 load-safety: opencode's loader invokes every named
  // export with the plugin-context object (sometimes undefined / {} during
  // reload). Destructure from {}-default so a non-object arg fails open to
  // "block" rather than crashing (the property the loader relies on).
  const { tool, targetRel, usedNav, navUnlock } = opts ?? {}
  if (tool === "read") return "allow"
  // Defensive (DEFECT B): a non-string targetRel (array/object from opencode's
  // real tool-call shape) is treated as null (whole-repo / unknown scope).
  const rel = typeof targetRel === "string" ? targetRel : null
  const docScoped = !rel || isDocPath(rel)
  if (docScoped && !usedNav && !navUnlock) return "block"
  return "allow"
}

// --- feature_021 think-gate (module-level, pure/exported + ledger reader) ---
// Pure decision: may the agent edit a file that carries TA: thoughts?
//   hasThoughts=false → allow (nothing to review).
//   hasThoughts=true && consulted → allow.
//   hasThoughts=true && !consulted → block.
export function thinkGateDecision(opts: {
  hasThoughts: boolean
  consulted: boolean
}): "allow" | "block" {
  // feature_023 Tier 3 load-safety: an undefined arg must fail open to "allow"
  // (no thoughts to review) instead of crashing on `.hasThoughts` destructure.
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

// THOUGHT_PATTERN: single source is the shared lib (meta_harness_dsl R1) —
// imported above; pinned by tests/scripts/omt/test_thought_pattern_pin.py.

// Grep TA: in a single file (cheap; used by the think-gate before-hook).
// Takes an absolute path so it works both at module level and inside the plugin.
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

export const OmtEnforcer = async ({ client, $, directory: cwd, worktree }) => {
  // F2/F17 (meta_harness_dsl R1): repo root = worktree ?? directory.
  // `directory` is the current working directory, so a subdir launch breaks
  // repo-relative paths exactly like a bare cwd did pre-R1; `worktree`
  // is the git worktree path. Body references below keep the name `directory`
  // (byte-stable e2e pins), now bound to the corrected root; the shared lib is
  // initialized with the same value.
  const directory = worktree ?? cwd
  initOmtShared(directory)

  // --- session state for feature_020 navigation enforcement ---
  // Track which sessions have used navigation tools vs search tools
  const sessionNavState = new Map<string, { usedNav: boolean; usedSearch: boolean; searchCount: number }>()

  // --- feature_022 D1: read-time thought injection state ---
  // absPaths already injected per session (sessionless → shared "" bucket).
  // Process-lifetime, mirrors sessionNavState; bounded by thought-files read.
  const injectedThisSession = new Map<string, Set<string>>()

  // --- feature_023 Tier 1c (F14c): live nav-reminder state ---
  // opencode 1.18.3 NEVER dispatches `session.start` (binary audit,
  // analysis_001 addendum) — the navReminderMsg() registration at line ~883
  // is inert. Emit the reminder once per session on the FIRST
  // tool.execute.after instead (any tool). Process-lifetime, mirrors the
  // two maps above; bounded by distinct sessionIDs.
  const navRemindedSessions = new Set<string>()

  // --- ledger helpers (shared lib: append adds ts; reads fail-open) ---------
  const writeLedger = (record) => {
    appendJsonl(ledgerPath(), record)
  }

  const readLedger = () => readJsonl(ledgerPath())

  // Latest phase/skip unlocking edits for this session (exact match preferred,
  // else any record within the time window — keeps the gate usable if sessionID
  // is not threaded through on this opencode version).
  const getActiveUnlock = (session) => {
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
  const hasNavUnlock = (session) => {
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
  const getActiveFeaturePhase = (feature, session) => {
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

  // Auto-detect a feature's design artifact from its slug (hardening — guide §12),
  // so the gate doesn't depend on the agent passing design_doc by hand.
  const detectDesignArtifact = (feature) => {
    if (!feature) return null
    const m = String(feature).match(/feature_(\d+)/)
    if (!m) return null
    const num = m[1]
    const rel = join(".meta", "software_development_process", "4.design", "features")
    const base = join(directory, rel)
    if (!existsSync(base)) return null
    let dirs
    try { dirs = readdirSync(base) } catch { return null }
    for (const d of dirs) {
      const match = d === `feature_${num}` || d.startsWith(`feature_${num}.`) || d.startsWith(`feature_${num}_`)
      if (!match) continue
      let files
      try { files = readdirSync(join(base, d)) } catch { continue }
      // Strict matching: only design_NNN_*.md files count as design artifacts (guide §12)
      const hit = files.find((f) => /^design_\d+_.+\.md$/i.test(f))
      // Optional: warn if .md files exist but no design_*.md (logged, not blocking)
      if (!hit && files.some(f => f.toLowerCase().endsWith(".md"))) {
        safeLog("warn", `Feature ${feature} has .md files but no design_NNN_*.md artifact in ${d}/`)
      }
      if (hit) return join(rel, d, hit)
    }
    return null
  }

  // Resolve the design artifact for a phase record: explicit design_doc first,
  // else auto-detected from the feature slug. Returns repo-relative path or null.
  const resolveArtifact = (record) => {
    if (record.design_doc && existsSync(join(directory, record.design_doc))) return record.design_doc
    const auto = detectDesignArtifact(record.feature)
    return auto && existsSync(join(directory, auto)) ? auto : null
  }
  const artifactPresent = (record) => !!resolveArtifact(record)

  // --- MVC++ lint delta (block only NEWLY introduced hard errors) ----------
  const lintFindings = async (abs) => {
    try {
      const res = await $`uv run scripts/omt/mvc_check.py ${abs} --json`.cwd(directory).quiet().nothrow()
      return JSON.parse(res.stdout.toString() || "{}").findings || []
    } catch { return [] }
  }
  const countByRule = (findings) => {
    const m = {}
    for (const f of findings) m[f.rule] = (m[f.rule] || 0) + 1
    return m
  }
  const hardSnapshot = new Map()  // abs path -> {rule: errorCount} captured pre-edit
  const refactorSnapshots = new Map()  // abs path -> file content captured pre-edit (REFACTOR revert)

  const safeLog = (level, message) => {
    try { client?.app?.log?.({ service: "omt-enforcer", level, message }) }
    catch { /* logging is best-effort */ }
  }

  const notify = async (message) => {
    // Non-blocking surfacing: try a toast, always fall back to the log.
    try { await client?.tui?.showToast?.({ message, variant: "warning" }) } catch { /* ignore */ }
    safeLog("warn", message)
  }

  // --- path classification -------------------------------------------------
  // relOf(raw) → {abs, rel} is imported from the shared lib (R1); it resolves
  // against the same root this factory was initialized with above.
  const isProtected = (rel) =>
    rel === "README.md" || rel === "uv.lock" || rel === "LICENSE" ||
    rel === ".env" || rel.startsWith(".env.")
  const isTests = (rel) => rel === "tests" || rel.startsWith("tests/")
  const isSrc = (rel) => rel.startsWith("src/")
  // isOmtHarness: single source is the shared lib (R1) — used inside the
  // imported omtHarnessE2eStatus below.

  // feature_020: extract the repo-relative search target from a grep/glob call
  // (the `path` arg). Returns null when no path is supplied (whole-repo search).
  // Defensive (DEFECT B): opencode's real tool-call shape can pass arrays or
  // objects for path/filePath/file (not just strings). Without coercion,
  // relOf() calls isAbsolute/join on a non-string and the plugin crashes at
  // bootstrap ("rel.startsWith is not a function"). Coerce: arrays -> first
  // string element; non-string -> null.
  const getSearchPath = (output) => {
    const raw = output?.args?.path ?? output?.args?.filePath ?? output?.args?.file
    if (!raw) return null
    const rawStr = Array.isArray(raw)
      ? (raw.find((v) => typeof v === "string") ?? null)
      : (typeof raw === "string" ? raw : null)
    if (!rawStr) return null
    return relOf(rawStr).rel
  }

  // receiptTimestampMs / isGitDirty / omtHarnessE2eStatus: single source is
  // the shared lib (R1) — omtHarnessE2eStatus imported above; the before-hook
  // call site below is unchanged.

  // --- teaching messages ---------------------------------------------------
  const denyMsg = (rel) =>
    `⛔ OMT++ gate: '${rel}' is protected by AGENTS.md (Core Directives — NEVER modify ` +
    `README.md / .env / uv.lock / LICENSE). Edit refused. If this is truly intended, ask the user.`

  const testsMsg = (rel) =>
    `⛔ OMT++ gate: editing '${rel}' requires explicit canary-test approval (AGENTS.md ` +
    `Stop Point #4). Get approval, then unlock with: omt_skip{reason:"approved canary test", scope:"tests"}.`

  const noPhaseMsg = (rel) =>
    `⛔ OMT++ gate: declare your OMT++ phase before editing src/ ('${rel}'). ` +
    `Run omt_phase{ task_type, scope } first (guide §2, §13). ` +
    `Trivial fix? omt_phase{task_type:"bug_fix", scope:"..."} is enough. To override: omt_skip{reason:"..."}.`

  const navReminderMsg = () =>
    `💡 NAVIGATION TIP (feature_020): Before searching META HARNESS *docs* with grep/glob, ` +
    `try the navigation tools first:\n` +
    `  • omt_nav{query:"SECTION:", tag_type:"CMD"} — find commands\n` +
    `  • omt_list_sections — list all documentation sections\n` +
    `  • omt_cross_ref{xref:"XREF_GUIDE"} — resolve cross-references\n` +
    `  • omt_quick_ref{workflow:"START_MAJOR"} — get workflow patterns\n` +
    `Note: \`read\` and src/code searches are exempt. To skip the nav gate: omt_skip{reason:"...", scope:"nav"}.`

  const navRequiredMsg = () =>
    `⛔ OMT++ gate (feature_020): before grep/glob on META HARNESS docs, use ` +
    `omt_nav / omt_list_sections / omt_cross_ref / omt_quick_ref first (AGENTS.md MANDATORY). ` +
    `Only fall back to grep/glob if navigation returns nothing. ` +
    `\`read\` and src/non-doc searches are exempt. To override: omt_skip{reason:"...", scope:"nav"}.\n` +
    `Navigation tools: omt_nav{query:"SECTION:"}, omt_list_sections, omt_cross_ref{xref:"..."}, omt_quick_ref{workflow:"..."}`

  const artifactMsg = (tt, record) =>
    `⛔ OMT++ gate: task_type '${tt}' may not edit src/ until a design artifact exists ` +
    `(guide §12). The gate auto-detects one under 4.design/features/feature_<n>/ from your ` +
    `feature slug ('${record.feature || "<none declared>"}'), or you can pass ` +
    `omt_phase{..., design_doc:"<path>"}. Scaffold one with: ` +
    `uv run scripts/omt/new_feature.py "<name>" --type ${tt}.`

  // --- custom tools --------------------------------------------------------
  // omt_status is registered by .opencode/plugins/omt_status.ts as its own
  // standalone plugin. Keeping it out of this enforcer avoids dynamic-import
  // cache/loading failures and duplicate tool registration.

  const omt_phase = tool({
    description:
      "Declare your OMT++ phase before editing src/. Records task_type/phase/scope to the " +
      "process ledger and unlocks edits according to the guide §12 matrix. This is the real " +
      "version of AGENTS.md's PROCESS CHECK. Call once per task before touching src/.",
    args: {
      task_type: tool.schema.string().describe(
        "one of: bug_fix, minor_feature, major_feature, new_screen, refactor, test, docs"),
      scope: tool.schema.string().describe("one sentence describing what 'done' looks like"),
      phase: tool.schema.string().optional().describe("Analysis | Design | Programming | Testing"),
      feature: tool.schema.string().optional().describe("feature slug, e.g. feature_006.x"),
      design_doc: tool.schema.string().optional().describe(
        "repo-relative path to the design/analysis artifact (required for major_feature/new_screen)"),
      tdd: tool.schema.boolean().optional().describe(
        "activate TDD enforcement for Programming phase (auto-on for major_feature/new_screen)"),
    },
    async execute(args, context) {
      const tt = String(args.task_type || "").trim()
      if (!VALID_TASK_TYPES.has(tt)) {
        return `❌ invalid task_type '${tt}'. Use one of: ${[...VALID_TASK_TYPES].join(", ")}.`
      }
      const session = context?.sessionID || undefined
      const newPhase = args.phase || ""

      // Phase exit validation: if transitioning FROM a feature-sized phase,
      // check artifacts exist. Bug fixes/refactors/tests intentionally keep the
      // lightweight §12 path: a recorded phase is enough.
      if (newPhase && args.feature) {
        const prevPhaseRecord = getActiveFeaturePhase(args.feature, session)
        if (prevPhaseRecord?.phase && prevPhaseRecord.phase !== newPhase) {
          const exitTaskType = prevPhaseRecord.task_type || tt
          if (ARTIFACT_REQUIRED.has(exitTaskType)) {
            const { ok, missing } = checkPhaseExitArtifacts(directory, args.feature, prevPhaseRecord.phase)
            if (!ok) {
              return `⛔ OMT++ gate: cannot leave ${prevPhaseRecord.phase} phase — missing required artifacts (guide §12):\n` +
                missing.map(m => `  • ${m}`).join("\n") +
                `\nComplete these before transitioning to ${newPhase}.`
            }
          }
        }
      }

      const tddMode = args.tdd === true || (ARTIFACT_REQUIRED.has(tt) && args.phase === "Programming")
      writeLedger({
        kind: "phase", session, task_type: tt, phase: args.phase || "",
        scope: args.scope || "", feature: args.feature || "", design_doc: args.design_doc || "",
        tdd_mode: tddMode,
      })
      const lines = [
        "📋 OMT++ PROCESS CHECK (recorded)",
        `- Task type: ${tt}`,
        `- Phase: ${args.phase || "(unspecified)"}`,
        `- Scope: ${args.scope || "(none)"}`,
      ]
      if (ARTIFACT_REQUIRED.has(tt)) {
        const found = resolveArtifact({ design_doc: args.design_doc, feature: args.feature })
        lines.push(found
          ? `- Artifact: ✅ ${found}`
          : `- Artifact: ⚠️ none found (checked design_doc + 4.design/features/${args.feature || "<feature>"}/) ` +
            `— src/ stays BLOCKED until a design doc exists ` +
            `(scaffold: uv run scripts/omt/new_feature.py "<name>" --type ${tt}).`)
      }
      lines.push("✅ src/ edits unlocked for this session" +
        (ARTIFACT_REQUIRED.has(tt) ? " once the artifact check passes." : "."))
      return lines.join("\n")
    },
  })

  const omt_skip = tool({
    description:
      "Logged escape hatch. Unlocks edits (or the feature_020 nav gate) without a full phase " +
      "declaration; the reason is recorded in the ledger for audit. Use sparingly (emergencies, " +
      "approved canary tests). Scopes: src | tests | nav | all (default: all).",
    args: {
      reason: tool.schema.string().describe("why the process is being skipped"),
      scope: tool.schema.string().optional().describe("src | tests | nav | all (default: all)"),
    },
    async execute(args, context) {
      const session = context?.sessionID || undefined
      const scope = args.scope || "all"
      writeLedger({
        kind: "skip", session, reason: args.reason || "(none)", scope,
        tests_approved: scope === "tests" || scope === "all",
      })
      const scopeNote =
        scope === "all" ? "scope=all unlocks src/tests/nav; also permits README.md/uv.lock/LICENSE edits (AGENTS.md #5 'unless explicitly asked'); .env stays denied."
        : scope === "nav" ? "scope=nav unlocks the feature_020 navigation gate for this session (grep/glob on docs no longer require prior omt_nav)."
        : scope === "tests" ? "scope=tests unlocks tests/ edits (canary approval)."
        : "scope=src unlocks src/ edits."
      return `⚠️ OMT++ skip recorded (scope=${scope}): "${args.reason}". ` +
        "This override is logged in .meta/.omt/ledger.jsonl. " + scopeNote
    },
  })

  // --- omt_complete: Verify phase completion and optionally advance ---
  const omt_complete = tool({
    description:
      "Verify that all required artifacts for the current phase exist, then optionally advance to the next phase. " +
      "Use this to formally complete a phase and unlock the next one with artifact validation.",
    args: {
      feature: tool.schema.string().describe("feature slug, e.g. feature_006.x"),
      advance_to: tool.schema.string().optional().describe("optional: phase to advance to after verification (Design | Programming | Testing | Done)"),
    },
    async execute(args, context) {
      const session = context?.sessionID || undefined
      const feature = args.feature || ""
      const advanceTo = args.advance_to || ""

      if (!feature) {
        return `❌ feature slug required (e.g., feature_006.x)`
      }

      const phaseRecord = getActiveFeaturePhase(feature, session)
      if (!phaseRecord) {
        return `❌ no active phase for feature ${feature} in this session`
      }

      const currentPhase = phaseRecord.phase
      if (!currentPhase) {
        return `❌ no current phase declared for this feature`
      }

      // Check exit artifacts for feature-sized work only. For bug fixes,
      // refactors, tests, and docs, omt_complete should verify the declared
      // process step without inventing major-feature artifact requirements.
      if (ARTIFACT_REQUIRED.has(phaseRecord.task_type || "")) {
        const { ok, missing } = checkPhaseExitArtifacts(directory, feature, currentPhase)
        if (!ok) {
          return `⛔ Phase ${currentPhase} incomplete — missing required artifacts:\n` +
            missing.map(m => `  • ${m}`).join("\n") +
            `\nCreate these before completing ${currentPhase}.`
        }
      }

      // All artifacts present - record completion
      // TDD validate-exit: check coverage gaps and dangling reds
      try {
        const tddRes = await $`uv run scripts/omt/tdd_check.py validate-exit --feature ${feature}`
          .cwd(directory).quiet().nothrow()
        const tddData = JSON.parse(tddRes.stdout.toString() || '{"ok":true}')
        if (!tddData.ok) {
          let msg = `⛔ TDD phase exit blocked:\n`
          if (tddData.dangling_reds?.length)
            msg += `  Dangling RED cycles: ${tddData.dangling_reds.join(", ")}\n`
          if (tddData.coverage_gaps?.length) {
            msg += `  Coverage gaps:\n`
            for (const g of tddData.coverage_gaps) {
              const names = g.untested.map((m: any) => m.class ? `${m.class}.${m.method}` : m.method).join(", ")
              msg += `    ${g.file}: ${names}\n`
            }
          }
          return msg + `Write tests or call omt_skip{reason:"..."} to override.`
        }
      } catch (e) {
        safeLog("warn", `TDD validate-exit failed: ${e?.message || e}`)
        return `⛔ TDD validate-exit error: ${e?.message || e}. Phase completion blocked.`
      }

      writeLedger({
        kind: "complete",
        session,
        feature,
        phase: currentPhase,
        ts: new Date().toISOString(),
      })

      let result = `✅ Phase ${currentPhase} complete for ${feature} — all artifacts verified.`

      // Advance to next phase if requested
      if (advanceTo) {
        const validNext = VALID_TRANSITIONS[currentPhase] || []
        if (!validNext.includes(advanceTo)) {
          return result + `\n⚠️ Invalid transition: ${currentPhase} → ${advanceTo}. Valid: ${validNext.join(", ")}`
        }

        // Declare new phase (will be validated on next omt_phase call, but we can pre-check)
        writeLedger({
          kind: "phase", session, task_type: phaseRecord.task_type || "major_feature",
          phase: advanceTo, scope: phaseRecord.scope || "", feature, design_doc: "",
        })
        result += `\n➡️ Advanced to ${advanceTo} phase.`
      }

      // Auto-sync WORK.md
      try { await syncWorkMdFromLedger() } catch { /* ignore */ }

      return result
    },
  })

  // --- TDD tools (feature_016: thin wrappers delegating to tdd_check.py) ---
  const tddTool = (name: string, subcmd: string, desc: string, argNames: string[]) => tool({
    description: desc,
    args: Object.fromEntries(
      argNames.map(n => [n, tool.schema.string().optional()])
    ),
    async execute(args, context) {
      const session = context?.sessionID || ""
      const flags = [subcmd]
      for (const [k, v] of Object.entries(args)) {
        if (v !== undefined && v !== null && v !== "")
          flags.push(`--${k.replace(/_/g, "-")}`, String(v))
      }
      flags.push("--session", session)
      try {
        const res = await $`uv run scripts/omt/tdd_check.py ${flags}`
          .cwd(directory).quiet().nothrow()
        const data = JSON.parse(res.stdout.toString() || "{}")
        return data.message || JSON.stringify(data)
      } catch (e) {
        safeLog("warn", `tdd_check.py ${subcmd} failed: ${e?.message || e}`)
        return `⚠️ TDD engine error: ${e?.message || e}`
      }
    },
  })

  const omt_testlist = tddTool("omt_testlist", "testlist",
    "Record the TDD test list (behaviors to implement). Sets TDD state to TESTLIST.",
    ["behaviors", "feature"])
  const omt_red = tddTool("omt_red", "start",
    "Declare a failing test (TDD Red). Runs pytest to verify the test fails, then AST analysis for true-RED verification. Sets TDD state to RED (test hat: only tests/ edits allowed).",
    ["test_node", "target_src", "feature"])
  const omt_green = tddTool("omt_green", "green",
    "Declare a passing test (TDD Green). Runs pytest to verify the test passes. Sets TDD state to GREEN (code hat: only src/ edits allowed).",
    ["test_node", "feature"])
  const omt_refactor = tddTool("omt_refactor", "refactor",
    "Declare refactor state (TDD Refactor). Runs pytest to verify tests are green. Sets TDD state to REFACTOR (refactor hat: only src/ edits allowed, tests must stay green per micro-edit).",
    ["test_node", "feature"])
  const omt_done = tddTool("omt_done", "done",
    "Declare TDD completion. Runs full suite + checklist verification. Sets TDD state to DONE.",
    ["feature"])
  async function syncWorkMdFromLedger() {
    const workMdPath = join(directory, "WORK.md")
    if (!existsSync(workMdPath)) return

    const ledger = readLedger()
    const completedFeatures = new Set<string>()

    // Find all completed phases from ledger
    for (const rec of ledger) {
      if (rec.kind === "complete" && rec.feature) {
        completedFeatures.add(rec.feature)
      }
    }

    let content = readFileSync(workMdPath, "utf8")
    let modified = false

    // Update checkboxes for completed features
    for (const feature of completedFeatures) {
      // Match both full slug (feature_006.opencode_process_enforcement) 
      // and short form (feature_006) since WORK.md may use either
      const shortFeature = feature.match(/feature_\d+/)?.[0]
      const matchPatterns = [feature]
      if (shortFeature && shortFeature !== feature) {
        matchPatterns.push(shortFeature)
      }

      const lines = content.split("\n")
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        // Check if this line contains any of our match patterns and is an unchecked checkbox
        if (line.trim().startsWith("- [ ]")) {
          for (const pattern of matchPatterns) {
            if (line.includes(pattern)) {
              lines[i] = line.replace("- [ ]", "- [x]")
              modified = true
              break
            }
          }
        }
      }
      content = lines.join("\n")
    }

    if (modified) {
      writeFileSync(workMdPath, content, "utf8")
    }
  }

  // --- hooks ---------------------------------------------------------------
  return {
    tool: { omt_phase, omt_skip, omt_complete, omt_testlist, omt_red, omt_green, omt_refactor, omt_done },

    "tool.execute.before": async (input, output) => {
      try {
        const session = input?.sessionID || undefined
        
        // feature_020: Track navigation vs search tool usage
        if (session) {
          const toolName = input?.tool
          if (!sessionNavState.has(session)) {
            sessionNavState.set(session, { usedNav: false, usedSearch: false, searchCount: 0 })
          }
          const state = sessionNavState.get(session)!
          
          // Track navigation tool usage
          if (NAV_TOOLS.has(toolName)) {
            state.usedNav = true
            safeLog("info", `Session ${session}: navigation tool ${toolName} used`)
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
              safeLog("warn", `Session ${session}: blocked ${toolName} (doc search '${targetRel || "repo"}') without prior navigation`)
              throw new OmtBlock(navRequiredMsg())
            }
            safeLog("info", `Session ${session}: ${toolName} allowed (nav-gate passed)`)
          }
        }
        
        if (!EDIT_TOOLS.has(input?.tool)) return
        // SDK contract: in tool.execute.before args live on OUTPUT (input={tool,
        // sessionID, callID} only). Reading input?.args here (a3ffb81's false
        // "F14 fix") made raw always undefined → every edit guard dead. The
        // AFTER hook is the one that reads input.args (genuine F14 fix).
        const raw = output?.args?.filePath ?? output?.args?.path ?? output?.args?.file
        if (!raw) return
        const { abs, rel } = relOf(raw)

        if (isProtected(rel)) {
          // .env / secrets are never editable (AGENTS.md #2 — no override).
          const isEnv = rel === ".env" || rel.startsWith(".env.")
          if (isEnv) throw new OmtBlock(denyMsg(rel))
          // README.md / uv.lock / LICENSE: AGENTS.md #5 allows edits "unless
          // explicitly asked". Honour an explicit omt_skip{scope:"all"} as that
          // explicit, ledger-audited unlock (aligns the gate with AGENTS.md so
          // a direct user request isn't mechanically blocked).
          const unlock = getActiveUnlock(session)
          const approved = unlock && unlock.type === "skip" && unlock.record.scope === "all"
          if (!approved) throw new OmtBlock(denyMsg(rel))
          safeLog("warn", `protected '${rel}' edit permitted under omt_skip(scope=all): ${unlock.record.reason || "(no reason)"}`)
          return
        }

        const e2e = omtHarnessE2eStatus(rel, abs)
        if (!e2e.ok) throw new OmtBlock(e2e.message)


        if (isTests(rel)) {
          // TDD gate: if TDD mode active, let tdd_check.py decide (two-hats)
          const unlock = getActiveUnlock(session)
          if (unlock?.record?.tdd_mode) {
            const tddRes = await $`uv run scripts/omt/tdd_check.py gate --path ${rel} --is-tests --session ${session || ""}`
              .cwd(directory).quiet().nothrow()
            const tddData = JSON.parse(tddRes.stdout.toString() || '{"allowed":true}')
            if (!tddData.allowed) throw new OmtBlock(tddData.reason)
            return  // TDD allows tests/ — skip canary approval
          }
          const approved = unlock && (unlock.type === "skip"
            ? unlock.record.tests_approved
            : unlock.record.tests_approved === true)
          if (!approved) throw new OmtBlock(testsMsg(rel))
          return
        }

        if (isSrc(rel)) {
          const unlock = getActiveUnlock(session)
          if (!unlock) throw new OmtBlock(noPhaseMsg(rel))
          if (unlock.type === "phase") {
            const tt = unlock.record.task_type
            if (ARTIFACT_REQUIRED.has(tt) && !artifactPresent(unlock.record)) {
              throw new OmtBlock(artifactMsg(tt, unlock.record))
            }
          }
          // TDD gate: if TDD mode active, check two-hats state
          if (unlock.record.tdd_mode) {
            const tddRes = await $`uv run scripts/omt/tdd_check.py gate --path ${rel} --session ${session || ""}`
              .cwd(directory).quiet().nothrow()
            const tddData = JSON.parse(tddRes.stdout.toString() || '{"allowed":true}')
            if (!tddData.allowed) throw new OmtBlock(tddData.reason)
          }
          // Gate passed → snapshot pre-edit hard errors so the after-hook blocks
          // only violations THIS edit introduces (pre-existing legacy errors don't block).
          if (rel.endsWith(".py")) {
            const pre = existsSync(abs)
              ? countByRule((await lintFindings(abs)).filter((f) => f.severity === "error"))
              : {}
            hardSnapshot.set(abs, pre)
            // TDD REFACTOR: save pre-edit content for revert if tests break
            if (unlock.record.tdd_mode && existsSync(abs)) {
              refactorSnapshots.set(abs, readFileSync(abs, "utf8"))
            }
          }
        }

        // --- feature_021 think-gate: block edits to thought-carrying files
        // until the session has consulted thoughts (omt_think_list). NOT
        // bypassable by omt_skip — thoughts are safety-relevant warnings. Runs
        // only for edits already permitted by the protected/e2e/tests/src checks.
        // feature_022 C2: consult is checked per-file (rel); the cross-session
        // window is dropped when the file carries a risk: thought. C1: the
        // block message renders risk: first and marks ⚠️ STALE lines.
        const thinkHits = fileThoughtsIn(abs)
        if (thinkHits.length) {
          // risk detection anchors at category position (TA:\s*risk:) — a
          // gotcha: thought mentioning "risk:" in its text does not match.
          const risk = thinkHits.some(t => /TA:\s*risk:/i.test(t.content))
          const consulted = hasConsultedThoughts(session, rel, { risk, root: directory })
          if (thinkGateDecision({ hasThoughts: true, consulted }) === "block") {
            throw new OmtBlock(thinkGateMsg(rel, thinkHits, { staleLines: staleLinesFor(directory, rel) }))
          }
        }
      } catch (e) {
        if (e instanceof OmtBlock) throw e          // intentional gate → block the edit
        safeLog("warn", "before-hook internal error (failing open): " + (e?.message || e))
      }
    },

    "tool.execute.after": async (input, output) => {
      // feature_023 Tier 1c (F14c): LIVE nav-reminder path. opencode 1.18.3
      // NEVER dispatches `session.start` (binary audit, analysis_001 addendum)
      // — the navReminderMsg() registration at the top of this hook object is
      // inert. Emit the feature_020 nav reminder once per session on the FIRST
      // tool result instead (any tool; before the read/edit branches). Fail-open.
      try {
        const remindSession = input?.sessionID || ""
        if (!navRemindedSessions.has(remindSession)) {
          navRemindedSessions.add(remindSession)
          if (typeof output?.output === "string") {
            output.output += "\n\n" + navReminderMsg()
          }
        }
      } catch (e) {
        safeLog("warn", "nav reminder failed open: " + (e?.message || e))
      }

      // feature_022 D1: non-blocking read-time thought injection — on the
      // FIRST read of a thought-carrying file per session, append the file's
      // thought-tags to the read result (point-of-use awareness, strictly
      // earlier than the edit-time think-gate block). Awareness ≠ consult:
      // NO think_consult record is written and the think-gate keeps blocking
      // edits until omt_think_list (C2 owns per-file consult — out of scope).
      // Fail-open: this branch never throws.
      // feature_023 Tier 1 (F14): args live on INPUT in tool.execute.after
      // (SDK contract), so read input?.args — output.args never existed in
      // any SDK version (the dead branch shipped in feature_022).
      if (input?.tool === "read") {
// TA: gotcha: F14 — output.args never existed in tool.execute.after (SDK contract: args on input, output={title,output,metadata}) so this branch never fired pre-feature_023; now reads input?.args?.filePath — see 6.testing/.../evaluation_001_post_shipment.md §3
        try {
          const raw = input?.args?.filePath ?? input?.args?.path ?? input?.args?.file
          if (typeof raw === "string" && raw) {
            const { abs, rel } = relOf(raw)
            const session = input?.sessionID || ""
            let seen = injectedThisSession.get(session)
            if (!seen) {
              seen = new Set<string>()
              injectedThisSession.set(session, seen)
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
        } catch (e) {
          safeLog("warn", "read-injection failed open: " + (e?.message || e))
        }
      }
      if (!EDIT_TOOLS.has(input?.tool)) return
      // feature_023 Tier 1 (F14b): same input?.args fix on the edit path —
      // output.args never existed, so the MVC++ post-edit gate was equally
      // dead since shipment. After this fix a src .py edit that introduces a
      // NEW mvc_check hard error throws OmtBlock post-write (correct-forward
      // doctrine — feature_006's documented intent, live for the first time).
      const raw = input?.args?.filePath ?? input?.args?.path ?? input?.args?.file
      if (!raw) return
      const { abs, rel } = relOf(raw)
      if (!isSrc(rel) || !rel.endsWith(".py")) return

      let findings
      try {
        findings = await lintFindings(abs)
      } catch (e) {
        safeLog("warn", "after-hook mvc_check failed: " + (e?.message || e))
        hardSnapshot.delete(abs)
        return
      }

      const before = hardSnapshot.get(abs) || {}
      hardSnapshot.delete(abs)
      const afterHard = countByRule(findings.filter((f) => f.severity === "error"))
      // NEW hard violations = error rules whose count rose vs the pre-edit snapshot.
      const introduced = findings.filter(
        (f) => f.severity === "error" && (afterHard[f.rule] || 0) > (before[f.rule] || 0))

      if (introduced.length) {
        const lines = introduced.map((f) => `  ${f.rule} (${f.file}:${f.line}) ${f.message}`).join("\n")
        // Block (decision: hard-errors block, soft warns). The file was written;
        // the agent must correct it forward before continuing.
        throw new OmtBlock(
          `⛔ OMT++ gate: your edit introduced a hard MVC++ violation in ${rel} (guide §16). ` +
          `Fix it now (correct the file forward):\n${lines}`)
      }

      const warns = findings.filter((f) => f.severity === "warning")
      if (warns.length) {
        const top = warns.slice(0, 3).map((f) => `  ${f.rule} (${f.file}:${f.line})`).join("\n")
        await notify(`MVC++ on ${rel}: ${warns.length} warning(s) (advisory).\n${top}\n` +
          `Run: uv run scripts/omt/mvc_check.py ${rel}`)
      }

      // TDD after-edit: advisory + REFACTOR revert check
      try {
        const tddSession = input?.sessionID || ""
        const tddUnlock = getActiveUnlock(tddSession)
        if (tddUnlock?.record?.tdd_mode) {
          const tddRes = await $`uv run scripts/omt/tdd_check.py after-edit --path ${rel} --session ${tddSession}`
            .cwd(directory).quiet().nothrow()
          const tddData = JSON.parse(tddRes.stdout.toString() || "{}")
          if (tddData.action === "revert_needed") {
            const content = refactorSnapshots.get(abs)
            if (content !== undefined) {
              writeFileSync(abs, content, "utf8")
              throw new OmtBlock(tddData.reason || "REFACTOR broke tests — edit reverted.")
            }
          }
          if (tddData.advisories?.length) {
            await notify(tddData.advisories.join("\n"))
          }
        }
      } catch (e) {
        if (e instanceof OmtBlock) throw e
        safeLog("warn", "TDD after-edit check failed: " + (e?.message || e))
      } finally {
        refactorSnapshots.delete(abs)
      }
    },

    event: async ({ event }) => {
      if (event?.type !== "session.idle") return
      try {
        const res = await $`uv run scripts/omt/mvc_check.py --json`.cwd(directory).quiet().nothrow()
        const data = JSON.parse(res.stdout.toString() || "{}")
        if ((data.errors || 0) > 0) {
          await notify(`MVC++ sweep: ${data.errors} architecture error(s) in src/. ` +
            "Run: uv run scripts/omt/mvc_check.py")
        }
      } catch (e) {
        safeLog("warn", "session.idle sweep failed: " + (e?.message || e))
      }
    },
  }
}
