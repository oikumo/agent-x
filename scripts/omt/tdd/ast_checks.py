"""TDD AST analysis (meta_harness_dsl R3) — stdlib ast helpers.

Extracted from the former monolithic scripts/omt/tdd_check.py:
  - import inference (test file -> agentx source targets)
  - name/reference extraction (true-RED verification)
  - public-method inventory (coverage gaps, snapshots)
  - test summary extraction + RED anti-pattern detection

Spec: .meta/doc/tdd/tdd-agent-spec.md (Kent Beck TDD v5)
"""
from __future__ import annotations

import ast
from pathlib import Path

# Built-in / common names to exclude from "missing references" check.
_BUILTINS = frozenset(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__)) | frozenset({
    "self", "cls", "True", "False", "None", "len", "str", "int", "list", "dict",
    "set", "tuple", "bool", "float", "type", "isinstance", "issubclass", "print",
    "range", "enumerate", "zip", "sorted", "reversed", "open", "Path", "pytest",
    "monkeypatch", "fixture", "mark", "parametrize", "skip", "xfail", "raises",
    "warns", "approx", "tmp_path", "capsys", "capfd", "caplog", "tmpdir",
    "MagicMock", "patch", "mock", "AsyncMock", "Any", "Optional", "Union",
    "dataclass", "field", "ABC", "abstractmethod", "property",
})


def _parse_file(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return None


def infer_target_src(test_file: Path) -> list[str]:
    """Parse test file imports → source file paths under src/."""
    tree = _parse_file(test_file)
    if not tree:
        return []
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("agentx"):
                p = "src/" + node.module.replace(".", "/") + ".py"
                if p not in targets:
                    targets.append(p)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("agentx"):
                    p = "src/" + alias.name.replace(".", "/") + ".py"
                    if p not in targets:
                        targets.append(p)
    return targets


def extract_test_references(test_file: Path, test_name: str) -> set[str]:
    """Find all method calls (ast.Call with ast.Attribute func) in a test function."""
    tree = _parse_file(test_file)
    if not tree:
        return set()
    refs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == test_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    refs.add(child.func.attr)
    return refs


def extract_defined_names(src_file: Path) -> set[str]:
    """Find all class names and public method/function names in source."""
    tree = _parse_file(src_file)
    if not tree:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_"):
                        names.add(item.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
    return names


def extract_public_methods(src_file: Path) -> list[dict]:
    """Extract public methods from a source file (module-level + class methods)."""
    tree = _parse_file(src_file)
    if not tree:
        return []
    methods: list[dict] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("_"):
                        continue
                    is_abstract = any(
                        "abstractmethod" in ast.unparse(d) for d in item.decorator_list
                    )
                    methods.append({
                        "class": node.name, "method": item.name,
                        "line": item.lineno, "is_abstract": is_abstract,
                    })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                methods.append({
                    "class": "", "method": node.name,
                    "line": node.lineno, "is_abstract": False,
                })
    return methods


def find_untested_methods(src_file: Path, test_files: list[Path]) -> list[dict]:
    """Find public methods not referenced by any test file."""
    src_methods = extract_public_methods(src_file)
    if not src_methods:
        return []
    tested_names: set[str] = set()
    for tf in test_files:
        tree = _parse_file(tf)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                tested_names.add(node.attr)
    return [m for m in src_methods if m["method"] not in tested_names]


def verify_true_red(test_file: Path, test_name: str, src_files: list[Path]) -> dict:
    """Check if test references code that doesn't exist in source yet."""
    test_refs = extract_test_references(test_file, test_name)
    all_defined: set[str] = set()
    for sf in src_files:
        all_defined |= extract_defined_names(sf)
    missing = sorted(r for r in test_refs if r not in all_defined and r not in _BUILTINS)
    return {"is_true_red": len(missing) > 0, "missing": missing}


def extract_test_summary(test_file: Path, test_name: str) -> dict:
    """Extract assertions and method calls from a test function."""
    tree = _parse_file(test_file)
    if not tree:
        return {"assertions": [], "calls": []}
    assertions: list[dict] = []
    calls: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == test_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    try:
                        assertions.append({"line": child.lineno, "test": ast.unparse(child.test)})
                    except Exception:
                        assertions.append({"line": child.lineno, "test": "<unparseable>"})
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    try:
                        calls.append({"line": child.lineno, "call": ast.unparse(child.func)})
                    except Exception:
                        pass
    return {"assertions": assertions, "calls": calls}


def detect_red_anti_patterns(test_file: Path) -> list[str]:
    """Detect anti-patterns in a test file during RED state."""
    warnings: list[str] = []
    tree = _parse_file(test_file)
    if not tree:
        return warnings
    test_fns = [n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    if len(test_fns) > 1:
        warnings.append(
            f"batch-N-tests: {len(test_fns)} test functions in file. "
            f"TDD requires 1 test:1 min impl loop. (spec anti-pattern)"
        )
    for fn in test_fns:
        has_assert = any(isinstance(c, ast.Assert) for c in ast.walk(fn))
        if not has_assert:
            for c in ast.walk(fn):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute):
                    if c.func.attr.startswith("assert"):
                        has_assert = True
                        break
        if not has_assert:
            warnings.append(f"test '{fn.name}' has no assertions.")
        parts = fn.name.split("_")
        if len(parts) < 3:
            warnings.append(
                f"test '{fn.name}' doesn't follow test_<subject>_<behavior> naming."
            )
        for dec in fn.decorator_list:
            try:
                dec_str = ast.unparse(dec)
            except Exception:
                dec_str = ""
            if "skip" in dec_str or "xfail" in dec_str:
                warnings.append(
                    f"test '{fn.name}' has skip/xfail — forbidden. (spec anti-pattern)"
                )
    return warnings
