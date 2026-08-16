# PROJECT: petri_net_library — Weighted P/T Petri-net library for agentx

> Status: **v1 (2026-08-16)** — project home created from the requirement anchor `.meta/doc/petri_nets/petri_net_python_coding_agents.md`. Scope draft recorded; NOT yet locked (user approval pending). Feature dir, phase declaration, and all implementation work deliberately deferred — this document is the project's *purpose* only.

---

## Summary (one line)

**A pure-Python, zero-dependency weighted Place/Transition Petri-net library for agentx** — two clearly separated layers: an **execution/model layer** (places, transitions, weighted arcs, markings, enabledness, atomic firing) and an **analysis layer** (BFS reachability, reachability graph, firing sequences, deadlocks, bounds, incidence matrix, P/T-invariants via exact rational arithmetic, transition liveness on complete finite graphs, SCC) — with explicit, completeness-aware semantics (`complete=True/False`, `max_states` limit only in v1, no overclaiming). Coverability, simulation, and advanced structural analyses are v2.

---

## Purpose

### What this project is

A new, standalone library in `src/agentx/model/petri_net/` (layout adapted to the agentx `src/agentx/model/<pkg>/` convention: `model.py`, `analysis.py`, `coverability.py`, `errors.py`, `__init__.py`, plus tests under `tests/model/petri_net/`). The library implements:

- **Model layer** — weighted P/T net `N = (P, T, F, W, M0)`; places hold integer token counts, transitions fire atomically when all input requirements are met, arcs carry positive integer weights; core API per doc §9/§10 (`add_place`, `add_transition`, `add_input`, `add_output`, `is_enabled_at`, `fire`, `fire_marking` (pure), `enabled_transitions_at`, `current_marking`, `reset`).
- **Analysis layer** — `PetriNetAnalyzer` operating on the model without mutating its live marking and without UI/database/visualization coupling: `reachable_markings`, `reachability_graph`, `firing_sequence_to`, `deadlocks`, `bounds`, `incidence_matrix`, `place_invariants`, `transition_invariants`, `transition_liveness`, `is_live`, `strongly_connected_components`. Coverability is a v2 stub (`NotImplementedError`).
- **Completeness semantics** — result objects expose `value: bool | None`, `complete: bool`, `explored_states`, `reason`; every exploration API takes `max_states` only in v1 (no `max_depth`/`time_limit`) and never claims proof from a truncated search (§27–28, §39).
- **Determinism** — canonical immutable tuple markings over a stable `place_order`; sorted iteration everywhere; no dependence on `set` order (§6.2, §29).
- **Exact arithmetic** — P/T invariants computed via pure-Python rational Gaussian elimination (zero dependencies; doc §18 "~40 lines sufficient for v1").

### What this project is **not**

- **Not feature_001.** `feature_001.session_user_objectives_driven_by_Petri_Net` (internal state module `src/agentx/model/internal_state`, `USER_OBJECTIVES.md` CRC-driven structure) is a *future consumer* of this library — the library is the generic foundation, feature_001 is the application wiring. Neither is implemented here; this project home defines only the library.
- **Not a UI/TUI/console feature.** Pure model+analysis library; no screens, no controllers, no deepagents/coding-agent integration.
- **Not a simulation engine.** `simulator.py` (one-path policies, doc §26) is **v2** — not part of v1 scope. The analysis layer is a reasoning layer, not a simulation layer.
- **Not an optimization project.** Correctness and explicit semantics first; doc §33 basics (tuples, precomputed indexes, deque, sorted order) only. Matrix/sparse/symbolic/partial-order methods are later work.
- **Not a graphviz/JSON reporting project.** DOT export and JSON reports are advanced optional tools (§36), out of the first iteration.
- **Not a coverability implementation.** `coverability.py` exports a stub raising `NotImplementedError`; Karp–Miller is v2 (doc §17).
- **No `graph.py` module in v1.** SCC (Tarjan) lives in `analysis.py`; separate `graph.py` is premature modularization.

### Requirement anchor (the starting point)

