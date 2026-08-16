"""RagV2CreateRepositoryView — console create-repo view (feature_027 G1)."""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IRagV2CreateRepositoryView


class RagV2CreateRepositoryView(IRagV2CreateRepositoryView):
    """Console repository-creation sub-screen view (G6(a) inner parity)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(rag-v2-create)")

    # --- IRagV2CreateRepositoryView -----------------------------------------

    def show(self) -> None:
        self.console.info("Create a new RAG v2 repository (q/quit to cancel):")
        name = self.console.capture_input()
        if name is None or name.strip().lower() in {"q", "quit", "exit"}:
            return
        self.controller.on_name_entered(name or "")

    def show_error(self, message: str) -> None:
        self.console.error(message)

    def show_success(self, repo_id: str, repo_path: str) -> None:
        self.console.info(f"Repository '{repo_id}' created at {repo_path}")
