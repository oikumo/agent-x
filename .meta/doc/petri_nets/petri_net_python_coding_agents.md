# Petri Nets in Python — Coding Agent Implementation and Analysis Guide

## Purpose

This document gives a coding agent enough information to implement a practical Petri-net library in Python.

The library should have **two clearly separated layers**:

1. **Execution/model layer** — places, transitions, arcs, markings, enabledness, and firing.
2. **Analysis layer** — reachability, deadlocks, boundedness, invariants, transition liveness, and related structural/state-space analysis.

Correctness and explicit semantics are more important than optimization in the first version. The analysis API should operate on the model layer without coupling it to a UI, database, or visualization framework.

---

## Scope and Build Order (v1 vs v2)

This document describes a complete toolkit, but the **first version should be built in two stages**:

- **v1 (core — the feasible first deliverable):** the model layer (§3–§10) and the BFS-based analyses — reachability, reachability graph, firing sequences, deadlocks, bounds — plus exact P/T-invariant algebra (§18–§19). Every analysis returns completeness-explicit results (§27–§28). v1 corresponds to Definition-of-Done items 1–17 and 19 (§40).
- **v2 (advanced — follow-up):** coverability trees (§17), siphons/traps (§25), home markings (§22), and reporting/export (§36 advanced). v2 corresponds to DoD item 18 and the advanced checklist.

Everything in v1 must be complete and tested before v2 is attempted. Coverability in particular is the most subtle algorithm in this document and must not be rushed.

---

## 1. Petri-Net Foundations

A **Petri net** is a formal model for systems in which **state, resources, events, and concurrency** interact. Unlike a conventional flowchart, a Petri net does not describe only one execution path. It describes a set of possible state changes and makes concurrency and synchronization explicit.

This document targets a **weighted Place/Transition (P/T) Petri net**. The model is intentionally small: places hold indistinguishable tokens, transitions represent events, and directed weighted arcs define which tokens an event consumes and produces.

### 1.1 The four core concepts

A Petri net has four essential elements:

- **Place (`P`)** — a state holder, condition, buffer, or resource location. Places do not execute actions.
- **Transition (`T`)** — an event or action that may occur when its input requirements are satisfied. Transitions do not store tokens.
- **Arc (`F`)** — a directed connection between a place and a transition. Arcs are allowed in both directions, but never directly from place to place or transition to transition.
- **Token / marking (`M`)** — tokens represent the current state of the modeled system. A marking assigns a non-negative integer number of tokens to every place.

The most important distinction is:

> **The places, transitions, and arcs define the net's structure; the marking defines its current state.**

For example:

```text
        input arc                 output arc
[Waiting Jobs] --1--> (Start Job) --1--> [Running Jobs]
       place             transition            place
```

If `Waiting Jobs` contains one or more tokens, `Start Job` may be enabled. When it fires, one token is removed from `Waiting Jobs` and one token is added to `Running Jobs`.

### 1.2 Why Petri nets are different from ordinary state machines

Petri nets are particularly useful when several activities can occur independently or when an event requires multiple conditions simultaneously.

For example:

```text
[Part A] --1--\
               \
                > (Assemble) --> [Product]
               /
[Part B] --1--/
```

`Assemble` requires **both** an `A` token and a `B` token. Firing consumes one token from each input place and produces one token in `Product`.

Petri nets also represent choice naturally:

```text
                    --> (Approve) -->
[Request] --1-------+
                    --> (Reject)  -->
```

If both transitions are enabled, either firing is possible. An analysis algorithm must therefore consider both possible successors unless a separate policy intentionally chooses one.

This ability to represent **synchronization, conflict, concurrency, and resource consumption** is central to the model and should not be reduced to "nodes and edges."

---

## 2. Formal Model

A weighted P/T Petri net is represented by the tuple:

```text
N = (P, T, F, W, M0)
```

where:

- `P` is a finite set of places.
- `T` is a finite set of transitions, with `P ∩ T = ∅`.
- `F` is the set of directed arcs:

```text
F ⊆ (P × T) ∪ (T × P)
```

- `W` assigns a positive integer weight to every arc:

```text
W : F -> N+
```

- `M0` is the initial marking.

A **marking** is a function:

```text
M : P -> N
```

where `M(p)` is the number of tokens currently in place `p`.

The current marking is the runtime state. `M0` is simply the starting state; later markings are produced by firing transitions.

### 2.1 Pre-set and post-set

For a transition `t`, define:

```text
•t = { p in P | (p, t) in F }     # input places
t• = { p in P | (t, p) in F }     # output places
```

The same notation can be used for places to identify their neighboring transitions.

The implementation should preserve this distinction because it makes the semantics of enabledness, firing, and structural analysis much clearer.

### 2.2 Input and output weights

For an input place `p` and transition `t`:

```text
W(p, t)
```

is the number of tokens consumed from `p` when `t` fires.

For an output place `p`:

```text
W(t, p)
```

is the number of tokens produced in `p`.

An arc weight must be a **positive integer**. A missing arc means weight zero.

Example:

```text
[Stock: 3] --2--> (Sell) --1--> [Revenue]
```

If `Sell` fires:

```text
Stock   = 1
Revenue = 1
```

The two numbers have different semantic roles: the input weight is a requirement and consumption amount; the output weight is a production amount.

---

## 3. Places

A **place** represents a location in which tokens can reside. Tokens are indistinguishable in a basic P/T net: the model cares about how many tokens are present, not which individual token is present.

A minimal Python representation is:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Place:
    name: str
```

For the first implementation, a place name is sufficient. Future metadata such as labels, capacities, colors, or visualization coordinates should not be required by the core semantics.

The reference engine (§10) treats **names (strings) as the canonical identity** of places and transitions. The dataclasses above are optional metadata carriers for future extensions; they are not required by the engine.

### 3.1 What a token means

The meaning of a token is domain-specific.

Depending on the model, a token may represent:

- a job waiting for service,
- an available machine,
- a permit or authorization,
- a message,
- a physical item,
- a unit of capacity,
- or simply a logical condition.

The Petri-net engine should **not** assign domain meaning to tokens. It should only enforce their integer counts and the transition rules that consume and produce them.

### 3.2 Zero tokens are meaningful

A place may contain zero tokens. Zero does not mean that the place is absent; it means that the modeled state currently contains no tokens there.

---

## 4. Transitions

A **transition** represents an event that changes the marking.

A minimal representation is:

```python
@dataclass(frozen=True)
class Transition:
    name: str
