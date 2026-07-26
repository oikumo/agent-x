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
- [x] **feature_023.test_refactor_live_only** — Consolidated test suite: removed Node-runner fixtures (feature_022 tier tests, feature_023 harness tests, production hook effects TS, lifecycle e2e). Kept source-pin tests + live opencode binary tests. Expanded test_omt_live_opencode_guards.py from 6 to 17 tests covering all 13 live verification points (plugin loading, after-hook effects, before-hook guards, think-gate, TDD two-hats, MVC++ gate, phase transitions, omt_skip, risk weighting, per-file consult, session isolation). All static tests (68) and e2e receipt pass; live tests marked opencode_live (skipped without opencode binary).
- [x] **feature_tui_dark_mode** — TUI dark mode toggle + theme selector
- [x] **feature_023.production_hook_effects_test** — Test 6 (MVC++ F14b gate): ROOT CAUSE FIXED in omt_enforcer.ts:944 (`output?.args` → `input?.args` per SDK contract). Fixed error-message check in test_hook_effects_production.ts:314 (check for "hard MVC++ violation"). All tests pass: `npx tsx tests/scripts/omt/test_hook_effects_production.ts` and `uv run pytest tests/features/feature_023.meta_harness_improvement/test_omt_harness_improvement.py -v` (22 passed).
- [~] **META HARNESS DSL** (refactor.meta_harness_dsl; supersedes refactor.meta_harness) — executing `.ws/sandbox/meta_harness_refactor_plan.md` (baseline anchor `a7163df`; workstreams R0–R8). **Resume:** R0 ✓ · R6 ✓ (reindex+rewrite class DELETED, tombstone fold, compact digest, S3 fallback kept Tier 1c) · R1 ✓ (shared lib `.opencode/lib/omt_shared.ts` + 4 plugins rewired + pin retargets; verified: static 984+3 known, live smoke GREEN, receipt fresh) · **R2 ☐ ← RESUME HERE** (enforcer split → lib/enforcer/*) · R3 ☐ · R4 ☐ · R5 ☐ · R7 ☐ · R8(HDL) ☐. Static: 984 passed + 3 known feature_018 failures. Live suite REDUCED by directive: 17 tests/~22 runs → 1 minimal smoke (plugins load, tools execute, after-hooks fire; 36s) — guard coverage now static-only (source pins + SDK contract); real-binary probe recipes kept below. Receipt fresh. <!-- id:T-HDL prio:high agent:true -->
- [x] **feature_023.deep_harness_tests** <!-- id:T-023d prio:high agent:true --> — DONE this session. BUG-B live test redesigned (git-dirty-first per TA todo, replaces the flawed os.utime-only probe); live module 6/6 GREEN (72s, real opencode 1.18.3); full harness suite 105/105 GREEN (23s, excluding live module); e2e receipt refreshed (.meta/.omt/omt_harness_e2e_last_run.json @ 02:08:40Z); **dist/ deleted** (git-ignored, orphaned, opencode loads .ts directly — proven live with dist/omt_nav.js removed + omt_list_sections call); TA index reconciled (removed stale live-test todo + 2 vanished dist thoughts, re-verified 3 wrongly-dropped live thoughts). Uncommitted (per directive): BUG-A/BUG-B source fixes in omt_enforcer.ts + 5 test files.

---

## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (full docs in each .meta/.../FEATURE.md + test_report.md — grep those for detail):
- feature_019 fix: invalid CSS (font-family, white-space) kills entire Textual DEFAULT_CSS parse.
- feature_020 nav + e2e, feature_021 think, feature_022 think-v2 (tiers A/B1+D1/C/B2+E1+E2): all shipped, harness set 246/246.
- feature_023.meta_harness_improvement: F14-F17 fixed, 13 TDD behaviors, 99 tests passing, contract-pinning mechanized.
- feature_tui_dark_mode: default dark mode (textual-dark), `k` toggles dark/light, `Ctrl+Shift+T` opens theme selector (21 built-in themes).

RECURRING GOTCHAS (apply on every future task — these cost hours when re-discovered):
- opencode loader (sk/nk) requires ALL named exports of a plugin .ts be functions; tool objects aren't. → plugins export ONLY `export default async () => ({tool:{...}})` (mirrors omt_status.ts). Deterministic guard test_no_named_exports_except_default pins omt_think only; omt_status/omt_nav/omt_enforcer load-guard is future work.
- omt_done strict full-suite unreachable: 3 pre-existing feature_018 react_screen Textual/mock failures + 2 tdd_check tests reading REAL 8h-window ledger (pass only when no TDD session in-window). → exit phase via omt_complete{advance_to:Testing→Done}, never omt_done (feature_021 prior art).
- omt_think.ts and omt_enforcer.ts are THINK-GATED (carry TA: thoughts). Before editing: omt_think_list{path:...} to clear gate. omt_enforcer.ts:~965 has an ACCIDENTAL anchored TA: → whole-repo consult covers it.
- Guarded files (.opencode/plugins/*.ts, omt_think.ts, omt_enforcer.ts, opencode.jsonc) require e2e receipt ≥ mtime: refresh between edits via `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`. Batch each plugin's changes into ONE write when possible.
- Write tool aborts on large payloads (empty params emitted; small payloads fine). → chunked edit() + receipt refresh between chunks for guarded files.
- TESTLIST two-hats gate blocks tests/ creation (chicken-and-egg). → omt_skip{scope:tests} to bootstrap; ledger-audited. Prior art: feature_021, feature_022 tiers A/B1+D1/C/remainder.
- omt_testlist behaviors MUST be JSON array (tdd_check.py:403 json.loads). Prose strings fail with 'Expecting value: line 1 column 1'.
- **SDK contract (feature_023/F14): `tool.execute.after` payload has `args` on `input`, NOT `output`** — output={title,output,metadata} only. The AFTER hook must read `input?.args?.filePath` (genuine F14 fix).
- **F14 MIRRORED (feature_023 deep audit, 2026-07-19): the BEFORE hook is the OPPOSITE — `args` on `output`, input={tool,sessionID,callID} only.** a3ffb81 applied the after-hook fix to both hooks → every before-hook edit guard (protected/e2e-receipt/tests-canary/src-phase/TDD) silently dead. Live-confirmed via real `opencode run`: README.md edit landed with no unlock. Fixed; pinned by tests/scripts/omt/test_omt_enforcer_guard_source_pins.py + test_omt_live_opencode_guards.py.
- **Runner fixtures can't catch contract/path drift — only real-binary tests can.** Recipe: `opencode run --format json "<prompt>"` + jq tool_use events; `--pure` = A/B control; `--print-logs --log-level DEBUG` for bootstrap; assert FILE-STATE byte-identical, snapshot+restore probe targets. opencode loads `.opencode/plugins/*.ts` directly (dist/ not loaded).
- **e2e receipt guard is a SECOND-EDIT guard** (enforcer omtHarnessE2eStatus: git-dirty check :554) — first edit of a clean harness file is allowed BY DESIGN. Pinch point: each `edit()` call on a guarded file bumps mtime > receipt → next edit blocked until `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` re-runs. Plan multi-edit refactors as receipt-rebuild cycles.
- **dist/ DELETED (2026-07-20):** `.opencode/dist/` was a git-ignored orphaned build dir (no tsconfig, no build script in .opencode/package.json, no tracked file referenced it). Proven UNUSED live: `mv dist/omt_nav.js{,.d.ts} /tmp && opencode run ... omt_list_sections` → tool still registered & callable from `.opencode/plugins/omt_nav.ts`. DO NOT recreate dist/ unless an NPM-distribution plugin (Plugin Creation Guide §NPM pattern) is added — local plugins load `.ts` directly via Bun.
- **BUG-B live-test recipe (git-dirty-first):** `omtHarnessE2eStatus` is content-`git status --porcelain`-based, NOT mtime-only — `os.utime`/touch on a CLEAN file NEVER engages it (returns ok early). To live-pin the guard: snapshot original bytes → Python `write_bytes(probe_content)` to dirty the file (content change ⇒ git-dirty; mtime=now ⇒ receipt stale) → `opencode run` a single edit of the probe marker with prompt forbidding omt_phase/omt_skip/bash/git/restore → assert file bytes == probe (guard blocked) and `err` contains "unverified changes" → `finally: write_bytes(before)`. Pinned in test_omt_live_opencode_guards.py::test_plugin_file_edit_blocked_by_e2e_receipt_guard.
- **RESOLVED (meta_harness_dsl R6 S1):** the omt_think_reindex over-prune bug class died with the tool — the rewrite-by-filter index path was DELETED (grep-is-truth made it redundant AND destructive-prone on the untracked index). The index is now append-only: add/verify/remove-tombstone events, latest-wins fold; digest stale-join keys on normalized thought TEXT (F28), path:line is display-only. Pre-R6 snapshot: `.meta/.omt/thoughts.jsonl.bak`.
- **Plugin behavioral probes WITHOUT the live suite (meta_harness_dsl R6 recipe):** `bun /tmp/probe.ts` with `await import("<abs>/.opencode/plugins/omt_<x>.ts")` + `await m.default()` gives the real tool map/hooks — imports resolve from `.opencode/node_modules` regardless of cwd, and REPO_ROOT = process.cwd() (run from repo root). Syntax gate: `cd .opencode && bun build --target=bun --outfile=/dev/null plugins/<f>.ts`. Used for the R6 tombstone/F28/C1 lifecycle probe; snapshot+restore `.meta/.omt/thoughts.jsonl` around probes that append records.
- **Write-tool large-payload workaround (confirmed this session):** full-file Writes of ~750-line guarded plugins abort with empty params. Working recipe: `rm <file>` (bash — the receipt guard returns ok on non-existent files), then rebuild via sequential `cat >> ... << 'QUOTED_EOF'` chunks (~100 lines each, quoted heredoc prevents $/` expansion), one e2e receipt refresh at the end.
- **CLOSED (meta_harness_dsl R0, F14):** opencode.jsonc `plugin` array was npm-only per official docs — all 4 `omt_*` entries REMOVED (local plugins auto-load from `.opencode/plugins/`), line-3 comment fixed to `plugins/` plural, and all 19 omt_* tool permissions made explicit (F35). Live-verified: tools register + e2e receipt refreshed.

R1 DONE (2026-07-25) — carried-forward notes:
- FINDING (pre-existing, still OPEN — separate bug_fix): `omt_nav`/`omt_list_sections` with an explicit `file` arg return empty — runGrep's grep argv lacks `-H`, so with a SINGLE input file grep omits the `file:` prefix and the `file:line:content` parser matches nothing; whole-corpus (multi-file) calls work. Candidate fix: add `"-H"` to the grep argv in runGrep + live-verify the single-file branch.
- `.gitignore` `!.opencode/lib/` negation in place — R2's `lib/enforcer/*` files inherit the fix.
- Live-suite marker change: the R6 compact TA digest prefix is `💡 TA:` (the old `THINK-ANYWHERE` string no longer exists — stale assertion class if old live tests are ever resurrected).

RECURRING GOTCHAS (new this session):
- **Receipt-rebuild ROUND-ROBIN (multi-file guarded refactors):** the e2e-receipt guard is PER-FILE (target mtime vs receipt). Optimal batch: ONE edit per file per round across all guarded files (parallel edit calls OK — different files), then ONE `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` refresh per round. Rounds = max hunks per file, not the sum. Watch for e2e SOURCE PINS asserting things the refactor moves (constants, factory shapes): update the e2e FIRST with transitional shape-agnostic asserts — the e2e file is receipt-EXEMPT (rel==OMT_HARNESS_E2E_TEST → guard ok), editable any number of times; tighten to final strict asserts at the end.
- **Plugin factory ctx (plan Appendix B3, verified in installed d.ts):** `{project, client, $, directory, worktree}`; repo root = `worktree ?? directory` (directory is cwd — a subdir launch breaks it exactly like process.cwd()). Post-R1 every plugin factory calls `initOmtShared(worktree ?? directory)`; all shared-lib path getters are LAZY functions (module-level constants would capture the pre-init cwd — the old nav META_FILES bug class). `tool()` in the SDK is identity (no execute wrapping) — direct `.execute(args, ctx)` calls in probes hit the real function.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.

IN PROGRESS (resume here):
- **META HARNESS DSL** — see task list entry (T-HDL): R0/R1/R6 DONE, **resume at R2** (enforcer split → `lib/enforcer/*`) per `.ws/sandbox/meta_harness_refactor_plan.md`.
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.

CURRENT DEBUG:
- (pruned per R7 T2 — DONE-feature debug narratives live in their feature dirs under .meta/.../6.testing/; scratchpad keeps CURRENT/RECURRING content only)
```

