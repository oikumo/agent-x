# Token Consumption Optimization Skill

---
name: optimize-token-consumption
description: >
  Analyze and optimize AI agent token consumption across documentation, skills, and workflows.
  Use this skill when token usage is high, documentation is verbose, or to maintain efficient
  AI-human communication. Reduces token costs by 30-50% while maintaining clarity.
version: 1.0.0
author: Agent-X
---

## Quick Start

**Load**: `skill optimize-token-consumption`
**First task**: Run Token Audit (Workflow 1)
**Time**: 30-45 minutes
**Savings**: Typically 30-50% token reduction

## When to Use

- Token usage seems excessive
- Documentation is verbose or redundant
- Before adding new documentation
- When agents struggle with context limits
- Regular maintenance (monthly)
- Cost optimization initiatives

## Decision Tree

```
Need to optimize tokens?
│
├─ Don't know current usage? → Token Audit (Workflow 1)
├─ Documentation too long? → Documentation Compression (Workflow 2)
├─ Skills redundant? → Skill Consolidation (Workflow 3)
├─ Workflows verbose? → Workflow Streamlining (Workflow 4)
└─ Want ongoing monitoring? → Continuous Monitoring (Workflow 5)
```

## Core Workflows

### Workflow 1: Token Consumption Audit (30-45 min)

**Use when**: Need baseline measurement

**Steps**:
1. Count total tokens in all `.md` files
2. Analyze token distribution by category:
   - Core documentation (META_HARNESS.md, AGENTS.md)
   - META.md files (all directories)
   - Skills documentation
   - Examples and templates
3. Identify redundancy patterns:
   - Duplicate content across files
   - Overlapping explanations
   - Redundant examples
4. Calculate compression opportunities
5. Generate audit report

**Tools**: `read`, `glob`, `bash`, `wc`

**Success criteria**:
- Complete token inventory
- Categorization by file type
- Redundancy identification
- Compression ratio estimate

**Output**: Token audit report with baseline metrics

### Workflow 2: Documentation Compression (45-60 min)

**Use when**: Documentation exceeds token limits

**Steps**:
1. Read all documentation files
2. Apply compression techniques:
   - Remove redundant explanations
   - Replace verbose examples with concise ones
   - Use tables instead of prose
   - Remove obvious statements
   - Consolidate duplicate sections
3. Maintain critical information:
   - Core directives (non-negotiable)
   - Essential workflows
   - Key examples
4. Apply compression ratio targets:
   - Core files: 30% reduction
   - META.md files: 40% reduction
   - Examples: 50% reduction
5. Validate clarity post-compression

**Compression techniques**:
- **Eliminate redundancy**: Remove repeated concepts
- **Simplify language**: Use shorter sentences
- **Use lists**: Replace paragraphs with bullet points
- **Remove filler**: Cut "however", "therefore", "in order to"
- **Consolidate examples**: One clear example beats three verbose ones

**Output**: Compressed documentation with token savings report

### Workflow 3: Skill Consolidation (1-2 hrs)

**Use when**: Skills have overlapping functionality

**Steps**:
1. Inventory all skills
2. Map skill dependencies
3. Identify overlaps:
   - Similar triggers
   - Related functionality
   - Duplicate documentation
4. Consolidate opportunities:
   - Merge related skills
   - Create skill families
   - Share common documentation
5. Remove deprecated skills
6. Update references

**Output**: Consolidated skill set with clear boundaries

### Workflow 4: Workflow Streamlining (1-2 hrs)

**Use when**: Workflows are verbose

**Steps**:
1. Analyze workflow documentation
2. Count steps per workflow
3. Identify bottlenecks:
   - Unnecessary steps
   - Redundant validation
   - Over-documentation
4. Streamline:
   - Remove non-value steps
   - Combine related steps
   - Use checklists instead of prose
5. Create quick-reference templates
6. Add decision trees

**Output**: Streamlined workflows with 40% fewer tokens

### Workflow 5: Continuous Monitoring (ongoing)

**Use when**: Establish ongoing optimization

**Steps**:
1. Set token budgets per file type:
   - Core docs: 2000 tokens max
   - META.md files: 500 tokens max
   - Skills: 1000 tokens max
2. Monitor token usage trends
3. Alert on budget overruns
4. Regular optimization cycles
5. Track savings over time

**Metrics to track**:
- Total tokens per session
- Average tokens per file
- Compression ratio achieved
- Token cost savings

**Output**: Monitoring dashboard with trends

## Token Compression Techniques

### 1. Remove Redundancy

**Before** (200 tokens):
```markdown
## Core Philosophy

The sandbox is a **safe space** for AI agents to:
- Test code changes before production
- Experiment with different implementations
- Validate fixes and features
- Run potentially risky operations

The sandbox provides a safe environment where AI agents can work
without affecting the production codebase. This is important because
it allows for experimentation without risk.
```

**After** (50 tokens):
```markdown
## Core Philosophy

Sandbox: Safe space for AI agents to test, modify, and
experiment without affecting production code.
```

**Savings**: 75% reduction

### 2. Use Tables Instead of Prose

**Before** (150 tokens):
```markdown
### When to Use Each Directory

#### .project_development/
Use when you need to understand project development rules,
check coding standards, review task workflows, or document
development processes.

#### .experiments/
Use when you need to test a new library or approach, prototype
a feature, validate a hypothesis, or explore alternatives.

#### .sandbox/
Use when you need to modify production code safely, test code
changes, work on multi-step tasks, or keep session-specific work.
```

