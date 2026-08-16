"""RagV2 display constants (feature_027).

Single source of truth for v2 display strings (analysis_001 surprise #3:
v1 constants.py vs FEATURE.md extract-preset drift — v2 keeps constants here
only, no FEATURE.md shadow).
"""

from __future__ import annotations

RAG_V2_PROMPT = "(rag-v2)"
RAG_V2_BANNER = "RAG v2 — retrieve, offload, and delegate (q/quit/exit to return)"
RAG_V2_MENU = (
    "[1] select repository  [2] create repository  [3] chat  "
    "[4] web ingestion  [5] pdf ingestion  [6] md ingestion  "
    "[s] switch repository  [q] quit"
)
