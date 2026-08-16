"""RagV2 tools — the retrieve-offload ``@tool`` surface (feature_027).

Mirrors ``coding_tools.py:18`` ``@tool`` pattern (feature_025):
  * ``rag_search`` — similarity search → ``backend.upload_files()`` chunk
    files (the "offload" step — gives the chunk-analyst subagent deterministic
    ``chunk_{i}.txt`` paths to read).
  * ``rag_ingest_status`` — read-only probe of the active repository's state.

The ``@tool`` docstring is the tool description the model sees — keep it
concise (REFACTOR phase may slim further). Dataclass return types carry the
citation metadata the orchestrator threads to the synthesizer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from langchain.tools import tool


# ── Result types ───────────────────────────────────────────────────────────────


@dataclass
class RagSearchHit:
    """A single retrieval hit with citation metadata."""

    chunk_id: str
    content: str
    score: float
    source_path: Optional[str] = None
    page: Optional[int] = None       # for PDF sources
    line: Optional[int] = None       # for MD sources


@dataclass
class RagSearchResult:
    """Result of the rag_search tool (see module header for the offload note)."""

    hits: List[RagSearchHit]
    chunks_uploaded: int             # how many chunk files landed in backend
    truncated: bool = False
    error: Optional[str] = None


# ── rag_search ────────────────────────────────────────────────────────────────


@tool
def rag_search(query: str, repository_path: str, k: int = 5) -> RagSearchResult:
    """Search the active RAG repository for chunks matching the query.

    Writes retrieved chunks to the agent backend filesystem via
    ``backend.upload_files()`` so the chunk-analyst subagent can read/grep
    them in parallel. Returns a pointer-and-preview result; the full chunks
    live in the backend (retrieve-offload-delegate pattern, D5).

    Args:
        query: The similarity-search query string.
        repository_path: The active repository's working directory (G5 switch swaps this).
        k: Top-k chunks to retrieve (default 5).
    """
    return _rag_search_impl(query, repository_path, k)


def _rag_search_impl(
    query: str,
    repository_path: str,
    k: int = 5,
    *,
    backend: Any | None = None,
    _retriever: Callable[[str, int], Any] | None = None,
    **_unused: Any,
) -> RagSearchResult:
    """Thin impl wrapper — similarity search + backend.upload_files().

    The ``backend`` + ``_retriever`` kwargs are dependency-injection seams:
    the ``@tool``-wrapped ``rag_search`` calls this without them (production
    builds the real backend/retriever); tests inject fakes to assert the
    offload step + citation metadata without a live ChromaDB store.

    The retriever yields tuples:
        (chunk_id, content, score, source_path, page, line)
    which this impl maps to ``RagSearchHit`` records + deterministic
    ``chunk_{i}.txt`` backend files (so the chunk-analyst's
    ``task(description="summarize chunk_0.txt")`` references a stable path).
    """
    if _retriever is None:
        # Production path — build a real retriever against the repository's
        # ChromaDB store. Built lazily so the ``@tool`` import stays light.
        from agentx.model.rag_v2.query.rag_v2_retriever import build_retriever

        _retriever = build_retriever(repository_path)

    try:
        rows = list(_retriever(query, k))
    except Exception as exc:  # pragma: no cover — defensive; retriever contract
        return RagSearchResult(hits=[], chunks_uploaded=0, error=str(exc))

    hits: List[RagSearchHit] = []
    files: list[tuple[str, bytes]] = []
    for i, row in enumerate(rows):
        # Accept both tuples and mapping-like rows; default missing fields.
        if isinstance(row, dict):
            cid = row.get("chunk_id") or row.get("id") or f"chunk_{i}"
            content = row.get("content") or row.get("text") or ""
            score = float(row.get("score", 0.0))
            source = row.get("source_path") or row.get("source")
            page = row.get("page")
            line = row.get("line")
        else:
            # Tuple shape (chunk_id, content, score, source_path, page, line).
            cid = row[0] if len(row) > 0 else f"chunk_{i}"
            content = row[1] if len(row) > 1 else ""
            score = float(row[2]) if len(row) > 2 else 0.0
            source = row[3] if len(row) > 3 else None
            page = row[4] if len(row) > 4 else None
            line = row[5] if len(row) > 5 else None
        hits.append(
            RagSearchHit(
                chunk_id=str(cid),
                content=str(content),
                score=score,
                source_path=source,
                page=page,
                line=line,
            )
        )
        files.append((f"chunk_{i}.txt", str(content).encode("utf-8")))

    chunks_uploaded = 0
    if backend is not None and files:
        uploaded = backend.upload_files(files)
        chunks_uploaded = len(uploaded) if isinstance(uploaded, (list, tuple)) else len(files)

    return RagSearchResult(
        hits=hits,
        chunks_uploaded=chunks_uploaded,
        truncated=False,
        error=None,
    )


# ── rag_ingest_status ─────────────────────────────────────────────────────────


@tool
def rag_ingest_status(repository_path: str) -> dict:
    """Probe the active repository's ingestion state (read-only).

    Returns a dict with database_exists / documents_exist / ingested_url
    fields — mirrors ``Rag.database_exists`` / ``documents_exist`` /
    ``get_ingested_url`` (rag.py:69-92) but as a @tool the deepagents stack
    can invoke.
    """
    return _rag_ingest_status_impl(repository_path)


def _rag_ingest_status_impl(repository_path: str) -> dict:
    from agentx.model.rag_v2.rag_v2 import RagV2

    rag = RagV2(working_directory=repository_path)
    return {
        "database_exists": rag.database_exists(),
        "documents_exist": rag.documents_exist(),
        "ingested_url": rag.get_ingested_url(),
    }


RAG_V2_TOOLS = [rag_search, rag_ingest_status]
