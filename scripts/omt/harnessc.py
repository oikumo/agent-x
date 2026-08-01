#!/usr/bin/env python3
"""harnessc — OMT-HDL compiler (meta_harness_dsl R8; plan Appendix D).

Single source: .meta/META_HARNESS.omt → projections:
  1. .meta/.omt/harness.ir.json   (plugins load once at init; HDL-1: data only)
  2. AGENTS.md                    (GENERATED — never hand-edit)
  3. .meta/.omt/nav.index.jsonl   (.omt records + scraped legacy app-doc tags)
  4. opencode.jsonc               (between // harnessc:begin/end read|bash|perm)
  5. .meta/.omt/harness.report    (sizes vs budgets — Appendix C self-maintaining)

Subcommands:
  check                       kind schema · id uniq · ref closure · pred vocab
                              · comp paths · hat/fsm agreement · budgets
  check --verify-projections  + committed projections == recompiled (drift test)
  build                       check, then write all projections + report

Stdlib-only by design (no deps approval). Grammar: plan Appendix D1 —
record := '@' kind SP id (SP attr)* (SP ' : ' payload)? ; attr := k=v | k="v v".
"""
from __future__ import annotations

import json
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OMT_REL = ".meta/META_HARNESS.omt"
OMT_PATH = REPO_ROOT / OMT_REL
IR_PATH = REPO_ROOT / ".meta" / ".omt" / "harness.ir.json"
NAV_PATH = REPO_ROOT / ".meta" / ".omt" / "nav.index.jsonl"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
CONFIG_PATH = REPO_ROOT / "opencode.jsonc"
REPORT_PATH = REPO_ROOT / ".meta" / ".omt" / "harness.report"
WORK_PATH = REPO_ROOT / "WORK.md"

KINDS = ("version", "var", "deny", "protect", "always", "phase", "fsm", "hat",
         "pred", "gate", "msg", "state", "inject", "doc", "budget", "tool",
         "flow", "xref")

SCHEMA: dict[str, dict[str, set[str]]] = {
    "version": {"req": {"n"}},
    "var":     {"req": set()},
    "deny":    {"req": {"scope", "match", "msg"}},
    "protect": {"req": {"path", "hard", "msg"}},
    "always":  {"req": set()},
    "phase":   {"req": {"applies", "requires"}},
    "fsm":     {"req": {"states", "initial"}},
    "hat":     {"req": {"allow"}},
    "pred":    {"req": set()},
    "gate":    {"req": {"on", "tools", "when", "msg", "hard", "skip_ok", "order"}},
    "msg":     {"req": {"sev"}},
    "state":   {"req": {"path", "mode"}},
    "inject":  {"req": {"on", "budget"}},
    "doc":     {"req": {"tags"}},
    "budget":  {"req": {"max"}},
    "tool":    {"req": {"perm", "args", "tags"}},
    "flow":    {"req": {"tags"}},
    "xref":    {"req": {"tags"}},
}

PREDS = {"path_in", "cmd_match", "ledger_has", "session_flag", "file_has",
         "receipt_fresh", "fsm_allows", "risk_high"}

TT_SET = {"bug_fix", "minor_feature", "major_feature", "new_screen",
          "refactor", "test", "docs"}

RID_RE = re.compile(r"[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$")
REF_RE = re.compile(r"@([a-z][a-z0-9_]*)(\.[a-z0-9_]+(\.[a-z0-9_]+)*|\.\*)?")
PRED_CALL_RE = re.compile(r"!?\b([a-z_][a-z0-9_]*)\s*\(")

# App docs still carrying legacy markdown nav tags (SECTION:/XREF_/…). The
# harness corpus itself is .omt-sourced — META_HARNESS.md (stub) and the
# GENERATED AGENTS.md are deliberately NOT scraped.
LEGACY_SCRAPE_FIXED = [
    ".meta/META.md",
    ".meta/software_development_process/META.md",
    ".meta/software_development_process/omt_agent_guide.md",
    "WORK.md",
]
LEGACY_SCRAPE_GLOB = ".meta/doc/omt++/*.md"

LEGACY_TAG_RES = [
    ("SECTION", re.compile(r"^#+\s*(SECTION:\S+)")),
    ("RULE", re.compile(r"^(RULE_[A-Z0-9]+):")),
    ("ERR", re.compile(r"^(ERR_[A-Z0-9]+):")),
    ("WRN", re.compile(r"^(WRN_[A-Z0-9]+):")),
    ("CMD", re.compile(r"^(CMD_[A-Z0-9]+):")),
    ("QUICK", re.compile(r"^(QUICK_[A-Z0-9_]+):")),
    ("XREF", re.compile(r"^(XREF_[A-Z0-9_]+):")),
    ("TT", re.compile(r"^(TT_[A-Z0-9_]+):")),
    ("PHASE", re.compile(r"^(PHASE_[A-Z0-9_]+):")),
    ("FEAT", re.compile(r"^(FEAT_[A-Z0-9_]+):")),
]

