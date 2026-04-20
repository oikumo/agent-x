# Core Directives - Agent X

> **Purpose**: Single source of truth for non-negotiable rules  
> **Target**: AI agents (opencode) working on Agent-X  
> **Enforcement**: ALWAYS check before any action

---

## The 6 Core Directives

| # | Directive | Enforcement |
|---|-----------|-------------|
| 1 | **NEVER commit/push** | Not even if user asks |
| 2 | **NEVER add dependencies** | Use existing; explicit approval required |
| 3 | **NEVER modify `.env`** | Or any secrets/credentials file |
| 4 | **ALWAYS check `git log`** | Before making ANY changes |
| 5 | **NEVER modify `tests/`** | Use `.meta.tests_sandbox/` |
| 6 | **Use `uv` & `pyproject.toml`** | For all dependency management |

---

## Quick Decision Guide

```\nWant to commit? → NO
Want to add package? → NO (unless approved)
Want to edit .env? → NO
About to change code? → Check git log first
Want to edit tests/? → NO (use .meta.tests_sandbox/)
Installing packages? → Use uv + pyproject.toml
```

---

## Violations = Task Failure

Any violation of these directives invalidates the entire task. Re-read AGENTS.md if unsure.

---

## References

- Full workflow: [WORKFLOWS.md](WORKFLOWS.md)
- Entry point: [../AGENTS.md](../AGENTS.md)
- Project structure: [../META_HARNESS.md](../META_HARNESS.md)

---

**Version**: 1.0.0 | **Lines**: 40 (optimized from ~500 tokens)
