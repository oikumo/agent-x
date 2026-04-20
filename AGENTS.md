# AGENTS.md - Agent-X System Agent Rules

> **Your primary entry point. Read this FIRST before any task.**

---

## ⚠️ Core Directives (NON-NEGOTIABLE)

| # | Directive | What It Means |
|---|-----------|---------------|
| 1 | **NEVER commit or push** | Not even if user asks |
| 2 | **NEVER add dependencies** | Use what exists; explicit approval required for exceptions |
| 3 | **NEVER modify `.env`** | Or any file likely to contain secrets/credentials |
| 4 | **ALWAYS check `git log`** | Before making ANY changes |
| 5 | **NEVER modify `tests/`** | Use `.meta.tests_sandbox/` for new tests (requires approval) |
| 6 | **Use `uv` & `pyproject.toml`** | For all dependency management; avoid pin drift |

---

## What is the Meta Project Harness?

A structured development system optimized for AI-assisted development providing:
- **Safe spaces** to work without affecting production
- **Clear workflows** for consistent, high-quality output
- **Comprehensive documentation** at every level
- **Quality gates** to ensure correctness

### Directory Structure
```
agent-x/
├── META_HARNESS.md # Master documentation
├── AGENTS.md # This file
├── .meta.project_development/ # Development standards
├── .meta.sandbox/ # Your safe workspace
├── .meta.experiments/ # Experimental features
├── .meta.tests_sandbox/ # TDD workspace
├── .meta.development_tools/ # Development utilities
├── .meta.knowledge_base/ # RAG knowledge base
└── .meta.reflection/ # Capability test logs
```

**Rule:** All harness directories start with `.meta.` and contain a `META.md` file you must read first.

---

## Your Workflow

### Before Any Task
1. **Check `git log`** - `git log --oneline -10`
2. **Read relevant META.md files** - Know the rules
3. **Identify correct directory** - Where to work
4. **Query knowledge base** - Use `kb_ask()` for guidance (optional)

### During Task
5. **Plan your approach** - Smallest viable change
6. **Execute in safe space** - Copy production code to `.meta.sandbox/`
7. **Test using TDD** - In `.meta.tests_sandbox/` (RED → GREEN → REFACTOR)

### After Task
8. **Document your changes** - Update META.md, add examples
9. **Store knowledge** - Use `kb_add_entry()` to document patterns
10. **Report to user** - What you did, test results, next steps

---

## Decision Tree

```
Need to...
├─ Modify code?       → Work in .meta.sandbox/
├─ Write tests?       → Use .meta.tests_sandbox/ (TDD)
├─ Test new idea?     → Use .meta.experiments/
├─ Use/create tools?  → Check .meta.development_tools/
├─ Ask for guidance?  → Use kb_ask() from knowledge base
└─ Understand rules?  → Read META.md files first
```

---

## Quality Gates

Before reporting completion, verify:
- [ ] Read relevant META.md files
- [ ] Checked `git log`
- [ ] Worked in correct directory
- [ ] Followed TDD (if applicable)
- [ ] All tests pass
- [ ] Documented changes
- [ ] Stored new knowledge (if applicable)
- [ ] Cleaned workspace
- [ ] No secrets exposed
- [ ] No production code modified

---

## Tools Available

### Core Tools
`read`, `glob`, `bash`, `edit`, `write`, `task`

### Knowledge Base Tools (via MCP)
```python
from .meta.development_tools.mcp.rag_tool import (
    rag_search, rag_ask, rag_add_entry, rag_correct, rag_evolve, rag_stats
)

# Before task: Ask for guidance
result = rag_ask("Where should I implement this feature?")

# After task: Document discovery
result = rag_add_entry(
    entry_type="pattern",
    category="workflow",
    title="My Discovery",
    finding="What I found",
    solution="How to handle it"
)
```

---

## Common Scenarios

### Scenario 1: Add Feature
```bash
1. Read META_HARNESS.md
2. Ask KB: rag_ask("Where to implement this?")
3. Create experiment in .meta.experiments/
4. Write tests in .meta.tests_sandbox/
5. Implement in .meta.sandbox/
6. Document: rag_add_entry(...)
7. Report to user
```

