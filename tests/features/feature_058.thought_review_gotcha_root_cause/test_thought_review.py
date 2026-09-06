"""Wave 4/E2+E1 thought_review_gotcha_root_cause — feature_058.

Contract (GREEN pins the implementation):
- REVIEW: omt_think{op:"review"} lists alive thoughts untouched >90d with exact
  one-call archive commands (A3 dangling-list idiom, never auto-deletes).
  Reuses path?/category?/query?/top? only (no new args → tool_args +7B).
  Records a think_consult for shown files (IS a consult). Unknown-index
  thoughts read as NOT stale (fail-open). Empty on the live repo (0 stale).
- CLUSTERS (E1): 18 gotcha ids partitioned into SDK/ISOLATION/RECEIPT/
  TOOLCHAIN/MISC exactly once each (analysis_001); cluster knowledge as .omt
  # comments (0 nav cost); no renames, no retags, no demotions this wave.

Bun probes exercise the REAL think plugin (feature_055 idiom): hermetic tmp
root + OMT_LEDGER_PATH pinned explicitly (feature_051 gotcha).
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
THINK_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_think.ts"
SHARED_LIB = REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts"
E2E_TEST = REPO_ROOT / "tests" / "scripts" / "omt" / "test_omt_harness_e2e.py"

BUN = shutil.which("bun")

SESSION = "s58"


def _ts(days_ago: float = 0.0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _think_src() -> str:
    return THINK_PLUGIN.read_text(encoding="utf-8")


# --- static pins ---------------------------------------------------------------

def test_review_threshold_is_90d() -> None:
    assert "STALE_AFTER_DAYS = 90" in _think_src(), (
        "E2 review threshold is a hardcoded 90d policy pin (no @var for zero benefit)")


def test_review_dispatched_and_advertised() -> None:
    src = _think_src()
    assert 'case "review": return omt_think_review.execute(args, context)' in src, (
        "dispatcher must route op=review to the review impl")
    assert "add|list|remove|verify|suggest|review" in src, (
        "op enum must advertise review (tool_args +7B only)")
    assert "want add|list|remove|verify|suggest|review" in src, (
        "unknown-op message must list review")


def test_tool_payload_mirrors_seed() -> None:
    omt = OMT.read_text(encoding="utf-8")
    assert "| review(stale>90d)." in omt, (
        ".omt @tool omt_think payload must carry the review schema text")
    assert _think_src().count('| review(stale>90d).') >= 1, (
        "TS irToolDescription seed must mirror the .omt payload (check_tool_seed_sync)")


def test_review_reuses_args_only() -> None:
    """No new top-level arg describes for review: path/category/query/top reused."""
    src = _think_src()
    # The registered dispatcher gains no new arg beyond the 9 existing ones.
    m = re.search(
        r'irToolDescription\(\s*"omt_think".*?async execute', src, re.DOTALL)
    assert m, "dispatcher block must exist"
    region = m.group(0)
    describes = re.findall(r'describe\(\s*"((?:[^"\\]|\\.)*)"', region)
    assert len(describes) == 9, (
        f"dispatcher keeps 9 arg describes (op + 8 args), got {len(describes)}")


def test_review_read_only_except_consult() -> None:
    body = _think_src().split("const omt_think_review")[1].split(
        "const omt_think = tool(")[0]
    assert "recordConsult(session," in body, (
        "review IS a consult → records think_consult (clears think-gate)")
    assert "appendIndex" not in body and "writeFileSync" not in body, (
        "review never writes the thought index or files (read-only advisor)")


def test_cluster_comments_present_zero_nav_cost() -> None:
    omt = OMT.read_text(encoding="utf-8")
    assert "# E1 (feature_058): cluster map" in omt, (
        "E1 cluster map must live in .omt # comments (parser-ignored, 0 nav cost)")


def test_cluster_partition_covers_18_exactly_once() -> None:
    expected = {
        # SDK-contract (4)
        "gotcha.loader_exports", "gotcha.sdk_contract",
        "gotcha.live_binary", "gotcha.ts_no_reload",
        # isolation (3, incl. demoted)
        "tdd.env_flaky_fixed", "gotcha.red_runnable", "gotcha.tdd_node",
        # receipt (4)
        "gotcha.receipt_second_edit", "gotcha.receipt_round_robin",
        "gotcha.bugb_recipe", "gotcha.write_large",
        # toolchain (3)
        "gotcha.testlist_json", "gotcha.tdd_toolchain", "gotcha.plugin_probe",
        # misc (4)
        "gotcha.done_reachable", "gotcha.think_gated",
        "gotcha.tests_canary_shadow", "gotcha.plugin_ctx",
    }
    omt = OMT.read_text(encoding="utf-8")
    found = set(re.findall(r"@doc (gotcha\.\w+|tdd\.env_flaky_fixed)\b", omt))
    assert found == expected, (
        f"cluster partition must cover exactly the 18 ids once each: "
        f"missing={sorted(expected - found)} extra={sorted(found - expected)}")


def test_no_new_tool_doc_msg_records() -> None:
    omt = OMT.read_text(encoding="utf-8")
    tools = re.findall(r"^@tool ", omt, re.M)
    assert len(tools) == 10, "no new @tool records (review rides omt_think)"


# --- bun probes (REAL plugin, hermetic tmp root) -------------------------------

_probe_template = """
import { initOmtShared } from "%LIB%"
initOmtShared(process.argv[2])
const mod = await import("%PLUGIN%")
const { tool } = await mod.default({ directory: process.argv[2], worktree: process.argv[2] })
const result = await tool.omt_think.execute(%ARGS%, { sessionID: "%SESSION%" })
console.log(JSON.stringify(result))
"""


def _probe(args: dict, tmp_path: Path,
           files: dict[str, str] | None = None,
           index: list[dict] | None = None) -> str:
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    for rel, contents in (files or {}).items():
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(contents, encoding="utf-8")
    omt_dir = tmp_path / ".meta" / ".omt"
    omt_dir.mkdir(parents=True, exist_ok=True)
    with (omt_dir / "thoughts.jsonl").open("w", encoding="utf-8") as fh:
        for r in (index or []):
            fh.write(json.dumps(r) + "\n")
    (omt_dir / "ledger.jsonl").write_text("", encoding="utf-8")
    probe = tmp_path / "probe.ts"
    probe.write_text(
        _probe_template
            .replace("%LIB%", str(SHARED_LIB))
            .replace("%PLUGIN%", str(THINK_PLUGIN))
            .replace("%ARGS%", json.dumps(args))
            .replace("%SESSION%", SESSION),
        encoding="utf-8",
    )
    env = {**os.environ,
           "OMT_LEDGER_PATH": str(omt_dir / "ledger.jsonl")}
    out = subprocess.run(
        [BUN, str(probe), str(tmp_path)],
        capture_output=True, text=True, timeout=60, cwd=str(REPO_ROOT), env=env)
    assert out.returncode == 0, f"probe failed: {out.stderr[-2000:]}"
    return json.loads(out.stdout)


def _ledger(tmp_path: Path) -> list[dict]:
    p = tmp_path / ".meta" / ".omt" / "ledger.jsonl"
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(
        encoding="utf-8").splitlines() if line.strip()]


def test_probe_empty_repo_zero_stale(tmp_path: Path) -> None:
    out = _probe({"op": "review"}, tmp_path)
    assert "0 stale thoughts" in out and ">90d" in out, out


def test_probe_old_thought_listed_with_remove_command(tmp_path: Path) -> None:
    files = {"a.py": "# TA: gotcha: ancient wisdom\nx = 1\n"}
    index = [{"ts": _ts(100), "path": "a.py", "line": 1,
              "category": "gotcha", "thought": "ancient wisdom"}]
    out = _probe({"op": "review"}, tmp_path, files=files, index=index)
    assert "1 stale thought" in out, out
    assert 'omt_think{op:"remove", path:"a.py", line:1}' in out, out
    assert "100d" in out, out


def test_probe_fresh_thought_not_listed(tmp_path: Path) -> None:
    files = {"a.py": "# TA: gotcha: fresh news\nx = 1\n"}
    index = [{"ts": _ts(10), "path": "a.py", "line": 1,
              "category": "gotcha", "thought": "fresh news"}]
    out = _probe({"op": "review"}, tmp_path, files=files, index=index)
    assert "0 stale thoughts" in out, out


def test_probe_unknown_index_fail_open(tmp_path: Path) -> None:
    files = {"a.py": "# TA: why: no index record\nx = 1\n"}
    out = _probe({"op": "review"}, tmp_path, files=files, index=[])
    assert "0 stale thoughts" in out, out


def test_probe_verify_refreshes_touch(tmp_path: Path) -> None:
    """A recent verify rescues an old add from the stale list."""
    files = {"a.py": "# TA: gotcha: rechecked\nx = 1\n"}
    index = [
        {"ts": _ts(100), "path": "a.py", "line": 1,
         "category": "gotcha", "thought": "rechecked"},
        {"kind": "verify", "ts": _ts(5), "path": "a.py", "line": 1,
         "category": "gotcha", "thought": "rechecked",
         "status": "verified", "basis": "exists"},
    ]
    out = _probe({"op": "review"}, tmp_path, files=files, index=index)
    assert "0 stale thoughts" in out, out


def test_probe_category_filter(tmp_path: Path) -> None:
    files = {"a.py": "# TA: gotcha: old g\n# TA: why: old w\nx = 1\n"}
    index = [
        {"ts": _ts(100), "path": "a.py", "line": 1,
         "category": "gotcha", "thought": "old g"},
        {"ts": _ts(100), "path": "a.py", "line": 2,
         "category": "why", "thought": "old w"},
    ]
    out = _probe({"op": "review", "category": "why"}, tmp_path,
                 files=files, index=index)
    assert "old w" in out and "old g" not in out, out


def test_probe_records_consult_for_shown_files(tmp_path: Path) -> None:
    files = {"a.py": "# TA: gotcha: ancient wisdom\nx = 1\n"}
    index = [{"ts": _ts(100), "path": "a.py", "line": 1,
              "category": "gotcha", "thought": "ancient wisdom"}]
    _probe({"op": "review"}, tmp_path, files=files, index=index)
    consults = [r for r in _ledger(tmp_path) if r.get("kind") == "think_consult"]
    assert len(consults) == 1 and consults[0]["files"] == ["a.py"], consults


def test_probe_live_repo_zero_stale() -> None:
    """Live-repo smoke (read-only): today's index has nothing >90d (analysis_001)."""
    result = subprocess.run(
        ["uv", "run", "--no-sync", "python", "-c",
         "import json; recs=[json.loads(l) for l in "
         "open('.meta/.omt/thoughts.jsonl')]; print(len(recs))"],
        capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert result.returncode == 0
    assert int(result.stdout.strip()) >= 100
