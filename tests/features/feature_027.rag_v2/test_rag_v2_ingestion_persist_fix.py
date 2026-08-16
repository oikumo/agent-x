"""Regression tests — rag_v2 ingestion persist fix (bug_fix 2026-08-16).

Pins the PRODUCTION ingestion path (``store=None``), which the original
feature_027 G4 tests never exercised: they inject a MagicMock ``store``, so
the silent no-op in ``_persist`` (building a ``RagV2`` aggregate that has no
``add_texts``/``add``/``upsert`` → every chunk dropped) passed GREEN.

The fix (per operation_spec_001, feature_027):

  * ``_persist`` builds the REAL Chroma vector store via
    ``AIService().rag_chromadb(directory=f"{repository_path}/chroma_db")`` —
    the v1-shared store (ONE Chroma per repository; the drifted ``/chroma``
    path created a second, empty skeleton store).
  * ``RagV2.vector_db_path`` pins ``<repo>/chroma_db``.
  * The retriever searches ``<repo>/chroma_db``.
  * web ingestion also writes the SQLite journal record (operation_spec_001:
    "The loader writes an ingestion record to the SQLite journal").
"""

from __future__ import annotations

import importlib
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest


def _load_symbol(module_path: str, name: str) -> Any:
    module = importlib.import_module(module_path)
    return getattr(module, name)


