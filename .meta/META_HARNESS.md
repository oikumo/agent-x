# META_HARNESS — GENERATED STUB (retired corpus)

> **GENERATED — DO NOT EDIT.** The hand-maintained corpus was RETIRED in
> meta_harness_dsl R8 (OMT-HDL-1). The single source of truth is
> **`.meta/META_HARNESS.omt`** (OMT-HDL).
>
> - **Query:** `omt_nav` (op=nav|list_sections|cross_ref|quick_ref)
>   (answers carry `.meta/META_HARNESS.omt:<line>` source lines)
> - **Build projections:** `uv run scripts/omt/harnessc.py build`
> - **Drift test:** `uv run scripts/omt/harnessc.py check --verify-projections`
> - **Hand version (pre-R8):** `git show HEAD:.meta/META_HARNESS.md`

## State notes (post-R8, dated)

- **2026-08-01 (improvement001 / OPT-A):** AGENTS.md projection slimmed in
  `harnessc.py render_agents` — the 18-row Tools table (duplicated the
  system-prompt tool schemas, F33 double-payment) replaced by a one-line
  pointer (`omt_nav{query:"CMD_", tag_type:"CMD"}`). 4273 → 2941 B
  (~330 tok saved **every turn**); `agents_md` budget pin unchanged (5120 B).
  Verified: harnessc check 0 err/226 rec · --verify-projections no drift ·
  tests/scripts/omt 116/116 · full suite 1062 passed + 3 known feature_018.
- **2026-08-01 (improvement002 / OPT-B):** 16 RECURRING GOTCHAS relocated from
  the WORK.md scratchpad into nav-indexed `@doc gotcha.*` records
  (`omt_nav{query:"GOTCHA_"}`); scratchpad keeps a pointer + top-3 inline.
  WORK.md 12117 → 7767 B (~1100 tok saved **every session startup**);
  scratchpad 5692 → 1342 B; `@budget work_scratchpad` shrunk 6144 → 3072
  (test pin `SCRATCHPAD_BUDGET` updated in the same session). Corpus
  226 → 242 records. Verified: harnessc check 0 err · --verify-projections
  no drift · e2e receipt refreshed · tests/scripts/omt 116/116 · full suite
  1062 passed + 3 known feature_018.
- **2026-08-01 (improvement003 / OPT-M):** WORK.md DONE-narrative diet — 4
  completed-task narratives (3316 B) compacted to one-liners + pointers per
  the new `CONV_WORK_DONE` convention record (`@doc conv.work_done`;
  WORK.md Convention section updated). WORK.md 7767 → 5899 B
  (~470 tok saved **every session startup**); `@budget work_md` shrunk
  14336 → 8192 (test pin `WORK_BUDGET` updated in the same session) so
  future DONE bloat is a compile error. Corpus 242 → 243 records.
  Verified: harnessc check 0 err · build + --verify-projections no drift ·
  e2e receipt refreshed · tests/scripts/omt 116/116 · full suite
  1062 passed + 3 known feature_018.
- **2026-08-01 (improvement004 / OPT-A):** AGENTS.md diet round 2 — the
  §12 Phase-Artifacts table, TDD/Navigation-Enforcement/Think-Anywhere
  paragraphs and the 5-row Quick Reference (all duplicated in nav-indexed
  `.omt` records) collapsed in `harnessc render_agents` to a 4-bullet
  "Process (full rules on demand via nav)" pointer block (§12 line stays
  data-driven from `@phase`; TDD cycle from `@fsm tdd`). AGENTS.md
  2941 → 2097 B (~210 tok saved **every turn**); `@budget agents_md`
  shrunk 5120 → 2560 (test pin `AGENTS_BUDGET` + stale docstring budgets
  updated in the same session); e2e assertion retargeted to the surviving
  think-gate pointer. Verified: harnessc check 0 err · build +
  --verify-projections no drift · e2e receipt refreshed ·
  tests/scripts/omt 116/116 · full suite 1062 passed + 3 known
  feature_018.
- **2026-08-01 (improvement005 / OPT-A):** per-turn injection diet —
  nav tip 489→155 B, TA-digest tail fold, AGENTS.md maintainer
  boilerplate trim (GENERATED header + ENF line). **−518 B every turn**;
  AGENTS.md 2097→1962 B. Verified: harnessc 0 err · e2e ✓ ·
  tests/scripts/omt 116/116 · full suite 1062 + 3 known feature_018.
  (State note recorded retroactively in the improvement006 entry batch.)
- **2026-08-01 (improvement006 / ALL OPT A–H, user mandate "do all at
  once"):** eight options, one session. (A) @tool schema diet 1484→1174 B;
  then (H) tool consolidation 18→7 registered tools (`omt_tdd`/`omt_nav`/
  `omt_think` op= dispatchers; phase/skip/complete/status kept) — schemas
  now **775 B/turn** (−48% vs loop start, budget 1024), plus ~11 fewer
  schema headers; all call sites, messages, guides, pins and live-test
  prompts updated. (B) WORK.md DONE rotation → `WORK_ARCHIVE.md` (pending
  + last-5 inline): 5899→3311 B/startup; `@budget work_md`→4096; `@var
  work_done_max` backstop; `CONV_WORK_ROTATE`. (C) harnessc
  `check_tool_seed_sync`: the 18→7 TS `irToolDescription` fallback seeds
  pinned ≡ .omt payloads (omt_phase drift class = build error). (D)
  projection-time `@derive` (PHASE_/TT_ from @fsm/TT_SET, SECTION from
  framed banners) — 36 hand records deleted; `@budget nav_index` 64000 +
  `ir_json` 20480 (the two largest projections were unchecked). (E)
  omt_status compact default (~1.5 KB→~350 B/call) + fixes: Feature
  Health 0% on non-artifact features, empty Valid-Next at Done. (F)
  **HDL-2**: `lib/enforcer/gate_driver.ts` — the before-hook chain is
  IR-driven (order=/tools=/when= via @pred registry; generic impl for
  pred-composed gates; specialized impls keep the exotic 20%; IR-missing
  fallback chain; order/tools/when/msg are .omt-only edits now). (G)
  repo-root hygiene gate (`@var root_allowlist` + `.meta/.omt *.bak`
  sweep; 3 stray ta_digest_*.py + thoughts.jsonl.bak removed). Verified:
  harnessc 0 err · build+verify no drift · tests/scripts/omt 116/116 ·
  e2e ✓ · live opencode smoke 2/2 (real binary, consolidated tools) ·
  full suite 1064 passed + 3 known feature_018 · driver/TDD probes green.
