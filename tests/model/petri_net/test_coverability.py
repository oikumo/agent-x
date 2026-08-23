"""Coverability stub tests (design_001 §8; DoD 18 = v2, out of v1 scope).

Imports are deferred inside test bodies for RED-collection safety (design_001
§8): at cycle-3 RED ``coverability.py`` does not exist yet.
"""
from __future__ import annotations

import pytest


def test_coverability_tree_raises_not_implemented():
    from agentx.model.petri_net.coverability import coverability_tree
    from agentx.model.petri_net.model import PetriNet

    with pytest.raises(NotImplementedError, match="v2"):
        coverability_tree(PetriNet())
