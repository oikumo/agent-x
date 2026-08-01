"""Console Fast Agent view — feature_024 console parity.

Duck-typed controller partner: the Fast Agent controller exposes
``send_message(user_message) -> bool``. Pattern follows ``chat_view.py``:
a ``UIConsole`` loop that exits on empty input; cycle results render via
``show_cycle_summary``.
"""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IFastAgentView


class ConsoleFastAgentView(IFastAgentView):
    """Console-based Fast Agent view (single-turn loop + cycle summary)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(fast-agent)")

    def show(self) -> None:
        self.console.info("Fast Agent (empty input to exit):")
        while True:
            user_input = self.console.capture_input()
            if not user_input:
                return
            self.controller.send_message(user_input)

    def show_cycle_summary(self, summary: dict) -> None:
        self.console.info("Cycle summary:")
        for key, value in summary.items():
            self.console.info(f"  {key}: {value}")

    def print_error(self, message: str) -> None:
        self.console.error(message)
