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

import json
import re
import shutil
import subprocess
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


IR = REPO_ROOT / ".meta" / ".omt" / "harness.ir.json"


class TestHarnessPathsIrSyncPin:
    """meta_harness_dsl R8 follow-up: isOmtHarness's TS fallback literal and
    the compiled IR `harness_paths` (.omt @var harness_paths → harnessc
    exact/prefix classification) must be the SAME set. The IR is the
    functional source at runtime; the literal only keeps the guard alive when
    the projection is missing — drift between them silently un-guards files
    (F9 alignment class, the BUG-B sibling)."""

    def test_ts_fallback_literal_matches_ir_harness_paths(self):
        import json
        src = SHARED_LIB.read_text(encoding="utf-8")
        body = src[src.index("export function isOmtHarness"):src.index("export function receiptTimestampMs")]
        ts_set = set(re.findall(r'rel === "([^"]+)"', body)) | set(
            re.findall(r'rel\.startsWith\("([^"]+)"\)', body))
        hp = json.loads(IR.read_text(encoding="utf-8"))["harness_paths"]
        ir_set = set(hp["exact"]) | set(hp["prefix"])
        assert ts_set == ir_set, (
            "isOmtHarness fallback literal drifted from IR harness_paths "
            "(source: .meta/META_HARNESS.omt @var harness_paths): "
            f"only-in-TS={sorted(ts_set - ir_set)} "
            f"only-in-IR={sorted(ir_set - ts_set)} — edit the .omt, run "
            "harnessc.py build, and update the fallback in the same commit")


NAV_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "nav_gate.ts"


DRIVER = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "gate_driver.ts"


