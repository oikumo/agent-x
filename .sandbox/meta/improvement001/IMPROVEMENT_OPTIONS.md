# IMPROVEMENT_OPTIONS — META HARNESS (improvement001, 2026-08-01)

> Strategy rules applied: (1) minimize future coding-agent token consumption,
> (2) optimize agent performance (not human readability) — prefer DSL/OMT-HDL extensions,
> (3) refactor opportunities considered wherever found.
> Token estimates are rough (≈4 chars/token). Effort: S <1 h · M ½ day · L ≥1 day.

---

## OPT-A — Slim the AGENTS.md projection (per-turn saver)
- **What**: drop the Tools table (18 rows duplicating the tool schemas already in the system
  prompt), compress NEVER/ALWAYS lists into single-line records, let `omt_nav{query:"CMD_"}`
  be the on-demand replacement. Change the AGENTS.md projection template in `harnessc.py` +
  keep budget pin.
- **Token impact**: ~1.2–1.5 KB (~300–375 tok) saved **every turn of every session**.
- **Risk**: low — info remains one tool-call away; AGENTS.md budget test updated.
- **Effort**: S. **Type**: DSL projection refactor.

## OPT-B — Relocate WORK.md scratchpad gotchas into nav-indexed `@doc gotcha.*` records
- **What**: move the ~20 RECURRING GOTCHAS bullets into `@doc` records (tags `GOTCHA_`) in
  `.meta/META_HARNESS.omt` (queryable via `omt_nav "GOTCHA_"`, injected on demand), leaving a
  ≤0.5 KB pointer + top-3 one-liners in WORK.md. Scratchpad budget pin shrinks accordingly.
- **Token impact**: ~4 KB (~1 000 tok) saved **every session startup**; gotchas paid only when relevant.
- **Risk**: medium — gotchas no longer auto-seen; relies on agents querying when harness-working.
  Mitigation: keep the 3 highest-cost ones inline; nav tip already teaches the query path.
- **Effort**: S–M. **Type**: knowledge-store refactor (DSL-native).

## OPT-C — Nav-index `@var` + `@budget` records (close the answers gap)
- **What**: extend harnessc to emit `@var`/`@budget` into nav.index.jsonl with `VAR_`/`BUDGET_`
  tags so `omt_nav "LEDGER_CAP"` / `omt_nav "BUDGET"` answer instead of forcing file reads.
- **Token impact**: small per event (~0.5–1 KB saved per avoided file read); index grows <1 KB.
- **Risk**: none (additive). **Effort**: S. **Type**: DSL compiler extension.

## OPT-D — OMT-HDL-2: compile gate predicates → kill TS↔IR dual maintenance
- **What**: extend the DSL so `@pred`/`@gate` compile to an executable IR interpreted by ONE
  generic TS gate-runner (or generate the TS gate bodies), replacing 7 hand-written enforcer
  modules + their parity pin tests (gate order, doc_paths, harness_paths, constants pins).
- **Token impact**: large long-term — future harness changes touch ONE .omt file instead of
  .omt + TS + pin tests + e2e (the round-robin receipt dance, see OPT-G); removes a whole
  gotcha class (~1 KB of scratchpad) and pin-test reading.
- **Risk**: high — rewrites the enforcement core; needs full live-probe re-verification.
- **Effort**: L. **Type**: DSL evolution (the "suggest a DSL" rule, next major version).

## OPT-E — Kill duplicate/stale constant stores (hygiene + drift-class removal)
- **What**: (1) verify consumers of `.meta/omt_constants.json`; make it a GENERATED projection
  of `@var`/`@fsm` (or delete if unused); (2) delete stale `thoughts.jsonl.bak`;
  (3) add a harnessc drift check for unlisted files in `.meta/.omt/`.
- **Token impact**: small; prevents future debugging token burn from split-brain constants.
- **Risk**: low (verification step first). **Effort**: S. **Type**: refactor.

## OPT-F — Consolidate the 5 `omt_think_*` tools into one `omt_think{op}`
- **What**: `list|remove|verify|suggest` become an `op` arg (schema-level), one tool entry.
- **Token impact**: ~0.4–0.6 KB (~100–150 tok) saved **every turn** (4 fewer schemas in system
  prompt); shorter AGENTS.md table too (or moot if OPT-A lands).
- **Risk**: medium — touches omt_think.ts (think-gated file), e2e + pin churn; tool-call
  ergonomics slightly worse (nested args).
- **Effort**: M. **Type**: tool-surface refactor.

## OPT-G — Harness-edit session mode (break the receipt round-robin)
- **What**: new logged unlock `omt_skip{scope:"harness"}` (or `omt_phase` flag) that suspends the
  per-file second-edit guard for the session BUT mandates a fresh e2e pass at phase exit
  (`cmd_validate_exit` consults, like the coverage-gate skip pattern already wired in gates.py).
- **Token impact**: large during harness work — eliminates N×(e2e run + receipt wait) turns per
  multi-file refactor (the documented round-robin recipe exists precisely because of this).
- **Risk**: medium — guard weakened inside the window; mitigated by mandatory exit e2e + ledger
  record; pattern precedent exists (feature_024 coverage-skip override).
- **Effort**: M. **Type**: gate-behavior refactor (Python side, re-read live — no TS hot-reload issue).

## OPT-H — Normalize TDD test_node granularity (kill the omt_done footgun)
- **What**: `scripts/omt/tdd/state.py` normalizes node ids (strip/align `::Class::test` suffixes)
  when folding red/green latest-wins, so red at `f.py::C::t` and green at `f.py` cannot strand a
  dangling red. Plus one pin test.
- **Token impact**: medium — each occurrence costs an omt_done block + recovery cycle
  (documented as costing a full block in feature_024).
- **Risk**: low–medium — state-fold logic is shape-pinned; change is localized but touches the
  dirty-WIP file `tdd/state.py` (needs fresh e2e receipt first).
- **Effort**: S. **Type**: bug-ward refactor.

---

## Recommendation snapshot
- **Best immediate ROI (per-turn/per-session)**: OPT-A + OPT-C (both S, additive).
- **Best structural (token-heavy harness work)**: OPT-G, then OPT-D as the long game.
- **Cheap correctness**: OPT-E + OPT-H.
