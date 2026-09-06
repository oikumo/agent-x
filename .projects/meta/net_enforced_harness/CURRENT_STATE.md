# CURRENT_STATE: net_enforced_harness

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-09-06 (auto — feature_050.net_as_gate Done)

- shipped: major_feature · test report @ 6.testing/features/feature_050.net_as_gate/test_report.md
- logged by omt_complete; expand by hand if resume needs more.

---


## 2026-09-06 (feature_050 wrap-up COMPLETE — all fixes applied, suite green, Done)

### Done

- Resumed from `.sandbox/pause_2026-09-05c.md` runbook: omt_phase{Programming} → applied all specced fixes.
- Receipt round-robin reality: pause-time TA: additions (00:14:45–52Z) had pushed the 5 target files past the 23:17:18Z e2e receipt → refreshed the receipt FIRST (e2e run), then edits (2-site files gate.py/cli.py via uv-run transform; single-site via edit tool).
- All 5 specced test-failure root causes fixed (invariant flag, seed `?`, net_mine skip, skip_ok=false + rebuild, WORK.md render was already fixed at pause) + all 5 code defects (2 DEBUG blocks + rm gate_debug.log, _start-suffix receipt filter, cli gate op live wiring).
- NEW defect found+fixed: g.net impl crashed omt_q op:plan (synthetic ctx `env.$ = {}` → TypeError → fail-open on every @var.net_paths path) — dry-run guard added; U2/U11 green in both test_omt_q.py and feature_026 golden smoke.
- 043 dashboard snapshot regenerated (rev 51 → 53).
- +5 regression tests in test_net_gate.py (receipt filter ×2, CLI gate op ×3) — 11/11 green.
- Live gate verification: empty ledger → ERR_NET_DRIFT_CONFLICT (drift precedes receipt, post-fix semantics); work_start-only → OK; work_complete-only → ERR_NET_NOT_ENABLED (filter proven live); real repo → OK. g.net ran its own fixed code on this session's edits.
- Numbers: omt suite + 043 = 430 passed; full suite FINAL = 1844 passed / 0 failed (incl. both live opencode guard tests); harnessc build+check 0 errors (256 records); e2e receipt ×3.
- POST-DONE fix (user-directed, no pause): test_omt_live_opencode_guards.py::test_plugins_load_and_tools_execute was order-flaky — the live LLM sometimes called omt_nav first and R7 T3 defers the nav reminder off nav-tool results; assertions made order-agnostic per the sessionBootstrap contract (digest → first result, reminder → first non-nav result). Note: omt_phase/omt_complete records shadow a prior canary skip in getActiveUnlock (nav has hasNavUnlock for this; tests gate does not) — a fresh omt_skip{scope:"tests"} re-arms it.

### In progress / Blocked

- _(nothing — feature_050 Done)_

### Next

- Phase B: feature_051.multi_session_concurrency (meta_harness_concurrent) — DEFERRED by user 2026-09-05, do not start unless re-asked. Known Phase-B limitations listed in the 050 test report.

### Notes / context

- Net rev 53 (pending=2 active=0 done=5; pending = feature_001/002 agentx, D1 out-of-scope). Uncommitted 050 tree ready for user commit (git commit is agent-denied).
- TA: thoughts planted at pause remain in the source files as historical annotations (grep-is-truth index consistent).

---

## 2026-09-05 (pause — feature_050 wrap-up Phase A: diagnosis done, fixes specced, NOT applied)

### Done

- Full read-only diagnosis of the uncommitted feature_050 tree (12 files +334/−179, gate.py/test_net_gate.py new, g.net:35 live in IR).
- 5 test failures root-caused: (1) cli.py invariant subparser missing --expected-revision → plugin-args RED; (2) WORK.md Pool line stale rev52 vs net rev53 → harnessc RED — FIXED at pause via sync net_to_md (render now rev53); (3) omt_net.ts seed 1B off vs .omt payload (gate(path,session?) missing ?); (4) history.py replay raises on net_mine records → TestLiveGolden + 043 dashboard sentinel RED; (5) .omt g.net skip_ok=true vs design/fallback false (any session skip bypasses the net gate).
- 050 defects specced: gate.py DEBUG log block, gate_driver.ts DEBUG block, _has_recent_fire_receipt accepts ANY net_fire (must filter _start-suffix), cli.py gate op dead branches (drift/stale-rev/net-down unreachable).
- 6 TA: thoughts planted (gate.py, cli.py ×2, history.py, omt_net.ts, gate_driver.ts).
- Resumption doc: `.sandbox/pause_2026-09-05c.md` (12-step runbook, windows, artifacts).

### In progress / Blocked

- feature_050 wrap-up PAUSED at diagnosis→fix boundary (user confirmed). Phase B (feature_051.multi_session_concurrency, meta_harness_concurrent) DEFERRED by user decision.

### Next

- Resume: read `.sandbox/pause_2026-09-05c.md` → omt_phase{Programming, feature_050.net_as_gate} → apply the specced fixes (one edit per file per e2e receipt round).

### Notes / context

- Net rev 53 (pending=2 active=0 done=5, work_start enabled; pending = feature_001/002 agentx, D1 out-of-scope). Break-glass skips + fire receipt expire ~06:45Z; after that fire work_start before harness edits.
- e2e receipt fresh (23:17:18Z) → resume gets ONE edit per file, then re-run the e2e.

---


## 2026-09-05 (iter 0 — project created)

### Done

- Project home created (`project.py new`, state: draft).

### In progress / Blocked

- _(nothing)_

### Next

- <!-- the single next action -->

### Notes / context

- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.