# Hard before-gates rendered in the AGENTS.md NEVER section. g.protect/g.nav
# are excluded (protect renders via @protect; nav is a search gate, not an
# edit-never). check() errors if a hard before-gate on edit tools is unlisted.
GATE_NEVER = {
    "g.receipt": "harness-surface 2nd edit w/o fresh e2e receipt",
    "g.tests": "`tests/` w/o canary approval",
    "g.phase": "`src/` w/o `omt_phase`",
    "g.think": "TA:-carrying files w/o `omt_think_list` consult",
}
GATE_NEVER_EXCLUDE = {"g.protect", "g.nav"}

# Doc records the AGENTS.md projection draws from (missing id = build error).
AGENTS_QUICK_FLOWS = ["start_bug", "start_major", "skip_src", "status", "lint"]

MEASURABLE_BUDGETS = {"agents_md", "work_md", "work_scratchpad", "tool_schemas",
                        "nav_index", "ir_json"}  # OPT-D: the two largest projections
REPORT_ONLY_BUDGETS = {"nav_tip", "digest_cap"}  # TS-rendered; test-pinned (R7 T5)


@dataclass
class Record:
    kind: str
    rid: str
    attrs: dict[str, str]
    payload: str
    line: int

    @property
    def full_id(self) -> str:
        return f"{self.kind}.{self.rid}"


@dataclass
class Corpus:
    records: list[Record]
    errors: list[str] = field(default_factory=list)

    def of(self, kind: str) -> list[Record]:
        return [r for r in self.records if r.kind == kind]

    def get(self, kind: str, rid: str) -> Record | None:
        for r in self.records:
            if r.kind == kind and r.rid == rid:
                return r
        return None


def split_payload(rest: str) -> tuple[str, str]:
    """Split attrs from payload at the first ' : ' outside double quotes."""
    in_q = False
    for i, c in enumerate(rest):
        if c == '"':
            in_q = not in_q
        elif not in_q and rest.startswith(" : ", i):
            return rest[:i], rest[i + 3:]
    return rest, ""


def parse(text: str, errors: list[str]) -> list[Record]:
    records: list[Record] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"@([a-z]+)\s+(\S+)(.*)$", line)
        if not m:
            errors.append(f"{OMT_REL}:{lineno}: malformed record line: {raw.strip()[:60]}")
            continue
        kind, rid, rest = m.group(1), m.group(2), m.group(3)
        if kind not in KINDS:
            errors.append(f"{OMT_REL}:{lineno}: unknown kind '@{kind}' (closed vocabulary: {', '.join(KINDS)})")
            continue
        if not RID_RE.match(rid):
            errors.append(f"{OMT_REL}:{lineno}: bad id '{rid}' (want {RID_RE.pattern})")
            continue
        attr_src, payload = split_payload(rest)
        attrs: dict[str, str] = {}
        try:
            tokens = shlex.split(attr_src, posix=True)
        except ValueError as e:
            errors.append(f"{OMT_REL}:{lineno}: attr parse: {e}")
            continue
        for tok in tokens:
            if "=" not in tok:
                errors.append(f"{OMT_REL}:{lineno}: attr '{tok}' is not k=v")
                continue
            k, v = tok.split("=", 1)
            attrs[k] = v
        records.append(Record(kind, rid, attrs, payload, lineno))
    return records


# --- check -------------------------------------------------------------------


# --- derive (improvement006/OPT-D) ---------------------------------------------
# Projection-time expansion of mechanically-derivable nav records so the .omt
# carries each fact ONCE: PHASE_* from @fsm phase states, TT_* from the closed
# task-type set, SECTION from framed banner comments ("# ====" / "# TITLE — text").
BANNER_RE = re.compile(r"^# ([A-Z][A-Z0-9_ +]+) — (.+)$")
BANNER_FRAME_RE = re.compile(r"^# ={10,}$")


def derive_records(c: Corpus, omt_text: str) -> None:
    """Append derived @doc records (ph.*/tt.*/sec.*) to the corpus. Hand-written
    copies were deleted (OPT-D); a hand record re-added under a derived id is a
    duplicate-id build error via check_ids."""
    fsm = c.get("fsm", "phase")
    decl = next((r for r in c.of("phase") if r.attrs.get("requires") == "decl"), None)
    if fsm:
        for s in (x.strip() for x in fsm.attrs.get("states", "").split(",") if x.strip()):
            c.records.append(Record("doc", f"ph.{s.lower()}",
                                    {"tags": f"PHASE_{s.upper()}"}, s, fsm.line))
    for tt in sorted(TT_SET):
        c.records.append(Record("doc", f"tt.{tt}", {"tags": f"TT_{tt.upper()}"},
                                tt, decl.line if decl else (fsm.line if fsm else 0)))
    lines = omt_text.splitlines()
    for i, raw in enumerate(lines):
        m = BANNER_RE.match(raw.strip())
        if m and i > 0 and BANNER_FRAME_RE.match(lines[i - 1].strip()):
            title, text = m.group(1).strip(), m.group(2).strip()
            rid = "sec." + title.lower().replace(" ", "_").replace("+", "")
            c.records.append(Record("doc", rid, {"tags": "SECTION"},
                                    f"{title} — {text}", i + 1))

