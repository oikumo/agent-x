# Optimize Meta Project Harness Skill

A specialized skill for analyzing, optimizing, and maintaining the Meta Project Harness structure for AI-assisted development.

## Quick Start

**Load**: `skill optimize-meta-harness`  
**First task**: Run Harness Health Check (Workflow 1)  
**Time**: 15-30 minutes

## Purpose

This skill provides systematic workflows to:
- Analyze harness effectiveness using agent tools
- Identify bottlenecks in AI agent workflows
- Optimize directory structure and documentation
- Improve development velocity
- Maintain harness health over time

## When to Use

- Harness seems slow or confusing
- Documentation needs updating
- Agents struggle with navigation
- Before major structural changes
- Regular maintenance (monthly)

## Core Workflows

### 1. Harness Health Check (15-30 min)

**Use when**: Need overall assessment

**Steps**:
1. Read all META.md files
2. Check completeness (purpose, target, rules, structure)
3. Verify directory structure matches documentation
4. Identify missing or incomplete documentation
5. Generate health report

**Tools**: `read`, `glob`, `bash`

**Success criteria**:
- All META.md files exist
- All META.md files have >100 words
- All required sections present
- Structure matches documentation

### 2. Documentation Quality Analysis (30-45 min)

**Use when**: Documentation quality questionable

**Steps**:
1. Read each META.md file
2. Score completeness (0-4 scale):
   - Purpose statement
   - Target audience
   - Rules/guidelines
   - Structure/workflow
3. Check word count (minimum 100 words)
4. Identify gaps
5. Generate improvement recommendations

**Scoring rubric**:
- 4/4: Excellent (all sections, >200 words)
- 3/4: Good (all sections, 100-200 words)
- 2/4: Fair (missing 1 section or <100 words)
- 1/4: Poor (missing 2+ sections)
- 0/4: Critical (file missing or empty)

### 3. Structure Optimization (1-2 hrs)

**Use when**: Navigation is confusing

**Steps**:
1. Map current directory structure
2. Identify usage patterns (via git log, file dates)
3. Find redundancies or overlaps
4. Compare with best practices
5. Propose structural improvements
6. Implement changes (in sandbox)
7. Validate improvements

**Metrics**: Directory depth, navigation clarity, naming consistency

### 4. Workflow Efficiency Analysis (1-2 hrs)

**Use when**: Workflows inefficient

**Steps**:
1. Review recent agent sessions
2. Identify common task patterns
3. Measure time-to-completion
4. Find bottlenecks
5. Analyze error patterns
6. Propose workflow improvements
7. Test optimized workflows

**Common bottlenecks**: Unclear directory choice, missing docs, complex navigation

### 5. Continuous Improvement (ongoing)

**Use when**: Establishing ongoing optimization

**Steps**:
1. Schedule regular health checks (monthly)
2. Collect agent feedback
3. Track metrics over time
4. Identify trends
5. Implement incremental improvements
6. Document changes
7. Share learnings

## Templates

### Health Check Report

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

### Optimization Plan

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

## Metrics

### Documentation Metrics
- Completeness score (0-4)
- Word count (100-500)
- Update frequency (monthly)
- Example coverage (100%)

### Structure Metrics
- Directory depth (≤3 levels)
- Naming consistency (100%)
- Navigation time (<1 min)

### Workflow Metrics
- Task completion time (decreasing)
- Error rate (0%)
- Steps per workflow (≤7)

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

## Getting Help

**Resources**:
- `META_HARNESS.md`: Master documentation
- `AGENTS.md`: Entry point rules
- `templates/`: Reusable templates
- `examples/`: Real examples

**Support**:
1. Check examples in `examples/`
2. Review templates in `templates/`
3. Follow workflows above
4. Consult metrics

## Version History

- **1.0.0** (2026-04-19): Initial version
  - Health check workflow
  - Documentation analysis
  - Structure optimization
  - Workflow efficiency
  - Templates and examples

## License

Apache 2.0 - Same as Agent-X project

---

**Ready to optimize? Load this skill and start with Workflow 1: Harness Health Check!**
