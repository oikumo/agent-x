# PROJECT: feature_kb_akb — Application Knowledge Base (v2)

> Source-code-primary KB. **Main goal: keep CONCEPTS + ABSTRACTION** — the KB is the concept layer over source code (WHAT/WHY/CONNECTS-TO), never implementation. Mandatory agent consult before `src/` edits. Hybrid: AST skeleton + curated concept text. **Index content is UNBOUNDED** — query-scoped, not size-capped. Supersedes `design_001_kb_akb.md` + `operation_spec_001_kb_operations.md` (see Decision log).

**v2 (2026-08-02)**: re-focus approved sess 6 (source-code-primary, Alt-1). Rewritten from sess-6 proof-of-concept findings (`kb_code_tools_sample.jsonl`, 11 records) + budget correction (index unbounded).

**v2.1 (2026-08-02, sess 9)**: refinement pass, live-verified — coverage policy FIXED (ALL 272 public classes, auto-text floor; v2's "~45-55" estimate contradicted reality); doc-tier polish (xref/quick_ref/path-aware) DEFERRED to follow-up; drift fixes: `kb_compiler.main()` placeholder = build gap (critical path), budget lives at 3 sites, layer table vs real tree, gate msg `op:list` is an invalid op, sample-append ephemerality, rebuild trigger undefined.

---

## Standing principle (non-negotiable)

**Main goal: the KB keeps CONCEPTS + ABSTRACTION.** It is the abstraction layer the agent consults instead of reading source — the class/contract/dep graph IS the abstraction of the codebase.

**KB records = CONCEPTS, not implementation.** Every record stays high-level: role + responsibility + connections (WHAT / WHY / CONNECTS-TO), never HOW — no full signatures, no field lists, no fallback-branch notes. Implementation lives in source; the record's `file:line` jumps there.

Corollary: **records are concepts (class/contract/dep), NOT files.** No per-file `module` records (low-value noise — `list_sections(file)` already groups by `src`); no `method` records (signatures = implementation; fold facade public API into the class record's `text`).

---

## Vision

Give a coding agent actionable knowledge of the agentx **source code** — classes, contracts (ABCs/Partners), dependency edges, MVC++ layer — so the `g.kb` consult before any `src/` edit returns **code structure + concept**, not prose. Cuts post-consult grep/glob token cost (the reason the KB exists).

- **Primary tier — source code**: concept records (class/contract/dep) over `src/agentx/**/*.py`. **Coverage = ALL public classes** (272 today; no significance filter — filters create `g.kb` consult gaps for edited files outside the "significant" set). Hybrid: AST extracts the structural skeleton + graph (drift-free, regenerated each build); un-curated records get **auto-text** (bases + abstractmethods) so coverage is comprehensive from day one; curation progressively authors the concept `text` (role/why/connections — the value-add AST cannot derive).
- **Supporting tier — concept docs**: `.meta/doc/omt++/*.kb.omt` (6 files, 62 records, all tiers core/extended/reference) — semantics AST cannot derive (flows, gotchas, patterns, xrefs).
- **Query** — `omt_kb_nav` over a unified index (mirrors `omt_nav` API).
- **Gate** — `g.kb` blocks `src/` edits until a consult is recorded.
- **Style** — non-human (symbols, predicates, ≤300 char `text`, no stopwords), compile-enforced.

---

## Architecture

```
src/agentx/**/*.py ──AST skeleton──┐
                                   ├─► kb_compiler.py ──► .meta/.omt/kb.index.jsonl  (UNBOUNDED)
.meta/doc/omt++/*.kb.omt ─curated──┘                    (+ kb.ir.json)
  + code.kb.omt concept-text overlay                    └─► AGENTS.md projection (KB pointer only)
```

### Source 1 — Source code (AST skeleton + curated text, PRIMARY)

`kb_ast_extract.py` parses `src/agentx/**/*.py` via `ast` → emits **skeleton records** (3 kinds only):

| Kind | Emit when | AST-extracted fields |
|---|---|---|
| `contract` | class is ABC with `@abstractmethod`s (I*View, I*Partner, IGoalManager…) | id, bases, abstractmethod names, src, line, layer, refs→realizers |
| `class` | concrete class (facade/realizer/value object) | id, bases, src, line, layer, refs→bases+compositions |
| `dep` | inheritance (realization) + composition edges | id, edge type, src, line, refs→both endpoints |

**No `module` kind, no `method` kind** (see Standing principle).

**Curated pass** authors each record's `text` (concept statement: role/why/connections) + enriches `refs`, in a `code.kb.omt` overlay keyed by record id. Un-curated records keep AST **auto-text** (bases + abstractmethods). Template + seed = `kb_code_tools_sample.jsonl` (11 tools-subsystem records, sess 6) — **its texts must be PORTED into `code.kb.omt` keyed by extractor-stable ids** (hand-named `dep.tools_hybrid` → extractor's `dep.<Class>_<Target>` scheme), else the first real compiler build loses them.

#### Extraction contract — what AST gives vs what's curated

| Field | Source | Drift-free? |
|---|---|---|
| `id` (`kind.rid` e.g. `class.ToolRegistry`) | AST (class/ABC name) | ✅ auto |
| `kind` (class/contract/dep) | AST (ABC+abstractmethod→contract; concrete→class; edge→dep) | ✅ auto |
| `src`, `line` | AST | ✅ auto |
| `tags` (`CLASS_*`/`CONTRACT_*`/`DEP_*` + `TIER_CODE` + `LAYER_*`) | AST (name + path) | ✅ auto |
| `tier` = `code` | fixed | ✅ auto |
| `refs` | AST (bases, composition) + curated enrichment | ⚠️ partial |
| `text` (concept: role/why/connections) | **CURATED** (overlay); **auto-text fallback** (bases+abstractmethods) when un-curated | ❌ manual — the value-add |

Rebuild refreshes skeleton + AST-derived refs; curated `text` re-merged from overlay (not regenerated).

#### Layer inference (path-based — refined in impl)

| Path segment in `src` (verified vs real tree, sess 9) | `LAYER_` tag |
|---|---|
| `/model/` (both `agent/model/` + top-level `model/`) — default | `LAYER_MODEL` |
| `/view/`, `/ui/`, `/screens/`, `/tui/`, `*_view.py`, `*_screen.py` | `LAYER_VIEW` |
| `/controller/`, `*_controller.py` | `LAYER_CONTROLLER` |
| `/persistence/`, `DP_` class prefix | `LAYER_DP` |
| `/utils/` | `LAYER_UTIL` |

(Real dirs: `agent/{model,view,controller,persistence,demo}`, `model/{ai,rag,session,chat,coding,react,program}`, `ui/{screens,tui,common}`, `utils/`. v2's `/dp/` + `/controllers/` do not exist.)

### Source 2 — Concept docs (curated, supporting)

`.meta/doc/omt++/*.kb.omt` (6 files) — `doc`/`flow`/`feature`/`pattern` rules + `gotcha` traps + `xref` map. All tiers (core/extended/reference), 62 records. Hand-authored, non-human style, compile-linted. Semantics AST cannot derive.

### Index record schema (JSONL)

```json
{"id":"class.ToolRegistry","kind":"class","src":"src/agentx/agent/model/tools/registry.py","line":29,"tags":["CLASS_TOOLREGISTRY","TIER_CODE","LAYER_MODEL"],"text":"ToolRegistry(IToolRegistryPartner) — Model-layer tool catalog. O(1) dict lookup. Owns registration, enablement, health, safe execution (validate+act). Upgrades same-id sensor+actuator to HYBRID. Agent+controllers reach tools via this, through the ABC.","refs":["contract.IToolRegistryPartner","contract.ISensor","contract.IActuator","class.ToolSpec"],"tier":"code"}
```

- `id` — `kind.rid` (e.g. `class.Agent`, `contract.ISensor`, `dep.Agent_ToolRegistry`, `doc.mvcpp`, `flow.boot`)
- `kind` — `class|contract|dep` (code) + `doc|flow|feature|pattern|xref|gotcha` (curated)
- `tier` — `code` (primary, auto) | `core|extended|reference` (supporting, curated)
- `tags` — domain prefix + `TIER_*` + `LAYER_*` (code only)
- `text` — ≤300 chars, non-human
- `refs` — resolved record IDs (graph)

---

## Query: `omt_kb_nav`

```
omt_kb_nav(op=nav, query="CLASS_AGENT" | "LAYER_MODEL" | "ARCH_")   # tag-prefix OR full-text
omt_kb_nav(op=nav, query="class.ToolRegistry")                      # symbol-precise (full-text on id)
omt_kb_nav(op=nav, query="CONTRACT_", tag_type="TIER_CODE")         # code contracts only
omt_kb_nav(op=list_sections, file="tools")                          # records whose src includes "tools"
omt_kb_nav(op=cross_ref, xref="XREF_ARCH_MVCPP")                    # resolves XREF map (todo)
omt_kb_nav(op=quick_ref, workflow="AGENT_API")                      # curated workflow sets (todo)
```

**Actual plugin semantics (verified sess 6):**
- `nav`: tag-prefix match (query ending `_` or `:` → uppercase prefix on `tags`) OR full-text substring over `id+text+tags+tier`. `class.ToolRegistry` works via full-text on `id` — **symbol-precise lookup without a dedicated `kind:` filter**.
- `tag_type`: filters **TIER only** (CORE/EXTENDED/REFERENCE/CODE) — NOT kind-prefix (design_001 was wrong). `tag_type:"TIER_CODE"` selects code records.
- `list_sections(file)`: filters records whose `src` includes `file`.
- `kind:` filter: NOT needed (tag-prefix + full-text cover it); add only if proven insufficient.

**Path-aware consult (planned enhancement):** when `g.kb` fires on a `src/.../tools/...` edit, the consult reminder biases to records whose `src` shares a path prefix with the edit target. Deferred to follow-up (§C); gate works globally today.

---

## Budget policy — UNBOUNDED index, query-bounded tokens

**The KB is for querying; its content must be unlimited.** The index holds ALL curated records (62) + ALL code concept records (comprehensive across `src/agentx`) — no size cap.

**Why unlimited is compatible with token minimization (project rule #2):** token cost is **per-QUERY**, not per-index. Each `omt_kb_nav` call returns a scoped, filtered slice (tag-prefix / full-text / `tag_type` / `file`) with a `truncated` flag — the agent never loads the whole index. A larger index = more knowledge available, NOT more tokens per query. Trimming content to fit a size cap actively harms the agent (knowledge loss) without saving tokens (queries are scoped anyway).

**Action (implementation phase — harness-surface edit, needs `omt_phase` + receipt):**
- **Remove the budget at ALL 3 sites** (verified sess 9): `META_HARNESS.omt:245` `@budget kb_index max=32768`; `kb_compiler.py` `DEFAULT_BUDGETS={"kb_index":32000}` + `check_budget()`; `harnessc.py:125` compiler-measurable set (`"kb_index"` entry). The index-size budget is the wrong mechanism.
- **Add** a per-query result bound to `omt_kb_nav` (e.g. `max_records` per call, `truncated:true` when exceeded) — bounds worst-case query token cost. Exact value TBD in impl; existing `truncated` field already supports it. **P0 — more important with ~500-800 code records than it was at 62.**

**Current measured state (sess 6 + sess 9):** curated 23449 B / 62 records (core 13040 B/34, extended 6118 B/16, reference 4291 B/12) — ALL retained. Code tier (sess-9 measured): **272 public classes** → ~270-280 class/contract records + ~250-500 dep edges ≈ **500-800 records** (~130-250 KB at auto-text size) — total index ~150-270 KB, unbounded. (v2's "~45-55 records" estimate was wrong — superseded by the all-public-classes coverage policy.)

---

## Gate (`g.kb`)

```omt
@gate g.kb on=before tools=@var.edit_tools when=path_in(src/) requires=session_flag(kb_consulted) ...
```
Blocks `src/` edits until `omt_kb_nav` consult recorded (ledger `kb_consult`). `read` on `src/` is exempt (only `edit_tools` gated). Order=55. **Path-aware consult** (above) is deferred to follow-up (§C).

**Live bug (verified sess 9)**: `@msg kb_required` (line 141) tells the agent to run `omt_kb_nav{op:list}` — **`op:list` does not exist** (ops: nav|list_sections|cross_ref|quick_ref); following the gate's own message returns "unknown op". Fix → `op:nav`.

**Missing**: `@inject kb_bootstrap` reminder (design §3.2) — never added to harness. To implement as a deliverable.

**Receipt batching**: budget removal + `@inject kb_bootstrap` + `@msg kb_required` fix = ONE `META_HARNESS.omt` edit round (receipt discipline: ONE edit per file per round).

---

## Tag taxonomy

| Prefix | Domain | Tier |
|---|---|---|
| `CLASS_` `CONTRACT_` `DEP_` | Source code (auto) | code |
| `LAYER_` | MVC++ layer (MODEL/VIEW/CONTROLLER/DP/UTIL) — code only | code |
| `ARCH_` `FLOW_` `FEAT_` `PAT_` | Concept docs (curated) | core/extended/reference |
| `XREF_` `GOTCHA_` | Cross-refs, gotchas | core/reference |
| `TIER_` | CODE / CORE / EXTENDED / REFERENCE | all |

(dropped: `MODULE_`, `METHOD_` — kinds removed)

---

## Implementation components

| Component | Path | Status |
|---|---|---|
| KB compiler (curated parse + skeleton merge) | `scripts/omt/kb_compiler.py` | ⚠️ **library-only — `main()` placeholder (l.220); NOTHING builds the index. Build-gap = critical-path blocker** |
| AST source skeleton extractor | `scripts/omt/kb_ast_extract.py` (NEW) | 📋 planned |
| Curated concept-text overlay (code `text` values) | `.meta/doc/omt++/code.kb.omt` | ✅ live — 17 entries (11 sess-6 sample texts ported to extractor-stable ids, +1 `class.Agent` facade sess-12, +5 more in TODO); curation progressive per subsystem → round_001 in `.sandbox/akb_smart_population_and_update/` |
| Rebuild trigger | `uv run scripts/omt/kb_compiler.py build` | 📋 define as THE rebuild command (sync acceptance runs it; harnessc chaining optional) |
| `omt_kb_nav` plugin | `.opencode/plugins/omt_kb_nav.ts` | ✅ exists (4 ops); ⚠️ no result-cap |
| `g.kb` gate | `META_HARNESS.omt` | ✅ exists (order=55); ⚠️ `@msg kb_required` says invalid `op:list` → fix to `op:nav` |
| `@budget kb_index` | `META_HARNESS.omt:245` + `kb_compiler.py DEFAULT_BUDGETS`/`check_budget` + `harnessc.py:125` | ❌ REMOVE at all 3 sites (unbounded) |
| Per-query result bound | `omt_kb_nav.ts` | 📋 planned (`truncated` exists) — P0 with 500-800 record index |
| `kb_bootstrap` inject | `META_HARNESS.omt` | ❌ missing |
| `quick_ref` workflows | `omt_kb_nav.ts` | ⏸️ DEFERRED (follow-up — doc-tier) |
| XREF map records | `.kb.omt` + nav | ⏸️ DEFERRED (follow-up — doc-tier; 2/16) |
| Tests | `tests/scripts/omt/test_kb_*.py` | ✅ 12; +AST tests planned |
| Proof-of-concept sample | `.projects/meta/feature_kb_akb/kb_code_tools_sample.jsonl` | ✅ 11 records (sess 6); ephemeral until ported to overlay |

---

## Acceptance criteria

### A — Baseline (MET, sess 5 — preserved)

1. ✅ `kb_compiler.py build` compiles 62 curated records, 0 errors.
2. ✅ `omt_kb_nav` 4 ops (nav/list_sections/cross_ref/quick_ref) functional.
3. ✅ `g.kb` gate exists (order=55), blocks `src/` edit without consult.
4. ✅ `kb_index` budget line exists (32768) — **to be REMOVED in v2**.
5. ✅ AGENTS.md has KB pointer only.
6. ✅ 12 `test_kb_*.py` tests green.

### B — Re-focus deliverables (v2.1 — P0 code-tier critical path)

1. **AST skeleton extractor** — `kb_ast_extract.py` emits class/contract/dep skeleton records (id, kind, src, line, tags, tier, AST-derived refs) from `src/agentx/**/*.py`; ALL public classes; auto-text for un-curated; 0 errors.
2. **Build CLI (critical path)** — `kb_compiler.py build` functional (replaces `main()` placeholder): curated `.kb.omt` + AST skeleton + `code.kb.omt` overlay merge → unified `kb.index.jsonl` + `kb.ir.json`; orphan overlay-key + orphan-ref checks. Nothing builds the index today.
3. **Curated-text overlay** — `code.kb.omt` seeded with the 11 ported sample texts (extractor-stable ids); curation progressive per subsystem (tools → agent facade → controllers → view partners → …); compiler merges.
4. **Comprehensive code coverage** — ALL public classes in `src/agentx` emitted (272 today; class/contract/dep only, no module/method). Coverage total, not filtered — a `g.kb` consult must never hit a coverage gap for an edited file. Curated `text` covers high-traffic subsystems first.
5. **Sample → live validated (ephemeral proof)** — append the 11 sess-6 tools records (backup first); `omt_kb_nav` returns: `CLASS_`→5, `CONTRACT_`→3, `DEP_`→3, `tag_type:TIER_CODE`→11, `"class.ToolRegistry"`→1, `list_sections file:"tools"`→tools records. Proves the code-tier query path TODAY; wiped by first real build → durable form is the overlay (item 3).
6. **Sync** — edit a `src/` class → `uv run scripts/omt/kb_compiler.py build` → skeleton reflects change (curated `text` re-merged from overlay; renamed/removed class → orphan overlay-key compile warning).
7. **Query** — `omt_kb_nav{op:nav, query:"CLASS_AGENT"}` returns Agent record with concept text + bases + file + refs.
8. **Budget policy** — `kb_index` budget REMOVED at all 3 sites (`META_HARNESS.omt:245`, `kb_compiler.py`, `harnessc.py:125`); per-query result bound added; index unbounded. `kb.index.jsonl` built by `kb_compiler.py build`, not hand-maintained.
9. **Curated clean** — all `.kb.omt` records pass style linter (≤300 chars, no stopwords); 0 corrupted IDs/text.
10. **Bootstrap + gate msg** — `@inject kb_bootstrap` emits AKB reminder once/session; `@msg kb_required` fixed (`op:list` → `op:nav`). ONE `META_HARNESS.omt` edit round (with budget removal).
11. **Projection** — AGENTS.md KB pointer unchanged (pointer only).
12. **Tests** — `uv run pytest tests/scripts/omt/test_kb_*.py` green (+AST extract, sync, query, budget-removed tests).
13. **design_001 + operation_spec_001** marked SUPERSEDED. (✅ done sess 7)

### C — Deferred to follow-up (doc-tier polish — NOT source code)

1. **quick_ref** — ≥6 curated workflows return scoped record sets (`omt_kb_nav.ts`).
2. **XREF** — `cross_ref("XREF_ARCH_MVCPP")` resolves (author 14 missing xref records).
3. **Path-aware consult** — gate biases records by edit-target path prefix.

---

## Prior-resume checklist (content debt)

> **All 6 `.kb.omt` content bugs below were APPLIED in session 10.** Kept here as audit trail — not live debt. Confirmed by `akb_smart_population_and_update` round_001 (2026-08-08): `subsystems.kb.omt:33 doc.utils`, `subsystems.kb.omt:17 doc.agent_persist`, `architecture.kb.omt:19 doc.decisions`, `features.kb.omt:27 features_xref`, `persistence.kb.omt:17 persist_xref` are all LIVE and clean in the rebuilt `.meta/.omt/kb.index.jsonl` (439 records, 0 errors). Subsequent overlay growth is tracked by `.sandbox/akb_smart_population_and_update/round_*.md`.

### `.kb.omt` content bugs (6 — APPLIED sess 10, recorded for audit)
| File:line | Record | Fix |
|---|---|---|
| `subsystems.kb.omt:17` | `doc.aontpresist` | → `doc.agent_persist`; text `v.taripol` → `volatile` |
| `subsystems.kb.omt:31` | `doc.to` | → `doc.demo`; text `Consisth` → `Console` |
| `subsystems.kb.omt:33` | `doc.utils` | `Xertion`→`EXCEPTION`, `dirflz`→`dir_utils`, `btS_OP_VERSION` cap; tag `SUBSYS_UTILS_REFERENCE` → add `TIER_REFERENCE` |
| `architecture.kb.omt:19` | `doc.Decisions` | → `doc.decisions` |
| `features.kb.omt:27` | `features_xref` | `§12Arrabits` → `§12 Artifacts` |
| `persistence.kb.omt:17` | `persist_xref` | trailing format fix |

### Superseded docs
- `design_001_kb_akb.md` — **SUPERSEDED** by this file (drift: id `<file>.<tag>` vs `kind.rid`; budget 32000 vs removed; tag_type kind vs TIER; pure-AST assumption).
- `operation_spec_001_kb_operations.md` — **SUPERSEDED** by this file (same drift + pre-source-code-primary scope).

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Unbounded index (~500-800 records) → query returns too much | Per-query result cap (`truncated` flag) — P0 — + scoped filters (tag_type/file/prefix); tier filtering |
| Curated `text` drifts from source (class renamed/removed) | Rebuild refreshes skeleton; **orphan overlay-key check** (`code.kb.omt` key with no matching skeleton id → compile warning) + orphan-ref check; CI `kb_compiler.py check` |
| Auto-text records = low-signal noise for un-curated classes | Accepted: auto-text (bases+abstractmethods) is the floor, not the ceiling; query-side scoping bounds tokens; concept-altitude filter (class/contract/dep only, no module/method) keeps the abstraction level |
| Curated-text authoring bottleneck (272 classes) | Not blocking: coverage comes from the skeleton; curate high-traffic subsystems first (tools — sample-proven); text is terse (≤300 chars) |
| Hand-appended sample records wiped by first real build | Append is validation-only (ephemeral); port texts → `code.kb.omt` with extractor-stable ids BEFORE first build |
| AST + curated ID collision | Namespaces: `class.*`/`contract.*`/`dep.*` vs `doc.*`/`flow.*` |
| Gate blocks legitimate reads | `read` exempt (like `g.nav`); only `edit_tools` gated |
| Harness-surface edits (budget removal, inject) | Receipt discipline: one edit per file per e2e receipt; `omt_phase` before `META_HARNESS.omt`/plugin edits |

---

## Implementation plan (harness-surface steps need `omt_phase` + receipt)

**P0 — code-tier critical path** (source code is the key):

*Non-gated (docs/data — safe):*
1. Append 11 sess-6 sample records → `.meta/.omt/kb.index.jsonl` (backup first); validate via `omt_kb_nav`. **Ephemeral validation only** — wiped by first real build (step 6).
2. Fix 6 `.kb.omt` content bugs (§Prior-resume checklist).
3. ✅ (done sess 7) `design_001` + `operation_spec_001` SUPERSEDED banners.
4. Author `code.kb.omt` overlay — **seed = 11 sample texts ported to extractor-stable ids** (`dep.tools_hybrid` → `dep.<Class>_<Target>`); then per-subsystem curation.

*Gated (harness-surface — `omt_phase` declared; receipt discipline: ONE edit per file per round):*
5. `kb_ast_extract.py` (NEW — creation free; TDD red first) — AST skeleton extractor: ALL public classes → class/contract/dep + auto-text; path+suffix layer inference.
6. `kb_compiler.py` — functional `build` CLI (replaces placeholder): curated `.kb.omt` + AST skeleton + overlay merge → unified `kb.index.jsonl` + `kb.ir.json`; orphan overlay-key + orphan-ref checks; REMOVE `DEFAULT_BUDGETS`/`check_budget` (+ `harnessc.py:125` entry).
7. `META_HARNESS.omt` — ONE batched edit: REMOVE `@budget kb_index`; ADD `@inject kb_bootstrap`; FIX `@msg kb_required` (`op:list`→`op:nav`).
8. `omt_kb_nav.ts` — per-query result bound (`max_records`, `truncated:true`) — P0 with 500-800 record index.
9. Rebuild unified index (`uv run scripts/omt/kb_compiler.py build`) → validate via `omt_kb_nav` (CLASS_AGENT, TIER_CODE, list_sections, sync-after-edit).
10. `tests/scripts/omt/test_kb_*.py` — AST extract, sync, query, budget-removed tests (green run = e2e receipt).

**P1 — DEFERRED to follow-up project (doc-tier polish):** quick_ref curated workflows (≥6); 14 missing xref records + `cross_ref` wiring; path-aware consult.

---

## Decision log (v2, 2026-08-02)

| Decision | Rationale |
|---|---|
| **Index UNBOUNDED** (remove `@budget kb_index`) | KB is for querying; content must be unlimited. Token cost is per-query (scoped + capped), not per-index. Trimming to fit a cap harms the agent without saving tokens. |
| Code kinds = `class/contract/dep` only | Concepts not files/signatures; matches sess-6 11-record sample; drop `module` (noise) + `method` (signatures). |
| Hybrid AST skeleton + curated `text` | AST gives drift-free skeleton+graph; concept `text` (role/why) is the value-add AST can't derive. |
| Layer inference = path-based | Deterministic, drift-free, no per-record annotation. |
| `tag_type` filters TIER (incl. CODE) | Verified sess 6; design_001's "filters kind" was wrong. |
| Path-aware consult = planned (not v2) | Gate works globally; path-awareness is polish. |
| `design_001` + `operation_spec_001` SUPERSEDED | Fundamental drift (id format, budget, tag_type, pure-AST); cheaper than in-place rewrite of 2 design docs. |
| **Coverage = ALL public classes (272), auto-text floor** (sess 9) | v2's "~45-55" contradicted reality (272 public classes in `src/agentx`). No significance filter: filters create `g.kb` consult gaps. Auto-text (bases+abstractmethods) makes coverage comprehensive day one; curation progressive. |
| **Doc-tier polish DEFERRED** (sess 9) | xref/quick_ref/path-aware consult are not source code; v2.1 P0 = code-tier critical path only (source code is the key). |
| **Concepts+abstraction = main goal** (sess 9, user) | KB = concept layer over source; the class/contract/dep graph IS the abstraction; implementation stays in source, reachable via `file:line`. |

---

*vCreated: 2026-08-02 | v2 rewritten: 2026-08-02 (source-code-primary, concept-altitude, unbounded index) | v2.1: 2026-08-02 sess 9 (coverage policy fixed: ALL public classes + auto-text floor; doc-tier deferred; live-verified drift fixes: build gap, 3-site budget, layer table, gate msg `op:list`, sample ephemerality, rebuild trigger) | Status: ✅ DONE (sess 12 — 439 records live; g.kb consult-gate wired; 21/21 test_kb_* green) — Prior-resume checklist APPLIED (sess 10); overlay grew 11→17 (sess 12 + Agent facade record). Subsequent overlay growth curated via `.workflows/app_knowledge_base/loops/akb_smart_population_and_update.md` → round artifacts in `.sandbox/akb_smart_population_and_update/`. |*
