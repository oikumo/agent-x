#!/usr/bin/env python3
"""OMT++ MVC++ architecture linter.

Implements the layer-violation checks from `omt_agent_guide.md` Section 16
("Common Mistakes to Catch") as a real, runnable check. Standard library only.

Usage:
    uv run scripts/omt/mvc_check.py                 # scan src/agentx
    uv run scripts/omt/mvc_check.py path/to/file.py # scan specific files
    uv run scripts/omt/mvc_check.py --json          # machine-readable (for the plugin)

Exit code:
    0  no ERROR-severity violations (WARNINGs may still be present)
    1  one or more ERROR-severity violations found
    2  bad invocation / file could not be parsed
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# --- Repo roots -------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "agentx"

GOD_CONTROLLER_MAX_LINES = 300

# Severity buckets. ERRORs fail the run (exit 1); WARNINGs are advisory.
ERROR_RULES = {
    "VIEW_IMPORTS_MODEL",
    "MODEL_IMPORTS_UI",
    "CONTROLLER_IN_MODEL",
    "PARTNER_NOT_ABC",
    "VIEW_CREATES_CONTROLLER",
}
WARNING_RULES = {
    "CONTROLLER_UI_CODE",
    "SQL_OUTSIDE_DP",
    "GOD_CONTROLLER",
}

# --- Regexes for source-text checks ----------------------------------------
RE_PRINT = re.compile(r"(?<![\w.])print\s*\(")
RE_CONSOLE = re.compile(r"\bConsole\s*\(|\bconsole\.(print|log)\b|from\s+rich\b|import\s+rich\b")
RE_EXECUTE = re.compile(r"\.execute(many|script)?\s*\(")
# SQL keywords are matched case-sensitively (uppercase) and in their full
# statement shape, so prose like "Select RAG repository" does not match.
RE_SQL = re.compile(r"\b(SELECT\b.+\bFROM|INSERT\s+INTO|DELETE\s+FROM|UPDATE\s+\w+\s+SET|CREATE\s+TABLE)\b")
RE_CTRL_INSTANTIATION = re.compile(r"\b([A-Z]\w*Controller)\s*\(")
# --- feature_059 D2 stack_profiles: TS text-mode --------------------------------
# mvc_ts is a TEXT/REGEX mode over **/*.{ts,tsx} (stdlib-only by design — no TS
# parser; AST rules are skipped, documented in --help). profile=none disables
# the check entirely (exit 0). Default profile comes from @var stack_profile
# when CWD is inside a repo, else mvc_py (backwards compatible).
TS_SUFFIXES = {".ts", ".tsx"}
TS_EXCLUDE_DIRS = {"node_modules", "__pycache__", ".venv", "dist", "build"}
STACK_PROFILES = ("mvc_py", "mvc_ts", "none")

RE_TS_NEW_CONTROLLER = re.compile(r"\bnew\s+([A-Z]\w*Controller)\s*\(")
RE_TS_IMPORT_MODEL = re.compile(r"\bimport\b.*\b[Mm]odel\b")
RE_TS_IMPORT_UI = re.compile(r"\bimport\b.*\bui\b|from\s+['\"][^'\"]*\bui\b")


def _is_ts_view(path: Path) -> bool:
    return "view" in path.name.lower()


def _is_ts_controller(path: Path) -> bool:
    return "controller" in path.name.lower()


def _is_ts_db(path: Path) -> bool:
    return path.name.endswith(("_db.ts", "_db.tsx"))


def _in_ts_model(path: Path) -> bool:
    return "/model/" in path.as_posix()


def _check_ts_file(path: Path, source: str, rel: str) -> list[Finding]:
    """Text-mode MVC rules for TS/TSX (mirrors the Python text rules)."""
    findings: list[Finding] = []
    is_view = _is_ts_view(path)
    is_controller = _is_ts_controller(path)
    is_db = _is_ts_db(path)
    in_model = _in_ts_model(path)
    for i, raw in enumerate(source.splitlines(), start=1):
        line = raw.split("//", 1)[0]  # crude TS comment strip (text-mode)
        if is_view and RE_TS_IMPORT_MODEL.search(line):
            findings.append(Finding(
                "VIEW_IMPORTS_MODEL", "error", rel, i,
                "View imports Model — View must not know about Model. "
                "Move the logic to the Controller.",
            ))
        if in_model and RE_TS_IMPORT_UI.search(line):
            findings.append(Finding(
                "MODEL_IMPORTS_UI", "error", rel, i,
                "Model imports a UI layer — invert the dependency. "
                "Model must be UI-independent.",
            ))
        if not is_db and (RE_EXECUTE.search(line) or RE_SQL.search(line)):
            findings.append(Finding(
                "SQL_OUTSIDE_DP", "warning", rel, i,
                "SQL / .execute() outside a *_db DP class. "
                "Encapsulate all SQL in a DP_* class.",
            ))
        if is_view:
            m = RE_TS_NEW_CONTROLLER.search(line)
            if m:
                findings.append(Finding(
                    "VIEW_CREATES_CONTROLLER", "error", rel, i,
                    f"View instantiates '{m.group(1)}' — Views must receive "
                    "the partner via constructor injection, never create a Controller.",
                ))
        if is_controller and (RE_PRINT.search(line) or RE_CONSOLE.search(line)):
            findings.append(Finding(
                "CONTROLLER_UI_CODE", "warning", rel, i,
                "Controller contains UI code (print/console) — delegate rendering "
                "to the View.",
            ))
    if is_controller:
        nlines = source.count("\n") + 1
        if nlines > GOD_CONTROLLER_MAX_LINES:
            findings.append(Finding(
                "GOD_CONTROLLER", "warning", rel, 1,
                f"Controller is {nlines} lines (> {GOD_CONTROLLER_MAX_LINES}) — "
                "extract sub-controllers.",
            ))
    return findings


def _default_profile() -> str:
    """Repo @var stack_profile when CWD is inside a repo, else mvc_py."""
    cwd = Path.cwd()
    for base in (cwd, *cwd.parents):
        omt = base / ".meta" / "META_HARNESS.omt"
        if omt.exists():
            try:
                text = omt.read_text(encoding="utf-8")
            except OSError:
                return "mvc_py"
            m = re.search(r"^@var\s+stack_profile\s*:\s*(\S+)", text, re.M)
            if m and m.group(1) in STACK_PROFILES:
                return m.group(1)
            return "mvc_py"
    return "mvc_py"


@dataclass
class Finding:
    rule: str
    severity: str          # "error" | "warning"
    file: str              # path relative to repo root
    line: int
    message: str


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _module_segments(node: ast.AST) -> list[str]:
    """Return the dotted segments of an import statement's target module."""
    segs: list[str] = []
    if isinstance(node, ast.ImportFrom):
        if node.module:
            segs.extend(node.module.split("."))
    elif isinstance(node, ast.Import):
        for alias in node.names:
            segs.extend(alias.name.split("."))
    return segs


