"""File system tools for the Coding Agent.

These tools provide safe, sandboxed access to the file system for the coding agent.
All paths are resolved relative to a sandbox root directory to prevent escaping.
"""

from __future__ import annotations

import fnmatch
import os
import difflib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from langchain.tools import tool
# TA: xref: NOTE (feature_025): these @tool wrappers return dataclasses; under create_deep_agent the FilesystemMiddleware offloads results exceeding 20k tokens to a StateBackend (pointer + 10-line preview in history). Tool inputs/outputs themselves UNCHANGED — only the in-history representation is compressed.


# ── Data Classes ────────────────────────────────────────────────────────────────

@dataclass
class FileMatch:
    """A single file search match with context."""
    path: str           # Relative to sandbox root
    line: int           # 1-indexed line number
    context: str        # Matching line ±3 context lines


@dataclass
class FileSearchResult:
    """Result of file_search tool."""
    matches: List[FileMatch]
    total: int
    truncated: bool
    error: Optional[str] = None


@dataclass
class FileReadResult:
    """Result of file_read tool."""
    path: str
    content: str
    start_line: int
    end_line: int
    error: Optional[str] = None


@dataclass
class FileEditResult:
    """Result of file_edit or file_create tool."""
    path: str
    success: bool
    diff: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DirectoryEntry:
    """Single directory entry from file_list."""
    name: str
    is_dir: bool
    size: int
    mtime: datetime
    path: str           # Relative to sandbox root
    error: Optional[str] = None


# ── Sandbox Root Management ────────────────────────────────────────────────────

_sandbox_root: Optional[Path] = None


def set_sandbox_root(root: Path | str) -> None:
    """Set the sandbox root directory for all file tools."""
    global _sandbox_root
    _sandbox_root = Path(root).resolve()


def get_sandbox_root() -> Path:
    """Get the current sandbox root."""
    if _sandbox_root is None:
        return Path.cwd().resolve()
    return _sandbox_root


def _resolve_safe_path(path: str) -> Path:
    """Resolve a path relative to sandbox root, ensuring it doesn't escape."""
    sandbox = get_sandbox_root()
    target = (sandbox / path).resolve()

    try:
        target.relative_to(sandbox)
    except ValueError:
        raise ValueError(f"Path escapes sandbox: {path}")

    return target


# ── Core Tool Implementations (used by tests and @tool wrappers) ──────────────

def _file_search_impl(pattern: str, path: str = ".") -> FileSearchResult:
    """Search for files matching a glob pattern within the sandbox.

    Args:
        pattern: Glob pattern (e.g., "**/*.py", "src/**/test_*.py")
        path: Relative path from sandbox root to search in (default: ".")

    Returns:
        FileSearchResult with matches (path, line, context), total count, truncated flag.
    """
    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return FileSearchResult([], 0, False, error=str(e))

    if not target.exists() or not target.is_dir():
        return FileSearchResult([], 0, False, error="Not a directory")

    matches = []
    try:
        for file_path in target.rglob(pattern):
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.splitlines()

                # Return first match (line 1) with context
                # For file search, we just indicate the file matches
                if lines:
                    rel_path = file_path.relative_to(get_sandbox_root())
                    matches.append(FileMatch(
                        path=str(rel_path),
                        line=1,
                        context="\n".join(lines[:5])  # First 5 lines as context
                    ))

                    if len(matches) >= 100:
                        break
            except Exception:
                pass  # Skip unreadable files

    except Exception as e:
        return FileSearchResult([], 0, False, error=str(e))

    return FileSearchResult(
        matches=matches,
        total=len(matches),
        truncated=len(matches) >= 100
    )


