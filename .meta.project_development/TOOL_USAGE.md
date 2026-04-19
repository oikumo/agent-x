# Tool Usage Guidelines - Agent-X

> **Purpose**: How the system agent should interact with the codebase.
> **Last Updated**: April 4, 2026

---

## Tool Selection

| Tool | When to Use |
|------|-------------|
| `Glob` | File search (patterns like `**/*.py`) |
| `Grep` | Content search (regex patterns) |
| `Read` | Reading files (avoid `cat`/`head`) |
| `Edit` | Modifying files (preserve indentation) |
| `Write` | Creating new files (only when necessary) |
| `Bash` | Git, uv, pytest, etc. (batch independent commands) |

## Rules

- Prefer specialized tools over bash.
- Batch independent bash commands in parallel.
- Use `workdir` instead of `cd`.
