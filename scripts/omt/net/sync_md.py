"""Net→md render + md→net propose — feature_045.work_md_net_driven.

Pure, deterministic, stdlib-only (no net I/O, no ledger). The caller
(`state.sync`) supplies live net/overlay/resources; this module formats
text and computes analyzer-validated proposals (D4 proposal-only).
"""
from __future__ import annotations

import re
from typing import Any

TASK_ROW_RE = re.compile(r"^- \[([ xX~!])\] \*\*feature_(\d+)")
_CHECKBOX_M0 = {" ": "pending", "~": "active", "!": "active", "x": "done", "X": "done"}
_SUBNET_RE = re.compile(r"^f(\d+)_")
POOL_PLACES = ("work_pending", "work_active", "work_done")
POOL_CAP = 15


def is_pool_net(net: Any) -> bool:
    """D20: pool detection — all three work_* places present (rev44+ migration)."""
    try:
        places = net.places
    except AttributeError:
        return False
    return all(pl in places for pl in POOL_PLACES)


def pool_counts(live_marking: dict[str, int]) -> dict[str, int]:
    """Live pool counts by place name."""
    return {pl: live_marking.get(pl, 0) for pl in POOL_PLACES}


def _actual_states(net: Any, live_marking: dict[str, int]) -> dict[str, str]:
    """Per-subnet lifecycle state from the live marking."""
    out: dict[str, str] = {}
    nums = sorted({m.group(1) for p in net.places if (m := _SUBNET_RE.match(p))})
    for n in nums:
        if live_marking.get(f"f{n}_done", 0) > 0:
            out[n] = "done"
        elif live_marking.get(f"f{n}_active", 0) > 0:
            out[n] = "active"
        else:
            out[n] = "pending"
    return out


def _box(state: str) -> str:
    return {"pending": " ", "active": "~", "done": "x"}[state]


def _start_num(name: str) -> tuple[int, str]:
    m = re.match(r"f(\d+)_start", name)
    return (int(m.group(1)), name) if m else (10**9, name)


def render_tasks_block(
    net: Any,
    live_marking: dict[str, int],
    overlay: dict[str, Any],
    resources: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    revision: int,
    slugs: dict[str, str] | None = None,
) -> str:
    """Deterministic Tasks block: rev-stamp + menu + per-subnet rows."""
    slugs = slugs or {}
    actual = _actual_states(net, live_marking)
    live_tuple = tuple(live_marking.get(p, 0) for p in net.place_order)
    pool_mode = is_pool_net(net)
    enabled = sorted(
        (
            t for t in net.enabled_transitions_at(live_tuple)
            if t.endswith("_start") or (pool_mode and t == "work_complete")
        ),
        key=_start_num,
    )
    blocked = sorted(c["transition"] for c in conflicts)
    lines = [
        f"<!-- net_rev:{revision} -->",
        f"NEXT: {enabled[0]} (recommended)" if enabled else "NEXT: none",
        f"Other enabled: {', '.join(enabled[1:]) or 'none'}",
        f"Blocked: {', '.join(blocked) or 'none'}",
        _resources_line(resources),
    ]
    if is_pool_net(net):
        counts = pool_counts(live_marking)
        try:
            nplaces = len(net.places)
        except AttributeError:
            nplaces = len(live_marking)
        lines.append(
            f"Pool: pending={counts['work_pending']} active={counts['work_active']} "
            f"done={counts['work_done']} (places {nplaces}/{POOL_CAP})"
        )
    lines.append("")
    for n in sorted(actual, key=int):
        slug = slugs.get(n, f"feature_{n}")
        lines.append(f"- [{_box(actual[n])}] **{slug}** — net:{actual[n]}")
    return "\n".join(lines) + "\n"


def _resources_line(resources: list[dict[str, Any]] | None) -> str:
    if not resources:
        return "Resources: n/a"
    free = sum(1 for r in resources if r.get("capacity_ok"))
    holders = sorted({h for r in resources for h in r.get("holders", [])})
    tail = f" holders:{','.join(holders)}" if holders else ""
    return f"Resources: {free}/{len(resources)} free{tail}"


