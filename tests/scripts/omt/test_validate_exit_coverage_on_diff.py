#!/usr/bin/env python3
"""Golden tests for P1-3: validate-exit coverage scoped to the feature diff
(feature_028, meta_harness_3 v1.2).

R5: the rolling per-edit snapshot baseline (last cmd_green) is NOT a feature
baseline — validate-exit must diff against a FEATURE-baseline snapshot tier
(captured at first RED, stored per-feature under SNAPSHOT_DIR/feature_baseline/)
so the coverage scan checks only methods ADDED by THIS feature. No baseline →
legacy full-file scan (protection preserved, D5).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

from tdd import gates, state  # noqa: E402
from tdd.ast_checks import extract_public_methods  # noqa: E402

FEATURE = "feature_synth.coverage_on_diff"

PRE_SRC = '''def old_helper():
    return 1


class SynthWidget:
    def legacy_render(self):
        return "old"
'''

ADDITIVE_SRC = PRE_SRC + '''

def new_featured():
    return 2
'''


@pytest.fixture()
def hermetic(tmp_path, monkeypatch):
    """Hermetic ledger + snapshot dir + synthetic repo: a feature-touched src
    file with pre-existing untested methods + the feature's test dir."""
    monkeypatch.setattr(state, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(state, "SNAPSHOT_DIR", tmp_path / "snapshots")
    monkeypatch.setattr(state, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gates, "REPO_ROOT", tmp_path)
    src = tmp_path / "src" / "agentx" / "synth.py"
    src.parent.mkdir(parents=True)
    src.write_text(PRE_SRC, encoding="utf-8")
    test_dir = tmp_path / "tests" / "features" / FEATURE
    test_dir.mkdir(parents=True)
    (test_dir / "test_synth.py").write_text(
        "import agentx.synth\n", encoding="utf-8")
    return tmp_path


def _write_baseline(root: Path, src: Path) -> None:
    """Place the feature-baseline snapshot (layout contract:
    SNAPSHOT_DIR/feature_baseline/<feature>/<stem>.json)."""
    baseline = {
        "file": str(src),
        "methods": extract_public_methods(src),
        "ts": "2026-08-16T09:00:00+00:00",
    }
    bdir = state.SNAPSHOT_DIR / "feature_baseline" / FEATURE
    bdir.mkdir(parents=True)
    (bdir / f"{src.stem}.json").write_text(json.dumps(baseline), encoding="utf-8")


class TestCoverageOnDiff:
    def test_additive_edit_with_preexisting_untested_exits_clean(self, hermetic):
        """P1-3: the §3.8 scenario — additive edit to a file whose pre-existing
        methods were never tested exits Testing clean (only THIS feature's
        added methods are coverage-checked)."""
        root = hermetic
        src = root / "src" / "agentx" / "synth.py"
        _write_baseline(root, src)
        # The feature's additive edit: one new method, referenced by the test.
        src.write_text(ADDITIVE_SRC, encoding="utf-8")
        (root / "tests" / "features" / FEATURE / "test_synth.py").write_text(
            "import agentx.synth\n\n\n"
            "def test_new_featured():\n"
            "    agentx.synth.new_featured()\n",
            encoding="utf-8")
        res = gates.cmd_validate_exit(SimpleNamespace(feature=FEATURE))
        assert res["ok"] is True
        assert res["coverage_gaps"] == []

    def test_new_untested_public_method_still_blocks(self, hermetic):
        """P1-3 protection preserved (D5): a NEW method added by this feature
        without any test reference still blocks; the pre-existing untested
        methods do NOT appear in the gap."""
        root = hermetic
        src = root / "src" / "agentx" / "synth.py"
        _write_baseline(root, src)
        src.write_text(ADDITIVE_SRC, encoding="utf-8")  # test never references it
        res = gates.cmd_validate_exit(SimpleNamespace(feature=FEATURE))
        assert res["ok"] is False
        names = [m["method"] for g in res["coverage_gaps"] for m in g["untested"]]
        assert "new_featured" in names
        assert "old_helper" not in names
        assert "legacy_render" not in names

    def test_no_baseline_falls_back_to_full_scan(self, hermetic):
        """No feature baseline captured (legacy feature) → the full-file scan
        applies unchanged (no protection regression, D5)."""
        root = hermetic
        src = root / "src" / "agentx" / "synth.py"
        src.write_text(ADDITIVE_SRC, encoding="utf-8")  # no baseline written
        res = gates.cmd_validate_exit(SimpleNamespace(feature=FEATURE))
        assert res["ok"] is False
        names = [m["method"] for g in res["coverage_gaps"] for m in g["untested"]]
        assert "old_helper" in names  # legacy strict scan sees everything

    def test_feature_baseline_first_write_wins(self, hermetic):
        """The capture helper: first-write-wins per (feature, file); missing
        src (true-RED new file) → no baseline; load round-trips."""
        root = hermetic
        src = root / "src" / "agentx" / "synth.py"
        first = state.snapshot_feature_baseline(FEATURE, src)
        assert first is not None
        assert [m["method"] for m in first["methods"]] == ["old_helper", "legacy_render"]
        src.write_text(ADDITIVE_SRC, encoding="utf-8")
        second = state.snapshot_feature_baseline(FEATURE, src)
        assert [m["method"] for m in second["methods"]] == ["old_helper", "legacy_render"]
        assert state.load_feature_baseline(FEATURE, src) == first
        absent = root / "src" / "agentx" / "absent.py"
        assert state.snapshot_feature_baseline(FEATURE, absent) is None
        assert state.load_feature_baseline("feature_never_touched.x", src) is None
