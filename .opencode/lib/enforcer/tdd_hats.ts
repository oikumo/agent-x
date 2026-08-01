// OMT++ TDD two-hats enforcement (feature_016; meta_harness_dsl R2 module).
//
// Thin wrappers around scripts/omt/tdd_check.py (the state machine lives in
// Python): the namespaced omt_tdd tool (improvement006/OPT-H: five tools
// consolidated into one op= dispatcher), the before-hook two-hats gate
// (tests/ and src/ branches), and the after-hook after-edit check
// (advisories + REFACTOR revert when a refactor edit breaks tests).
// R8 (OMT-HDL-1): tool descriptions resolve from the compiled IR
// (irToolDescription) with the in-source text as fallback seed.

import { tool } from "@opencode-ai/plugin"
import { writeFileSync } from "node:fs"
import { OmtBlock, getActiveUnlock, type EnforcerEnv } from "./session_state"
import { irToolDescription } from "../omt_shared"

// --- TDD tools (thin wrappers delegating to tdd_check.py) -------------------
// improvement006/OPT-H: one registered tool; op dispatches to the subcommands
// (red → the engine's "start" subcommand — the tdd/ package is unchanged).
const TDD_SUBCMD: Record<string, string> = {
  testlist: "testlist", red: "start", green: "green", refactor: "refactor", done: "done",
}

export function createTddTools(env: EnforcerEnv) {
  const omt_tdd = tool({
    description: irToolDescription("omt_tdd", "TDD cycle driver. op=testlist(behaviors,feature) | red(test_node,target_src,feature) | green(test_node,feature) | refactor(test_node,feature) | done(feature)."),
    args: {
      op: tool.schema.string().describe("testlist | red | green | refactor | done"),
      behaviors: tool.schema.string().optional().describe("op=testlist: JSON array of behaviors"),
      feature: tool.schema.string().optional().describe("feature slug"),
      test_node: tool.schema.string().optional().describe("op=red/green/refactor: pytest node id"),
      target_src: tool.schema.string().optional().describe("op=red: src file under test"),
    },
    async execute(args, context) {
      const subcmd = TDD_SUBCMD[args?.op ?? ""]
      if (!subcmd) {
        return `⛔ omt_tdd: unknown op '${args?.op}' — want testlist|red|green|refactor|done ` +
          "(testlist(behaviors,feature) red(test_node,target_src,feature) green(test_node,feature) refactor(test_node,feature) done(feature))."
      }
      const session = context?.sessionID || ""
      const flags = [subcmd]
      for (const k of ["behaviors", "feature", "test_node", "target_src"]) {
        const v = args?.[k]
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
  return { omt_tdd }
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
