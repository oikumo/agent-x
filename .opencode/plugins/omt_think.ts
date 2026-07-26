// OMT++ Think Anywhere — persistent inline TA: thought-tag layer (feature_021,
// hardened by feature_022 Tier A: anchored thought pattern, explicit extension
// map, string-context insertion guard, filter/dedup/EOL correctness; Tier B1:
// after:/symbol: anchor-based insertion — drift-resistant, anchor in index;
// Tier C: omt_think_verify placement-integrity lifecycle (verified/stale),
// digest stale count, per-file consult records; Tier remainder: omt_think_suggest
// AST-ranked site advisor (B2); E1 resolved by meta_harness_dsl R6: the
// reindex/rewrite class was DELETED — the index is append-only (add / verify /
// remove-tombstone events, latest-wins fold), grep stays the source of truth.
//
// Adapts the Think-Anywhere paper's on-demand reasoning to the META HARNESS as a
// PERSISTENT, grep-friendly annotation/memory layer. opencode drops compact
// `TA:` comment tags inline in real (non-protected) files so hard-won context
// survives across sessions. Retrieval is grep-backed (O(hits) tokens); a
// per-session digest surfaces accumulated thoughts; a blocking think-gate
// (in omt_enforcer.ts) refuses to edit thought-carrying files until consulted.
//
// Contract (mirrors omt_nav.ts / omt_status.ts — feature_020 defect-free):
//   • import { tool } from "@opencode-ai/plugin"; args + tool.schema.* (DEFECT-C safe)
//   • async execute(args, context) returns a plain string (DEFECT-D safe)
//   • default export async () => ({ tool, "tool.execute.after" })
//   • NO named tool-object exports (DEFECT-A safe); only the default factory
//   • file ops via execFileSync/readFileSync/writeFileSync (no shell — H3 safe)

import { tool } from "@opencode-ai/plugin"
import { existsSync, readFileSync, writeFileSync } from "node:fs"
import { join, relative, isAbsolute, extname } from "node:path"
import { execFileSync } from "node:child_process"
// Single source (meta_harness_dsl R1): THOUGHT_PATTERN, state paths, JSONL IO
// and repo-root live in the shared lib (root injected at plugin-init, F2/F17).
import {
  initOmtShared, repoRoot, ledgerPath, thoughtsIndexPath,
  relOf as sharedRelOf, toAbs, readJsonl, appendJsonl, THOUGHT_PATTERN,
} from "../lib/omt_shared"

// Protected files: TA: tags are NEVER written here (AGENTS.md NEVER set + JSON).
const PROTECTED_FILES = new Set(["README.md", "uv.lock", "LICENSE", ".env"])
function isProtectedPath(rel: string): boolean {
  if (typeof rel !== "string") return true
  return rel === ".env" || rel.startsWith(".env.") ||
    PROTECTED_FILES.has(rel) || rel === "README.md" || rel.endsWith("/README.md")
}

// Escape a user-supplied string for safe interpolation into a grep -E / JS
// regex pattern (feature_022 A4 / F7).
function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

// Language-aware comment wrapper (feature_022 A2): EXPLICIT extension map —
// unknown/none → null (denied). The v1 "hash is safe for most text formats"
// default was unsafe (F2: e.g. .sql would have gotten '#' comments). .json has
// no comments → denied (dedicated message at the call site). .jsonc allows //.
// NOT exported: opencode's loader calls every named export at load time with a
// non-string arg, which would crash `(ext||"").toLowerCase` (DEFECT-A load-crash
// class). Only `export default` may leave this module — mirrors omt_nav.ts.
function commentSyntaxFor(ext: string): { open: string; close: string } | null {
  const e = (ext || "").toLowerCase()
  if (e === ".json") return null
  if ([".py", ".toml", ".cfg", ".ini", ".sh", ".yml", ".yaml", ".rb", ".r", ".pl"].includes(e))
    return { open: "#", close: "" }
  if ([".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx", ".jsonc",
    ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".swift", ".kt", ".scala"].includes(e))
    return { open: "//", close: "" }
  if ([".md", ".mdx", ".html", ".xml", ".vue", ".svelte"].includes(e))
    return { open: "<!--", close: "-->" }
  if ([".css", ".scss", ".less"].includes(e))
    return { open: "/*", close: "*/" }
  if (e === ".sql") return { open: "--", close: "" }
  return null
}

