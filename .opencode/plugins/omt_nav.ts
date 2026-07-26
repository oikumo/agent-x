// OMT++ Navigation Tool — structured navigation for META HARNESS documentation
// Provides navigation using SECTION:/XREF_/CMD_/ERR_/WRN_/QUICK_ tags.
// Returns plain-string results (opencode ToolResult: string | {output:string}).
//
// meta_harness_dsl R8 (OMT-HDL-1): answers come from the COMPILED nav index
// (.meta/.omt/nav.index.jsonl via loadNavIndex) whenever the projection
// exists; the grep path is kept verbatim as the fallback for a missing/empty
// index. Tool descriptions resolve from the compiled IR (irToolDescription),
// so the tools are built inside createNavTools() AFTER initOmtShared ran (a
// module-level tool() would read the IR under the pre-init cwd — F2/F17).

import { tool } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync } from "node:fs"
import { join, relative } from "node:path"
import { execFileSync } from "node:child_process"
// Single source (meta_harness_dsl R1): repo-root lives in the shared lib
// (root injected at plugin-init, F2/F17 — fixes the subdir-launch divergence).
// R8: IR tool descriptions + the compiled nav index come from there too.
import { initOmtShared, repoRoot, irToolDescription, loadNavIndex } from "../lib/omt_shared"

// Core documentation files in the META HARNESS ecosystem — the LEGACY corpus
// searched by the grep fallback (the compiled index already covers these via
// its legacy-scraped records plus the .omt source). Computed per call (lazy:
// the shared lib's repo root is injected at plugin-init — module-level
// constants would capture the pre-init cwd). Auto-discovers
// .meta/doc/omt++/*.md so newly added docs are covered without editing this
// list. Sorted for deterministic output.
function metaFiles(): string[] {
  const omtPpDir = join(repoRoot(), ".meta", "doc", "omt++")
  const omtPpFiles: string[] = existsSync(omtPpDir)
    ? readdirSync(omtPpDir).filter(f => f.endsWith(".md")).sort().map(f => `.meta/doc/omt++/${f}`)
    : []
  return [
    ".meta/META_HARNESS.md",
    ".meta/META.md",
    ".meta/software_development_process/META.md",
    ".meta/software_development_process/omt_agent_guide.md",
    ...omtPpFiles,
    "AGENTS.md",
    "WORK.md",
  ]
}

// Tag patterns for structured navigation.
// NOTE: these validate the `tag_type` input and document the canonical tag
// shapes. The actual grep patterns are built per-tool in runGrep(); grep uses
// BRE by default, so `+` is literal there — see the grep fallback of
// omt_list_sections for the BRE-safe one-or-more-`#` pattern (`^##* SECTION:`).
const TAG_PATTERNS = {
  SECTION: /^#+ SECTION:/m,
  RULE_: /^RULE_[A-Z0-9]+:/m,
  ERR_: /^ERR_[A-Z0-9]+:/m,
  WRN_: /^WRN_[A-Z0-9]+:/m,
  CMD_: /^CMD_[A-Z0-9]+:/m,
  QUICK_: /^QUICK_[A-Z0-9_]+:/m,
  XREF_: /^XREF_[A-Z0-9_]+:/m,
  TT_: /^TT_[A-Z0-9_]+:/m,
  PHASE_: /^PHASE_[A-Z0-9_]+:/m,
  FEAT_: /^FEAT_[A-Z0-9_]+:/m,
}

interface NavResult {
  file: string
  line: number
  content: string
  context?: string
}

// Execute grep command and parse results.
// Uses execFileSync with array argv (no shell) so the pattern is passed as a
// literal argument — no shell injection and no quoting breakage. grep still
// interprets the pattern as a BRE regex, which is intentional for tag nav.
// R8: -H forces the `file:` prefix even for a single-file search — without it
// grep omits the prefix and the file:line:content parser below matched
// nothing, so an explicit `file` arg always returned empty (WORK.md R1 OPEN
// finding, fixed here).
function runGrep(pattern: string, files: string[]): NavResult[] {
  const results: NavResult[] = []
  const existingFiles = files.filter(f => existsSync(join(repoRoot(), f)))

  if (existingFiles.length === 0) return results

  try {
    const absFiles = existingFiles.map(f => join(repoRoot(), f))
    const output = execFileSync("grep", ["-nH", "--", pattern, ...absFiles], {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "ignore"],
    })

    for (const line of output.trim().split("\n")) {
      if (!line) continue
      // Parse grep output: file:line:content
      // Non-greedy file group binds to the first :<digits>: (the real line
      // number), so colons/digits inside content don't misparse.
      const match = line.match(/^(.+?):(\d+):(.*)$/)
      if (match) {
        const [, file, lineNum, content] = match
        const relPath = relative(repoRoot(), file)
        results.push({
          file: relPath,
          line: parseInt(lineNum, 10),
          content: content.trim(),
        })
      }
    }
  } catch {
    // grep returns non-zero when no matches, which is fine
  }

  return results
}

