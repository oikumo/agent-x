#!/usr/bin/env python3
"""feature_051.ledger_test_isolation (meta_harness_6 A1) — harness tests never
touch the real session ledger.

Three invariants:
  1. The Python client (scripts/omt/tdd/state.py) honors OMT_LEDGER_PATH in
     subprocesses — a fabricated TDD-active ledger AT THE ENV PATH flips the
     gate verdict (proof the subprocess reads the redirect, both ways).
  2. The TS client (.opencode/lib/omt_shared.ts) honors OMT_LEDGER_PATH —
     ledgerPath() returns it and appendLedger writes there (bun probe); the
     repo-relative default is not touched.
  3. KNOWN_SUITE_FAILURES is permanently empty (A1: suite green means green;
     canonical shape-pin lives in tests/scripts/omt/test_ledger_rotation.py).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BUN = shutil.which("bun")


def _tdd(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "scripts/omt/tdd_check.py", *args],
        capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT), env=env,
    )


def _hermetic_env(tmp_path: Path) -> dict[str, str]:
    return {
        **os.environ,
        "OMT_LEDGER_PATH": str(tmp_path / "ledger.jsonl"),
        "OMT_SNAPSHOT_DIR": str(tmp_path / "tdd_snapshots"),
    }


class TestPythonClientHonorsEnvOverride:
    def test_empty_tmp_ledger_gate_allows(self, tmp_path):
        """No ledger at the env path → no TDD mode → src edits allowed,
        regardless of what live sessions wrote to the REAL ledger."""
        out = _tdd(["gate", "--path", "src/foo.py", "--session", ""],
                   _hermetic_env(tmp_path))
        assert out.returncode == 0, out.stderr
        data = json.loads(out.stdout)
        assert data["tdd_mode"] is False
        assert data["allowed"] is True

    def test_fabricated_tdd_ledger_at_env_path_blocks(self, tmp_path):
        """A tdd-active phase record AT THE ENV PATH flips the gate — proof
        the subprocess reads the REDIRECTED ledger. Together with the empty-
        ledger test this pins hermeticity in both directions: live-session
        state can never leak in, and fabricated state is fully in control
        (the historical window-flaky root cause, now impossible)."""
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": "phase", "session": "ses_iso",
            "feature": "feature_051.ledger_test_isolation",
            "phase": "Programming", "tdd_mode": True,
        }) + "\n", encoding="utf-8")
        out = _tdd(["gate", "--path", "src/foo.py", "--session", ""],
                   _hermetic_env(tmp_path))
        assert out.returncode == 0, out.stderr
        data = json.loads(out.stdout)
        assert data["tdd_mode"] is True
        # tdd active + state testlist (no cycle records) → src blocked
        assert data["allowed"] is False


class TestTsClientHonorsEnvOverride:
    PROBE = """
import { initOmtShared, ledgerPath, appendLedger } from "%LIB%"
initOmtShared(process.argv[2])
console.log(JSON.stringify({ path: ledgerPath() }))
appendLedger({ kind: "probe" })
"""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_ledger_path_and_append_follow_env(self, tmp_path):
        """feature_051/A1: the TS shared lib honors OMT_LEDGER_PATH — the
        same lever as the Python client (parity; TS probes + live-binary
        probes stay off the real session ledger). Env wins over the injected
        root: process-level override beats library-level default."""
        assert BUN is not None, "bun runtime required (guard against skipif bypass)"
        target = tmp_path / "env-ledger.jsonl"
        probe = tmp_path / "probe.ts"
        probe.write_text(
            self.PROBE.replace(
                "%LIB%", str(REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts")),
            encoding="utf-8")
        env = {**os.environ, "OMT_LEDGER_PATH": str(target)}
        out = subprocess.run(
            [BUN, str(probe), str(tmp_path)], capture_output=True,
            text=True, timeout=60, env=env)
        assert out.returncode == 0, out.stderr
        data = json.loads(out.stdout.strip().splitlines()[-1])
        assert data["path"] == str(target)
        # the append LANDED at the env path — and nowhere else
        lines = [l for l in target.read_text(encoding="utf-8").splitlines() if l.strip()]
        recs = [json.loads(l) for l in lines]
        assert len(recs) == 1 and recs[0]["kind"] == "probe"
        assert not (tmp_path / ".meta" / ".omt" / "ledger.jsonl").exists()


class TestAllowlistPermanentlyEmpty:
    def test_known_suite_failures_empty(self):
        """A1: zero tolerated failures — suite green means green. Growing
        KNOWN_SUITE_FAILURES reverts the A1 decision (canonical shape-pin:
        tests/scripts/omt/test_ledger_rotation.py)."""
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))
        from tdd import state  # noqa: PLC0415
        assert len(state.KNOWN_SUITE_FAILURES) == 0
