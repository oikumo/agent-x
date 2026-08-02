# CURRENT_STATE — META HARNESS (improvement003, 2026-08-01)

> Gathered ONLY via META HARNESS artifacts + toolbox (omt_status, omt_list_sections, omt_nav,
> harness.report, .omt single source, WORK.md, git log). No source-code search (per loop rule).
> Base: improvement002/CURRENT_STATE.md + EXECUTION.md (OPT-B executed, committed 1f5fcef).

## 1. Delta since improvement002 (OPT-B executed)

| Surface | improvement002 | NOW (verified) | Δ |
|---|---|---|---|
| WORK.md (every startup) | 7767 B | 7767 B (54% of 14336) | stable — but see F1 |
| WORK.md scratchpad | 5692 B (93% → risk) | **1342/3072 B (44%)** | OPT-B DONE — risk retired |
| .omt corpus | 226 rec / 300 lines | **242 rec / 321 lines** | +16 `@doc gotcha.*` |
| nav.index.jsonl | 52 KB / 235 rec | 58588 B / 251 rec | +16 gotcha records |
| AGENTS.md | 2941 B (57%) | 2941 B (57%) | stable |
| tool_schemas | 1484 B (58%) | 1484 B (58%) | stable |
| harness.ir.json | 17429 B | 17429 B | stable |
| ledger | 32553 B hot | 35283 B hot (54% cap) + 127257 B 202607 archive | rotation by design |
| Gotcha access | auto-paid every session | on-demand `omt_nav "GOTCHA_"` (16 recs) | OPT-B DONE |

All measurable budgets OK per `harness.report` (compile fails on overflow). Git tree CLEAN
(improvement002 committed as `1f5fcef`; no uncommitted harness WIP).

## 2. improvement002 options re-verified (still open)

- **OPT-C (nav-index @var/@budget)**: OPEN — `omt_nav "VAR_"` → no results (verified today).
- **OPT-D (HDL-2 compiled predicates)**: OPEN — 8 gates still data-only; logic in TS ×7
  (`.opencode/lib/enforcer/` = mvc_after, nav_gate, phase_gate, receipt_guard, session_state,
  tdd_hats, think_gate — verified listing).
- **OPT-E (drift-class duplicates)**: OPEN — `.meta/omt_constants.json` (428 B, 2026-07-12) present;
  `thoughts.jsonl.bak` verified **byte-identical** to thoughts.jsonl (diff -q); `tdd_snapshots/` empty (0 files).
- **OPT-F (omt_think_* consolidation)**: OPEN — 18 tools still (5 omt_think_*); schema budget 58%.
- **OPT-G (harness-edit session mode)**: OPEN — OPT-B needed no 2nd edit so pain not re-felt,
  but round-robin recipe remains the standing cost for multi-edit harness work (GOTCHA_RECEIPT_ROUND_ROBIN).
- **OPT-H (TDD node normalization)**: OPEN — footgun now nav-indexed (GOTCHA_TDD_NODE) but not fixed.
- **OPT-I (evolution-loop prompt stale)**: OPEN — verified TODAY: step 3/4/5 say `./sandbox/meta/...`
  (practice = `.sandbox/meta/`); step 7 says "Update only the ./meta/META_HARNESS.md" (retired stub
  since R8; truth = .omt + projections). This is run #3 paying the reconciliation.
- **OPT-J (trivial @doc records)**: OPEN — 12 one-word `@doc ph.*`/`@doc tt.*` (.omt 209–220) +
  18 `@doc sec.*` (221–238) still hand-maintained; payloads duplicate `@fsm`/`@phase`/comment banners.
- **OPT-K (omt_status feature-health noise)**: OPEN — verified LIVE today:
  `improvement002.opt_b_gotchas_to_nav: overall 0% (R:0 A:0 D:0 I:0 T:0)` printed for a DONE,
  verified, committed option (same phantom class as improvement001's slug).
- **OPT-L (TS-side budgets unmeasurable)**: OPEN — harness.report still shows
  `digest_cap: -/1024 n/a (TS-pinned)`, `nav_tip: -/512 n/a (TS-pinned)`; `@inject session_bootstrap
  budget=1536` untracked. 3 of 6 budget knobs declaration-only.

## 3. New findings (improvement003)

1. **F1 — WORK.md DONE-narrative bloat**: 4 completed-task lines carry 3316 B of narrative
   (L24 R4=406 B, L33 feature_024=619 B, L59 DSL=634 B, L61 T-024=1657 B) — ~830 tokens paid
   **every session startup** for history already in git log + feature dirs. Budget-compliant (54%)
   but token-wasteful; the work_md budget measures compliance, not startup cost.
2. **F2 — omt_nav include_context redundancy**: `omt_nav{query:"SECTION:", include_context:true}`
   returned ~30 KB with heavy duplication (each hit re-prints overlapping neighbor windows —
   same `@doc sec.*` records repeated up to 4×). Context windows not deduped; paid per nav query.
3. **F3 — GOTCHA corpus has no staleness lifecycle**: 16 gotchas (~5.5 KB in .omt + index) are
   immortal — no date/validity marker, no verify path (contrast: TA: thoughts have omt_think_verify
   + stale ⚠️). A fixed underlying bug leaves a forever-paid gotcha in every `GOTCHA_` full-list query.
4. **F4 — evolution loop not in the harness corpus**: no `@doc`/`@flow` record points at
   `../../../workflows/meta_harness/loops/meta_harness_evolution.md`; each run re-reads the raw prompt + re-pays the
   OPT-I reconciliation. (Folds into OPT-I fix.)
5. **F5 — process state**: phase=Done, refactor unlock active (~8 h), e2e receipt fresh
   (omt_harness_e2e_last_run.json 2026-08-01 16:14). Pending product features unchanged:
   feature_001 (Petri Net), feature_002 (RAG) — scope unset. 6 TA: thoughts across 4 files live.

## 4. Architecture snapshot (condensed; unchanged since improvement001)

- Single source: `.meta/META_HARNESS.omt` (OMT-HDL v1; `@kind id k=v : payload`) → compiler
  `scripts/omt/harnessc.py` → projections (AGENTS.md, opencode.jsonc blocks, harness.ir.json,
  nav.index.jsonl, harness.report). NEVER hand-edit projections.
- Enforcement: omt_enforcer.ts + lib/enforcer/ ×7; 8 gates order-pinned 0–70 as data (HDL-1:
  gates-as-data, LOGIC in TS; TS↔IR parity via pin tests).
- Records (242): 23 @var · 9 @deny · 5 @protect · 5 @always · 3 @phase · 2 @fsm · 5 @hat ·
  8 @pred · 8 @gate · 21 @msg · 3 @state · 2 @inject · 100 @doc (incl. 16 gotcha.*) · 6 @budget ·
  18 @tool · 11 @flow · 10 @xref.
