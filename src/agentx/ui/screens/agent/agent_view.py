"""Console Advanced Agent view — feature_024 console parity.

Duck-typed controller partner: ``AgentController`` exposes
``send_message(user_message) -> bool``. Pattern follows ``chat_view.py``:
a ``UIConsole`` REPL loop that exits on empty input.
"""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IAgentView


class ConsoleAgentView(IAgentView):
    """Console-based Advanced Agent view (REPL loop + token streaming)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(agent)")

    def show(self) -> None:
        self.console.info("Starting Agent session (empty input to exit):")
        while True:
            user_input = self.console.capture_input()
            if not user_input:
                return
            self.controller.send_message(user_input)

    def show_message(self, message: str, role: str = "assistant") -> None:
        self.console.info(f"[{role}] {message}")

    def show_partial_message(self, message: str) -> None:
        self.console.stream_write(message)

    def show_stream_message(self, message: str) -> None:
        self.console.info(message)

    def print_error(self, message: str) -> None:
        self.console.error(message)
