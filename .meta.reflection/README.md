# Meta Reflection Test Logs

This directory contains timestamped logs from Meta Harness Reflection tests.

## Structure

Each test session generates a log file named:
```
YYYY-MM-DD_HH-MM-SS_reflection_log.md
```

## Contents

Each log contains:
- Test timestamp and agent information
- Total score and performance tier
- Category breakdown
- Detailed responses for all 36 questions
- Knowledge gaps identified
- Recommendations
- Next steps

## Performance Tiers

| Tier | Score Range | Description |
|------|-------------|-------------|
| Expert | 97-100% | Comprehensive understanding |
| Proficient | 89-96% | Strong grasp with minor gaps |
| Competent | 78-86% | Adequate knowledge, needs review |
| Needs Improvement | <78% | Significant gaps, re-study required |

## Running Tests

### Interactive Mode
```bash
uv run python .opencode/skills/meta-harness-reflection/run_reflection.py
```

### Automated Mode
```bash
uv run python .opencode/skills/meta-harness-reflection/run_automated.py
```

## Viewing Results

```bash
# List all test logs
ls -la .meta.reflection/

# View latest test
cat .meta.reflection/latest_reflection_log.md

# Compare two tests
diff .meta.reflection/first_log.md .meta.reflection/second_log.md
```

## Best Practices

1. Run tests monthly or after KB updates
2. Review incorrect answers immediately
3. Track progress over time
4. Archive old logs periodically
5. Update questions as harness evolves
