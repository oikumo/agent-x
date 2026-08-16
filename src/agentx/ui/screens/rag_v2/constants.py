"""RagV2 display constants (feature_027; reworked for feature_029 slash grammar).

Single source of truth for v2 display strings (analysis_001 surprise #3:
v1 constants.py vs FEATURE.md extract-preset drift — v2 keeps constants here
only, no FEATURE.md shadow).
"""

from __future__ import annotations

RAG_V2_PROMPT = "(rag-v2)"
RAG_V2_BANNER = "RAG v2 — retrieve, offload, and delegate"
# feature_029: the numeric menu is gone — bare text is chat, `/…` is a command.
RAG_V2_MENU = "Type a question to ask the active repository, or /help for commands."
RAG_V2_HELP = (
    "Commands:\n"
    "  /search <question>                ask the active repository (same as typing a question)\n"
    "  /repos                            list repositories\n"
    "  /use [id]                         pick a repository (no arg = interactive list)\n"
    "  /create [name]                    create a repository (no arg = prompt)\n"
    "  /ingest <web|pdf|md> <url|path>   ingest into the active repository\n"
    "  /status                           show the active repository + ingestion state\n"
    "  /reset                            start a new conversation\n"
    "  /quit                             return to the main menu"
)
