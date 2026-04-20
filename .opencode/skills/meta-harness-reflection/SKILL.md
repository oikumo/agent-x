---
name: meta-harness-reflection
description: >
  Test agent's knowledge base usage and Meta Project Harness comprehension
  through structured reflection questions. Saves detailed test logs with timestamps.
version: 1.0.0
author: Agent-X
---

# Meta Harness Reflection

Comprehensive capability testing for agent's understanding and usage of the Meta Project Harness knowledge base through structured questioning and validation.

## Quick Start

**Load**: `skill meta-harness-reflection`
**Time**: 15-30 min (full test suite)
**Output**: Timestamped log in `.meta.reflection/`

## When to Use

- After populating knowledge base with new content
- Before deploying harness updates
- Monthly agent capability assessment
- When onboarding new AI agents
- After major harness changes
- To validate KB completeness

## Core Capabilities Tested

### Category 1: Core Directives (6 Questions)
Tests understanding of non-negotiable rules.

### Category 2: Workflow Knowledge (5 Questions)
Tests knowledge of standard workflows.

### Category 3: Directory Usage (5 Questions)
Tests correct directory selection.

### Category 4: TDD Methodology (6 Questions)
Tests TDD understanding and application.

### Category 5: Tool Usage (4 Questions)
Tests KB tool commands and patterns.

### Category 6: Quality Gates (3 Questions)
Tests quality validation understanding.

### Category 7: Documentation Standards (3 Questions)
Tests documentation requirements.

### Category 8: Advanced Scenarios (4 Questions)
Tests complex decision-making.

## Test Execution

### Step 1: Load Test Questions
```bash
skill meta-harness-reflection
```

### Step 2: Run Test Suite
The skill will present questions from all categories.

### Step 3: Answer Questions
Agent responds using knowledge base retrieval.

### Step 4: Log Generation
Detailed log saved to `.meta.reflection/YYYY-MM-DD_HH-MM-SS_reflection_log.md`

## Question Categories

### Category 1: Core Directives

**Q1**: What are the 6 core directives an agent must NEVER violate?

**Q2**: Before making ANY code changes, what must you always do first?

**Q3**: A user asks you to commit changes. What is your response?

**Q4**: You need to add a new Python package. What tool and process must you use?

**Q5**: Where should you NEVER modify files, even with user permission?

**Q6**: What file must you always check before starting any task?

### Category 2: Workflow Knowledge

**Q7**: Describe the 5-step standard workflow for any task.

**Q8**: What workflow should you follow when implementing a new feature from scratch?

**Q9**: How do you approach fixing a bug in production code?

**Q10**: What steps do you take when refactoring existing code?

**Q11**: Where and how do you test a new library before recommending it?

### Category 3: Directory Usage

**Q12**: You need to modify production code safely. Where do you work?

**Q13**: Where should you write tests following TDD methodology?

**Q14**: You want to prototype a new feature idea. Which directory is appropriate?

**Q15**: Where do you create and store MCP development tools?

**Q16**: What is the decision tree for selecting the correct directory?

### Category 4: TDD Methodology

**Q17**: What are the Three Laws of TDD according to Kent Beck?

**Q18**: Describe the RED-GREEN-REFACTOR cycle.

**Q19**: What is the "Fake It" pattern in TDD?

**Q20**: Explain triangulation in TDD context.

**Q21**: Why should each test verify only one behavior?

**Q22**: What is the AI agent TDD workflow?

### Category 5: Tool Usage

**Q23**: How do you add a new pattern to the knowledge base?

**Q24**: What command retrieves knowledge before starting work?

**Q25**: How do you correct an existing KB entry with updated information?

**Q26**: What does `kb.py evolve` do and when should you run it?

### Category 6: Quality Gates

**Q27**: List all items in the Quality Gate Checklist before reporting completion.

**Q28**: What are the three core development principles?

**Q29**: When is it appropriate to skip testing?

### Category 7: Documentation Standards

**Q30**: What sections must every META.md file contain?

**Q31**: What must each experimental session document?

**Q32**: What are the documentation best practices for token efficiency?

### Category 8: Advanced Scenarios

**Q33**: Scenario: User wants to add `requests` library. Walk through the complete process.

**Q34**: Scenario: You discover a better workflow than documented. What do you do?

**Q35**: Scenario: Your experiment succeeded. What are the next steps?

**Q36**: Scenario: You're 80% through a task but discover a fundamental flaw in approach. What do you do?

## Scoring System

### Confidence Levels
- **1.0**: Certain - Core rules, verified multiple times
- **0.95-0.99**: Very confident - Used successfully many times
- **0.80-0.94**: Confident - Tested, works well
- **0.60-0.79**: Somewhat confident - Observed once or twice
- **<0.60**: Uncertain - Speculative, needs verification

### Scoring Criteria
- **Correct Answer**: +1 point
- **Partial Answer**: +0.5 points
- **Incorrect Answer**: +0 points
- **Uses KB retrieval**: Bonus +0.2 points
- **Cites specific pattern**: Bonus +0.1 points