The full requirement is `.meta/doc/petri_nets/petri_net_python_coding_agents.md` (41 sections). **v1 scope extracts only §1–16, §18–21, §23–24, §27–34, §36, §40 items 1–17, 19** (model layer, BFS analyses, exact invariants, liveness on finite graphs, SCC, completeness semantics, test patterns, architecture rules, minimum toolkit). v2 sections (§17 coverability, §22 home markings, §25 siphons/traps, §36 advanced, §37 example) are explicitly excluded from v1.

Non-negotiable requirements this project inherits:

1. Two-layer separation (execution vs analysis) — §Purpose, §34.
2. Weighted P/T semantics: `M'(p) = M(p) − W(p,t) + W(t,p)`; enabledness is AND over inputs; firing is atomic; disabled firing raises `TransitionNotEnabledError`; pure `fire_marking` + mutable `fire` (§4–5).
3. Canonical ordering (`place_order`/`place_index`) and deterministic iteration (§6.2, §29).
4. Edge-case coverage: self-loops, no-input (always enabled), no-output transitions, parallel transitions (distinct labels), zero-token places, **empty net allowed** (consistent analysis), duplicate-arc policy: reject (§8, §38).
5. Exact integer/rational arithmetic for incidence matrix and invariants (§18–19) — **pure-Python rational Gaussian elimination** (zero dependencies; D4 decision).
6. Completeness-explicit results and analysis limits (§27–28, §39): `True` = proven, `False` = disproven, `None` = unknown/incomplete.
7. Coverability (Karp–Miller) as a separate v2 module; truncated BFS is never labeled "unbounded" (§17).
8. Definition of Done = doc §40 items 1–17, 19; minimum analysis toolkit = doc §36 checklist (v1 items only).

### Recurring principles (invariants the library preserves)

- **Model defines possible state changes; marking is the state; firing changes the state; analysis systematically explores or mathematically reasons about those state changes** (doc §41).
- **No overclaiming** — proven true / proven false / unknown are distinct, never conflated (§39).
- **Analysis never mutates the live marking** — pure transformations over immutable markings (§5.4, §34).
- **Deterministic tests** — sorted places/transitions, reproducible reports (§29, §34).
- **TDD** — when this project becomes a feature, it is `task_type:"major_feature"`; feature_016 TDD auto-activates at Programming (red → green → refactor at the same test_node).
- **Zero dependencies** — pure Python standard library only; exact rational arithmetic implemented inline.

---

## Vision + standing principle + main objectives

**Standing principle (non-negotiable): the analysis layer is a reasoning layer, not a simulation layer.** The model layer executes one firing at a time; the analysis layer explores *all* relevant possibilities (BFS over markings, exact algebra for invariants) and reports *exactly* what it proved, what it disproved, and what remains unknown — never a bare `False` for "search stopped early."

**Main objectives — the project is justified by three outcomes:**