```

A transition has no tokens of its own. Its behavior is completely determined by its input and output arcs in a basic P/T net.

As with places, the engine identifies transitions by name (string); the dataclass is optional metadata.

### 4.1 Transition enabling

A transition is **enabled** in marking `M` when every input place contains at least the number of tokens required by its input arc.

Formally:

```text
t is enabled in M
iff
for every p in •t:

    M(p) >= W(p, t)
```

This is an **AND condition** across all input places.

For:

```text
[A: 2] --2--\
             > (t) --> [C]
[B: 1] --1--/
```

`t` is enabled exactly when:

```text
A >= 2 AND B >= 1
```

The transition does not partially fire if only one requirement is satisfied.

A transition with **no input places** is always enabled in the basic P/T semantics because there are no token requirements to violate.

### 4.2 Conflict and concurrency

If two transitions require the same token, they may be in **conflict**:

```text
             --> (t1)
[A: 1] ------+
             --> (t2)
```

With one token in `A`, both transitions may initially be enabled, but firing either one consumes the token. The other transition may then become disabled.

By contrast, independent transitions can be enabled simultaneously without competing for the same tokens. This is one of the main ways Petri nets represent concurrency.

The implementation should not infer a scheduling order from a Python `set`. When enumerating enabled transitions for deterministic tests or reports, use a stable ordering.

---

## 5. Firing Semantics

**Firing** is the state-changing operation of a Petri net.

If transition `t` is enabled in marking `M`, firing it produces a new marking `M'`.

For each place `p`:

```text
M'(p) = M(p) - W(p, t) + W(t, p)
```

where a missing input or output arc contributes zero.

This single equation captures both token consumption and token production.

### 5.1 Example

Given:

```text
[A: 2] --1--\
             > (t) --2--> [B]
[C: 1] --1--/
```

the marking:

```text
A = 2
B = 0
C = 1
```

enables `t`.

After firing:

```text
A = 1
B = 2
C = 0
```

The transition consumes one token from each input place and produces two tokens in `B`.

### 5.2 Firing is atomic

A transition firing should be treated as one atomic state change:

```text
M  --t-->  M'
```

The implementation must not expose an intermediate state in which some inputs have been consumed but outputs have not yet been produced.

This matters both for correctness and for analysis: a successor marking is produced directly from a predecessor marking.

### 5.3 Disabled transitions cannot fire

Attempting to fire a disabled transition is an error in the core API.

The engine should check enabledness **before** modifying any marking. If the transition is not enabled, the original marking must remain unchanged.

A suitable exception is:

```python
class TransitionNotEnabledError(PetriNetError):
    pass
```

### 5.4 Pure firing operation

For analysis, firing should preferably be exposed as a pure transformation:

```python
def fire_marking(
    marking: tuple[int, ...],
    transition: str,
) -> tuple[int, ...]:
    ...
```

It should:

1. validate the transition;
2. check enabledness against the supplied marking;
3. calculate the successor marking;
4. return the new marking;
5. never mutate the live net.

The mutable convenience method `fire()` can then apply that result to the current runtime marking.

---

## 6. Markings and State Representation

A **marking** is the complete state of the net at a particular instant.

For example:

```python
marking = {
    "waiting": 2,
    "running": 1,
    "finished": 0,
}
```

The marking must contain a token count for every known place.

### 6.1 Runtime representation vs analysis representation

A dictionary is convenient for a user-facing API:

```python
{
    "waiting": 2,
    "running": 1,
    "finished": 0,
}
```

For state-space analysis, use a canonical immutable tuple:

```python
(2, 1, 0)
```

if the stable place order is:

```python
("waiting", "running", "finished")
```

This distinction is important:

```text
Petri-net structure
    places + transitions + arcs

Current state
    marking

Successor state
    result of firing an enabled transition
```

The analyzer should treat markings as values, not as mutable objects belonging to the live simulation state.

### 6.2 Canonical ordering

A marking tuple is meaningful only when its place order is stable.

The implementation should maintain:

```python
place_order: tuple[str, ...]
place_index: dict[str, int]
```

and use the same ordering everywhere.

Do not depend on the iteration order of an unordered `set` when constructing marking tuples, graph edges, or analysis results.

### 6.3 Marking validity

For a basic P/T net, every marking must satisfy:

```text
M(p) >= 0
```

for every place `p`.

A firing operation should never produce a negative token count because enabledness guarantees that all consumed tokens are available.

If a caller supplies an external marking for analysis, validate its length and non-negativity before using it.

---

## 7. Incidence-Matrix View

The operational semantics above have an equivalent matrix representation that is important for invariants and structural analysis.

Let:

```text
C[p,t] = W(t,p) - W(p,t)
```

Then `C` is the **incidence matrix** of the net.

If `M` is represented as a column vector and transition `t` fires once, the marking changes according to:

```text
M' = M + C[:, t]
```

For a firing-count vector `σ`, the corresponding state equation is:

```text
M' = M + Cσ
```

This equation is useful for reasoning about possible token changes, but it is not by itself a complete firing-sequence semantics: a vector may satisfy the equation even when no valid sequence of enabled transitions can realize it.

That distinction should be preserved in the implementation and documentation.

---

## 8. Self-Loops, Source Transitions, and Sinks

Several edge cases follow directly from the formal semantics.

### 8.1 Self-loop

A transition may both consume from and produce to the same place:

```text
[counter] --1--> (process) --1--> [counter]
```

The net effect is zero tokens in `counter`:

```text
M'(counter) = M(counter) - 1 + 1
```

The implementation must apply both contributions rather than treating the arc as invalid.

### 8.2 Transition with no input places

A transition with no input arcs is always enabled in a basic P/T net.

Example:

```text
            (generate) --1--> [Jobs]
```

Every firing adds one token to `Jobs`.

This pattern can therefore create an unbounded net when repeated indefinitely.

### 8.3 Transition with no output places

A transition with input arcs but no output arcs consumes its required tokens and produces nothing:

```text
[Jobs] --1--> (discard)
```

This is valid and can model consumption, completion, loss, or disposal.

### 8.4 Parallel transitions

Two transitions may have identical pre-sets and post-sets:

```text
[A] --> (t1) --> [B]
[A] --> (t2) --> [B]
```

