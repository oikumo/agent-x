# Implementation Notes — feature_055.gate_preflight (Wave 2/A4)

> meta_harness_6 · minor_feature · 2026-09-06 · Programming→Testing→Done

## What shipped

`omt_status{op:"preflight", tool, path}` — the ordered gates that WILL fire for a
prospective (tool, path) edit + the clearing action for each. One call instead of
N denials (kills the deny-learn-retry loop). Read-only, fast (short-circuits before
the default path's lint/tdd subprocesses), ledger-write-free.

## Surface (3 harness files + tests; one edit per file per receipt round)

1. **`.opencode/plugins/omt_status.ts`** (2 rounds: preflight block + arg-contract fix):
   - `CLEARING_ACTIONS` map (10 gates) — the concise "what unblocks this" layer;
     consistent with the `@msg` escape prose (meta_harness_5 #9), completeness-pinned
     by tests (a new @gate without an action fails the suite). NOT a `@gate clear=`
     attribute: nav_index headroom is 174B (Wave 3/B1 owns that budget).
   - `DRY_CAVEATS` (g.net only): the dry-run cannot shell out to the live net gate —
     surfaced on the row instead of silently under-reporting.
   - `buildPreflightCtx` — synthetic GateCtx mirroring the omt_q plan idiom
     (input={tool}, output={args:{filePath}} — BUG-A pin literal; env.$ non-function
     so shell-out impls take their dry path).
   - `preflightProjection` — before-chain via `runBeforeGatesDry` (real verdicts,
     chain-stop semantics included); after-chain as IR-projected NOTES (g.mvc/
     g.tdd_after verdicts depend on edit content — notes, not predictions).
     `whenPathMatches` — local path_in matcher for after-gate `when=` (non-path
     when= fires conservatively: a false "will fire" costs a hint, a miss a surprise).
   - `preflightLines` — the actionable checklist rendering (WOULD BLOCK → `clear:`).
   - **Arg contract (round 2, live-canary driven)**: `op` describe is
     `"status (default) | preflight"` and `op:"status"` is an accepted alias for the
     default. The first live run caught the model filling `op:"preflight"` when told
     to just call omt_status (the original describe `"preflight"` read like the only
     value) — the alias + steer fixed it; re-verified live.
2. **`.opencode/lib/enforcer/gate_driver.ts`** (think-gate consulted — the one TA:
   risk thought is STALE, both items shipped in feature_050 wrap-up): `GateDecision`
   gains optional `fired`/`stop` (additive; omt_q's `predicted_chain` mapping
   untouched). `fired=false` = when=-miss (not applicable — distinguishable from a
   passed gate now); `stop=true` = chain halt (g.protect override / g.tests).
3. **`.meta/META_HARNESS.omt`** (2 rounds): `@tool omt_status` args `op?,tool?,path?`
   + payload documents the preflight op with "(default: full status)". Seed synced.

## Key design decisions

- **Reuse over reimplementation**: before-chain verdicts come from the SAME
  `runBeforeGatesDry` sibling omt_q uses — no second gate-evaluation engine to
  drift against the live chain.
- **No "TA:" literal in omt_status.ts** — the preflight surface stays think-gate-free
  on itself (one less ceremony); pinned by test.
- **Preflight is op-dispatched inside omt_status** (not a new tool): §10-tool budget,
  perm-block unchanged, and the process-context tool is the natural home.

## Gotchas encountered (session-local)

- `relOf` import forgotten in round 1 (bun probe caught: `ReferenceError`) — the
  feature test suite's real-module probes pay for themselves immediately.
- `g.protect`'s `when=path_in(@protect.*)` does NOT match ordinary paths →
  `fired:false` rows (test recalibrated; a when=-miss is visible-but-n/a by design).
- `g.receipt` blocks only on **git-dirty** harness paths (`isGitDirty`): hermetic
  tmp probes must `git init` to exercise the staleness path.
- Live-model arg priming: an arg describe that names a single op value gets filled
  by the model even when the call intends the default — always give the default
  first and accept it as an alias.

## Budgets (after)

tool_args 2291/2304 (13B headroom — tightest yet) · tool_schemas 1716/1792 ·
nav_index 63826/64000 (174B) · ir_json 19794/20480 · all 12 green; check 0 errors
(259 records).

## Evidence

Full suite **1902 passed / 0 failed** (empty allowlist; 1887 + 13 new + 2 alias/default
probe variants) · live opencode guards green (plugin loads, model calls omt_status
correctly under the new schema) · e2e receipt refreshed (check 15:
"feature_055 A4: gate_preflight wired").