def _file_read_impl(path: str, start: int = 1, end: int = -1) -> FileReadResult:
    """Read a file from the sandbox with optional line range.

    Args:
        path: Relative path from sandbox root
        start: 1-indexed start line (default: 1)
        end: 1-indexed end line inclusive (default: -1 = EOF)

    Returns:
        FileReadResult with content, line range, or error.
    """
    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return FileReadResult(path, "", 0, 0, error=str(e))

    if not target.exists():
        return FileReadResult(path, "", 0, 0, error="File not found")

    if not target.is_file():
        return FileReadResult(path, "", 0, 0, error="Not a file")

    try:
        content = target.read_text(encoding="utf-8")
        lines = content.splitlines()
        total_lines = len(lines)

        start_idx = max(0, start - 1)
        end_idx = total_lines if end == -1 else min(total_lines, end)

        selected = lines[start_idx:end_idx]
        return FileReadResult(
            path=path,
            content="\n".join(selected),
            start_line=start_idx + 1,
            end_line=end_idx
        )
    except Exception as e:
        return FileReadResult(path, "", 0, 0, error=str(e))


def _file_edit_impl(path: str, old_str: str, new_str: str) -> FileEditResult:
    """Make a precise edit to a file. old_str must match exactly once.

    Args:
        path: Relative path from sandbox root
        old_str: Exact text to replace (must be unique in file)
        new_str: Replacement text

    Returns:
        FileEditResult with success, unified diff, or error.
    """
    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return FileEditResult(path, False, error=str(e))

    if not target.exists():
        return FileEditResult(path, False, error="File not found")

    if not target.is_file():
        return FileEditResult(path, False, error="Not a file")

    try:
        content = target.read_text(encoding="utf-8")

        # Count occurrences
        count = content.count(old_str)
        if count == 0:
            return FileEditResult(path, False, error="old_str not found in file")
        if count > 1:
            return FileEditResult(path, False, error="old_str matches multiple locations; be more specific")

        new_content = content.replace(old_str, new_str, 1)

        # Atomic write via temp file
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_text(new_content, encoding="utf-8")
        temp.replace(target)

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            content.splitlines(), new_content.splitlines(),
            fromfile=f"a/{path}", tofile=f"b/{path}", lineterm=""
        ))
        diff = "\n".join(diff_lines)

        return FileEditResult(path, True, diff=diff)
    except Exception as e:
        return FileEditResult(path, False, error=str(e))


def _file_list_impl(path: str = ".", recursive: bool = False) -> List[DirectoryEntry]:
    """List directory contents within the sandbox.

    Args:
        path: Relative path from sandbox root (default: ".")
        recursive: Whether to recurse into subdirectories

    Returns:
        List of DirectoryEntry (name, is_dir, size, mtime, relative_path).
    """
    entries = []

    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return [DirectoryEntry("", False, 0, datetime.min, "", error=str(e))]

    if not target.exists() or not target.is_dir():
        return [DirectoryEntry("", False, 0, datetime.min, "", error="Not a directory")]

    try:
        if recursive:
            for root, dirs, files in os.walk(target):
                root_path = Path(root)
                for d in dirs:
                    p = root_path / d
                    try:
                        rel = p.relative_to(get_sandbox_root())
                        stat = p.stat()
                        entries.append(DirectoryEntry(
                            name=d,
                            is_dir=True,
                            size=stat.st_size,
                            mtime=datetime.fromtimestamp(stat.st_mtime),
                            path=str(rel)
                        ))
                    except Exception:
                        pass
                for f in files:
                    p = root_path / f
                    try:
                        rel = p.relative_to(get_sandbox_root())
                        stat = p.stat()
                        entries.append(DirectoryEntry(
                            name=f,
                            is_dir=False,
                            size=stat.st_size,
                            mtime=datetime.fromtimestamp(stat.st_mtime),
                            path=str(rel)
                        ))
                    except Exception:
                        pass
        else:
            for p in target.iterdir():
                try:
                    rel = p.relative_to(get_sandbox_root())
                    stat = p.stat()
                    entries.append(DirectoryEntry(
                        name=p.name,
                        is_dir=p.is_dir(),
                        size=stat.st_size,
                        mtime=datetime.fromtimestamp(stat.st_mtime),
                        path=str(rel)
                    ))
                except Exception:
                    pass
    except Exception as e:
        entries.append(DirectoryEntry("", False, 0, datetime.min, "", error=str(e)))

    return entries