def check_schema(c: Corpus) -> None:
    for r in c.records:
        spec = SCHEMA[r.kind]
        missing = spec["req"] - set(r.attrs)
        if missing:
            c.errors.append(f"{OMT_REL}:{r.line}: @{r.kind} {r.rid}: missing attrs {sorted(missing)}")
        if r.kind == "always" and not ({"run", "glob"} & set(r.attrs)):
            c.errors.append(f"{OMT_REL}:{r.line}: @always {r.rid}: needs run= or glob=")
        if r.kind == "deny" and r.attrs.get("scope") not in ("bash", "read", "toplevel"):
            c.errors.append(f"{OMT_REL}:{r.line}: @deny {r.rid}: scope must be bash|read|toplevel")
        if r.kind == "msg" and r.attrs.get("sev") not in ("block", "warn", "info"):
            c.errors.append(f"{OMT_REL}:{r.line}: @msg {r.rid}: sev must be block|warn|info")
        if r.kind == "state" and r.attrs.get("mode") not in ("append", "rotate", "rewrite"):
            c.errors.append(f"{OMT_REL}:{r.line}: @state {r.rid}: mode must be append|rotate|rewrite")
        if r.kind == "tool" and r.attrs.get("perm") not in ("allow", "ask", "deny"):
            c.errors.append(f"{OMT_REL}:{r.line}: @tool {r.rid}: perm must be allow|ask|deny")
        if r.kind in ("protect", "gate"):
            for a in ("hard", "skip_ok"):
                if a in r.attrs and r.attrs[a] not in ("true", "false"):
                    c.errors.append(f"{OMT_REL}:{r.line}: @{r.kind} {r.rid}: {a} must be true|false")
        if r.kind == "gate":
            if not re.match(r"^(before|after|event:.+)$", r.attrs.get("on", "")):
                c.errors.append(f"{OMT_REL}:{r.line}: @gate {r.rid}: on must be before|after|event:<name>")
            if not r.attrs.get("order", "").isdigit():
                c.errors.append(f"{OMT_REL}:{r.line}: @gate {r.rid}: order must be an integer")
        if r.kind in ("budget", "inject"):
            a = "max" if r.kind == "budget" else "budget"
            if not r.attrs.get(a, "").isdigit():
                c.errors.append(f"{OMT_REL}:{r.line}: @{r.kind} {r.rid}: {a} must be an integer")


def check_ids(c: Corpus) -> None:
    seen: dict[str, int] = {}
    for r in c.records:
        if r.full_id in seen:
            c.errors.append(f"{OMT_REL}:{r.line}: duplicate id {r.full_id} (first at line {seen[r.full_id]})")
        seen[r.full_id] = r.line


def check_refs(c: Corpus) -> None:
    ids = {r.full_id for r in c.records}
    kinds_with_records = {r.kind for r in c.records}
    for r in c.records:
        haystacks = list(r.attrs.values()) + ([r.payload] if r.payload else [])
        for hay in haystacks:
            for m in REF_RE.finditer(hay):
                kind, sub = m.group(1), m.group(2)
                if kind not in KINDS:
                    c.errors.append(f"{OMT_REL}:{r.line}: {r.full_id}: ref to unknown kind '@{kind}'")
                    continue
                if not sub:
                    if kind not in kinds_with_records:
                        c.errors.append(f"{OMT_REL}:{r.line}: {r.full_id}: bare ref '@{kind}' has no records")
                    continue
                if sub == ".*":
                    if kind not in kinds_with_records:
                        c.errors.append(f"{OMT_REL}:{r.line}: {r.full_id}: wildcard ref '@{kind}.*' has no records")
                    continue
                if f"{kind}{sub}" not in ids:
                    c.errors.append(f"{OMT_REL}:{r.line}: {r.full_id}: unresolved ref '@{kind}{sub}'")


def check_preds(c: Corpus) -> None:
    for r in c.of("pred"):
        m = PRED_CALL_RE.match(r.payload)
        if not m or m.group(1) not in PREDS:
            c.errors.append(f"{OMT_REL}:{r.line}: @pred {r.rid}: payload must start with a closed-vocabulary builtin {sorted(PREDS)}")
    for r in c.of("gate"):
        for attr in ("when", "requires"):
            for m in PRED_CALL_RE.finditer(r.attrs.get(attr, "")):
                if m.group(1) not in PREDS:
                    c.errors.append(f"{OMT_REL}:{r.line}: @gate {r.rid}: {attr}= uses unknown pred '{m.group(1)}'")


