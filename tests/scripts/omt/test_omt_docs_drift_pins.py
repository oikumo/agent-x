#!/usr/bin/env python3
"""Docs/config drift pins (meta_harness_dsl R5 + R7 T1/T5 ride-alongs).

The P2 drift class (four audit rounds of path/singular drift: F3/F4/F5/F14/F16)
is pinned mechanically here so it cannot recur:

1. NO singular `.opencode/plugin/` (literal AND Path-parts forms, F5) anywhere
   outside an explicit frozen set (see FROZEN_*): README.md is NEVER-edit
   protected (F25; user hand-edits at leisure); the guard source-pins docstring
   quotes the pre-rename path BY DESIGN (F24 — it describes the bug it pins);
   per-feature docs + PoC eval docs are frozen point-in-time records (F16 —
    rewriting them falsifies history); .sandbox/ holds planning docs/audit records.
2. opencode.jsonc's `plugin` array carries NO local omt_* plugin names (F14:
   the array is npm-only; local plugins auto-load from .opencode/plugins/).
3. Startup contract (R7 T1/F30): .agents_prompts/build.md carries the
   WORK.md-only startup sentence (R8: the AGENTS.md leg is now pinned by
   `harnessc check --verify-projections` — the .omt single-sources it).
4. Tool-set sync (R8 form): plugin-registered tools == IR `tools` keys (F35).
   The AGENTS.md table, opencode.jsonc perm keys and CMD_ entries are
   compiler-projected from the same IR — verify-projections owns those legs.
5. R7 T5 token budget pins (F32: conversation-resident injections re-pay EVERY
   model turn): AGENTS.md ≤ 2816 B; WORK.md ≤ 8 KiB with scratchpad ≤ 3 KiB;
   nav tip ≤ 0.5 KiB; TA digest hard-capped at DIGEST_CAP_BYTES ≤ 1 KiB.

R8 DELETED pins (now compiler-owned): the old #5 COMP_*-paths-exist pin —
harnessc `check_comp_paths` owns it against the .omt, and META_HARNESS.md is a
generated stub.

Budget failures say "grow the budget deliberately in the same commit" — the pin
forces a conscious edit, not a hard ceiling (plan §5).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

AGENTS = REPO_ROOT / "AGENTS.md"
BUILD_PROMPT = REPO_ROOT / ".agents_prompts" / "build.md"
CONFIG = REPO_ROOT / "opencode.jsonc"
WORK = REPO_ROOT / "WORK.md"
IR = REPO_ROOT / ".meta" / ".omt" / "harness.ir.json"
SHARED_LIB = REPO_ROOT / ".opencode" / "lib" / "omt_shared.ts"
NAV_GATE = REPO_ROOT / ".opencode" / "lib" / "enforcer" / "nav_gate.ts"


def _eval_int_expr(expr: str) -> int:
    """Evaluate a pure-integer arithmetic literal (e.g. '8 * 60 * 60 * 1000')."""
    assert re.fullmatch(r"[\d\s*]+", expr), f"not a pure int expr: {expr!r}"
    return int(eval(expr))  # input regex-pinned to digits, spaces and '*'


# --- 1. singular-path drift (P2/F3/F4/F5/F16) -------------------------------

SINGULAR_LITERAL = re.compile(r"\.opencode/plugin/")
SINGULAR_PATH_PARTS = re.compile(r"""["']\.opencode["']\s*/\s*["']plugin["']""")

