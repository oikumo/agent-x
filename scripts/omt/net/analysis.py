"""Analysis layer for the Petri-net library (doc §11–§24, §31; design_001 §6).

HARNESS CLONE (feature_039, D2): byte-faithful copy of
`src/agentx/model/petri_net/analysis.py` for the meta-harness net layer
(meta_harness_concurrent) — the ONLY delta is the import
(`agentx.model.petri_net.model` → `.model`, relative inside the package).
Parity pinned by the 9 shared conformance vectors. Do NOT extend here (F6).

The analysis layer is a REASONING layer, not a simulation layer (§26/§34): it
systematically explores all relevant possibilities (BFS over markings) or
reasons exactly (rational-arithmetic invariants) and reports precisely what it
proved, disproved, or could not decide (§39 — no overclaiming):

- ``True``  = proven, ``False`` = disproven, ``None`` = unknown/incomplete.
- Every exploration API takes a required keyword-only ``max_states`` (``int |
  None``; ``None`` = explicitly unlimited — F2). A truncated search returns
  ``complete=False`` and NEVER claims "deadlock-free", ``bounded=True``, or
  "unbounded" (§17/§39).
- Analysis never mutates the live marking — pure transformations over
  immutable tuple markings (§5.4, §34). Deterministic ordering everywhere
  (sorted places/transitions, BFS fixed by ``transition_order`` — §29).
- ``transition_liveness``/``is_live``/``strongly_connected_components``
  operate on a PRECOMPUTED :class:`ReachabilityGraph` (§32); an incomplete
  graph yields ``value=None, complete=False``.
- SCC note: components are computed over the graph's vertex set
  (``graph.states``); edges to targets outside the vertex set can only come
  from a truncated graph and are dangling references (§13), so they do not
  create phantom single-state components.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from typing import TypeAlias

from .model import PetriNet

Marking: TypeAlias = tuple[int, ...]


# ---------------------------------------------------------------------------
# Result dataclasses (§31 exact — F3: no extra fields)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Analyzer (constructor-bound — lock checklist resolution)
# ---------------------------------------------------------------------------

class PetriNetAnalyzer:
    """Analysis toolkit over a :class:`PetriNet` (never mutates its marking)."""

    def __init__(self, net: PetriNet) -> None:
        self.net = net

    # ------------------------------------------------------------------
    # Shared BFS exploration core (§31)
    # ------------------------------------------------------------------

    def _explore(
        self, *, max_states: int | None
    ) -> tuple[
        frozenset[Marking],
        dict[Marking, tuple[Marking | None, str | None]],
        dict[Marking, tuple[tuple[str, Marking], ...]],
        bool,
        int,
    ]:
        """BFS from M0. Truncation finishes the current state's edges, then
        stops: edges to unvisited successors are recorded (§13), the
        successors are not enqueued, and ``complete`` is False.
        ``explored_states`` = distinct visited markings incl. the initial."""
        net = self.net
        initial = net.initial_marking_tuple()
        queue: deque[Marking] = deque([initial])
        visited: set[Marking] = {initial}
        predecessors: dict[Marking, tuple[Marking | None, str | None]] = {
            initial: (None, None)
        }
        edges: dict[Marking, list[tuple[str, Marking]]] = {}
        complete = True
        while queue:
            marking = queue.popleft()
            outgoing: list[tuple[str, Marking]] = []
            for transition in net.enabled_transitions_at(marking):
                successor = net.fire_marking(marking, transition)
                outgoing.append((transition, successor))
                if successor in visited:
                    continue
                if max_states is not None and len(visited) >= max_states:
                    complete = False
                    continue
                visited.add(successor)
                predecessors[successor] = (marking, transition)
                queue.append(successor)
            edges[marking] = outgoing
            if not complete:
                break
        return (
            frozenset(visited),
            predecessors,
            {m: tuple(o) for m, o in edges.items()},
            complete,
            len(visited),
        )

    # ------------------------------------------------------------------
    # Exploration APIs (F2 signatures: required keyword-only max_states)
    # ------------------------------------------------------------------

    def reachable_markings(self, *, max_states: int | None) -> ReachabilityResult:
        states, preds, _edges, complete, n = self._explore(max_states=max_states)
        return ReachabilityResult(
            markings=states, predecessors=preds, complete=complete, explored_states=n
        )

    def reachability_graph(self, *, max_states: int | None) -> ReachabilityGraph:
        states, _preds, edges, complete, _n = self._explore(max_states=max_states)
        return ReachabilityGraph(states=states, edges=edges, complete=complete)

    def deadlocks(self, *, max_states: int | None) -> DeadlockResult:
        states, _preds, _edges, complete, n = self._explore(max_states=max_states)
        deadlocks = tuple(
            sorted(m for m in states if self.net.enabled_transitions_at(m) == [])
        )
        reason = None
        if not complete:
            reason = (
                "State-space exploration was truncated; "
                "listed deadlocks are only those among explored states."
            )
        return DeadlockResult(
            deadlocks=deadlocks, complete=complete, explored_states=n, reason=reason
        )

    def bounds(self, *, max_states: int | None) -> BoundResult:
        states, _preds, _edges, complete, _n = self._explore(max_states=max_states)
        maxima = {p: 0 for p in self.net.place_order}
        for marking in states:
            for i, tokens in enumerate(marking):
                place = self.net.place_order[i]
                if tokens > maxima[place]:
                    maxima[place] = tokens
        if complete:
            return BoundResult(bounded=True, bounds=maxima, complete=True)
        return BoundResult(
            bounded=None,
            bounds=maxima,
            complete=False,
            reason="State-space exploration was truncated; boundedness is unknown.",
        )

    # ------------------------------------------------------------------
    # Graph-driven APIs (no exploration; §32)
    # ------------------------------------------------------------------

    def firing_sequence_to(
        self, result: ReachabilityResult, target: Marking
    ) -> list[str] | None:
        """Shortest (BFS edge count) firing sequence to ``target``, or None.

        ``None`` is a PROOF of unreachability only when ``result.complete``
        is True (§14); on a truncated result it means "not found among the
        explored states".
        """
        if target not in result.markings:
            return None
        sequence: list[str] = []
        current = target
        while True:
            previous, transition = result.predecessors[current]
            if previous is None:
                break
            assert transition is not None  # non-initial predecessors carry a label
            sequence.append(transition)
            current = previous
        sequence.reverse()
        return sequence

    def transition_liveness(
        self, transition: str, graph: ReachabilityGraph
    ) -> AnalysisResult:
        """Is ``transition`` live on this COMPLETE graph (§20–§21, §32)?

        A transition is live when from every reachable state an enabling
        state is reachable (reverse multi-source BFS). Incomplete graph ->
        ``value=None`` (unknown), never a bare bool.
        """
        if not graph.complete:
            return AnalysisResult(
                None, False, len(graph.states),
                "Reachability graph is incomplete; liveness is unknown.",
            )
        enabling = {
            s for s in graph.states if self.net.is_enabled_at(s, transition)
        }
        if not enabling:
            return AnalysisResult(False, True, len(graph.states))
        reverse: dict[Marking, list[Marking]] = {s: [] for s in graph.states}
        for state in sorted(graph.states):
            for _t, successor in graph.edges.get(state, ()):
                if successor in reverse:
                    reverse[successor].append(state)
        can_reach = set(enabling)
        stack = sorted(enabling)
        while stack:
            state = stack.pop()
            for predecessor in reverse.get(state, ()):
                if predecessor not in can_reach:
                    can_reach.add(predecessor)
                    stack.append(predecessor)
        return AnalysisResult(
            can_reach == set(graph.states), True, len(graph.states)
        )

    def is_live(self, graph: ReachabilityGraph) -> AnalysisResult:
        """Is the whole net live on this COMPLETE graph (every transition)?

        Empty net -> ``AnalysisResult(True, True, 1)`` (F1: §31 uniform rule,
        ``explored_states == len(graph.states)``).
        """
        if not graph.complete:
            return AnalysisResult(
                None, False, len(graph.states),
                "Reachability graph is incomplete; global liveness is unknown.",
            )
        for transition in self.net.transition_order:
            result = self.transition_liveness(transition, graph)
            if result.value is not True:
                return result
        return AnalysisResult(True, True, len(graph.states))

    def strongly_connected_components(
        self, graph: ReachabilityGraph
    ) -> list[frozenset[Marking]]:
        """Tarjan SCCs over the graph's vertex set (§23).

        Recursive Tarjan (recursion limit fine for v1 test nets). Neighbors
        are followed in edge-tuple order, start nodes in sorted-state order,
        and edge targets outside ``graph.states`` (possible only on truncated
        graphs) are not treated as vertices. Empty net ->
        ``[frozenset({()})]``.
        """
        indices: dict[Marking, int] = {}
        lowlinks: dict[Marking, int] = {}
        on_stack: set[Marking] = set()
        stack: list[Marking] = []
        components: list[frozenset[Marking]] = []
        counter = 0
        states = set(graph.states)

        def strongconnect(v: Marking) -> None:
            nonlocal counter
            indices[v] = lowlinks[v] = counter
            counter += 1
            stack.append(v)
            on_stack.add(v)
            for _t, w in graph.edges.get(v, ()):
                if w not in states:
                    continue
                if w not in indices:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif w in on_stack:
                    lowlinks[v] = min(lowlinks[v], indices[w])
            if lowlinks[v] == indices[v]:
                component: set[Marking] = set()
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    component.add(w)
                    if w == v:
                        break
                components.append(frozenset(component))

        for v in sorted(graph.states):
            if v not in indices:
                strongconnect(v)
        return components

    # ------------------------------------------------------------------
    # Exact algebra (§7/§18/§19; D4 zero-dependency; F6/F7)
    # ------------------------------------------------------------------

    def incidence_matrix(self) -> list[list[int]]:
        """``C[p][t] = W(t,p) - W(p,t)``; rows=``place_order``, cols=``transition_order``."""
        return [
            [
                self.net.outputs[t].get(p, 0) - self.net.inputs[t].get(p, 0)
                for t in self.net.transition_order
            ]
            for p in self.net.place_order
        ]

    def place_invariants(self) -> list[tuple[int, ...]]:
        """Basis of ``Cᵀ x = 0`` (token-conservation laws), coprime int tuples.

        Degenerate nets (F7): places-but-no-transitions -> identity basis;
        empty net -> ``[]``.
        """
        matrix = self.incidence_matrix()
        n_places = len(self.net.place_order)
        if n_places == 0:
            return []
        transposed = [list(row) for row in zip(*matrix)] if matrix else []
        return [
            _coprime_int_vector(v)
            for v in nullspace(transposed, n_cols=n_places)
        ]

    def transition_invariants(self) -> list[tuple[int, ...]]:
        """Basis of ``C y = 0`` (cyclic firing multisets), coprime int tuples.

        Doc caveat: a non-negative T-invariant is a necessary but not always
        realizable firing count vector (§19). Degenerate nets (F7):
        transitions-but-no-places -> identity basis; empty net -> ``[]``.
        """
        matrix = self.incidence_matrix()
        n_trans = len(self.net.transition_order)
        if n_trans == 0:
            return []
        return [
            _coprime_int_vector(v)
            for v in nullspace(matrix, n_cols=n_trans)
        ]


# ---------------------------------------------------------------------------
# Exact rational nullspace (§18 — D4: pure-Python, zero dependencies)
# ---------------------------------------------------------------------------

def nullspace(
    matrix: list[list[int]], n_cols: int | None = None
) -> list[list[Fraction]]:
    """Exact nullspace basis via Fraction Gauss–Jordan to FULL RREF.

    Free columns each emit one basis vector: 1 at the free column,
    ``-rows[pivot_row[c]][f]`` at each pivot column ``c``, 0 elsewhere.
    ``n_cols`` is inferred from the first row when None (0 for an empty
    matrix) — PASS IT EXPLICITLY on degenerate (zero-row) shapes (F7).
    """
    rows = [list(map(Fraction, row)) for row in matrix]
    n_rows = len(rows)
    if n_cols is None:
        n_cols = len(rows[0]) if rows else 0
    pivot_row_of_col: dict[int, int] = {}
    r = 0
    for c in range(n_cols):
        pivot = None
        for i in range(r, n_rows):
            if rows[i][c] != 0:
                pivot = i
                break
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        factor = rows[r][c]
        rows[r] = [x / factor for x in rows[r]]
        for i in range(n_rows):
            if i != r and rows[i][c] != 0:
                f = rows[i][c]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[r])]
        pivot_row_of_col[c] = r
        r += 1
        if r == n_rows:
            break
    basis: list[list[Fraction]] = []
    for f in range(n_cols):
        if f in pivot_row_of_col:
            continue
        vec = [Fraction(0)] * n_cols
        vec[f] = Fraction(1)
        for c, pivot_row in pivot_row_of_col.items():
            vec[c] = -rows[pivot_row][f]
        basis.append(vec)
    return basis


def _coprime_int_vector(vec: list[Fraction]) -> tuple[int, ...]:
    """Deterministic integer representative: LCM-scale to ints, divide by the
    gcd-content, negate when the first nonzero component is negative (§19)."""
    lcm = 1
    for x in vec:
        lcm = lcm * x.denominator // gcd(lcm, x.denominator)
    ints = [int(x * lcm) for x in vec]
    content = 0
    for v in ints:
        content = gcd(content, abs(v))
    if content > 1:
        ints = [v // content for v in ints]
    for v in ints:
        if v != 0:
            if v < 0:
                ints = [-x for x in ints]
            break
    return tuple(ints)
