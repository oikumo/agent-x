# Test report: feature_044.mined_behavioral_net (IDEA-004 v2, upward mining)

> Type: minor_feature · Phases: Analysis → Programming → Testing → Done
> Date: 2026-09-05 · Project: meta_harness_concurrent (optional phase-2, 3/3)

## Scope

Ledger→net behavioral mining via `omt_net{op:mine}` (the single D7-gated
extension of the closed op enum): `miner.py` α-variant (EXTRACT ledger store →
session-context attribution → directly-follows → causality/parallelism/choice →
observed fragment in the `m_` namespace) + intended-vs-observed drift report +
empirical invariants + reproducible manifest. Proposal-only (D4 — drafts
materialize only via splice, which runs the 9-vector gate + D20 cap check);
no revision bump; ledger-audited (`kind: net_mine`). Honest v1 limits kept:
mined = observed (never normative), attribution heuristic (flagged + counted),
corpus starts small, simplified α (one place per causal edge, duplicates
under-expressed). Everything pruned/skipped is surfaced, never silent.

## RED → GREEN (manual, tdd_mode:false)

- RED: new tests/scripts/omt/test_net_mine.py — 18 tests green on first run
  against the implementation (golden α case, attribution, seed-ts, window,
  proposal-only, invalid params, CLI dispatch, bootstrap ordering).
- GREEN rounds (harness surface, receipt discipline — one edit per file per
  e2e receipt, e2e ~0.7s): `miner.py` new (2 fix-up edits, each receipted) +
  recency/window addition; state.py `mine` + `_parse_mine_params` (one append);
  cli.py `_mine` + subparser + dispatch + header (receipted); omt_net.ts
  OPS/OP_ARGS/description (scripted, first touch); .omt @tool description;
  plugin_args pin (mine joins the --session group); harnessc build.
- Regression: tests/scripts/omt 415 passed + 1 stale-projection pin (fixed by
  the build) → 416/416 with the new suite; drift pins + plugin-args pins green.

## Dogfood (live SSOT rev51, read-only)

`mine --reasoning ... --feature feature_044.mined_behavioral_net` on the real
bundle: ok, revision still 51, pool_net true, places_after 26 →
would_exceed_cap true (draft stays a proposal — D20 holds). 61 cases, 1101
used / 894 skipped (seed_ts 1, no_case_after_attribution 893 — the measured
sparsity, now mechanically visible), attributed_support 378. Top observed
paths: tdd→complete ×13, phase[Analysis]→think_consult ×9,
phase[Done]→phase[Analysis] ×8 (the revisit loops IDEA-004 predicted),
project_link→net_sync ×8. Empirical place invariants: 3. Draft files written
(`META_NET.mined.petri.json` + sidecar + manifest, D14 runtime state, git-ignored).

## Numbers

- test_net_mine.py ×18 (golden relations + determinism + pruning + attribution
  + seed-ts + window + pool proposal-only + empty ledger + 8 invalid params +
  CLI live + bootstrap ordering)
- omt suite 416/416 green; harnessc 0 err (tool_schemas 1590/1792, tool_args
  flat 2148/2304 — zero-churn args reuse, --mutation/--reasoning/--session/--feature)
- live rev51 drift-free, NEXT unchanged (work_start)
