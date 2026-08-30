# Feature 039: Adaptive Net Engine

> **Status:** [x] Complete (2026-08-30)
> **Created:** 2026-08-30
> **Project:** meta_harness_concurrent (core roadmap 1/3 — PROJECT.md D1–D18)
> **WORK.md task:** feature_039.adaptive_net_engine

---

## Summary

The harness-owned Petri-net **engine** for the meta_harness_concurrent SSOT layer (D16): a stdlib-only Python clone-in-spirit of the shipped `src/agentx/model/petri_net/` library living in `scripts/omt/net/` (`errors`/`model`/`analysis`/`io` + `state` + `conformance` + `cli`), parity-proven by the 9 shared conformance vectors (`shared/petri-net/conformance/analysis-v1/`), with **zero runtime import of `src/`** (D2). On top of the engine, `state.py` implements the three-file net bundle store (`META_NET.petri.json` v1 structure+M0 · `net_state.sidecar.json` live marking+revision · `supervisor.overlay.json` composition view) with atomic saves + rollback and name-based marking rebase (D6/D11/D13), and the single `omt_net` tool (D10) ships the canonical closed op enum `probe|fire|splice|sync|synthesize|invariant` (IDEA-002 v4 §5.0) with `probe`/`fire`/`invariant` implemented and `splice`/`sync`/`synthesize` reserved as clean not-implemented envelopes (feature_040+).

## Scope (one sentence — what "done" looks like)

`omt_net{op:probe|fire|invariant}` works against the three-file net bundle (bootstrap-ordered §5.1: clean "net not bootstrapped" envelope when absent), the engine passes all 9 conformance vectors from pytest, `omt_net` is registered (META_HARNESS.omt @tool + harnessc build + TS plugin) with the v4-canonical op enum, sentinel stays green.

## Task type

**minor_feature**

---

## Deferred (explicit)

- `splice`/`sync`/`synthesize` op implementations → feature_040 (composition) / feature_042 (synthesis).
- `omt_complete`-exit drift-check hook wiring (D7 cadence) → feature_040/041 (the `invariant` op itself ships here, tested).
- Subnet overlay population (`f{N}_` prefixes, boundary ports) → feature_040.

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_039.adaptive_net_engine/` | [x] |
| Analysis | _declaration only (minor_feature)_ — design basis: IDEA-001/IDEA-002 v4 (`.projects/meta/meta_harness_concurrent/ideas/`) | — | [x] |
| Design | _declaration only (minor_feature)_ — canonical op taxonomy IDEA-002 v4 §5.0, schemas §1.4/§7.2 | — | [x] |
| Implementation | `scripts/omt/net/` + `scripts/omt/net_check.py` + `.opencode/plugins/omt_net.ts` | — | [x] |
| Testing | Test report | `6.testing/features/feature_039.adaptive_net_engine/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
