"""Wave 5/D2 stack profiles RED — feature_059.

Contract (GREEN pins per design_001 §4 + operation_spec_001):
- mvc_check --profile none: exit 0, scans nothing, disabled banner.
- mvc_check --profile mvc_ts: text/regex scan of **/*.{ts,tsx} flagging
  view-creates-controller (new XController(), TS spelling).
- mvc_check default (mvc_py): current Python behavior byte-identical.
- @var stack_profile respected as the default when CWD is inside a repo.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
MVC = REPO_ROOT / "scripts" / "omt" / "mvc_check.py"


def _run(*args: str, cwd: Path | None = None):
    return subprocess.run(
        [sys.executable, str(MVC), *args],
        capture_output=True, text=True, cwd=str(cwd or REPO_ROOT))


def test_profile_none_disables(tmp_path):
    victim = tmp_path / "bad_view.py"
    victim.write_text("from agentx.model.foo import Bar\n", encoding="utf-8")
    p = _run("--profile", "none", str(victim))
    assert p.returncode == 0
    assert "profile=none" in p.stdout


def test_profile_mvc_ts_flags_view_creates_controller(tmp_path):
    view = tmp_path / "home_view.tsx"
    view.write_text(
        "import { FooController } from './foo';\n"
        "const c = new FooController();\n", encoding="utf-8")
    p = _run("--profile", "mvc_ts", str(tmp_path))
    assert p.returncode == 1
    assert "VIEW_CREATES_CONTROLLER" in p.stdout


def test_profile_mvc_py_unchanged(tmp_path):
    bad = tmp_path / "home_view.py"
    bad.write_text("from agentx.model.store import Store\n", encoding="utf-8")
    p = _run("--profile", "mvc_py", str(bad))
    assert p.returncode == 1
    assert "VIEW_IMPORTS_MODEL" in p.stdout
    ok = tmp_path / "clean.py"
    ok.write_text("x = 1\n", encoding="utf-8")
    assert _run(str(ok)).returncode == 0
