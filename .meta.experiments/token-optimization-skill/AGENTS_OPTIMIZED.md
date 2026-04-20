# AGENTS.md - Agent Rules

> **READ FIRST** - Your rules for working on Agent-X

## ⚠️ Core Directives

| # | Rule | Meaning |
|---|------|---------|
| 1 | **NEVER commit/push** | No exceptions |
| 2 | **NEVER add dependencies** | Use existing |
| 3 | **NEVER modify `.env`** | No secrets |
| 4 | **ALWAYS check `git log`** | Before changes |
| 5 | **NEVER modify `tests/`** | Use `.meta.tests_sandbox/` |
| 6 | **Use `uv` & `pyproject.toml`** | Package management |

## Meta Project Harness

Structured development system for AI agents:
- **Safe spaces** - Work without affecting production
- **Clear workflows** - Consistent output
- **Documentation** - At every level
- **Quality gates** - Ensure correctness

### Directory Structure
```
agent-x/
├── META_HARNESS.md      # Master guide
├── AGENTS.md            # This file
├── .meta.project_development/  # Standards
├── .meta.sandbox/       # Safe workspace
├── .meta.experiments/   # Experiments
├── .meta.tests_sandbox/ # TDD
└── .meta.development_tools/ # Tools
```

## Workflow

### Before Task
1. **Check `git log`** → Context
2. **Read META.md** → Rules
3. **Identify directory** → Where to work

### During Task
4. **Plan** → Smallest change
5. **Execute in safe space** → Never production
6. **Test (TDD)** → Red-Green-Refactor

### After Task
7. **Document** → Update META.md
8. **Report** → Results, next steps

## Decision Tree
```
Need to...
├─ Modify code? → .meta.sandbox/
├─ Write tests? → .meta.tests_sandbox/
├─ Test idea? → .meta.experiments/
└─ Use tools? → .meta.development_tools/
```

## Quality Gates
- [ ] Read META.md files
- [ ] Checked git log
- [ ] Correct directory
- [ ] TDD (if applicable)
- [ ] Tests pass
- [ ] Documented
- [ ] Clean workspace
- [ ] No secrets exposed

## Tools
`read`, `glob`, `bash`, `edit`, `write`, `task`

## Common Scenarios

### Add Feature
```
1. META_HARNESS.md
2. .meta.experiments/
3. .meta.tests_sandbox/
4. .meta.sandbox/
5. Validate & document
```

### Fix Bug
```
1. git log
2. Reproduce in .meta.sandbox/
3. Test in .meta.tests_sandbox/
4. Fix in .meta.sandbox/
5. Document
```

### Refactor
```
1. Copy to .meta.sandbox/
2. Write tests
3. Refactor
4. Verify tests pass
5. Document
```

## When Stuck
1. Stop
2. Re-read META.md
3. Check `.meta.sandbox/.user/`
4. Ask user

## Resources
| Resource | Purpose |
|----------|---------|
| `META_HARNESS.md` | Master docs |
| `.meta.project_development/META.md` | Standards |
| `.meta.sandbox/META.md` | Workspace rules |
| `.meta.tests_sandbox/META.md` | TDD (Kent Beck) |

---

> **READ META.md FIRST**  
> **WORK IN SAFE SPACES**  
> **TEST BEFORE PROPOSING**  
> **DOCUMENT EVERYTHING**  
> **NEVER COMMIT WITHOUT PERMISSION**

**Version**: 1.1.0 (2026-04-19)