def check_fsm_hats(c: Corpus) -> None:
    fsm = c.get("fsm", "tdd")
    if fsm:
        states = {s.strip().lower() for s in fsm.attrs.get("states", "").split(",")}
        for r in c.of("hat"):
            if "." in r.rid:
                fs, st = r.rid.split(".", 1)
                if fs == "tdd" and st not in states:
                    c.errors.append(f"{OMT_REL}:{r.line}: @hat {r.rid}: state '{st}' not in @fsm tdd states")
    for r in c.of("phase"):
        for tt in r.attrs.get("applies", "").split(","):
            if tt.strip() and tt.strip() not in TT_SET:
                c.errors.append(f"{OMT_REL}:{r.line}: @phase {r.rid}: unknown task_type '{tt.strip()}'")
    # improvement006/OPT-D: tt.* records are derived from TT_SET at projection
    # time; a hand-written subset (override attempt) is an error, absence is fine.
    tt_docs = {r.rid.split(".", 1)[1] for r in c.of("doc") if r.rid.startswith("tt.")}
    if tt_docs and tt_docs != TT_SET:
        c.errors.append(f"{OMT_REL}: @doc tt.* records {sorted(tt_docs)} != task-type set {sorted(TT_SET)} (tt.* is derived — do not hand-write a subset)")


def check_comp_paths(c: Corpus) -> None:
    for r in c.of("doc"):
        if not r.rid.startswith("comp."):
            continue
        first_seg = r.payload.split(" — ")[0]
        for tok in re.split(r"[,+]", first_seg):
            p = tok.strip().split(" ")[0].rstrip("/")
            if p and not (REPO_ROOT / p).exists():
                c.errors.append(f"{OMT_REL}:{r.line}: @doc {r.rid}: path '{p}' missing on disk")


def check_gate_never_coverage(c: Corpus) -> None:
    for r in c.of("gate"):
        if r.attrs.get("on") == "before" and r.attrs.get("hard") == "true" \
                and "edit" in r.attrs.get("tools", ""):
            if r.rid not in GATE_NEVER and r.rid not in GATE_NEVER_EXCLUDE:
                c.errors.append(f"{OMT_REL}:{r.line}: @gate {r.rid}: hard before-edit gate lacks a GATE_NEVER phrase (or exclusion)")



# improvement006/OPT-G: repo-root hygiene. Stray root files (probe leftovers like
# ta_digest_*.py, 2026-07-19) confuse agents; .meta/.omt *.bak contradicts the
# append-only state model (R6 S1). Allowlist is data (@var root_allowlist).
ROOT_VOLATILE = {".git", ".venv", ".idea", ".pytest_cache", ".ruff_cache",
                 ".mypy_cache", "local_sessions", "test_sandbox", ".sandbox"}


def check_root_hygiene(c: Corpus) -> None:
    r = c.get("var", "root_allowlist")
    if r is None:
        c.errors.append(f"{OMT_REL}: @var root_allowlist missing (OPT-G hygiene gate needs it)")
        return
    allowed = {e.strip().rstrip("/") for e in r.payload.split(",") if e.strip()}
    for entry in sorted(REPO_ROOT.iterdir()):
        name = entry.name
        if name in ROOT_VOLATILE or name == ".env" or name.startswith(".env."):
            continue
        if name not in allowed:
            c.errors.append(f"repo root: '{name}' not in @var root_allowlist "
                            "(stray hygiene — delete it or list it deliberately)")
    omt_dir = REPO_ROOT / ".meta" / ".omt"
    if omt_dir.is_dir():
        baks = sorted(p.name for p in omt_dir.glob("*.bak"))
        if baks:
            c.errors.append(f".meta/.omt: stale *.bak files {baks} — state is append-only (R6 S1); delete")


def check_work_done_max(c: Corpus) -> None:
    """improvement006/OPT-B: WORK.md DONE rotation backstop — pending + last-5
    DONE inline (CONV_WORK_ROTATE); older rotate to WORK_ARCHIVE.md."""
    r = c.get("var", "work_done_max")
    if r is None or not r.payload.isdigit() or not WORK_PATH.exists():
        return
    done = sum(1 for line in WORK_PATH.read_text(encoding="utf-8").splitlines()
               if line.startswith("- [x]"))
    if done > int(r.payload):
        c.errors.append(f"WORK.md: {done} DONE entries > @var work_done_max={r.payload} "
                        "— rotate older DONE to WORK_ARCHIVE.md (CONV_WORK_ROTATE)")


# improvement006/OPT-C: the TS irToolDescription(name, seed) fallback seeds must
# mirror the .omt @tool payloads EXACTLY (single source; seed = IR-missing
# fallback only). Drift (e.g. omt_phase pre-006) = build error here.
TOOL_SEED_DIRS = (".opencode/plugins", ".opencode/lib/enforcer")