// Get context around a match (3 lines before and after)
function getContext(filePath: string, lineNum: number, contextLines: number = 3): string {
  const fullPath = join(repoRoot(), filePath)
  if (!existsSync(fullPath)) return ""

  try {
    const content = readFileSync(fullPath, "utf8")
    const lines = content.split("\n")
    const start = Math.max(0, lineNum - 1 - contextLines)
    const end = Math.min(lines.length, lineNum - 1 + contextLines + 1)
    return lines.slice(start, end).join("\n")
  } catch {
    return ""
  }
}

// Render grep hits as "file:line: content" lines — the simplest opencode
// ToolResult is a plain string (mirrors omt_enforcer.ts tools like omt_phase).
function render(results: NavResult[]): string {
  return results.map(r => `${r.file}:${r.line}: ${r.content}`).join("\n")
}

// --- compiled nav index (meta_harness_dsl R8 / OMT-HDL-1) -------------------
// Record shapes: {id,kind,tags[],text,src,line} (+`name` on legacy scraped
// lines). Kinds: doc/flow/xref/tool compiled from .meta/META_HARNESS.omt; msg
// err_*/wrn_* records get uppercased rid tags (ERR_V2M); legacy scraped lines
// keep {id:"legacy:<rel>:<n>",kind:"legacy",tags:["SECTION"],name:"SECTION:X"}.
interface NavRecord {
  id: string
  kind: string
  tags: string[]
  text: string
  src: string
  line: number
  name?: string
}

// The index records, or null when the projection is missing/empty (→ callers
// take the legacy grep path unchanged). `file` restricts to one source doc
// (the omt_nav / omt_list_sections file arg).
function navRecords(file?: string): NavRecord[] | null {
  const idx = loadNavIndex()
  if (!idx) return null
  const recs = idx.filter((r: any) =>
    r && typeof r.src === "string" && Array.isArray(r.tags) &&
    typeof r.text === "string" && typeof r.line === "number") as NavRecord[]
  return file ? recs.filter(r => r.src === file) : recs
}

// Substring haystack: every searchable surface of a record.
function navHay(r: NavRecord): string {
  return `${r.id} ${r.name || ""} ${r.text} ${r.tags.join(" ")}`.toLowerCase()
}

