# PROJECT: meta_harness_concurrent — Meta Harness Concurrent

> Status: **active** · **v0.5 (2026-08-30)** — created by `project.py new` (v0.1 scaffold); project definition written on resume, scope directive D1 (meta harness only, not agentx) locked same session. Iterate freely (non-gated); spawn features with `new_feature.py "<name>" --type <tt> --project meta_harness_concurrent`; log sessions in CURRENT_STATE.md (newest on top).
> **Main objective (user directive 2026-08-30 → D16):** the meta harness must allow concurrency with **state management driven by a single Petri net** — the net, **in complement with other files** (sidecar + overlay + ledger + WORK.md projection), is the **global state single source of truth (SSOT)**.
> **Architecture decisions locked via IDEA-001 (file-backed net control) + IDEA-002 v4 (compositional net-of-nets) + IDEA-005 (WORK.md net projection):** ONE flat supervisor net (subnets are partitions, not separate nets); 3-feature core + 4 optional phase-2; `petri-net-json` v1 + sidecar for live marking + overlay for composition; single `omt_net` tool with ops. D16 amends the v0.4 "additive observability layer" authority framing (IDEA-003): the net owns **state**, gates keep **enforcement**, the ledger keeps **audit** — approval ≠ state; all gate mechanics (D3) stand.

---

## New Session Quick Start

> One line: A **meta-harness-scoped** design project — **concurrency state management driven by a single Petri net** (D16): ONE flat supervisor net composes per-project/per-feature subnets as partitions (`f{N}_` prefixes + boundary ports `feature_ready`/`resource_token`/`goal_satisfied`), resource places (`agent_attention`=1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`) make conflicts/deadlocks structural, and the net bundle (net file + sidecar + overlay) — **in complement with** the ledger (audit) and WORK.md (human projection) — is the **global state single source of truth**. Gates keep enforcement; the analyzer blocks invalid fires. **Meta harness only — NOT agentx (D1).**

**Next:** approve the **3-feature core roadmap** (feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency — feature_042/043/044/045 are optional phase-2), then scaffold: `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`.

---

## Summary (one line)

**A single Petri net driving concurrency state management for the META HARNESS — the global state single source of truth, in complement with other files (D16).** ONE flat supervisor net (`META_NET.petri.json`, `petri-net-json` v1) composes per-project/per-feature subnets as **partitions** (collision-safe `f{N}_` prefixes + boundary ports `feature_ready`/`resource_token`/`goal_satisfied`); resource places (`agent_attention`=1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`) make concurrency conflicts structurally visible; live marking persists in the sidecar, composition in the overlay — **net + sidecar + overlay, complemented by the ledger (audit) and WORK.md (projection), together are the SSOT**. The analyzer blocks invalid fires; drift checks reconcile net state vs ledger audit at every `omt_complete` exit; single `omt_net` tool (ops: probe/fire/splice/sync/synthesize/invariant, IDEA-002 v4 canonical). Scoped to harness tooling only (D1) — agentx stays out.

---

## Purpose

### What this project is

