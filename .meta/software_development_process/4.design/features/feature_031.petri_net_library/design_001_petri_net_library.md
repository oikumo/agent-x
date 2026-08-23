# Design 001 — feature_031.petri_net_library: v1 implementation blueprint

> Date: 2026-08-22 · Phase: Design · Sources: PROJECT.md v1.1 (LOCKED) + analysis_001 (anchors A1–A12, findings F1–F10) + anchor doc §10/§31 (canonical code, subordinate to the locks per its own authority clause line 1814).
> Rule: Programming copies this doc; anything ambiguous here is resolved HERE, not in code.

---

## 1. Must-pin checklist resolutions (from PROJECT.md — all 7 closed)

| # | Item | PIN |
|---|---|---|
| 1 | `AnalysisResult` fields | `@dataclass(frozen=True) AnalysisResult(value: bool\|None, complete: bool, explored_states: int, reason: str\|None = None)` — §31 exact (F3). Payload dataclasses §31 exact too (§4 below): NO extra fields anywhere. |
| 2 | `PetriNetAnalyzer` binding | **Constructor-bound**: `PetriNetAnalyzer(net)` stores `self.net`; liveness/SCC/firing-sequence take the precomputed graph/result per-call (§32). |
| 3 | `fire_marking` disabled | raises `TransitionNotEnabledError(transition)` AFTER `UnknownTransitionError`/marking-`ValueError`; never mutates; input marking unchanged. |
| 4 | `reset()` target | restores `M0`: `self.marking = self.initial_marking.copy()`; structure untouched. |
| 5 | `max_states` policy | **required keyword-only, `int \| None`, NO default; `None` = explicitly unlimited** (F2). Signatures: `def f(self, *, max_states: int \| None) -> …`. |
| 6 | Per-function test matrix | analysis_001 §5 — realized as the TDD behavior list (§7 below). |
| 7 | `__init__.py` exports | docstring-only, no re-exports (rag_v2 convention, A5). Callers import `agentx.model.petri_net.model` / `.analysis` / `.errors`. |

## 2. F-findings dispositions (analysis_001 → design)

