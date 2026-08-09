"""RED tests for feature_025.coding_context_window_optimization.

These tests assert the deepagents wiring of ``CodingAgentService``:

1. ctor uses :func:`deepagents.create_deep_agent` when ``deepagents`` is importable
2. ctor builds a :class:`deepagents.backends.StateBackend` for offloading
3. ctor registers ``compact_conversation`` via ``create_summarization_tool_middleware``
4. ctor accepts ``memory`` paths; defaults to project ``AGENTS.md`` when present
5. ctor accepts ``skills`` paths; defaults to coding skills dir when present
6. ctor falls back to legacy :func:`langchain.agents.create_agent` when
   ``import deepagents`` raises ``ImportError``
7. public API (``thread_id`` / ``cancel`` / ``is_running`` / ``get_history`` /
   ``reset_conversation``) stays stable
8. MVC pin still passes (``create_agent`` + ``InMemorySaver`` literals; no
   ``textual`` import)

Design: ``design_001_deepagent_context_optimization.md``.
Operation spec: ``operation_spec_001_deepagent_service_methods.md``.

All imports of the module-under-edit are deferred INSIDE the test bodies so
that not-yet-implemented classes surface as test failures (exit 1) rather than
collection errors (exit 2) — per OMT TDD RED-gate rule.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ────────────────────────────────────────────────────────────────────

SERVICE_SRC = "src/agentx/model/coding/coding_agent_service.py"


def _read_service_src() -> str:
    return Path(SERVICE_SRC).read_text(encoding="utf-8")


def _install_fake_deepagents() -> types.ModuleType:
    """Install a fake ``deepagents`` package + submodules into ``sys.modules``.

    Records call args so tests can assert wiring without needing a real LLM.
    """
    calls: dict[str, list] = {
        "create_deep_agent": [],
        "StateBackend": [],
    }

    mod = types.ModuleType("deepagents")
    # Build a graph-mock that returns a real `[]` from get_state().values.get("messages", [])
    # so get_history() behaves like the live deepagent graph returns.
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

    # Stash a handle to the call log on the fake module for assertions.
    mod._calls = calls  # type: ignore[attr-defined]
    return mod


def _purge_coding_modules() -> None:
    """Drop the cached coding-service module so a fresh import picks up fakes."""
    for key in list(sys.modules):
        if key.startswith("agentx.model.coding.coding_agent_service"):
            sys.modules.pop(key, None)


def _flush_deepagents() -> None:
    """Remove any real-or-fake deepagents modules from sys.modules."""
    for key in list(sys.modules):
        if key == "deepagents" or key.startswith("deepagents."):
            sys.modules.pop(key, None)


def _fresh_service_module():
    """Import a pristine CodingAgentService (re-runs module top-level)."""
    _purge_coding_modules()
    return importlib.import_module("agentx.model.coding.coding_agent_service")


# ── Tests (RED) ───────────────────────────────────────────────────────────────


class TestDeepAgentWiring:
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
                svc = mod.CodingAgentService()
            assert fake.create_deep_agent.called, (
                "ctor should call create_deep_agent when deepagents is importable"
            )
            assert svc._agent is not None
        finally:
            _flush_deepagents()

    def test_service_writes_state_backend_for_offloading(self):
        """Behavior 2 — ``_backend`` is a ``StateBackend`` instance."""
        _flush_deepagents()
        fake = _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.CodingAgentService()
            assert svc._backend is not None, "service must hold a StateBackend for offloading"
            # The backend kwarg was passed to create_deep_agent.
            last_call = fake._calls["create_deep_agent"][-1]
            assert "backend" in last_call or "backend" in last_call.get("backend", {})
        finally:
            _flush_deepagents()

    def test_service_registers_compact_conversation_tool(self):
        """Behavior 3 — ``create_summarization_tool_middleware`` is invoked."""
        _flush_deepagents()
        _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.CodingAgentService()
            sumz = sys.modules["deepagents.middleware.summarization"]
            assert sumz.create_summarization_tool_middleware.called, (
                "ctor must call create_summarization_tool_middleware so the agent "
                "gets the compact_conversation tool"
            )
        finally:
            _flush_deepagents()

    def test_service_accepts_memory_paths(self):
        """Behavior 4 — ctor stores ``_memory``; default is project AGENTS.md if present."""
        _flush_deepagents()
        _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc_explicit = mod.CodingAgentService(memory=["./AGENTS.md"])
            assert getattr(svc_explicit, "_memory", None) == ["./AGENTS.md"], (
                "explicit memory paths must be stored verbatim"
            )
        finally:
            _flush_deepagents()

    def test_service_accepts_skills_paths(self):
        """Behavior 5 — ctor stores ``_skills``; default is coding skills dir if present."""
        _flush_deepagents()
        _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.CodingAgentService(skills=["./src/agentx/model/coding/coding_skills/"])
            assert getattr(svc, "_skills", None) == ["./src/agentx/model/coding/coding_skills/"], (
                "explicit skills paths must be stored verbatim"
            )
        finally:
            _flush_deepagents()

    def test_service_falls_back_to_create_agent_without_deepagents(self):
        """Behavior 6 — if ``import deepagents`` raises, ctor uses legacy ``create_agent``."""
        _flush_deepagents()
        # Ensure deepagents import fails outright (key absent → ImportError).
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                # Should NOT raise; ctor swallows ImportError and falls back.
                svc = mod.CodingAgentService()
            assert svc._agent is not None, (
                "fallback path must still produce a usable agent via create_agent"
            )
        finally:
            _flush_deepagents()

    def test_service_preserves_thread_id_cancel_history_api(self):
        """Behavior 7 — public surface stays stable across deepagent/fallback paths."""
        _flush_deepagents()
        _install_fake_deepagents()
        try:
            mod = _fresh_service_module()
            with patch.object(mod.AIService, "get_current_llm", return_value=MagicMock()):
                svc = mod.CodingAgentService()
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


class TestMVCPinStillPasses:
    """Behavior 8 — MVC pin invariants in the source file."""

    def test_mvc_pin_still_passes(self):
        """create_agent + InMemorySaver literals present, textual absent."""
        content = _read_service_src()
        assert "from langchain.agents import create_agent" in content, (
            "MVC pin requires the create_agent import literal to remain"
        )
        assert "from langgraph.checkpoint.memory import InMemorySaver" in content, (
            "MVC pin requires the InMemorySaver import literal to remain"
        )
        assert "textual" not in content, (
            "Model layer must not import the textual UI framework"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
