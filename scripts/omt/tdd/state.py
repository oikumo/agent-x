"""TDD state layer (meta_harness_dsl R3) — ledger/snapshot/state IO.

Extracted from the former monolithic scripts/omt/tdd_check.py:
  - repo-root / state-path constants (env-var redirectable for tests)
  - ledger read/write + session-record selection (8 h window fallback)
  - TDD state derivation (mode / state / current test node / cycles)
  - source snapshots (public-method inventories) + diffs
  - pytest subprocess runners
  - test/src path resolution
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .ast_checks import extract_public_methods

# Package module: scripts/omt/tdd/state.py — parents[3] is the repo root
# (the pre-R3 single-file script used parents[2]).
REPO_ROOT = Path(__file__).resolve().parents[3]
# Tests redirect the ledger/snapshot dir to a temp path via these env vars so
# they NEVER wipe the real .meta/.omt/ledger.jsonl (clear_ledger is destructive).
_LEDGER_ENV = os.environ.get("OMT_LEDGER_PATH")
LEDGER_PATH = Path(_LEDGER_ENV) if _LEDGER_ENV else REPO_ROOT / ".meta" / ".omt" / "ledger.jsonl"
_SNAPSHOT_ENV = os.environ.get("OMT_SNAPSHOT_DIR")
SNAPSHOT_DIR = Path(_SNAPSHOT_ENV) if _SNAPSHOT_ENV else REPO_ROOT / ".meta" / ".omt" / "tdd_snapshots"
UNLOCK_WINDOW_MS = 8 * 60 * 60 * 1000  # 8 hours (keep in sync with .opencode/lib/omt_shared.ts — single TS source since meta_harness_dsl R1; pinned by tests/scripts/omt/test_thought_pattern_pin.py)


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_ledger() -> list[dict]:
    if not LEDGER_PATH.exists():
        return []
    records: list[dict] = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if not s:
            continue
        try:
            records.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return records


def write_ledger(record: dict) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now_iso(), **record}) + "\n")


def _within_window(record: dict, now_ms: float) -> bool:
    ts = record.get("ts", "")
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000
        return now_ms - t < UNLOCK_WINDOW_MS
    except (ValueError, OSError):
        return False


def get_session_records(session: str) -> list[dict]:
    """Get phase/skip/tdd/tdd_testlist records for this session."""
    records = read_ledger()
    relevant = [r for r in records
                if r.get("kind") in ("phase", "skip", "tdd", "tdd_testlist", "complete")]
    if not relevant:
        return []
    if session:
        mine = [r for r in relevant if r.get("session") == session]
        if mine:
            return mine
    now_ms = time.time() * 1000
    return [r for r in relevant if _within_window(r, now_ms)]


def get_tdd_mode(session: str) -> bool:
    """Check if TDD mode is active from the latest phase record."""
    records = get_session_records(session)
    phase_recs = [r for r in records if r.get("kind") == "phase"]
    if not phase_recs:
        return False
    return bool(phase_recs[-1].get("tdd_mode", False))


def get_tdd_state(session: str) -> str:
    """Current TDD state: testlist/red/green/refactor/done/none."""
    if not get_tdd_mode(session):
        return "none"
    records = get_session_records(session)
    tdd_recs = [r for r in records if r.get("kind") in ("tdd", "tdd_testlist")]
    if not tdd_recs:
        return "testlist"  # TDD active but no cycle started
    latest = tdd_recs[-1]
    if latest.get("kind") == "tdd_testlist":
        return "testlist"
    return latest.get("state", "none")


def get_current_test_node(session: str) -> str | None:
    records = get_session_records(session)
    tdd_recs = [r for r in records if r.get("kind") == "tdd"]
    if not tdd_recs:
        return None
    return tdd_recs[-1].get("test_node")


def get_tdd_cycles(feature: str) -> list[dict]:
    records = read_ledger()
    return [r for r in records if r.get("kind") == "tdd" and r.get("feature") == feature]


# ---------------------------------------------------------------------------
# Snapshot management
# ---------------------------------------------------------------------------

def snapshot_source(src_file: Path) -> dict:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    methods = extract_public_methods(src_file)
    snapshot = {"file": str(src_file), "methods": methods, "ts": _now_iso()}
    (SNAPSHOT_DIR / f"{src_file.stem}.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )
    return snapshot


def load_snapshot(src_file: Path) -> dict | None:
    p = SNAPSHOT_DIR / f"{src_file.stem}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def diff_snapshots(before: dict | None, after: dict | None) -> list[dict]:
    if not before:
        return after.get("methods", []) if after else []
    before_set = {(m["class"], m["method"]) for m in before.get("methods", [])}
    after_methods = after.get("methods", []) if after else []
    return [m for m in after_methods if (m["class"], m["method"]) not in before_set]


# ---------------------------------------------------------------------------
# Pytest runner
# ---------------------------------------------------------------------------

def run_pytest(test_node: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_node, "-x", "-q", "--no-header", "--tb=short"],
            capture_output=True, text=True, timeout=timeout, cwd=str(REPO_ROOT),
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"pytest timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def run_full_suite(timeout: int = 120) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "--tb=short"],
            capture_output=True, text=True, timeout=timeout, cwd=str(REPO_ROOT),
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"pytest timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _resolve_test_path(test_node: str) -> Path:
    test_file = test_node.split("::")[0]
    p = Path(test_file)
    if not p.is_absolute():
        p = REPO_ROOT / test_file
    return p


def _resolve_src_path(target: str) -> Path:
    p = Path(target)
    if not p.is_absolute():
        p = REPO_ROOT / target
    return p
