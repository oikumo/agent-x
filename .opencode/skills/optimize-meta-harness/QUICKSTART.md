# Quick Start - Optimize Meta Project Harness

## 30-Second Overview

**What**: Skill to analyze and optimize Meta Project Harness  
**Where**: `.opencode/skills/optimize-meta-harness/`  
**How**: Load skill → Choose workflow → Follow steps  
**When**: Monthly maintenance or when issues arise

---

## Quick Start Guide

### Step 1: Load the Skill

```
skill optimize-meta-harness
```

### Step 2: Choose Your Task

**I want to...**

- **Check if everything is OK** → Run Health Check (Workflow 1)
- **Fix documentation** → Run Documentation Analysis (Workflow 2)
- **Reorganize directories** → Run Structure Optimization (Workflow 3)
- **Improve workflows** → Run Workflow Enhancement (Workflow 4)
- **Set up monitoring** → Run Continuous Improvement (Workflow 5)

### Step 3: Follow the Workflow

Each workflow has:
- Clear goal
- Step-by-step instructions
- Tools to use
- Expected output
- Success criteria

---

## Most Common: Health Check

**Time**: 15-30 minutes  
**Goal**: Assess overall harness health

**Steps**:
1. Read all META.md files (5 files)
2. For each META.md, check:
   - Has purpose statement? (Yes/No)
   - Has target audience? (Yes/No)
   - Has rules? (Yes/No)
   - Has structure? (Yes/No)
3. Count words (target: 100-500)
4. Score each (0-4)
5. Document findings

**Template**:
```markdown
## Health Check Results

| File | Score | Words | Status |
|------|-------|-------|--------|
| .project_development/META.md | 4/4 | 250 | ✅ |
| .experiments/META.md | 4/4 | 200 | ✅ |
| .sandbox/META.md | 4/4 | 220 | ✅ |
| .tests_sandbox/META.md | 4/4 | 450 | ✅ |
| .development_tools/META.md | 4/4 | 180 | ✅ |

Status: All healthy
```

---

## Common Scenarios

### Scenario 1: "Something feels slow"

**Problem**: Agents taking too long to complete tasks  
**Solution**: Run Workflow 4 (Workflow Enhancement)

**Quick steps**:
1. Identify slow workflow
2. Count steps
3. Find bottlenecks
4. Eliminate unnecessary steps
5. Add templates
6. Test improvement

---

### Scenario 2: "Nobody uses the sandbox"

**Problem**: Agents not using correct directories  
**Solution**: Run Workflow 2 (Documentation Analysis) + Update META.md

**Quick steps**:
1. Check if META.md is clear
2. Add decision tree
3. Include examples
4. Clarify when to use
5. Test with sample task

---

### Scenario 3: "Documentation is outdated"

**Problem**: META.md files don't match reality  
**Solution**: Run Workflow 2 (Documentation Analysis)

**Quick steps**:
1. Read each META.md
2. Compare to actual structure
3. Update mismatches
4. Add "last updated" date
5. Set review reminder

---

### Scenario 4: "Monthly check-in"

**Problem**: Need regular maintenance  
**Solution**: Run Workflow 1 (Health Check) + Workflow 5 (Continuous Improvement)

**Quick steps**:
1. Run health check
2. Compare to last month
3. Note trends
4. Update metrics
5. Schedule next review

---

## Templates at a Glance

### Quick Health Check Template

```markdown
# Quick Health Check
Date: YYYY-MM-DD
Reviewer: [Your name]

## Scores (0-4 each)
- .project_development: _/4
- .experiments: _/4
- .sandbox: _/4
- .tests_sandbox: _/4
- .development_tools: _/4

## Issues
- Critical: 0
- Warnings: 0

## Status: [HEALTHY / NEEDS ATTENTION / CRITICAL]
```

### Quick Fix Template

```markdown
## Issue: [Name]

**What**: [What's wrong]
**Where**: [Which file/dir]
**Impact**: [Who/what affected]

**Fix**: [What to do]
**Time**: [How long]
**Priority**: [High/Medium/Low]

**Done when**: [Success criteria]
```

---

## Decision Tree

```\nNeed to optimize?\n│\n├─ Don't know current state?\n│  └─→ Health Check (Workflow 1)\n│\n├─ Documentation unclear?\n│  └─→ Documentation Analysis (Workflow 2)\n│\n├─ Structure confusing?\n│  └─→ Structure Optimization (Workflow 3)\n│\n├─ Workflows slow?\n│  └─→ Workflow Enhancement (Workflow 4)\n│\n└─ Want ongoing improvement?\n   └─→ Continuous Improvement (Workflow 5)\n```

---

## Success Indicators

✅ **Good signs**:
- All META.md scores ≥ 3/4
- Clear decision paths
- Agents use correct directories
- Workflows complete quickly
- Few errors
- Regular updates

⚠️ **Warning signs**:
- META.md scores < 3/4
- Confusion about where to work
- Workflows have many steps
- Frequent errors
- Outdated documentation
- No regular reviews

---

## Next Steps

1. **Load the skill**: `skill optimize-meta-harness`
2. **Pick a workflow**: Start with Health Check
3. **Follow steps**: Use templates
4. **Document**: Record findings
5. **Maintain**: Schedule reviews

---

## Resources

- **Full guide**: `workflow.md`
- **Checklist**: `checklist.md`
- **Templates**: `templates/`
- **Examples**: `examples/`
- **Master doc**: `META_HARNESS.md`

---

## Need Help?

1. Check `README.md` for overview
2. Review `examples/` for patterns
3. Use `templates/` for consistency
4. Follow `checklist.md` for completeness

---

**Ready? Start with Workflow 1: Health Check!**