def _base_names(cls: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for base in cls.bases:
        try:
            names.append(ast.unparse(base))
        except Exception:  # pragma: no cover - defensive
            names.append(getattr(base, "id", ""))
    return names


def check_file(path: Path) -> list[Finding]:
    """Run every applicable MVC++ check against one Python file."""
    findings: list[Finding] = []
    name = path.name
    rel = _rel(path)

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Finding("PARSE_ERROR", "error", rel, 0, f"cannot read: {exc}")]

    if path.suffix in TS_SUFFIXES:
        return _check_ts_file(path, source, rel)

    is_view = name.endswith("_view.py")
    is_controller = name.endswith("_controller.py")
    is_db = name.endswith("_db.py")
    in_model = "/model/" in path.as_posix() or path.as_posix().endswith("/model")

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [Finding("PARSE_ERROR", "error", rel, exc.lineno or 0, f"syntax error: {exc.msg}")]

    # --- AST-based checks (imports, class bases) ---------------------------
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            segs = _module_segments(node)
            if is_view and "model" in segs:
                findings.append(Finding(
                    "VIEW_IMPORTS_MODEL", "error", rel, node.lineno,
                    "View imports Model — View must not know about Model (guide §5). "
                    "Move the logic to the Controller.",
                ))
            if in_model and "ui" in segs:
                findings.append(Finding(
                    "MODEL_IMPORTS_UI", "error", rel, node.lineno,
                    "Model imports a UI layer — invert the dependency (guide §5). "
                    "Model must be UI-independent.",
                ))

        if isinstance(node, ast.ClassDef):
            cname = node.name
            bases = _base_names(node)
            # Abstract Partner interfaces (I*Partner) must be ABCs.
            if re.match(r"^I[A-Z].*Partner$", cname) and not any("ABC" in b for b in bases):
                findings.append(Finding(
                    "PARTNER_NOT_ABC", "error", rel, node.lineno,
                    f"Abstract Partner '{cname}' is not an ABC (guide §6). "
                    "Make it inherit ABC and mark methods @abstractmethod.",
                ))
            # No *Controller classes inside the model layer.
            if in_model and cname.endswith("Controller"):
                findings.append(Finding(
                    "CONTROLLER_IN_MODEL", "error", rel, node.lineno,
                    f"Class '{cname}' lives under model/ (guide §16.9). "
                    "Rename to *Manager or *Service — Controllers belong to ui/.",
                ))

    # --- Text-based checks -------------------------------------------------
    for i, raw in enumerate(source.splitlines(), start=1):
        line = raw.split("#", 1)[0]  # ignore trailing comments for matching

        if is_controller and (RE_PRINT.search(line) or RE_CONSOLE.search(line)):
            findings.append(Finding(
                "CONTROLLER_UI_CODE", "warning", rel, i,
                "Controller contains UI code (print/console) — delegate rendering "
                "to the View (guide §5).",
            ))

        if not is_db and (RE_EXECUTE.search(line) or RE_SQL.search(line)):
            findings.append(Finding(
                "SQL_OUTSIDE_DP", "warning", rel, i,
                "SQL / .execute() outside a *_db.py DP class (guide §9). "
                "Encapsulate all SQL in a DP_* class.",
            ))

        if is_view:
            m = RE_CTRL_INSTANTIATION.search(line)
            if m:
                findings.append(Finding(
                    "VIEW_CREATES_CONTROLLER", "error", rel, i,
                    f"View instantiates '{m.group(1)}' (guide §6) — Views must receive "
                    "the partner via constructor injection, never create a Controller.",
                ))

    # --- Whole-file checks -------------------------------------------------
    if is_controller:
        nlines = source.count("\n") + 1
        if nlines > GOD_CONTROLLER_MAX_LINES:
            findings.append(Finding(
                "GOD_CONTROLLER", "warning", rel, 1,
                f"Controller is {nlines} lines (> {GOD_CONTROLLER_MAX_LINES}) — "
                "extract sub-controllers (guide §16.7).",
            ))

    return findings


