# IMPROVEMENT_OPTIONS — META HARNESS (improvement002, 2026-08-01)

> Strategy rules applied: (1) minimize future coding-agent token consumption,
> (2) optimize agent performance (not human readability) — prefer DSL/OMT-HDL extensions,
> (3) refactor opportunities considered wherever found.
> Token estimates rough (≈4 chars/token). Effort: S <1 h · M ½ day · L ≥1 day.
> OPT-B..OPT-H carried forward from improvement001 (re-verified OPEN today); OPT-I..OPT-L are new.

---

## Carried forward (re-verified)

## OPT-B — Relocate WORK.md scratchpad gotchas into nav-indexed `@doc gotcha.*` records ⚠️ NOW URGENT
- **What**: move the ~20 RECURRING GOTCHAS bullets into `@doc` records (tags `GOTCHA_`) in
  `.meta/META_HARNESS.omt` (queryable via `omt_nav "GOTCHA_"`), leaving ≤0.5 KB pointer + top-3
  one-liners in WORK.md. Scratchpad budget pin shrinks accordingly.
- **Why urgent**: scratchpad at **5692/6144 B (93%)** — the next gotcha appended risks a
  `harnessc build` compile FAILURE on an agent-edited file the compiler doesn't control.
- **Token impact**: ~4 KB (~1000 tok) saved **every session startup**; gotchas paid only when relevant.
- **Risk**: medium — gotchas no longer auto-seen; mitigation: keep top-3 inline, nav tip teaches query.
- **Effort**: S–M. **Type**: knowledge-store refactor (DSL-native).

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
  @var/@fsm); make it a GENERATED projection or delete; delete `thoughts.jsonl.bak`; add harnessc
  drift check for unlisted files in `.meta/.omt/`. (Both files verified still present today.)
- **Token impact**: small; prevents future split-brain debugging burn.
- **Risk**: low (verify first). **Effort**: S. **Type**: refactor/hygiene.

## OPT-F — Consolidate the 5 `omt_think_*` tools into one `omt_think{op}`
- **What**: `list|remove|verify|suggest` become an `op` arg; one schema entry.
- **Token impact**: ~0.4–0.6 KB (~100–150 tok) saved **every turn**.
- **Risk**: medium — think-gated files, e2e/pin churn; worse ergonomics. Schema budget has
  headroom (58%) so less urgent than in improvement001.
- **Effort**: M. **Type**: tool-surface refactor.

## OPT-G — Harness-edit session mode (break the receipt round-robin)
- **What**: logged unlock (e.g. `omt_skip{scope:"harness"}`) suspending the per-file second-edit
  guard for the session, BUT mandating a fresh e2e pass at phase exit (precedent: feature_024
  coverage-skip consult in gates.py). improvement001 execution re-validated the pain
  (2 receipt refreshes for 3 sequential edits).
- **Token impact**: large during harness work — eliminates N×(e2e run + wait) turns per refactor.
- **Risk**: medium — guard weakened in-window; mitigated by mandatory exit e2e + ledger record.
- **Effort**: M. **Type**: gate-behavior refactor (Python side — no TS hot-reload issue).

## OPT-H — Normalize TDD test_node granularity (kill the omt_done footgun)
- **What**: `tdd/state.py` normalizes node ids when folding red/green latest-wins so red at
  `f.py::C::t` + green at `f.py` cannot strand a dangling red. +1 pin test.
- **Token impact**: medium — each occurrence costs an omt_done block + recovery cycle.
- **Risk**: low–medium — touches dirty-WIP `tdd/state.py` (fresh e2e receipt first).
- **Effort**: S. **Type**: bug-ward refactor.

---

## New (improvement002 findings)

## OPT-I — Fix the evolution-loop prompt itself (meta-meta repair)
- **What**: update `prompts/loops/meta_harness_evolution.md`: path `./sandbox/` → `.sandbox/`;
  step 7 → "regenerate projections from `.meta/META_HARNESS.omt` (harnessc build) and append a
  dated note to the retired `.meta/META_HARNESS.md` stub" (codifies improvement001's reconciliation).
- **Token impact**: small per loop run, but every future loop re-pays the reconciliation + risks
  path forking (`sandbox/` vs `.sandbox/` splitting the improvement history).
- **Risk**: none (docs edit, no phase needed). **Effort**: S. **Type**: process repair.

## OPT-J — Compile trivial @doc records; drop one-word payloads
- **What**: delete the 12 one-word `@doc ph.*`/`@doc tt.*` records (payloads already in
  `@fsm phase states=` / `@phase applies=`); have harnessc DERIVE the 18 `@doc sec.*` records
  from the .omt comment banners (or vice versa). ~30 hand-maintained lines → generated.
- **Token impact**: small — .omt −~1 KB (read on every harness edit); index −~30 records;
  removes a drift class (banner text vs sec.* text can diverge silently today).
- **Risk**: low — nav answers for PHASE_/TT_/SECTION: must stay stable; pin via harnessc check.
- **Effort**: S–M. **Type**: DSL compiler extension + de-duplication refactor.

## OPT-K — Filter omt_status feature-health noise
- **What**: status prints `improvement001.opt_a_slim_agents_md: overall 0%` for a DONE option whose
  slug has no process-phase feature dirs. Filter health lines to slugs with ≥1 artifact dir, or
  resolve DONE slugs from ledger `complete` records.
- **Token impact**: small per omt_status call; removes a misleading signal (agent may burn turns
  "fixing" a phantom 0% feature).
- **Risk**: low. **Effort**: S. **Type**: status-output refactor (Python side).

## OPT-L — Make TS-side budgets measurable (close the budget blind spot)
- **What**: 3 of 6 budget knobs are declaration-only today (`nav_tip`, `digest_cap` "n/a TS-pinned";
  `@inject session_bootstrap budget=1536` untracked in harness.report). Extend harnessc to read the
  TS-pinned constants (already pinned by tests) or measure the emitted bootstrap bytes, so ALL
  per-turn surfaces are compile-enforced.
- **Token impact**: none direct — prevents silent regression of the F32/F33 control panel
  (a bootstrap growth would currently pass `harnessc check` undetected).
- **Risk**: low. **Effort**: M. **Type**: compiler/observability extension.

---

## Recommendation snapshot
- **Urgent + best session-level ROI**: OPT-B (scratchpad at 93% — budget failure imminent) + OPT-C.
- **Cheap correctness/hygiene**: OPT-E + OPT-I + OPT-K (all S, low risk).
- **Structural (token-heavy harness work)**: OPT-G now, OPT-D as the long game.
- **Compiler hardening**: OPT-J + OPT-L.
