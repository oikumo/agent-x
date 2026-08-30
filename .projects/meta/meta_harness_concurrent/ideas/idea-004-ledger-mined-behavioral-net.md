# IDEA-004 — Ledger-Mined Behavioral Net (process mining: the net learns the agent's ACTUAL process from the ledger)

> Created 2026-08-30 · the inverse-direction idea. IDEA-001/002/003 all build the net **downward** (goals → templates → net; architecture → supervisor + subnets). This idea builds it **upward**: the net is *mined from the agent's own recorded behavior* — the ledger is already an event log, so the harness can discover its own process empirically instead of only hand-modeling it.
> **v2 (2026-08-30, iter 6)** — refinement pass aligned to the locked architecture (PROJECT.md v0.4 D1–D15, IDEA-002 v4, IDEA-003) + source-verified against the **real ledger corpus** (`.meta/.omt/ledger*.jsonl`, 3 files, 1,650 records; analyzed this session):
> - **Ledger = a rotated STORE, not one file.** v1 said "read `ledger.jsonl`" — reality: hot `ledger.jsonl` (88 rows) + `ledger-202608.jsonl` (934) + `ledger-202607.jsonl` (628). EXTRACT reads the store glob; mining window ≠ gate truth window (`@state ledger` truth = "hot + latest archive"; mining = full archive span). New §3.
> - **Correlation keys are sparse — attribution is a first-class design decision, not a footnote.** 62% of records lack `feature`; **skips carry `feature` on 0 of 229 records**. Per-feature traces must be *enriched* by session-context attribution (open item #1 → RESOLVED in design, §8).
> - **`mine` positioned on the v4 canonical ops taxonomy** (IDEA-002 v4 §5.0: `probe|fire|splice|sync|synthesize|invariant`, closed at feature_039): `mine` is the **single gated extension point** of that enum at feature_044 — one enum value + one `miner.py` module + one switch case, still ONE `omt_net` registration (F5 preserved). §5, IDEA-004.D7.
> - **Real-corpus feasibility numbers added** (§3): 13 features with full 5-phase flows, median trace length 3, duplicate `complete` records confirmed (feature_022 ×16), phase-revisit loops confirmed, placeholder `ts` seeds present in the corpus.
> - Open items #1–#6 → **all RESOLVED (design, v2)**; new evidence-backed item #7 (rotation + seed-ts tolerance) added and resolved. Decision log extended D7–D12.
> **Status:** candidate idea — completely new direction, builds on the core roadmap (feature_039–041), NOT part of core. Proposes an optional phase-2 slot (feature_044) *after* the core proves valuable (same re-scope rule as IDEA-003 §6 / IDEA-002 §10: re-scope, not cancellation).
> **Project context:** meta_harness_concurrent (D1: meta-harness-only, no `src/agentx/`; D2: no runtime import; D3: additive over the gate contract; D4: agent owns net mutations, user owns goals).

---

## The idea, in one line

**A `mine` op (process mining) that reads the existing ledger STORE (`.meta/.omt/ledger*.jsonl` — hot + rotated archives) as an event log, discovers the harness's *actual* behavioral Petri net (places = states, transitions = ledger `kind`+`phase` events, arcs = observed ordering), and surfaces it as a second net — the `META_NET.mined.petri.json` "observed net" — so the agent can compare *what it actually does* (mined) against *what it intended to do* (goal-synthesized, IDEA-002 §4), detect behavioral drift, and answer "what usually happens next" / "what-if I had done X before Y" using the existing analyzer.**

---

## Why this is the right NEW direction (what it fixes)

Every prior idea shares one unexamined assumption: **the net is authored downward.** IDEA-002 §4 synthesizes subnets from *goals* (declared intent); IDEA-001/003 treat the net as a file + sidecar mirror of the *phase FSM*. In all three, the structure comes from what the process *should* be.

That leaves a blind spot: **the harness already records what it *actually* does — the ledger — but nothing mines it.** The ledger is a timestamped, case-correlated event log (`ts`, `kind` ∈ {phase, complete, skip, q, think_consult, tdd, tdd_testlist, project, project_link}, `feature`, `session`, `phase`), which is precisely the input format the field of **process mining** was invented for. Fixes three real gaps:

1. **The hand-modeled net can be wrong and nobody notices.** The goal-synthesized / sync-derived net (IDEA-002 §4, D12) encodes intent, not behavior. If the agent actually follows a different path — an undocumented shortcut, a skip-heavy feature, a `q`-probe storm between phases — the intended net silently diverges from reality. IDEA-004 makes that divergence *mechanically visible*: behavioral drift between mined and intended nets.

2. **Empirical invariants are discoverable, not only designable.** IDEA-002's resource invariants (`agent_attention=1`, `src_edit_capacity`, …) are hand-written by modeling. A mined net exposes *observed* token-conservation laws ("every feature_ready is followed by exactly one goal_satisfied", "no feature fires start_feature twice"), which can confirm or contradict the hand-written ones — a second, evidence-based invariant source (validated the same way: `analyzer.place_invariants()`).

3. **One-directional modeling wastes the ledger's predictive power.** After mining, replaying the latest event on the observed net gives *empirically-grounded* next-event candidates with observed frequencies — the net becomes a lightweight predictor, and the existing `reachable_markings`/`deadlocks` analysis becomes a *counterfactual simulator* for hindsight ("had the tests_capacity claim fired before the src_edit claim, would feature_040 have deadlocked?").

**Positioning:** IDEA-004 is the *upward complement* to IDEA-002 §4's downward synthesis. Synthesis says "here is the net implied by your goals"; mining says "here is the net implied by your actions." Their difference is the harness's process-fidelity gap, and that gap is the deliverable.

---

## The event log today (verified this session — the empirical base)

The mining input is not a hypothesis; it was measured. Corpus = `.meta/.omt/ledger*.jsonl` (3 files, 1,650 records, 2026-07 → 2026-08-30):

| Fact | Value | Consequence for the miner |
|---|---|---|
| Files | `ledger.jsonl` (88), `ledger-202608.jsonl` (934), `ledger-202607.jsonl` (628) — `mode=rotate cap=65536` | EXTRACT must glob the store, not one path |
| Kinds (9) | think_consult 630, phase 278, skip 229, tdd 164, q 144, complete 147, tdd_testlist 29, project 12, project_link 17 | Activity vocabulary confirmed; richer than the XREF_LEDGER line (`phase\|skip\|complete\|tdd\|tdd_testlist\|think_consult` — omits q/project/project_link, which DO exist in the real ledger) |
| `feature` key | present on **619/1,650 (37.5%)** | Per-feature traces cover only ⅓ of records — case enrichment is mandatory |
| `session` key | present on 1,088/1,650 (66%) | Session is the denser correlation key — the attribution vehicle |
| **skip × feature** | **0 of 229** (100% missing) | **Without attribution, `skip` never appears in a feature trace** — the observed net would literally omit the harness's most distinctive deviation activity |
| Feature phase-flow traces | 43 features with ≥1 `phase` record; **13 with all five phases** (Analysis…Done); median trace length 3, max 26 | Sparse-but-real: v1 α-variant has enough traces to mine a small phase-flow net; min_support defaults must be absolute, not %-only |
| Duplicate `complete` | confirmed (feature_022 ×16, meta_harness_refactor ×13, feature_036 ×6) | The v1 "duplicates under-expressed" caveat is a *measured* phenomenon, not hypothetical |
| Phase revisits | feature_022 phase counts: Programming 8, Analysis 5, Design 5, Testing 4, Done 4 — real cycles, not a linear FSM walk | The mined net will (correctly) express revisit loops; the intended net must too, or drift is instantly non-zero |
| `q` ops | state 139, drift 4, plan 1 | Probe-friction view is dominated by `q[state]` — friction = repeated state-probing, worth one activity, not 139 |
| `ts` quality | placeholders present (`2024-01-01T00:00:00.000000` seeds) | Miner must skip/flag seed & malformed ts, count them in the report envelope |
| Gate truth window | `@state ledger`: "ledger.jsonl hot + latest ledger-YYYYMM.jsonl archive" (`@var.unlock_window_ms` 8h) | **Mining window ≠ gate truth window.** Gates reconcile against hot+latest; mining legitimately scans the full archive span. The mined draft must record its ledger range (draft manifest, §5) |

Takeaway: the ledger **is** an event log, but a young and correlation-sparse one. That does not weaken the idea — it *shapes* it: attribution (open item #1/#2) is the miner's most important design decision, and the honest v1 verdict is "small but real observed net + a drift mechanism that grows with the corpus."

---

## The mining workflow (intent)

```
EXTRACT   read ledger*.jsonl (ts-ordered across files) → per-case traces
              case = feature (primary) — see §8 #1 for attribution rules
              activity = kind + phase normalization, e.g. "phase[Programming]", "skip", "q[state]"
OBSERVE   omt_net{op:mine, window: corpus|last N features, min_support, case, activity_view}
              → α-miner on traces → observed net: places = discovered states,
                transitions = activities, arcs = causality/parallelism/choice relations
COMPARE   behavioral drift = symmetric diff (intended net vs mined net)
              → report divergences: mined-only paths, skipped-intended paths, frequency/support
PREDICT   replay current live marking on mined net → next-event candidates + observed %
EXPLAIN   omt_net{op:probe, net:"mined", explain:true} → prose rendering
              ("88% of features: design → programming → testing → done; 12% skip")
APPLY     materialize/minimize = proposal through the EXISTING splice path (D4, never silent)
```

The mined net is *always* a proposal artifact first. Applying it (or a repair to the intended net) goes through `omt_net_splice` with reasoning + conformance regression — never silent, never auto-applied (D3/D4).

Two pre-bootstrap notes (IDEA-002 v4 §5.1 applies): `mine` itself works **before** the intended net exists — EXTRACT/OBSERVE are ledger-only, and COMPARE reports `intended net not bootstrapped` as a finding (the absence of a declared-intent net is itself a first drift record). Once `sync`/`synthesize` have materialized the intended net, COMPARE activates fully.

---

## Feasibility (grounded in the actual repo + measured corpus, verified this session)

| Component | Evidence | Assessment |
|---|---|---|
| Event log exists | `.meta/.omt/ledger*.jsonl` — measured 1,650 records / 9 kinds / 43 feature-traces / 13 full 5-phase flows (§3). Case id (`feature` via attribution), activity (`kind`+`phase`), timestamp (`ts`) all present. | **High — this IS an event log**, young and sparse; attribution is the enabling design decision, not a blocker |
| Mining algorithm | α-algorithm (van der Aalst) is a textbook, stdlib-only algorithm (~200–300 LOC): directly-follows relation → causality/parallelism/choice → places = maximal sets, transitions = activities. Simplified v1 variant tailored to flat `kind` activities. | **High — no new dependency; pure stdlib Python in `scripts/omt/net/`** (D1/D2 intact) |
| Output consumption | Mined net is built with the SAME `PetriNet.add_place/add_transition/add_input/add_output` API (verified present in `model.py`) and serialized via the SAME `io.py` → `petri-net-json` v1 (`META_NET.mined.petri.json` + mined sidecar + draft manifest; three-file draft transaction, IDEA-002 §1.4/§7.2 style) | **High — pure reuse; mined net is just another net** |
| Analysis on mined net | `PetriNetAnalyzer.reachable_markings/deadlocks/place_invariants` (158 tests) consume the mined net unchanged — prediction + counterfactual + empirical invariants are free | **High — no analysis extension** |
| Conformance | Mined nets are library-conformant by construction (same io, same vectors); engine conformance (9 vectors) applies to the mined net's *serialization* unchanged; the miner *semantics* get their own 10th golden case (see §8 #6) | **High — adds vectors, doesn't touch the existing 9** |

**Verdict: feasible, mostly reuse + one well-understood algorithm + one measured-design decision (attribution).** The genuinely new work is `miner.py` (α-variant over enriched ledger traces) + the drift-comparison glue between intended and mined nets. Everything upstream (event log store) and downstream (net file, sidecar, overlay, analyzer, splice path) already exists in this project's core.

---

## The α-miner sketch (v1, harness-flavored)

For each enriched case trace `T = [a1, a2, …, an]`:

1. **Extract + attribute (see §8 #1)**: build traces from the ledger store; records without `feature` inherit their session's active feature (most recent feature-bearing `phase`/`complete`/`project_link` in the same session ≤ ts), flagged `attributed:true`. Records that still have no case are counted and skipped (surfaced in the report, never silent).
2. **Directly-follows**: `a > b` iff `b` appears immediately after `a` in some trace (attributed records count toward support, with their attributed flag).
3. **Relations**:
   - causality: `a → b` iff `a > b` and not `b > a`
   - parallelism: `a ∥ b` iff `a > b` and `b > a`
   - choice: `a # b` iff neither `a > b` nor `b > a`
4. **Places**: one place per maximal set `Y` of transitions that *share the same precursor set* (standard α `Y_W` construction over the causality relation).
5. **Arcs**: input/output arcs from the relation pairs; start/end places from trace-initial/final activities.
6. **Prune**: drop low-frequency paths below a `min_support` threshold — v1 default is **absolute** `≥3` traces OR `≥10%` of case count (with the measured corpus of 43 traces, the absolute floor dominates and both should be tunable); everything pruned stays in the report's `pruned` list — a *surfaced* maintenance detail, never silently dropped (§8 #3).
7. **Serialize**: `PetriNet` + `io.py` → `META_NET.mined.petri.json`, `M0` = all-zero + observed start marking; plus `net_state.mined.sidecar.json` (observed mark + draft revision) + `mine.draft.manifest.json` (window/min_support/case/activity_view/ledger files+range/attribution flag/records used vs skipped — the re-mining reproducibility record, §8 #5).

Measured-α notes (the corpus already exhibits both):
- **Phase-revisit loops are real** (feature_022: Programming 8×) — the directly-follows relation will express `phase[Programming] ↔ phase[Testing]` style cycles correctly as causality+choice; the intended net should mirror them or drift is expected, not surprising.
- **Duplicate `complete` records are real** (feature_022 ×16) — the simplified variant under-expresses duplicates by design; acceptable for v1 and documented in the mined net's prose (this is exactly the "mined = observed, imperfections and all" limit, §7).

Known α weaknesses are directly mitigated:
- **Invisible transitions / short loops / noise** → v1 deliberately uses a simplified variant (no invisible-transition recovery, no loop-detection bells) and leans on `min_support` pruning; feature design can upgrade later.
- **Sparse logs** → `window` parameter (corpus | last N features) + explicit "insufficient evidence" envelope when a relation cannot be established (with the current corpus, a handful of relations will land here — that is honest output, not failure).

---

## New capabilities unlocked (the payoff)

### 1. Behavioral drift: a THIRD truth in the reconciliation triangle

Reality: **ledger + gates** (primary authority, D3). Models: **intended net** (goal-synthesized, IDEA-002 §4) and **observed net** (mined, this idea). Drift is now two-dimensional:

| Comparison | Meaning | Surfaced by |
|---|---|---|
| observed vs reality | net fidelity (existing net-vs-ledger drift, IDEA-002 §8) | `invariant` op (existing) |
| **observed vs intended** | process fidelity — what the agent does vs what it planned | **`mine` op (new)** |

A mined-only path (e.g. `phase[Programming] → q → phase[Programming]` repeated) signals a process friction the intended model doesn't express. An intended-only path that never appears in `window` signals a goal the agent isn't honouring. Both feed the drift log (`harness.net.drift.jsonl`, same envelope pattern as `omt_q{op:drift}`), and the mine report also carries the "intended net not bootstrapped yet" finding for pre-bootstrap runs (§4). Every mined arc carries support counts + attributed counts, so drift claims are auditable — never bare assertions.

### 2. Empirical invariants

Run `place_invariants()` on the mined net; compare the discovered token-conservation laws against the hand-written resource invariants (IDEA-002 §2.1 catalog). A mined law the intended model lacks = a resource constraint the agent *actually* respects (candidate to promote into the intended modeling). A hand-written law the mined net contradicts = candidate *design smell* — evidence-based challenge to the hand-model, surfaced as a proposal, never auto-applied (D4).

### 3. Probabilistic next-event prediction

Given the live marking on the mined net: enabled transitions + their observed frequency from the directly-follows histogram. The net answers "what usually happens next" with counts — e.g. after `phase[Design]`, 92% `phase[Programming]`, 8% `skip`. This is guidance, not control (F7, D3): it sharpens the agent's DECIDE step in the IDEA-003 control loop without ever overriding a gate.

### 4. Counterfactual reachability (hindsight)

The existing `reachable_markings(max_states=…)` on the *mined* net answers what-if questions after a real deadlock/conflict: "at the marking where feature_040 blocked on `tests_capacity`, was there a reachable alternative order that avoids the deadlock?" That's root-cause analysis with replayable evidence — the mined structure is *known to match observed behavior*, so the counterfactual is grounded, not hypothetical.

### 5. Self-correcting intended net (as proposal, not automation)

`mine` → diff → **repair proposal**: splice the mined structure into the intended net (or vice versa) — always through the normal `splice{mode}` path with reasoning + conformance regression + ledger audit (D4). The harness *offers* to align its model with its behavior; the agent (via gates) decides. Cooldown + support rules keep this from spamming (§8 #4).

---

## Tool surface (F5: one READ-ONLY op — surface stays flat)

Per the canonical ops taxonomy (IDEA-002 v4 §5.0 — `probe|fire|splice|sync|synthesize|invariant`, **closed** at feature_039 design), **`mine` is the single sanctioned extension point of that closed set at feature_044**: one new enum value, one `miner.py` module, one new switch case — still **one** `omt_net` registration (F5 preserved; the op set is *closed-then-extended* by explicit phase-2 decision, not silently grown). `mine` is a **read-only op** (computes the observed net + reports drift; materialization goes through the existing `splice` path — no new mutation mechanism):

| op | Class | Mutates | What it does |
|---|---|---|---|
| `mine` | read | **no** (draft artifacts only) | Extract ledger-store traces (attributed) → α-mine → observed net; report intended-vs-observed behavioral drift + empirical invariants + next-event predictions. Params: `window` (corpus | last N features), `min_support`, `case` (feature | session | project), `activity_view` (phase-flow | probe-friction). Writes *draft* `META_NET.mined.petri.json` + `net_state.mined.sidecar.json` + `mine.draft.manifest.json` so subsequent ops can replay on it (draft = a proposed artifact, NOT an applied net; git-ignored runtime state per D14) |
| `probe` | read | no | gains `net:"mined"` + `explain:true` → prose rendering of ANY net (intended, mined, composed): dominant paths with %, mined-only paths, invariant summary, pruned-behavior list (fires the prose-renderer used by `mine`) |

Draft artifacts (all runtime state, `.meta/.omt/*` git-ignored — D14):
```json
// .meta/.omt/mine.draft.manifest.json  (re-mining reproducibility record)
{
  "draft_revision": 3,
  "ledger_files": ["ledger-202607.jsonl", "ledger-202608.jsonl", "ledger.jsonl"],
  "ledger_range": ["2026-07-01", "2026-08-30"],
  "case": "feature", "attribution": true, "activity_view": "phase-flow",
  "window": {"mode": "corpus"}, "min_support": 3,
  "records_total": 1650, "records_used": 1198, "records_skipped": 452,
  "skipped_reasons": {"no_case_after_attribution": 320, "seed_ts": 132}
}
```

Applying a mined draft to the supervised world = existing `splice` (conformance regression already required — mined nets pass by construction, and the *9 existing vectors* now also guard the mined net's output shape; the miner's *semantics* are pinned separately by the 10th golden case, §8 #6).

**Why only one new op:** the mutation surface is untouched (F5; `splice` stays the single structural authority); `mine` is observability in exactly the same spirit as `probe`/`invariant`. Approved at feature_044 design time only — the op set is closed at feature_039 design (IDEA-002 v4 §5.0) and `mine` is explicitly a phase-2 extension candidate, not a core charter change.

---

## Roadmap position (phase-2, sibling to synthesis + dashboard)

| # | Feature | Type | Deliverable | Depends on |
|---|---|---|---|---|
| 4 | `feature_042.goal_net_synthesis` (existing IDEA-002) | minor_feature (optional) | Template composition + splice | 2 |
| 5 | `feature_043.meta_net_dashboard` (existing IDEA-002) | major_feature (optional) | Studio reuse dashboard | 1–3 |
| **6** | **`feature_044.mined_behavioral_net` (NEW)** | **minor_feature (optional)** | **`miner.py` (α-variant + attribution) + `mine` op (gated enum extension) + behavioral-drift report (intended vs observed) + empirical-invariant comparison + counterfactual replay + prose `explain`** | 2 (overlay/composition); **full COMPARE reach requires 4** (goal-synthesized intended net) |

**Not core. Not required for feature_039–041.** Same rule as IDEA-003 §6: phase-2 only if the core proves valuable — and specifically only if the observed-vs-intended question has real value by then. The *evidence base* (the ledger store) accumulates regardless, so nothing is wasted by deferring. Note the dependency subtlety: a v1 `mine` compares against the *synced/composed* intended net (available after feature_040); the comparison only reaches its sharpest form against the *goal-synthesized* intended net (feature_042).

---

## Open items (must resolve before ANY build — all RESOLVED in design by v2, validation points noted)

| # | Item | Status / v2 resolution | Validate at |
|---|---|---|---|
| 1 | **Case-id & trace extraction + attribution** — what is a "case"? Per-`feature` lifetime, per-`session`, per-`project`? **Measured reality:** only 37.5% of records carry `feature`; **skips carry it 0%**; 66% carry `session`. | **RESOLVED (design, v2)**: primary `case = feature` (mirrors the composed net's per-feature subnet partition, so mined-vs-intended comparison is structurally aligned); records without `feature` inherit their session's active feature (most recent feature-bearing `phase`/`complete`/`project_link` in the same session ≤ ts), flagged `attributed:true`; survivors with no case are counted + skipped + surfaced. Secondary views: `case = session` (dense, mixed-feature — friction signals) and `case = project` (cross-check via `project_link`). Must be decided before miner v1 | feature_044 design: replay attribution over the real corpus; verify the skipped tail is *explainable* |
| 2 | **Activity normalization** — raw `kind` (too coarse) vs `kind+phase` (`phase[Programming]`; good for feature-level flow) vs `kind+op` (`q[state]`; good for friction). | **RESOLVED (design, v2)**: two views shipped in v1 — "phase-flow net" (coarse: `phase[<phase>]` + `skip` + `complete`, after attribution) and "probe-friction net" (fine: `q[<op>]`, `think_consult`, for mined-only-path detection). Measured: `q` is 139× `state` — collapse `q[op]` to activity `q` + count (frequency = the signal), do not split into 139 activities | feature_044 design: confirm view granularity on real corpus; probe-friction only meaningful per-session |
| 3 | **Noise & support threshold** — which behaviors are "the process" vs one-off ad-hoc. | **RESOLVED (design, v2)**: v1 default `min_support` = **absolute ≥3 traces OR ≥10%** of case count (measured corpus → absolute floor dominates); pruned behaviors stay in the report's `pruned` list (surfaced, never silent); parameters tunable per `mine` call | feature_044 design: tune after first real mine on the full corpus |
| 4 | **Behavioral-drift rule** — when does a divergence trigger a splice-repair proposal? | **RESOLVED (design, v2)**: drift logged to `harness.net.drift.jsonl` (same envelope as §8/IDEA-003 — `{ts, feature, net_state, ledger_state, resolved}`); repair proposal only when ≥3 divergences, each at ≥ `min_support`, **and** a per-feature cooldown (no identical proposal until the intended net revision changes); bounded volume (cap per feature per revision) — no spam | feature_044 design: cooldown constants; never auto-fix (D4) |
| 5 | **Mined-net lifecycle** — draft vs persisted revisioned artifact. | **RESOLVED (design, v2)**: `META_NET.mined.petri.json` + `net_state.mined.sidecar.json` + `mine.draft.manifest.json` are **draft runtime artifacts** (git-ignored per D14), recomputed per `mine` call; draft revision = ledger-derived (count of `kind:"net_mine"` records); a *promoted* mined net becomes a normal revisioned net **via `splice`** — nothing else can promote it; the draft manifest makes every re-mining reproducible | feature_044 design: audit chain mine→splice promotion must be unambiguous in the ledger |
| 6 | **Miner conformance guard** — two DISTINCT pins. | **RESOLVED (design, v2)**: (a) the mined net is a plain `petri-net-json` v1 file → the **9 existing engine vectors** guard its serialization path unchanged; (b) miner *semantics* get a **10th golden case**: synthetic trace set → known mined net, byte-pinned, run in the miner unit suite + CI on every `miner.py` change (mirrors F6/D8 discipline; a miner change that silently changes mined results is a pinned regression, not a silent improvement) | feature_044 design: generate the golden case from a hand-built trace set covering causality/parallelism/choice + attribution |
| 7 | **Ledger-store rotation + data quality** — monthly rotated files, seed/placeholder `ts`. | **RESOLVED (design, v2)** (new this pass, from §3 measurement): EXTRACT globs `.meta/.omt/ledger*.jsonl` (hot + archives; gate truth window ≠ mining window — record the span in the manifest); records with seed/malformed `ts` are skipped with a surfaced count; stable sort by `ts` then file order | feature_044 design: rotation-triggered draft-revision bump rule (same spirit as IDEA-002 D14) |

---

## Honest limits (keep, don't forget)

- **Mined = observed, not desired.** If the agent took shortcuts, the mined net models the shortcuts faithfully. That's the point (fidelity measurement), but never mistake the observed net for a normative model — only the intended net (goal-synthesized, IDEA-002 §4) encodes declared intent.
- **Attribution is a heuristic.** Session-context inheritance can mis-attribute a record when a session genuinely straddles features. The `attributed` flag keeps it auditable; the mined report counts attribute-driven support separately, and the "insufficient evidence" envelope flags relations that depend heavily on attribution.
- **The corpus is young and sparse — the mined net starts small.** Measured: 13 full 5-phase feature flows today; median per-feature trace 3 records. The v1 observed net is a *small but real* model; its value (drift + prediction + empirical invariants) compounds as the ledger grows. Do not over-interpret early mined structure.
- **The ledger is the evidence window.** Re-mining after ledger-schema evolution (new `kind`s, rotation) must bump the mined draft revision and re-run the golden miner case (§8 #6/#7). Old mined drafts are historical, not stale — same reasoning as IDEA-002 D14 runtime-state durability.
- **Not a scheduler, still.** Prediction from the mined net is probabilistic *guidance* (F7/D3 — `agent_attention=1`). No new automation; every application is a splice proposal the agent approves.
- **α-miner v1 is deliberately naive.** No invisible-transition recovery, no loop/duplicate-activity sophistication (duplicate `complete` records for feature_022 ×16 are a *measured* real phenomenon — the simplified variant may under-express them; that's acceptable for v1 and documented in the mined net's prose).
- **Behavioral drift is a signal, not a verdict.** A mined-only path may be a legitimate process improvement the intended net hasn't caught up to. The report frames divergence neutrally with support counts; the agent decides (D4).

---

## References

- `IDEA-001` — file-backed net control (the file/sidecar authority `mine`'s output must conform to)
- `IDEA-002` (v4) — compositional net-of-nets; §4 goal→net synthesis (the DOWNWARD direction `mine` complements); §5.0 canonical ops taxonomy (the closed enum whose single gated extension `mine` is); §5.1 bootstrap ordering (pre-bootstrap `mine` behavior); §7 sidecar + §1.4 overlay three-file transaction (draft-transaction pattern); §8 net-vs-ledger drift (the existing observed-vs-reality check `mine` extends with observed-vs-intended)
- `IDEA-003` — additive observability layer framing (D1/D2/D3); the DECIDE step `mine`'s prediction sharpens
- `.meta/.omt/ledger*.jsonl` — **measured** event-log store this session: `ledger.jsonl` (88) + `ledger-202608.jsonl` (934) + `ledger-202607.jsonl` (628) = 1,650 records, 9 kinds, 43 feature-traces, 13 full 5-phase flows, 37.5% carry `feature`, skips 0% → attribution required
- `.meta/META_HARNESS.omt` — `@state ledger` line 149 (`truth="ledger.jsonl hot + latest ledger-YYYYMM.jsonl archive"`, `mode=rotate` — gate window ≠ mining window) + XREF_LEDGER line 289 (schema; under-specifies real kinds: omits q/project/project_link, which exist in the corpus)
- `src/agentx/model/petri_net/model.py` — `PetriNet.add_place/add_transition/add_input/add_output` API the miner outputs to (D2 parity target, no runtime import)
- `src/agentx/model/petri_net/analysis.py` — `PetriNetAnalyzer.reachable_markings/deadlocks/place_invariants` reused unchanged for prediction/counterfactual/empirical invariants
- `shared/petri-net/FORMAT.md` + conformance vectors — mined nets serialize via the same `io.py`/`petri-net-json` v1 path (9 existing vectors guard serialization + §8 #6's 10th golden case guards miner semantics)
- `.opencode/plugins/omt_q.ts` (817 lines) — single-tool-with-ops + drift-envelope pattern for the `mine` op surface
- **Process mining (external literature):** α-algorithm — van der Aalst, *Process Mining: Data Science in Action* (2016) — the theoretical basis for the v1 α-variant miner (`miner.py`)

---

## Decision Log (this idea)

- **IDEA-004.D1 — Mining is the upward direction, synthesis is the downward.** IDEA-002 §4 = goals → net (declared intent); IDEA-004 = ledger → net (observed behavior). Their diff = process-fidelity gap = the deliverable. Complement, not replacement.
- **IDEA-004.D2 — The ledger STORE IS the event log (v2).** Measured: 3 files / 1,650 records / 9 kinds / 43 feature-traces — no new instrumentation, no harness-surface change to collect data. Mining reads the store glob, not a single file.
- **IDEA-004.D3 — `mine` is read-only; application is `splice`.** One gated enum extension (v2: positioned on the IDEA-002 v4 §5.0 closed op set); mined drafts materialize via the existing structural-transaction path with reasoning + conformance regression (D4, never silent).
- **IDEA-004.D4 — Observed ≠ desired.** The mined net models behavior neutrally; it is never a normative model and never overrides gates (D3/F7).
- **IDEA-004.D5 — Phase-2, not core.** `feature_044.mined_behavioral_net` ships only if core (feature_039–041) proves valuable; evidence accumulates in the ledger regardless.
- **IDEA-004.D6 — α-variant v1 with support pruning.** No invisible-transition/loop sophistication; `min_support` pruning surfaces pruned behavior; a 10th golden miner case pins miner semantics (§8 #6).
- **IDEA-004.D7 — `mine` = the single gated extension point of the closed op enum (v2).** One enum value + one `miner.py` module + one switch case at feature_044; still ONE `omt_net` registration (F5); the closed-at-feature_039 discipline is preserved by *explicit phase-2 extension*, not silent growth (IDEA-002 v4 §5.0).
- **IDEA-004.D8 — Case = feature + session-context attribution (v2).** Primary case mirrors the composed net's per-feature subnet partition; feature-less records inherit the session's active feature with an `attributed` flag; unattributable records are counted/skipped/surfaced. Motivated by measured 62% feature-less corpus + 0% skip correlation (§3).
- **IDEA-004.D9 — Mined drafts are runtime state + reproducible (v2).** `META_NET.mined.petri.json` + `net_state.mined.sidecar.json` + `mine.draft.manifest.json`, git-ignored (D14); recomputed per `mine`; promotion ONLY via `splice`; manifest records window/support/case/view/ledger-range for byte-reproducible re-mining (§5).
- **IDEA-004.D10 — Two activity views in v1 (v2).** "phase-flow" (coarse: `phase[<phase>]`/`skip`/`complete`) + "probe-friction" (fine: `q`/`think_consult`, per-session); measured `q` dominance (139× `state`) → collapse op into frequency, not 139 activities (§8 #2).
- **IDEA-004.D11 — Two conformance pins, distinct (v2).** Engine vectors (9) guard the mined net's serialization; a new golden miner case (10th, synthetic) pins miner semantics — run on `miner.py` change, not per-splice (§8 #6).
- **IDEA-004.D12 — Drift-repair rule with support + cooldown (v2).** Proposals only for ≥3 divergences at ≥ `min_support`, per-feature cooldown until intended-net revision changes; bounded `harness.net.drift.jsonl` volume; never auto-fix (D4).

---

*End of IDEA-004 (v2)*