"""Wave 3/B1+B2 gate_budget_ceremony_meter — feature_057.

Contract (GREEN pins the implementation):
- B1 GATE BUDGET: @budget gates max=12 is compile-enforced (past max = build
  error via the generic budget loop, with a gates-aware unit); reaching the
  cap warns (never errors) with net-zero advice — the most-skipped gate is
  the toll-booth candidate, bypassable zero-skip gates are dead-weight watch
  (skip-frequency attribution via SKIP_SCOPE_TO_GATES).
- B2 CEREMONY METER: per task_type median of agent-issued ledger records
  before the session's first phase record (pre-unlock consults); alarm
  (warning, never error) when the bug_fix median > 3.
- MIRROR: harnessc.py (Python) and omt_status.ts gateBudget/ceremonyMeter
  agree on the same fixtures (scope map, ceremony kinds, alarm threshold).

Bun probes exercise the REAL status plugin (feature_056 idiom): hermetic
ledger via OMT_LEDGER_PATH + fixture IR under the tmp root.

Process note: tests/ writes via omt_skip{scope:"tests", purpose:"canary"}
under the declared minor_feature phase (see implementation_notes.md).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

import harnessc  # noqa: E402

OMT = REPO_ROOT / ".meta" / "META_HARNESS.omt"
STATUS_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts"

BUN = shutil.which("bun")

F = "feature_057.gate_budget_ceremony_meter"
NOW_MS = time.time() * 1000


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _corpus(text: str) -> harnessc.Corpus:
    errors: list[str] = []
    records = harnessc.parse(text, errors)
    assert not errors, f"fixture .omt failed to parse: {errors}"
    return harnessc.Corpus(records)


def _run_probe(tmp_path: Path, body: str) -> dict:
    """Write body to tmp/probe.ts, run bun with a hermetic ledger env."""
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    probe = tmp_path / "probe.ts"
    probe.write_text(body, encoding="utf-8")
    env = {**os.environ, "OMT_LEDGER_PATH": str(tmp_path / "ledger.jsonl")}
    out = subprocess.run([BUN, str(probe)], capture_output=True, text=True,
                         timeout=90, cwd=str(tmp_path), env=env)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


# --- B1 static pins ---------------------------------------------------------------

_GATE_FIXTURE = (
    "@msg m sev=block : m\n"
    "@gate g.a on=before tools=edit when=path_in(\"src/\") msg=@msg.m "
    "hard=true skip_ok=true order=1 : t\n"
)


class TestGateBudgetStatic:
    def test_budget_record_and_count(self) -> None:
        omt = OMT.read_text(encoding="utf-8")
        assert "@budget gates max=12" in omt
        assert "gates" in harnessc.MEASURABLE_BUDGETS
        c = harnessc.Corpus(harnessc.parse(omt, []))
        sizes = harnessc.measure_budgets(c, "")
        size, cap = sizes["gates"]
        assert (size, cap) == (10, 12), f"gates={size}/{cap}"

    def test_over_max_is_a_build_error_with_gate_unit(self) -> None:
        gates = "".join(
            f"@gate g{i:02d} on=before tools=edit when=path_in(\"src/\") "
            f"msg=@msg.m hard=true skip_ok=false order={i} : t\n" for i in range(13))
        c = _corpus("@budget gates max=12\n@msg m sev=block : m\n" + gates)
        sizes = harnessc.measure_budgets(c, "")
        assert sizes["gates"] == (13, 12)
        harnessc.run_all_checks(c, "")
        assert any("budget gates: 13 gates > 12 gates" in e for e in c.errors), c.errors

    def test_at_cap_warns_with_candidates_never_errors(self, monkeypatch) -> None:
        monkeypatch.setattr(harnessc, "_read_repo_ledger_records", lambda: [])
        c = _corpus("@budget gates max=1\n" + _GATE_FIXTURE)
        harnessc.check_gate_retirement(c)
        assert c.errors == []
        assert any("gate-budget: 1/1 gates at cap" in w and "net-zero" in w
                   for w in c.warnings), c.warnings

    def test_under_cap_is_silent(self, monkeypatch) -> None:
        monkeypatch.setattr(harnessc, "_read_repo_ledger_records", lambda: [])
        c = _corpus("@budget gates max=12\n" + _GATE_FIXTURE)
        harnessc.check_gate_retirement(c)
        assert c.errors == [] and c.warnings == []


# --- B1 retirement matrices ---------------------------------------------------------

def _skip(scope: str, age_h: float = 1.0) -> dict:
    return {"ts": _iso(_now() - timedelta(hours=age_h)), "kind": "skip",
            "session": "s", "reason": "r", "scope": scope}


class TestRetirementCandidates:
    def test_scope_attribution_and_stale_exclusion(self) -> None:
        recs = [_skip("nav"), _skip("nav"), _skip("tests"),
                _skip("src"), _skip("all"), _skip("nav", age_h=8 * 24)]
        counts = harnessc.gate_skip_counts(recs, NOW_MS)
        assert counts == {"g.nav": 2, "g.tests": 1, "g.phase": 1, "g.net": 1}, counts

    def test_unknown_scope_and_unparseable_ts_ignored(self) -> None:
        recs = [_skip("bogus"), {"kind": "skip", "ts": "not-a-time", "scope": "nav"},
                {"kind": "phase", "ts": _iso(_now()), "scope": "nav"}]
        assert harnessc.gate_skip_counts(recs, NOW_MS) == {}

    def test_toll_booth_and_dead_weight(self) -> None:
        toll, dead = harnessc.gate_retirement_candidates(
            {"g.nav": 7, "g.tests": 2}, ["g.nav", "g.tests", "g.phase", "g.net"],
            {"g.nav": True, "g.tests": True, "g.phase": True, "g.net": False})
        assert toll == ("g.nav", 7)
        assert dead == ["g.phase"]  # bypassable, never skipped; g.net not bypassable

    def test_no_skips_means_no_toll(self) -> None:
        toll, dead = harnessc.gate_retirement_candidates(
            {}, ["g.nav"], {"g.nav": True})
        assert toll is None and dead == ["g.nav"]


# --- B2 ceremony matrices -------------------------------------------------------------


def _phase(session: str, tt: str, age_h: float, **kw) -> dict:
    rec = {"ts": _iso(_now() - timedelta(hours=age_h)), "kind": "phase",
           "session": session, "task_type": tt, "phase": "Programming",
           "scope": "s", "feature": "feature_001.a"}
    rec.update(kw)
    return rec


def _consult(session: str, kind: str, age_h: float) -> dict:
    return {"ts": _iso(_now() - timedelta(hours=age_h)), "kind": kind,
            "session": session}


class TestCeremonyStats:
    def test_median_odd_even_and_variety(self) -> None:
        recs = [
            _consult("b1", "think_consult", 5), _consult("b1", "q", 4),
            _phase("b1", "bug_fix", 3),
            _phase("b2", "bug_fix", 2),
            _consult("m1", "think_consult", 5), _consult("m1", "skip", 4),
            _phase("m1", "minor_feature", 3),
            _phase("m2", "minor_feature", 2),
            _consult("m3", "q", 5), _consult("m3", "q", 4),
            _consult("m3", "think_consult", 3), _phase("m3", "minor_feature", 2),
            _consult("orphan", "think_consult", 1),  # no phase → skipped
        ]
        stats = harnessc.ceremony_stats(recs)
        assert stats["bug_fix"] == {"sessions": 2, "median": 1.0}, stats
        assert stats["minor_feature"] == {"sessions": 3, "median": 2}, stats
        assert "unknown" not in stats

    def test_system_kinds_are_not_ceremony(self) -> None:
        recs = [_consult("s", "net_sync", 5), _consult("s", "complete", 4),
                _consult("s", "project_link", 3), _phase("s", "test", 2)]
        assert harnessc.ceremony_stats(recs) == {"test": {"sessions": 1, "median": 0}}

    def test_missing_session_or_ts_skipped(self) -> None:
        recs = [{"kind": "think_consult", "ts": _iso(_now())},
                {"kind": "think_consult", "session": "s"},
                _phase("s", "docs", 1)]
        assert harnessc.ceremony_stats(recs) == {"docs": {"sessions": 1, "median": 0}}

    def test_alarm_fires_only_past_three(self, monkeypatch) -> None:
        hot = [_consult("b", "think_consult", 5) for _ in range(4)] + [_phase("b", "bug_fix", 1)]
        monkeypatch.setattr(harnessc, "_read_repo_ledger_records", lambda: hot)
        c = _corpus("@budget gates max=12\n" + _GATE_FIXTURE)
        harnessc.check_ceremony_alarm(c)
        assert c.errors == []
        assert any("ceremony: bug_fix pre-unlock median 4" in w and "alarm>3" in w
                   for w in c.warnings), c.warnings

    def test_alarm_silent_at_three(self, monkeypatch) -> None:
        calm = [_consult("b", "q", 5) for _ in range(3)] + [_phase("b", "bug_fix", 1)]
        monkeypatch.setattr(harnessc, "_read_repo_ledger_records", lambda: calm)
        c = _corpus("@budget gates max=12\n" + _GATE_FIXTURE)
        harnessc.check_ceremony_alarm(c)
        assert c.errors == [] and c.warnings == []


# --- TS mirror: the REAL status plugin ----------------------------------------------

MIRROR_PROBE = """import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
const LEDGER = process.env.OMT_LEDGER_PATH;
const ROOT = "TMP_ABS";
const H = 3600 * 1000, D = 24 * H, now = Date.now();
const iso = (ms) => new Date(ms).toISOString();
const gates = [
  { id: "g.nav", on: "before", tools: "x", paths: "", when: "a()", requires: "", msg: "m", hard: true, skip_ok: true, order: 0, text: "t" },
  { id: "g.tests", on: "before", tools: "x", paths: "", when: "a()", requires: "", msg: "m", hard: true, skip_ok: true, order: 30, text: "t" },
  { id: "g.phase", on: "before", tools: "x", paths: "", when: "a()", requires: "", msg: "m", hard: true, skip_ok: true, order: 40, text: "t" },
  { id: "g.net", on: "before", tools: "x", paths: "", when: "a()", requires: "", msg: "m", hard: true, skip_ok: false, order: 35, text: "t" },
];
mkdirSync(join(ROOT, ".meta", ".omt"), { recursive: true });
writeFileSync(join(ROOT, ".meta", ".omt", "harness.ir.json"),
  JSON.stringify({ gates, budgets: { gates: 12 }, vars: {} }));
