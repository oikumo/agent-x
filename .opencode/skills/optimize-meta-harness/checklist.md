# Meta Project Harness Optimization Checklist

## Pre-Optimization Assessment

### Structure Validation
- [ ] All META.md files exist
- [ ] All META.md files have content (>100 words)
- [ ] Directory structure matches documentation
- [ ] No orphaned directories
- [ ] Clear naming conventions

### Documentation Quality
- [ ] Purpose statements are clear
- [ ] Target audience is defined
- [ ] Rules are explicit
- [ ] Examples are provided
- [ ] Workflows are documented
- [ ] Quick reference available

### Workflow Efficiency
- [ ] Decision trees are clear
- [ ] No redundant steps
- [ ] Safe spaces are properly isolated
- [ ] TDD workflow is functional
- [ ] Experiment lifecycle is defined

## Optimization Workflows

### Workflow 1: Harness Health Check

**Use when**: Need to assess overall harness health

**Steps**:
- [ ] Read META_HARNESS.md
- [ ] Read all directory META.md files
- [ ] Check completeness (4/4 score for each)
- [ ] Verify word counts (100-500 words ideal)
- [ ] Identify missing sections
- [ ] Generate health report
- [ ] Prioritize issues

**Tools**: `read`, `glob`, `bash` (for file stats)

**Output**: Health report with scores and recommendations

---

### Workflow 2: Documentation Quality Analysis

**Use when**: Documentation seems unclear or incomplete

**Steps**:
- [ ] Read each META.md file
- [ ] Score each section (0-4):
  - [ ] Purpose statement present and clear
  - [ ] Target audience defined
  - [ ] Rules/guidelines explicit
  - [ ] Structure/workflow documented
- [ ] Count words (target: 100-500)
- [ ] Check for examples
- [ ] Verify links/references work
- [ ] Identify gaps
- [ ] Create improvement plan

**Scoring**:
- 4/4: Excellent (all sections, >200 words, examples)
- 3/4: Good (all sections, 100-200 words)
- 2/4: Fair (missing 1 section or <100 words)
- 1/4: Poor (missing 2+ sections)
- 0/4: Critical (missing or empty)

**Output**: Documentation quality report with specific improvements

---

### Workflow 3: Structure Optimization

**Use when**: Navigation is confusing or inefficient

**Steps**:
- [ ] Map current directory structure
- [ ] Identify all META directories
- [ ] Check naming consistency
- [ ] Verify hierarchy clarity
- [ ] Find redundancies
- [ ] Analyze usage patterns (git log, file dates)
- [ ] Compare with best practices
- [ ] Propose improvements
- [ ] Test in sandbox
- [ ] Implement changes
- [ ] Update documentation

**Metrics**:
- Directory depth (target: ≤3 levels)
- Sibling count (target: ≤7 per level)
- Naming consistency
- Navigation clarity

**Output**: Optimized structure with migration plan

---

### Workflow 4: Workflow Efficiency Analysis

**Use when**: Agents struggle with workflows or take too long

**Steps**:
- [ ] Review recent agent sessions
- [ ] Identify common task types
- [ ] Map decision paths
- [ ] Count steps per workflow
- [ ] Identify bottlenecks
- [ ] Find error patterns
- [ ] Measure completion time
- [ ] Propose simplifications
- [ ] Create templates
- [ ] Add examples
- [ ] Test improved workflows

**Common issues**:
- Unclear which directory to use
- Missing decision trees
- Too many steps
- Missing templates
- Unclear success criteria

**Output**: Streamlined workflows with templates

---

### Workflow 5: Continuous Improvement

**Use when**: Establishing ongoing optimization practice

**Steps**:
- [ ] Schedule monthly health checks
- [ ] Define metrics to track
- [ ] Create feedback collection system
- [ ] Set up tracking spreadsheet
- [ ] Establish review cadence
- [ ] Document improvements
- [ ] Share learnings
- [ ] Update skill

**Metrics to track**:
- Documentation completeness
- Task completion time
- Error rate
- Agent satisfaction
- Issue count

**Output**: Continuous improvement system

---

## Implementation Checklist

### Phase 1: Analysis
- [ ] Run health check workflow
- [ ] Document current state
- [ ] Identify pain points
- [ ] Gather feedback
- [ ] Prioritize issues

### Phase 2: Planning
- [ ] Create improvement plan
- [ ] Define success criteria
- [ ] Estimate effort
- [ ] Schedule work
- [ ] Prepare rollback plan

### Phase 3: Implementation
- [ ] Execute high-priority items
- [ ] Test changes
- [ ] Document updates
- [ ] Validate improvements
- [ ] Gather feedback

### Phase 4: Validation
- [ ] Run health check
- [ ] Compare metrics
- [ ] Verify improvements
- [ ] Document results
- [ ] Update documentation

### Phase 5: Maintenance
- [ ] Schedule reviews
- [ ] Monitor metrics
- [ ] Collect feedback
- [ ] Update as needed
- [ ] Share learnings

## Common Optimization Patterns

### Pattern: Consolidation
**Problem**: Too many similar directories  
**Solution**: Merge related directories  
**Example**: Combine redundant experiment folders

### Pattern: Clarification
**Problem**: Unclear purpose or rules  
**Solution**: Rewrite META.md with examples  
**Example**: Add decision trees to META.md

### Pattern: Automation
**Problem**: Repetitive manual steps  
**Solution**: Create templates/scripts  
**Example**: Template for session directories

### Pattern: Standardization
**Problem**: Inconsistent patterns  
**Solution**: Define and enforce standards  
**Example**: Standard META.md template

### Pattern: Documentation
**Problem**: Missing or outdated docs  
**Solution**: Regular documentation updates  
**Example**: Weekly META.md review

## Post-Optimization Validation

### Immediate Checks
- [ ] All files accessible
- [ ] All links work
- [ ] No broken references
- [ ] Tests pass
- [ ] Tools work

### Short-term (1 week)
- [ ] Agents using new structure
- [ ] No critical issues
- [ ] Positive feedback
- [ ] Improved metrics
- [ ] Fewer errors

### Long-term (1 month)
- [ ] Sustained improvements
- [ ] Higher productivity
- [ ] Better quality
- [ ] Agent satisfaction
- [ ] Continuous adoption

## Rollback Plan

If optimization causes issues:

1. **Stop**: Halt all optimization work
2. **Assess**: Identify what went wrong
3. **Document**: Record the issue
4. **Revert**: Return to previous state
5. **Learn**: Document lessons learned
6. **Retry**: Plan improved approach

## Resources

- `META_HARNESS.md`: Master documentation
- `AGENTS.md`: Entry point
- `.project_development/QUICK_REFERENCE.md`: Quick reference
- This checklist

## Version

- **Version**: 1.0.0
- **Last Updated**: 2026-04-19
- **Maintainer**: opencode AI agent
