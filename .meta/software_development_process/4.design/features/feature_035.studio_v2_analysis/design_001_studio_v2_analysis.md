# Design 001 — feature_035.studio_v2_analysis: v2 implementation blueprint

> Date: 2026-08-26 · Phase: Design · Sources: PROJECT.md scope LOCKED v1.1 (roadmap #4, D1–D10; iter-7 D8 re-lock) + analysis_001 (port matrix, findings B1–B12) + `src/agentx/model/petri_net/analysis.py` (executable spec) + `tests/model/petri_net/test_analysis.py` (38 behaviors) + `tools/petri-net-studio/src/engine/{model,errors}.ts` (feature_034 port) + `shared/petri-net/FORMAT.md` (LOCKED v1) + `shared/META.md`.
> Rule: Programming copies this doc; anything ambiguous here is resolved HERE, not in code.

---

## 1. Deliverable & definition of done

`tools/petri-net-studio/` v2 — TS analysis engine port + no-overclaim analysis dashboard (D10) + conformance-vector generator (D8 re-lock). Done when:

1. `src/engine/fraction.ts` + `src/engine/analysis.ts` port the analysis layer with exact parity (B2/B3);
2. Vitest green: fraction behaviors + 38 analysis behaviors (1:1 port of `test_analysis.py`) + conformance-vector suite;
3. `scripts/generate-vectors.py` (uv run) emits `shared/petri-net/conformance/analysis-v1/*.json` — canonical, deterministic `{net, expected}` docs the TS suite reads via fs (B8/B9);
4. Dashboard renders every verdict with ✅/❌/❓ + `complete` + `reason` + `max_states` dial (D10); `npm run build` green;
5. Independence lint still passes (no new cross-boundary `src/` imports); agentx pytest suite untouched/green (zero `src/` edits in this feature).

## 2. B-findings dispositions (analysis_001 → design PINs)

| # | PIN |
|---|---|
| B1 | `markingKey(m) = m.join(",")` exported from analysis.ts (markings are non-negative ints ⇒ unambiguous). All visited/predecessors/edges maps keyed by it. Results re-materialize arrays from keys in deterministic order. |
| B2 | Hand-rolled `fraction.ts` (§4): `Fraction(num, den)` normalized den>0 + gcd-divided, mirroring `fractions.Fraction`; `gcd`/`lcm` helpers mirror `math.gcd`. `nullspace` copies `analysis.py` line-for-line (Fraction Gauss–Jordan to FULL RREF). `_coprimeIntVector` mirrors `_coprime_int_vector` (LCM-scale → gcd-content divide → negate if first nonzero negative). NO floats in the algebra path. |
| B3 | `_explore` port copies the Python loop 1:1 (edge-recording + no-enqueue + `complete=false` + finish-current-state-edges + break). Truncated-graph test pins the `(1,0)`→`t1`→`(0,1)` edge. |
| B4 | `exploredStates` = distinct visited markings incl. initial (`visited.size`). `transitionLiveness`/`isLive` report `graph.states.length`. Empty net `isLive` → `{value:true, complete:true, exploredStates:1}`. |
| B5 | Result interfaces (§5) carry EXACT Python fields (F3 no extras): `value: boolean\|null`, `complete: boolean`, `exploredStates: number`, `reason?: string\|null`. Deep-equality tests compare field-by-field / toSorted arrays. |
| B6 | All iteration orders deterministic: edges in `enabledTransitionsAt` order (= code-point-sorted transitionOrder); SCC start nodes sorted; reverse-liveness sorted; deadlocks sorted; marking arrays sorted lexicographically (`compareMarkings`). |
| B7 | SCC skips edge targets outside `graph.states` (truncation-only). Recursive Tarjan (depth fine for v1 nets). |
| B8 | Generator = `tools/petri-net-studio/scripts/generate-vectors.py` (uv run; dev-time; never bundled; independence lint scans `src/` .ts(x) only). Vectors = `shared/petri-net/conformance/analysis-v1/<id>.json` (dir reserved by `shared/META.md` DIR_PETRI_NET; D5-locked contract data — NOT a schema/FORMAT/examples edit). |
| B9 | Vector serialization §7: no JSON objects keyed by markings/place-names (A2 integer-like-key reorder hazard) — use sorted ARRAYS of pairs/triples everywhere; reason strings verbatim; net = FORMAT §8 canonical doc (schema-valid; TS `documentFromJson` builds it). |
| B10 | `maxStates: number \| null` (null = unlimited, Python `None`). Dashboard dial = number input 1..N + "unlimited" toggle; **default 1000** (visible, never hidden — D10); every verdict row: badge (✅/❌/❓) + `complete` + `reason` verbatim; truncation renders unknown, never overclaims. |
| B11 | TDD = manual red→green under Vitest (A11 precedent). Declared in Programming scope; evidence pasted into the test report. |
| B12 | Analysis is DERIVED state: memoized (`useMemo` keyed on net identity + `maxStates`) in the dashboard component from `toNet(doc)`; `maxStates` + `analysisVisible` are store UI state (§8), never written into the document/format. |

## 3. Repository changes (all new/edited under `tools/petri-net-studio/` + shared conformance dir; nothing existing agentx/shared-contract touched)

```
tools/petri-net-studio/
├── scripts/
│   ├── check-independence.mjs        (existing, UNCHANGED — no new src/ cross-boundary imports)
│   └── generate-vectors.py           (NEW §6 — dev-time Python; runs via `uv run`; not bundled)
├── src/engine/
│   ├── fraction.ts                   (NEW §4 — pure TS, no imports)
│   ├── analysis.ts                   (NEW §5 — imports model.ts only)
│   ├── model.ts                      (existing, UNCHANGED)
│   └── errors.ts                     (existing, UNCHANGED)
├── src/state/store.ts                (EDIT §8 — add maxStates/analysisVisible/setMaxStates/toggleAnalysis; additive)
├── src/ui/
│   ├── App.tsx                       (EDIT — toolbar Analyze toggle + render AnalysisPanel)
│   └── AnalysisPanel.tsx             (NEW §9 — dashboard)
└── tests/
    ├── engine/fraction.test.ts       (NEW §10.1)
    ├── engine/analysis.test.ts       (NEW §10.2 — 38 behaviors)
    ├── engine/conformance.test.ts    (NEW §10.3 — reads vectors via fs)
    └── state/store.test.ts           (EDIT — additive cases for maxStates/analysisVisible)
shared/petri-net/conformance/analysis-v1/
    ├── two_way_cycle.json            (NEW §6/§7)
    ├── unbounded_net.json
    ├── deadlock_net.json
    ├── token_drain_net.json
    ├── two_deadlocks_net.json
    ├── weighted_reaction.json
    ├── producer_consumer.json
    └── hello.json
```

No `src/` (agentx) edits. No `shared/petri-net/{FORMAT.md,schema,examples}` edits (LOCKED). `shared/META.md` DIR_PETRI_NET already names `petri-net/conformance/` — the vectors dir is its realization (a one-line directory entry is allowed as project-home-style bookkeeping; not a contract rule change).

## 4. `fraction.ts` — full API pin (mirrors `fractions.Fraction` + `math.gcd`, B2)

```ts
export class Fraction {
  readonly num: number;   // signed
  readonly den: number;   // > 0 always (normalized)
  constructor(num: number, den?: number);   // den default 1; den=0 → throw ValueError-class? NO — den 0 never occurs in the port; still guard with RangeError("Fraction denominator cannot be zero")
  static zero(): Fraction;  // 0/1
  add(o: Fraction): Fraction;  sub(o: Fraction): Fraction;
  mul(o: Fraction): Fraction;  div(o: Fraction): Fraction;
  neg(): Fraction;  isZero(): boolean;  equals(o: Fraction): boolean;
  /** Exact int? (den===1). Used by tests/vector checks. */
  toInt(): number;
}
export function gcd(a: number, b: number): number;   // math.gcd semantics: gcd(0,0)=0; signs → abs; gcd(0,x)=abs(x)
export function lcm(a: number, b: number): number;   // a/gcd(a,b)*b (overflow-safe order)
```

Normalization: `num,den` from args; if `den<0` → `num=-num, den=-den`; `d=gcd(|num|,den)`; divide both; `den=0` guard. Multiplication/division/± straightforward exact integer arithmetic (JS numbers exact for |int|<2^53 — matrix entries are weights/tokens of v1 test nets, far below). `compareMarkings` + numeric-lexicographic marking sort helpers also live here? No — B6 marking ordering is analysis-layer; keep `compareMarkings` in analysis.ts.

## 5. `analysis.ts` — API pin (semantics = `analysis.py` exactly)

```ts
import { PetriNet, Marking, compareCodePoints } from "./model.js";
import { Fraction, gcd } from "./fraction.js";

export function markingKey(m: Marking): string;                 // m.join(",") — B1
export function compareMarkings(a: Marking, b: Marking): number;// numeric lexicographic

export interface AnalysisResult { value: boolean | null; complete: boolean; exploredStates: number; reason?: string | null; }
export interface ReachabilityResult { markings: number[][]; predecessors: Map<string, { prev: number[] | null; transition: string | null }>; complete: boolean; exploredStates: number; }
export interface ReachabilityGraph { states: number[][]; edges: Map<string, Array<[string, number[]]>>; complete: boolean; }
export interface DeadlockResult { deadlocks: number[][]; complete: boolean; exploredStates: number; reason?: string | null; }
export interface BoundResult { bounded: boolean | null; bounds: Array<[string, number]>; complete: boolean; reason?: string | null; }  // sorted [place, max] pairs (B9 — no object keys)

export class PetriNetAnalyzer {
  constructor(readonly net: PetriNet);
  reachableMarkings(maxStates: number | null): ReachabilityResult;
  reachabilityGraph(maxStates: number | null): ReachabilityGraph;
  deadlocks(maxStates: number | null): DeadlockResult;
  bounds(maxStates: number | null): BoundResult;
  firingSequenceTo(result: ReachabilityResult, target: number[]): string[] | null;
  transitionLiveness(transition: string, graph: ReachabilityGraph): AnalysisResult;
  isLive(graph: ReachabilityGraph): AnalysisResult;
  stronglyConnectedComponents(graph: ReachabilityGraph): number[][][]; // Tarjan order; inner arrays sorted (B6)
  incidenceMatrix(): number[][];
  placeInvariants(): number[][];      // coprime int tuples (B2)
  transitionInvariants(): number[][];
  private explore(maxStates: number | null): ExploreOut;  // B3 loop 1:1
}
```

- `markings` / `states` in results: sorted by `compareMarkings` (deterministic; frozenset equality via sorted-array equality).
- `deadlocks`: sorted markings of states with `enabledTransitionsAt(m) === []`.
- `bounds`: `bounded = complete ? true : null`; `reason` verbatim `"State-space exploration was truncated; boundedness is unknown."` when truncated; maxima over explored states only.
- `firingSequenceTo`: back-walk `predecessors`; `[]` for initial; `null` when absent (proof only if complete — docstring).
- `transitionLiveness`: `!graph.complete` → `{value:null, complete:false, exploredStates:states.length, reason:"Reachability graph is incomplete; liveness is unknown."}`; no enabling → `{value:false, complete:true, ...}`; else reverse-BFS over sorted states → `value = canReach.size === states.length`.
- `isLive`: incomplete → `None`+`"Reachability graph is incomplete; global liveness is unknown."`; loop transitions in `transitionOrder` (short-circuit on first non-True); empty net → `{true, true, 1}`.
- `stronglyConnectedComponents`: Tarjan (recursive) over `graph.states` keyed by `markingKey`; skip targets outside states (B7); start nodes `sorted(graph.states)`; neighbors in edge-tuple order; components as arrays of sorted markings in Tarjan finish order.
- `incidenceMatrix`: rows=placeOrder, cols=transitionOrder; `outputs[t].get(p) - inputs[t].get(p)`.
- `placeInvariants`/`transitionInvariants`: degenerate identity bases (places-only → identity for P-invariants; transitions-only → identity for T-invariants; empty → `[]`); `nullspace` port (B2) + `_coprimeIntVector` (LCM-scale → gcd-content → negate-first-nonzero).
- `explore`: B3 1:1 port — `visited`/`predecessors`/`edges` Maps keyed by `markingKey`; `maxStates !== null && visited.size >= maxStates` before enqueue; `complete=false` + record edge + continue; finish current state's edges; `break` outer; returns `{ visitedMarkings, predecessors, edges, complete, exploredStates }`.

## 6. Conformance-vector generator — `scripts/generate-vectors.py`

- Runs via `uv run python tools/petri-net-studio/scripts/generate-vectors.py` (library = executable spec). Imports `agentx.model.petri_net.model/analysis/io`; stdlib only (json).
- **Corpus** (net defs from `test_analysis.py` fixtures + shared examples):
  - `two_way_cycle` (TWO_WAY_CYCLE, LIVE_BOUNDED_M0) — `max_states: null` + `max_states: 1` (truncated reachability/graph/deadlocks/bounds)
  - `unbounded_net` (UNBOUNDED_NET, M0 {p:1}) — `max_states: 5` (truncated; bounds unknown; no deadlocks among explored)
  - `deadlock_net` (DEADLOCK_NET, M0 {p:0}) — `max_states: null` (deadlock at M0; not live; SCC single)
  - `token_drain_net` (TOKEN_DRAIN_NET, M0 {p1:1}) — `max_states: null` (2 SCCs; not live)
  - `two_deadlocks_net` (TWO_DEADLOCKS_NET, M0 {p1:1}) — `max_states: null` (sorted deadlocks)
  - `weighted_reaction` / `producer_consumer` / `hello` (shared examples) — `max_states: null` (weighted invariants; rational-free but exact; net docs already canonical)
- **Per vector computes** (Python analyzer): `reachable_markings`, `reachability_graph`, `deadlocks`, `bounds`, `incidence_matrix`, `place_invariants`, `transition_invariants`, `firing_sequences` (each reachable marking → shortest sequence; plus one provably-unreachable target → `null`), `liveness` (`is_live` + per-transition on the same graph), `sccs`. Truncated vectors: the SAME `max_states` feeds every exploration API (graph-driven APIs see the truncated graph).
- **Deterministic serialization (§7 format) — the generator and the TS reader are the two sides of the same contract.**
- Writes one canonical JSON file per id (FORMAT §8 style: `json.dumps(doc, indent=2, ensure_ascii=False) + "\n"`; keys sorted; arrays sorted by the pinned orders). Re-run = byte-identical (deterministic) → doubles as a stability check.

## 7. Vector JSON format (per-net files in `shared/petri-net/conformance/analysis-v1/`)

```jsonc
{
  "format": "petri-net-conformance",
  "version": 1,
  "id": "two_way_cycle",
  "max_states": null | 5,
  "net": { /* FORMAT §8 canonical petri-net-json v1 doc */ },
  "expected": {
    "reachable_markings": { "markings": [[1,0],[0,1]], "complete": true, "explored_states": 2,
                            "predecessors": [ [[1,0], null, null], [[0,1], [1,0], "t1"] ] },
    "reachability_graph": { "states": [[1,0],[0,1]], "complete": true,
                            "edges": [ ["1,0", [["t1", [0,1]]]], ["0,1", [["t2", [1,0]]]] ] },
    "deadlocks": { "deadlocks": [], "complete": true, "explored_states": 2, "reason": null },
    "bounds": { "bounded": true, "bounds": [["p1",1],["p2",1]], "complete": true, "reason": null },
    "incidence_matrix": [[-1,1],[1,-1]],
    "place_invariants": [[1,1]],
    "transition_invariants": [[1,1]],
    "firing_sequences": [ [[1,0], []], [[0,1], ["t1"]] ],
    "liveness": { "is_live": [true, true, 2, null],
                  "transitions": [ ["t1", true, true, 2, null], ["t2", true, true, 2, null] ] },
    "sccs": [ [[1,0],[0,1]] ]
  }
}
```

Rules (B9): no object keyed by markings/place-names — `predecessors`/`edges`/`bounds`/`firing_sequences`/`liveness.transitions` are sorted ARRAYS of pairs/triples; markings sorted lexicographically; `reason` verbatim or `null`; `net` = schema-valid canonical doc so TS `documentFromJson` builds it; `liveness` + `sccs` computed over the SAME graph the exploration produced (with the vector's `max_states`). Truncated vectors carry `complete:false` entries and reasons — the no-overclaim corpus.

## 8. Store & dashboard pin (v2 additive — v1 state untouched otherwise)

```ts
// store additions (UI state only — B12; never written into doc/format):
interface StudioState extends StudioData {
  maxStates: number | null;        // default 1000 (B10 — visible dial, never hidden)
  analysisVisible: boolean;        // default false
  setMaxStates(n: number | null): void;
  toggleAnalysis(): void;
}
```

- `initialDataState()` gains `maxStates: 1000, analysisVisible: false`. Guarded by `editLocked`? NO — analysis is view-only over M0; available in BOTH modes (edit + simulate). `setMode` does NOT touch `maxStates`/`analysisVisible`.
- Dashboard derivation: `AnalysisPanel` computes `useMemo(() => new PetriNetAnalyzer(toNet(doc)).<all APIs>(maxStates), [doc, maxStates])` — doc identity changes on any structural/M0 edit; simulate firing does NOT change `doc` ⇒ analysis stays over M0 (B12 — analysis never depends on live marking). A stale-result caveat: in simulate mode the marking moves but analysis still describes M0 reachability — label the panel "from initial marking M0".

## 9. `AnalysisPanel.tsx` — UI pin (D10 no-overclaim)

- `max_states` dial: number input (min 1, step 1) + "unlimited" checkbox → `setMaxStates(checked ? null : value)`; always rendered with current value text (D10).
- Sections, each a verdict row with badge component `Verdict({value, complete, reason})`:
  - ✅ = `value === true && complete` · ❌ = `value === false && complete` · ❓ = `complete === false || value === null` (reason shown verbatim).
  - **Reachability**: explored-states count + marking table (M0 first, then sorted reachable markings) + `complete` badge.
  - **Deadlocks**: count + sorted marking list; truncated → ❓ + verbatim reason.
  - **Bounds**: per-place maxima list (`bounds` pairs) + `bounded` badge (✅ true / ❓ unknown-on-truncation).
  - **Liveness**: `is_live` badge + per-transition liveness badges.
  - **SCCs**: count + component groups.
  - **Invariants**: P/T-invariant vector rows with place/transition column labels (coprime int tuples).
  - **Incidence**: places × transitions matrix table (small caps for v1).
- Toolbar: "Analyze" toggle button → `toggleAnalysis()`; panel renders below the canvas when visible.
- Styling: plain CSS consistent with v1 (badges colored: green/red/amber).

## 10. Test plan (Vitest; manual red→green per B11)

### 10.1 `tests/engine/fraction.test.ts` — fraction behaviors (~10)
gcd(0,0)=0 · gcd(0,x)=|x| · gcd negatives → abs · lcm · Fraction normalize (1/2, -1/2, 2/4→1/2, 1/-2→-1/2, 0/5→0/1) · add/sub/mul/div exact · neg · isZero · toInt exact-only.

### 10.2 `tests/engine/analysis.test.ts` — 38 behaviors (1:1 port of `test_analysis.py`; fixtures inlined from the Python file)
Same class structure (TestReachableMarkings 2, TestReachabilityGraph 2, TestFiringSequenceTo 4, TestDeadlocks 2, TestBounds 2, TestIncidenceMatrix 5, TestPlaceInvariants 4, TestTransitionInvariants 4, TestTransitionLiveness 3, TestIsLive 4, TestStronglyConnectedComponents 4, TestDeterminism 2). Assertions: deep equality on result objects (frozensets → sorted-array equality via `compareMarkings`); `AnalysisResult` deep-equal incl. reason; truncated reasons verbatim.

### 10.3 `tests/engine/conformance.test.ts` — vector suite
`fs.readdirSync` over `shared/petri-net/conformance/analysis-v1/*.json`; for each: parse (JSON.parse — vector docs are generator-written, loader strictness not under test here), `documentFromJson(net)` → net, run ALL analysis APIs with `max_states` from the doc, compare against `expected` (deep equal; marking arrays sorted; maps re-keyed by markingKey). Failures name the vector id + API. `// @vitest-environment node` docblock (fs; jsdom rewrites `import.meta.url` — feature_034 precedent).

### 10.4 `tests/state/store.test.ts` — additive cases
defaults (`maxStates===1000`, `analysisVisible===false`) · setMaxStates(null | n) · toggleAnalysis · mode transitions leave them untouched.

### 10.5 Evidence protocol (B11)
Each cycle: write spec/tests → stub → `npx vitest run <file>` RED summary → implement → GREEN summary; paste into the test report.

## 11. Programming sequence (copy order)

1. **B11 scope declaration**: `omt_phase{task_type:"major_feature", phase:"Programming", …}` — declares the Vitest/omt_tdd mismatch (A11 precedent; manual red→green).
2. **Cycle 1 (fraction)**: `fraction.ts` stub + `tests/engine/fraction.test.ts` spec → RED → implement → GREEN.
3. **Cycle 2 (analysis)**: `analysis.ts` stub + `tests/engine/analysis.test.ts` (38) → RED → implement (B2/B3 exact) → GREEN.
4. **Cycle 3 (vectors)**: `scripts/generate-vectors.py` → `uv run python …` → 8 vector files → `tests/engine/conformance.test.ts` spec → RED (vectors exist but engine already green — RED via a deliberately-wrong expected? NO: conformance RED comes BEFORE engine implementation is guaranteed correct; sequence: write generator + conformance test, run against a stub engine to see RED, then rely on cycle-2 GREEN engine for final GREEN) → GREEN on full suite.
   - Simplification: cycle 2's GREEN engine already passes 10.2; conformance test is written in cycle 3 and passes against the same engine (the generator is the untested half — its RED/GREEN is: run generator → run conformance test → if diff, fix generator; evidence = conformance suite green + re-run byte-identical).
5. **Cycle 4 (dashboard)**: store edits (§8) + store test additions (10.4) → RED → GREEN; `AnalysisPanel.tsx` + App toggle → `tsc` clean + `npm run build` green; manual `vite preview` smoke.
6. **Independence**: `npm run check-independence` — must stay green (no new src/ cross-boundary imports; generator `.py` unscanned).
7. **Sentinel + suite**: `tests/features/feature_035.studio_v2_analysis/test_studio_v2_analysis_sentinel.py` (feature_034 precedent: executes `npx vitest run`, env-skip without node, structural floor always-on; canary-approval skip logged) → `uv run pytest -q` full agentx suite green.
8. **Bookkeeping**: implementation notes, test report, FEATURE.md/PLAN.md checkboxes, WORK.md, project CURRENT_STATE/PROJECT iter-8, `omt_complete` Programming → Testing → Done.

## 12. Explicit non-goals (locked scope reminders)

No reachability-graph EXPLORER UI / auto-layout / animation / conformance RUNNER wiring (#5), no coverability, no current-marking snapshot in analysis (analysis describes M0 only), no backend, no npm publish, no `src/` (agentx) edits, no changes to `shared/petri-net/{FORMAT.md,schema,examples}` (LOCKED), no new runtime npm deps (fraction.ts hand-rolled, B2).