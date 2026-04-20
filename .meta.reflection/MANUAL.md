# Meta Harness Reflection - User Manual

## Quick Start

### Option 1: Load as Skill
```bash
skill meta-harness-reflection
```

### Option 2: Run Directly

**Interactive Mode** (manual answers):
```bash
cd /home/oikumo/develop/projects/production/agent-x
uv run python .opencode/skills/meta-harness-reflection/run_reflection.py
```

**Automated Mode** (KB search):
```bash
cd /home/oikumo/develop/projects/production/agent-x
uv run python .opencode/skills/meta-harness-reflection/run_automated.py
```

**Using Launcher Script**:
```bash
.opencode/skills/meta-harness-reflection/test_reflection.sh interactive
.opencode/skills/meta-harness-reflection/test_reflection.sh automated
```

## What This Does

Tests an AI agent's comprehension of the Meta Project Harness through **36 structured questions** across **8 categories**:

1. **Core Directives** (6 questions) - Non-negotiable rules
2. **Workflow Knowledge** (5 questions) - Standard workflows
3. **Directory Usage** (5 questions) - Correct directory selection
4. **TDD Methodology** (6 questions) - Test-driven development
5. **Tool Usage** (4 questions) - Knowledge base commands
6. **Quality Gates** (3 questions) - Validation checkpoints
7. **Documentation Standards** (3 questions) - Documentation rules
8. **Advanced Scenarios** (4 questions) - Complex decision-making

## Output

- **Test Log**: Saved to `.meta.reflection/YYYY-MM-DD_HH-MM-SS_reflection_log.md`
- **Detailed Report**: Includes scores, confidence levels, and KB usage
- **Performance Tier**: Expert (97%+), Proficient (89%+), Competent (78%+), or Needs Improvement (<78%)

## Scoring

- **1.0 point**: Correct and complete answer
- **0.5 points**: Partially correct
- **0.0 points**: Incorrect
- **+0.2 bonus**: Using knowledge base retrieval
- **+0.1 bonus**: Citing specific patterns

## Performance Tiers

| Tier | Score Range | Description |
|------|-------------|-------------|
| Expert | 97-100% | Comprehensive understanding |
| Proficient | 89-96% | Strong grasp with minor gaps |
| Competent | 78-86% | Adequate knowledge, needs review |
| Needs Improvement | <78% | Significant gaps, re-study required |

## Files

```
.opencode/skills/meta-harness-reflection/
├── SKILL.md                 # Skill definition
├── README.md                # Quick reference
├── run_reflection.py        # Interactive test runner
├── run_automated.py         # Automated test runner
└── test_reflection.sh       # Bash launcher
```

## Integration

Works with:
- Knowledge Base (`.meta.knowledge_base/`)
- All META.md files
- `.meta.reflection/` for logs

## Best Practices

1. **Run monthly** or after KB updates
2. **Review incorrect answers** immediately
3. **Update KB** if gaps are found
4. **Track progress** over time
5. **Use as onboarding** tool for new agents

## Troubleshooting

**No results from KB search?**
- Ensure knowledge base is populated
- Check that `kb.py` is working: `python .meta.knowledge_base/kb.py stats`

**Script errors?**
- Ensure dependencies: `uv add sentence-transformers numpy`
- Check Python version: Python 3.14+

**Low scores?**
- Review all META.md files
- Practice using kb.py commands
- Re-read .meta.tests_sandbox/META.md for TDD

## Example Output

```markdown
# Meta Harness Reflection Test Log

**Timestamp**: 2026-04-19 22:59:36
**Agent**: opencode
**Total Score**: 32.0/36.0 (88.9%)
**Performance Tier**: Proficient

## Category Breakdown
| Category | Score | Max | % |
|----------|-------|-----|---|
| Core Directives | 5.0/6 | 6 | 83% |
| Workflow Knowledge | 4.5/5 | 5 | 90% |
...
```

## Next Steps

After running the test:
1. Review the generated log file
2. Identify knowledge gaps
3. Update knowledge base if needed
4. Re-test after improvements
5. Archive old logs

---

**Maintained by**: Agent-X
**Test Frequency**: Monthly or after major changes
**Passing Score**: 28/36 (78%)
