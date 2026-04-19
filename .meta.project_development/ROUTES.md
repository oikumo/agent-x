# ROUTES - Agent-X

> **Last Updated**: April 19, 2026
> **Version**: 0.2.0
> **Python**: 3.14+
> **Package Manager**: uv

---

## Project Overview

Defined in README.md file.

---

## Module Index

| Module | Files | Description |
|--------|-------|-------------|
| [src/common/](#srccommon) | 3 | Shared utilities and security |
| [src/controllers/](#srccontrollers) | 9 | Command routing and controllers |
| [src/model/](#srcmodel) | 5 | Data persistence, SQLite, session management |
| [src/services/](#srcservices) | 24 | AI/LLM service layer with providers |
| [src/views/](#srcviews) | 8 | User interface components |

---

## src/common/

**Path**: `src/common/`

| File | Description |
|------|-------------|
| `utils.py` | General utilities, safe_int, console clearing, directory management |
| `security.py` | Security constants and deletion safeguards |
| `__init__.py` | Package initialization |

---

## src/controllers/

**Path**: `src/controllers/`

| File | Description |
|------|-------------|
| `chat_controller/chat_controller.py` | Handles chat-specific commands |
| `chat_controller/__init__.py` | Package initialization for chat controller |
| `main_controller/main_controller.py` | Core command registry and REPL integration |
| `main_controller/commands.py` | Command implementations |
| `main_controller/commands_base.py` | Base command classes |
| `main_controller/commands_parser.py` | Command parsing logic |
| `main_controller/repl.py` | REPL application loop |
| `main_controller/__init__.py` | Package initialization for main controller |
| `__init__.py` | Package initialization |

---

## src/model/

**Path**: `src/model/`

| File | Description |
|------|-------------|
| `db/session_db.py` | SQLite session database implementation |
| `db/__init__.py` | Package initialization for db module |
| `session/session.py` | Session lifecycle management |
| `session/__init__.py` | Package initialization for session module |
| `__init__.py` | Package initialization |

---

## src/services/

**Path**: `src/services/`

| File | Description |
|------|-------------|
| `__init__.py` | Package initialization |
| `ai/__init__.py` | Package initialization for AI services |
| `ai/providers.py` | LLM provider factory and strategy interface |
| `ai/services.py` | High-level service orchestration |
| `ai/vectorstores/__init__.py` | Package initialization for vectorstores |
| `ai/vectorstores/vectorstore_chroma.py` | ChromaDB wrapper |
| `ai/vectorstores/vectorstore_pinecone.py` | Pinecone wrapper |
| `ai/cloud/__init__.py` | Package initialization for cloud providers |
| `ai/cloud/google/__init__.py` | Package initialization for Google provider |
| `ai/cloud/google/google_gemini.py` | Google Gemini LLM provider |
| `ai/cloud/google/google.md` | Google provider documentation |
| `ai/cloud/open_ai/__init__.py` | Package initialization for OpenAI provider |
| `ai/cloud/open_ai/open_ai_gpt.py` | OpenAI GPT LLM provider |
| `ai/cloud/open_ai/open_ai.md` | OpenAI provider documentation |
| `ai/local/__init__.py` | Package initialization for local providers |
| `ai/local/llama_cpp/__init__.py` | Package initialization for LlamaCpp provider |
| `ai/local/llama_cpp/llamacpp.py` | LlamaCpp LLM provider |
| `ai/local/llama_cpp/llamacpp_config.py` | LlamaCpp configuration |
| `ai/local/llama_cpp/llama_cpp_factory.py` | Pre-configured LlamaCpp factory |
| `ai/local/ollama/__init__.py` | Package initialization for Ollama provider |
| `ai/local/ollama/ollama.py` | Ollama LLM provider |
| `ai/local/ollama/ollama_embeddings.py` | Ollama embeddings provider |
| `ai/local/ollama/ollama_factory.py` | Ollama model manager |

---

## src/views/

**Path**: `src/views/`

| File | Description |
|------|-------------|
| `chat_view/chat_view.py` | Chat UI component |
| `chat_view/chat_loop.py` | Chat REPL loop implementation |
| `chat_view/__init__.py` | Package initialization for chat view |
| `main_view/main_view.py` | Main application UI |
| `main_view/__init__.py` | Package initialization for main view |
| `src/views/common/console.py` | Shared console output utilities |
| `src/views/common/__init__.py` | Package initialization for common views |
| `src/views/__init__.py` | Package initialization |

---

## Meta

**Path**: `/.project_development/`

| File | Description |
|------|-------------|

---

## Architecture

**Current Version**: v0.2.0 - MVC Architecture (April 2026)

- **Model** (`src/model/`): Data persistence, SQLite, session management
- **View** (`src/views/`): User interface components (chat view, main view)
- **Controller** (`src/controllers/`): Business logic and command routing
- **Services** (`src/services/`): AI/LLM service layer with providers and vectorstores
- **Common** (`src/common/`): Shared utilities and security helpers
