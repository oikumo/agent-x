# Implementation Notes — feature_058.thought_review_gotcha_root_cause (Wave 4/E2+E1)

> meta_harness_6 · minor_feature · 2026-09-06 · Programming→Testing→Done

## What shipped

**E2 review** — `omt_think{op:review}` read-only stale-thought advisor
(hardcoded 90d policy, A3 dangling-list idiom: exact one-call
`omt_think{op:remove, path, line}` commands + verify pointer, never
auto-deletes). Reuses path?/category?/query?/top? — zero new args.
Records think_consult for shown files (IS a consult → clears think-gate).
Unknown-index thoughts read as NOT stale (fail-open). Live repo returns
0 stale (correct — oldest index add is 51d per analysis_001).

**E1 clusters** — 18-id partition (SDK 4 / ISOLATION 3 / RECEIPT 4 /
TOOLCHAIN 3 / MISC 4) in analysis_001 + `# E1:` comments in the .omt
(parser-ignored → 0 nav cost). No renames, no retags, no demotions:
A1/F1/A3 already root-caused the isolation/SDK/canary classes; the 17
survivors stay GOTCHA (demote only when root-caused, per env_flaky precedent).

## Surface (2 harness files + e2e, receipt round-robin; tests via canary skip)

1. **`.opencode/plugins/omt_think.ts`** (R1: review impl + seed/op-enum;
   R2: dispatcher case after refresh): `STALE_AFTER_DAYS=90`,
   `omt_think_review` (grep + foldThoughtEvents age join, consult, capped
   listing), dispatcher `case "review"`, seed `| review(stale>90d).`,
   op enum `|review`. Cost: tool_args 2271→2278 (+7B), tool_schemas
   1750→1770 (+20B), nav_index 63900→63920 (+20B via @tool record),
   ir_json +20B. All green, no diet.
2. **`.meta/META_HARNESS.omt`** (R1: @tool payload; R2: E1 comments):
   payload mirrors the TS seed (check_tool_seed_sync); comments carry the
   cluster map. 261 records, 0 errors.
3. **`tests/scripts/omt/test_omt_harness_e2e.py`** (check 18,
   receipt-exempt): pins the seed text, threshold, dispatcher case, enum,
   consult behavior, and cluster comment.

## Rounds & incidents

- **R1**: think.ts (impl+seed) + .omt payload → check green (budgets as
  predicted) + bun syntax OK → e2e refresh (check 17, no new asserts yet).
- **R2**: think.ts dispatcher + .omt comments → check green → 14/16 new
  tests (2 expectation bugs in MY tests, not impl: describe-count 9 not
  10 — the seed is not a describe(); `@tool ` substring count hits
  payloads — anchor to ^@tool) → 16/16 → e2e check 18 → build green.
- **Live-review note** (GOTCHA_TS_NO_RELOAD class): this session's MCP
  `omt_think` surface predates the change, so no live `op=review` call was
  possible in-session; the hermetic bun probes (fresh process, tmp root)
  assert the exact rendered lines instead — same recipe as feature_057's
  ceremony lines.
- **Dogfood note**: live review today = 0 stale (51d oldest). The toll it
  prunes is future-dated by design — the 90d pin is policy, not cleanup.
