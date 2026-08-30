"""Weighted Place/Transition Petri-net model layer (doc §4–§10; design_001 §5).

HARNESS CLONE (feature_039, D2): byte-faithful copy of
`src/agentx/model/petri_net/model.py` for the meta-harness net layer
(meta_harness_concurrent) — only the module header carries this clone note.
Parity pinned by the 9 shared conformance vectors. Do NOT extend here (F6).

The model defines possible state changes; a marking is the state; firing
changes the state (doc §41). Semantics:

- ``M'(p) = M(p) - W(p,t) + W(t,p)`` for a fired transition ``t`` (§4).
- Enabledness is an AND over all input arcs (vacuously true for no-input
  transitions); firing is atomic; disabled firing raises
  :class:`TransitionNotEnabledError` (§5).
- ``fire_marking`` is pure (net and input marking untouched); ``fire`` is the
  mutable convenience applying the same check against the live marking (§5.4).
- Canonical ordering: ``place_order``/``transition_order`` are sorted tuples;
  markings are immutable tuples over ``place_order`` (§6.2, §29).

Edge-case policy (§8, §38, D7): self-loops legal; no-input transitions always
enabled; no-output transitions legal (consume-and-vanish); parallel
transitions distinct by name; zero-token places meaningful; the empty net is
allowed; duplicate arcs are rejected (:class:`DuplicateArcError`).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .errors import (
    DuplicateArcError,
    DuplicatePlaceError,
    InvalidModelError,
    PetriNetError,
    TransitionNotEnabledError,
    UnknownPlaceError,
    UnknownTransitionError,
)


@dataclass
class PetriNet:
    """Weighted P/T net ``N = (P, T, F, W, M0)`` (doc §10 canonical engine).

    ``inputs``/``outputs`` map transition -> {place: weight} (pre-set ``•t``
    / post-set ``t•``). ``marking`` is the live state; ``initial_marking``
    (M0) is what :meth:`reset` restores. Add-only mutation (build-once, §34);
    no ``remove_*`` API in v1.
    """

    places: set[str] = field(default_factory=set)
    transitions: set[str] = field(default_factory=set)
    inputs: dict[str, dict[str, int]] = field(default_factory=dict)
    outputs: dict[str, dict[str, int]] = field(default_factory=dict)
    marking: dict[str, int] = field(default_factory=dict)
    initial_marking: dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutation API (§9)
    # ------------------------------------------------------------------

    def add_place(self, name: str, tokens: int = 0) -> None:
        if not name:
            raise ValueError("Place name cannot be empty")
        if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
            raise ValueError("Token count must be a non-negative integer")
        if name in self.places:
            raise DuplicatePlaceError(f"Place already exists: {name}")
        self.places.add(name)
        self.marking[name] = tokens
        self.initial_marking[name] = tokens

    def add_transition(self, name: str) -> None:
        if not name:
            raise ValueError("Transition name cannot be empty")
        if name in self.transitions:
            # F4 asymmetry (§10): duplicate transition is a plain ValueError.
            raise ValueError(f"Transition already exists: {name}")
        self.transitions.add(name)
        self.inputs[name] = {}
        self.outputs[name] = {}

    def add_input(self, place: str, transition: str, weight: int = 1) -> None:
        self._validate_arc(place, transition, weight)
        if place in self.inputs[transition]:
            raise DuplicateArcError(f"Input arc already exists: {place} -> {transition}")
        self.inputs[transition][place] = weight

    def add_output(self, transition: str, place: str, weight: int = 1) -> None:
        # §9 gotcha: argument order follows arc direction (transition, place)
        # — swapped vs add_input(place, transition). Call by keyword.
        self._validate_arc(place, transition, weight)
        if place in self.outputs[transition]:
            raise DuplicateArcError(f"Output arc already exists: {transition} -> {place}")
        self.outputs[transition][place] = weight

    def _validate_arc(self, place: str, transition: str, weight: int) -> None:
        if place not in self.places:
            raise UnknownPlaceError(place)
        if transition not in self.transitions:
            raise UnknownTransitionError(transition)
        if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
            raise ValueError("Arc weight must be a positive integer")

    def _require_transition(self, transition: str) -> None:
        if transition not in self.transitions:
            raise UnknownTransitionError(transition)

    # ------------------------------------------------------------------
    # Order / marking API (§6)
    # ------------------------------------------------------------------

    @property
    def place_order(self) -> tuple[str, ...]:
        return tuple(sorted(self.places))

    @property
    def transition_order(self) -> tuple[str, ...]:
        return tuple(sorted(self.transitions))

    @property
    def place_index(self) -> dict[str, int]:
        return {p: i for i, p in enumerate(self.place_order)}

    def current_marking(self) -> tuple[int, ...]:
        return tuple(self.marking[p] for p in self.place_order)

    def initial_marking_tuple(self) -> tuple[int, ...]:
        return tuple(self.initial_marking[p] for p in self.place_order)

    def marking_to_dict(self, marking: tuple[int, ...]) -> dict[str, int]:
        if len(marking) != len(self.places):
            raise ValueError("Marking length does not match place count")
        if any(tokens < 0 for tokens in marking):
            raise ValueError("Marking contains a negative token count")
        return dict(zip(self.place_order, marking))

    # ------------------------------------------------------------------
    # Execution API (§4–§5)
    # ------------------------------------------------------------------

    def is_enabled_at(self, marking: tuple[int, ...], transition: str) -> bool:
        self._require_transition(transition)
        m = self.marking_to_dict(marking)  # validation propagates (ValueError)
        return all(m[p] >= w for p, w in self.inputs[transition].items())

    def enabled_transitions_at(self, marking: tuple[int, ...]) -> list[str]:
        return [t for t in self.transition_order if self.is_enabled_at(marking, t)]

    def fire_marking(self, marking: tuple[int, ...], transition: str) -> tuple[int, ...]:
        """Pure firing: return the successor marking; raise when disabled.

        Error precedence (must-pin 3): :class:`UnknownTransitionError`, then
        marking ``ValueError``, then :class:`TransitionNotEnabledError`.
        The net and the input marking are never mutated (atomic, §5).
        """
        self._require_transition(transition)
        if not self.is_enabled_at(marking, transition):
            raise TransitionNotEnabledError(transition)
        index = self.place_index
        result = list(marking)
        for place, weight in self.inputs[transition].items():
            result[index[place]] -= weight
        for place, weight in self.outputs[transition].items():
            result[index[place]] += weight
        return tuple(result)

    def fire(self, transition: str) -> None:
        """Mutable convenience: apply ``fire_marking`` to the live marking.

        All errors propagate; the live marking is unchanged on error.
        """
        self.marking = self.marking_to_dict(
            self.fire_marking(self.current_marking(), transition)
        )

    def reset(self) -> None:
        """Restore the initial marking M0 (structure untouched)."""
        self.marking = self.initial_marking.copy()

    # ------------------------------------------------------------------
    # Structural queries (§24, F5)
    # ------------------------------------------------------------------

    def pre_set(self, node: str) -> frozenset[str]:
        """Transition -> input places; place -> producer transitions (§2.1)."""
        in_places, in_transitions = self._dispatch(node)
        if in_transitions:
            return frozenset(self.inputs[node])
        return frozenset(t for t in self.transition_order if node in self.outputs[t])

    def post_set(self, node: str) -> frozenset[str]:
        """Transition -> output places; place -> consumer transitions (§2.1)."""
        in_places, in_transitions = self._dispatch(node)
        if in_transitions:
            return frozenset(self.outputs[node])
        return frozenset(t for t in self.transition_order if node in self.inputs[t])

    def _dispatch(self, node: str) -> tuple[bool, bool]:
        in_places = node in self.places
        in_transitions = node in self.transitions
        if in_places and in_transitions:
            raise InvalidModelError(f"Ambiguous node name: {node}")
        if not in_places and not in_transitions:
            raise PetriNetError(f"Unknown node: {node}")
        return in_places, in_transitions
