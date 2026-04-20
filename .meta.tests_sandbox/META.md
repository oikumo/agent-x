# Testing Sandbox - Agent X

> **Purpose**: TDD strategy (Kent Beck)  
> **Target**: AI agents (opencode)  
> **Mandatory**: NEVER call cloud LLM - use mocks

---

## Core Philosophy

TDD is about **design**, **confidence**, and **incremental progress** — not just testing.

---

## Three Laws of TDD

1. **No production code** until you have a failing test
2. **No more test** than sufficient to fail
3. **No more production code** than sufficient to pass the failing test

---

## Red-Green-Refactor Cycle

```\nRED    → Write small failing test\n  ↓\nGREEN  → Make it pass (fast, even if ugly)\n  ↓\nREFACTOR → Clean up (no behavior changes)\n  ↓\nREPEAT\n```\n\n### RED Phase
- Smallest test for one behavior
- Test should fail for right reason
- Name after behavior, not method\n\n### GREEN Phase
- Make it pass FAST
- No design thinking
- Fake it (return constants)\n\n### REFACTOR Phase
- Remove duplication
- Improve names\n- Never change behavior\n\n---

## Key Patterns\n\n### Fake It\n```python\n# Return constant first, then generalize\ndef run(self, args):\n    return CommandResultPrint(\"5\")  # Fake\n    # Then implement properly after triangulation\n```\n\n### Triangulation\nWrite multiple tests with different values before generalizing.\n\n### One Assert Per Concept\nTest one behavior. Split if you need \"and\" in test name.\n\n---

## AI Agent Workflow\n\n```\n1. Understand requirement\n2. Identify smallest test\n3. Write failing test → RED\n4. Make it pass → GREEN  \n5. Refactor\n6. Repeat\n```\n\n---

## Structure\n\n```\n.meta.tests_sandbox/\n├── META.md              # This file\n├── features/            # Integration tests\n│   └── test_<feature>.py\n└── test_<module>.py     # Unit tests\n```\n\n---

## Rules\n\n**DO**: Simplest test first, run frequently, keep isolated, name by behavior  \n**DON'T**: Skip RED, write multiple tests, test private methods, leave failures\n\n---

## Commands\n\n```bash\nuv run pytest .tests_sandbox/ -v           # All tests\nuv run pytest .tests_sandbox/test_x.py -v  # Specific file\nuv run pytest -k \"pattern\" -v              # By pattern\n```\n\n---

**Version**: 2.0.0 (lazy-optimized) | **Lines**: 90 (reduced from 260, ~65% savings)\n\n**Full TDD guide**: See Kent Beck's *Test Driven Development: By Example*
