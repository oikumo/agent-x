# IDEA-001 — File-Backed Net Control (real petri-net file as the control authority)

> Created 2026-08-30 · session re-scoping that supersedes the vague "in-memory mirror" framing of PROJECT.md.
> Decision captured here (user-confirmed): **control is by a REAL, persisted Petri-net FILE in the repo's own `petri-net-json` v1 format, where the file is the AUTHORITY and the analysis authority feeds back into decisions.**

---

## Status

- **State:** candidate idea — not yet a locked project decision, not yet a feature.
- **Supersedes in intent:** PROJECT.md's loose "net-of-nets, supervisor + subnets, in-memory store" framing. This doc pins the *control mechanism* concretely: a file.

---

## The idea, in one line

**The META HARNESS drives its own observe → decide → fire → re-verify control loop off a real, versioned, persisted Petri-net FILE (repo `petri-net-json` v1) whose live marking is the authority, and whose analysis (deadlock / bounds / liveness / invariants, via an in-repo engine) decides whether a fire is allowed.**

---

## Why this is the right sharpening (what it fixes)

The prior framing ("net-of-nets mirror", "JSON store", "in-memory marking") had a fatal weakness: **the net had no authority** — the agent drove the net, so it was a journal, not a controller. Making the net a **real file** dissolves that:

1. **The file is the control artifact.** Mutating the file (atomic, versioned, audit-logged) IS the "fire." The loop is structural, not a re-labeling of `omt_q`.
2. **Analysis is the external-to-the-net authority.** A fire is accepted only if the analyzer says the transition is enabled and post-fire invariants hold. The net can *block* (reject a fire that would deadlock / invariant-breach) — that is real control, not advisory-only.
3. **It makes D4 concrete.** The agent owns the *net file* (mutate, version, audit); the user owns *goals*. The file is the object of that ownership.

---

## The control workflow (intent)

```
OBSERVE   read META_NET.<rev>.petri.json  → current marking (the FILE is truth)
DECIDE    omt_net_probe: enabled transitions at that marking + analyzer advice
             (deadlocks / bounds / liveness / place-invariants)
FIRE      omt_net_fire {transition, reasoning} → validate enablement via analyzer
             → apply marking change → write NEW rev of the file (transactional)
RE-VERIFY omt_net_invariant: re-run analyzer on the new file; REJECT/splice on violation
```

Every fire carries reasoning (D4). Every file mutation bumps the revision and is audit-logged. Analysis is deterministic per the pinned engine semantics.

---

## Format decision (user-confirmed)

**Format: the repo's OWN `petri-net-json` v1** (`shared/petri-net/FORMAT.md`, `io.py` + `io.ts`, conformance vectors, JSON schema). NOT PNML / ISO 15909 / a third-party tool format.

