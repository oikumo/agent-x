// OMT++ Status Tool — returns complete process context for the agent
// Reads ledger + workspace state, computes actionable summary
// Uses only Node.js standard library (no external deps)
// R8 (OMT-HDL-1): the tool is built inside createStatusTool() so its
// description resolves from the compiled IR AFTER initOmtShared ran (a
// module-level tool() would read the IR under the pre-init cwd — F2/F17).

import { tool } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync, mkdirSync } from "node:fs"
import { join, relative, dirname } from "node:path"
import { execSync } from "node:child_process"
// Single source (meta_harness_dsl R1): state paths, JSONL IO, UNLOCK_WINDOW_MS
// and repo-root live in the shared lib (root injected at plugin-init, F2/F17).
// R8: tool descriptions resolve from the compiled IR (irToolDescription).
import {
  initOmtShared, repoRoot, workMdPath, designRoot, loadIr,
  readLedger as sharedReadLedger, readLedgerAll as sharedReadLedgerAll, resolveFeatureDir, globToRegex, UNLOCK_WINDOW_MS,
  irToolDescription, phaseTransitions,
} from "../lib/omt_shared"
// feature_055 A4 gate_preflight → feature_062 P0-1: the projection core lives
// in lib/enforcer/preflight.ts (shared home for this op and the omt_phase
// declare-embed) — same dry-run sibling, no second gate engine to drift.
import {
  PREFLIGHT_DEFAULT_TOOL, preflightProjection, preflightLines,
} from "../lib/enforcer/preflight"

const VALID_PHASES = ["Analysis", "Design", "Programming", "Testing"]
const VALID_TASK_TYPES = ["bug_fix", "minor_feature", "major_feature", "new_screen", "refactor", "test", "docs"]
const ARTIFACT_REQUIRED = new Set(["major_feature", "new_screen"])

// Valid phase transitions per guide §12: resolved through the shared lib's
// phaseTransitions() — .omt @fsm phase transitions= is the FUNCTIONAL source
// (improvement007/OPT-E; the hand mirror here is deleted).

interface LedgerRecord {
  ts: string
  kind: "phase" | "skip"
  session?: string
  task_type?: string
  phase?: string
  scope?: string
  feature?: string
  design_doc?: string
  reason?: string
  tests_approved?: boolean
  purpose?: string
  abandons?: string
}

function readLedger(): LedgerRecord[] {
  return sharedReadLedger() as LedgerRecord[]
}

function getActiveUnlock(sessionId?: string): LedgerRecord | null {
  const recs = readLedger().filter(r => r.kind === "phase" || r.kind === "skip")
  if (!recs.length) return null

  if (sessionId) {
    const mine = recs.filter(r => r.session === sessionId)
    if (mine.length) return mine[mine.length - 1]
  }

  const now = Date.now()
  const recent = recs.filter(r => {
    const t = Date.parse(r.ts || "")
    return !Number.isNaN(t) && now - t < UNLOCK_WINDOW_MS
  })
  return recent.length ? recent[recent.length - 1] : null
}

function resolveDesignArtifact(feature: string, explicitDoc?: string): string | null {
  if (explicitDoc && existsSync(join(repoRoot(), explicitDoc))) return explicitDoc
  if (!feature) return null

  const m = feature.match(/feature_(\d+)/)
  if (!m) return null
  const num = m[1]
  const base = designRoot()
  if (!existsSync(base)) return null

  for (const d of readdirSync(base)) {
    if (d === `feature_${num}` || d.startsWith(`feature_${num}.`) || d.startsWith(`feature_${num}_`)) {
      const files = readdirSync(join(base, d))
      const hit = files.find(f => /^design_\d+_.+\.md$/i.test(f))
      if (hit) return join(".meta", "software_development_process", "4.design", "features", d, hit)
    }
  }
  return null
}

// resolveFeatureDir: single source is the shared lib (R1) — imported above.

