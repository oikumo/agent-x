# Experiments - Agent X

> **Purpose**: Experimental workspace for testing new features/ideas  
> **Target**: AI agents (opencode)  
> **Rule**: Document and integrate or clean up

---

## Purpose

Safe space for:
- Testing new libraries/dependencies
- Prototyping features
- Exploring alternatives
- Validating hypotheses

---

## Structure

```
.meta.experiments/
├── META.md               # This file
└── YYYY-MM-DD-experiment/
    ├── README.md         # Purpose + findings
    └── code/             # Experimental code
```

---

## Lifecycle (5 Steps)

```\n1. CREATE: Clear hypothesis/goal\n2. DOCUMENT: What + why\n3. VALIDATE: Test hypothesis\n4. DECIDE: Integrate / iterate / discard\n5. CLEAN: Remove or archive\n```\n\n---

## Rules

**DO**: Date folders, document findings, clean up, use for TDD prep  
**DON'T**: Leave broken, mix with production, skip documentation

---

## Integration Workflow

```\nSuccess → Document → Test in .meta.tests_sandbox/ → Move to .meta.sandbox/ → Archive
Failure → Document why → Remove
```\n\n---

**Version**: 2.0.0 (lazy-optimized) | **Lines**: 40 (reduced from 153)
