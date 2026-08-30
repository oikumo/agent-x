# Test report — feature_039.adaptive_net_engine (meta_harness_concurrent)

> Date: 2026-08-30 · minor_feature (declaration-only artifact; tests live in `tests/scripts/omt/test_net_*.py` + sentinel `tests/features/feature_039.adaptive_net_engine/`) · PROJECT.md D1–D18, IDEA-002 v4 §5.0/§5.1 · Resumed from `.sandbox/pause_2026-08-30b.md`

## Verdict

**COMPLETED.** The harness-owned Petri-net engine (`scripts/omt/net/`) passes all 9 shared conformance vectors (parity vs the shipped `src/agentx/model/petri_net/` spec, zero runtime import — D2); the three-file net-bundle store (`state.py`) persists atomically with rollback; the single `omt_net` tool ships the v4-canonical closed op enum with `probe`/`fire`/`invariant` implemented and `splice`/`sync`/`synthesize` reserved as clean not-implemented envelopes (bootstrap ordering §5.1). Full sentinel **1703 passed, 0 failures**; harnessc build+check 0 errors; e2e receipt refreshed; drift pins 12/12.

## Red→green cycles (manual; minor_feature → tdd_mode:false)

| Cycle | Target | Tests | Evidence |
|-------|--------|-------|----------|
| 1 | Engine (`errors`/`model`/`analysis`/`io`/`conformance`) | 19 (11 conformance + 8 engine) | 9 vectors byte-parity + corpus + summary; io golden byte round-trip ×3; D2 no-agentx-import static scan |
| 2a | State store (`state.py`) | 7 | bootstrap ×2, fire ×2, atomic rollback, name rebase, revision mismatch |
| 2b | CLI (`cli.py`) — **this session** | 11 | RED observed (module absent) → GREEN 11/11 in 0.09s |

Cycle 2b contract (`tests/scripts/omt/test_net_cli.py` IS the spec): one JSON envelope/stdout, exit 0/1; bootstrap-ordered `net_not_bootstrapped`; probe marking+enabled+advice (deadlocks `[[0,1]]`, bounded, place invariants `[[1,1]]`, max_states default 1000); fire delegating to `state.fire` (revision bump, `net_fire` ledger, `transition_not_enabled` clean fail); invariant place/transition invariants + live-marking hold + net↔ledger drift (`harness.net.drift.jsonl`, exit stays 0 on drift); reserved ops `not_implemented` naming feature_040; argparse rejects unknown ops (exit 2).

## Registration round (one e2e receipt per edit, round-robin discipline)

- `.meta/META_HARNESS.omt` (2 edits, receipt refreshed between): `@budget tool_schemas` 1280→1536 + `@budget tool_args` 1792→2048 (deliberate, commented); `@tool omt_net perm=allow args="op,transition?,reasoning?,session?,max_states?" tags="CMD_NET"`.
- `.opencode/plugins/omt_net.ts` (new): thin proxy → `uv run scripts/omt/net_check.py <op>` (tdd_hats.ts pattern; SDK array-coercion guard; envelope pass-through incl. non-zero exits; description via `irToolDescription` R8).
- `harnessc build` OK — **253 records → 5 projections** (IR + opencode.jsonc perm block + AGENTS.md `{n_tools}` 9→10); `check` **0 errors** (tool_schemas 1489/1536, tool_args 1834/2048).
- `tests/scripts/omt/test_omt_harness_e2e.py` `HARNESS_FILES` +10 (net package ×9 + plugin) — receipt-exempt; receipt refreshed after.
- `tests/scripts/omt/test_omt_docs_drift_pins.py` `WORK_BUDGET` 5632→6144 synced to `.omt @budget work_md` (stale from the previous session's bump — same-session fix).

## Live smoke (`uv run scripts/omt/net_check.py`, OMT_NET_DIR sandbox)

| Op | Envelope |
|----|----------|
| `probe` (no bundle) | `{"ok": false, "error": "net_not_bootstrapped", …}` exit 1 |
| `probe` | `{"ok": true, "revision": 0, "marking": {"p1":1,"p2":0}, "enabled": ["t1"], "advice": {"deadlocks": [[0,1]], "bounded": true, "place_invariants": [[1,1]], …}}` |
| `fire --transition t1 --reasoning smoke --session smoke` | `{"ok": true, "revision": 1, "marking": {"p1":0,"p2":1}}` |
| `invariant` | `{"ok": true, "place_invariants": [[1,1]], "transition_invariants": [], "live_marking_invariants_hold": true, "drift": {"drifted": false, "net_revision": 1, "ledger_revision": 1}}` |

TS plugin note (GOTCHA_TS_NO_RELOAD): `omt_net.ts` takes effect in the next opencode session; the CLI path is verified directly.

## Suite numbers

- `tests/scripts/omt/test_net_*.py`: **37 passed** (11 conformance + 8 engine + 7 state + 11 CLI).
- Sentinel `tests/features/feature_039.adaptive_net_engine/`: **2 passed** (structural floor + subprocess re-execution of the 37 — feature_036 precedent; module-local fixtures rule out plain re-export).
- Full sentinel `uv run pytest`: **1703 passed, 0 failed** (baseline 1664 + 37 + 2).
- Drift pins **12/12** · e2e **1 passed** (receipt covering the new files).

## Deferred (per FEATURE.md)

- `splice`/`sync`/`synthesize` implementations → feature_040/042 (reserved envelopes verified here).
- `omt_complete`-exit drift-check hook (D7 cadence) → feature_040/041 (the `invariant` op itself shipped + tested here).
- Subnet overlay population (`f{N}_` prefixes, boundary ports) → feature_040.
