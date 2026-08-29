"""Sentinel bridge for feature_035.studio_v2_analysis.

Satisfies the `omt_complete{Programming -> Testing}` pattern matcher
`tests/features/<feature>/test_*.py`. The feature's CANONICAL test suite is
Vitest — design_001 B11: `omt_tdd` is pytest-shaped; the runner mismatch was
declared in the Programming phase scope (feature_034 A11 precedent) — and
lives at `tools/petri-net-studio/tests/**` (245 tests at feature completion:
60 model + 59 io + 3 golden examples + 22 fraction + 38 analysis + 10
conformance + 52 store + 1 independence; evidence @
`6.testing/features/feature_035.studio_v2_analysis/test_report.md`).

This sentinel executes that suite via `npx vitest run` so the per-feature
pytest dir runs the feature's real tests (feature_031 sentinel precedent:
duplicates execution, not logic). It SKIPS — never fails — when the JS
toolchain is absent (no `npx` on PATH or `node_modules` not installed), so
the agentx suite stays portable on Python-only checkouts; the structural
tests below keep the sentinel non-vacuous in that case.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO = REPO_ROOT / "tools" / "petri-net-studio"
CONFORMANCE_DIR = REPO_ROOT / "shared" / "petri-net" / "conformance" / "analysis-v1"

VITEST_SUITE_FILES = [
    "tests/engine/model.test.ts",
    "tests/engine/io.test.ts",
    "tests/engine/examples.test.ts",
    "tests/engine/fraction.test.ts",
    "tests/engine/analysis.test.ts",
    "tests/engine/conformance.test.ts",
    "tests/state/store.test.ts",
    "tests/independence.test.ts",
]


def test_vitest_suite_files_exist() -> None:
    """Structural floor (always on): the canonical Vitest suite, the
    independence script, the vector generator, and the conformance-vector
    corpus exist where the design pinned them (§3 layout, §6, §7)."""
    missing = [f for f in VITEST_SUITE_FILES if not (STUDIO / f).is_file()]
    assert not missing, f"Vitest suite files missing under {STUDIO}: {missing}"
    assert (STUDIO / "scripts" / "check-independence.mjs").is_file()
    assert (STUDIO / "scripts" / "generate-vectors.py").is_file()
    vectors = list(CONFORMANCE_DIR.glob("*.json")) if CONFORMANCE_DIR.is_dir() else []
    assert vectors, f"no conformance vectors under {CONFORMANCE_DIR}"


def test_vitest_suite_green() -> None:
    """Execute the canonical Vitest suite (245/245 at feature completion).

    Skips when the JS toolchain is unavailable — the studio is an
    independent runtime (D4) and Python-only checkouts must stay green.
    """
    if shutil.which("npx") is None:
        pytest.skip("npx not on PATH — JS toolchain absent")
    if not (STUDIO / "node_modules").is_dir():
        pytest.skip("tools/petri-net-studio/node_modules not installed")

    proc = subprocess.run(
        ["npx", "vitest", "run"],
        cwd=STUDIO,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"vitest run failed (exit {proc.returncode}):\n{output[-4000:]}"
    summary = re.search(r"Tests\s+(\d+) passed", output)
    assert summary, f"vitest summary line not found in output:\n{output[-2000:]}"