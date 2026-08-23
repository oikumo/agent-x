# Test report — feature_034.studio_v1_editor

> Date: 2026-08-23 · Phase: Testing · Design: `4.design/features/feature_034.studio_v1_editor/design_001_studio_v1_editor.md` (+ `operation_spec_001`) · Impl: `5.implementation/features/feature_034.studio_v1_editor/implementation_001_manual_cycles.md`

## Verdict

**SHIP.** v1 scope (PROJECT.md v1.1 LOCKED, roadmap #3) implemented and verified: `tools/petri-net-studio/` standalone Vite+React+TS app — TS engine port (model + io, byte-parity with Python), zustand document/store layer, React Flow editor UI (edit/simulate modes, click-to-fire, enabled highlighting, import/export), independence lint, static build. Vitest **170/170**, `tsc --noEmit` clean, independence OK, `vite build` + static-serve smoke green. Zero `src/` (agentx) edits; agentx suite 1637 passed + 2 allowlisted known failures (below), zero regressions.

## DoD coverage (design §1 items 1–5)

| §1 | Item | Where proven |
|---|---|---|
| 1 | `npm run build` produces static `dist/` | Build output below: `dist/index.html` + 2 hashed assets; preview smoke 200/200/200 |
| 2 | Vitest green: model port (60), io port (59 + 3 golden), store smoke | Cycles 1–3 evidence below; final suite 170/170 |
| 3 | walking skeleton: draw → edit → fire → export → re-import identical canonical JSON | Store round-trip tests (`tests/state/store.test.ts`: export→import doc equality; fire/reset/mode transitions); UI covered by store tests + build per design §10 step 6 (no component-test mandate in v1); manual in-browser smoke user-verifiable |
| 4 | `node scripts/check-independence.mjs` passes | `independence OK: 12 files scanned, 36 imports checked` (exit 0); also asserted by `tests/independence.test.ts` under `npm test` |
| 5 | `harnessc check` clean with `tools` in root_allowlist; agentx pytest untouched/green | `harnessc: check OK — 250 records, 0 errors`; agentx suite below — zero `src/` edits in this feature |

## Manual red→green evidence (design §9.4 protocol — substitute for `omt_tdd` receipts, A11)

- **Cycle 1 (model) RED**: `npx vitest run tests/engine/model.test.ts` → `Test Files 1 failed (1) · Tests 60 failed (60)` (stub "not implemented (RED stub)").
- **Cycle 1 GREEN**: same cmd → `Test Files 1 passed (1) · Tests 60 passed (60)` (Duration ~0.9s).
- **Cycle 2 (io + examples) RED**: `npx vitest run tests/engine/io.test.ts tests/engine/examples.test.ts` → `Test Files 2 failed (2) · Tests 58 failed | 4 passed (62)` (stub; 4 passers = 3 schema-example validations + subclass test).
- **Cycle 2 GREEN (full suite)**: `npx vitest run` → `Test Files 3 passed (3) · Tests 122 passed (122)` (Duration ~0.7s).
- **Cycle 3 (store) RED**: `npx vitest run tests/state/store.test.ts` → `Test Files 1 failed (1) · Tests 46 failed | 1 passed (47)` (stub "not implemented (RED stub)"; passer = initial-state test).
- **Cycle 3 GREEN (full suite)**: `npx vitest run` → `Test Files 4 passed (4) · Tests 169 passed (169)` (Duration ~1.1s).
- **Cycle 4 (independence) RED**: `npx vitest run tests/independence.test.ts` → `Test Files 1 failed (1) · Tests 1 failed (1)` (spawn ENOENT — script not yet written).
- **Cycle 4 GREEN (full suite)**: `npx vitest run` → `Test Files 5 passed (5) · Tests 170 passed (170)` (Duration ~1.2s).

Environment fixes during RED/GREEN (TA-pinned): jsdom rewrites `import.meta.url` → `// @vitest-environment node` docblock atop engine tests + independence test; `-10 ** 15` Python-ism → `-1e15` (JS forbids unary minus before `**`).

## Suite results

- **Studio Vitest (final, re-verified at Testing)**: `Test Files 5 passed (5) · Tests 170 passed (170)` — 60 model + 59 io + 3 golden-examples + 47 store + 1 independence.
- **Typecheck**: `npx tsc --noEmit` → clean (exit 0).
- **Independence CLI**: `node scripts/check-independence.mjs` → `independence OK: 12 files scanned, 36 imports checked` (exit 0).
- **Build** (`npm run build` = `tsc --noEmit && vite build`):

  ```
  dist/index.html                   0.40 kB │ gzip:   0.27 kB
  dist/assets/index-CpzIhfaZ.css   19.55 kB │ gzip:   3.66 kB
  dist/assets/index-CUV9Irhm.js   357.09 kB │ gzip: 114.25 kB
  ✓ built in 1.86s
  ```

- **Static-serve smoke** (`npx vite preview`): `GET /` → 200 · `GET /assets/index-CUV9Irhm.js` → 200 · `GET /assets/index-CpzIhfaZ.css` → 200. Shared examples bundled via `?raw` (`petri-net-json` format marker present in the JS bundle) — no runtime fs needed.
- **Harness**: `harnessc: check OK — 250 records, 0 errors` (`tools` in root_allowlist since A10).
- **Agentx suite**: `uv run pytest -q` → **1637 passed, 2 failed** — the 2 are `test_gate_no_tdd_allows_everything` / `test_gate_no_tdd_allows_tests`, both in `KNOWN_SUITE_FAILURES` (`scripts/omt/tdd/state.py`): TDD-gate probes reading the live 8h ledger, failing because feature_031's TDD entries (17:50–18:25 UTC) are still in-window; they pass again once the window clears. Zero `src/` edits in this feature ⇒ not regressions (feature_031 test-report precedent: same 2 tolerated while its session was live).

## Scope conformance (PROJECT.md v1.1)

- Files: all new under `tools/petri-net-studio/` (`src/engine/{errors,model,io}.ts`, `src/state/{document,store}.ts`, `src/ui/{flow,PlaceNode,TransitionNode,Inspector,App}.tsx/ts`, `src/{examples.ts,main.tsx,styles.css}`, `scripts/check-independence.mjs`, `tests/**`) + the A10 harness allowlist line. Nothing existing touched; no `src/` (agentx) edits; no `shared/` edits (contract LOCKED).
- D1 pure browser / static build ✅ · D2 React+TS+Vite+React Flow ✅ · D4 independent runtime (harness governs development only) ✅ · D5 format-only coupling: the ONLY cross-boundary imports are `shared/petri-net/examples/*.json?raw` (allowlisted substring in the independence check) ✅.
- Golden byte-identity: TS `netToJson(documentFromJson(example))` === on-disk bytes for all 3 shared examples — cross-impl parity with Python `io.py` verified WITHOUT Python.
- §11 non-goals honored: no analysis dashboard (#4), no reachability explorer/conformance runner (#5), no coverability, no current-marking snapshot in exports, no backend, no npm publish.

## Design-gap resolutions (Programming-time, consistent with pins — also in implementation_001)

1. **`addArc` op added** to document.ts: operation_spec_001 omits an arc-creation op, but design §7 pins the connect-drag gesture → `addArc(doc, source, target)` (V2/V3/V4-checked, weight 1); ALL doc mutation stays in pure ops (A8). TA-pinned.
2. **Import ⇒ edit mode**: op spec silent → import lands in `edit` with marking cleared; store-level simulate lock (A9) implemented as a guard in EVERY mutating action (toolbar hint alone insufficient). TA-pinned.
3. Minor: positions snap to integers on WRITE (add/move; design §7); selection cleared on mode switch + node/arc removal; `loadExample` unknown name → `importError`, returns false.

## Known limitations / caveats (recorded; no action — TA-pinned or docstringed)

- io.ts: A2 integer-like-key reorder caveat (layout extension values); integral-float acceptance diverges from Python strict-int (schema-correct; outside the pinned matrix).
- FORMAT.md §8.5 UTF-16≡code-point claim = erratum candidate (fails for astral-plane names; TS pins the code-point comparator = spec primary rule). Spec LOCKED — surfaced, no edit.
- UI has no component tests (design §10 step 6): covered by store tests + `tsc` + build; manual in-browser smoke remains user-verifiable.
- `omt_tdd` not used (A11 declared in the Programming scope): manual Vitest red→green with the pasted evidence above substitutes for receipts.
