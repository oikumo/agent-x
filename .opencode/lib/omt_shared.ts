// OMT++ shared library — single source for cross-plugin constants, repo-root
// resolution, state paths, JSONL state IO, and the e2e-receipt status check
// (meta_harness_dsl R1; audit P1 duplication map, F2/F17 root fix).
// R2 S6: the think-anywhere machinery shared by the think plugin's tools AND
// the enforcer's session-bootstrap digest (grepThoughts / parseThoughtLine /
// foldThoughtEvents / readThoughtsIndex / thinkDigest) lives here too.
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

import { appendFileSync, mkdirSync, existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs"
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

// improvement007/OPT-E: .omt @var thought_pattern (compiled ir.vars) is the
// FUNCTIONAL source; the const above stays the pinned IR-missing fallback
// (never die open; value-pinned by tests/scripts/omt/test_thought_pattern_pin.py).
export function thoughtPattern(): string {
  const v = loadIr()?.vars?.thought_pattern
  return typeof v === "string" && v ? v : THOUGHT_PATTERN
}

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

// --- ledger rotation (meta_harness_dsl R4; audit F21/C10) -------------------
// The ledger grew unbounded (~124 KB and counting) and the think-gate parses
// it on EVERY gated edit (hasConsultedThoughts), so gate latency grew with
// history. Cap the hot file: when an append pushes it past LEDGER_CAP_BYTES,
// its content moves to `ledger-YYYYMM.jsonl` (appended — repeated same-month
// rotations stay chronological) and a fresh hot file starts. Readers scan the
// LATEST archive + the hot file; the 8 h unlock window shared by every gate
// reader makes current+latest sufficient. scripts/omt/tdd/state.py keeps its
// own copy of the cap (cross-language) — keep in sync; pinned by
// tests/scripts/omt/test_thought_pattern_pin.py.
export const LEDGER_CAP_BYTES = 64 * 1024

export function latestLedgerArchive(root?: string): string | null {
  try {
    const dir = dirname(ledgerPath(root))
    const names = readdirSync(dir)
      .filter((n) => /^ledger-\d{6}\.jsonl$/.test(n))
      .sort()
    return names.length ? join(dir, names[names.length - 1]) : null
  } catch { return null }
}

// Rotation-aware ledger read: latest archive (older) followed by the hot file
// (newer) — chronological order preserved. Fail-open [] per readJsonl.
export function readLedger(root?: string): any[] {
  const archive = latestLedgerArchive(root)
  const older = archive ? readJsonl(archive) : []
  return [...older, ...readJsonl(ledgerPath(root))]
}

// Append one record, then rotate the hot file if it exceeded the cap.
export function appendLedger(record: Record<string, unknown>, root?: string): void {
  appendJsonl(ledgerPath(root), record)
  rotateLedgerIfNeeded(root)
}

export function rotateLedgerIfNeeded(root?: string): void {
  try {
    const hot = ledgerPath(root)
    if (!existsSync(hot) || statSync(hot).size <= LEDGER_CAP_BYTES) return
    const now = new Date()
    const ym = `${now.getUTCFullYear()}${String(now.getUTCMonth() + 1).padStart(2, "0")}`
    appendFileSync(join(dirname(hot), `ledger-${ym}.jsonl`), readFileSync(hot))
    writeFileSync(hot, "")
  } catch { /* best-effort — rotation failure never breaks a session */ }
}

// --- e2e receipt status check (the OMT-harness second-edit guard) -----------
// Extracted from omt_enforcer.ts (R1); the enforcer calls omtHarnessE2eStatus
// from its before-hook (R2: the receipt_guard module). The guard requires a
// fresh comprehensive e2e receipt before a SECOND edit of any already-dirty
// harness file.
export const OMT_HARNESS_E2E_COMMAND = "uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q"
export const OMT_HARNESS_E2E_RECEIPT = join(".meta", ".omt", "omt_harness_e2e_last_run.json")
export const OMT_HARNESS_E2E_TEST = "tests/scripts/omt/test_omt_harness_e2e.py"

// improvement007/OPT-E: .omt @var e2e_cmd is the FUNCTIONAL source; the const
// above stays the pinned IR-missing fallback.
export function e2eCommand(): string {
  const v = loadIr()?.vars?.e2e_cmd
  return typeof v === "string" && v ? v : OMT_HARNESS_E2E_COMMAND
}

// improvement007/R6: .omt @var receipt_path / e2e_test are the FUNCTIONAL
// source; the consts above stay the pinned IR-missing fallback. The @var
// payload is forward-slash — identical to the join() literal on linux, so the
// rel-equality exempt check below keeps holding.
export function e2eReceiptPath(): string {
  const v = loadIr()?.vars?.receipt_path
  return typeof v === "string" && v ? v : OMT_HARNESS_E2E_RECEIPT
}

export function e2eTestPath(): string {
  const v = loadIr()?.vars?.e2e_test
  return typeof v === "string" && v ? v : OMT_HARNESS_E2E_TEST
}

// --- compiler projections (meta_harness_dsl R8 / OMT-HDL-1) -----------------
// harnessc.py compiles .meta/META_HARNESS.omt into two runtime-consumed
// projections: harness.ir.json (tool descriptions, vars) and nav.index.jsonl
// (navigation records). FRESH READ per call — no module-level caching (IR
// ~17 KB / index ~52 KB are trivial; a cache risks stale reads and captures
// the pre-init cwd — the F2/F17 poisoning class).
export function irPath(root?: string): string {
  return join(root ?? REPO_ROOT, ".meta", ".omt", "harness.ir.json")
}

export function navIndexPath(root?: string): string {
  return join(root ?? REPO_ROOT, ".meta", ".omt", "nav.index.jsonl")
}

export function loadIr(root?: string): any | null {
  try {
    const p = irPath(root)
    if (!existsSync(p)) return null
    return JSON.parse(readFileSync(p, "utf8"))
  } catch { return null }
}

// Tool description from the IR, with the in-source text as fallback when the
// projection is missing/corrupt or has no entry for the id — the static text
// stays the seed harnessc.py scraped into the .omt single source.
export function irToolDescription(id: string, fallback: string): string {
  const desc = loadIr()?.tools?.[id]?.description
  return typeof desc === "string" && desc ? desc : fallback
}

// Nav index records; null when missing/empty so callers take the legacy grep
// path unchanged.
export function loadNavIndex(root?: string): any[] | null {
  const recs = readJsonl(navIndexPath(root))
  return recs.length ? recs : null
}

// --- KB (Application Knowledge Base) index (feature_kb_akb) ------------------
export function kbIndexPath(root?: string): string {
  return join(root ?? REPO_ROOT, ".meta", ".omt", "kb.index.jsonl")
}

export function kbIrPath(root?: string): string {
  return join(root ?? REPO_ROOT, ".meta", ".omt", "kb.ir.json")
}

export function loadKbIndex(root?: string): any[] | null {
  const recs = readJsonl(kbIndexPath(root))
  return recs.length ? recs : null
}

export function loadKbIr(root?: string,): any | null {
  try {
    const p = kbIrPath(root)
    if (!existsSync(p)) return null
    return JSON.parse(readFileSync(p, "utf8"))
  } catch { return null }
}

// --- OMT-HDL-1 IR accessors (improvement007/OPT-E) ---------------------------
// The .omt records (compiled into the IR) are the FUNCTIONAL source for the
// values below; each FALLBACK_* literal keeps its guard alive when the
// projection is missing/corrupt (never die open) and is value-pinned against
// the IR by tests/scripts/omt/test_omt_enforcer_guard_source_pins.py — edit
// the .omt, run harnessc.py build, and update the fallback in the same commit.

const FALLBACK_PHASE_TRANSITIONS = "Analysis>Design,Testing;Design>Programming,Analysis;Programming>Testing,Design,Analysis;Testing>Analysis,Design,Programming,Done"

// Parse an @fsm transitions= spec ("A>B,C;D>E") into the Record shape.
function parseTransitions(spec: string): Record<string, string[]> {
  const out: Record<string, string[]> = {}
  for (const edge of spec.split(";")) {
    const [from, tos] = edge.split(">")
    if (!from || !tos) continue
    out[from.trim()] = tos.split(",").map((t) => t.trim()).filter(Boolean)
  }
  return out
}

// Valid phase transitions per guide §12 (.omt @fsm phase transitions=).
export function phaseTransitions(): Record<string, string[]> {
  const spec = loadIr()?.fsm?.phase?.transitions
  return parseTransitions(typeof spec === "string" && spec ? spec : FALLBACK_PHASE_TRANSITIONS)
}

const FALLBACK_TDD_AUTO_ON = "major_feature@Programming,new_screen@Programming"

// TDD auto-on per feature_016 (.omt @fsm tdd auto_on= — "tt@Phase,...").
export function tddAutoOn(taskType: string, phase: string): boolean {
  const spec = loadIr()?.fsm?.tdd?.auto_on
  const src = typeof spec === "string" && spec ? spec : FALLBACK_TDD_AUTO_ON
  return src.split(",").some((e) => {
    const [t, p] = e.split("@")
    return t?.trim() === taskType && p?.trim() === phase
  })
}

const FALLBACK_PROTECT: { path: string; hard: boolean }[] = [
  { path: ".env", hard: true },
  { path: ".env.*", hard: true },
  { path: "README.md", hard: false },
  { path: "uv.lock", hard: false },
  { path: "LICENSE", hard: false },
]

// Protected files per AGENTS.md NEVER (.omt @protect records → ir.protect).
export function protectList(): { path: string; hard: boolean }[] {
  const p = loadIr()?.protect
  return Array.isArray(p) && p.length ? p : FALLBACK_PROTECT
}

// Trailing "*" = prefix match (the gate_driver pathIn "@protect.*" semantic).
export function matchesProtect(rel: string, p: { path: string }): boolean {
  return p.path.endsWith("*") ? rel.startsWith(p.path.slice(0, -1)) : rel === p.path
}

// improvement007 R8/OPT-G: gate block/warn text resolves from the compiled IR
// (@msg records — the .omt is the single source; {@var.x} refs were baked at
// build time). {rel}/{tt}/{feature} placeholders interpolate per call. There
// is deliberately NO FALLBACK_* text mirror: a missing projection degrades the
// text to the msg id — guard LOGIC never dies (FALLBACK_GATES & co. own that);
// message text is teaching, not logic (genericImpl's established posture).
export function gateMsg(
  id: string,
  ctx?: { rel?: string | null; tt?: string; feature?: string },
): string {
  const raw = loadIr()?.msgs?.[id]?.text
  const text = typeof raw === "string" && raw ? raw : id
  return text
    .replaceAll("{rel}", ctx?.rel ?? "")
    .replaceAll("{tt}", ctx?.tt ?? "")
    .replaceAll("{feature}", ctx?.feature ?? "")
}

export function isOmtHarness(rel: string): boolean {
  // meta_harness_dsl R8 follow-up (F9 class killed): the compiled IR is the
  // FUNCTIONAL source (.omt @var harness_paths → harnessc exact/prefix
  // classification); the literal below is only the fallback when the
  // projection is missing/corrupt — the guard must never die open. The two
  // are pinned in sync by test_omt_enforcer_guard_source_pins.py.
  const hp = loadIr()?.harness_paths
  if (Array.isArray(hp?.exact) && Array.isArray(hp?.prefix)) {
    return hp.exact.includes(rel) || hp.prefix.some((p: string) => rel.startsWith(p))
  }
  return rel === "AGENTS.md" || rel === "opencode.jsonc" ||
    rel === ".meta/META_HARNESS.omt" ||
    rel === ".meta/software_development_process/omt_agent_guide.md" ||
    rel.startsWith(".opencode/plugins/omt_") ||
    rel.startsWith(".opencode/lib/omt_") ||
    rel.startsWith(".opencode/lib/enforcer/") ||
    rel.startsWith("scripts/omt/") ||
    rel.startsWith(".meta/templates/") ||
    rel.startsWith(".meta/software_development_process/2.requirements/features/feature_006.opencode_process_enforcement/") ||
    rel.startsWith("tests/scripts/omt/")
}

export function receiptTimestampMs(): number {
  const receipt = join(REPO_ROOT, e2eReceiptPath())
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
  if (rel === e2eTestPath() || rel === e2eReceiptPath()) {
    return { ok: true, message: "" }
  }
  if (!existsSync(abs)) return { ok: true, message: "" }
  if (!isGitDirty(rel)) return { ok: true, message: "" }

  const lastPassed = receiptTimestampMs()
  let targetMtime = 0
  try { targetMtime = statSync(abs).mtimeMs } catch { return { ok: true, message: "" } }
  if (lastPassed >= targetMtime) return { ok: true, message: "" }

  // improvement007 R8/OPT-G: block text from the IR @msg receipt_stale
  // record ({@var.e2e_cmd}/{@var.receipt_path} baked at build; {rel} per call).
  return { ok: false, message: `⛔ OMT++ gate: ${gateMsg("receipt_stale", { rel })}` }
}

// --- think-anywhere shared machinery (meta_harness_dsl R2 S6) ---------------
// Moved out of omt_think.ts so BOTH the think plugin's tools and the
// enforcer's session-bootstrap digest share one implementation. grep (the
// inline comments) stays the source of truth; the JSONL index is an
// append-only sidecar of add / verify / remove-tombstone events (R6 S1 — the
// reconcile/reindex rewrite class was DELETED: grep-is-truth made it
// redundant AND destructive-prone on an untracked, backup-less index; audit
// P8/F12).

// Read the JSONL index (append-only event log: add / verify / remove records).
// Skips corrupt lines, fail-open [].
export function readThoughtsIndex(root?: string): any[] {
  return readJsonl(thoughtsIndexPath(root))
}

// grep thought lines across a target (file or dir), honoring excludes. Returns
// parsed {file,line,content} hits. Uses execFileSync (array argv — no shell,
// H3 safe). -E: callers pass ERE patterns (THOUGHT_PATTERN-based, feature_022
// A1). A1b: .venv/__pycache__ excluded (noise dirs that polluted the digest).
export function grepThoughts(pattern: string, target: string): { file: string; line: number; content: string }[] {
  const results: { file: string; line: number; content: string }[] = []
  const absTarget = isAbsolute(target) ? target : join(repoRoot(), target)
  if (!existsSync(absTarget)) return results
  try {
    const output = execFileSync("grep", [
      "-rnHE",
      "--exclude-dir=.git", "--exclude-dir=node_modules", "--exclude-dir=.omt",
      "--exclude-dir=.venv", "--exclude-dir=__pycache__",
      "--exclude=*.env*",
      "--", pattern, absTarget,
    ], { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] })
    for (const line of output.trim().split("\n")) {
      if (!line) continue
      const match = line.match(/^(.+?):(\d+):(.*)$/)
      if (match) {
        const [, file, lineNum, content] = match
        results.push({
          file: relative(repoRoot(), file).split("\\").join("/"),
          line: parseInt(lineNum, 10),
          content: content.trim(),
        })
      }
    }
  } catch { /* grep returns non-zero when no matches — fine */ }
  return results
}