They are still distinct transitions. Analysis results should preserve their names because the transition labels describe different events even when they have the same token effect.

---

### 8.5 Petri-Net Semantics in One Example

The following small net demonstrates the core semantics:

```text
             --1--> (start) --1-->
            /                       \
[Waiting]                         [Running]
    |                                |
    |                                |
    +---------- 1 token -------------+
```

A clearer operational example is:

```text
[Waiting: 1] --1--> (start) --1--> [Running: 0]
```

Initial marking:

```text
M0 = {
    Waiting: 1,
    Running: 0
}
```

Enabledness:

```text
Waiting >= 1
```

therefore `start` is enabled.

After firing:

```text
M1 = {
    Waiting: 0,
    Running: 1
}
```

Now `start` is disabled because:

```text
Waiting < 1
```

If another transition consumes from `Running`:

```text
[Running] --1--> (finish) --1--> [Finished]
```

then the reachable execution is:

```text
M0 --start--> M1 --finish--> M2
```

The analyzer should represent these markings explicitly and use the transition labels to describe the state changes.

#### 8.5.1 Why this example matters

This example captures the fundamental cycle of every P/T Petri-net implementation:

```text
current marking
      |
      v
check transition requirements
      |
      v
enabled?
   /      \
 no        yes
 |          |
reject      fire
              |
              v
        consume inputs
              |
              v
        produce outputs
              |
              v
        successor marking
```

The analysis layer then repeats this process over **all relevant enabled transitions**, rather than choosing only one.

---

## 9. Recommended Core API

The core model should provide:

```python
add_place(name, tokens=0)
add_transition(name)
add_input(place, transition, weight=1)
add_output(transition, place, weight=1)
is_enabled(transition)
is_enabled_at(marking, transition)
fire(transition)
fire_marking(marking, transition)
enabled_transitions()
enabled_transitions_at(marking)
current_marking()
reset()
```

The analysis layer should not directly mutate `net.marking` while exploring a state space.

---

## 10. Complete Minimal Engine

```python
from __future__ import annotations

from dataclasses import dataclass, field


class PetriNetError(Exception):
    pass


class InvalidModelError(PetriNetError):
    pass


class UnknownPlaceError(PetriNetError):
    pass


class UnknownTransitionError(PetriNetError):
    pass


class TransitionNotEnabledError(PetriNetError):
    pass


@dataclass
class PetriNet:
    places: set[str] = field(default_factory=set)
    transitions: set[str] = field(default_factory=set)
    inputs: dict[str, dict[str, int]] = field(default_factory=dict)
    outputs: dict[str, dict[str, int]] = field(default_factory=dict)
    marking: dict[str, int] = field(default_factory=dict)
    initial_marking: dict[str, int] = field(default_factory=dict)

    def add_place(self, name: str, tokens: int = 0) -> None:
        if not name:
            raise ValueError("Place name cannot be empty")
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
            raise ValueError("Token count must be a non-negative integer")
        if name in self.places:
            raise ValueError(f"Place already exists: {name}")

        self.places.add(name)
        self.marking[name] = tokens
        self.initial_marking[name] = tokens

    def add_transition(self, name: str) -> None:
        if not name:
            raise ValueError("Transition name cannot be empty")
        if name in self.transitions:
            raise ValueError(f"Transition already exists: {name}")

        self.transitions.add(name)
        self.inputs[name] = {}
        self.outputs[name] = {}

    def add_input(self, place: str, transition: str, weight: int = 1) -> None:
        self._validate_arc(place, transition, weight)
        if place in self.inputs[transition]:
            raise InvalidModelError(
                f"Input arc already exists: {place} -> {transition}"
            )
        self.inputs[transition][place] = weight

    def add_output(self, transition: str, place: str, weight: int = 1) -> None:
        self._validate_arc(place, transition, weight)
        if place in self.outputs[transition]:
            raise InvalidModelError(
                f"Output arc already exists: {transition} -> {place}"
            )
        self.outputs[transition][place] = weight

    def _validate_arc(self, place: str, transition: str, weight: int) -> None:
        if place not in self.places:
            raise UnknownPlaceError(place)
        if transition not in self.transitions:
            raise UnknownTransitionError(transition)
        if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
            raise ValueError("Arc weight must be a positive integer")

    def _require_transition(self, transition: str) -> None:
        if transition not in self.transitions:
            raise UnknownTransitionError(transition)

    @property
    def place_order(self) -> tuple[str, ...]:
        return tuple(sorted(self.places))

    @property
    def transition_order(self) -> tuple[str, ...]:
        return tuple(sorted(self.transitions))

    def current_marking(self) -> tuple[int, ...]:
        return tuple(self.marking[p] for p in self.place_order)

    def initial_marking_tuple(self) -> tuple[int, ...]:
        return tuple(self.initial_marking[p] for p in self.place_order)

    def marking_to_dict(self, marking: tuple[int, ...]) -> dict[str, int]:
        if len(marking) != len(self.place_order):
            raise ValueError("Marking length does not match place count")
        return dict(zip(self.place_order, marking))

    def is_enabled_at(self, marking: tuple[int, ...], transition: str) -> bool:
        self._require_transition(transition)
        m = self.marking_to_dict(marking)

        return all(
            m[place] >= weight
            for place, weight in self.inputs[transition].items()
        )

    def is_enabled(self, transition: str) -> bool:
        return self.is_enabled_at(self.current_marking(), transition)

    def enabled_transitions_at(self, marking: tuple[int, ...]) -> list[str]:
        return [
            t
            for t in self.transition_order
            if self.is_enabled_at(marking, t)
        ]

    def enabled_transitions(self) -> list[str]:
        return self.enabled_transitions_at(self.current_marking())

    def fire_marking(
        self,
        marking: tuple[int, ...],
        transition: str,
    ) -> tuple[int, ...]:
        self._require_transition(transition)
        if not self.is_enabled_at(marking, transition):
            raise TransitionNotEnabledError(transition)

        result = list(marking)
        indexes = {p: i for i, p in enumerate(self.place_order)}

        for place, weight in self.inputs[transition].items():
            result[indexes[place]] -= weight

        for place, weight in self.outputs[transition].items():
            result[indexes[place]] += weight

        return tuple(result)

    def fire(self, transition: str) -> None:
        next_marking = self.fire_marking(self.current_marking(), transition)
        self.marking = self.marking_to_dict(next_marking)

    def reset(self) -> None:
        self.marking = self.initial_marking.copy()
```

