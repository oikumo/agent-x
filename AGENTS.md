# AGENTS.md - Agent-X System Agent Rules

> **Your primary entry point. Read this FIRST before any task.**

This file defines the mandatory rules and workflows for AI agents (opencode) working on Agent-X. You **MUST** follow these rules at all times.

---

## ⚠️ Core Directives (NON-NEGOTIABLE)

These 6 rules are absolute. Never violate them:

| # | Directive | What It Means |
|---|-----------|---------------|
| 1 | **NEVER commit or push** | Not even if user asks. Not even "just this once". |
| 2 | **NEVER add dependencies** | Use what exists. Explicit approval required for exceptions. |
| 3 | **NEVER modify `.env`** | Or any file likely to contain secrets/credentials. |
| 4 | **ALWAYS check `git log`** | Before making ANY changes. Understand context first. |
| 5 | **NEVER modify `tests/`** | Use `.tests_sandbox/` for new tests (requires approval). |
| 6 | **Use `uv` & `pyproject.toml`** | For all dependency management. Avoid pin drift. |

---

## What is the Meta Project Harness?

The **Meta Project Harness** is a structured development system optimized for AI-assisted development. It provides:

- **Safe spaces** to work without affecting production
- **Clear workflows** for consistent, high-quality output
- **Comprehensive documentation** at every level
- **Quality gates** to ensure correctness

### Directory Structure

```\nagent-x/\n├── META_HARNESS.md              # Master documentation\n├── AGENTS.md                    # This file - your rules\n├── .project_development/        # Development standards\n│   ├── META.md\n│   └── QUICK_REFERENCE.md\n├── .sandbox/                    # Your safe workspace\n│   └── META.md\n├── .experiments/                # Experimental features\n│   └── META.md\n├── .tests_sandbox/              # TDD workspace\n│   └── META.md\n└── .development_tools/          # Development utilities\n    └── META.md\n```\n\n**All harness directories start with `.` (dot)** and contain a `META.md` file you must read first.

---

## Your Workflow (Step by Step)

### Before Any Task

1. **Check `git log`** - Understand recent changes
   ```bash
   git log --oneline -10
   ```

2. **Read relevant META.md files** - Know the rules
   - `META_HARNESS.md` - Master guide
   - `.project_development/META.md` - Development standards
   - Directory-specific META.md for your task

3. **Identify correct directory** - Where to work
   - Code changes → `.sandbox/`
   - New tests → `.tests_sandbox/`
   - Experiments → `.experiments/`
   - Tools → `.development_tools/`

### During Task

4. **Plan your approach** - Think before acting
   - Smallest viable change
   - Required tests
   - Expected outcome

5. **Execute in safe space** - Never production
   - Copy production code to `.sandbox/`
   - Make changes there
   - Test thoroughly

6. **Test using TDD** - In `.tests_sandbox/`
   - Write failing test first (RED)
   - Make it pass (GREEN)
   - Refactor (REFACTOR)
   - Follow Kent Beck methodology

### After Task

7. **Document your changes**
   - Update relevant META.md if needed
   - Add examples
   - Note any issues

8. **Report to user**
   - What you did
   - Test results
   - Next steps
   - Any blockers

---

## Decision Tree

```\nNeed to...\n├─ Modify code?\n│  └─→ Work in .sandbox/\n│\n├─ Write tests?\n│  └─→ Use .tests_sandbox/ (TDD)\n│\n├─ Test new idea?\n│  └─→ Use .experiments/\n│\n├─ Use/create tools?\n│  └─→ Check .development_tools/\n│\n└─ Understand rules?\n   └─→ Read META.md files first\n```\n\n---

## Quality Gates

Before reporting completion, verify:

- [ ] Read relevant META.md files
- [ ] Checked `git log`
- [ ] Worked in correct directory
- [ ] Followed TDD (if applicable)
- [ ] All tests pass
- [ ] Documented changes
- [ ] Cleaned workspace
- [ ] No secrets exposed
- [ ] No production code modified

---

## Tools You Have

- `read` - Read files
- `glob` - Find files by pattern
- `bash` - Run commands (git, ls, etc.)
- `edit` - Edit files
- `write` - Write new files
- `task` - Delegate complex tasks

---

## Common Scenarios

### Scenario 1: "Add a new feature"

```\n1. Read META_HARNESS.md\n2. Create experiment in .experiments/\n3. Write tests in .tests_sandbox/\n4. Implement in .sandbox/\n5. Validate & document\n6. Report to user\n```\n\n### Scenario 2: "Fix a bug"

```\n1. Check git log\n2. Reproduce in .sandbox/\n3. Write failing test in .tests_sandbox/\n4. Fix in .sandbox/\n5. Verify test passes\n6. Document fix\n```\n\n### Scenario 3: "Refactor code"

```\n1. Copy to .sandbox/\n2. Write behavior tests\n3. Refactor\n4. Verify tests still pass\n5. Document improvements\n```\n\n### Scenario 4: "Monthly maintenance"

```\n1. Run health check (see skill: optimize-meta-harness)\n2. Review all META.md files\n3. Update as needed\n4. Document changes\n```\n\n---

## Available Skills

### optimize-meta-harness

Use this skill to analyze and optimize the harness itself.

```bash\nskill optimize-meta-harness\n```\n\n**Workflows**:\n1. Health Check - Assess current state\n2. Documentation Analysis - Score META.md files\n3. Structure Optimization - Improve organization\n4. Workflow Enhancement - Streamline processes\n5. Continuous Improvement - Monitor & maintain\n\n---

## When Things Go Wrong

### If you're unsure:\n1. Stop\n2. Re-read META.md files\n3. Check examples in `.sandbox/.user/`\n4. Ask user for clarification\n\n### If you made a mistake:\n1. Document what happened\n2. Don't hide it\n3. Propose fix\n4. Learn from it\n\n### If production code is affected:\n1. Stop immediately\n2. Document the change\n3. Propose rollback plan\n4. Get user approval\n\n---

## Resources

| Resource | Purpose |\n|----------|---------|  \n| `META_HARNESS.md` | Complete harness documentation |\n| `.project_development/META.md` | Development standards |\n| `.project_development/QUICK_REFERENCE.md` | Quick decision guide |\n| `.sandbox/META.md` | Safe workspace rules |\n| `.tests_sandbox/META.md` | TDD methodology (Kent Beck) |\n| `README.md` | Project overview |\n\n---

## Remember\n\n> **READ META.md FIRST**  \n> **WORK IN SAFE SPACES**  \n> **TEST BEFORE PROPOSING**  \n> **DOCUMENT EVERYTHING**  \n> **NEVER COMMIT WITHOUT PERMISSION**\n\n---\n\n**Version**: 1.1.0 (2026-04-19)  \n**Maintained by**: opencode AI agent  \n**License**: Apache 2.0
