"""RagV2RepositorySelectionView — console repo-selection view (feature_027)."""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IRagV2RepositorySelectionView


class RagV2RepositorySelectionView(IRagV2RepositorySelectionView):
    """Console repository-selection sub-screen view (G6(a) inner parity)."""

    _EXIT_TOKENS = frozenset({"q", "quit", "exit", "back"})

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(rag-v2-select)")

    # --- IRagV2RepositorySelectionView --------------------------------------

    def show(self) -> None:
        self.console.info("Select a repository (q/quit/back to return):")
        repos = self.controller.get_repositories()
        if not repos:
            self.console.info("No repositories found. Create one first.")
            return
        for i, rid in enumerate(repos, 1):
            self.console.info(f"  [{i}] {rid}")

    def get_selected_index(self) -> int:
        self.console.info("Enter the repository number:")
        choice = self.console.capture_input()
        try:
            return int((choice or "").strip())
        except (TypeError, ValueError):
            return 0
