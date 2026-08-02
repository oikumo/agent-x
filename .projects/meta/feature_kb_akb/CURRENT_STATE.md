# CURRENT_STATE — feature_kb_akb

> Paused 2026-08-02. Resume by reading this file, then following NEXT STEPS.

## Status: ANALYSIS_COMPLETE → Ready for Programming

### What happened
- User invoked meta-harness project workflow for AKB (Application Knowledge Base)
- Agent read all design artifacts, researched harnessc.py pipeline, omt_nav.ts plugin, gate architecture, enforcer patterns
- Plan refined and approved: full migration of 6 .md docs → .kb.omt + compiler + plugin + gate + tests

### Plan Approved
| Phase | Artifact | Status |
|-------|----------|--------|
| 1 | `scripts/omt/kb_compiler.py` | 📋 planned |
| 2 | 6 `.kb.omt` source migrations | 📋 planned |
| 3 | `.opencode/plugins/omt_kb_nav.ts` | 📋 planned |
| 4 | META_HARNESS.omt: `g.kb`, `@inject kb_bootstrap`, `@budget kb_index` | 📋 planned |
| 5 | `.opencode/lib/enforcer/kb_gate.ts` + gate_driver.ts registration | 📋 planned |
| 6 | Tests + e2e integration | 📋 planned |

### Key design decisions
- **Full migration (not incremental)**: all 6 `.md`→`.kb.omt` in one pass
- **`.md` deletion timing**: after full verification (compile + query + gate pass)
- **Gate enforcement**: hard gate `g.kb` blocks `src/` edits until `omt_kb_nav` consult
- **`.kb.omt` sources in `.meta/doc/omt++/`**: co-located with originals until deletions

### Implementation order (when resumed)
1. `kb_compiler.py` — parse `.kb.omt`, style lint, build `kb.index.jsonl` + `kb.ir.json`
2. Migration: `architecture.md` → `architecture.kb.omt` (start here — biggest, most complex)
3. Migrate remaining 5: `data_flow`, `features`, `extending`, `subsystems`, `persistence`
4. `omt_kb_nav.ts` — plugin loading `kb.index.jsonl`, 4 ops, writes `kb_consult` ledger
5. META_HARNESS.omt additions: `@gate g.kb` (order=35), `@inject kb_bootstrap`, `@budget kb_index max=32000`
6. `kb_gate.ts` enforcer module + gate_driver.ts registration
7. Tests: `test_kb_compiler.py`, `test_kb_nav.py`, e2e updates, source pins
8. `harnessc.py build` → verify projections
9. Delete 6 `.md` originals after full acceptance criteria pass

### Key harness pattern references (for mirroring)
- **Compiler**: `scripts/omt/harnessc.py` (parse, interpolate, derive, render_nav_index, build_ir, budget measure)
- **Plugin**: `.opencode/plugins/omt_nav.ts` (loadNavIndex, navQuery, 4 ops, flat string returns)
- **Gate**: `.opencode/lib/enforcer/nav_gate.ts` (pure decision fn + guard handler)
- **Gate registration**: `.opencode/lib/enforcer/gate_driver.ts` (IMPLS map + FALLBACK_GATES array)
- **Shared lib**: `.opencode/lib/omt_shared.ts` (readJsonl, initOmtShared, repoRoot resolution)

### Gate order slots
- 0: g.nav | 10: g.protect | 20: g.receipt | 30: g.tests | **35: g.kb (NEW)** | 40: g.phase | 50: g.think

### Files that will be created/modified
**New**: `scripts/omt/kb_compiler.py`, `.opencode/plugins/omt_kb_nav.ts`, `.opencode/lib/enforcer/kb_gate.ts`, 6× `.kb.omt` files, `tests/scripts/omt/test_kb_compiler.py`, `tests/scripts/omt/test_kb_nav.py`
**Modified**: `.meta/META_HARNESS.omt`, `.opencode/lib/enforcer/gate_driver.ts`, `.opencode/lib/omt_shared.ts` (maybe), `tests/scripts/omt/test_omt_harness_e2e.py`, `tests/scripts/omt/test_omt_enforcer_guard_source_pins.py`
**Deleted (post-verify)**: `.meta/doc/omt++/architecture.md`, `data_flow.md`, `features.md`, `extending.md`, `subsystems.md`, `persistence.md`

## NEXT STEPS (to resume)

```bash
# 1. Read this file (done) + relevant artifacts
# 2. Declare phase (TDD auto-activates for major_feature@Programming)
omt_phase{task_type:major_feature, scope:"AKB: compiler + 6 .kb.omt migrations + omt_kb_nav + g.kb gate + tests", feature:feature_kb_akb, design_doc:".projects/meta/feature_kb_akb/design_001_kb_akb.md"}

# 3. TDD testlist
omt_tdd{op:testlist, behaviors:[
  "kb_compiler build produces kb.index.jsonl and kb.ir.json from .kb.omt sources",
  "kb_compiler check validates style (≤300 chars, no stopwords, symbol density ≥0.3)",
  "kb_compiler check rejects unresolved xrefs",
  "kb_compiler check rejects duplicate IDs",
  "kb_compiler check enforces kb_index budget ≤32000",
  "omt_kb_nav op=nav returns records matching tag prefix",
  "omt_kb_nav op=list_sections lists unique tags per file",
  "omt_kb_nav op=cross_ref returns record by ID",
  "omt_kb_nav successful call writes kb_consult to ledger",
  "g.kb blocks src/ edit without kb_consult",
  "g.kb exempts read tools (read, glob on src/)"
], feature:features_kb_akb}

# 4. Education → green → refactor cycles
```

---

*Created: 2026-08-02*