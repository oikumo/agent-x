# Operation Spec 001 — feature_036.studio_v3_graph: public operation contracts

> Phase: Design companion to design_001. Each operation: signature · pre · post/effects · errors. Semantics = the feature_035 engine (`analysis.ts`/`model.ts`) exactly — **engine UNCHANGED except the `markingFromKey` export (C1)**; this spec is the caller-facing TS contract for the NEW public operations introduced by design_001. `M` = marking (`readonly number[]`) over `placeOrder`. `net` = `PetriNet` instance (`engine/model.ts`); `analyzer` = `PetriNetAnalyzer` instance (`engine/analysis.ts:96`).

## engine/analysis.ts — `markingFromKey` export (C2; the ONLY engine edit)

| Op | Contract |
|---|---|
| `markingFromKey(key: string) → number[]` | Pre: `key` produced by `markingKey` (join of non-negative ints, or `""` for the empty marking). Post: the marking array; **`markingFromKey("") === []`** (empty-marking gotcha, TA analysis.ts:31 — `"".split(",")` would yield `[0]`); non-empty keys split on `","` and `Number`-map each part. Errors: none (internal engine format; callers pass `markingKey`-produced keys). Mirrors the existing private fn at analysis.ts:30; change = `export` keyword only. |

### Consumed engine APIs (existing, UNCHANGED — read-only contract the explorer relies on)

| Op (PetriNetAnalyzer) | Signature / contract |
|---|---|
| `reachableMarkings(maxStates)` | → `ReachabilityResult` `{markings, predecessors, complete, exploredStates}`; markings sorted by `compareMarkings`. Source for `firingSequenceTo`. |
| `reachabilityGraph(maxStates)` | → `ReachabilityGraph` `{states: number[][], edges: Map<key, Array<[transition, successorMarking]>>, complete}`; edge arrays in `enabledTransitionsAt` order (deterministic B6); truncation → `complete:false` + edges to unvisited successors present (dangling). |
| `deadlocks(maxStates)` | → `DeadlockResult` `{deadlocks: number[][], complete, exploredStates, reason?}`. |
| `stronglyConnectedComponents(graph)` | → `number[][][]` (Tarjan; truncation skips dangling targets — no phantom components). |
| `transitionLiveness(transition, graph)` | → `AnalysisResult` `{value: boolean\|null, complete, exploredStates, reason?}`. |
| `isLive(graph)` | → `AnalysisResult` (AND over transitions). |
| `firingSequenceTo(result, target)` | → `string[]` M0-rooted transition sequence (predecessors walk) or `null` when target unreachable. |
| `markingKey(m)` (module fn) | `m.join(",")`; `m` non-negative ints ⇒ unambiguous (B1). |

## src/ui/graphProjection.ts — pure projection (design §4; C5)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `projectGraph(graph, sccs, deadlocks, positions, placeOrder) → { nodes: ExplorerNode[]; edges: ExplorerEdge[] }` | `graph` = `reachabilityGraph(maxStates)`; `sccs` = Tarjan output; `deadlocks` = `DeadlockResult.deadlocks`; `positions` = elkjs map keyed by markingKey (may be partial); `placeOrder` = `net.placeOrder` | PURE — deterministic given identical inputs (deep-equal output). **Nodes** (1 per state, `kind:"state"`): `id = markingKey(marking)`; `label = "M0"` when `marking` equals the net's `initialMarkingTuple` else `` `(${m.join(",")})` `` (e.g. `(1,0)`); `data.marking = marking` (the engine's array, already sorted); `data.sccIndex` = index of the component in `sccs` containing `marking`; `data.deadlock` = membership in `deadlocks`; `data.initial` = is-M0 flag; `position = positions[id] ?? {x:0,y:0}` (missing → origin). **Edges** (1 per `graph.edges` entry in map array order = engine order): `id = markingKey(src) + "::" + transition + "::" + markingKey(dst)` (parallel transitions ⇒ distinct ids); `source`/`target` = node ids (dangling target → edge still emitted, no node — React Flow drops it, banner carries the message); `label = transition`; `markerEnd` arrow (mirrors flow.ts). `data.transition = transition`. | none (pure projection over trusted engine types) |