const recs = [
  { ts: iso(now - H), kind: "skip", session: "p", reason: "a", scope: "nav", purpose: "override" },
  { ts: iso(now - H), kind: "skip", session: "p", reason: "b", scope: "nav", purpose: "override" },
  { ts: iso(now - H), kind: "skip", session: "p", reason: "c", scope: "tests", purpose: "canary", tests_approved: true },
  { ts: iso(now - 8 * D), kind: "skip", session: "p", reason: "d", scope: "all", purpose: "emergency" },
  { ts: iso(now - 5 * H), kind: "think_consult", session: "b1" },
  { ts: iso(now - 4 * H), kind: "think_consult", session: "b1" },
  { ts: iso(now - 3 * H), kind: "q", session: "b1" },
  { ts: iso(now - 2 * H), kind: "skip", session: "b1", reason: "c", scope: "tests" },
  { ts: iso(now - H), kind: "phase", session: "b1", task_type: "bug_fix", phase: "Programming", scope: "s", feature: "feature_001.a" },
  { ts: iso(now - H), kind: "phase", session: "m1", task_type: "minor_feature", phase: "Programming", scope: "s", feature: "feature_002.b" },
  { ts: iso(now - 3 * H), kind: "q", session: "m2" },
  { ts: iso(now - 2 * H), kind: "think_consult", session: "m2" },
  { ts: iso(now - H), kind: "phase", session: "m2", task_type: "minor_feature", phase: "Programming", scope: "s", feature: "feature_003.c" },
  { ts: iso(now - H), kind: "think_consult", session: "orphan" },
];
writeFileSync(LEDGER, recs.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
const mod = await import("STATUS_ABS");
const budget = mod.gateBudget();
const ceremony = mod.ceremonyMeter();
const plugin = await mod.default({ directory: ROOT, worktree: ROOT });
const res = await plugin.tool.omt_status.execute({}, {});
console.log(JSON.stringify({ budget, ceremony, output: res.output, meta: { gate_budget: res.metadata.gate_budget, ceremony: res.metadata.ceremony } }));
"""


class TestStatusMirror:
    def test_gate_budget_and_ceremony_lines(self, tmp_path: Path) -> None:
        body = (MIRROR_PROBE.replace("STATUS_ABS", STATUS_PLUGIN.as_posix())
                .replace("TMP_ABS", tmp_path.as_posix()))
        out = _run_probe(tmp_path, body)
        assert out["budget"]["lines"] == [
            "Gates 4/12 (net-zero: retire to add; top-skipped g.navx2; watch g.phase)"], out["budget"]
        assert out["budget"]["summary"] == {
            "count": 4, "max": 12, "top_skipped": ["g.nav", 2],
            "dead_weight_watch": ["g.phase"]}, out["budget"]
        assert out["ceremony"]["summary"]["medians"] == {
            "bug_fix": {"sessions": 1, "median": 4},
            "minor_feature": {"sessions": 2, "median": 1}}, out["ceremony"]
        assert out["ceremony"]["summary"]["alarm"] is True
        text = out["output"]
        assert "Gates 4/12 (net-zero: retire to add; top-skipped g.navx2; watch g.phase)" in text
        assert "Ceremony median (pre-unlock records): bug_fix 4 · minor_feature 1 (alarm bug_fix>3) ⚠ over alarm" in text
        assert out["meta"]["gate_budget"]["count"] == 4
        assert out["meta"]["ceremony"]["alarm"] is True


# --- static pins: wiring + no schema growth ------------------------------------------

class TestStaticPins:
    def test_helpers_present_and_synced(self) -> None:
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        for token in ("export function gateBudget", "export function ceremonyMeter",
                      "Gates ${ids.length}/${max}", "Ceremony median (pre-unlock records)",
                      "result.gate_budget", "result.ceremony"):
            assert token in src

    def test_status_stays_read_only(self) -> None:
        """A4 pin holds: the B1+B2 section reads the ledger, never writes it."""
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        assert "appendLedger" not in src and "writeLedger" not in src

    def test_no_new_tool_args_on_status(self) -> None:
        """B1+B2 ride the default status output — no schema growth on omt_status."""
        omt = OMT.read_text(encoding="utf-8")
        line = next(ln for ln in omt.splitlines() if ln.startswith("@tool omt_status"))
        assert 'args="op?,tool?,path?,include_ledger?"' in line
