---
name: optimize-meta-harness
description: >
  Analyze and optimize the Meta Project Harness structure, documentation, and workflows.
  Use this skill when the harness seems slow or confusing, documentation needs updating,
  agents struggle with navigation, before major structural changes, or for regular maintenance.
version: 1.1.0
author: Agent-X
---

# Optimize Meta Project Harness Skill

Systematic analysis and optimization of the Meta Project Harness for AI-assisted development.

## Quick Start

**Load**: `skill optimize-meta-harness`  
**First task**: Run Harness Health Check (Workflow 1)  
**Time**: 15-30 minutes

## When to Use

- Harness seems slow or confusing
- Documentation needs updating
- Agents struggle with navigation
- Before major structural changes
- Regular maintenance (monthly)

## Decision Tree

```
Need to optimize?
│
├─ Don't know current state? → Health Check (Workflow 1)
├─ Documentation unclear? → Documentation Analysis (Workflow 2)
├─ Structure confusing? → Structure Optimization (Workflow 3)
├─ Workflows slow? → Workflow Enhancement (Workflow 4)
└─ Want ongoing improvement? → Continuous Improvement (Workflow 5)
```

## Core Workflows

### Workflow 1: Harness Health Check (15-30 min)

**Use when**: Need overall assessment

**Steps**:
1. Read all META.md files (META_HARNESS.md, .project_development/META.md, .experiments/META.md, .sandbox/META.md, .tests_sandbox/META.md, .development_tools/META.md)
2. Check completeness (purpose, target, rules, structure)
3. Verify directory structure matches documentation
4. Identify missing or incomplete documentation
5. Generate health report using template below

**Tools**: `read`, `glob`, `bash`

**Success criteria**:
- All META.md files exist
- All META.md files have >100 words
- All required sections present
- Structure matches documentation

**Output**: Health report with scores and recommendations

### Workflow 2: Documentation Quality Analysis (30-45 min)

**Use when**: Documentation quality questionable

**Steps**:
1. Read each META.md file
2. Score completeness (0-4 scale):
   - Purpose statement (0-1)
   - Target audience (0-1)
   - Rules/guidelines (0-1)
   - Structure/workflow (0-1)
3. Check word count (minimum 100 words, target 100-500)
4. Identify gaps
5. Generate improvement recommendations

**Scoring rubric**:
- 4/4: Excellent (all sections, >200 words, examples)
- 3/4: Good (all sections, 100-200 words)
- 2/4: Fair (missing 1 section or <100 words)
- 1/4: Poor (missing 2+ sections)
- 0/4: Critical (file missing or empty)

**Output**: Documentation quality report with specific improvements

### Workflow 3: Structure Optimization (1-2 hrs)

**Use when**: Navigation is confusing

**Steps**:
1. Map current directory structure
2. Identify all META directories
3. Check naming consistency
4. Analyze usage patterns (via git log, file dates)
5. Find redundancies or overlaps
6. Compare with best practices (directory depth ≤3, siblings ≤7)
7. Propose structural improvements
8. Implement changes (in sandbox)
9. Validate improvements
10. Update documentation

**Metrics**: Directory depth, navigation clarity, naming consistency

**Output**: Optimized structure with migration plan

### Workflow 4: Workflow Efficiency Analysis (1-2 hrs)

**Use when**: Workflows inefficient

**Steps**:
1. Review recent agent sessions
2. Identify common task patterns
3. Map decision paths
4. Count steps per workflow
5. Measure time-to-completion
6. Find bottlenecks
7. Analyze error patterns
8. Propose workflow simplifications
9. Create templates
10. Add examples
11. Test optimized workflows

**Common bottlenecks**: Unclear directory choice, missing docs, complex navigation, missing templates

**Output**: Streamlined workflows with templates

### Workflow 5: Continuous Improvement (ongoing)

**Use when**: Establishing ongoing optimization

**Steps**:
1. Schedule regular health checks (monthly)
2. Collect agent feedback
3. Track metrics over time (documentation completeness, task completion time, error rate)
4. Identify trends
5. Implement incremental improvements
6. Document changes
7. Share learnings

**Metrics to track**:
- Documentation completeness score
- Task completion time
- Error rate
- Agent satisfaction
- Issue count

**Output**: Continuous improvement system with scheduled reviews

## Templates

### Health Check Report Template

```markdown
# Meta Harness Health Report
Date: YYYY-MM-DD

## Summary
- Overall Status: [HEALTHY | NEEDS ATTENTION | CRITICAL]
- Total Issues: X (Critical: X, Warnings: X)

## Documentation Status
| File | Status | Score | Words |
|------|--------|-------|-------|
| .project_development/META.md | ✅ | 4/4 | 250 |
| .experiments/META.md | ✅ | 4/4 | 200 |
| .sandbox/META.md | ✅ | 4/4 | 220 |
| .tests_sandbox/META.md | ✅ | 4/4 | 450 |
| .development_tools/META.md | ✅ | 4/4 | 180 |

## Recommendations
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

## Next Actions
- [ ] Action 1
- [ ] Action 2
```

### Optimization Plan Template

```markdown
# Optimization Plan
Date: YYYY-MM-DD

## Current State
[Description]

## Issues Identified
1. Issue 1 (Severity: High/Medium/Low)
2. Issue 2

## Proposed Changes
### Change 1
- **What**: [Description]
- **Why**: [Rationale]
- **Impact**: [Expected impact]
- **Effort**: [Low/Medium/High]

## Implementation Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Validation
- [ ] Tests pass
- [ ] Documentation updated
```

## Best Practices

### Documentation
- Keep META.md between 100-500 words
- Include purpose, target, rules, and structure
- Use clear, simple language
- Provide examples
- Update regularly

### Structure
- Maintain clear hierarchy
- Use consistent naming
- Keep depth ≤ 3 levels
- Isolate concerns properly

### Workflows
- Minimize steps
- Provide decision trees
- Include examples
- Define success criteria

### Quality
- Regular health checks
- Track metrics
- Collect feedback
- Continuous improvement

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| META.md too short (<100 words) | Expand with examples, workflows |
| Missing purpose statement | Add clear "why exists" section |
| No examples provided | Add 2-3 concrete usage examples |
| Unclear which directory | Add decision tree to META_HARNESS.md |
| Workflows too complex | Eliminate steps, add templates |

## Integration

### With Other Skills
- `python-static-analysis`: For code quality
- `mcp-issue-tracker-analysis`: For workflow analysis
- `find-skills`: Discover new capabilities

### With Tools
- `read`: Read and analyze files
- `glob`: Find files and patterns
- `bash`: Structure analysis
- `edit`: Update documentation

## Resources

- `META_HARNESS.md`: Master documentation
- `AGENTS.md`: Entry point rules
- `templates/`: Reusable templates
- `examples/`: Real examples

## Version History

- **1.1.0** (2026-04-19): Consolidated workflows, removed redundant files
- **1.0.0** (2026-04-19): Initial version with health check, documentation analysis, structure optimization, workflow efficiency
