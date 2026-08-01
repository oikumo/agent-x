"""feature_024.no_tui_full_features — cycle 2 RED tests.

Console parity commands + console views:

  (a) The 5 command classes call ``controller.show_*()`` then
      ``controller._<x>_view.show()`` — KEY DESIGN: ``show_*`` must NOT call
      ``view.show()`` (TUI pushes screens; console commands enter the REPL
      via ``view.show()``).
  (b) ``MainController.load_commands`` registers
      react/coding/models/agent/fast-agent.
  (c) ``ConsoleReactView.show()`` REPL loop → ``controller.send_message``;
      exits on empty input (real controllers expose ``send_message``, NOT the
      spec'd ``process_user_message`` — duck-typed partner).
  (d) ``ConsoleReactView.show_partial_message`` → ``console.stream_write``.
  (e) ``ConsoleModelsView`` provider listing + numeric selection.
  (f) ``ConsoleFastAgentView.show_cycle_summary`` rendering.

Testlist behaviors covered: ReactCommand/CodingCommand/ModelsCommand/
AgentCommand/FastAgentCommand → show_*; load_commands registration;
ConsoleReactView loop + partial; ConsoleModelsView listing;
ConsoleFastAgentView summary.

Note: not-yet-existing classes are imported lazily inside the tests so the
RED failures surface as test failures (exit 1) rather than collection
errors (exit 2) — the TDD gate requires runnable RED.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from agentx.ui.interfaces import IUIProvider
from agentx.ui.screens.main.main_controller import MainController

_COMMANDS_MODULE = "agentx.ui.screens.main.commands.commands"


def _load_symbol(module_path: str, name: str) -> Any:
    """Import a symbol that may not exist yet (RED) — fails inside the test."""
    module = importlib.import_module(module_path)
    return getattr(module, name)


class TestConsoleParityCommands(TestCase):
    """(a) Command classes call controller.show_*() then view.show()."""

    def _assert_command_flow(
        self,
        class_name: str,
        key: str,
        show_method: str,
        view_attr: str,
    ) -> None:
        command_cls = _load_symbol(_COMMANDS_MODULE, class_name)
        controller = MagicMock()
        view = MagicMock()
        setattr(controller, view_attr, view)

        calls: list[str] = []
        getattr(controller, show_method).side_effect = lambda: calls.append("show_*")
        view.show.side_effect = lambda: calls.append("view.show")

        command = command_cls(key, controller)
        command.run([])

        getattr(controller, show_method).assert_called_once()
        view.show.assert_called_once()
        assert calls == ["show_*", "view.show"], (
            "command must wire via show_*() first, then enter the view REPL"
        )

    def test_react_command_calls_show_react_then_view_show(self) -> None:
        self._assert_command_flow("ReactCommand", "react", "show_react", "_react_view")

    def test_coding_command_calls_show_coding_then_view_show(self) -> None:
        self._assert_command_flow("CodingCommand", "coding", "show_coding", "_coding_view")

    def test_models_command_calls_show_models_then_view_show(self) -> None:
        self._assert_command_flow("ModelsCommand", "models", "show_models", "_models_view")

    def test_agent_command_calls_show_agent_then_view_show(self) -> None:
        self._assert_command_flow("AgentCommand", "agent", "show_agent", "_agent_view")

    def test_fast_agent_command_calls_show_fast_agent_then_view_show(self) -> None:
        self._assert_command_flow(
            "FastAgentCommand", "fast-agent", "show_fast_agent", "_fast_agent_view"
        )


class TestLoadCommandsRegistration(TestCase):
    """(b) load_commands registers the 5 console-parity commands."""

    def test_load_commands_registers_console_parity_commands(self) -> None:
        controller = MainController(provider=MagicMock(spec=IUIProvider))

        for key in ("react", "coding", "models", "agent", "fast-agent"):
            assert key in controller.commands, f"missing command: {key}"


class TestConsoleReactView(TestCase):
    """(c)/(d) ConsoleReactView REPL loop + token streaming."""

    def setUp(self) -> None:
        view_cls = _load_symbol("agentx.ui.screens.react.react_view", "ConsoleReactView")
        self.controller = MagicMock()
        self.controller.send_message.return_value = True
        self.view = view_cls(self.controller)
        self.view.console = MagicMock()

    def test_show_enters_repl_loop_and_exits_on_empty_input(self) -> None:
        self.view.console.capture_input.side_effect = ["hello agent", None]

        self.view.show()

        self.controller.send_message.assert_called_once_with("hello agent")
        assert self.view.console.capture_input.call_count == 2

    def test_show_partial_message_streams_via_stream_write(self) -> None:
        self.view.show_partial_message("token-1")

        self.view.console.stream_write.assert_called_once_with("token-1")


def _provider(pid: str, name: str, kind: str = "cloud") -> SimpleNamespace:
    return SimpleNamespace(id=pid, name=name, kind=kind, description=f"{name} provider")


class TestConsoleModelsView(TestCase):
    """(e) ConsoleModelsView provider listing + selection."""

    def setUp(self) -> None:
        view_cls = _load_symbol("agentx.ui.screens.models.models_view", "ConsoleModelsView")
        self.controller = MagicMock()
        self.providers = [
            _provider("openrouter", "OpenRouter"),
            _provider("ollama", "Ollama", kind="local"),
        ]
        self.controller.list_providers.return_value = self.providers
        self.controller.get_current_id.return_value = "openrouter"
        self.controller.get_status_text.return_value = "Current: OpenRouter (cloud)"
        self.controller.select_provider.return_value = True
        self.view = view_cls(self.controller)
        self.view.console = MagicMock()

    def test_show_lists_providers_and_selects_on_numeric_input(self) -> None:
        self.view.console.capture_input.side_effect = ["2", None]

        self.view.show()

        self.controller.list_providers.assert_called()
        printed = " ".join(
            str(call.args[0]) for call in self.view.console.info.call_args_list
        )
        assert "OpenRouter" in printed and "Ollama" in printed
        self.controller.select_provider.assert_called_once_with("ollama")

    def test_show_models_for_provider_lists_models(self) -> None:
        self.view.show_models_for_provider("openrouter", ["gpt-4o", "claude-3.5"])

        printed = " ".join(
            str(call.args[0]) for call in self.view.console.info.call_args_list
        )
        assert "openrouter" in printed
        assert "gpt-4o" in printed and "claude-3.5" in printed


class TestConsoleFastAgentView(TestCase):
    """(f) ConsoleFastAgentView cycle summary rendering."""

    def test_show_cycle_summary_prints_summary_fields(self) -> None:
        view_cls = _load_symbol(
            "agentx.ui.screens.fast_agent.fast_agent_view", "ConsoleFastAgentView"
        )
        controller = MagicMock()
        view = view_cls(controller)
        view.console = MagicMock()
        summary = {"cycles": 3, "status": "done", "answer": "42"}

        view.show_cycle_summary(summary)

        printed = " ".join(
            str(call.args[0]) for call in view.console.info.call_args_list
        )
        assert "cycles" in printed and "42" in printed
