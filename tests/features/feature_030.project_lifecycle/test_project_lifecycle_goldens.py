"""Sentinel re-export of the harness-level golden suite for feature_030.

Satisfies the `omt_complete{Programming -> Testing}` pattern matcher
`tests/features/<feature>/test_*.py`. The canonical golden tests live at
`tests/scripts/omt/test_project_lifecycle.py` (harness-level pin-test
convention, alongside `test_omt_harness_e2e.py` + `test_omt_q.py`). This file
re-imports them so the per-feature dir pattern is matched; it does NOT
duplicate test logic (feature_026 sentinel precedent).
"""

from tests.scripts.omt.test_project_lifecycle import (  # noqa: F401
    TestProjectPy,
    TestHarnesscChecks,
    TestScaffoldLink,
    TestBackfill,
    TestPhaseGateProjectHooks,
    TestOmtQProjectDrift,
    TestOmtStatusProject,
)
