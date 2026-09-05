"""Sentinel bridge for feature_043.meta_net_dashboard.

Satisfies the `omt_complete{Programming -> Testing}` pattern matcher
`tests/features/<feature>/test_*.py`. The feature's suites are split by
toolchain (GOTCHA_TDD_TOOLCHAIN): pytest (`tests/scripts/omt/
test_net_history.py` — ledger replay + snapshot vectors incl. the LIVE
golden) and Vitest (`tools/petri-net-studio/tests/dashboard/` — blockage,
snapshot guard, Dashboard render).

This sentinel runs the dashboard Vitest scope via `npx vitest run` (036
precedent: duplicates execution, not logic) and replays the live ledger in
pytest (no node needed). It SKIPS — never fails — the Vitest half when the
JS toolchain is absent, so the agentx suite stays portable; the structural
floor + live replay keep it non-vacuous in that case.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO = REPO_ROOT / "tools" / "petri-net-studio"
LIVE_BASE = REPO_ROOT / ".meta" / ".omt"

SCRIPTS_DIR = REPO_ROOT / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))

DASHBOARD_SRC_FILES = [
    "tools/petri-net-studio/src/dashboard/blockedPlaces.ts",
    "tools/petri-net-studio/src/dashboard/Dashboard.tsx",
    "tools/petri-net-studio/src/dashboard/dashboard-main.tsx",
    "tools/petri-net-studio/src/dashboard/snapshot.json",
    "tools/petri-net-studio/dashboard.html",
    "scripts/omt/net/history.py",
    "scripts/omt/net_snapshot.py",
]

DASHBOARD_VITEST_FILES = [
    "tests/dashboard/blockedPlaces.test.ts",
    "tests/dashboard/snapshot.test.ts",
    "tests/dashboard/Dashboard.test.tsx",
]


def test_dashboard_files_exist() -> None:
    """Structural floor (always on): dashboard sources, entry page, tests,
    snapshot builder + replay module exist where the design pinned them."""
    missing = [f for f in DASHBOARD_SRC_FILES if not (REPO_ROOT / f).is_file()]
    assert not missing, f"feature_043 source files missing: {missing}"
    missing_tests = [f for f in DASHBOARD_VITEST_FILES if not (STUDIO / f).is_file()]
    assert not missing_tests, f"feature_043 Vitest files missing: {missing_tests}"
    snap = json.loads((STUDIO / "src/dashboard/snapshot.json").read_text(encoding="utf-8"))
    assert snap["format"] == "meta-net-dashboard-snapshot" and snap["version"] == 1
    assert snap["snapshots"] and snap["snapshots"][-1]["revision"] == snap["net_revision"]


def test_dashboard_vitest_green() -> None:
    """Execute the dashboard Vitest scope (9/9 at feature completion).

    Skips when the JS toolchain is unavailable (036 precedent).
    """
    if shutil.which("npx") is None:
        pytest.skip("npx not on PATH — JS toolchain absent")
    if not (STUDIO / "node_modules").is_dir():
        pytest.skip("tools/petri-net-studio/node_modules not installed")

    proc = subprocess.run(
        ["npx", "vitest", "run", "tests/dashboard"],
        cwd=STUDIO,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"dashboard vitest failed:\n{output[-4000:]}"
    summary = re.search(r"Tests\s+(\d+) passed", output)
    assert summary, f"vitest summary line not found:\n{output[-2000:]}"


def test_live_replay_matches_bundle() -> None:
    """Pytest half of the bridge (no node needed): the committed snapshot is
    fresh — ledger replay reproduces the live bundle exactly."""
    if not (LIVE_BASE / "META_NET.petri.json").is_file():
        pytest.skip("harness net not bootstrapped")
    from net import history, state  # noqa: PLC0415

    snaps = history.replay(LIVE_BASE)
    st = state.load(LIVE_BASE)
    assert snaps and snaps[-1]["revision"] == st.revision
    assert snaps[-1]["marking"] == st.live_marking
    snap = json.loads((STUDIO / "src/dashboard/snapshot.json").read_text(encoding="utf-8"))
    assert snap["net_revision"] == st.revision, (
        f"committed snapshot rev {snap['net_revision']} != live rev {st.revision} — "
        "regen via uv run scripts/omt/net_snapshot.py"
    )
