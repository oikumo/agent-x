// OMT++ KB Navigation Tool — structured nav for Application Knowledge Base
// Reads .meta/.omt/kb.index.jsonl (compiled by kb_compiler.py from
// .meta/doc/omt++/*.kb.omt). Mirrors omt_nav.ts pattern: ONE registered tool
// with op dispatch to four implementations (nav|list_sections|cross_ref|quick_ref).
//
// feature_kb_akb — README in .projects/meta/feature_kb_akb/PROJECT.md
//
// API (op):
//   nav(query,file?,tag_type?,include_context?) — full-text + tag search
//   list_sections(file?) — list all records for a source file (tier-filterable)
//   cross_ref(xref) — resolve a cross-reference id
//   quick_ref(workflow?) — find patterns by QUICK_ tag

import { tool } from "@opencode-ai/plugin"
import {
  initOmtShared, repoRoot, loadKbIndex, irToolDescription,
} from "../lib/omt_shared"

interface KbRecord {
  id: string
  kind: string
  tags: string[]
  text: string
  src: string
  line: number
  refs?: string[]
  tier: string
}

// --- record search primitives (index-only; no grep fallback) -----------------
function kbRecords(file?: string): KbRecord[] | null {
  const idx = loadKbIndex()
  if (!idx) return null
  const recs = idx.filter((r: any) =>
    r && typeof r.src === "string" && Array.isArray(r.tags) &&
    typeof r.text === "string" && typeof r.line === "number") as KbRecord[]
  return file ? recs.filter(r => r.src && r.src.includes(file)) : recs
}

function kbHay(r: KbRecord): string {
  return `${r.id} ${r.text} ${r.tags.join(" ")} ${r.tier}`.toLowerCase()
}

function kbQuery(recs: KbRecord[], query: string): KbRecord[] {
  const q = query.trim()
  if (!q) return []
  // Tag-queries: token ending in ":" or "_" → tag prefix match
  if (/[:_]$/.test(q)) {
    const prefix = q.replace(/[:_]+$/, "").toUpperCase()
    const byTag = recs.filter(r => r.tags.some(t => t.startsWith(prefix)))
    if (byTag.length) return byTag
  }
  const needle = q.toLowerCase()
  return recs.filter(r => kbHay(r).includes(needle))
}