- **The global state single source of truth for concurrency (D16, user directive 2026-08-30):** ONE single Petri net drives state management — every concurrency fact (which features are active, which phase each is in, which resources are held, what is blocked/deadlocked, what may fire next) is **stored in and read from the net bundle**. The net **owns state**; the gates (`g.phase`/`g.tests`/`g.think`/`g.receipt`) keep **enforcement authority** (they block illegal transitions mechanically); the ledger keeps **audit authority** (append-only approval/mutation history). Approval ≠ state: D3's mechanics stand (no gate removed, the net never overrides a gate, the analyzer blocks invalid fires), but the v0.4 "secondary observability layer" label (IDEA-003 §2.1) is superseded — the net is not a mirror of some other state store, **it IS the state store**.
- A **single flat supervisor net** composing per-project/per-feature subnets as **partitions of one net** (not separate net files) through boundary ports (`feature_ready`, `resource_token`, `goal_satisfied`) — composition is a modeling overlay (flat union + collision-safe `f{N}_` prefixes + boundary places), not engine hierarchy.
- **Concurrency modeling via complement places**: resource capacities (`agent_attention`=1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`) modeled as token-conservation invariants; conflicts/deadlocks = structural properties detected by `analyzer.deadlocks()` / `place_invariants()`.
- **Atomic structural transactions**: splice (add/remove/disable) with versioned net file + sidecar + overlay three-file atomic write, conformance-vector regression on every mutation, full audit in ledger `kind:"net_*"` records.
- **Single `omt_net` tool with ops** (probe/fire/splice/sync/synthesize/invariant — IDEA-002 v4 canonical) — follows `omt_q` precedent, avoids harness surface churn (F5).
- **Net↔reality sync** via `omt_net{op:sync}`: bootstrap + re-sync on `project.py` lifecycle events + `new_feature.py --project` link; sync = deterministic proposal through splice path, never silent (D4). Under D16 this is also the **SSOT bootstrap**: it materializes the net from `.projects/` + feature dirs and renders WORK.md (feature_045).

### The SSOT = net + complement files (D16)

| File | Authority role | Written by |
|---|---|---|
| `.meta/.omt/META_NET.petri.json` | **Structure + M0** of the single net (v1, pure flat union) | `splice` / `sync` / `synthesize` (atomic, revisioned) |
| `.meta/.omt/net_state.sidecar.json` | **Live marking + revision** (net state proper) | `fire` (atomic with the net file) |
| `.meta/.omt/supervisor.overlay.json` | **Composition view** — subnet partitions, boundary ports, disabled set | `splice` / `sync` (same three-file transaction) |
| `.meta/.omt/ledger.jsonl` | **Audit history** — `kind:"net_*"` + phase/complete records (durability, not state) | all ops |
| `WORK.md` tasks/projects sections | **Human projection** of net state — rendered, never hand-maintained (IDEA-005, feature_045) | `sync` render (net→md); hand edits = proposals (md→net) |
| `.meta/.omt/harness.net.drift.jsonl` | **Drift log** — net state vs ledger audit divergences | `invariant` op at every `omt_complete` exit |

One state truth (the net bundle), one audit truth (the ledger), one human view (the WORK.md render), mechanical enforcement (the gates) — reconciled by the drift protocol, never by silent resolution.

### What this project is **not**

- **NOT agentx (D1 — user directive 2026-08-30).** This project does NOT touch `src/agentx/`, does NOT build `src/agentx/model/internal_state`, and does NOT advance feature_001 (session user objectives / `USER_OBJECTIVES.md`). agentx's internal adaptive Petri net is a separate agentx feature. The net-of-nets here models the *harness's own* concurrent work; agentx is out of scope entirely.
- **NOT a redesign of the OMT gate/phase FSM.** Existing before/after gates, phase FSM, TDD pipeline, and `omt_*` tool contract stay. The net owns *state*; the gates keep *enforcement* — the analyzer blocks invalid fires, but no gate is removed, bypassed, or re-implemented (D3 mechanics, D16 authority split).
- **NOT a new Petri-net semantics.** The harness-owned engine (`scripts/omt/net/`) reproduces the shipped library semantics — parity-tested against the `src/agentx/model/petri_net/` spec via conformance vectors, with **no runtime import** (D2).
- **NOT a general workflow/BPM engine or user-facing tooling.** Scoped to the META HARNESS's own development process (projects, features, phases, resources).
- **NOT a mutation of user goals.** Goals/requirements stay in the user store (WORK.md + requirement docs); the agent synthesizes *net fragments from* goals (deterministic templates only), never edits goals unilaterally (D4).
- **NOT distributed execution.** "Concurrency" = modeled concurrency within the single agent/harness — the `agent_attention` resource has exactly 1 token (F7).
- **NOT a v2 format change.** Live marking persists in a sidecar (`net_state.sidecar.json`); `petri-net-json` v1 stays pure (structure + initial marking only).
- **NOT a second/duplicated state store.** State is not maintained twice: WORK.md is a deterministic render of the net, the ledger is an audit log of net mutations, and the enforcer's internal state files remain its private mechanism (reconciled by drift checks). There is exactly one global state authority — the net bundle (D16).

---

## Scope & success criteria

**Scope (declared, not executed; design basis = `.sandbox/pause_2026-08-30.md` + the candidate idea docs under `ideas/` — IDEA-001 file-backed control, IDEA-002 compositional architecture, IDEA-003 additive observability layer, IDEA-004 ledger-mined behavioral net, IDEA-005 net-driven WORK.md projection. Roadmap numbers verified available: highest done = feature_038, next slots 039+.)**

Proposed feature roadmap (each spawned via `new_feature.py`; numbers auto-assigned at scaffold time, `--project meta_harness_concurrent`):

| # | Proposed slug | Type | Deliverable | Depends on |
|---|---|---|---|---|
| 1 | `feature_039.adaptive_net_engine` | minor_feature | Harness engine (`scripts/omt/net/`): `model.py`/`analysis.py`/`io.py`/`errors.py` clones + `state.py` (loads v1 net + sidecar + overlay, atomic saves, rebases marking on splice), `probe`/`fire`/`invariant` ops, 9-vector parity, no runtime import | — |
| 2 | `feature_040.net_composition_supervisor` | minor_feature | Supervisor + subnet composition: flat union + `f{N}_` prefixes + boundary ports, per-subnet + cross-analysis (deadlock), incremental re-verify, `supervisor.overlay.json` persistence | 1 |
| 3 | `feature_041.resource_places_concurrency` | minor_feature | Complement-place capacities (`agent_attention`=1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`); `place_invariants()` verification; deadlock/conflict surfacing | 2 |
| 4 | `feature_042.goal_net_synthesis` | minor_feature (optional, phase-2) | Deterministic template composition + splice (task→chain, dependency→arc, resource→capacity place, acceptance→invariant) | 2 |
| 5 | `feature_043.meta_net_dashboard` | major_feature (optional, phase-2) | Static-build dashboard reusing studio projection/animation/gallery: reads `.meta/.omt/META_NET.petri.json` + sidecar at build; deadlock highlight, revision slider | 1–3 |
| 6 | `feature_044.mined_behavioral_net` | minor_feature (optional, phase-2) | IDEA-004: `miner.py` (α-variant + session attribution over the ledger store) + `mine` op (single gated extension of the closed op enum) + intended-vs-observed behavioral drift report + empirical invariants | 2 (+4 for full compare) |
| 7 | `feature_045.work_md_net_driven` | minor_feature (optional, phase-2) | IDEA-005: WORK.md as deterministic net projection + proposal surface — `sync.py` render/parse/propose, `omt_net{op:sync}` md directions, round-trip conformance vectors | 1–3 |

