# Development Tools - Agent X

> **Purpose**: Collection of development tools, scripts, and utilities
> **Target**: AI agents (opencode) and human developers working on Agent-X
> **MANDATORY**: All tools must be documented and follow project conventions

---

## Purpose

The `.development_tools/` directory contains:
- MCP (Model Context Protocol) tools
- Development scripts
- Code generation utilities
- Automation helpers
- Debugging aids

---

## Structure

```
.development_tools/
├── META.md                 # This file
├── mcp/                    # MCP tool implementations
│   └── <tool-name>/
│       ├── META.md         # Tool-specific documentation
│       └── tool.py         # Tool implementation
└── scripts/                # Utility scripts
```

---

## MCP Tools

MCP tools provide structured interfaces for AI agents to interact with external systems.

### Creating a New MCP Tool

1. Create directory: `.development_tools/mcp/<tool-name>/`
2. Add META.md with tool documentation
3. Implement tool following existing patterns
4. Test in sandbox before deployment
5. Document usage in main README

### Tool Structure

Each MCP tool should have:
- Clear purpose and scope
- Well-defined inputs and outputs
- Error handling
- Documentation
- Test coverage

---

## Rules

### DO
- Document all tools thoroughly
- Follow existing tool patterns
- Test tools in sandbox first
- Keep tools modular and focused
- Use `uv` for dependency management

### DON'T
- Create tools without clear purpose
- Modify tools without testing
- Leave tools undocumented
- Add unnecessary dependencies

---

## Available Tools

To check for available tools, explore the directory structure:

```bash
# List all MCP tools
ls .development_tools/mcp/

# List all scripts
ls .development_tools/scripts/
```

**Current tools**: *(Populate this table as tools are created)*

| Tool | Purpose | Location | Status |
|------|---------|----------|--------|
| *(No tools registered yet)* | | | |

### Tool Registration Template

When creating a new tool, add it to this table:

```markdown
| tool-name | Brief description | `.development_tools/mcp/tool-name/` | ✅ Active |
```

---

## Maintenance

- Review tools periodically
- Remove unused tools
- Update documentation
- Ensure compatibility with current Python version

---
