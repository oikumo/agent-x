# Implementation notes — feature_059.harness_tiered_template (Wave 5 D1+D2+D3)

> major_feature · Programming done 2026-09-06 · design_001 + operation_spec_001

## What shipped (design §1–§4)

- **D1 `harnessc init --tier 1|2|3 [--with-net] [--profile P] <dir>`**
  (`scripts/omt/harnessc.py`: `TIER_*_DROP` tables, `filter_corpus_for_tier`,
  `check_template_vars`, `cmd_init`, `check_tree`, `_build_tree`,
  `_emit_omt_text`, `_tier_skip_payload`, `render_getting_started`,
  `_fallback_agents_md`, `_swap_root`). Tier capability:
  T1 gates {g.phase, g.protect, g.tdd_after, g.tests}, 5 core tools;
  T2 +{g.nav, g.think, g.kb} + 4 knowledge tools; T3 +{g.receipt, g.mvc},
  net only behind `--with-net` (DG3). All tiers validate 0 errors
  (prototype `/tmp/opencode/probe_tiers.py`, then `check_tree` self-check).
- **D2 `@var stack_profile`** (mvc_py|mvc_ts|none — a `@var`, NOT a new
  `@profile` kind: KINDS stays closed, zero compiler-kind churn) +
  `mvc_check.py --profile` (explicit flag beats repo `@var` beats mvc_py;
  `none` exits 0; `mvc_ts` = stdlib text/regex mode over `**/*.{ts,tsx}`,
  documented no-AST limitation).
- **D3 `render_getting_started` + `build` emission** (`GETTING_STARTED_PATH`,
  tier-3-full for this repo; gitignored, never committed).
- **`.omt`**: exactly 2 new `@var` (`template_default_tier`,
  `stack_profile`) + `root_allowlist += GETTING_STARTED.md`. No new
  doc/tool/msg → nav_index/tool_args/tool_schemas/agents_md untouched
  (pinned by `test_budget_pins.py`).

## Round discipline (receipt guard, 5 rounds)

- R1: `.omt` 2 vars → check → e2e refresh. R2: harnessc TIERS+filter+vars
  check (ONE script op) → check+build → tests → e2e refresh. R3 mega-round:
  harnessc init+render+dispatch+build-emit, mvc profile, allowlist,
  gitignore, e2e check-19 (one op per file, parallel) → check+build → e2e
  refresh. R4: esc-scope fix (harnessc) + ts-collect fix (mvc) → e2e refresh
  FIRST (no src edit without it), then edits. R5: TS seed sync → refresh.
- Incidents (all fail-closed, all caught by the feature's own pins):
  1. `_derive_prot_esc` needs every advertised skip scope backed by a
     skip_ok gate — T1 drops g.nav ⇒ emission rewrites omt_skip Scopes
     per tier (T1 `src|tests|all`) via `_tier_skip_payload` (prototype
     derived-then-filtered and missed this; target filters-then-derives).
  2. `check_tool_seed_sync` mirrors the omt_skip payload EXACTLY in
     `phase_gate.ts` — `_build_tree` re-points the copied seed.
  3. `collect_targets` ts branch ignored explicit paths (scanned 0 files).
  4. `render_agents` needs 8 docs incl. think.021 — T1 uses
     `_fallback_agents_md`; T2/T3 render fully (doc prefix-drops are T1-only).
- Target-tree requirements discovered via `check_tree`
  (fail-closed init): `.projects/meta/META.md` + WORK.md Projects section
  generated via `project_state` pure projectors; `AGENTS.md` always written;
  `GETTING_STARTED.md` allowlisted; `comp.workflows` dropped at T1 only
  (target copies `.workflows/` at T2+); `node_modules` never copied.

## Deltas vs design (documented deviations)

1. **Runtime copied verbatim** (scripts/omt, .opencode plugins/lib,
   .meta/templates, guide, f006 dir, package.json; .workflows at T2+):
   tiering = policy, not bytes — the runtime is policy-agnostic/IR-driven.
   Unused T3 scripts ship inert in T1 trees (no IR records → never fire).
   Follow-up: per-tier runtime manifests.
2. **Budgets kept, not re-baselined**: emitted `@budget` caps are the source
   caps (loose but green in target). Follow-up: measure-then-set at init.
3. **TS scope validation stays loose**: T1 `omt_skip{scope:nav}` records but
   unlocks nothing (no g.nav). Logged, visible in the skip report.
4. **No new MCP tools**: `init`/`check_tree` are harnessc CLI (no tool_args
   cost); `review`-style surfacing via CLI only.

## Evidence

- New suite `tests/features/feature_059.harness_tiered_template/` (12 tests:
  tier_filter 4, init_fs 4, mvc_profile 3, budget_pins 1) — all green.
- Full suite **1979 passed / 0 failed** (1967 + 12 new), empty allowlist.
- `harnessc check` 0 errors (263 records), `build` OK, all 12 budgets green
  (ir_json +82B for 2 vars + allowlist entry; nav_index +3B line drift).
- e2e receipt refreshed per round (check 19 pins D1+D2+D3 wiring).