**Core = features 1–3.** Features 4–7 are phase-2, only if core proves valuable (IDEA-003 §6 re-scope, not cancellation). **Feature 7 (WORK.md projection) completes the SSOT loop of D16** — it is the first phase-2 pick and a candidate for promotion into the core at the feature_041 exit review (D17).

**In scope:**

1. Harness-tooling files only: `scripts/omt/net/` module, `.meta/META_HARNESS.omt` (TOOL section + `omt_net` tool definition), `.opencode/plugins/omt_net.ts`, `harnessc.py` build wiring, project/feature scaffolding integration (`omt_net_sync` hook).
2. Parity discipline: the harness engine passes conformance vectors generated from the shipped library spec — same semantics, byte-identical where applicable.
3. Observability via petri-net-studio reuse (no new viz stack).
4. Full agentx suite stays green; the net engine is live-smoke + vitest-style tested like sibling harness tooling.
5. Three-file atomic persistence: `META_NET.petri.json` (v1, structure + M0) + `net_state.sidecar.json` (live marking + revision) + `supervisor.overlay.json` (composition view); git-ignored (runtime state, durability via revision + ledger + conformance vectors).
6. Drift check: `omt_net{op:invariant}` runs net-vs-ledger reconciliation at every `omt_complete` exit; logs to `harness.net.drift.jsonl`.
7. WORK.md projection surface (phase-2, feature_045): deterministic render of net state into WORK.md tasks/projects sections + proposal path for hand edits (IDEA-005). WORK.md convention sections (CONV_WORK_*) stay under their existing authority; only the tasks/projects blocks become renders.

