# IDEA-002 — Compositional Net-of-Nets Architecture (supervisor + subnets + resource places + structural transactions)

> Created 2026-08-30 · deep-dive from source verification of `src/agentx/model/petri_net/`, `tools/petri-net-studio/src/engine/`, `shared/petri-net/conformance/`, `.opencode/plugins/omt_q.ts`.
> **v2 (2026-08-30)** — refined to align the doc with the project's current understanding (PROJECT.md D1–D4, IDEA-001, IDEA-003):
> - **IDEA-003 reframing adopted:** the net-of-nets is an **additive observability/guidance layer** over the existing phase-FSM + ledger control plane — it informs, guides, and can **block** via the analyzer, but it never replaces the gates (D3; IDEA-003.D1/D2). Summary, §1, §8 updated.
> - **IDEA-001 live-marking + reconciliation open items carried:** §7 sidecar schema conformed to IDEA-003 §3.1 (`net_state.sidecar.json`); §8 drift check runs at **every `omt_complete` exit** with the ledger as **primary** approval authority.
> - **Roadmap numbered** per PROJECT.md: feature_039.adaptive_net_engine … feature_043.meta_net_dashboard (§10).
> - **Open items 1–5 marked RESOLVED (design)** per IDEA-003 §4; three genuinely remaining items added (§11).
> **v3 (2026-08-30)** — source-verified hardening pass:
> - **Open items 6–9 resolved in design** (§11): net↔reality sync (hooked to `project.py` lifecycle + `omt_net_sync`), `place_order` stability (derived-by-name ordering + splice rebase + revision guard), subnet lifecycle (disable ≡ remove-with-policy + ledger `net_*` records, undo = inverse splice replay), composition-overlay persistence.
> - **Composition overlay file added (§1.4):** `supervisor.overlay.json` — subnet membership/boundary ports/disabled set live OUTSIDE the v1 file (which stays a pure flat union).
> - **Source facts verified & fixed:** `analysis.ts` = 509 lines (was 510); 9 conformance vectors re-confirmed by file listing; §3.3 ledger example conformed to the real `.meta/.omt/ledger.jsonl` (flat `kind`-discriminated records; verified kinds: phase/complete/skip/q/think_consult/project*); `.meta/.omt/*` git-ignored (net artifacts are runtime state, mirroring ledger policy).
> - **Remaining control-plane wording removed** (§5 description, §8.1).
> **v4 (2026-08-30)** — ops-surface + modeling-semantics refinement pass (source-verified against the trio's scattered op lists + omt_q.ts pattern):
> - **Canonical `omt_net` op taxonomy (§5)** — the ops surface was inconsistent across IDEA-001/002/003: IDEA-002 §5 listed `probe|fire|splice|synthesize|invariant`; IDEA-001 added `drift` as an explicit op; §11 #6/#13 D11 added `sync`; §11 #7 referenced a `--repair` path; §11 #8 added `disable`; yet none were consolidated. v4 defines ONE canonical op set + a mutating-vs-read-only split + a conformance-regression trigger matrix, so `omt_net.ts`'s `z.enum` is fixed at feature_039 design time instead of guessed.
> - **`agent_attention` serial-mirror semantics documented (§2.2/§2.3)** — because capacity 1 is input from *all* transitions, the composed net's reachable behavior mirrors the single-threaded agent exactly; v4 makes this explicit (it is the engineering reason F7 holds) and adds the multi-resource-consumption modeling note.
> - **Sync authorization + bootstrap ordering (§11 #6, §13 D15)** — `omt_net_sync` proposal approval path tied to the gates (never silent, D4); drift/bootstrap-gap ordering resolved (probe/invariant no-op cleanly before the net exists).
> **Builds on IDEA-001** (file-backed net control with `petri-net-json` v1 format).
> **Status:** design doc for locked project (PROJECT.md v0.4 D1–D15) — the net-of-nets architecture is an additive observability/guidance layer over the phase-FSM + ledger control plane per IDEA-003.D1/D2. This doc validates the design that features feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency carry. All open items 1–9 resolved in design (IDEAA-002 v4). Ready for feature scaffolding per CURRENT_STATE.md iter 5: "User approval of the 3-feature core roadmap → scaffold `feature_039.adaptive_net_engine`". The net mirrors/guides/blocks via the analyzer; `META_HARNESS.omt` + phase FSM + ledger remain PRIMARY approval authority (D3, IDEA-003.D1/D2).

---

## Summary

**The META HARNESS gains an *additive* Petri-net *net-of-nets* observability/guidance layer (IDEA-003) over its existing phase-FSM + ledger control plane: a flat *supervisor net* composing per-project and per-feature subnets through boundary ports (`feature_ready`, `resource_token`, `goal_satisfied`), with resource places (`agent_attention=1`, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`) making concurrency conflicts structurally visible, and adaptive mutation via atomic versioned structural transactions. The net mirrors, guides, and observes — it can *block* an invalid fire through the analyzer and *log* drift, but it never overrides the gates; the ledger + phase FSM remain the primary approval authority (D3, IDEA-003.D1/D2).**

The library is flat — no hierarchy. Composition is a **modeling overlay** in the net-state store + analysis glue, keeping the engine flat and parity surface small (F1 mitigation). The harness engine is an in-repo parity clone of the library (D2) — no runtime import of `src/agentx/` under any circumstances.

---

## 1. Net-of-Nets Composition (Flat Union + Boundary Ports)

> **Role (v2):** the composed net is the *observability model* of the harness's own flow. It sits **ON TOP of** the existing gates, not in place of them (D3). The net may say "this fire is safe"; only the phase gate (`g.phase`/`g.tests`/`g.receipt`) says "this fire happens" (§8).

### 1.1 Why Flat Union?

The library (`PetriNet` + `PetriNetAnalyzer`) is **intentionally flat** — no hierarchy support. This is a *feature* for parity: the harness engine stays a clone of `model.py`/`analysis.py`, and composition lives in the overlay/store.

**Composition Mechanics (modeling layer, not engine):**

```
Supervisor Net (persisted as petri-net-json v1)
  ├─ Places: feature_ready, resource_token, goal_satisfied, agent_attention, src_edit_capacity, ...
  ├─ Transitions: start_feature, claim_resource, complete_goal, ...
  │
  ├─ Subnet: feature_039 (prefix: f039_)
  │   └─ places/transitions: f039_design_start, f039_impl_start, f039_test_start, ...
  │
  ├─ Subnet: feature_040 (prefix: f040_)
  │   └─ f040_...
  │
  └─ ...
```

**Collision-safe renaming:** Every subnet place/transition gets a prefix (`f{N}_`). Boundary ports are **shared places** (no prefix) connecting supervisor ↔ subnet.

### 1.2 Boundary Ports (The Composition Contract)

| Port Place | Role | Connected To |
|------------|------|--------------|
| `feature_ready` | Feature may start | Supervisor `start_feature` → Subnet `f{N}_design_start` |
| `resource_token` | Resource capacity claim | Subnet transitions needing capacity → `resource_token` (complement place) |
| `goal_satisfied` | Feature/phase complete | Subnet `f{N}_done` → Supervisor `complete_goal` |

**Analysis Glue:** After each mutation, run:
1. Per-subnet `PetriNetAnalyzer` (independent, parallelizable)
2. Supervisor cross-analysis: `deadlocks()` across full composed net
3. Invariant check: `place_invariants()` on full net validates capacity constraints

### 1.3 Incremental Re-verify (F3 Mitigation)

The library's `PetriNetAnalyzer` is **constructor-bound** — no partial analysis API. v1 approximation:

```python
# After mutating subnet f040:
affected = [subnet_f040, supervisor_net]  # manual scope
for net in affected:
    analyzer = PetriNetAnalyzer(net)
    analyzer.deadlocks(max_states=1000)
    analyzer.place_invariants()
# Full recompute fallback when nets grow
```

**Do not extend the library** (D2/D3) — the harness engine implements its own scoped-analysis helper without touching agentx.

### 1.4 Composition Overlay File (New in v3 — Resolves Open Item #9)

Where does "which node belongs to which subnet" live? **Not in the v1 file** — it must stay a pure flat union (D2). A harness-internal overlay file sits beside the union net; it is NOT part of `petri-net-json` (no conformance impact, no format change):

```json
// .meta/.omt/supervisor.overlay.json
{
  "net_file": "META_NET.petri.json",
  "revision": 42,
  "supervisor": { "places": ["feature_ready", "..."], "transitions": ["start_feature", "..."] },
  "subnets": {
    "feature_039": {
      "prefix": "f039_",
      "places": ["f039_design_start", "..."],
      "transitions": ["f039_run_tests", "..."],
      "ports": { "entry": "feature_ready", "exit": "goal_satisfied",
                 "resources": ["resource_token", "src_edit_capacity"] }
    }
  },
  "disabled": []
}
```

- Written atomically with the net file + sidecar (three-file transaction, §7.2).
- Composition view = `v1 union net` + `overlay`; the analysis glue (§1.2) reads both.
- `disabled` keeps **archive visibility** for soft-removed subnets even after their nodes were spliced out of the union — the dashboard/probe can still show history (§11 #8).

---

## 2. Resource Places & Concurrency Modeling (Complement Places)

> **v2 note:** IDEA-003 keeps the full resource catalog in the core roadmap (§6). This section is unchanged.

### 2.1 Standard Petri-net Capacity Modeling

The library has **no native place capacity**. We model it with **complement places** — already the invariant-verification idiom:

```
Place: src_edit_capacity (initial tokens = 1)
Complement: src_edit_active (initial tokens = 0)

For each transition needing src_edit:
  add_input("src_edit_capacity", transition, 1)
  add_output(transition, "src_edit_active", 1)

Invariant: tokens(src_edit_capacity) + tokens(src_edit_active) = 1
```

**Verified via:** `analyzer.place_invariants()` — returns basis vectors for `Cᵀ x = 0` (token-conservation laws). Capacity constraint = invariant holds.

### 2.2 Resource Place Catalog

| Place | Capacity | Consumers | Meaning |
|-------|----------|-----------|---------|
| `agent_attention` | 1 | All transitions | Single-threaded agent (hard constraint) |
| `src_edit_capacity` | 1 | Any `src/` edit transition | Phase gate + e2e receipt |
| `tests_capacity` | 1 | Test execution transitions | Test runner exclusivity |
| `harness_surface_round` | 1 | Harness surface edit transitions | `omt_*` tool edits + docs |
| `e2e_receipt` | 1 | Features needing e2e refresh | E2E test receipt token |

**Conflict = structural mutual exclusion:** Two features needing `src_edit_capacity` have transitions both input from it — only one can fire at a time. **Deadlock = two features blocked on same resource place** — detected by `analyzer.deadlocks()`.

### 2.3 The `agent_attention = 1` Serial-Mirror Semantics (v4)

> **v4 note:** v3 cataloged `agent_attention` ("consumed by all transitions") but never stated the *modeling consequence*. It matters for two reasons.

1. **It is the engineering reason F7 holds.** Because *every* transition inputs from the capacity-1 `agent_attention`, any reachable marking has at most one token in a `*_active` complement of `agent_attention` at a time. The composed net's reachable behavior therefore *mirrors the single-threaded agent exactly* — at no reachable marking can two "real" work transitions both be enabled. "Concurrency" in the net is capacity-constrained by construction, not by coincidence. This is by design (F7: decision support, not a scheduler), not a modeling bug. `deadlocks()` still has value: it detects structural *conflict traps* (two features permanently blocked on the same resource), which is the guidance the agent needs — it is not predicting actual parallel execution.

2. **Multi-resource consumption is the mutual-exclusion mechanism, not single-token-per-fire.** A transition that needs both `src_edit` *and* `tests` inputs from *both* capacity/complement pairs — each pair consumed independently. Because `agent_attention` is a *separate* complement pair, a transition inputting `src_edit_capacity` + `agent_attention` claims both in one fire; this is correct and does not double-count the "one agent" constraint. Conformance vectors (§3.4) must include a case proving a multi-resource fire conserves the sums `tokens(cap)+tokens(active)=1` **for each** pair after firing.

---

## 3. Structural Transactions (Atomic, Versioned, Audit-Logged)

### 3.1 Mutation Operations (Splice API)

```python
# omt_net_splice op
mutation = {
    "revision": 42,
    "reasoning": "feature_040 needs resource_token for tests_capacity",
    "add_places": [{"name": "f040_test_start", "tokens": 0}],
    "add_transitions": [{"name": "f040_run_tests"}],
    "add_arcs": [
        {"source": "f040_test_start", "target": "f040_run_tests", "weight": 1},
        {"source": "resource_token", "target": "f040_run_tests", "weight": 1},  # capacity claim
        {"source": "f040_run_tests", "target": "f040_test_done", "weight": 1},
    ],
    "disable_places": [],      # soft removal
    "remove_places": [],       # hard removal (requires token policy)
}
```

> **v3 note:** the library has **no `disable` primitive** (verified — `model.py` API is add_/is_/fire_/reset only). "Soft removal" is therefore an *overlay* concept: `disable_places` ≡ remove-with-policy on the flat net + a ledger `kind:"net_disable"` record carrying the full mutation, so undo = inverse splice replay from the ledger (§11 #8).

### 3.2 Token Policies on Removal

| Policy | Behavior |
|--------|----------|
| `drain` | Fire enabled transitions to consume tokens before removal |
| `reroute` | Move tokens to sibling place (specified in mutation) |
| `forbid` | Block removal if tokens present (default, safest) |

### 3.3 Ledger Record (Appends to `.meta/.omt/ledger.jsonl`)

```json
{
  "ts": "2026-08-30T...",
  "kind": "net_splice",
  "session": "...",
  "revision": 42,
  "reasoning": "feature_040 needs resource_token for tests_capacity",
  "mutation": { "add_places": [...], "add_transitions": [...], "add_arcs": [...] },
  "conformance_vector_regression": true,
  "feature": "feature_040.net_composition_supervisor"
}
```

**Record style (v3, conformed to the real ledger):** `.meta/.omt/ledger.jsonl` uses flat, `kind`-discriminated records — verified kinds in-repo: `phase`, `complete`, `skip`, `q`, `think_consult`, `project`/`project_link`. Net ops use `kind: net_*` (`net_splice`, `net_disable`, `net_fire`, `net_sync`).

### 3.4 Conformance Vector Regression

After each structural mutation, re-run the **9 conformance vectors** against the mutated net to ensure the engine's semantics haven't drifted. This is the same discipline as studio D8. (Trigger policy locked in IDEA-003 §4 #4: **every** splice, CI block on failure, dev-mode fast-check of the first 3 vectors.)

---

## 4. Goal→Net Synthesis (Bounded to Deterministic Templates)

### 4.1 Explicit Non-Goal: No Free-Form Synthesis

> **F4 mitigation:** "Synthesize a subnet from a goal" is the least mechanical feature; without a structured goal schema it becomes free prose → unbounded modeling. **Scope to declared mapping only.**

### 4.2 Template Mapping (Declarative)

| Goal Fragment (from WORK.md / FEATURE.md) | Net Template (Deterministic) |
|------------------------------------------|------------------------------|
| Task bullet: "Implement X" | Chain: `f{N}_start_X` → `f{N}_impl_X` → `f{N}_done_X` |
| Dependency: "X before Y" | Arc: `f{N}_done_X` → `f{N}_start_Y` |
| Resource need: "needs src_edit" | Input arc from `src_edit_capacity` (weight=1) |
| Acceptance criterion: "X works" | Output place `f{N}_X_verified` + invariant check |

### 4.3 Synthesis Workflow

```
1. Parse WORK.md / FEATURE.md for structured bullets (not free prose)
2. For each bullet, select template
3. Compose templates into fragment (connect shared places)
4. omt_net_splice with atomic transaction + reasoning
5. omt_net_invariant (re-verify full net)
```

**Only deterministic template composition + splice ships. Free-form = explicitly out.**

---

## 5. Tool Surface: Single `omt_net` Tool with Ops (F5 Mitigation)

**Pattern:** `.opencode/plugins/omt_q.ts` — one registered tool, internal sub-tools dispatched via `op`.

> **v4 note:** this section supersedes the scattered op lists in IDEA-001 §5 (`probe|fire|invariant|drift|splice`), IDEA-003 §5 (`probe|fire|splice|invariant|synthesize`), and the earlier v2/v3 wording (`probe|fire|splice|synthesize|invariant` plus a separately-introduced `sync`). **The canonical set below is what `omt_net.ts`'s `z.enum` must match at feature_039 design time.** v3 dropped `drift` as a standalone op (folded into `invariant` per §8); v4 keeps that choice but makes it explicit and adds the mutating/read-only split + regression matrix that the earlier versions lacked.

### 5.0 The Ops Taxonomy (canonical — v4)

Every net operation is a `switch` case under the single `omt_net` registration. The set is **closed** at feature_039 design time; v4 adds no new mechanics, it consolidates the ones already scattered across the trio and §11:

| op | Class | Mutates | Conformance vectors? | What it does |
|---|---|---|---|---|
| `probe` | read | no | — | Observe current marking + enabled transitions + analyzer advice (deadlocks/bounds/invariants). Pure report. |
| `fire` | mutate (marking) | **yes** (sidecar only) | **no** | Validate enablement via analyzer, apply marking change, write sidecar atomically, ledger `kind:"net_fire"`. *Structural change? No — so no conformance regression.* |
| `splice` | mutate (structure) | **yes** (net + sidecar + overlay) | **yes (9 vectors)** | Atomic structural mutation. Sub-actions via a `mode` arg: `add`, `remove`, `disable` (≡ remove-with-policy, §3.1), `undo` (inverse splice replay from ledger, §11 #8). All write atomically with rollback, bump revision, `kind:"net_splice"/"net_disable"`. |
| `sync` | mutate (structure, agent-visible) | **yes** | **yes (9 vectors)** | net↔reality bootstrap/resync (§11 #6 / §13 D11). Emits a deterministic **proposal** through the normal `splice` path; never silent (D4). On `close`/`archive` lifecycle events it drives subnet `disable`. |
| `synthesize` | mutate (structure + goal mapping) | **yes** | **yes (9 vectors)** | Goal→net template composition (bounded, §4) followed by the `splice` that materializes it. |
| `invariant` | read | no | — | Re-run full-net invariants + **surface net-vs-ledger drift** (§8). This is where the `drift` op from IDEA-001 lands. |

**Read-only ops (`probe`, `invariant`) never write.** Mutating ops (`fire`, `splice`, `sync`, `synthesize`) bump `revision` and write atomically. **Conformance regression (§3.4) is required only for structure-changing ops** (`splice`, `sync`, `synthesize` — every one, 9 vectors, CI block); `fire` changes marking only, never structure, so it is exempt from the 9-vector run (it still re-checks invariants via the analyzer per §7.2). This matrix was ambiguous in v3 (§3.4 said "every splice" but never addressed `fire`/`sync`); v4 fixes it.

> **Note on `disable` vs a separate op:** §11 #8 resolves `disable` ≡ remove-with-policy + ledger `kind:"net_disable"` + undo-by-inverse-replay. v4 keeps that *mechanism* inside `splice{mode}` and does **not** add a 7th op — preserving the F5 rationale (one registration, small surface). Similarly `undo`/`--repair` (§11 #7 rebase repair) is a *recovery path*, not a separate tool op: it is exposed as `splice{mode:"undo"}` and `splice{mode:"repair"}`, both replayed from ledger mutations.

```typescript
// .opencode/plugins/omt_net.ts (one registration — canonical op set, v4)
const omt_net = tool({
  description: "Net observability layer: probe|fire|splice|sync|synthesize|invariant",
  args: {
    op: z.enum(["probe", "fire", "splice", "sync", "synthesize", "invariant"]),
    // op-specific args... (splice: mode add|remove|disable|undo|repair)
  },
  async execute(args) {
    switch (args.op) {
      case "probe":      return omt_net_probe.execute(args);
      case "fire":       return omt_net_fire.execute(args);
      case "splice":     return omt_net_splice.execute(args);
      case "sync":       return omt_net_sync.execute(args);
      case "synthesize": return omt_net_synthesize.execute(args);
      case "invariant":  return omt_net_invariant.execute(args);
    }
  }
});
```

**Avoids:** 6 separate tool registrations × drift-pinned budgets × nav-indexed gotchas × quick_ref/workflow docs × e2e receipt refresh per tool. (F5 — the main *process* cost, per PROJECT.md feasibility.)

### 5.1 Bootstrap Ordering (net does not exist yet — v4)

`probe`/`invariant`/`fire` are no-ops (fail clean with a "net not bootstrapped" envelope) until the first `omt_net_sync` has materialized `META_NET.petri.json` + `net_state.sidecar.json` + `supervisor.overlay.json`. This ordering was implicit in v3 (§7.2 files, §11 #6 bootstrap) but never stated as a guard; feature_039 design must treat `sync` (not `probe`) as the first-call entry point.

---

## 6. War-Room Dashboard (Reuse, Not Build)

> **v2 note:** scope decision locked per IDEA-003 §4 #5 — **static build only**. Dashboard reads `.meta/.omt/META_NET.petri.json` + `net_state.sidecar.json` at build time; no dev server, no live WebSocket.

### 6.1 Studio Assets (Feature_036 — SHIPPED)

| Asset | File | Reuse Target |
|-------|------|--------------|
| Graph projection | `graphProjection.ts` | Live supervisor net rendering |
| Token animation | `animation.ts` | Animated token flow |
| Gallery | `Gallery.tsx` | Revision slider (snapshots) |
| Graph Explorer | `GraphExplorer.tsx` | Collapsible subnets, deadlock highlight |

### 6.2 New Work Only

- Read harness net JSON store (not studio's)
- Deadlock highlight overlay (colors from `deadlocks()` result)
- Revision slider binding (ledger revisions → snapshots)

### 6.3 Build Pipeline

Same `npm run build` → `dist/` + preview smoke (feature_034-036 proven). Static build only (no dev server).

---

## 7. File Persistence & Live Marking (Resolves IDEA-001 Open Item #1)

### 7.1 The Gap

`petri-net-json` v1: `"tokens is the initial marking M0, never the live marking; v1 has no current-marking snapshots."` (Confirmed in `FORMAT.md` §1: "The format describes **structure + initial marking only**.")

### 7.2 Decision: Sidecar File (Path B) — Schema per IDEA-003 §3.1

**Files (both in `.meta/.omt/`):**

```
.meta/.omt/META_NET.petri.json     → net structure + initial marking (petri-net-json v1, UNCHANGED)
.meta/.omt/net_state.sidecar.json  → live marking (v2 schema, IDEA-003 §3.1)
```

```json
{
  "live_marking": [0, 1, 0, 2, ...],  // tuple over place_order of META_NET.petri.json
  "revision": 42,
  "updated_at": "2026-08-30T..."
}
```

**Atomic write protocol (IDEA-003 §4 #1):** `omt_net_fire` writes both files in a single `try/except` that **rolls both back on failure** — the net file and sidecar can never drift mid-write.

**Rationale:**
- No format change to proven v1 (no ripple to `io.py`/`io.ts`/studio/conformance)
- Live marking is inherently ephemeral — sidecar reflects that
- `omt_net_probe` reads both files; `omt_net_fire` writes both atomically
- **v2 wording fix:** the sidecar holds *live marking only*; the net file remains the structural authority. This is the two-source-of-truth pattern, per IDEA-003 §2.1.
- **Git policy (v3):** `.meta/.omt/*` is git-ignored — only `harness.ir.json` + `nav.index.jsonl` are tracked (`.gitignore`). Net artifacts are runtime state like the ledger itself: durability comes from the revision field + ledger audit + git-pinned conformance vectors, not from git history.
- **Ordering & rebase (v3):** `place_order` is **derived** (sorted names — verified `place_order = tuple(sorted(...))` in `model.py`), never append position; the sidecar tuple is re-bound to names at load and rebased inside structure-changing splices (§11 #7).

---

## 8. Net-vs-Ledger Reconciliation (Resolves IDEA-001 Open Item #2)

### 8.1 The Drift Problem — Two Sources of Truth

1. **Net file + sidecar + overlay** — observability model (marking, structure, concurrency conflicts)
2. **Ledger + Phase FSM + TDD FSM** — *real approval authority* (`g.phase`, `g.tests`, `g.think`, `g.receipt`)

Per IDEA-003 §2.1, the ledger/gates are **primary**; the net is **secondary** (observability/guidance).

### 8.2 Reconciliation Rule (Explicit — IDEA-003 §4 #2)

```python
# omt_net_invariant op — run as the drift check at EVERY omt_complete exit
def reconcile_net_vs_ledger():
    # 1. Net says feature_040 can fire start_feature
    # 2. Ledger says feature_040 phase = "Design" (gate allows)
    # 3. If net allows but ledger blocks → LOG drift, do NOT fire (gate wins)
    # 4. If ledger allows but net blocks → LOG drift, net authority wins for the fire
    #    (the analyzer blocks the fire), but the workflow may still proceed via gates
    # 5. Append record to .meta/.omt/harness.net.drift.jsonl:
    #    {"ts", "feature", "net_state", "ledger_state", "resolved"}
```

**Model:** `omt_q{op:drift}` — KB-vs-source classification. Here: net-vs-ledger. Drift is **logged, not silently resolved** (IDEA-003.D2). Record shape mirrors `omt_q{op:drift}`'s `drift_records` envelope (classification tags, e.g. GONE/MOVED-style), so surfacing is consistent across both drift kinds.

---

## 9. Harness Engine Implementation (Parity Clone)

### 9.1 Location & Structure

```
scripts/omt/net/
├── __init__.py
├── model.py          # Clone of src/agentx/model/petri_net/model.py
├── analysis.py       # Clone of src/agentx/model/petri_net/analysis.py
├── errors.py         # Clone of errors
├── io.py             # Clone of io.py (petri-net-json v1)
├── conformance.py    # Runs 9 vectors against engine (byte-identical)
└── state.py          # NetState: loads META_NET.petri.json + net_state.sidecar.json +
                      # supervisor.overlay.json; saves all atomically (rollback on failure);
                      # appends drift records; rebases marking on splice (§1.4, §11 #7)
```

Runtime artifacts (IDEA-003 §3.1 + §1.4): `.meta/.omt/META_NET.petri.json`, `.meta/.omt/net_state.sidecar.json`, `.meta/.omt/supervisor.overlay.json`, `.meta/.omt/harness.net.drift.jsonl`.

### 9.2 Parity Discipline (D2)

- **Never imports `src/agentx/model/petri_net/` at runtime**
- Conformance vectors generated from the tested library → pinned byte-identical
- Harness engine is a Python clone of a Python spec (lower risk than studio's TS port)

### 9.3 Testing

- `tests/scripts/omt/test_net_conformance.py` — runs 9 vectors
- `tests/scripts/omt/test_net_engine.py` — unit tests for fire/probe/splice
- Sentinel bridge: `tests/features/feature_039/...` (pytest-side verification)

---

## 10. Roadmap Re-scoped (3 Core + 2 Optional — numbered per PROJECT.md)

| # | Feature | Type | Deliverable | Depends |
|---|---------|------|-------------|---------|
| 1 | `feature_039.adaptive_net_engine` | minor_feature | Harness engine + net file + sidecar + probe/fire/invariant ops + 9-vector parity | — |
| 2 | `feature_040.net_composition_supervisor` | minor_feature | Supervisor + subnet composition, boundary ports, incremental cross-analysis | 1 |
| 3 | `feature_041.resource_places_concurrency` | minor_feature | Complement-place capacities, deadlock detection, conflict surfacing | 2 |
| 4 | `feature_042.goal_net_synthesis` | minor_feature (optional) | Template composition + splice | 2 |
| 5 | `feature_043.meta_net_dashboard` | major_feature (optional) | Studio reuse dashboard | 1-3 |

**Core = 1-3.** 4-5 are phase-2, only if core proves valuable (IDEA-003 §6 re-scope, not cancellation).

---

## 11. Open Items (Must Resolve Before Build)

**v3 status:** open items 1–5 were **resolved in design** by IDEA-003 §4 (ship with feature_039/040). Items 6–9 were **resolved in design by this v3 pass** (rows below; validation points noted). No blockers remain — feature_039 (engine + sidecar + sync) and feature_040 (composition + overlay) carry the validated designs.
**v4 status:** items 4/6/7/8 cross-referenced to the §5.0 ops taxonomy + §5.1 bootstrap ordering; sync authorization sharpened (#6). No new open items.

| # | Item | Status |
|---|------|--------|
| 1 | **Live marking sidecar schema** — exact JSON structure, atomic write protocol | **RESOLVED (design)** — IDEA-003 §3.1/§4 #1: `net_state.sidecar.json` `{live_marking, revision, updated_at}`; two-file atomic write with rollback |
| 2 | **Net-vs-ledger drift check** — when to run, how to surface, what to do on conflict | **RESOLVED (design)** — IDEA-003 §4 #2: every `omt_complete` exit; ledger primary, net blocks fires; `harness.net.drift.jsonl` |
| 3 | **Subnet prefix scheme** — `f{N}_` vs `feature_{N}_` vs UUID; collision guarantee | **RESOLVED (design)** — IDEA-003 §4 #3: `f{N}_` where N = roadmap feature number (auto-assigned at scaffold) |
| 4 | **Conformance regression trigger** — on every splice? on commit? CI only? | **RESOLVED (design)** — IDEA-003 §4 #4: after **every** structure-changing op (`splice`, `sync`, `synthesize`) → 9 vectors; CI block; dev fast-check (3 vectors). `fire` is **exempt** (marking-only, no structure). Matrix locked in §5.0 (v4) |
| 5 | **Dashboard scope** — static build only? live WebSocket updates? | **RESOLVED (design)** — IDEA-003 §4 #5: static build only; reads sidecar at build time |
| 6 | **Net↔reality sync** — how the net is born and kept faithful to WORK.md + `.projects/` + feature dirs | **RESOLVED (design, v3; v4 sharpens authorization + ordering)** — `omt_net_sync` op: bootstrap + re-sync on `project.py` lifecycle events (`new\|link\|log\|status\|close\|archive\|reopen\|backfill\|sync` — verified CLI) + `new_feature.py --project` link; skeleton derived from `.projects/meta/META.md` + WORK.md `## Projects` + feature dirs; sync emits a deterministic **proposal** through the normal splice path — never silent (D4). **v4:** the *proposal* is **not** auto-applied — it is surfaced for the agent to approve and fire via `splice` (the gates still own real approval, D3; the net never self-mutates reality). Bootstrap ordering: `sync` is the **first-call** entry (§5.1) — probe/invariant/fire no-op until the net exists. Validate trigger wiring at feature_039 design |
| 7 | **`place_order` stability** — sidecar tuple vs place-set changes | **RESOLVED (design, v3)** — order is **derived** (sorted names; verified `place_order = tuple(sorted(...))` in `model.py`); tuple → name map at load; every structure-changing splice rebases the marking **by name** and writes the sidecar in the same transaction; `revision` mismatch → refuse probe/fire; rebase repair is replayed from the ledger mutation via `splice{mode:"repair"}` (v4: recovery path, **not** a separate op — §5.0). Validate repair path at feature_039/040 |
| 8 | **Subnet lifecycle & archive policy** — completed features/projects | **RESOLVED (design, v3)** — library has **no disable primitive** (verified); `disable` ≡ remove-with-policy (default `forbid`; drained at completion) recorded `kind:"net_disable"` with the full mutation → undo = inverse splice replay (`splice{mode:"undo"}`, §5.0); `project.py close/archive` triggers subnet disable via `omt_net_sync`; ledger truth untouched (D3). Overlay keeps archive visibility (§1.4) |
| 9 | **Composition overlay persistence** — WHERE subnet membership / boundary ports / disabled set live (the v1 file must stay a pure flat union) | **RESOLVED (design, v3, §1.4)** — `supervisor.overlay.json` beside the union net; three-file atomic transaction; no conformance impact. **Least battle-tested** — validate schema at feature_040 design |

---

## 12. References (Source-Verified)

- `PROJECT.md` (this project) — locked decisions D1–D4; feasibility F1–F7; roadmap proposal feature_039–043
- `IDEA-001` — file-backed net control, format decision, open items 1-4 (nos. 1-2 resolved by this doc + IDEA-003 §4)
- `IDEA-003` — additive observability layer (net guides/observes, gates own approval); resolves the single-source-of-truth tension; §4 = design resolutions for open items 1-5
- `.sandbox/pause_2026-08-30.md` — original architecture deep-dive summary (superseded in parts by IDEA-001/002/003)
- `shared/petri-net/FORMAT.md` — v1 = structure + initial marking only; **no current-marking snapshots** (the sidecar gap, §7)
- `src/agentx/model/petri_net/model.py` (200 lines) — flat P/T net API
- `src/agentx/model/petri_net/analysis.py` (430 lines) — BFS, invariants, exact rational
- `tools/petri-net-studio/src/engine/model.ts` (233 lines) — TS parity port (A3 code-point sort)
- `tools/petri-net-studio/src/engine/analysis.ts` (509 lines) — 1:1 explore, Fraction nullspace
- `shared/petri-net/conformance/analysis-v1/` — 9 byte-identical vectors
- `tools/petri-net-studio/tests/engine/conformance.test.ts` — vector test pattern
- `.opencode/plugins/omt_q.ts` (817 lines) — single-tool-with-ops pattern (and `op:drift` = model for §8)
- `scripts/omt/new_feature.py` / `project.py` — scaffolding integration
- `META_HARNESS.omt` — phase FSM + gates + budgets; the PRIMARY authority the net layer sits atop (D3)
- `.meta/.omt/ledger.jsonl` — real record shape (flat `kind`-discriminated; verified kinds: phase/complete/skip/q/think_consult/project*) — §3.3/§8 conform to it
- `.gitignore` — `.meta/.omt/*` ignored except `harness.ir.json` + `nav.index.jsonl`; net artifacts are runtime state (§7.2)
- `scripts/omt/project.py` — lifecycle CLI (`new|link|log|status|close|archive|reopen|backfill|sync`) + `_sync_all()`; net re-sync hook points (§11 #6)
- `scripts/omt/new_feature.py` — `--project` chains to `project.py link` (subnet creation trigger, §11 #6)
- `src/agentx/model/petri_net/model.py` — `place_order = tuple(sorted(...))` (derived order); **no disable primitive** — verified (§3.1, §11 #7/#8)

---

## 13. Decision Log (This Idea)

- **IDEA-002.D1 — Flat engine, compositional overlay:** The harness engine stays flat (parity). Composition = modeling layer in store + analysis glue.
- **IDEA-002.D2 — Complement places for capacity:** Standard Petri-net technique; verified by existing `place_invariants()`; no engine change.
- **IDEA-002.D3 — Single `omt_net` tool with ops:** Follows `omt_q` precedent; avoids F5 harness surface churn. **(v4 supersedes the op-list reference: canonical set = §5.0 `probe|fire|splice|sync|synthesize|invariant`.)**
- **IDEA-002.D4 — Sidecar for live marking (schema = IDEA-003 §3.1):** Resolves IDEA-001 open item #1 without touching proven v1 format; `net_state.sidecar.json` + atomic two-file write.
- **IDEA-002.D5 — Net-vs-ledger reconciliation as drift check:** Resolves IDEA-001 open item #2; modeled on `omt_q{op:drift}`; refined v2: drift check runs at **every `omt_complete` exit**; ledger = primary approval authority (IDEA-003 §4 #2).
- **IDEA-002.D6 — Synthesis = templates only:** Free-form explicitly out; bounds scope to deterministic composition.
- **IDEA-002.D7 — Core roadmap = 3 features:** feature_039–041 ship; feature_042–043 optional phase-2 (IDEA-003 §6 re-scope).
- **IDEA-002.D8 — Additive layer, not control plane (v2, adopts IDEA-003):** the net-of-nets mirrors/guides/blocks via the analyzer; `META_HARNESS.omt` + phase FSM + ledger remain PRIMARY (D3; IDEA-003.D1/D2). Supersedes the v1 summary framing ("the META HARNESS control plane is a flat Petri net").
- **IDEA-002.D9 — Resolved-in-design open items 1–5 (v2):** per IDEA-003 §4 — sidecar schema, drift-check cadence, `f{N}_` prefix, splice-time conformance regression, static dashboard. Not re-litigated; ship with feature_039/040.
- **IDEA-002.D10 — Remaining open items 6–9 (v2/v3):** net↔reality sync, `place_order` stability, subnet lifecycle, composition-overlay persistence — all resolved-in-design in v3 (§11); ship with feature_039–041.
- **IDEA-002.D11 — Net↔reality sync via lifecycle hooks (v3):** `omt_net_sync` op; bootstrap + re-sync on `project.py` lifecycle events + `new_feature.py --project` link; sync = deterministic proposal through the splice path, never silent (D4). **v4 sharpening: the proposal is surfaced for agent approval + `splice`, never auto-applied (gates own approval, D3); sync is first-call (§5.1).**
- **IDEA-002.D12 — Derived ordering + splice rebase (v3):** `place_order` = sorted names (library-verified); marking rebased by name inside every structure-changing splice; `revision` mismatch → refuse; rebase repair replayed from ledger via `splice{mode:"repair"}` — recovery path, not a separate op (§5.0).
- **IDEA-002.D13 — Lifecycle = remove-with-policy + ledger `net_*` records (v3):** no library disable primitive; `disable` ≡ structural removal w/ token policy, `kind:"net_disable"`, undo = inverse splice replay (`splice{mode:"undo"}`); overlay keeps composition view (§1.4).
- **IDEA-002.D14 — Net artifacts are runtime state (v3):** `.meta/.omt/*` git-ignored (ledger pattern); durability via revision + ledger audit + git-pinned conformance vectors.
- **IDEA-002.D15 — Canonical ops surface + mutating/read-only split (v4):** `omt_net` op set consolidated to §5.0 (`probe|fire|splice|sync|synthesize|invariant`); `drift` folded into `invariant`, `disable`/`undo`/`repair` are `splice{mode}` sub-actions (not new ops), `sync` promoted to a first-class op; conformance regression required only for structure-changing ops (`splice`/`sync`/`synthesize`), `fire` exempt; bootstrap ordering (`sync` = first call, §5.1).

---

*End of IDEA-002 (v4)*