# Operation Spec 001 — feature_031.petri_net_library: public operation contracts

> Phase: Design companion to design_001. Each operation: signature · pre · post/effects · errors. Signatures pinned in design_001 §4–§7; this spec is the caller-facing contract. `M` = marking tuple over `place_order`.

## model.py — PetriNet

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `add_place(name, tokens=0)` | — | place added; `marking[name]=initial_marking[name]=tokens` | `ValueError` empty name / bad tokens (non-int, bool, <0); `DuplicatePlaceError` |
| `add_transition(name)` | — | transition added; empty input/output maps | `ValueError` empty name / duplicate (F4) |
| `add_input(place, transition, weight=1)` | place, transition exist | `inputs[transition][place]=weight` | `UnknownPlaceError`, `UnknownTransitionError`, `ValueError` weight ≤0/non-int/bool, `DuplicateArcError` |
| `add_output(transition, place, weight=1)` | place, transition exist | `outputs[transition][place]=weight` | same set as add_input |
| `is_enabled_at(M, t) -> bool` | t exists; M well-formed | AND over inputs (vacuous True if none) | `UnknownTransitionError`, `ValueError` malformed M |
| `enabled_transitions_at(M) -> list[str]` | M well-formed | enabled t's, sorted order | `ValueError` malformed M |
| `fire_marking(M, t) -> M'` | t exists; M well-formed | `M'(p)=M(p)−W(p,t)+W(t,p)`; PURE (net+M unchanged); atomic | `UnknownTransitionError`, `ValueError`, `TransitionNotEnabledError` |
| `fire(t) -> None` | t enabled at live marking | live marking := fire_marking result (re-validated) | same set; live marking unchanged on error |
| `reset() -> None` | — | live marking := copy of M0 | — |
| `current_marking() / initial_marking_tuple() -> tuple` | — | tuple over `place_order` (sorted) | — |
| `marking_to_dict(M) -> dict` | len(M)=|places|, all ≥0 | dict view of M | `ValueError` length/negative |
| `place_order / transition_order / place_index` | — | sorted tuples / index map (recomputed properties) | — |
| `pre_set(node) / post_set(node) -> frozenset[str]` | node is place XOR transition | neighbors per §2.1 (place: producers/consumers; transition: inputs/outputs) | `InvalidModelError` ambiguous; `PetriNetError` unknown |

## analysis.py — PetriNetAnalyzer(net) (constructor-bound)

| Op | Returns | Contract |
|---|---|---|
| `reachable_markings(*, max_states: int\|None) -> ReachabilityResult` | markings+predecessors+complete+explored_states | BFS from M0; `None`=unlimited (explicit); truncation: complete=False, preds cover visited only |
| `reachability_graph(*, max_states) -> ReachabilityGraph` | states+edges+complete | edges of explored states recorded even to unvisited targets; check `complete` before conclusions |
| `deadlocks(*, max_states) -> DeadlockResult` | sorted deadlock tuple+complete+explored+reason | truncated ⇒ partial list + pinned reason; never "deadlock-free" claim |
| `bounds(*, max_states) -> BoundResult` | bounded+bounds+complete+reason | complete ⇒ proven maxima, bounded=True; truncated ⇒ bounded=None + observed maxima only (§16) |
| `firing_sequence_to(result, target) -> list[str]\|None` | shortest sequence or None | no exploration; None = unreachable-proof ONLY if result.complete |
| `transition_liveness(t, graph) -> AnalysisResult` | True/False/None | complete graph required; incomplete ⇒ (None, False, n, reason) |
| `is_live(graph) -> AnalysisResult` | True/False/None | every transition live; empty net ⇒ (True, True, 1) (F1) |
| `strongly_connected_components(graph) -> list[frozenset[Marking]]` | Tarjan SCCs | deterministic; empty net ⇒ [frozenset({()})] |
| `incidence_matrix() -> list[list[int]]` | C[p][t]=W(t,p)−W(p,t) | exact ints; rows=places, cols=transitions, sorted orders |
| `place_invariants() / transition_invariants() -> list[tuple[int,…]]` | coprime int bases | exact Fraction RREF nullspace; degenerate ⇒ identity basis; empty ⇒ [] (F7) |

## coverability.py

| Op | Contract |
|---|---|
| `coverability_tree(net)` | raises `NotImplementedError` — v2 (Karp–Miller, doc §17) |

**Global invariants:** analysis never mutates the live marking; no result overclaims from truncation (§39); deterministic ordering everywhere (sorted places/transitions); zero external dependencies.
