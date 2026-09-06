"""Wave 3/A2 skip_purpose_taxonomy — feature_056.

Contract (GREEN pins the implementation):
- A2.1 PURPOSE ARG: omt_skip accepts only canary|emergency|break_glass|override
  (rejects anything else); omitted purpose defaults to canary for scope=tests,
  override otherwise; the effective purpose lands on the ledger record.
- A2.2 FRICTION REPORT: 7-day split — friction (canary|emergency|break_glass)
  vs nav-escapes (override + scope=nav) vs evasion (override + other scopes);
  unmarked history classifies via the scope-aware default.
- A2.3 OVERRIDE ALARM: harnessc check warns (never errors, exit stays 0) when
  7-day evasion crosses @var skip_override_warn_per_week (default 5).

Process note: this session's tool surface exposes no omt_skip, so the tests/
canary skip is unrepresentable here — test files were written via the
sanctioned bash path under a declared minor_feature phase (see
implementation_notes.md). No skip record from this session exists in the live
ledger; the taxonomy is exercised against hermetic ledgers below.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "omt"))

import harnessc  # noqa: E402

OMT = REPO_ROOT / ".meta" / "META_HARNESS.omt"
PHASE_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts"

F = "feature_056.skip_taxonomy_phase_hygiene"


def _ts(days_ago: float = 0.0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _skip(scope: str = "tests", purpose: str | None = None,
          days_ago: float = 0.0, ts: str | None = None) -> dict:
    rec = {"ts": ts if ts is not None else _ts(days_ago),
           "kind": "skip", "session": "s1", "reason": "t",
           "scope": scope, "tests_approved": scope in ("tests", "all")}
    if purpose is not None:
        rec["purpose"] = purpose
    return rec


# --- A2.1 effective-purpose default rule (pure) --------------------------------

class TestEffectivePurpose:
    def test_explicit_purposes_survive(self) -> None:
        for p in ("canary", "emergency", "break_glass", "override"):
            assert harnessc.skip_effective_purpose(_skip("src", p)) == p

    def test_scope_tests_defaults_canary(self) -> None:
        assert harnessc.skip_effective_purpose(_skip("tests")) == "canary"

    def test_other_scopes_default_override(self) -> None:
        for scope in ("src", "nav", "all"):
            assert harnessc.skip_effective_purpose(_skip(scope)) == "override", scope

    def test_unknown_purpose_falls_back_to_default(self) -> None:
        # A ledger record written around validation (or a future taxonomy value
        # from a newer binary) must classify, never crash the report.
        assert harnessc.skip_effective_purpose(_skip("tests", "bogus")) == "canary"
        assert harnessc.skip_effective_purpose(_skip("src", "bogus")) == "override"

    def test_non_string_purpose_falls_back_to_default(self) -> None:
        assert harnessc.skip_effective_purpose(_skip("tests", 7)) == "canary"  # type: ignore[arg-type]


# --- A2.2 seven-day split (pure) -------------------------------------------------

class TestHygieneCounts:
    def test_split_buckets(self) -> None:
        recs = [
            _skip("tests"),                       # canary → friction (default)
            _skip("src", "emergency"),            # friction (explicit)
            _skip("all", "break_glass"),          # friction (explicit)
            _skip("nav"),                         # override + nav → nav-escape
            _skip("src"),                         # override → evasion
            _skip("all", "override"),             # evasion (explicit)
        ]
        counts = harnessc.skip_hygiene_counts(recs, time.time() * 1000)
        assert counts == {"total": 6, "friction": 3,
                          "nav_escapes": 1, "evasion": 2}

    def test_window_excludes_old_and_keeps_recent(self) -> None:
        recs = [_skip("src", days_ago=8.0), _skip("src", days_ago=6.0)]
        counts = harnessc.skip_hygiene_counts(recs, time.time() * 1000)
        assert counts["total"] == 1 and counts["evasion"] == 1

    def test_non_skip_kinds_and_corrupt_ts_ignored(self) -> None:
        recs = [
            {"ts": _ts(), "kind": "phase", "scope": "src"},
            _skip("src", ts="not-a-timestamp"),
            _skip("src", ts=""),
        ]
        assert harnessc.skip_hygiene_counts(recs, time.time() * 1000) == {
            "total": 0, "friction": 0, "nav_escapes": 0, "evasion": 0}


# --- A2.3 override alarm (pure core + check wrapper) -------------------------------

class TestOverrideWarning:
    def test_at_threshold_is_quiet(self) -> None:
        assert harnessc.skip_override_warning({"evasion": 5}, 5) is None

    def test_over_threshold_warns_with_counts(self) -> None:
        w = harnessc.skip_override_warning(
            {"evasion": 6, "friction": 2, "nav_escapes": 1}, 5)
        assert w is not None and "6 evasion" in w and "warn>5/week" in w

    def test_zero_evasion_never_warns(self) -> None:
        assert harnessc.skip_override_warning(
            {"evasion": 0, "friction": 9, "nav_escapes": 9}, 5) is None


def _harnessc_corpus(var_text: str) -> harnessc.Corpus:
    errors: list[str] = []
    return harnessc.Corpus(harnessc.parse(var_text, errors))


class TestCheckAlarmWrapper:
    def test_alarm_is_warning_not_error(self, tmp_path: Path,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
        ledger = tmp_path / ".meta" / ".omt"
        ledger.mkdir(parents=True)
        (ledger / "ledger.jsonl").write_text("\n".join(
            __import__("json").dumps(_skip("src", days_ago=0.1))
            for _ in range(6)), encoding="utf-8")
        monkeypatch.setattr(harnessc, "REPO_ROOT", tmp_path)
        c = _harnessc_corpus("@var skip_override_warn_per_week : 5\n")
        harnessc.check_skip_override_alarm(c)
        assert c.errors == [] and len(c.warnings) == 1

    def test_quiet_week_no_warning(self, tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
        ledger = tmp_path / ".meta" / ".omt"
        ledger.mkdir(parents=True)
        (ledger / "ledger.jsonl").write_text("\n".join([
            __import__("json").dumps(_skip("tests", days_ago=0.1)),
            __import__("json").dumps(_skip("nav", days_ago=0.1)),
        ]), encoding="utf-8")
        monkeypatch.setattr(harnessc, "REPO_ROOT", tmp_path)
        c = _harnessc_corpus("@var skip_override_warn_per_week : 5\n")
        harnessc.check_skip_override_alarm(c)
        assert c.errors == [] and c.warnings == []

    def test_missing_ledger_fails_open(self, tmp_path: Path,
                                       monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(harnessc, "REPO_ROOT", tmp_path)
        c = _harnessc_corpus("")
        harnessc.check_skip_override_alarm(c)  # default threshold 5
        assert c.errors == [] and c.warnings == []

    def test_zero_threshold_disables(self, tmp_path: Path,
                                     monkeypatch: pytest.MonkeyPatch) -> None:
        ledger = tmp_path / ".meta" / ".omt"
        ledger.mkdir(parents=True)
        (ledger / "ledger.jsonl").write_text(
            __import__("json").dumps(_skip("src")), encoding="utf-8")
        monkeypatch.setattr(harnessc, "REPO_ROOT", tmp_path)
        c = _harnessc_corpus("@var skip_override_warn_per_week : 0\n")
        harnessc.check_skip_override_alarm(c)
        assert c.errors == [] and c.warnings == []


# --- static pins (SSOT + diet) -------------------------------------------------------

class TestStaticPins:
    def test_tool_record_carries_taxonomy_and_arg(self) -> None:
        line = next(ln for ln in OMT.read_text(encoding="utf-8").splitlines()
                    if ln.startswith("@tool omt_skip"))
        assert 'args="reason,scope?,purpose?"' in line
        assert "purpose: canary|emergency|break_glass|override" in line
        # doc.esc derive needs the literal 'Scopes: a|b' shape (harnessc regex).
        assert "Scopes: src|tests|nav|all" in line

    def test_var_threshold_present(self) -> None:
        line = next(ln for ln in OMT.read_text(encoding="utf-8").splitlines()
                    if ln.startswith("@var skip_override_warn_per_week"))
        assert line.split(":")[1].strip() == "5"

    def test_state_ledger_documents_semantics(self) -> None:
        line = next(ln for ln in OMT.read_text(encoding="utf-8").splitlines()
                    if ln.startswith("@state ledger"))
        for token in ("skip.purpose=", "EXPIRE", "abandoned"):
            assert token in line, f"@state ledger must document {token}"

    def test_ts_seed_in_sync(self) -> None:
        """The TS fallback seed must equal the .omt payload (check_tool_seed_sync
        enforces this at build; pinned here so the diet stays honest)."""
        omt = OMT.read_text(encoding="utf-8")
        payload = next(ln for ln in omt.splitlines()
                       if ln.startswith("@tool omt_skip")).split(" : ", 1)[1]
        src = PHASE_GATE.read_text(encoding="utf-8")
        assert f'irToolDescription("omt_skip", "{payload}")' in src

    def test_ts_purpose_vocab_and_default(self) -> None:
        src = PHASE_GATE.read_text(encoding="utf-8")
        for token in ('"canary", "emergency", "break_glass", "override"',
                      'scope === "tests" ? "canary" : "override"',
                      "invalid purpose"):
            assert token in src

    def test_tool_args_diet_trims(self) -> None:
        """The purpose describe is funded by trims, not growth (tool_args headroom)."""
        src = PHASE_GATE.read_text(encoding="utf-8")
        for trimmed in ('"design artifact path (major/new_screen only)"',
                        '"TDD for Programming (auto-on majors)"',
                        '"advance to: Design|Programming|Testing|Done"',
                        '"why (logged)"'):
            assert trimmed in src
