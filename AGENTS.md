# AGENTS.md - Agent-X System Agent Rules

* Primary entry point for the system agent opencode. Defines rules, commands, and navigation paths.
* You, the opencode coding agent must use the `Meta Project Harness` to execute any task.
* The `Meta Project Harness` structure is optimized for opencode agent programming tasks and to produce code quality optimal code.
* Each `Meta Project Harness` directory have a META.md file that must be read first to understand it purpose. 
* The `Meta Project Harness` directories name allways start with ´.´ (dot) character.

## Project Meta Directories

* .project_development/
* .experiments/
* .sanbox/
* .test_sandbox/

---

## Core Directives

Non-negotiable rules the system agent must follow at all times.

| # | Directive                       | Details                                                       |
|---|---------------------------------|---------------------------------------------------------------|
| 1 | **NEVER commit or push**        | Despite the user ask you, never commit or push.               |
| 2 | **NEVER add new dependencies**  | Use existing ones. Explicit approval required for exceptions. |
| 3 | **NEVER modify `.env`**         | Or any file likely to contain secrets.                        |
| 4 | **ALWAYS check `git log`**      | Before making any changes.                                    |
| 5 | **NEVER modify `tests/`**       | Use `tests_sandbox/` for new tests (requires approval).       |
| 6 | **Use `uv` & `pyproject.toml`** | For all dependency management. Avoid pin drift.               |

## Quick Reference

| Category | File | Description |
|----------|------|-------------|

---