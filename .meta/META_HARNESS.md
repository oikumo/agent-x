# META_HARNESS — OMT++ Enforcement Quick Reference
# GUID:META_HARNESS | VERSION:2.0 | FOR:llm-agent-grep-glob

# ============================================================
# SECTION:RULES — Core Enforcement Rules (grep:RULE_)
# ============================================================
RULE_R1: src/edit REQUIRES omt_phase{task_type,phase,scope}
  task_type: bug_fix|minor_feature|major_feature|new_screen|refactor|test|docs
  phase: Analysis|Design|Programming|Testing
  scope: one-sentence "done" definition

RULE_R2: major_feature|new_screen REQUIRES design_*.md on disk
  scaffold: uv run scripts/omt/new_feature.py "<name>" --type major_feature|new_screen

RULE_R3: TDD AUTO-ACTIVATES for major_feature|new_screen in Programming phase
  sequence: omt_testlist → omt_red → omt_green → omt_refactor → omt_done

RULE_RIGOR: Artifact requirements by task_type
  bug_fix|minor_feature|refactor|test → phase declaration ONLY
  major_feature|new_screen → phase + design doc
  docs → no phase required

# ============================================================
# SECTION:TDD — TDD State Machine (grep:TDD_)
# ============================================================
TDD_TS: TESTLIST — omt_testlist{behaviors,feature}
TDD_RD: RED — omt_red{test_node,target_src,feature} → tests/ ONLY (fail verified)
TDD_GN: GREEN — omt_green{test_node,feature} → src/ ONLY (pass)
TDD_RF: REFACTOR — omt_refactor{test_node,feature} → src/ ONLY (green, auto-revert on break)
TDD_DN: DONE — omt_done{feature} → full suite + coverage gaps + dangling reds check

TDD_HAT_RED: tests/ edits ALLOWED, src/ edits BLOCKED
TDD_HAT_GREEN: tests/ edits BLOCKED, src/ edits ALLOWED
TDD_HAT_REFACTOR: tests/ edits BLOCKED, src/ edits ALLOWED (revert if tests break)
TDD_HAT_DONE: neither (validation only)

TDD_TRUE_RED: AST+pytest verify — must import target src, fail on missing behavior (not syntax)
TDD_COVERAGE_GAPS: public src/ methods without test calls → blocks phase exit
TDD_DANGLING_REDS: tests declared RED never turned GREEN → blocks phase exit

# ============================================================
# SECTION:COMPONENTS — Enforcement Components (grep:COMP_)
# ============================================================
COMP_ENF: .opencode/plugins/omt_enforcer.ts — gate plugin (tool.execute.before/after)
COMP_STS: .opencode/plugins/omt_status.ts — omt_status tool
COMP_NAV: .opencode/plugins/omt_nav.ts — feature_020 navigation tools (omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref)
COMP_THINK: .opencode/plugins/omt_think.ts — feature_021 think-anywhere tools (omt_think, omt_think_list, omt_think_remove)
COMP_LNT: scripts/omt/mvc_check.py — MVC++ linter
COMP_TDD: scripts/omt/tdd_check.py — TDD engine (9 subcommands)
COMP_SCAF: scripts/omt/new_feature.py — feature scaffolder
COMP_LG: .meta/.omt/ledger.jsonl — audit log (phase/skip/complete records)
COMP_RUL: opencode.jsonc, AGENTS.md — config + system rules

# ============================================================
# SECTION:ERRORS — Hard Blocks (grep:ERR_)
# ============================================================
ERR_V2M: View imports Model (ui/←model.*) — BLOCK
ERR_M2V: Model imports View/UI (model/←ui.*) — BLOCK
ERR_PRT_ABC: Abstract Partner not ABC+@abstractmethod — BLOCK

# ============================================================
# SECTION:WARNINGS — Soft Alerts (grep:WRN_)
# ============================================================
WRN_SQL_DP: SQL outside DP classes (¬*_db.py has SQL) — TOAST
WRN_GOD_CTL: Controller >300 lines — TOAST
WRN_CTL_UI: print()/console in Controller — TOAST

# ============================================================
# SECTION:PROTECTED — Gate-Protected Files (grep:PROT_)
# ============================================================
PROT_FILES: README.md, uv.lock, LICENSE, .env*, tests/ (requires omt_skip{scope:tests})

# ============================================================
# SECTION:ESCAPE — Override Hatch (grep:ESC_)
# ============================================================
ESC_SKIP: omt_skip{reason,scope:src|tests|nav|all} → logged to ledger
ESC_SCOPE_SRC: unlocks src/ edits without phase
ESC_SCOPE_TESTS: unlocks tests/ edits (canary approval)
ESC_SCOPE_NAV: unlocks feature_020 nav gate (grep/glob on docs no longer require prior omt_nav)
ESC_SCOPE_ALL: unlocks all including PROT_FILES (except .env*)

