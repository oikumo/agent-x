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
# TA: gotcha: BUG (feature_024): ConsoleFastAgentView missing show_memory_view required by IAgentViewPartner — m9 isinstance check fails. Added in bug_fix phase.
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

    # --- Additional methods for AgentController compatibility ---

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

    def show_message(self, message: str, role: str = "assistant") -> None:
        """Show a complete message."""
        self.console.info(f"[{role}] {message}")

    def show_partial_message(self, message: str) -> None:
        """Show partial (streaming) message."""
        self.console.stream_write(message)

    def show_stream_message(self, message: str) -> None:
        """Stream message with typing effect."""
        self.console.info(message)

    # --- IAgentViewPartner contract (feature_024 bug fix) ---

    def show_memory_view(self, query: Any) -> None:
        """Search/show memory entries (no-op for console)."""
        pass