def _file_create_impl(path: str, content: str) -> FileEditResult:
    """Create a new file in the sandbox.

    Args:
        path: Relative path from sandbox root
        content: File content

    Returns:
        FileEditResult with success and diff (new file).
    """
    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return FileEditResult(path, False, error=str(e))

    if target.exists():
        return FileEditResult(path, False, error="File already exists; use file_edit")

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        # Generate diff for new file
        lines = content.splitlines()
        diff_lines = [f"--- /dev/null", f"+++ b/{path}", f"@@ -0,0 +1,{len(lines)} @@"]
        diff_lines.extend(f"+{line}" for line in lines)
        diff = "\n".join(diff_lines)

        return FileEditResult(path, True, diff=diff)
    except Exception as e:
        return FileEditResult(path, False, error=str(e))


# ── @tool Decorated Versions (for langchain agent) ────────────────────────────

@tool
def file_search(pattern: str, path: str = ".") -> FileSearchResult:
    """Search for files matching a glob pattern within the sandbox.

    Args:
        pattern: Glob pattern (e.g., "**/*.py", "src/**/test_*.py")
        path: Relative path from sandbox root to search in (default: ".")

    Returns:
        FileSearchResult with matches (path, line, context), total count, truncated flag.
    """
    return _file_search_impl(pattern, path)


@tool
def file_read(path: str, start: int = 1, end: int = -1) -> FileReadResult:
    """Read a file from the sandbox with optional line range.

    Args:
        path: Relative path from sandbox root
        start: 1-indexed start line (default: 1)
        end: 1-indexed end line inclusive (default: -1 = EOF)

    Returns:
        FileReadResult with content, line range, or error.
    """
    return _file_read_impl(path, start, end)


@tool
def file_edit(path: str, old_str: str, new_str: str) -> FileEditResult:
    """Make a precise edit to a file. old_str must match exactly once.

    Args:
        path: Relative path from sandbox root
        old_str: Exact text to replace (must be unique in file)
        new_str: Replacement text

    Returns:
        FileEditResult with success, unified diff, or error.
    """
    return _file_edit_impl(path, old_str, new_str)


@tool
def file_list(path: str = ".", recursive: bool = False) -> List[DirectoryEntry]:
    """List directory contents within the sandbox.

    Args:
        path: Relative path from sandbox root (default: ".")
        recursive: Whether to recurse into subdirectories

    Returns:
        List of DirectoryEntry (name, is_dir, size, mtime, relative_path).
    """
    return _file_list_impl(path, recursive)


@tool
def file_create(path: str, content: str) -> FileEditResult:
    """Create a new file in the sandbox.

    Args:
        path: Relative path from sandbox root
        content: File content

    Returns:
        FileEditResult with success and diff (new file).
    """
    return _file_create_impl(path, content)


# ── Exports ────────────────────────────────────────────────────────────────────

# Core implementations (for tests and direct use)
__all__ = [
    "FileMatch",
    "FileSearchResult",
    "FileReadResult",
    "FileEditResult",
    "DirectoryEntry",
    "set_sandbox_root",
    "get_sandbox_root",
    "file_search",
    "file_read",
    "file_edit",
    "file_list",
    "file_create",
    # Core implementations
    "_file_search_impl",
    "_file_read_impl",
    "_file_edit_impl",
    "_file_list_impl",
    "_file_create_impl",
    # @tool decorated versions (for langchain)
]

# Registry of @tool decorated functions for langchain
CODING_TOOLS = [file_search, file_read, file_edit, file_list, file_create]