- **(a) A correct, semantics-explicit P/T Petri-net engine.** Places/transitions/weighted arcs/enabledness/firing per the doc's formal model; all edge cases (§38) behave per formal semantics; errors are typed (`PetriNetError` hierarchy: `InvalidModelError`, `UnknownPlaceError`, `UnknownTransitionError`, `TransitionNotEnabledError`). Verified by doc §40 DoD items 1–6 tests.
- **(b) A trustworthy analysis toolkit (v1).** Reachability, reachability graph, shortest firing sequence, deadlocks, bounds, incidence matrix, P/T-invariants (pure-Python exact rational arithmetic), transition liveness on complete finite graphs, SCC — each returning completeness-explicit results with `max_states` limit. Verified by DoD items 7–17, 19 tests, including "unknown" cases (§30, §40-19).
- **(c) The foundation feature_001 consumes.** When `feature_001.session_user_objectives_driven_by_Petri_Net` is scoped, the library is the ready, tested substrate for the internal-state Petri net — no re-implementation needed. (The feature_001 wiring itself is NOT this project's scope.)

**What is NOT the vision:** not a UI feature; not a research-grade state-space optimizer; not a graphviz/reporting tool; not a simulation engine; not a coverability implementation (v2).

---

## Scope & success criteria (draft — NOT locked; user approval pending)

> Draft v1. The requirement doc is the anchor; this section records the proposed boundary for user approval. Locking this boundary (or a revised version) is the precondition for any feature work.

### In scope (draft v1)

1. **Model layer** — `PetriNet` with the doc §9 API (streamlined): `add_place`, `add_transition`, `add_input`, `add_output`, `is_enabled_at`, `fire`, `fire_marking` (pure), `enabled_transitions_at`, `current_marking`, `reset`, canonical tuple markings (`place_order`/`place_index`), structural queries (`pre_set`/`post_set`, §24). Convenience wrappers `is_enabled()` and `enabled_transitions()` omitted (call `_at` variants directly).
2. **Analysis layer (v1 minimum toolkit, doc §36 filtered)** — `reachable_markings` (BFS, predecessor map), `reachability_graph`, `firing_sequence_to`, `deadlocks`, `bounds`, `incidence_matrix` (exact), `place_invariants`, `transition_invariants` (pure-Python exact rational Gaussian elimination), `transition_liveness`/`is_live` (finite complete graphs, reverse-BFS), `strongly_connected_components` (Tarjan in `analysis.py`). `coverability_tree` is a stub raising `NotImplementedError`.
3. **Completeness semantics + limits** — result dataclasses with `complete`/`reason`; **`max_states` only** on every exploration API (no `max_depth`/`time_limit` in v1); no hidden hard-coded limits.
4. **Edge cases** — self-loops, no-input/no-output transitions, parallel transitions, zero-token places, empty net allowed (consistent analysis: `()` marking, no enabled transitions, bounded=True, empty invariants), duplicate arcs: reject.
5. **Tests** — `tests/model/petri_net/` (`test_model.py`, `test_analysis.py`, `test_coverability.py`): model, analysis, coverability stub; both positive results AND "unknown" cases (doc §30, §40-19). Explicit test matrix for truncated vs complete analyses.

### Out of scope (explicit non-goals, draft v1)

- **No feature_001 work** — no `src/agentx/model/internal_state/`, no `USER_OBJECTIVES.md`/CRC wiring.
- **No UI/TUI/console/deepagents integration.**
- **No `simulator.py`** — v2 (doc §26: simulation is not analysis).
- **No `graph.py`** — SCC in `analysis.py` for v1; separate module only if needed later.
- **No coverability implementation** — `coverability.py` stub only; Karp–Miller is v2 (doc §17).
- **No siphons/traps** (§25 — advanced optional).
- **No home-marking analysis** (§22 — advanced optional).
- **No Graphviz/DOT export or JSON analysis reports** (advanced optional, §36).
- **No state-space optimization** (sparse matrices, partial-order/symmetry/symbolic reduction — §33 "later optimizations").
- **No `max_depth`/`time_limit` parameters** — v1 uses `max_states` only.

### Success criteria (draft — mapped to requirement doc)

- Doc §40 DoD items 1–17, 19 all demonstrably pass (execution items 1–6; analysis items 7–17, 19).
- Doc §36 minimum analysis toolkit checklist complete (v1 items only).
- Every truncated/limited exploration returns `complete=False` with a reason — tests assert this, not just the happy path (§30).
- Full suite green; when implemented as a feature: TDD closed via `omt_tdd{op:done}` with `checklist.suite_passes:true`, NOT via `omt_skip`.
- Zero external dependencies (`pyproject.toml` unchanged for this library).

### Boundaries (draft, one line each)

- **What changes (will change):** new `src/agentx/model/petri_net/` package (`model.py`, `analysis.py`, `coverability.py`, `errors.py`, `__init__.py`) + real tests under `tests/model/petri_net/` (`test_model.py`, `test_analysis.py`, `test_coverability.py`) replacing the placeholder `test_petri_net.py` stub; `pyproject.toml` **unchanged** (zero dependencies).
- **What does not change:** `src/agentx/model/internal_state/` (does not exist yet — feature_001's future home, untouched by design), the harness, the enforcer, all existing agentx modules.
- **What is deferred (future, not this project):** feature_001 integration, coverability implementation, siphons/traps, home markings, DOT/JSON export, state-space optimization, `simulator.py`, `graph.py`, `max_depth`/`time_limit` parameters.

---

## Status

- [x] Summary (one line)
- [x] Purpose (what it is / what it isn't / requirement anchor / principles)
- [x] Vision + standing principle + main objectives (draft v1)
- [x] Scope & success criteria (**draft v1 — awaiting user approval**)
- [ ] Scope & success criteria **locked** — pending user decision (approve as-is or revise)
- [ ] Architecture — pending (deferred to the feature design phase; `feature_030.petri_net_library/design_001_*.md` will own it once the feature dir is scaffolded)
- [ ] Tasks — pending (no tasks until the feature dir exists and the first phase is declared)
- [ ] Feature dir scaffolded — pending (`uv run scripts/omt/new_feature.py "petri net library" --type major_feature` — deliberately NOT run; user said project only, no feature yet)
- [ ] Phase declared — pending (`omt_phase{task_type:"major_feature", ...}` — deferred, see above)

---

## Out-of-scope reminders (deferred, not done by this document)

- Feature dir scaffolding — `.meta/software_development_process/{2.requirements,...}/features/feature_030.petri_net_library/` is **not** created by this document (user: "project, no feature yet").
- Phase declaration — no `omt_phase` is invoked by this document.
- `src/` edits — none; this document is project-home markdown only.
- Any design/analysis/test artifacts — owned by the future feature phases, not by this project home.

---

## Decisions log (draft — confirm or revise on approval)

- **D1 — Project slug is `petri_net_library`; feature slug will be `feature_030.petri_net_library`.** Next free feature slot: 030 (029 = rag_v2_slash_commands is last in `2.requirements/features/`). Confirmed NOT scaffolded yet.
- **D2 — Library location `src/agentx/model/petri_net/`** (agentx model-layer convention, e.g. `session/`, `rag_v2/`), module layout: `model.py`, `analysis.py`, `coverability.py`, `errors.py`, `__init__.py` exposing `PetriNet`, `PetriNetAnalyzer`. **No `graph.py`, no `simulator.py` in v1.**
- **D3 — Two-layer separation is mandatory** — execution/model layer and analysis layer; analysis never mutates the live marking; `fire_marking` is pure (§5.4, §34).
- **D4 — Exact arithmetic for invariants: pure-Python rational Gaussian elimination (LOCKED).** Doc §18 recommends `sympy` but also states *"a small exact-rational Gaussian-elimination nullspace (~40 lines) is sufficient for v1"*. **Decision: zero dependencies, implement inline.** No `sympy` added to `pyproject.toml`.
- **D5 — Completeness-explicit results everywhere** (§27, §39): `AnalysisResult(value: bool | None, complete: bool, explored_states: int, reason: str | None)`; liveness/boundedness/home queries return `None` (never bare `False`) when incomplete.
- **D6 — Deterministic ordering** — `place_order`/`transition_order` sorted; markings are tuples; no `set`-iteration dependence anywhere (§6.2, §29).
- **D7 — Edge-case policy** — self-loops legal; no-input transitions always enabled; no-output transitions legal (consume-and-vanish); parallel transitions distinct by name; zero tokens meaningful; empty net allowed with consistent analysis (`()` initial marking, no enabled transitions, bounded=True, empty invariants); duplicate arcs: reject (doc §38 "simplest API should reject duplicates").
- **D8 — API simplification: no convenience wrappers** — `is_enabled(transition)` and `enabled_transitions()` removed from v1; callers use `is_enabled_at(current_marking(), transition)` and `enabled_transitions_at(current_marking())` directly. Pure `fire_marking` + mutable `fire` retained.
- **D9 — v1 limits: `max_states` only** — no `max_depth`/`time_limit` parameters in v1 signatures; add in v2 when needed.
- **D10 — TDD is mandatory when implemented** — `major_feature` → feature_016 auto-activates at Programming; close via `omt_tdd{op:done}`, not `omt_skip`.
- **D11 — feature_001 relationship: consumer, not scope** — this library is the generic substrate; `feature_001.session_user_objectives_driven_by_Petri_Net` (internal state, USER_OBJECTIVES.md) is a separate future feature that consumes it.

---

## Iteration log

- **iter 1 (2026-08-16)** — project home `.projects/meta/petri_net_library/` created per user request ("create a new project for a petri net library for agentx, follow this doc as a requirement starting point"; "do not implement anything, just create the project"; "project, no feature yet"). PROJECT.md v1 shipped: Summary, Purpose (what/not/requirement anchor/principles), Vision + standing principle + objectives (draft), Scope & success criteria (draft — explicitly NOT locked, awaiting user approval), Status checklist (feature dir + phase marked pending by user instruction), Decisions log D1–D9 (draft), Iteration log, References. Companion `CURRENT_STATE.md` iter-0 created. Facts verified before writing: next free feature slot is 030; `tests/model/petri_net/test_petri_net.py` exists as a June placeholder stub (library tests will replace it); `src/agentx/model/petri_net/` does not exist; `pyproject.toml` has `numpy`, no `sympy` (drives D4); `src/agentx/model/` uses flat packages with empty `__init__.py` (drives D2).
- **iter 2 (2026-08-16)** — scope refinement for feasibility & simplicity per user review: (1) extracted v1-only scope from 41-section doc, (2) locked D4 to pure-Python rational nullspace (zero deps), (3) removed `simulator.py` and `graph.py` from v1, (4) coverability.py is stub only, (5) `max_states` only limit in v1, (6) removed convenience wrappers `is_enabled()`/`enabled_transitions()`, (7) explicit empty-net policy, (8) test matrix for "unknown" cases, (9) updated module list, decisions D1–D11, boundaries, success criteria.

---

## References
<!-- TA: risk: risk: requirement doc §17/§39 — a truncated BFS must NEVER be reported as "unbounded" or "deadlock-free"; only coverability-tree analysis can prove unboundedness. The tests must include "unknown" cases (doc §40-19), not just happy paths. Design phase must pin the AnalysisResult(value: bool|None, complete, explored_states, reason) contract before any analysis function is written. -->
<!-- TA: xref: xref: tests/model/petri_net/test_petri_net.py is a June placeholder stub (assertTrue(True)); src/agentx/model/petri_net/ does not exist; feature_001.session_user_objectives_driven_by_Petri_Net (FEATURE.md: internal_state module, USER_OBJECTIVES.md CRC update) is the FUTURE CONSUMER, not part of this project's scope (D11). Verified 2026-08-16 at iter-0. -->
<!-- TA: gotcha: gotcha: doc §18 recommends sympy for exact invariant nullspace, but D4 LOCKS to pure-Python rational Gaussian elimination (zero deps). Do not silently implement invariants with numpy floating-point nullspace — doc §18 explicitly rejects float rank/null-space for Petri-net invariants. -->

- **Requirement doc (the anchor)** — `.meta/doc/petri_nets/petri_net_python_coding_agents.md`. 41 sections covering foundations (§1–2), model layer (§3–10), analysis layer (§11–25), design rules (§26–34), structure (§35), minimum feature set (§36), end-to-end example (§37), edge cases (§38), no-overclaiming (§39), Definition of Done (§40), final mental model (§41). **v1 scope: §1–16, §18–21, §23–24, §27–34, §36, §40 items 1–17, 19 only.**
- **feature_001 requirement** — `.meta/software_development_process/2.requirements/features/feature_001.session_user_objectives_driven_by_Petri_Net/FEATURE.md`. The future consumer: agentx internal state in `src/agentx/model/internal_state`, adaptive Petri net, structure updated when `local_sessions/current/USER_OBJECTIVES.md` CRC changes.
- **Harness project-home convention** — `.meta/META_HARNESS.omt:184-185` + `:208`. `.projects/meta/<feature>/{PROJECT.md, CURRENT_STATE.md}` non-gated; PROJECT.md canonical, CURRENT_STATE.md session log + resume point; companion to the phase-gated design doc.
- **Sibling project for convention** — `.projects/meta/rag_v2/PROJECT.md` (project-home structure: Summary → Purpose → Vision → Scope matrix → Status → Decisions → Iteration log → References) and `.projects/meta/meta_harness_3/CURRENT_STATE.md` (session-log format).