function getArtifactStatus(feature: string, taskType: string): {
  required: string[]
  missing: string[]
  present: string[]
} {
  const required: string[] = []
  const missing: string[] = []
  const present: string[] = []

  if (!feature) return { required, missing, present }
  if (!ARTIFACT_REQUIRED.has(taskType)) return { required, missing, present }

  // Normalize feature slug: extract number part (feature_004.modern_ui -> feature_004)
  const featureNum = feature.match(/feature_(\d+)/)?.[0] || feature
  const PROCESS_ROOT = ".meta/software_development_process"

  // [phase, pattern, features-parent-dir] — the parent is resolved to the actual
  // feature subdir via resolveFeatureDir so full-slug features are found.
  const checks: [string, string, string][] = [
    ["Requirements", "FEATURE.md", join(repoRoot(), PROCESS_ROOT, "2.requirements", "features")],
    ["Analysis", "analysis_001_*.md", join(repoRoot(), PROCESS_ROOT, "3.analysis", "features")],
    ["Design", "design_*.md", join(repoRoot(), PROCESS_ROOT, "4.design", "features")],
    ["Implementation", "*.md", join(repoRoot(), PROCESS_ROOT, "5.implementation", "features")],
    ["Testing", "test_report.md", join(repoRoot(), PROCESS_ROOT, "6.testing", "features")],
  ]

  for (const [phase, pattern, featuresParent] of checks) {
    let exists = false
    try {
      const dir = resolveFeatureDir(featuresParent, feature, featureNum)
      if (dir) {
        const files = readdirSync(dir, { recursive: true })
        // R1: converged from the inline unanchored regex to the shared
        // globToRegex (anchored + escaped) — same answers on flat feature dirs.
        exists = files.some(f => globToRegex(pattern).test(f))
      }
    } catch { /* ignore */ }

    if (exists) {
      present.push(`${phase}: ${pattern}`)
    } else if (phase === "Requirements" || ARTIFACT_REQUIRED.has(taskType) || phase === "Design") {
      required.push(`${phase}: ${pattern}`)
      missing.push(`${phase}: ${pattern}`)
    }
  }
  return { required, missing, present }
}

function runLintBaseline(): { errors: number; warnings: number; timestamp: string } {
  try {
    const out = execSync("uv run scripts/omt/mvc_check.py --json", {
      cwd: repoRoot(),
      encoding: "utf8",
      timeout: 30000,
      stdio: ["ignore", "pipe", "ignore"]
    })
    const data = JSON.parse(out || "{}")
    return { errors: data.errors || 0, warnings: data.warnings || 0, timestamp: new Date().toISOString() }
  } catch {
    return { errors: -1, warnings: -1, timestamp: new Date().toISOString() }
  }
}

function runTddStatus(sessionId?: string): { tdd_mode: boolean; state: string; test_node: string | null; cycles_count: number; testlist: any } | null {
  try {
    const out = execSync(`uv run scripts/omt/tdd_check.py status --session "${sessionId || ""}"`, {
      cwd: repoRoot(),
      encoding: "utf8",
      timeout: 10000,
      stdio: ["ignore", "pipe", "ignore"]
    })
    return JSON.parse(out || "{}")
  } catch {
    return null
  }
}

function getWorkMdNextTask(): string | null {
  if (!existsSync(workMdPath())) return null
  const content = readFileSync(workMdPath(), "utf8")
  const lines = content.split("\n")
  for (const line of lines) {
    if (line.trim().startsWith("- [ ]") || line.trim().startsWith("- [~]")) {
      return line.trim().replace(/^-\s*\[[ ~]\]\s*/, "")
    }
  }
  return null
}

function computeFeatureHealth(feature: string, taskType: string): {
  requirements: number
  analysis: number
  design: number
  implementation: number
  testing: number
  overall: number
} {
  const { present, required } = getArtifactStatus(feature, taskType)
  const phases = ["Requirements", "Analysis", "Design", "Implementation", "Testing"]
  const scores = phases.map(p => present.some(x => x.startsWith(p)) ? 1 : required.some(x => x.startsWith(p)) ? 0 : 0.5)
  const overall = scores.reduce((a, b) => a + b, 0) / scores.length
  return {
    requirements: scores[0],
    analysis: scores[1],
    design: scores[2],
    implementation: scores[3],
    testing: scores[4],
    overall: Math.round(overall * 100) / 100
  }
}

