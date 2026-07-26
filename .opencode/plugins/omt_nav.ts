// OMT++ Navigation Tool — structured navigation for META HARNESS documentation
// Provides grep-based navigation using SECTION:/XREF_/CMD_/ERR_/WRN_/QUICK_ tags
// Returns plain-string results (opencode ToolResult: string | {output:string}).

import { tool } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync } from "node:fs"
import { join, relative } from "node:path"
import { execFileSync } from "node:child_process"
// Single source (meta_harness_dsl R1): repo-root lives in the shared lib
// (root injected at plugin-init, F2/F17 — fixes the subdir-launch divergence).
import { initOmtShared, repoRoot } from "../lib/omt_shared"

// Core documentation files in the META HARNESS ecosystem. Computed per call
// (lazy: the shared lib's repo root is injected at plugin-init — module-level
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
// BRE by default, so `+` is literal there — see omt_list_sections for the
// BRE-safe one-or-more-`#` pattern (`^##* SECTION:`).
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
function runGrep(pattern: string, files: string[]): NavResult[] {
  const results: NavResult[] = []
  const existingFiles = files.filter(f => existsSync(join(repoRoot(), f)))

  if (existingFiles.length === 0) return results

  try {
    const absFiles = existingFiles.map(f => join(repoRoot(), f))
    const output = execFileSync("grep", ["-n", "--", pattern, ...absFiles], {
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

// --- omt_nav: Main navigation tool ---
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
const omt_nav = tool({
  description: "Navigate META HARNESS documentation using structured tags (SECTION:/XREF_/CMD_/ERR_/etc.). Returns structured results for agent consumption.",
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

    // Determine which files to search
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
  description: "List all SECTION: headers across META HARNESS documentation with file locations.",
  args: {
    file: tool.schema.string().optional().describe(
      "Optional: specific file to list sections from"),
  },
  async execute(args, context) {
    const file = args?.file
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
  description: "Resolve XREF_ cross-references to find related documentation sections.",
  args: {
    xref: tool.schema.string().describe(
      "Cross-reference ID (e.g., 'XREF_GUIDE', 'XREF_RULES')"),
  },
  async execute(args, context) {
    const xref = args?.xref ?? ""
    if (!xref) {
      return "'xref' is required (e.g., xref:'XREF_GUIDE')."
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
  description: "Get QUICK_ workflow patterns for common agent tasks.",
  args: {
    workflow: tool.schema.string().optional().describe(
      "Workflow name or keyword (e.g., 'START_MAJOR', 'TDD', 'DEBUG')"),
  },
  async execute(args, context) {
    const workflow = args?.workflow ?? ""
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

// Standalone opencode plugin. This file lives under .opencode/plugins/, so it
// must export a default plugin FUNCTION. opencode's plugin loader (sk/nk)
// iterates Object.values(module) and requires EACH export to be a function (or
// an object with a .server function). The tool objects below are NOT functions,
// so they must NOT be named-exported from this file — only the default export
// is allowed. Mirrors omt_status.ts lines 364-366.
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
export default async ({ directory, worktree }) => {
  initOmtShared(worktree ?? directory)
  return {
    tool: { omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref },
  }
}
