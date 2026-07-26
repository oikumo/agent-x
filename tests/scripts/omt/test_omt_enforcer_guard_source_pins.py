"""
Harness-level STATIC guard pins for omt_enforcer.ts (feature_023 deep audit).

These tests exist because of two LIVE-CONFIRMED dead-guard defects (2026-07-19,
proven by driving the real opencode 1.18.3 binary — the live suite has since
been reduced to the minimal smoke in test_omt_live_opencode_guards.py; these
static pins are now the standing guard coverage, with the real-binary probe
recipes preserved in the WORK.md scratchpad):

  BUG-A (before-hook contract violation, F14 mirrored):
    commit a3ffb81 ("feature_023") changed the before-hook edit chain from the
    CORRECT `output?.args?.filePath` to `input?.args?.filePath` with a false
    "F14 fix" comment. The installed SDK d.ts pins the contract:
        tool.execute.before: input={tool,sessionID,callID}  (NO args)
                             output={args}
        tool.execute.after:  input={…,args}  output={title,output,metadata}
    So in the REAL runtime `raw` was always undefined in the before-hook and
    `if (!raw) return` silently bypassed EVERY edit guard: isProtected
    (.env/README.md/uv.lock/LICENSE), the OMT-harness e2e receipt gate, the
    tests/ canary, the src/ phase gate, and the TDD two-hats gate. Live proof:
    a real `opencode run` edit of README.md landed with no phase/skip declared.

  BUG-B (path drift, directory renamed but prefix not):
    the same commit renamed .opencode/plugin/ → .opencode/plugins/ but left
    isOmtHarness checking rel.startsWith(".opencode/plugin/omt_") — which never
    matches ".opencode/plugins/omt_*" ("/" vs "s" at position 16). The e2e
    receipt guard for the four plugin files was dead code.

Both defects are F14-class: a guard silently dead while every runner-based
test stayed green (fixtures fabricated shapes/paths that matched the buggy
code). These pins assert the PLUGIN SOURCE itself, so a regression fails here
even if every behavior test is skipped.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
ENFORCER = REPO_ROOT / ".opencode" / "plugins" / "omt_enforcer.ts"
SHARED_LIB = REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts"
E2E_TEST = REPO_ROOT / "tests" / "scripts" / "omt" / "test_omt_harness_e2e.py"


def _hook_body(source: str, hook: str) -> str:
    """Slice one registered-hook body out of the plugin's returned object:
    from the `"<hook>":` key to the next top-level `"…":` hook key or the
    closing of the returned literal. Good enough for a source pin."""
    start = source.index(f'"{hook}"')
    # next registered key after this one (hook keys are quoted, end with ':')
    m = re.search(r'\n\s{4}"[a-z._]+":\s*async', source[start + 1:])
    end = start + 1 + m.start() if m else len(source)
    return source[start:end]


class TestBeforeHookContractPin:
    """BUG-A pin: the before-hook EDIT path must read args from `output`
    (SDK contract: before input has NO args; after input HAS args)."""

    def test_before_hook_edit_path_reads_output_args(self):
        body = _hook_body(ENFORCER.read_text(encoding="utf-8"), "tool.execute.before")
        assert "output?.args?.filePath" in body, (
            "before-hook edit path must read output?.args?.filePath "
            "(before-hook contract: args on output, not input)")

    def test_before_hook_edit_path_never_reads_input_args_for_filepath(self):
        body = _hook_body(ENFORCER.read_text(encoding="utf-8"), "tool.execute.before")
        assert "input?.args?.filePath" not in body, (
            "BUG-A: before-hook input carries NO args per SDK d.ts — reading "
            "input?.args?.filePath makes every edit guard dead (F14 mirrored)")

    def test_after_hook_edit_path_reads_input_args(self):
        body = _hook_body(ENFORCER.read_text(encoding="utf-8"), "tool.execute.after")
        assert "input?.args?.filePath" in body, (
            "after-hook edit path must read input?.args?.filePath "
            "(after-hook contract: args on input — the genuine F14 fix)")

    def test_no_false_f14_comment_in_before_hook(self):
        body = _hook_body(ENFORCER.read_text(encoding="utf-8"), "tool.execute.before")
        assert "args live on input in tool.execute.before" not in body, (
            "false contract comment (a3ffb81): before-hook args live on OUTPUT")


class TestHarnessPathCoveragePin:
    """BUG-B pin: isOmtHarness must classify the REAL plugin paths.

    meta_harness_dsl R1: isOmtHarness moved to the shared lib
    (.opencode/lib/omt_shared.ts); these pins read the lib source. The lib
    itself is receipt-guarded via the .opencode/lib/omt_ prefix (R1 added it —
    the guard must cover the file the guard now lives in)."""

    @staticmethod
    def _is_omt_harness(rel: str) -> bool:
        """Python port of the shared lib's isOmtHarness (keep in sync — the
        pin feeds REAL paths through the SAME literals found in the source)."""
        src = SHARED_LIB.read_text(encoding="utf-8")
        body = src[src.index("export function isOmtHarness"):src.index("export function receiptTimestampMs")]
        exacts = set(re.findall(r'rel === "([^"]+)"', body))
        prefixes = re.findall(r'rel\.startsWith\("([^"]+)"\)', body)
        return rel in exacts or any(rel.startswith(p) for p in prefixes)

    @pytest.mark.parametrize("rel", [
        ".opencode/plugins/omt_enforcer.ts",
        ".opencode/plugins/omt_nav.ts",
        ".opencode/plugins/omt_status.ts",
        ".opencode/plugins/omt_think.ts",
        ".opencode/lib/omt_shared.ts",
    ])
    def test_plugin_files_are_harness_guarded(self, rel: str):
        assert (REPO_ROOT / rel).exists(), f"{rel} missing — path drift?"
        assert self._is_omt_harness(rel), (
            f"BUG-B: isOmtHarness does not cover {rel} — the e2e receipt guard "
            "is dead for the enforcement plugins (dir renamed plugin→plugins "
            "but prefix never updated)")

    def test_guard_prefixes_match_real_repo_paths(self):
        """Every path literal in isOmtHarness must match ≥1 real repo path —
        catches the whole stale-prefix defect class, not just BUG-B."""
        src = SHARED_LIB.read_text(encoding="utf-8")
        body = src[src.index("export function isOmtHarness"):src.index("export function receiptTimestampMs")]
        literals = (re.findall(r'rel === "([^"]+)"', body)
                    + re.findall(r'rel\.startsWith\("([^"]+)"\)', body))
        stale = [lit for lit in literals
                 if not (REPO_ROOT / lit).exists()
                 and not any(REPO_ROOT.glob(lit + "*"))
                 and not any(REPO_ROOT.glob(lit.rstrip("/") + "/*"))]
        assert not stale, (
            f"isOmtHarness literals match NO real repo path (stale guards): {stale}")


class TestE2EHarnessFileListPin:
    """The e2e receipt covers HARNESS_FILES — every entry must exist."""

    def test_harness_files_all_exist(self):
        src = E2E_TEST.read_text(encoding="utf-8")
        m = re.search(r"HARNESS_FILES = \[(.*?)\]", src, re.DOTALL)
        assert m, "HARNESS_FILES list not found in e2e test"
        entries = re.findall(r'"([^"]+)"', m.group(1))
        missing = [e for e in entries if not (REPO_ROOT / e).exists()]
        assert not missing, (
            f"e2e HARNESS_FILES entries do not exist (stale paths — the "
            f"receipt then guards nothing): {missing}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
