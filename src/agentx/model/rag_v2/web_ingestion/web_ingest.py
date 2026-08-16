"""RagV2 web ingestion — ``ingest_web`` (feature_027, G4).

Ported from v1's asyncio path (``agentx.model.rag.web.web_ingestion``),
cleansed of stdout pollution (analysis_001 surprise #1: pprint in the model
layer). Asyncio is confined to this loader (D6 invariant v2 preserves)."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

# WebBaseLoader is referenced on this module so tests can patch it here
# (``agentx.model.rag_v2.web_ingestion.web_ingest.WebBaseLoader``).
try:
    from langchain_community.document_loaders import WebBaseLoader
except ImportError:  # pragma: no cover — optional dep
    WebBaseLoader = None  # type: ignore[assignment]


def ingest_web(
    url: str,
    *,
    repository_path: str,
    store: Any = None,
    llm: Any = None,
) -> int:
    """Ingest a web URL into the v2 vector store (async load); returns chunk count."""
    if WebBaseLoader is None:  # pragma: no cover — dep missing
        return 0
    loader = WebBaseLoader(url)
    try:
        aloaded = loader.aload()  # type: ignore[union-attr]
        # aload may be a coroutine (real) or a plain list (test injection).
        if asyncio.iscoroutine(aloaded):
            docs = asyncio.run(aloaded)
        else:
            docs = aloaded
    except TypeError:
        # aload may not be a coroutine in some stubs — fall back to load().
        docs = loader.load()  # type: ignore[union-attr]
    chunks = _split(docs, source=url)

    _persist(chunks, repository_path, store, kind="web", source=url)
    return len(chunks)


def _split(docs: list[Any], *, source: str) -> list[dict]:
    out: list[dict] = []
    for d in docs:
        text = getattr(d, "page_content", "") or (d.get("page_content") if isinstance(d, dict) else "")
        out.append({"content": text, "source_path": source, "page": None, "line": None})
    return out


def _persist(
    chunks: list[dict],
    repository_path: str,
    store: Any,
    *,
    kind: str,
    source: Optional[str] = None,
) -> None:
    texts = [c["content"] for c in chunks]
    metadatas = [
        {"source": c.get("source_path"), "page": c.get("page"), "line": c.get("line")}
        for c in chunks
    ]
    if store is None:
        # bug_fix 2026-08-16: the production path MUST build the real Chroma
        # vector store — the old `RagV2(...)` aggregate has no add_texts/add/
        # upsert, so the hasattr chain below silently dropped every chunk
        # (observed: ingestion reported "N chunks" but nothing was searchable).
        # operation_spec_001 pins the v1-shared store at `<repo>/chroma_db`.
        from agentx.model.ai.service import AIService

        store = AIService().rag_chromadb(directory=f"{repository_path}/chroma_db")
    if hasattr(store, "add_texts"):
        store.add_texts(texts=texts, metadatas=metadatas)
    elif hasattr(store, "add"):
        store.add(texts, metadatas)
    elif hasattr(store, "upsert"):
        store.upsert(texts, metadatas)
    # Journal record — operation_spec_001: "The loader writes an ingestion
    # record to the SQLite journal" (web was the only loader missing it).
    try:
        from agentx.model.rag_v2.rag_v2 import RagV2

        RagV2(repository_path).record_ingestion(url=source, kind=kind)
    except Exception:
        pass
