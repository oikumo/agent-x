# Workflows - Agent X

> **Purpose**: Standardized workflow patterns (lazy reference)  
> **Target**: AI agents (opencode)  
> **Usage**: Reference by workflow type

---

## Workflow Decision Tree

```
Task Type?
├─ New feature     → Workflow A (experiments)
├─ Bug fix         → Workflow B (reproduce & fix)
├─ Refactor        → Workflow C (copy & refactor)
├─ Test library    → Workflow D (isolate & validate)
└─ Maintenance     → Workflow E (health check)
```

---

## Workflow A: New Feature

```
1. Read: META_HARNESS.md + relevant META.md
2. Create: .meta.experiments/<date>-<feature>/
3. Test: .meta.tests_sandbox/ (TDD: RED→GREEN→REFACTOR)
4. Implement: .meta.sandbox/<session>/
5. Validate: All tests pass, no production break
6. Document: Update META.md + session notes
7. Report: Summarize to user
```

**Token tip**: Only read what's needed for current step.

---

## Workflow B: Bug Fix

```
1. Reproduce in .meta.sandbox/
2. Write failing test in .meta.tests_sandbox/
3. Fix in .meta.sandbox/
4. Verify test passes
5. Document fix pattern
6. Report to user
```

---

## Workflow C: Refactoring

```
1. Copy code to .meta.sandbox/
2. Write behavior tests (preserve functionality)
3. Refactor incrementally
4. Verify tests pass
5. Document improvements
6. Report to user
```

---

## Workflow D: Test New Library

```
1. Create: .meta.experiments/<date>-<library>/
2. Document: Hypothesis + success criteria
3. Test: In isolation
4. Validate: Benefits vs cost
5. Document: Findings + recommendation
6. Decide: Integrate or discard
```

---

## Workflow E: Maintenance (Monthly)

```
1. Health check (see: optimize-meta-harness skill)
2. Review all META.md files
3. Update as needed
4. Archive old sessions
5. Document changes
```

---

## Quality Gates (All Workflows)

Before reporting completion:

- [ ] Read relevant META.md
- [ ] Checked `git log`
- [ ] Correct directory used
- [ ] TDD followed (if applicable)
- [ ] Tests pass
- [ ] Documented changes
- [ ] Workspace clean
- [ ] No secrets exposed
- [ ] No production code modified

---

## References

- Core rules: [DIRECTIVES.md](DIRECTIVES.md)
- TDD details: [.meta.tests_sandbox/META.md](../.meta.tests_sandbox/META.md)
- Sandbox rules: [.meta.sandbox/META.md](../.meta.sandbox/META.md)

---

**Version**: 1.0.0 | **Lines**: 100 (optimized from ~800 tokens)
