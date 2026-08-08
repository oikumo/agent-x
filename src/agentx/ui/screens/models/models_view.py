"""Console Models view — feature_024 console parity.

Duck-typed controller partner: real ``ModelsController`` exposes
``list_providers()`` / ``get_current_id()`` / ``select_provider(id)`` /
``get_status_text()`` (NOT the spec'd ``select_model(provider, model)``).
Provider objects are duck-typed (``.id`` / ``.name`` / ``.kind``).
"""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IModelsView


class ConsoleModelsView(IModelsView):
    """Console-based Models selector view (numbered menu + selection)."""

    #: Exit tokens for the models REPL (case-insensitive). Matches the RAG
    #: views convention (``rag_chat_controller``: quit/exit; ``rag_*_view``:
    #: cancel/back/q/quit) and the TUI ``models_screen`` ``q`` binding.
    #: Without these the picker traps the user on ``Invalid selection``.
    _EXIT_TOKENS = frozenset({"q", "quit", "back", "exit"})

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(models)")

    def show(self) -> None:
        providers = self.controller.list_providers()
        self.show_available_providers(providers)
        self.show_message(self.controller.get_status_text())
        while True:
            user_input = self.console.capture_input()
            if not user_input:
                return
            if user_input.strip().lower() in self._EXIT_TOKENS:
                return
            provider = self._resolve_selection(user_input, providers)
            if provider is None:
                self.print_error(f"Invalid selection: {user_input}")
                continue
            if self.controller.select_provider(provider.id):
                self.show_message(self.controller.get_status_text())
            else:
                self.print_error(f"Failed to select provider: {provider.id}")

    def _resolve_selection(self, user_input: str, providers: list) -> Any | None:
        """Resolve user input to a provider: 1-based index or exact id."""
        try:
            index = int(user_input)
        except ValueError:
            index = None
        if index is not None and 1 <= index <= len(providers):
            return providers[index - 1]
        for provider in providers:
            if getattr(provider, "id", None) == user_input:
                return provider
        return None

    def show_available_providers(self, providers: list) -> None:
        self.console.info("Available providers (q/quit/back/exit to return):")
        for i, provider in enumerate(providers, 1):
            name = getattr(provider, "name", str(provider))
            kind = getattr(provider, "kind", "")
            self.console.info(f"  {i}. {name} ({kind})")

    def show_models_for_provider(self, provider: str, models: list[str]) -> None:
        self.console.info(f"Models for {provider}:")
        for model in models:
            self.console.info(f"  {model}")

    def show_message(self, message: str) -> None:
        self.console.info(message)

    def print_error(self, message: str) -> None:
        self.console.error(message)