function formatDuration(ms: number): string {
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  if (ms < 3600000) return `${Math.round(ms / 60000)}m`
  return `${Math.round(ms / 3600000)}h`
}

// ---------------------------------------------------------------------------
// feature_055 A4 gate_preflight / feature_062 P0-1: the projection core
// (CLEARING_ACTIONS, buildPreflightCtx, preflightProjection, preflightLines)
// moved to lib/enforcer/preflight.ts — the shared home for this op and the
// omt_phase declare-embed. This plugin is a thin consumer (op=preflight
// branch below).
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// feature_056 A2+A3 skip taxonomy + phase hygiene. READ-ONLY (the A4
// ledger-write-free pin holds — this section never writes the ledger):
//   • 7-day skip-signal split — friction (the process toll, paid by design)
//     vs nav-escapes (cheap efficiency bypass, tracked, never alarming) vs
//     evasion (uncategorized bypass of discipline gates). Unmarked history
//     classifies via the scope-aware default (scope=tests → canary).
//   • dangling-phase list — declared-never-completed EXPIRED phases with the
//     exact one-call resume (omt_phase re-declare) / abandon (omt_phase
//     phase="abandoned" tombstone) commands.
// ---------------------------------------------------------------------------
const SKIP_PURPOSES = ["canary", "emergency", "break_glass", "override"]
const FRICTION_PURPOSES = new Set(["canary", "emergency", "break_glass"])
const SKIP_HYGIENE_WEEK_MS = 7 * 24 * 60 * 60 * 1000
const SKIP_OVERRIDE_WARN_DEFAULT = 5
const DANGLING_LIST_CAP = 10

function skipEffectivePurpose(r: any): string {
  const p = typeof r?.purpose === "string" ? r.purpose : ""
  if ((SKIP_PURPOSES as string[]).includes(p)) return p
  return r?.scope === "tests" ? "canary" : "override"
}