**After** (80 tokens):
```markdown
### Directory Usage

| Directory | Use When |
|-----------|----------|
| `.project_development/` | Understand rules, check standards, document |
| `.experiments/` | Test libraries, prototype, validate hypotheses |
| `.sandbox/` | Modify code safely, test changes, multi-step tasks |
```

**Savings**: 47% reduction

### 3. Simplify Language

**Before** (100 tokens):
```markdown
It is absolutely critical that you never commit or push
changes to the repository without explicit permission from
the user. This is one of the most important rules and must
be followed at all times without exception.
```

**After** (20 tokens):
```markdown
**NEVER commit or push** without explicit user permission.
```

**Savings**: 80% reduction

### 4. Remove Filler Words

**Before**: "In order to ensure that you are following the
correct procedure, it is recommended that you always read
the META.md files first before making any changes."

**After**: "Read META.md files before making changes."

**Savings**: 70% reduction

### 5. Use Decision Trees

**Before** (200 tokens of prose):
```markdown
If you need to modify code, you should work in the sandbox
directory. If you need to write tests, use the tests sandbox.
If you want to test a new idea, use experiments. If you need
to create or use tools, check the development tools directory.
```

**After** (50 tokens):
```markdown
## Decision Tree
```
Need to...
├─ Modify code? → .sandbox/
├─ Write tests? → .tests_sandbox/
├─ Test idea? → .experiments/
└─ Use tools? → .development_tools/
```

**Savings**: 75% reduction

## Token Budget Guidelines

### File Type Budgets

| File Type | Token Budget | Priority |
|-----------|--------------|----------|
| Core directives (AGENTS.md) | 1500 | Critical |
| Master docs (META_HARNESS.md) | 2000 | Critical |
| Directory META.md | 500 | High |
| Skill documentation | 1000 | High |
| Examples | 300 | Medium |
| Templates | 400 | Medium |

### Compression Targets

| File Type | Target Reduction |
|-----------|------------------|
| Core docs | 30% |
| META.md files | 40% |
| Skills | 35% |
| Examples | 50% |
| Overall | 35-45% |

## Templates

### Token Audit Report Template

```markdown
# Token Audit Report
Date: YYYY-MM-DD

## Summary
- Total tokens: X,XXX
- Reduction opportunity: XX%
- Estimated savings: X,XXX tokens

## Token Distribution
| Category | Tokens | % | Status |
|----------|--------|---|--------|
| Core docs | X,XXX | XX% | ⚠️ Over budget |
| META.md files | XXX | XX% | ✅ On budget |
| Skills | XXX | XX% | ✅ On budget |

## Top Opportunities
1. File X: Reduce by XX% (redundant section)
2. File Y: Consolidate with File Z
3. Examples: Replace prose with tables

## Recommendations
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]
```

### Compression Checklist

- [ ] Remove redundant explanations
- [ ] Replace paragraphs with tables
- [ ] Remove filler words
- [ ] Simplify language
- [ ] Use decision trees
- [ ] Consolidate examples
- [ ] Remove obvious statements
- [ ] Verify critical info preserved
- [ ] Test clarity with sample tasks

## Best Practices

### Writing Efficient Documentation

1. **One concept per sentence** - Keep sentences under 20 words
2. **Use active voice** - "Do this" not "This should be done"
3. **Prefer lists over paragraphs** - Bullet points are scannable
4. **Show, don't tell** - Examples over explanations
5. **Remove meta-commentary** - Cut "this section will explain"
6. **Use consistent terminology** - Avoid synonym proliferation
7. **Link, don't repeat** - Reference other sections instead of duplicating

### Token-Efficient Patterns

**Good**:
- Tables for comparisons
- Decision trees for workflows
- Checklists for validation
- Code examples over explanations
- Inline comments for context

**Avoid**:
- Long introductory paragraphs
- Multiple similar examples
- Redundant section headers
- Over-explaining obvious concepts
- Repeating information across files

## Common Issues & Solutions

| Issue | Solution | Savings |
|-------|----------|---------|
| Documentation >1000 words | Split into focused sections | 30-40% |
| Multiple similar examples | Keep 1 best example | 50-60% |
| Verbose explanations | Replace with tables/lists | 40-50% |
| Redundant across files | Consolidate, link, deduplicate | 20-30% |
| Long decision paths | Use decision trees | 60-70% |

## Integration

### With Other Skills

- `optimize-meta-harness`: Structural optimization
- `python-static-analysis`: Code documentation quality
- `find-skills`: Discover token-efficient patterns

### With Tools

- `wc`: Count tokens/lines
- `bash`: Token analysis scripts
- `read`: Analyze content
- `edit`: Apply compression

## Resources

- **Token counters**: Use `wc -w` for word count estimate
- **Compression ratio**: (Original - Compressed) / Original
- **Budget tracker**: Maintain token counts in README
- **Examples**: See before/after examples above

## Version History

- **1.0.0** (2026-04-19): Initial version with audit workflow,
  compression techniques, and monitoring system

---

## Appendix: Token Calculation

### Estimation Method

- 1 word ≈ 1.3 tokens (English average)
- 1 line ≈ 10-15 tokens (code/documentation)
- Use `wc -w` for word count, multiply by 1.3

### Quick Calculation

```bash
# Count words in all .md files
find . -name "*.md" -exec wc -w {} \; | awk '{sum+=$1} END {print sum}'

# Estimate tokens (words * 1.3)
WORD_COUNT * 1.3 = TOKEN_ESTIMATE
```

### Typical Token Distribution

```\nCore Documentation: 40%\nMETA.md Files: 30%\nSkills: 20%\nExamples/Templates: 10%\n```

---

**Version**: 1.0.0 (2026-04-19)
**Maintained by**: opencode AI agent
**License**: Apache 2.0
