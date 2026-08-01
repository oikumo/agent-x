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
- [x] **feature_024.no_tui_full_features** — DONE (2026-08-01): console parity for react/coding/models/agent/fast-agent via IUIProvider + 5 console REPL views + streaming. TDD 28 behaviors / 37 tests / 9 cycles; omt_done (1055 passed + 6 allowlisted); cmd_done latent bug FIXED (latest-per-test_node collapse + 4 pins); phase-exit coverage-gate skip override wired in `gates.py` cmd_validate_exit (skip-ledger consult — phase_gate.ts advertised it but never checked; TS parity + is_abstract filter deferred). Docs: analysis_001/design_001/operation_spec_001 + implementation_notes + test_report in the feature dirs.
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
- [x] **META HARNESS DSL** (refactor.meta_harness_dsl; supersedes refactor.meta_harness) — `.sandbox/meta_harness_refactor_plan.md` (anchor `a7163df`; workstreams R0–R8 **ALL DONE** 2026-07-26): ledger rotation · enforcer split (lib/enforcer/ ×7) · tdd/ package · docs single-source · think index append-only · budget pins (T5) · OMT-HDL-1 (`.meta/META_HARNESS.omt` + `scripts/omt/harnessc.py`; IR/nav.index/AGENTS.md/jsonc projections; AGENTS.md user-ADOPTED; META_HARNESS.md → GENERATED stub; 226 records 0 errors; suite 1011 + 3 known feature_018). Per-workstream narratives: git history of this file + plan §0 audit.
- [x] **feature_023.deep_harness_tests** <!-- id:T-023d prio:high agent:true --> — BUG-B live test redesigned (git-dirty-first); suite 105/105 ✓; dist/ deleted (proven unused); TA index reconciled.
- [x] **Evaluate META HARNESS DSL + verify implementation (fix if needed)** <!-- id:T-024 prio:high agent:true --> — DONE (2026-07-26). Evaluation VERIFIED GREEN (harnessc check 0 errors/226 records · --verify-projections no drift · live bun probe: nav tools answer from nav.index.jsonl + IR tool descriptions · opencode.jsonc splice correct; WIP adopted: IR-driven harness_paths exact/prefix + stale-entry compile error + TS↔IR sync pin + g.mvc/g.tdd_after 60/70 matching runtime call order + feature_006 dir guarded). All 4 fix candidates implemented: (1) **gate order pinned** — TestGateOrderIrPin (test_omt_enforcer_guard_source_pins.py) maps gate id→hook fn via GATE_IMPL (set-equality vs IR = forcing function) and asserts omt_enforcer.ts before/after call sequence == IR gates[].order ascending, duplicate-order rejected; (2) **@var doc_paths IR-driven** — nav_gate.ts isDocPath reads IR vars.doc_paths (comma string, trailing "/" = prefix else exact) with literal fallback + TestDocPathsIrSyncPin (mirrors the harness_paths F9 kill); (3) **numeric constants .omt-sourced** — test_thought_pattern_pin.py asserts UNLOCK_WINDOW_MS / LEDGER_CAP_BYTES TS==PY==@var unlock_window_ms/ledger_cap_bytes via _omt_var_int (hard-coded third copy deleted); (4) **harnessc.py robustness** — build_ir raises clean SystemExit on missing/non-integer @version instead of IndexError/ValueError traceback (+2 tests). Verification: tests/scripts/omt 112/112 (e2e receipt fresh) · harnessc check --verify-projections 0 errors · full suite 1021 passed + 3 known feature_018 ✓. Uncommitted WIP retained per instruction (no commit without user request).

---

## Agent Scratchpad (auto-managed, do not edit manually)

```
FEATURES DONE (docs in each .meta/.../FEATURE.md + test_report.md):
- feature_020 nav + e2e · feature_021 think · feature_022 think-v2 · feature_023.meta_harness_improvement (F14-F17) · feature_tui_dark_mode (default dark, `k` toggles, `Ctrl+Shift+T` 21 themes) · feature_024 console parity (react/coding/models/agent/fast-agent REPL + streaming via IUIProvider; 28 behaviors/37 tests).

RECURRING GOTCHAS — 16 nav-indexed: omt_nav{query:"GOTCHA_"} (improvement002/OPT-B → .omt @doc gotcha.*). Top-3 by cost kept inline:
- **TDD node-granularity:** declare red/green/refactor at the SAME test_node — red at `f.py::C::t` + green at `f.py` strands latest=red → omt_done blocked (recovery: omt_green at the exact red node).
- **omt_testlist behaviors MUST be a JSON array** (tdd cli.py json.loads); prose fails 'Expecting value: line 1 column 1'.
- **Receipt round-robin (harness edits):** per-file SECOND-edit guard on harness surface → ONE edit per file per e2e receipt (parallel OK), ONE refresh per round; the e2e test file itself is receipt-EXEMPT.

PENDING FEATURES (next work):
- feature_001.session_user_objectives_driven_by_Petri_Net — scope & success criteria unset.
- feature_002.rag_retrieval_augmented_generation — scope & success criteria unset.
```
