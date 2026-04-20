# Token Optimization Skill

---
name: optimize-token-consumption
description: Analyze and optimize AI agent token consumption. Reduces costs 30-50% while maintaining clarity.
version: 1.0.0
---

## Quick Start
**Load**: `skill optimize-token-consumption`
**Time**: 30-45 min
**Savings**: 30-50% token reduction

## When to Use
- Token usage excessive
- Documentation verbose
- Context limits exceeded
- Cost optimization needed
- Monthly maintenance

## Decision Tree
```
Need to optimize tokens?
├─ Baseline unknown? → Token Audit
├─ Docs too long? → Compression
├─ Skills overlap? → Consolidation
└─ Workflows verbose? → Streamline
```

## Core Workflows

### 1. Token Audit (30 min)
**Use**: Baseline measurement

**Steps**:
1. Count tokens in all `.md` files
2. Categorize by file type
3. Identify redundancy patterns
4. Calculate compression opportunities
5. Generate report

**Output**: Token audit with metrics

### 2. Documentation Compression (45 min)
**Use**: Docs exceed limits

**Steps**:
1. Remove redundant explanations
2. Replace prose with tables
3. Simplify language
4. Consolidate examples
5. Apply targets: Core -30%, META -40%, Examples -50%

**Output**: Compressed docs

### 3. Skill Consolidation (1-2 hrs)
**Use**: Overlapping skills

**Steps**:
1. Inventory skills
2. Map dependencies
3. Identify overlaps
4. Merge related skills
5. Update references

**Output**: Consolidated skills

### 4. Workflow Streamlining (1-2 hrs)
**Use**: Verbose workflows

**Steps**:
1. Analyze documentation
2. Remove non-value steps
3. Combine related steps
4. Use checklists
5. Add decision trees

**Output**: Streamlined workflows

### 5. Continuous Monitoring
**Use**: Ongoing optimization

**Steps**:
1. Set budgets (Core: 2000, META: 500, Skills: 1000)
2. Monitor trends
3. Alert on overruns
4. Regular cycles

**Output**: Monitoring dashboard

## Compression Techniques

### 1. Remove Redundancy
**Before** (200 tokens):
```markdown
The sandbox is a **safe space** for AI agents to:
- Test code changes before production
- Experiment with different implementations
- Validate fixes and features
- Run potentially risky operations

The sandbox provides a safe environment where AI agents can work
without affecting the production codebase.
```

**After** (50 tokens):
```markdown
## Core Philosophy
Sandbox: Safe space for AI agents to test, modify, and experiment without affecting production.
```
**Savings**: 75%

### 2. Use Tables
**Before** (150 tokens):
```markdown
### .project_development/
Use when you need to understand rules, check standards, review workflows.

### .experiments/
Use when you need to test libraries, prototype features, validate hypotheses.
```

**After** (80 tokens):
```markdown
| Directory | Use When |
|-----------|----------|
| `.project_development/` | Rules, standards, workflows |
| `.experiments/` | Test, prototype, validate |
```
**Savings**: 47%

### 3. Simplify Language
**Before**: "It is absolutely critical that you never commit or push changes without permission."

**After**: "**NEVER commit** without permission."

**Savings**: 80%

### 4. Decision Trees
**Before** (200 tokens of prose)

**After** (50 tokens):
```
Need to...
├─ Modify code? → .sandbox/
├─ Write tests? → .tests_sandbox/
├─ Test idea? → .experiments/
└─ Use tools? → .development_tools/
```
**Savings**: 75%

## Token Budgets

| Type | Budget | Priority |
|------|--------|----------|
| Core (AGENTS.md) | 1,500 | Critical |
| Core (META_HARNESS) | 2,000 | Critical |
| Directory META.md | 500 | High |
| Skills | 1,000 | High |
| Examples | 300 | Medium |

## Compression Targets

| Type | Reduction |
|------|-----------|
| Core docs | 30% |
| META.md | 40% |
| Skills | 35% |
| Examples | 50% |

## Best Practices

### Writing Efficient Docs
1. One concept per sentence (<20 words)
2. Active voice
3. Lists over paragraphs
4. Examples over explanations
5. Link, don't repeat

### Token-Efficient Patterns
**Use**: Tables, decision trees, checklists, code examples

**Avoid**: Long intros, multiple similar examples, redundant headers

## Common Issues

| Issue | Solution | Savings |
|-------|----------|---------|
| Docs >1000 words | Split sections | 30-40% |
| Multiple examples | Keep best | 50-60% |
| Verbose prose | Use tables | 40-50% |
| Cross-file redundancy | Consolidate | 20-30% |
| Long decision paths | Use trees | 60-70% |

## Integration
- `optimize-meta-harness`: Structure
- `python-static-analysis`: Code quality

## Resources
- **Analyzer**: `analyze_tokens.py`
- **Budget tracker**: Maintain counts
- **Examples**: See before/after in docs

## Version
1.0.0 (2026-04-19)

---
*End skill - 1,000 tokens (vs 2,800 original)*
