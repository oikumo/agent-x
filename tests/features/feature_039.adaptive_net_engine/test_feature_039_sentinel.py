"""Sentinel bridge for feature_039.adaptive_net_engine.

Satisfies the `omt_complete{Programming -> Testing}` pattern matcher
`tests/features/<feature>/test_*.py`. The feature's CANONICAL test suite
lives at `tests/scripts/omt/test_net_{conformance,engine,state,cli}.py`
(37 tests at feature completion: 11 conformance + 8 engine + 7 state +
11 CLI; evidence @
`6.testing/features/feature_039.adaptive_net_engine/test_report.md`).

This sentinel executes that suite via a pytest subprocess so the per-feature
pytest dir runs the feature's real tests (feature_036 sentinel precedent:
duplicates execution, not logic — plain re-export is NOT usable here because
the canonical modules carry module-local fixtures, which do not cross a
re-export boundary). The structural test below keeps the sentinel non-vacuous
on partial checkouts.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

CANONICAL_SUITE = [
    "tests/scripts/omt/test_net_conformance.py",
    "tests/scripts/omt/test_net_engine.py",
    "tests/scripts/omt/test_net_state.py",
    "tests/scripts/omt/test_net_cli.py",
]

FEATURE_SRC_FILES = [
    "scripts/omt/net/__init__.py",
    "scripts/omt/net/errors.py",
    "scripts/omt/net/model.py",
    "scripts/omt/net/analysis.py",
    "scripts/omt/net/io.py",
    "scripts/omt/net/conformance.py",
    "scripts/omt/net/state.py",
    "scripts/omt/net/cli.py",
    "scripts/omt/net_check.py",
]

CONFORMANCE_DIR = REPO_ROOT / "shared" / "petri-net" / "conformance" / "analysis-v1"


def test_feature_files_exist() -> None:
    """Structural floor (always on): the feature's engine/state/CLI sources,
    the canonical suite, and the 9-vector conformance corpus exist where the
    feature pinned them."""
    missing = [f for f in FEATURE_SRC_FILES if not (REPO_ROOT / f).is_file()]
    assert not missing, f"feature_039 source files missing: {missing}"
    missing_tests = [f for f in CANONICAL_SUITE if not (REPO_ROOT / f).is_file()]
    assert not missing_tests, f"canonical suite files missing: {missing_tests}"
    vectors = list(CONFORMANCE_DIR.glob("*.json")) if CONFORMANCE_DIR.is_dir() else []
    assert len(vectors) >= 9, f"expected >=9 conformance vectors, found {len(vectors)}"


def test_canonical_suite_green() -> None:
    """Execute the canonical pytest suite (37/37 at feature completion)."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *CANONICAL_SUITE, "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        f"canonical net suite failed (exit {proc.returncode}):\n{output[-4000:]}"
    )
    summary = re.search(r"(\d+) passed", output)
    assert summary, f"pytest summary line not found in output:\n{output[-2000:]}"