### Scenario 2: Fix Bug
```bash
1. Check git log
2. Search KB: rag_search("similar bug")
3. Reproduce in .meta.sandbox/
4. Write failing test in .meta.tests_sandbox/
5. Fix in .meta.sandbox/
6. Document: rag_add_entry(type="finding", ...)
7. Report to user
```

### Scenario 3: Refactor Code
```bash
1. Copy to .meta.sandbox/
2. Write behavior tests
3. Refactor
4. Verify tests pass
5. Document: rag_add_entry(type="pattern", ...)
```

### Scenario 4: Maintenance
```bash
1. Run health check: rag_stats()
2. Run evolution: rag_evolve()
3. Review META.md files
4. Update as needed
5. Document changes
```

### Scenario 5: Capability Testing
```bash
1. Run reflection test: skill meta-harness-reflection
2. Review generated log: .meta.reflection/<timestamp>_log.md
3. Identify knowledge gaps
4. Update KB if needed
5. Re-test after improvements
```

---

## Available Skills

### optimize-meta-harness
Use to analyze and optimize the harness itself:
```bash
skill optimize-meta-harness
```
**Workflows:** Health Check → Documentation Analysis → Structure Optimization → Workflow Enhancement → Continuous Improvement

### meta-harness-reflection
Use to test agent's knowledge base usage and harness comprehension:
```bash
skill meta-harness-reflection
```
**Modes:** Interactive (manual answers) | Automated (KB search)
**Output:** Timestamped logs in `.meta.reflection/`
**Frequency:** Monthly or after KB updates

---

## Knowledge Base Integration

### Available Tools

| Tool | Function | Use Case |
|------|----------|----------|
| `kb_search` | `rag_search(query, top_k)` | Find specific patterns |
| `kb_ask` | `rag_ask(question)` | Get RAG-augmented guidance |
| `kb_add_entry` | `rag_add_entry(...)` | Document discoveries |
| `kb_correct` | `rag_correct(entry_id, reason, new_finding)` | Auto-correct knowledge |
| `kb_evolve` | `rag_evolve()` | Run evolution cycle |
| `kb_stats` | `rag_stats()` | Monitor KB health |

### Example Usage
```python
# Search for TDD patterns
result = rag_search("TDD workflow", top_k=3, category="workflow")

# Ask a question (RAG-augmented)
result = rag_ask("Where should I write tests?")
print(result["augmented_prompt"])

# Add new knowledge
result = rag_add_entry(
    entry_type="pattern",
    category="workflow",
    title="Feature Implementation",
    finding="Work in .meta.sandbox/",
    solution="Copy → Modify → Test",
    confidence=0.95
)

# Get statistics
result = rag_stats()
print(f"Total entries: {result['total_entries']}")
```

### Response Format
All tools return standardized JSON:
```json
{
  "success": true,
  "message": "Human-readable message",
  ... (tool-specific fields)
}
```

---

## When Things Go Wrong

| Situation | Action |
|-----------|--------|
| **Unsure** | Stop → Re-read META.md → Check examples → Ask KB (`rag_ask()`) |
| **Made mistake** | Document → Don't hide → Propose fix → Learn |
| **Production affected** | Stop → Document → Propose rollback → Get approval |
| **No KB results** | Try broader query → Check spelling → Verify DB exists |

---

## Resources

| Resource | Purpose |
|----------|---------|
| `META_HARNESS.md` | Complete harness documentation |
| `.meta.project_development/META.md` | Development standards |
| `.meta.project_development/QUICK_REFERENCE.md` | Quick decision guide |
| `.meta.sandbox/META.md` | Safe workspace rules |
| `.meta.tests_sandbox/META.md` | TDD methodology (Kent Beck) |
| `.meta.development_tools/mcp/README.md` | MCP KB tools documentation |
| `.meta.development_tools/mcp/INTEGRATION.md` | KB integration guide |
| `.meta.knowledge_base/META.md` | Knowledge base usage |
| `.meta.reflection/README.md` | Reflection test documentation |
| `README.md` | Project overview |

---

> **READ META.md FIRST** · **WORK IN SAFE SPACES** · **TEST BEFORE PROPOSING** · **DOCUMENT EVERYTHING** · **STORE KNOWLEDGE** · **NEVER COMMIT WITHOUT PERMISSION**

---

**Version**: 1.4.0 (2026-04-19) - Added meta-harness-reflection skill
**Maintained by**: opencode AI agent
**License**: Apache 2.0