class TestGateDriverIrPin:
    """improvement006/OPT-F (HDL-2): the before-hook gate chain is data-driven.
    gate_driver.ts iterates IR before-gates in ascending order= and dispatches
    to the IMPLS registry; the composition root only calls navTrack +
    runBeforeGates. Drift between IR order and code order (the former textual
    call-order pin, T-024 fix 1) is structurally impossible for before-gates
    now; these pins cover the new invariants. improvement007 R7/OPT-F: the
    after-gates (g.mvc, g.tdd_after) are data-driven too — AFTER_IMPLS +
    runAfterGates own the after-chain; the textual after-order pin became the
    delegate/sort/registry pins below."""

    def test_impls_cover_exactly_the_ir_before_gates(self):
        import json
        ids = {g["id"] for g in json.loads(IR.read_text(encoding="utf-8"))["gates"]
               if g["on"] == "before"}
        src = DRIVER.read_text(encoding="utf-8")
        m = re.search(r"const IMPLS[^{]*\{(.*?)\n\}", src, re.DOTALL)
        assert m, "IMPLS registry not found in gate_driver.ts"
        impls = set(re.findall(r'"(g\.\w+)"\s*:', m.group(1)))
        assert impls == ids, (
            "IMPLS registry drifted from IR before-gates: "
            f"only-in-IMPLS={sorted(impls - ids)} only-in-IR={sorted(ids - impls)} "
            "(an IR before-gate without an impl runs as a GENERIC pred-composed "
            "gate — register an impl or accept generic semantics deliberately)")

    def test_driver_sorts_gates_by_ir_order(self):
        src = DRIVER.read_text(encoding="utf-8")
        assert re.search(r"\.sort\(\(a[^)]*\)\s*=>\s*a\.order\s*-\s*b\.order\)", src), (
            "gate_driver must iterate before-gates in ascending IR order= "
            "(HDL-2: order is data, not code)")

    def test_composition_root_delegates_to_driver(self):
        body = _hook_body(ENFORCER.read_text(encoding="utf-8"), "tool.execute.before")
        assert "runBeforeGates(" in body, "before-hook must delegate to the HDL-2 driver"
        assert "navTrack(" in body, "before-hook must run nav instrumentation"
        for legacy in ("guardProtectedPath(", "guardHarnessReceipt(",
                       "guardTestsPath(", "guardSrcPath(", "guardThoughts("):
            assert legacy not in body, (
                f"hand-ordered gate call {legacy} survived in the composition "
                "root — HDL-2: the driver owns the before-chain")

    def test_after_hook_delegates_to_driver(self):
        """improvement007 R7/OPT-F: the after-hook keeps composition-only
        concerns (bootstrap, thought injection, raw guard) and delegates the
        gate chain to runAfterGates — no hand-ordered impl calls survive."""
        body = _hook_body(ENFORCER.read_text(encoding="utf-8"), "tool.execute.after")
        assert "runAfterGates(" in body, "after-hook must delegate to the HDL-2 driver"
        for legacy in ("mvcAfterEdit(", "tddAfterEdit("):
            assert legacy not in body, (
                f"hand-ordered after-gate call {legacy} survived in the "
                "composition root — HDL-2 R7: the driver owns the after-chain")

    def test_driver_sorts_after_gates_by_ir_order(self):
        src = DRIVER.read_text(encoding="utf-8")
        region = src[src.index("export async function runAfterGates"):]
        assert '.on === "after"' in region, (
            "runAfterGates must select the IR after-gates (on=after)")
        assert re.search(r"\.sort\(\(a[^)]*\)\s*=>\s*a\.order\s*-\s*b\.order\)", region), (
            "runAfterGates must iterate after-gates in ascending IR order= "
            "(HDL-2: order is data, not code; IR order uniqueness per on= "
            "group is compiler-enforced via check_grammar_vocab)")

    def test_after_impls_cover_exactly_the_ir_after_gates(self):
        import json
        ids = {g["id"] for g in json.loads(IR.read_text(encoding="utf-8"))["gates"]
               if g["on"] == "after"}
        src = DRIVER.read_text(encoding="utf-8")
        m = re.search(r"const AFTER_IMPLS[^{]*\{(.*?)\n\}", src, re.DOTALL)
        assert m, "AFTER_IMPLS registry not found in gate_driver.ts"
        impls = set(re.findall(r'"(g\.\w+)"\s*:', m.group(1)))
        assert impls == ids, (
            "AFTER_IMPLS registry drifted from IR after-gates: "
            f"only-in-AFTER_IMPLS={sorted(impls - ids)} "
            f"only-in-IR={sorted(ids - impls)} (an IR after-gate without an "
            "impl is skipped fail-open — register an impl deliberately)")


class TestDocPathsIrSyncPin:
    """meta_harness_dsl R8 follow-up (T-024 fix 2, the @var harness_paths F9
    sibling): nav_gate.ts isDocPath's fallback literal and the compiled IR
    `vars.doc_paths` (.omt @var doc_paths — comma string; a trailing "/"
    entry is a prefix, anything else exact) must be the SAME set. The IR is
    the functional source at runtime; the literal only keeps the nav gate
    alive when the projection is missing — drift silently un-gates doc
    searches."""

    def test_ts_fallback_literal_matches_ir_doc_paths(self):
        import json
        src = NAV_GATE.read_text(encoding="utf-8")
        body = src[src.index("export function isDocPath"):src.index("export function navGateDecision")]
        ts_exact = set(re.findall(r'rel === "([^"]+)"', body))
        ts_prefix = set(re.findall(r'rel\.startsWith\("([^"]+)"\)', body))
        dp = json.loads(IR.read_text(encoding="utf-8"))["vars"]["doc_paths"]
        entries = [e.strip() for e in dp.split(",") if e.strip()]
        ir_exact = {e for e in entries if not e.endswith("/")}
        ir_prefix = {e for e in entries if e.endswith("/")}
        assert ts_exact == ir_exact and ts_prefix == ir_prefix, (
            "isDocPath fallback literal drifted from IR vars.doc_paths "
            "(source: .meta/META_HARNESS.omt @var doc_paths): "
            f"exact only-in-TS={sorted(ts_exact - ir_exact)} "
            f"only-in-IR={sorted(ir_exact - ts_exact)}; "
            f"prefix only-in-TS={sorted(ts_prefix - ir_prefix)} "
            f"only-in-IR={sorted(ir_prefix - ts_prefix)} — edit the .omt, run "
            "harnessc.py build, and update the fallback in the same commit")


