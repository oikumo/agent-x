"""
Script to create 30+ tickets for Agent-X project related to real development tasks.
These tickets cover: LLM managers, agents, RAG, graph agents, MCP, testing, docs, etc.
"""

import json
import sys
from pathlib import Path

# Read the project structure to create relevant tickets
project_root = Path("/home/oikumo/develop/projects/agent-x")

tickets = [
    # Release 1.0.0 Epic - Core Infrastructure (SCRUM-1)
    {"type": "Epic", "summary": "Agent-x release 1.0.0", "status": "En curso"},
    {"type": "Epic", "summary": "Agent-x release 1.1.0", "status": "En curso"},
    
    # LLM Manager tickets
    {"type": "Tarea", "summary": "Implement LLM factory pattern for provider abstraction", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add OpenAI GPT-4o provider implementation", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add Anthropic Claude provider implementation", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add Ollama local LLM provider support", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement rate limiting for LLM API calls", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add retry logic with exponential backoff", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create token usage tracking and logging", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement LLM response caching layer", "status": "Tareas por hacer"},
    
    # Agent core tickets
    {"type": "Historia", "summary": "Implement base agent class with conversation memory", "status": "Tareas por hacer"},
    {"type": "Historia", "summary": "Add chat agent with tool calling support", "status": "Tareas por hacer"},
    {"type": "Historia", "summary": "Implement ReAct agent for reasoning loops", "status": "Tareas por hacer"},
    {"type": "Historia", "summary": "Create graph-based agent using LangGraph", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add conversation history persistence to SQLite", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement agent state management", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create agent configuration schema", "status": "Tareas por hacer"},
    
    # RAG tickets
    {"type": "Epic", "summary": "RAG module implementation", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement document loader for PDF files", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement document loader for Markdown files", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add text chunking with overlap strategy", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement ChromaDB vector store integration", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add FAISS vector store as alternative", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create embedding service with OpenAI embeddings", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add local embeddings with sentence-transformers", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement semantic search with reranking", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create RAG query pipeline with context compression", "status": "Tareas por hacer"},
    
    # MCP (Model Context Protocol) tickets
    {"type": "Epic", "summary": "MCP local servers implementation", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create MCP server for issue tracker system integration", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create MCP server for Confluence integration", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create MCP server for filesystem operations", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create MCP server for GitHub integration", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement MCP tool discovery and registration", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add MCP resource management", "status": "Tareas por hacer"},
    
    # Testing and Quality
    {"type": "Tarea", "summary": "Set up pytest framework with fixtures", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create unit tests for LLM factory", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create integration tests for RAG pipeline", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add code coverage reporting", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Set up pre-commit hooks with ruff and mypy", "status": "Tareas por hacer"},
    
    # Documentation
    {"type": "Tarea", "summary": "Write API documentation with Sphinx", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Create getting started guide", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Document agent architecture and design decisions", "status": "Tareas por hacer"},
    
    # Infrastructure
    {"type": "Tarea", "summary": "Create Docker image for Agent-X", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Set up CI/CD pipeline with GitHub Actions", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add structured logging with JSON output", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement configuration management with pydantic", "status": "Tareas por hacer"},
    
    # UI/CLI
    {"type": "Historia", "summary": "Create interactive CLI with Rich library", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add REPL with syntax highlighting", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement command history and auto-completion", "status": "Tareas por hacer"},
    
    # Performance
    {"type": "Tarea", "summary": "Add async support for LLM calls", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement connection pooling for vector stores", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add performance profiling and benchmarking", "status": "Tareas por hacer"},
    
    # Security
    {"type": "Tarea", "summary": "Add API key encryption at rest", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Implement secrets management with dotenv", "status": "Tareas por hacer"},
    {"type": "Tarea", "summary": "Add input validation and sanitization", "status": "Tareas por hacer"},
]

print(json.dumps(tickets, indent=2))