class _TempRepo:
    """One-test temp repository directory (cleaned up on exit)."""

    def __init__(self) -> None:
        self.path = tempfile.mkdtemp(prefix="rag_v2_persist_")

    def repo(self, name: str = "repo-x") -> str:
        p = Path(self.path) / name
        p.mkdir(parents=True, exist_ok=True)
        return str(p)

    def cleanup(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


class TestIngestionPersistsToRealChromaStore(TestCase):
    """G4 production path — store=None must persist into the REAL Chroma store."""

    def _assert_persisted_via_rag_chromadb(self, ingest_fn, *args, **kwargs) -> None:
        tmp = _TempRepo()
        self.addCleanup(tmp.cleanup)
        repo = tmp.repo()
        fake_store = MagicMock()
        with patch(
            "agentx.model.ai.service.AIService.rag_chromadb",
            return_value=fake_store,
        ) as mock_factory:
            count = ingest_fn(*args, repository_path=repo, **kwargs)

        assert count > 0, "ingestion must return the chunk count (not 0)"
        mock_factory.assert_called_once()
        called_dir = mock_factory.call_args.kwargs.get("directory")
        assert called_dir == f"{repo}/chroma_db", (
            "production persist must target the v1-shared store "
            f"<repo>/chroma_db (got {called_dir!r}) — the /chroma drift "
            "created a second, empty Chroma store per repository"
        )
        fake_store.add_texts.assert_called_once()
        args_texts = fake_store.add_texts.call_args.kwargs.get("texts")
        assert isinstance(args_texts, list) and len(args_texts) == count, (
            "add_texts must receive one text per chunk returned (silent no-op regression)"
        )

    def test_web_ingest_persists_to_chroma_db_store(self) -> None:
        """ingest_web with store=None builds the real store at <repo>/chroma_db."""
        ingest_web = _load_symbol(
            "agentx.model.rag_v2.web_ingestion.web_ingest", "ingest_web"
        )
        with patch(
            "agentx.model.rag_v2.web_ingestion.web_ingest.WebBaseLoader",
            return_value=MagicMock(
                aload=MagicMock(
                    return_value=[
                        MagicMock(page_content="hello world", metadata={"source": "https://example.com"})
                    ]
                )
            ),
        ):
            self._assert_persisted_via_rag_chromadb(
                ingest_web, "https://example.com"
            )

    def test_md_ingest_persists_to_chroma_db_store(self) -> None:
        """ingest_md with store=None builds the real store at <repo>/chroma_db."""
        ingest_md = _load_symbol(
            "agentx.model.rag_v2.md_ingestion.md_ingest", "ingest_md"
        )
        fake_md = Path(__file__).parent / "fixtures" / "sample.md"
        # sample.md carries real text — the persisted texts must be non-empty.
        tmp = _TempRepo()
        self.addCleanup(tmp.cleanup)
        repo = tmp.repo()
        fake_store = MagicMock()
        with patch(
            "agentx.model.ai.service.AIService.rag_chromadb",
            return_value=fake_store,
        ) as mock_factory:
            count = ingest_md(str(fake_md), repository_path=repo)
        assert count > 0
        assert mock_factory.call_args.kwargs.get("directory") == f"{repo}/chroma_db"
        texts = fake_store.add_texts.call_args.kwargs.get("texts")
        assert texts and all(isinstance(t, str) and t for t in texts), (
            "md ingestion must persist real chunk texts (silent no-op regression)"
        )

    def test_pdf_ingest_persists_to_chroma_db_store(self) -> None:
        """ingest_pdf with store=None builds the real store at <repo>/chroma_db."""
        ingest_pdf = _load_symbol(
            "agentx.model.rag_v2.pdf_ingestion.pdf_ingest", "ingest_pdf"
        )
        fake_pdf = Path(__file__).parent / "fixtures" / "sample.pdf"
        self._assert_persisted_via_rag_chromadb(ingest_pdf, str(fake_pdf))

    def test_web_ingest_writes_journal_record(self) -> None:
        """web ingestion records the URL in the SQLite journal (op_spec_001)."""
        ingest_web = _load_symbol(
            "agentx.model.rag_v2.web_ingestion.web_ingest", "ingest_web"
        )
        tmp = _TempRepo()
        self.addCleanup(tmp.cleanup)
        repo = tmp.repo()
        with patch(
            "agentx.model.rag_v2.web_ingestion.web_ingest.WebBaseLoader",
            return_value=MagicMock(
                aload=MagicMock(
                    return_value=[MagicMock(page_content="hello", metadata={"source": "u"})]
                )
            ),
        ), patch(
            "agentx.model.ai.service.AIService.rag_chromadb",
            return_value=MagicMock(),
        ):
            ingest_web("https://example.com/doc", repository_path=repo)

        rag_cls = _load_symbol("agentx.model.rag_v2.rag_v2", "RagV2")
        assert rag_cls(repo).get_ingested_url() == "https://example.com/doc", (
            "web ingestion must record the URL in the journal (missing-record regression)"
        )


class TestSingleChromaStoreContract(TestCase):
    """RagV2.vector_db_path + retriever must target <repo>/chroma_db (ONE store)."""

    def test_rag_v2_vector_db_path_is_chroma_db(self) -> None:
        """RagV2.vector_db_path == <repo>/chroma_db (no /chroma skeleton store)."""
        tmp = _TempRepo()
        self.addCleanup(tmp.cleanup)
        repo = tmp.repo()
        rag_cls = _load_symbol("agentx.model.rag_v2.rag_v2", "RagV2")
        rag = rag_cls(repo)
        assert rag.vector_db_path == f"{repo}/chroma_db", (
            "RagV2.vector_db_path must pin <repo>/chroma_db (v1-shared store); "
            "the /chroma drift created a second Chroma store per repository"
        )
        assert not Path(repo, "chroma").exists(), (
            "instantiating RagV2 must NOT create a /chroma skeleton store"
        )

    def test_retriever_searches_chroma_db(self) -> None:
        """build_retriever queries AIService.rag_chromadb at <repo>/chroma_db."""
        build_retriever = _load_symbol(
            "agentx.model.rag_v2.query.rag_v2_retriever", "build_retriever"
        )
        tmp = _TempRepo()
        self.addCleanup(tmp.cleanup)
        repo = tmp.repo()
        fake_store = MagicMock()
        fake_store.similarity_search.return_value = [
            MagicMock(
                page_content="retrieved content",
                metadata={"chunk_id": "c1", "score": 0.8, "source": "doc.md", "line": 3},
            )
        ]
        with patch(
            "agentx.model.ai.service.AIService.rag_chromadb",
            return_value=fake_store,
        ) as mock_factory:
            retriever = build_retriever(repo)
            rows = retriever("query", k=3)

        mock_factory.assert_called_once()
        assert mock_factory.call_args.kwargs.get("directory") == f"{repo}/chroma_db", (
            "retriever must search the v1-shared store <repo>/chroma_db"
        )
        fake_store.similarity_search.assert_called_once_with("query", k=3)
        assert rows and rows[0][0] == "c1" and rows[0][1] == "retrieved content", (
            "retriever must yield (chunk_id, content, score, source_path, page, line)"
        )


if __name__ == "__main__":
    import unittest
    unittest.main()