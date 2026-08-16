"""RED tests for feature_027.rag_v2 — the retrieve-offload rag_search @tool.

Asserts the retrieve-offload-delegate D5 pattern (design_001):

  * ``rag_search(...)`` uploads retrieved chunks to the agent backend via
    ``backend.upload_files(...)`` (the "offload" step — gives the chunk-analyst
    subagent a deterministic chunk_{i}.txt path to read).
  * The returned ``RagSearchResult`` carries citation metadata (``hits[i]``
    populate ``source_path`` + ``page``/``line`` — the "pointer-and-preview"
    result the orchestrator passes to the synthesizer).
  * The ``CHUNK_ANALYST`` SubAgent dict spec has the required fields
    (``name``/``description``/``system_prompt``) and is present in
    ``RAG_V2_SUBAGENTS``.

All v2 symbol imports are deferred inside the test bodies so RED failures
surface as test failures (pytest exit 1), NOT collection errors (exit 2).
"""

from __future__ import annotations

import importlib
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest


def _load_symbol(module_path: str, name: str) -> Any:
    module = importlib.import_module(module_path)
    return getattr(module, name)


# ── rag_search @tool ─────────────────────────────────────────────────────────


class TestRagSearchTool(TestCase):
    """The rag_search retrieve-offload @tool."""

    def test_rag_search_uploads_chunks_to_backend(self) -> None:
        """rag_search writes retrieved chunks via backend.upload_files()."""
        # Import the tool module's impl so we can exercise the offload call.
        impl = _load_symbol(
            "agentx.model.rag_v2.rag_v2_tools", "_rag_search_impl"
        )
        # Build a fake backend that records upload_files calls.
        uploads: list[Any] = []

        class _FakeBackend:
            def upload_files(self, files):
                uploads.append(files)
                return [name for name, _ in files]

        # Fake the similarity-search layer to return N hits with content.
        # Each hit tuple: (chunk_id, content, score, source_path, page, line)
        hits = [
            ("chunk_id_0", "content of chunk 0", 0.9, "doc0.md", None, 42),
            ("chunk_id_1", "content of chunk 1", 0.7, "doc1.pdf", 7, None),
        ]

        # Drive the impl with a fake backend + fake retriever.
        result = impl(
            query="test query",
            repository_path="/tmp/rag_v2_test",
            k=2,
            backend=_FakeBackend(),
            _retriever=lambda query, k: hits,  # type: ignore[call-arg]
        )
        assert uploads, (
            "rag_search must call backend.upload_files() with the retrieved chunks "
            "(retrieve-offload-delegate D5 — offload step)"
        )
        # The uploaded chunk filenames must be deterministic (chunk_0.txt, chunk_1.txt, …)
        # so the chunk-analyst's task(description="summarize chunk_0.txt") resolves.
        first_upload = uploads[0]
        names = [name for name, _ in first_upload]
        assert "chunk_0.txt" in names and "chunk_1.txt" in names, (
            "chunk filenames must be deterministic: chunk_0.txt, chunk_1.txt, …"
        )
        assert getattr(result, "chunks_uploaded", 0) == 2

    def test_rag_search_returns_pointer_result_with_citation_metadata(self) -> None:
        """RagSearchResult.hits[i] carries source_path + page/line citation."""
        impl = _load_symbol(
            "agentx.model.rag_v2.rag_v2_tools", "_rag_search_impl"
        )
        result_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_tools", "RagSearchResult"
        )
        hit_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_tools", "RagSearchHit"
        )

        hits_in = [
            ("c0", "content 0", 0.9, "doc0.md", None, 42),  # MD → line
            ("c1", "content 1", 0.7, "doc1.pdf", 7, None),  # PDF → page
        ]

        class _FakeBackend:
            def upload_files(self, files):
                return [name for name, _ in files]

        result = impl(
            query="q",
            repository_path="/tmp/rag_v2_test",
            k=2,
            backend=_FakeBackend(),
            _retriever=lambda query, k: hits_in,  # type: ignore[call-arg]
        )
        assert isinstance(result, result_cls), "rag_search returns a RagSearchResult"
        assert len(result.hits) == 2
        # Each hit is a RagSearchHit with citation metadata populated.
        md_hit = result.hits[0]
        pdf_hit = result.hits[1]
        assert isinstance(md_hit, hit_cls) and isinstance(pdf_hit, hit_cls)
        assert md_hit.source_path == "doc0.md" and md_hit.line == 42
        assert pdf_hit.source_path == "doc1.pdf" and pdf_hit.page == 7
        # Pointer-and-preview: chunks_uploaded tracks the backend offload.
        assert result.chunks_uploaded == 2
        assert result.error is None


# ── chunk-analyst SubAgent dict spec ──────────────────────────────────────────


class TestChunkAnalystSubagent(TestCase):
    """The chunk-analyst SubAgent dict spec (G6(b) subagent closure)."""

    def test_chunk_analyst_spec_has_required_fields(self) -> None:
        """CHUNK_ANALYST dict has name/description/system_prompt."""
        spec = _load_symbol(
            "agentx.model.rag_v2.rag_v2_subagents", "CHUNK_ANALYST"
        )
        assert isinstance(spec, dict), "CHUNK_ANALYST must be a SubAgent dict"
        for field in ("name", "description", "system_prompt"):
            assert field in spec and spec[field], (
                f"CHUNK_ANALYST must populate the '{field}' field "
                "(deepagents SubAgent dict spec)"
            )
        assert spec["name"] == "chunk-analyst", (
            "SubAgent name must be 'chunk-analyst' (task(subagentType=...) key)"
        )

    def test_chunk_analyst_in_rag_v2_subagents_list(self) -> None:
        """CHUNK_ANALYST appears in RAG_V2_SUBAGENTS."""
        spec = _load_symbol(
            "agentx.model.rag_v2.rag_v2_subagents", "CHUNK_ANALYST"
        )
        lst = _load_symbol(
            "agentx.model.rag_v2.rag_v2_subagents", "RAG_V2_SUBAGENTS"
        )
        assert isinstance(lst, list) and spec in lst, (
            "RAG_V2_SUBAGENTS must be a list containing CHUNK_ANALYST"
        )


if __name__ == "__main__":
    import unittest
    unittest.main()