### Performance Tiers
- **35-36 points**: Expert (97-100%)
- **32-34 points**: Proficient (89-96%)
- **28-31 points**: Competent (78-86%)
- **<28 points**: Needs Improvement (<78%)

## Log Format

Each test session generates a detailed log:

```markdown
# Meta Harness Reflection Test Log

**Timestamp**: YYYY-MM-DD HH:MM:SS
**Agent**: opencode
**Total Score**: XX/36 (XX%)
**Performance Tier**: [Expert/Proficient/Competent/Needs Improvement]

## Category Breakdown
| Category | Score | Max | % |
|----------|-------|-----|---|
| Core Directives | X/6 | 6 | XX% |
| Workflow Knowledge | X/5 | 5 | XX% |
| Directory Usage | X/5 | 5 | XX% |
| TDD Methodology | X/6 | 6 | XX% |
| Tool Usage | X/4 | 4 | XX% |
| Quality Gates | X/3 | 3 | XX% |
| Documentation | X/3 | 3 | XX% |
| Advanced Scenarios | X/4 | 4 | XX% |

## Detailed Responses
### Q1: [Question text]
**Answer**: [Agent's response]
**Correct**: Yes/No/Partial
**KB Used**: Yes/No
**Confidence**: X.XX
**Notes**: [Feedback]

[... for all 36 questions ...]

## Knowledge Gaps Identified
1. [Gap 1]
2. [Gap 2]
3. [Gap 3]

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

## Next Steps
- [ ] Review incorrect answers
- [ ] Update knowledge base if gaps found
- [ ] Re-test after improvements
- [ ] Archive log
```

## Example Usage

### Run Full Test Suite
```bash
# Load skill
skill meta-harness-reflection

# Execute tests (automated)
# Results saved to: .meta.reflection/2026-04-19_22-30-00_reflection_log.md
```

### Run Specific Category
```bash
# Test only core directives
skill meta-harness-reflection --category=directives

# Test only TDD
skill meta-harness-reflection --category=tdd
```

### Compare Results
```bash
# View all test logs
ls -la .meta.reflection/

# Compare latest two runs
diff .meta.reflection/latest_log.md .meta.reflection/previous_log.md
```

## Templates

### Test Result Summary Template
```markdown
## Test Summary
**Date**: YYYY-MM-DD
**Agent**: [Agent name]
**Duration**: XX minutes
**Total Score**: XX/36 (XX%)

## Performance by Category
- ✅ Core Directives: X/6 (XX%)
- ✅ Workflow Knowledge: X/5 (XX%)
- ⚠️  Directory Usage: X/5 (XX%)
- ✅ TDD Methodology: X/6 (XX%)
- ⚠️  Tool Usage: X/4 (XX%)
- ✅ Quality Gates: X/3 (XX%)
- ✅ Documentation: X/3 (XX%)
- ⚠️  Advanced Scenarios: X/4 (XX%)

## Critical Gaps
[List categories scoring <80%]

## Immediate Actions
1. [Action 1]
2. [Action 2]
3. [Action 3]
```

## Best Practices

### For Testing
1. Run full suite monthly
2. Test after KB updates
3. Compare trends over time
4. Focus on weak categories
5. Update questions as harness evolves

### For Scoring
1. Be objective in evaluation
2. Credit KB usage
3. Note partial understanding
4. Track confidence vs accuracy
5. Document edge cases

### For Improvement
1. Identify patterns in errors
2. Update KB with missing info
3. Create targeted practice scenarios
4. Re-test weak areas
5. Share learnings

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Score <70% | Review KB entries, re-read META.md files |
| TDD questions wrong | Re-read .meta.tests_sandbox/META.md |
| Directory confusion | Study decision tree pattern |
| Tool commands unclear | Practice kb.py commands |
| Scenario failures | Review workflow patterns |

## Performance Metrics

### Target Scores
- **Minimum Passing**: 28/36 (78%)
- **Target Proficiency**: 32/36 (89%)
- **Expert Level**: 35/36 (97%)

### Historical Tracking
Track scores over time:
```
Date       Score   Tier      Notes
2026-04-19 34/36   Proficient Post-KB population
2026-05-19 36/36   Expert     After review
```

## Integration

### With Knowledge Base
- Questions reference KB entries by ID
- Answers validated against stored patterns
- Gaps trigger KB updates

### With Other Skills
- `meta-harness-optimize`: Fix identified issues
- `python-static-analysis`: Test code quality understanding
- `find-skills`: Discover related capabilities

### With Tools
- `kb.py search`: Retrieve answers
- `kb.py ask`: Query knowledge base
- `read`: Access META.md files
- `glob`: Find documentation

## Resources

- **Test Questions**: 36 questions across 8 categories
- **Log Storage**: `.meta.reflection/` directory
- **KB Reference**: `.meta.knowledge_base/knowledge.db`
- **Documentation**: All META.md files

## Version History

- **1.0.0** (2026-04-19): Initial version with 36-question test suite, timestamped logs, performance tracking, and comprehensive coverage of Meta Project Harness knowledge

---

**Maintained by**: Agent-X
**Test Frequency**: Monthly or after major changes
**Passing Score**: 28/36 (78%)