---

## 11. Petri-Net Analysis Layer

The analysis layer should answer questions about the behavior and structure of the net without requiring the caller to run a simulation manually.

Recommended module:

```text
petri_net/
├── model.py
├── analysis.py
├── simulator.py
├── errors.py
└── tests/
```

The main analysis object can be:

```python
class PetriNetAnalyzer:
    def __init__(self, net: PetriNet):
        self.net = net
```

Recommended first-class analysis operations:

```python
reachable_markings()
reachability_graph()
firing_sequence_to()
deadlocks()
bounds()
place_invariants()
transition_invariants()
transition_liveness()
is_live()
is_home_marking()
```

For potentially infinite state spaces, every exploration API must expose a limit such as `max_states` or `max_depth` and report whether exploration completed.

---

## 12. Reachability Analysis

A marking `M` is **reachable** when there is a sequence of enabled transition firings from the initial marking `M0` to `M`.

The safest basic implementation is breadth-first search over markings.

### Why BFS?

BFS is a good default because:

- it avoids revisiting states
- it naturally constructs a reachability graph
- it can record a shortest firing sequence to each discovered state
- it supports deadlock analysis
- it makes bounded-state analysis straightforward

### Data structure

```python
@dataclass(frozen=True)
class ReachabilityResult:
    markings: frozenset[tuple[int, ...]]
    predecessors: dict[tuple[int, ...], tuple[tuple[int, ...] | None, str | None]]
    complete: bool
    explored_states: int
```

### Implementation

```python
from collections import deque


def reachable_markings(
    net: PetriNet,
    max_states: int | None = None,
) -> ReachabilityResult:
    initial = net.initial_marking_tuple()
    queue = deque([initial])
    visited = {initial}
    predecessors = {initial: (None, None)}
    complete = True

    while queue:
        marking = queue.popleft()

        for transition in net.enabled_transitions_at(marking):
            successor = net.fire_marking(marking, transition)

            if successor in visited:
                continue

            if max_states is not None and len(visited) >= max_states:
                complete = False
                queue.clear()
                break

            visited.add(successor)
            predecessors[successor] = (marking, transition)
            queue.append(successor)

        if not complete:
            break

    return ReachabilityResult(
        markings=frozenset(visited),
        predecessors=predecessors,
        complete=complete,
        explored_states=len(visited),
    )
```

The caller must not assume that `complete=True` is possible for every Petri net. An unbounded net can have infinitely many reachable markings.

---

## 13. Reachability Graph

A reachability graph contains:

- one node per reachable marking
- one directed edge per enabled transition firing

Recommended representation:

```python
@dataclass(frozen=True)
class ReachabilityGraph:
    states: frozenset[tuple[int, ...]]
    edges: dict[tuple[int, ...], tuple[tuple[str, tuple[int, ...]], ...]]
    complete: bool
```

Implementation:

```python
def reachability_graph(
    net: PetriNet,
    max_states: int | None = None,
) -> ReachabilityGraph:
    initial = net.initial_marking_tuple()
    queue = deque([initial])
    visited = {initial}
    edges: dict[tuple[int, ...], list[tuple[str, tuple[int, ...]]]] = {}
    complete = True

    while queue:
        marking = queue.popleft()
        outgoing = []

        for transition in net.enabled_transitions_at(marking):
            successor = net.fire_marking(marking, transition)
            outgoing.append((transition, successor))

            if successor not in visited:
                if max_states is not None and len(visited) >= max_states:
                    complete = False
                    continue
                visited.add(successor)
                queue.append(successor)

        edges[marking] = outgoing

        if not complete:
            break

    frozen_edges = {
        state: tuple(outgoing)
        for state, outgoing in edges.items()
    }

    return ReachabilityGraph(
        states=frozenset(visited),
        edges=frozen_edges,
        complete=complete,
    )
```

A reachability graph is the central structure from which several analyses can be derived.

---

## 14. Recovering a Firing Sequence

Given the predecessor map from BFS, implement:

```python
def firing_sequence_to(
    result: ReachabilityResult,
    target: tuple[int, ...],
) -> list[str] | None:
    if target not in result.markings:
        return None

    transitions: list[str] = []
    current = target

    while True:
        previous, transition = result.predecessors[current]
        if previous is None:
            break
        assert transition is not None
        transitions.append(transition)
        current = previous

    transitions.reverse()
    return transitions
```

This gives a shortest firing sequence under BFS edge count.

If `target` is not in `result.markings` and `result.complete` is `False`, the returned `None` means "no sequence found in the explored prefix" — the target may still be reachable beyond the search limit. Only a complete result turns `None` into a proof of unreachability.

---

## 15. Deadlock Analysis

A **deadlock marking** is a reachable marking where no transition is enabled.

Because exploration can be truncated, deadlocks must not be returned as a bare list — that would violate the completeness rule of §27. The result carries the `complete` flag, and the markings are sorted for determinism (§29):

```python
@dataclass(frozen=True)
class DeadlockResult:
    deadlocks: tuple[tuple[int, ...], ...]
    complete: bool
    explored_states: int
    reason: str | None = None


def deadlocks(
    net: PetriNet,
    max_states: int | None = None,
) -> DeadlockResult:
    result = reachable_markings(net, max_states=max_states)

    found = sorted(
        marking
        for marking in result.markings
        if not net.enabled_transitions_at(marking)
    )

    return DeadlockResult(
        deadlocks=tuple(found),
        complete=result.complete,
        explored_states=result.explored_states,
        reason=None if result.complete else
            "State-space exploration was truncated; listed deadlocks are only those among explored states.",
    )
```

Important limitation: if exploration is incomplete because of a state limit, the returned deadlocks are only deadlocks among the explored states. The `complete` flag makes that explicit instead of pretending the result is exhaustive.

---

## 16. Boundedness Analysis

A Petri net is **bounded** when there exists a finite upper bound on tokens in every place across all reachable markings.

For a finite reachability graph, boundedness is easy to determine:

1. Explore reachable markings.
2. Compute the maximum token count observed in each place.
3. If exploration completes, those maxima are valid bounds.

Implementation:

```python
@dataclass(frozen=True)
class BoundResult:
    bounded: bool | None
    bounds: dict[str, int]
    complete: bool
    reason: str | None = None


def bounds(
    net: PetriNet,
    max_states: int | None = None,
) -> BoundResult:
    result = reachable_markings(net, max_states=max_states)
    place_order = net.place_order

    maxima = {place: 0 for place in place_order}
    for marking in result.markings:
        for i, place in enumerate(place_order):
            maxima[place] = max(maxima[place], marking[i])

    if result.complete:
        return BoundResult(
            bounded=True,
            bounds=maxima,
            complete=True,
        )

    return BoundResult(
        bounded=None,
        bounds=maxima,
        complete=False,
        reason="State-space exploration was truncated; boundedness is unknown.",
    )
```

### Important

A truncated finite search does **not** prove boundedness. It only gives observed maxima.

For serious unboundedness detection, implement a separate **coverability/tree analysis** instead of relying only on a state limit.

---

## 17. Coverability and Karp–Miller-Style Analysis

For an unbounded Petri net, the reachability graph may be infinite. A practical analyzer should therefore support **coverability analysis**.

Use `omega` (`∞`) as an abstract token count.

A marking such as:

```text
(2, ω, 0)
```

means the second place can grow without a finite bound in the abstract state.

### Ordering

Define:

```python
OMEGA = None
```

or use a dedicated singleton to distinguish `ω` from zero.

For abstract markings `a` and concrete marking `m`, define component-wise:

```text
a >= m
```

with `ω` greater than every finite integer.

### Acceleration idea

When a newly generated marking is component-wise greater than an ancestor marking, and the same transition sequence can repeat, set the strictly increasing components to `ω`.

This is the core idea behind Karp–Miller coverability trees.

A coding agent should implement this as a separate module because the algorithm is significantly more subtle than BFS.

Recommended API:

```python
@dataclass(frozen=True)
class CoverabilityResult:
    nodes: tuple[tuple[int | None, ...], ...]
    edges: tuple[tuple[int, int], ...]  # parent-index -> child-index
    complete: bool
    unbounded_places: frozenset[str]


def coverability_tree(net: PetriNet) -> CoverabilityResult:
    ...
```

The result must include the tree edges (or parent pointers): a set of nodes without their ancestor relations cannot be interpreted as a coverability tree.

**Scope note:** coverability is **v2** work (see "Scope and Build Order"). It is the most subtle algorithm in this document; do not attempt it until the v1 BFS-based analyses are complete and tested.

Minimum correctness tests should include:

- a known bounded net
- a net where one place can grow forever
- a net with multiple potentially unbounded places

Do not label a net "unbounded" merely because BFS hit `max_states`.

---

## 18. Place Invariants (P-Invariants)

A **place invariant** is an integer vector `x` satisfying:

```text
C^T x = 0
```

where `C` is the incidence matrix.

Equivalently, `x^T M` remains constant after every transition firing.

Example idea:

```text
p1 + p2 = constant
```

This can prove conservation properties such as:

- total number of resources
- number of jobs in a closed system
- conservation of tokens between places

### Incidence matrix

For each place `p` and transition `t`:

```text
C[p,t] = output_weight(t,p) - input_weight(p,t)
```

In Python, construct:

```python
def incidence_matrix(net: PetriNet):
    import numpy as np

    places = net.place_order
    transitions = net.transition_order

    matrix = np.zeros((len(places), len(transitions)), dtype=int)

    for j, transition in enumerate(transitions):
        for place in places:
            produced = net.outputs[transition].get(place, 0)
            consumed = net.inputs[transition].get(place, 0)
            matrix[places.index(place), j] = produced - consumed

    return matrix
```

For production code, avoid repeated `places.index()` calls by precomputing an index map.

### Solving the invariant equation

A numerical null-space calculation can find candidate vectors, but Petri-net invariants are normally interpreted over integers.

For a research-grade implementation, use exact rational/integer linear algebra rather than floating-point rank/null-space results. If the project prefers zero added dependencies, a small exact-rational Gaussian-elimination nullspace (~40 lines) is sufficient for v1; do not use numpy floating-point rank/null-space either way.

Recommended dependency:

```text
sympy
```

Example starting point:

```python
from sympy import Matrix


def incidence_matrix_sympy(net: PetriNet) -> Matrix:
    places = net.place_order
    transitions = net.transition_order
    p_index = {p: i for i, p in enumerate(places)}

    data = [
        [
            net.outputs[t].get(p, 0) - net.inputs[t].get(p, 0)
            for t in transitions
        ]
        for p in places
    ]
    return Matrix(data)


def place_invariants(net: PetriNet):
    c = incidence_matrix_sympy(net)
    return c.T.nullspace()
```

This returns a rational basis. Normalize vectors before exposing them as user-facing integer invariants. v1 scope: expose the exact rational basis normalized to coprime integers. Computing *minimal non-negative* invariants is research-level work and is out of scope for the first version; tests should assert conservation properties (e.g. "p1 + p2 = constant") rather than a canonical minimal vector.

---

## 19. Transition Invariants (T-Invariants)

A **transition invariant** is a vector `y` satisfying:

```text
C y = 0
```

It represents a multiset of transition firings that returns the marking to its original value, at least at the incidence-equation level.

Use:

```python
def transition_invariants(net: PetriNet):
    c = incidence_matrix_sympy(net)
    return c.nullspace()
```

Again, this is a structural property. The existence of a non-negative T-invariant does not automatically mean that every marking can execute the corresponding firing sequence.

The analyzer should document this distinction.

---

## 20. Liveness Analysis

A transition is **live** if, informally, from every reachable marking there is some future firing sequence that can eventually fire that transition.

For a **finite complete reachability graph**, a useful state-space check is:

```text
For every reachable marking M,
there exists a path from M to some marking where transition t is enabled.
```

Implementation strategy:

1. Build the complete reachability graph.
2. For a transition `t`, find all states where `t` is enabled.
3. For every reachable state, run/reuse a graph search to determine whether one of those target states is reachable.

A more efficient implementation can reverse the graph and perform one multi-source BFS from all states enabling `t`.

### Example implementation

