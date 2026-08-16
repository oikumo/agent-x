"""RED tests for feature_027.rag_v2 — command registration + console views.

Mirrors ``test_console_commands_and_views.py`` (feature_024) for v2:

  (a) The console ``rag`` command repoints to ``show_rag_v2`` then calls
      ``controller._rag_v2_view.show()`` (KEY: ``show_*`` must NOT call
      ``view.show()`` — the console command enters the REPL via ``view.show()``).
      v2 is console-only; the TUI path keeps v1's ``show_rag``.
  (b) ``MainController.load_commands`` registers the v2 console ``rag`` command.
  (c) ``RagV2View.show()`` REPL loop → ``controller.send_message``; empty input
      re-prompts; ``q``/``quit``/``exit`` or Ctrl+C/Ctrl+D exits.
  (d) ``RagV2View.show_partial_message`` → ``console.stream_write``.

All v2 symbol imports are deferred inside the test bodies so RED failures
surface as test failures (pytest exit 1), NOT collection errors (exit 2).
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from agentx.ui.interfaces import IUIProvider
from agentx.ui.screens.main.main_controller import MainController


def _load_symbol(module_path: str, name: str) -> Any:
    """Import a symbol that may not exist yet (RED) — fails inside the test."""
    module = importlib.import_module(module_path)
    return getattr(module, name)


# ── (a) console rag command repoints → show_rag_v2 ─────────────────────────


class TestConsoleRagCommandRoutesToV2(TestCase):
    """The console `rag` command routes to show_rag_v2 via a new RagV2ShowCommand.

    v2 is console-only; v1's ``RagShowCommand`` stays for the TUI path. In
    console mode the new ``RagV2ShowCommand("rag", ...)`` is registered at the
    ``rag`` key (repoint, not a new key) — calls ``controller.show_rag_v2()``
    then ``controller._rag_v2_view.show()`` (feature_024 parity wiring).
    """

    def test_rag_command_calls_show_rag_v2_then_view_show(self) -> None:
        controller = MagicMock()

        calls: list[str] = []
        controller.show_rag_v2 = MagicMock(
            side_effect=lambda: calls.append("show_rag_v2")
        )
        view = MagicMock()
        controller._rag_v2_view = view
        view.show.side_effect = lambda: calls.append("view.show")

        command_cls = _load_symbol(
            "agentx.ui.screens.main.commands.commands", "RagV2ShowCommand"
        )
        command = command_cls("rag", controller)
        command.run([])

        controller.show_rag_v2.assert_called_once()
        view.show.assert_called_once()
        # The command must wire show_rag_v2() first, then enter the view REPL.
        assert calls == ["show_rag_v2", "view.show"], (
            "console rag command (RagV2ShowCommand) must call show_rag_v2() then "
            "view.show() (repoint)"
        )


# ── (b) load_commands registers the v2 console rag command ─────────────────


class TestLoadCommandsRegistration(TestCase):
    """MainController.load_commands registers the console rag command."""

    def test_load_commands_registers_rag_command(self) -> None:
        controller = MainController(provider=MagicMock(spec=IUIProvider))
        assert "rag" in controller.commands, "missing command: rag"


# ── (c) RagV2View REPL loop ────────────────────────────────────────────────


class TestRagV2View(TestCase):
    """(c)/(d) RagV2View REPL loop + token streaming."""

    def setUp(self) -> None:
        view_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_view", "RagV2View"
        )
        self.controller = MagicMock()
        self.controller.send_message.return_value = True
        self.view = view_cls(self.controller)
        self.view.console = MagicMock()

    def test_show_enters_repl_loop_and_exits_on_interrupt(self) -> None:
        """None (Ctrl+C/Ctrl+D) exits the v2 module to the main menu."""
        self.view.console.capture_input.side_effect = ["hello agent", None]

        self.view.show()

        self.controller.send_message.assert_called_once_with("hello agent")
        assert self.view.console.capture_input.call_count == 2

    def test_show_empty_input_reprompts_does_not_exit(self) -> None:
        """A bare Enter (empty string) re-prompts the v2 module instead of
        returning to the agentx main menu (feature_024 parity)."""
        self.view.console.capture_input.side_effect = ["", "hello agent", "q"]

        self.view.show()

        self.controller.send_message.assert_called_once_with("hello agent")
        assert self.view.console.capture_input.call_count == 3

    def test_show_exits_on_quit_token(self) -> None:
        """q/quit/exit tokens exit the v2 module (case-insensitive)."""
        for token in ("q", "quit", "exit", "QUIT", "Exit"):
            self.controller.reset_mock()
            self.view.console.reset_mock()
            self.view.console.capture_input.side_effect = [token]

            self.view.show()

            self.controller.send_message.assert_not_called()

    def test_show_partial_message_streams_via_stream_write(self) -> None:
        """Streaming tokens go through console.stream_write (no per-delta newline)."""
        self.view.show_partial_message("token-1")
        self.view.console.stream_write.assert_called_once_with("token-1")


if __name__ == "__main__":
    import unittest
    unittest.main()
