# Feature 055: Gate Preflight

> **Status:** [~] In progress (Programming)
> **Created:** 2026-09-06
> **WORK.md task:** meta_harness_6 Wave 2/A4 (PROJECT.md §The program)

---

## Summary

`omt_status{op:"preflight", tool, path}` returns the **ordered gates that will fire** for a
 prospective (tool, path) edit plus the **clearing action for each** — a read-only projection
 of the `@gate` table that kills the deny-learn-retry loop (ONE call instead of N denials).
 meta_harness_6 Wave 2/A4, evaluation §5: `omt_q op:plan` already predicts the raw chain —
 A4 builds the clearing-action layer on it and surfaces it in the process-context tool.

## Scope (one sentence — what "done" looks like)

`omt_status` accepts `op=preflight` with `tool` (default edit) + `path`, returning ordered
 before-gate rows (fired / blocked / halts-chain, real verdicts via the `runBeforeGatesDry`
 sibling omt_q uses) each with a concise clearing action, plus after-gate notes projected
 from the IR; full suite green, budgets green, e2e check added.

## Task type

minor_feature (§12 declaration-only)

---

## Design (key decisions)

1. **Reuse over reimplementation**: before-chain verdicts come from `runBeforeGatesDry`
   (gate_driver.ts) on a synthetic GateCtx — same idiom as `omt_q op:plan`. No second
   gate-evaluation engine to drift.
2. **`GateDecision` gains optional `fired`/`stop` flags** (gate_driver.ts, additive —
   omt_q's `predicted_chain` mapping untouched): `fired=false` marks when=-missed gates;
   `stop=true` marks chain halts (g.protect override / g.tests). This is what makes
   "gates that WILL fire" honest.
3. **Clearing actions live as a TS map** (`CLEARING_ACTIONS` in omt_status.ts) keyed by
   gate_id — the .omt `@msg` records already embed the same escapes as prose (meta_harness_5
   #9); the map is the concise actionable distillation, consistency-pinned by tests. NOT a
   new `@gate clear=` attribute: nav_index budget headroom is ~281B (Wave 3/B1 owns it).
4. **After-gates are notes, not predictions** (g.mvc/g.tdd_after verdicts depend on the
   edit content): IR projection (on=after + tools match + when= path match via a local
   path_in matcher; non-path when= fires conservatively).
5. **No "TA:" literal added to omt_status.ts** (keeps g.think off the file itself — one
   less ceremony on the preflight surface), and no "dynamic"/"p.split" (e2e pins).
6. **Preflight short-circuits before the lint/tdd subprocesses** of the default status
   path (fast, read-only, no ledger writes — omt_status stays ledger-clean).

## Phase artifacts (traceability)

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_055.gate_preflight/` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_055.gate_preflight/implementation_notes.md` | [x] |
| Testing | Test report | `6.testing/features/feature_055.gate_preflight/test_report.md` | [x] |
