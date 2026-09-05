# Design 001: snapshot replay + read-only dashboard page

> feature_043.meta_net_dashboard (major_feature) — implements analysis_001.
> Two halves, one contract (the snapshot schema §2): Python replays the ledger
> into per-revision markings; the studio renders them. No new tool, no `src/`.

## 1. Python half — `scripts/omt/net/history.py` + `scripts/omt/net_snapshot.py`

- `replay(store) -> list[Snapshot]`: walk the FULL ledger store (ALL
  `ledger-*.jsonl` sorted + hot, append order = time order) filtering
  `kind.startswith("net_")`; genesis = first `net_sync` with `bootstrap=true`
  (skeleton: feature_ready=1, resource_token=1, goal_satisfied=0,
  RESOURCE_PLACES=1 — same literals as `sync`). Appliers reuse engine code
  (zero new semantics):
  - `net_splice` add → `_apply_add` + `rebase_marking` (mutation in record).
  - `net_splice` remove / `net_disable` → scratch-`NetState` + `_remove_nodes`
    with recorded `token_policy`/`reroute` (record carries `removed` full structure).
  - `net_splice` undo → resolve `undoes` revision in the replay log, apply the
    `_splice_undo` inverse (add→forbid-remove; remove/disable→re-add recorded
    structure + recorded live tokens).
  - `net_splice` repair / `net_sync` resync / `net_synthesize` → no state change, no snapshot.
  - `net_fire` → `fire_marking` (unknown/disabled at replay = fail-closed).
- Unknown kind/mode or any applier error → `SpliceError` (build refuses, D16).
- Each mutating record emits `{revision, kind, label, marking}` (marking =
  name→tokens dict). Revisions are record `revision` values (monotone by construction).
- `build_snapshot(base) -> dict`: live bundle load + `replay` + fail-closed
  gate `replay[-1].marking == live_marking` (exact dict equality) AND
  `replay[-1].revision == live revision`; pool counts + resource report +
  deterministic grid positions (§4); emits §2 JSON.
- `scripts/omt/net_snapshot.py`: thin shim (net_check.py pattern) —
  `uv run scripts/omt/net_snapshot.py [--out PATH]` writes the snapshot JSON
  (default `tools/petri-net-studio/src/dashboard/snapshot.json`).

## 2. Snapshot schema (the contract — both halves pin it)

```json
{
  "format": "meta-net-dashboard-snapshot", "version": 1,
  "net_revision": 49, "built_at": "<utc>",
  "place_order": ["agent_attention", "..."],
  "net": {"places": [{"name": "...", "tokens": 0}], "transitions": [{"name": "..."}],
           "arcs": [{"source": "...", "target": "...", "weight": 1}]},
  "positions": {"<node>": {"x": 0, "y": 0}},
  "pool": {"pending": 4, "active": 0, "done": 3},
  "snapshots": [{"revision": 44, "kind": "net_splice", "label": "add pool",
                 "marking": {"work_pending": 6, "...": 0}}],
  "skipped": [{"ts": "...", "kind": "net_fire", "mode": "", "revision": 1,
               "reasoning": "t"}]
}
```

- `net` reuses petri-net-json v1 shape (minus format envelope) so `io.ts`
  parses it unchanged; `marking` dicts convert via `placeIndex`.
- `label`: human short string (fire → transition name; splice → `mode` + feature).

## 3. Studio half — `tools/petri-net-studio/src/dashboard/`

- `blockedPlaces.ts` (pure, DOM-free): `(doc: NetDocument, marking: number[]) ->
  { blocked: string[], deadlocked: boolean }` — for each transition, if not
  enabled (engine `isEnabled` semantics via `model.ts`), collect its empty
  input places; `deadlocked` = no transition enabled. Vitest vectors incl. the
  live pool shape (attention-held ⇒ work_start blocked by agent_attention).
- `Dashboard.tsx` (read-only): own React root (no zustand, `useState` slider
  index only). Reuses `toFlowGraph(doc, positions, markingTuple, enabled)` +
  `nodeTypes {place, transition}` + engine enabled computation; blocked places
  get CSS class `blocked` (styles.css addition, additive only); header shows
  revision slider (`<input type=range>` over `snapshots`), pool counts,
  resources line, snapshot-revision banner (`net rev R, snapshot rev S`).
- Entry: `dashboard.html` + `src/dashboard/dashboard-main.tsx`; vite
  `rollupOptions.input` gains the dashboard page (editor entry untouched).
- `snapshot.json`: generated + committed (git-pinned like conformance vectors);
  regen = `uv run scripts/omt/net_snapshot.py`.

## 4. Deterministic grid positions (builder-side, no elkjs at runtime)

Rows by role (x = index*180, y = row*140): pool places y=0
(work_pending/active/done + archive_pool), resources y=140 (5 catalog),
boundary y=280 (feature_ready/resource_token/goal_satisfied). Transitions
interleave at x offsets. Unknown (non-pool) places append alphabetically —
pool nets are the target; pre-pool nets render unsorted-but-stable.

## 5. Tests (TDD testlist at Programming)

- pytest `tests/scripts/omt/test_net_history.py`: genesis vectors (add/fire/
  remove-reroute/undo-add/undo-remove/skip-kinds/unknown-kind-fails) on
  synthetic stores + LIVE golden (replay real store ⇒ final == live marking
  and revision; fail-closed mismatch vector via tampered copy).
- vitest `tests/dashboard/blockedPlaces.test.ts` + `snapshot.test.ts`
  (schema guard incl. version) + `Dashboard.test.tsx` (render: slider steps
  change token text; blocked class present when attention held).
- Sentinel bridge `tests/features/feature_043.meta_net_dashboard/
  test_dashboard_sentinel.py` (036 pattern): structural floor (files + vite
  input + snapshot keys) + scoped `npx vitest run tests/dashboard src/dashboard`
  + pytest replay-live golden (runs even without node).
- Manual (test-report evidence): `npm run build` green + `dist/dashboard.html`
  serves the snapshot (preview smoke), independence check green.

## 6. Non-goals (locked)

GraphExplorer reachability reuse · live updates · editor integration ·
new tool/budget · `src/` touches · free-form synthesis input.