FROZEN_FILES = {
    "README.md",  # F25: NEVER-edit protected; user hand-edits at leisure
    # F24: the docstring quotes the pre-rename path to describe the pinned bug
    "tests/scripts/omt/test_omt_enforcer_guard_source_pins.py",
    # self-exclusion: this file carries the pattern by definition
    "tests/scripts/omt/test_omt_docs_drift_pins.py",
}
FROZEN_PREFIXES = (
    ".meta/software_development_process/",  # F16: per-feature docs = frozen history
    ".meta/proof_of_concepts/",             # historical PoC eval doc
    ".sandbox/",                             # sandbox planning docs / audit records
)


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def test_no_singular_plugin_path_outside_frozen_history() -> None:
    hits: list[str] = []
    for rel in _tracked_files():
        if rel in FROZEN_FILES or any(rel.startswith(p) for p in FROZEN_PREFIXES):
            continue
        path = REPO_ROOT / rel
        if not path.exists():
            continue  # tracked but deleted in the worktree (pending commit)
        if path.suffix.lower() not in (".md", ".py", ".ts", ".jsonc", ".txt"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            if SINGULAR_LITERAL.search(line) or SINGULAR_PATH_PARTS.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()[:80]}")
    assert not hits, (
        "singular `.opencode/plugin/` drift outside the frozen historical set "
        "(the plugins dir is PLURAL; R0 fixed the live set — do not let it "
        "regrow):\n" + "\n".join(hits)
    )


# --- 2. plugin array is npm-only (F14) --------------------------------------


def test_plugin_array_has_no_local_plugins() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    stripped = re.sub(r"//[^\n]*", "", text)  # jsonc: strip line comments
    m = re.search(r'"plugin"\s*:\s*\[(.*?)\]', stripped, re.DOTALL)
    if not m:
        return  # no plugin array at all — the F14 end state, fine
    entries = re.findall(r'"([^"]+)"', m.group(1))
    local = [e for e in entries if e.startswith("omt_")]
    assert not local, (
        "opencode.jsonc `plugin` array is npm-only (F14); local plugins "
        f"auto-load from .opencode/plugins/ — remove: {local}")


# --- 3. startup contract (R7 T1/F30; R8: build.md leg only) -----------------

STARTUP_SENTENCE = (
    "Read `WORK.md` (only) at session start; summarize current state in ≤ 15 "
    "lines (in-progress / blocked / next). All other docs on demand via "
    "`omt_nav` (op=nav|list_sections|cross_ref|quick_ref)."
)


def test_build_prompt_carries_startup_contract() -> None:
    text = BUILD_PROMPT.read_text(encoding="utf-8")
    assert STARTUP_SENTENCE in text, (
        ".agents_prompts/build.md lost the WORK.md-only startup sentence "
        "(R7 T1/F30 — drift here re-inflates every session by ~10-11k tok. "
        "R8: the AGENTS.md leg is pinned by `harnessc check "
        "--verify-projections`; the .omt single-sources it)")


# --- 4. tool-set sync (R8: plugin-registered ↔ IR `tools` keys) --------------


def _registered_omt_tools() -> set[str]:
    """Tool names the plugins actually register: `tool: { ... }` map keys in
    .opencode/plugins/omt_*.ts plus the `const omt_<x> = …` tool factories in
    the enforcer lib modules (phase_gate uses `tool(...)`, tdd_hats its
    `tddTool(...)` wrapper — both declare `const omt_<x> =`)."""
    tools: set[str] = set()
    for path in sorted((REPO_ROOT / ".opencode" / "plugins").glob("omt_*.ts")):
        src = path.read_text(encoding="utf-8")
        for m in re.finditer(r"tool:\s*\{([^}]*)\}", src, re.DOTALL):
            tools.update(re.findall(r"\bomt_\w+\b", m.group(1)))
    for path in sorted((REPO_ROOT / ".opencode" / "lib" / "enforcer").glob("*.ts")):
        src = path.read_text(encoding="utf-8")
        tools.update(re.findall(r"const\s+(omt_\w+)\s*=", src))
    return tools


def test_omt_tool_set_is_in_sync_everywhere() -> None:
    registered = _registered_omt_tools()
    assert registered, "no omt_* tools found in the plugin sources?"
    ir_tools = set(json.loads(IR.read_text(encoding="utf-8"))["tools"])
    assert registered == ir_tools, (
        "omt_* tool-set drift: only in plugins="
        f"{sorted(registered - ir_tools)} only in IR={sorted(ir_tools - registered)} "
        "(R8/F35: the IR is the single source — AGENTS.md table, opencode.jsonc "
        "perm keys and CMD_ entries are compiler projections owned by "
        "`harnessc check --verify-projections`)")


