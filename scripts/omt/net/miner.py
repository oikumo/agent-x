"""Ledger-mined behavioral net — feature_044.mined_behavioral_net (IDEA-004 v2).

Upward complement to synthesize (IDEA-002 §4 downward templates): the ledger
STORE (hot + ALL rotated archives — the mining window, not the gate-truth
window) is read as an event log and an observed P/T net is discovered with a
simplified α-variant (stdlib-only, ~200 LOC):

    EXTRACT  glob ledger*.jsonl → ts-ordered records → per-case traces
             (case = feature primary + session-context attribution, §8 #1)
    MINE     directly-follows → causality/parallelism/choice → places/arcs
    REPORT   intended-vs-observed drift + empirical invariants + manifest

Honest v1 limits (IDEA-004 §7, kept): mined = observed, never normative;
attribution is a heuristic (flagged `attributed:true`, support split);
corpus starts small; simplified α (one place per causal edge — no Y_W
maximal-set merging, no invisible-transition recovery); duplicate activities
under-expressed by design. Everything pruned/skipped is surfaced in the
report, never silent.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

MINED_FILENAME = "META_NET.mined.petri.json"
MINED_SIDECAR_FILENAME = "net_state.mined.sidecar.json"
MINE_MANIFEST_FILENAME = "mine.draft.manifest.json"

DEFAULT_MIN_SUPPORT = 3
SEED_CUTOFF = "2025-01-01T00:00:00+00:00"

_PHASE_ACTIVITY_RE = re.compile(r"^[A-Za-z]+$")
_SANITIZE_RE = re.compile(r"[^A-Za-z0-9]+")


def _ledger_hot_path() -> Path:
    env = os.environ.get("OMT_LEDGER_PATH")
    return Path(env) if env else REPO_ROOT / ".meta" / ".omt" / "ledger.jsonl"


def store_files() -> list[Path]:
    """Mining window = the FULL archive span (IDEA-004 §3 — gate truth uses
    hot + latest only; mining legitimately scans everything)."""
    hot = _ledger_hot_path()
    archives = sorted(hot.parent.glob("ledger-*.jsonl"))
    files = [p for p in archives if p != hot]
    if hot.exists():
        files.append(hot)
    return files


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def activity_of(record: dict[str, Any], view: str) -> str:
    """Activity normalization (IDEA-004 §8 #2 — two views shipped in v1)."""
    kind = str(record.get("kind", ""))
    if view == "probe-friction":
        if kind == "q":
            return f"q[{record.get('op', '?')}]"
        return kind or "unknown"
    # phase-flow (coarse): phase[<Phase>] + skip + complete; every other kind
    # collapses to its kind name (frequency, not 139 split activities).
    if kind == "phase":
        phase = str(record.get("phase", "?"))
        name = phase if _PHASE_ACTIVITY_RE.match(phase) else "?"
        return f"phase[{name}]"
    return kind or "unknown"


def _feature_bearing(record: dict[str, Any]) -> str:
    feature = record.get("feature", "")
    return feature if isinstance(feature, str) and feature.strip() else ""


def extract_traces(
    records: list[dict[str, Any]],
    *,
    case: str = "feature",
    activity_view: str = "phase-flow",
) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """Build per-case traces with session-context attribution (§8 #1).

    Primary case = feature (mirrors the composed net's per-feature partition
    so mined-vs-intended comparison is structurally aligned). Records without
    `feature` inherit their session's active feature — the most recent
    feature-bearing phase/complete/project_link in the SAME session at
    ts <= record ts — flagged attributed. Survivors with no case are counted
    + skipped + surfaced (never silent). Seed/malformed ts records are
    skipped with a surfaced count (§8 #7)."""
    if case not in ("feature", "session", "project"):
        raise ValueError(f"unknown case: {case!r}")
    if activity_view not in ("phase-flow", "probe-friction"):
        raise ValueError(f"unknown activity_view: {activity_view!r}")

    cutoff = datetime.fromisoformat(SEED_CUTOFF)
    skipped_reasons: dict[str, int] = {}
    ordered: list[tuple[datetime, int, dict[str, Any]]] = []
    for seq, rec in enumerate(records):
        ts = _parse_ts(rec.get("ts"))
        if ts is None:
            skipped_reasons["bad_ts"] = skipped_reasons.get("bad_ts", 0) + 1
            continue
        if ts < cutoff:
            skipped_reasons["seed_ts"] = skipped_reasons.get("seed_ts", 0) + 1
            continue
        ordered.append((ts, seq, rec))
    ordered.sort(key=lambda item: (item[0], item[1]))

    # Session → feature-bearing timeline for attribution (feature case only).
    timelines: dict[str, list[tuple[datetime, str]]] = {}
    if case == "feature":
        for ts, _, rec in ordered:
            if rec.get("kind") in ("phase", "complete", "project_link"):
                feat = _feature_bearing(rec)
                if feat:
                    timelines.setdefault(str(rec.get("session", "")), []).append((ts, feat))
        for timeline in timelines.values():
            timeline.sort(key=lambda item: item[0])

    def _attribute(rec: dict[str, Any], ts: datetime) -> tuple[str, bool] | None:
        if case == "session":
            session = rec.get("session", "")
            key = session if isinstance(session, str) and session else "no-session"
            return key, False
        if case == "project":
            project = rec.get("project", "")
            if isinstance(project, str) and project.strip():
                return project, False
            return None
        feat = _feature_bearing(rec)
        if feat:
            return feat, False
        timeline = timelines.get(str(rec.get("session", "")), [])
        active = ""
        for when, name in timeline:
            if when <= ts:
                active = name
            else:
                break
        if active:
            return active, True
        return None

    traces: dict[str, list[str]] = {}
    recency: dict[str, datetime] = {}
    attributed_support = 0
    used = 0
    for ts, _, rec in ordered:
        resolved = _attribute(rec, ts)
        if resolved is None:
            skipped_reasons["no_case_after_attribution"] = (
                skipped_reasons.get("no_case_after_attribution", 0) + 1
            )
            continue
        key, attributed = resolved
        traces.setdefault(key, []).append(activity_of(rec, activity_view))
        if key not in recency or ts > recency[key]:
            recency[key] = ts
        if attributed:
            attributed_support += 1
        used += 1
    stats = {
        "cases": len(traces),
        "records_total": len(records),
        "records_used": used,
        "records_skipped": len(records) - used,
        "skipped_reasons": skipped_reasons,
        "attributed_support": attributed_support,
        "case_latest": {key: when.isoformat() for key, when in recency.items()},
    }
    return traces, stats


def select_window(
    traces: dict[str, list[str]], stats: dict[str, Any], window: str
) -> dict[str, list[str]]:
    """Mining window: "corpus" (all cases) or "last:N" (N most recently
    active cases by observed ts — the corpus compounds, recent behavior
    matters most for drift). Unknown windows raise ValueError."""
    if window == "corpus":
        return traces
    match = re.fullmatch(r"last:(\d+)", window.strip())
    if not match or int(match.group(1)) < 1:
        raise ValueError(f"unknown window: {window!r}")
    latest = stats.get("case_latest", {})
    ranked = sorted(traces, key=lambda key: latest.get(key, ""), reverse=True)
    keep = set(ranked[: int(match.group(1))])
    return {key: traces[key] for key in traces if key in keep}


def mine_relations(
    traces: dict[str, list[str]], *, min_support: int = DEFAULT_MIN_SUPPORT
) -> dict[str, Any]:
    """Simplified α-variant over enriched traces: directly-follows histogram
    → causality / parallelism / choice. Edges below support stay in `pruned`
    (surfaced, never silent — §8 #3). Support threshold = absolute floor OR
    10% of case count (the measured corpus makes the absolute floor dominate;
    both tunable per mine call)."""
    n_cases = len(traces)
    follows: dict[tuple[str, str], int] = {}
    for trace in traces.values():
        for left, right in zip(trace, trace[1:]):
            follows[(left, right)] = follows.get((left, right), 0) + 1
    relative_floor = max(1, -(-n_cases // 10))  # ceil(10%) — at least 1
    threshold = min_support
    causal: dict[tuple[str, str], int] = {}
    parallel: list[list[str]] = []
    pruned: list[dict[str, Any]] = []
    for (left, right), support in sorted(follows.items()):
        if support < threshold and support < relative_floor:
            pruned.append({"edge": [left, right], "support": support})
            continue
        if (right, left) in follows:
            pair = sorted([left, right])
            if pair not in parallel:
                parallel.append(pair)
        else:
            causal[(left, right)] = support
    # Choice pairs are implicit (neither direction observed) — surfaced as the
    # activity vocabulary minus related pairs, computed by callers if needed.
    return {
        "directly_follows": [
            {"edge": [left, right], "support": support}
            for (left, right), support in sorted(follows.items())
        ],
        "causal": [
            {"edge": [left, right], "support": support}
            for (left, right), support in sorted(causal.items())
        ],
        "parallel": sorted(parallel),
        "pruned": sorted(pruned, key=lambda item: (item["edge"], item["support"])),
        "min_support": min_support,
        "cases": n_cases,
    }


def _transition_name(activity: str) -> str:
    slug = _SANITIZE_RE.sub("_", activity).strip("_")
    return f"m_do_{slug or 'unknown'}"


def build_observed_fragment(
    relations: dict[str, Any], traces: dict[str, list[str]]
) -> dict[str, Any]:
    """Observed net fragment (splice-ready shape, `m_` namespace — never
    collides with supervised `f{N}_` subnets). Simplified α construction: one
    place per causal edge + start/end places; each trace-initial transition
    hangs off start, each trace-final feeds end. Deterministic: same traces →
    byte-identical fragment."""
    activities = sorted({act for trace in traces.values() for act in trace})
    trans_of = {act: _transition_name(act) for act in activities}
    add_places = [
        {"name": "m_start", "tokens": 1},
        {"name": "m_end", "tokens": 0},
    ]
    for left, right in sorted(
        tuple(item["edge"]) for item in relations["causal"]
    ):
        add_places.append({"name": f"m_p_{trans_of[left]}__{trans_of[right]}", "tokens": 0})
    add_transitions = [{"name": trans_of[act]} for act in activities]
    add_arcs: list[dict[str, Any]] = []
    for initial in sorted({trace[0] for trace in traces.values() if trace}):
        add_arcs.append({"source": "m_start", "target": trans_of[initial], "weight": 1})
    for final in sorted({trace[-1] for trace in traces.values() if trace}):
        add_arcs.append({"source": trans_of[final], "target": "m_end", "weight": 1})
    for left, right in sorted(
        tuple(item["edge"]) for item in relations["causal"]
    ):
        place = f"m_p_{trans_of[left]}__{trans_of[right]}"
        add_arcs.append({"source": trans_of[left], "target": place, "weight": 1})
        add_arcs.append({"source": place, "target": trans_of[right], "weight": 1})
    return {
        "add_places": add_places,
        "add_transitions": add_transitions,
        "add_arcs": add_arcs,
        "transition_of": trans_of,
    }