## src/ui/animation.ts — sequence stepping helpers (design §5/§11-4; C3, C10)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `markingAt(net, m0, seq, step) → number[]` | `m0` = `net.initialMarkingTuple()`; `seq` non-empty `string[]` (from `firingSequenceTo` — M0-rooted, valid on `net`); `step` integer | PURE fold: `step = 0` → copy of `m0`; `step = k` → `net.fireMarking` folded over `seq.slice(0, k)`; **clamped** to `[0, seq.length]` (step > len → final marking; step < 0 → 0). Returns a NEW array each call (never aliases). | `TransitionNotEnabledError` etc. propagate — unreachable in practice (seq is engine-produced for this net/M0); UI never guards. |
| `sequenceSteps(net, m0, seq) → number[][]` | as above | `[m0, markingAt(1), …, markingAt(seq.length)]` — length `seq.length + 1`; deterministic. | as above |
| (null-sequence handling) | — | `firingSequenceTo` returning `null` is a CALLER case: the UI renders "unreachable" (no crash); the helpers above are never called with `null`. | — |

## src/state/store.ts — additive view state (design §6; C3)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `graphVisible: boolean` (StudioData field) | — | default `false` in `initialDataState()`; NOT edit-locked (view over M0 in both modes, like `analysisVisible`); `setMode` does NOT touch it; never written into doc/format. | — |
| `toggleGraph(): void` (StudioState action) | — | flips `graphVisible` (mirrors `toggleAnalysis`, store.ts:313). | — |

## src/examples.ts — gallery metadata + load path extension (design §8; C6/C7)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `interface GalleryEntry { id: string; text: string; description: string }` | — | Gallery card contract; `description` one-line studio-local copy (NOT format data). | — |
| `GALLERY_ENTRIES: GalleryEntry[]` | — | 8 entries in display order: `hello`, `producer_consumer`, `weighted_reaction` (existing `?raw` texts) + `two_way_cycle`, `unbounded_net`, `deadlock_net`, `token_drain_net`, `two_deadlocks_net` (from `../../../shared/petri-net/conformance/analysis-v1/<id>.json?raw`; `JSON.parse(raw).net` extracted and re-stringified preserving canonical member order). `two_way_cycle_truncated` EXCLUDED (same net as `two_way_cycle`). `text` = canonical petri-net-json doc string; every entry parses via `documentFromJson` (schema-valid). | none (build-time data; `tests/ui/gallery.test.ts` asserts validity) |
| `EXAMPLE_TEXTS` (extension) | — | gains the 5 fixture-net ids → canonical doc text (so `store.loadExample(id)` succeeds for ALL 8 gallery ids — test 10.3). | — |
| `EXAMPLE_NAMES` (unchanged) | — | stays the 3 canonical examples (select path unchanged). | — |
| `loadExample(id)` (existing store op) | id ∈ `EXAMPLE_TEXTS` keys | as feature_034: `importJson(text)` path → edit mode; unknown id → `importError` set, `false`. | captured, not thrown |

## scripts/conformance.mjs — runner formalization (design §7; C8)

| Op | Contract |
|---|---|
| `npm run conformance` → `node scripts/conformance.mjs` (cwd = `tools/petri-net-studio/`) | Sequential side-effect script, exit 0 ONLY if all pass: (1) `spawnSync("uv", ["run", "python", "scripts/generate-vectors.py"], cwd=STUDIO)` — regenerate vectors; (2) assert `git status --porcelain shared/petri-net/conformance/` is EMPTY (byte-identical re-run — generator determinism contract); fail with a diff hint otherwise; (3) `spawnSync("npx", ["vitest", "run", "tests/engine/conformance.test.ts"], cwd=STUDIO)` — the existing suite. Prints a step-by-step summary. Non-zero exit + message on any failure. Disposition: the Vitest runner was shipped in feature_035; this script is the #5 "runner wiring" formality + the corpus extension path. |

