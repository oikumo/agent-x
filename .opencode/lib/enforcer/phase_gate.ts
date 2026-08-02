// OMT++ phase gate (feature_006; meta_harness_dsl R2 module).
//
// The src/ edit gate (a declared phase is required; major_feature/new_screen
// additionally require a design artifact on disk per guide §12), the phase
// lifecycle tools (omt_phase / omt_skip / omt_complete), and the §12
// phase-exit artifact matrix they enforce.
// R8 (OMT-HDL-1): tool descriptions resolve from the compiled IR
// (irToolDescription) with the in-source text as fallback seed.

import { tool } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs"
import { join } from "node:path"
import { resolveFeatureDir, globToRegex, irToolDescription, phaseTransitions, tddAutoOn, gateMsg } from "../omt_shared"
import {
  OmtBlock, writeLedger, readLedger, getActiveUnlock, getActiveFeaturePhase, type EnforcerEnv,
} from "./session_state"
import { tddGateCheck } from "./tdd_hats"
import { capturePreEditSnapshot } from "./mvc_after"

const VALID_TASK_TYPES = new Set([
  "bug_fix", "minor_feature", "major_feature", "new_screen", "refactor", "test", "docs",
])
// Task types that may not touch src/ until a design artifact exists on disk (guide §12).
const ARTIFACT_REQUIRED = new Set(["major_feature", "new_screen"])

// Valid phase transitions per guide §12: .omt @fsm phase transitions= is the
// FUNCTIONAL source (improvement007/OPT-E), resolved per call through the
// shared lib's phaseTransitions() (the pinned IR-missing fallback lives there).

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

// Auto-detect a feature's design artifact from its slug (hardening — guide §12),
// so the gate doesn't depend on the agent passing design_doc by hand.
function detectDesignArtifact(env: EnforcerEnv, feature: string): string | null {
  if (!feature) return null
  const m = String(feature).match(/feature_(\d+)/)
  if (!m) return null
  const num = m[1]
  const rel = join(".meta", "software_development_process", "4.design", "features")
  const base = join(env.directory, rel)
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
      env.safeLog("warn", `Feature ${feature} has .md files but no design_NNN_*.md artifact in ${d}/`)
    }
    if (hit) return join(rel, d, hit)
  }
  return null
}

// Resolve the design artifact for a phase record: explicit design_doc first,
// else auto-detected from the feature slug. Returns repo-relative path or null.
function resolveArtifact(env: EnforcerEnv, record: any): string | null {
  if (record.design_doc && existsSync(join(env.directory, record.design_doc))) return record.design_doc
  const auto = detectDesignArtifact(env, record.feature)
  return auto && existsSync(join(env.directory, auto)) ? auto : null
}
const artifactPresent = (env: EnforcerEnv, record: any): boolean => !!resolveArtifact(env, record)

// --- teaching messages ---------------------------------------------------
// improvement007 R8/OPT-G: block texts resolve from the IR @msg records via
// gateMsg ({rel}/{tt}/{feature} interpolated per call) — .omt-only edits.

// --- before-hook src/ gate -------------------------------------------------
// Phase declaration required; ARTIFACT_REQUIRED task types additionally need a
// design artifact; tdd_mode defers to the two-hats gate; a passing .py edit
// gets its pre-edit MVC++/REFACTOR snapshots captured (mvc_after).
export async function guardSrcPath(
  env: EnforcerEnv,
  session: string | undefined,
  rel: string,
  abs: string,
): Promise<void> {
  const unlock = getActiveUnlock(session)
  if (!unlock) throw new OmtBlock(`⛔ OMT++ gate: ${gateMsg("no_phase", { rel })}`)
  if (unlock.type === "phase") {
    const tt = unlock.record.task_type
    if (ARTIFACT_REQUIRED.has(tt) && !artifactPresent(env, unlock.record)) {
      throw new OmtBlock(`⛔ OMT++ gate: ${gateMsg("artifact", { tt, feature: unlock.record.feature || "<none declared>" })}`)
    }
  }
  // TDD gate: if TDD mode active, check two-hats state
  if (unlock.record.tdd_mode) {
    await tddGateCheck(env, session, rel, false)
  }
  await capturePreEditSnapshot(env, abs, rel, unlock.record.tdd_mode === true)
}

// --- phase lifecycle tools ---------------------------------------------------
export function createPhaseTools(env: EnforcerEnv) {
  const { directory, $, safeLog } = env

  const omt_phase = tool({
    description: irToolDescription("omt_phase", "Declare phase before src/ edits (task_type/scope → ledger; §12 unlock matrix)."),
    args: {
      task_type: tool.schema.string().describe("bug_fix|minor_feature|major_feature|new_screen|refactor|test|docs"),
      scope: tool.schema.string().describe("one sentence describing what 'done' looks like"),
      phase: tool.schema.string().optional().describe("Analysis|Design|Programming|Testing"),
      feature: tool.schema.string().optional().describe("feature slug, e.g. feature_006.x"),
      design_doc: tool.schema.string().optional().describe("design artifact path (required for major_feature/new_screen)"),
      tdd: tool.schema.boolean().optional().describe("TDD for Programming (auto-on major_feature/new_screen)"),
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

      const tddMode = args.tdd === true || tddAutoOn(tt, args.phase || "")
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
        const found = resolveArtifact(env, { design_doc: args.design_doc, feature: args.feature })
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
    description: irToolDescription("omt_skip", "Logged escape hatch: unlock without phase. Scopes: src|tests|nav|all (default all)."),
    args: {
      reason: tool.schema.string().describe("why the process is being skipped"),
      scope: tool.schema.string().optional().describe("src|tests|nav|all (default all)"),
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
    description: irToolDescription("omt_complete", "Verify phase artifacts; optionally advance (Design|Programming|Testing|Done)."),
    args: {
      feature: tool.schema.string().describe("feature slug, e.g. feature_006.x"),
      advance_to: tool.schema.string().optional().describe("phase after verification (Design|Programming|Testing|Done)"),
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
      } catch (e: any) {
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
        const validNext = phaseTransitions()[currentPhase] || []
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

  return { omt_phase, omt_skip, omt_complete }
}
