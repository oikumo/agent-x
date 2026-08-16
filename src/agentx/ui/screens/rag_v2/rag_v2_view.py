"""RagV2View — the console RAG v2 outer composite view (feature_027;
slash-command grammar added in feature_029).

Console-only (no TUI screen sibling — v2 is console-only per the user's
scope decision; v1 stays for the TUI path). Hybrid interaction grammar
(feature_029): bare text is a chat question for the active repository;
``/…`` prefixes deterministic, no-LLM local commands (``/help`` lists them).
Empty input re-prompts; exit tokens / ``/quit`` / interrupt return to the
main menu; answer deltas stream via ``console.stream_write`` (no per-delta
newline).
"""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IRagV2View
from agentx.ui.screens.rag_v2.constants import (
    RAG_V2_BANNER,
    RAG_V2_HELP,
    RAG_V2_MENU,
)


class RagV2View(IRagV2View):
    """Console RAG v2 view — slash commands + chat REPL + streaming callbacks."""

    _EXIT_TOKENS = frozenset({"q", "quit", "exit"})

    # Slash commands routed to same-named controller operations (deterministic,
    # no-LLM). ``help``/``quit`` are view-local; ``search`` is the explicit
    # chat route (send_message). feature_029 design_001 §Command surface.
    _CONTROLLER_COMMANDS = {
        "repos": "list_repositories",
        "use": "use_repository",
        "create": "create_repository_named",
        "ingest": "ingest",
        "status": "show_status",
        "reset": "reset_chat",
    }
    # Commands whose controller operation takes NO argument.
    _NO_ARG_COMMANDS = frozenset({"repos", "status", "reset"})

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(rag-v2)")

    # --- IRagV2View ---------------------------------------------------------

    def show(self) -> None:
        self.show_menu()
        while True:
            user_input = self.console.capture_input()
            # None = Ctrl+C / Ctrl+D (interrupt) → exit to the agentx main menu.
            if user_input is None:
                return
            # Bare Enter (empty string) → re-prompt, do NOT exit (feature_024 fix).
            if user_input.strip() == "":
                continue
            token = user_input.strip()
            if token.lower() in self._EXIT_TOKENS:
                return
            # feature_029: `/…` is a deterministic command; anything else is a
            # chat question for the active repository (the old _MENU_ACTIONS
            # digit map is gone — bare "1"/"s" reach the agent).
            if token.startswith("/"):
                if not self._dispatch_command(token):
                    return
                continue
            # Drive the agent's retrieval+synthesis turn.
            if not self.controller.send_message(user_input):
                self.console.error("Agent is busy; please wait.")
            self._wait_for_agent()

    # --- Slash-command dispatch (feature_029) -------------------------------

    def _dispatch_command(self, text: str) -> bool:
        """Route a `/…` command. Returns False only for `/quit` (exit)."""
        parts = text[1:].split(maxsplit=1)
        name = parts[0].lower() if parts and parts[0] else ""
        args = parts[1].strip() if len(parts) > 1 else ""
        if name == "quit":
            return False
        if name == "help":
            self.console.info(RAG_V2_HELP)
            return True
        if name == "search":
            if not args:
                self.console.error("Usage: /search <question>")
                return True
            if not self.controller.send_message(args):
                self.console.error("Agent is busy; please wait.")
            self._wait_for_agent()
            return True
        method_name = self._CONTROLLER_COMMANDS.get(name)
        if method_name is None:
            self.console.error(f"Unknown command: /{name} — try /help")
            return True
        handler = getattr(self.controller, method_name, None)
        if not callable(handler):
            self.console.error(f"Command /{name} is not available.")
            return True
        if name in self._NO_ARG_COMMANDS:
            handler()
        elif name == "ingest":
            kind, _, target = args.partition(" ")
            handler(kind or None, target.strip() or None)
        else:
            handler(args or None)
        return True

    def print_message(self, message: str) -> None:
        self.console.info(message)

    def print_message_error(self, message: str) -> None:
        self.console.error(message)

    def show_repository_state(self, state: object) -> None:
        self.console.info(f"Repository state: {state}")

    def show_menu(self) -> None:
        """Banner + hint (feature_029: the command table prints on /help)."""
        self.console.info(RAG_V2_BANNER)
        self.console.info(RAG_V2_MENU)

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
