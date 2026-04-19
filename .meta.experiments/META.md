# Experiments - Agent X

> **Purpose**: Experimental workspace for testing new features, ideas, and approaches
> **Target**: AI agents (opencode) working on Agent-X
> **MANDATORY**: All experiments should be documented and either integrated or cleaned up

---

## Purpose

The `.experiments/` directory is a sandbox for:
- Testing new libraries or dependencies
- Prototyping features before integration
- Exploring alternative implementations
- Validating hypotheses about code structure or performance

---

## Rules

### DO
- Create dated experiment folders (e.g., `2024-04-19-feature-x/`)
- Document findings in experiment README files
- Clean up or integrate experiments after validation
- Use experiments to validate TDD approaches before `.tests_sandbox/`

### DON'T
- Leave experiments in an broken state
- Mix experimental code with production code
- Forget to document what you learned

---

## Structure

```
.experiments/
├── META.md                    # This file
├── YYYY-MM-DD-experiment/     # Dated experiment folder
│   ├── README.md             # Purpose and findings
│   └── code/                 # Experimental code
```

---

## Lifecycle

1. **Create**: Start with a clear hypothesis or goal
2. **Document**: Write what you're testing and why
3. **Validate**: Test the hypothesis
4. **Decide**: Integrate, iterate, or discard
5. **Clean**: Remove or archive completed experiments

---

## Examples

### Example 1: Testing a New LLM Provider

**Goal**: Validate integration with a new LLM provider before adding as dependency

**Structure**:
```
.experiments/
└── 2024-04-19-llm-provider-test/
    ├── README.md
    └── test_provider.py
```

**README.md content**:
```markdown
# LLM Provider Test

**Hypothesis**: Provider X offers better latency than current provider

**Date**: 2024-04-19

## Approach
- Test response times with 100 requests
- Compare error rates
- Evaluate cost per token

## Results
- ✅ Latency: 150ms avg (vs 200ms current)
- ❌ Error rate: 2% (vs 0.5% current)
- ✅ Cost: $0.50/1M tokens (vs $2.00 current)

## Decision
Discard - error rate too high for production use

## Next Steps
None - experiment closed
```

### Example 2: Prototyping a New Command

**Goal**: Test a new `deploy` command implementation

**Structure**:
```
.experiments/
└── 2024-04-19-deploy-command/
    ├── README.md
    └── deploy_cmd.py
```

**Process**:
1. Create experiment folder with hypothesis
2. Prototype command in isolation
3. Test with `.tests_sandbox/` TDD approach
4. If successful, move to `.sandbox/` for integration
5. Document findings and clean up

### Example 3: Exploring Alternative Implementation

**Goal**: Test if async improves performance for command parsing

**Approach**:
```python
# .experiments/2024-04-19-async-parser/parser_test.py
import asyncio
import time

async def test_async_parsing():
    """Compare async vs sync parsing performance"""
    start = time.time()
    # Test implementation
    elapsed = time.time() - start
    print(f"Async: {elapsed}ms")
```

**Outcome**: Document performance metrics and recommend async or sync

---

## Integration Workflow

When experiment succeeds:

```
1. Document success in experiment README
2. Create test in .tests_sandbox/ for new feature
3. Move validated code to .sandbox/ for integration
4. Update main documentation
5. Archive or remove experiment folder
```

**Archive decision tree**:
- ✅ Success → Integrate via `.sandbox/`, then archive experiment
- ⚠️ Partial → Document learnings, iterate or discard
- ❌ Failure → Document why, remove experiment

---
