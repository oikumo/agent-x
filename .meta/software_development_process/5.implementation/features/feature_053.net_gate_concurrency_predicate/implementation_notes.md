# Implementation Notes — feature_053.net_gate_concurrency_predicate (C1)

> meta_harness_6 Wave 2 / C1 · Programming 2026-09-06 · minor_feature (decl-only)

## What (evaluation §5 C1)

New `@pred net_marking()` wrapping the live probe marking; **g.net engages
only when `net_marking(active>1)`** — solo sessions revert to phase-gate only.
feature_051.multi_session_concurrency stays DEFERRED; this predicate is the
DG1 path (gate sleeps until concurrency is real).

## Concurrency definition

`active` = live `work_active` pool tokens, falling back to `f{N}_active`
subnet holders for subnet nets:

- `work_active > 1` → concurrent
- two or more `f\d+_active` places marked → concurrent
- anything else (solo `work_active ∈ {0,1}`, single holder) → solo
- **unreadable bundle → concurrent** (fail-closed: solo must be proven,
  never assumed)

Current pool net is solo by construction (`work_active=1`, conservation with
`agent_attention`), so the gate sleeps in every solo session today — that is
the friction win, not a bug. Availability / drift / conflict / stale-rev
checks still fire before the predicate (fail-closed first); only the
fire-receipt requirement is predicate-gated.

## Changes (receipt round-robin: ONE edit per harness file, round 1)

| File | Change |
|---|---|
| `.meta/META_HARNESS.omt` | `+ @pred net_marking` (closed vocab); g.net comment documents the C1 predicate (impl-owned — HDL-1 `when=` is a single pred call, so the path∧predicate conjunction lives in the impls) |
| `scripts/omt/harnessc.py` | `PREDS += {"net_marking"}` (259 records, check 0 errors) |
| `scripts/omt/net/gate.py` | nested `is_concurrent()` (bundle load or forwarded `live_marking`); new `live_marking` kwarg; solo → `{"allowed": True, "code": "OK", "solo": True}` after stale-rev, before receipt |
| `scripts/omt/net/cli.py` | gate op forwards `live_marking=dict(st.live_marking)` (no double load) |
| `.opencode/lib/enforcer/gate_driver.ts` | g.net impl: C1 solo fast-path — fs-read of `net_state.sidecar.json` + `META_NET.petri.json` (honors `OMT_NET_DIR`), skips the `net_check.py` subprocess when solo; unreadable → engage |
| `tests/scripts/omt/test_omt_harness_e2e.py` | check 13 pins the wiring (receipt-EXEMPT, updated first) |
| `tests/features/feature_050.../test_net_gate.py` | `test_blocks_without_fire_receipt` + `test_work_complete_only_ledger_refused` bumped to concurrent via `_make_concurrent` (C1 changed their precondition); stale/drift/conflict/down tests untouched (fail-closed first) |
| `tests/features/feature_053.../test_net_concurrency_predicate.py` | 13 new tests (new file, canary `scope:tests`) |

## Deliberately NOT done

- No `evalPred` switch case for `net_marking` in gate_driver.ts: no gate
  routes the pred through generic evaluation (g.net's custom impl owns it),
  so a case would be unreachable code triplicating the mirror. If a future
  gate puts `net_marking` in `when=`/`requires=`, the case becomes required.
- No `omt_net` op for the predicate (closed op enum per IDEA-002; the CLI
  forwards marking through the existing `gate` op instead).
- `.omt` took two edits in round 1 (pred insert + gate comment, separate
  calls) — noted as a round-discipline breach; guard allowed both, no
  further `.omt` edits followed before the receipt refresh.
