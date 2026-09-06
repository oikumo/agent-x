# Analysis 001 — Gotcha clusters + thought staleness (feature_058)

> meta_harness_6 Wave 4 E2+E1 · 2026-09-06 · minor_feature

## 1. Live state (measured 2026-09-06, net rev 57, HEAD 9bc0051)

- Thoughts index: 101 events (84 add, 10 remove, 7 verify), 50 distinct paths.
- Live grep: 76 TA: lines (repo-wide, excl. *.jsonl). omt_q risky_thoughts: 101.
- Index age: oldest add 2026-07-16 (51d), newest 2026-09-06. **>90d stale: 0.**
  E2's 90d threshold is a policy pin, not a current cleanup — the review op
  ships with an empty live result and is proven by hermetic tests with old fixtures.
- Gotchas: 17 `@doc gotcha.*` + 1 demoted `tdd.env_flaky_fixed` = 18 records.
  Budgets: tool_args 2271/2304 (33B), tool_schemas 1750/1792 (42B),
  nav_index 63900/64000 (100B), ir_json 19892/20480 (588B). All green.

## 2. Gotcha cluster map (E1 — 5 classes per evaluation §2)

| Cluster | Members (4/3/4/3/4 = 18 incl. demoted) | Root cause | Status after A1/F1/A3 |
|---|---|---|---|
| SDK-contract (4) | loader_exports, sdk_contract, live_binary, ts_no_reload | opencode plugin API coupling (DEFECT-A, args on input/output, direct .ts load, no hot-reload) | F1 (feature_052 version canary + live-binary probes) makes quiet failure LOUD. Survivors are inherent teachings — KEEP. |
| Test-isolation (3) | env_flaky_fixed (DEMOTED by A1), red_runnable, tdd_node | global ledger shared with live sessions; TDD node granularity | A1 (feature_051 hermetic OMT_LEDGER_PATH) root-caused the class. red_runnable + tdd_node are discipline pins — KEEP. |
| Receipt-discipline (4) | receipt_second_edit, receipt_round_robin, bugb_recipe, plugin_probe | content-git-status second-edit guard + probe recipes | Inherent to the receipt model (feature_050). bugb/plugin_probe are recipes — KEEP. |
| TDD-toolchain (3) | testlist_json, tdd_toolchain, red_runnable* | polyglot dispatch, prose fallback | feature_037 (prose fallback) + feature_038 (vitest dispatch) shipped the fixes. KEEP as pins. (*red_runnable counted here; tdd_node stays in isolation-discipline — either partition sums to 18 with env_flaky.) |
| Misc/discipline (4) | done_reachable, think_gated, tests_canary_shadow, plugin_ctx, write_large (5 with write_large; pick 4 + write_large as receipt-adjacent) | phase/canary/ctx mechanics | A3 (feature_056 expiry + tombstones) root-caused the canary_shadow class. think_gated is safety (NOT skip-bypassable). write_large is a tool-limit workaround. KEEP. |

Canonical partition used by the pin test (18 ids, each exactly once):

- SDK (4): loader_exports, sdk_contract, live_binary, ts_no_reload
- ISOLATION (3): env_flaky_fixed, red_runnable, tdd_node
- RECEIPT (4): receipt_second_edit, receipt_round_robin, bugb_recipe, write_large
- TOOLCHAIN (2+testlist=3): testlist_json, tdd_toolchain + plugin_probe (probe recipe rides toolchain)
- MISC (4): done_reachable, think_gated, tests_canary_shadow, plugin_ctx

No renames, no retags: cluster knowledge lives in THIS doc + `# E1:` comments
in the .omt (comments are parser-ignored → 0 nav_index cost). Demotion policy:
demote only when root-caused like env_flaky_fixed (A1); none of the 17
survivors meet that bar today — all stay GOTCHA.

## 3. E2 review design (budget-neutral, mirrors B1+B2 discipline)

- New op: `omt_think{op:review}` — read-only stale-thought advisor (like suggest).
- Reuses existing args only: path?, category?, query?, top? (no new describes).
  Fixed 90d threshold (STALE_AFTER_DAYS = 90, hardcoded + pinned; a future
  @var would cost nav+IR for zero current benefit).
- Semantics: alive adds (foldThoughtEvents) ∩ live grep hits, filtered by the
  existing args; stale = latest add/verify ts > 90d AND no newer verify.
  Records a think_consult (clears think-gate — it IS a consult) with the
  consulted file set. Output: N stale lines + exact one-call archive commands
  (`omt_think{op:remove, path, line}`) + re-verify pointer — the A3 dangling-list
  idiom, not auto-delete (safe direction; no destructive one-call).
- Cost: TS op describe +7B (`|review` in the op enum), @tool payload +19B
  (` | review(stale>90d)`), total tool_args 2278/2304, tool_schemas 1769/1792.
  No new @doc/@tool/@msg → nav_index untouched, IR +~30B. All green, no diet.

## 4. Acceptance

- `omt_think{op:review}` lists stale>90d with exact remove commands; empty on live repo (0 stale — correct).
- Hermetic tests with old fixtures prove listing, filtering, consult-recording, read-only (no index/ledger writes beyond consult), 90d boundary.
- Cluster pin test asserts the 18-id partition above (each id exactly once).
- harnessc check+build green, all 12 budgets green, e2e check 18, full suite green.
