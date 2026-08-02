# CURRENT_STATE — META HARNESS (improvement002, 2026-08-01)

> Gathered ONLY via META HARNESS artifacts + toolbox (omt_status, omt_list_sections, omt_nav,
> omt_quick_ref, harness.report, .omt single source, WORK.md). No source-code search (per loop rule).
> Base: improvement001/CURRENT_STATE.md (same day) — this doc records the VERIFIED DELTA + new findings.

## 1. Delta since improvement001 (OPT-A executed)

| Surface | improvement001 | NOW (verified) | Δ |
|---|---|---|---|
| AGENTS.md | 4273 B (83%) | **2941 B (57% of 5120)** | OPT-A DONE (−1332 B/turn) |
| WORK.md scratchpad | 4994 B (81%) | **5692 B (93% of 6144)** | +698 B — budget nearly full |
| tool_schemas | 1484 B | 1484 B (58% of 2560) | headroom |
| harness.ir.json | 17.4 KB | 17429 B | stable |
| nav.index.jsonl | 52 KB / 235 rec | 52412 B / 235 rec | stable |
| ledger | 30 KB hot + 127 KB archive | 32553 B hot + 127257 B 202607 archive | rotation by design |
| .omt source | 300 lines | 300 lines / 30180 B / 226 records | unchanged |

All budgets OK per `harness.report` (compile fails on overflow).

## 2. improvement001 options re-verified (still open)

- **OPT-B (scratchpad→@doc GOTCHA_)**: OPEN, now URGENT — scratchpad at 93%; next gotcha additions
  risk a `harnessc build` budget FAILURE (budgets are compile errors, and WORK.md is agent-edited
  outside the compiler's control). `omt_nav "GOTCHA_"` → no results (verified).
- **OPT-C (nav-index @var/@budget)**: OPEN — `omt_nav "VAR_"` → no results (verified).
- **OPT-D (HDL-2 compiled predicates)**: OPEN — long game; gates still data-only, logic in TS ×7.
- **OPT-E (drift-class duplicates)**: OPEN — `.meta/omt_constants.json` (428 B, 2026-07-12) still
  exists; `.meta/.omt/thoughts.jsonl.bak` still byte-identical stale; `.meta/.omt/tdd_snapshots/` empty.
- **OPT-F (omt_think_* consolidation)**: OPEN — 18 tools still; less urgent (schema budget 58%).
- **OPT-G (harness-edit session mode)**: OPEN — improvement001 EXECUTION.md re-validated the pain
  (2 receipt refreshes for 3 sequential harnessc.py edits).
- **OPT-H (TDD node normalization)**: OPEN — footgun still documented in WORK.md scratchpad.

## 3. New findings (improvement002)

1. **The evolution-loop prompt itself is stale** (`../../../workflows/meta_harness/loops/meta_harness_evolution.md`):
   - step 3/4/5 path `./sandbox/meta/...` ≠ actual practice `.sandbox/meta/...` (improvement001 used `.sandbox`);
   - step 7 "Update only the ./meta/META_HARNESS.md" predates R8 — that file is a retired
     non-compiled stub (1155 B); truth = `.meta/META_HARNESS.omt` + projections. improvement001
     had to burn tokens reconciling this; every future loop run re-pays it.
2. **omt_status feature-health noise**: status prints `improvement001.opt_a_slim_agents_md: overall 0%`
   although OPT-A is DONE and verified — the slug lives in the ledger but has no feature dirs under
   the process phases, so health scans 0%. A misleading line paid on every omt_status call.
3. **Trivial one-word @doc records**: 12 records (`@doc ph.*`, `@doc tt.*`, .omt lines 209–220) carry
   payloads that are just the name itself ("Analysis", "bug_fix") — duplicating data already in
   `@fsm phase states=` / `@phase applies=`. 18 `@doc sec.*` records (221–238) similarly mirror the
   .omt comment banners. Compiler-derivable; hand-maintained today.
4. **Unmeasurable budgets**: `@budget nav_tip` / `digest_cap` report as "n/a (TS-pinned)" and
   `@inject session_bootstrap budget=1536` is not tracked in harness.report at all — the compiler
   cannot measure TS-side bytes, so 3 of 6 budget knobs are declaration-only.
5. **Session-resident injections working as designed**: nav tip + TA digest present in omt_status
   output; `omt_quick_ref` answers from compiled index (.omt:275) — the F32/F33 control panel is live.

## 4. Architecture snapshot (unchanged from improvement001, condensed)

- Single source: `.meta/META_HARNESS.omt` (OMT-HDL v1; `@kind id k=v : payload`).
- Compiler `scripts/omt/harnessc.py` → projections: AGENTS.md, opencode.jsonc blocks,
  harness.ir.json (TS plugins), nav.index.jsonl (nav tools), harness.report. NEVER hand-edit.
- Enforcement mechanical: omt_enforcer.ts + lib/enforcer/ ×7; 8 gates order-pinned 0–70 as data;
  HDL-1 = gates-as-data, LOGIC in TS; TS↔IR parity via pin tests.
- Records: 23 @var · 9 @deny · 5 @protect · 5 @always · 3 @phase · 2 @fsm · 5 @hat · 8 @pred ·
  8 @gate · 21 @msg · 3 @state · 2 @inject · 84 @doc · 6 @budget · 18 @tool · 11 @flow · 10 @xref.

## 5. Process state

- Phase: Done; refactor unlock active (~8 h). e2e receipt fresh (2026-08-01 15:51).
- Uncommitted harness WIP (no-commit-without-request): `scripts/omt/tdd/{state,cli,gates}.py` +
  `test_ledger_rotation.py` dirty — any edit there needs a fresh e2e receipt first.
- Pending product features: feature_001 (Petri Net), feature_002 (RAG) — scope unset.
