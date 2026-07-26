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
    ".opencode/plugins/omt_nav.ts",
    ".opencode/lib/omt_shared.ts",
    ".opencode/lib/enforcer/session_state.ts",
    ".opencode/lib/enforcer/nav_gate.ts",
    ".opencode/lib/enforcer/receipt_guard.ts",
    ".opencode/lib/enforcer/phase_gate.ts",
    ".opencode/lib/enforcer/tdd_hats.ts",
    ".opencode/lib/enforcer/think_gate.ts",
    ".opencode/lib/enforcer/mvc_after.ts",
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
    assert "export default async ({" in status
    assert "initOmtShared(" in status  # R1: ctx root (worktree ?? directory) injected
    assert "tool: { omt_status }" in status
    assert "p.split" not in status
    assert "dynamic" not in status.lower()
    assert "omt_status is registered by .opencode/plugins/omt_status.ts" in enforcer
    checks.append("standalone omt_status plugin has no dynamic p.split path")

    # 2. Phase declarations and completions are real opencode tools, scoped to
    # feature phases, with lightweight task types excluded from major-feature
    # artifact over-enforcement. R2: the tools live in lib/enforcer/phase_gate.ts;
    # the composition root wires them via createPhaseTools.
    phase_gate = _read(".opencode/lib/enforcer/phase_gate.ts")
    assert "const omt_phase = tool" in phase_gate
    assert "const omt_skip = tool" in phase_gate
    assert "const omt_complete = tool" in phase_gate
    assert "getActiveFeaturePhase(feature, session)" in phase_gate
    assert 'ARTIFACT_REQUIRED.has(phaseRecord.task_type || "")' in phase_gate
    assert "checkPhaseExitArtifacts(directory, feature, currentPhase)" in phase_gate
    assert "createPhaseTools" in enforcer
    checks.append("omt_phase/omt_complete tool chain is wired and scoped")

    # 3. The harness now enforces this e2e test for repeated edits to the OMT
    # enforcement surface. R1: the receipt-guard machinery (constants +
    # isOmtHarness + omtHarnessE2eStatus) lives in the shared lib; R2: the
    # before-hook call site lives in lib/enforcer/receipt_guard.ts.
    shared = _read(".opencode/lib/omt_shared.ts")
    assert "OMT_HARNESS_E2E_COMMAND" in shared
    assert E2E_COMMAND in shared
    assert "omtHarnessE2eStatus" in shared
    assert "OMT_HARNESS_E2E_RECEIPT" in shared
    assert ".meta/software_development_process/omt_agent_guide.md" in shared
    receipt_guard = _read(".opencode/lib/enforcer/receipt_guard.ts")
    assert "omtHarnessE2eStatus" in receipt_guard  # R2: before-hook call site
    checks.append("OMT harness edit guard requires this e2e receipt (shared lib + receipt_guard call site)")

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
    # R2: the §12 artifact matrix lives in lib/enforcer/phase_gate.ts.
    assert "Essential vs. Optional" in guide
    assert "Bug Fix" in guide and "Minor Feature" in guide and "Major Feature" in guide
    assert 'ARTIFACT_REQUIRED = new Set(["major_feature", "new_screen"])' in phase_gate
    assert "PHASE_EXIT_REQUIREMENTS" in phase_gate
    assert "operation_spec_*.md" in phase_gate
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

    # 7. TDD enforcement tools are wired (feature_016). R2: the two-hats gate
    # and tools live in lib/enforcer/tdd_hats.ts; snapshots in session_state.ts.
    tdd_hats = _read(".opencode/lib/enforcer/tdd_hats.ts")
    session_state = _read(".opencode/lib/enforcer/session_state.ts")
    assert "const omt_testlist" in tdd_hats
    assert "const omt_red" in tdd_hats
    assert "const omt_green" in tdd_hats
    assert "const omt_refactor" in tdd_hats
    assert "const omt_done" in tdd_hats
    assert "tdd_check.py" in tdd_hats
    assert "tdd_mode" in tdd_hats
    assert "refactorSnapshots" in session_state
    assert "revert_needed" in tdd_hats
    checks.append("TDD tools and gate are wired in tdd_hats/session_state")

    # 8. tdd_check.py runs successfully through uv.
    tdd = _run(["uv", "run", "scripts/omt/tdd_check.py", "status", "--session", ""])
    assert tdd.returncode == 0, tdd.stdout + tdd.stderr
    tdd_data = json.loads(tdd.stdout)
    assert "tdd_mode" in tdd_data
    assert "state" in tdd_data
    checks.append("tdd_check.py status subcommand returns valid JSON")

    # 9. feature_021 think-anywhere: standalone plugin + think-gate (R2: the
    # gate lives in lib/enforcer/think_gate.ts; the plugin is tools-only).
    think = _read(".opencode/plugins/omt_think.ts")
    assert "export default async ({" in think
    assert "initOmtShared(" in think  # R1: ctx root injected
    assert "tool: { omt_think, omt_think_list, omt_think_remove, omt_think_verify, omt_think_suggest }" in think
    assert "commentSyntaxFor" in think
    # meta_harness_dsl R6 S1: reindex tool deleted (append-only index, grep-is-truth).
    assert "const omt_think_reindex" not in think
    think_gate = _read(".opencode/lib/enforcer/think_gate.ts")
    assert "thinkGateDecision" in think_gate
    assert "hasConsultedThoughts" in think_gate
    assert "think_consult" in think_gate
    assert '"omt_think": "allow"' in config
    assert '"omt_think_list": "allow"' in config
    assert '"omt_think_remove": "allow"' in config
    assert '"omt_think_verify": "allow"' in config
    assert '"omt_think_suggest": "allow"' in config
    assert '"omt_think_reindex": "allow"' not in config
    assert "Think Anywhere" in _read("AGENTS.md")
    assert "SECTION:THINK" in _read(".meta/META_HARNESS.md")
    checks.append("feature_021 think-anywhere plugin + think-gate + docs wired")

    # 10. meta_harness_dsl R1: all four plugins import the shared lib (single
    # source for THOUGHT_PATTERN, UNLOCK_WINDOW_MS, state paths, JSONL IO,
    # repo-root and the e2e-receipt guard), initialize it with the plugin-ctx
    # root (worktree ?? directory, F2/F17), and no longer resolve repo paths
    # from the process cwd.
    nav = _read(".opencode/plugins/omt_nav.ts")
    for name, src in (("omt_enforcer.ts", enforcer), ("omt_status.ts", status),
                      ("omt_think.ts", think), ("omt_nav.ts", nav)):
        assert 'from "../lib/omt_shared"' in src, (
            f"{name} must import the shared lib (R1 single source)")
        assert "initOmtShared(" in src, (
            f"{name} must init the shared lib with the ctx root (worktree ?? directory)")
        assert "process.cwd()" not in src, (
            f"{name} must not resolve repo paths from the process cwd (R1 F2/F17)")
    checks.append("meta_harness_dsl R1: shared lib imported + initialized by all four plugins")

    # 11. meta_harness_dsl R2: the enforcer is a THIN COMPOSITION ROOT (single
    # default export per Appendix B2 — hook registration + dispatch only); all
    # gate logic lives in lib/enforcer/* modules, which are themselves covered
    # by the receipt guard. R6 S6: the session bootstrap (nav tip + compact TA
    # digest) has ONE emission site in the enforcer after-hook; the think
    # plugin's Tier-1c hook is deleted and the digest builder is shared-lib.
    assert "export default async ({" in enforcer
    assert "\nexport function" not in enforcer
    assert "\nexport const" not in enforcer
    for mod in ("session_state", "nav_gate", "receipt_guard", "phase_gate",
                "tdd_hats", "think_gate", "mvc_after"):
        assert f'from "../lib/enforcer/{mod}"' in enforcer, (
            f"composition root must import lib/enforcer/{mod} (R2 split)")
    assert ".opencode/lib/enforcer/" in shared, (
        "isOmtHarness must cover lib/enforcer/ (R2 modules are the "
        "enforcement surface — an unguarded enforcer is a BUG-B-class hole)")
    assert "sessionBootstrap" in enforcer
    assert "thinkDigest" in shared
    assert "digestSessions" not in think  # R2 S6: Tier-1c hook deleted
    assert '"tool.execute.after"' not in think  # tools-only plugin now
    checks.append("meta_harness_dsl R2: composition root + guarded lib/enforcer modules + S6 single bootstrap")

    _write_receipt(checks)
    assert RECEIPT_PATH.exists()