def _ts_seed(src: str, name: str) -> str | None:
    m = re.search(rf'irToolDescription\(\s*"{re.escape(name)}"\s*,', src)
    if not m:
        return None
    i, depth, in_s, esc = m.end(), 1, False, False
    while i < len(src) and depth:
        ch = src[i]
        if in_s:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_s = False
        elif ch == '"':
            in_s = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        i += 1
    lits = re.findall(r'"((?:[^"\\]|\\.)*)"', src[m.end():i - 1], re.DOTALL)
    if not lits:
        return None
    return "".join(lits).replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def check_tool_seed_sync(c: Corpus) -> None:
    srcs = [p for d in TOOL_SEED_DIRS for p in sorted((REPO_ROOT / d).glob("*.ts"))]
    texts = [p.read_text(encoding="utf-8") for p in srcs]
    for r in c.of("tool"):
        seed = None
        for text in texts:
            seed = _ts_seed(text, r.rid)
            if seed is not None:
                break
        if seed is None:
            c.errors.append(f"{OMT_REL}:{r.line}: @tool {r.rid}: no irToolDescription call site in {TOOL_SEED_DIRS}")
        elif seed != r.payload:
            c.errors.append(f"{OMT_REL}:{r.line}: @tool {r.rid}: TS fallback seed drifted from the .omt payload "
                            f"(seed {len(seed)} B vs payload {len(r.payload)} B) — sync the seed to the single source")

# --- projections ---------------------------------------------------------------

def render_agents(c: Corpus) -> str:
    docs = {r.rid: r.payload for r in c.of("doc")}
    flows = {r.rid: r.payload for r in c.of("flow")}
    for need in ("startup", "runtime", "enforcement", "nav.enforcement",
                 "think.021", "think.gate_not_skip"):
        if need not in docs:
            raise SystemExit(f"harnessc: error: @doc {need} missing (AGENTS.md projection needs it)")
    for need in AGENTS_QUICK_FLOWS:
        if need not in flows:
            raise SystemExit(f"harnessc: error: @flow {need} missing (AGENTS.md quickref needs it)")

    n_tools = len(c.of("tool"))

    deny = c.of("deny")
    bash = " ".join(f"`{r.attrs['match']}`" for r in deny if r.attrs["scope"] == "bash")
    read = " ".join(f"`{r.attrs['match']}`" for r in deny if r.attrs["scope"] == "read")
    toplevel = " ".join(f"`{r.attrs['match']}`" for r in deny if r.attrs["scope"] == "toplevel")
    prot_hard = " ".join(f"`{r.attrs['path']}`" for r in c.of("protect") if r.attrs["hard"] == "true")
    prot_soft = " ".join(f"`{r.attrs['path']}`" for r in c.of("protect") if r.attrs["hard"] == "false")
    gate_phrases = [GATE_NEVER[r.rid] for r in sorted(c.of("gate"), key=lambda r: int(r.attrs["order"]))
                    if r.rid in GATE_NEVER]

    always_parts = []
    for r in c.of("always"):
        always_parts.append(f"`{r.attrs['run']}`" if "run" in r.attrs else f"`{r.attrs['glob']}` per dir")
    always_line = " → ".join(always_parts)

    decl = next((r for r in c.of("phase") if r.attrs["requires"] == "decl"), None)
    design = next((r for r in c.of("phase") if r.attrs["requires"] == "decl,design"), None)
    if decl is None or design is None:
        raise SystemExit("harnessc: error: @phase decl/decl,design records required for AGENTS.md projection")
    decl_tts = " ".join(f"`{t.strip()}`" for t in decl.attrs["applies"].split(","))
    design_tts = " ".join(f"`{t.strip()}`" for t in design.attrs["applies"].split(","))

    fsm = c.get("fsm", "tdd")
    if fsm is None:
        raise SystemExit("harnessc: error: @fsm tdd record required for AGENTS.md projection")
    states = [s.strip().lower() for s in fsm.attrs["states"].split(",")]
    if c.get("tool", "omt_tdd") is not None:
        cycle = "omt_tdd{op: " + " → ".join(states) + "}"  # OPT-H: namespaced tool
    else:
        cycle = " → ".join(f"omt_{s}" for s in states)

    # improvement004/OPT-A: §12 table / TDD / Tools / NAV / THINK / QuickRef sections
    # collapsed to nav-pointer one-liners (~1100 B/turn saved); full rules stay
    # nav-indexed in the .omt corpus (RULE_/NAV_/THINK_/QUICK_ records).
    return f"""# AGENTS.md — System Rules

> GENERATED from .meta/META_HARNESS.omt — DO NOT EDIT; edit the source, then `uv run scripts/omt/harnessc.py build`.

> **STARTUP:** {docs['startup']}
> **RUNTIME:** {docs['runtime']}

## Enforcement
**ENF:** {docs['enforcement']}

## NEVER (blocked by gate)
- bash deny: {bash}
- read deny: {read}; toplevel deny: {toplevel}
- protected: {prot_hard} (hard — no override) · {prot_soft} (`omt_skip{{scope:"all"}}` only)
- edit gates: {" · ".join(gate_phrases)}

## ALWAYS
{always_line}

## Process (full rules on demand via nav)
- **§12 artifacts:** {decl_tts} → declaration only · {design_tts} → + design doc on disk (`new_feature.py`) · `docs` → none
- **TDD (feature_016):** `major_feature`/`new_screen` @Programming auto-activates `{cycle}` — two-hats: RED tests/ only · GREEN/REFACTOR src/ only (auto-revert on break)
- **Tools:** {n_tools} `omt_*` — catalog `omt_nav{{query:"CMD_", tag_type:"CMD"}}` · workflows `omt_quick_ref`
- **Nav gate (feature_020):** nav tools before grep/glob on docs (read + src/non-doc exempt) · **Think gate (feature_021):** TA: files need `omt_think{{op:list}}` consult (NOT skip-bypassable)
"""