// --- tools -------------------------------------------------------------------
function createKbNavTools() {
  // --- omt_kb_nav_query ---
  const omt_kb_nav_query = tool({
    description: "Query Application Knowledge Base index by tag-prefix or keyword.",
    args: {
      query: tool.schema.string().describe(
        "Search query: tag prefix (e.g. 'ARCH_', 'TIER_CORE') or keyword"),
      file: tool.schema.string().optional().describe(
        "Optional: restrict to records from one source file"),
      tag_type: tool.schema.string().optional().describe(
        "Optional: TIER_CORE|TIER_EXTENDED|TIER_REFERENCE|all"),
      include_context: tool.schema.boolean().optional().describe(
        "Include full record text (default: id+line+text+tags)"),
    },
    async execute(args, context) {
      const query = args?.query ?? ""
      const file = args?.file
      const tag_type = args?.tag_type ?? "all"
      const include_context = args?.include_context === true

      if (!query) {
        return "'query' is required (e.g., query:'ARCH_', query:'boot', query:'TIER_CORE')."
      }

      const recs = kbRecords(file)
      if (!recs) {
        return "No KB index found — run kb_compiler.py build first."
      }

      let pool = recs
      if (tag_type !== "all") {
        const tt = tag_type.replace(/[:_]+$/, "").toUpperCase()
        pool = pool.filter(r => r.tags.some(t => t === tt || t.startsWith(tt + "_")))
      }

      const hits = kbQuery(pool, query)
      if (hits.length === 0) {
        return `No KB results for "${query}". Try: ARCH_, TIER_CORE, FEAT_, FLOW_, EXT_, SUBSYS_, PERSIST_`
      }

      if (include_context) {
        return hits
          .map(r => `${r.id} (${r.tier}) [${r.kind}] : ${r.text}` + (r.refs?.length ? ` →${r.refs.join(",")}` : "" ))
          .join("\n\n")
      }

      return hits.map(r => `${r.id}: ${r.text}`).join("\n")
    },
  })

  // --- omt_kb_list_sections ---
  const omt_kb_list_sections = tool({
    description: "List all KB records, optionally filtered by file or tier.",
    args: {
      file: tool.schema.string().optional().describe(
        "Optional: restrict to one source file"),
    },
    async execute(args, context) {
      const file = args?.file
      const recs = kbRecords(file)
      if (!recs) {
        return "No KB index found — run kb_compiler.py build first."
      }
      // Tier order: core > extended > reference
      const tierOrd: Record<string, number> = { core: 0, extended: 1, reference: 2 }
      const sorted = [...recs].sort((a, b) => (tierOrd[a.tier] ?? 9) - (tierOrd[b.tier] ?? 9))
      return sorted.map(r => `${r.tier}: ${r.id}  [${r.tags.join(", ")}]`).join("\n")
    },
  })

  // --- omt_kb_cross_ref ---
  const omt_kb_cross_ref = tool({
    description: "Resolve cross-references in the KB index.",
    args: {
      xref: tool.schema.string().describe(
        "Cross-reference ID or keyword (e.g., 'doc.mvcpp', 'XREF')"),
    },
    async execute(args, context) {
      const xref = args?.xref ?? ""
      if (!xref) {
        return "'xref' is required (e.g., xref:'ARCH_MVCPP', xref:'doc.mvcpp')."
      }
      const recs = kbRecords()
      if (!recs) {
        return "No KB index found — run kb_compiler.py build first."
      }
      // Match by id, by tags containing the xref, or by the xref keyword in text
      const hits = recs.filter(r =>
        r.id === xref ||
        r.tags.some(t => t.includes(xref.toUpperCase()) || t.includes(xref)) ||
        r.text.toLowerCase().includes(xref.toLowerCase())
      )
      return hits.length
        ? hits.map(r => `${r.id} (${r.tier}): ${r.text}`).join("\n")
        : `No references for "${xref}".`
    },
  })

  // --- omt_kb_quick_ref ---
  const omt_kb_quick_ref = tool({
    description: "Get quick KB patterns by tag/subject.",
    args: {
      workflow: tool.schema.string().optional().describe(
        "Tag or keyword (e.g., 'ARCH_', 'TIER_CORE', 'FLOW_')"),
    },
    async execute(args, context) {
      const workflow = args?.workflow ?? ""
      const recs = kbRecords()
      if (!recs) {
        return "No KB index found — run kb_compiler.py build first."
      }
      let pool = recs
      if (workflow) {
        const needle = workflow.toLowerCase()
        pool = pool.filter(r => kbHay(r).includes(needle))
      } else {
        // Default: show only TIER_CORE records
        pool = pool.filter(r => r.tags.some(t => t.startsWith("TIER_CORE")))
      }
      return pool.length
        ? pool.map(r => `${r.id} (${r.tier}): ${r.text}`).join("\n")
        : `No patterns${workflow ? ` for "${workflow}"` : ""}. Try: TIER_CORE, ARCH_, FLOW_`
    },
  })

  // ONE registered tool; op dispatches to the impls above.
  const omt_kb_nav = tool({
    description: irToolDescription("omt_kb_nav", "App Knowledge Base nav. op=nav(query,file?,tag_type?,include_context?) | list_sections(file?) | cross_ref(xref) | quick_ref(workflow?)."),
    args: {
      op: tool.schema.string().describe("nav|list_sections|cross_ref|quick_ref"),
      query: tool.schema.string().optional().describe("nav: tag prefix ('ARCH_', 'TIER_CORE') or keyword"),
      file: tool.schema.string().optional().describe("nav/list_sections: restrict to one source file"),
      tag_type: tool.schema.string().optional().describe("nav: TIER_CORE|TIER_EXTENDED|TIER_REFERENCE|all"),
      include_context: tool.schema.boolean().optional().describe("nav: include full record text (default: false)"),
      xref: tool.schema.string().optional().describe("cross_ref: e.g. 'doc.mvcpp'"),
      workflow: tool.schema.string().optional().describe("quick_ref: e.g. 'TIER_CORE', 'ARCH_'"),
    },
    async execute(args, context) {
      switch (args?.op ?? "nav") {
        case "nav": return omt_kb_nav_query.execute(args, context)
        case "list_sections": return omt_kb_list_sections.execute(args, context)
        case "cross_ref": return omt_kb_cross_ref.execute(args, context)
        case "quick_ref": return omt_kb_quick_ref.execute(args, context)
        default: return `⚠️ omt_kb_nav: unknown op '${args?.op}' — want nav|list_sections|cross_ref|quick_ref`
      }
    },
  })

  return { omt_kb_nav }
}

export default async ({ directory, worktree }) => {
  initOmtShared(worktree ?? directory)
  const { omt_kb_nav } = createKbNavTools()
  return {
    tool: { omt_kb_nav },
  }
}