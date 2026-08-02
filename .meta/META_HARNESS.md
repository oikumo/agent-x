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

> ROTATION (improvement007/OPT-B): only the LATEST note stays inline; older
> notes live in git history (`git log -p -- .meta/META_HARNESS.md`). New
> notes land one-liner + pointer style.

- **2026-08-01 (improvement007 / ALL OPT A–I):** R1–R11 — {@var.x}
  interpolation · grammar-vocab check · arg-describe diet (1609→1285 B/turn)
  + tool_args budget · TS+py consume IR (7 hand-mirrors deleted) ·
  after-gates into gate_driver · IR-driven gate msgs + orphan-@msg check ·
  @derive round 2 (14 hand records → 13 derived + 2 pruned) ·
  META_HARNESS/META doc diet (this stub + 2 budgets) · guide dedup
  (27.5→23.9 KB, §15 drift fixed, @xref guide 6→16 routes). Details:
  .sandbox/meta/improvement007/OUTCOME.md + git log. Verified: harnessc
  0 err (234 rec) · build+verify no drift · tests/scripts/omt 163/163 ·
  e2e ✓ · live smoke 2/2 · full suite 1109 + 3 known feature_018.
