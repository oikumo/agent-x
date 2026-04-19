# Meta Project Harness Optimization Workflow

A comprehensive guide for optimizing the Meta Project Harness using agent tools.

## Overview

This workflow provides step-by-step instructions for analyzing and optimizing the Meta Project Harness structure, documentation, and workflows.

## Prerequisites

- Access to project root directory
- Read/write permissions to `.opencode/skills/`
- Familiarity with Meta Project Harness structure
- Understanding of AI agent workflows

## Phase 1: Initial Assessment

### Step 1.1: Gather Current State

**Goal**: Understand the current harness structure

**Actions**:
1. List all directories starting with `.`
2. Find all META.md files
3. Read META_HARNESS.md
4. Read AGENTS.md
5. Map directory relationships

**Tools**:
```
- glob: Find all META.md files
- read: Read each META.md
- bash: List directory structure
```

**Output**: Current state documentation

---

### Step 1.2: Documentation Audit

**Goal**: Assess documentation quality and completeness

**Actions**:
1. Read each META.md file
2. Score completeness (0-4 scale):
   - Purpose statement (0-1)
   - Target audience (0-1)
   - Rules/guidelines (0-1)
   - Structure/workflow (0-1)
3. Count words (target: 100-500)
4. Check for required sections
5. Identify gaps

**Scoring Rubric**:
- 4/4: Excellent (all sections, >200 words, examples)
- 3/4: Good (all sections, 100-200 words)
- 2/4: Fair (missing 1 section or <100 words)
- 1/4: Poor (missing 2+ sections)
- 0/4: Critical (missing or empty)

**Output**: Documentation audit report

---

### Step 1.3: Structure Analysis

**Goal**: Evaluate directory structure effectiveness

**Actions**:
1. Map current hierarchy
2. Count directory depth
3. Check naming consistency
4. Identify redundancies
5. Analyze usage patterns (file dates, git log)
6. Compare with best practices

**Metrics**:
- Directory depth (target: ≤3 levels)
- Sibling count (target: ≤7 per level)
- Naming consistency
- Usage frequency

**Output**: Structure analysis report

---

## Phase 2: Issue Identification

### Step 2.1: Categorize Issues

**Goal**: Organize identified issues by type and severity

**Categories**:
- **Critical**: Missing core components
- **High**: Major blockers or confusion
- **Medium**: Inefficiencies or gaps
- **Low**: Nice-to-have improvements

**Issue Types**:
- Documentation gaps
- Structural problems
- Workflow inefficiencies
- Missing templates
- Quality issues

**Output**: Categorized issue list

---

### Step 2.2: Prioritize Issues

**Goal**: Rank issues by impact and effort

**Prioritization Matrix**:
```\n              High Impact\n                  │\n    Fix First    │  Strategic\n    (High/High)  │  (High/Low)\n                  │\n    ─────────────┼─────────────
                  │\n    Fill-in      │  Low Priority
    (Low/High)   │  (Low/Low)\n                  │\n              Low Impact\n                  │\n        Low Effort ─────── High Effort\n```

**Output**: Prioritized issue list

---

## Phase 3: Optimization Planning

### Step 3.1: Develop Solutions

**Goal**: Create specific solutions for each issue

**For each issue**:
1. Define the problem clearly
2. Brainstorm potential solutions
3. Evaluate trade-offs
4. Select best approach
5. Document rationale

**Solution Template**:
```markdown
### Issue: [Name]

**Problem**: [Clear description]
**Impact**: [Who/what is affected]
**Root Cause**: [Why this exists]

**Proposed Solution**: [What to do]
**Effort**: [Low/Medium/High]
**Timeline**: [When to do it]

**Success Criteria**:
- [Criterion 1]
- [Criterion 2]

**Risks**:
- [Risk 1]
- [Risk 2]
```

**Output**: Solution proposals

---

### Step 3.2: Create Implementation Plan

**Goal**: Sequence optimizations logically

**Sequencing Rules**:
1. Fix critical issues first
2. Address dependencies
3. Group related changes
4. Minimize disruption
5. Enable quick wins

**Plan Template**:
```markdown
## Phase [N]: [Name]

**Goal**: [What we're achieving]

**Changes**:
1. [Change 1]
   - Files to modify
   - Expected impact
   - Validation method

2. [Change 2]
   ...

**Timeline**: [Duration]
**Validation**: [How to verify]
```

**Output**: Implementation plan

---

## Phase 4: Implementation

### Step 4.1: Execute Changes

**Goal**: Implement optimizations safely