PHASE_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "phase_gate.ts"
RECEIPT_GUARD = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "receipt_guard.ts"
STATUS = REPO_ROOT / ".opencode" / "plugins" / "omt_status.ts"
THINK = REPO_ROOT / ".opencode" / "plugins" / "omt_think.ts"
THINK_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "think_gate.ts"
MVC_AFTER = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "mvc_after.ts"
TDD_HATS = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "tdd_hats.ts"


class TestIrAccessorFallbackSyncPin:
    """improvement007/OPT-E: the TS guards now resolve their values from the
    compiled IR at runtime (.omt is the single source); each FALLBACK_*
    literal keeps its guard alive only when the projection is missing/corrupt
    and must equal the IR value it mirrors — drift silently mis-gates paths
    (the F9/BUG-B defect class)."""

    @staticmethod
    def _ir() -> dict:
        import json
        return json.loads(IR.read_text(encoding="utf-8"))

    def test_phase_transitions_fallback_matches_ir(self):
        src = SHARED_LIB.read_text(encoding="utf-8")
        m = re.search(r'FALLBACK_PHASE_TRANSITIONS = "([^"]+)"', src)
        assert m, "FALLBACK_PHASE_TRANSITIONS missing in omt_shared.ts"
        assert m.group(1) == self._ir()["fsm"]["phase"]["transitions"], (
            "phase-transitions fallback drifted from IR fsm.phase.transitions "
            "(source: .omt @fsm phase transitions=)")

    def test_tdd_auto_on_fallback_matches_ir(self):
        src = SHARED_LIB.read_text(encoding="utf-8")
        m = re.search(r'FALLBACK_TDD_AUTO_ON = "([^"]+)"', src)
        assert m, "FALLBACK_TDD_AUTO_ON missing in omt_shared.ts"
        assert m.group(1) == self._ir()["fsm"]["tdd"]["auto_on"], (
            "tdd auto_on fallback drifted from IR fsm.tdd.auto_on "
            "(source: .omt @fsm tdd auto_on=)")

    def test_search_tools_fallback_matches_ir(self):
        src = NAV_GATE.read_text(encoding="utf-8")
        m = re.search(r'FALLBACK_SEARCH_TOOLS = "([^"]+)"', src)
        assert m, "FALLBACK_SEARCH_TOOLS missing in nav_gate.ts"
        assert m.group(1) == self._ir()["vars"]["search_tools"], (
            "search-tools fallback drifted from IR vars.search_tools "
            "(source: .omt @var search_tools)")

    def test_protect_fallback_matches_ir(self):
        src = SHARED_LIB.read_text(encoding="utf-8")
        region = src[src.index("const FALLBACK_PROTECT"):]
        region = region[:region.index("\n]")]
        ts = [(p, h == "true") for p, h in
              re.findall(r'\{ path: "([^"]+)", hard: (true|false) \}', region)]
        ir = [(p["path"], p["hard"]) for p in self._ir()["protect"]]
        assert ts == ir, (
            "protect fallback drifted from IR protect (source: .omt @protect): "
            f"TS={ts} IR={ir}")

    def test_e2e_cmd_fallback_matches_ir(self):
        src = SHARED_LIB.read_text(encoding="utf-8")
        m = re.search(r'OMT_HARNESS_E2E_COMMAND = "([^"]+)"', src)
        assert m, "OMT_HARNESS_E2E_COMMAND missing in omt_shared.ts"
        assert m.group(1) == self._ir()["vars"]["e2e_cmd"], (
            "e2e-command fallback drifted from IR vars.e2e_cmd "
            "(source: .omt @var e2e_cmd)")

    def test_e2e_receipt_fallback_matches_ir(self):
        src = SHARED_LIB.read_text(encoding="utf-8")
        m = re.search(r'OMT_HARNESS_E2E_RECEIPT = join\(([^)]*)\)', src)
        assert m, "OMT_HARNESS_E2E_RECEIPT missing in omt_shared.ts"
        parts = re.findall(r'"([^"]+)"', m.group(1))
        assert parts and "/".join(parts) == self._ir()["vars"]["receipt_path"], (
            "e2e-receipt fallback drifted from IR vars.receipt_path "
            "(source: .omt @var receipt_path)")

    def test_e2e_test_fallback_matches_ir(self):
        src = SHARED_LIB.read_text(encoding="utf-8")
        m = re.search(r'OMT_HARNESS_E2E_TEST = "([^"]+)"', src)
        assert m, "OMT_HARNESS_E2E_TEST missing in omt_shared.ts"
        assert m.group(1) == self._ir()["vars"]["e2e_test"], (
            "e2e-test fallback drifted from IR vars.e2e_test "
            "(source: .omt @var e2e_test)")

    def test_consumers_resolve_through_accessors(self):
        """The hand mirrors are deleted: consumers call the IR accessors."""
        checks = [
            (PHASE_GATE, "phaseTransitions()", r"\bVALID_TRANSITIONS\b"),
            (PHASE_GATE, "tddAutoOn(", None),
            (STATUS, "phaseTransitions()", r"\bVALID_TRANSITIONS\b"),
            (NAV_GATE, "searchTools()", r"\bSEARCH_TOOLS\b"),
            (RECEIPT_GUARD, "protectList()", None),
            (SHARED_LIB, "thoughtPattern()", None),
            (SHARED_LIB, "e2eCommand()", None),
            (SHARED_LIB, "e2eReceiptPath()", None),
            (SHARED_LIB, "e2eTestPath()", None),
            (THINK, "thoughtPattern()", None),
            (THINK_GATE, "thoughtPattern()", None),
            # improvement007 R8/OPT-G: gate block/warn texts resolve from the
            # IR @msg records via the shared gateMsg renderer (the inline msg
            # helpers are deleted — texts are .omt-only edits now).
            (SHARED_LIB, "export function gateMsg", None),
            (RECEIPT_GUARD, 'gateMsg("protect_env"', r"\bdenyMsg\b"),
            (RECEIPT_GUARD, 'gateMsg("protect_file"', r"\btestsMsg\b"),
            (RECEIPT_GUARD, 'gateMsg("tests_canary"', None),
            (PHASE_GATE, 'gateMsg("no_phase"', r"\bnoPhaseMsg\b"),
            (PHASE_GATE, 'gateMsg("artifact"', r"\bartifactMsg\b"),
            (SHARED_LIB, 'gateMsg("receipt_stale"', None),
            (THINK_GATE, 'gateMsg("think_gate"', None),
            (MVC_AFTER, 'gateMsg("mvc_new_hard"', None),
            (MVC_AFTER, 'gateMsg("mvc_warn"', None),
            (TDD_HATS, 'gateMsg("tdd_revert"', None),
            (DRIVER, 'gateMsg("nav_required"', r"\bnavRequiredMsg\b"),
            (NAV_GATE, "navGateDecision", r"\bnavRequiredMsg\b"),
        ]
        for path, needed, banned in checks:
            src = path.read_text(encoding="utf-8")
            assert needed in src, f"{path.name}: {needed} missing (OPT-E accessor)"
            if banned:
                assert not re.search(banned, src), (
                    f"{path.name}: hand mirror {banned} survived (OPT-E deletes it)")


