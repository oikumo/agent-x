"""Typed error hierarchy for the Petri-net library (doc §5.3/§10).

HARNESS CLONE (feature_039, D2): byte-faithful copy of
`src/agentx/model/petri_net/errors.py` for the meta-harness net layer
(meta_harness_concurrent). Parity pinned by the 9 shared conformance
vectors. Do NOT extend here — sync with the library as one deliberate,
versioned event (F6).
"""


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
