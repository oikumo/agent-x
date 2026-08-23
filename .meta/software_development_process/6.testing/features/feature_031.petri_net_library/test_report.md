# Test report — feature_031.petri_net_library

> Date: 2026-08-23 · Phase: Testing · Design: `4.design/features/feature_031.petri_net_library/design_001_petri_net_library.md` · Impl: `5.implementation/features/feature_031.petri_net_library/implementation_001_tdd_cycles.md`

## Verdict

**SHIP.** v1 scope (PROJECT.md v1.1 LOCKED) implemented and verified: model layer + analysis layer + coverability v2 stub, exact-rational invariants, completeness-explicit results, 99 canonical tests green, full suite 1577 passed with zero regressions vs the phase baseline.

## DoD coverage (doc §40 items 1–17, 19 — item 18 = v2 stub)

| §40 | Items | Where proven |
|---|---|---|
| 1–3 | places/transitions/weighted arcs build | `test_model.py` TestBuild, TestArcs (60 tests) |
| 4–5 | enabledness AND / firing (self-loop, sources, sinks, parallel) | TestEnabledness, TestFireMarking, TestFireAndReset, TestSelfLoop, TestParallelTransitions |
| 6 | invalid models raise typed errors | TestDuplicateNames (F4 asymmetry), TestAddValidation, TestArcs error matrix |
| 7–8 | reachability + reachability graph (finite) | TestReachableMarkings, TestReachabilityGraph (incl. truncated edges-to-unvisited) |
| 9 | firing sequences (shortest; None semantics) | TestFiringSequenceTo (complete-proof vs truncated-not-proof) |
| 10 | deadlocks | TestDeadlocks (DEADLOCK_NET + truncated-never-deadlock-free) |
| 11–12 | bounds complete / `complete=False` on truncation | TestBounds (LIVE_BOUNDED proven; UNBOUNDED truncated ⇒ `bounded=None`, observed maxima only) |
| 13 | incidence matrix exact | TestIncidenceMatrix (incl. degenerate P×0 / 0-row / 0×0 shapes) |
| 14–15 | P/T-invariants exact (pure-Python rational nullspace, D4) | TestPlaceInvariants / TestTransitionInvariants (TWO_WAY_CYCLE `(1,1)` + conservation + identity bases, F7) |
| 16 | liveness on complete finite graphs | TestTransitionLiveness / TestIsLive (live / fire-once-dead / incomplete⇒None / empty net F1 `(True,True,1)`) |
| 17 | SCC (Tarjan) | TestStronglyConnectedComponents (cycle, deadlock, 2-component, empty net) |
| 18 | coverability (unbounded) — **v2** | `test_coverability.py`: stub raises `NotImplementedError` |
| 19 | positive AND "unknown" cases | per-function matrix: every exploration API has a truncated test asserting `complete=False` (+ pinned reason strings) |

§36 v1 toolkit checklist: all 11 items shipped (`reachable_markings`, `reachability_graph`, `firing_sequence_to`, `deadlocks`, `bounds`, `incidence_matrix`, `place_invariants`, `transition_invariants`, `transition_liveness`/`is_live`, `strongly_connected_components`, `coverability_tree` stub).

## TDD evidence (feature_016; closed via `omt_tdd{op:done}`, not skip)

- testlist: 26 behaviors (JSON array) → 3 red→green→refactor cycles, each at the SAME file-level test_node (GOTCHA_TDD_NODE honored): `test_model.py` (behaviors 1–12, 60 tests), `test_analysis.py` (13–25, 38 tests), `test_coverability.py` (26, 1 test). Genuine REDs (exit 1, runnable — deferred imports per design §8; a top-level import of the not-yet-existing module would abort collection with exit 2, which `cmd_start` rejects).
- `omt_tdd{op:done}` checklist: suite_passes ✅ · feature_suite_passes ✅ · repo_hygiene_passes ✅ · refactor_recorded ✅ · naming_ok ✅. 2 allowlisted known failures (TDD gate probes reading the live 8h ledger — KNOWN_SUITE_FAILURES, they pass again once the TDD session closed); 3 baseline drift failures tolerated (below).

## Suite results

- `tests/model/petri_net/`: **99 passed** (60 model + 38 analysis + 1 coverability).
- Sentinel `tests/features/feature_031.petri_net_library/` (re-export + conftest fixture bridge, feature_026/030 precedent): **99 passed**.
- **Full suite: 1577 passed, 3 failed** — the 3 are the pre-existing baseline drift trio (repo hygiene, NOT this feature):
  - `test_repo_omt_check_has_zero_errors` + `test_work_md_within_budget` — WORK.md 5170 B > 5120 B budget; cleared by DONE-rotation in the wrap-up.
  - `test_repo_projections_are_fresh` — projections stale vs doc edits; cleared by `harnessc build` in the wrap-up.
- Zero regressions vs the phase baseline (`baseline_failures` on the Programming phase record).

## Scope conformance (PROJECT.md v1.1)

- Files: `src/agentx/model/petri_net/{__init__.py (docstring-only), errors.py, model.py, analysis.py, coverability.py}` + `tests/model/petri_net/{test_model,test_analysis,test_coverability}.py`; June placeholder `test_petri_net.py` deleted. No `graph.py`, no `simulator.py`, no `pyproject.toml` change (zero dependencies — `nullspace` is pure-Python Fraction Gauss–Jordan, D4).
- Non-negotiables: two-layer separation (analysis never mutates the live marking — `fire_marking` pure, tested); canonical ordering/determinism (sorted orders, tuple markings, repeated-call equality test); edge cases per D7 (self-loops, no-input/no-output, parallel, zero-token, empty net, degenerate nets, duplicate-arc rejection); completeness tri-state with `max_states` required keyword-only (F2), never overclaiming from truncation (pinned reason strings).
- feature_001 NOT touched (D11 — future consumer; add-only API sufficient via rebuild).

## Deviations from design §8/§9 (all in-phase, documented in implementation_001)

1. Deferred imports kept in ALL three test files (the "direct imports fine" note only holds once the cycle's own module exists — cycles 2/3 RED-phase modules never exist yet).
2. Placeholder deletion at TDD_BOOTSTRAP (two-hats blocks tests/ during the green hat); same Programming phase per F8.
3. TDD_BOOTSTRAP `omt_skip{scope:"tests"}` for the first tests/ write (feature_030 analysis F6 pattern); cycle discipline then kept manually per design §9.
4. SCC restricted to the graph's vertex set (no phantom components from truncated-graph dangling edges; no-op on complete graphs) — pinned in `analysis.py` docstring.
5. Advisory warnings accepted: batch-N-tests (design §9 plans per-FILE cycles); "no assertions" on `pytest.raises` tests (AST-checker false positives).

## Known limitations (v2 backlog, out of v1 scope)

- Coverability (Karp–Miller), siphons/traps, home markings, simulator, DOT/JSON export, state-space optimization, `max_depth`/`time_limit` parameters.
- Tarjan SCC is recursive (docstring-noted): recursion limit bounds very large graphs — fine for v1 test nets.
- `omt_complete` feature-suite pattern requires `tests/features/<feature>/`; canonical tests live at `tests/model/petri_net/` (model-layer convention, A6) — bridged by the sentinel re-export (duplicates execution, not logic).
