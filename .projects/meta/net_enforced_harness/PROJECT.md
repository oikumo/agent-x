# PROJECT: net_enforced_harness — Net_Enforced_Harness

> Status: **active** · **v0.1 (2026-09-05)** — created by `project.py new`. Iterate freely (non-gated); spawn features with `new_feature.py "<name>" --type <tt> --project net_enforced_harness`; log sessions in CURRENT_STATE.md (newest on top).

---

## New Session Quick Start

> Petri net (rev 53) is the controlling gate for harness usage — no src/tests/harness edit without enabled-transition + fire.

**Next:** feature_050.net_as_gate is DONE (2026-09-06, wrap-up per `.sandbox/pause_2026-09-05c.md`). Phase B = `feature_051.multi_session_concurrency` (meta_harness_concurrent) — DEFERRED by user 2026-09-05; do not start unless re-asked.

---

## Summary (one line)

Enforce `omt_net` as SOLE permission-to-act for meta-harness: enforcer pre-tool `fire`-required, stale-rev + drift/conflict hard-block (Alt A Net-as-Gate).

---

## Purpose

### What this project is

Alt A Net-as-Gate: `g.net:35 BLOCK skip_ok=false` between g.tests and g.phase; `probe` enabled-check + `fire --expected-revision` required before `edit/write` to `src/tests/harness-surface`; `invariant drifted/conflicts!=[]` → BLOCK; `splice/sync` conformance-fail → BLOCK; WORK.md Tasks writable only via `sync net_to_md`; TS hot-reload fix + break-glass `omt_skip{scope:all}` with expiry+audit.

### What this project is **not**

Not a new net model (reuses rev 51 places/transitions); not user-task execution (that's feature_001); not dashboard-only (that's done in 043).

---

## Scope & success criteria

- Scope: `.opencode/plugins/omt_enforcer.ts` + `lib/enforcer/*` (g.net), `omt_net.ts` proxy (stale-rev all ops, fail-closed policy), `opencode.jsonc` (deny fire-bypass), `scripts/omt/net/*` (fire conformance regression), `harnessc check` (WORK.md canonical), e2e receipts.
- Success: `src/` edit without `fire(work_start)` BLOCKs with ERR_NET_*; stale-rev BLOCKs; drift/conflict BLOCKs (not logs); `uv run pytest` + sentinel green; dogfood rev+1 drift-free; break-glass logged + expiring.
- Non-goals: changing 12 places / caps (D2 add-only); auto-splice (stays D4 proposal-only until Phase 2).

---

## Status

- [x] feature_050.net_as_gate — DONE 2026-09-06: g.net:35 live (skip_ok=false, break-glass scope:all only), _start-suffixed fire-receipt filter, drift/stale-rev/net-down fail-closed in the live enforcer path, omt_q plan dry-run-safe. omt suite 430 green, full 1842 green (+2 allowlisted TDD-window knowns). Details: `6.testing/features/feature_050.net_as_gate/test_report.md`.

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — Alt A Net-as-Gate selected 2026-09-05:** user picked A over B/C/D at sandbox approval gate; rationale = full control > adoption ease.
- **D2 — Net owns state, gates own enforcement (D16 preserved):** net remains SSOT for marking/caps/invariants; enforcer adds g.net hook that queries net (no logic duplication).
- **D3 — Fail-closed + break-glass:** net-down = BLOCK + expiring scope:all skip with audit (vs current fail-open); TS reload fix mandatory.

---

## References

- <!-- anchors, feature dirs, evidence -->
