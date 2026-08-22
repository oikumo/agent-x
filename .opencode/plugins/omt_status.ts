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
  initOmtShared, repoRoot, workMdPath, designRoot,
  readLedger as sharedReadLedger, readLedgerAll as sharedReadLedgerAll, resolveFeatureDir, globToRegex, UNLOCK_WINDOW_MS,
  irToolDescription, phaseTransitions,
} from "../lib/omt_shared"

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
    description: irToolDescription("omt_status", "Process context: phase, unlock, artifacts, lint, valid next phases, WORK.md next task."),
    args: {
      include_ledger: tool.schema.boolean().optional().describe("include last 5 phase/skip ledger entries"),
    },
    async execute(args, context) {
      const sessionId = context?.sessionID
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
