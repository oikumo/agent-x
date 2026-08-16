"""Regression tests for the feature_027 console-REPL bug (2026-08-16).

Bug class pinned here: the v2 view↔controller contract drifted — the
``RagV2View`` REPL calls ``controller.send_message(...)`` /
``controller._worker_thread``, but ``RagV2MainController`` never implemented
them (every REPL input crashed with AttributeError → "Command execution
failed", session unusable). The shipped tests MOCKED the controller, so the
drift passed CI. These tests pin the REAL controller contract.

Second bug pinned: the module-level ``RAG_V2_TOOLS`` take ``repository_path``
as a MODEL-SUPPLIED argument; the LLM does not know the real path and
hallucinates one (observed '/home/user/...' → PermissionError inside
``RagV2Database`` mkdir). ``build_rag_v2_tools`` binds the path server-side —
the tool schemas must expose NO ``repository_path`` parameter.
"""

from __future__ import annotations

import importlib
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock


def _load_symbol(module_path: str, name: str) -> Any:
    module = importlib.import_module(module_path)
    return getattr(module, name)


# ── Real-controller REPL contract (the AttributeError crash) ─────────────────


class TestSendMessageRealController(TestCase):
    """RagV2MainController implements the send_message/_worker_thread contract
    that RagV2View.show() drives (feature_024 console parity pattern)."""

    def _controller(self):
        controller_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        controller = controller_cls()
        view = MagicMock()
        controller.set_view(view)
        return controller, view

    def test_send_message_and_worker_thread_exist(self) -> None:
        """The REPL's two touchpoints exist on the real controller."""
        controller, _ = self._controller()
        assert callable(getattr(controller, "send_message", None)), (
            "RagV2MainController.send_message must exist — RagV2View.show() "
            "calls it for every non-menu input (crashed with AttributeError)"
        )
        assert hasattr(controller, "_worker_thread"), (
            "RagV2MainController._worker_thread must exist — "
            "RagV2View._wait_for_agent() joins it"
        )

    def test_send_message_without_repository_is_graceful(self) -> None:
        """No active repository → True (handled) + error via the view, NOT a
        crash and NOT False (which would misreport 'Agent is busy')."""
        controller, view = self._controller()
        assert controller.current_repository is None
        result = controller.send_message("hello agent")
        assert result is True
        view.print_message_error.assert_called_once()

    def test_send_message_busy_agent_returns_false(self) -> None:
        """A running agent rejects with False (the view shows 'Agent is busy')."""
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller, _ = self._controller()
        controller.current_repository = repo_cls(id="r", path="/tmp/rag_v2_test")
        fake_service = MagicMock()
        fake_service.is_running = True
        controller._agent_service = fake_service
        assert controller.send_message("hello") is False

    def test_send_message_streams_answer_via_worker_thread(self) -> None:
        """A full turn: worker thread spawns, stream callbacks reach the view."""
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller, view = self._controller()
        controller.current_repository = repo_cls(id="r", path="/tmp/rag_v2_test")

        def _fake_stream(message: str, **callbacks: Any) -> None:
            callbacks["on_answer"]("answer-token")
            callbacks["on_done"]()

        fake_service = MagicMock()
        fake_service.is_running = False
        fake_service.stream_agent.side_effect = _fake_stream
        controller._agent_service = fake_service

        assert controller.send_message("what is RAG?") is True
        assert controller._worker_thread is not None
        controller._worker_thread.join(timeout=5)
        assert not controller._worker_thread.is_alive()
        fake_service.stream_agent.assert_called_once()
        view.show_partial_message.assert_any_call("answer-token")

    def test_agent_service_invalidated_on_repository_switch(self) -> None:
        """G5: switching the active repo drops the service bound to the old path."""
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller, view = self._controller()
        old = repo_cls(id="old", path="/tmp/old")
        new = repo_cls(id="new", path="/tmp/new")
        controller.current_repository = old
        controller.repositories = {"old": old, "new": new}
        controller._agent_service = MagicMock()
        view.get_selected_repository_id.return_value = "new"
        controller.switch_repository()
        assert controller.current_repository is new
        assert controller._agent_service is None, (
            "repository switch must invalidate the path-bound agent service"
        )


# ── Repository-bound tool schema (the '/home/user' hallucination) ────────────


class TestBoundToolSchema(TestCase):
    """build_rag_v2_tools exposes no model-supplied repository_path."""

    def test_bound_tools_have_no_repository_path_argument(self) -> None:
        factory = _load_symbol(
            "agentx.model.rag_v2.rag_v2_tools", "build_rag_v2_tools"
        )
        tools = factory("/tmp/rag_v2_test")
        names = {t.name for t in tools}
        # feature_029 rename: rag_search → search_documents,
        # rag_ingest_status → ingestion_status (clean cut, no aliases).
        assert names == {"search_documents", "ingestion_status"}
        for t in tools:
            assert "repository_path" not in t.args, (
                f"bound tool '{t.name}' must NOT expose repository_path — "
                "the model hallucinates paths it is allowed to supply"
            )

    def test_bound_rag_search_uses_the_bound_path(self) -> None:
        """The bound search_documents routes to the impl with the factory's path."""
        tools_mod = importlib.import_module("agentx.model.rag_v2.rag_v2_tools")
        tools = tools_mod.build_rag_v2_tools("/tmp/rag_v2_bound_test")
        search = next(t for t in tools if t.name == "search_documents")
        hits = [("c0", "content 0", 0.9, "doc0.md", None, 1)]
        # Inject a fake retriever via the impl seam; assert the bound path.
        seen: dict[str, Any] = {}

        original = tools_mod._search_documents_impl

        def _spy(query: str, repository_path: str, k: int = 5, **kw: Any):
            seen["repository_path"] = repository_path
            return original(
                query, repository_path, k, _retriever=lambda q, kk: hits
            )

        tools_mod._search_documents_impl = _spy  # type: ignore[attr-defined]
        try:
            # The bound closure captured the module-level name at def time, so
            # rebind through the tool's underlying function globals instead:
            search.func.__globals__["_search_documents_impl"] = _spy  # type: ignore[union-attr]
            result = search.invoke({"query": "q", "k": 1})
        finally:
            search.func.__globals__["_search_documents_impl"] = original  # type: ignore[union-attr]
        assert seen.get("repository_path") == "/tmp/rag_v2_bound_test"
        assert len(result.hits) == 1


if __name__ == "__main__":
    import unittest
    unittest.main()
