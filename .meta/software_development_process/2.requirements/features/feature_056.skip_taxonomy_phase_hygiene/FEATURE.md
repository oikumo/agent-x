# Feature 056: Skip Taxonomy Phase Hygiene

> **Status:** [~] In progress (Programming)
> **Created:** 2026-09-06
> **Project:** meta_harness_6 · Wave 3 / A2+A3 (eval `.sandbox/meta_harness_6_evaluation.md` §5)
> **WORK.md task:** paused meta_harness_6 program execution (Wave 3)

---

## Summary

Two behaviors in one minor feature. **A2 skip_purpose_taxonomy**: `omt_skip` gains an
optional `purpose: canary|emergency|break_glass|override` arg (scope-aware default:
`scope=tests` → `canary`, else `override`), so the 266 opaque historical skips become
signal — `omt_status` reports the friction:evasion split and `harnessc check` warns when
uncategorized bypasses cross `@var skip_override_warn_per_week`. **A3 phase_hygiene**:
phase records auto-expire after `@var unlock_window_ms` (expired records neither unlock
nor shadow — kills the GOTCHA_TESTS_CANARY_SHADOW class beyond the ordering rule) and
`omt_status` lists dangling (declared-never-completed, expired) phases with one-call
resume (`omt_phase` re-declare) / abandon (`omt_phase{phase:"abandoned"}` tombstone).

## Scope (one sentence — what "done" looks like)

`purpose:` on omt_skip with scope-aware default + friction:evasion:nav report in
omt_status + check-time override/week warning + window-enforced unlock expiry with
abandon-tombstones + dangling-phase list with one-call abandon/resume; full suite green,
all 12 budgets green, e2e receipt refreshed.

## Task type

minor_feature

---

## Behaviors

1. **A2.1 purpose arg**: `omt_skip{reason, scope?, purpose?}` accepts only
   `canary|emergency|break_glass|override` (rejects anything else); omitted purpose
   defaults to `canary` for `scope=tests`, `override` otherwise; the effective purpose
   is written on the ledger skip record and echoed in the tool result.
2. **A2.2 friction report**: `omt_status` default output gains a 7-day skip line —
   `Skips 7d: N (friction F · nav-escapes V · evasion E, warn>E_T/week)` where
   friction = canary|emergency|break_glass, nav-escapes = override+scope=nav,
   evasion = override+any-other-scope; unmarked historical skips classify via the
   A2.1 default rule.
3. **A2.3 override alarm**: `harnessc check` emits a non-blocking warning (exit stays 0)
   when 7-day evasion exceeds `@var skip_override_warn_per_week` (default 5);
   counting is a pure, pinned function; a missing/unreadable ledger fails open silent.
4. **A3.1 auto-expire**: `getActiveUnlock` / `getActiveFeaturePhase` ignore records
   older than `@var unlock_window_ms` — including session-matched ones (the shadow
   hole: a stale session phase no longer shadows a later tests-approval, and stale
   `scope=all` no longer opens protected paths). A session whose records are all
   expired resolves to no-unlock (fail-closed; re-declare). `hasFastPathUnlock` /
   `hasNavUnlock` keep their semantics (C2 owns them — out of scope).
5. **A3.2 abandon tombstone**: `omt_phase{task_type, phase:"abandoned", feature, scope}`
   tombstones the feature's latest dangling phase (`{kind:phase, phase:abandoned,
   abandons:<phase>}`); unlock selectors skip tombstones; nothing dangling → message,
   no write. `phase:"abandoned"` is taught point-of-use (status printer + @state), not
   added to the phase arg describe (tool_args headroom).
6. **A3.3 dangling list**: `omt_status` lists expired dangling (feature,phase) pairs —
   a phase record with no later `complete{feature,phase}` and no later abandon
   tombstone — oldest-first capped at 10, each with the exact one-call resume and
   abandon commands; plus a `Dangling phases: D (K expired)` count line.
7. **Budgets stay green**: tool_args/tool_schemas/nav_index are within ~13/76/174 B of
   their caps — the one-liner grows ≤34 B, the new `purpose` describe is funded by
   trims to redundant arg describes, no new @tool/@doc/@msg records; only @var
   (free), @state (ir_json only), @xref ledger fields, and one @flow example change.

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_056.skip_taxonomy_phase_hygiene/` | [ ] |
| Analysis | Analysis doc | `3.analysis/features/feature_056.skip_taxonomy_phase_hygiene/analysis_001_*.md` | [ ] |
| Design | Design doc | `4.design/features/feature_056.skip_taxonomy_phase_hygiene/design_001_*.md` | [ ] |
| Implementation | Impl notes | `5.implementation/features/feature_056.skip_taxonomy_phase_hygiene/` | [ ] |
| Testing | Test report | `6.testing/features/feature_056.skip_taxonomy_phase_hygiene/` | [ ] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
