"""Console Coding view — feature_024 console parity.

Duck-typed controller partner: real ``CodingController`` exposes
``send_message(user_message) -> bool``. Pattern follows ``chat_view.py``:
a ``UIConsole`` REPL loop that exits on empty input.
"""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import ICodingView


class ConsoleCodingView(ICodingView):
    """Console-based Coding view (REPL loop + token streaming)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(coding)")

    def show(self) -> None:
        self.console.info("Starting Coding session (empty input to exit):")
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