**Out of scope (explicit non-goals):**

- **No `src/` work at all** — agentx internal state, `USER_OBJECTIVES.md`, and agentx features (feature_001/002) are out (D1). Any feature that would need a `src/` edit is out of scope — escalate instead.
- No change to the existing gate/phase FSM contract (D3).
- No runtime import / re-implementation of `src/agentx/model/petri_net/` inside the harness (D2).
- No user-goal mutation; no general workflow/BPM engine; no distributed execution.
- No `petri-net-json` v2 format change (live marking stays in sidecar).
- No free-form goal synthesis (feature 4 = deterministic templates only).
- No live dashboard (feature 5 = static build only).

**Success criteria (sharpened per IDEA-002 v3):**

- The single net **holds** the actual project/feature state (synced from `.projects/` + feature dirs via `omt_net{op:sync}` bootstrap + lifecycle hooks; WORK.md rendered from it under feature_045) and detects structural conflicts/deadlocks mechanically — demonstrable on a ≥2-concurrent-feature scenario.
- **SSOT discipline (D16):** every concurrency-state read resolves through the net bundle; no state is hand-duplicated in WORK.md or prose docs; drift between net state and ledger audit is logged and reconciled at every `omt_complete` exit.
- Fire/mutate ops are atomic, versioned, audit-logged (`kind:"net_*"`); every firing carries reasoning; conformance vectors pass after every splice.
- Core features 1–3 ship with parity + sentinel green; drift check runs at every `omt_complete` exit.
- Zero `src/` edits recorded under this project; agentx suite untouched.

---

## Feasibility

**Verdict: feasible — every roadmap item is a pattern-extension of shippable assets already in this repo, not green-field invention.** The highest-risk parts (net semantics parity, dashboard rendering) are the *same moves* already proven by `petri_net_studio`; the genuinely new parts (composition overlay, synthesis) are modeling layers that stay within the flat-library semantics. Two hard constraints keep risk bounded: **no `src/` edits (D1)** and **no runtime import of the library (D2)**.

### Existing assets that de-risk

