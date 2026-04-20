# Sandbox - Agent X

> **Purpose**: Safe workspace for code modifications  
> **Target**: AI agents (opencode)  
> **Rule #1**: NEVER modify production code directly

---

## Core Philosophy

Safe space to:
- Test code changes before production
- Experiment with implementations
- Validate fixes and features
- Run risky operations

---

## Structure

```
.meta.sandbox/
├── META.md           # This file
├── .agent/           # Agent configs
├── .user/            # User configs
└── <session>/        # Session workspace
    ├── src/          # Copied source
    ├── tests/        # Test files
    └── notes.md      # Session notes
```

---

## Workflow

```\n1. COPY: Duplicate production code to sandbox\n2. MODIFY: Make changes safely\n3. TEST: Validate in .meta.tests_sandbox/\n4. DOCUMENT: Record changes in notes.md\n5. PROPOSE: Present for review\n```\n\n---

## Rules

**DO**: Work in sandbox, document changes, test thoroughly, clean up  
**DON'T**: Modify production, leave messy, skip testing, assume production-ready

---

## Session Management

Each session must:
- Have clear purpose
- Be time-boxed or task-boxed
- Include documentation
- Be cleaned after use

---

**Version**: 2.0.0 (lazy-optimized) | **Lines**: 50 (reduced from 69)
