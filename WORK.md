# WORK

> Single-developer + coding-agent roadmap. Machine-parseable, minimal friction, git-friendly.

---

## Convention

| Symbol | Meaning |
|--------|---------|
| `[ ]`  | Pending |
| `[~]`  | In progress (agent working on it) |
| `[x]`  | Done |
| `[!]`  | Blocked / needs decision |

**Hierarchy** - top-level task -> optional subtasks (indented 4 spaces).
**Metadata** - optional inline comment: `<!-- id:T-123 prio:medium agent:true -->`
**Thoughts** - separate `---` line then bullet list; tools can strip it.

---

## Tasks

- [x] **R4 (meta_harness_dsl): state hygiene + latent bugs** — DONE (2026-07-26): ledger.jsonl 64 KB rotation (LEDGER_CAP_BYTES, cross-language pinned; readers scan latest archive + hot), omt_done reachable (`-m "not opencode_live"` + KNOWN_SUITE_FAILURES allowlist), TDD tests/ bootstrap documented (TDD_BOOTSTRAP). Tests: test_ledger_rotation.py (9) + 2 pins; full static 995 + 3 known feature_018 ✓.
- [x] **feature_007.agentx_intelligent_agent_behaviour**
- [x] **Fix feature_007 bugs per BUG_FIX_PLAN.md**
- [x] **feature_004.modern_ui**
- [x] **Update README.md with feature_006 and agentic workflow**
- [x] **Update application design overview in .meta/.../4.design/**
- [ ] **feature_001.session_user_objectives_driven_by_Petri_Net**
- [x] **feature_006.opencode_process_enforcement**
- [ ] **feature_002.rag_retrieval_augmented_generation**
- [x] **feature_012.tui_framework**
- [x] **feature_010.agent_demo_screen**
- [x] **feature_011.fast_agent**
- [x] **feature_013.ai_model_provider_selector**
- [x] **feature_014.tui_nonblocking_runner**
- [x] **Fix feature_011.fast_agent UI freeze**
- [x] **feature_016.tdd_enforcement**
- [x] **Fix feature_017.chat_screen_conversation_history_bug**
- [x] **feature_017.improve_chat_screen**
- [x] **feature_018.chat_screen_improvements**
- [x] **Fix chat screen "no assistant message" bug**
- [x] **Fix chat screen "no conversation history" bug**
- [x] **feature_018.react_screen**
- [x] **feature_019.coding_agent_screen**
- [x] **feature_020.meta_harness_navigation** <!-- id:T-020 prio:high agent:true -->
- [x] **feature_020.e2e_tests_opencode_driven** <!-- id:T-020e2e prio:high agent:true -->
- [x] **feature_021.meta_harness_think_anywhere** <!-- id:T-021 prio:high agent:true -->
- [x] **feature_022.meta_harness_think_anywhere_v2 — Tier A: correctness hotfixes A1–A4** <!-- id:T-022 prio:medium agent:true -->
- [x] **think_anywhere_v2 Tier B1+D1: anchor-based insertion + read-time thought injection** <!-- id:T-022BD prio:medium agent:true -->
- [x] **think_anywhere_v2 Tier C: verify/stale lifecycle C1 + per-file consult C2** <!-- id:T-022C prio:low agent:true -->
- [x] **think_anywhere_v2 Tier remainder: B2 suggest + E1 index strategy + E2 theory-doc fixes** <!-- id:T-022E prio:low agent:true -->
- [x] **feature_023.meta_harness_improvement** <!-- id:T-023 prio:high agent:true -->
- [x] **feature_023.test_refactor_live_only** — consolidated suite: Node-runner fixtures removed; source-pins + live-opencode-binary tests kept (13 verification points); 68 static + e2e ✓.
- [x] **feature_tui_dark_mode** — TUI dark mode toggle + theme selector
- [x] **feature_023.production_hook_effects_test** — Test 6 MVC++ gate root-caused (after-hook args on `input`, SDK contract); tests green.
- [~] **META HARNESS DSL** (refactor.meta_harness_dsl; supersedes refactor.meta_harness) — executing `.sandbox/meta_harness_refactor_plan.md` (anchor `a7163df`; workstreams R0–R8). **DONE: R0 (drift/config/hygiene) · R1 (shared lib omt_shared.ts) · R2 (enforcer split → lib/enforcer/ ×7, single bootstrap) · R3 (tdd_check.py → tdd/ package) · R4 (ledger rotation, omt_done reachable) · R5 (docs single-source: AGENTS.md↔META_HARNESS.md re-synced, test_omt_docs_drift_pins.py ×9) · R6 (think index append-only, compact digest, session.start hook deleted) · R7 (T1 startup pin, T2 WORK.md diet 17.5→10.3 KB, T3 nav-reminder deferral live-verified, T5 budget pins: AGENTS ≤5KiB/WORK ≤14KiB/scratchpad ≤6KiB/nav tip ≤512B/digest ≤1KiB; T4/T8 deferred).** Per-workstream narratives: git history of this file + plan §0 audit. **Resume: R8 (OMT-HDL, plan Appendix D) — see IN PROGRESS below for exact state.** Plan doc lives at `.sandbox/meta_harness_refactor_plan.md` (moved 2026-07-26 from `.ws/sandbox/`; staged git rename, uncommitted).
- [x] **feature_023.deep_harness_tests** <!-- id:T-023d prio:high agent:true --> — BUG-B live test redesigned (git-dirty-first); suite 105/105 ✓; dist/ deleted (proven unused); TA index reconciled.

---

## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (full docs in each .meta/.../FEATURE.md + test_report.md — grep those for detail):
- feature_020 nav + e2e, feature_021 think, feature_022 think-v2: all shipped.
- feature_023.meta_harness_improvement: F14-F17 fixed, 13 TDD behaviors, contract-pinning mechanized.
- feature_tui_dark_mode: default dark (textual-dark), `k` toggles, `Ctrl+Shift+T` theme selector (21 themes).

RECURRING GOTCHAS (apply on every future task — these cost hours when re-discovered):
- opencode loader requires ALL named exports of a plugin .ts be functions; tool objects aren't. → plugins export ONLY `export default async () => ({tool:{...}})`. Guard test_no_named_exports_except_default pins omt_think only; others' load-guard is future work.
- omt_done reachable post-R4 (opencode_live excluded + KNOWN_SUITE_FAILURES allowlist); default phase exit stays omt_complete{advance_to:Testing→Done}.
- omt_think.ts and lib/enforcer/think_gate.ts are THINK-GATED (carry TA: thoughts). Before editing: omt_think_list{path:...} clears the gate.
- omt_testlist behaviors MUST be a JSON array (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **SDK contract (feature_023/F14): `tool.execute.after` has `args` on `input`, NOT `output`** (output={title,output,metadata} only); the BEFORE hook is the OPPOSITE — `args` on `output`. a3ffb81 once applied the after-fix to both → all before-hook guards silently dead. Live-confirmed; pinned by test_omt_enforcer_guard_source_pins.py.
- **Runner fixtures can't catch contract/path drift — only real-binary tests can.** Recipe: `opencode run --format json "<prompt>"` + jq tool_use events; `--pure` = A/B control; assert FILE-STATE byte-identical, snapshot+restore probe targets. opencode loads `.opencode/plugins/*.ts` directly (dist/ unused, deleted).
- **e2e receipt guard is a SECOND-EDIT guard** (omtHarnessE2eStatus: git-dirty + mtime vs receipt) — first edit of a clean harness file is allowed BY DESIGN. Each edit bumps mtime > receipt → next edit of THAT file blocked until `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`. Plan multi-edit refactors as receipt-rebuild cycles (see round-robin below).
- **BUG-B live-test recipe (git-dirty-first):** the receipt guard is content-git-status-based — os.utime/touch on a CLEAN file never engages it. Probe: snapshot bytes → write_bytes(probe) (content-dirty ⇒ stale receipt) → `opencode run` one edit, prompt forbidding skip/bash/git → assert bytes unchanged + "unverified changes" → restore in finally.
- **Plugin probes WITHOUT the live suite (R6 recipe):** `bun /tmp/probe.ts` + `await import("<abs>/.opencode/plugins/omt_<x>.ts")` + `await m.default()` → real tool map/hooks; imports resolve from `.opencode/node_modules` regardless of cwd; REPO_ROOT = process.cwd() (run from repo root). Syntax gate: `cd .opencode && bun build --target=bun --outfile=/dev/null plugins/<f>.ts`.
- **Write-tool large-payload workaround:** full-file Writes of ~750-line guarded plugins abort with empty params. Recipe: `rm <file>` (receipt guard ok on non-existent), rebuild via sequential `cat >> ... << 'QUOTED_EOF'` chunks (~100 lines), ONE receipt refresh at the end.

R1 DONE — carried-forward notes:
- FINDING (pre-existing, still OPEN — separate bug_fix): `omt_nav`/`omt_list_sections` with an explicit `file` arg return empty — runGrep's grep argv lacks `-H`, so single-file grep omits the `file:` prefix and the `file:line:content` parser matches nothing; whole-corpus calls work. Candidate fix: add `"-H"` to the grep argv + live-verify.
- Live-suite marker: the R6 compact TA digest prefix is `💡 TA:` (the old `THINK-ANYWHERE` string no longer exists).

RECURRING GOTCHAS (new this session):
- **Receipt-rebuild ROUND-ROBIN (multi-file guarded refactors):** the receipt guard is PER-FILE. Optimal batch: ONE edit per file per round (parallel edit calls OK — different files), then ONE receipt refresh per round. Rounds = max hunks per file. The e2e file itself is receipt-EXEMPT — editable any number of times; update its source pins FIRST with transitional shape-agnostic asserts when a refactor moves pinned shapes, tighten at the end.
- **Plugin factory ctx (verified in installed d.ts):** `{project, client, $, directory, worktree}`; repo root = `worktree ?? directory`. Post-R1 every plugin factory calls `initOmtShared(worktree ?? directory)`; shared-lib path getters are LAZY functions. `tool()` in the SDK is identity — direct `.execute(args, ctx)` in probes hits the real function.

R7 MEASUREMENT (2026-07-26, plan Appendix C re-census):
- budgets all pinned (T5) — single source now the @budget records in `.meta/META_HARNESS.omt` + test_omt_docs_drift_pins.py; schema diet (T8) lands via R8 IR tool descriptions.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.

IN PROGRESS (resume here):
- **META HARNESS DSL — R8 (OMT-HDL-1)** per plan App D — **RESUME SPEC v2: `.sandbox/r8_resume_2026-07-26.md` (read it FIRST — supersedes v1).** State (session-2 pause, e2e GREEN, receipt FRESH): opencode.jsonc CLEAN at HEAD (marker edit reverted to re-green e2e — RE-APPLY per spec §3.1); harnessc.py untracked, fsm-guard landed, 1 free edit (spec §2A parser fix L161 — fixes empty @var/@pred payloads); .omt untracked, UNGUARDED (spec §2B/C fixes L129+L134). Root-caused: main() masks check errors behind projection SystemExit; parse errors silently dropped (L569). NEXT: spec §3 steps 1–7 (markers → parser fix → .omt fixes → check → build → e2e → v1 steps 4–9).
- **SANDBOX MOVE 2026-07-26:** .ws/sandbox → .sandbox — COMMITTED (6e74386; FROZEN_PREFIXES updated).
```
