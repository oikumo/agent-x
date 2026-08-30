# Feature 040: Net Composition Supervisor

> **Status:** [x] Done (2026-08-30)
> **Created:** 2026-08-30
> **Project:** meta_harness_concurrent (core roadmap 2/3 — PROJECT.md D1–D18)
> **WORK.md task:** feature_040.net_composition_supervisor

---

## Summary

The **composition layer** of the meta_harness_concurrent single-net SSOT (D16): `omt_net{op:splice}` — atomic structural transactions on the supervisor net with modes `add` / `remove` (token policies forbid·reroute·drain, IDEA-002 §3.2) / `disable` (≡ remove-with-policy + `kind:"net_disable"` + overlay archive visibility, §11 #8) / `undo` (inverse splice replay from the ledger) / `repair` (sidecar↔overlay revision realignment, D12) — and `omt_net{op:sync}`, the net↔reality bootstrap + resync (§5.1 first-call: materializes the supervisor skeleton with boundary ports `feature_ready`/`resource_token`/`goal_satisfied`; then derives a deterministic **proposal** from `.projects/` + WORK.md + feature dirs that is surfaced for agent approval and applied via `splice`, never silent — D4/D11). The composition view (`supervisor.overlay.json`, §1.4) is **derived** from the flat union net (`f{N}_` prefix membership, boundary-port wiring, disabled set) at every save, so overlay↔net drift is impossible by construction. Every structure-changing op re-runs the 9 conformance vectors as the regression gate (§5.0 trigger matrix), and `omt_complete` gains the D7 drift-check exit hook (`omt_net{op:invariant}` at every exit, fail-open).

## Scope (one sentence — what "done" looks like)

`omt_net{op:splice}` (all five modes) and `omt_net{op:sync}` (bootstrap + proposal) work against the three-file bundle with atomic saves, `net_splice`/`net_disable`/`net_sync` ledger records, and 9-vector conformance regression; the overlay is populated/derived with `f{N}_` subnets + boundary ports; `omt_complete` surfaces net↔ledger drift at exit; `synthesize` stays cleanly reserved (feature_042); sentinel + e2e stay green.

## Task type

**minor_feature**

---

## Deferred (explicit)

- `synthesize` op (goal→net template composition) → feature_042 (optional phase-2).
- Resource capacity places (`agent_attention`, `src_edit_capacity`, …) + serial-mirror semantics → feature_041.
- `project.py` lifecycle-event auto-sync triggers (`new|link|close|…` → `omt_net{op:sync}` hook wiring) → feature_041+ (the `sync` op itself ships here, tested).
- WORK.md net-projection render (md→net proposals) → feature_045 (phase-2, D17).

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_040.net_composition_supervisor/` | [x] |
| Analysis | _declaration only (minor_feature)_ — design basis: IDEA-002 v4 §1.4/§3/§5/§11 (`.projects/meta/meta_harness_concurrent/ideas/`) | — | [x] |
| Design | _declaration only (minor_feature)_ — canonical op taxonomy IDEA-002 v4 §5.0; overlay-as-derived-view; subnet lifecycle chain template | — | [x] |
| Implementation | `scripts/omt/net/{state,cli}.py` + `scripts/omt/net_check.py` + `.opencode/plugins/omt_net.ts` + `.opencode/lib/enforcer/phase_gate.ts` (drift hook) | — | [x] |
| Testing | Test report | `6.testing/features/feature_040.net_composition_supervisor/` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
