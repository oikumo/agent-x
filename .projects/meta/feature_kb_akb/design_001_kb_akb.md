# AKB Design — Application Knowledge Base

> ⚠️ **SUPERSEDED (2026-08-02, sess 7)** by `.projects/meta/feature_kb_akb/PROJECT.md` v2. Kept for history. Drift: id `<file>.<tag>` vs `kind.rid`; budget 32000 vs removed (index unbounded); `tag_type` filters kind vs TIER; pure-AST assumption vs hybrid AST+curated. Do NOT use as current spec — read PROJECT.md v2.

> Single-source compile-time index for agentx concept docs. Mirrors meta-harness OMT-HDL pipeline. Mandatory agent consultation via enforced gate.

---

## 1. Problem

Current state:
- Agentx concepts split across `.meta/doc/omt++/*.md` (architecture, data_flow, features, extending, subsystems, persistence)
- Legacy `# SECTION:` tags scraped at build but **no compiled index**, **no query tool**, **no consultation gate**
- Agents grep/glob raw markdown → token waste, drift, missed context

Required:
- **Compile-time index** (JSONL, machine-optimal)
- **Query tool** (`omt_kb_nav`) answering from index
- **Mandatory consultation gate** (like `g.nav` for meta-harness)
- **Non-human language style** (compact, structured, token-efficient)
- **Single source of truth** (source `.omt` or structured markdown → compiler → index)

---

## 2. Architecture

```
.meta/doc/omt++/*.md (source)
       │
       ▼
scripts/omt/kb_compiler.py (NEW)
       │
       ├─► .meta/.omt/kb.index.jsonl     (compiled index — query target)
       ├─► .meta/.omt/kb.ir.json         (internal representation — plugins)
       └─► AGENTS.md projection (kb pointers only, ≤256B)
```

### 2.1 Source Format: `.kb.omt` (preferred) OR Structured Markdown

**Option A — Native `.kb.omt` (OMT-HDL subset):**
```omt
@version kb_hdl n=1
@var kb_paths : .meta/doc/omt++
@var kb_index : .meta/.omt/kb.index.jsonl

@doc arch.mvcpp tags="ARCH_MVCPP" : MVC++ layer rules: View←Model, Model←View BLOCK; Controller≤300 lines; no SQL outside DP; no print() in Controller
@doc arch.partner tags="ARCH_PARTNER" : Abstract Partner = ABC+abstractmethod; Console↔TUI via IUIProvider; AgentController registers virtual subclass
@doc flow.boot tags="FLOW_BOOT" : main.py → AppModel → MainScreen → CommandRegistry → Agent.run_cycle
@doc flow.agent_cycle tags="FLOW_AGENT_CYCLE" : perceive→decide→act→observe; streaming via IUIProvider callbacks
@doc feature.f006 tags="FEAT_F006" : Opencode process enforcement — omt_phase, omt_nav, omt_think, omt_tdd, gates, receipts
...
```

**Option B — Enhanced Markdown (migration path):**
Keep `.md` but enforce front-matter + structured sections:
```markdown
---
kb_id: arch.mvcpp
tags: [ARCH_MVCPP]
---
# ARCH_MVCPP
MVC++ layer rules: View←Model, Model←View BLOCK; Controller≤300 lines; no SQL outside DP; no print() in Controller
```

**Decision: Option A** — new `.kb.omt` source, one-time migration. Cleaner, matches meta-harness, no markdown parsing ambiguity.

### 2.2 Index Record Schema (JSONL)

```json
{
  "id": "arch.mvcpp",
  "kind": "doc",
  "line": 42,
  "src": ".meta/doc/omt++/architecture.kb.omt",
  "tags": ["ARCH_MVCPP", "MVCPP"],
  "text": "MVC++ layer rules: View←Model, Model←View BLOCK; Controller≤300 lines; no SQL outside DP; no print() in Controller",
  "refs": ["arch.partner", "flow.boot"],
  "tier": "core"
}
```

Fields:
- `id` — stable key (`<file>.<tag>`)
- `kind` — `doc` | `flow` | `feature` | `pattern` | `xref` | `gotcha`
- `tags` — queryable labels (prefix by domain: `ARCH_`, `FLOW_`, `FEAT_`, `PAT_`, `XREF_`, `GOTCHA_`)
- `text` — **compact, non-human** (≤300 chars, symbols over words)
- `refs` — explicit cross-refs for graph traversal
- `tier` — `core` | `extended` | `reference` (budget filter)

### 2.3 Query Tool: `omt_kb_nav`

```python
# ops mirror omt_nav
omt_kb_nav(op="nav", query="ARCH_", tag_type="ARCH", include_context=False)
omt_kb_nav(op="list_sections", file="architecture")
omt_kb_nav(op="cross_ref", xref="XREF_ARCH_PATTERNS")
omt_kb_nav(op="quick_ref", workflow="MVCPP_RULES")
```

Returns: `{records: [...], total: N, truncated: bool}` — same envelope as `omt_nav`.

---

## 3. Mandatory Consultation Gate

### 3.1 Gate Definition (in META_HARNESS.omt)

```omt
@gate g.kb on=before tools=@var.edit_tools when=path_in(src/) requires=session_flag(kb_consulted) msg=@msg.kb_required hard=true skip_ok=false order=5 : agent MUST consult AKB before src/ edits; omt_kb_nav{op:"list"} or omt_kb_nav{op:"nav",query:"..."} records consult
```

### 3.2 Session Bootstrap Injection

```omt
@inject kb_bootstrap on=first_tool_result budget=1024 : emit "AKB: omt_kb_nav{op:list} → core tiers (ARCH_, FLOW_, FEAT_) — consult before edits"
```

