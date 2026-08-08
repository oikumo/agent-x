# CURRENT_STATE — feature_kb_akb

> **DONE 2026-08-08 (session 12)**. AKB unified index live (437 records); feature advanced to Done phase. This file retained for archive/reference; for new work consult `PROJECT.md` v2.1 + `test_report.md` under `.meta/software_development_process/6.testing/features/feature_kb_akb.application_knowledge_base/`.

## Status: ✅ DONE (session 12, 2026-08-08)

## Session 12 (2026-08-08) — P0 non-gated step 9 COMPLETE; feature advanced to Done

- ✅ **Step 9a — `subsystems.kb.omt:33` doc.utils stopword fix**: reworded `is_directory_allowed_to_deletion`→`dir-deletion predicate`, `is_valid_url`→`url validation` (kept text ≤300c, stopword-free per `STOPWORDS = {"the","a","an","is","are","was","were","must","should","will","would","could","may","might","shall","can","need","require","ensure","verify","confirm"}`).
- ✅ **Step 9b — `kb_compiler.py build`**: 437 records (class=239, contract=32, dep=104, doc=39, feature=12, flow=9, xref=2), **0 errors**, 4 dup warnings (legacy splits, expected per §Session-11 gotcha #8).
- ✅ **Step 9c — `omt_kb_nav` live validation (4 queries)**:
  - `nav CLASS_AGENT` → `class.Agent` returns curated overlay text (B7 closed post-9d).
  - `nav "class.ToolRegistry"` → 1 hit, OVERLAY text (rich curated concept text wins).
  - `nav "CONTRACT_" tag_type:TIER_CODE` → 25/32 + `… truncated: 25/32 records — refine query` marker.
  - `list_sections file:"tools"` → 24 records (15 class + 2 contract + 7 dep).
- ✅ **Step 9d — B7 acceptance gap CLOSED**: added `@class Agent tier=code refs=...` record to `code.kb.omt` overlay (auto-text was just `Agent(IAgentModelPartner)`; curated text now `Agent(IAgentModelPartner) — facade orchestrating all agent subsystems. Wires memory+policy+goals+reflection+tools+environment through one entry. Owns session lifecycle: persist/resume snapshots register built-in tools (filesystem/rag/session). Controllers reach model via ABC partner.`).
- ✅ **Test artifact**: authored test report at `.meta/software_development_process/6.testing/features/feature_kb_akb.application_knowledge_base/test_report.md` (required for Testing→Done transition per PHASE_EXIT_REQUIREMENTS in `phase_gate.ts`).
- ✅ **omt_tdd done → blocked → omt_skip override → omt_complete advance_to:Done**: full-suite had 6 pre-existing baseline failures (verified via `git stash` on clean HEAD) — 2× `test_mvc_compliance` (regression from `feature_024` paused work — agent_controller.py 350 LOC > 300 god-limit), 3× `test_react_screen` (textual + py3.14 mock `__name__` interaction), 1× `test_tdd_check::test_gate_returns_allowed_when_no_tdd` (stale assertion from prior `feature kb` commit expecting Python gate to enforce g.kb; g.kb lives in TS gate_driver). Plus one stale dangling RED (`test_work_md_within_budget`) for this feature from earlier WORK.md-budget probe. Sanctioned skips recorded; `omt_complete{advance_to:Done}` succeeded.
- ✅ **WORK.md**: feature marked `[x]` DONE + 1-line pointer; within 5120 B budget (4914 B final).

### Session-12 gotchas (must survive)
1. **Baseline gate tyranny**: `omt_tdd{op:done}` and `omt_complete` (Testing→Done) both run `tdd_check.py validate-exit` and indirectly check full-suite via pre-existing gate expectations. Pre-existing baseline failures (NOT caused by this feature) block Done without `omt_skip`. Sanity: always `git stash` + re-run to confirm baseline before claiming a feature introduced a regression — 30s saves hours of misdiagnosis.
2. **Test report artifact REQUIREMENT for Done**: `PHASE_EXIT_REQUIREMENTS["Testing"]` in `phase_gate.ts` checks for `test_report.md` under `.meta/software_development_process/6.testing/features/<feature>/`. Major_feature → MUST author this even if all unit tests pass; Done is unreachable otherwise. Use an existing one (e.g. `feature_023.test_report.md`) as template — sections: Summary, Test Execution, Behavior Verification (or live validation), Pre-Existing Failures, Artifacts, Conclusion.
3. **Stale dangling REDs pollute validate-exit**: any prior session's `omt_tdd{op:red}` recorded for a feature stays in `ledger.jsonl` forever; if no green cycle follows at the same test_node, validate-exit blocks. For genuinely-balanced features (real cycles all red→green→refactor→done), use `omt_skip{scope:all}` and log the stale ledger entry (test_node + verify it now passes via direct pytest). No destructive "clear ledger" path sanctioned — skip is the escape.
4. **Stopword lint splits snake_case**: `[a-zA-Z]+` regex means any `is_*`/`can_*`/`should_*`/`would_*`/`will_*` identifier in CURATED `.kb.omt` text trips the stopword checker (Auto-text skeleton is exempt — length-only). Cure is rewording identifiers into prose noun-phrases (`dir-deletion predicate`, `url validation`), NOT relaxing the linter. Stopword set is small but easily forgotten — re-read `kb_compiler.py STOPWORDS` before authoring overlay text.

## Session 11 (2026-08-02) — P0 GATED steps 4-8 DONE (TDD ×2 cycles); PAUSED mid-step 9 on ONE blocker

- ✅ **Step 4-5 — AST extractor (TDD cycle 1)**: `scripts/omt/kb_ast_extract.py` NEW (pass1 symbols → pass2 class/contract/dep; ALL public classes; auto-text=bases+abstractmethods ≤280c; path+suffix layer inference; composition via `self.x=Foo()`+AnnAssign in `__init__`; dup names → first-by-sorted-path + warning; deterministic: sorted everywhere). `tests/scripts/omt/test_kb_ast_extract.py` NEW — 10/10 green + refactor. Real tree: **375 skeleton records** (239 class / 32 contract / 104 dep), 4 dup warnings (SessionDatabase, ChatMessage, IModelsViewPartner, MainTUIScreen — legacy `agent/view/tui`+`agent/persistence` vs `ui/tui`+`model/*` splits).
- ✅ **Step 6 — build CLI (TDD cycle 2)**: `kb_compiler.py` rewritten — `build_index(kb_src_dir, src_root, repo_root)` = curated `.kb.omt` (EXCLUDING `code.kb.omt`) + skeleton + overlay merge (overlay text wins+full lint; refs union; skeleton src/line/tags win; auto-text length-only lint) → `build`/`check` CLI functional. Orphan overlay-key → warning; dup-id + unresolved-ref → errors. `DEFAULT_BUDGETS`/`check_budget` REMOVED (+ `harnessc.py:125` `"kb_index"` out of MEASURABLE_BUDGETS). Tests: budget test → removal pin + 3 build-unified = 11 compiler tests; **21/21 test_kb_\* green**.
- ✅ **Step 7 — META_HARNESS.omt batched** (uv-python multi-site transform, sanctioned): `@budget kb_index` REMOVED; `@inject kb_bootstrap on=first_tool_result budget=256` ADDED + **wired** `nav_gate.ts sessionBootstrap` (reads `ir.injects` id=kb_bootstrap, rides firstEver branch — B10 literal); `@msg kb_required` FIXED `op:list`→`op:nav` (+query hints). `harnessc build` OK (240 records, no kb_index budget line).
- ✅ **Step 8 — `omt_kb_nav.ts` result bound**: `MAX_RECORDS=25` + `… truncated: 25/N records — refine query` marker on ALL 4 ops; tag_type describe +`TIER_CODE`; tierOrd +code.
- ⏸️ **Step 9 — PAUSED at first real build**: `uv run scripts/omt/kb_compiler.py build` → **437 records** (239 class, 32 contract, 104 dep, doc=39, feature=12, flow=9, xref=2), 4 dup warnings OK — but **1 ERROR blocks output write**:
  - `KB:doc.utils: keyword 'is' in text` — `subsystems.kb.omt:33` (sess-10 rewrite): identifiers `is_directory_allowed_to_deletion`, `is_valid_url` split by the linter's `[a-zA-Z]+` regex → "is" stopword hit. **FIX (non-gated, option a — reword, do NOT relax linter):** replace `is_directory_allowed_to_deletion`→`dir-deletion predicate`, `is_valid_url`→`url validation`. Only doc.utils errored (other 61 curated clean).

### Resume point (sess 12 — NON-gated throughout; re-declare `omt_phase{major_feature, Programming, feature_kb_akb, design_doc:PROJECT.md}` only if gated edits needed — ledger unlocks expire ~8h)
1. Fix `subsystems.kb.omt:33` doc.utils text per above (keep ≤300c, stopword-free).
2. `uv run scripts/omt/kb_compiler.py build` → expect `wrote ...kb.index.jsonl (~437 records, unbounded) + kb.ir.json`.
3. Validate live via `omt_kb_nav`: `nav CLASS_AGENT`→class.Agent (auto-text — Agent un-curated); `nav "class.ToolRegistry"`→1 hit OVERLAY text; `nav CONTRACT_ tag_type:TIER_CODE`→25+`truncated` marker; `list_sections file:"tools"`→tools records; sync: trivially edit a src class name in overlay-irrelevant file → rebuild reflects (or trust extractor tests).
4. ⚠️ **Acceptance B7 gap**: wants `CLASS_AGENT` → "concept text" — Agent has AUTO-text only (overlay covers tools subsystem only; curation progressive per B3). Decide: add `class.Agent`(+facade) record to `code.kb.omt` (non-gated) OR accept auto-text as B7's letter. Recommend adding Agent record — 10 min.
5. `uv run pytest tests/scripts/omt/test_kb_*.py` → 21 green; then FULL suite `uv run pytest` (= e2e receipt).
6. `omt_tdd{op:done}` (GREEN state dangling from cycle 2) → `omt_complete{feature:feature_kb_akb, advance_to:Testing}` → verify → Done.
7. Update WORK.md line → done; mark PROJECT.md acceptance B items.

### Session-11 gotchas (must survive)
1. **TDD bootstrap chicken-and-egg BOTH sides**: TESTLIST state forbids ALL edits; `red` needs an EXISTING test node (exit 4 on missing file = no transition); `green` needs passing module. Sanctioned path: `omt_skip{scope:tests}` → write test → `red`; `omt_skip{scope:src}` → write impl → `green` (precedent: ledger 2026-08-02T19:47Z). Both used ×2 this session.
2. **Receipt round-robin enforced live**: `tests/scripts/omt/`, `scripts/omt/`, `.opencode/**`, `META_HARNESS.omt` all harness surface — ONE edit/file/e2e receipt; `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` refreshes; multi-region single-file transforms → uv-python via bash (META_HARNESS 3-site batch used this).
3. **harnessc closed-set coupling**: `@budget` rid must ∈ MEASURABLE∪REPORT_ONLY — removing `kb_index` from `harnessc.py` while `@budget kb_index` exists → check error. Sites must land SAME round (parallel files OK).
4. **Run `harnessc build` after META_HARNESS edits** (regenerates IR/projections; AGENTS.md content unchanged this time — kb edits land in IR only) — then e2e.
5. **Linter vs identifiers**: `[a-zA-Z]+` regex splits snake_case — any `is_*`/`can_*`/`should_*` identifier in CURATED text = stopword error. Auto-text exempt by design (length-only); curated must reword (doc.utils is the live case).
6. **TDD batch-N-tests warnings** (10/11 tests per file) — advisory, recorded, accepted (module-cohesive cycles).
7. **No DP_-prefixed classes exist** in real tree — layer rule is literal `DP_` (fixture must use `DP_Thing`, not `DPThing`).
8. **Duplicate class names** (4 real) — extractor keeps first-by-sorted-path; overlay keys bind to the FIRST occurrence's id.

## Session 10 (2026-08-02) — P0 non-gated steps 1-3 executed + validated live

- ✅ **Step 1 — sample append + validate**: backup → `.projects/meta/feature_kb_akb/kb.index.jsonl.pre_sample_append.bak` (NOT `.meta/.omt/` — `*.bak` there violates append-only R6 S1, harnessc check errors); 11 records appended → **73-record index** (62 curated + 11 code; ids unique; tiers 34/16/12/11). ALL 6 validations passed via `omt_kb_nav`: `CLASS_`→5, `CONTRACT_`→3, `DEP_`→3, `tag_type:TIER_CODE`→11, `"class.ToolRegistry"`→1, `list_sections file:"tools"`→9 tools records. Plugin `loadKbIndex` reads fresh per call (no cache) — appends visible immediately. **Ephemeral** — first real build wipes the append (durable form = overlay, step 3 ✅).
- ✅ **Step 2 — 6 `.kb.omt` bugs fixed in sources AND index**. Deviations from sess-9 checklist (verified vs `src/agentx/utils/`): `Xertion`→**`DIRECTORIES_DELETION_ALLOWED`** (checklist said EXCEPTION — no such symbol; checklist itself was corrupted), `btS_OP_VERSION`→**`APP_VERSION`**, **`SESSION_DEFAULT_TEMP_DIR`→`SESSION_DEFAULT_BASE_DIRECTORY`** (extra drift, not in checklist), `dirflz`→`utils_directories.py`, `valid_url`→`is_valid_url`; `persistence.kb.omt:17` trailing fix = added final `.`; `doc.utils` text rewritten accurate-to-source. Index patched via **uv-run python json script** (load/modify/dump, `ensure_ascii=True` matches existing style) — **Edit tool cannot match raw `\uXXXX` escapes** that Read renders as unicode.
- ✅ **Step 3 — `.meta/doc/omt++/code.kb.omt` overlay authored**: 16 records (3 contract + 5 class + 8 dep). `dep.tools_hybrid` split → 6 `dep.<Class>_<Target>` scheme edges; stopwords stripped from sample texts (would fail linter); refs enrichment only on `class.ToolRegistry` + `dep.Agent_ToolRegistry` (AST covers the rest). Validated: 16/16 parse clean, 0 style errors, max text 242c. Sample `src`/`line` values verified accurate vs real source.

### Session-10 gotchas (must survive)
1. **Overlay format quirk**: every overlay record REQUIRES an attr before ` : ` (use `tier=code`) — `split_payload(rest.strip())` strips the leading space, so an attr-less payload leaks into shlex attr parsing (text empty; apostrophes → "No closing quotation"). Documented in `code.kb.omt` header.
2. **Build CLI must** (step 6): add `class`/`contract`/`dep` to `KB_KINDS` for the overlay pass AND **EXCLUDE `code.kb.omt` from the curated `*.kb.omt` glob** (else overlay records emit as curated with wrong src/line).
3. **Test drift**: PROJECT says "12 `test_kb_*.py` tests" — actual **8** (`test_kb_compiler.py` only). `test_budget_fails_when_oversize` tests `check_budget` → **must be updated/replaced** when budget removed in step 6 (acceptance 12 wants budget-removed tests).
4. **WORK.md budget = 5120 B** — sess-9 verbose entry blew it to 6029 (harnessc error); sess-10 pointer style fixed to ~4970. Keep WORK.md a pointer; detail lives here.
5. **Gate layout re-verified**: `scripts/omt/`, `tests/scripts/omt/`, `.opencode/plugins/omt_`, `META_HARNESS.omt` ∈ `harness_paths` (receipt guard: 1st edit of clean file free, 2nd needs e2e); `src/` → `g.phase`+`g.kb`; `tests/` → `g.tests` canary; `.kb.omt`/index/`.projects` → non-gated.

### Resume point (sess 11 — GATED steps 4-10; RE-DECLARE `omt_phase{task_type:major_feature, phase:Programming, feature:feature_kb_akb, design_doc:.projects/meta/feature_kb_akb/PROJECT.md}` — TDD auto-activates; receipt: ONE edit/file/round)
4. `omt_tdd{op:testlist}` (JSON array!) → red `tests/scripts/omt/test_kb_ast_extract.py` (conventions: `sys.path.insert` scripts/omt, lazy import, tmp_path, class-per-behavior — see `test_kb_compiler.py`).
5. GREEN `scripts/omt/kb_ast_extract.py` (NEW — creation free) — design: §Session 8 AST extractor design + PROJECT.md v2.1 layer table (`/persistence/`→DP, no `/dp/`/`/controllers/`); coverage = ALL public classes; auto-text = bases+abstractmethods; composition via `self.x=Class()`+AnnAssign.
6. `kb_compiler.py` — functional `build` CLI: curated `.kb.omt` (EXCLUDING `code.kb.omt`) + AST skeleton + overlay merge → unified `kb.index.jsonl` + `kb.ir.json`; orphan overlay-key + orphan-ref checks; REMOVE `DEFAULT_BUDGETS`/`check_budget` + `harnessc.py:125` entry; UPDATE `test_budget_fails_when_oversize`.
7. `META_HARNESS.omt` — ONE batched edit: REMOVE `@budget kb_index max=32768` (l.245); ADD `@inject kb_bootstrap`; FIX `@msg kb_required` (`op:list`→`op:nav`, l.141).
8. `omt_kb_nav.ts` — per-query result bound (`max_records`, `truncated:true`) — P0 with 500-800 record index.
9. Rebuild (`uv run scripts/omt/kb_compiler.py build`) → validate via `omt_kb_nav` (CLASS_AGENT, TIER_CODE, list_sections, sync-after-edit).
10. `uv run pytest tests/scripts/omt/test_kb_*.py` green = e2e receipt → `omt_complete`.

## Session 9 (2026-08-02) — PROJECT.md v2.1 refinement (meta-loop, doc-only)

- ✅ Meta-loop pass per `workflows/meta_harness/loops/meta_harness_project.md` (focus: KB is for source code; user: **main goal = concepts+abstraction**). No code/harness edits — PROJECT.md + this file only.
- ✅ **7 drift points live-verified → fixed in PROJECT.md v2.1**: (1) "~45-55 records" vs **272 public classes** measured in `src/agentx`; (2) component table "kb_compiler ✅ exists" vs `main()` placeholder = build gap (critical path, now acceptance B2); (3) budget at **3 sites** (`META_HARNESS.omt:245`, `kb_compiler.py DEFAULT_BUDGETS`/`check_budget`, `harnessc.py:125`) — v2 named only the first; (4) layer table vs real tree (`/dp/`+`/controllers/` don't exist; actual `/persistence/`→DP, `/controller/`, `/tui/`, `*_view.py`/`*_screen.py` suffixes); (5) **gate msg bug**: `@msg kb_required` says `omt_kb_nav{op:list}` — invalid op (ops: nav|list_sections|cross_ref|quick_ref) → fix to `op:nav`; (6) sample-append **ephemeral** — wiped by first real build; port 11 texts → `code.kb.omt` keyed by extractor-stable ids (`dep.tools_hybrid` → `dep.<Class>_<Target>`) BEFORE first build; (7) rebuild trigger defined: `uv run scripts/omt/kb_compiler.py build`.
- ✅ **User decisions (sess 9)**: coverage = ALL public classes + auto-text floor (no significance filter — filters create `g.kb` consult gaps); doc-tier polish (xref/quick_ref/path-aware) DEFERRED to follow-up §C; main goal restated: concepts+abstraction.
- ✅ Acceptance re-tiered: **B = P0 code-tier critical path (13 items)**; **C = deferred doc-tier**. Impl plan P0/P1 with receipt batching (ONE `META_HARNESS.omt` edit round: budget removal + `@inject kb_bootstrap` + msg fix).
- ✅ PROJECT.md is single source (v2.1); on any disagreement with this file, **PROJECT.md v2.1 wins**.

### Resume point (v2.1 — start here)
**NON-GATED (safe, no omt_phase):**
1. Append 11 sample records → `.meta/.omt/kb.index.jsonl` (`cp` backup to /tmp/opencode first); validate via `omt_kb_nav`: `CLASS_`→5, `CONTRACT_`→3, `DEP_`→3, `tag_type:TIER_CODE`→11, `"class.ToolRegistry"`→1, `list_sections file:"tools"`→tools records. **Ephemeral proof** — wiped by first real build.
2. Fix 6 `.kb.omt` bugs (confirmed LIVE): `subsystems.kb.omt:17` (`aontpresist`→`agent_persist`, `v.taripol`→`volatile`), `:31` (`to`→`demo`, `Consisth`→`Console`), `:33` (add `TIER_REFERENCE` tag, `Xertion`→`EXCEPTION`, `dirflz`→`dir_utils`, `btS_OP_VERSION` cap), `architecture.kb.omt:19` (`Decisions`→`decisions`), `features.kb.omt:27` (`§12Arrabits`→`§12 Artifacts`), `persistence.kb.omt:17` (trailing format).
3. Author `.meta/doc/omt++/code.kb.omt` overlay — SEED = 11 sample texts ported to extractor-stable ids; then per-subsystem (tools → agent facade → controllers → view partners → …).

**GATED (harness-surface — RE-DECLARE `omt_phase{task_type:major_feature, phase:Programming, feature:feature_kb_akb}` in the new session — ledger unlocks expire ~7h; receipt: ONE edit per file per round):**
4. TDD red `tests/scripts/omt/test_kb_ast_extract.py`.
5. `scripts/omt/kb_ast_extract.py` (NEW — creation free) — design in §Session 8 below (pass1 symbols → pass2 class/contract/dep; ALL public classes; auto-text fallback; path+suffix layers per PROJECT.md v2.1 table; composition via `self.x=Class()`+AnnAssign).
6. `kb_compiler.py` — functional `build` CLI (curated + AST skeleton + overlay merge → unified index; orphan overlay-key + orphan-ref checks); REMOVE `DEFAULT_BUDGETS`/`check_budget` + `harnessc.py:125` entry.
7. `META_HARNESS.omt` — ONE batched edit: REMOVE `@budget kb_index max=32768` (l.245); ADD `@inject kb_bootstrap`; FIX `@msg kb_required` (`op:list`→`op:nav`, l.141).
8. `omt_kb_nav.ts` — per-query result bound (`max_records`, `truncated:true`) — P0 with 500-800 record index.
9. Rebuild (`uv run scripts/omt/kb_compiler.py build`) → validate via `omt_kb_nav` (CLASS_AGENT, TIER_CODE, list_sections, sync-after-edit).
10. `uv run pytest tests/scripts/omt/test_kb_*.py` green = e2e receipt.

PROJECT.md rewritten to v2 (source-code-primary, concept-altitude, **unbounded index**). The re-focus design is now single-sourced in PROJECT.md v2; `design_001` + `operation_spec_001` are SUPERSEDED. Implementation plan (10 steps) is laid out in PROJECT.md §"Implementation plan" — non-gated steps 1-4 safe to start; gated steps 5-10 need `omt_phase` + receipt.

## Session 8 (2026-08-02) — exploration + plan ready, ZERO edits made

### Done this session (analysis only — no src/data/harness edits)
- ✅ Full exploration of every relevant artifact: PROJECT.md v2, CURRENT_STATE, `kb_compiler.py` (library-only — CLI `main()` is a placeholder; index NOT auto-built by any script), `omt_kb_nav.ts` (4 ops, NO per-query result-cap, `quick_ref`=generic filter not curated workflows, `cross_ref`=id/tag/text match), `kb.index.jsonl` (62 curated records, 6 bugs confirmed LIVE at the lines below), sample `kb_code_tools_sample.jsonl` (11 records), all 6 `.kb.omt` source files, `src/agentx` tree (~100 .py: agent/model/{tools,reflection,goal,memory,policy} + agent/{controller,view,persistence,adapter,types,demo} + model/{ai,rag,session,coding,react,chat,program} + ui/{screens,tui,common} + utils), `test_kb_compiler.py` (7 test methods), `META_HARNESS.omt` (`g.kb` order=55 @ line 115; `@budget kb_index max=32768` @ line 245), receipt rules (`META_HARNESS.omt:214-218`).
- ✅ Confirmed the **build gap** (key blocker): `kb_compiler.py main()` returns 0 without building; `harnessc.py build_ir` (line 882) is the SEPARATE harness-corpus compiler, not KB. → Deliverable: make `kb_compiler.py build` functional (parse `.kb.omt` + AST-extract `src/agentx` + merge `code.kb.omt` overlay → unified `kb.index.jsonl` + `kb.ir.json`).
- ✅ Confirmed **receipt discipline** (META_HARNESS.omt:214-218): first edit of a CLEAN harness file is free BY DESIGN; second edit of SAME file needs e2e receipt; per-file (parallel OK); ONE receipt refresh per round; e2e test file is receipt-EXEMPT (edit tests freely). `scripts/omt/kb_ast_extract.py` = NEW file (creation free). `kb_compiler.py`/`omt_kb_nav.ts`/`META_HARNESS.omt` = existing clean harness files (first edit free, second needs receipt).
- ✅ 11-step plan confirmed as todo list (see Resume point).

### Resume point (precise — start here)
**NON-GATED (data/docs, safe, no omt_phase):**
1. Append 11 sample records → index + validate:
   `cp .meta/.omt/kb.index.jsonl /tmp/opencode/kb.index.jsonl.bak` then `cat .projects/meta/feature_kb_akb/kb_code_tools_sample.jsonl >> .meta/.omt/kb.index.jsonl`.
   Validate via `omt_kb_nav`: `nav CLASS_`→5, `nav CONTRACT_`→3, `nav DEP_`→3, `nav tag_type:TIER_CODE`→11, `nav "class.ToolRegistry"`→1, `list_sections file:"tools"`→tools records. Proves code-tier query path TODAY.
2. Fix 6 `.kb.omt` bugs (confirmed LIVE at these source lines):
   - `subsystems.kb.omt:17` `@doc aontpresist` → `@doc agent_persist`; text `v.taripol`→`volatile`.
   - `subsystems.kb.omt:31` `@doc to` → `@doc demo`; text `Consisth`→`Console`.
   - `subsystems.kb.omt:33` `@doc utils` tags=`SUBSYS_UTILS_REFERENCE` → add `TIER_REFERENCE`; text `Xertion`→`EXCEPTION`, `dirflz`→`dir_utils`, `btS_OP_VERSION`→`BITS_OP_VERSION` (cap fix).
   - `architecture.kb.omt:19` `@doc Decisions` → `@doc decisions`.
   - `features.kb.omt:27` `features_xref` text `§12Arrabits` → `§12 Artifacts`.
   - `persistence.kb.omt:17` `persist_xref` trailing format fix.
3. Verify `design_001_kb_akb.md` + `operation_spec_001_kb_operations.md` SUPERSEDED banners (added sess 7).
4. Author `.meta/doc/omt++/code.kb.omt` concept-text overlay (per-subsystem; template = the 11 sample records).

**GATED (harness-surface — `omt_phase` already declared `major_feature Programming feature_kb_akb`; receipt discipline applies):**
5. TDD red → create `scripts/omt/kb_ast_extract.py` (NEW) — AST skeleton extractor.
6. Integrate `scripts/omt/kb_compiler.py` — `build` CLI: curated `.kb.omt` + AST skeleton + `code.kb.omt` overlay merge → unified `kb.index.jsonl` (code tier) + `kb.ir.json`.
7. `META_HARNESS.omt` — REMOVE `@budget kb_index max=32768` (line 245); ADD `@inject kb_bootstrap`.
8. `omt_kb_nav.ts` — per-query result bound (`truncated` exists); `quick_ref` curated workflows (≥6); wire `cross_ref`.
9. Rebuild unified index → validate via `omt_kb_nav` (CLASS_AGENT, TIER_CODE, list_sections, sync-after-edit).
10. `tests/scripts/omt/test_kb_*.py` green (AST extract, sync, query, budget-removed) — this run = the e2e receipt.

### AST extractor design (ready to implement — `scripts/omt/kb_ast_extract.py`)
- **Pass 1 — collect symbols**: walk `src/agentx/**/*.py` via `ast`; for each `ClassDef` record `{name, file(repo-rel), line, bases(names), is_abc, abstractmethod_names, layer}`. Build global symbol table name→symbol.
- **Pass 2 — emit records** (3 kinds only, tier=`code`):
  - `contract.<Name>` — when `is_abc` (inherits `ABC`/`ABCMeta` OR has `@abstractmethod`s). refs→realizers (classes whose bases include Name).
  - `class.<Name>` — concrete. refs→bases (resolved to `class.`/`contract.` for project symbols) + compositions.
  - `dep.<Class>_<Target>` — per realization edge (class→project contract) + per composition edge (class→project-class attribute). refs→both endpoints.
- **Layer inference (path-based)**: `/utils/`→LAYER_UTIL · `/controller/`|`/controllers/`|`*_controller.py`→LAYER_CONTROLLER · `/view/`|`/screens/`|`/tui/`|`*_view.py`|`*_screen.py`→LAYER_VIEW · `DP_` prefix|`/persistence/`→LAYER_DP · `/model/`→LAYER_MODEL (default).
- **tags**: `CLASS_<NAME>`/`CONTRACT_<NAME>`/`DEP_<...>` + `TIER_CODE` + `LAYER_*`.
- **Composition detection**: `self.<attr> = <ProjectClass>(` in `__init__`/body + `AnnAssign` annotations → resolved against symbol table (project classes only; skip stdlib/3rd-party).
- **Overlay merge**: `code.kb.omt` keyed by record id overrides skeleton `text` + enriches `refs`; un-curated records keep a minimal auto-text (bases + abstractmethods) so coverage is comprehensive even before curation completes.
- **Concept-altitude filter**: class/contract/dep only (NO module/method); all project ClassDefs emitted (no floor; ~45-55 records expected).

### Standing principle (carried into PROJECT.md v2 — non-negotiable)
**KB records = concepts, not implementation.** Every record stays high-level: role + responsibility + connections (WHAT/WHY/CONNECTS-TO), never HOW (no full signatures, no field lists, no fallback-branch notes). Implementation lives in source; the record's `file:line` jumps there. Records are concepts (class/contract/dep), NOT files — drop per-file `module`; fold facade API into class `text` (no `method` kind).

### Done this session (session 7)
- ✅ Diagnosed 8 drift points between prior PROJECT.md and the sess-6 approved principle (5 code kinds vs 3; "AST drift-free/zero-maintenance" vs hybrid; no layer inference; single budget vs split; tag_type kind vs TIER; global gate vs path-aware; mixed acceptance; design docs current vs drifted).
- ✅ Measured budget reality: curated 23449 B / 62 records (core 13040/34, extended 6118/16, reference 4291/12); free 9319 B → only ~20 code records at 448 B/record avg — below ≥40 acceptance. Surfaced the budget fork.
- ✅ User decisions: (a) **index UNBOUNDED** — remove `@budget kb_index max=32768`; token cost is per-query (scoped+capped), not per-index; trimming harms the agent; (b) code kinds = class/contract/dep only; (c) design_001 + operation_spec_001 SUPERSEDED.
- ✅ Rewrote `PROJECT.md` to v2: standing principle, vision, architecture (AST skeleton + curated-text overlay), extraction contract (AST vs curated table), path-based layer inference, index schema, query semantics (verified), budget policy (unbounded + per-query bound), gate, tag taxonomy, components, acceptance split (A baseline-met / B re-focus deliverables), 6 .kb.omt bugs, superseded docs, risks, 10-step impl plan, decision log.
- ✅ Added SUPERSEDED banners to `design_001_kb_akb.md` + `operation_spec_001_kb_operations.md`.

### Done prior (session 6 — preserved)
- ✅ Audit via `omt_nav` + `omt_kb_nav` (no source search): 62 curated records, 0 code records live; `CLASS_`/`LAYER_`/`CONTRACT_` queries empty; `quick_ref`/`cross_ref` unimplemented.
- ✅ Read agentx tools subsystem source; authored **11 high-level code records** (3 contracts ISensor/IActuator/IToolRegistryPartner + 5 classes ToolSpec/ToolRegistry/FileSystemTool/RagSensorTool/SessionTool + 3 deps) → `kb_code_tools_sample.jsonl` (durable). NOT yet appended to live index.
- ✅ Verified plugin query semantics + gate scope (see findings below).

### NOT done — resume here (matches PROJECT.md v2 impl plan)

**Non-gated (docs/data — safe, no omt_phase):**
1. Append the 11 sess-6 records to `.meta/.omt/kb.index.jsonl` (backup first: `cp .meta/.omt/kb.index.jsonl /tmp/opencode/kb.index.jsonl.bak`; then `cat .projects/meta/feature_kb_akb/kb_code_tools_sample.jsonl >> .meta/.omt/kb.index.jsonl`). Index is NON-gated — safe.
2. Validate via `omt_kb_nav` (expect): `nav CLASS_`→5, `nav CONTRACT_`→3, `nav DEP_`→3, `nav tag_type:TIER_CODE`→11, `nav "class.ToolRegistry"`→1, `list_sections file:"tools"`→tools records. If all pass → code-tier query path proven.
3. Fix 6 corrupted `.kb.omt` records (see PROJECT.md §"Prior-resume checklist").
4. Author `code.kb.omt` concept-text overlay for code records (per-subsystem, template = sample).

**Gated (harness-surface — `omt_phase` + e2e receipt):**
5. `kb_ast_extract.py` — AST skeleton extractor (class/contract/dep) → feed `kb_compiler.py`.
6. `kb_compiler.py` — integrate AST skeleton + overlay merge; unified index; `code` tier.
7. `META_HARNESS.omt` — REMOVE `@budget kb_index max=32768` (line 245); ADD `@inject kb_bootstrap`.
8. `omt_kb_nav.ts` — per-query result bound (`truncated` exists); `quick_ref` workflows (≥6); wire `cross_ref`.
9. `.kb.omt` — author 14 missing `xref` records.
10. `tests/scripts/omt/test_kb_*.py` — AST extract, sync, query, budget-removed tests.

## Key findings (session 6 — must survive)
- **Gate scope**: `.meta/.omt/kb.index.jsonl` is NOT in `harness_paths`, NOT `src/`, NOT `tests/`, NOT protected → **editing it is non-gated** (safe for test populate; regenerable by `kb_compiler.py build`).
- **Plugin `omt_kb_nav` semantics** (`.opencode/plugins/omt_kb_nav.ts`):
  - `nav`: tag-prefix match (query token ending `_` or `:` → uppercase prefix on `tags`) OR full-text substring over `id+text+tags+tier`. So `query:"CLASS_"` works IF records carry `CLASS_*` tags; `query:"class.ToolRegistry"` works via full-text on `id` (symbol-precise lookup WITHOUT a dedicated `kind:` filter).
  - `tag_type`: filters **TIER only** (CORE/EXTENDED/REFERENCE/CODE) — NOT kind-prefix as design_001 claimed. DRIFT (now documented in PROJECT.md v2). `tag_type:"TIER_CODE"` works for code records.
  - `list_sections(file)`: filters records whose `src` includes `file`.
  - No `kind:` filter exists; tag-prefix + full-text covers code records.
- **Read of `src/` is exempt** from gates (only `edit_tools` on `src/` is gated by `g.kb`); reading source to author records is fine.
- **Sample records** are high-level concept altitude (see principle above) — the template for the AST extractor's output style + the `code.kb.omt` overlay.

## Budget reality (session 7 — measured)
```
kb_index budget (hard, compile-enforced): 32768 B  ← TO BE REMOVED (unbounded)
Current curated records:                  23449 B  (62 records)
  core      34 records  13040 B
  extended  16 records   6118 B
  reference 12 records   4291 B
Free for code (under old cap):            9319 B  → ~20 code records (below ≥40)
Sample code-record avg:                   ~448 B  (11 records / 4924 B)
```
Decision: index UNBOUNDED — keep all 62 curated + all code records; bound tokens per-query.

## Gate scope (verified)
- `.meta/doc/omt++/*.kb.omt` + `.projects/**` + `.meta/.omt/*.jsonl` → NOT in `harness_paths` or `src/` → editable without `omt_phase`/receipt/`g.kb`.
- `scripts/omt/kb_compiler.py` + `.meta/META_HARNESS.omt` + `.opencode/plugins/omt_kb_nav.ts` → IN `harness_paths` → receipt discipline applies (gated steps only).

---

*Updated: 2026-08-02 session 7 (PROJECT.md v2 — unbounded index, 3 kinds, hybrid AST+curated, design docs superseded) · session 8 (exploration+plan, ZERO edits) · session 9 (PROJECT.md v2.1 — coverage=all public classes+auto-text, doc-tier deferred §C, 7 live-verified drift fixes, P0/P1 re-tier; doc-only) · session 10 (P0 non-gated steps 1-3 DONE: sample append+validate, 6 .kb.omt fixes sources+index, code.kb.omt overlay 16 recs; PAUSED before gated step 4). Resume at `PROJECT.md` (v2.1) → here (§Session 10) → `kb_code_tools_sample.jsonl`.*
