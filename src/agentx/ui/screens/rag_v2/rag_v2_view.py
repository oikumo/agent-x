"""RagV2View — the console RAG v2 outer composite view (feature_027).

Console-only (no TUI screen sibling — v2 is console-only per the user's
scope decision; v1 stays for the TUI path). Mirrors ``ConsoleReactView``'s
REPL loop + token streaming (feature_024): empty input re-prompts, exit
tokens / interrupt return to the main menu, answer deltas stream via
``console.stream_write`` (no per-delta newline).
"""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IRagV2View


class RagV2View(IRagV2View):
    """Console RAG v2 view — REPL loop + streaming callbacks."""

    _EXIT_TOKENS = frozenset({"q", "quit", "exit"})

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(rag-v2)")

    # --- IRagV2View ---------------------------------------------------------

    def show(self) -> None:
        self.console.info("Starting RAG v2 session (q/quit/exit to return):")
        while True:
            user_input = self.console.capture_input()
            # None = Ctrl+C / Ctrl+D (interrupt) → exit to the agentx main menu.
            if user_input is None:
                return
            # Bare Enter (empty string) → re-prompt, do NOT exit (feature_024 fix).
            if user_input.strip() == "":
                continue
            if user_input.strip().lower() in self._EXIT_TOKENS:
                return
            # Drive the agent's retrieval+synthesis turn.
            if not self.controller.send_message(user_input):
                self.console.error("Agent is busy; please wait.")
            self._wait_for_agent()

    def print_message(self, message: str) -> None:
        self.console.info(message)

    def print_message_error(self, message: str) -> None:
        self.console.error(message)

    def show_repository_state(self, state: object) -> None:
        self.console.info(f"Repository state: {state}")

    def show_menu(self) -> None:
        self.console.info(
            "[1] select repository  [2] create repository  "
            "[3] chat  [4] web ingestion  [5] pdf ingestion  "
            "[6] md ingestion  [s] switch repository  [q] quit"
        )

    # --- Console-parity streaming (feature_024 pattern) ---------------------

    def show_partial_message(self, message: str) -> None:
        """Token streaming — append without a newline (one line per answer)."""
        self.console.stream_write(message)

    def _wait_for_agent(self) -> None:
        """Block the REPL until the agent worker thread finishes (console mode
        has no app.call_from_thread — the worker calls view callbacks directly)."""
        worker = getattr(self.controller, "_worker_thread", None)
        if worker is not None and worker.is_alive():
            worker.join()

    # --- View-driven name capture (used by the controller's create/switch) --

    def capture_repository_name(self) -> str:
        """Prompt the user for a new repository name (console)."""
        self.console.info("Enter a name for the new repository:")
        name = self.console.capture_input()
        return (name or "").strip()

    def get_selected_repository_id(self) -> str | None:
        """Prompt the user for a repository id to switch to (console)."""
        self.console.info("Enter the repository id to switch to:")
        choice = self.console.capture_input()
        if choice is None or choice.strip() == "":
            return None
        return choice.strip()

    def get_selected_index(self) -> int:
        """Prompt the user for a 1-based display index (repository selection)."""
        self.console.info("Enter the repository number to select:")
        choice = self.console.capture_input()
        try:
            return int((choice or "").strip())
        except (TypeError, ValueError):
            return 0
