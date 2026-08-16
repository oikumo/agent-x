"""RagV2 PDF ingestion — ``ingest_pdf`` (feature_027, G4 new).

Loads a PDF, splits into chunks, embeds, and persists into the v2 vector
store. Sync wrapper over LangChain's PDF loaders (PyPDF / pdfplumber-backed).
The store receives the split chunks via ``add``/``upsert``/``add_texts``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


def ingest_pdf(
    pdf_path: str,
    *,
    repository_path: str,
    store: Any = None,
    llm: Any = None,
) -> int:
    """Ingest a PDF file into the v2 vector store; returns chunk count."""
    path = Path(pdf_path)
    # Load + split (lazy import — pypdf is an optional dep).
    from langchain_community.document_loaders import PyPDFLoader

    loader = PyPDFLoader(str(path))
    pages = loader.load()
    chunks = _split(pages)

    _persist(chunks, repository_path, store, kind="pdf", source=str(path))
    return len(chunks)


def _split(pages: list[Any]) -> list[dict]:
    """Flatten PDF pages into chunk dicts (content + page citation)."""
    out: list[dict] = []
    for i, page in enumerate(pages):
        text = getattr(page, "page_content", "") or (page.get("page_content") if isinstance(page, dict) else "")
        out.append({"content": text, "source_path": None, "page": i + 1, "line": None})
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
        {"source": source, "page": c.get("page"), "line": c.get("line")}
        for c in chunks
    ]
    if store is None:
        # bug_fix 2026-08-16: build the REAL Chroma store — the old RagV2
        # aggregate has no add_texts/add/upsert, so ingestion silently
        # dropped every chunk. operation_spec_001 pins `<repo>/chroma_db`.
        from agentx.model.ai.service import AIService

        store = AIService().rag_chromadb(directory=f"{repository_path}/chroma_db")
    if hasattr(store, "add_texts"):
        store.add_texts(texts=texts, metadatas=metadatas)
    elif hasattr(store, "add"):
        store.add(texts, metadatas)
    elif hasattr(store, "upsert"):
        store.upsert(texts, metadatas)
    # Record the ingestion in the repo journal (best-effort; store may be a mock).
    try:
        from agentx.model.rag_v2.rag_v2 import RagV2

        RagV2(repository_path).record_ingestion(url=source, kind=kind)
    except Exception:
        pass
