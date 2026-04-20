# META_HARNESS.md - Master Guide

> **Purpose**: Master guide for Meta Project Harness  
> **Target**: AI agents (opencode)  
> **MANDATORY**: Read before any task

## What is Meta Project Harness?

Structured project organization for AI-assisted development:
- **Clear separation** - Production, experiments, testing
- **Safe spaces** - Work without affecting production
- **Structured workflows** - Consistent output
- **Documentation** - Comprehensive at every level

## Core Directives

| # | Directive | Details |
|---|-----------|---------|
| 1 | **NEVER commit/push** | Despite user ask |
| 2 | **NEVER add dependencies** | Use existing, explicit approval |
| 3 | **NEVER modify `.env`** | Or secrets |
| 4 | **ALWAYS check `git log`** | Before changes |
| 5 | **NEVER modify `tests/`** | Use `.tests_sandbox/` |
| 6 | **Use `uv` & `pyproject.toml`** | Package management |

## Directory Structure
```
agent-x/
├── .project_development/  # Development guidelines
│   ├── META.md
│   ├── CODING_STYLE.md
│   ├── ENVIRONMENT.md
│   └── TASK_WORKFLOW.md
├── .experiments/          # Experimental workspace
│   └── META.md
├── .sandbox/              # Safe modification space
│   └── META.md
├── .tests_sandbox/        # TDD workspace
│   └── META.md
└── .development_tools/    # Development utilities
    └── META.md
```

**All meta directories start with `.`** and contain `META.md`.

## When to Use Each

| Directory | Use When |
|-----------|----------|
| `.project_development/` | Understand rules, check standards, document |
| `.experiments/` | Test libraries, prototype, validate hypotheses |
| `.sandbox/` | Modify code safely, test changes, multi-step tasks |
| `.tests_sandbox/` | Write tests (TDD), test features, validate fixes |
| `.development_tools/` | Create/use MCP tools, scripts, automation |

## Standard Workflow

### 1. Understand Task
```
1.1 Read task requirements
1.2 Check git log
1.3 Review META.md files
1.4 Identify directory
```

### 2. Plan Approach
```
2.1 New features → .experiments/ or .tests_sandbox/
2.2 Modifications → .sandbox/
2.3 Tests → .tests_sandbox/
2.4 Tools → .development_tools/
```

### 3. Execute
```
3.1 Create session folder
3.2 Document plan
3.3 Work incrementally
3.4 Test frequently
3.5 Document findings
```

### 4. Validate
```
4.1 Run tests
4.2 Verify no breakage
4.3 Check requirements
4.4 Document results
```

### 5. Report
```
5.1 Summarize changes
5.2 Show test results
5.3 Explain next steps
5.4 Clean workspace
```

## Documentation Standards

### META.md Files
Every directory must have META.md with:
- Purpose statement
- Target audience
- Mandatory rules
- Structure overview
- Usage guidelines
- Examples

### Session Documentation
- Dated folders
- Purpose and goals
- What was tried
- Successes and failures
- Next steps

### Code Documentation
- Docstrings for public APIs
- Inline comments for complex logic
- Follow existing style
- Keep updated

## Quality Gates

### Code Quality
- [ ] PEP 8 style
- [ ] Type hints
- [ ] Docstrings
- [ ] No linting errors

### Testing
- [ ] Tests in `.tests_sandbox/`
- [ ] All tests pass
- [ ] Edge cases covered
- [ ] TDD followed

### Documentation
- [ ] META.md updated
- [ ] Changes documented
- [ ] README updated
- [ ] Clear commit messages

### Safety
- [ ] No secrets exposed
- [ ] No direct production changes
- [ ] Tests validate changes
- [ ] Rollback plan ready

## Common Scenarios

### Scenario 1: Add Feature
```
1. META_HARNESS.md
2. .experiments/
3. .tests_sandbox/
4. .sandbox/
5. Validate & document
6. Report
```

### Scenario 2: Fix Bug
```
1. Reproduce in .sandbox/
2. Test in .tests_sandbox/
3. Fix in .sandbox/
4. Verify
5. Document
6. Report
```

### Scenario 3: Refactor
```
1. Copy to .sandbox/
2. Write tests
3. Refactor
4. Verify tests pass
5. Document
6. Report
```

### Scenario 4: Test Library
```
1. Create experiment
2. Document hypothesis
3. Test in isolation
4. Validate benefits
5. Document findings
6. Recommend
```

## AI Agent Responsibilities

### MUST
- Read META.md first
- Work in appropriate directories
- Follow TDD
- Document changes
- Test thoroughly
- Respect directives
- Never commit without permission
- Never modify `.env`
- Use `uv`
- Check git log

### SHOULD
- Proactive documentation
- Suggest improvements
- Keep clean workspace
- Share learnings
- Follow Kent Beck TDD
- Use incremental approach
- Validate before proposing

### MUST NOT
- Modify production directly
- Skip testing
- Work outside harness
- Ignore META.md
- Leave messy workspace
- Commit without permission
- Add dependencies unapproved

## Maintenance

### Regular Tasks
- Clean old experiments
- Archive completed sessions
- Update META.md files
- Remove unused tools
- Consolidate learnings

### Housekeeping
- Keep structure clean
- Remove temp files
- Update documentation
- Archive old sessions
- Maintain test coverage

## Getting Started Checklist

- [ ] Read AGENTS.md
- [ ] Read relevant META.md
- [ ] Check git log
- [ ] Identify directory
- [ ] Create session folder
- [ ] Document plan
- [ ] Follow workflow
- [ ] Test thoroughly
- [ ] Document results
- [ ] Clean workspace

## Resources
- **AGENTS.md**: Entry point
- **README.md**: Project overview
- **pyproject.toml**: Configuration
- **.tests_sandbox/META.md**: TDD strategy
- **.project_development/**: Guidelines

---

**Version**: 1.0.0  
**Last Updated**: 2026-04-19  
**Maintained By**: opencode AI agent