function skipHygiene(): { lines: string[]; summary: Record<string, any> } {
  const now = Date.now()
  const recs = sharedReadLedgerAll()
  const week = recs.filter((r: any) => r?.kind === "skip" &&
    !Number.isNaN(Date.parse(r.ts || "")) && now - Date.parse(r.ts || "") < SKIP_HYGIENE_WEEK_MS)
  let friction = 0, navEscapes = 0, evasion = 0
  for (const r of week) {
    const purpose = skipEffectivePurpose(r)
    if (FRICTION_PURPOSES.has(purpose)) friction += 1
    else if (r?.scope === "nav") navEscapes += 1
    else evasion += 1
  }
  const rawT = (loadIr() as any)?.vars?.skip_override_warn_per_week
  const parsedT = Number.isInteger(rawT) ? rawT : parseInt(String(rawT ?? ""), 10)
  const warnAt = Number.isFinite(parsedT) && parsedT > 0 ? parsedT : SKIP_OVERRIDE_WARN_DEFAULT
  // Dangling: phase records (feature set, not tombstones) with no later
  // complete{feature,phase} and no later abandon tombstone for that phase.
  const dangling: { feature: string; phase: string; task_type: string; scope: string; age: number }[] = []
  recs.forEach((r: any, i: number) => {
    if (r?.kind !== "phase" || !r?.feature || !r?.phase || r.phase === "abandoned") return
    const later = recs.slice(i + 1)
    const resolved = later.some((x: any) =>
      (x?.kind === "complete" && x?.feature === r.feature && x?.phase === r.phase) ||
      (x?.kind === "phase" && x?.phase === "abandoned" && x?.feature === r.feature && x?.abandons === r.phase))
    if (resolved) return
    const t = Date.parse(r.ts || "")
    dangling.push({
      feature: String(r.feature), phase: String(r.phase),
      task_type: String(r.task_type || ""), scope: String(r.scope || ""),
      age: Number.isNaN(t) ? 0 : now - t,
    })
  })
  const expired = dangling.filter((d) => d.age > UNLOCK_WINDOW_MS)
  const active = dangling.filter((d) => d.age <= UNLOCK_WINDOW_MS)
  const q = (s: string): string => s.replace(/"/g, "'")
  const lines = [
    `Skips 7d: ${week.length} (friction ${friction} · nav-escapes ${navEscapes} · evasion ${evasion}, warn>${warnAt}/week)`,
    `Dangling phases: ${dangling.length} (${expired.length} expired)`,
  ]
  // feature_060 P0-2 dangling-active-only: list <=10 unexpired oldest-first
  // (closest to expiry); expired auto-hide behind a GC count line. The 8h
  // UNLOCK_WINDOW is the one-session grace — hidden expired records stay
  // resumable via explicit re-declare / abandon tombstone (one-call idiom).
  const shown = [...active].sort((a, b) => b.age - a.age).slice(0, DANGLING_LIST_CAP)
  for (const d of shown) {
    lines.push(`  • ${d.feature} ${d.phase} — ${formatDuration(d.age)} — resume: omt_phase{task_type:"${q(d.task_type)}", phase:"${d.phase}", scope:"${q(d.scope)}", feature:"${d.feature}"} · abandon: omt_phase{task_type:"${q(d.task_type)}", phase:"abandoned", scope:"abandon ${d.phase}: <reason>", feature:"${d.feature}"}`)
  }
  if (active.length > shown.length) lines.push(`  … and ${active.length - shown.length} more active (oldest shown)`)
  if (expired.length) lines.push(`  … and ${expired.length} expired auto-hidden (GC: abandon to tombstone, or re-declare to resume)`)
  return {
    lines,
    summary: {
      week_total: week.length, friction, nav_escapes: navEscapes, evasion,
      warn_at: warnAt, dangling_total: dangling.length, dangling_expired: expired.length,
      dangling_active: active.length,
    },
  }
}

// ---------------------------------------------------------------------------
// feature_057 B1+B2 gate budget + ceremony meter. READ-ONLY (the A4
// ledger-write-free pin holds — this section never writes the ledger):
//   • gate budget — IR gate count vs @budget gates max (net-zero: retire to
//     add); retirement candidates from 7-day skip-frequency (the scope→gate
//     map mirrors harnessc.py SKIP_SCOPE_TO_GATES — keep the two in sync).
//   • ceremony meter — median pre-unlock ledger records (q/think_consult/
//     skip/tdd/tdd_testlist before the session's first phase) per task_type;
//     alarm when the bug_fix median > 3.
// ---------------------------------------------------------------------------
const SKIP_SCOPE_TO_GATES: Record<string, string[]> = {
  tests: ["g.tests"],
  nav: ["g.nav"],
  src: ["g.phase"],
  all: ["g.net"],
}
const CEREMONY_KINDS = new Set(["q", "think_consult", "skip", "tdd", "tdd_testlist"])
const CEREMONY_BUG_FIX_ALARM = 3

export function gateBudget(): { lines: string[]; summary: Record<string, any> } {
  const ir = loadIr() as any
  const gates: any[] = Array.isArray(ir?.gates) ? ir.gates : []
  const ids = gates.map((g: any) => String(g.id))
  const skipOk: Record<string, boolean> = {}
  for (const g of gates) skipOk[String(g.id)] = g.skip_ok === true
  const rawMax = (ir as any)?.budgets?.gates
  const parsed = Number.isInteger(rawMax) ? rawMax : parseInt(String(rawMax ?? ""), 10)
  const max = Number.isFinite(parsed) && parsed > 0 ? parsed : 12
  const now = Date.now()
  const counts: Record<string, number> = {}
  for (const r of sharedReadLedgerAll() as any[]) {
    if (r?.kind !== "skip") continue
    const t = Date.parse(r.ts || "")
    if (Number.isNaN(t) || now - t >= SKIP_HYGIENE_WEEK_MS) continue
    for (const g of SKIP_SCOPE_TO_GATES[String(r.scope ?? "")] ?? []) {
      counts[g] = (counts[g] ?? 0) + 1
    }
  }
  const ranked = Object.entries(counts).sort((a, b) => b[1] - a[1])
  const toll = ranked.length ? `${ranked[0][0]}x${ranked[0][1]}` : "no skips to rank"
  const dead = ids.filter((id) => skipOk[id] && !counts[id])
  return {
    lines: [`Gates ${ids.length}/${max} (net-zero: retire to add; top-skipped ${toll}${dead.length ? `; watch ${dead.join(",")}` : ""})`],
    summary: {
      count: ids.length, max, top_skipped: ranked[0] ?? null, dead_weight_watch: dead,
    },
  }
}

export function ceremonyMeter(): { lines: string[]; summary: Record<string, any> } {
  const bySession = new Map<string, any[]>()
  for (const r of sharedReadLedgerAll() as any[]) {
    if (!r?.session || !r?.ts) continue
    if (!bySession.has(r.session)) bySession.set(r.session, [])
    bySession.get(r.session)!.push(r)
  }
  const perTt = new Map<string, number[]>()
  for (const rs of bySession.values()) {
    rs.sort((a, b) => String(a.ts).localeCompare(String(b.ts)))
    const fi = rs.findIndex((r) => r?.kind === "phase")
    if (fi < 0) continue
    const tt = String(rs[fi].task_type || "unknown")
    const pre = rs.slice(0, fi).filter((r) => CEREMONY_KINDS.has(String(r?.kind))).length
    if (!perTt.has(tt)) perTt.set(tt, [])
    perTt.get(tt)!.push(pre)
  }
  const medians: Record<string, { sessions: number; median: number }> = {}
  for (const [tt, vals] of perTt) {
    vals.sort((a, b) => a - b)
    const n = vals.length
    medians[tt] = { sessions: n, median: n % 2 ? vals[n >> 1] : (vals[n / 2 - 1] + vals[n / 2]) / 2 }
  }
  const bug = medians["bug_fix"]
  const parts = Object.entries(medians).map(([tt, m]) => `${tt} ${m.median}`).join(" · ") || "no attributable sessions"
  const alarm = !!bug && bug.median > CEREMONY_BUG_FIX_ALARM
  return {
    lines: [`Ceremony median (pre-unlock records): ${parts} (alarm bug_fix>${CEREMONY_BUG_FIX_ALARM})${alarm ? " ⚠ over alarm" : ""}`],
    summary: { medians, alarm },
  }
}

// R8: build the tool AFTER initOmtShared so irToolDescription reads the IR
// under the injected repo root (never the pre-init cwd).

// feature_030: active project = project linked to the active feature (derived
// per call, never stored — D1). Full fold: project links span months.
function deriveActiveProject(feature: string): { project: string; state: string; last_log: string } | null {
  if (!feature) return null
  const records = sharedReadLedgerAll()
  let link: any = null
  for (const r of records) if (r.kind === "project_link" && r.feature === feature) link = r
  if (!link) return null
  let state = "unknown"
  for (const r of records) {
    if (r.kind === "project" && r.project === link.project) {
      if (r.op === "close") state = "complete"
      else if (r.op === "archive") state = "archived"
      else if (r.op === "create" || r.op === "reopen") state = "active"  // a link exists by construction
    }
  }
  let last_log = ""
  try {
    const m = readFileSync(
      join(repoRoot(), ".projects", "meta", link.project, "CURRENT_STATE.md"), "utf8",
    ).match(/^## (\d{4}-\d{2}-\d{2})/m)
    last_log = m ? m[1] : ""
  } catch { /* home missing */ }
  return { project: link.project, state, last_log }
}

function createStatusTool() {
  return tool({
    description: irToolDescription("omt_status", "Process context: phase, unlock, artifacts, lint, valid next phases, WORK.md next task; op=preflight(tool,path) → ordered gates that will fire + clearing action each (default: full status)."),
    args: {
      op: tool.schema.string().optional().describe("status (default) | preflight"),
      tool: tool.schema.string().optional().describe("target tool (default edit)"),
      path: tool.schema.string().optional().describe("target path"),
      include_ledger: tool.schema.boolean().optional().describe("include last 5 ledger entries"),
    },
    async execute(args, context) {
      const sessionId = context?.sessionID

      // feature_055 A4: preflight short-circuits BEFORE the lint/tdd
      // subprocesses of the default status path — fast, read-only, no ledger
      // writes (omt_status stays ledger-clean).
      if (args?.op === "preflight") {
        const path = String(args.path ?? "")
        if (!path) {
          return {
            title: "OMT++ Preflight",
            output: "⛔ omt_status preflight: path required — omt_status{op:\"preflight\", tool?, path}",
            metadata: { op: "preflight", error: "path required" },
          }
        }
        const toolName = String(args.tool ?? PREFLIGHT_DEFAULT_TOOL)
        const proj = await preflightProjection(path, toolName, sessionId)
        return {
          title: "OMT++ Preflight",
          output: preflightLines(proj).join("\n"),
          metadata: proj,
        }
      }
      if (args?.op && args?.op !== "status") {
        return {
          title: "OMT++ Status",
          output: `⛔ omt_status: unknown op '${args.op}' — want status (default) | preflight`,
          metadata: { op: args.op, error: "unknown op" },
        }
      }

      const unlock = getActiveUnlock(sessionId)
      const ledger = readLedger()
      const statusRecords = ledger.filter(r => r.kind === "phase" || r.kind === "skip")
      const recent = statusRecords.slice(-5)
      const includeLedger = args.include_ledger === true

      let currentPhase = "None"
      let activeUnlock = null
      let expiresIn = "N/A"

      if (unlock) {
        currentPhase = unlock.phase || "Unknown"
        const started = Date.parse(unlock.ts || "")
        const elapsed = Date.now() - started
        const remaining = Math.max(0, UNLOCK_WINDOW_MS - elapsed)
        expiresIn = remaining > 0 ? formatDuration(remaining) : "expired"

        activeUnlock = {
          task_type: unlock.task_type || "unknown",
          phase: unlock.phase || "",
          scope: unlock.scope || "",
          feature: unlock.feature || "",
          design_doc: unlock.design_doc || "",
          session: unlock.session || "",
          started_at: unlock.ts || "",
          expires_in: expiresIn
        }
      }

      const feature = unlock?.feature || ""
      const taskType = unlock?.task_type || ""
      const { required, missing, present } = getArtifactStatus(feature, taskType)

      const lint = runLintBaseline()

      // improvement006/OPT-E bug 2: Done has no outgoing transitions — a
      // completed cycle restarts at Analysis, so offer the full phase set.
      const nextPhases = currentPhase !== "None" && currentPhase !== "Unknown"
        ? phaseTransitions()[currentPhase] ?? ["Analysis", "Design", "Programming", "Testing"]
        : ["Analysis", "Design", "Programming", "Testing"]

      const featureHealth: Record<string, any> = {}
      // improvement006/OPT-E bug 1: only meaningful when the feature has
      // artifact dirs — otherwise every score collapsed to 0%/50% noise.
      if (feature && (present.length || required.length)) {
        featureHealth[feature] = computeFeatureHealth(feature, taskType)
      }

      const nextTask = getWorkMdNextTask()
      const projectInfo = deriveActiveProject(feature)

      const lastLedger = recent.length ? recent[recent.length - 1] : null
      const result: Record<string, any> = {
        current_phase: currentPhase,
        active_unlock: activeUnlock,
        artifacts_required: required,
        artifacts_missing: missing,
        artifacts_present: present,
        lint_baseline: lint,
        next_valid_phases: nextPhases,
        work_md_next_task: nextTask,
        project: projectInfo,
        feature_health: featureHealth,
        recent_ledger_summary: {
          total_phase_or_skip_records: statusRecords.length,
          last_entry: lastLedger
            ? {
                ts: lastLedger.ts,
                kind: lastLedger.kind,
                task_type: lastLedger.task_type || "",
                phase: lastLedger.phase || "",
                feature: lastLedger.feature || "",
              }
            : null,
        },
      }
      if (includeLedger) result.recent_ledger = recent

      // improvement006/OPT-E: compact default (frequent on-demand surface);
      // "OMT++ STATUS" banner literal preserved (live-smoke pin).
      const lines = [
        `📊 OMT++ STATUS — ${currentPhase} · ${activeUnlock ? `${activeUnlock.task_type !== "unknown" ? activeUnlock.task_type : `skip/${activeUnlock.scope || "all"}`} (${activeUnlock.phase || "—"}) expires ${activeUnlock.expires_in}` : "no unlock (src/ blocked)"} · lint ${lint.errors >= 0 ? `${lint.errors} err, ${lint.warnings} warn` : "unavailable"}`,
        ...(activeUnlock?.scope ? [`Scope: ${activeUnlock.scope}`] : []),
        `Artifacts: ${required.length ? `${required.length} required` : "none"}${missing.length ? ` — missing: ${missing.join(", ")}` : ""}${present.length ? ` · present: ${present.join(", ")}` : ""}`,
        `Valid next: ${nextPhases.join(", ")} · Next task: ${nextTask || "none pending"}`,
        ...(projectInfo ? [`Project: ${projectInfo.project} (${projectInfo.state}) · last log ${projectInfo.last_log || "—"}`] : []),
      ]

      if (Object.keys(featureHealth).length) {
        lines.push(
          ...Object.entries(featureHealth).map(([f, h]) =>
            `Feature Health ${f}: ${Math.round(h.overall * 100)}% (R:${h.requirements} A:${h.analysis} D:${h.design} I:${h.implementation} T:${h.testing})`
          )
        )
      }

      const tddStatus = runTddStatus(sessionId)
      result.tdd_status = tddStatus
      if (tddStatus && tddStatus.tdd_mode) {
        lines.push(
          `TDD Mode: ACTIVE (${tddStatus.state.toUpperCase()})${tddStatus.test_node ? ` — ${tddStatus.test_node}` : ""} — cycles: ${tddStatus.cycles_count}`,
        )
      }

      if (includeLedger) {
        lines.push(
          "Recent Ledger:",
          ...recent.map(r =>
            `  [${r.ts?.slice(11, 19)}] ${r.kind} ${r.task_type || ""} ${r.phase || ""} ${r.feature || ""} ${r.reason ? `— ${r.reason}` : ""}`
          )
        )
      } else if (statusRecords.length) {
        lines.push(`Ledger: hidden (${statusRecords.length} records; omt_status{include_ledger:true} for audit detail)`)
      }

      // feature_056 A2+A3: skip-signal split + dangling-phase hygiene.
      const hygiene = skipHygiene()
      lines.push(...hygiene.lines)
      result.skip_hygiene = hygiene.summary

      // feature_057 B1+B2: gate budget + ceremony meter.
      const budget = gateBudget()
      lines.push(...budget.lines)
      result.gate_budget = budget.summary
      const ceremony = ceremonyMeter()
      lines.push(...ceremony.lines)
      result.ceremony = ceremony.summary

      return {
        title: "OMT++ Status",
        output: lines.join("\n"),
        metadata: result,
      }
    }
  })
}

// Standalone opencode plugin. This file lives under .opencode/plugins/, so it
// must export a plugin function, not only a helper tool object. The enforcer
// plugin registers the gate tools; this plugin registers status independently.
// R1 (F2/F17): repo root = worktree ?? directory, injected into the shared lib
// before any hook runs (all lib path getters are lazy — see lib header).
export default async ({ directory, worktree }) => {
  initOmtShared(worktree ?? directory)
  const omt_status = createStatusTool()
  return {
    tool: { omt_status },
  }
}
