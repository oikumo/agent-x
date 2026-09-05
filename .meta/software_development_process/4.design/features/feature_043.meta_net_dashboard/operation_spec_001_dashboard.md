# Operation Spec 001 — feature_043.meta_net_dashboard: public operation contracts

> Phase: Design companion to design_001. Each operation: signature · pre · post/effects · errors. `M` = marking. Python engine (`scripts/omt/net/`) UNCHANGED — replay reuses `_apply_add` / `_remove_nodes` / `fire_marking` / `rebase_marking` exactly; TS engine (`engine/model.ts`, `analysis.ts`, `io.ts`) UNCHANGED — dashboard consumes read-only.

## scripts/omt/net/history.py — ledger replay (design §1)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `replay(store: Path) -> list[dict]` | `store` = ledger dir holding `ledger-*.jsonl` (sorted) + `ledger.jsonl`; append order = time order | Ordered snapshots, one per state-mutating `net_*` record: `{revision, kind, label, marking}` (`marking` = name→tokens dict). Genesis = first `net_sync` with `bootstrap=true` (skeleton literals = `sync` bootstrap). `net_splice` add → `_apply_add`+`rebase_marking`; remove/`net_disable` → scratch-`NetState`+`_remove_nodes` with recorded policy/reroute; `net_splice` undo → inverse of the `undoes`-revision record (`_splice_undo` cases); repair/resync/`net_synthesize` → skipped (no snapshot). Deterministic: same store → identical list. | `SpliceError` fail-closed on: unknown kind/mode, missing bootstrap, applier failure, fire of disabled/unknown transition |
| `build_snapshot(base: Path) -> dict` | `base` = live bundle dir (bootstrapped) | §2 schema dict. Fail-closed gate FIRST: `replay[-1].marking == live_marking` (exact dict equality) AND `replay[-1].revision == live revision` — mismatch raises `SpliceError("replay_mismatch")`. Pool counts via `pool_counts`, resources via `resource_report`, grid positions per §4. | `SpliceError("replay_mismatch", ...)`; `NetNotBootstrappedError` when unbootstrapped |

## scripts/omt/net_snapshot.py — build shim (design §1)

| Op | Contract |
|---|---|
| `uv run scripts/omt/net_snapshot.py [--out PATH]` | Thin shim (net_check.py pattern): `build_snapshot(net_dir())` → write pretty JSON + `{"snapshot_revision": R}` on stdout, exit 0. Default out = `tools/petri-net-studio/src/dashboard/snapshot.json`. Errors → `{"ok": false, ...}` envelope on stdout, exit 1 (CLI convention). |

## src/dashboard/blockedPlaces.ts — pure blockage (design §3)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `blockedPlaces(doc: NetDocument, marking: number[]) → { blocked: string[]; deadlocked: boolean }` | `doc` parses via `documentFromJson`; `marking` aligned to `toNet(doc).placeIndex` | PURE, DOM-free. For each transition: enabled per engine `isEnabled` semantics (input places hold ≥ weight); when disabled, collect input places with < weight tokens. `blocked` sorted code-point, deduped. `deadlocked` = zero transitions enabled. | none (pure over trusted engine types; empty net ⇒ `{blocked: [], deadlocked: true}`) |

## src/dashboard/Dashboard.tsx — read-only view (design §3)

| Op | Pre | Post / effects |
|---|---|---|
| `Dashboard` render | `snapshot.json` import (pinned §2 shape, `version: 1` asserted at module load — mismatch throws a descriptive error, fail-closed) | Own React root (no zustand): `useState` slider index over `snapshots` (default = last = live). Per index: marking dict → tuple via `placeIndex` → `toFlowGraph(doc, positions, tuple, enabled)` with the SHARED `nodeTypes`; blocked places get `blocked` className; header = revision slider + pool counts + resources line + `net rev R, snapshot rev S` banner. Slider stepping never writes store/doc/net (read-only by construction — no store import). |
| `dashboard-main.tsx` | `#root` in `dashboard.html` | `createRoot(...).render(<ReactFlowProvider><Dashboard /></ReactFlowProvider>)` (provider needed by `useReactFlow`-free canvas? — mirrors main.tsx provider shape; dashboard does not call screenToFlowPosition, provider kept for node-type parity) |

## dashboard.html + vite.config.ts — second page (design §3)

| Op | Contract |
|---|---|
| `dashboard.html` entry | Static page (title "Meta Net Dashboard", `<div id="root">`, module script to `src/dashboard/dashboard-main.tsx`); editor `index.html` untouched |
| `rollupOptions.input` extension | Gains `dashboard: resolve(dashboard.html)`; editor input byte-identical; `npm run build` emits both pages; `tsc --noEmit` covers `src/dashboard/` |

## styles.css — additive highlight (design §3)

| Op | Contract |
|---|---|
| `.blocked` place style | Additive CSS only (existing classes untouched): blocked place nodes get a distinct border (amber) + the dashboard legend documents it; no layout/structural CSS changes |

## tests/dashboard/ — Vitest suite (design §5)

| Op | Contract |
|---|---|
| `blockedPlaces.test.ts` | Pure vectors: single-blocked input; multi-transition dedupe+sort; all-enabled ⇒ `[]`/not-deadlocked; empty net ⇒ deadlocked; live-pool shape (attention 0 ⇒ `work_start` blocked by `agent_attention`) |
| `snapshot.test.ts` | Schema guard: committed `snapshot.json` parses, `version === 1`, `place_order` covers all marking keys, each snapshot marking covers `place_order`, revisions strictly increasing, last == `net_revision` |
| `Dashboard.test.tsx` | Render (testing-library + jsdom): header shows pool counts; slider `max` = snapshots-1; stepping the slider changes a place token text; blocked class present on the attention-held fixture |

## Global invariants

- **Engines untouched** — Python `model.py`/`analysis.py`/`io.py` and TS `engine/*` unchanged (no `export` additions needed: dashboard uses existing `toNet`/`placeIndex`/enabled paths).
- **Dashboard is read-only** — no zustand/store import, no doc/marking writes; the ONLY harness coupling is the generated `snapshot.json` (independence check: relative import inside src/, allowed).
- **Snapshot committed + rev-stamped** — regen is one script run; stale snapshot is banner-visible, never silent.
- **All sorts code-point (A3)**; Python formatting black-compatible (repo convention).
