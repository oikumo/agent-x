"""Sentinel re-export of the Petri-net library test suite for feature_031.

Satisfies the `omt_complete{Programming -> Testing}` pattern matcher
`tests/features/<feature>/test_*.py`. The canonical tests live at
`tests/model/petri_net/` (`test_model.py`, `test_analysis.py`,
`test_coverability.py`) — the model-layer convention (`tests/model/<pkg>/`
mirrors `src/agentx/model/<pkg>/`; analysis_001 A6). This file re-imports
them so the per-feature dir pattern is matched; it does NOT duplicate test
logic (feature_026 / feature_030 sentinel precedent).
"""

from tests.model.petri_net.test_analysis import (  # noqa: F401
    TestBounds,
    TestDeadlocks,
    TestDeterminism,
    TestFiringSequenceTo,
    TestIncidenceMatrix,
    TestIsLive,
    TestPlaceInvariants,
    TestReachabilityGraph,
    TestReachableMarkings,
    TestStronglyConnectedComponents,
    TestTransitionInvariants,
    TestTransitionLiveness,
)
from tests.model.petri_net.test_coverability import (  # noqa: F401
    test_coverability_tree_raises_not_implemented,
)
from tests.model.petri_net.test_model import (  # noqa: F401
    TestAddValidation,
    TestArcs,
    TestBuild,
    TestDuplicateNames,
    TestEmptyNet,
    TestEnabledness,
    TestFireAndReset,
    TestFireMarking,
    TestMarkingAccessors,
    TestParallelTransitions,
    TestSelfLoop,
    TestStructuralQueries,
)