// Query semantics for omt_nav over the index: a tag-shaped query (ends ":" or
// "_") tries tag-prefix first, then falls back to a substring scan; anything
// else is a plain substring scan.
function navQuery(recs: NavRecord[], query: string): NavRecord[] {
  const q = query.trim()
  if (!q) return []
  if (/[:_]$/.test(q)) {
    const prefix = q.replace(/[:_]+$/, "").toUpperCase()
    const byTag = recs.filter(r => r.tags.some(t => t.startsWith(prefix)))
    if (byTag.length) return byTag
  }
  const needle = q.toLowerCase()
  return recs.filter(r => navHay(r).includes(needle))
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

// --- the four nav tools (built post-init — see the factory) ------------------
// API notes:
//  DEFECT C (fixed): use `args`/`tool.schema` + execute(args, context), NOT
//    raw JSON-schema `input:{type,properties}` (opencode ignores `input` and
//    registers the tool with no params -> real calls crash on undefined args).
//  DEFECT D (fixed): execute() must return a plain string (or {output:string}).
//    Returning a raw object {results,...} with no `output` field crashes
//    opencode: it reads `result.output` (undefined) and .split()s it ->
//    "undefined is not an object (evaluating 'u.split')". The function-level
//    tests (via _nav_runner.mjs calling execute() directly + JSON.stringify)
//    never crossed opencode's ToolResult boundary, so this was invisible.
function createNavTools() {
  // --- omt_nav: Main navigation tool ---
  const omt_nav = tool({
    description: irToolDescription("omt_nav",
      "Navigate META HARNESS documentation using structured tags (SECTION:/XREF_/CMD_/ERR_/etc.). Returns structured results for agent consumption."),
    args: {
      query: tool.schema.string().describe(
        "Search query: tag prefix (e.g., 'SECTION:', 'CMD_', 'ERR_') or keyword"),
      file: tool.schema.string().optional().describe(
        "Optional: specific file to search (e.g., '.meta/META_HARNESS.md')"),
      tag_type: tool.schema.string().optional().describe(
        "Optional: restrict to specific tag type (SECTION, RULE, ERR, WRN, CMD, QUICK, XREF, TT, PHASE, FEAT, all)"),
      include_context: tool.schema.boolean().optional().describe(
        "Include surrounding context for each match (default: false)"),
    },
    async execute(args, context) {
      const query = args?.query ?? ""
      const file = args?.file
      const tag_type = args?.tag_type ?? "all"
      const include_context = args?.include_context === true

      if (!query) {
        return "'query' is required (e.g., query:'SECTION:', query:'CMD_')."
      }

      // R8: answer from the compiled index when present.
      const recs = navRecords(file)
      if (recs) {
        let pool = recs
        if (tag_type !== "all") {
          const tt = tag_type.replace(/[:_]+$/, "").toUpperCase()
          pool = pool.filter(r => r.tags.some(t => t === tt || t.startsWith(tt + "_")))
        }
        const hits = navQuery(pool, query)
        if (hits.length === 0) {
          return `No results for "${query}". Try: SECTION:, CMD_, ERR_, QUICK_, XREF_`
        }
        if (include_context) {
          return hits
            .map(r => `${r.src}:${r.line}: ${r.text}` + (getContext(r.src, r.line) ? `\n${getContext(r.src, r.line)}` : ""))
            .join("\n\n")
        }
        return hits.map(r => `${r.src}:${r.line}: ${r.text}`).join("\n")
      }

      // Legacy grep fallback (no compiled index on disk).
      const filesToSearch = file ? [file] : metaFiles().filter(f => existsSync(join(repoRoot(), f)))

      // Build grep pattern based on tag type
      let pattern = query
      if (tag_type !== "all" && TAG_PATTERNS[tag_type as keyof typeof TAG_PATTERNS]) {
        // If query looks like a tag, use it as-is; otherwise prepend tag prefix
        if (!query.startsWith(tag_type)) {
          pattern = `${tag_type}_.*${query}`
        }
      }

      // Run grep search
      const rawResults = runGrep(pattern, filesToSearch)

      // Enrich results with context if requested
      const results: NavResult[] = rawResults.map(r => ({
        ...r,
        ...(include_context ? { context: getContext(r.file, r.line) } : {}),
      }))

      if (results.length === 0) {
        return `No results for "${query}". Try: SECTION:, CMD_, ERR_, QUICK_, XREF_`
      }

      // With context, append the context block under each hit.
      if (include_context) {
        return results.map(r => `${r.file}:${r.line}: ${r.content}` + (r.context ? `\n${r.context}` : "")).join("\n\n")
      }
      return render(results)
    },
  })

  // --- omt_list_sections: List all SECTION: headers across META HARNESS ---
  const omt_list_sections = tool({
    description: irToolDescription("omt_list_sections",
      "List all SECTION: headers across META HARNESS documentation with file locations."),
    args: {
      file: tool.schema.string().optional().describe(
        "Optional: specific file to list sections from"),
    },
    async execute(args, context) {
      const file = args?.file

      // R8: answer from the compiled index when present.
      const recs = navRecords(file)
      if (recs) {
        return recs
          .filter(r => r.tags.includes("SECTION"))
          .map(r => `${r.src}:${r.line}: ${r.text.replace(/^#+ SECTION:\s*/, "").trim()}`)
          .join("\n")
      }

      const filesToSearch = file ? [file] : metaFiles()

      // BRE-safe "one or more leading '#'": `##*` = first '#' literal, then
      // zero-or-more '#' (i.e. one-or-more '#'). Matches the `# SECTION:` style
      // used across META HARNESS docs. (`^##+` would be wrong in BRE: `+` is
      // literal there, and even in ERE `##+` requires two-or-more '#'.)
      const rawResults = runGrep("^##* SECTION:", filesToSearch)

      const sections = rawResults.map(r => ({
        file: r.file,
        line: r.line,
        title: r.content.replace(/^#+ SECTION:\s*/, "").trim(),
      }))

      return sections.map(s => `${s.file}:${s.line}: ${s.title}`).join("\n")
    },
  })

  // --- omt_cross_ref: Resolve cross-references ---
  const omt_cross_ref = tool({
    description: irToolDescription("omt_cross_ref",
      "Resolve XREF_ cross-references to find related documentation sections."),
    args: {
      xref: tool.schema.string().describe(
        "Cross-reference ID (e.g., 'XREF_GUIDE', 'XREF_RULES')"),
    },
    async execute(args, context) {
      const xref = args?.xref ?? ""
      if (!xref) {
        return "'xref' is required (e.g., xref:'XREF_GUIDE')."
      }

      // R8: answer from the compiled index when present — tags match the xref
      // id exactly, or the XREF_.*<xref> regex for a bare suffix.
      const recs = navRecords()
      if (recs) {
        const bare = xref.startsWith("XREF_") ? null : new RegExp(`^XREF_.*${escapeRegExp(xref)}`)
        const hits = recs.filter(r => r.tags.some(t => t === xref || (bare ? bare.test(t) : false)))
        return hits.length
          ? hits.map(r => `${r.src}:${r.line}: ${r.text}`).join("\n")
          : `No references for "${xref}".`
      }

      const pattern = xref.startsWith("XREF_") ? xref : `XREF_.*${xref}`
      const results = runGrep(pattern, metaFiles())
      return results.length
        ? render(results)
        : `No references for "${xref}".`
    },
  })

  // --- omt_quick_ref: Get quick workflow patterns ---
  const omt_quick_ref = tool({
    description: irToolDescription("omt_quick_ref",
      "Get QUICK_ workflow patterns for common agent tasks."),
    args: {
      workflow: tool.schema.string().optional().describe(
        "Workflow name or keyword (e.g., 'START_MAJOR', 'TDD', 'DEBUG')"),
    },
    async execute(args, context) {
      const workflow = args?.workflow ?? ""

      // R8: answer from the compiled index when present — flow records carry
      // QUICK_* tags; legacy scraped lines carry the QUICK_ name in `name`.
      const recs = navRecords()
      if (recs) {
        let hits = recs.filter(r =>
          r.tags.some(t => t.startsWith("QUICK_")) || (r.name || "").startsWith("QUICK_"))
        if (workflow) {
          const needle = workflow.toLowerCase()
          hits = hits.filter(r => navHay(r).includes(needle))
        }
        const workflows = hits.map(r => {
          const m = r.text.match(/^(QUICK_[A-Z0-9_]+):\s*(.+)$/)
          const name = m ? m[1]
            : (r.tags.find(t => t.startsWith("QUICK_")) || r.name || "QUICK_UNKNOWN")
          const pattern = m ? m[2] : r.text
          return `${name}: ${pattern}  (${r.src}:${r.line})`
        })
        return workflows.length
          ? workflows.join("\n")
          : `No workflows${workflow ? ` matching "${workflow}"` : ""}.`
      }

      const pattern = workflow ? `QUICK_.*${workflow}` : "^QUICK_"
      const results = runGrep(pattern, metaFiles())

      const workflows = results.map(r => {
        const match = r.content.match(/^(QUICK_[A-Z0-9_]+):\s*(.+)$/)
        return {
          name: match ? match[1] : "QUICK_UNKNOWN",
          pattern: match ? match[2] : r.content,
          file: r.file,
          line: r.line,
        }
      })

      return workflows.length
        ? workflows.map(w => `${w.name}: ${w.pattern}  (${w.file}:${w.line})`).join("\n")
        : `No workflows${workflow ? ` matching "${workflow}"` : ""}.`
    },
  })

  return { omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref }
}

// Standalone opencode plugin. This file lives under .opencode/plugins/, so it
// must export a default plugin FUNCTION. opencode's plugin loader (sk/nk)
// iterates Object.values(module) and requires EACH export to be a function (or
// an object with a .server function). The tool objects below are NOT functions,
// so they must NOT be named-exported from this file — only the default export
// is allowed. Mirrors omt_status.ts.
//
// (DEFECT A, prior: named tool-object export only -> "Plugin export is not a
//  function", tools never registered. Fixed by the default factory below.)
// (DEFECT C, prior: `input:{type,properties}` instead of `args`/`tool.schema`
//  -> tools registered with no params -> real calls crashed on undefined args.)
// (DEFECT D, prior: tools returned raw objects {results,...} with no `output`
//  string -> opencode reads result.output (undefined) and .split()s it ->
//  "undefined is not an object (evaluating 'u.split')". Fixed by returning
//  plain strings, the simplest ToolResult (mirrors omt_enforcer.ts tools).)
// R1 (F2/F17): repo root = worktree ?? directory, injected into the shared lib
// before any hook runs (all lib path getters are lazy — see lib header).
// R8: tools build post-init (createNavTools) so descriptions read the IR under
// the injected root.
export default async ({ directory, worktree }) => {
  initOmtShared(worktree ?? directory)
  const { omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref } = createNavTools()
  return {
    tool: { omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref },
  }
}
