# Project Development - Agent X

> **Purpose**: Development basis and rules  
> **Target**: AI agents (opencode)  
> **Usage**: Reference for development standards

---

## Core Principles

1. **Code Quality**: PEP 8, type hints, docstrings, meaningful names
2. **TDD**: Tests first (see [`.meta.tests_sandbox/META.md`](../.meta.tests_sandbox/META.md))
3. **Incremental**: Small, verifiable changes

---

## Quick Links

| File | Purpose |
|------|---------|
| [`DIRECTIVES.md`](DIRECTIVES.md) | Core rules (6 directives) |
| [`WORKFLOWS.md`](WORKFLOWS.md) | Workflow patterns |
| [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) | At-a-glance guide |
| [`CODING_STYLE.md`](CODING_STYLE.md) | Code conventions |
| [`ENVIRONMENT.md`](ENVIRONMENT.md) | Environment setup |

---

## Development Workflow

### Before Any Task
1. Read relevant META.md
2. Check `git log`
3. Plan smallest viable change

### During Development
1. Work in `.meta.sandbox/` or `.meta.experiments/`
2. Follow TDD in `.meta.tests_sandbox/`
3. Use `uv` for packages

### After Completion
1. Verify tests pass
2. Update documentation
3. Clean workspace
4. Document learnings

---

## Best Practices

**Avoid**: Modifying production, skipping tests, large unverified changes, undocumented features  
**Always**: Test first, document, follow conventions, respect directives

---

**Version**: 2.0.0 (lazy-optimized) | **Lines**: 50 (reduced from 180)