// Parse a rendered thought line into {cat, text} for dedup comparison (A4).
// Returns null for non-thought lines (anchored-pattern test first), so prose
// mentions never collide with real thoughts.
export function parseThoughtLine(line: string): { cat: string; text: string } | null {
  if (!new RegExp(thoughtPattern()).test(line)) return null
  let t = line.trim()
  t = t.replace(/^(#|\/\/|\/\*|<!--|--)\s*/, "") // comment opener
  t = t.replace(/^TA:\s*/, "") // marker
  t = t.replace(/\s*(-->|\*\/)$/, "") // trailing html/block closer
  t = t.replace(/\s+/g, " ").trim()
  let cat = ""
  const m = t.match(/^([a-z0-9_-]+):\s+(.*)$/)
  if (m) { cat = m[1]; t = m[2] }
  return { cat, text: t.trim() }
}

// Append-only event fold (meta_harness_dsl R6 S1): the index is NEVER rewritten
// (grep is truth, audit P8/F12). Records are add (no kind) / verify /
// remove-tombstone events; the fold is latest-wins. A slot (path:line) is
// ALIVE when its newest add/remove event is an add — a tombstoned slot reads
// as absent, and a re-added thought (newer add-record) starts unverified
// (feature_022 C1 semantics, zero rewrites). Verify verdicts join by
// normalized thought TEXT (identity), never path:line (audit F28: line drift
// must not re-attach a verdict to the wrong thought; path:line is a display
// key only).
export function foldThoughtEvents(recs: any[]): {
  aliveAdds: any[]
  latestAddTsByText: Map<string, number>
  latestVerifyByText: Map<string, { status: string; ts: number }>
} {
  const slotLatest = new Map<string, { kind: string; r: any }>()
  const latestAddTsByText = new Map<string, number>()
  const latestVerifyByText = new Map<string, { status: string; ts: number }>()
  for (const r of recs) {
    if (!r || typeof r.path !== "string") continue
    const ts = Date.parse(r.ts || "") || 0
    if (r.kind === "verify") {
      if (typeof r.thought === "string" && r.thought) {
        const cur = latestVerifyByText.get(r.thought)
        if (!cur || ts >= cur.ts) latestVerifyByText.set(r.thought, { status: String(r.status || ""), ts })
      }
      continue
    }
    if (r.kind === "remove") {
      slotLatest.set(`${r.path}:${r.line}`, { kind: "remove", r })
      continue
    }
    // add-record (no kind field)
    slotLatest.set(`${r.path}:${r.line}`, { kind: "add", r })
    if (typeof r.thought === "string" && r.thought) {
      if (ts >= (latestAddTsByText.get(r.thought) || 0)) latestAddTsByText.set(r.thought, ts)
    }
  }
  const aliveAdds = [...slotLatest.values()].filter(e => e.kind === "add").map(e => e.r)
  return { aliveAdds, latestAddTsByText, latestVerifyByText }
}

// --- per-session digest (R6 S7 compact form) --------------------------------
// Compact by design (audit F32/C4: a conversation-resident injection is re-paid
// EVERY model turn — full texts × ~30 turns ≈ 10k tok/session). Counts +
// per-file counts + stale ⚠️ survive; full texts are re-injected point-of-use
// by D1 on file read and are one omt_think_list call away.
// R2 S6: emitted by the enforcer's session bootstrap (nav_gate), once per
// session on the first tool result.
// R7 T5: hard byte cap as the last line of defense under the structural caps
// (top-6 files, top-5 stale) — source-pinned by
// tests/scripts/omt/test_omt_docs_drift_pins.py (token budget pins).
export const DIGEST_CAP_BYTES = 1024
export function thinkDigest(): string {
  const hits = grepThoughts(thoughtPattern(), ".")
  if (hits.length === 0) {
    return "💡 TA: 0 thoughts indexed. Drop one with omt_think{path, thought} when you learn a gotcha."
  }
  const files = new Set(hits.map(h => h.file))
  // Stale join (C1/F28): verdicts matched to live hits by normalized TEXT, and
  // only when the verdict is newer than the thought's latest add (a re-added
  // thought starts unverified). Index unreadable/corrupt → 0 stale (fail-open
  // — the digest never breaks a session).
  const { latestAddTsByText, latestVerifyByText } = foldThoughtEvents(readThoughtsIndex())
  const stale: string[] = []
  for (const h of hits) {
    const p = parseThoughtLine(h.content)
    if (!p) continue
    const v = latestVerifyByText.get(p.text)
    if (!v || v.status !== "stale") continue
    if (v.ts >= (latestAddTsByText.get(p.text) || 0)) stale.push(`${h.file}:${h.line}`)
  }
  const perFile = new Map<string, number>()
  for (const h of hits) perFile.set(h.file, (perFile.get(h.file) || 0) + 1)
  const top = [...perFile.entries()].sort((a, b) => b[1] - a[1])
  const shown = top.slice(0, 6).map(([f, n]) => `${f}(${n})`).join(" ")
  let out = `💡 TA: ${hits.length} thought${hits.length === 1 ? "" : "s"} across ${files.size} file${files.size === 1 ? "" : "s"} — ${shown}` +
    (top.length > 6 ? ` … (+${top.length - 6} files)` : "") +
    (stale.length ? `\n⚠️ ${stale.length} stale: ${stale.slice(0, 5).join(", ")}${stale.length > 5 ? " …" : ""} — re-check with omt_think{op:"verify", path, line}.` : "")
  out += ` · full texts: omt_think{op:list} (think-gate applies).`
  return out.length > DIGEST_CAP_BYTES ? out.slice(0, DIGEST_CAP_BYTES - 1) + "…" : out
}