def collect_targets(args_paths: list[str],
                      profile: str = "mvc_py") -> list[Path]:
    if profile == "mvc_ts":
        roots = [Path(p) for p in args_paths] if args_paths else [REPO_ROOT]
        out: list[Path] = []
        for root in roots:
            if root.is_dir():
                out.extend(p for p in root.rglob("*")
                         if p.suffix in TS_SUFFIXES and p.is_file()
                         and not (TS_EXCLUDE_DIRS & set(p.parts)))
            elif root.suffix in TS_SUFFIXES:
                out.append(root)
        return sorted(out)
    if args_paths:
        paths: list[Path] = []
        for p in args_paths:
            path = Path(p)
            if path.is_dir():
                paths.extend(sorted(path.rglob("*.py")))
            elif path.suffix == ".py":
                paths.append(path)
        return paths
    return sorted(SRC_ROOT.rglob("*.py"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OMT++ MVC++ architecture linter")
    parser.add_argument("paths", nargs="*", help="files or dirs to check (default: src/agentx)")
    parser.add_argument("--json", action="store_true", help="emit JSON for tooling")
    parser.add_argument("--profile", choices=list(STACK_PROFILES), default=None,
                        help="stack profile (default: repo @var stack_profile, else mvc_py); "
                        "mvc_ts = TS text-mode (no AST); none = disabled, exit 0")
    args = parser.parse_args(argv)

    profile = args.profile or _default_profile()
    if profile == "none":
        print("\u2705 MVC++ disabled (profile=none)")
        if args.json:
            print(json.dumps({"files_scanned": 0, "errors": 0, "warnings": 0, "findings": []}))
        return 0

    targets = [t for t in collect_targets(args.paths, profile) if "__pycache__" not in t.parts]
    findings: list[Finding] = []
    for path in targets:
        findings.extend(check_file(path))

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    if args.json:
        print(json.dumps({
            "files_scanned": len(targets),
            "errors": len(errors),
            "warnings": len(warnings),
            "findings": [asdict(f) for f in findings],
        }, indent=2))
        return 1 if errors else 0

    if not findings:
        print(f"✅ MVC++ clean — {len(targets)} file(s) scanned, no violations.")
        return 0

    def emit(group: list[Finding], header: str) -> None:
        if not group:
            return
        print(f"\n{header} ({len(group)})")
        for f in group:
            print(f"  {f.file}:{f.line}  [{f.rule}] {f.message}")

    emit(errors, "⛔ ERRORS")
    emit(warnings, "⚠️  WARNINGS")
    print(f"\n{len(targets)} file(s) scanned — {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
