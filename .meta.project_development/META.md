# Project Development - Agent X

> **Purpose**: Define the basis to project software development, with Agent helpers and rules
> **Target**: AI agents (opencode) working on Agent-X
> **MANDATORY**: Consider this ALLWAYS before making any action

---

## Core Development Principles

### 1. Code Quality First
- Follow PEP 8 style guidelines
- Write self-documenting code
- Keep functions small and focused
- Use meaningful names

### 2. Test-Driven Development
- Always write tests first (see `.tests_sandbox/META.md`)
- Never modify production code without tests
- Maintain high test coverage
- Use the Red-Green-Refactor cycle

### 3. Incremental Progress
- Make small, verifiable changes
- Commit frequently (when allowed)
- Document all changes
- Review before implementing

---

## Development Workflow

### Before Any Task
1. Read relevant META.md files
2. Understand the current state via `git log`
3. Check existing tests and documentation
4. Plan the smallest viable change

### During Development
1. Work in `.sandbox/` or `.experiments/`
2. Follow TDD in `.tests_sandbox/`
3. Use `uv` for all package management
4. Never modify `.env` or commit secrets

### After Completion
1. Verify all tests pass
2. Update documentation if needed
3. Clean up sandbox/experiment files
4. Document what was learned

---

## File Structure

```
.project_development/
├── META.md                 # This file
├── CODING_STYLE.md         # Coding conventions
├── ENVIRONMENT.md          # Environment setup
├── PROJECT_TASKS.md        # Current tasks
├── ROUTES.md              # API/command routes
├── TASK_WORKFLOW.md        # Task workflow guide
└── TOOL_USAGE.md          # Tool usage guidelines
```

---

## Coding Standards

See `CODING_STYLE.md` for detailed coding standards.

Key points:
- Python 3.14+
- Type hints required
- Docstrings for public APIs
- Follow existing patterns

---

## Environment Setup

See `ENVIRONMENT.md` for environment configuration.

Key requirements:
- Python 3.14+
- `uv` package manager
- Virtual environment (`.venv/`)
- Proper `.env` configuration

---

## Task Management

See `TASK_WORKFLOW.md` for task workflow details.

Process:
1. Understand the requirement
2. Plan the approach
3. Implement in sandbox
4. Test thoroughly
5. Document changes

---

## Tool Usage

See `TOOL_USAGE.md` for available tools and their usage.

Categories:
- Development tools
- Testing tools
- Debugging tools
- Automation tools

---

## Routes and Commands

See `ROUTES.md` for command documentation.

Key commands:
- All REPL commands
- Utility functions
- API endpoints

---

## Best Practices

### Code Organization
- Keep related code together
- Follow the project structure
- Use meaningful module names
- Avoid circular imports

### Documentation
- Document public APIs
- Keep README updated
- Use docstrings
- Add inline comments for complex logic

### Testing
- Test in `.tests_sandbox/`
- Follow TDD principles
- Test edge cases
- Maintain test coverage

### Version Control
- Check git log before changes
- Write clear commit messages (when allowed)
- Keep commits atomic
- Never commit secrets

---

## Common Pitfalls

### Avoid
- Modifying production code directly
- Skipping tests
- Large, unverified changes
- Undocumented features
- Breaking existing functionality

### Always
- Test before proposing changes
- Document what you do
- Follow project conventions
- Respect the core directives

---

## Getting Help

1. Check existing META.md files
2. Review similar code in the project
3. Consult README.md
4. Use sandbox for experimentation

---
