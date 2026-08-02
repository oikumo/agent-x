"""Console ReAct view — feature_024 console parity.

Duck-typed controller partner: real ``ReactController`` exposes
``send_message(user_message) -> bool`` (NOT the spec'd
``process_user_message``). Pattern follows ``chat_view.py``: a
``UIConsole`` REPL loop that exits on empty input.
"""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IReactView


class ConsoleReactView(IReactView):
# TA: gotcha: BUG (feature_024): ConsoleReactView missing 6 streaming callbacks (show_thinking, show_tool_call, show_tool_result, show_answer_chunk, show_answer_final, show_error) — ReactController streaming silently no-ops. Added in bug_fix phase.
    """Console-based ReAct view (REPL loop + token streaming)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(react)")

    def show(self) -> None:
        self.console.info("Starting ReAct session (empty input to exit):")
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

    # --- Streaming callbacks (feature_024 bug fix) ---

    def show_thinking(self, text: str) -> None:
        """Display reasoning/thinking from the agent."""
        self.console.info(f"💭 {text}")

    def show_tool_call(self, name: str, args: str) -> None:
        """Display a tool call."""
        self.console.info(f"🔧 {name}({args})")

    def show_tool_result(self, name: str, result: str) -> None:
        """Display a tool result."""
        self.console.info(f"📊 {result}")

    def show_answer_chunk(self, text: str) -> None:
        """Display a streaming answer chunk."""
        self.console.stream_write(text)

    def show_answer_final(self) -> None:
        """Finalize the streaming answer."""
        pass  # No state to reset in console mode

    def show_error(self, text: str) -> None:
        """Display an error message."""
        self.console.error(f"⚠️ {text}")