```python
def transition_liveness(
    net: PetriNet,
    transition: str,
    graph: ReachabilityGraph,
) -> bool | None:
    if not graph.complete:
        return None

    enabling_states = {
        state
        for state in graph.states
        if net.is_enabled_at(state, transition)
    }

    if not enabling_states:
        return False

    reverse: dict[tuple[int, ...], list[tuple[int, ...]]] = {
        state: [] for state in graph.states
    }

    for source, outgoing in graph.edges.items():
        for _, target in outgoing:
            reverse.setdefault(target, []).append(source)

    stack = list(enabling_states)
    can_reach_enabled = set(enabling_states)

    while stack:
        current = stack.pop()
        for predecessor in reverse.get(current, []):
            if predecessor not in can_reach_enabled:
                can_reach_enabled.add(predecessor)
                stack.append(predecessor)

    return can_reach_enabled == set(graph.states)
```

This is only an exhaustive result when the graph itself is complete.

---

## 21. Global Liveness

To determine whether the whole net is live over a finite complete reachability graph:

```python
def is_live(net: PetriNet, graph: ReachabilityGraph) -> bool | None:
    for transition in net.transition_order:
        result = transition_liveness(net, transition, graph)
        if result is not True:
            return result
    return True
```

A result of `None` should mean "unknown because analysis was incomplete," not false.

---

## 22. Home Markings and Reachability Queries

A **home marking** is a marking reachable from every reachable marking.

For a finite reachability graph, one simple implementation is:

1. Candidate `H` must be reachable from the initial marking.
2. For every reachable state `M`, verify `H` is reachable from `M`.

This is expensive if implemented with separate BFS from every state, but acceptable for a small analyzer.

A more advanced implementation can use strongly connected components and graph algorithms.

Recommended API:

```python
def is_home_marking(
    net: PetriNet,
    target: tuple[int, ...],
    graph: ReachabilityGraph,
) -> bool | None:
    ...
```

---

## 23. Strongly Connected Components

Strongly connected components (SCCs) are useful for analyzing recurring behavior, cycles, and liveness.

Once the reachability graph exists, implement Tarjan's algorithm or Kosaraju's algorithm in a generic graph helper.

Recommended API:

```python
def strongly_connected_components(
    graph: ReachabilityGraph,
) -> list[frozenset[tuple[int, ...]]]:
    ...
```

This can later support:

- recurrent-state analysis
- cycle detection
- liveness diagnostics
- terminal component detection

Do not implement SCC logic inside the Petri-net transition engine.

---

## 24. Structural Analysis Helpers

The analyzer should also expose cheap structural queries that do not require state-space exploration:

```python
places_of_transition(t)
transitions_of_place(p)
input_places(t)
output_places(t)
pre_set(t)
post_set(t)
pre_set(place)
post_set(place)
```

For example:

```python
def pre_set(net: PetriNet, transition: str) -> frozenset[str]:
    return frozenset(net.inputs[transition])


def post_set(net: PetriNet, transition: str) -> frozenset[str]:
    return frozenset(net.outputs[transition])
```

These helpers are useful for diagnostics, visualization, and advanced analyses such as traps and siphons.

---

## 25. Siphons and Traps — Optional Structural Analysis

For a more complete analysis toolkit, implement:

- **Siphons** — sets of places whose input transitions are contained in their output transitions.
- **Traps** — sets of places whose output transitions are contained in their input transitions.

These are structural concepts and can be useful for deadlock and resource-loss analysis.

Do not attempt brute-force enumeration of all subsets for large nets. For small examples it can be acceptable, but a production implementation should use a more appropriate structural algorithm or integer programming formulation.

Suggested APIs:

```python
def minimal_siphons(net: PetriNet) -> list[frozenset[str]]:
    ...


def minimal_traps(net: PetriNet) -> list[frozenset[str]]:
    ...
```

This can be marked as an advanced feature after the core analysis toolkit is stable.

---

## 26. Simulation vs Analysis

Do not confuse simulation with analysis.

### Simulation

Simulation chooses one enabled transition at a time:

```python
while True:
    enabled = net.enabled_transitions()
    if not enabled:
        break

    transition = choose_transition(enabled)
    net.fire(transition)
```

This explores one execution path.

### Analysis

Analysis systematically explores many or all possible executions:

```text
M0
├── t1 -> M1
│        └── t3 -> M3
└── t2 -> M2
         └── t3 -> M3
```

The analyzer should therefore operate over immutable/canonical markings and maintain a visited set.

---

## 27. Analysis Result Design

Do not return bare booleans for analyses that can be incomplete.

Bad:

```python
is_bounded(net) -> False
```

when the search merely stopped at 100,000 states.

Better:

```python
@dataclass(frozen=True)
class AnalysisResult:
    value: bool | None
    complete: bool
    explored_states: int
    reason: str | None = None
```

Meaning:

- `True` = property proven
- `False` = property disproven
- `None` = unknown because the analysis was incomplete or inconclusive

This rule should be applied consistently to reachability, boundedness, liveness, and similar queries.

---

## 28. Analysis Limits

Every potentially expensive analysis should allow resource limits.

Recommended parameters:

```python
max_states: int | None = None
max_depth: int | None = None
time_limit: float | None = None
```

A coding agent should not introduce a hidden hard-coded limit that can silently produce incorrect conclusions. **v1 scope:** implement `max_states` only; `max_depth` and `time_limit` are reserved for later versions. Do not invent partial semantics for them in v1.

When a limit is hit:

1. stop cleanly
2. return partial information
3. set `complete=False`
4. provide a reason

---

## 29. Concurrency and Nondeterminism

A key reason to use Petri nets is that multiple transitions may be enabled simultaneously.

Example:

```text
        -> (t1) ->
[p] ----+
        -> (t2) ->
```

If both `t1` and `t2` are enabled, a simulator may choose either. An analyzer must account for both possibilities unless the caller explicitly asks for a constrained execution policy.

Never make analysis depend on the iteration order of a Python `set`.

Use deterministic sorted orders:

```python
for transition in net.transition_order:
    ...
```

This makes tests and generated reports reproducible.

---

## 30. Testing the Analysis Layer

The test suite should include small nets with known properties.

### Reachability

```python
def test_reachability_finds_successor():
    net = PetriNet()
    net.add_place("a", tokens=1)
    net.add_place("b", tokens=0)
    net.add_transition("move")
    net.add_input("a", "move")
    net.add_output("move", "b")

    result = reachable_markings(net)

    assert len(result.markings) == 2
    assert result.complete is True
```

### Deadlock

