# Meta Project Harness - Quick Reference Card

## At a Glance

```
READ FIRST: META_HARNESS.md
WORK IN: .sandbox/ or .experiments/
TEST IN: .tests_sandbox/
NEVER MODIFY: production code directly
```

---

## Directory Decision Tree

```\nNeed to...\n├─ Understand rules?          → Read META.md files first\n├─ Modify code?               → .sandbox/\n├─ Test new idea?             → .experiments/\n├─ Write tests?               → .tests_sandbox/\n├─ Use/create tools?          → .development_tools/\n└─ Check development rules?   → .project_development/\n```\n\n---

## Core Directives (Remember All 6)\n\n1. ❌ **NEVER commit or push**\n2. ❌ **NEVER add dependencies** (without approval)\n3. ❌ **NEVER modify `.env`**\n4. ✅ **ALWAYS check `git log`**\n5. ❌ **NEVER modify `tests/`** (use `.tests_sandbox/`)\n6. ✅ **Use `uv` & `pyproject.toml`**\n\n---\n\n## Standard Workflow\n\n```bash\n# 1. Read META.md files\nread .project_development/META.md\n\n# 2. Check git log\ngit log --oneline -10\n\n# 3. Work in sandbox\ncp src/module.py .sandbox/session/\n\n# 4. Test in tests_sandbox\nuv run pytest .tests_sandbox/ -v\n\n# 5. Document changes\necho \"Changes made\" > .sandbox/session/notes.md\n```\n\n---\n\n## File Locations\n\n| File | Purpose |\n|------|--------|\n| `META_HARNESS.md` | Master documentation |\n| `AGENTS.md` | Entry point rules |\n| `README.md` | Project overview |\n| `.project_development/META.md` | Dev standards |\n| `.sandbox/META.md` | Sandbox rules |\n| `.tests_sandbox/META.md` | TDD guide |\n| `.experiments/META.md` | Experiment guide |\n| `.development_tools/META.md` | Tools guide |\n\n---\n\n## Workflow by Task Type\n\n### New Feature\n```\n1. Read META_HARNESS.md\n2. Create experiment in .experiments/\n3. Write tests in .tests_sandbox/\n4. Implement in .sandbox/\n5. Validate & document\n```\n\n### Bug Fix\n```\n1. Reproduce in .sandbox/\n2. Write failing test\n3. Fix in .sandbox/\n4. Verify test passes\n5. Document fix\n```\n\n### Refactoring\n```\n1. Copy to .sandbox/\n2. Write behavior tests\n3. Refactor\n4. Verify tests pass\n5. Document improvements\n```\n\n### Testing New Library\n```\n1. Create .experiments/date-feature/\n2. Document hypothesis\n3. Test in isolation\n4. Validate & document\n5. Recommend\n```\n\n---\n\n## Quality Checklist\n\nBefore reporting completion:\n\n- [ ] Read relevant META.md\n- [ ] Checked git log\n- [ ] Worked in correct directory\n- [ ] Followed TDD (if applicable)\n- [ ] All tests pass\n- [ ] Documented changes\n- [ ] Cleaned workspace\n- [ ] No secrets exposed\n- [ ] No production code modified\n\n---\n\n## Common Commands\n\n```bash\n# Run tests\nuv run pytest .tests_sandbox/ -v\n\n# Check project structure\nls -la .*\n\n# View git history\ngit log --oneline -10\n\n# Install dependencies\nuv add package-name\n\n# Sync environment\nuv sync\n```\n\n---\n\n## Emergency Stops\n\n**STOP and ask user if:**\n- Task requires new dependency\n- Unclear which directory to use\n- Tests won't pass after fix\n- Production code already modified\n- Git conflicts detected\n\n---\n\n## Remember\n\n> **READ META.md FIRST**  \n> **WORK IN SAFE SPACES**  \n> **TEST BEFORE PROPOSING**  \n> **DOCUMENT EVERYTHING**  \n> **NEVER COMMIT WITHOUT PERMISSION**\n\n---\n\n## Version\n\n- **Version**: 1.0.0\n- **Updated**: 2026-04-19\n- **For**: opencode AI agent\n\n