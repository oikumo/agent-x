# AKB Operations Specification

> ⚠️ **SUPERSEDED (2026-08-02, sess 7)** by `.projects/meta/feature_kb_akb/PROJECT.md` v2. Kept for history. Drift: budget 32000 vs removed (index unbounded); `tag_type` filters kind vs TIER; record schema id `<file>.<tag>` vs `kind.rid`; pre-source-code-primary scope. Do NOT use as current spec — read PROJECT.md v2.

> Machine-readable operation contracts for Application Knowledge Base.

---

## op:compile

**Input:** `.meta/doc/omt++/*.kb.omt`  
**Output:** `.meta/.omt/kb.index.jsonl`, `.meta/.omt/kb.ir.json`  
**Errors:** Style violations, unresolved refs, budget exceed, duplicate IDs

```bash
uv run scripts/omt/kb_compiler.py build
```

**Verify:**
```bash
uv run scripts/omt/kb_compiler.py check --verify-projections
```

---

## op:query

**Tool:** `omt_kb_nav`  
**Args:** `{op, query?, file?, tag_type?, include_context?, xref?, workflow?}`  
**Returns:** `{records: KBRecord[], total: int, truncated: bool}`

### op=nav
```json
{"op": "nav", "query": "ARCH_", "tag_type": "ARCH", "include_context": false}
```
Matches `tags` array (prefix or exact). `tag_type` filters `kind` prefix.

### op=list_sections
```json
{"op": "list_sections", "file": "architecture"}
```
Lists unique `tags` from records with `src` containing file name.

### op=cross_ref
```json
{"op": "cross_ref", "xref": "XREF_ARCH_MVCPP"}
```
Returns record with matching `id` or `tags` containing xref.

### op=quick_ref
```json
{"op": "quick_ref", "workflow": "MVCPP_RULES"}
```
Pre-defined workflow → curated record set.

---

## op:consult

**Side-effect:** Records consultation in ledger.  
**Trigger:** Any successful `omt_kb_nav` call.  
**Ledger entry:**
```json
{"ts": "2026-08-02T...", "kind": "kb_consult", "session": "...", "query": "ARCH_", "records_returned": 7}
```

Clears `session_flag(kb_consulted)` → unblocks `g.kb` gate.

---

## op:validate_style

**Runs at compile.** Checks each record `text`:
- `len(text) ≤ 300`
- No stopwords: `the|a|an|is|are|was|were|must|should|will|would|could|may|might|shall|can|need|require|ensure|verify|confirm`
- Symbol density: `symbol_count / word_count ≥ 0.3`
- Required tags per `kind`:
  - `doc`: ≥1 domain tag (`ARCH_`, `FLOW_`, `FEAT_`, `PAT_`)
  - `flow`: ≥1 `FLOW_` tag
  - `feature`: ≥1 `FEAT_` tag
  - `pattern`: ≥1 `PAT_` tag
  - `xref`: ≥1 `XREF_` tag
  - `gotcha`: ≥1 `GOTCHA_` tag

---

## op:gate_check

**Gate:** `g.kb` (in `META_HARNESS.omt`)  
**Condition:** `session_flag(kb_consulted) == true`  
**Tools:** `@var.edit_tools` (edit, write, patch, multiedit)  
**Paths:** `src/**`  
**Message:** `@msg.kb_required`  
**Hard:** true, **Skip:** false, **Order:** 5

---

## op:bootstrap_inject

**Inject:** `kb_bootstrap`  
**Trigger:** `first_tool_result`  
**Budget:** 1024 bytes  
**Content:** `"AKB: omt_kb_nav{op:list} → core tiers (ARCH_, FLOW_, FEAT_) — consult before edits"`

---

## op:budget_check

**Budget:** `@budget kb_index max=32000`  
**Enforced at:** `kb_compiler.py build`  
**Error:** `KB_INDEX_BUDGET_EXCEEDED: 35241 > 32000`

---

## Record Schema (KBRecord)

```typescript
interface KBRecord {
  id: string;                    // "<file>.<tag>" e.g. "architecture.mvcpp"
  kind: "doc" | "flow" | "feature" | "pattern" | "xref" | "gotcha";
  line: number;                  // source line
  src: string;                   // ".meta/doc/omt++/architecture.kb.omt"
  tags: string[];                // ["ARCH_MVCPP", "MVCPP", "CORE"]
  text: string;                  // compact non-human (≤300 chars)
  refs: string[];                // ["arch.partner", "flow.boot"]
  tier: "core" | "extended" | "reference";
}
```

---

## Tag Taxonomy

| Prefix | Domain | Example |
|--------|--------|---------|
| `ARCH_` | Architecture | `ARCH_MVCPP`, `ARCH_PARTNER`, `ARCH_DP` |
| `FLOW_` | Data Flow | `FLOW_BOOT`, `FLOW_AGENT_CYCLE`, `FLOW_NAV`, `FLOW_CHAT`, `FLOW_RAG`, `FLOW_SESSION`, `FLOW_PERSIST` |
| `FEAT_` | Features | `FEAT_CATALOG`, `FEAT_F006`, `FEAT_F020` |
| `PAT_` | Patterns | `PAT_DP`, `PAT_COMMAND`, `PAT_PROVIDER`, `PAT_FAST_AGENT` |
| `XREF_` | Cross-refs | `XREF_ARCH_MVCPP`, `XREF_FLOW_BOOT` |
| `GOTCHA_` | Gotchas | `GOTCHA_RECEIPT_ROUND_ROBIN`, `GOTCHA_TDD_NODE` |
| `TIER_` | Tier | `TIER_CORE`, `TIER_EXTENDED`, `TIER_REFERENCE` |

---

## Workflow Quick Refs

| Workflow | Query | Returns |
|----------|-------|---------|
| `MVCPP_RULES` | `ARCH_MVCPP` | MVC++ hard rules + warnings |
| `PARTNER_PATTERN` | `ARCH_PARTNER` | Abstract Partner + Console/TUI |
| `BOOT_SEQUENCE` | `FLOW_BOOT` | main.py → AppModel → MainScreen |
| `AGENT_CYCLE` | `FLOW_AGENT_CYCLE` | perceive→decide→act→observe |
| `SCREEN_NAV` | `FLOW_NAV` | TUI screen stack + transitions |
| `CHAT_STREAM` | `FLOW_CHAT` | Streaming via IUIProvider |
| `RAG_PIPELINE` | `FLOW_RAG` | Ingest → embed → query → rerank |
| `ADD_SCREEN` | `PAT_SCREEN` | MVC++ triad scaffold |
| `ADD_COMMAND` | `PAT_COMMAND` | CommandRegistry + handler |
| `ADD_TOOL` | `PAT_TOOL` | Agent tool registration |