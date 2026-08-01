# CURRENT_STATE — META HARNESS (improvement001, 2026-08-01)

> Gathered ONLY via META HARNESS artifacts + toolbox (omt_status, omt_list_sections, omt_nav,
> omt_quick_ref, harness.report, .omt single source). No source-code search (per loop rule).

## 1. Identity & architecture (HDL-1)

- Single source of truth: `.meta/META_HARNESS.omt` — **OMT-HDL v1** DSL (300 lines, ~226 records;
  grammar: `@kind id k=v : payload`, `#` comments, refs `@kind.id`).
- Compiler: `scripts/omt/harnessc.py` (`check` / `build` / `--verify-projections`).
- Projections (NEVER hand-edited): `AGENTS.md` (system rules), `opencode.jsonc` harnessc blocks,
  `.meta/.omt/harness.ir.json` (17.4 KB — consumed by TS plugins), `.meta/.omt/nav.index.jsonl`
  (52 KB, 235 records — consumed by nav tools), `harness.report`.
- Enforcement is mechanical: `.opencode/plugins/omt_enforcer.ts` (composition root) +
  `.opencode/lib/enforcer/` ×7 (phase_gate, tdd_hats, think_gate, nav_gate, receipt_guard,
  mvc_after, session_state) + `opencode.jsonc` denies. **HDL-1 = gates as data; LOGIC stays in TS**;
  TS↔IR parity kept by pin tests (gate order, doc_paths, harness_paths, numeric constants).

## 2. Record inventory (.omt)

| Kind | Count | Role |
|---|---|---|
| @var | 23 | single-sourced constants (windows, caps, paths, tool sets) |
| @deny | 9 | NEVER bash/read/toplevel rules → jsonc |
| @protect | 5 | .env* hard; README/uv.lock/LICENSE skip-all |
| @always | 5 | standing rules (git status, META.md, phase, artifacts, green tests) |
| @phase + @fsm | 3 + 2 | §12 artifact matrix; phase lifecycle + TDD two-hats FSM |
| @hat | 5 | TDD hat edit-scopes (testlist/red/green/refactor/done) |
| @pred | 8 | closed gate-condition vocabulary (TS owns builtins) |
| @gate | 8 | enforcer concerns as data, order-pinned: nav 0, protect 10, receipt 20, tests 30, phase 40, think 50, mvc-after 60, tdd-after 70 |
| @msg | 21 | block/warn texts (ERR_/WRN_) |
| @state | 3 | ledger (rotate 64 KB, hot+monthly archive), thoughts (append-only sidecar; inline `TA:` truth), receipt (rewrite) |
| @inject | 2 | session_bootstrap (≤1536 B) + file_thoughts (≤1024 B); ONE per trigger; conversation-resident |
| @doc | ~70 | nav-indexed knowledge corpus (RULE_/COMP_/NAV_/THINK_/…) |
| @budget | 6 | compile-enforced token budgets (build errors on overflow) |
| @tool | 18 | omt_* tool registry (perms → jsonc; one-line descriptions → IR) |
| @flow | 11 | QUICK_ workflow patterns |
| @xref | 10 | cross-reference map |

## 3. Token-cost surfaces (the F32/F33 control panel)

| Surface | Current | Budget | Pays |
|---|---|---|---|
| AGENTS.md | 4 273 B | 5 120 B (83%) | **every turn** (system prompt) |
| 18 tool schemas | 1 484 B | 2 560 B | **every turn** |
| session bootstrap + nav tip + TA digest | ≤ ~1.5 KB | 512 + 1024 | **every turn** (conversation-resident) |
| WORK.md | 12 117 B on disk (9 954 B counted) | 14 336 B | **every session startup** |
| └ Agent Scratchpad | 4 994 B | 6 144 B (81%) | every session startup |
| nav.index.jsonl | 52 KB (235 rec) | — | on disk; answers are small/on-demand |

All budgets OK per `harness.report` (compile-fails on overflow).

## 4. Runtime behavior (as experienced this session)

- `omt_status`: phase=Done, unlock 8 h window, artifact checklist, lint baseline (0 err/34 warn),
  ledger tail, WORK.md next task (feature_001).
- `omt_list_sections` / `omt_nav` / `omt_quick_ref` answer from the compiled index with compact
  one-line records (file:line + text). Nav gate: grep/glob on doc paths blocked until nav used;
  read exempt; `omt_skip{scope:nav}` escape.
- **Gap observed:** `@var`/`@budget` records are NOT nav-indexed — `omt_nav "LEDGER_CAP"` and
  `omt_nav "BUDGET"` return no results. Constants are only answerable by reading files.
- Ledger: `ledger.jsonl` 30 KB hot + `ledger-202607.jsonl` 127 KB archive (rotation proven).

## 5. Recurring friction (WORK.md scratchpad — costs tokens when re-discovered)

1. **Receipt-guard round-robin**: per-file second-edit guard → ONE edit per harness-surface file
   per e2e receipt; multi-file harness refactors need many receipt refreshes (each = a pytest run).
2. **TDD node granularity**: red at `f.py::C::t` + green at `f.py` leaves latest=red → blocks
   `omt_done` (recovery: re-declare green at the exact red node).
3. **TDD bootstrap**: TESTLIST blocks tests/ creation → new test files need `omt_skip{scope:tests}`.
4. **TS plugins don't hot-reload**; Python-side gate changes re-read live.
5. **SDK contract pins**: before/after hook `args` placement — pinned by guard-source-pin tests.
6. **KNOWN_SUITE_FAILURES** shape-pinned; grow + pin in the same session.

## 6. Hygiene observations (artifact-level)

- `.meta/omt_constants.json` — parallel constants file duplicating @var/`@fsm` data
  (UNLOCK_WINDOW_MS, VALID_TASK_TYPES, VALID_TRANSITIONS). Not a listed projection in the .omt →
  **drift-class duplicate** (consumers unverified — verification step required before action).
- `.meta/.omt/thoughts.jsonl.bak` — byte-identical stale backup of thoughts.jsonl (2026-07-25).
- `.meta/.omt/tdd_snapshots/` — present, empty.
- AGENTS.md carries a **Tools table duplicating the tool descriptions** that already ride the
  system prompt as schemas (double payment per turn).
- WORK.md scratchpad carries ~5 KB of gotchas every session; most are harness-work-specific and
  only relevant in a minority of sessions.

## 7. Process state

- All R0–R8 DSL workstreams DONE; feature_020–024 DONE; pending: feature_001 (Petri Net),
  feature_002 (RAG) — scope unset.
- Uncommitted harness WIP: `scripts/omt/tdd/{state,cli,gates}.py` + `test_ledger_rotation.py`
  dirty (no-commit-without-request).
- e2e receipt fresh (2026-08-01 15:36).