### 3.3 Consultation Recording

`omt_kb_nav` writes `{kind: "kb_consult", ts, query, records_returned}` to ledger → clears `kb_consulted` flag.

---

## 4. Non-Human Language Style

Rules for `text` field:
| Rule | Example |
|------|---------|
| Symbols over words | `View←Model BLOCK` not "View imports Model is blocked" |
| No articles | `Controller≤300 lines` not "Controller must be 300 lines or less" |
| Predicate prefix | `ERR:View←Model` `WRN:SQL∉DP` |
| Compact refs | `→arch.partner` not "see arch.partner" |
| Tier tag | `tier:core` for mandatory, `tier:ref` for lookup |

### 4.1 Style Linter (compile-time)

`kb_compiler.py` validates:
- `text` ≤ 300 chars
- No natural language stopwords (the, a, an, is, must, should, etc.)
- Required tags present per `kind`
- `refs` resolve to existing `id`s

---

## 5. Migration Plan

### 5.1 Phase 1: Scaffold (Analysis → Design)
- [ ] Create `scripts/omt/kb_compiler.py` (skeleton + test)
- [ ] Define `@kind` vocabulary: `doc`, `flow`, `feature`, `pattern`, `xref`, `gotcha`
- [ ] Define tag taxonomy per domain

### 5.2 Phase 2: Source Authoring (Design)
- [ ] Migrate `../../../.meta/doc/omt++/architecture.md` → `architecture.kb.omt`
- [ ] Migrate `data_flow.md` → `data_flow.kb.omt`
- [ ] Migrate `features.md` → `features.kb.omt`
- [ ] Migrate `extending.md` → `extending.kb.omt`
- [ ] Migrate `subsystems.md` → `subsystems.kb.omt`
- [ ] Migrate `persistence.md` → `persistence.kb.omt`

### 5.3 Phase 3: Compiler + Index (Programming)
- [ ] Implement parser → IR → index.jsonl
- [ ] Implement `omt_kb_nav` tool (plugin)
- [ ] Add gate `g.kb` to `META_HARNESS.omt`
- [ ] Add `@inject kb_bootstrap`
- [ ] Budget: `@budget kb_index max=32000`

### 5.4 Phase 4: Validation (Testing)
- [ ] Compile → verify index loads
- [ ] Gate blocks src/ edit without consult
- [ ] `omt_kb_nav` returns expected records
- [ ] Style linter passes on all sources
- [ ] AGENTS.md projection updated with KB pointer

---

## 6. Token Budget

| Budget | Limit | Rationale |
|--------|-------|-----------|
| `kb_index` | 32 KB | On-demand answers; larger than nav (64 KB) but scoped to app concepts |
| `kb_bootstrap` | 1 KB | Session injection |
| `agents_md` KB pointer | 128 B | "AKB: omt_kb_nav — consult before edits" |

---

## 7. Cross-Reference Map (XREF)

| XREF | Target |
|------|--------|
| `XREF_ARCH_MVCPP` | MVC++ layer rules |
| `XREF_ARCH_PARTNER` | Abstract Partner pattern |
| `XREF_FLOW_BOOT` | Boot sequence |
| `XREF_FLOW_AGENT_CYCLE` | Agent cycle |
| `XREF_FLOW_NAV` | TUI navigation |
| `XREF_FLOW_CHAT` | Chat streaming |
| `XREF_FLOW_RAG` | RAG ingest/query |
| `XREF_FLOW_SESSION` | Session lifecycle |
| `XREF_FLOW_PERSIST` | Persistence flow |
| `XREF_PAT_DP` | Database Partner pattern |
| `XREF_PAT_COMMAND` | Command pattern |
| `XREF_PAT_PROVIDER` | Provider/Adapter pattern |
| `XREF_FEAT_CATALOG` | Feature catalog |
| `XREF_EXT_SCREEN` | Add screen (MVC++ triad) |
| `XREF_EXT_CMD` | Add command |
| `XREF_EXT_TOOL` | Add agent tool |

---

## 8. Acceptance Criteria

1. **Compile**: `uv run scripts/omt/kb_compiler.py build` → produces `kb.index.jsonl` + `kb.ir.json` with 0 errors
2. **Query**: `omt_kb_nav{op:"nav",query:"ARCH_"}` returns ≥5 `ARCH_*` records
3. **Gate**: Edit `../../../src` without `omt_kb_nav` consult → blocked by `g.kb`
4. **Style**: All `text` fields pass non-human linter (≤300 chars, no stopwords, symbols)
5. **Budget**: `kb.index.jsonl` ≤ 32 KB
6. **Projection**: `../../../AGENTS.md` contains KB pointer line only
7. **Migration**: All 6 `.md` files migrated to `.kb.omt` with ≥80% content coverage

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Migration drift (markdown ↔ .omt) | One-time migration; markdown deleted post-verify; single source |
| Gate too aggressive (blocks legitimate reads) | `read` tool exempt (like `g.nav`); only `edit_tools` gated |
| Index staleness | `kb_compiler.py check --verify-projections` in CI; `omt_complete` triggers rebuild |
| Token bloat | Hard budget `kb_index max=32000` enforced at compile; tier filtering |

---

## 10. Implementation Order

1. `kb_compiler.py` (parser, IR, index writer, style linter, verify)
2. Source `.kb.omt` files (6 migrations)
3. `omt_kb_nav` plugin (reads index, same envelope as omt_nav)
4. `META_HARNESS.omt` additions: `@gate g.kb`, `@inject kb_bootstrap`, `@budget kb_index`
5. `harnessc.py` integration: `kb` target in build/verify
6. Tests: compile, query, gate, style, budget