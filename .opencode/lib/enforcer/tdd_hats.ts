// OMT++ TDD two-hats enforcement (feature_016; meta_harness_dsl R2 module).
//
// Thin wrappers around scripts/omt/tdd_check.py (the state machine lives in
// Python): the five omt_* TDD tools, the before-hook two-hats gate (tests/
// and src/ branches), and the after-hook after-edit check (advisories +
// REFACTOR revert when a refactor edit breaks tests).

import { tool } from "@opencode-ai/plugin"
import { writeFileSync } from "node:fs"
import { OmtBlock, getActiveUnlock, type EnforcerEnv } from "./session_state"

// --- TDD tools (thin wrappers delegating to tdd_check.py) -------------------
const tddTool = (env: EnforcerEnv, subcmd: string, desc: string, argNames: string[]) => tool({
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
      const res = await env.$`uv run scripts/omt/tdd_check.py ${flags}`
        .cwd(env.directory).quiet().nothrow()
      const data = JSON.parse(res.stdout.toString() || "{}")
      return data.message || JSON.stringify(data)
    } catch (e: any) {
      env.safeLog("warn", `tdd_check.py ${subcmd} failed: ${e?.message || e}`)
      return `⚠️ TDD engine error: ${e?.message || e}`
    }
  },
})

export function createTddTools(env: EnforcerEnv) {
  const omt_testlist = tddTool(env, "testlist",
    "Record the TDD test list (behaviors to implement). Sets TDD state to TESTLIST.",
    ["behaviors", "feature"])
  const omt_red = tddTool(env, "start",
    "Declare a failing test (TDD Red). Runs pytest to verify the test fails, then AST analysis for true-RED verification. Sets TDD state to RED (test hat: only tests/ edits allowed).",
    ["test_node", "target_src", "feature"])
  const omt_green = tddTool(env, "green",
    "Declare a passing test (TDD Green). Runs pytest to verify the test passes. Sets TDD state to GREEN (code hat: only src/ edits allowed).",
    ["test_node", "feature"])
  const omt_refactor = tddTool(env, "refactor",
    "Declare refactor state (TDD Refactor). Runs pytest to verify tests are green. Sets TDD state to REFACTOR (refactor hat: only src/ edits allowed, tests must stay green per micro-edit).",
    ["test_node", "feature"])
  const omt_done = tddTool(env, "done",
    "Declare TDD completion. Runs full suite + checklist verification. Sets TDD state to DONE.",
    ["feature"])
  return { omt_testlist, omt_red, omt_green, omt_refactor, omt_done }
}

// --- before-hook two-hats gate ----------------------------------------------
// Runs tdd_check.py gate for a path and throws when the current TDD state
// (hat) forbids the edit. isTestsDir selects the tests/ branch of the gate.
export async function tddGateCheck(
  env: EnforcerEnv,
  session: string | undefined,
  rel: string,
  isTestsDir: boolean,
): Promise<void> {
  const tddRes = isTestsDir
    ? await env.$`uv run scripts/omt/tdd_check.py gate --path ${rel} --is-tests --session ${session || ""}`
      .cwd(env.directory).quiet().nothrow()
    : await env.$`uv run scripts/omt/tdd_check.py gate --path ${rel} --session ${session || ""}`
      .cwd(env.directory).quiet().nothrow()
  const tddData = JSON.parse(tddRes.stdout.toString() || '{"allowed":true}')
  if (!tddData.allowed) throw new OmtBlock(tddData.reason)
}

// --- after-hook after-edit check (advisory + REFACTOR revert) ---------------
// Runs only when tdd_mode is active. A revert_needed verdict restores the
// pre-edit content captured in the before-hook (refactorSnapshots) and blocks.
// The snapshot slot is always released (finally) so a stale snapshot never
// leaks into the next edit.
export async function tddAfterEdit(
  env: EnforcerEnv,
  input: any,
  abs: string,
  rel: string,
): Promise<void> {
  try {
    const tddSession = input?.sessionID || ""
    const tddUnlock = getActiveUnlock(tddSession)
    if (tddUnlock?.record?.tdd_mode) {
      const tddRes = await env.$`uv run scripts/omt/tdd_check.py after-edit --path ${rel} --session ${tddSession}`
        .cwd(env.directory).quiet().nothrow()
      const tddData = JSON.parse(tddRes.stdout.toString() || "{}")
      if (tddData.action === "revert_needed") {
        const content = env.state.refactorSnapshots.get(abs)
        if (content !== undefined) {
          writeFileSync(abs, content, "utf8")
          throw new OmtBlock(tddData.reason || "REFACTOR broke tests — edit reverted.")
        }
      }
      if (tddData.advisories?.length) {
        await env.notify(tddData.advisories.join("\n"))
      }
    }
  } catch (e: any) {
    if (e instanceof OmtBlock) throw e
    env.safeLog("warn", "TDD after-edit check failed: " + (e?.message || e))
  } finally {
    env.state.refactorSnapshots.delete(abs)
  }
}
