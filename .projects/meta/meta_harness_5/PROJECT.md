# PROJECT: meta_harness_5 — Meta Harness requirements backlog (from `.sandbox/meta_harness_3_idea.md`)

> Status: **active** · **v0.1 (2026-08-29)** — created by `project.py new`. Iterate freely (non-gated); spawn features with `new_feature.py "<name>" --type <tt> --project meta_harness_5`; log sessions in CURRENT_STATE.md (newest on top).

---

## New Session Quick Start

> One line: `meta_harness_5` is the **forward-looking requirements backlog** transcribed from the harness review analysis `.sandbox/meta_harness_3_idea.md` — the key requirement ideas for improving the META HARNESS, with #10 (prose fallback) explicitly marked as already shipped in `meta_harness_4`, so this project scopes what to pursue next.

**Next:** review the requirements backlog below, pick the first item with real remaining value, and declare it as a scoped feature (`new_feature.py "<name>" --type <tt> --project meta_harness_5`). Priorities/downsides for each idea are captured inline to guide that choice.

---

## Summary (one line)

**A requirements/spec backlog distilled from `.sandbox/meta_harness_3_idea.md`** — every harness-improvement idea from the review, marked with status (shipped / deliberate-reject / sanity-check-open), so `meta_harness_5` can pick new work that is not redundant with `meta_harness_4`.

---

## Purpose

### What this project is

- A **single, forward-looking requirement record** for future META HARNESS work, sourced from the critical review in `.sandbox/meta_harness_3_idea.md` (10 proposals evaluated at HEAD `5789125`).
- Captures **all** the requirement ideas in one place with an explicit status per idea, so a fresh session can see at a glance what is already done, what was deliberately rejected, and what genuinely remains open.
- The requirement ideas are **requirement-formatted** (each: idea → current status → remaining value → next action), making the doc directly actionable as a backlog rather than a prose review.

### What this project is **not**

