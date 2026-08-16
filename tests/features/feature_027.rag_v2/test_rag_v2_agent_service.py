"""RED tests for feature_027.rag_v2 — DeepAgents wiring of RagV2AgentService.

Mirrors ``test_deepagent_context_optimization.py`` (feature_025):

  1. ctor uses :func:`deepagents.create_deep_agent` when ``deepagents`` is importable
  2. ctor registers the ``chunk-analyst`` subagent (``subagents=[CHUNK_ANALYST]``)
  3. ctor builds a :class:`deepagents.backends.StateBackend` for offloading
  4. ctor falls back to legacy :func:`langchain.agents.create_agent` when
     ``import deepagents`` raises ``ImportError`` (chunk-analyst unavailable)
  5. public API (``thread_id`` / ``cancel`` / ``is_running`` / ``get_history`` /
     ``reset_conversation``) stays stable (same surface as CodingAgentService)

Design: ``design_001_retrieve_offload_delegate.md``.
Operation spec: ``operation_spec_001_rag_v2_service_and_tools.md``.

All imports of the module-under-edit are deferred INSIDE the test bodies so
that not-yet-implemented classes surface as test failures (exit 1) rather than
collection errors (exit 2) — per OMT TDD RED-gate rule.
"""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ────────────────────────────────────────────────────────────────────

SERVICE_MOD = "agentx.model.rag_v2.rag_v2_agent_service"


def _install_fake_deepagents() -> types.ModuleType:
    """Install a fake ``deepagents`` package into ``sys.modules``.

    Records ``create_deep_agent`` + ``StateBackend`` call args so tests can
    assert wiring without needing a real LLM. Mirrors the feature_025 helper.
    """
    calls: dict[str, list] = {
        "create_deep_agent": [],
        "StateBackend": [],
    }

    mod = types.ModuleType("deepagents")

    def _build_agent_graph(**_):
        graph = MagicMock(name="deep_agent_graph")
        state = MagicMock(name="state")
        state.values = {"messages": []}
        graph.get_state.return_value = state
        return graph

    mod.create_deep_agent = MagicMock(  # type: ignore[attr-defined]
        name="create_deep_agent",
        side_effect=lambda **kw: (
            calls["create_deep_agent"].append(kw),
            _build_agent_graph(**kw),
        )[1],
    )
    mod.__version__ = "0.7.0"  # type: ignore[attr-defined]

    backends = types.ModuleType("deepagents.backends")
    backends.StateBackend = MagicMock(  # type: ignore[attr-defined]
        name="StateBackend",
        side_effect=lambda *a, **kw: (
            calls["StateBackend"].append((a, kw)),
            MagicMock(name="state_backend"),
        )[1],
    )

    middleware = types.ModuleType("deepagents.middleware")
    middleware.FilesystemMiddleware = MagicMock(  # type: ignore[attr-defined]
        name="FilesystemMiddleware"
    )

    summarization = types.ModuleType("deepagents.middleware.summarization")
    summarization.create_summarization_tool_middleware = MagicMock(  # type: ignore[attr-defined]
        name="create_summarization_tool_middleware",
        side_effect=lambda *a, **kw: MagicMock(name="summarization_tool_middleware"),
    )

    sys.modules["deepagents"] = mod
    sys.modules["deepagents.backends"] = backends
    sys.modules["deepagents.middleware"] = middleware
    sys.modules["deepagents.middleware.summarization"] = summarization

    mod._calls = calls  # type: ignore[attr-defined]
    return mod


def _flush_deepagents() -> None:
    for key in list(sys.modules):
        if key == "deepagents" or key.startswith("deepagents."):
            sys.modules.pop(key, None)


def _purge_v2_modules() -> None:
    """Drop the cached v2 agent-service module so a fresh import picks up fakes."""
    for key in list(sys.modules):
        if key.startswith("agentx.model.rag_v2"):
            sys.modules.pop(key, None)


def _fresh_service_module():
    _purge_v2_modules()
    return importlib.import_module(SERVICE_MOD)


# ── Tests (RED) ───────────────────────────────────────────────────────────────


