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
3. Startup contract single-source (R7 T1/F30): AGENTS.md and
   .agents_prompts/build.md carry the SAME WORK.md-only startup sentence.
4. Tool-set sync: AGENTS.md tools table == META_HARNESS.md CMD_ entries ==
   opencode.jsonc omt_* permission keys == plugin-registered tools (F35).
5. Every COMP_* path in META_HARNESS.md exists on disk.
6. R7 T5 token budget pins (F32: conversation-resident injections re-pay EVERY
   model turn): AGENTS.md ≤ 5 KiB; WORK.md ≤ 14 KiB with scratchpad ≤ 6 KiB;
   nav tip ≤ 0.5 KiB; TA digest hard-capped at DIGEST_CAP_BYTES ≤ 1 KiB.

Budget failures say "grow the budget deliberately in the same commit" — the pin
forces a conscious edit, not a hard ceiling (plan §5).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

AGENTS = REPO_ROOT / "AGENTS.md"
META_HARNESS = REPO_ROOT / ".meta" / "META_HARNESS.md"
BUILD_PROMPT = REPO_ROOT / ".agents_prompts" / "build.md"
CONFIG = REPO_ROOT / "opencode.jsonc"
WORK = REPO_ROOT / "WORK.md"
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


# --- 3. startup contract single-source (R7 T1/F30) --------------------------

STARTUP_SENTENCE = (
    "Read `WORK.md` (only) at session start; summarize current state in ≤ 15 "
    "lines (in-progress / blocked / next). All other docs on demand via nav "
    "tools (`omt_nav`, `omt_list_sections`, `omt_cross_ref`, `omt_quick_ref`)."
)


def test_startup_contract_single_sourced() -> None:
    for path in (AGENTS, BUILD_PROMPT):
        text = path.read_text(encoding="utf-8")
        assert STARTUP_SENTENCE in text, (
            f"{path.relative_to(REPO_ROOT)} lost the WORK.md-only startup "
            "sentence (R7 T1: AGENTS.md and .agents_prompts/build.md must "
            "carry the SAME startup contract — drift here re-inflates every "
            "session by ~10-11k tok, F30)")


# --- 4. tool-set sync (AGENTS.md ↔ META_HARNESS CMD_ ↔ config ↔ plugins) ----


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


def _md_section(text: str, heading: str) -> str:
    """One markdown section: from `## <heading>` to the next `## ` heading."""
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text,
                  re.DOTALL | re.MULTILINE)
    return m.group(1) if m else ""


def test_omt_tool_set_is_in_sync_everywhere() -> None:
    registered = _registered_omt_tools()
    assert registered, "no omt_* tools found in the plugin sources?"
    # AGENTS.md: only the Tools table section counts (the ENF line names the
    # omt_enforcer.ts PLUGIN — a file, not a tool).
    agents_tools = set(re.findall(
        r"\bomt_\w+\b", _md_section(AGENTS.read_text(encoding="utf-8"), "Tools")))
    meta = META_HARNESS.read_text(encoding="utf-8")
    cmd_tools = set(re.findall(r"\bomt_\w+\b", "\n".join(
        line for line in meta.splitlines() if line.startswith("CMD_"))))
    config_tools = set(re.findall(r'"(omt_\w+)"\s*:', CONFIG.read_text(encoding="utf-8")))
    for label, found in (("AGENTS.md", agents_tools), ("META_HARNESS CMD_", cmd_tools),
                         ("opencode.jsonc", config_tools)):
        assert registered == found, (
            f"omt_* tool-set drift vs {label}: "
            f"only in plugins={sorted(registered - found)} "
            f"only in {label}={sorted(found - registered)} "
            "(R5/F35: one set, four places, kept equal)")


# --- 5. COMP_* paths exist on disk ------------------------------------------


def test_comp_paths_exist_on_disk() -> None:
    missing: list[str] = []
    for line in META_HARNESS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"COMP_\w+:\s+(.+?)(?:\s+—|\s*$)", line)
        if not m:
            continue
        for token in m.group(1).split(","):
            p = token.strip()
            if p and not (REPO_ROOT / p).exists():
                missing.append(f"{line.split(':', 1)[0]}: {p}")
    assert not missing, (
        "META_HARNESS.md COMP_* paths missing on disk: " + "; ".join(missing))


# --- 6. R7 T5 token budget pins (F32) ---------------------------------------

AGENTS_BUDGET = 5 * 1024        # rides the system prompt EVERY turn (F33)
WORK_BUDGET = 14 * 1024         # read at every session startup
SCRATCHPAD_BUDGET = 6 * 1024    # T2: CURRENT/RECURRING only
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


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
