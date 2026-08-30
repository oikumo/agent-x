"""TDD state layer (meta_harness_dsl R3) — ledger/snapshot/state IO.

Extracted from the former monolithic scripts/omt/tdd_check.py:
  - repo-root / state-path constants (env-var redirectable for tests)
  - ledger read/write + session-record selection (8 h window fallback)
  - TDD state derivation (mode / state / current test node / cycles)
  - source snapshots (public-method inventories) + diffs
  - pytest subprocess runners
  - test/src path resolution

meta_harness_dsl R4: the hot ledger is capped (LEDGER_CAP_BYTES) and rotates
into ledger-YYYYMM.jsonl archives; readers scan the latest archive + the hot
file. run_full_suite excludes opencode_live and cmd_done tolerates only
KNOWN_SUITE_FAILURES (audit F6/F7 — omt_done was unreachable).
"""
from __future__ import annotations

import json
import os
import re
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
UNLOCK_WINDOW_MS = 8 * 60 * 60 * 1000  # 8 hours literal fallback (keep in sync with .opencode/lib/omt_shared.ts — single TS source since meta_harness_dsl R1; pinned by tests/scripts/omt/test_thought_pattern_pin.py)
LEDGER_CAP_BYTES = 64 * 1024  # 64 KB hot-file cap literal fallback (meta_harness_dsl R4 — keep in sync with .opencode/lib/omt_shared.ts; pinned by tests/scripts/omt/test_thought_pattern_pin.py)


def _ir_var_int(name: str) -> int | None:
    """meta_harness_dsl R8: the .omt is the single source — when the compiled IR
    is present, its @var values override the literal fallbacks above (the
    literals + the TS consts stay as the no-IR fallback; the thought-pattern
    pin regexes `NAME\\s*=\\s*([0-9 *]+)` must keep matching them). Best-effort:
    missing/corrupt IR (pre-build checkout) → None → literal wins."""
    try:
        ir = json.loads(
            (REPO_ROOT / ".meta" / ".omt" / "harness.ir.json").read_text(encoding="utf-8")
        )
        value = ir.get("vars", {}).get(name)
        return int(value) if value is not None else None
    except (OSError, ValueError):
        return None


UNLOCK_WINDOW_MS = _ir_var_int("unlock_window_ms") or UNLOCK_WINDOW_MS
LEDGER_CAP_BYTES = _ir_var_int("ledger_cap_bytes") or LEDGER_CAP_BYTES


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if not s:
            continue
        try:
            records.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return records


def _ledger_archives() -> list[Path]:
    """ledger-YYYYMM.jsonl files next to the hot ledger, oldest first
    (lexicographic == chronological)."""
    return sorted(
        LEDGER_PATH.parent.glob("ledger-[0-9][0-9][0-9][0-9][0-9][0-9].jsonl")
    )


def read_ledger() -> list[dict]:
    """Latest archive (older) + hot file (newer), chronological — meta_harness_dsl
    R4 rotation: the 8 h unlock window shared by every gate reader makes
    current+latest sufficient."""
    archives = _ledger_archives()
    records = _read_jsonl(archives[-1]) if archives else []
    return records + _read_jsonl(LEDGER_PATH)


def write_ledger(record: dict) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now_iso(), **record}) + "\n")
    _rotate_ledger_if_needed()


def _rotate_ledger_if_needed() -> None:
    """R4: cap the hot ledger at LEDGER_CAP_BYTES; overflow moves to
    ledger-YYYYMM.jsonl (appended, so repeated same-month rotations stay
    chronological). Best-effort — rotation failure never breaks a session."""
    try:
        if not LEDGER_PATH.exists() or LEDGER_PATH.stat().st_size <= LEDGER_CAP_BYTES:
            return
        archive = LEDGER_PATH.parent / f"ledger-{datetime.now(timezone.utc):%Y%m}.jsonl"
        with open(archive, "a", encoding="utf-8") as out:
            out.write(LEDGER_PATH.read_text(encoding="utf-8"))
        LEDGER_PATH.write_text("", encoding="utf-8")
    except OSError:
        pass


