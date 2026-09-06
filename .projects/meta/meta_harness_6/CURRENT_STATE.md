# CURRENT_STATE: meta_harness_6

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-09-05 (iter 1 — deep evaluation performed + program defined; ZERO execution)

### Done

- **Deep evaluation of the META HARNESS as a whole** (usage gains with vs without, for future opencode projects): architecture scorecard, ledger/archive metrics (327 phase / 266 skip / 173 complete / 696 think_consult), size split (~14K harness LOC vs ~23K app LOC), gotcha clustering (18 → 5 classes), economic model, tiered adoption recommendation (Tier 1/2/3).
- **Improvement options menu produced** (13 items: A1–A4, B1–B2, C1–C2, D1–D3, E1–E2, F1) with impact/cost/mechanism/sequencing.
- **Program created** (user: "create the new meta_harness_6 project … include all"): `project.py new` + PROJECT.md filled (waves, baseline, decision gates DG1–DG3, execution rules, success criteria) + this entry.
- **Evidence record saved:** `.sandbox/meta_harness_6_evaluation.md` (self-contained; PROJECT.md is the actionable distillation).

### In progress / Blocked

- _(nothing — program defined, nothing executed; next session starts Wave 1)_

### Next

1. Read `PROJECT.md` §New Session Quick Start → §Decision gates → §Execution rules.
2. Scaffold Wave 1 / A1: `uv run scripts/omt/new_feature.py "ledger test isolation" --type minor_feature --project meta_harness_6` — **this takes feature number 051** (DG2: reword the deferred "feature_051.multi_session_concurrency" WORK.md prose to "multi_session_concurrency (deferred, unnumbered)" in the same session).
3. `omt_phase{task_type:minor_feature, phase:Programming, scope:"harness tests run on isolated tmp ledger; KNOWN_SUITE_FAILURES deleted; full suite green"}` → execute per Execution rules (net work_start FIRST — g.net:35 live; receipt round-robin; canary ordering).

### Notes / context

- All Wave 1–4 items are `minor_feature`; Wave 5 D1 is `major_feature` (TDD auto-on, design doc). E1 analysis pass may be `docs`.
- Harness-surface discipline applies to every feature here (harness_paths + net_paths): fire work_start, ONE edit per file per receipt round, e2e refresh per round, harnessc check+build with budgets green.
- Check `meta_harness_5` backlog before each scaffold (Execution rule 5 — no re-implementation of its shipped items).
- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.

---

## 2026-09-05 (iter 0 — project created)

### Done

- Project home created (`project.py new`, state: draft).

### In progress / Blocked

- _(nothing)_

### Next

- <!-- superseded by iter 1 above -->

### Notes / context

- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.
