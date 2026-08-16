"""RagV2CreateRepositoryController — console create-repo (feature_027 G1 parity)."""

from __future__ import annotations

from agentx.model.rag_v2.rag_v2_repository import RagV2Repository
from agentx.ui.screens.rag_v2.rag_v2_create_repository_view import (
    RagV2CreateRepositoryView,
)


class RagV2CreateRepositoryController:
    """Console repository-creation sub-controller (G1 parity)."""

    def __init__(self, working_directory: str) -> None:
        self._view = RagV2CreateRepositoryView(self)
        self._working_directory = working_directory
        self._created_repository: RagV2Repository | None = None

    def show(self) -> RagV2Repository | None:
        self._view.show()
        return self._created_repository

    def get_prompt(self) -> str:
        return "(rag-v2-create-repository)"

    def on_name_entered(self, name: str) -> bool:
        import re
        from pathlib import Path

        name = name.strip()
        if not name or not re.match(r"^[A-Za-z0-9_\-]+$", name):
            self._view.show_error("Invalid repository name")
            return False
        repo_path = str(Path(self._working_directory) / name)
        Path(repo_path).mkdir(parents=True, exist_ok=True)
        repo = RagV2Repository(id=name, path=repo_path)
        self._created_repository = repo
        self._view.show_success(name, repo_path)
        return True
