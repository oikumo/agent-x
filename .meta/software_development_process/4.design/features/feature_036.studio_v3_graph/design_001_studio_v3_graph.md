# Design 001 — feature_036.studio_v3_graph: v3 implementation blueprint

> Date: 2026-08-29 · Phase: Design · Sources: PROJECT.md scope LOCKED v1.1 (roadmap #5, D1–D10; iter-7 D8 re-lock; iter-8 v2-complete) + analysis_001 (C1–C10) + `tools/petri-net-studio/src/engine/analysis.ts` (feature_035 port — reachabilityGraph/firingSequenceTo/transitionLiveness/isLive/stronglyConnectedComponents all present) + `src/ui/{AnalysisPanel,App,flow}.tsx` + `src/state/store.ts` + `src/examples.ts` + `scripts/{check-independence.mjs,generate-vectors.py}` + `shared/petri-net/conformance/analysis-v1/` (9 vectors) + D2 (graph viz stack).
> Rule: Programming copies this doc; anything ambiguous here is resolved HERE, not in code.

---

## 1. Deliverable & definition of done

`tools/petri-net-studio/` v3 — reachability-graph explorer (auto-layout) + firing-sequence animation + liveness/SCC views + conformance-runner formalization + example gallery. Done when:

1. `src/ui/GraphExplorer.tsx` renders the reachability graph (nodes = states, edges = transitions) with elkjs auto-layout (D2), SCC coloring, deadlock highlight, truncation banner (D10);
2. Firing-sequence animation: clicking a state → `firingSequenceTo` sequence shown → Play/Step/Reset animates `fireMarking` steps in a preview strip (M0-rooted; never mutates doc/live marking);
3. Liveness/SCC views: per-transition liveness badges + SCC-color legend, same-graph semantics as the dashboard (never re-explore);
4. `scripts/conformance.mjs` (`npm run conformance`): regenerate vectors via `uv run`, assert byte-identical (`git status --porcelain` clean), run the Vitest conformance suite;
5. Example gallery: `src/ui/Gallery.tsx` (cards: name + description + Load) over 3 canonical examples + 5 unique fixture nets from the vector corpus; `loadExample` stays the load path;
6. Vitest green (existing 245 + new suites); `tsc` clean; `npm run build` green; independence OK (allowlist extended per §3); agentx pytest suite untouched/green (zero `src/` edits — sentinel bridge).

## 2. C-findings dispositions (analysis_001 → design PINs)

| # | PIN |
|---|---|
| C1 | **Engine untouched.** `src/engine/*.ts` is listed UNCHANGED; the explorer consumes `reachabilityGraph`/`firingSequenceTo`/`transitionLiveness`/`isLive`/`stronglyConnectedComponents`/`markingKey` as-is. The ONE additive export: `markingFromKey` (analysis.ts) — the explorer needs marking arrays from `markingKey`-keyed edge maps (C2). |
| C2 | **Export `markingFromKey`** from analysis.ts (currently private). One-line additive; mirrors `markingKey`. Empty-marking gotcha (TA analysis.ts:31) stays in the function. |
| C3 | **Store additions minimal.** `graphVisible: boolean` (default false) + `toggleGraph()` mirror `analysisVisible`/`toggleAnalysis` (B12 pattern). Animation state is COMPONENT-LOCAL (`useState` sequence/step/playing + `setTimeout` driver) — ephemeral, derived from a fixed sequence, never stored. `maxStates` remains THE shared dial (dashboard + explorer use the same value). |
| C4 | **Explorer is a sibling view.** AnalysisPanel tables stay; "Graph" toolbar button toggles `graphVisible` → renders `<GraphExplorer />` below the canvas (mirrors `analysisVisible && <AnalysisPanel />`). Both can be open. |
| C5 | **New pure projection** `src/ui/graphProjection.ts` (mirrors `flow.ts`): `reachabilityGraph` + SCC + deadlocks → React Flow nodes/edges with style flags; positions injected as a parameter so layout is a separate step (testable without elkjs). Node ids = `markingKey(marking)`; edge ids = `markingKey(src) + "::" + t + "::" + markingKey(dst)` — parallel transitions yield distinct ids (injective enough for v1; no separator collisions: markings are int-comma strings, transitions are non-empty names). |
| C6 | **Gallery replaces the dropdown's role, not the load path.** `loadExample`/`importJson` unchanged; Gallery is a new toggle panel (`galleryOpen` local state in App) rendering cards; each card calls `loadExample(id)` on click (same as the `<select>`). The `<select>` stays (cheap) OR is removed — Design picks: **keep both** (select for keyboard speed, Gallery for discovery); no conflict since both call `loadExample`. |
| C7 | **Independence allowlist (a).** Extend `scripts/check-independence.mjs` `ALLOWED_OUTSIDE` to accept BOTH `shared/petri-net/examples/` and `shared/petri-net/conformance/` substrings (regex alternation); update the docblock. `src/examples.ts` or new `src/gallery.ts` imports the vector `net` docs via `?raw` (established coupling mechanism). `shared/META.md` DIR_PETRI_NET already names `petri-net/conformance/`. |
| C8 | **Conformance disposition: runner exists; add regeneration script.** Do NOT rebuild the Vitest suite. `scripts/conformance.mjs`: (1) `uv run python scripts/generate-vectors.py` (regenerate), (2) assert `git status --porcelain shared/petri-net/conformance/` empty (byte-identical re-run stability check — the generator's determinism contract), (3) `npx vitest run tests/engine/conformance.test.ts`. Wired as `npm run conformance`. |
| C9 | **Layout = elkjs (D2-faithful).** Add `elkjs` dev dependency (`npm install elkjs`; network). Layout is a separate pure step `layoutGraph(nodes, edges) → positions` (ELK layered); the projection never embeds positions (testability). Layout determinism: ELK is deterministic for identical input; we do NOT gate conformance on layout bytes (visual-only determinism — documented, not tested). React Flow renders with `nodesDraggable={false}` (a VIEW, not an editor). |
| C10 | **TDD = manual red→green under Vitest (A11 precedent).** Declared in Programming scope; evidence pasted into the test report. RED targets are the pure functions (projection, animation stepping, gallery metadata) + store additive cases. |

## 3. Repository changes

```
tools/petri-net-studio/
├── package.json                        (EDIT — devDep elkjs; script "conformance")
├── scripts/
│   ├── check-independence.mjs          (EDIT — ALLOWED_OUTSIDE regex: examples/ OR conformance/ + docblock)
│   └── conformance.mjs                 (NEW §7 — regeneration + byte-identical + vitest conformance)
├── src/engine/
│   ├── analysis.ts                     (EDIT — export markingFromKey; one-line)
│   └── model.ts                        (existing, UNCHANGED)
├── src/state/store.ts                  (EDIT §6 — graphVisible/toggleGraph; additive)
├── src/examples.ts                     (EDIT §8 — gallery metadata + conformance-net ?raw imports)
├── src/ui/
│   ├── App.tsx                         (EDIT — "Graph" toolbar toggle + render GraphExplorer + Gallery)
│   ├── graphProjection.ts              (NEW §4 — pure projection)
│   ├── GraphExplorer.tsx               (NEW §5 — canvas + animation strip + liveness/SCC legend)
│   ├── Gallery.tsx                     (NEW §8 — card grid)
│   └── AnalysisPanel.tsx               (existing, UNCHANGED)
├── styles.css                          (EDIT §9 — explorer/gallery/animation styles)
└── tests/
    ├── engine/analysis.test.ts         (EDIT — additive case: markingFromKey round-trip + empty-marking)
    ├── ui/graphProjection.test.ts      (NEW §10.1)
    ├── ui/animation.test.ts            (NEW §10.2)
    ├── ui/gallery.test.ts              (NEW §10.3)
    └── state/store.test.ts             (EDIT — additive: graphVisible/toggleGraph)
shared/petri-net/                       (NO edits — vectors are D5-locked; gallery READS them)
tests/features/feature_036.studio_v3_graph/test_studio_v3_graph_sentinel.py   (NEW — §11)
```

No `src/` (agentx) edits. No `shared/petri-net/{FORMAT.md,schema,examples}` edits (LOCKED). `shared/petri-net/conformance/analysis-v1/*.json` READ-ONLY (gallery + runner inputs).

## 4. `graphProjection.ts` — pure projection (API pin)

```ts
import type { Edge, Node } from "@xyflow/react";
import type { ReachabilityGraph } from "../engine/analysis.js";
import type { Point } from "../state/store.js";

export interface GraphNodeData extends Record<string, unknown> {
  kind: "state";
  marking: number[];
  label: string;          // "M0" for initial, "(1,0)" tuple text otherwise (§10.1)
  sccIndex: number;       // -1 when graph.complete === false? NO — SCC always computed (engine skips dangling); -1 never used
  deadlock: boolean;
  initial: boolean;
}
export type ExplorerNode = Node<GraphNodeData, "state">;

export interface ExplorerEdgeData extends Record<string, unknown> {
  transition: string;
}
export type ExplorerEdge = Edge<ExplorerEdgeData>;

export function projectGraph(
  graph: ReachabilityGraph,
  sccs: number[][][],          // Tarjan output (engine)
  deadlocks: number[][],       // engine deadlocks(maxStates).deadlocks
  positions: Record<string, Point>,  // elkjs output keyed by markingKey; NOT computed here
  placeOrder: string[],        // for named tooltips
): { nodes: ExplorerNode[]; edges: ExplorerEdge[] };
```

- Node id = `markingKey(marking)`; label = `"M0"` (marking === initialMarkingTuple) else `(m.join(","))`; `sccIndex` = index of the component containing the node (sorted components, engine order); `deadlock` = in the deadlock set; positions from the passed map (missing → `{x:0,y:0}`).
- Edge id = `markingKey(src) + "::" + t + "::" + markingKey(dst)`; `source`/`target` = node ids; label = transition name; markerEnd arrow (mirrors flow.ts).
- Edge order = graph.edges.get(srcKey) array order (= `enabledTransitionsAt` order, deterministic B6).
- Determinism: given the same graph/sccs/deadlocks/positions, output is identical (pure). Marking arrays are the engine's, already sorted.

## 5. `GraphExplorer.tsx` — component pin

- **Derived state (B12)**: `useMemo` over `toNet(doc)` + `maxStates` → `reachabilityGraph`, `deadlocks`, `sccs`, `transitionLiveness` per transition (same `graph` object — never re-explore; the SAME graph the dashboard would show).
- **Layout**: `layoutGraph(nodes, edges)` = `elkjs` layered layout (`ELK().layout({id:"root", children, edges})` → positions map); memoized on graph identity; **positions never stored**.
- **Rendering**: `<ReactFlow>` (existing provider) `fitView`, `nodesDraggable={false}`, `nodesConnectable={false}`, `deleteKeyCode={null}` — a pure view. Node fill = SCC color (HSL palette, `sccIndex % palette.length`); deadlock nodes get a distinct border + ⛔ marker; initial node labelled M0 with ring.
- **Truncation banner (D10)**: `!graph.complete` → persistent banner "State-space exploration was truncated — graph shows explored states only; liveness/SCC verdicts are unknown." + dangling edges rendered (engine records edges to unvisited successors — those target node ids have no node; React Flow drops them; the banner carries the no-overclaim message; edge count shown from the map). Liveness badges in the legend render ❓ when `!complete`.
- **Animation (3.2)**: click a node → `firingSequenceTo(reachResult, marking)`; show sequence strip `M0 --t1--> M1 --t2--> … --tn--> target`. Play/Step/Reset:
  - `step` = `useState<number>` (0..seq.length); `markingAt(step)` = fold `net.fireMarking` over `seq.slice(0, step)` (pure, M0-rooted — C1 engine semantics);
  - Play: `setInterval`-driven `setStep(s => min(s+1, len))` ~700ms; pause on reaching end; Reset → 0;
  - strip cells highlight the transition at the current boundary; the target cell shows the clicked marking;
  - **never touches store marking / doc** — the strip is self-contained (C3).
- **Legend (liveness/SCC views)**: SCC color chips (count) + per-transition liveness badges (`transitionLiveness` on the same graph; ✅/❌/❓ via the existing badge semantics) — reuses the AnalysisPanel `StatusBadge`-style CSS classes.

## 6. Store & gallery state pin (additive — v1/v2 state untouched)

```ts
interface StudioState extends StudioData {
  graphVisible: boolean;   // default false (mirrors analysisVisible)
  toggleGraph(): void;
}
```
- `initialDataState()` gains `graphVisible: false`. NOT edit-locked (view over M0 in both modes, like analysis). `setMode` does NOT touch it.
- Gallery: `galleryOpen` is App-local `useState` (not store) — pure UI chrome, no test surface beyond the card list (tested via gallery.test.ts metadata, not store).

## 7. `scripts/conformance.mjs` — runner formalization (C8)

```
npm run conformance  →  node scripts/conformance.mjs
```
1. `spawnSync("uv", ["run", "python", "scripts/generate-vectors.py"], cwd=STUDIO)` — regenerate;
2. `git status --porcelain shared/petri-net/conformance/` must be EMPTY (byte-identical re-run — the generator's determinism contract; fail otherwise with a diff hint);
3. `spawnSync("npx", ["vitest", "run", "tests/engine/conformance.test.ts"])` — the existing suite;
4. Exit 0 only if all three pass; print step-by-step summary.
Documented disposition (C8): the Vitest runner was shipped in feature_035; this script is the #5 "runner wiring" formality + the extension path for the corpus.

## 8. Gallery — `examples.ts` edit + `Gallery.tsx`

```ts
// examples.ts (EDIT):
export interface GalleryEntry { id: string; text: string; description: string; }
export const GALLERY_ENTRIES: GalleryEntry[];   // order = display order
```
- Entries (8): `hello`, `producer_consumer`, `weighted_reaction` (existing ?raw) + `two_way_cycle`, `unbounded_net`, `deadlock_net`, `token_drain_net`, `two_deadlocks_net` (fixture nets) — imported from the vector corpus as `?raw` (`../../../shared/petri-net/conformance/analysis-v1/<id>.json?raw`), `JSON.parse(...).net` extracted and re-stringified to a canonical petri-net-json doc. `two_way_cycle_truncated` is EXCLUDED (same net as `two_way_cycle`, different max_states — no gallery value).
- Descriptions: one line each (e.g. `hello`: "One place and one transition: a single enabled step."; pin exact strings in the test §10.3). Studio-local metadata — NOT format data.
- `Gallery.tsx`: toolbar toggle (`galleryOpen`) → modal-like panel (reuse `.dialog` styles) with cards (name + description + "Load" button); Load → `loadExample(id)` (existing path → edit mode; import errors surface via `importError` banner).
- The `EXAMPLE_TEXTS`/`EXAMPLE_NAMES` select path stays for the 3 canonical examples.

## 9. Styling — `styles.css` additive sections

- `.explorer-panel` (mirrors `.analysis-panel`), `.explorer-legend` (chips + badges), `.scc-chip` (colored), `.state-node` (round, colored fill, deadlock border), `.truncation-banner` (amber, distinct), `.sequence-strip` (cells + arrows), `.sequence-cell.active` (highlight), `.gallery-grid` / `.gallery-card` / `.gallery-card button`. Reuse the existing `status-ok`/`status-no`/`status-unknown` badge classes. Palette: 6 HSL hues, deterministic order.

## 10. Test plan (Vitest; manual red→green per C10)

### 10.1 `tests/ui/graphProjection.test.ts` — pure projection (~12)
Two-state hello net (graph 2 states / 1 edge) + weighted_reaction (weighted edge labels) + truncated net (edge to absent node id still emitted): node ids = markingKey · labels (M0 vs tuple) · sccIndex assignment · deadlock flag · edge ids unique with parallel transitions · edge order = engine order · positions injected (missing → origin) · determinism (same input → deep-equal output).

### 10.2 `tests/ui/animation.test.ts` — sequence stepping (~8)
`firingSequenceTo` on hello → `["t1"]`; step fold `markingAt(step)` via `net.fireMarking` matches `reachableMarkings` successors at each step; reset → M0; full sequence → target marking; sequence null (unreachable) → strip shows "unreachable" (no crash); step bounds clamp; determinism.

### 10.3 `tests/ui/gallery.test.ts` — gallery metadata (~6)
8 entries · ids unique · every entry's text parses via `documentFromJson` (schema-valid canonical) · `loadExample(id)` returns true for every id · description non-empty · `two_way_cycle_truncated` excluded.

### 10.4 `tests/state/store.test.ts` — additive (~2)
`graphVisible` default false · `toggleGraph` flips.

### 10.5 `tests/engine/analysis.test.ts` — additive (~2)
`markingFromKey` round-trips `markingKey` for non-empty markings · `markingFromKey("") === []` (empty-marking gotcha).

### 10.6 Evidence protocol (C10)
Each cycle: write spec/tests → stub → `npx vitest run <file>` RED summary → implement → GREEN summary; paste into the test report.

## 11. Programming sequence (copy order)

1. **C10 scope declaration**: `omt_phase{task_type:"major_feature", phase:"Programming", …}` — declares the Vitest/omt_tdd mismatch (A11 precedent; manual red→green).
2. **Cycle 1 (engine additive)**: export `markingFromKey` + analysis.test.ts additive cases (10.5) → RED → GREEN.
3. **Cycle 2 (projection)**: `graphProjection.ts` stub + `tests/ui/graphProjection.test.ts` (10.1) → RED → implement (pure) → GREEN.
4. **Cycle 3 (animation)**: `tests/ui/animation.test.ts` (10.2) → RED → implement `markingAt`/step helpers (exported from GraphExplorer or a small `src/ui/animation.ts` pure module) → GREEN.
5. **Cycle 4 (store + gallery data)**: store `graphVisible`/`toggleGraph` + store test additions (10.4) → RED → GREEN; `examples.ts` GALLERY_ENTRIES + `gallery.test.ts` (10.3) → RED → GREEN.
6. **Cycle 5 (UI)**: `npm install elkjs` → `GraphExplorer.tsx` + `graphProjection` wiring + `App.tsx` Graph/Gallery toggles + `styles.css` §9 → `tsc` clean + `npm run build` green + `vite preview` smoke; independence allowlist edit (C7) + `npm run check-independence` green.
7. **Cycle 6 (conformance runner)**: `scripts/conformance.mjs` + `package.json` script → run → byte-identical + suite green.
8. **Sentinel + suite**: `tests/features/feature_036.studio_v3_graph/test_studio_v3_graph_sentinel.py` (feature_035 precedent: executes `npx vitest run`, env-skip without node, structural floor always-on incl. new files; canary-approval skip logged) → `uv run pytest -q` full agentx suite green.
9. **Bookkeeping**: implementation notes, test report, FEATURE.md/PLAN.md checkboxes, WORK.md, project CURRENT_STATE/PROJECT iter-9, `omt_complete` Programming → Testing → Done.

## 12. Explicit non-goals (locked scope reminders)

No engine changes beyond the `markingFromKey` export (C1); no coverability; no current-marking snapshot in the explorer (M0-only, B12); no animation of the EDITOR canvas marking (preview strip only — C3; the strip is the success criterion "animates firing_sequence_to results"); no layout-byte gating (C9); no new shared/ contract edits; no backend; no `src/` (agentx) edits; no cytoscape.js (elkjs only, D2); no persistence of layout/explorer state into the document/format.