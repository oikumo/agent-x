# Implementation notes 001 — feature_031.petri_net_library TDD cycles

> Date: 2026-08-23 · Phase: Programming · Design: `4.design/features/feature_031.petri_net_library/design_001_petri_net_library.md` (+ `operation_spec_001`)

## Cycle log (3 cycles, node-consistent — GOTCHA_TDD_NODE honored)

| Cycle | Test node (red=green=refactor) | Src written | Behaviors | Result |
|---|---|---|---|---|
| 1 | `tests/model/petri_net/test_model.py` | `errors.py`, `model.py`, `__init__.py` (docstring-only) | 1–12 (build, duplicates F4, validation, arcs, enabledness, fire_marking purity, fire/reset, self-loop, parallel, accessors, pre/post-set, empty net) | 60/60 GREEN |
| 2 | `tests/model/petri_net/test_analysis.py` | `analysis.py` | 13–25 (reachability+truncation, graph, firing sequences, deadlocks, bounds, incidence, P/T-invariants, liveness, is_live F1, SCC, determinism) | 38/38 GREEN |
| 3 | `tests/model/petri_net/test_coverability.py` | `coverability.py` (v2 stub) | 26 (NotImplementedError) | 1/1 GREEN |

Suite: **99 passed** in `tests/model/petri_net/`; `omt_tdd{op:done}` checklist all green (suite_passes, refactor_recorded, naming_ok). June placeholder `test_petri_net.py` deleted (locked in-scope #5).

## Decisions taken during the build

- **Deferred imports in ALL THREE test files** (design_001 §8: "imports deferred inside test bodies where RED-collection-safety matters"). The design's parenthetical "modules exist from cycle 1; direct imports fine" holds only for cycles whose module already exists — at cycle-N RED the cycle's own module (`analysis.py`, `coverability.py`) never exists yet, and a top-level import aborts collection (pytest exit 2), which `cmd_start` rejects as a red. Deferred imports make every RED a runnable exit-1 failure (feature_030 "lazy importlib" precedent).
- **Placeholder deletion at bootstrap** (not "inside cycle-1 green" as design §9 literally said): two-hats blocks tests/ during the green hat; deletion landed in the same Programming phase via the TDD_BOOTSTRAP skip — satisfies F8 ("deleted in the same phase").
- **TDD_BOOTSTRAP skip** (`omt_skip{scope:"tests"}`, logged): first tests/ write precedes red-hat coverage (feature_030 analysis F6 pattern). Cycle discipline (red=tests-only, green=src-only) then kept manually per design §9.
- **SCC vertex-set filter:** Tarjan follows edges only to targets inside `graph.states`; truncated graphs can carry dangling edge targets (§13) and must not invent phantom single-state components. No-op on complete graphs; pinned in the `analysis.py` docstring.
- **`fire_marking` error precedence** (must-pin 3) verified by test: `UnknownTransitionError` → marking `ValueError` → `TransitionNotEnabledError`.
- **Empty-net `is_live` = `AnalysisResult(True, True, 1)`** (F1, §31 uniform rule) pinned by test, superseding §38's literal `0`.
- **`assert transition is not None`** in `firing_sequence_to` back-walk: non-initial predecessor entries always carry a label; narrows `str | None` for the type checker.

## Advisory warnings accepted (with reasons)

- **batch-N-tests** (50 + 38 functions per red): design §9 plans one red commit per FILE (3 cycles for 26 behaviors), not 1 test : 1 impl loop. Accepted per design.
- **"no assertions"** on `pytest.raises` tests: AST checker false positives — `pytest.raises` context managers are the assertions (error-matrix behaviors 2–4, 6, 11).

## Verification evidence

- 3 red→green→refactor cycles, all at the SAME file-level test_node (ledger records).
- `omt_tdd{op:done}`: ✅ all checklist items — 2 allowlisted known failures (TDD gate probes reading the live 8h ledger, KNOWN_SUITE_FAILURES) + 3 baseline drift failures (harnessc budget/projections — repo-hygiene triage, cleared in the wrap-up) tolerated, zero regressions.
- Full suite: 99 new + all prior tests, no regressions vs the phase baseline.