class TestRagV2AgentService:
    """RED: assert the ctor builds a deepagent graph (deepagents importable)."""

    def test_service_uses_create_deep_agent_when_available(self):
        """Behavior 1 — ctor wires ``_agent`` from :func:`create_deep_agent`."""
        _flush_deepagents()
        fake = _install_fake_deepagents()
        try:
            fake.create_deep_agent.reset_mock(side_effect=True)
            fake.create_deep_agent.side_effect = lambda **kw: MagicMock(name="agent")
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.RagV2AgentService(repository_path="/tmp/rag_v2_test")
            assert fake.create_deep_agent.called, (
                "ctor should call create_deep_agent when deepagents is importable"
            )
            assert svc._agent is not None
        finally:
            _flush_deepagents()

    def test_service_registers_chunk_analyst_subagent(self):
        """Behavior 2 — ``subagents=[CHUNK_ANALYST]`` is passed to create_deep_agent."""
        _flush_deepagents()
        fake = _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.RagV2AgentService(repository_path="/tmp/rag_v2_test")
            last_call = fake._calls["create_deep_agent"][-1]
            assert "subagents" in last_call, "ctor must pass subagents= to create_deep_agent"
            subs = last_call["subagents"]
            # The chunk-analyst must appear in the subagent list (by name).
            names = [s.get("name") for s in subs if isinstance(s, dict)]
            assert "chunk-analyst" in names, (
                "subagents= must include the chunk-analyst (G6(b) deepagents closure)"
            )
        finally:
            _flush_deepagents()

    def test_service_writes_state_backend_for_offloading(self):
        """Behavior 3 — ``_backend`` is a ``StateBackend`` instance."""
        _flush_deepagents()
        fake = _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.RagV2AgentService(repository_path="/tmp/rag_v2_test")
            assert svc._backend is not None, (
                "service must hold a StateBackend for offloading (ephemeral chunks)"
            )
            assert fake._calls["StateBackend"], "StateBackend() must be constructed"
        finally:
            _flush_deepagents()

    def test_service_falls_back_to_create_agent_without_deepagents(self):
        """Behavior 4 — if ``import deepagents`` raises, ctor uses legacy ``create_agent``."""
        import sys
        _flush_deepagents()
        # Poison sys.modules so the re-imported service module's `import
        # deepagents` (and the submodules its try/except imports) raises
        # ImportError — CPython contract: a None entry makes `import <name>`
        # raise. Without this, the installed deepagents is importable so the
        # ctor takes the deepagents path and calls the real
        # create_summarization_tool_middleware with a MagicMock llm → TypeError
        # (NOT the fallback under test).
        _poisoned = (
            "deepagents",
            "deepagents.backends",
            "deepagents.middleware.summarization",
        )
        sys.modules["deepagents"] = None  # type: ignore[assignment]
        sys.modules["deepagents.backends"] = None  # type: ignore[assignment]
        sys.modules["deepagents.middleware.summarization"] = None  # type: ignore[assignment]
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                # Should NOT raise; ctor swallows ImportError and falls back.
                svc = mod.RagV2AgentService(repository_path="/tmp/rag_v2_test")
            assert svc._agent is not None, (
                "fallback path must still produce a usable agent via create_agent"
            )
            # Fallback path has NO StateBackend (deepagents unavailable).
            assert getattr(svc, "_backend", None) is None, (
                "fallback path must set _backend = None (no deepagents)"
            )
        finally:
            for key in _poisoned:
                sys.modules.pop(key, None)
            _flush_deepagents()

    def test_service_preserves_thread_id_cancel_history_api(self):
        """Behavior 5 — public surface stays stable across deepagent/fallback paths."""
        _flush_deepagents()
        _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.RagV2AgentService(repository_path="/tmp/rag_v2_test")
            # thread_id — str, stable until reset.
            assert isinstance(svc.thread_id, str) and svc.thread_id
            old = svc.thread_id
            svc.reset_conversation()
            assert svc.thread_id != old, "reset_conversation must mint a new thread_id"
            # is_running — bool, default False.
            assert isinstance(svc.is_running, bool)
            assert svc.is_running is False
            # cancel / get_history — callable.
            assert callable(svc.cancel)
            assert callable(svc.get_history)
            history = svc.get_history()
            assert isinstance(history, list)
        finally:
            _flush_deepagents()


if __name__ == "__main__":
    import unittest
    unittest.main()
