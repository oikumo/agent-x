"""RED tests for feature_027.rag_v2 — the G1–G6 closure matrix.

This file pins the remaining G1–G6 closure matrix behaviors sharpened to
pytest node IDs in design_001's Test plan:

  * **G3** — ``RagV2MainController.get_rag_state()`` returns a populated
    ``RagV2State`` when a repository is selected WITH artifacts present, and
    returns None when no repository is selected (parity with v1's
    ``rag_controller.py:66-107``).
  * **G4** — PDF, MD, and web-URL ingestion fixtures land in the v2 vector
    store (the three ingestion sub-screens; PDF/MD are net-new, web is ported
    from v1's asyncio path).
  * **G5** — multi-repo session switch: create repo_A + repo_B → select A →
    switch to B → switch back to A with no state leak.

v2 is console-only; v1 RAG stays untouched for the TUI path.

All imports of not-yet-existing v2 symbols are deferred INSIDE the test bodies
so RED failures surface as test failures (pytest exit 1), NOT collection errors
(exit 2) — per OMT TDD RED-gate rule (runnable RED).
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest


def _load_symbol(module_path: str, name: str) -> Any:
    module = importlib.import_module(module_path)
    return getattr(module, name)


# ── G3 — get_rag_state() hygiene ──────────────────────────────────────────────


class TestRagV2StateHygiene(TestCase):
    """G3 — RagV2MainController.get_rag_state() populated/None handling."""

    def test_get_rag_state_returns_populated_state_with_repository_and_artifacts(self) -> None:
        """Selected repository + artifacts present on disk → get_rag_state()
        returns a populated RagV2State (path fields non-None). Parity with
        v1's rag_controller.py:66-107."""
        controller_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        state_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2State"
        )
        controller = controller_cls()
        controller.current_repository = repo_cls(id="repo-x", path="/tmp/rag_v2_repo_x")

        # Stub the inner Rag aggregation to report database + documents present.
        controller._rag_for_current = MagicMock(  # type: ignore[attr-defined]
            return_value=MagicMock(
                database_exists=MagicMock(return_value=True),
                documents_exist=MagicMock(return_value=True),
                vector_db_path="/tmp/rag_v2_repo_x/chroma",
                documents_path="/tmp/rag_v2_repo_x/docs",
                get_ingested_url=MagicMock(return_value="https://example.com/doc"),
            )
        )

        result = controller.get_rag_state()
        assert result is not None, (
            "get_rag_state must return a populated RagV2State (NOT None) when a "
            "repository is selected and artifacts present (G3 parity)"
        )
        assert isinstance(result, state_cls)
        # At least one path field must be populated (database/documents/url).
        populated = any(
            getattr(result, f, None)
            for f in ("url", "data_base_location", "documents_location")
        )
        assert populated, "RagV2State path fields must be non-None for a live repo"

    def test_get_rag_state_returns_none_when_no_repository_selected(self) -> None:
        """No repository selected → get_rag_state() returns None (graceful case)."""
        controller_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        controller = controller_cls()
        # current_repository stays None (default, fresh controller).
        assert controller.current_repository is None
        result = controller.get_rag_state()
        assert result is None, (
            "get_rag_state must return None when no repository is selected (G3)"
        )


# ── G4 — ingestion fixtures land in the v2 vector store ──────────────────────


class TestRagV2PdfIngestion(TestCase):
    """G4 PDF — a PDF fixture lands in the v2 vector store."""

    def test_pdf_fixture_lands_in_vector_store(self) -> None:
        ingest_cls = _load_symbol(
            "agentx.model.rag_v2.pdf_ingestion.pdf_ingest", "ingest_pdf"
        )
        fake_pdf = Path(__file__).parent / "fixtures" / "sample.pdf"
        # The impl should accept a path + repository_path, parse the PDF,
        # split, embed, and persist into the v2 ChromaDB store.
        store = MagicMock()
        ingest_cls(str(fake_pdf), repository_path="/tmp/rag_v2_repo_x", store=store)
        # The store must have received at least one vector (the split chunk).
        assert store.add.called or store.upsert.called or store.add_texts.called, (
            "PDF fixture must produce vectors that land in the v2 store (G4 PDF)"
        )


class TestRagV2MdIngestion(TestCase):
    """G4 MD — an MD fixture lands in the v2 vector store."""

    def test_md_fixture_lands_in_vector_store(self) -> None:
        ingest_cls = _load_symbol(
            "agentx.model.rag_v2.md_ingestion.md_ingest", "ingest_md"
        )
        fake_md = Path(__file__).parent / "fixtures" / "sample.md"
        store = MagicMock()
        ingest_cls(str(fake_md), repository_path="/tmp/rag_v2_repo_x", store=store)
        assert store.add.called or store.upsert.called or store.add_texts.called, (
            "MD fixture must produce vectors that land in the v2 store (G4 MD)"
        )


class TestRagV2WebIngestion(TestCase):
    """G4 web — a web-URL fixture lands in the v2 vector store (v1 async ported)."""

    def test_web_url_fixture_lands_in_vector_store(self) -> None:
        ingest_cls = _load_symbol(
            "agentx.model.rag_v2.web_ingestion.web_ingest", "ingest_web"
        )
        store = MagicMock()
        # Fake the aiohttp load so we don't hit the network.
        with patch(
            "agentx.model.rag_v2.web_ingestion.web_ingest.WebBaseLoader",
            return_value=MagicMock(
                aload=MagicMock(return_value=[MagicMock(page_content="hello", metadata={"source": "https://example.com"})])
            ),
        ):
            ingest_cls("https://example.com", repository_path="/tmp/rag_v2_repo_x", store=store)
        assert store.add.called or store.upsert.called or store.add_texts.called, (
            "web-URL fixture must produce vectors that land in the v2 store (G4 web)"
        )


# ── G5 — multi-repo session switch ────────────────────────────────────────────


class TestRagV2SessionSwitch(TestCase):
    """G5 — switch between two repositories with no state leak."""

    def test_switch_between_two_repositories_no_leak(self) -> None:
        controller_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        repo_a = repo_cls(id="repo-a", path="/tmp/rag_v2_repo_a")
        repo_b = repo_cls(id="repo-b", path="/tmp/rag_v2_repo_b")

        controller = controller_cls()
        controller.repositories = {repo_a.id: repo_a, repo_b.id: repo_b}

        # Select repo A.
        controller.current_repository = repo_a
        assert controller.current_repository.id == "repo-a"

        # Switch to repo B (the user picks it from the selection list).
        controller.view = MagicMock()
        controller.view.get_selected_repository_id.return_value = repo_b.id
        controller.switch_repository()
        assert controller.current_repository is not None
        assert controller.current_repository.id == "repo-b", (
            "switch_repository must swap the active repository to the user's pick (G5)"
        )

        # Switch back to repo A — no leak of repo B's state.
        controller.view.get_selected_repository_id.return_value = repo_a.id
        controller.switch_repository()
        assert controller.current_repository.id == "repo-a", (
            "switching back to A must restore A — no stale B leak (G5 closure)"
        )


if __name__ == "__main__":
    import unittest
    unittest.main()
