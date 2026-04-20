# Agent-X

> **Version**: 0.3.0
> **Python**: 3.14+
> **Package Manager**: uv

---

## What is Agent-X?

Agent-X is a Python-based LLM agent framework with a REPL (Read-Eval-Print Loop) interface, created strictly for educational purposes. This project is free to use for everyone, including enterprise users, under the Apache 2.0 License.

It lets you interact with language models through a command-line shell, supporting chat, web search, PDF Q&A, function calling, and graph-based reasoning workflows. 

The development of this project is assisted by opencode coding agent (https://opencode.ai/).

---

## ⚠️ Important Legal Notice

**THIS IS AN EDUCATIONAL PROJECT ONLY**

Agent-X is created solely for educational and experimental purposes. It is not affiliated with, endorsed by, or sponsored by any of the companies or projects mentioned herein.

All product names, logos, brands, trademarks, and registered trademarks mentioned in this documentation or code are the property of their respective owners. Use of these names, logos, brands, and trademarks does not imply endorsement.

Specifically, but not limited to:
- OpenAI, OpenRouter, Ollama, LlamaCpp, Qwen are trademarks of their respective owners
- LangChain, LangGraph, FAISS, Pinecone, Chroma, Tavily are trademarks of their respective owners
- Any other third-party products or services mentioned are trademarks of their respective owners

This project may reference these trademarks solely for the purpose of describing compatibility or educational examples, which is permissible under nominative fair use. No association with or endorsement by these trademark owners is implied or intended.

Users are solely responsible for ensuring their use of any third-party services (such as OpenAI API, etc.) complies with those services' terms of service and applicable laws.

---

## Getting Started

### Prerequisites

- Python 3.14 or later
- `uv` package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agent-x

# Install dependencies
uv sync
```

### API Keys

Agent-X requires at least an **OpenRouter API key** to run the default chat agent. Other features may need additional keys. Set them in a `.env` file:

```env
# Required for default chat
OPENROUTER_API_KEY=your_key_here

# For web search agents
TAVILY_API_KEY=your_key_here

# For OpenAI models
OPENAI_API_KEY=your_key_here
```

If `OPENROUTER_API_KEY` is not set, the application will prompt for it on startup.

### Starting the Application

```bash
python main.py
```

You will see the Agent-X banner and the prompt:

```
(agent-x) >
```

Type `help` to see all available commands, or `quit` to exit.

---

## The REPL Interface

Agent-X uses an interactive command loop. Each line you enter is parsed as a command with optional arguments:

```
(agent-x) > command arg1 arg2
```

After each command, Agent-X prints the command history for the current session.

### Exiting

- Type `quit`
- Press `Ctrl+C`
- Press `Ctrl+D` (EOF)

---

## Commands Reference

### Utility Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `help` | `help` | Lists all available commands with descriptions |
| `quit` | `quit` | Exits the application |
| `clear` | `clear` | Clears the terminal screen |
| `read` | `read <filename>` | Reads and displays the contents of a file |
| `sum` | `sum <a> <b>` | Adds two integers together |

**Examples:**

```
(agent-x) > help
(agent-x) > read README.md
(agent-x) > sum 42 58
100
(agent-x) > clear
(agent-x) > quit
```

---

### AI Chat

The `chat` command is the primary way to interact with LLMs. It supports three modes:

#### Single-Query Chat

```
(agent-x) > chat What is Python?
```

Sends your query to the LLM and streams back the response with token-per-second metrics.

#### Interactive Chat

```
(agent-x) > chat
Starting interactive chat (type 'quit' or 'exit' to end):
> Tell me a joke
> quit
```

Enters a persistent conversation loop. Message history is preserved between turns. Type `quit` or `exit` to leave.

#### Chat with Model Selection

```
(agent-x) > chat --model gpt-4 Explain quantum computing
```

Uses a specific model for the query. The `--model` flag can appear anywhere in the command:

```
(agent-x) > chat Explain quantum computing --model gpt-4
(agent-x) > chat --model claude-3-opus --model gpt-4 Hello
```

When multiple `--model` flags are given, the last one wins. If `--model` is provided without a query, it starts interactive chat with that model.

**Streaming Metrics:** After each response, Agent-X displays performance metrics:

```
150 tokens in 3.2s (46.9 tok/s)
```

---

### Web Search

| Command | Usage | Description |
|---------|-------|-------------|
| `search` | `search` | Launches a ReAct web search agent using Tavily |

```
(agent-x) > search
```

Starts an interactive web search agent that can browse the internet and provide sourced answers.

---

### PDF RAG

| Command | Usage | Description |
|---------|-------|-------------|
| `rag` | `rag <query>` | Queries a PDF document using Retrieval-Augmented Generation |

```
(agent-x) > rag What is the main topic of this document?
```

Loads the configured PDF, creates a FAISS vector index, and retrieves relevant passages to answer your query.

---

### Function Calling

| Command | Usage | Description |
|---------|-------|-------------|
| `function` | `function` | Demonstrates AI-powered function dispatch |

```
(agent-x) > function
```

Uses Ollama tool calling to intelligently route your request to the appropriate function (weather, game recommendations, etc.).

---

### Router Agents

| Command | Usage | Description |
|---------|-------|-------------|
| `router` | `router` | Runs an agent that routes between CSV and QR code agents |

```
(agent-x) > router
```

---

### ReAct Agent with Tools

| Command | Usage | Description |
|---------|-------|-------------|
| `react` | `react` | Runs a ReAct agent with local LLM and tools |

```
(agent-x) > react
```

Executes a Reason+Act loop using a local LlamaCpp model (Qwen 2.5) with tool integration.

---

### LangGraph Workflows

| Command | Usage | Description |
|---------|-------|-------------|
| `graph` | `graph` | Runs a simple LangGraph ReAct workflow |
| `chains` | `chains` | Runs a LangGraph reflector chains graph (generate ↔ reflect loop) |
| `reflex` | `reflex` | Runs a LangGraph reflexion agent (draft → execute → revise) |

```
(agent-x) > graph
(agent-x) > chains
(agent-x) > reflex
```

These commands demonstrate increasingly sophisticated graph-based reasoning patterns using LangGraph state machines.

---

## Session Management

Each Agent-X session creates:
- A timestamped directory under `local_sessions/`
- A SQLite database for command history

Sessions are isolated and command history is persisted per session.

---

## Troubleshooting

### "Unknown command" error
Check your spelling with `help`. Commands are case-sensitive.

### API key prompt on startup
Set `OPENROUTER_API_KEY` in your `.env` file to avoid the interactive prompt.

### LLM connection errors
- Verify your API key is valid
- Check your internet connection
- For local models, ensure Ollama or LlamaCpp is properly configured

### RAG PDF errors
- Ensure the PDF file exists at the configured path (`_resources/react.pdf` by default)
- Check that required embeddings dependencies are installed

---

## Architecture Overview

```
main.py
└── create_controller()
    └── MainController (registers 14 commands)
        └── ReplApp(controller).run()
            ├── Model(session) - command history
            ├── Loop: parse → find → run → apply → history
            └── Exit on quit / Ctrl+C / Ctrl+D
```

### Design Patterns

- **Command Pattern**: Every REPL command implements a consistent `run()` interface
- **Factory Pattern**: Agents are created via factory functions, decoupling instantiation from usage
- **Strategy Pattern**: LLM providers (OpenRouter, OpenAI, LlamaCpp) are interchangeable
- **State Machine**: LangGraph workflows use `StateGraph` for multi-step reasoning

---

## Development with Meta Project Harness

Agent-X uses the **Meta Project Harness** - a structured development system optimized for AI-assisted development.

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `.meta.project_development/` | Rules, standards, workflows |
| `.meta.sandbox/` | Safe workspace for code modifications |
| `.meta.tests_sandbox/` | TDD workspace (Kent Beck methodology) |
| `.meta.experiments/` | Experimental features and prototyping |
| `.meta.development_tools/` | Development utilities and MCP tools |
| `.meta.knowledge_base/` | RAG knowledge storage |
| `.meta.reflection/` | Test logs & capability assessment |

### Knowledge Base (MCP Tool)

The project includes a **self-evolving knowledge base** accessible via MCP (Model Context Protocol):

- **Location**: `.meta.knowledge_base/`
- **Purpose**: Stores project patterns, findings, and decisions
- **Features**: RAG-enabled, auto-correcting, confidence scoring
- **For AI Agents**: Automatically activated via MCP tools

**MCP Tools:**
- `kb_search`: Search knowledge base
- `kb_ask`: Ask questions with RAG context
- `kb_add_entry`: Document new patterns
- `kb_correct`: Correct existing knowledge
- `kb_evolve`: Run evolution cycle
- `kb_stats`: Monitor KB health

**Documentation**: See `.meta.knowledge_base/META.md`

### For AI Agents

If you're an AI agent working on this project:
1. Read `AGENTS.md` first - it contains mandatory rules
2. Review `META_HARNESS.md` for complete harness documentation
3. **Use the Knowledge Base** - Query with `kb_ask` before starting work
4. Always work in safe spaces (`.meta.sandbox/`, `.meta.experiments/`)
5. Follow TDD in `.meta.tests_sandbox/`
6. Never modify production code directly
7. **Document discoveries** - Add to knowledge base after completing tasks

### For Human Developers

- **Getting Started**: See `META_HARNESS.md` for development workflows
- **Quick Reference**: `.meta.project_development/QUICK_REFERENCE.md`
- **Standards**: `.meta.project_development/` directory
- **Knowledge Base**: `.meta.knowledge_base/META.md`

---

## License

Agent-X is provided as-is for educational and experimental purposes.
