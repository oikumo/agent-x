#!/usr/bin/env python3
"""Comprehensive e2e smoke test for the OMT++ META HARNESS.

This test intentionally spans the whole process-enforcement surface instead of
only one unit:

- the opencode plugin source that gates OMT phases;
- the standalone status plugin;
- the Python OMT helper scripts;
- the live opencode permission config;
- the OMT guide / template contract that the gate enforces.

When it passes, it writes an ignored runtime receipt under `.meta/.omt/`. The
opencode plugin uses that receipt to force a fresh run before repeatedly editing
the OMT harness after it has changed.

Run with:
    uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
E2E_COMMAND = "uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q"
RECEIPT_PATH = REPO_ROOT / ".meta" / ".omt" / "omt_harness_e2e_last_run.json"

HARNESS_FILES = [
    ".opencode/plugins/omt_enforcer.ts",
    ".opencode/plugins/omt_status.ts",
    ".opencode/plugins/omt_think.ts",
    "opencode.jsonc",
    "AGENTS.md",
    ".meta/software_development_process/omt_agent_guide.md",
    "scripts/omt/mvc_check.py",
    "scripts/omt/new_feature.py",
    "scripts/omt/tdd_check.py",
    "tests/scripts/omt/test_omt_harness_e2e.py",
]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _sha256(rel_path: str) -> str:
    return hashlib.sha256((REPO_ROOT / rel_path).read_bytes()).hexdigest()


def _write_receipt(checks: list[str]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(
        json.dumps(
            {
                "passed_at": datetime.now(UTC).isoformat(),
                "command": E2E_COMMAND,
                "checks": checks,
                "covered_files": HARNESS_FILES,
                "sha256": {rel: _sha256(rel) for rel in HARNESS_FILES},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_omt_meta_harness_end_to_end_contract() -> None:
    enforcer = _read(".opencode/plugins/omt_enforcer.ts")
    status = _read(".opencode/plugins/omt_status.ts")
    config = _read("opencode.jsonc")
    guide = _read(".meta/software_development_process/omt_agent_guide.md")

    checks: list[str] = []

    # 1. The status plugin is standalone and the previous dynamic import failure
    # mode cannot return.
    assert "export default async () => ({" in status
    assert "tool: { omt_status }" in status
    assert "p.split" not in status
    assert "dynamic" not in status.lower()
    assert "omt_status is registered by .opencode/plugins/omt_status.ts" in enforcer
    checks.append("standalone omt_status plugin has no dynamic p.split path")

    # 2. Phase declarations and completions are real opencode tools, scoped to
    # feature phases, with lightweight task types excluded from major-feature
    # artifact over-enforcement.
    assert "const omt_phase = tool" in enforcer
    assert "const omt_skip = tool" in enforcer
    assert "const omt_complete = tool" in enforcer
    assert "getActiveFeaturePhase(feature, session)" in enforcer
    assert 'ARTIFACT_REQUIRED.has(phaseRecord.task_type || "")' in enforcer
    assert "checkPhaseExitArtifacts(directory, feature, currentPhase)" in enforcer
    checks.append("omt_phase/omt_complete tool chain is wired and scoped")

    # 3. The harness now enforces this e2e test for repeated edits to the OMT
    # enforcement surface.
    assert "OMT_HARNESS_E2E_COMMAND" in enforcer
    assert E2E_COMMAND in enforcer
    assert "omtHarnessE2eStatus" in enforcer
    assert "OMT_HARNESS_E2E_RECEIPT" in enforcer
    assert ".meta/software_development_process/omt_agent_guide.md" in enforcer
    checks.append("OMT harness edit guard requires this e2e receipt")

    # 4. Coarse permissions still force uv and deny the risky actions the meta
    # harness is meant to prevent.
    assert '"$schema": "https://opencode.ai/config.json"' in config
    assert '"uv *": "allow"' in config
    assert '"python *": "deny"' in config
    assert '"python3 *": "deny"' in config
    assert '"pip *": "deny"' in config
    assert '"pytest *": "deny"' in config
    assert '"git commit *": "deny"' in config
    assert '"git push *": "deny"' in config
    checks.append("opencode config enforces uv and denies risky actions")

    # 5. The guide contract and plugin gate agree on adaptive rigor.
    assert "Essential vs. Optional" in guide
    assert "Bug Fix" in guide and "Minor Feature" in guide and "Major Feature" in guide
    assert 'ARTIFACT_REQUIRED = new Set(["major_feature", "new_screen"])' in enforcer
    assert "PHASE_EXIT_REQUIREMENTS" in enforcer
    assert "operation_spec_*.md" in enforcer
    checks.append("guide §12 and plugin artifact matrix stay aligned")

    # 6. Python OMT helper scripts execute successfully through uv.
    mvc = _run(["uv", "run", "scripts/omt/mvc_check.py", "--json"])
    assert mvc.returncode == 0, mvc.stdout + mvc.stderr
    mvc_data = json.loads(mvc.stdout)
    assert mvc_data["errors"] == 0
    assert mvc_data["files_scanned"] > 0
    checks.append("mvc_check full-project JSON run has zero errors")

    scaffolder = _run(
        [
            "uv",
            "run",
            "scripts/omt/new_feature.py",
            "harness e2e canary",
            "--type",
            "minor_feature",
            "--dry-run",
        ]
    )
    assert scaffolder.returncode == 0, scaffolder.stdout + scaffolder.stderr
    assert "[dry-run] would create" in scaffolder.stdout
    assert "FEATURE.md" in scaffolder.stdout
    assert "plan/PLAN.md" in scaffolder.stdout
    checks.append("new_feature scaffolder dry-run succeeds")

    # 7. TDD enforcement tools are wired in the enforcer (feature_016).
    assert "const omt_testlist" in enforcer
    assert "const omt_red" in enforcer
    assert "const omt_green" in enforcer
    assert "const omt_refactor" in enforcer
    assert "const omt_done" in enforcer
    assert "tdd_check.py" in enforcer
    assert "tdd_mode" in enforcer
    assert "refactorSnapshots" in enforcer
    assert "revert_needed" in enforcer
    checks.append("TDD tools and gate are wired in omt_enforcer")

    # 8. tdd_check.py runs successfully through uv.
    tdd = _run(["uv", "run", "scripts/omt/tdd_check.py", "status", "--session", ""])
    assert tdd.returncode == 0, tdd.stdout + tdd.stderr
    tdd_data = json.loads(tdd.stdout)
    assert "tdd_mode" in tdd_data
    assert "state" in tdd_data
    checks.append("tdd_check.py status subcommand returns valid JSON")

    # 9. feature_021 think-anywhere: standalone plugin + think-gate in enforcer.
    think = _read(".opencode/plugins/omt_think.ts")
    assert "export default async () => ({" in think
    assert "tool: { omt_think, omt_think_list, omt_think_remove, omt_think_verify, omt_think_suggest, omt_think_reindex }" in think
    assert "commentSyntaxFor" in think
    assert "thinkGateDecision" in enforcer
    assert "hasConsultedThoughts" in enforcer
    assert "think_consult" in enforcer
    assert '"omt_think": "allow"' in config
    assert '"omt_think_list": "allow"' in config
    assert '"omt_think_remove": "allow"' in config
    assert '"omt_think_verify": "allow"' in config
    assert '"omt_think_suggest": "allow"' in config
    assert '"omt_think_reindex": "allow"' in config
    assert "Think Anywhere" in _read("AGENTS.md")
    assert "SECTION:THINK" in _read(".meta/META_HARNESS.md")
    checks.append("feature_021 think-anywhere plugin + think-gate + docs wired")

    _write_receipt(checks)
    assert RECEIPT_PATH.exists()