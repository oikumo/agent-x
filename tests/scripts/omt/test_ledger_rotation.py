#!/usr/bin/env python3
"""Ledger rotation + omt_done state-hygiene tests (meta_harness_dsl R4).

The hot ledger (.meta/.omt/ledger.jsonl) is capped at LEDGER_CAP_BYTES;
overflow rotates into ledger-YYYYMM.jsonl archives. Every gate reader scans
the LATEST archive + the hot file — the 8 h unlock window shared by all
readers makes current+latest sufficient (plan R4; audit F21: the think-gate
parses the ledger per gated edit, so the cap is also the gate-latency fix).

Pinned here:
  1. write_ledger rotates at the cap; archive naming; repeated same-month
     rotations APPEND (chronological); read_ledger returns archive + hot in
     order; no-archive behavior unchanged; corrupt lines still skipped.
  2. The TS shared lib honours the same contract (bun subprocess probe —
     skipped when bun is absent): appendLedger rotates, readLedger scans the
     latest archive + hot.
  3. suite_failures (-rf summary parsing) + KNOWN_SUITE_FAILURES sanity for
     the R4 omt_done allowlist.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

from tdd import state  # noqa: E402


@pytest.fixture()
def ledger_dir(tmp_path, monkeypatch):
    """Redirect the module-level ledger path into a temp dir (the env var is
    read at import time, so monkeypatch the resolved constant directly)."""
    path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(state, "LEDGER_PATH", path)
    return tmp_path


def _rec(i: int) -> dict:
    return {"kind": "probe", "i": i}


def _write_big(n: int, pad: int = 512, start: int = 0) -> None:
    for i in range(start, start + n):
        state.write_ledger({**_rec(i), "pad": "x" * pad})


class TestPythonRotation:
    def test_no_rotation_under_cap(self, ledger_dir):
        state.write_ledger(_rec(1))
        assert not list(ledger_dir.glob("ledger-*.jsonl"))
        assert [r["i"] for r in state.read_ledger()] == [1]

    def test_rotation_at_cap(self, ledger_dir, monkeypatch):
        monkeypatch.setattr(state, "LEDGER_CAP_BYTES", 1024)
        _write_big(10)  # ~0.6 KB per record → rotates well before the 10th
        archives = list(ledger_dir.glob("ledger-*.jsonl"))
        assert len(archives) == 1
        assert archives[0].name == f"ledger-{datetime.now(timezone.utc):%Y%m}.jsonl"
        hot = ledger_dir / "ledger.jsonl"
        assert hot.stat().st_size <= 1024
        assert [r["i"] for r in state.read_ledger()] == list(range(10))

    def test_same_month_rotation_appends(self, ledger_dir, monkeypatch):
        monkeypatch.setattr(state, "LEDGER_CAP_BYTES", 1024)
        _write_big(5)
        archive = next(ledger_dir.glob("ledger-*.jsonl"))
        first_size = archive.stat().st_size
        _write_big(5, start=5)  # second rotation, same month → APPEND
        assert archive.stat().st_size > first_size
        assert len(list(ledger_dir.glob("ledger-*.jsonl"))) == 1
        assert [r["i"] for r in state.read_ledger()] == list(range(10))

    def test_read_ledger_scans_latest_archive_plus_current(self, ledger_dir):
        """The R4 window-reader contract: ONLY the latest archive + hot file
        are read — older archives are cold storage."""
        old = ledger_dir / "ledger-202001.jsonl"
        latest = ledger_dir / "ledger-209901.jsonl"
        old.write_text(json.dumps(_rec(0)) + "\n", encoding="utf-8")
        latest.write_text(json.dumps(_rec(1)) + "\n", encoding="utf-8")
        (ledger_dir / "ledger.jsonl").write_text(
            json.dumps(_rec(2)) + "\n", encoding="utf-8")
        assert [r["i"] for r in state.read_ledger()] == [1, 2]

    def test_corrupt_lines_skipped_everywhere(self, ledger_dir):
        archive = ledger_dir / f"ledger-{datetime.now(timezone.utc):%Y%m}.jsonl"
        archive.write_text(
            "not json\n" + json.dumps(_rec(1)) + "\n", encoding="utf-8")
        (ledger_dir / "ledger.jsonl").write_text(
            "{broken\n" + json.dumps(_rec(2)) + "\n", encoding="utf-8")
        assert [r["i"] for r in state.read_ledger()] == [1, 2]


BUN = shutil.which("bun")
PROBE = """
import { initOmtShared, appendLedger, readLedger, LEDGER_CAP_BYTES } from "%LIB%"
initOmtShared(process.argv[2])
for (let i = 0; i < 20; i++) appendLedger({ kind: "probe", i, pad: "x".repeat(4096) })
const recs = readLedger()
console.log(JSON.stringify({ cap: LEDGER_CAP_BYTES, count: recs.length, first: recs[0]?.i, last: recs[recs.length - 1]?.i }))
"""


@pytest.mark.skipif(BUN is None, reason="bun runtime not available")
def test_ts_shared_lib_rotation_contract(tmp_path):
    """Same contract, other language: appendLedger rotates at the cap and
    readLedger stitches latest archive + hot back together (order kept)."""
    probe = tmp_path / "probe.ts"
    probe.write_text(
        PROBE.replace("%LIB%", str(REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts")),
        encoding="utf-8")
    out = subprocess.run(
        [BUN, str(probe), str(tmp_path)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout.strip().splitlines()[-1])
    assert data == {"cap": 64 * 1024, "count": 20, "first": 0, "last": 19}
    # The shared lib resolves state under <root>/.meta/.omt/ (initOmtShared root)
    state_dir = tmp_path / ".meta" / ".omt"
    archives = list(state_dir.glob("ledger-*.jsonl"))
    assert len(archives) == 1
    assert (state_dir / "ledger.jsonl").stat().st_size <= data["cap"]


class TestOmtDoneAllowlistHelpers:
    def test_suite_failures_parses_rf_summary(self):
        stdout = (
            "....F....\n=== short test summary info ===\n"
            "FAILED tests/a/test_x.py::TestA::test_one - assert 1 == 2\n"
            "FAILED tests/b.py::test_two - RuntimeError\n"
            "2 failed, 10 passed in 3.21s\n"
        )
        assert state.suite_failures(stdout) == [
            "tests/a/test_x.py::TestA::test_one", "tests/b.py::test_two",
        ]

    def test_suite_failures_clean_run(self):
        assert state.suite_failures("984 passed, 1 deselected in 37.61s\n") == []

    def test_known_suite_failures_documented_shape(self):
        """Exactly the audited F6 set: feature_018 ×3 + the window-flaky
        real-ledger gate probe. Grow this set DELIBERATELY — a new known
        failure must be understood, not swept under the allowlist."""
        assert len(state.KNOWN_SUITE_FAILURES) == 4
        assert sum("feature_018.react_screen" in f
                   for f in state.KNOWN_SUITE_FAILURES) == 3
