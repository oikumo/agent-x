// OMT++ shared library — single source for cross-plugin constants, repo-root
// resolution, state paths, JSONL state IO, and the e2e-receipt status check
// (meta_harness_dsl R1; audit P1 duplication map, F2/F17 root fix).
//
// Loader contract (plan Appendix B2): this file lives OUTSIDE
// .opencode/plugins/, so named non-function exports are legal here (plain Bun
// module resolution). Plugin files in plugins/ keep function-only named
// exports + the default factory.
//
// Repo-root (F2/F17): every plugin factory MUST call
// initOmtShared(worktree ?? directory) before returning its hooks.
// `directory` is the current working directory, so a subdir launch breaks
// repo-relative paths exactly like process.cwd() did; `worktree` is the git
// worktree path. All path getters below are LAZY (functions, not module-level
// constants) so the injected root is always honored; pre-init they fall back
// to the process working directory (hermetic test imports never run the
// factory).

import { appendFileSync, mkdirSync, existsSync, readFileSync, readdirSync, statSync } from "node:fs"
import { join, relative, isAbsolute, dirname } from "node:path"
import { execFileSync } from "node:child_process"

let REPO_ROOT = process.cwd()

// Called by each plugin factory with the plugin-context root
// (worktree ?? directory). Idempotent; last call wins (all four plugins
// receive the same ctx root in practice). Returns the effective root.
export function initOmtShared(root: string): string {
  if (typeof root === "string" && root) REPO_ROOT = root
  return REPO_ROOT
}

export function repoRoot(): string {
  return REPO_ROOT
}

// --- state paths (lazy getters — see header) --------------------------------
export function ledgerPath(root?: string): string {
  return join(root ?? REPO_ROOT, ".meta", ".omt", "ledger.jsonl")
}

export function thoughtsIndexPath(root?: string): string {
  return join(root ?? REPO_ROOT, ".meta", ".omt", "thoughts.jsonl")
}

export function workMdPath(root?: string): string {
  return join(root ?? REPO_ROOT, "WORK.md")
}

export function designRoot(root?: string): string {
  return join(root ?? REPO_ROOT, ".meta", "software_development_process", "4.design", "features")
}

// --- shared constants -------------------------------------------------------
// Anchored TA: thought pattern (feature_022 A1 / F3): matches only real
// comment-opener thought lines, never prose mentions (META:/DATA:/string
// literals). Covers every opener omt_think can emit (#, //, /*, <!--, --) so
// list/gate are never blind to what omt_think wrote. grep -E / JS RegExp
// compatible (\s is a GNU-grep ERE extension — confirmed on box).
// SINGLE SOURCE (R1): previously byte-duplicated in omt_enforcer.ts and
// omt_think.ts (audit P1/F10); pinned by tests/scripts/omt/test_thought_pattern_pin.py.
export const THOUGHT_PATTERN = "^\\s*(#|//|/\\*|<!--|--)\\s*TA:"

// 8-hour unlock window. Single source for all TS plugins (previously named in
// omt_enforcer.ts, inline magic number ×2 in omt_status.ts — audit P1).
// scripts/omt/tdd_check.py keeps its own copy (cross-language) — keep in sync;
// pinned by test_thought_pattern_pin.py::test_unlock_window_ms_agrees_across_languages.
export const UNLOCK_WINDOW_MS = 8 * 60 * 60 * 1000

// --- path helpers -----------------------------------------------------------
// Resolve a raw (absolute or repo-relative) path against the repo root.
// rel is always forward-slash normalized.
export function relOf(raw: string): { abs: string; rel: string } {
  const abs = isAbsolute(raw) ? raw : join(REPO_ROOT, raw)
  return { abs, rel: relative(REPO_ROOT, abs).split("\\").join("/") }
}

export function toAbs(rel: string): string {
  return isAbsolute(rel) ? rel : join(REPO_ROOT, rel)
}

// Resolve the actual feature subdirectory under a `features/` parent.
// Handles BOTH naming conventions: short "feature_004" and full
// "feature_007.agentx_intelligent_agent_behaviour" (new_feature.py scaffolder
// default). Without this, full-slug features are never found and phase-exit
// artifact checks report false negatives.
export function resolveFeatureDir(featuresParent: string, feature: string, featureNum: string): string | null {
  try {
    if (!existsSync(featuresParent)) return null
    const entries = readdirSync(featuresParent, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name)
    // 1. exact matches (full slug first, then short)
    for (const c of [feature, featureNum]) {
      if (c && entries.includes(c)) return join(featuresParent, c)
    }
    // 2. prefix match: a full-slug dir that starts with "feature_NNN." or "feature_NNN_"
    for (const p of [featureNum + ".", featureNum + "_"]) {
      if (!featureNum || p === "." || p === "_") continue
      const m = entries.find(e => e.startsWith(p))
      if (m) return join(featuresParent, m)
    }
    return null
  } catch { return null }
}

