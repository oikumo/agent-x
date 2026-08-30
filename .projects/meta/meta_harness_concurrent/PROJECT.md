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

## Feasibility

**Verdict: feasible — every roadmap item is a pattern-extension of shippable assets already in this repo, not green-field invention.** The highest-risk parts (net semantics parity, dashboard rendering) are the *same moves* already proven by `petri_net_studio`; the genuinely new parts (composition overlay, synthesis) are modeling layers that stay within the flat-library semantics. Two hard constraints keep risk bounded: **no `src/` edits (D1)** and **no runtime import of the library (D2)**.

### Existing assets that de-risk

| Asset | Evidence | What it proves for this project |
|---|---|---|
| Shipped Petri-net library (99 tests) | `src/agentx/model/petri_net/{model,analysis,errors,coverability,io}.py` + `tests/model/petri_net/` | Executable spec for the harness engine: `PetriNet` (add_place/add_transition/add_input/add_output, marking tuples, `fire_marking`, `is_enabled_at`) + `PetriNetAnalyzer` (`reachable_markings`, `deadlocks`, `bounds`, `transition_liveness`, `strongly_connected_components`, `place_invariants`, `transition_invariants`) — everything the control plane needs, already implemented and tested |
| Parity-without-import pattern (proven) | feature_035/036 `tools/petri-net-studio/src/engine/` — TS port passing golden vectors from the Python library (exact-rational B2/B3 parity, B6 deterministic ordering, byte-identical re-runs, 9 conformance vectors @ `shared/petri-net/conformance/analysis-v1/`) | The D2 approach (harness-owned engine, conformance-vector parity, zero runtime import) is a *repeat* of a shipped move — highest-confidence part of the plan. The harness engine is a Python clone-in-spirit of `model.py`/`analysis.py`, stdlib-only like the library (library D4) |
| Harness tool surface pattern | `scripts/omt/` (tdd/cli.py, tdd_check.py, project.py, new_feature.py, harnessc.py, project_state.py) + `.opencode/plugins/` (omt_nav.ts, omt_kb_nav.ts, omt_q.ts, omt_status.ts, omt_think.ts, omt_enforcer.ts) | `omt_net_*` tools are CLI modules + TS plugin proxies, same shape as the 9 existing tools. **`omt_q.ts` (817 lines) is the direct template**: one tool, fixed-shape *ops* (state/plan/drift) with a JSON envelope — the net tools should follow that, not spawn 4 separate tool registrations |
| Studio visualization assets | `tools/petri-net-studio/src/ui/` (graphProjection.ts, animation.ts, Gallery.tsx, GraphExplorer.tsx — all SHIPPED in feature_036) | The war-room dashboard (roadmap #5) is *reuse*, not build: live supervisor net = graph projection over the harness net JSON store; deadlock highlight + revision slider ride existing analysis/UI |
| Ledger/state precedent | `.meta/.omt/` JSONL ledger + state files pattern used by all `omt_*` tools | Structural transactions + audit log = new `kind:"net"` ledger records + a net-state JSON store; no new substrate concept |
| Static-build pipeline proven | feature_034–036 `npm run build` → `dist/` + preview smoke | Dashboard feature has a known-good build/test/deploy path; sentinel bridge pattern (`tests/features/feature_0xx/…`) exists for pytest-side verification |

### Technical risks & mitigations

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| F1 | **Net-of-nets composition**: the library is a *flat* P/T net — no hierarchy support. Supervisors/ports/subnets are not a library concept, so composition must be a modeling layer (flat union of subnets with collision-safe renaming + boundary places/transitions + a supervisor structure persisted separately). | Medium | Keep the engine flat (parity preserved); make composition an overlay in the net-state store + analysis glue. Define the composition contract in the feature's design doc before coding (.net_composition_supervisor). Invariants (`place_invariants`/`transition_invariants`) verify the composed net — already in the library |
| F2 | **Resource capacity semantics**: no native place-capacity in the library; `agent_attention`=1 etc. need capacity. | Low | Standard complement-place modeling (already the invariant-verification idiom); capacity constraints checked via place invariants. Well-understood Petri-net technique, no engine change |
| F3 | **Incremental re-verify is approximated**: library analysis is whole-net (constructor-bound `PetriNetAnalyzer`); no partial analysis API. | Medium | v1 approximation: re-verify the union of affected subnets + supervisor invariants manually scoped, full recompute only as fallback while nets are small. Do not extend the library (D2/D3) — the harness engine can implement its own scoped-analysis helper without touching agentx |
| F4 | **Goal→net synthesis over-promise**: "synthesize a subnet from a goal" is the least mechanical feature; without a structured goal schema it becomes free prose → unbounded modeling. | Medium | Scope `.goal_net_synthesis` to a *declared mapping*: goal fragments (acceptance criteria rows / task bullets from WORK.md + requirement docs) → predefined fragment templates (task → transition chain, dependency → arc, resource need → place). Ship only deterministic template composition + splice; free-form synthesis is explicitly out |
| F5 | **Harness surface churn**: every new CMD record touches drift-pinned budgets (`test_omt_docs_drift_pins.py`), nav-indexed gotchas, quick_ref/workflow docs, and harness-surface edits demand e2e receipt refresh — the main *process* cost (feature_037/038 each carried sentinel + e2e refresh). | Medium (cost, not risk) | Follow the `omt_q` precedent: **one `omt_net` tool with ops** (probe/fire/splice/synthesize) instead of 4 registrations; batch CMD/doc updates per feature; declare features minor_feature (declaration-only) where possible to avoid the major_feature design-doc + TDD pipeline overhead where not needed |
| F6 | **Parity drift / truncation semantics**: conformance vectors pinned to library behavior can rot as the library evolves (max_states, canonical ordering). | Low | Same discipline as studio D8: vectors generated from the tested library, byte-identical pinned, regenerated on library changes; the harness engine is a clone, so a library change is a deliberate, versioned, audited event |
| F7 | **No real parallelism**: `agent_attention` = 1 token means the metanet is a *decision-support model* for a single-threaded agent, not a scheduler. If the model says "these two features can run in parallel," the agent still executes them serially. | Low (by design) | State it explicitly: the deliverable is *concurrency modeling* (conflict/deadlock visibility, capacity planning), not *concurrent execution*. That is what keeps feasibility high — no async/distributed machinery |

### Per-roadmap feasibility

| Roadmap item | Feasibility | Basis |
|---|---|---|
| 1 `.adaptive_net_engine` | **High** | Clone-in-spirit of `model.py`/`analysis.py` (stdlib, flat); parity proven by the studio port; no new concepts |
| 2 `.net_composition_supervisor` | **Medium** | Composition is new modeling (F1), but flat-union + boundary ports is a standard technique and invariants validate it |
| 3 `.resource_places_concurrency` | **Medium-Low** | Complement-place capacity (F2) + existing invariant analysis; semantics well-understood |
| 4 `.goal_net_synthesis` | **Medium** | Bounded to deterministic template composition (F4); free-form synthesis rejected |
| 5 `.meta_net_dashboard` | **High** | Studio assets reuse (proven static-build pipeline); new work = reading the harness net JSON store + deadlock highlight overlay |

### Deliberately NOT pursued (feasibility guardrails)

- **No real concurrent execution** — no threads/async/workers; `agent_attention` = 1 token by design (F7).
- **No library extension** — the harness engine never patches `src/agentx/model/petri_net/`; parity is one-directional (library → conformance vectors → harness engine).
- **No hierarchy in the engine** — composition lives in the overlay/store, keeping parity surface small.
- **No free-form synthesis** — `.goal_net_synthesis` is template composition only.

---

## Status

- [x] Project home created (`project.py new`, state: draft) — `.projects/meta/meta_harness_concurrent/`
- [x] Project definition written (this doc, v0.2) — scope directive D1 locked: meta harness only, not agentx
- [x] Feasibility section added (v0.3) — verdict: feasible; assets/risks/per-roadmap assessment grounded in shipped code
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