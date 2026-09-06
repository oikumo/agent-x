#!/usr/bin/env python3
"""Unit tests for tdd_check.py — TDD enforcement engine.

Tests cover AST functions, gate logic, ledger interaction, and the
subcommand JSON interface. Uses temp files + temp ledger to avoid
polluting the real project state.

Run with: uv run pytest tests/scripts/omt/test_tdd_check.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts/omt to path for importing tdd_check
SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))

import tdd_check
from tdd import state as tdd_state
from tdd.cli import _parse_behaviors


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_test_file(tmp_path):
    """Create a temporary test file with imports from agentx."""
    f = tmp_path / "test_foo.py"
    f.write_text(
        "from agentx.model.session.session import Session\n"
        "from agentx.model.session.session_db import DP_Session\n"
        "\n"
        "def test_session_create():\n"
        "    session = Session()\n"
        "    assert session.create() is True\n"
        "    assert session.oid is not None\n"
        "\n"
        "def test_session_load():\n"
        "    session = Session()\n"
        "    assert session.load(1) is not None\n",
        encoding="utf-8",
    )
    return f


@pytest.fixture
def tmp_src_file(tmp_path):
    """Create a temporary source file with a class and methods."""
    f = tmp_path / "session.py"
    f.write_text(
        "class Session:\n"
        "    def __init__(self):\n"
        "        self.oid = None\n"
        "\n"
        "    def create(self) -> bool:\n"
        "        self.oid = 1\n"
        "        return True\n"
        "\n"
        "    def load(self, oid: int):\n"
        "        return self\n"
        "\n"
        "    def _private(self):\n"
        "        pass\n"
        "\n"
        "def public_func():\n"
        "    pass\n"
        "\n"
        "def _private_func():\n"
        "    pass\n",
        encoding="utf-8",
    )
    return f


# ---------------------------------------------------------------------------
# AST function tests
# ---------------------------------------------------------------------------

class TestInferTargetSrc:
    def test_infers_agentx_imports(self, tmp_test_file):
        targets = tdd_check.infer_target_src(tmp_test_file)
        assert "src/agentx/model/session/session.py" in targets
        assert "src/agentx/model/session/session_db.py" in targets

    def test_ignores_non_agentx_imports(self, tmp_path):
        f = tmp_path / "test_other.py"
        f.write_text(
            "import os\n"
            "from pathlib import Path\n"
            "import pytest\n"
            "\n"
            "def test_something():\n"
            "    assert True\n",
            encoding="utf-8",
        )
        assert tdd_check.infer_target_src(f) == []

    def test_handles_invalid_file(self):
        assert tdd_check.infer_target_src(Path("/nonexistent/file.py")) == []


class TestExtractTestReferences:
    def test_extracts_method_calls(self, tmp_test_file):
        refs = tdd_check.extract_test_references(tmp_test_file, "test_session_create")
        assert "create" in refs  # session.create() is a method call
        # Note: session.oid is a bare attribute access, not a method call —
        # extract_test_references only collects ast.Call with ast.Attribute func

    def test_returns_empty_for_missing_test(self, tmp_test_file):
        refs = tdd_check.extract_test_references(tmp_test_file, "nonexistent_test")
        assert refs == set()

    def test_handles_invalid_file(self):
        assert tdd_check.extract_test_references(Path("/nonexistent"), "test_x") == set()


class TestExtractDefinedNames:
    def test_extracts_class_and_public_methods(self, tmp_src_file):
        names = tdd_check.extract_defined_names(tmp_src_file)
        assert "Session" in names
        assert "create" in names
        assert "load" in names
        assert "public_func" in names
        # Private should be excluded
        assert "_private" not in names
        assert "_private_func" not in names

    def test_handles_invalid_file(self):
        assert tdd_check.extract_defined_names(Path("/nonexistent")) == set()


class TestExtractPublicMethods:
    def test_extracts_methods_with_class_and_line(self, tmp_src_file):
        methods = tdd_check.extract_public_methods(tmp_src_file)
        assert len(methods) == 3  # create, load, public_func
        class_methods = [m for m in methods if m["class"] == "Session"]
        assert len(class_methods) == 2
        assert {"create", "load"} == {m["method"] for m in class_methods}
        # Check line numbers are present
        assert all("line" in m for m in methods)

    def test_excludes_private_methods(self, tmp_src_file):
        methods = tdd_check.extract_public_methods(tmp_src_file)
        method_names = [m["method"] for m in methods]
        assert "_private" not in method_names


class TestFindUntestedMethods:
    def test_finds_untested(self, tmp_src_file, tmp_test_file):
        # tmp_test_file references create and load, but not public_func
        untested = tdd_check.find_untested_methods(tmp_src_file, [tmp_test_file])
        method_names = [m["method"] for m in untested]
        assert "public_func" in method_names
        assert "create" not in method_names
        assert "load" not in method_names


class TestVerifyTrueRed:
    def test_true_red_when_method_missing(self, tmp_test_file, tmp_src_file):
        # test references create and load, both exist in src → not true red
        result = tdd_check.verify_true_red(tmp_test_file, "test_session_create", [tmp_src_file])
        assert result["is_true_red"] is False
        # But "oid" is an attribute, not a method name — it might be "missing"
        # since it's not a defined name (it's an instance attribute)

    def test_true_red_when_source_empty(self, tmp_test_file, tmp_path):
        empty_src = tmp_path / "empty.py"
        empty_src.write_text("# empty\n", encoding="utf-8")
        result = tdd_check.verify_true_red(tmp_test_file, "test_session_create", [empty_src])
        assert result["is_true_red"] is True
        assert "create" in result["missing"]


class TestDetectRedAntiPatterns:
    def test_single_test_no_warnings(self, tmp_path):
        f = tmp_path / "test_ok.py"
        f.write_text(
            "def test_session_create_returns_true():\n"
            "    assert True\n",
            encoding="utf-8",
        )
        warnings = tdd_check.detect_red_anti_patterns(f)
        assert len(warnings) == 0

    def test_batch_n_tests_warning(self, tmp_path):
        f = tmp_path / "test_batch.py"
        f.write_text(
            "def test_a():\n    assert True\n"
            "def test_b():\n    assert True\n"
            "def test_c():\n    assert True\n",
            encoding="utf-8",
        )
        warnings = tdd_check.detect_red_anti_patterns(f)
        assert any("batch-N-tests" in w for w in warnings)

    def test_no_assertions_warning(self, tmp_path):
        f = tmp_path / "test_no_assert.py"
        f.write_text(
            "def test_something():\n"
            "    x = 1 + 1\n",
            encoding="utf-8",
        )
        warnings = tdd_check.detect_red_anti_patterns(f)
        assert any("no assertions" in w for w in warnings)

    def test_bad_naming_warning(self, tmp_path):
        f = tmp_path / "test_bad_name.py"
        f.write_text(
            "def test_foo():\n"
            "    assert True\n",
            encoding="utf-8",
        )
        warnings = tdd_check.detect_red_anti_patterns(f)
        assert any("naming" in w for w in warnings)

    def test_skip_xfail_warning(self, tmp_path):
        f = tmp_path / "test_skip.py"
        f.write_text(
            "import pytest\n"
            "@pytest.mark.skip\n"
            "def test_session_create_behavior():\n"
            "    assert True\n",
            encoding="utf-8",
        )
        warnings = tdd_check.detect_red_anti_patterns(f)
        assert any("skip" in w for w in warnings)


class TestSnapshotDiff:
    def test_diff_finds_new_methods(self):
        before = {"methods": [{"class": "Foo", "method": "bar", "line": 1, "is_abstract": False}]}
        after = {"methods": [
            {"class": "Foo", "method": "bar", "line": 1, "is_abstract": False},
            {"class": "Foo", "method": "baz", "line": 5, "is_abstract": False},
        ]}
        new = tdd_check.diff_snapshots(before, after)
        assert len(new) == 1
        assert new[0]["method"] == "baz"

    def test_diff_empty_before(self):
        after = {"methods": [{"class": "Foo", "method": "bar", "line": 1, "is_abstract": False}]}
        new = tdd_check.diff_snapshots(None, after)
        assert len(new) == 1


# ---------------------------------------------------------------------------
# Gate logic tests
# ---------------------------------------------------------------------------

class TestGateRules:
    """Test the HAT_RULES lookup table directly."""

    def test_testlist_blocks_all(self):
        rules = tdd_check.HAT_RULES["testlist"]
        assert rules["src"] is False
        assert rules["tests"] is False

    def test_red_allows_tests_only(self):
        rules = tdd_check.HAT_RULES["red"]
        assert rules["src"] is False
        assert rules["tests"] is True

    def test_green_allows_src_only(self):
        rules = tdd_check.HAT_RULES["green"]
        assert rules["src"] is True
        assert rules["tests"] is False

    def test_refactor_allows_src_only(self):
        rules = tdd_check.HAT_RULES["refactor"]
        assert rules["src"] is True
        assert rules["tests"] is False

    def test_done_blocks_all(self):
        rules = tdd_check.HAT_RULES["done"]
        assert rules["src"] is False
        assert rules["tests"] is False

    def test_none_allows_all(self):
        rules = tdd_check.HAT_RULES["none"]
        assert rules["src"] is True
        assert rules["tests"] is True


class TestHatFallbackIrSyncPin:
    """improvement007 R5/OPT-E: gates.py derives HAT_RULES/HAT_REVERT_ON from
    ir.hats at module load (.omt @hat = single source); the _FALLBACK_*
    literals keep the engine alive on a pre-build checkout and must equal the
    IR-derived values — drift silently mis-hats edits (F9/BUG-B defect class;
    mirror of the R4 TS FALLBACK_* pins in test_omt_enforcer_guard_source_pins)."""

    @staticmethod
    def _ir_hats() -> dict:
        ir_path = SCRIPTS_DIR.parent.parent / ".meta" / ".omt" / "harness.ir.json"
        return json.loads(ir_path.read_text(encoding="utf-8"))["hats"]

    def test_fallback_hat_rules_match_ir(self):
        from tdd import gates
        expected = {
            rid.split(".", 1)[-1]: {
                "src": hat["allow"] == "src/",
                "tests": hat["allow"] == "tests/",
            }
            for rid, hat in self._ir_hats().items()
        }
        expected["none"] = {"src": True, "tests": True}  # engine-local, not in IR
        assert gates._FALLBACK_HAT_RULES == expected, (
            "gates._FALLBACK_HAT_RULES drifted from ir.hats (source: .omt @hat "
            "records) — edit the .omt, run harnessc.py build, and update the "
            "fallback in the same commit")

    def test_fallback_hat_revert_on_matches_ir(self):
        from tdd import gates
        expected = {rid.split(".", 1)[-1]: hat["revert_on"]
                    for rid, hat in self._ir_hats().items()}
        assert gates._FALLBACK_HAT_REVERT_ON == expected, (
            "gates._FALLBACK_HAT_REVERT_ON drifted from ir.hats revert_on "
            "(source: .omt @hat records) — edit the .omt, run harnessc.py "
            "build, and update the fallback in the same commit")

    def test_effective_hats_derived_from_ir(self):
        """IR present in this repo ⇒ the module-level values ARE the IR-derived
        ones (the derive path, not the fallback, is the live one)."""
        from tdd import gates
        assert gates._IR_HATS, "IR missing — derive path untested"
        assert gates.HAT_RULES == gates._derive_hat_rules(gates._IR_HATS)
        assert gates.HAT_REVERT_ON == {
            rid.split(".", 1)[-1]: h.get("revert_on", "")
            for rid, h in gates._IR_HATS.items()}

    def test_after_edit_revert_branch_is_revert_on_driven(self, monkeypatch):
        """The refactor auto-revert branch is selected via HAT_REVERT_ON
        (ir.hats tdd.refactor revert_on="tests_break"), not a hardcoded state."""
        from tdd import gates

        class _Args:
            session = "s"
            path = "src/x.py"

        monkeypatch.setattr(gates, "get_tdd_state", lambda _s: "refactor")
        monkeypatch.setattr(gates, "HAT_REVERT_ON", {"refactor": ""})
        assert gates.cmd_after_edit(_Args())["action"] == "ok"
        monkeypatch.setattr(gates, "HAT_REVERT_ON", {"refactor": "tests_break"})
        monkeypatch.setattr(gates, "get_current_test_node", lambda _s: "t.py::t")
        monkeypatch.setattr(gates, "run_test",
                            lambda _n, timeout=30: (1, "", "boom"))
        assert gates.cmd_after_edit(_Args())["action"] == "revert_needed"


class TestParseBehaviors:
    """feature_037: _parse_behaviors prose fallback for omt_tdd testlist
    (GOTCHA_TESTLIST_JSON) — JSON array/string/bullets/numbered prose.
    Covers the idea-doc Before/After table (.sandbox/meta_harness_3_idea.md)."""

    @pytest.mark.parametrize("raw,expected", [
        ('["Write a test", "Fix bug"]', ["Write a test", "Fix bug"]),  # JSON array (canonical, unchanged)
        ("Write a test", ["Write a test"]),                            # bare prose
        ("- Write a test\n- Fix bug", ["Write a test", "Fix bug"]),    # hyphen bullets
        ("• Task 1\n• Task 2", ["Task 1", "Task 2"]),                  # bullet chars
        ("1. Write a test\n2. Fix bug", ["Write a test", "Fix bug"]),  # numbered list
        ('"Write a test"', ["Write a test"]),                          # JSON string (no quotes kept)
        ("123", ["123"]),                                              # JSON scalar falls to prose
        ("", []),                                                      # empty/omitted
        ("[]", []),                                                    # empty array (argparse default)
        ("- \n1. ", []),                                               # empty marker lines skipped
    ])
    def test_parse_behaviors_table(self, raw, expected):
        assert _parse_behaviors(raw) == expected


class TestRunTestDispatch:
    """feature_038 (toolchain-aware TDD): run_test dispatches on test-file
    suffix — `.py` -> pytest (unchanged), `.ts/.tsx` -> vitest from the
    project root. Verifies the command + subprocess cwd via a mocked
    subprocess.run; keeps prior behavior for unknown suffixes.

    Uses a temp REPO_ROOT so _resolve_test_path maps relative nodes under
    tmp_path, letting us create real .ts/.tsx test files that pass
    test_path.exists() and real package.json markers for root discovery."""

    @pytest.fixture
    def fake_repo(self, tmp_path, monkeypatch):
        # Redirect the module-level constants used by state.py resolution so
        # temp files under tmp_path behave like real repo files.
        monkeypatch.setattr(tdd_state, "REPO_ROOT", tmp_path)
        calls = {}

        def fake_run(cmd, capture_output=None, text=None, timeout=None, cwd=None):
            calls["cmd"] = cmd
            calls["cwd"] = cwd
            return _FakeResult(0, "", "")
        monkeypatch.setattr(tdd_state.subprocess, "run", fake_run)
        return tmp_path, calls

    def test_py_suffix_runs_pytest(self, fake_repo):
        tmp_path, calls = fake_repo
        f = tmp_path / "test_foo.py"
        f.write_text("def test_x(): pass\n", encoding="utf-8")
        code, _o, _e = tdd_state.run_test("test_foo.py", timeout=30)
        assert code == 0
        assert calls["cmd"][0:3] == [sys.executable, "-m", "pytest"]
        assert "test_foo.py" in str(calls["cmd"][3:])

    def test_ts_suffix_runs_vitest_from_project_root(self, fake_repo):
        tmp_path, calls = fake_repo
        proj = tmp_path / "tools" / "studio" / "tests" / "engine"
        proj.mkdir(parents=True)
        (tmp_path / "tools" / "studio" / "package.json").write_text(
            json.dumps({"name": "studio", "devDependencies": {"vitest": "^2.0.0"}}),
            encoding="utf-8")
        (proj / "analysis.test.ts").write_text(
            'import { it } from "vitest"; it("x", () => {});\n', encoding="utf-8")
        # relative node under REPO_ROOT (tmp_path)
        code, _o, _e = tdd_state.run_test(
            "tools/studio/tests/engine/analysis.test.ts", timeout=30)
        assert code == 0
        assert calls["cmd"][0:2] == ["npx", "vitest"]
        # cwd must be the project root, NOT the test file's dir (the OPEN ITEM)
        assert calls["cwd"] == str(tmp_path / "tools" / "studio")

    def test_tsx_suffix_runs_vitest(self, fake_repo):
        tmp_path, calls = fake_repo
        proj = tmp_path / "tools" / "ui"
        proj.mkdir(parents=True)
        (proj / "package.json").write_text(
            json.dumps({"name": "ui", "devDependencies": {"vitest": "^2.0.0"}}),
            encoding="utf-8")
        (proj / "tests").mkdir(exist_ok=True)
        (proj / "tests" / "widget.test.tsx").write_text("export {};\n", encoding="utf-8")
        code, _o, _e = tdd_state.run_test("tools/ui/tests/widget.test.tsx", timeout=30)
        assert code == 0
        assert calls["cmd"][0:2] == ["npx", "vitest"]
        assert "widget.test.tsx" in str(calls["cmd"])
        assert calls["cwd"] == str(proj)

    def test_unknown_suffix_falls_back_to_pytest(self, fake_repo):
        tmp_path, calls = fake_repo
        f = tmp_path / "run.js"
        f.write_text(";", encoding="utf-8")
        code, _o, _e = tdd_state.run_test("run.js", timeout=30)
        assert code == 0
        assert calls["cmd"][0:3] == [sys.executable, "-m", "pytest"]

    def test_find_vitest_root_skips_non_vitest_pkg(self, fake_repo):
        tmp_path, _calls = fake_repo
        proj = tmp_path / "tools" / "nonvitest"
        proj.mkdir(parents=True)
        # package.json WITHOUT a vitest dep -> NOT the root
        (proj / "package.json").write_text(
            json.dumps({"name": "plain", "dependencies": {"react": "^18.0.0"}}),
            encoding="utf-8")
        # a parent WITH vitest -> that becomes the root
        (tmp_path / "package.json").write_text(
            json.dumps({"name": "root", "devDependencies": {"vitest": "^2.0.0"}}),
            encoding="utf-8")
        test_file = proj / "tests" / "x.test.ts"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("export {};\n", encoding="utf-8")
        root = tdd_state._find_vitest_root(test_file)
        # nearest ancestor with a vitest dep is REPO_ROOT (tmp_path)
        assert root == tmp_path

    def test_find_vitest_root_falls_back_to_parent(self, fake_repo):
        tmp_path, _calls = fake_repo
        # no package.json / vitest marker anywhere up to REPO_ROOT
        f = tmp_path / "tests" / "x.test.ts"
        f.parent.mkdir(parents=True)
        f.write_text("export {};\n", encoding="utf-8")
        assert tdd_state._find_vitest_root(f) == f.parent


class _FakeResult:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# ---------------------------------------------------------------------------
# Integration test: tdd_check.py as subprocess
# ---------------------------------------------------------------------------

class TestTddCheckSubprocess:
    """Run tdd_check.py as a subprocess and verify JSON output.

    feature_051 (A1 — ledger test isolation): subprocesses run against a
    fresh TMP ledger (OMT_LEDGER_PATH / OMT_SNAPSHOT_DIR) so verdicts never
    depend on live-session ledger state (the historical window-flaky root —
    the real ledger + the 8h window made gate output flip with whatever TDD
    session happened to be active)."""

    @staticmethod
    def _hermetic_env(tmp_path) -> dict:
        import os
        return {
            **os.environ,
            "OMT_LEDGER_PATH": str(tmp_path / "ledger.jsonl"),
            "OMT_SNAPSHOT_DIR": str(tmp_path / "tdd_snapshots"),
        }

    def test_status_returns_valid_json(self, tmp_path):
        import subprocess
        result = subprocess.run(
            ["uv", "run", "scripts/omt/tdd_check.py", "status", "--session", ""],
            capture_output=True, text=True, timeout=10,
            cwd=str(SCRIPTS_DIR.parent.parent), env=self._hermetic_env(tmp_path),
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "tdd_mode" in data
        assert "state" in data

    def test_gate_returns_allowed_when_no_tdd(self, tmp_path):
        import subprocess
        result = subprocess.run(
            ["uv", "run", "scripts/omt/tdd_check.py", "gate", "--path", "src/foo.py", "--session", ""],
            capture_output=True, text=True, timeout=10,
            cwd=str(SCRIPTS_DIR.parent.parent), env=self._hermetic_env(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # tdd_check.py gate enforces ONLY the TDD two-hats rule (red/test-only,
        # green/src-only, refactor/src-only, done/blocked, none/allow-both).
        # It does NOT enforce the g.kb KB-consult gate — that lives in the TS
        # gate_driver.ts (order=55, runBeforeGates), wired via kbTrack
        # (nav_gate.ts) + SESSION_FLAGS[kb_consulted]. The python gate's job is
        # only two-hats; the consult enforcement is the opencode plugin's job.
        # feature_051: the tmp ledger is empty by construction → tdd_mode is
        # deterministically False → allowed deterministically True (previously
        # this depended on no live TDD session being in the real 8h window).
        assert "allowed" in data
        assert "tdd_mode" in data
        assert data["allowed"] is True
        assert data["tdd_mode"] is False
        assert data["state"] in ("none", "red", "green", "refactor", "testlist", "done")

    def test_validate_exit_returns_ok_for_unknown_feature(self, tmp_path):
        import subprocess
        result = subprocess.run(
            ["uv", "run", "scripts/omt/tdd_check.py", "validate-exit", "--feature", "feature_999.nonexistent"],
            capture_output=True, text=True, timeout=10,
            cwd=str(SCRIPTS_DIR.parent.parent), env=self._hermetic_env(tmp_path),
        )
        data = json.loads(result.stdout)
        assert data["ok"] is True  # No test files = no gaps = ok


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