## UI ops (App / GraphExplorer / Gallery — component-level contract; design §4–6, §8)

| Op | Pre | Post / effects |
|---|---|---|
| App "Graph" toolbar button | — | toggles `store.graphVisible` via `toggleGraph()`; active class when open (mirrors "Analyze"); `{graphVisible && <GraphExplorer />}` rendered below the canvas (sibling to `AnalysisPanel`, both can be open — C4). |
| App "Gallery" toolbar button | — | toggles App-local `galleryOpen` (`useState`); `{galleryOpen && <Gallery />}` panel. |
| `GraphExplorer.tsx` render | `doc` + `maxStates` from store | Derived `useMemo` over `toNet(doc)` + `maxStates`: `reachableMarkings`, `reachabilityGraph`, `deadlocks`, `stronglyConnectedComponents`, `transitionLiveness` per transition — same exploration semantics as the dashboard (never a second explore pass for the sub-views). Layout: `elkjs` `ELK().layout({id:"root", children, edges})` → positions map, memoized on graph identity; **positions never stored** (C9; no layout-byte gating). Renders `<ReactFlow>` (existing provider) with `nodesDraggable={false}`, `nodesConnectable={false}`, `deleteKeyCode={null}`, `fitView` — a VIEW, not an editor. Node fill = SCC color (`sccIndex % palette.length`, 6 HSL hues); deadlock nodes distinct border + ⛔ marker; M0 node ring. `!graph.complete` → persistent truncation banner (D10) + liveness badges ❓. |
| GraphExplorer node click | mode any (view over M0, B12) | `seq = firingSequenceTo(reach, targetMarking)`; `null` → strip shows "unreachable" (no crash); else sequence strip `M0 --t1--> M1 --t2--> … --tn--> target`. Strip state = COMPONENT-LOCAL `useState` (`step` 0..seq.length, `playing`) — **never touches store marking/doc** (C3). |
| GraphExplorer Play/Step/Reset | seq non-null | Play: `setInterval` ~700ms `setStep(s => min(s+1, len))`, pause at end; Step: `min(step+1, len)`; Reset: 0. Cell highlight = transition at current boundary; target cell shows clicked marking. `markingAt`-derived displays (pure). |
| GraphExplorer legend | — | SCC color chips (count) + per-transition liveness badges (✅/❌/❓ via existing `status-*` badge classes); `!complete` → ❓. |
| `Gallery.tsx` render | `galleryOpen` | Card grid (`.gallery-grid`): name + description + "Load" button per `GALLERY_ENTRIES`; Load → `store.loadExample(id)` (existing path → edit mode); import failures surface via the existing `importError` banner. |

## Global invariants

- **Engine untouched (C1)** — the ONLY `engine/*.ts` edit is `export` on `markingFromKey`; `model.ts`/`analysis.ts` semantics (fraction-exact, B6 ordering, completeness-explicit) unchanged.
- **Explorer is read-only over M0 (B12/C3)** — the store's live `marking`, `doc`, and format are never written by GraphExplorer/animation; only `graphVisible`/`toggleGraph` are added.
- **Pure layer before UI** — `projectGraph`, `markingAt`, `sequenceSteps`, and gallery metadata are pure (DOM-free) and are the primary Vitest RED targets (C10); layout positions are injected/returned, never computed inside projections.
- **Independence by construction (D5/C7)** — `src/` (studio) imports nothing from agentx/harness; cross-boundary `?raw` coupling allowed ONLY under `shared/petri-net/examples/` OR `shared/petri-net/conformance/` (allowlist regex in `scripts/check-independence.mjs`); `shared/petri-net/conformance/analysis-v1/*.json` READ-ONLY.
- **All sorts code-point (A3)**; store/UI never bypass the engine for semantics.