**Rules**:
- Work in `.sandbox/` for code changes
- Test each change independently
- Document as you go
- Validate before proceeding
- Keep rollback option ready

**Process**:
1. Create backup if needed
2. Implement change
3. Test immediately
4. Document change
5. Validate against success criteria
6. Proceed to next change

**Output**: Implemented changes

---

### Step 4.2: Update Documentation

**Goal**: Ensure documentation reflects changes

**Actions**:
1. Update META.md files as needed
2. Add examples of new patterns
3. Update workflows
4. Verify links and references
5. Check word counts
6. Update version info

**Output**: Updated documentation

---

## Phase 5: Validation

### Step 5.1: Run Health Check

**Goal**: Verify improvements

**Actions**:
1. Re-run documentation audit
2. Compare scores to baseline
3. Check all quality gates
4. Verify workflows function
5. Test examples

**Validation Checklist**:
- [ ] All META.md files present
- [ ] All scores improved or maintained
- [ ] No new issues introduced
- [ ] Workflows tested and working
- [ ] Examples validated

**Output**: Validation report

---

### Step 5.2: Gather Feedback

**Goal**: Collect user/agent feedback

**Methods**:
- Test with sample tasks
- Measure completion time
- Check error rates
- Survey users (if applicable)
- Review agent logs

**Metrics**:
- Task completion time
- Error rate
- User satisfaction
- Agent efficiency

**Output**: Feedback summary

---

## Phase 6: Continuous Improvement

### Step 6.1: Establish Monitoring

**Goal**: Create ongoing monitoring system

**Actions**:
1. Define key metrics
2. Set measurement frequency
3. Create tracking system
4. Schedule regular reviews
5. Assign responsibilities

**Metrics to Track**:
- Documentation completeness
- Structure clarity
- Workflow efficiency
- Issue count
- Resolution time

**Output**: Monitoring system

---

### Step 6.2: Schedule Reviews

**Goal**: Ensure ongoing optimization

**Review Schedule**:
- **Daily**: Automated checks (if implemented)
- **Weekly**: Quick health scan
- **Monthly**: Full health check
- **Quarterly**: Deep dive analysis
- **Annually**: Strategic review

**Review Template**:
```markdown
## Review Date: YYYY-MM-DD

**Reviewer**: [Name]
**Type**: [Weekly/Monthly/Quarterly]

**Changes Since Last Review**:
- [Change 1]
- [Change 2]

**Current Status**:
- Overall: [Status]
- Issues: [Count]
- Trends: [Observations]

**Action Items**:
- [ ] [Item 1]
- [ ] [Item 2]

**Next Review**: [Date]
```

**Output**: Review reports

---

## Common Optimization Scenarios

### Scenario 1: New Directory Needed

**When**: New functionality requires new directory

**Steps**:
1. Justify need (can existing directory serve?)
2. Define purpose clearly
3. Create META.md using template
4. Add to structure documentation
5. Update META_HARNESS.md
6. Create initial content
7. Validate with test tasks

---

### Scenario 2: Documentation Gap

**When**: Missing or incomplete documentation

**Steps**:
1. Identify gap (which section missing?)
2. Gather requirements
3. Draft content using template
4. Review for completeness
5. Add examples
6. Validate clarity
7. Update version info

---

### Scenario 3: Workflow Inefficiency

**When**: Workflow has too many steps or unclear

**Steps**:
1. Map current workflow
2. Identify bottlenecks
3. Eliminate unnecessary steps
4. Clarify decision points
5. Add missing examples
6. Test optimized workflow
7. Update documentation

---

### Scenario 4: Structure Reorganization

**When**: Current structure causes confusion

**Steps**:
1. Document current structure
2. Identify pain points
3. Design new structure
4. Create migration plan
5. Test in sandbox
6. Implement gradually
7. Update all references
8. Validate with users

---

## Tools and Resources

### Analysis Tools
- `read`: Read files
- `glob`: Find files
- `bash`: Structure analysis
- `grep`: Content search

### Templates
- META.md template
- Health report template
- Optimization plan template
- Review template

### Reference Documents
- META_HARNESS.md
- AGENTS.md
- This workflow guide

---

## Success Criteria

Optimization is successful when:

- ✅ All META.md scores ≥ 3/4
- ✅ No critical issues remain
- ✅ Workflows tested and documented
- ✅ Users can navigate easily
- ✅ Agents complete tasks efficiently
- ✅ Documentation is current
- ✅ Monitoring is in place

---

## Version

- **Version**: 1.0.0
- **Last Updated**: 2026-04-19
- **Maintainer**: opencode AI agent
