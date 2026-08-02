// OMT++ path-classification edit guards (meta_harness_dsl R2).
//
// The before-hook guards that refuse edits to specific PATH classes,
// independent of the declared phase:
//   • protected files (.env*, README.md, uv.lock, LICENSE) — AGENTS.md NEVER
//   • the OMT-harness e2e receipt (second-edit guard — shared lib machinery)
//   • the tests/ canary (AGENTS.md Stop Point #4; TDD two-hats delegates to
//     tdd_hats when tdd_mode is active)

import { omtHarnessE2eStatus, protectList, matchesProtect, gateMsg } from "../omt_shared"
import { OmtBlock, getActiveUnlock, type EnforcerEnv } from "./session_state"
import { tddGateCheck } from "./tdd_hats"

// --- path classification -------------------------------------------------
// improvement007/OPT-E: .omt @protect records (via the shared lib's
// protectList) are the FUNCTIONAL source; the pinned IR-missing fallback
// lives in the shared lib (never die open on the AGENTS.md NEVER paths).
export const isProtected = (rel: string): boolean =>
  protectList().some((p) => matchesProtect(rel, p))
export const isTests = (rel: string): boolean => rel === "tests" || rel.startsWith("tests/")
export const isSrc = (rel: string): boolean => rel.startsWith("src/")

// --- teaching messages ---------------------------------------------------
// improvement007 R8/OPT-G: block texts resolve from the IR @msg records via
// gateMsg ({rel} interpolated per call) — .omt-only edits. hard=true @protect
// records map to protect_env (no override), the rest to protect_file.

// Protected-file guard. Returns true when the edit was explicitly permitted
// (caller stops processing — no further guards run), throws OmtBlock on
// denial, and returns false when rel is not protected at all.
export async function guardProtectedPath(
  env: EnforcerEnv,
  session: string | undefined,
  rel: string,
): Promise<boolean> {
  if (!isProtected(rel)) return false
  // .env / secrets are never editable (AGENTS.md #2 — no override).
  const isEnv = protectList().some((p) => p.hard && matchesProtect(rel, p)) // hard=true ≡ no-override (the .env class)
  if (isEnv) throw new OmtBlock(`⛔ OMT++ gate: ${gateMsg("protect_env", { rel })}`)
  // README.md / uv.lock / LICENSE: AGENTS.md #5 allows edits "unless
  // explicitly asked". Honour an explicit omt_skip{scope:"all"} as that
  // explicit, ledger-audited unlock (aligns the gate with AGENTS.md so
  // a direct user request isn't mechanically blocked).
  const unlock = getActiveUnlock(session)
  const approved = unlock && unlock.type === "skip" && unlock.record.scope === "all"
  if (!approved) throw new OmtBlock(`⛔ OMT++ gate: ${gateMsg("protect_file", { rel })}`)
  env.safeLog("warn", `protected '${rel}' edit permitted under omt_skip(scope=all): ${unlock.record.reason || "(no reason)"}`)
  return true
}

// OMT-harness e2e receipt guard (second-edit guard; machinery lives in the
// shared lib since R1 — this is the before-hook call site).
export async function guardHarnessReceipt(rel: string, abs: string): Promise<void> {
  const e2e = omtHarnessE2eStatus(rel, abs)
  if (!e2e.ok) throw new OmtBlock(e2e.message)
}

// tests/ canary guard. TDD mode active → the two-hats gate decides (allowed
// tests/ edits skip the canary approval entirely). Otherwise an explicit
// canary approval (phase record with tests_approved or omt_skip) is required.
export async function guardTestsPath(
  env: EnforcerEnv,
  session: string | undefined,
  rel: string,
): Promise<void> {
  const unlock = getActiveUnlock(session)
  if (unlock?.record?.tdd_mode) {
    await tddGateCheck(env, session, rel, true)
    return // TDD allows tests/ — skip canary approval
  }
  const approved = unlock && (unlock.type === "skip"
    ? unlock.record.tests_approved
    : unlock.record.tests_approved === true)
  if (!approved) throw new OmtBlock(`⛔ OMT++ gate: ${gateMsg("tests_canary", { rel })}`)
}
