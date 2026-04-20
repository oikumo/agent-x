# Meta Harness Reflection - Quick Start

## What is This?

A comprehensive testing skill that validates an AI agent's understanding of the Meta Project Harness through 36 structured questions.

## Run in 30 Seconds

```bash
# Navigate to project
cd /home/oikumo/develop/projects/production/agent-x

# Run automated test (uses KB search)
uv run python .opencode/skills/meta-harness-reflection/run_automated.py
```

## Output

- **Test Log**: `.meta.reflection/YYYY-MM-DD_HH-MM-SS_reflection_log.md`
- **Performance Score**: Out of 36 points
- **Tier**: Expert (97%+), Proficient (89%+), Competent (78%+), or Needs Improvement

## What Gets Tested?

| Category | Questions | Focus |
|----------|-----------|-------|
| Core Directives | 6 | Never commit, always git log, use uv, etc. |
| Workflow Knowledge | 5 | Feature implementation, bug fixes, refactoring |
| Directory Usage | 5 | sandbox, experiments, tests_sandbox, tools |
| TDD Methodology | 6 | RED-GREEN-REFACTOR, three laws, patterns |
| Tool Usage | 4 | kb.py commands (add, search, correct, evolve) |
| Quality Gates | 3 | Checklists, principles, testing rules |
| Documentation | 3 | META.md structure, session docs |
| Advanced Scenarios | 4 | Real-world decision making |

## Modes

**Interactive**: Manual answers with self-evaluation
```bash
uv run python .opencode/skills/meta-harness-reflection/run_reflection.py
```

**Automated**: KB search for answers
```bash
uv run python .opencode/skills/meta-harness-reflection/run_automated.py
```

## Next Steps

1. Run the test
2. Review the generated log
3. Identify knowledge gaps
4. Study weak areas
5. Re-test

## Files

- `SKILL.md` - Full documentation
- `README.md` - Overview
- `QUICKSTART.md` - This file
- `run_reflection.py` - Interactive mode
- `run_automated.py` - Automated mode

---

**Pass Score**: 28/36 (78%)
**Time**: 15-30 minutes
**Frequency**: Monthly or after KB updates