def harness_path_entries(c: Corpus) -> list[str]:
    """@var harness_paths comma entries (empty-safe)."""
    r = c.get("var", "harness_paths")
    return [] if r is None else [e.strip() for e in r.payload.split(",") if e.strip()]


def harness_path_lists(c: Corpus) -> dict[str, list[str]]:
    """Classify @var harness_paths entries: an existing FILE is an exact match,
    anything else a prefix (`.opencode/plugins/omt_` never exists on disk).
    Entries matching NOTHING on disk are compile errors — check_harness_paths."""
    lists: dict[str, list[str]] = {"exact": [], "prefix": []}
    for e in harness_path_entries(c):
        lists["exact" if (REPO_ROOT / e).is_file() else "prefix"].append(e)
    return lists


def build_ir(c: Corpus) -> dict:
    vars_: dict[str, object] = {}
    for r in c.of("var"):
        v = r.payload
        vars_[r.rid] = int(v) if v.isdigit() else v

    def resolve(val: str) -> object:
        m = re.fullmatch(r"@var\.([a-z0-9_]+)", val or "")
        return vars_.get(m.group(1), val) if m else val

    ver = c.of("version")
    if not ver or not ver[0].attrs.get("n", "").isdigit():
        raise SystemExit(
            "harnessc: error: @version record with integer n= is required "
            "(the IR projection carries version=n)")
    return {
        "version": int(ver[0].attrs["n"]),
        "generated_from": OMT_REL,
        "vars": vars_,
        "harness_paths": harness_path_lists(c),
        "deny": [{"id": r.rid, "scope": r.attrs["scope"], "match": r.attrs["match"],
                  "msg": r.attrs["msg"].removeprefix("@msg.")} for r in c.of("deny")],
        "protect": [{"id": r.rid, "path": r.attrs["path"], "hard": r.attrs["hard"] == "true",
                     "msg": r.attrs["msg"].removeprefix("@msg.")} for r in c.of("protect")],
        "phases": [{"id": r.rid, "applies": r.attrs["applies"], "requires": r.attrs["requires"]}
                   for r in c.of("phase")],
        "fsm": {r.rid: {"states": r.attrs["states"], "initial": r.attrs["initial"],
                        **({"transitions": r.attrs["transitions"]} if "transitions" in r.attrs else {}),
                        **({"auto_on": r.attrs["auto_on"]} if "auto_on" in r.attrs else {})}
                for r in c.of("fsm")},
        "hats": {r.rid: {"allow": r.attrs["allow"], "revert_on": r.attrs.get("revert_on", "")}
                 for r in c.of("hat")},
        "preds": [r.payload.split("(")[0].lstrip("!") for r in c.of("pred")],
        "gates": [{"id": r.rid, "on": r.attrs["on"], "tools": resolve(r.attrs["tools"]),
                   "paths": resolve(r.attrs.get("paths", "")), "when": r.attrs["when"],
                   "requires": r.attrs.get("requires", ""),
                   "msg": r.attrs["msg"].removeprefix("@msg."),
                   "hard": r.attrs["hard"] == "true", "skip_ok": r.attrs["skip_ok"] == "true",
                   "order": int(r.attrs["order"]),
                   **({"run": resolve(r.attrs["run"])} if "run" in r.attrs else {}),
                   "text": r.payload} for r in c.of("gate")],
        "msgs": {r.rid: {"sev": r.attrs["sev"], "see": r.attrs.get("see", ""), "text": r.payload}
                 for r in c.of("msg")},
        "state": {r.rid: {"path": resolve(r.attrs["path"]), "mode": r.attrs["mode"],
                          **({"cap": int(r.attrs["cap"])} if "cap" in r.attrs else {}),
                          **({"window": int(r.attrs["window"])} if "window" in r.attrs else {}),
                          "truth": r.attrs.get("truth", "")} for r in c.of("state")},
        "injects": [{"id": r.rid, "on": r.attrs["on"], "budget": int(r.attrs["budget"]),
                     "text": r.payload} for r in c.of("inject")],
        "budgets": {r.rid: int(r.attrs["max"]) for r in c.of("budget")},
        "tools": {r.rid: {"perm": r.attrs["perm"], "args": r.attrs["args"],
                          "tags": r.attrs["tags"], "description": r.payload}
                  for r in c.of("tool")},
    }