export function globToRegex(pattern: string): RegExp {
  const escaped = pattern
    .replace(/[.+?^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*")
  return new RegExp(`^${escaped}$`)
}

// --- JSONL state IO ---------------------------------------------------------
// Shared readers/writers for the harness state files (ledger.jsonl,
// thoughts.jsonl, ...). Append adds the `ts` field; callers pass the rest.
// Fail-open: missing/corrupt files read as [], append errors are swallowed
// (best-effort — identical semantics to the pre-R1 per-plugin copies).
export function readJsonl(path: string): any[] {
  if (!existsSync(path)) return []
  try {
    const out: any[] = []
    for (const line of readFileSync(path, "utf8").split("\n")) {
      const s = line.trim()
      if (!s) continue
      try { out.push(JSON.parse(s)) } catch { /* skip corrupt line */ }
    }
    return out
  } catch { return [] }
}

export function appendJsonl(path: string, record: Record<string, unknown>): void {
  try {
    mkdirSync(dirname(path), { recursive: true })
    appendFileSync(path, JSON.stringify({ ts: new Date().toISOString(), ...record }) + "\n")
  } catch { /* best-effort */ }
}

// --- e2e receipt status check (the OMT-harness second-edit guard) -----------
// Extracted from omt_enforcer.ts (R1); the enforcer calls omtHarnessE2eStatus
// from its before-hook. The guard requires a fresh comprehensive e2e receipt
// before a SECOND edit of any already-dirty harness file.
export const OMT_HARNESS_E2E_COMMAND = "uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q"
export const OMT_HARNESS_E2E_RECEIPT = join(".meta", ".omt", "omt_harness_e2e_last_run.json")
export const OMT_HARNESS_E2E_TEST = "tests/scripts/omt/test_omt_harness_e2e.py"

export function isOmtHarness(rel: string): boolean {
  return rel === "AGENTS.md" || rel === "opencode.jsonc" ||
    rel === ".meta/software_development_process/omt_agent_guide.md" ||
    rel.startsWith(".opencode/plugins/omt_") ||
    rel.startsWith(".opencode/lib/omt_") ||
    rel.startsWith("scripts/omt/") ||
    rel.startsWith(".meta/templates/") ||
    rel.startsWith(".meta/software_development_process/2.requirements/features/feature_006.opencode_process_enforcement/") ||
    rel.startsWith("tests/scripts/omt/")
}

export function receiptTimestampMs(): number {
  const receipt = join(REPO_ROOT, OMT_HARNESS_E2E_RECEIPT)
  if (!existsSync(receipt)) return 0
  let parsed = 0
  try {
    const data = JSON.parse(readFileSync(receipt, "utf8") || "{}")
    const t = Date.parse(data.passed_at || data.timestamp || "")
    parsed = Number.isNaN(t) ? 0 : t
  } catch { /* ignore invalid receipt */ }
  try { return Math.max(parsed, statSync(receipt).mtimeMs) } catch { return parsed }
}

export function isGitDirty(rel: string): boolean {
  try {
    const out = execFileSync("git", ["status", "--porcelain", "--", rel], {
      cwd: REPO_ROOT,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    })
    return out.trim().length > 0
  } catch {
    // If git is unavailable, fail open. The e2e test still verifies the source guard.
    return false
  }
}

export function omtHarnessE2eStatus(rel: string, abs: string): { ok: boolean; message: string } {
  if (!isOmtHarness(rel)) return { ok: true, message: "" }
  if (rel === OMT_HARNESS_E2E_TEST || rel === OMT_HARNESS_E2E_RECEIPT) {
    return { ok: true, message: "" }
  }
  if (!existsSync(abs)) return { ok: true, message: "" }
  if (!isGitDirty(rel)) return { ok: true, message: "" }

  const lastPassed = receiptTimestampMs()
  let targetMtime = 0
  try { targetMtime = statSync(abs).mtimeMs } catch { return { ok: true, message: "" } }
  if (lastPassed >= targetMtime) return { ok: true, message: "" }

  return {
    ok: false,
    message:
      `⛔ OMT++ gate: '${rel}' is part of the META HARNESS / OMT enforcement surface ` +
      `and already has unverified changes. Run the comprehensive harness e2e test before ` +
      `editing it again:\n  ${OMT_HARNESS_E2E_COMMAND}\n` +
      `This test refreshes ${OMT_HARNESS_E2E_RECEIPT}.`,
  }
}
