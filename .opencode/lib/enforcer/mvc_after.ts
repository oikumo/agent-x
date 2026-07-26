// OMT++ MVC++ after-hook machinery (feature_006; meta_harness_dsl R2 module).
//
//   • capturePreEditSnapshot — before-hook (src/ branch, .py only): record
//     the pre-edit hard-error counts (and, under tdd_mode, the full content
//     for a REFACTOR revert) so the after-hook blocks only violations THIS
//     edit introduces (pre-existing legacy errors don't block).
//   • mvcAfterEdit         — after-hook: lint the touched src/*.py, block on
//     NEWLY introduced hard errors (correct-forward doctrine), warn advisory.
//   • sessionIdleSweep     — event hook: repo-wide MVC++ sweep on session.idle.

import { existsSync, readFileSync } from "node:fs"
import { OmtBlock, type EnforcerEnv } from "./session_state"

// --- MVC++ lint delta (block only NEWLY introduced hard errors) ----------
async function lintFindings(env: EnforcerEnv, abs: string): Promise<any[]> {
  try {
    const res = await env.$`uv run scripts/omt/mvc_check.py ${abs} --json`.cwd(env.directory).quiet().nothrow()
    return JSON.parse(res.stdout.toString() || "{}").findings || []
  } catch { return [] }
}

function countByRule(findings: any[]): Record<string, number> {
  const m: Record<string, number> = {}
  for (const f of findings) m[f.rule] = (m[f.rule] || 0) + 1
  return m
}

// Before-hook (src/ branch): snapshot pre-edit hard errors so the after-hook
// blocks only violations THIS edit introduces. Under tdd_mode also capture the
// pre-edit content for the REFACTOR revert (tdd_hats.tddAfterEdit consumes it).
export async function capturePreEditSnapshot(
  env: EnforcerEnv,
  abs: string,
  rel: string,
  tddMode: boolean,
): Promise<void> {
  if (!rel.endsWith(".py")) return
  const pre = existsSync(abs)
    ? countByRule((await lintFindings(env, abs)).filter((f) => f.severity === "error"))
    : {}
  env.state.hardSnapshot.set(abs, pre)
  // TDD REFACTOR: save pre-edit content for revert if tests break
  if (tddMode && existsSync(abs)) {
    env.state.refactorSnapshots.set(abs, readFileSync(abs, "utf8"))
  }
}

// After-hook post-edit gate (feature_023 Tier 1 / F14b): the caller (root)
// reads input?.args — output.args never existed, so this gate was equally
// dead since shipment pre-feature_023. A src .py edit that introduces a NEW
// mvc_check hard error throws OmtBlock post-write (correct-forward doctrine —
// feature_006's documented intent, live for the first time since the fix).
// Returns false when the lint itself failed (caller skips the TDD after-edit,
// mirroring the monolith's early return); true otherwise.
export async function mvcAfterEdit(env: EnforcerEnv, abs: string, rel: string): Promise<boolean> {
  let findings
  try {
    findings = await lintFindings(env, abs)
  } catch (e: any) {
    env.safeLog("warn", "after-hook mvc_check failed: " + (e?.message || e))
    env.state.hardSnapshot.delete(abs)
    return false
  }

  const before = env.state.hardSnapshot.get(abs) || {}
  env.state.hardSnapshot.delete(abs)
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
    await env.notify(`MVC++ on ${rel}: ${warns.length} warning(s) (advisory).\n${top}\n` +
      `Run: uv run scripts/omt/mvc_check.py ${rel}`)
  }
  return true
}

// event hook: repo-wide MVC++ sweep when the session goes idle (advisory).
export async function sessionIdleSweep(env: EnforcerEnv, event: any): Promise<void> {
  if (event?.type !== "session.idle") return
  try {
    const res = await env.$`uv run scripts/omt/mvc_check.py --json`.cwd(env.directory).quiet().nothrow()
    const data = JSON.parse(res.stdout.toString() || "{}")
    if ((data.errors || 0) > 0) {
      await env.notify(`MVC++ sweep: ${data.errors} architecture error(s) in src/. ` +
        "Run: uv run scripts/omt/mvc_check.py")
    }
  } catch (e: any) {
    env.safeLog("warn", "session.idle sweep failed: " + (e?.message || e))
  }
}
