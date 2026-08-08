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
# TA: gotcha: BUG (feature_024): ConsoleCodingView missing 6 streaming callbacks (show_thinking, show_tool_call, show_tool_result, show_answer_chunk, show_answer_final, show_error) — CodingController streaming silently no-ops. Added in bug_fix phase.
    """Console-based Coding view (REPL loop + token streaming)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(coding)")
        # Streaming think-state: reasoning deltas accumulate inline on a single
        # line; flushed (one \n) on answer_final or before any non-thinking
        # callback (feature_024 single-line think output).
        self._thinking_active: bool = False

    def show(self) -> None:
        self.console.info("Starting Coding session (empty input to exit):")
        while True:
            user_input = self.console.capture_input()
            if not user_input:
                return
            if not self.controller.send_message(user_input):
                self.console.error("Agent is busy; please wait.")
            self._wait_for_agent()

    def _wait_for_agent(self) -> None:
        """Block the REPL until the agent worker thread finishes.

        ``send_message`` returns immediately after spawning a daemon thread.
        Without this sync point the REPL loop would re-prompt while the agent
        is still running, interleaving user input with streaming output. In
        console (no-TUI) mode there is no ``app.call_from_thread`` — the
        worker calls view callbacks directly — so we simply join the thread.
        """
        worker = getattr(self.controller, "_worker_thread", None)
        if worker is not None and worker.is_alive():
            worker.join()

    def show_message(self, message: str, role: str = "assistant") -> None:
        self.console.info(f"[{role}] {message}")

    def show_partial_message(self, message: str) -> None:
        self.console.stream_write(message)

    def show_stream_message(self, message: str) -> None:
        self.console.info(message)

    def print_error(self, message: str) -> None:
        self.console.error(message)

    # --- Streaming callbacks (feature_024 bug fix) ---

    def _flush_thinking(self) -> None:
        """Emit the trailing newline that closes the single-line thinking block.

        Only fires once per reasoning stream: the first delta printed the ``💭 ``
        prefix inline and subsequent deltas appended without newlines, so the
        whole reasoning block sits on one line. This restores the cursor to a
        fresh line before any tool/answer/error output.
        """
        if self._thinking_active:
            print()  # newline closes the single-line thinking block
            self._thinking_active = False

    def show_thinking(self, text: str) -> None:
# TA: gotcha: gotcha: show_thinking MUST stream via stream_write (no per-delta newline) and flush a single \n on answer_final/_flush_thinking — calling console.info per delta (one print() per reasoning token) renders each token on its own line. Mirrors react_view.py fix.
        """Display reasoning/thinking from the agent.

        Reasoning deltas stream inline on a single line: the first delta prints
        the ``💭 `` prefix (no newline), subsequent deltas append in place, and
        the trailing newline is emitted by ``_flush_thinking`` when the answer
        finalizes or another callback interrupts the block (feature_024 —
        think output must render on one line, not one line per token).
        """
        if not self._thinking_active:
            self.console.stream_write("💭 ")
            self._thinking_active = True
        self.console.stream_write(text)

    def show_tool_call(self, name: str, args: str) -> None:
        """Display a tool call."""
        self._flush_thinking()
        self.console.info(f"🔧 {name}({args})")

    def show_tool_result(self, name: str, result: str) -> None:
        """Display a tool result."""
        self._flush_thinking()
        self.console.info(f"📊 {result}")

    def show_answer_chunk(self, text: str) -> None:
        """Display a streaming answer chunk."""
        self._flush_thinking()
        self.console.stream_write(text)

    def show_answer_final(self) -> None:
        """Finalize the streaming answer (and close any pending thinking line)."""
        self._flush_thinking()

    def show_error(self, text: str) -> None:
        """Display an error message."""
        self._flush_thinking()
        self.console.error(f"⚠️ {text}")