# ============================================================
# SECTION:EXIT — Phase Completion (grep:EXT_)
# ============================================================
EXT_COMPLETE: omt_complete{feature,advance_to:Design|Programming|Testing|Done}
  → verifies phase artifacts + TDD validate-exit + syncs WORK.md[x]

# ============================================================
# SECTION:STATUS — Status Check (grep:STS_)
# ============================================================
STS_CMD: uv run scripts/omt/tdd_check.py status{--check.py status
STS_OUT: phase, TDD_state, pending_items, unlock_expiry

# ============================================================
# SECTION:NAV — Navigation Enforcement (grep:NAV_)
# ============================================================
NAV_020: feature_020.meta_harness_navigation — mandatory doc navigation before grep/glob/read
NAV_TOOLS: omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref (opencode plugin tools)
NAV_FILES: .opencode/plugins/omt_nav.ts (implementation), AGENTS.md (enforcement), META_HARNESS.md (docs)
NAV_ENFORCEMENT: scoped gate in omt_enforcer.ts — blocks grep/glob on doc paths until nav used; read & src/non-doc searches exempt; omt_skip{scope:nav} escape; AGENTS.md "MANDATORY" section
NAV_TAGS: SECTION:, RULE_, ERR_, WRN_, CMD_, QUICK_, XREF_, TT_, PHASE_, FEAT_ (grep-friendly prefixes)
NAV_WORKFLOW: omt_nav{query} → omt_list_sections → omt_cross_ref → omt_quick_ref (fallback to grep only if no results)

# ============================================================
# SECTION:THINK — Think Anywhere (feature_021) (grep:THINK_)
# ============================================================
THINK_021: feature_021.meta_harness_think_anywhere — persistent inline TA: thought-tags
THINK_TOOLS: omt_think, omt_think_list, omt_think_remove, omt_think_verify, omt_think_suggest (opencode plugin: .opencode/plugins/omt_think.ts; omt_think_reindex deleted in meta_harness_dsl R6 — append-only index, grep-is-truth)
THINK_FORMAT: <comment> TA: [<category>: ] <thought> — e.g. # TA: gotcha: mutates history
THINK_SYNTAX: .py/.toml/.sh/.yml→#  | .ts/.js/.mjs/.jsonc→//  | .md/.mdx→<!-- -->  | .css→/* */  | .json→DENIED
THINK_PROTECTED: TA: refused on .env*, README.md, uv.lock, LICENSE, .json (no comments)
THINK_INDEX: .meta/.omt/thoughts.jsonl — append-only sidecar {ts,path,line,category,thought}; inline TA: is source of truth
THINK_GATE: thinkGateDecision({hasThoughts,consulted}) → block edits to TA:-carrying files until omt_think_list consulted
THINK_GATE_NOT_SKIP: think-gate NOT bypassable by omt_skip (safety-relevant); only omt_think_list clears it
THINK_DIGEST: first tool result of each session carries the compact TA: digest (counts + per-file counts + stale ⚠️ + pointer — meta_harness_dsl R6 S7) — live path is tool.execute.after (feature_023 Tier 1c; inert session.start hook deleted R6)
THINK_CONSULT: omt_think_list writes {kind:"think_consult"} to ledger → clears think-gate

# ============================================================
# SECTION:PATHS — Key Filesystem Paths (grep:PTH_)
# ============================================================
PTH_GUIDE: .meta/software_development_process/omt_agent_guide.md
PTH_DESIGN: .meta/software_development_process/4.design/features/feature_XXX/
PTH_TEST: .meta/software_development_process/6.testing/features/feature_XXX/
PTH_WORK: WORK.md
PTH_RULES: AGENTS.md

# ============================================================
# SECTION:TREE — Decision Tree (grep:TREE_)
# ============================================================
TREE_SRC: src edit? → omt_phase → (major|new_screen)? → design_*.md → (Programming)? → TDD(RD→GN→RF→DN)
TREE_TST: tests edit? → canary|TDD_RED
TREE_DOC: docs edit? → no_phase

# ============================================================
# SECTION:CMDS — All Tools (grep:CMD_)
# ============================================================
CMD_OMT_PHASE: omt_phase{task_type,phase,scope,feature?,design_doc?,tdd?}
CMD_OMT_SKIP: omt_skip{reason,scope}
CMD_OMT_COMPLETE: omt_complete{feature,advance_to}
CMD_TDD_LIST: omt_testlist{behaviors,feature}
CMD_TDD_RED: omt_red{test_node,target_src,feature}
CMD_TDD_GREEN: omt_green{test_node,feature}
CMD_TDD_REFACTOR: omt_refactor{test_node,feature}
CMD_TDD_DONE: omt_done{feature}
CMD_LINT: uv run scripts/omt/mvc_check.py [path]
CMD_SCAFFOLD: uv run scripts/omt/new_feature.py "<name>" --type major_feature|new_screen
CMD_STATUS: omt_status{include_ledger?}
CMD_NAV: omt_nav{query,file?,tag_type?,include_context?} — grep-based doc navigation (feature_020)
CMD_LIST_SECTIONS: omt_list_sections{file?} — list all SECTION: headers
CMD_CROSS_REF: omt_cross_ref{xref} — resolve XREF_ cross-references
CMD_QUICK_REF: omt_quick_ref{workflow?} — get QUICK_ workflow patterns
CMD_THINK: omt_think{path,thought,line?,category?} — insert inline TA: thought-tag (feature_021)
CMD_THINK_LIST: omt_think_list{path?,category?,query?} — grep TA: retrieval + clears think-gate
CMD_THINK_REMOVE: omt_think_remove{path,line} — remove a TA: line + reconcile index

# ============================================================
# SECTION:PHASES — Phase Names (grep:PHASE_)
# ============================================================
PHASE_ANALYSIS: Analysis
PHASE_DESIGN: Design
PHASE_PROGRAMMING: Programming
PHASE_TESTING: Testing
PHASE_DONE: Done

# ============================================================
# SECTION:TASK_TYPES — Task Type Values (grep:TT_)
# ============================================================
TT_BUG_FIX: bug_fix
TT_MINOR_FEATURE: minor_feature
TT_MAJOR_FEATURE: major_feature
TT_NEW_SCREEN: new_screen
TT_REFACTOR: refactor
TT_TEST: test
TT_DOCS: docs

# ============================================================
# SECTION:QUICK — Common Agent Queries (grep:QUICK_)
# ============================================================
QUICK_START_MAJOR: omt_phase{tt:major_feature,ph:Analysis,sc:"..."} → new_feature.py → design → omt_complete{advance_to:Design} → omt_phase{ph:Programming} → TDD cycle
QUICK_START_MINOR: omt_phase{tt:minor_feature,ph:Design,sc:"..."} → code → omt_complete{advance_to:Testing}
QUICK_START_BUG: omt_phase{tt:bug_fix,ph:Programming,sc:"..."} → fix → test → omt_complete{advance_to:Testing}
QUICK_TDD_RED: omt_red → write failing test in tests/ → gate verifies true RED
QUICK_TDD_GREEN: omt_green → write minimal src/ code → test passes
QUICK_TDD_REFACTOR: omt_refactor → improve src/ → auto-revert if tests break
QUICK_TDD_DONE: omt_done → full suite + coverage check
QUICK_SKIP_SRC: omt_skip{reason:"emergency",scope:"src"} (logged)
QUICK_SKIP_TESTS: omt_skip{reason:"canary approved",scope:"tests"} (logged)
QUICK_STATUS: omt_status → phase, unlock, artifacts, lint, next phases, WORK.md next
QUICK_LINT: uv run scripts/omt/mvc_check.py [file|dir]
QUICK_NAV_DOCS: omt_nav{query:"SECTION:"} → omt_list_sections → omt_cross_ref{xref} → omt_quick_ref{workflow} (feature_020 mandatory before grep/glob/read)

# ============================================================
# SECTION:XREF — Cross-Reference Map (grep:XREF_)
# ============================================================
XREF_GUIDE: omt_agent_guide.md §2(Phase), §11.4(TDD), §12(Artifacts), §13(Checklist), §14(Do/Don't), §16(Mistakes)
XREF_MVC: mvc_check.py validates: ERR_V2M, ERR_M2V, ERR_PRT_ABC, WRN_SQL_DP, WRN_GOD_CTL, WRN_CTL_UI
XREF_TDD: tdd_check.py subcommands: testlist,start,green,refactor,done,gate,after-edit,status,validate-exit
XREF_SCAFFOLD: new_feature.py creates: FEATURE.md, plan/PLAN.md under .meta/.../2.requirements/features/feature_XXX.<slug>/
XREF_LEDGER: .meta/.omt/ledger.jsonl — JSONL lines: {ts,kind:phase|skip|complete,session,task_type,phase,scope,feature,design_doc,tdd_mode}
XREF_WORK: WORK.md — task list with [x]/[~]/[ ]/![], auto-synced by omt_complete
XREF_NAV: .opencode/plugins/omt_nav.ts — feature_020 navigation tools (omt_nav, omt_list_sections, omt_cross_ref, omt_quick_ref)
XREF_NAV_ENF: .opencode/plugins/omt_enforcer.ts — first-tool-result nav reminder (session.start retained, inert in opencode 1.18.3; feature_023 Tier 1c moved the live path to tool.execute.after), AGENTS.md mandatory requirement
XREF_THINK: .opencode/plugins/omt_think.ts — feature_021 think-anywhere tools (omt_think, omt_think_list, omt_think_remove)
XREF_THINK_GATE: .opencode/plugins/omt_enforcer.ts — thinkGateDecision + hasConsultedThoughts + before-hook think-gate

# ============================================================
# FOOTER
# ============================================================
# GATE: mechanical, no manual discipline
# USE: grep "SECTION:" for sections | grep "RULE_" for rules | grep "CMD_" for tools | grep "ERR_" for blocks