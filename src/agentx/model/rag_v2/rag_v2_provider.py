"""RagV2Provider — factory constructing the RagV2 aggregate (feature_027).

Mirrors v1 ``RagProvider`` (``agentx.model.rag.rag_provider``) shape.
"""

from __future__ import annotations

from agentx.model.rag_v2.rag_v2 import RagV2
from agentx.model.rag_v2.rag_v2_repository import RagV2Repository


class RagV2Provider:
    """Discovers + builds v2 repository aggregates from a working directory."""

    def __init__(self, working_directory: str) -> None:
        self._working_directory = working_directory

    def get_repositories(self) -> list[RagV2Repository]:
        """Return the list of valid repositories under the working directory."""
        from pathlib import Path

        root = Path(self._working_directory)
        if not root.is_dir():
            return []
        repos: list[RagV2Repository] = []
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                repos.append(RagV2Repository(id=entry.name, path=str(entry)))
        return repos

    def get_repository(self, repo_id: str) -> RagV2Repository | None:
        for repo in self.get_repositories():
            if repo.id == repo_id:
                return repo
        return None

    def build(self, repository_path: str) -> RagV2:
        return RagV2(working_directory=repository_path)