class TestFallbackGatesIrSyncPin:
    """improvement007/OPT-E: the gate_driver FALLBACK_GATES literal (the
    IR-missing never-die-open chain) must mirror the IR before-gates on every
    field the driver consumes — except requires=, which the registered impls
    deliberately own (the fallback keeps it empty). R7/OPT-F: the same
    discipline covers FALLBACK_AFTER_GATES vs the IR after-gates (run= is
    impl-owned too and excluded like requires=)."""

    FIELDS = ("id", "on", "tools", "when", "msg", "hard", "skip_ok", "order")

    @staticmethod
    def _parse_fallback(src: str, const_name: str) -> list:
        region = src[src.index(f"const {const_name}"):]
        region = region[: region.index("\n]")]
        objs = re.findall(r"\{(.*?)\}", region, re.DOTALL)
        assert objs, f"{const_name} entries not found in gate_driver.ts"

        def parse(obj: str) -> dict:
            out: dict = {}
            for f in TestFallbackGatesIrSyncPin.FIELDS:
                m = re.search(
                    rf"{f}: " + r'"((?:[^"\\]|\\.)*)"|'
                    + rf"{f}: " + r"'((?:[^'\\]|\\.)*)'|"
                    + rf"{f}: (true|false|\d+)", obj)
                assert m, f"field {f} not found in {const_name} entry {obj!r}"
                raw = next(g for g in m.groups() if g is not None)
                if raw == "true":
                    out[f] = True
                elif raw == "false":
                    out[f] = False
                elif raw.isdigit():
                    out[f] = int(raw)
                else:
                    # DSL attr parser strips quotes compiling when= into the IR
                    out[f] = raw.replace('"', "") if f in ("when", "requires") else raw
            return out

        return sorted((parse(o) for o in objs), key=lambda g: g["order"])

    @staticmethod
    def _ir_gates(on: str) -> list:
        import json
        return sorted(
            ({f: g[f] for f in TestFallbackGatesIrSyncPin.FIELDS}
             for g in json.loads(IR.read_text(encoding="utf-8"))["gates"]
             if g["on"] == on),
            key=lambda g: g["order"])

    def test_fallback_gates_mirror_ir_before_gates(self):
        ts_gates = self._parse_fallback(
            DRIVER.read_text(encoding="utf-8"), "FALLBACK_GATES")
        expected = self._ir_gates("before")
        assert expected == ts_gates, (
            "FALLBACK_GATES drifted from the IR before-gates (source: .omt "
            "@gate records) — edit the .omt, run harnessc.py build, and update "
            "the fallback in the same commit: "
            f"only-in-IR={ [e for e in expected if e not in ts_gates] } "
            f"only-in-TS={ [t for t in ts_gates if t not in expected] }")

    def test_fallback_after_gates_mirror_ir_after_gates(self):
        ts_gates = self._parse_fallback(
            DRIVER.read_text(encoding="utf-8"), "FALLBACK_AFTER_GATES")
        expected = self._ir_gates("after")
        assert expected == ts_gates, (
            "FALLBACK_AFTER_GATES drifted from the IR after-gates (source: "
            ".omt @gate records) — edit the .omt, run harnessc.py build, and "
            "update the fallback in the same commit: "
            f"only-in-IR={ [e for e in expected if e not in ts_gates] } "
            f"only-in-TS={ [t for t in ts_gates if t not in expected] }")