def render_nav_index(c: Corpus) -> str:
    out: list[dict] = []
    for r in c.records:
        if r.kind in ("doc", "flow", "xref", "tool"):
            tags = [t.strip() for t in r.attrs.get("tags", "").split(",") if t.strip()]
            out.append({"id": r.full_id, "kind": r.kind, "tags": tags, "text": r.payload,
                        "src": OMT_REL, "line": r.line})
        elif r.kind == "msg":
            tag = r.rid.upper()
            if tag.startswith(("ERR_", "WRN_")):
                out.append({"id": r.full_id, "kind": "msg", "tags": [tag], "text": r.payload,
                            "src": OMT_REL, "line": r.line})
    legacy_files = [f for f in LEGACY_SCRAPE_FIXED if (REPO_ROOT / f).exists()]
    legacy_files += sorted(str(p.relative_to(REPO_ROOT))
                           for p in REPO_ROOT.glob(LEGACY_SCRAPE_GLOB))
    for rel in legacy_files:
        for lineno, line in enumerate((REPO_ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
            for tag, rx in LEGACY_TAG_RES:
                m = rx.match(line)
                if m:
                    out.append({"id": f"legacy:{rel}:{lineno}", "kind": "legacy",
                                "tags": [tag], "name": m.group(1), "text": line.strip(),
                                "src": rel, "line": lineno})
                    break
    return "".join(json.dumps(o, sort_keys=True) + "\n" for o in out)


def config_blocks(c: Corpus) -> dict[str, list[str]]:
    deny = c.of("deny")
    blocks: dict[str, list[str]] = {}
    for name, scope in (("read", "read"), ("bash", "bash")):
        entries = [f'{json.dumps(r.attrs["match"])}: "deny"' for r in deny if r.attrs["scope"] == scope]
        blocks[name] = entries
    perm = [f'{json.dumps(r.attrs["match"])}: "deny"' for r in deny if r.attrs["scope"] == "toplevel"]
    perm += [f'{json.dumps(r.rid)}: "{r.attrs["perm"]}"' for r in c.of("tool")]
    blocks["perm"] = perm
    return blocks


def splice_config(text: str, blocks: dict[str, list[str]]) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    found: set[str] = set()
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)// harnessc:begin (\w+)\s*$", line)
        if not m:
            out.append(line)
            i += 1
            continue
        indent, name = m.group(1), m.group(2)
        if name not in blocks:
            raise SystemExit(f"harnessc: error: opencode.jsonc has unknown harnessc block '{name}'")
        out.append(line)
        j = i + 1
        while j < len(lines) and not re.match(rf"^\s*// harnessc:end {name}\s*$", lines[j]):
            j += 1
        if j >= len(lines):
            raise SystemExit(f"harnessc: error: opencode.jsonc block '{name}' has no end marker")
        entry_indent = indent + "  "
        out.extend(entry_indent + e + ("," if k < len(blocks[name]) - 1 else "")
                   for k, e in enumerate(blocks[name]))
        out.append(lines[j])
        found.add(name)
        i = j + 1
    missing = set(blocks) - found
    if missing:
        raise SystemExit(f"harnessc: error: opencode.jsonc missing harnessc blocks: {sorted(missing)}")
    return "\n".join(out)


# --- budgets -------------------------------------------------------------------

def measure_budgets(c: Corpus, agents_md: str, nav_text: str = "", ir_text: str = "") -> dict[str, tuple[int, int | None]]:
    sizes: dict[str, tuple[int, int | None]] = {}
    budgets = {r.rid: int(r.attrs["max"]) for r in c.of("budget")}
    for rid in budgets:
        if rid not in MEASURABLE_BUDGETS | REPORT_ONLY_BUDGETS:
            c.errors.append(f"{OMT_REL}: @budget {rid}: unknown budget id (closed set: {sorted(MEASURABLE_BUDGETS | REPORT_ONLY_BUDGETS)})")
    sizes["agents_md"] = (len(agents_md.encode("utf-8")), budgets.get("agents_md"))
    sizes["tool_schemas"] = (sum(len(r.payload.encode("utf-8")) for r in c.of("tool")),
                             budgets.get("tool_schemas"))
    work_size = WORK_PATH.stat().st_size if WORK_PATH.exists() else 0
    sizes["work_md"] = (work_size, budgets.get("work_md"))
    scratch = 0
    if WORK_PATH.exists():
        parts = WORK_PATH.read_text(encoding="utf-8").split("## Agent Scratchpad", 1)
        if len(parts) == 2:
            scratch = len(("## Agent Scratchpad" + parts[1]).encode("utf-8"))
    sizes["work_scratchpad"] = (scratch, budgets.get("work_scratchpad"))
    sizes["nav_index"] = (len(nav_text.encode("utf-8")), budgets.get("nav_index"))
    sizes["ir_json"] = (len(ir_text.encode("utf-8")), budgets.get("ir_json"))
    for rid in REPORT_ONLY_BUDGETS:
        if rid in budgets:
            sizes[rid] = (-1, budgets[rid])  # TS-rendered; pinned by tests (R7 T5)
    return sizes


def check_harness_paths(c: Corpus) -> None:
    """Every @var harness_paths entry must match >=1 real repo path — the
    compile-time BUG-B pin: a renamed dir leaves a stale prefix that silently
    un-guards files (the TS-side source pin covers the fallback literal)."""
    r = c.get("var", "harness_paths")
    if r is None:
        return  # ref closure already reports the missing var
    for e in harness_path_entries(c):
        p = REPO_ROOT / e
        if p.exists() or any(REPO_ROOT.glob(e + "*")) \
                or any(REPO_ROOT.glob(e.rstrip("/") + "/*")):
            continue
        c.errors.append(f"{OMT_REL}:{r.line}: @var harness_paths: entry '{e}' "
                        "matches no real repo path (stale guard)")


def run_all_checks(c: Corpus, agents_md: str, nav_text: str = "", ir_text: str = "") -> dict[str, tuple[int, int | None]]:
    check_schema(c)
    check_ids(c)
    check_refs(c)
    check_preds(c)
    check_fsm_hats(c)
    check_comp_paths(c)
    check_gate_never_coverage(c)
    check_harness_paths(c)
    check_root_hygiene(c)
    check_work_done_max(c)
    check_tool_seed_sync(c)
    sizes = measure_budgets(c, agents_md, nav_text, ir_text)
    for rid, (size, cap) in sizes.items():
        if size >= 0 and cap is not None and size > cap:
            c.errors.append(f"budget {rid}: {size} B > {cap} B (grow the budget deliberately in the same .omt edit)")
    return sizes


# --- main ----------------------------------------------------------------------

def main(argv: list[str]) -> int:
    args = argv[1:]
    cmd = args[0] if args and not args[0].startswith("-") else "check"
    if cmd not in ("check", "build"):
        print(__doc__)
        return 2
    if not OMT_PATH.exists():
        print(f"harnessc: error: {OMT_REL} not found", file=sys.stderr)
        return 1

    omt_text = OMT_PATH.read_text(encoding="utf-8")
    c = Corpus(parse(omt_text, []))
    derive_records(c, omt_text)
    agents_md = render_agents(c)
    ir_text = json.dumps(build_ir(c), indent=2, sort_keys=True) + "\n"
    nav_text = render_nav_index(c)
    config_text = splice_config(CONFIG_PATH.read_text(encoding="utf-8"), config_blocks(c))
    sizes = run_all_checks(c, agents_md, nav_text, ir_text)

    if "--verify-projections" in args:
        for label, path, text in (("harness.ir.json", IR_PATH, ir_text),
                                  ("nav.index.jsonl", NAV_PATH, nav_text),
                                  ("AGENTS.md", AGENTS_PATH, agents_md),
                                  ("opencode.jsonc", CONFIG_PATH, config_text)):
            if not path.exists():
                c.errors.append(f"projection {label} missing on disk — run harnessc.py build")
            elif path.read_text(encoding="utf-8") != text:
                c.errors.append(f"projection {label} is stale — run harnessc.py build (the .omt is the source)")

    if c.errors:
        for e in c.errors:
            print(f"harnessc: error: {e}", file=sys.stderr)
        return 1

    if cmd == "build":
        IR_PATH.parent.mkdir(parents=True, exist_ok=True)
        IR_PATH.write_text(ir_text, encoding="utf-8")
        NAV_PATH.write_text(nav_text, encoding="utf-8")
        AGENTS_PATH.write_text(agents_md, encoding="utf-8")
        CONFIG_PATH.write_text(config_text, encoding="utf-8")
        report = ["# harnessc report — projection sizes vs budgets (Appendix C self-maintaining)"]
        report.append(f"projection harness.ir.json: {len(ir_text.encode())} B")
        report.append(f"projection nav.index.jsonl: {len(nav_text.encode())} B ({nav_text.count(chr(10))} records)")
        report.append(f"projection AGENTS.md: {sizes['agents_md'][0]} B")
        for rid, (size, cap) in sorted(sizes.items()):
            state = "n/a (TS-pinned)" if size < 0 else ("OK" if cap is None or size <= cap else "OVER")
            report.append(f"budget {rid}: {size if size >= 0 else '-'}/{cap} {state}")
        REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report[1:]))
        print(f"harnessc: build OK — {len(c.records)} records → 5 projections")
    else:
        for rid, (size, cap) in sorted(sizes.items()):
            state = "n/a" if size < 0 else ("OK" if cap is None or size <= cap else "OVER")
            print(f"budget {rid}: {size if size >= 0 else '-'}/{cap} {state}")
        print(f"harnessc: check OK — {len(c.records)} records, 0 errors")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
