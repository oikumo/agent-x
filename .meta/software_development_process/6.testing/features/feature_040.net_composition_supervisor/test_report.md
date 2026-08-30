# Test report — feature_040.net_composition_supervisor (meta_harness_concurrent core 2/3)

> Date: 2026-08-30 · minor_feature (declaration-only artifact; tests live in `tests/scripts/omt/test_net_{splice,sync,cli}.py` + sentinel `tests/features/feature_040.net_composition_supervisor/`) · PROJECT.md D1–D18, IDEA-002 v4 §3/§5.0/§5.1/§11 · Resumed from `.sandbox/pause_2026-08-30c.md` (consolidated design P1–P10)

## Verdict

**COMPLETED.** `omt_net{op:splice}` ships all five modes — `add` (validate-all-then-apply on a deepcopy, arc direction by node kinds by keyword), `remove` (REBUILD from survivors, model is add-only D2; token policies `forbid`/`reroute`/`drain` with deterministic drain), `disable` (≡ remove-with-policy by `f{N}_` prefix + `kind:"net_disable"` with full structure for inverse replay + `overlay.disabled` archive), `undo` (inverse replay of the latest structural ledger record), `repair` (sidecar↔overlay revision realignment with missing-node validation) — and `omt_net{op:sync}` ships the §5.1 first-call bootstrap (boundary ports `feature_ready`=1/`resource_token`=1/`goal_satisfied`=0, NO supervisor transitions in v1) plus the deterministic reality scan (feature dirs + WORK.md tasks/projects) emitting a proposal that is NEVER auto-applied (D4). The overlay is derived at every `save()` (P10 — drift impossible by construction); every structure-changing op re-runs the 9 conformance vectors pre-save (P8); `omt_complete` gained the D7 fail-open drift hook; `synthesize` stays cleanly reserved → feature_042. Full sentinel **1736 passed, 0 failed**; harnessc build+check 0 errors; e2e receipt refreshed; drift pins 12/12.

## Red→green cycles (manual; minor_feature → tdd_mode:false)

| Cycle | Target | Tests | Evidence |
|-------|--------|-------|----------|
| 1 | Splice engine (`state.splice` + modes) | 24 | RED 33 failed (ops reserved/attrs absent) → GREEN; validate-all-then-apply (bytes unchanged on reject), conformance-gate failure blocks write + no ledger, token policies (forbid refuse/reroute move/drain consume+no-progress), disable archive, undo ×3, repair ×2, args ×3 |
| 2 | Sync (`state.sync` bootstrap + scan) | 9 | RED → GREEN same run; skeleton materialization, gate failure blocks bundle, checkbox M0 mapping, P7 template arcs, skip-existing, disable-missing-dir proposal, resync read-only, D4 applies-nothing capstone |
| 3 | CLI reserved-set update | 9 (suite) | `TestReservedOps` parametrize 3→1 (`synthesize`); message feature_040→feature_042 |

## Registration round (one e2e receipt per edit, round-robin discipline)

- `scripts/omt/net/state.py` (2 edits, receipt refreshed between): splice engine + `derive_overlay` (P10) wired into `save()` + sync scan helpers + `OMT_NET_FEATURES_DIR`/`OMT_NET_WORK_MD` hermetic overrides.
- `scripts/omt/net/cli.py` (1 edit): `RESERVED_OPS` → `("synthesize",)` (message → feature_042), splice/sync subparsers + dispatch, `SpliceError`→envelope code mapping, mutation JSON parse guard.
- `.opencode/plugins/omt_net.ts` (1 edit): args `mode/mutation/subnet/feature` (array-guard re-serialization), description splice|sync live / synthesize reserved→feature_042; OPS enum unchanged; stale TA todo removed.
- `.opencode/lib/enforcer/phase_gate.ts` (1 edit): D7 drift hook at `omt_complete` exit — spawn `uv run scripts/omt/net_check.py invariant` FAIL-OPEN (quiet/nothrow — tdd_check pattern); `ok && drift.drifted` → ⚠️ line; `net_not_bootstrapped` → silent; stale TA todo removed.
- `.meta/META_HARNESS.omt` (2 edits, receipt refreshed between): `@tool omt_net` args/description; `@budget tool_schemas` 1536→1792 + `@budget tool_args` 2048→2304 (deliberate, commented — splice args +15/+14 B over).
- `harnessc build` OK — **253 records → 5 projections**; `check` **0 errors** (budgets OK).
- `tests/scripts/omt/test_omt_harness_e2e.py` **1 passed** (receipt refreshed); drift pins **12/12**.

## Live smoke (`uv run scripts/omt/net_check.py`, REAL bundle — SSOT bootstrap, D16)

| Op | Envelope (truncated) |
|----|----------------------|
| `sync` (first call) | `{"ok": true, "bootstrap": true, "revision": 0, "conformance": {"vectors": 9, "ok": true}, "proposal": {"add_subnets": [feature_001 pending, feature_002 pending, …], "disable_subnets": []}}` — skeleton materialized from the real feature dirs + WORK.md |
| `probe` | `{"ok": true, "marking": {"feature_ready": 1, "goal_satisfied": 0, "resource_token": 1}, "enabled": [], "advice": {"bounded": true, …}}` |
| `invariant` | `{"ok": true, "live_marking_invariants_hold": true, "drift": {"drifted": false, "net_revision": 0, "ledger_revision": 0}}` → the `omt_complete` hook stays silent |

Proposal verified against reality: `feature_001.session_user_objectives_driven_by_Petri_Net` `[ ]`→pending (M0 `f001_pending`=1), P7 lifecycle-chain arcs exactly as designed. Proposal NOT auto-applied (D4) — net still holds only the skeleton.

## Suite numbers

- `tests/scripts/omt/test_net_*.py`: **68 passed** (24 splice + 9 sync + 9 CLI + 7 state + 11 conformance + 8 engine — feature_039 suites stay green under the derived-overlay `save()`).
- Sentinel `tests/features/feature_040.net_composition_supervisor/`: **2 passed** (structural floor + subprocess re-execution of the 42 canonical splice/sync/CLI tests — feature_039 precedent).
- Full sentinel `uv run pytest`: **1736 passed, 0 failed** (baseline 1703 + 24 splice + 9 sync + 2 sentinel − 2 reserved-parametrize shrink).
- Drift pins **12/12** · e2e **1 passed**.

## Deferred (per FEATURE.md)

- `synthesize` op (goal→net templates) → feature_042 (reserved envelope verified).
- Resource capacity places + `ports.resources` refinement → feature_041.
- `project.py` lifecycle-event auto-sync triggers → feature_041+.
- WORK.md net-projection render (md→net proposals) → feature_045.
