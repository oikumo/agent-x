# Coding Style - Agent-X

> **Purpose**: Code style conventions for the project.
> **Last Updated**: April 4, 2026

---

## General

- **Language**: Python 3.14+
- **Line Length**: 88 characters
- **Docstrings**: Google-style for public APIs

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions/variables | `snake_case` | `get_user_name()` |
| Classes | `PascalCase` | `UserManager` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private members | `_prefix` | `_internal_cache` |
| Modules/files | `snake_case.py` | `user_manager.py` |

## Tests

- Mirror source structure in `tests_sandbox/`
- Use `unittest.TestCase` framework
