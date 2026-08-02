# PROJECT: feature_kb_akb — Application Knowledge Base

> Compile-time index for agentx concept docs with mandatory agent consultation gate.

---

## Vision

Replace raw markdown `.meta/doc/omt++/*.md` with a **machine-optimal knowledge base** that:
- Compiles to structured index (`.meta/.omt/kb.index.jsonl`)
- Queries via `omt_kb_nav` (mirrors `omt_nav` API)
- **Enforces consultation** before any `../../../src` edit via gate `g.kb`
- Uses **non-human language style** (symbols, predicates, ≤300 chars, no stopwords)

---

## Artifacts in This Folder

| File | Purpose |
|------|---------|
| `design_001_kb_akb.md` | Full design: architecture, migration plan, gates, budgets, acceptance criteria |
| `operation_spec_001_kb_operations.md` | Machine-readable op contracts: compile, query, consult, validate_style, gate_check, bootstrap_inject, budget_check |

---

## Core Design Decisions

### Source Format: `.kb.omt` (not markdown)
- OMT-HDL subset: `@version`, `@var`, `@doc`, `@xref`, `@budget`
- Single source of truth — no markdown parsing ambiguity
- One-time migration from 6 `.md` files → 6 `.kb.omt` files

### Index Schema (JSONL)
```json
{
  "id": "arch.mvcpp",
  "kind": "doc",
  "tags": ["ARCH_MVCPP", "TIER_CORE"],
  "text": "MVC++: View←Model BLOCK, Model←View BLOCK, Controller≤300, SQL∉DP, print∉Controller",
  "refs": ["arch.partner", "flow.boot"],
  "tier": "core"
}
```

### Mandatory Consultation Gate (`g.kb`)
```omt
@gate g.kb on=before tools=@var.edit_tools when=path_in(src/) requires=session_flag(kb_consulted)
```
- Blocks `../../../src` edits until `omt_kb_nav` consult recorded
- Consult recorded via ledger entry `{kind: "kb_consult", ...}`
- Session bootstrap injection reminds agent: "AKB: omt_kb_nav{op:list} → core tiers — consult before edits"

### Non-Human Language Style (compile-enforced)
| Rule | Example |
|------|---------|
| Symbols over words | `View←Model BLOCK` |
| No articles | `Controller≤300 lines` |
| Predicate prefix | `ERR:View←Model`, `WRN:SQL∉DP` |
| Compact refs | `→arch.partner` |
| ≤300 chars, stopword-free | Linter rejects "the", "must", "should", "ensure" |

### Tag Taxonomy
| Prefix | Domain |
|--------|--------|
| `ARCH_` | Architecture (MVCPP, PARTNER, DP, STACK) |
| `FLOW_` | Data Flow (BOOT, AGENT_CYCLE, NAV, CHAT, RAG, SESSION, PERSIST) |
| `FEAT_` | Features (CATALOG, F006, F020...) |
| `PAT_` | Patterns (DP, COMMAND, PROVIDER, SCREEN, TOOL) |
| `XREF_` | Cross-refs |
| `GOTCHA_` | Gotchas |
| `TIER_` | CORE, EXTENDED, REFERENCE |

---

## Migration Targets (6 files)

| Current | Target | Key Content |
|---------|--------|-------------|
| `architecture.md` | `architecture.kb.omt` | MVC++, Partner, DP, Stack, Config, Decisions |
| `data_flow.md` | `data_flow.kb.omt` | Boot, Nav, AgentCycle, Chat, RAG, Session, Persist |
| `features.md` | `features.kb.omt` | Catalog, F001–F024, Cross-cutting |
| `extending.md` | `extending.kb.omt` | Screen/Command/Tool patterns, Checklist, QuickRef |
| `subsystems.md` | `subsystems.kb.omt` | Agent, RAG, Session, AI, UI, Demo, Utils |
| `persistence.md` | `persistence.kb.omt` | DBs, Schemas, DP convention, Filesystem |

---

## Implementation Components (Future)

| Component | Path | Status |
|-----------|------|--------|
| Compiler | `scripts/omt/kb_compiler.py` | 📋 Planned |
| Query Tool | `.opencode/plugins/omt_kb_nav.ts` | 📋 Planned |
| Gate + Inject | `META_HARNESS.omt` additions | 📋 Planned |
| Budget | `@budget kb_index max=32000` | 📋 Planned |
| Tests | `tests/scripts/omt/test_kb_*.py` | 📋 Planned |

---

## Acceptance Criteria (Design)

1. **Compile**: `kb_compiler.py build` → `kb.index.jsonl` + `kb.ir.json` (0 errors)
2. **Query**: `omt_kb_nav{op:"nav",query:"ARCH_"}` → ≥5 `ARCH_*` records
3. **Gate**: Edit `../../../src` without consult → blocked by `g.kb`
4. **Style**: All `text` fields pass non-human linter
5. **Budget**: `kb.index.jsonl` ≤ 32 KB
6. **Projection**: `../../../AGENTS.md` contains KB pointer only
7. **Coverage**: 6 `.kb.omt` files ≥80% content coverage of original `.md`

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Migration drift | One-time migration; markdown deleted post-verify |
| Gate blocks reads | `read` tool exempt (like `g.nav`); only `edit_tools` gated |
| Index staleness | `kb_compiler.py check --verify-projections` in CI; `omt_complete` triggers rebuild |
| Token bloat | Hard budget `max=32000` enforced at compile; tier filtering |

---

## Related

- **Meta-Harness Pattern**: Mirrors `META_HARNESS.omt` → `harnessc.py` → `nav.index.jsonl` → `omt_nav`
- **SDP Guide**: `../../../.meta/software_development_process/omt_agent_guide.md` §12 (Artifacts), §15 (FileTree)
- **Current Docs**: `../../../.meta/doc/omt++` (architecture, data_flow, features, extending, subsystems, persistence)

---

## Next Steps (When Prioritized)

```bash
# 1. Declare phase
omt_phase{task_type:major_feature, phase:Programming, scope:"Implement AKB compiler, migrate 6 .md→.kb.omt, build omt_kb_nav, add g.kb gate", feature:feature_kb_akb}

# 2. TDD auto-activates (major_feature@Programming)
omt_tdd{op:testlist, behaviors:[...], feature:feature_kb_akb}

# 3. Implement compiler → index → nav tool → gate → tests
```

---

*Created: 2026-08-02 | Status: DESIGN_COMPLETE | Projects: .projects/meta/feature_kb_akb/*