# --- 6. R7 T5 token budget pins (F32) ---------------------------------------

AGENTS_BUDGET = 2816             # rides the system prompt EVERY turn (F33; improvement004/OPT-A: §12/TDD/NAV/THINK/QuickRef tables → nav pointers — .omt @budget agents_md=2816 is the source of truth; 2026-08-08: 2560→2816 to add .projects/ component line)
# TA: why: meta.projects_harness_surface: AGENTS_BUDGET 2560→2816 to admit the `**Projects home (.projects/):**` line mirroring `.workflows/`. AGENTS.md now 2626 B (190 B headroom). Each similar future line costs ~250-300 B — grow the budget deliberately in the same .omt commit per the existing convention.
WORK_BUDGET = 8192          # read at every session startup (feature_kb_akb: +1 task → 5120; feature_038 active row → 5632; feature_039 pause line + project-link row → 6144; feature_041 paused task row → 7168, two +512 steps at once; feature_045 DONE-row detail → 7680; feature_048 WIP-pool row + duplicate-link project row → 8192 — .omt @budget work_md=8192 is the source of truth)
SCRATCHPAD_BUDGET = 3 * 1024    # T2: CURRENT/RECURRING only (improvement002/OPT-B: gotchas relocated to @doc gotcha.* — .omt @budget work_scratchpad=3072 is the source of truth)
NAV_TIP_BUDGET = 512            # C5: conversation-resident once per session
DIGEST_BUDGET = 1024            # C4: conversation-resident once per session


def _budget_fail(what: str, size: int, budget: int) -> str:
    return (f"{what} is {size} B > {budget} B budget (R7 T5; paid every "
            "session/turn — trim, or grow the budget deliberately in the "
            "same commit)")


def test_agents_md_within_budget() -> None:
    size = AGENTS.stat().st_size
    assert size <= AGENTS_BUDGET, _budget_fail("AGENTS.md", size, AGENTS_BUDGET)


def test_work_md_within_budget() -> None:
    size = WORK.stat().st_size
    assert size <= WORK_BUDGET, _budget_fail("WORK.md", size, WORK_BUDGET)
    text = WORK.read_text(encoding="utf-8")
    scratch = text.split("## Agent Scratchpad", 1)
    assert len(scratch) == 2, "WORK.md lost the '## Agent Scratchpad' section"
    scratch_size = len(("## Agent Scratchpad" + scratch[1]).encode("utf-8"))
    assert scratch_size <= SCRATCHPAD_BUDGET, _budget_fail(
        "WORK.md scratchpad", scratch_size, SCRATCHPAD_BUDGET)


def test_nav_tip_within_budget() -> None:
    src = NAV_GATE.read_text(encoding="utf-8")
    m = re.search(r"const navReminderMsg = \(\) =>\n(.*?)\n\n", src, re.DOTALL)
    assert m, "navReminderMsg not found in nav_gate.ts (R5 budget pin target)"
    segs = re.findall(r"`([^`]*)`", m.group(1))
    assert segs, "navReminderMsg carries no template literals?"
    size = sum(len(s.encode("utf-8")) for s in segs)
    assert size <= NAV_TIP_BUDGET, _budget_fail("nav tip", size, NAV_TIP_BUDGET)


def test_digest_byte_cap_pinned() -> None:
    src = SHARED_LIB.read_text(encoding="utf-8")
    m = re.search(r"DIGEST_CAP_BYTES\s*=\s*([0-9 *]+)", src)
    assert m, ("DIGEST_CAP_BYTES missing in omt_shared.ts (R7 T5: the digest "
               "needs a hard byte cap — F32 re-pays it every model turn)")
    cap = _eval_int_expr(m.group(1))
    assert cap <= DIGEST_BUDGET, _budget_fail("DIGEST_CAP_BYTES", cap, DIGEST_BUDGET)
    digest_fn = src.split("export function thinkDigest", 1)
    assert len(digest_fn) == 2 and "DIGEST_CAP_BYTES" in digest_fn[1], (
        "thinkDigest must actually apply DIGEST_CAP_BYTES to its return value")


