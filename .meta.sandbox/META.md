# Sandbox - Agent X

> **Purpose**: Safe workspace for AI agents to test, modify, and experiment with code
> **Target**: AI agents (opencode) working on Agent-X
> **MANDATORY**: NEVER modify production code without going through the sandbox first

---

## Core Philosophy

The sandbox is a **safe space** for AI agents to:
- Test code changes before production
- Experiment with different implementations
- Validate fixes and features
- Run potentially risky operations

---

## Structure

```
.sandbox/
├── META.md              # This file
├── .agent/              # Agent-specific configurations
├── .user/               # User-specific configurations
└── <session>/           # Session-specific workspaces
    ├── src/             # Copied source for modification
    ├── tests/           # Test files
    └── notes.md         # Session notes
```

---

## Rules for AI Agents

### DO
- Work in the sandbox before touching production code
- Document all changes made in the sandbox
- Test thoroughly before proposing changes to production
- Clean up sandbox sessions when done
- Use sandbox for all code modifications

### DON'T
- Modify production code directly
- Leave sandbox in a messy state
- Skip testing in sandbox before production
- Assume sandbox code is production-ready

---

## Workflow

1. **Copy**: Duplicate relevant production code to sandbox
2. **Modify**: Make changes in the sandbox
3. **Test**: Validate changes work as expected
4. **Document**: Record what was changed and why
5. **Propose**: Present changes for review/integration

---

## Session Management

Each sandbox session should:
- Have a clear purpose
- Be time-boxed or task-boxed
- Include documentation of changes
- Be cleaned up after use

---
