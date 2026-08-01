# META_HARNESS — GENERATED STUB (retired corpus)

> **GENERATED — DO NOT EDIT.** The hand-maintained corpus was RETIRED in
> meta_harness_dsl R8 (OMT-HDL-1). The single source of truth is
> **`.meta/META_HARNESS.omt`** (OMT-HDL).
>
> - **Query:** `omt_nav` / `omt_list_sections` / `omt_cross_ref` / `omt_quick_ref`
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
