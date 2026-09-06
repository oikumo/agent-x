"""Wave 2/A4 gate_preflight — feature_055.

Contract (GREEN pins the implementation):
- PROJECTION: omt_status{op:"preflight", tool, path} returns the ORDERED
  gates that will fire for the prospective edit + a clearing action each —
  before-chain verdicts via the runBeforeGatesDry sibling (fired/stop flags:
  when=-miss vs pass vs chain-halt are distinguishable), after-chain as IR
  notes. Read-only: no ledger writes, no lint/tdd subprocesses.
- CLEARING ACTIONS: every @gate id has one; consistent with the .omt @msg
  escape hints (meta_harness_5 #9); g.think stays NOT skip-bypassable.
- GUARDRAILS: omt_status.ts gains no "TA:" literal (no self think-gate) and
  stays ledger-write-free; the default (no-op) status path is unchanged.

Bun probes exercise the REAL plugin (test_omt_q.py idiom): hermetic tmp root
+ real IR copy + OMT_LEDGER_PATH pinned explicitly (the feature_051 gotcha —
env beats the injected root, so pin it, never rely on ambient state).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
OMT = REPO_ROOT / ".meta" / "META_HARNESS.omt"
STATUS_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts"
GATE_DRIVER = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "gate_driver.ts"
SHARED_LIB = REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts"
E2E_TEST = REPO_ROOT / "tests" / "scripts" / "omt" / "test_omt_harness_e2e.py"

BUN = shutil.which("bun")

SESSION = "s55"


# --- helpers -------------------------------------------------------------------

def _ts(hours_ago: float = 0.0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def _copy_real_ir(tmp_path: Path) -> None:
    dst = tmp_path / ".meta" / ".omt"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / ".meta" / ".omt" / "harness.ir.json",
        dst / "harness.ir.json",
    )


def _write_ledger(tmp_path: Path, records: list[dict]) -> None:
    p = tmp_path / ".meta" / ".omt" / "ledger.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


# Bare probe scaffold: init the shared lib on the tmp root, import the REAL
# omt_status plugin, execute once, print the JSON result.
_probe_template = """
import { initOmtShared } from "%LIB%"
initOmtShared(process.argv[2])
const mod = await import("%PLUGIN%")
const { tool } = await mod.default({ directory: process.argv[2], worktree: process.argv[2] })
const result = await tool.omt_status.execute(%ARGS%, { sessionID: "%SESSION%" })
console.log(JSON.stringify(result))
"""


def _probe(args: dict, tmp_path: Path, ledger: list[dict] | None = None,
           extra_files: dict[str, str] | None = None) -> dict:
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    _copy_real_ir(tmp_path)
    if ledger is not None:
        _write_ledger(tmp_path, ledger)
    for rel, contents in (extra_files or {}).items():
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(contents, encoding="utf-8")
    probe = tmp_path / "probe.ts"
    probe.write_text(
        _probe_template
            .replace("%LIB%", str(SHARED_LIB))
            .replace("%PLUGIN%", str(STATUS_PLUGIN))
            .replace("%ARGS%", json.dumps(args))
            .replace("%SESSION%", SESSION),
        encoding="utf-8",
    )
    # OMT_LEDGER_PATH pinned explicitly: the env override beats the injected
    # root (feature_051 gotcha) — never depend on ambient env state.
    env = {
        **os.environ,
        "OMT_LEDGER_PATH": str(tmp_path / ".meta" / ".omt" / "ledger.jsonl"),
    }
    out = subprocess.run(
        [BUN, str(probe), str(tmp_path)],
        capture_output=True, text=True, timeout=90, env=env,
    )
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


# --- static pins ---------------------------------------------------------------

class TestStaticPins:
    def test_omt_tool_schema_carries_preflight(self) -> None:
        line = next(
            ln for ln in OMT.read_text(encoding="utf-8").splitlines()
            if ln.startswith("@tool omt_status"))
        assert 'args="op?,tool?,path?,include_ledger?"' in line
        assert "op=preflight(tool,path)" in line
        assert "ordered gates that will fire + clearing action" in line

    def test_clearing_actions_cover_every_gate(self) -> None:
        """Completeness: every @gate id in the SSOT has a clearing action —
        a new gate without one fails here (and the projection degrades to
        an empty hint, never a wrong one)."""
        gate_ids = set(re.findall(
            r"^@gate (g\.[a-z_]+)", OMT.read_text(encoding="utf-8"), re.M))
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        block = src.split("const CLEARING_ACTIONS", 1)[1].split("\n}", 1)[0]
        covered = set(re.findall(r'"(g\.[a-z_]+)":', block))
        assert gate_ids, "no @gate records parsed — the .omt shape changed?"
        assert covered == gate_ids, (
            f"clearing actions out of sync: missing={gate_ids - covered} "
            f"extra={covered - gate_ids}")

    def test_clearing_actions_consistent_with_msg_escapes(self) -> None:
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        block = src.split("const CLEARING_ACTIONS", 1)[1].split("\n}", 1)[0]

        def action(gate: str) -> str:
            m = re.search(rf'"{gate}":\s*(.+)', block)
            assert m, f"no clearing action for {gate}"
            return m.group(1)

        assert "omt_think" in action("g.think")
        assert "NOT skip-bypassable" in action("g.think")
        assert 'omt_skip{reason:"approved canary test", scope:"tests"}' in action("g.tests")
        assert "work_start" in action("g.net")
        assert "omt_phase{task_type, scope}" in action("g.phase")
        assert "test_omt_harness_e2e.py" in action("g.receipt")
        assert "omt_kb_nav" in action("g.kb")
        assert "omt_nav" in action("g.nav")
        assert "ask the user" in action("g.protect")

    def test_gate_driver_decision_flags(self) -> None:
        src = GATE_DRIVER.read_text(encoding="utf-8")
        assert "fired?: boolean" in src
        assert "stop?: boolean" in src

    def test_status_plugin_guardrails(self) -> None:
        """No TA: literal (the preflight surface stays think-gate-free on
        itself), no ledger writes (read-only projection), and the preflight
        branch short-circuits BEFORE the default path's subprocess calls."""
        src = STATUS_PLUGIN.read_text(encoding="utf-8")
        assert "TA:" not in src, (
            "omt_status.ts must not carry the TA: literal — the preflight "
            "surface would trip g.think on itself")
        assert "appendLedger" not in src and "writeLedger" not in src, (
            "omt_status stays ledger-write-free (read-only)")
        assert src.index('args?.op === "preflight"') < src.index("const lint = runLintBaseline()"), (
            "the preflight branch must short-circuit before the lint subprocess")

    def test_e2e_check_added(self) -> None:
        assert "feature_055 A4: gate_preflight wired" in E2E_TEST.read_text(
            encoding="utf-8")


