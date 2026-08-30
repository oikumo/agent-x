# IDEA-003 — Petri Net as Additive Observability Layer (not workflow driver)

> Created 2026-08-30 · follows IDEA-001 (file-backed net control) and IDEA-002 (compositional net-of-nets architecture).
> **Status:** candidate idea — resolves the "single source of truth" tension identified in the critical feasibility analysis.
> **Project context:** meta_harness_concurrent draft v0.2 (D1: meta harness only, not agentx); roadmap slots 039-043 verified free.

---

## 1. Problem Statement

The critical feasibility analysis (feature_039–043 roadmap, D1/D2 constraints) identified a **category error** in the central question:

> *"Create an intend workflow driven by a single source of truth a petri net tool formatted file"*

The `petri-net-json v1` format is **structurally unsuited** to be a workflow driver because it carries only **structure + initial marking M0**, not **current marking, priorities, or intended next action**. Making it the single source of truth would:

- Lose the enforced phase FSM discipline (`META_HARNESS.omt` → gates → receipt → edit loop)
- Bypass the TDD two-hat mechanism (red/green/refactor/done)
- Remove nav/think gates that prevent scope creep
- Require format extensions that risk conformance vector regression

**The harness already has a proven single source of truth:** `META_HARNESS.omt` + phase FSM + ledger + nav/think gates. This is enforced, tested, and working.

---

## 2. Resolution: Petri Net as Additive Layer

Instead of replacing the workflow driver, the Petri net model serves as an **observability/guidance overlay** that informs but does not control the workflow. This aligns with:

- **D3 — Additive over the gate contract:** "The net mirrors/guides/observes existing project/feature/phase flow; it does not replace, merge, or drop any gate, phase-FSM state, or TDD engine rule."
- **D1 — Meta-harness-only scope:** All net work stays in `scripts/omt/` + `.meta/`, no `src/agentx/` edits. *Project constraint: D1 locked per user directive 2026-08-30; this project does NOT touch src/agentx/, does NOT build agentx internal state.*
- **D2 — Parity-tested, no runtime import:** The harness engine is a Python clone of the library spec, conformance-vector pinned. *Engine lives in scripts/omt/; never imports src/agentx/model/petri_net/ at runtime (proven pattern from feature_035/036).*
- **Project Roadmap Alignment:** This idea maps to roadmap slots **feature_039.adaptive_net_engine** (minor_feature, core) through **feature_043.meta_net_dashboard** (major_feature, optional phase-2). Slots verified free in project draft v0.2.

### 2.1 The Two-Source-of-Truth Pattern

| Source | Authority | Role in Workflow |
|---|---|---|
| **`META_HARNESS.omt` + phase FSM + ledger** | **Primary** — controls phase exit, TDD cycle, gate enforcement, receipt freshness | **Workflow driver** — `nav → phase → tdd → complete → receipt → edit` |
| **Harnet net file + sidecar** | **Secondary** — models concurrent project/feature state, detects structural conflicts/deadlocks | **Observability layer** — `omt_net_probe` reports marking, `omt_net_fire` guides transitions |