Consequences:
- **Reuses everything proven** — `io.py`/`io.ts` round-trip byte-identity, 9 conformance vectors, JSON schema validation. Persisting the net is a solved, tested problem.
- **"External analysis" = the in-repo `PetriNetAnalyzer`** copy (parity engine), NOT PIPE/TINA/WoPeD (none can read `petri-net-json`). This must be stated plainly in the design so it never becomes a scope surprise.
- **D2 preserved:** the harness never imports `src/agentx/model/petri_net/` at runtime; it is a parity clone (Python-clone-of-a-Python-spec — lower risk than the studio's TS port was).

---

## Feasibility (grounded in the actual API, verified this session)

| Component | Evidence | Assessment |
|---|---|---|
| Net modeling surface | `PetriNet.add_place/add_transition/add_input/add_output`, `is_enabled_at`, `enabled_transitions_at`, `fire_marking/fire`, `current_marking`, `marking_to_dict`, `reset` | High — everything needed for deterministic observe/fire |
| Analysis authority | `PetriNetAnalyzer.deadlocks/bounds/reachable_markings/transition_liveness/strongly_connected_components/place_invariants/transition_invariants/incidence_matrix` (158 tests) | High — full authority exists |
| Persistence / io | `petri-net-json` v1, round-trip byte-identity, conformance vectors, JSON schema | High — pure reuse |
| Parity-without-import | Proven by studio TS port (9 vectors, byte-identical); harness is a Python clone of a Python spec | High — lower risk than the TS port |

**Verdict: feasible, mostly reuse.** Choosing the repo format (over PNML) removes the largest new-work item (XML parsing + external-tool validation + conformance matrix).

---

## Four open items that MUST be settled before building (ranked)

### 1. Live-marking persistence — THE #1 blocker (RESOLVED: v2 format extension)

`petri-net-json` v1 explicitly has *no current-marking snapshot*: "tokens is the initial marking M0, never the live marking; v1 has no current-marking snapshots" (FORMAT.md §7, io.py line 309-310). A control loop must persist the *live* marking.

**Decision: (a) v2 format extension** adding a `currentMarking` field — this is the only path that preserves "the file is authority" without a second artifact.

Rationale:
- The sidecar (b) reintroduces a second artifact, weakening the core thesis
- The v2 extension is surgical: add optional `currentMarking: array[int]` (parallel to `places` order) + bump `version: 2`
- Ripple is bounded: `io.py`/`io.ts` load/dump, schema, 9 conformance vectors — all proven patterns
- Studio already consumes `layout` (UI-namespaced, semantically inert); `currentMarking` is the semantic dual
- Versioning policy (FORMAT.md §9) exists exactly for this: structural members change → version bump

**v2 sketch:**
```json
{
  "format": "petri-net-json",
  "version": 2,
  "places": [...],
  "transitions": [...],
  "arcs": [...],
  "currentMarking": [1, 0, 3],     // NEW: parallel to sorted(places), omitted = M0
  "layout": {...}
}
```
- Loaders: v1 docs accepted, `currentMarking` absent → treat as M0 (backward compatible)
- Writers: always emit v2; if `currentMarking` == `initial_marking`, omit (canonical minimal form)
- Schema: `currentMarking` optional array of non-negative ints, length = places.length

### 2. Net-vs-gates reconciliation rule (D3) — RESOLVED: drift check protocol

The net file is authority *for the net*, but the **ledger + phase FSM + TDD FSM still own the real approval authority** (`g.phase/g.tests/g.think/g.receipt`). Net-fire can *guide* and *log intent*, but cannot override the gates.

**Rule:** Every `omt_net_fire` emits a `kind:"net"` ledger record. Before any gate transition (phase advance, TDD step, harness surface edit), the agent MUST run `omt_net{op:drift}` which:
- Loads current net file marking
- Compares against ledger's last `net` record's expected marking
- Reports `drift: true|false` + divergence detail (places, expected vs actual)
- On `drift: true`: agent MUST reconcile (replay missing fires / splice correction) before proceeding

This mirrors `omt_q{op:drift}` exactly — same envelope, same gate. The net is a *controlled mirror* of the harness process, not a parallel authority.

### 3. Plain statement of analysis authority — LOCKED

**Locked:** "External analysis" = the in-repo parity engine (harness-owned clone of `PetriNetAnalyzer`), NOT an external tool. The repo format (`petri-net-json`) cannot be read by PIPE/TINA/WoPeD. If the user later wants external-tool interop, that requires a separate PNML export feature (out of scope for core).

### 4. Scope the roadmap down — LOCKED: 3-part core

The core is NOT the 5-feature sprawl of PROJECT.md. The core is **exactly three features**:

| # | Slug | Type | Deliverable |
|---|---|---|---|
| 1 | `feature_039.adaptive_net_engine` | minor_feature | Harness-owned net engine (`scripts/omt/net/`): v2 io (load/dump with `currentMarking`), `fire`/`probe`/`invariant` ops, parity engine clone, conformance-vector tested, no runtime import |
| 2 | `feature_040.net_composition_supervisor` | minor_feature | Net-of-nets composition: supervisor + per-project/per-feature subnets, boundary ports (`feature_ready`, `resource_token`, `goal_satisfied`), flat-union with collision-safe renaming, per-subnet + cross-analysis (deadlock), incremental re-verify |
| 3 | `feature_041.resource_places_concurrency` | minor_feature | Resource places & capacities (`agent_attention`=1, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt`); complement-place modeling + invariant verification; conflicts/deadlocks surfaced structurally |

**Phase 2 (optional, separate decision):** `goal_net_synthesis` (template composition only), `meta_net_dashboard` (studio projection reuse).

---

## `omt_net` tool surface (single tool, ops-based — mirrors `omt_q`)

Following the `omt_q.ts` precedent (817 lines, one tool, ops=state|plan|drift), **one `omt_net` tool with ops**:

| op | Purpose | Input | Output |
|---|---|---|---|
| `probe` | Observe | `{rev?, marking?}` | `{marking, enabled_transitions, analyzer_advice: {deadlocks, bounds, liveness, invariants}}` |
| `fire` | Decide+execute | `{transition, reasoning, rev_expected}` | `{rev_new, marking_new, analyzer_advice_post, ledger_record_id}` |
| `invariant` | Re-verify | `{rev?}` | `{deadlocks, bounds, place_invariants, transition_invariants, complete, explored_states}` |
| `drift` | Reconcile (gate) | `{rev?}` | `{drift: bool, divergence: [{place, expected, actual}], resolution_hint}` |
| `splice` | Structural mutate | `{add_places?, add_transitions?, add_arcs?, remove_subnet?, disable_transition?}` | `{rev_new, analyzer_advice_post, ledger_record_id}` |

All ops return JSON envelope with `as_of_commit=HEAD-sha`. `fire` and `splice` are the only mutating ops; both bump revision, write new file atomically, emit ledger `kind:"net"`.

---

## Honest limits (keep, don't forget)

- **Still not a scheduler.** `agent_attention = 1` (single-threaded agent) means the net fires transitions the *agent* then executes serially. The net's real control value is (a) **blocking** invalid fires via the analyzer, and (b) rigorous audit. Frame it as a **gate-augmenting blocker**, not an executor.
- **Two sources of truth** (net file + ledger/gates) — reconciled by the drift protocol (item 2), not hand-waved.
- **Pure software-dependency risk is low** but the v2 format-touch (item 1) is the one place a proven asset could regress — mitigate by generating conformance vectors from the library *after* v2 io is stable.

---

## References

- `PROJECT.md` (this project) — the original net-of-nets intent framing (parts superseded by this doc).
- `shared/petri-net/FORMAT.md` + `petri-net-json-v1.schema.json` — the v1 format (live-marking gap documented in §7, io.py:309-310).
- `src/agentx/model/petri_net/{model,analysis,io}.py` + `tests/model/petri_net/` — executable spec (D2 parity target).
- `tools/petri-net-studio/src/engine/{model,analysis,io,errors}.ts` — the proven parity port + conformance vectors (`shared/petri-net/conformance/analysis-v1/`).
- `.opencode/plugins/omt_q.ts` — the existing observe/interrogative layer the net loop aligns with (and its `op:drift` is the model for the net-vs-ledger reconciliation).

---

## Next actions (if user approves)

1. Lock this idea as a project decision (update PROJECT.md Summary/Purpose to reflect file-backed control)
2. Scaffold core feature: `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`
3. Design doc for feature_039 must include: v2 io spec, parity engine clone plan, conformance vector generation, `omt_net` tool spec with 5 ops

(End of file)