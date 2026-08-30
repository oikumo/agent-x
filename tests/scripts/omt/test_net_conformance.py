"""Conformance-vector parity — feature_039.adaptive_net_engine (D2).

Runs the 9 shared vectors (`shared/petri-net/conformance/analysis-v1/*.json`)
against the HARNESS engine (`scripts/omt/net/`) and deep-compares every
expected section. This is the parity proof that the harness clone reproduces
the shipped library semantics with NO runtime import of `src/` (the vectors
were generated from the tested library by
`tools/petri-net-studio/scripts/generate-vectors.py`).

Mirror of `tools/petri-net-studio/tests/engine/conformance.test.ts` (the TS
port's suite) — same vectors, same deep-compare discipline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))

REPO_ROOT = Path(__file__).resolve().parents[3]
VECTORS_DIR = REPO_ROOT / "shared" / "petri-net" / "conformance" / "analysis-v1"

VECTOR_FILES = sorted(VECTORS_DIR.glob("*.json"))


def _load_conformance():
    """Lazy import so a missing engine is a test FAILURE (exit 1), not a
    collection error (exit 2) — GOTCHA_RED_RUNNABLE."""
    from net import conformance  # noqa: PLC0415

    return conformance


class TestConformanceVectors:
    def test_corpus_present(self) -> None:
        assert len(VECTOR_FILES) >= 9, (
            f"expected >=9 conformance vectors in {VECTORS_DIR}, "
            f"found {len(VECTOR_FILES)}"
        )

    @pytest.mark.parametrize(
        "vector_path", VECTOR_FILES, ids=lambda p: p.stem
    )
    def test_vector_matches_expected(self, vector_path: Path) -> None:
        conformance = _load_conformance()
        vector = json.loads(vector_path.read_text(encoding="utf-8"))
        result = conformance.run_vector(vector)
        assert result["ok"], (
            f"conformance vector {vector_path.stem!r} mismatches: "
            f"{result['mismatches']}"
        )

    def test_run_vectors_summary(self) -> None:
        conformance = _load_conformance()
        results = conformance.run_vectors(VECTORS_DIR)
        assert len(results) >= 9
        failed = [r["id"] for r in results if not r["ok"]]
        assert not failed, f"failing vectors: {failed}"
