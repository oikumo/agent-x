# IMPROVEMENT_OPTIONS — META HARNESS (improvement003, 2026-08-01)

> Strategy rules applied: (1) minimize future coding-agent token consumption,
> (2) optimize agent performance (not human readability) — prefer DSL/OMT-HDL extensions,
> (3) refactor opportunities considered wherever found, (4) flexibility for future change.
> Token estimates rough (≈4 chars/token). Effort: S <1 h · M ½ day · L ≥1 day.
> OPT-C..OPT-L carried forward from improvement002 (re-verified OPEN today); OPT-M..OPT-P are new.

---

## New (improvement003 findings) — recommended first

## OPT-M — Compact WORK.md DONE narratives (startup token diet) ⭐ RECOMMENDED
- **What**: replace the 4 narrative DONE lines (L24/33/59/61 = 3316 B) with one-line summaries +
  pointer (feature dir / git log); add a `@doc` convention record ("DONE entries = one line;
  narrative lives in git history + feature dirs") so future completions stay compact. Optionally
  tighten `@budget work_md` 14336 → 8192 to compile-enforce the diet.
- **Token impact**: ~800 tok saved **every session startup** — the largest single recurring
  saving available today (WORK.md is the only mandatory startup read).
- **Risk**: low — WORK.md is agent-edited (not harness-surface); no receipt round-robin. History
  preserved in git. Mitigation for detail loss: pointers to `.meta/.../features/<f>/` + git log.
- **Effort**: S. **Type**: knowledge-store refactor (process-convention + one edit).

## OPT-N — Dedupe omt_nav include_context windows
- **What**: make the nav tool emit each index record at most once per response (verified today:
  `omt_nav "SECTION:" include_context` re-printed the same `@doc sec.*` records up to 4× in
  overlapping neighbor windows; ~30 KB response for a 251-record corpus query).
- **Token impact**: ~30–60% smaller multi-hit nav responses; paid per nav query with context.
- **Risk**: low–medium — TS side (omt_nav.ts; harness-surface → receipt round-robin applies);
  context semantics unchanged (same records, no repeats).
- **Effort**: S–M. **Type**: tool-output refactor.

## OPT-O — GOTCHA staleness lifecycle
- **What**: add `since=YYYY-MM` (+ optional `until=`) to `@doc gotcha.*` records; harnessc warns on
  gotchas older than N months; full-list queries could filter/sort by age. Prevents the corpus from
  becoming immortal (contrast: TA: thoughts already have verify/stale).
- **Token impact**: indirect — keeps every `GOTCHA_` full-list query proportional to *live* knowledge.
- **Risk**: low (additive k=v; compiler + docs change). **Effort**: M. **Type**: DSL extension.

## OPT-P — (folded into OPT-I) — see below.

---

## Carried forward (re-verified OPEN)

## OPT-C — Nav-index `@var` + `@budget` records
- **What**: harnessc emits `@var`/`@budget` into nav.index.jsonl with `VAR_`/`BUDGET_` tags so
  `omt_nav "LEDGER_CAP"` answers instead of forcing file reads. (Verified still missing today.)
- **Token impact**: ~0.5–1 KB saved per avoided file read; index grows <1 KB.
- **Risk**: none (additive). **Effort**: S. **Type**: DSL compiler extension.

## OPT-D — OMT-HDL-2: compile gate predicates → kill TS↔IR dual maintenance
- **What**: `@pred`/`@gate` compile to executable IR interpreted by ONE generic TS gate-runner,
  replacing 7 hand-written enforcer modules + parity pin tests.
- **Token impact**: large long-term — harness changes touch ONE .omt file instead of
  .omt + TS + pins + e2e round-robin; removes a whole gotcha class.
- **Risk**: high — rewrites enforcement core; full live-probe re-verification needed.
- **Effort**: L. **Type**: DSL evolution (next major version).

## OPT-E — Kill duplicate/stale constant stores
- **What**: verify consumers of `.meta/omt_constants.json` (428 B, drift-class duplicate of
  @var/@fsm); make it a GENERATED projection or delete; delete `thoughts.jsonl.bak` (verified
  byte-identical today); add harnessc drift check for unlisted files in `.meta/.omt/`.
- **Token impact**: small; prevents future split-brain debugging burn.
- **Risk**: low (verify first). **Effort**: S. **Type**: refactor/hygiene.

## OPT-F — Consolidate the 5 `omt_think_*` tools into one `omt_think{op}`
- **What**: `list|remove|verify|suggest` become an `op` arg; one schema entry.
- **Token impact**: ~0.4–0.6 KB (~100–150 tok) saved **every turn**.
- **Risk**: medium — think-gated files, e2e/pin churn; worse ergonomics. Schema budget has headroom (58%).
- **Effort**: M. **Type**: tool-surface refactor.

## OPT-G — Harness-edit session mode (break the receipt round-robin)
- **What**: logged unlock (e.g. `omt_skip{scope:"harness"}`) suspending the per-file second-edit
  guard for the session, BUT mandating a fresh e2e pass at phase exit (precedent: feature_024
  coverage-skip consult in gates.py).
- **Token impact**: large during harness work — eliminates N×(e2e run + wait) turns per refactor.
- **Risk**: medium — guard weakened in-window; mitigated by mandatory exit e2e + ledger record.
- **Effort**: M. **Type**: gate-behavior refactor (Python side — no TS hot-reload issue).

## OPT-H — Normalize TDD test_node granularity (kill the omt_done footgun)
- **What**: `tdd/state.py` normalizes node ids when folding red/green latest-wins so red at
  `f.py::C::t` + green at `f.py` cannot strand a dangling red. +1 pin test.
- **Token impact**: medium — each occurrence costs an omt_done block + recovery cycle.
- **Risk**: low–medium — touches `tdd/state.py` (harness-surface → fresh e2e receipt first).
- **Effort**: S. **Type**: bug-ward refactor.

## OPT-I — Fix the evolution-loop prompt itself (meta-meta repair) ⚠️ re-verified TODAY
- **What**: update `prompts/loops/meta_harness_evolution.md`: path `./sandbox/` → `.sandbox/`;
  step 7 → "regenerate projections from `.meta/META_HARNESS.omt` (harnessc build) and append a
  dated note to the retired `.meta/META_HARNESS.md` stub". Optionally add a `@flow meta.evolution`
  record so future runs are discoverable via omt_quick_ref (absorbs finding F4).
- **Token impact**: small per loop run; this is run #3 paying the reconciliation + path-fork risk.
- **Risk**: none (docs edit, no phase needed). **Effort**: S. **Type**: process repair.

## OPT-J — Compile trivial @doc records; drop one-word payloads
- **What**: delete the 12 one-word `@doc ph.*`/`@doc tt.*` records; have harnessc DERIVE the 18
  `@doc sec.*` records from the .omt comment banners (or vice versa). ~30 hand-maintained lines → generated.
- **Token impact**: small — .omt −~1 KB; index −~30 records; removes a silent-drift class.
- **Risk**: low — nav answers for PHASE_/TT_/SECTION: must stay stable; pin via harnessc check.
- **Effort**: S–M. **Type**: DSL compiler extension + de-duplication refactor.

## OPT-K — Filter omt_status feature-health noise ⚠️ re-verified LIVE today
- **What**: status prints `improvement002.opt_b_gotchas_to_nav: overall 0%` for a DONE, committed
  option with no process-phase dirs. Filter health lines to slugs with ≥1 artifact dir, or resolve
  DONE slugs from ledger `complete` records.
- **Token impact**: small per omt_status call; removes a misleading signal (phantom 0% → wasted "fix" turns).
- **Risk**: low. **Effort**: S. **Type**: status-output refactor (Python side).

## OPT-L — Make TS-side budgets measurable (close the budget blind spot)
- **What**: extend harnessc to read the TS-pinned constants / measure emitted bootstrap bytes, so
  ALL per-turn surfaces are compile-enforced (3 of 6 knobs declaration-only today).
- **Token impact**: none direct — prevents silent regression of per-turn injections.
- **Risk**: low. **Effort**: M. **Type**: compiler/observability extension.

---

## Recommendation snapshot
- **Best session-level ROI**: OPT-M (~800 tok/startup, S effort, no harness-surface friction).
- **Cheap correctness/hygiene bundle**: OPT-I + OPT-K + OPT-E (all S, low/no risk).
- **Query-path savings**: OPT-N (nav) + OPT-C (var index).
- **Structural (token-heavy harness work)**: OPT-G now, OPT-D as the long game.
- **Compiler hardening**: OPT-J + OPT-L + OPT-O.
