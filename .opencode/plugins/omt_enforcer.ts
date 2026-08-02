// OMT++ Process Enforcer — opencode plugin (feature_006).
//
// Turns AGENTS.md's *voluntary* process checkpoints into a *real* gate, tuned for a
// solo-dev learning scaffold: it blocks the edit that would skip a phase, but every block
// is a teaching message that names the OMT++ rule and the exact next command. Internal
// errors fail OPEN (never brick a working session); only genuine process violations block.
//
// meta_harness_dsl R2: this file is the THIN COMPOSITION ROOT — hook
// registration + dispatch only (single default export per Appendix B2). All
// gate logic lives in the lib modules:
//   ../lib/enforcer/session_state.ts  — the 5 process-lifetime containers
//                                       (audit P5/F20) + ledger helpers + OmtBlock
//   ../lib/enforcer/nav_gate.ts       — feature_020 nav gate + R6 S6 session
//                                       bootstrap (nav tip + TA digest, ONE Set)
//   ../lib/enforcer/receipt_guard.ts  — protected files, e2e receipt, tests/ canary
//   ../lib/enforcer/phase_gate.ts     — src/ phase+artifact gate, §12 matrix,
//                                       omt_phase/omt_skip/omt_complete
//   ../lib/enforcer/tdd_hats.ts       — feature_016 two-hats gate + TDD tools
//   ../lib/enforcer/think_gate.ts     — feature_021 think-gate + feature_022 D1
//                                       read-time thought injection
//   ../lib/enforcer/gate_driver.ts    — HDL-2 data-driven before/after gate
//                                       chains (IR @gate records)
//   ../lib/enforcer/mvc_after.ts      — MVC++ lint delta gate + idle sweep
//
// Mechanics:
//   • omt_phase  custom tool → agent declares task_type/phase/scope; recorded in the ledger.
//   • omt_skip   custom tool → logged escape hatch that unlocks edits for the session.
//   • tool.execute.before → gate edits to src/ (needs a phase), tests/ (needs approval),
//     and hard-deny README/.env/uv.lock/LICENSE.
//   • tool.execute.after  → data-driven after-chain (IR after-gates in order=: MVC++ delta, TDD revert).
//
// Ledger: .meta/.omt/ledger.jsonl  (gitignored runtime state, one JSON record per line)
//
// API note (verify on opencode 1.17.x via the Step-0 probe): assumes `input.sessionID`
// on tool.execute.before and `context.sessionID` on custom-tool execute. If absent, the
// gate falls back to an 8-hour time window so it still functions for a single user.

import { initOmtShared } from "../lib/omt_shared"
import {
  OmtBlock, createSessionState, makeSafeLog, makeNotify, type EnforcerEnv,
} from "../lib/enforcer/session_state"
import { navTrack, sessionBootstrap } from "../lib/enforcer/nav_gate"
import { runAfterGates, runBeforeGates } from "../lib/enforcer/gate_driver"
import { createPhaseTools } from "../lib/enforcer/phase_gate"
import { createTddTools } from "../lib/enforcer/tdd_hats"
import { injectThoughtsOnRead } from "../lib/enforcer/think_gate"
import { sessionIdleSweep } from "../lib/enforcer/mvc_after"


// omt_status is registered by .opencode/plugins/omt_status.ts as its own
// standalone plugin. Keeping it out of this enforcer avoids dynamic-import
// cache/loading failures and duplicate tool registration.

export default async ({ client, $, directory: cwd, worktree }) => {
  // F2/F17 (meta_harness_dsl R1): repo root = worktree ?? directory.
  // `directory` is the current working directory, so a subdir launch breaks
  // repo-relative paths exactly like a bare cwd did pre-R1; `worktree`
  // is the git worktree path. The shared lib is initialized with the same
  // value; all lib path getters are lazy and honor it.
  const directory = worktree ?? cwd
  initOmtShared(directory)

  const safeLog = makeSafeLog(client)
  const env: EnforcerEnv = {
    client, $, directory,
    state: createSessionState(),
    safeLog,
    notify: makeNotify(client, safeLog),
  }

  // --- hooks ---------------------------------------------------------------
  return {
    tool: { ...createPhaseTools(env), ...createTddTools(env) },

    "tool.execute.before": async (input, output) => {
      try {
        const session = input?.sessionID || undefined

        // feature_020: nav-vs-search tracking (instrumentation — the g.nav
        // block decision is in the data-driven chain below).
        await navTrack(env, session, input)

        // HDL-2 (improvement006/OPT-F): the gate chain is data-driven — the
        // driver iterates IR before-gates in order=, matching tools= and
        // evaluating when= via the @pred registry (lib/enforcer/gate_driver.ts).
        // SDK contract: in tool.execute.before args live on OUTPUT (input=
        // {tool, sessionID, callID} only). Reading input?.args here (a3ffb81's
        // false "F14 fix") made raw always undefined → every edit guard dead.
        // The AFTER hook is the one that reads input.args (genuine F14 fix).
        const raw = output?.args?.filePath ?? output?.args?.path ?? output?.args?.file
        await runBeforeGates(env, session, input, output,
          typeof raw === "string" && raw ? raw : null)
      } catch (e: any) {
        if (e instanceof OmtBlock) throw e          // intentional gate → block the edit
        safeLog("warn", "before-hook internal error (failing open): " + (e?.message || e))
      }
    },

    "tool.execute.after": async (input, output) => {
      // R6 S6: session bootstrap — nav reminder + TA digest, once per session
      // on the FIRST tool result (any tool). Fail-open.
      await sessionBootstrap(env, input, output)
      // feature_022 D1: read-time thought injection (first read per file per
      // session). Fail-open.
      await injectThoughtsOnRead(env, input, output)

      // HDL-2 (improvement007 R7/OPT-F): the after-chain is data-driven too —
      // the driver iterates IR after-gates in order=; the edit-tools filter
      // and the src/**.py scope are exactly the gates' tools=/when= attrs.
      // SDK contract: in tool.execute.after args live on INPUT — the genuine
      // F14 fix (output.args never existed in any SDK version).
      const raw = input?.args?.filePath ?? input?.args?.path ?? input?.args?.file
      if (typeof raw !== "string" || !raw) return
      await runAfterGates(env, input?.sessionID || undefined, input, output, raw)
    },

    event: async ({ event }) => {
      await sessionIdleSweep(env, event)
    },
  }
}