- **F1** empty-net `is_live` = `AnalysisResult(True, True, 1)` (§31 uniform `len(graph.states)`; §38's literal `0` superseded). Test pins 1.
- **F2** `max_states` required-kw-only `int|None` no default (must-pin 5).
- **F3** result dataclasses §31-exact; `ReachabilityResult`/`ReachabilityGraph` have NO `reason`; truncation signal = `complete=False` (+`explored_states==max_states` where present).
- **F4** duplicate-name asymmetry preserved: duplicate place → `DuplicatePlaceError`; duplicate transition → plain `ValueError`. Tests pin both.
- **F5** model grows `pre_set(name)/post_set(name) -> frozenset[str]`: transition→inputs/outputs keys; place→producers/consumers; name in both → `InvalidModelError("Ambiguous node name: …")`; unknown → `PetriNetError("Unknown node: …")`.
- **F6** `place_index` property `{p: i for i, p in enumerate(self.place_order)}` (recompute idiom like `place_order`); used by `fire_marking` + `incidence_matrix`.
- **F7** `nullspace(matrix, n_cols=None)` — explicit `n_cols` on degenerate shapes; empty-net guards return `[]` before calling.
- **F8** Programming: first tests/ write via `omt_skip{scope:"tests"}` (TDD_BOOTSTRAP), then red hat; placeholder `test_petri_net.py` deleted in Programming.
- **F9** `omt_kb_nav` consult before first src/ edit.
- **F10** TDD: same `test_node` for red→green→refactor; testlist = JSON array.

## 3. `errors.py` — full content

```python
"""Typed error hierarchy for the Petri-net library (doc §5.3/§10)."""


class PetriNetError(Exception):
    """Base class for all Petri-net errors."""


class InvalidModelError(PetriNetError):
    """The net structure is invalid (incl. duplicate arcs/places, ambiguity)."""


class DuplicatePlaceError(InvalidModelError):
    """add_place() with an existing place name."""


class DuplicateArcError(InvalidModelError):
    """add_input()/add_output() for an arc endpoint pair that already exists."""


class UnknownPlaceError(PetriNetError):
    """A referenced place does not exist in the net."""


class UnknownTransitionError(PetriNetError):
    """A referenced transition does not exist in the net."""


class TransitionNotEnabledError(PetriNetError):
    """fire_marking()/fire() on a transition disabled in the given marking."""
```

## 4. Result dataclasses (§31 exact — F3)

```python
Marking: TypeAlias = tuple[int, ...]

@dataclass(frozen=True)
class AnalysisResult:
    value: bool | None
    complete: bool
    explored_states: int
    reason: str | None = None

@dataclass(frozen=True)
class ReachabilityResult:
    markings: frozenset[Marking]
    predecessors: dict[Marking, tuple[Marking | None, str | None]]
    complete: bool
    explored_states: int

@dataclass(frozen=True)
class ReachabilityGraph:
    states: frozenset[Marking]
    edges: dict[Marking, tuple[tuple[str, Marking], ...]]
    complete: bool

@dataclass(frozen=True)
class DeadlockResult:
    deadlocks: tuple[Marking, ...]
    complete: bool
    explored_states: int
    reason: str | None = None

@dataclass(frozen=True)
class BoundResult:
    bounded: bool | None
    bounds: dict[str, int]
    complete: bool
    reason: str | None = None
```

`Marking` + all five live in `analysis.py` (§31). Frozen; deterministic repr order = field order.


## 5. `model.py` — PetriNet (§10 canonical + F5/F6)

Imports: `from __future__ import annotations`, `from dataclasses import dataclass, field`, errors from `.errors`. No other deps.

### 5.1 Fields (`@dataclass`, mutable — §10)

```python
@dataclass
class PetriNet:
    places: set[str] = field(default_factory=set)
    transitions: set[str] = field(default_factory=set)
    inputs: dict[str, dict[str, int]] = field(default_factory=dict)    # t -> {place: weight}  (pre-set •t)
    outputs: dict[str, dict[str, int]] = field(default_factory=dict)   # t -> {place: weight}  (post-set t•)
    marking: dict[str, int] = field(default_factory=dict)
    initial_marking: dict[str, int] = field(default_factory=dict)
```

### 5.2 Mutation API

| Method | Behavior (raises) |
|---|---|
| `add_place(name: str, tokens: int = 0) -> None` | `ValueError("Place name cannot be empty")` if `not name`; `ValueError("Token count must be a non-negative integer")` if non-int/bool/`<0`; `DuplicatePlaceError(f"Place already exists: {name}")`. Else `places.add`, `marking[name] = initial_marking[name] = tokens`. |
| `add_transition(name: str) -> None` | `ValueError("Transition name cannot be empty")` if `not name`; **`ValueError(f"Transition already exists: {name}")` on duplicate (F4 asymmetry)**. Else `transitions.add`, `inputs[name] = {}`, `outputs[name] = {}`. |
| `add_input(place: str, transition: str, weight: int = 1) -> None` | `_validate_arc(place, transition, weight)`; `DuplicateArcError(f"Input arc already exists: {place} -> {transition}")`; else `inputs[transition][place] = weight`. |
| `add_output(transition: str, place: str, weight: int = 1) -> None` | **arg order (transition, place) — swapped vs add_input (§9 gotcha)**; `_validate_arc(place, transition, weight)`; `DuplicateArcError(f"Output arc already exists: {transition} -> {place}")`; else `outputs[transition][place] = weight`. |
| `_validate_arc(place, transition, weight) -> None` (private) | `UnknownPlaceError(place)` first; `UnknownTransitionError(transition)` second; `ValueError("Arc weight must be a positive integer")` if non-int/bool/`<=0`. |
| `_require_transition(transition) -> None` (private) | `UnknownTransitionError(transition)` if absent. |

### 5.3 Order/marking API

| Member | Behavior |
|---|---|
| `place_order` (property) `-> tuple[str, ...]` | `tuple(sorted(self.places))` |
| `transition_order` (property) `-> tuple[str, ...]` | `tuple(sorted(self.transitions))` |
| `place_index` (property, F6) `-> dict[str, int]` | `{p: i for i, p in enumerate(self.place_order)}` |
| `current_marking() -> tuple[int, ...]` | `tuple(self.marking[p] for p in self.place_order)` |
| `initial_marking_tuple() -> tuple[int, ...]` | `tuple(self.initial_marking[p] for p in self.place_order)` |
| `marking_to_dict(marking) -> dict[str, int]` | `ValueError("Marking length does not match place count")` on length mismatch; `ValueError("Marking contains a negative token count")` on any `<0`; else `dict(zip(self.place_order, marking))`. |

### 5.4 Execution API (semantics §4–§5; must-pins 3–4)

| Method | Behavior |
|---|---|
| `is_enabled_at(marking, transition) -> bool` | `_require_transition`; `marking_to_dict(marking)` (validation propagates); `all(m[p] >= w for p, w in self.inputs[transition].items())` — AND over inputs; vacuously True for no-input. |
| `enabled_transitions_at(marking) -> list[str]` | `[t for t in self.transition_order if self.is_enabled_at(marking, t)]` — deterministic sorted. |
| `fire_marking(marking, transition) -> tuple[int, ...]` | `_require_transition`; `if not self.is_enabled_at(marking, transition): raise TransitionNotEnabledError(transition)`; compute via `place_index` into a local list (subtract inputs, add outputs); return `tuple(result)`. **Pure — net and input marking untouched; atomic (no intermediate exposure).** |
| `fire(transition) -> None` | `self.marking = self.marking_to_dict(self.fire_marking(self.current_marking(), transition))` — re-validates successor; all errors propagate; live marking unchanged on error. |
| `reset() -> None` | `self.marking = self.initial_marking.copy()`. |

### 5.5 Structural queries (F5)

```python
def pre_set(self, node: str) -> frozenset[str]: ...   # t: frozenset(inputs[t]); p: {t for t in transitions if p in outputs[t]}
def post_set(self, node: str) -> frozenset[str]: ...  # t: frozenset(outputs[t]); p: {t for t in transitions if p in inputs[t]}
```
Dispatch: `in_places = node in self.places`, `in_transitions = node in self.transitions`; both → `InvalidModelError(f"Ambiguous node name: {node}")`; neither → `PetriNetError(f"Unknown node: {node}")`. Place-branch iterates `self.transition_order` (deterministic; result is a frozenset anyway).

**No** `is_enabled()`/`enabled_transitions()` wrappers (D8); **no** `remove_*` (build-once, §34); **`Place`/`Transition` dataclasses omitted** — string names are identity (§3/§4 v1 note).


## 6. `analysis.py` — PetriNetAnalyzer (§31 canonical + F1/F2/F3/F7)

Imports: `from __future__ import annotations`, `from collections import deque`, `from dataclasses import dataclass`, `from fractions import Fraction`, `from math import gcd`, `from typing import TypeAlias`, `from agentx.model.petri_net.model import PetriNet`. Result dataclasses per §4 above live at module top.

### 6.1 Binding + shared exploration core

```python
class PetriNetAnalyzer:
    def __init__(self, net: PetriNet) -> None:
        self.net = net

    def _explore(self, *, max_states: int | None) -> tuple[
        frozenset[Marking],
        dict[Marking, tuple[Marking | None, str | None]],
        dict[Marking, tuple[tuple[str, Marking], ...]],
        bool,
        int,
    ]:
```

`_explore` algorithm (§31): `initial = net.initial_marking_tuple()`; `queue = deque([initial])`; `visited = {initial}`; `predecessors = {initial: (None, None)}`; `edges: dict[Marking, list[tuple[str, Marking]]] = {}`; `complete = True`. Loop `while queue`: `marking = popleft()`; `outgoing = []`; for `transition` in `net.enabled_transitions_at(marking)`: `successor = net.fire_marking(marking, transition)`; `outgoing.append((transition, successor))`; if `successor in visited`: continue; elif `max_states is not None and len(visited) >= max_states`: `complete = False`; continue (edge kept, successor NOT enqueued); else `visited.add`, `predecessors[successor] = (marking, transition)`, `queue.append(successor)`. After inner loop: `edges[marking] = outgoing`; `if not complete: break`. Return `(frozenset(visited), predecessors, {m: tuple(o) for m, o in edges.items()}, complete, len(visited))`. Determinism: BFS order fixed by sorted `transition_order`; no set iteration anywhere.

### 6.2 Exploration APIs (F2 signatures)

| Method | Returns | Spec |
|---|---|---|
| `reachable_markings(*, max_states: int \| None) -> ReachabilityResult` | wraps `_explore` (drops edges): `ReachabilityResult(markings=states, predecessors=preds, complete=complete, explored_states=n)` |
| `reachability_graph(*, max_states: int \| None) -> ReachabilityGraph` | wraps `_explore` (drops preds/n): `ReachabilityGraph(states=states, edges=edges, complete=complete)` — truncated graphs MAY have edge targets outside `states` (§13; consumers check `complete`) |
| `deadlocks(*, max_states: int \| None) -> DeadlockResult` | wraps `_explore`; deadlock = visited marking with `net.enabled_transitions_at(m) == []`; **sorted tuple** (§29); `reason=None` if complete else exactly `"State-space exploration was truncated; listed deadlocks are only those among explored states."` |
| `bounds(*, max_states: int \| None) -> BoundResult` | wraps `_explore`; per-place maxima over ALL discovered markings (init 0 per `place_order`); complete → `BoundResult(True, maxima, True)`; truncated → `BoundResult(None, maxima, False, "State-space exploration was truncated; boundedness is unknown.")` — **never `bounded=True` from truncation (§16/F3)** |

### 6.3 Graph-driven APIs (no exploration; §32)

| Method | Returns | Spec |
|---|---|---|
| `firing_sequence_to(result: ReachabilityResult, target: Marking) -> list[str] \| None` | `None` if `target not in result.markings`; else walk `result.predecessors` from target to initial (`previous is None`), collect labels, reverse. Shortest under BFS edge count. `None` is a proof of unreachability ONLY when `result.complete is True` (§14). |
| `transition_liveness(transition: str, graph: ReachabilityGraph) -> AnalysisResult` | incomplete graph → `AnalysisResult(None, False, len(graph.states), "Reachability graph is incomplete; liveness is unknown.")`. Else: `enabling = {s for s in graph.states if net.is_enabled_at(s, transition)}`; empty → `AnalysisResult(False, True, len(graph.states))`; else reverse multi-source BFS (stack) over reversed `graph.edges` from all enabling states → `can_reach`; return `AnalysisResult(can_reach == set(graph.states), True, len(graph.states))`. Reverse adjacency built in sorted-state iteration for determinism. |
| `is_live(graph: ReachabilityGraph) -> AnalysisResult` | incomplete → `AnalysisResult(None, False, len(graph.states), "Reachability graph is incomplete; global liveness is unknown.")`; else for `t` in `net.transition_order`: first `transition_liveness(t, graph)` whose `value is not True` is returned as-is; all live → `AnalysisResult(True, True, len(graph.states))` (F1: empty net ⇒ `(True, True, 1)`). |
| `strongly_connected_components(graph: ReachabilityGraph) -> list[frozenset[Marking]]` | Recursive Tarjan over `graph.states`/`graph.edges` (indices/lowlinks/on_stack/stack; pop SCC when `lowlinks[v] == indices[v]`). Iterate neighbors in edge-tuple order; start nodes in sorted-state order → deterministic component contents (frozensets). Empty net ⇒ `[frozenset({()})]`. Recursion limit: fine for v1 test nets; note in docstring. |

### 6.4 Exact algebra (§7/§18/§19; D4 zero-dep; F6/F7)

| Method | Returns | Spec |
|---|---|---|
| `incidence_matrix() -> list[list[int]]` | `C[p][t] = outputs[t].get(p,0) - inputs[t].get(p,0)`; rows=`place_order`, cols=`transition_order`. Pure ints. |
| `place_invariants() -> list[tuple[int, ...]]` | `n_places==0` → `[]`; else transpose C → `nullspace(Ct, n_cols=n_places)` → `[_coprime_int_vector(v) ...]` (solves `Cᵀx=0`; token-conservation laws). |
| `transition_invariants() -> list[tuple[int, ...]]` | `n_trans==0` → `[]`; else `nullspace(C, n_cols=n_trans)` → coprime tuples (solves `Cy=0`; cyclic firing multisets — doc-caveat: non-negative T-invariant ≠ realizable sequence, noted in docstring). |

Module-level helpers (private except by convention):

```python
def nullspace(matrix: list[list[int]], n_cols: int | None = None) -> list[list[Fraction]]:
    # Fraction Gauss–Jordan to FULL RREF (eliminate above+below); pivot cols tracked;
    # free cols each emit basis vector: 1 at f, -rows[pivot_row[c]][f] at pivot c, else 0.
    # n_cols inferred from first row when None (0 for empty matrix) — PASS EXPLICITLY on degenerate shapes (F7).

def _coprime_int_vector(vec: list[Fraction]) -> tuple[int, ...]:
    # lcm of denominators -> scale to ints -> divide by gcd-content ->
    # negate if first nonzero component negative (deterministic representative).
```

## 7. `coverability.py` + `__init__.py`

```python
# coverability.py
"""Coverability analysis — v2 (Karp–Miller, doc §17). v1 ships the stub only."""
from __future__ import annotations
from agentx.model.petri_net.model import PetriNet

def coverability_tree(net: PetriNet) -> None:
    """v2 placeholder — Karp–Miller coverability tree (doc §17)."""
    raise NotImplementedError("coverability_tree is v2 (Karp–Miller); see doc §17")
```

`__init__.py`: docstring-only, e.g. `"""Weighted P/T Petri-net library — model + analysis layers (feature_031). Import from agentx.model.petri_net.model / .analysis / .errors."""` No imports, no `__all__` (must-pin 7).


## 8. Test plan (realizes analysis_001 §4–§5; §30 nets as fixtures)

Files: `tests/model/petri_net/test_model.py`, `test_analysis.py`, `test_coverability.py` (+ keep existing empty `__init__.py`); **delete** placeholder `test_petri_net.py` (F8). Style: modern pytest (plain `Test*` classes, bare asserts, `@pytest.fixture` builders, `from __future__ import annotations`); imports deferred inside test bodies where RED-collection-safety matters (feature_027 pattern not needed — modules exist from cycle 1; direct imports fine).

Shared fixtures (§30, alphabetical place order):
- `TWO_WAY_CYCLE`: places p1,p2; t1: p1→p2 (1/1); t2: p2→p1 (1/1). M0 variants: `CONSERVATION_M0=(1,1)`, `LIVE_BOUNDED_M0=(1,0)`.
- `UNBOUNDED_NET`: p=1; t: p→p weight in 1 / out 2.
- `DEADLOCK_NET`: p=0; t: in p:1, no outputs.
- `SELF_LOOP_NET`: counter=1; process: in counter:1, out counter:1.
- `SOURCE_NET`/sink cases inline; `EMPTY_NET`: `PetriNet()`; places-only; transitions-only.
- `make_net(defn, initial_marking=None)` helper in `test_analysis.py` mirroring §30.

### test_model.py behaviors (DoD 1–6)

1. build: places with tokens / transitions / weighted arcs appear in orders + markings.
2. duplicate place → DuplicatePlaceError; duplicate transition → ValueError (F4).
3. empty names → ValueError; bad tokens (bool/-1/float) → ValueError.
4. add_input/add_output: unknown place → UnknownPlaceError (before transition check); unknown transition → UnknownTransitionError; bad weight (0/-1/bool) → ValueError; duplicate input/output arc → DuplicateArcError; **arg-order pin**: `add_output(transition=…, place=…)` by keyword.
5. enabledness: AND across inputs; insufficient tokens → False; no-input → True; zero-token place blocks weight-1 input.
6. fire_marking pure: successor correct; net.marking + input tuple unchanged; disabled → TransitionNotEnabledError; unknown → UnknownTransitionError; malformed marking (length/negative) → ValueError.
7. fire mutable: applies; on error live marking unchanged; reset() restores M0 after fires.
8. self-loop net effect M−1+1 (marking unchanged, enabled throughout).
9. parallel transitions: both enabled, distinct successors by name.
10. current_marking/initial_marking_tuple/marking_to_dict round-trip + sorted orders + place_index (F6).
11. pre_set/post_set: transition inputs/outputs; place producers/consumers; unknown → PetriNetError; ambiguous (place+transition same name) → InvalidModelError (F5).
12. empty net: `current_marking()==()`, `enabled_transitions_at(())==[]`, `reset()` no-op.

### test_analysis.py behaviors (DoD 7–17, 19)

13. reachable TWO_WAY_CYCLE/LIVE_BOUNDED_M0: `{(1,0),(0,1)}`, complete=True, explored=2; predecessors of M0 = (None,None).
14. reachable truncated `max_states=1`: `{M0}`, complete=False, explored=1.
15. reachability_graph complete: exact edges `{ (1,0):(('t1',(0,1)),), (0,1):(('t2',(1,0)),) }`; truncated: edges recorded to unvisited targets, complete=False.
16. firing_sequence_to: to (0,1) → `['t1']`; to M0 → `[]`; absent+complete → None; absent+truncated → None (not a proof — assert via complete flag of result).
17. deadlocks DEADLOCK_NET: `((0,),)`, complete=True, reason None; truncated search on UNBOUNDED_NET: complete=False + exact reason string; never a deadlock-free claim.
18. bounds complete LIVE_BOUNDED_M0: `bounded=True, {'p1':1,'p2':1}`; UNBOUNDED_NET `max_states=5`: `bounded=None, complete=False, reason=…`, observed `{'p':5}` (§30 mandate — never finite-bound claim).
19. incidence_matrix: TWO_WAY_CYCLE `[[-1,1],[1,-1]]`; UNBOUNDED_NET `[[1]]`; degenerate shapes (places-only P×0, transitions-only 0×T, empty 0×0).
20. place_invariants TWO_WAY_CYCLE: `[(1,1)]`; conservation check p1+p2 constant across markings; places-only → identity basis; transitions-only → []; empty → [].
21. transition_invariants TWO_WAY_CYCLE: `[(1,1)]`; transitions-only → identity basis; places-only → []; empty → [].
22. transition_liveness live net: t1/t2 True, explored=2; DEADLOCK_NET t → False; incomplete graph → `value=None, complete=False`, reason pinned.
23. is_live: live net True; net with fire-once-then-dead transition → False (that transition's result propagated); incomplete → None; empty net → `AnalysisResult(True, True, 1)` (F1).
24. SCC: TWO_WAY_CYCLE one component `{(1,0),(0,1)}`; DEADLOCK_NET single `{(0,)}`; two-component net (token flows to deadlock) → 2 components; empty net → `[frozenset({()})]`.
25. determinism: repeated analyzer calls return equal results (dataclass equality); deadlocks sorted.

### test_coverability.py behaviors

26. `coverability_tree(net)` raises NotImplementedError (v2 marker present in message).

## 9. TDD execution plan (feature_016; omt_tdd ops)

- **testlist**: one JSON array of the 26 behaviors (grouped by file) at Programming start.
- **Cycles** (red→green→refactor at the SAME test_node, F10): cycle 1 `test_model.py` (behaviors 1–12, one red commit of the file then green `errors.py`+`model.py`); cycle 2 `test_analysis.py` (13–25; green `analysis.py`); cycle 3 `test_coverability.py` (26; green `coverability.py`); placeholder deletion inside cycle-1 green; `__init__.py` docstring in cycle-1 green.
- Per-behavior node granularity kept at method level: red at `test_model.py::TestX::test_y`, green at the SAME node (F10 gotcha).
- **Pre-src gates**: `omt_kb_nav` consult (F9); first tests/ write `omt_skip{scope:"tests"}` (F8).
- Close via `omt_tdd{op:done}` with `checklist.suite_passes:true` — never `omt_skip` (D10).

## 10. Boundaries / non-goals (unchanged from PROJECT.md)

New files only: `src/agentx/model/petri_net/{__init__.py,errors.py,model.py,analysis.py,coverability.py}`, `tests/model/petri_net/{test_model.py,test_analysis.py,test_coverability.py}`; delete `test_petri_net.py`. **No** pyproject change (zero deps); **no** other src/ module touched; **no** simulator/graph.py/coverability impl/home-marking/siphons-traps/DOT/JSON/max_depth/time_limit (v2). feature_001 wiring NOT in scope (D11 — consumer rebuilds on CRC change; add-only API sufficient).

## 11. Design sign-off

All 7 must-pins closed (§1); all 10 findings disposed (§2). The blueprint is complete: §4–§7 are transcribable to code without the anchor doc; §8 is transcribable to the omt_tdd testlist. **Ready for Programming.**
