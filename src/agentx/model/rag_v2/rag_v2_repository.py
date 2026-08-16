"""RagV2Repository — value object (name + path). Mirrors v1 ``RagRepository``.

Console-only v2 (feature_027); v1 ``agentx.model.rag.rag_repository`` untouched.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RagV2Repository:
    """A single RAG v2 repository (id + working-directory path).

    The active-repository handle carried by ``RagV2MainController``. Pure
    value object — no DB/vector-store concerns here (those live in ``RagV2`` /
    ``RagV2Database``).
    """

    id: str
    path: str
