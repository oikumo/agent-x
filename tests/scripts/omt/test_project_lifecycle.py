# tests/scripts/omt/test_project_lifecycle.py — feature_030.project_lifecycle goldens.
#
# Hermetic: OMT_LEDGER_PATH / OMT_PROJECTS_ROOT / OMT_PROJECTS_ARCHIVE redirect
# all state to tmp_path (project_state.py reads env PER CALL — design_001 §1).
# Lazy importlib loads: RED rounds run with scripts/omt/project.py absent
# (GOTCHA_RED_RUNNABLE — failures surface as test failures, not collection errors).
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "omt"

import sys  # noqa: E402

sys.path.insert(0, str(SCRIPT_DIR))  # harnessc imports project_state at module level


def _mod(name: str):
    """Import scripts/omt/<name>.py (lazy — module may not exist at RED)."""
    if str(SCRIPT_DIR) in sys.path:
        return importlib.import_module(name)
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Hermetic state env: ledger + projects root + archive under tmp_path."""
    ledger = tmp_path / "ledger.jsonl"
    proots = tmp_path / ".projects" / "meta"
    parch = tmp_path / ".projects" / "archive"
    proots.mkdir(parents=True)
    monkeypatch.setenv("OMT_LEDGER_PATH", str(ledger))
    monkeypatch.setenv("OMT_PROJECTS_ROOT", str(proots))
    monkeypatch.setenv("OMT_PROJECTS_ARCHIVE", str(parch))
    return {"ledger": ledger, "root": proots, "archive": parch, "tmp": tmp_path}


def _records(ledger: Path) -> list[dict]:
    if not ledger.exists():
        return []
    return [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]


class TestProjectPy:
    """R1 (testlist ❶–❻): project.py CLI + project_state derivations."""

    def test_new_creates_home_record_manifest(self, env):
        project = _mod("project")
        rc = project.main(["new", "alpha proj"])
        assert rc == 0
        home = env["root"] / "alpha_proj"
        project_md = (home / "PROJECT.md").read_text()
        assert (home / "CURRENT_STATE.md").exists()
        assert re.search(r"> Status: \*\*draft\*\*", project_md)
        kinds = [r for r in _records(env["ledger"]) if r.get("kind") == "project"]
        assert len(kinds) == 1 and kinds[0]["op"] == "create" and kinds[0]["project"] == "alpha_proj"
        manifest = (env["root"] / "META.md").read_text()
        assert "alpha_proj" in manifest and "draft" in manifest

    def test_link_idempotent(self, env):
        project = _mod("project")
        project.main(["new", "alpha proj"])
        assert project.main(["link", "feature_030.x", "alpha_proj"]) == 0
        assert project.main(["link", "feature_030.x", "alpha_proj"]) == 0
        links = [r for r in _records(env["ledger"]) if r.get("kind") == "project_link"]
        assert len(links) == 1
        assert links[0]["project"] == "alpha_proj" and links[0]["feature"] == "feature_030.x"

    def test_derive_state_fsm(self, env):
        ps = _mod("project_state")
        records = [
            {"kind": "project", "op": "create", "project": "p"},
        ]
        links = {}
        assert ps.derive_state("p", records, links) == "draft"
        links["feature_001.a"] = {"project": "p", "origin": "manual", "ts": "t"}
        assert ps.derive_state("p", records, links) == "active"
        records.append({"kind": "project", "op": "close", "project": "p"})
        assert ps.derive_state("p", records, links) == "complete"
        records.append({"kind": "project", "op": "archive", "project": "p"})
        assert ps.derive_state("p", records, links) == "archived"
        records.append({"kind": "project", "op": "reopen", "project": "p"})
        assert ps.derive_state("p", records, links) == "active"
        assert ps.derive_state("ghost", records, links) == "unknown"

    def test_log_blocks(self, env):
        project = _mod("project")
        project.main(["new", "alpha proj"])
        assert project.main(["log", "alpha_proj", "first note"]) == 0
        assert project.main(["log", "alpha_proj", "second note"]) == 0
        text = (env["root"] / "alpha_proj" / "CURRENT_STATE.md").read_text()
        assert "first note" in text and "second note" in text
        # same-day merge: exactly one dated block header for today
        assert len(re.findall(r"^## \d{4}-\d{2}-\d{2}", text, re.M)) == 1

    def test_close_guard_and_force(self, env):
        project = _mod("project")
        project.main(["new", "alpha proj"])
        project.main(["link", "feature_099.x", "alpha_proj"])
        # linked feature has no complete record → guard refuses (exit 3)
        assert project.main(["close", "alpha_proj"]) == 3
        # --force proceeds; header flips to complete
        assert project.main(["close", "alpha_proj", "--force"]) == 0
        header = (env["root"] / "alpha_proj" / "PROJECT.md").read_text()
        assert re.search(r"> Status: \*\*complete\*\*", header)

    def test_sync_reconciles_header_and_manifest(self, env):
        project = _mod("project")
        project.main(["new", "alpha proj"])
        project.main(["link", "feature_030.x", "alpha_proj"])
        # header still says draft (link does not flip); sync reconciles
        assert project.main(["sync"]) == 0
        header = (env["root"] / "alpha_proj" / "PROJECT.md").read_text()
        assert re.search(r"> Status: \*\*active\*\*", header)
        manifest = (env["root"] / "META.md").read_text()
        row = [ln for ln in manifest.splitlines() if "alpha_proj" in ln]
        assert row and "active" in row[0] and "feature_030.x" in row[0]


def _corpus(extra: str = ""):
    harnessc = _mod("harnessc")
    text = ("@var projects_root : .projects/meta\n"
            "@var projects_archive : .projects/archive\n"
            "@var project_resume_threshold_bytes : 16384\n" + extra)
    errors: list[str] = []
    records = harnessc.parse(text, errors)
    assert not errors, f"fixture .omt failed to parse: {errors}"
    return harnessc.Corpus(records)


class TestHarnesscChecks:
    """R2 (testlist ❼–⓫): the five check_projects_* compiler checks."""

    def test_structure_flags_missing_pair_bak_and_order(self, env):
        harnessc = _mod("harnessc")
        (env["root"] / "no_current").mkdir()
        (env["root"] / "no_current" / "PROJECT.md").write_text("# x\n> Status: **draft**\n")
        (env["root"] / "with_bak").mkdir()
        (env["root"] / "with_bak" / "PROJECT.md").write_text("# x\n> Status: **draft**\n")
        (env["root"] / "with_bak" / "CURRENT_STATE.md").write_text("# c\n")
        (env["root"] / "with_bak" / "stale.bak").write_text("x")
        (env["root"] / "bad_order").mkdir()
        (env["root"] / "bad_order" / "PROJECT.md").write_text("# x\n> Status: **draft**\n")
        (env["root"] / "bad_order" / "CURRENT_STATE.md").write_text(
            "# c\n## 2026-08-15 (old)\n\n---\n\n## 2026-08-16 (newer on bottom)\n")
        c = _corpus()
        harnessc.check_projects_structure(c)
        joined = "\n".join(c.errors)
        assert "no_current" in joined and ".bak" in joined and "bad_order" in joined

    def test_links_phantom_and_after_close(self, env):
        harnessc = _mod("harnessc")
        ps = _mod("project_state")
        (env["root"] / "p1").mkdir()
        (env["root"] / "p1" / "PROJECT.md").write_text("> Status: **active**\n")
        (env["root"] / "p1" / "CURRENT_STATE.md").write_text("# c\n")
        ps.write_record({"kind": "project", "op": "create", "project": "p1"})
        ps.write_record({"kind": "project_link", "project": "p1",
                         "feature": "feature_999.phantom", "origin": "manual", "ts": "2026-08-22T01:00:00"})
        ps.write_record({"kind": "project", "op": "close", "project": "p1", "ts": "2026-08-22T02:00:00"})
        ps.write_record({"kind": "project_link", "project": "p1",
                         "feature": "feature_030.project_lifecycle", "origin": "manual",
                         "ts": "2026-08-22T03:00:00"})  # after close
        c = _corpus()
        harnessc.check_projects_links(c)
        joined = "\n".join(c.errors)
        assert "feature_999.phantom" in joined  # phantom feature dir
        assert "after close" in joined          # link written after close

    def test_links_backfill_shaped_ledger_passes(self, env):
        harnessc = _mod("harnessc")
        ps = _mod("project_state")
        (env["root"] / "rag_v2").mkdir()
        (env["root"] / "rag_v2" / "PROJECT.md").write_text("> Status: **active**\n")
        (env["root"] / "rag_v2" / "CURRENT_STATE.md").write_text("# c\n")
        ps.write_record({"kind": "project", "op": "create", "project": "rag_v2"})
        for feat in ("feature_027.rag_v2", "feature_029.rag_v2_slash_commands"):
            ps.write_record({"kind": "project_link", "project": "rag_v2",
                             "feature": feat, "origin": "backfill"})
        c = _corpus()
        harnessc.check_projects_links(c)
        assert c.errors == []

    def test_resume_block(self, env):
        harnessc = _mod("harnessc")
        (env["root"] / "big").mkdir()
        (env["root"] / "big" / "CURRENT_STATE.md").write_text("# c\n")
        (env["root"] / "big" / "PROJECT.md").write_text("> Status: **draft**\n" + "x" * 17000)
        (env["root"] / "big_ok").mkdir()
        (env["root"] / "big_ok" / "CURRENT_STATE.md").write_text("# c\n")
        (env["root"] / "big_ok" / "PROJECT.md").write_text(
            "> Status: **draft**\n\n## New Session Quick Start\n\n" + "x" * 17000)
        c = _corpus()
        harnessc.check_projects_resume(c)
        joined = "\n".join(c.errors)
        assert "big/" in joined and "big_ok" not in joined

    def test_status_mismatch_hint_and_manifest_staleness(self, env):
        harnessc = _mod("harnessc")
        ps = _mod("project_state")
        (env["root"] / "p1").mkdir()
        (env["root"] / "p1" / "PROJECT.md").write_text("> Status: **draft**\n")
        (env["root"] / "p1" / "CURRENT_STATE.md").write_text("# c\n")
        ps.write_record({"kind": "project", "op": "create", "project": "p1"})
        ps.write_record({"kind": "project_link", "project": "p1",
                         "feature": "feature_030.project_lifecycle", "origin": "manual"})
        c = _corpus()
        harnessc.check_projects_status(c)      # header draft vs derived active
        harnessc.check_projects_manifest(c)    # no manifest written
        joined = "\n".join(c.errors)
        assert "draft" in joined and "active" in joined and "project.py sync" in joined
        assert "META.md missing" in joined


class TestScaffoldLink:
    """R2 component 3: new_feature.py --project writes the spawn-time link."""

    def test_dry_run_announces_project_link(self, capsys):
        new_feature = _mod("new_feature")
        rc = new_feature.main(["zzz probe", "--type", "minor_feature",
                               "--project", "alpha_proj", "--dry-run"])
        out = capsys.readouterr().out
        assert rc == 0 and "alpha_proj" in out


class TestBackfill:
    """R2/R5 (testlist ⓰): backfill command + header normalization."""

    def test_backfill_create_record_idempotent(self, env):
        project = _mod("project")
        ps = _mod("project_state")
        (env["root"] / "old_home").mkdir()
        (env["root"] / "old_home" / "PROJECT.md").write_text("> Status: **v1.3 (2026-08-01)** — stuff\n")
        (env["root"] / "old_home" / "CURRENT_STATE.md").write_text("# c\n")
        assert project.main(["backfill", "old_home"]) == 0
        assert project.main(["backfill", "old_home"]) == 0  # no-op second time
        creates = [r for r in ps.read_ledger_all()
                   if r.get("kind") == "project" and r.get("op") == "create"]
        assert len(creates) == 1
        # sync normalizes the unparseable legacy header to the machine form
        assert project.main(["sync"]) == 0
        header = (env["root"] / "old_home" / "PROJECT.md").read_text()
        assert "> Status: **draft**" in header


# --- R3: phase_gate.ts hooks (bun probes, test_omt_q.py idiom) ----------------

BUN = shutil.which("bun")
SHARED_LIB = REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts"
PHASE_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts"

_pg_probe_template = """
import { initOmtShared } from "%LIB%"
initOmtShared(process.argv[2])
const pg = await import("%PHASE_GATE%")
const env = { directory: process.argv[2], safeLog: () => {} }
const out = %CALL%
console.log(JSON.stringify(out ?? null))
"""


def _pg_probe(call: str, tmp_path: Path, ledger: list[dict] | None = None,
              files: dict | None = None):
    """Probe an exported phase_gate.ts helper under a hermetic tmp root."""
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    lp = tmp_path / ".meta" / ".omt" / "ledger.jsonl"
    lp.parent.mkdir(parents=True, exist_ok=True)
    if ledger is not None:  # None = keep the ledger the previous probe wrote
        with lp.open("w", encoding="utf-8") as fh:
            for r in ledger:
                fh.write(json.dumps(r) + "\n")
    for rel, contents in (files or {}).items():
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(contents, encoding="utf-8")
    probe = tmp_path / "probe.ts"
    probe.write_text(
        _pg_probe_template.replace("%LIB%", str(SHARED_LIB))
        .replace("%PHASE_GATE%", str(PHASE_GATE)).replace("%CALL%", call),
        encoding="utf-8",
    )
    out = subprocess.run([BUN, str(probe), str(tmp_path)],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return json.loads(out.stdout.strip().splitlines()[-1])


def _tmp_ledger_records(tmp_path: Path) -> list[dict]:
    lp = tmp_path / ".meta" / ".omt" / "ledger.jsonl"
    if not lp.exists():
        return []
    return [json.loads(x) for x in lp.read_text().splitlines() if x.strip()]


@pytest.mark.skipif(BUN is None, reason="bun runtime not available")
class TestPhaseGateProjectHooks:
    """R3 (testlist ⓬–⓭): design_doc inference + omt_complete ship-sync."""

    def test_infer_link_from_design_doc_writes_once(self, tmp_path):
        call = ('pg.maybeLinkProjectFromDesignDoc(env, "ses_probe", '
                '"feature_030.x", ".projects/meta/p1/PROJECT.md")')
        files = {".projects/meta/p1/PROJECT.md": "# p\n> Status: **draft**\n"}
        first = _pg_probe(f"await {call}", tmp_path, files=files)
        assert first == "p1"
        links = [r for r in _tmp_ledger_records(tmp_path)
                 if r.get("kind") == "project_link"]
        assert len(links) == 1 and links[0]["origin"] == "inferred"
        second = _pg_probe(f"await {call}", tmp_path, files=files)
        assert second is None  # already linked — no duplicate record
        links = [r for r in _tmp_ledger_records(tmp_path)
                 if r.get("kind") == "project_link"]
        assert len(links) == 1

    def test_infer_ignores_non_project_and_missing_paths(self, tmp_path):
        non_project = _pg_probe(
            'pg.maybeLinkProjectFromDesignDoc(env, "ses_probe", "feature_030.x", '
            '".meta/software_development_process/4.design/features/feature_030.x/design_001_a.md")',
            tmp_path,
            files={".meta/software_development_process/4.design/features/feature_030.x/design_001_a.md": "# d\n"},
        )
        assert non_project is None
        missing = _pg_probe(
            'pg.maybeLinkProjectFromDesignDoc(env, "ses_probe", "feature_030.x", '
            '".projects/meta/ghost/PROJECT.md")', tmp_path)
        assert missing is None
        assert _tmp_ledger_records(tmp_path) == [] or all(
            r.get("kind") != "project_link" for r in _tmp_ledger_records(tmp_path))

    def test_ship_sync_inserts_block_idempotently(self, tmp_path):
        ledger = [{"kind": "project_link", "project": "p1",
                   "feature": "feature_030.x", "origin": "backfill", "ts": "t0"}]
        files = {".projects/meta/p1/CURRENT_STATE.md":
                 "# CURRENT_STATE: p1\n\n> log\n\n---\n\n## 2026-08-01 (iter 0)\n\n- old\n"}
        call = ('pg.syncProjectLogFromLedger(env, "feature_030.x", "major_feature")')
        note = _pg_probe(f"await {call}", tmp_path, ledger=ledger, files=files)
        assert note and "p1" in note
        text = (tmp_path / ".projects/meta/p1/CURRENT_STATE.md").read_text()
        assert text.count("(auto — feature_030.x Done)") == 1
        assert "test_report.md" in text
        again = _pg_probe(f"await {call}", tmp_path, ledger=ledger, files=None)
        assert again and ("already" in again or "p1" in again)
        text2 = (tmp_path / ".projects/meta/p1/CURRENT_STATE.md").read_text()
        assert text2.count("(auto — feature_030.x Done)") == 1  # idempotent

    def test_ship_sync_unlinked_feature_is_note_only(self, tmp_path):
        note = _pg_probe(
            'pg.syncProjectLogFromLedger(env, "feature_030.x", "bug_fix")', tmp_path)
        assert note and "no project link" in note
        assert not (tmp_path / ".projects").exists() or not any(
            (tmp_path / ".projects").rglob("CURRENT_STATE.md"))


# --- R4: omt_q project_drift + omt_status project line (bun probes) -----------

OMT_Q_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_q.ts"
OMT_STATUS_PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts"

_tool_probe_template = """
import { initOmtShared } from "%LIB%"
initOmtShared(process.argv[2])
const mod = await import("%PLUGIN%")
const { tool } = await mod.default({ directory: process.argv[2], worktree: process.argv[2] })
const result = await tool.%TOOL%.execute(%ARGS%, { sessionID: "ses_probe" })
console.log(typeof result === "string" ? result : JSON.stringify(result))
"""


def _tool_probe(plugin: Path, tool_name: str, args_json: str, tmp_path: Path,
                ledger: list[dict] | None = None, files: dict | None = None):
    assert BUN is not None, "bun runtime required (guard against skipif bypass)"
    lp = tmp_path / ".meta" / ".omt" / "ledger.jsonl"
    lp.parent.mkdir(parents=True, exist_ok=True)
    with lp.open("w", encoding="utf-8") as fh:
        for r in (ledger or []):
            fh.write(json.dumps(r) + "\n")
    for rel, contents in (files or {}).items():
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(contents, encoding="utf-8")
    probe = tmp_path / "probe.ts"
    probe.write_text(
        _tool_probe_template.replace("%LIB%", str(SHARED_LIB))
        .replace("%PLUGIN%", str(plugin)).replace("%TOOL%", tool_name)
        .replace("%ARGS%", args_json),
        encoding="utf-8",
    )
    out = subprocess.run([BUN, str(probe), str(tmp_path)],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, f"bun probe failed:\n{out.stderr}\n---"
    return out.stdout.strip().splitlines()[-1]


@pytest.mark.skipif(BUN is None, reason="bun runtime not available")
class TestOmtQProjectDrift:
    """R4 (testlist ⓮): additive project_drift in op=drift; U3 pins intact."""

    def _fixtures(self, tmp_path):
        old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        ledger = [
            {"kind": "project", "op": "create", "project": "p1", "ts": old},
            {"kind": "project", "op": "create", "project": "p3", "ts": old},
            {"kind": "project_link", "project": "p1", "feature": "feature_030.x",
             "origin": "scaffold", "ts": old},
            {"kind": "project_link", "project": "p1", "feature": "feature_999.ghost",
             "origin": "manual", "ts": old},
            {"kind": "complete", "feature": "feature_030.x", "ts": "2026-08-20T10:00:00"},
            {"kind": "phase", "feature": "feature_031.y", "task_type": "major_feature",
             "design_doc": ".projects/meta/p2/PROJECT.md", "ts": old},
        ]
        files = {
            ".projects/meta/p1/PROJECT.md": "# p1\n> Status: **active**\n",
            ".projects/meta/p1/CURRENT_STATE.md": "# c\n\n---\n\n## 2026-08-01 (old top)\n\n- x\n",
            ".projects/meta/p2/PROJECT.md": "# p2\n> Status: **draft**\n",
            ".projects/meta/p2/CURRENT_STATE.md": "# c\n",
            ".projects/meta/p3/PROJECT.md": "# p3\n> Status: **draft**\n",
            ".projects/meta/p3/CURRENT_STATE.md": "# c\n",
            ".meta/software_development_process/2.requirements/features/feature_030.x/FEATURE.md": "# f\n",
        }
        return ledger, files

    def test_project_drift_classes_and_u3_intact(self, tmp_path):
        ledger, files = self._fixtures(tmp_path)
        raw = _tool_probe(OMT_Q_PLUGIN, "omt_q", '{"op":"drift"}', tmp_path,
                          ledger=ledger, files=files)
        out = json.loads(raw)
        assert "project_drift" in out, f"additive field missing: {list(out)}"
        classes = {(e["class"], e.get("feature") or e.get("project"))
                   for e in out["project_drift"]}
        assert ("stale-log", "feature_030.x") in classes
        assert ("phantom-link", "feature_999.ghost") in classes
        assert ("unlinked-project-backed", "feature_031.y") in classes
        assert ("aging-draft", "p3") in classes
        # U3 legacy surface untouched
        assert out["count_drift"]["direction_b_only"] is True
        assert "drift_records" in out


@pytest.mark.skipif(BUN is None, reason="bun runtime not available")
class TestOmtStatusProject:
    """R4 (testlist ⓯): omt_status shows the derived active project."""

    def test_project_line_when_linked(self, tmp_path):
        now = datetime.now(timezone.utc).isoformat()
        ledger = [
            {"kind": "project", "op": "create", "project": "p1", "ts": now},
            {"kind": "project_link", "project": "p1", "feature": "feature_030.x",
             "origin": "scaffold", "ts": now},
            {"kind": "phase", "session": "ses_probe", "feature": "feature_030.x",
             "task_type": "major_feature", "phase": "Programming", "ts": now},
        ]
        files = {
            ".projects/meta/p1/PROJECT.md": "# p1\n> Status: **active**\n",
            ".projects/meta/p1/CURRENT_STATE.md": "# c\n\n---\n\n## 2026-08-20 (top)\n\n- x\n",
        }
        raw = _tool_probe(OMT_STATUS_PLUGIN, "omt_status", "{}", tmp_path,
                          ledger=ledger, files=files)
        assert "Project: p1 (active)" in raw, raw
        assert "last log 2026-08-20" in raw

    def test_no_project_line_when_unlinked(self, tmp_path):
        now = datetime.now(timezone.utc).isoformat()
        ledger = [{"kind": "phase", "session": "ses_probe", "feature": "feature_030.x",
                   "task_type": "bug_fix", "phase": "Programming", "ts": now}]
        raw = _tool_probe(OMT_STATUS_PLUGIN, "omt_status", "{}", tmp_path, ledger=ledger)
        assert "Project:" not in raw
