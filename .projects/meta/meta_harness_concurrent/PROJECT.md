# PROJECT: meta_harness_concurrent — Meta Harness Concurrent

> Status: **draft** · **v0.2 (2026-08-30)** — created by `project.py new` (v0.1 scaffold); project definition written on resume, scope directive D1 (meta harness only, not agentx) locked same session. Iterate freely (non-gated); spawn features with `new_feature.py "<name>" --type <tt> --project meta_harness_concurrent`; log sessions in CURRENT_STATE.md (newest on top).

---

## New Session Quick Start

> One line: A **meta-harness-scoped** design project — replace the harness's implicit serial phase discipline with an explicit **adaptive Petri-net net-of-nets** that models concurrent projects/features and resource capacities, giving the agent an observe → decide → fire → re-verify control plane over the harness's own development process (supervisor net + per-project/per-feature subnets). **Meta harness only — NOT agentx (D1).**

**Next:** confirm the feature roadmap proposal below (feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency, feature_042.goal_net_synthesis, feature_043.meta_net_dashboard — slots verified free, highest done = feature_038), then on user go scaffold the first feature: `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`.

---

## Summary (one line)

**An explicit, adaptive Petri-net "net of nets" as the META HARNESS's own control plane for running concurrent projects/features** — supervisor net + per-project/per-feature subnets with resource places (`agent_attention` = 1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`) that model concurrency instead of the implicit serial FSM; net-management tooling (`omt_net_probe`/`fire`/`splice`/`synthesize`) + a war-room dashboard reusing the petri-net-studio projection. Scoped to harness tooling only (D1) — agentx stays out.

---

## Purpose

### What this project is

- A **harness-owned control plane**: the agent's active projects/features (WORK.md + `.projects/` + feature dirs) are mirrored as an adaptive Petri-net **net-of-nets** — a supervisor net composing per-project and per-feature subnets through boundary ports (`feature_ready`, `resource_token`, `goal_satisfied`).
- **Concurrency modeling**: resource places make "what can run in parallel" explicit and analyzable — conflicts and deadlocks become *structural* properties of the net (two features blocked on the same resource place = deadlock), not session folklore.
- **Adaptive by design**: the agent (not the user) owns net mutation — splice synthesized goal fragments in, disable/remove finished subnets, all as atomic **structural transactions** (versioned, audit-logged, revision-incremented with conformance-vector regression).
- **A small net-management tool surface**: `omt_net_probe` (observe marking) → `omt_net_fire` (decide, then fire with logged reasoning) → `omt_net_splice` (mutate structure) → `omt_net_synthesize` (goal → subnet fragment), registered in `.meta/META_HARNESS.omt` TOOL section + `.opencode/plugins/`.
- **Incremental analysis**: per-subnet analysis + supervisor cross-analysis; after a mutation only affected subnets + supervisor invariants are re-verified (no full recompute).
- **Observability**: a "war-room" dashboard reusing the petri-net-studio graph projection/animation/gallery — live supervisor net, collapsible subnets, animated tokens, deadlock highlighting, revision slider.

### What this project is **not**

- **NOT agentx (D1 — user directive 2026-08-30).** This project does NOT touch `src/agentx/`, does NOT build `src/agentx/model/internal_state`, and does NOT advance feature_001 (session user objectives / `USER_OBJECTIVES.md`). agentx's internal adaptive Petri net is a separate agentx feature. The net-of-nets here models the *harness's own* concurrent work; agentx is out of scope entirely.
- **NOT a redesign of the OMT gate/phase FSM.** Existing before/after gates, phase FSM, TDD pipeline, and `omt_*` tool contract stay. The net is an *additive* control/observability plane — it mirrors and guides concurrent project/feature flow; it does not replace the enforcement layer (D3).
- **NOT a new Petri-net semantics.** The harness-owned engine (`scripts/omt/`) reproduces the shipped library semantics — parity-tested against the `src/agentx/model/petri_net/` spec via conformance vectors, with **no runtime import** (D2).
- **NOT a general workflow/BPM engine or user-facing tooling.** Scoped to the META HARNESS's own development process (projects, features, phases, resources).
- **NOT a mutation of user goals.** Goals/requirements stay in the user store (WORK.md + requirement docs); the agent synthesizes *net fragments from* goals, never edits goals unilaterally (D4).
- **NOT distributed execution.** "Concurrency" = modeled concurrency within the single agent/harness — the `agent_attention` resource has exactly 1 token.

---

## Scope & success criteria

**Scope (declared, not executed; the pause-file deep-dive is the design basis — `.sandbox/pause_2026-08-30.md`. Roadmap numbers verified available: highest done = feature_038, next slots 039+.)**

Proposed feature roadmap (each spawned via `new_feature.py`; numbers auto-assigned at scaffold time, `--project meta_harness_concurrent`):

