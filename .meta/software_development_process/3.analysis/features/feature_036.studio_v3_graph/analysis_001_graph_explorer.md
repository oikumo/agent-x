# Analysis 001 — feature_036.studio_v3_graph: reachability-graph explorer & gallery

> Date: 2026-08-29 · Phase: Analysis · Sources: PROJECT.md scope LOCKED v1.1 (roadmap #5, D1–D10; iter-7 D8 re-lock; iter-8 project-v2-complete), `tools/petri-net-studio/src/engine/analysis.ts` (feature_035 port — 510 LOC), `tools/petri-net-studio/src/ui/{AnalysisPanel,App,flow}.tsx` + `src/state/store.ts` + `src/examples.ts` (feature_034/035 tree), `tools/petri-net-studio/tests/engine/conformance.test.ts` + `tests/state/store.test.ts`, `scripts/generate-vectors.py`, `scripts/check-independence.mjs`, `shared/petri-net/conformance/analysis-v1/` (9 vectors), `shared/petri-net/examples/` (3 canonical), design_001/analysis_001 of feature_035.
> Purpose: inventory what roadmap #5 must add given the feature_035 tree, resolve the deliverables that are already shipped, and record the traps/decisions for Design.

---

## 1. Scope anchor (locked)

Roadmap #5 (PROJECT.md, LOCKED v1.1): **Reachability-graph explorer (auto-layout), firing-sequence animation, liveness/SCC views, conformance-suite runner wired into Vitest, example gallery**. Depends on #4 ✅ (analysis port + vectors) and #2 ✅ (vector generation source). Project v2 completion; **no `src/` (agentx) edits** — this feature lives entirely under `tools/petri-net-studio/` (+ the per-feature pytest sentinel dir).

**Headline finding (C1):** the engine layer roadmap #5 describes is ALREADY SHIPPED by feature_035. `analysis.ts` exposes `reachabilityGraph`, `firingSequenceTo`, `transitionLiveness`, `isLive`, `stronglyConnectedComponents`, `markingKey` — every graph/liveness/SCC API the explorer needs exists and passes the 9-vector conformance suite. Feature #5 is a **UI/UX layer feature**: the reachability-graph VIEW (nodes=states, edges=transitions, auto-layout), the animation driver, the liveness/SCC visualization, the conformance-runner formalization, and the example gallery. **No engine changes are expected** (any engine diff would be a re-port regression risk; flag to Design to keep `engine/*.ts` untouched).

## 2. Existing assets (feature_034 + feature_035 tree — the palette #5 composes)

| Asset | Path | Notes for #5 |
|---|---|---|
| Analysis engine | `src/engine/analysis.ts` | `reachabilityGraph(maxStates)` → `{states, edges: Map<markingKey, Array<[transition, successor]>>, complete}` — the explorer's data source. `firingSequenceTo(reach, target)` → transition sequence (or null) — the animation source. `transitionLiveness`/`isLive`/`stronglyConnectedComponents` — the liveness/SCC views. `markingKey` exported; `markingFromKey` is PRIVATE (C2). |
| Model | `src/engine/model.ts` | `placeOrder`, `transitionOrder`, `initialMarkingTuple`, `isEnabledAt`, `fireMarking` — for animation stepping + state labeling. |
| Store | `src/state/store.ts` | `maxStates` (dial value), `analysisVisible`; doc/positions/mode/marking. Graph-explorer visibility + animation state = #5 additive (C3). |
| Dashboard | `src/ui/AnalysisPanel.tsx` | Text/table rendering of reachability/deadlocks/bounds/liveness/SCC/invariants. The graph explorer is a NEW view (sibling, not replacement) — the tables stay (C4). |
| Flow projection | `src/ui/flow.ts` | Pure React Flow projection for the EDITOR canvas. The explorer needs its own projection (states/transitions, not places/transitions) — new pure function (C5). |
| Examples | `src/examples.ts` | 3 canonical shared examples via `?raw` (the ONLY allowed cross-boundary coupling). Gallery needs more entries + descriptions (C6/C7). |
| Vectors | `shared/petri-net/conformance/analysis-v1/` (9 .json) | Each has a schema-valid canonical `net` doc — a ready-made gallery source without touching LOCKED shared/examples (C7). |
| Conformance suite | `tests/engine/conformance.test.ts` | ALREADY wired into Vitest (feature_035 §10.3; 10 tests). "Runner wiring" re-examined in C8. |
| Independence | `scripts/check-independence.mjs` + `tests/independence.test.ts` | `ALLOWED_OUTSIDE = "shared/petri-net/examples/"` — any new cross-boundary `?raw` import (e.g. conformance nets) needs an allowlist decision (C7). |
| Toolchain | package.json | deps: @xyflow/react, react, react-dom, zustand. D2 names cytoscape.js/elkjs for graph viz — new-dep decision (C9). |

## 3. Deliverables → work breakdown (what "done" means per roadmap item)

### 3.1 Reachability-graph explorer (auto-layout) — the core deliverable
A new view rendering the reachability graph of the current net from M0, with the vector's `max_states` dial semantics:
- **Nodes** = reachable markings (labeled `M0`, `(1,0)` etc. — pin exact label format in Design; C2/C5), styled by **SCC component** (per-state color) and **deadlock** (distinct highlight) — the liveness/SCC views fold in here.
- **Edges** = transitions between states, labeled with the transition name; multiple edges between the same states allowed (parallel transitions) — React Flow handles via distinct edge ids (`markingKey(source)::t::markingKey(target)` or index; pin in Design).
- **Auto-layout**: D2 locked "reachability graph viz uses cytoscape.js/elkjs auto-layout (feature 5)" → **elkjs** (layout-only engine, pairs with existing React Flow renderer) is the D2-faithful choice; hand-rolled deterministic layered layout is the zero-new-dep alternative (needs a note; see C9).
- **No-overclaim (D10)**: `complete:false` graphs render a persistent truncation banner + the dangling-edge/partial-state visual is distinct; liveness/SCC verdicts stay unknown-styled (AnalysisPanel badge semantics reused).
- Recomputed like the dashboard: derived `useMemo` over `toNet(doc)` + `maxStates` (B12 pattern) — never stored in the document.

### 3.2 Firing-sequence animation
- User selects a target state in the explorer → `firingSequenceTo(reach, target)` → the explorer shows the sequence (e.g. `t1 → t2 → t3`).
- **Play** drives a step animation: for each transition in sequence, highlight it in the EDITOR canvas (or a preview strip), fire it via `net.fireMarking` (engine-pure — the library semantics, not a UI simulation), and update the displayed marking; **Reset** returns to M0; **Step** advances one transition.
- Animation state = UI-local or store additive (C3); must not corrupt the document; works from M0 by definition (`firingSequenceTo` returns M0-rooted sequences).
- Success criterion (PROJECT.md): "v3 graph explorer animates `firing_sequence_to` results."

### 3.3 Liveness/SCC views (in the explorer)
- SCC coloring per component (Tarjan result already engine-side); deadlock states distinct; liveness per-transition rendered in the explorer legend/toolbar (reusing `transitionLiveness` on the same `complete` graph; truncated ⇒ ❓ per D10).

### 3.4 Conformance-suite runner wired into Vitest
- **Already wired**: `tests/engine/conformance.test.ts` runs inside `npm test` (Vitest) and reads the 9 vectors. The D8-locked "runner wiring" is thereby satisfied in substance by feature_035's delivery (C8). Remaining formality: a **regeneration workflow** npm script (`npm run conformance`: `uv run python scripts/generate-vectors.py` → byte-identical check → `npx vitest run tests/engine/conformance.test.ts`) so the corpus can be extended + re-verified deterministically, plus (optional) extending the corpus with gallery nets — Design pins scope.

### 3.5 Example gallery
- A gallery panel (grid of cards: name + description + load button) replacing/augmenting the Examples dropdown (C6).
- **Sources**: (a) the 3 canonical shared examples (existing `?raw`); (b) the 9 conformance-vector nets (schema-valid canonical docs already on disk) as gallery entries — no LOCKED shared/ edits (C7). Gallery metadata (description strings, display order) is studio-local (`src/examples.ts` or a new `src/gallery.ts`), NOT format data.
- Load = existing `loadExample`/`importJson` path (validated import; on success lands in edit mode).

## 4. Findings (traps/decisions the design must pin)

- **C1 — Engine is done; UI is the feature.** Any `engine/*.ts` change in #5 is a regression risk and scope creep. Design must list `engine/*.ts` as UNCHANGED.
- **C2 — `markingFromKey` is private.** The explorer needs marking arrays from `markingKey`-keyed structures (edge targets) for labels/click handlers. Design: export it from analysis.ts (one-line additive) or re-derive locally in the explorer projection. Favor exporting (single source of truth, mirrors `markingKey`); note the empty-marking gotcha (TA-pinned at analysis.ts:31).
- **C3 — Explorer/animation state home.** Follow B12 precedent: analysis-derived state stays in components; only VIEW VISIBILITY + animation control (playing/paused, current step, selected target) are store/UI state. `graphVisible` toggle mirrors `analysisVisible`; animation can be component-local (`useState`/`useRef` timer) since it is ephemeral and derived from a fixed sequence. Design pins which; keep `maxStates` as THE shared dial between dashboard + explorer (single source of truth for truncation semantics).
- **C4 — Explorer is a sibling view, not a replacement.** AnalysisPanel tables remain (they are the no-overclaim dashboard; the graph is a visualization of the same data). Toggle: a "Graph" button next to "Analyze" (or a tab within the analysis panel — Design picks; keep it cheap and additive).
- **C5 — Explorer projection is a new pure function.** Mirror `flow.ts`: `reachabilityGraph` → React Flow nodes/edges with SCC/deadlock styling inputs. Purely testable in Vitest (node ids, labels, edge ids, style flags) — the primary RED target (C10).
- **C6 — Gallery vs dropdown.** Replace the `<select>` with the gallery panel, or add a "Gallery" toggle — Design picks. The dropdown is a v1 element; replacing it wholesale is additive-free if `loadExample` stays the load path.
- **C7 — Gallery source & independence allowlist.** Reusing conformance-vector nets as gallery entries requires importing `shared/petri-net/conformance/analysis-v1/*.json?raw` — the independence lint `ALLOWED_OUTSIDE` currently allows only `shared/petri-net/examples/`. Two options: (a) extend the allowlist substring to the conformance dir (one-line `check-independence.mjs` edit + comment), (b) bundle gallery nets as studio-local copies in `src/examples.ts` (duplicates data; violates "one spec, one source"). Favor (a) — the conformance dir is D5-locked contract data already in `shared/`, and the `?raw` import is the established coupling mechanism. `shared/META.md` DIR_PETRI_NET already names the conformance dir. (Also update the independence docblock.)
- **C8 — Conformance "runner" disposition.** Feature_035 already ships the Vitest suite; D8's runner requirement is substantively met. #5's value-add: `npm run conformance` regeneration script (uv → byte-identical → suite) + documented extension path. Do NOT rebuild the runner. (Record this disposition so the locked D8 doesn't get re-litigated at Testing.)
- **C9 — Layout library.** D2 names cytoscape.js/elkjs. **elkjs** (pure layout, ~no runtime cost, pairs with existing React Flow) is the D2-faithful, lowest-footprint choice: `elkjs` layout engine + React Flow renderer for the explorer. cytoscape.js would add a second full rendering stack — heavier, not needed. Hand-rolled layered layout keeps zero-new-deps but re-litigates the D2 stack pick (needs a re-lock note) and risks layout quality on large graphs. Recommend elkjs; Design pins the npm install (network) + determinism (ELK is deterministic given identical input — same graph ⇒ same layout; verify in a test or accept visual-only determinism; do not gate conformance on layout bytes).
- **C10 — TDD mismatch (A11 precedent).** `omt_tdd` is pytest-shaped; runner is Vitest. Declare in Programming scope; manual red→green with pasted evidence (feature_034/035 precedent). Primary RED targets: explorer projection (pure), animation sequence stepping (pure), gallery metadata (pure), store additive cases.

## 5. Capability → implementation map (for design)

| Capability (locked roadmap) | Implementation |
|---|---|
| Reachability-graph explorer | `src/ui/GraphExplorer.tsx` (new): derived `reachabilityGraph(maxStates)` → projection (C5) → React Flow canvas with elkjs layout (C9); truncation banner (D10) |
| Auto-layout | elkjs layered layout (C9) |
| Firing-sequence animation | Select state → `firingSequenceTo` → sequence strip + play/step/reset via `net.fireMarking` stepping (3.2); component-local animation state (C3) |
| Liveness/SCC views | SCC-color per node + deadlock highlight + per-transition liveness legend (3.3); same-graph semantics as AnalysisPanel (never re-explore) |
| Conformance runner wired into Vitest | Already shipped (C8); add `npm run conformance` regeneration script |
| Example gallery | `src/ui/Gallery.tsx` (new) + `src/examples.ts`/`src/gallery.ts` metadata + conformance-vector net imports (C7) |
| No-overclaim (D10) | Explorer reuses badge/truncation semantics; incomplete graphs visually distinct |
| Tests | Vitest: projection, animation stepping, gallery metadata, store additive; conformance + independence stay green; sentinel bridge |
| Independence | `check-independence.mjs` allowlist (a) if C7(a) |

## 6. Open decisions for Design

1. Explorer placement: panel below canvas (sibling to AnalysisPanel) vs tab within a combined analysis view vs full-screen overlay. (Recommend: sibling panel toggled by a "Graph" button — cheapest additive, mirrors `analysisVisible`.)
2. Node label format: `M0`, `(1,0)` tuple text vs `p1=1, p2=0` named form vs both (short label + tooltip). (Recommend: `M0` for initial + `(1,0)` tuple text; tooltip with named form.)
3. elkjs vs hand-rolled layout (C9). (Recommend elkjs — D2-faithful.)
4. Gallery: replace dropdown vs toggle panel; include conformance-vector nets? (Recommend: keep dropdown OR add "Gallery" toggle; include vector nets via allowlist (a).)
5. Animation rendering surface: animate in the editor canvas (simulate-style highlighting) vs a preview strip inside the explorer. (Recommend: preview strip + fire in the editor canvas when mode=simulate; strip-only otherwise — cheapest, no mode coupling.)
6. Animation state: component-local vs store (C3). (Recommend component-local; only `graphVisible` in store.)