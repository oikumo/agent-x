# Analysis 001: dashboard reuse surface + snapshot replay feasibility

> feature_043.meta_net_dashboard (major_feature, meta_harness_concurrent phase-2 2/3)
> IDEA-002 §6 + PROJECT.md roadmap #5: static-build dashboard reusing studio
> projection/animation/gallery over the harness net bundle.

## What the dashboard must show (locked scope, IDEA-002 §6 + D19/D20)

1. Live supervisor net graph (12-place pool net: 3 pool + 5 resources + 3 boundary + archive).
2. Deadlock highlight — structural blockage made visible (D20 conflict semantics).
3. Revision slider — step through revision → marking history (PROJECT.md "revision slider (snapshots)").
4. Pool/resource status — pending/active/done counts + capacity line (D19 menu data).
5. Static build only — no dev server, no live WebSocket (explicit non-goal).

## Reuse surface (all shipped, verified on disk this session)

| Need | Asset | Evidence |
|---|---|---|
| Net→ReactFlow nodes | `src/ui/flow.ts` `toFlowGraph(doc, positions, marking, enabled)` — places show LIVE tokens, transitions carry `enabled` | read 2026-09-05; used by App simulate mode |
| Node views | `PlaceNode.tsx` / `TransitionNode.tsx` (same `nodeTypes` map as App) | App.tsx:31 |
| Net engine client-side | `src/engine/model.ts` + `analysis.ts` (TS parity port, 9 conformance vectors green) — enabled/fire/deadlocks computable in-browser | tests/engine/ (6 files) |
| v1 parse | `src/engine/io.ts` — petri-net-json v1 (structure + M0) | io.test.ts |
| Slider UI pattern | plain `<input type=range>` (Gallery is an example grid, NOT a slider — no reuse there; animation.ts drives token flow, reuse TBD in design) | Gallery.tsx read |
| Build pipeline | `npm run build` (`tsc --noEmit && vite build`) → `dist/` + preview smoke (034–036 proven) | package.json |
| Test pattern | vitest (`tests/**`, 274 @036) + pytest sentinel bridge (`tests/features/feature_036.../test_studio_v3_graph_sentinel.py`: structural floor + `npx vitest run`, skips without toolchain) | bridge read |
| Independence fence | `scripts/check-independence.mjs` — src/ imports must resolve inside src/ (only `shared/petri-net/*` ?raw escapes) ⇒ snapshot JSON must live under `src/` | check read; `resolveJsonModule: true` in tsconfig |

## Slider data problem → replay design (key analysis finding)

`net_fire` ledger records carry NO marking (transition + revision only —
state.py:398-404), so history cannot be read off the ledger. But every
mutation primitive is replayable from record shapes already pinned on disk:

| Record | Replay op (reuse, no new engine) |
|---|---|
| `net_sync` bootstrap=true | reconstruct genesis skeleton (boundary + RESOURCE_PLACES M0=1, sync:1067-1086) |
| `net_splice` add | record carries full `mutation` → `_apply_add` + `rebase_marking` |
| `net_splice` remove / `net_disable` | record carries `mutation` + `token_policy` + `reroute` + `removed` (full structure for inverse replay) → scratch-`NetState` + `_remove_nodes` path |
| `net_splice` undo | record carries `undoes` revision pointer → apply inverse of the referenced record (same two cases as `_splice_undo`: add→forbid-remove, remove/disable→re-add recorded structure + live tokens) |
| `net_splice` repair / `net_sync` resync / `net_synthesize` | no state mutation → skip (emit no snapshot) |
| `net_fire` | `fire_marking` on the replay net |

Order = append order across the full ledger store (ALL archives + hot —
`read_ledger_net_records` reads hot + latest archive only, so replay needs its
own store walk). Fail-closed acceptance: replay final marking MUST equal the
live sidecar marking exactly, else the snapshot build refuses (mechanical
fidelity bound — no silent drift, D16).

## Out of scope (locked)

- GraphExplorer reachability reuse for the dashboard (elkjs layout cost; the
  slider already steps markings — document as follow-up, not v1).
- Live updates / WebSocket / dev server (IDEA-002 §6 static-only).
- `src/` edits of any kind (D1 — dashboard lives in tools/ + scripts/omt/net/).
- New `omt_net` op or @tool change (F5 — snapshot is a build script, not a tool
  registration; zero budget churn expected).
- Free-form goal synthesis (042 shipped templates-only; dashboard consumes).

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Old-format ledger records (039-era) missing replay fields | Fail-closed + golden test replays the REAL ledger store; gaps surface immediately in RED |
| R2 | Multi-page vite entry disturbs the editor bundle | Separate `dashboard.html` entry + own main; editor entry untouched; independence + build green both |
| R3 | Snapshot staleness (committed JSON vs live net) | Snapshot carries its revision; dashboard banners it; regen is one script run (preview-smoke pattern) |
