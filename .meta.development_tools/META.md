# Development Tools - Agent X

> **Purpose**: Development tools and utilities  
> **Target**: AI agents (opencode) and developers  
> **Rule**: Document and test all tools

---

## Purpose

Contains:
- MCP (Model Context Protocol) tools
- Development scripts
- Code generation utilities
- Automation helpers
- Debugging aids

---

## Structure

```
.meta.development_tools/
├── META.md          # This file
├── mcp/             # MCP tools
│   └── <tool-name>/
│       ├── META.md  # Tool docs
│       └── tool.py  # Implementation
└── scripts/         # Utility scripts
```

---

## MCP Tools

### Creating New Tool

```\n1. Create: .meta.development_tools/mcp/<tool-name>/\n2. Document: Add META.md\n3. Implement: Follow existing patterns\n4. Test: In sandbox first\n5. Register: Update table below\n```\n\n### Tool Requirements\n- Clear purpose and scope\n- Well-defined inputs/outputs\n- Error handling\n- Documentation\n- Test coverage\n\n---

## Rules\n\n**DO**: Document thoroughly, follow patterns, test first, keep modular  \n**DON'T**: Create without purpose, modify untested, leave undocumented, add dependencies\n\n---

## Available Tools\n\n| Tool | Purpose | Location | Status |\n|------|---------|----------|--------|\n| *(Add tools as created)* | | | |\n\n---

## Maintenance\n\n- Review periodically\n- Remove unused tools\n- Update documentation\n- Ensure Python compatibility\n\n---

**Version**: 2.0.0 (lazy-optimized) | **Lines**: 50 (reduced from 109)\n\n