```python
def test_deadlock_is_detected():
    net = PetriNet()
    net.add_place("p", tokens=0)
    net.add_transition("t")
    net.add_input("p", "t")

    result = deadlocks(net)

    assert result.deadlocks == ((0,),)
    assert result.complete is True
```

### Boundedness

A move-only net should be bounded:

```text
p1 --t--> p2
```

The token simply moves between places.

### Unboundedness

Construct:

```text
      +----------+
      |          |
      v          |
[p] --t----------+
       |
       +--> [p]
```

More concretely, use an input of one token and an output of two tokens to demonstrate growth:

```text
p --1--> t --2--> p
```

Each firing increases the number of tokens by one.

BFS with no state limit does not terminate on this net, so the test must use coverability analysis or a bounded exploration limit and verify that the result is reported as incomplete rather than falsely bounded.

### P-invariant

For:

```text
p1 --t--> p2
p2 --u--> p1
```

there is a conservation law:

```text
p1 + p2 = constant
```

The analyzer should find an equivalent place invariant such as:

```text
[1, 1]
```

up to scalar multiplication/sign normalization.

### T-invariant

For the same two-way cycle:

```text
p1 --t--> p2
p2 --u--> p1
```

there is a transition invariant corresponding to firing `t` and `u` once each.

### Liveness

A simple cyclic net is live when its sole token can continue cycling forever:

```text
p1 --t--> p2 --u--> p1
```

A net with a transition that can only fire once and then becomes permanently disabled should fail the transition-liveness test.

---

## 31. Partial Analysis Module Skeleton (BFS Core)

A practical first version can look like:

```python
# analysis.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TypeAlias

from .model import PetriNet

Marking: TypeAlias = tuple[int, ...]


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
class BoundResult:
    bounded: bool | None
    bounds: dict[str, int]
    complete: bool
    reason: str | None = None


@dataclass(frozen=True)
class DeadlockResult:
    deadlocks: tuple[Marking, ...]
    complete: bool
    explored_states: int
    reason: str | None = None


class PetriNetAnalyzer:
    def __init__(self, net: PetriNet):
        self.net = net

    def reachable_markings(
        self,
        max_states: int | None = None,
    ) -> ReachabilityResult:
        initial = self.net.initial_marking_tuple()
        queue = deque([initial])
        visited = {initial}
        predecessors = {initial: (None, None)}
        complete = True

        while queue:
            marking = queue.popleft()
            for transition in self.net.enabled_transitions_at(marking):
                successor = self.net.fire_marking(marking, transition)

                if successor in visited:
                    continue

                if max_states is not None and len(visited) >= max_states:
                    complete = False
                    queue.clear()
                    break

                visited.add(successor)
                predecessors[successor] = (marking, transition)
                queue.append(successor)

            if not complete:
                break

        return ReachabilityResult(
            markings=frozenset(visited),
            predecessors=predecessors,
            complete=complete,
            explored_states=len(visited),
        )

    def deadlocks(self, max_states: int | None = None) -> DeadlockResult:
        result = self.reachable_markings(max_states)
        found = sorted(
            marking
            for marking in result.markings
            if not self.net.enabled_transitions_at(marking)
        )
        return DeadlockResult(
            deadlocks=tuple(found),
            complete=result.complete,
            explored_states=result.explored_states,
            reason=None if result.complete else
                "State-space exploration was truncated.",
        )

    def bounds(self, max_states: int | None = None) -> BoundResult:
        result = self.reachable_markings(max_states)
        maxima = {place: 0 for place in self.net.place_order}

        for marking in result.markings:
            for i, place in enumerate(self.net.place_order):
                maxima[place] = max(maxima[place], marking[i])

        if result.complete:
            return BoundResult(True, maxima, True)

        return BoundResult(
            bounded=None,
            bounds=maxima,
            complete=False,
            reason="State-space exploration was truncated.",
        )
```

Add graph, SCC, liveness, and invariant functions to this module as they mature (v1); coverability is v2 (see "Scope and Build Order").

---

## 32. Recommended Public API

Expose a stable API roughly like:

```python
from petri_net import PetriNet, PetriNetAnalyzer

net = PetriNet()

# Build model...

analyzer = PetriNetAnalyzer(net)

reachability = analyzer.reachable_markings(max_states=100_000)
deadlocks = analyzer.deadlocks(max_states=100_000)
bounds = analyzer.bounds(max_states=100_000)
graph = analyzer.reachability_graph(max_states=100_000)
p_invariants = analyzer.place_invariants()
t_invariants = analyzer.transition_invariants()
liveness = analyzer.transition_liveness("t1")
```

Keep names stable and make result types serializable when practical.

---

## 33. Performance Guidance

The state space can grow exponentially, so analysis must be designed with that in mind.

Important optimizations:

1. Represent markings as tuples, not dictionaries.
2. Precompute place indexes.
3. Precompute input requirements per transition as integer index/weight pairs.
4. Use `deque` for BFS.
5. Use sets for visited states.
6. Avoid copying the entire `PetriNet` during exploration.
7. Cache enabled-transition checks when useful.
8. Keep deterministic transition order.

The reference engine in §10 favors clarity and rebuilds indexes per call; apply the precomputations above only when profiling shows they matter, and keep the same observable semantics.

For larger nets, consider optimized matrix/vector operations, sparse matrices, partial-order reduction, symmetry reduction, or symbolic state-space methods. These should be later optimizations, not requirements for the first implementation.

---

## 34. Architecture Rules for a Coding Agent

The agent should follow these rules:

- Keep the mathematical model independent from analysis and rendering.
- Never use simulation as a substitute for exhaustive analysis.
- Never call a truncated search "proof of boundedness" or "proof of liveness."
- Use canonical immutable markings for graph/search keys.
- Treat transition firing as a pure transformation when possible.
- Keep analysis result objects explicit about completeness.
- Use exact integer arithmetic for incidence matrices and invariants.
- Do not silently impose state limits.
- Do not mutate the live marking from analysis code.
- v1 models are **build-once**: construct a net, analyze it, and if the modeled system's structure must change, construct a new `PetriNet`. `remove_place`/`remove_transition` are out of scope for v1.
- Make tests deterministic by sorting places and transitions.

---

## 35. Recommended Project Structure