// Thin local adapter: this plugin's relOf returns the rel string only (the
// shared lib's relOf returns {abs, rel}); toAbs is imported from the lib.
function relOf(raw: string): string {
  return sharedRelOf(raw).rel
}

// Append a record to the JSONL index (best-effort structured sidecar; inline
// thought-tags remain the source of truth). APPEND-ONLY (R6 S1): no code path
// may rewrite this file — pinned by test_thought_pattern_pin.py.
function appendIndex(record: Record<string, unknown>): void {
  appendJsonl(thoughtsIndexPath(), record)
}

// Read the JSONL index (append-only event log: add / verify / remove records).
// Skips corrupt lines, fail-open [].
function readThoughtsIndex(): any[] {
  return readJsonl(thoughtsIndexPath())
}

// Append-only event fold (meta_harness_dsl R6 S1): the index is NEVER rewritten
// (the reconcile/reindex rewrite-by-filter class was deleted — grep is truth,
// audit P8/F12). Records are add (no kind) / verify / remove-tombstone events;
// the fold is latest-wins. A slot (path:line) is ALIVE when its newest
// add/remove event is an add — a tombstoned slot reads as absent, and a
// re-added thought (newer add-record) starts unverified (feature_022 C1
// semantics, zero rewrites). Verify verdicts join by normalized thought TEXT
// (identity), never path:line (audit F28: line drift must not re-attach a
// verdict to the wrong thought; path:line is a display key only).
function foldThoughtEvents(recs: any[]): {
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

// Record a think_consult in the shared ledger so the enforcer's think-gate
// clears. C2: per-file granularity — files = rel paths the listing actually
// matched (what the agent was shown), capped at 200 (+ files_truncated flag;
// a truncated record covers only listed files — safe direction). Empty result
// → files: [] (covers nothing; no clearance granted).
function recordConsult(session: string | undefined, files: string[]): void {
  appendJsonl(ledgerPath(), {
    kind: "think_consult", session: session || "",
    files: files.slice(0, 200),
    ...(files.length > 200 ? { files_truncated: true } : {}),
  })
}

// grep thought lines across a target (file or dir), honoring excludes. Returns
// parsed {file,line,content} hits. Uses execFileSync (array argv — no shell,
// H3 safe). -E: callers pass ERE patterns (THOUGHT_PATTERN-based, feature_022
// A1). A1b: .venv/__pycache__ excluded (noise dirs that polluted the digest).
function grepThoughts(pattern: string, target: string): { file: string; line: number; content: string }[] {
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

// Build the rendered TA: line for a given extension/category/thought.
function buildThoughtLine(ext: string, category: string | undefined, thought: string): string | null {
  const wrap = commentSyntaxFor(ext)
  if (!wrap) return null
  // strip a user-prepended "TA:" so we control the marker uniformly
  let t = thought.replace(/\s+/g, " ").trim()
  t = t.replace(/^TA:\s*/i, "")
  // A4: category normalized to lowercase at insert (F7 case defect).
  const cat = category ? `${category.trim().toLowerCase()}: ` : ""
  const tail = wrap.close ? ` ${wrap.close}` : ""
  return `${wrap.open} TA: ${cat}${t}${tail}`
}

// Parse a rendered thought line into {cat, text} for dedup comparison (A4).
// Returns null for non-thought lines (anchored-pattern test first), so prose
// mentions never collide with real thoughts.
function parseThoughtLine(line: string): { cat: string; text: string } | null {
  if (!new RegExp(THOUGHT_PATTERN).test(line)) return null
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

// A3: naïve parity guard — is the insertion point (0-based index into lines)
// inside a triple-quoted string (.py) or a code fence (.md/.mdx)? Odd parity
// of delimiters seen BEFORE the insertion point ⇒ inside. Same-line open+close
// counts 2 ⇒ outside. Failure direction is refuse, which is safe. (Other exts
// ⇒ false; .ts template literals deferred beyond Tier A — documented.)
function inStringContext(lines: string[], insertAt: number, ext: string): boolean {
  const e = (ext || "").toLowerCase()
  const before = lines.slice(0, Math.max(0, insertAt))
  if (e === ".py") {
    let dq = 0, sq = 0
    for (const l of before) {
      dq += l.split('"""').length - 1
      sq += l.split("'''").length - 1
    }
    return dq % 2 === 1 || sq % 2 === 1
  }
  if (e === ".md" || e === ".mdx") {
    let fences = 0
    for (const l of before) {
      if (/^\s*(```|~~~)/.test(l)) fences++
    }
    return fences % 2 === 1
  }
  return false
}

// B1 (feature_022): resolve after:/symbol: anchors to an insertion index.
// after: literal substring (case-sensitive, no regex path). symbol: per-family
// definition regex with the name escapeRegex'd (metachars treated literally).
// Match policy (both modes): 0 → not-found refusal; >1 → ambiguity refusal
// listing up to 5 candidate lines (forces drift-resistant anchors — same
// philosophy as A2's deny-unknown-extension; first-match-on-ambiguous would
// silently retarget, reintroducing the F6 fragility this tier removes).
// Module-local (DEFECT-A: no named exports — opencode's loader calls every
// export at load time).
function resolveAnchor(
  lines: string[],
  ext: string,
  rel: string,
  after: string | undefined | null,
  symbol: string | undefined | null,
): { ok: true; insertAt: number; anchor: { kind: "after" | "symbol"; value: string } } | { ok: false; err: string } {
  const preview = (s: string) => {
    const p = s.replace(/\s+/g, " ").trim()
    return p.length > 60 ? p.slice(0, 60) + "…" : p
  }
  const matches: number[] = []
  let kind: "after" | "symbol"
  let value: string
  if (after !== undefined && after !== null) {
    kind = "after"
    value = after
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(value)) matches.push(i)
    }
  } else {
    kind = "symbol"
    value = symbol as string
    const e = (ext || "").toLowerCase()
    const name = escapeRegex(value)
    let rx: RegExp
    if (e === ".py") {
      rx = new RegExp(`^\\s*(?:async\\s+def|def|class)\\s+${name}\\b`)
    } else if ([".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx"].includes(e)) {
      rx = new RegExp(`(?:^|\\s)(?:export\\s+)?(?:default\\s+)?(?:async\\s+)?(?:function|class|const|let|var)\\s+${name}\\b`)
    } else {
      return {
        ok: false,
        err: `⛔ TA: refused — symbol addressing is not supported for '${ext || "(none)"}'; ` +
          `use after: with a literal anchor.`,
      }
    }
    for (let i = 0; i < lines.length; i++) {
      if (rx.test(lines[i])) matches.push(i)
    }
  }
  if (matches.length === 0) {
    return { ok: false, err: `⛔ TA: refused — anchor not found in ${rel}: '${preview(value)}'` }
  }
  if (matches.length > 1) {
    const candidates = matches.slice(0, 5).map((i) => i + 1).join(", ")
    return {
      ok: false,
      err: `⛔ TA: refused — anchor matches ${matches.length} lines in ${rel} ` +
        `(e.g. lines ${candidates}). Use a more specific anchor.`,
    }
  }
  // Insert AFTER the anchor line — same convention as line mode.
  return { ok: true, insertAt: matches[0] + 1, anchor: { kind, value } }
}

// --- omt_think: add a thought inline ---------------------------------------
const omt_think = tool({
  description:
    "Add a persistent TA: thought-tag inline in a non-protected file (feature_021). " +
    "The thought becomes a language-valid single-line comment so it survives across " +
    "sessions and is grep-retrievable. Bypasses phase/canary gates (annotation, not code). " +
    "Address by line (1-based), after (literal substring anchor), or symbol " +
    "(definition-name anchor, .py/.ts-family) — at most one (feature_022 B1).",
  args: {
    path: tool.schema.string().describe("repo-relative target file (must already exist)"),
    thought: tool.schema.string().describe("the thought text (single line; newlines stripped)"),
    line: tool.schema.number().optional().describe("1-based line to insert AFTER (default: append at EOF)"),
    after: tool.schema.string().optional().describe(
      "literal substring anchor; insert AFTER the unique matching line (0 or >1 matches → refused)"),
    symbol: tool.schema.string().optional().describe(
      "definition-name anchor (.py def/class/async def; .ts/.js-family function/class/const); insert AFTER the unique definition line"),
    category: tool.schema.string().optional().describe(
      "lowercase token: gotcha|why|risk|xref|todo|... (enables `TA: <category>:` filtering)"),
  },
  async execute(args, context) {
    const rawPath = args?.path ?? ""
    const thought = args?.thought ?? ""
    const lineArg = args?.line
    const afterArg = args?.after
    const symbolArg = args?.symbol
    const category = args?.category
    if (!rawPath) return "❌ 'path' is required."
    if (!thought) return "❌ 'thought' is required."
    // B1: at most one addressing mode (none → EOF append, back-compat).
    const modes = [
      lineArg !== undefined && lineArg !== null ? "line" : null,
      afterArg !== undefined && afterArg !== null ? "after" : null,
      symbolArg !== undefined && symbolArg !== null ? "symbol" : null,
    ].filter(Boolean)
    if (modes.length > 1) {
      return `⛔ TA: refused — pass at most one of line, after, symbol (got ${modes.join("+")}).`
    }
    const rel = relOf(rawPath)
    if (isProtectedPath(rel)) {
      return `⛔ TA: refused — '${rel}' is protected (.env*, README.md, uv.lock, LICENSE).`
    }
    const ext = extname(rel)
    if (ext.toLowerCase() === ".json") {
      return `⛔ TA: refused — '.json' has no comments (would break parsing). Use .jsonc instead.`
    }
    const abs = toAbs(rel)
    if (!existsSync(abs)) {
      return `⛔ TA: refused — '${rel}' does not exist. (omt_think never creates files.)`
    }
    const newLine = buildThoughtLine(ext, category, thought)
    if (!newLine) {
      // A2: unknown extension → deny (F2: no unsafe default comment syntax).
      return `⛔ TA: refused — unsupported file type '${ext || "(none)"}'. ` +
        `Add an explicit mapping in commentSyntaxFor (omt_think.ts, feature_022) ` +
        `only if a real comment syntax exists.`
    }
    const content = readFileSync(abs, "utf8")
    // A4: preserve the file's own EOL style (F9: no mixed CRLF/LF endings).
    const eol = content.includes("\r\n") ? "\r\n" : "\n"
    const lines = content.split(/\r?\n/)
    // A4 dedup: refuse an identical (category, thought) pair already present.
    const normText = thought.replace(/\s+/g, " ").trim().replace(/^TA:\s*/i, "")
    const normCat = (category || "").trim().toLowerCase()
    for (let i = 0; i < lines.length; i++) {
      const p = parseThoughtLine(lines[i])
      if (p && p.cat === normCat && p.text === normText) {
        return `⛔ TA: refused — duplicate of existing thought at ${rel}:${i + 1}.`
      }
    }
    // If the file ends with a trailing newline, split produces a trailing "".
    // Insert the thought AFTER `line` (1-based), clamped to EOF.
    let insertAt: number
    // B1: anchor mode resolves to an insertion index carrying its anchor for
    // the index record (consumed later by E1 drift-repair), then flows through
    // the same pipeline as line mode (trailing-newline adjust → A3 → splice).
    let anchor: { kind: "after" | "symbol"; value: string } | null = null
    if ((afterArg !== undefined && afterArg !== null) || (symbolArg !== undefined && symbolArg !== null)) {
      const r = resolveAnchor(lines, ext, rel, afterArg, symbolArg)
      if (!r.ok) return r.err
      insertAt = r.insertAt
      anchor = r.anchor
    } else if (lineArg === undefined || lineArg === null) {
      insertAt = lines.length // append at very end
    } else {
      insertAt = Math.min(Math.max(1, Math.floor(lineArg)), lines.length)
    }
    // If there's a trailing "" from a final newline, insert before it.
    if (lines.length > 0 && lines[lines.length - 1] === "" && insertAt >= lines.length) {
      insertAt = lines.length - 1
    }
    // A3: never splice INTO a string literal / code fence (F1 class: broke
    // Textual CSS via a triple-quoted string in main_screen.py).
    if (inStringContext(lines, insertAt, ext)) {
      return `⛔ TA: refused — insertion point ${rel}:${insertAt + 1} lies inside a ` +
        `string/code-fence (F1 class: broke Textual CSS via triple-quoted string). ` +
        `Choose a line outside the literal.`
    }
    lines.splice(insertAt, 0, newLine)
    writeFileSync(abs, lines.join(eol), "utf8")
    const newLineNo = insertAt + 1 // 1-based line number of the inserted line
    appendIndex({ path: rel, line: newLineNo, category: normCat || null, thought: normText, anchor })
    return `✅ TA: ${normText} → ${rel}:${newLineNo}`
  },
})

// --- omt_think_list: retrieve thoughts (grep-backed, authoritative inline) --
const omt_think_list = tool({
  description:
    "List TA: thought-tags (feature_021). Grep-backed retrieval over inline tags " +
    "(the source of truth). Marks the session consulted, clearing the think-gate " +
    "for exactly the files the listing matched (feature_022 C2 per-file consult). " +
    "Also usable as plain `grep -rn \"TA:\" <path>`. Caps output at 50 lines.",
  args: {
    path: tool.schema.string().optional().describe("restrict to a file/dir (default: whole repo)"),
    category: tool.schema.string().optional().describe("filter `TA: <category>:`"),
    query: tool.schema.string().optional().describe("extra substring filter"),
  },
  async execute(args, context) {
    const session = context?.sessionID
    const pathArg = args?.path
    const category = args?.category
    const query = args?.query
    // A1: anchored base pattern (F3 prose false-positives). A4: category
    // lowercased; both filters regex-escaped before interpolation (F7).
    let pattern = THOUGHT_PATTERN
    const cat = category ? category.trim().toLowerCase() : ""
    if (cat) pattern += "\\s*" + escapeRegex(cat) + ":"
    if (query) pattern += ".*" + escapeRegex(query)
    const target = pathArg || "."
    const hits = grepThoughts(pattern, target)
    // Always record consult (clears the think-gate) — even on empty results.
    // C2: the record carries the consulted file set (what the agent was shown).
    const consultedFiles = [...new Set(hits.map(h => h.file))]
    recordConsult(session, consultedFiles)
    if (hits.length === 0) {
      return `0 thoughts${category ? ` matching category '${category}'` : ""}${query ? ` / query '${query}'` : ""}.\n` +
        `Add one with omt_think{path, thought}.`
    }
    const cap = 50
    const shown = hits.slice(0, cap)
    const rendered = shown.map(h => `${h.file}:${h.line}: ${h.content}`).join("\n")
    const fileCount = consultedFiles.length
    let out = `${rendered}\n\n${hits.length} thought${hits.length === 1 ? "" : "s"} across ${fileCount} file${fileCount === 1 ? "" : "s"}.`
    if (hits.length > cap) {
      out += ` … (+${hits.length - cap} more: omt_think_list{${category ? `category:"${category}"` : "path:\"<subdir>\""}})`
    }
    return out
  },
})

// --- omt_think_remove: remove a thought -------------------------------------
const omt_think_remove = tool({
  description:
    "Remove a TA: thought-tag line from a file (feature_021) and append a " +
    "remove-tombstone to the JSONL index (append-only, R6 S1: the index is " +
    "never rewritten; the latest-wins fold reads a tombstoned slot as absent).",
  args: {
    path: tool.schema.string().describe("target file"),
    line: tool.schema.number().describe("1-based line of the TA: comment to remove"),
  },
  async execute(args, context) {
    const rawPath = args?.path ?? ""
    const lineArg = args?.line
    if (!rawPath) return "❌ 'path' is required."
    if (lineArg === undefined || lineArg === null) return "❌ 'line' is required."
    const rel = relOf(rawPath)
    if (isProtectedPath(rel)) {
      return `⛔ TA: refused — '${rel}' is protected.`
    }
    const abs = toAbs(rel)
    if (!existsSync(abs)) {
      return `⛔ TA: refused — '${rel}' does not exist.`
    }
    const content = readFileSync(abs, "utf8")
    const lines = content.split("\n")
    const idx = Math.floor(lineArg) - 1
    if (idx < 0 || idx >= lines.length) {
      return `⛔ TA: refused — line ${lineArg} out of range (file has ${lines.length} lines).`
    }
    // A1: only real anchored thought lines are removable (prose mentions refused).
    if (!new RegExp(THOUGHT_PATTERN).test(lines[idx])) {
      return `⛔ TA: refused — line ${lineArg} is not a TA: comment:\n  ${lines[idx]}`
    }
    lines.splice(idx, 1)
    writeFileSync(abs, lines.join("\n"), "utf8")
    // R6 S1 append-only tombstone: the index is NEVER rewritten (the
    // reconcile-by-rewrite path was deleted — grep is truth, audit P8/F12).
    // The fold reads a tombstoned slot as absent; a re-added thought (newer
    // add-record) starts unverified — C1 semantics, zero rewrites.
    appendIndex({ kind: "remove", path: rel, line: Math.floor(lineArg) })
    return `🗑 removed TA: at ${rel}:${lineArg}`
  },
})

// --- omt_think_verify: structural placement-integrity check (feature_022 C1) -
// Re-checks that a thought exists where expected AND that its B1 anchor still
// resolves to it. STRUCTURAL, not semantic: never judges whether the thought's
// claim is still true (the agent's job at consult/read time). This is the
// RLVR-analogue feedback signal: drifted/detached thoughts are flagged stale
// instead of silently persisting as trustworthy.
const omt_think_verify = tool({
  description:
    "Re-check a TA: thought's placement integrity (feature_022 C1): existence at " +
    "the given line plus, when the index add-record carries an anchor, re-resolution " +
    "of that anchor (drift/ambiguity/removal → stale). Structural only — never judges " +
    "semantic truth. Appends a verified/stale record to the index (latest per " +
    "path:line wins); the digest + think-gate surface stale thoughts.",
  args: {
    path: tool.schema.string().describe("repo-relative file carrying the TA: comment"),
    line: tool.schema.number().describe("1-based line of the TA: comment to verify"),
  },
  async execute(args, context) {
    const rawPath = args?.path ?? ""
    const lineArg = args?.line
    if (!rawPath) return "❌ 'path' is required."
    if (lineArg === undefined || lineArg === null) return "❌ 'line' is required."
    const rel = relOf(rawPath)
    if (isProtectedPath(rel)) {
      return `⛔ TA: refused — '${rel}' is protected.`
    }
    const abs = toAbs(rel)
    if (!existsSync(abs)) {
      return `⛔ TA: refused — '${rel}' does not exist.`
    }
    const content = readFileSync(abs, "utf8")
    const lines = content.split(/\r?\n/)
    const lineNo = Math.floor(lineArg)
    const idx = lineNo - 1
    if (idx < 0 || idx >= lines.length) {
      return `⛔ TA: refused — line ${lineArg} out of range (file has ${lines.length} lines).`
    }
    if (!new RegExp(THOUGHT_PATTERN).test(lines[idx])) {
      return `⛔ TA: refused — line ${lineArg} is not a TA: comment:\n  ${lines[idx]}`
    }
    const parsed = parseThoughtLine(lines[idx])
    const text = parsed?.text || ""
    const cat = parsed?.cat || null
    // Index lookup over ALIVE add-records (R6 S1 fold: tombstoned slots read
    // as absent): latest add-record at (path,line); drift fallback: latest
    // add-record with (path, thought-text). Latest wins.
    const { aliveAdds } = foldThoughtEvents(readThoughtsIndex())
    const adds = aliveAdds.filter(r => r.path === rel)
    let rec = [...adds].reverse().find(r => r.line === lineNo)
    if (!rec) rec = [...adds].reverse().find(r => r.thought === text)
    let status: "verified" | "stale"
    let basis: "anchor" | "exists"
    let reason = ""
    if (rec?.anchor) {
      basis = "anchor"
      const r = resolveAnchor(lines, extname(rel), rel,
        rec.anchor.kind === "after" ? rec.anchor.value : null,
        rec.anchor.kind === "symbol" ? rec.anchor.value : null)
      if (r.ok && r.insertAt + 1 === lineNo) {
        status = "verified"
      } else {
        status = "stale"
        reason = r.ok
          ? `anchor moved (thought at ${lineNo}, anchor resolves to ${r.insertAt + 1})`
          : r.err.replace(/^⛔ TA: refused — /, "").replace(/\.$/, "")
      }
    } else {
      // No record or anchor:null → weaker verification: existence only.
      basis = "exists"
      status = "verified"
    }
    appendIndex({ kind: "verify", path: rel, line: lineNo, category: cat, thought: text, status, basis })
    if (status === "verified") {
      return basis === "anchor"
        ? `✅ TA: verified — ${rel}:${lineNo} (basis: anchor)`
        : `✅ TA: verified — ${rel}:${lineNo} (basis: exists — placement only, no anchor recorded)`
    }
    return `⚠️ TA: STALE — ${rel}:${lineNo} — ${reason}. ` +
      `Re-place with omt_think or remove with omt_think_remove.`
  },
})

// --- omt_think_suggest: AST-ranked insertion-site advisor (feature_022 B2) ---
// The paper's high-entropy position table as a MECHANICAL proxy (no model in
// the loop): rank candidate TA: sites by node type Assign>Return>Expr>If>
// AugAssign, tie-break source order. Real AST via `uv run python` (stdlib ast,
// same execFileSync class as grepThoughts — H3 safe); AST-walk is inherently
// string-safe (never yields lines inside string literals — composes with A3).
// Read-only advisor: no target writes, no index writes, no ledger records.
const SITE_RANK: Record<string, number> = { Assign: 1, Return: 2, Expr: 3, If: 4, AugAssign: 5 }
// keep in sync with the RANK map inside SUGGEST_PY_SCRIPT below
const SUGGEST_PY_SCRIPT =
  "import ast, json, sys\n" +
  'RANK = {"Assign": 1, "Return": 2, "Expr": 3, "If": 4, "AugAssign": 5}\n' +
  'tree = ast.parse(open(sys.argv[1], encoding="utf-8").read())\n' +
  'out = [{"line": n.lineno, "end": n.end_lineno, "kind": type(n).__name__}\n' +
  "       for n in ast.walk(tree)\n" +
  '       if type(n).__name__ in RANK and getattr(n, "lineno", None)]\n' +
  "print(json.dumps(out))\n"

const omt_think_suggest = tool({
  description:
    "Rank candidate TA: insertion sites in a .py file (feature_022 B2): AST-walk " +
    "ordered by the Think-Anywhere paper's table (Assign > Return > Expr > If > " +
    "AugAssign), source-order tie-break; sites already carrying a thought (±1 line) " +
    "are excluded. Read-only — suggests line/anchor targets for omt_think.",
  args: {
    path: tool.schema.string().describe("repo-relative .py file to analyze"),
    top: tool.schema.number().optional().describe("max sites returned (default 5, clamped 1..20)"),
  },
  async execute(args, context) {
    const rawPath = args?.path ?? ""
    if (!rawPath) return "❌ 'path' is required."
    const rel = relOf(rawPath)
    if (isProtectedPath(rel)) {
      return `⛔ TA: refused — '${rel}' is protected (.env*, README.md, uv.lock, LICENSE).`
    }
    const abs = toAbs(rel)
    if (!existsSync(abs)) {
      return `⛔ TA: refused — '${rel}' does not exist.`
    }
    const ext = extname(rel).toLowerCase()
    if (ext !== ".py") {
      return `⛔ TA: suggest refused — ranking is Python-AST-based (paper's table); got '${ext || "(none)"}'.`
    }
    const top = Math.min(20, Math.max(1, Math.floor(args?.top ?? 5)))
    const content = readFileSync(abs, "utf8")
    const lines = content.split(/\r?\n/)
    // AST extraction (fail-open refusal on any subprocess/parse failure).
    let sites: { line: number; end: number; kind: string }[]
    try {
      const out = execFileSync("uv", ["run", "--no-sync", "python", "-c", SUGGEST_PY_SCRIPT, abs],
        { encoding: "utf8", timeout: 60000, stdio: ["ignore", "pipe", "pipe"] })
      sites = JSON.parse(out.trim() || "[]")
    } catch (e: any) {
      const err = String(e?.stderr || e?.message || e).split("\n")
        .filter((l: string) => l.trim()).pop() || "unknown error"
      return `⛔ TA: suggest refused — '${rel}' is not parseable Python (${err.trim().slice(0, 120)}).`
    }
    // Rank: paper-table priority, then source order.
    const rankOf = (k: string) => SITE_RANK[k] ?? 99
    sites.sort((a, b) => rankOf(a.kind) - rankOf(b.kind) || a.line - b.line)
    // Coverage exclusion: a real thought line at site.line ± 1 covers the site.
    const thoughtAt = new Set<number>()
    const rx = new RegExp(THOUGHT_PATTERN)
    for (let i = 0; i < lines.length; i++) if (rx.test(lines[i])) thoughtAt.add(i + 1)
    const covered = sites.filter(s => thoughtAt.has(s.line - 1) || thoughtAt.has(s.line) || thoughtAt.has(s.line + 1))
    const open = sites.filter(s => !(thoughtAt.has(s.line - 1) || thoughtAt.has(s.line) || thoughtAt.has(s.line + 1)))
    const shown = open.slice(0, top)
    const preview = (no: number) => {
      const p = (lines[no - 1] || "").replace(/\s+/g, " ").trim()
      return p.length > 60 ? p.slice(0, 60) + "…" : p
    }
    if (shown.length === 0) {
      return `💡 TA: suggest — ${rel}: 0 candidate sites (${covered.length} covered). Nothing to suggest.`
    }
    const items = shown.map((s, i) =>
      ` ${i + 1}. L${s.line} ${s.kind} → insert after L${s.end}: \`${preview(s.line)}\``)
    return `💡 TA: suggest — ${rel}: ${shown.length} candidate site${shown.length === 1 ? "" : "s"}, ${covered.length} already covered.\n` +
      items.join("\n") +
      `\n→ omt_think{path:"${rel}", line:<end>, thought:"..."}  (or after:"<preview>" — unique-match caveat)`
  },
})

// (meta_harness_dsl R6 S1: omt_think_reindex DELETED — grep-is-truth made the
// reconcile/rewrite class redundant AND destructive-prone on an untracked,
// backup-less index; audit P8/F12. Append-only events + latest-wins fold
// deliver identical semantics — incl. C1 re-added-starts-unverified — with
// zero rewrites. thoughts.jsonl.bak snapshot retained for the historical record.)

// --- per-session digest (R6 S7 compact form) --------------------------------
// Compact by design (audit F32/C4: a conversation-resident injection is re-paid
// EVERY model turn — full texts × ~30 turns ≈ 10k tok/session). Counts +
// per-file counts + stale ⚠️ survive; full texts are re-injected point-of-use
// by D1 on file read and are one omt_think_list call away.
function thinkDigest(): string {
  const hits = grepThoughts(THOUGHT_PATTERN, ".")
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
    (stale.length ? `\n⚠️ ${stale.length} stale: ${stale.slice(0, 5).join(", ")}${stale.length > 5 ? " …" : ""} — re-check with omt_think_verify{path, line}.` : "")
  out += `\nFull texts: omt_think_list (auto-injected per thought-carrying file on read; think-gate applies).`
  return out
}

// feature_023 Tier 1c (kept as the R6 S3 FALLBACK): the digest rides the FIRST
// tool.execute.after per session (mutating output.output — the guaranteed
// agent-visible channel, headless or not). The inert "session.start" hook was
// DELETED in R6 (never dispatched: audited 1.18.3, re-verified 1.18.5; the
// official event list has no session.start). Moving the trigger to the
// documented `event` hook on session.created is DEFERRED — no agent-visible
// delivery channel from event hooks is verified on 1.18.5 headless (plan R6
// S3 hard GATE; fallback recorded in WORK.md). Process-lifetime Set, bounded
// by distinct sessionIDs; R2 moves it into enforcer session_state (S6).
const digestSessions = new Set<string>()

// Standalone opencode plugin (mirrors omt_nav.ts / omt_status.ts).
// NO named tool-object exports — opencode's loader requires every export to be a
// function (DEFECT-A safe). Only the default factory is exported.
// R1 (F2/F17): repo root = worktree ?? directory, injected into the shared lib
// before any hook runs (all lib path getters are lazy — see lib header).
export default async ({ directory, worktree }) => {
  initOmtShared(worktree ?? directory)
  return {
    tool: { omt_think, omt_think_list, omt_think_remove, omt_think_verify, omt_think_suggest },
    "tool.execute.after": async (input, output) => {
      // Tier 1c: append the TA digest to the FIRST tool result per session.
      // Fail-open — the digest never blocks tool results.
      try {
        const session = input?.sessionID || ""
        if (!digestSessions.has(session)) {
          digestSessions.add(session)
          if (typeof output?.output === "string") {
            output.output += "\n\n" + thinkDigest()
          }
        }
      } catch { /* fail-open */ }
    },
  }
}
// TA: xref: feature_022.meta_harness_think_anywhere_v2 FEATURE.md catalogs 13 flaws of this v1 (string-unaware insertion F1, unsafe # default F2, gate substring false-positives F3) + tiered fixes A-E — read before modifying
