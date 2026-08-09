"""Sentinel re-export of the harness-level golden suite for feature_026.

This thin wrapper satisfies the `omt_complete{Programming -> Testing}` pattern
matcher `tests/features/<feature>/test_*.py`. The canonical golden tests live
at `tests/scripts/omt/test_omt_q.py` (harness-level pin-test convention, alongside
`test_omt_enforcer_guard_source_pins.py` + `test_omt_harness_e2e.py`). This file
re-imports them so the per-feature dir pattern is matched; it does NOT duplicate
test logic.
"""

# Re-export every test class + helper so a collection under this feature dir
# runs the same suite as the harness-level path.
from tests.scripts.omt.test_omt_q import (  # noqa: F401
    # constants
    REPO_ROOT,
    OMT_Q_PLUGIN,
    GATE_DRIVER,
    SHARED_LIB,
    SESSION_STATE,
    STATE_PY,
    BUN,
    # helpers
    _copy_real_ir,
    _write_ledger,
    _q_probe,
    # test classes (one per behavior node)
    TestOpStateResumeSnapshot,
    TestOpPlanPredictsBeforeChain,
    TestOpDriftCountDriftDirectionB,
    TestOpStateStrandedRed,
    TestOpStateClosedViaSkip,
    TestOpStateDecreeHealth,
    TestOpStateSkipReasonTally,
    TestOpStateKnownSuiteFailuresParse,
    TestOpPlanReceiptDetail,
    TestOpStateConsultDedup,
    TestEnvelopeAsOfCommit,
    TestRunBeforeGatesDryDoesNotBreakRealPath,
)