```text
petri_net/
├── __init__.py
├── model.py          # PetriNet, Place, Transition, firing semantics
├── analysis.py       # reachability, deadlocks, bounds, liveness, invariants
├── coverability.py   # Karp-Miller-style analysis for unbounded nets
├── graph.py          # generic graph algorithms such as SCC
├── simulator.py      # one-path simulation policies
├── errors.py         # custom exceptions
└── tests/
    ├── test_model.py
    ├── test_analysis.py
    ├── test_coverability.py
    └── test_graph.py
```

For a tiny project, `analysis.py` can initially contain the graph helpers too. Split modules when complexity increases.

The library is **build-once** in v1: consumers that need structural adaptation (e.g. `feature_001` rebuilding its net when `USER_OBJECTIVES.md` changes CRC) construct a fresh `PetriNet`; no `remove_*` API is provided in v1 (§34).

---

## 36. Analysis Tools — Minimum Feature Set

The implementation should not be considered a complete Petri-net toolkit if it only supports firing transitions.

The **minimum analysis toolkit** should include:

- [ ] Reachability search from the initial marking.
- [ ] Reachability graph construction.
- [ ] Shortest firing sequence to a reachable marking.
- [ ] Deadlock detection.
- [ ] Boundedness analysis for finite state spaces.
- [ ] Explicit incomplete/unknown result handling when limits are hit.
- [ ] Incidence matrix construction.
- [ ] P-invariant calculation.
- [ ] T-invariant calculation.
- [ ] Transition liveness analysis on finite complete reachability graphs.
- [ ] Strongly connected component analysis.

Advanced optional tools (v2 and later):

- [ ] Coverability-tree analysis for unbounded nets.
- [ ] Home-marking analysis.
- [ ] Siphon analysis.
- [ ] Trap analysis.
- [ ] Structural deadlock analysis.
- [ ] Partial-order reduction.
- [ ] State-space export to Graphviz/DOT.
- [ ] Analysis reports in JSON.

---

## 37. Example End-to-End Analysis

Consider:

```text
        +--------+
        |        v
[A: 1] -> (t1) -> [B] -> (t2) -> [A]
```

Python:

```python
net = PetriNet()
net.add_place("A", tokens=1)
net.add_place("B", tokens=0)
net.add_transition("t1")
net.add_transition("t2")

net.add_input("A", "t1")
net.add_output("t1", "B")

net.add_input("B", "t2")
net.add_output("t2", "A")

analyzer = PetriNetAnalyzer(net)
```

Reachability:

```python
result = analyzer.reachable_markings()
```

Expected markings:

```text
(1, 0)
(0, 1)
```

Deadlocks:

```python
assert analyzer.deadlocks().deadlocks == ()
```

Bounds:

```text
A <= 1
B <= 1
```

P-invariant:

```text
A + B = 1
```

T-invariant:

```text
t1 + t2
```

The net is cyclic and the two transitions are live in the finite reachable state space.

This single example is useful as an integration test for multiple analysis tools.

---

## 38. Important Semantic Edge Cases

Most structural edge cases are already specified in §8 (self-loops, no-input transitions, no-output transitions, parallel transitions) and §3.2 (zero-token places). This section adds the API-level policies:

### Multiple arcs to the same endpoint

The internal representation should merge duplicate logical arcs by summing or replacing according to a clearly documented rule. The simplest API should reject duplicates to avoid ambiguity.

### Zero-token places

A place can legally hold zero tokens (see §3.2).

### Empty net

Decide whether an empty Petri net is allowed. If allowed, analysis should behave consistently: its initial marking is the empty tuple and there are no enabled transitions.

---

## 39. Do Not Overclaim Results

Analysis tooling must distinguish between:

```text
Proven true
Proven false
Unknown / incomplete
```

Examples:

- A complete finite reachability graph with a detected deadlock gives a proven deadlock witness.
- A truncated BFS that found no deadlock does **not** prove the net is deadlock-free.
- A finite complete state space proves boundedness.
- A finite prefix of an apparently growing state space does **not** prove unboundedness unless a valid coverability/unboundedness argument is produced.
- A complete reachability graph can support exhaustive liveness checks.
- A partial graph can only support partial diagnostics.

This distinction is one of the most important requirements for a trustworthy analysis library.

---

## 40. Definition of Done

The basic execution implementation is complete when:

1. Places can be created with initial token counts.
2. Transitions can be created.
3. Weighted input arcs and output arcs are supported.
4. Enabled transitions are computed correctly.
5. Enabled transitions can be fired correctly.
6. Invalid models and operations raise clear exceptions.

The analysis implementation is complete when:

7. Reachability search works on finite examples.
8. A reachability graph can be generated.
9. Firing sequences can be reconstructed.
10. Deadlocks can be identified.
11. Bounds can be calculated for complete finite state spaces.
12. Incomplete searches explicitly report `complete=False`.
13. Incidence matrices can be generated.
14. P-invariants can be calculated using exact arithmetic.
15. T-invariants can be calculated using exact arithmetic.
16. Transition liveness can be checked on finite complete graphs.
17. SCC analysis is available.
18. Coverability analysis exists for unbounded nets. **(v2 — see "Scope and Build Order"; not required for v1 sign-off.)**
19. Tests cover both positive results and cases where the analyzer must return "unknown."

**v1 sign-off requires items 1–17 and 19. Item 18 (coverability) is v2.**

---

## 41. Final Mental Model for the Coding Agent

The core semantics are:

```text
             MARKING M
                 |
                 v
        +------------------+
        | Enabled?         |
        +------------------+
          |            |
         no            yes
          |             |
          v             v
       reject       fire transition
                        |
                        v
             consume input tokens
                        |
                        v
             produce output tokens
                        |
                        v
               NEW MARKING M'
```

The analysis semantics are:

```text
                     Initial Marking M0
                              |
                 +------------+------------+
                 |            |            |
                t1           t2           t3
                 |            |            |
                M1           M2           M3
                 |                         |
                ...                       ...
                 |
          Reachability Graph
                 |
       +---------+----------+----------------+
       |                    |                |
    Deadlocks           Bounds          Liveness
       |                    |                |
       +------------+-------+----------------+
                    |
              Other Analysis
                    |
        +-----------+-----------+
        |                       |
    P-invariants          T-invariants
        |                       |
   conservation          cyclic firing patterns
```

The **Petri-net model defines possible state changes**. The **marking is the state**. **Firing changes the state**. The **analysis layer systematically explores or mathematically reasons about those state changes**.

That separation should guide the entire Python implementation.