# --- bun probes: the projection on the REAL plugin ------------------------------

class TestPreflightProjectionBun:
    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_src_path_empty_ledger(self, tmp_path) -> None:
        """src target, no phase: g.phase+g.kb would block; when=-missed gates
        (g.protect/g.receipt/g.tests/g.think) report fired=false; after-gates
        projected."""
        out = _probe(
            {"op": "preflight", "tool": "edit", "path": "src/agentx/__init__.py"},
            tmp_path,
            ledger=[],
            extra_files={"src/agentx/__init__.py": "# hermetic probe target\n"},
        )
        meta = out["metadata"]
        assert meta["op"] == "preflight"
        rows = {r["gate_id"]: r for r in meta["before"]}
        # ordered ascending by gate order=
        orders = [r["order"] for r in meta["before"]]
        assert orders == sorted(orders)
        assert [r["gate_id"] for r in meta["before"]] == [
            "g.protect", "g.receipt", "g.tests", "g.net",
            "g.phase", "g.think", "g.kb"], meta["before"]
        # when=-missed gates are visible but fired=false (not applicable)
        assert rows["g.protect"]["fired"] is False
        assert rows["g.receipt"]["fired"] is False
        assert rows["g.tests"]["fired"] is False
        assert rows["g.think"]["fired"] is False
        assert rows["g.net"]["fired"] is True and not rows["g.net"]["blocked"]
        assert rows["g.phase"]["fired"] is True and rows["g.phase"]["blocked"] is True
        assert rows["g.kb"]["fired"] is True and rows["g.kb"]["blocked"] is True
        assert meta["summary"]["first_blocker"] == "g.phase"
        assert meta["summary"]["would_block"] == 2
        assert meta["summary"]["before_fired"] == 3
        assert meta["summary"]["not_applicable"] == 4
        # every fired row carries a clearing action
        for r in meta["before"]:
            if r["fired"]:
                assert r["clearing_action"], f"{r['gate_id']} fired without a clearing action"
        # after-gates: notes, both projected for src/**.py
        assert [(a["gate_id"], a["order"]) for a in meta["after"]] == [
            ("g.mvc", 60), ("g.tdd_after", 70)]
        assert all(a["note"] for a in meta["after"])
        # rendered text is the actionable checklist
        assert out["output"].startswith("🛫 OMT++ PREFLIGHT")
        assert "WOULD BLOCK" in out["output"]
        assert "clear: omt_phase{task_type, scope}" in out["output"]

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_src_path_bug_fix_fast_path(self, tmp_path) -> None:
        """C2 integration: a bug_fix phase record clears g.phase AND g.kb —
        the preflight shows all-clear (the ONE-write fast path visible)."""
        out = _probe(
            {"op": "preflight", "tool": "edit", "path": "src/agentx/__init__.py"},
            tmp_path,
            ledger=[{
                "ts": _ts(), "kind": "phase", "session": SESSION,
                "task_type": "bug_fix", "phase": "Programming",
                "scope": "a4 probe", "feature": "feature_055.gate_preflight",
            }],
            extra_files={"src/agentx/__init__.py": "# hermetic probe target\n"},
        )
        meta = out["metadata"]
        rows = {r["gate_id"]: r for r in meta["before"]}
        assert rows["g.phase"]["blocked"] is False
        assert rows["g.kb"]["blocked"] is False
        assert meta["summary"]["would_block"] == 0
        assert meta["summary"]["first_blocker"] is None
        assert "all clear" in out["output"]

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_harness_path_receipt_and_think(self, tmp_path) -> None:
        """A harness-surface file carrying a thought marker: g.receipt AND
        g.think both fire and block (git-dirty + stale receipt, no consult) —
        first blocker is the lower-order receipt gate."""
        # git-init the tmp root so the copied harness file is untracked →
        # isGitDirty true → the receipt gate's staleness path engages.
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True,
                       capture_output=True)
        gd = GATE_DRIVER.read_text(encoding="utf-8")
        out = _probe(
            {"op": "preflight", "tool": "edit",
             "path": ".opencode/lib/enforcer/gate_driver.ts"},
            tmp_path,
            ledger=[],
            extra_files={".opencode/lib/enforcer/gate_driver.ts": gd},
        )
        meta = out["metadata"]
        rows = {r["gate_id"]: r for r in meta["before"]}
        assert rows["g.receipt"]["fired"] is True and rows["g.receipt"]["blocked"] is True
        assert rows["g.think"]["fired"] is True and rows["g.think"]["blocked"] is True
        assert rows["g.phase"]["fired"] is False  # not src/
        assert rows["g.kb"]["fired"] is False
        assert meta["summary"]["first_blocker"] == "g.receipt"
        assert "test_omt_harness_e2e.py" in out["output"]

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_tests_path_canary_halts_chain(self, tmp_path) -> None:
        """tests/ with a canary skip: g.tests fires, allows, and HALTS the
        chain — no later before-gate rows exist (the stop flag is honest)."""
        out = _probe(
            {"op": "preflight", "tool": "edit",
             "path": "tests/features/feature_055.gate_preflight/test_probe.py"},
            tmp_path,
            ledger=[{
                "ts": _ts(), "kind": "skip", "session": SESSION,
                "reason": "canary", "scope": "tests", "tests_approved": True,
            }],
        )
        meta = out["metadata"]
        assert [r["gate_id"] for r in meta["before"]] == [
            "g.protect", "g.receipt", "g.tests"], meta["before"]
        tests_row = meta["before"][2]
        assert tests_row["fired"] is True
        assert tests_row["blocked"] is False
        assert tests_row["halts_chain"] is True
        assert meta["after"] == []  # not src/ — no after-gates
        assert "halts the chain" in out["output"]

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_search_tool_nav_gate(self, tmp_path) -> None:
        """tool=grep on a doc path: ONLY g.nav fires (search-tools chain)."""
        out = _probe(
            {"op": "preflight", "tool": "grep", "path": ".meta/META_HARNESS.omt"},
            tmp_path,
            ledger=[],
        )
        meta = out["metadata"]
        assert [r["gate_id"] for r in meta["before"]] == ["g.nav"], meta["before"]
        assert meta["before"][0]["blocked"] is True
        assert meta["summary"]["first_blocker"] == "g.nav"
        assert "omt_nav" in out["output"]
        assert meta["after"] == []

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_path_required_unknown_op_and_protected(self, tmp_path) -> None:
        missing = _probe({"op": "preflight", "tool": "edit"}, tmp_path, ledger=[])
        assert missing["metadata"]["error"] == "path required"
        assert "path required" in missing["output"]
        bogus = _probe({"op": "bogus"}, tmp_path, ledger=[])
        assert bogus["metadata"]["error"] == "unknown op"
        assert "unknown op" in bogus["output"]
        assert "status (default) | preflight" in bogus["output"]
        # protected path: g.protect FIRES and blocks (the one gate whose
        # when= matches README.md) — clearing action points at the user ask.
        prot = _probe(
            {"op": "preflight", "tool": "edit", "path": "README.md"},
            tmp_path, ledger=[])
        meta = prot["metadata"]
        rows = {r["gate_id"]: r for r in meta["before"]}
        assert rows["g.protect"]["fired"] is True and rows["g.protect"]["blocked"] is True
        assert meta["summary"]["first_blocker"] == "g.protect"
        assert "ask the user" in prot["output"]

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_bun_default_path_banner_intact(self, tmp_path) -> None:
        """No op (or the explicit op:"status" alias) → the full default status
        (banner preserved; the preflight branch did not regress the contract;
        a live model filling the schema's default does not get an error)."""
        out = _probe({"include_ledger": False}, tmp_path, ledger=[])
        assert out["title"] == "OMT++ Status"
        assert out["output"].startswith("📊 OMT++ STATUS")
        assert "preflight" not in out["output"].splitlines()[0]
        alias = _probe({"op": "status"}, tmp_path, ledger=[])
        assert alias["title"] == "OMT++ Status"
        assert alias["output"].startswith("📊 OMT++ STATUS")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
