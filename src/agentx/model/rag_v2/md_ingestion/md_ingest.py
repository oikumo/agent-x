"""RagV2 MD ingestion — ``ingest_md`` (feature_027, G4 new)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


def ingest_md(
    md_path: str,
    *,
    repository_path: str,
    store: Any = None,
    llm: Any = None,
) -> int:
    """Ingest a Markdown file into the v2 vector store; returns chunk count."""
    path = Path(md_path)
    from langchain_community.document_loaders import TextLoader

    loader = TextLoader(str(path))
    docs = loader.load()
    chunks = _split(docs, source=str(path))

    _persist(chunks, repository_path, store, kind="md", source=str(path))
    return len(chunks)


def _split(docs: list[Any], *, source: str) -> list[dict]:
    out: list[dict] = []
    for d in docs:
        text = getattr(d, "page_content", "") or (d.get("page_content") if isinstance(d, dict) else "")
        out.append({"content": text, "source_path": source, "page": None, "line": 1})
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
        from agentx.model.rag_v2.rag_v2 import RagV2

        store = RagV2(working_directory=repository_path)
    if hasattr(store, "add_texts"):
        store.add_texts(texts=texts, metadatas=metadatas)
    elif hasattr(store, "add"):
        store.add(texts, metadatas)
    elif hasattr(store, "upsert"):
        store.upsert(texts, metadatas)
    try:
        from agentx.model.rag_v2.rag_v2 import RagV2

        RagV2(repository_path).record_ingestion(url=source, kind=kind)
    except Exception:
        pass