# Known, pre-existing suite failures that must NOT block omt_done
# (meta_harness_dsl R4; audit F6): the feature_018 react_screen trio
# (Textual/mock failures predating the harness) and the window-flaky gate
# probes that read the REAL 8 h-window ledger (red exactly when a TDD session
# is in-window — i.e. when omt_done runs): the test_tdd_check subprocess
# probe plus the feature_016 TestTddCheckCli pair (same real-ledger root;
# allowlisted in feature_024 per user decision). A failure OUTSIDE this set
# blocks.
KNOWN_SUITE_FAILURES = frozenset({
    "tests/features/feature_018.react_screen/test_react_screen.py::TestReactScreenPilot::test_react_screen_mounts_and_displays_welcome",
    "tests/features/feature_018.react_screen/test_react_screen.py::TestReactScreenPilot::test_react_screen_escape_pops",
    "tests/features/feature_018.react_screen/test_react_screen.py::TestReactScreenPilot::test_react_screen_input_and_send",
    "tests/scripts/omt/test_tdd_check.py::TestTddCheckSubprocess::test_gate_returns_allowed_when_no_tdd",
    "tests/features/feature_016.tdd_enforcement/test_tdd_enforcement.py::TestTddCheckCli::test_gate_no_tdd_allows_everything",
    "tests/features/feature_016.tdd_enforcement/test_tdd_enforcement.py::TestTddCheckCli::test_gate_no_tdd_allows_tests",
})


def suite_failures(stdout: str) -> list[str]:
    """Failed node IDs from pytest's -rf short summary ('FAILED <node> - …')."""
    return [m.group(1) for line in stdout.splitlines()
            if (m := re.match(r"^FAILED (\S+)", line))]


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


def _active_feature(session: str) -> str | None:
    """Active feature for a session = the feature on its latest phase record
    (P1-1/R3). None when the session has no phase record or the phase carries
    no feature ('' → legacy session scope)."""
    records = get_session_records(session)
    phase_recs = [r for r in records if r.get("kind") == "phase"]
    if not phase_recs:
        return None
    return phase_recs[-1].get("feature") or None


def _tdd_records(session: str) -> list[dict]:
    """Feature-scoped TDD records (P1-1/R3): the cycle belongs to the FEATURE,
    not the session — a resumed session must see the prior session's red/green
    records (eval §3.1). Precedent: get_tdd_cycles (feature-scoped, below).
    Empty feature → legacy session scope."""
    feature = _active_feature(session)
    if feature:
        return [r for r in read_ledger()
                if r.get("kind") in ("tdd", "tdd_testlist") and r.get("feature") == feature]
    records = get_session_records(session)
    return [r for r in records if r.get("kind") in ("tdd", "tdd_testlist")]


def get_tdd_state(session: str) -> str:
    """Current TDD state: testlist/red/green/refactor/done/none."""
    if not get_tdd_mode(session):
        return "none"
    tdd_recs = _tdd_records(session)
    if not tdd_recs:
        return "testlist"  # TDD active but no cycle started
    latest = tdd_recs[-1]
    if latest.get("kind") == "tdd_testlist":
        return "testlist"
    return latest.get("state", "none")


def get_current_test_node(session: str) -> str | None:
    tdd_recs = [r for r in _tdd_records(session) if r.get("kind") == "tdd"]
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


def load_feature_baseline(feature: str, src_file: Path) -> dict | None:
    """P1-3 (feature_028, R5): the feature-baseline snapshot for (feature,
    src_file); None when never captured (legacy feature → validate-exit keeps
    the full-file coverage scan — D5: no protection regression)."""
    p = SNAPSHOT_DIR / "feature_baseline" / feature / f"{src_file.stem}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def snapshot_feature_baseline(feature: str, src_file: Path) -> dict | None:
    """P1-3 (feature_028, R5): capture the feature-baseline tier — the
    pre-feature public-method inventory for src_file, diffed against at
    validate-exit so coverage scopes to methods ADDED by THIS feature.
    First-write-wins per (feature, file): the baseline is the inventory BEFORE
    the feature's first touch (cmd_start captures it at first RED). None when
    src_file does not exist (true-RED new file → no baseline → diff_snapshots
    treats every method as feature-added)."""
    p = SNAPSHOT_DIR / "feature_baseline" / feature / f"{src_file.stem}.json"
    existing = load_feature_baseline(feature, src_file)
    if existing is not None:
        return existing
    if not src_file.exists():
        return None
    p.parent.mkdir(parents=True, exist_ok=True)
    baseline = {"file": str(src_file),
                "methods": extract_public_methods(src_file), "ts": _now_iso()}
    p.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    return baseline


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