| Asset | Evidence | What it proves for this project |
|---|---|---|
| Shipped Petri-net library (158 tests) | `src/agentx/model/petri_net/{model,analysis,errors,coverability,io}.py` + `tests/model/petri_net/` | Executable spec for the harness engine: `PetriNet` (add_place/add_transition/add_input/add_output, marking tuples, `fire_marking`, `is_enabled_at`) + `PetriNetAnalyzer` (`reachable_markings`, `deadlocks`, `bounds`, `transition_liveness`, `strongly_connected_components`, `place_invariants`, `transition_invariants`) — everything the control plane needs, already implemented and tested |
| Parity-without-import pattern (proven) | feature_035/036 `tools/petri-net-studio/src/engine/` — TS port passing golden vectors from the Python library (exact-rational B2/B3 parity, B6 deterministic ordering, byte-identical re-runs, 9 conformance vectors @ `shared/petri-net/conformance/analysis-v1/`) | The D2 approach (harness-owned engine, conformance-vector parity, zero runtime import) is a *repeat* of a shipped move — highest-confidence part of the plan. The harness engine is a Python clone-in-spirit of `model.py`/`analysis.py`, stdlib-only like the library (library D4) |
| Harness tool surface pattern | `scripts/omt/` (tdd/cli.py, tdd_check.py, project.py, new_feature.py, harnessc.py, project_state.py) + `.opencode/plugins/` (omt_nav.ts, omt_kb_nav.ts, omt_q.ts, omt_status.ts, omt_think.ts, omt_enforcer.ts) | `omt_net_*` tools are CLI modules + TS plugin proxies, same shape as the 9 existing tools. **`omt_q.ts` (817 lines) is the direct template**: one tool, fixed-shape *ops* (state/plan/drift) with a JSON envelope — `omt_net` follows that (D10): one registration with ops (probe/fire/splice/sync/synthesize/invariant — IDEA-002 v4 canonical), not 5 separate tool registrations |
| Studio visualization assets | `tools/petri-net-studio/src/ui/` (graphProjection.ts, animation.ts, Gallery.tsx, GraphExplorer.tsx — all SHIPPED in feature_036) | The war-room dashboard (roadmap #5) is *reuse*, not build: live supervisor net = graph projection over the harness net JSON store; deadlock highlight + revision slider ride existing analysis/UI |
| Ledger/state precedent | `.meta/.omt/` JSONL ledger + state files pattern used by all `omt_*` tools | Structural transactions + audit log = new `kind:"net"` ledger records + a net-state JSON store; no new substrate concept |
| Static-build pipeline proven | feature_034–036 `npm run build` → `dist/` + preview smoke | Dashboard feature has a known-good build/test/deploy path; sentinel bridge pattern exists for pytest-side verification (e.g. `tests/features/feature_035.studio_v2_analysis/`, `feature_036.studio_v3_graph/`; also 031/034) |

### Technical risks & mitigations

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| F1 | **Net-of-nets composition**: the library is a *flat* P/T net — no hierarchy support. Supervisors/ports/subnets are not a library concept, so composition must be a modeling layer (flat union of subnets with collision-safe renaming + boundary places/transitions + a supervisor structure persisted separately). | Medium | Keep the engine flat (parity preserved); make composition an overlay in the net-state store + analysis glue. Define the composition contract in the feature's design doc before coding (.net_composition_supervisor). Invariants (`place_invariants`/`transition_invariants`) verify the composed net — already in the library |
| F2 | **Resource capacity semantics**: no native place-capacity in the library; `agent_attention`=1 etc. need capacity. | Low | Standard complement-place modeling (already the invariant-verification idiom); capacity constraints checked via place invariants. Well-understood Petri-net technique, no engine change |
| F3 | **Incremental re-verify is approximated**: library analysis is whole-net (constructor-bound `PetriNetAnalyzer`); no partial analysis API. | Medium | v1 approximation: re-verify the union of affected subnets + supervisor invariants manually scoped, full recompute only as fallback while nets are small. Do not extend the library (D2/D3) — the harness engine can implement its own scoped-analysis helper without touching agentx |
| F4 | **Goal→net synthesis over-promise**: "synthesize a subnet from a goal" is the least mechanical feature; without a structured goal schema it becomes free prose → unbounded modeling. | Medium | Scope `.goal_net_synthesis` to a *declared mapping*: goal fragments (acceptance criteria rows / task bullets from WORK.md + requirement docs) → predefined fragment templates (task → transition chain, dependency → arc, resource need → place). Ship only deterministic template composition + splice; free-form synthesis is explicitly out |
| F5 | **Harness surface churn**: every new CMD record touches drift-pinned budgets (`test_omt_docs_drift_pins.py`), nav-indexed gotchas, quick_ref/workflow docs, and harness-surface edits demand e2e receipt refresh — the main *process* cost (feature_037/038 each carried sentinel + e2e refresh). | Medium (cost, not risk) | Follow the `omt_q` precedent: **one `omt_net` tool with ops** (probe/fire/splice/sync/synthesize/invariant) instead of 5+ registrations; batch CMD/doc updates per feature; declare features minor_feature (declaration-only) where possible to avoid the major_feature design-doc + TDD pipeline overhead where not needed |
| F6 | **Parity drift / truncation semantics**: conformance vectors pinned to library behavior can rot as the library evolves (max_states, canonical ordering). | Low | Same discipline as studio D8: vectors generated from the tested library, byte-identical pinned, regenerated on library changes; the harness engine is a clone, so a library change is a deliberate, versioned, audited event |
| F7 | **No real parallelism**: `agent_attention` = 1 token means the metanet is a *decision-support model* for a single-threaded agent, not a scheduler. If the model says "these two features can run in parallel," the agent still executes them serially. | Low (by design) | State it explicitly: the deliverable is *concurrency modeling* (conflict/deadlock visibility, capacity planning), not *concurrent execution*. That is what keeps feasibility high — no async/distributed machinery |

### Per-roadmap feasibility

| Roadmap item | Feasibility | Basis |
|---|---|---|
| 1 `feature_039.adaptive_net_engine` | **High** | Clone-in-spirit of `model.py`/`analysis.py` (stdlib, flat); parity proven by the studio port; no new concepts |
| 2 `feature_040.net_composition_supervisor` | **Medium** | Composition is new modeling (F1), but flat-union + boundary ports is a standard technique and invariants validate it |
| 3 `feature_041.resource_places_concurrency` | **Medium-Low** | Complement-place capacity (F2) + existing invariant analysis; semantics well-understood |
| 4 `feature_042.goal_net_synthesis` *(optional)* | **Medium** | Bounded to deterministic template composition (F4); free-form synthesis rejected |
| 5 `feature_043.meta_net_dashboard` *(optional)* | **High** | Studio assets reuse (proven static-build pipeline); new work = reading the harness net JSON store + deadlock highlight overlay |

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
- [x] Design locked via IDEA-001/002/003 + PROJECT.md v0.4 — decisions D5–D15; roadmap re-scoped 3 core + 2 optional (feature_039–041 core, 042–043 phase-2)
- [x] Doc audit (v0.4 + iter 6) — factual corrections applied (library = 158 tests, not 99; slug convention aligned to `feature_0xx.`; IDEA-003 referenced)
- [x] SSOT refinement (v0.5) — user directive locked as D16: single-Petri-net concurrency state management; net + complement files = global state SSOT; D3 authority framing amended (state/enforcement/audit split); IDEA-005 adopted as WORK.md projection (D17, feature_045); idea-numbering collision fixed (D18); roadmap now 3 core + 4 optional phase-2
- [ ] First linked feature (header flips draft → active mechanically) — pending user approval of the roadmap proposal

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — Meta-harness-only scope (user directive 2026-08-30, "meta harness only scope, not agentx"):** this project covers the META HARNESS tooling only — the adaptive net-of-nets controlling concurrent harness projects/features. **agentx is out of scope entirely**: no `src/agentx/`, no `src/agentx/model/internal_state`, no `USER_OBJECTIVES.md`/feature_001 work here. agentx's internal Petri net remains a separate agentx feature. Rationale: keeps the harness's control-plane evolution independent of the application and prevents silent scope creep into agentx during a harness design project.
- **D2 — Harness-owned engine, parity-tested, no runtime import:** the net engine lives in `scripts/omt/net/` and reproduces the shipped `src/agentx/model/petri_net/` semantics via conformance vectors; the harness never imports agentx at runtime. Keeps the harness independent and the library the single executable spec.
- **D3 — Additive over the gate contract:** the net mirrors/guides/observes existing project/feature/phase flow; it does not replace, merge, or drop any gate, phase-FSM state, or TDD engine rule. Changes there (if ever required) need a new locked decision with evidence. **(Amended by D16: the "primary/secondary" authority framing is replaced by the state/enforcement/audit split; D3's mechanics are unchanged.)**
- **D4 — Role split: user owns goals, agent owns the net:** goals/acceptance live in the user store (WORK.md + requirement docs); the agent mutates only the net (synthesize fragments, splice, disable, remove) in atomic versioned transactions with logged reasoning. The agent never edits goals unilaterally.
- **D5 — File-backed net control (IDEA-001):** control is by a REAL, persisted Petri-net FILE in the repo's own `petri-net-json` v1 format, where the file is the AUTHORITY for structure + initial marking; live marking persists in a sidecar (`net_state.sidecar.json`); analysis = in-repo parity engine.
- **D6 — v1 format unchanged, sidecar for live marking (IDEA-001 item 1 resolved):** `petri-net-json` v1 stays pure (structure + M0 only); live marking in `net_state.sidecar.json` `{live_marking, revision, updated_at}`; atomic two-file write with rollback. No format ripple to io.py/io.ts/studio/conformance.
- **D7 — Net-vs-ledger reconciliation as drift check (IDEA-001 item 2 resolved):** `omt_net{op:invariant}` runs drift check at **every `omt_complete` exit**; per D16 the ledger keeps **audit** authority and the gates keep **enforcement** (the v0.4 wording "ledger = primary approval authority" is superseded by the state/enforcement/audit split); net blocks fires via analyzer; logs to `harness.net.drift.jsonl` (mirrors `omt_q{op:drift}` envelope).
- **D8 — Analysis authority = in-repo parity engine only (IDEA-001 item 3 resolved):** "External analysis" = harness-owned `PetriNetAnalyzer` clone. PIPE/TINA/WoPeD cannot read `petri-net-json`; external interop = separate PNML export feature (out of scope).
- **D9 — 3-feature core roadmap (IDEA-001 item 4 resolved):** feature_039 (engine), feature_040 (composition), feature_041 (resources) = core; feature_042 (synthesis), feature_043 (dashboard) = optional phase-2. **(Extended by D17/D18: feature_044 mined behavioral net + feature_045 WORK.md projection added as optional phase-2.)**
- **D10 — Single `omt_net` tool with ops (IDEA-002.D3):** one tool, ops = probe/fire/splice/sync/synthesize/invariant (IDEA-002 v4 canonical; supersedes the earlier 5-op list that omitted `sync`); follows `omt_q` precedent; avoids F5 harness surface churn.
- **D11 — Composition overlay file (IDEA-002.D14, §1.4):** `supervisor.overlay.json` beside union net; subnet membership/ports/disabled live there; v1 stays pure flat union; three-file atomic transaction.
- **D12 — Net↔reality sync via lifecycle hooks (IDEA-002.D11):** `omt_net_sync` op; bootstrap + re-sync on `project.py` lifecycle + `new_feature.py --project`; sync = deterministic splice proposal, never silent (D4).
- **D13 — Derived `place_order` + splice rebase (IDEA-002.D12):** `place_order = tuple(sorted(...))` (library-verified); marking rebased by name in every structure-changing splice; `revision` mismatch → refuse + ledger-replay repair.
- **D14 — Subnet lifecycle = remove-with-policy + ledger `net_*` records (IDEA-002.D13):** no library disable primitive; `disable` ≡ structural removal w/ token policy, `kind:"net_disable"`, undo = inverse splice replay; overlay keeps archive visibility.
- **D15 — Net artifacts are runtime state (IDEA-002.D14):** `.meta/.omt/*` git-ignored (ledger pattern); durability via revision + ledger audit + git-pinned conformance vectors.
- **D16 — Single-Petri-net global state SSOT (user directive 2026-08-30: "concurrency with state management driven by a single petri net; the net, in complement with other files, is the global state single source of truth"):** ONE flat net drives concurrency state management; the SSOT = the net bundle (`META_NET.petri.json` + `net_state.sidecar.json` + `supervisor.overlay.json`) **complemented by** the ledger (audit) and WORK.md (projection). **Amends the v0.4 authority framing (D3 wording, IDEA-003 §2.1 "primary/secondary"):** replaced by an authority split — the net owns **state**, the gates keep **enforcement**, the ledger keeps **audit**. All D3/D5–D15 mechanics stand unchanged (no gate removed; the analyzer blocks fires; the drift check reconciles net state vs ledger audit at every `omt_complete` exit). IDEA-003's category-error caution (don't replace the workflow driver) is honored: enforcement stays out of the net; only state ownership moves.
- **D17 — WORK.md is a deterministic projection of the net (IDEA-005 adopted):** under the SSOT, WORK.md's tasks/projects sections are rendered from net state via `omt_net{op:sync}` (net→md); hand edits to projected sections are proposals through the splice path (md→net), never authoritative state. Ships as phase-2 **feature_045** (depends on core 1–3); first phase-2 pick and candidate for promotion into the core at the feature_041 exit review.
- **D18 — Idea numbering collision resolved:** the WORK.md net-driven idea (created as a duplicate "IDEA-004") is renumbered **IDEA-005** (`ideas/idea-005-work-md-net-driven-concurrency.md`), slot **feature_045**; IDEA-004 + feature_044 remain the ledger-mined behavioral net. No content change beyond renumbering (+ `drift`→`invariant` op-name conformance).

---

## References

- `.sandbox/pause_2026-08-30.md` — the architecture deep-dive summary (net-of-nets composition, resource places, structural transactions, incremental analysis, goal→net synthesis, war-room, harness integration points), written while PROJECT.md was still a bare scaffold; consume it for the deep-dive iterations.
- `IDEA-001` — `.projects/meta/meta_harness_concurrent/ideas/idea-001-file-backed-net-control.md` — file-backed net control, format decision, live-marking sidecar, drift check, 3-feature core scope.
- `IDEA-002` — `.projects/meta/meta_harness_concurrent/ideas/idea-002-compositional-net-of-nets-architecture.md` (v4) — compositional net-of-nets architecture, additive layer, sidecar/overlay schemas, structural transactions, tool surface, sync hooks, all open items resolved in design; canonical `omt_net` op taxonomy (probe|fire|splice|sync|synthesize|invariant, mutating-vs-read-only split, conformance-regression trigger matrix).
- `IDEA-003` — `.projects/meta/meta_harness_concurrent/ideas/idea-003-petri-net-additive-observability-layer.md` — the net as an additive observability/guidance layer (not a workflow driver); resolves the single-source-of-truth tension (gates own approval, net blocks via analyzer); §6 roadmap re-scope (3 core + 2 optional). **(Authority framing amended by D16: the net owns state; its category-error caution — never replace the enforcement gates — stands.)**
- `IDEA-004` — `.projects/meta/meta_harness_concurrent/ideas/idea-004-ledger-mined-behavioral-net.md` (v2) — process mining of the ledger store (`.meta/.omt/ledger*.jsonl`, hot + rotated archives) into a `META_NET.mined.petri.json` "observed net"; `mine` op as the single gated extension of the `omt_net` enum at optional phase-2 slot feature_044; NOT part of core roadmap.
- `IDEA-005` — `.projects/meta/meta_harness_concurrent/ideas/idea-005-work-md-net-driven-concurrency.md` — WORK.md as a deterministic projection of the net + proposal mutation surface (net→md render, md→net proposals, both via `omt_net{op:sync}`); renumbered from a duplicate "IDEA-004" per D18; optional phase-2 slot feature_045, first phase-2 pick (completes the D16 SSOT loop). `ideas/WORK.md.net-driven-example` = target render sketch.
- `feature_001.session_user_objectives_driven_by_Petri_Net` — the agentx-side adaptive Petri-net feature (**out of scope per D1**); `.meta/software_development_process/2.requirements/features/feature_001.session_user_objectives_driven_by_Petri_Net/FEATURE.md`.
- `src/agentx/model/petri_net/` + `tests/model/petri_net/` (158 tests) — the executable spec the harness engine must parity against (D2).
- `.meta/META_HARNESS.omt` — harness spec; TOOL section where `omt_net` tool registers; §12 artifact rules.
- `petri_net_studio` project — `tools/petri-net-studio/` graph projection/animation/gallery to reuse for the war-room dashboard (roadmap feature 5).
- `scripts/omt/tdd/cli.py` — reference for harness tool-surface patterns.
- `shared/petri-net/FORMAT.md` + `petri-net-json-v1.schema.json` — v1 format (structure + M0 only).
- `tools/petri-net-studio/src/engine/{model,analysis,io,errors}.ts` — proven parity port + conformance vectors (`shared/petri-net/conformance/analysis-v1/`).
- `.opencode/plugins/omt_q.ts` — single-tool-with-ops pattern + `op:drift` model.
- `scripts/omt/project.py` / `new_feature.py` — scaffolding + lifecycle CLI (sync hooks).
- `.meta/.omt/ledger.jsonl` — real record shape (flat `kind`-discriminated).
- `.gitignore` — `.meta/.omt/*` ignored (net artifacts = runtime state).