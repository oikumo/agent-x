#!/usr/bin/env python3
"""kb_ast_extract — AST skeleton extractor for the Application Knowledge Base.

feature_kb_akb P0 (PROJECT.md v2.1): parses src/agentx/**/*.py via `ast` and
emits skeleton records (3 kinds only: class/contract/dep) in kb.index.jsonl
schema. Concept-altitude: NO module/method records. Coverage = ALL public
classes (no significance filter). Un-curated records get auto-text
(bases + abstractmethods); the curated code.kb.omt overlay overrides text at
build merge time (kb_compiler.py build).

Pass 1 — collect class symbols: name, src, line, bases, abstractmethods,
          __init__ composition candidates, layer.
Pass 2 — emit records:
          contract.<Name>  — ABC base or any @abstractmethod
          class.<Name>     — concrete
          dep.<A>_<B>      — realization (A bases contract B) + composition
                             (self.x = B() / self.x: B in __init__)

Deterministic: files sorted, symbols sorted, refs sorted, records sorted by id.
Duplicate class names: first-by-sorted-path wins + warning.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

ABC_BASES = {"ABC", "ABCMeta"}
MAX_AUTO_TEXT = 280  # headroom under the 300-char style cap


@dataclass
class ClassSymbol:
    """Pass-1 symbol-table entry for one public ClassDef."""

    name: str
    src: str  # repo-relative path
    line: int
    bases: list[str] = field(default_factory=list)  # simple names, as written
    abstractmethods: list[str] = field(default_factory=list)
    compositions: list[tuple[str, int]] = field(default_factory=list)  # (name, line)
    layer: str = "LAYER_MODEL"

    @property
    def is_contract(self) -> bool:
        return bool(self.abstractmethods) or any(b in ABC_BASES for b in self.bases)


# ---------------------------------------------------------------------------
# Layer inference (PROJECT.md v2.1 table — path segments + suffixes)
# ---------------------------------------------------------------------------
def infer_layer(rel_path: str, class_name: str) -> str:
    p = rel_path.replace("\\", "/")
    parts = p.split("/")
    if class_name.startswith("DP_") or "persistence" in parts:
        return "LAYER_DP"
    if "utils" in parts:
        return "LAYER_UTIL"
    if "controller" in parts or "controllers" in parts or p.endswith("_controller.py"):
        return "LAYER_CONTROLLER"
    if (
        {"view", "ui", "screens", "tui"} & set(parts)
        or p.endswith("_view.py")
        or p.endswith("_screen.py")
    ):
        return "LAYER_VIEW"
    return "LAYER_MODEL"  # /model/ + default


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------
def _simple_name(expr: ast.expr) -> str | None:
    """Resolve an expression to a simple class-ish name (Name/Attribute/Subscript)."""
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Subscript):
        return _simple_name(expr.value)
    if isinstance(expr, ast.Call):
        return _simple_name(expr.func)
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value  # string annotation: "Foo"
    return None


def _decorator_name(dec: ast.expr) -> str | None:
    return _simple_name(dec)


def _collect_class(node: ast.ClassDef, src: str) -> ClassSymbol | None:
    """Build a ClassSymbol from a ClassDef; None if private."""
    if node.name.startswith("_"):
        return None
    sym = ClassSymbol(
        name=node.name,
        src=src,
        line=node.lineno,
        layer=infer_layer(src, node.name),
    )
    for base in node.bases:
        name = _simple_name(base)
        if name:
            sym.bases.append(name)

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decs = {_decorator_name(d) for d in item.decorator_list}
            if "abstractmethod" in decs:
                sym.abstractmethods.append(item.name)
            if item.name == "__init__":
                sym.compositions.extend(_collect_compositions(item))
    return sym


def _collect_compositions(init: ast.FunctionDef | ast.AsyncFunctionDef) -> list[tuple[str, int]]:
    """self.x = Foo() / self.x: Foo = ... candidates inside __init__."""
    found: list[tuple[str, int]] = []
    for node in ast.walk(init):
        if isinstance(node, ast.Assign):
            if not any(
                isinstance(t, ast.Attribute)
                and isinstance(t.value, ast.Name)
                and t.value.id == "self"
                for t in node.targets
            ):
                continue
            if isinstance(node.value, ast.Call):
                name = _simple_name(node.value.func)
                if name:
                    found.append((name, node.lineno))
        elif isinstance(node, ast.AnnAssign):
            t = node.target
            if not (
                isinstance(t, ast.Attribute)
                and isinstance(t.value, ast.Name)
                and t.value.id == "self"
            ):
                continue
            if node.value is not None and isinstance(node.value, ast.Call):
                name = _simple_name(node.value.func)
                if name:
                    found.append((name, node.lineno))
            elif node.value is None:
                name = _simple_name(node.annotation)
                if name:
                    found.append((name, node.lineno))
    return found


# ---------------------------------------------------------------------------
# Pass 1 — symbol collection
# ---------------------------------------------------------------------------
def collect_symbols(src_root: Path, repo_root: Path) -> tuple[dict[str, ClassSymbol], list[str]]:
    """Walk src_root/**/*.py; return (symbol table name->ClassSymbol, warnings).

    Duplicate class names: first-by-sorted-path wins; warning recorded.
    """
    symbols: dict[str, ClassSymbol] = {}
    warnings: list[str] = []
    files = sorted(src_root.rglob("*.py"))
    for f in files:
        try:
            rel = f.relative_to(repo_root).as_posix()
        except ValueError:
            rel = f.as_posix()
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as e:
            warnings.append(f"kb_ast_extract: {rel}: parse error: {e}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            sym = _collect_class(node, rel)
            if sym is None:
                continue
            if sym.name in symbols:
                first = symbols[sym.name]
                warnings.append(
                    f"kb_ast_extract: duplicate class '{sym.name}' at {rel}:{node.lineno}"
                    f" — keeping first ({first.src}:{first.line})"
                )
                continue
            symbols[sym.name] = sym
    return symbols, warnings


# ---------------------------------------------------------------------------
# Pass 2 — record emission
# ---------------------------------------------------------------------------
def _rid(sym: ClassSymbol) -> str:
    return f"{'contract' if sym.is_contract else 'class'}.{sym.name}"


def _join_limited(items: list[str], prefix: str) -> str:
    """Render ' a, b, c (+N more)' after prefix, keeping auto-text bounded."""
    if not items:
        return ""
    out = prefix
    for i, it in enumerate(items):
        chunk = ("" if i == 0 else ", ") + it
        if len(out) + len(chunk) > MAX_AUTO_TEXT - 12:
            return out + f" (+{len(items) - i} more)"
        out += chunk
    return out


def _auto_text(sym: ClassSymbol) -> str:
    bases = f"({', '.join(sym.bases)})" if sym.bases else ""
    text = f"{sym.name}{bases}"
    if sym.abstractmethods:
        text += _join_limited(sym.abstractmethods, " abstractmethods: ")
    return text[:MAX_AUTO_TEXT]


def emit_records(symbols: dict[str, ClassSymbol]) -> list[dict]:
    """Emit class/contract/dep records (kb.index.jsonl schema) from symbols."""
    records: list[dict] = []

    for name in sorted(symbols):
        sym = symbols[name]
        kind = "contract" if sym.is_contract else "class"
        tag_prefix = "CONTRACT" if kind == "contract" else "CLASS"

        refs: set[str] = set()
        if kind == "contract":
            # back-edge: every concrete class realizing this contract
            for other in symbols.values():
                if not other.is_contract and name in other.bases:
                    refs.add(f"class.{other.name}")
        else:
            for base in sym.bases:
                if base in symbols:
                    refs.add(_rid(symbols[base]))
            for comp, _line in sym.compositions:
                if comp in symbols:
                    refs.add(_rid(symbols[comp]))

        records.append({
            "id": f"{kind}.{name}",
            "kind": kind,
            "src": sym.src,
            "line": sym.line,
            "tags": [f"{tag_prefix}_{name.upper()}", "TIER_CODE", sym.layer],
            "text": _auto_text(sym),
            "refs": sorted(refs),
            "tier": "code",
        })

    # dep edges: realization (base is a project contract) + composition
    seen_dep: set[str] = set()
    for name in sorted(symbols):
        sym = symbols[name]
        src_rid = _rid(sym)
        for base in sym.bases:
            target = symbols.get(base)
            if target is None or not target.is_contract:
                continue
            dep_id = f"dep.{sym.name}_{base}"
            if dep_id in seen_dep:
                continue
            seen_dep.add(dep_id)
            records.append({
                "id": dep_id,
                "kind": "dep",
                "src": sym.src,
                "line": sym.line,
                "tags": [f"DEP_{sym.name.upper()}_{base.upper()}", "TIER_CODE", sym.layer],
                "text": f"{sym.name} --|> {base} (realization)",
                "refs": [src_rid, _rid(target)],
                "tier": "code",
            })
        for comp, line in sym.compositions:
            target = symbols.get(comp)
            if target is None:
                continue
            dep_id = f"dep.{sym.name}_{comp}"
            if dep_id in seen_dep:
                continue
            seen_dep.add(dep_id)
            records.append({
                "id": dep_id,
                "kind": "dep",
                "src": sym.src,
                "line": line,
                "tags": [f"DEP_{sym.name.upper()}_{comp.upper()}", "TIER_CODE", sym.layer],
                "text": f"{sym.name} --composes--> {comp}",
                "refs": [src_rid, _rid(target)],
                "tier": "code",
            })

    records.sort(key=lambda r: r["id"])
    return records


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------
def extract(src_root: Path, repo_root: Path) -> tuple[list[dict], list[str]]:
    """Extract skeleton records from src_root; return (records, warnings)."""
    symbols, warnings = collect_symbols(Path(src_root), Path(repo_root))
    return emit_records(symbols), warnings
