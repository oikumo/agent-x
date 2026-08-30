// OMT++ omt_net — meta-harness concurrency net (feature_039.adaptive_net_engine
// + feature_040.net_composition_supervisor)
// Thin proxy around scripts/omt/net_check.py (the state machine lives in
// Python, scripts/omt/net/; D2 — no src/ import). One registered tool, closed
// op enum per IDEA-002 v4 §5.0 (probe|fire|splice|sync|invariant live;
// synthesize reserved → clean not_implemented from the CLI, feature_042+).
// R8 (OMT-HDL-1): the tool is built inside createNetTool() so its description
// resolves from the compiled IR AFTER initOmtShared ran (module-level tool()
// would read the IR under the pre-init cwd — F2/F17).

import { tool } from "@opencode-ai/plugin"
import { execFileSync } from "node:child_process"
import { initOmtShared, repoRoot, irToolDescription } from "../lib/omt_shared"

const OPS = ["probe", "fire", "invariant", "splice", "sync", "synthesize"]

function createNetTool() {
  return tool({
    description: irToolDescription("omt_net", "Meta-harness concurrency net — single-net SSOT (IDEA-002 v4 §5.0 closed enum). op=probe(marking+enabled+advice) | fire(transition,reasoning,session?) | splice(mode,mutation?,subnet?,reasoning) | sync(bootstrap+proposal, D4) | invariant(invariants+net↔ledger drift) | synthesize reserved (feature_042+)."),
    args: {
      op: tool.schema.string().describe("probe|fire|splice|sync|invariant|synthesize"),
      transition: tool.schema.string().optional().describe("fire: transition name"),
      reasoning: tool.schema.string().optional().describe("fire/splice: why (audit, D4)"),
      session: tool.schema.string().optional().describe("session id (default: context)"),
      max_states: tool.schema.number().optional().describe("probe: analyzer exploration cap (default 1000)"),
      mode: tool.schema.string().optional().describe("splice: add|remove|disable|undo|repair"),
      mutation: tool.schema.string().optional().describe("splice: JSON mutation string (add_places/add_transitions/add_arcs | remove_places/remove_transitions/token_policy/reroute)"),
      subnet: tool.schema.string().optional().describe("splice disable: subnet key, e.g. feature_039"),
      feature: tool.schema.string().optional().describe("splice: owning feature slug (audit)"),
    },
    async execute(args, context) {
      const op = String(args?.op ?? "")
      if (!OPS.includes(op)) {
        return JSON.stringify({
          ok: false, error: "unknown_op", op,
          message: `want ${OPS.join("|")}`,
        })
      }
      const argv = ["run", "scripts/omt/net_check.py", op]
      for (const k of ["transition", "reasoning", "session", "mode", "mutation", "subnet", "feature"] as const) {
        let v: any = args?.[k]
        if (k === "session" && (v === undefined || v === null || v === "")) v = context?.sessionID
        if (v !== undefined && v !== null && v !== "")
          // Array guard: opencode SDK coerces JSON-array-looking strings fed to a
          // tool.schema.string() arg into actual JS arrays; String(v) collapses
          // to "a,b". Re-serialize arrays back to valid JSON (feature_027 fix).
          argv.push(`--${k}`, Array.isArray(v) ? JSON.stringify(v) : String(v))
      }
      if (args?.max_states !== undefined && args?.max_states !== null)
        argv.push("--max-states", String(args.max_states))
      try {
        const out = execFileSync("uv", argv, {
          cwd: repoRoot(), encoding: "utf8", timeout: 30000,
          stdio: ["ignore", "pipe", "pipe"],
        })
        return out.trim() // the CLI prints exactly one JSON envelope
      } catch (e: any) {
        // non-zero exit: the CLI's error envelope is on stdout — surface it
        const stdout = String(e?.stdout || "").trim()
        if (stdout) return stdout
        return JSON.stringify({ ok: false, error: "engine_error", op, message: String(e?.message || e) })
      }
    },
  })
}

// Standalone opencode plugin (omt_status.ts pattern): repo root = worktree ??
// directory, injected into the shared lib before any hook runs.
export default async ({ directory, worktree }: { directory: string; worktree?: string }) => {
  initOmtShared(worktree ?? directory)
  const omt_net = createNetTool()
  return {
    tool: { omt_net },
  }
}
