# Test Report — feature_055.gate_preflight (Wave 2/A4)

> meta_harness_6 · minor_feature · 2026-09-06 · suite 1902/0 (empty allowlist)

## Suite

`tests/features/feature_055.gate_preflight/test_gate_preflight.py` — 13 tests
(6 static pins + 7 bun probes on the REAL plugin, hermetic tmp root + real IR copy +
`OMT_LEDGER_PATH` pinned explicitly per the feature_051 gotcha).

## Static pins

| Test | Pins |
|---|---|
| `test_omt_tool_schema_carries_preflight` | `@tool omt_status` args `op?,tool?,path?,include_ledger?` + payload documents the ordered-gates contract |
| `test_clearing_actions_cover_every_gate` | **Completeness**: every `@gate` id in the SSOT has a CLEARING_ACTIONS entry (new gate w/o action = red suite) |
| `test_clearing_actions_consistent_with_msg_escapes` | g.think → omt_think + NOT skip-bypassable; g.tests → canary skip form; g.net → work_start; g.phase → omt_phase; g.receipt → e2e cmd; g.kb/g.nav → their tools; g.protect → ask the user |
| `test_gate_driver_decision_flags` | `fired?: boolean` + `stop?: boolean` on GateDecision (additive) |
| `test_status_plugin_guardrails` | no `TA:` literal (no self think-gate); no ledger writes; preflight branch precedes the lint subprocess call |
| `test_e2e_check_added` | e2e check 15 present (receipt-pinned wiring) |

## Bun probes (real omt_status plugin via `mod.default(...)` + `execute`)

| Scenario | Verdict |
|---|---|
| src path, empty ledger | rows `[g.protect†, g.receipt†, g.tests†, g.net, g.phase, g.think†, g.kb]` (†=fired:false when-miss); g.phase+g.kb WOULD BLOCK; first_blocker=g.phase; fired=3/n-a=4; after=[g.mvc(60), g.tdd_after(70)] with notes; output renders `clear: omt_phase{task_type, scope}` |
| src path, bug_fix phase (C2 integration) | g.phase+g.kb cleared by the ONE fast-path write → all clear, first_blocker=None |
| harness path (git-init'd tmp + real gate_driver.ts) | g.receipt FIRED+BLOCKED (git-dirty, stale receipt) AND g.think FIRED+BLOCKED; first_blocker=g.receipt (lower order wins) |
| tests path + canary skip | g.tests fires, allows, **halts_chain=true** — no later before-gate rows (stop flag honest); after=[] |
| search tool (grep) on doc path | ONLY g.nav fires and blocks; after=[] |
| op errors + protected path | path-less preflight → "path required"; op:"bogus" → "unknown op"; README.md → g.protect FIRED+BLOCKED, first_blocker=g.protect |
| default path intact | no op AND op:"status" alias → `📊 OMT++ STATUS` banner (live-model schema-fill safe) |

## Live verification

- `test_omt_live_opencode_guards.py::test_plugins_load_and_tools_execute` — real
  opencode run: plugin loads, model calls omt_status and completes. **Caught a real
  bug pre-ship**: with the original `op` describe (`"preflight"`), the live model
  filled `op:"preflight"` on a plain omt_status call → fixed via
  `"status (default) | preflight"` describe + accepted alias; re-verified green.
- Full suite: **1902 passed / 0 failed**, empty allowlist, e2e receipt refreshed
  (check 15 recorded).

## Guardrails confirmed

- g.think/g.protect semantics untouched (C2 exclusion respected; no changes to their
  @gate lines or impls).
- omt_q op:plan unaffected (GateDecision extension is additive; its 49-test group green).
- Budgets all green: tool_args 2291/2304 · tool_schemas 1716/1792 · nav_index 63826/64000.