def render_projects_block(
    overlay: dict[str, Any], projects_map: dict[str, str] | None = None
) -> str:
    """Deterministic Projects table body (rows sorted by subnet)."""
    projects_map = projects_map or {}
    rows = [
        "| project | state | features |",
        "|---|---|---|",
    ]
    for key in sorted(overlay.get("subnets", {})):
        n = key[len("feature_"):]
        proj = projects_map.get(n, "—")
        state = "disabled" if key in overlay.get("disabled", []) else "active"
        rows.append(f"| {proj} | {state} | {key} |")
    return "\n".join(rows) + "\n"


def render_net_status(
    live_marking: dict[str, int],
    resources: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    revision: int,
) -> str:
    return (
        f"- rev: {revision}\n"
        f"- {_resources_line(resources)}\n"
        f"- conflicts: {len(conflicts)}\n"
    )


def parse_tasks_block(text: str) -> dict[str, str]:
    """Parse checkbox rows → {N: pending|active|done} (unknown rows ignored)."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = TASK_ROW_RE.match(line)
        if m:
            out[m.group(2)] = _CHECKBOX_M0[m.group(1)]
    return out


def propose_diff(
    net: Any, live_marking: dict[str, int], desired: dict[str, str]
) -> dict[str, list]:
    """Fire proposals for desired-vs-actual diff, analyzer-validated (D4)."""
    actual = _actual_states(net, live_marking)
    live_tuple = tuple(live_marking.get(p, 0) for p in net.place_order)
    fires: list[str] = []
    blocked: list[dict[str, Any]] = []
    for n in sorted(desired, key=int):
        want, have = desired[n], actual.get(n, "pending")
        if want == have:
            continue
        candidate: str | None = None
        if want == "active" and have == "pending":
            candidate = f"f{n}_start"
        elif want == "done" and have == "active":
            candidate = f"f{n}_complete"
        if candidate is None or candidate not in net.transitions:
            blocked.append({"subnet": f"feature_{n}", "reason": "no_valid_fire"})
            continue
        if net.is_enabled_at(live_tuple, candidate):
            fires.append(candidate)
        else:
            blocked.append({
                "subnet": f"feature_{n}",
                "transition": candidate,
                "blocked_by": sorted(
                    p for p in net.inputs.get(candidate, {})
                    if not _SUBNET_RE.match(p) and live_marking.get(p, 0) == 0
                ),
            })
    # Serial-mirror: two simultaneous claims → keep first, block rest.
    if len(fires) > 1 and live_marking.get("agent_attention", 1) == 1:
        priority = sorted(fires, key=_start_num)
        fires = priority[:1]
        for t in priority[1:]:
            m = re.match(r"f(\d+)_", t)
            blocked.append({
                "subnet": f"feature_{m.group(1)}" if m else t,
                "transition": t,
                "blocked_by": ["agent_attention"],
            })
    return {"fires": fires, "blocked": blocked}


def menu_lines(
    enabled: list[str],
    resources: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    revision: int,
    pool: dict[str, Any] | None = None,
) -> list[str]:
    """D19 session-start menu: ordered starts + resources + rev stamp.

    feature_049: pool-aware — when pool counts are supplied (D20 pool nets),
    include the `Pool: pending/active/done (places N/CAP)` line so the
    STARTUP menu shows WIP without per-feature rows (which pool nets omit).
    """
    ordered = sorted(enabled, key=_start_num)
    blocked = sorted(c.get("transition", c.get("subnet", "")) for c in conflicts)
    lines = [
        f"NEXT: {ordered[0]} (recommended)" if ordered else "NEXT: none",
        f"Other enabled: {', '.join(ordered[1:]) or 'none'}",
        f"Blocked: {', '.join(blocked) or 'none'}",
        _resources_line(resources),
    ]
    if pool is not None:
        lines.append(
            f"Pool: pending={pool.get('pending', 0)} active={pool.get('active', 0)} "
            f"done={pool.get('done', 0)} (places {pool.get('places', 0)}/{pool.get('cap', POOL_CAP)})"
        )
    lines.append(f"(net rev {revision})")
    return lines