- NOT a re-execution of the single surviving improvement. **Idea #10 (`omt_tdd testlist` prose fallback) is already DONE** — shipped as `feature_037.tdd_testlist_prose_fallback` in `meta_harness_4` (2026-08-29). Do not re-plan or re-implement it here.
- NOT a revert of the deliberate rejections (#4 nav soft/hard, #5 budget removal, #7 tighten-to-actual). Those verdicts stand unless new evidence emerges.
- NOT the analysis document itself (that lives at `.sandbox/meta_harness_3_idea.md` and is unchanged). This PROJECT.md is the distilled, requirement-oriented projection of it.

---

## Scope & success criteria

**Scope (declared, not executed):**

1. Maintain a requirements backlog (below) with one entry per harness-improvement idea from `.sandbox/meta_harness_3_idea.md`.
2. Each entry records: idea, status (`shipped` / `reject` / `open`), remaining value, and the concrete next action if pursued.
3. **#10 marked `shipped`** — pointer to `meta_harness_4` / `feature_037`; excluded from new work.
4. New work is scoped per-item via `new_feature.py` when the backlog item is chosen.

**Success criteria:**

- A fresh session can read the backlog and immediately identify (a) what is already done, (b) which ideas are deliberately rejected, and (c) the 1–2 genuinely open ideas worth scoping next.
- No new feature re-implements #10 (guarded by the `#10 — shipped` marker).

---

## Requirements backlog (from `.sandbox/meta_harness_3_idea.md`)

> Each idea = the review's proposal, tagged with its verdict, remaining value, and next action. Locked verdicts carry evidence from the analysis; `open` ideas are candidates for new features.

| # | Requirement idea (from review) | Status | Remaining value / next action |
|---|-------------------------------|--------|-------------------------------|
| 1 | First-edit allowance on clean harness files by design (no severity reduction to `g.receipt`) | **shipped** (impl.) | None — already implemented; do not soften. |
| 2 | `g.think` per-file consult tracking (`omt_think{op:list}` clears gate; `risk_high` drops window) | **shipped** (impl.) | None — already implemented. |
| 3 | `g.kb` session-once flag (`omt_kb_nav` consult/session) | **shipped** (impl.) | None — already implemented. |
| 6 | `g.tdd_after` advisory auto-revert (two-hats invariant) | **shipped** (impl.) | None — already implemented. |
| 8 | TDD two-hats discipline (tests/ ↔ src/ auto-revert) | **shipped** (impl.) | None — already implemented. |
| 9 | Gate-message escape visibility (`nav_required`/`think_gate`/`receipt_stale`/`no_phase`) | **shipped** (impl.) | None — all four `@msg` records already embed escape hints; verified `.omt` L130–134. |
| 10 | `omt_tdd testlist` behavior parsing: accept JSON array **and** prose (newline/bullet/numbered) | **shipped** — `feature_037` in `meta_harness_4` | **None — already done.** Pointer: `scripts/omt/tdd/cli.py:68` `_parse_behaviors` + `TestParseBehaviors` tests. This project **must not** re-plan it. |
| 4 | `g.nav` soft-warn first session, hard after 3 violations | **reject** | Correctly rejected (gate already hard w/ `omt_skip{scope:"nav"}` escape + read/src exemptions; 3-strike adds complexity). Revisit only with new evidence. |
| 5 | Remove/replace TS-pinned budgets (`nav_tip`, `digest_cap`) | **reject** | Correctly rejected (single-source budgets drift-pinned by `test_omt_docs_drift_pins.py`). |
| 7 | Tighten budgets to actual+5% | **reject** | Correctly rejected (budgets carry review-gated growth headroom; actual+5% would *loosen* not tighten). |

**Open ideas / candidates for new `meta_harness_5` work:** per the analysis, **none of the 10 proposals are open** — 6 implemented, 3 rejected, 1 (the only genuine DX win) now shipped in `meta_harness_4`. Therefore this backlog currently has **no green-field entry**: every idea is either done or deliberately declined. If meta_harness_5 is to advance the harness, the next step is to produce **new proposals** (e.g. a follow-up `_idea.md` review at the current HEAD) rather than re-run the old 10. That is the recommended forward scope below.

**Recommended forward scope for meta_harness_5:**
- Produce a fresh harness review (`_idea.md`) at the *current* HEAD to discover **new** requirement ideas (the 2026-08-29 analysis is now partially stale: #10 shipped, gotcha count 17, budgets/records may have drifted since).
- Declare any new genuine DX win found as a feature in this project.

---

## Status

- [x] Project home created (`project.py new`, state: draft) — `meta_harness_5`
- [x] PROJECT.md written: forward-looking requirements backlog from `.sandbox/meta_harness_3_idea.md` (all 10 proposals tagged shipped/reject; #10 pointer to `meta_harness_4`)
- [x] **Forward scope (D4) executed 2026-08-29:** fresh harness review `.sandbox/meta_harness_5_idea.md` @ HEAD `544b40285` produced → single NEW genuine DX win identified (Proposal A: toolchain-aware `omt_tdd` dispatch) → declared as **feature_038.tdd_toolchain_aware** (minor_feature) → header flips draft → **active** (paused mid-implementation; see `.sandbox/pause_2026-08-29f.md`).
- [x] **feature_038.tdd_toolchain_aware COMPLETE (iter 2, 2026-08-29):** OPEN ITEM fixed (`_find_vitest_root` project-root cwd; whole-file vitest run), live RED/GREEN verified, `TestRunTestDispatch` ×6 green, sentinel 1664 passed, `harnessc check` 0 errors, GOTCHA_TDD_TOOLCHAIN added (17→18). Details @ FEATURE.md + test_report.md.

---

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — Backlog not re-execution:** per user, this project is a **requirements backlog** drawn from `.sandbox/meta_harness_3_idea.md`, NOT the single-improvement execution (that belongs to `meta_harness_4`/`feature_037`). Rationale: `meta_harness_5` would otherwise duplicate already-shipped work.
- **D2 — #10 marked shipped, not open:** the prose fallback was fully executed and closed in `meta_harness_4` (sentinel green, 1658 passed). Reopening it here risks redundant re-implementation.
- **D3 — Project slug `meta_harness_5`:** `meta_harness_4` already exists (complete); per user instruction the new backlog project is `meta_harness_5`.
- **D4 — No open backlog entries:** the analysis shows all 10 proposals are done/rejected. Forward scope is a **fresh review** at current HEAD to find new ideas. This is locked until new evidence (a new `_idea.md`) exists.

---

## References

- `.sandbox/meta_harness_3_idea.md` — the source analysis (10 proposals, verdicts, evidence; non-gated)
- `meta_harness_4` project home — where the one surviving improvement (#10 prose fallback) was executed as `feature_037`
- `.projects/meta/meta_harness_5/CURRENT_STATE.md` — session log
- `scripts/omt/tdd/cli.py:68` — the `_parse_behaviors` site (evidence #10 shipped)