def _find_vitest_root(test_path: Path) -> Path:
    """Walk up from a test file toward the vitest project root.

    Feature_038 (toolchain-aware TDD): a `.ts` test like
    `tools/petri-net-studio/tests/engine/analysis.test.ts` must run vitest
    from the project root (`tools/petri-net-studio/`), NOT from
    `tests/engine/` — a wrong cwd makes vitest config/root not found and
    returns a bogus exit 1 / "no tests matched" that breaks RED/GREEN truth.
    The root is the nearest ancestor that either contains a `package.json`
    declaring a `vitest` dep or a `vitest.config.*` marker. Falls back to
    the test file's parent (prior behavior) if nothing is found up to the
    repo root.
    """
    cur = test_path.parent
    root_marker = REPO_ROOT.resolve()
    while True:
        pkg = cur / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                deps = {**(data.get("dependencies") or {}),
                        **(data.get("devDependencies") or {})}
                if "vitest" in deps:
                    return cur
            except (json.JSONDecodeError, OSError):
                pass
        for cfg in ("vitest.config.ts", "vitest.config.js",
                    "vitest.config.mts", "vitest.config.mjs"):
            if (cur / cfg).exists():
                return cur
        if cur == root_marker or cur.parent == cur:
            break
        cur = cur.parent
    return test_path.parent


def run_test(test_node: str, timeout: int = 30) -> tuple[int, str, str]:
    """Runner that dispatches on the test file's suffix.

    Feature_038 (toolchain-aware TDD): pytest for `.py` test files; Vitest
    (`npx vitest run <file> [-t <name>]`) for `.ts`/`.tsx`. The `::` node
    separator is shared by both (vitest `-t` filters by test name). Unknown
    suffixes fall back to pytest, preserving prior behavior. The repo is
    polyglot (Python agentx + TypeScript petri_net_studio), so a pytest-only
    runner hard-fails (exit 4 "file not found") on Vitest test nodes and
    forced the documented A11/B11 manual red→green workaround across
    features_034/035/036. Runs vitest from the resolved project root
    (`_find_vitest_root`) so config/test discovery is correct.
    """
    test_path = _resolve_test_path(test_node)
    suffix = test_path.suffix.lower()
    if suffix in (".ts", ".tsx") and test_path.exists():
        # NOTE: no `-t <name>` filter. Vitest treats `-t` as a regex and a
        # name that matches nothing (regex-special chars, or an unknown
        # `::Class::method` segment — the Python class names don't exist in
        # vitest) returns exit 0 ("N skipped") = a FALSE GREEN/RED. The
        # established studio RED/GREEN practice (features 034/035/036 A11/B11/
        # C10) already runs the WHOLE file (`npx vitest run <file>`), so the
        # whole-file run is both safer and backward-compatible with precedent.
        cmd = ["npx", "vitest", "run", str(test_path)]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd=str(_find_vitest_root(test_path)),
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"vitest timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    # pytest path (default)
    return run_pytest(test_node, timeout=timeout)


def run_full_suite(timeout: int = 120) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            # R4 (audit F7): exclude opencode_live — with the opencode binary
            # present, live tests blew the 120 s timeout and made omt_done
            # unreachable. -rf emits the FAILED short summary that
            # suite_failures parses for the KNOWN_SUITE_FAILURES allowlist.
            [sys.executable, "-m", "pytest", "-q", "--no-header", "--tb=short",
             "-rf", "-m", "not opencode_live"],
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
