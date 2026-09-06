"""g.net gate helper — feature_050.net_as_gate (Alt A Net-as-Gate).

Pure-Python permission-to-act check used by the TS enforcer (g.net:35)
and by harnessc WORK.md canonical verification. Fail-closed: net-down
or missing receipt BLOCKs unless expiring break-glass scope:all.

Contract (tests/scripts/omt/test_net_gate.py IS the spec):
  check_edit_allowed(...) -> {"allowed": bool, "code": str, ...}
Codes: ERR_NET_NOT_ENABLED / ERR_NET_STALE_REV / ERR_NET_DRIFT_CONFLICT
  / ERR_NET_DOWN / OK (+ break_glass flag).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def _ledger_path() -> Path:
    env = os.environ.get("OMT_LEDGER_PATH")
    return Path(env) if env else REPO_ROOT / ".meta" / ".omt" / "ledger.jsonl"


def _has_active_skip_all() -> bool:
    """Check ledger for an active omt_skip with scope=all (within 8h window)."""
    ledger = _ledger_path()
    if not ledger.exists():
        return False
    try:
        now = time.time()
        window = 28800  # 8h in seconds, matches unlock_window_ms
        for line in ledger.read_text(encoding="utf-8").strip().splitlines():
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("kind") == "skip" and rec.get("scope") == "all":
                ts_str = rec.get("ts", "")
                try:
                    ts = __import__("datetime").datetime.fromisoformat(
                        ts_str.replace("Z", "+00:00")
                    ).timestamp()
                    if now - ts < window:
                        return True
                except Exception:
                    continue
    except Exception:
        pass
    return False


def _has_recent_fire_receipt() -> bool:
    """Check ledger for a recent _start-suffixed net_fire record (within 8h window)."""
    ledger = _ledger_path()
    if not ledger.exists():
        return False
    try:
        now = time.time()
        window = 28800  # 8h in seconds, matches unlock_window_ms
        for line in ledger.read_text(encoding="utf-8").strip().splitlines():
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("kind") == "net_fire" and str(
                rec.get("transition", "")
            ).endswith("_start"):
                # Only _start-suffixed transitions grant edit permission
                # (AGENTS.md NEVER: fire(work_start) required). Any session —
                # session→work binding is Phase B (feature_051, deferred).
                ts_str = rec.get("ts", "")
                try:
                    ts = __import__("datetime").datetime.fromisoformat(
                        ts_str.replace("Z", "+00:00")
                    ).timestamp()
                    if now - ts < window:
                        return True
                except Exception:
                    continue
    except Exception:
        pass
    return False


def check_edit_allowed(
# TA: risk: risk (feature_050 wrap-up @ .sandbox/pause_2026-09-05c.md): (1) DEBUG block writes .meta/.omt/gate_debug.log on EVERY check — remove before ship; (2) _has_recent_fire_receipt accepts ANY net_fire (any transition incl. work_complete, any session) — must filter to _start-suffix transitions per AGENTS.md NEVER "fire(work_start) required"; (3) session param accepted-but-ignored (session→work binding needs Phase B identity map)
    base: Path | str | None = None,
    path: str = "",
    has_fire_receipt: bool = False,
    expected_revision: int | None = None,
    live_revision: int | None = None,
    drifted: bool = False,
    conflicts: list[dict[str, Any]] | None = None,
    net_available: bool = True,
    break_glass_scope_all: bool = False,
    session: str | None = None,
    live_marking: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decide whether an src/tests/harness edit may proceed.

    Order mirrors operation_spec_001_net_gate.md: break-glass → availability
    → drift/conflicts → stale-rev → C1 concurrency predicate → fire-receipt.
    """
    _ = (base, path, session)

    def is_concurrent() -> bool:
        """C1 predicate — feature_053.net_gate_concurrency_predicate.

        Mirrors @pred net_marking(active>1): true under real concurrency
        (work_active>1 or 2+ f{N}_active subnet holders). An explicit
        live_marking wins; otherwise the bundle at base is loaded (the live
        cli.py path always forwards it — no double load). Unreadable bundle
        → True (fail-closed: solo must be proven, never assumed).
        """
        marking = dict(live_marking) if isinstance(live_marking, dict) else None
        if marking is None and base is not None:
            try:
                from . import state as _state  # local: bundle layout lives there
                marking = dict(_state.load(Path(base)).live_marking)
            except Exception:
                return True
        if not marking:
            return True
        import re as _re
        if int(marking.get("work_active", 0) or 0) > 1:
            return True
        holders = sum(
            1
            for _k, _v in marking.items()
            if _re.match(r"^f\d+_active$", str(_k)) and (_v or 0) > 0
        )
        return holders > 1
    # Break-glass: check ledger for active omt_skip scope=all
    if break_glass_scope_all or _has_active_skip_all():
        return {"allowed": True, "code": "OK", "break_glass": True}
    if not net_available:
        return {"allowed": False, "code": "ERR_NET_DOWN"}
    if drifted or (conflicts or []):
        return {"allowed": False, "code": "ERR_NET_DRIFT_CONFLICT"}
    if expected_revision is not None and live_revision is not None:
        if expected_revision != live_revision:
            return {"allowed": False, "code": "ERR_NET_STALE_REV"}
    # C1 (feature_053): solo sessions revert to phase-gate only — the
    # fire-receipt requirement engages only under real concurrency.
    if not is_concurrent():
        return {"allowed": True, "code": "OK", "solo": True}
    # Check ledger for fire receipt if not explicitly provided
    if not has_fire_receipt:
        has_fire_receipt = _has_recent_fire_receipt()
    if not has_fire_receipt:
        return {"allowed": False, "code": "ERR_NET_NOT_ENABLED"}
    return {"allowed": True, "code": "OK"}