# --- R11 (improvement007/OPT-H): guide dedup drift pins -----------------------
# The guide stays the METHODOLOGY authority (§12/§16 single-sourced there); the
# .omt corpus owns harness mechanics. These pins keep the R11 cut from drifting
# back: live §-refs resolve, @xref guide routes every section, mvc_check's
# §16.N row citations keep their rows, §11.4 stays a summary (no restatement
# regrowth).
GUIDE = REPO_ROOT / ".meta" / "software_development_process" / "omt_agent_guide.md"
TEMPLATES_DIR = REPO_ROOT / ".meta" / "templates"
OMT_SRC = REPO_ROOT / ".meta" / "META_HARNESS.omt"


def _guide_section_numbers() -> set[str]:
    text = GUIDE.read_text(encoding="utf-8")
    return set(re.findall(r"^## (\d+(?:\.\d+)?)\.", text, flags=re.M))


def test_live_guide_section_refs_resolve() -> None:
    """Every omt_agent_guide §-ref in live templates/scripts resolves to a section."""
    sections = _guide_section_numbers()
    anchors = {s.split(".")[0] for s in sections}
    refs: set[str] = set()
    live = sorted(TEMPLATES_DIR.glob("*.md")) + sorted(
        (REPO_ROOT / "scripts" / "omt").glob("*.py"))
    for path in live:
        for line in path.read_text(encoding="utf-8").splitlines():
            if "omt_agent_guide" in line:
                refs.update(re.findall(r"§(\d+(?:\.\d+)?)", line))
    missing = {r for r in refs if r not in sections and r.split(".")[0] not in anchors}
    assert refs, "no live guide §-refs found — pin lost its target"
    assert not missing, f"guide §-refs without a matching section: {sorted(missing)}"


def test_xref_guide_covers_all_guide_sections() -> None:
    """@xref guide routes every methodology section (nav answers 'where is X')."""
    omt = OMT_SRC.read_text(encoding="utf-8")
    xref_line = next(l for l in omt.splitlines() if l.startswith("@xref guide "))
    covered = set(re.findall(r"§(\d+(?:\.\d+)?)", xref_line))
    missing = _guide_section_numbers() - covered
    assert not missing, f"guide sections not routed by @xref guide: {sorted(missing)}"


def test_mvc_check_cited_mistake_rows_exist() -> None:
    """mvc_check.py message citations (guide §16.N) must keep their §16 table rows."""
    mvc_src = (REPO_ROOT / "scripts" / "omt" / "mvc_check.py").read_text(encoding="utf-8")
    cited = set(re.findall(r"guide §16\.(\d+)", mvc_src))
    sec16 = GUIDE.read_text(encoding="utf-8").split("## 16.", 1)[1]
    rows = set(re.findall(r"^\| (\d+) \|", sec16, flags=re.M))
    assert cited, "mvc_check no longer cites guide §16 rows — pin lost its target"
    assert cited <= rows, f"mvc_check cites §16 rows missing from the guide: {cited - rows}"


def test_guide_tdd_section_defers_to_corpus() -> None:
    """§11.4 stays a summary + nav pointer — the corpus owns TDD mechanics (R11)."""
    sec = GUIDE.read_text(encoding="utf-8").split("## 11.4", 1)[1].split("\n## ", 1)[0]
    assert "omt_nav" in sec and "@fsm tdd" in sec, (
        "§11.4 lost its corpus pointer — restatement crept back?")
    assert len(sec.splitlines()) <= 25, (
        f"§11.4 regrew to {len(sec.splitlines())} lines — TDD mechanics belong "
        "in the .omt corpus (@fsm tdd / @hat / @doc tdd.*), not in guide prose")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