BUN = shutil.which("bun")
DRIVER_PROBE = """
import { initOmtShared } from "%LIB%"
import { runBeforeGates } from "%DRIVER%"
import { createSessionState, OmtBlock } from "%STATE%"
initOmtShared(process.argv[2])
const env = {
  client: {}, $: {}, directory: process.argv[2],
  state: createSessionState(),
  safeLog: () => {},
  notify: async () => {},
}
let result = "NO_BLOCK"
try {
  await runBeforeGates(env, "r6-probe", { tool: "edit" }, { args: { filePath: "README.md" } }, "README.md")
} catch (e) {
  result = e instanceof OmtBlock ? "BLOCKED" : "OTHER:" + (e?.message || e)
}
console.log(JSON.stringify({ result }))
"""


class TestGateDriverProtectIrMissing:
    """improvement007 R6(a): HDL-2 die-open fix — with the IR projection
    missing, the g.protect when= pre-filter evaluated path_in(@protect.*)
    against an EMPTY ir.protect and skipped the gate: protected files were
    unguarded on the fallback chain (the protectList fallback was unreachable
    via the chain). pathIn now falls back to the shared-lib protectList()
    (FALLBACK_PROTECT literal). Bun probe: runBeforeGates on README.md with NO
    IR under the probe root must STILL block."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_ir_missing_chain_still_blocks_protected(self, tmp_path):
        (tmp_path / "README.md").write_text("# probe\n", encoding="utf-8")
        probe = tmp_path / "probe.ts"
        probe.write_text(
            DRIVER_PROBE.replace("%LIB%", str(SHARED_LIB))
            .replace("%DRIVER%", str(DRIVER))
            .replace("%STATE%", str(
                REPO_ROOT / ".opencode" / "lib" / "enforcer" / "session_state.ts")),
            encoding="utf-8")
        out = subprocess.run(
            [BUN, str(probe), str(tmp_path)],
            capture_output=True, text=True, timeout=60)
        assert out.returncode == 0, out.stderr
        data = json.loads(out.stdout.strip().splitlines()[-1])
        assert data["result"] == "BLOCKED", (
            "IR-missing fallback chain must still block protected files "
            f"(g.protect die-open regression): {data}")



DRIVER_PROBE_IR_MSG = """
import { initOmtShared } from "%LIB%"
import { runBeforeGates } from "%DRIVER%"
import { createSessionState, OmtBlock } from "%STATE%"
initOmtShared(process.argv[2])
const env = {
  client: {}, $: {}, directory: process.argv[2],
  state: createSessionState(),
  safeLog: () => {},
  notify: async () => {},
}
let out = { result: "NO_BLOCK", message: "" }
try {
  await runBeforeGates(env, "r8-probe", { tool: "edit" }, { args: { filePath: "README.md" } }, "README.md")
} catch (e) {
  out = { result: e instanceof OmtBlock ? "BLOCKED" : "OTHER", message: e?.message || "" }
}
console.log(JSON.stringify(out))
"""


class TestGateDriverIrRenderedMsg:
    """improvement007 R8/OPT-G: with the IR projection present, the g.protect
    block text is the IR @msg protect_file record rendered through gateMsg
    ({rel} interpolated) — never a hand-mirrored inline string. Hermetic: the
    repo IR is copied into a tmp root (empty ledger => no unlock)."""

    @pytest.mark.skipif(BUN is None, reason="bun runtime not available")
    def test_ir_msg_text_rendered_in_block(self, tmp_path):
        (tmp_path / "README.md").write_text("# probe\n", encoding="utf-8")
        ir_dst = tmp_path / ".meta" / ".omt"
        ir_dst.mkdir(parents=True)
        shutil.copy2(IR, ir_dst / "harness.ir.json")
        probe = tmp_path / "probe.ts"
        probe.write_text(
            DRIVER_PROBE_IR_MSG.replace("%LIB%", str(SHARED_LIB))
            .replace("%DRIVER%", str(DRIVER))
            .replace("%STATE%", str(
                REPO_ROOT / ".opencode" / "lib" / "enforcer" / "session_state.ts")),
            encoding="utf-8")
        out = subprocess.run(
            [BUN, str(probe), str(tmp_path)],
            capture_output=True, text=True, timeout=60)
        assert out.returncode == 0, out.stderr
        data = json.loads(out.stdout.strip().splitlines()[-1])
        assert data["result"] == "BLOCKED", f"protect gate must block: {data}"
        assert "protected (README.md / uv.lock / LICENSE)" in data["message"], (
            "block text must be the IR @msg protect_file record via gateMsg "
            f"(R8/OPT-G): {data['message']!r}")
        assert "README.md" in data["message"], "{rel} must interpolate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
