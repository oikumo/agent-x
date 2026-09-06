# Operation Spec 001 — g.net gate

> feature_050 · Design → Programming contract · 2026-09-05

## Op: `g.net` (order 35, BLOCK, skip_ok=false, break-glass scope:all expiring 8h only)
- **Inputs:** tool call {tool, path, operation}, session ledger, net revision.
- **Pre:** `probe` → enabled contains required transition (`work_start` or `f{N}_start` for src/tests/harness-surface); `invariant` → drifted==false and conflicts==[]; `fire --expected-revision HEAD` must succeed (records `net_fire` receipt, 8h window).
- **Post:** on success attach `net_fire:{transition, rev, ts}` to ledger; on fail emit `ERR_NET_NOT_ENABLED / ERR_NET_STALE_REV / ERR_NET_DRIFT_CONFLICT / ERR_NET_DOWN` and BLOCK.
- **Fail-closed:** net-down/unknown/IR-error → BLOCK (invert current fail-open for this gate only); break-glass via `omt_skip{scope:all}` with reason + expiry + audit to `harness.net.drift.jsonl`.
- **Interactions:** runs after g.tests:30, before g.phase:40; receipt-gate (20) still requires fresh e2e for 2nd harness-surface edit; think/kb gates unchanged.

## Op: `fire hardening`
- stale-rev check on ALL ops (extend feat_046 OP_ARGS whitelist); `fire` adds conformance regression (cap/ invariants); exit 1 on TransitionNotEnabled/Unknown/NotBootstrapped/stale.

## Op: `WORK.md canonical`
- `sync net_to_md` renders Tasks block; `harnessc check` errors on hand-drift (like work_done_max).

## Observability
Every BLOCK logs {gate, reason, rev, marking, conflicts} to ledger + drift jsonl; dashboard shows g.net BLOCKs.