| # | Proposed slug | Type | Deliverable | Depends on |
|---|---|---|---|---|
| 1 | `.adaptive_net_engine` | minor_feature | Harness-owned net engine (`scripts/omt/`): adaptive net data model + fire/mutate/structural-transaction ops, parity-tested vs library spec, no runtime import | — |
| 2 | `.net_composition_supervisor` | minor_feature | Net-of-nets composition: supervisor + per-project/per-feature subnets, boundary ports, per-subnet + cross-analysis (deadlock), incremental re-verify | 1 |
| 3 | `.resource_places_concurrency` | minor_feature | Resource places & capacities (`agent_attention` = 1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`); conflicts/deadlocks surfaced structurally | 2 |
| 4 | `.goal_net_synthesis` | minor_feature | Goal → subnet fragment synthesis + splice; mid-flight add/disable/remove via atomic versioned structural transactions | 2 |
| 5 | `.meta_net_dashboard` | major_feature | War-room dashboard reusing petri-net-studio projection/animation/gallery: live supervisor net, animated tokens, deadlock highlight, revision slider | 1–4 (studio assets) |

**In scope:**

1. Harness-tooling files only: `scripts/omt/` net module, `.meta/META_HARNESS.omt` (TOOL section + tool definitions), `.opencode/plugins/omt_net_*.ts`, `harnessc.py` build wiring, project/feature scaffolding integration.
2. Parity discipline: the harness engine passes conformance vectors generated from the shipped library spec — same semantics, byte-identical where applicable.
3. Observability via petri-net-studio reuse (no new viz stack).
4. Full agentx suite stays green; the net engine is live-smoke + vitest-style tested like sibling harness tooling.

**Out of scope (explicit non-goals):**

- **No `src/` work at all** — agentx internal state, `USER_OBJECTIVES.md`, and agentx features (feature_001/002) are out (D1). Any feature that would need a `src/` edit is out of scope — escalate instead.
- No change to the existing gate/phase FSM contract (D3).
- No runtime import / re-implementation of `src/agentx/model/petri_net/` inside the harness (D2).
- No user-goal mutation; no general workflow/BPM engine; no distributed execution.

**Success criteria (draft — to be sharpened at first lock):**

- The harness net mirrors actual project/feature state (WORK.md + `.projects/` + feature dirs) and detects structural conflicts/deadlocks (e.g. two features blocked on the same resource place) mechanically — demonstrable on a ≥2-concurrent-feature scenario.
- Fire/mutate ops are atomic, versioned, audit-logged; every firing carries reasoning.
- Roadmap features 1–4 ship with parity + sentinel green; dashboard (5) builds with the studio-style static pipeline.
- Zero `src/` edits recorded under this project; agentx suite untouched.

---

## Status

- [x] Project home created (`project.py new`, state: draft) — `.projects/meta/meta_harness_concurrent/`
- [x] Project definition written (this doc, v0.2) — scope directive D1 locked: meta harness only, not agentx
- [ ] First linked feature (header flips draft → active mechanically) — pending user approval of the roadmap proposal

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — Meta-harness-only scope (user directive 2026-08-30, "meta harness only scope, not agentx"):** this project covers the META HARNESS tooling only — the adaptive net-of-nets controlling concurrent harness projects/features. **agentx is out of scope entirely**: no `src/agentx/`, no `src/agentx/model/internal_state`, no `USER_OBJECTIVES.md`/feature_001 work here. agentx's internal Petri net remains a separate agentx feature. Rationale: keeps the harness's control-plane evolution independent of the application and prevents silent scope creep into agentx during a harness design project.
- **D2 — Harness-owned engine, parity-tested, no runtime import:** the net engine lives in `scripts/omt/` and reproduces the shipped `src/agentx/model/petri_net/` semantics via conformance vectors; the harness never imports agentx at runtime. Keeps the harness independent and the library the single executable spec.
- **D3 — Additive over the gate contract:** the net mirrors/guides/observes existing project/feature/phase flow; it does not replace, merge, or drop any gate, phase-FSM state, or TDD engine rule. Changes there (if ever required) need a new locked decision with evidence.
- **D4 — Role split: user owns goals, agent owns the net:** goals/acceptance live in the user store (WORK.md + requirement docs); the agent mutates only the net (synthesize fragments, splice, disable, remove) in atomic versioned transactions with logged reasoning. The agent never edits goals unilaterally.

---

## References

- `.sandbox/pause_2026-08-30.md` — the architecture deep-dive summary (net-of-nets composition, resource places, structural transactions, incremental analysis, goal→net synthesis, war-room, harness integration points), written while PROJECT.md was still a bare scaffold; consume it for the deep-dive iterations.
- `feature_001.session_user_objectives_driven_by_Petri_Net` — the agentx-side adaptive Petri-net feature (**out of scope per D1**); `.meta/software_development_process/2.requirements/features/feature_001.session_user_objectives_driven_by_Petri_Net/FEATURE.md`.
- `src/agentx/model/petri_net/` + `tests/model/petri_net/` (99 tests) — the executable spec the harness engine must parity against (D2).
- `.meta/META_HARNESS.omt` — harness spec; TOOL section where `omt_net_*` tools register; §12 artifact rules.
- `petri_net_studio` project — `tools/petri-net-studio/` graph projection/animation/gallery to reuse for the war-room dashboard (roadmap feature 5).
- `scripts/omt/tdd/cli.py` — reference for harness tool-surface patterns.