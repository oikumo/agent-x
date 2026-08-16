"""RagV2 retriever builder (feature_027).

``build_retriever`` returns a callable ``(query, k) -> list[tuple]`` against
the repository's ChromaDB vector store. Production path; the @tool path calls
this when no ``_retriever`` is injected. The retriever yields the tuple shape
``_search_documents_impl`` consumes:
    (chunk_id, content, score, source_path, page, line)
"""

from __future__ import annotations

from typing import Any, Callable, List, Tuple


Retriever = Callable[[str, int], List[Tuple[Any, ...]]]


def build_retriever(repository_path: str) -> Retriever:
    """Build a similarity-search retriever over the repository's ChromaDB."""

    def _retriever(query: str, k: int = 5) -> List[Tuple[Any, ...]]:
        from agentx.model.ai.service import AIService

        # AIService builds the v2 ChromaDB store; the embedding model is the
        # active LLM's embeddings. Lazy import keeps the @tool import light.
        # bug_fix 2026-08-16: `chroma_db`, NOT `chroma` — operation_spec_001
        # pins the v1-shared store path (one Chroma per repository).
        rag = AIService().rag_chromadb(directory=f"{repository_path}/chroma_db")
        docs = rag.similarity_search(query, k=k)
        rows: List[Tuple[Any, ...]] = []
        for d in docs:
            md = getattr(d, "metadata", {}) or {}
            rows.append(
                (
                    md.get("chunk_id") or md.get("id") or "",
                    getattr(d, "page_content", "") or "",
                    float(md.get("score", 0.0)),
                    md.get("source") or md.get("source_path"),
                    md.get("page"),
                    md.get("line"),
                )
            )
        return rows

    return _retriever
