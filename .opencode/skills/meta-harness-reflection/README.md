# Meta Harness Reflection Test Suite

## Quick Start

```bash
# Run the full test suite
cd /home/oikumo/develop/projects/production/agent-x
uv run python .opencode/skills/meta-harness-reflection/run_reflection.py
```

## What This Does

This skill tests an AI agent's comprehension and proper usage of the Meta Project Harness through 36 structured questions across 8 categories:

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

## Usage

### Interactive Mode
```bash
uv run python .opencode/skills/meta-harness-reflection/run_reflection.py
```

### Automated Mode
```bash
uv run python .opencode/skills/meta-harness-reflection/run_automated.py
```

### Load as Skill
```bash
skill meta-harness-reflection
```

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

- `SKILL.md` - Skill definition and documentation
- `run_reflection.py` - Interactive test runner
- `run_automated.py` - Automated test runner
- `README.md` - This file

## Integration

Works with:
- Knowledge Base (`.meta.knowledge_base/`)
- All META.md files
- `.meta.reflection/` for logs

## Best Practices

1. Run monthly or after KB updates
2. Review incorrect answers immediately
3. Update KB if gaps are found
3. Track progress over time
4. Use as onboarding tool for new agents