**Reconciliation rule (IDEA-001 open item #2, IDEA-002 §8, Project D1):** The net may *guide* and *block* (via analyzer), but the ledger/gates own *approval authority*. Drift is logged, not silently resolved. *Project D1 constraint: All net work is confined to `scripts/omt/` + `.meta/` — no `src/agentx/` edits are permitted under this project.*

---

## 3. Architecture — How the Layer Works

### 3.1 Files (Stored in `.meta/.omt/` or `scripts/omt/`)

| File | Content | Who Writes |
|---|---|---|
| `META_NET.petri.json` | Net structure + live marking (via sidecar) | `omt_net_fire` / `omt_net_splice` |
| `net_state.sidecar.json` | Live marking tuple over `place_order`, revision, updated_at | `omt_net_fire` (atomic write with net file) |
| `.meta/.omt/harness.net.drift.jsonl` | Drift records: `{ts, feature, net_state, ledger_state, resolved}` | `omt_net_invariant` / phase exit |

### 3.2 The Control Loop (Enhanced, Not Replaced)

```
OBSERVE   read META_NET.petri.json + net_state.sidecar → current marking + analyzer advice
DECIDE    omt_net_probe: enabled transitions + deadlock/bounds/invariant status
           ↓ (net informs, does not dictate)
PHASE GATE: g.phase check + g.tests check + g.receipt check → proceed or block
FIRE      omt_net_fire {transition, reasoning} → if analyzer says enabled → apply marking
           → write NEW rev of META_NET.petri.json + net_state.sidecar → audit-logledger
RE-VERIFY omt_net_invariant: re-run analyzer; on violation → LOG drift, reject/splice
```

**Key difference from IDEA-001's "net as authority":** The phase gate (`g.phase`, `g.tests`, `g.receipt`) runs **between** DECIDE and FIRE. The net may advise "this fire is safe" but cannot override a gate block.

---

## 4. Open Items (Must Resolve Before Build)

| # | Item | Current Resolution | Risk if Unresolved | IDEA-002 Resolution |
|---|---|---|---|---|
| 1 | **Live-marking sidecar schema** — exact JSON structure, atomic write protocol | Sidecar = `{live_marking: [int,...], revision: int, updated_at: iso_ts}`; `omt_net_fire` writes both files in a `try/except` that rolls back both on failure | **High** — without this, net file and sidecar can drift; "file is authority" claim collapses | **Resolved by IDEA-002 §7**: sidecar file `.meta/.omt/net_state.json` chosen over v2 format extension to avoid format ripples; atomic write protocol documented |
| 2 | **Net-vs-ledger drift check** — when to run, how to surface, what to do on conflict | Drift check runs at every `omt_complete` exit; if net allows fire but ledger blocks → LOG drift, do NOT fire; if ledger allows but net blocks → net authority wins (blocks), LOG drift | **High** — two sources of truth will diverge without explicit reconciliation | **Resolved by IDEA-002 §8**: drift check modeled on `omt_q{op:drift}`; reconciliation rule: net guides but ledger/gates own approval authority |
| 3 | **Subnet prefix scheme** — `f{N}_` vs `feature_{N}_` vs UUID; collision guarantee | `f{N}_` prefix where N = roadmap feature number (from PROJECT.md); guaranteed unique because roadmap numbers are auto-assigned at scaffold time | **Medium** — wrong prefix causes node name collisions in the flat net | IDEA-002 §1.1 uses `f{N}_` prefix scheme; guaranteed unique because roadmap numbers are auto-assigned at scaffold time (same rationale) |
| 4 | **Conformance regression trigger** — on every splice? on commit? CI only? | Run 9 conformance vectors after **every** `omt_net_splice`; CI block on failure; dev-mode optional fast-check (first 3 vectors) | **Medium** — if vectors drift, engine semantics are unknown; highest-confidence guardrail | IDEA-002 §3.4: same discipline — 9 vectors after each structural mutation; CI block on failure; studio D8 proven pattern |
| 5 | **Dashboard scope** — static build only? live WebSocket updates? | Static build only (`npm run build` → `dist/` + preview smoke); dashboard reads `.meta/.omt/net_state.sidecar.json` at build time; no runtime viz stack | **Low** — already proven by studio reuse (feature_036); static is lower risk | IDEA-002 §5.3: static build pipeline proven by feature_034-036; no dev server required |

---

## 5. Tool Surface: Single `omt_net` Tool with Ops (F5 Mitigation)

Following the `omt_q.ts` precedent (one registered tool, internal sub-tools dispatched via `op`):

```
.opencode/plugins/omt_net.ts — one registration:
- op: "probe"        → returns current marking + enabled transitions + deadlocks + invariants
- op: "fire"         → validates enablement via analyzer, applies marking change, writes net file + sidecar, logs reasoning
- op: "splice"       → structural mutation (add/disable/remove places/transitions/arcs) + conformance regression + ledger record
- op: "invariant"    → re-run full net invariants; surface drift if net/ledger mismatch
- op: "synthesize"   → goal→net template composition + splice (bounded, deterministic only)
```

**Why one tool (not 5):** Avoids F5 harness surface churn (5× CMD records × drift-pinned budgets × nav-indexed gotchas × quick_ref/workflow docs × e2e receipt refresh). One tool = one set of budgets, one nav index entry, one receipt cycle.

*Tool registration pending: follows `omt_q.ts` pattern. Will be registered in `.meta/META_HARNESS.omt` TOOL section + `.opencode/plugins/` after feature_039 is scaffolded.*

---

## 5a. Prerequisites for Scaffolding feature_039

Before scaffolding `feature_039.adaptive_net_engine` (minor_feature), the following must be in place:

1. **`.meta/.omt/` directory exists** — already present with ledger, thoughts, nav.index
2. **Sidecar schema documented** — `net_state.sidecar.json` format `{live_marking, revision, updated_at}` (resolved per IDEA-002 §7)
3. **Conformance vectors verified** — 9 golden vectors from `shared/petri-net/conformance/analysis-v1/` are byte-identical against the harness engine clone (per D2)
4. **`omt_net` tool not yet registered** — will follow `omt_q.ts` pattern; registration occurs when feature is scaffolded via `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`
5. **Project D1 confirmed** — "meta harness only, not agentx" locked; no `src/agentx/` edits will be made under this project

## 6. Roadmap Re-Scoped Implications

| Feature | Slots | Status vs IDEA-002 | Reason |
|---|---|---|---|
| 1 `.adaptive_net_engine` | **feature_039** | **Proceed as planned** (minor_feature) | Core engine + net file + sidecar + probe/fire/invariant ops + 9-vector parity |
| 2 `.net_composition_supervisor` | **feature_040** | **Proceed as planned** (minor_feature) | Supervisor net + boundary ports + incremental cross-analysis |
| 3 `.resource_places_concurrency` | **feature_041** | **Proceed as planned** (minor_feature) | Complement places + deadlock detection + conflict surfacing |
| 4 `.goal_net_synthesis` | **feature_042** | **Proceed as minor_feature (optional)** | Already bounded to deterministic templates (IDEA-002 §4); no free-form synthesis |
| 5 `.meta_net_dashboard` | **feature_043** | **Proceed as major_feature (optional)** | Studio reuse only; reads harness net JSON store + deadlock highlight overlay |

**Core = features 1-3** (ship as minor_features). Features 4-5 are optional phase-2 builds the observability UI on proven core.

*Roadmap alignment: slots 039-043 verified free in project draft v0.2 (D1: meta harness only). Feature 039 will be scaffolded first via `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`.*

---

## 7. Honest Limits (Keep, Don't Forget)

- **Still not a scheduler.** `agent_attention = 1` (single-threaded agent) means the net fires transitions the *agent* then executes serially. The net's real control value is **(a) blocking invalid fires via the analyzer**, and **(b) rigorous audit**. Frame it as a **gate-augmenting blocker**, not an executor.

- **Two sources of truth** (net file + ledger/gates) — must be reconciled, not hand-waved. Drift check at `omt_complete` exit is the reconciliation mechanism.

- **Pure software-dependency risk is low** but the format-touch (sidecar schema, conformance regression) is the one place a proven asset could regress. Mitigation: every conformance vector change requires a new audit tag in the ledger.

- **The net model mirrors actual project/feature state** (WORK.md + `.projects/` + feature dirs) and detects structural conflicts/deadlocks mechanically — this is the deliverable. It does **not** execute features in parallel; it models concurrency for visibility and conflict detection.

---

## 8. References (Source-Verified)

- `IDEA-001` — file-backed net control, format decision, live-marking open items 1-4
- `IDEA-002` — compositional net-of-nets architecture, resource places, structural transactions, goal→net templates, dashboard
- `shared/petri-net/FORMAT.md` + `petri-net-json-v1.schema.json` — the v1 format (live-marking gap documented here)
- `src/agentx/model/petri_net/model.py` + `analysis.py` — executable spec (D2 parity target)
- `tools/petri-net-studio/src/engine/` — proven parity port + conformance vectors (9 golden vectors)
- `.opencode/plugins/omt_q.ts` (817 lines) — single-tool-with-ops pattern (template for `omt_net`)
- `scripts/omt/tdd/cli.py` — two-hats gate + phase FSM (the workflow the net layer sits atop)
- `META_HARNESS.omt` — single source of truth for phase FSM, gates, budgets, nav/think enforcement
- feature_034-036 `npm run build` → `dist/` + preview smoke — static build pipeline for dashboard

---

## 9. Decision Log (This Idea)

- **IDEA-003.D1 — Petri net as additive layer, not workflow driver:** The net models/guides/observes; the phase FSM + ledger own approval authority. D3 compliance. *Project D1: net work confined to `scripts/omt/` + `.meta/`, no `src/agentx/` edits.*
- **IDEA-003.D2 — Two-source-of-truth pattern:** Net file + sidecar inform but do not override g.phase/g.tests/g.receipt. Drift check at omt_complete exit. *Project D1 confinement confirmed.*
- **IDEA-003.D3 — Single `omt_net` tool with ops:** Follows `omt_q` precedent; avoids F5 harness surface churn (5× budgets, nav gotchas, receipt cycles). *Tool registration to follow omt_q.ts pattern upon feature scaffolding.*
- **IDEA-003.D4 — Sidecar for live marking:** No format change to proven v1; sidecar is inherently ephemeral; written atomically with net file. *Resolved per IDEA-002 §7; sidecar chosen over v2 format extension.*
- **IDEA-003.D5 — Conformance regression on every splice:** 9 vectors after each structural mutation; CI block on failure; dev-mode fast-check available. *IDEA-002 §3.4 discipline; 9 golden vectors from studio parity port.*
- **IDEA-003.D6 — Roadmap core = features 1-3:** 1-3 ship as minor_features (feature_039, feature_040, feature_041); 4-5 optional phase-2 builds the observability UI on proven core. *Maps to project slots 039-043 verified free.*
- **IDEA-003.D7 — Net blocks but does not execute:** `agent_attention = 1`; net can block invalid fires; agent executes serially. Frame as gate-augmenting blocker.
- **IDEA-003.D8 — Project D1 compliance:** All net work confined to `scripts/omt/` + `.meta/`; no `src/agentx/` edits permitted. *User directive 2026-08-30; project draft v0.2 locked.*

---

*End of IDEA-003*