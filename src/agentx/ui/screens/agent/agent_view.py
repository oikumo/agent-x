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
# TA: gotcha: BUG (feature_024): ConsoleAgentView missing show_memory_view required by IAgentViewPartner — m9 isinstance check fails. Added in bug_fix phase.
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

    # --- Additional methods for controller compatibility ---

    def show_status(self, status: Any) -> None:
        """Display agent status."""
        if isinstance(status, dict):
            self.console.info(
                f"Agent: {status.get('name', '?')} | "
                f"state: {status.get('state', '?')} | "
                f"goals: {status.get('goals', 0)} | "
                f"rules: {status.get('rules', 0)} | "
                f"tools: {status.get('tools', 0)}"
            )
        else:
            self.console.info(str(status))

    def refresh_goal_tree(self) -> None:
        """Refresh the goal tree display (no-op for console)."""
        pass

    def show_reflection_log(self, entries: list) -> None:
        """Display reflection log entries."""
        for entry in entries:
            critique = getattr(entry, 'critique', None)
            if critique:
                summary = getattr(critique, 'summary', 'N/A')
                self.console.info(f"Reflection: {summary}")
            else:
                self.console.info("Reflection: (no critique)")

    def show_policy_editor(self, rules: list) -> None:
        """Display policy editor (no-op for console)."""
        pass

    # --- IAgentViewPartner contract (feature_024 bug fix) ---

    def show_memory_view(self, query: Any) -> None:
        """Search/show memory entries (no-op for console)."""
        pass
