"""RagV2RepositorySelectionController — console repo-selection (feature_027).

G2 parity mirror of v1 ``RagRepositorySelectionController``: returns the
selected ``RagV2Repository`` on a valid 1-based display index, None on
out-of-bounds. Clean filename (no v1 ``rag_repostitory_selection_view.py``
``[sic]`` typo — analysis_001 surprise #4).
"""

from __future__ import annotations

from agentx.model.rag_v2.rag_v2_provider import RagV2Provider
from agentx.model.rag_v2.rag_v2_repository import RagV2Repository
from agentx.ui.screens.rag_v2.rag_v2_repository_selection_view import (
    RagV2RepositorySelectionView,
)


class RagV2RepositorySelectionController:
    """Console repository-selection sub-controller (G2 parity)."""

    def __init__(self, working_directory: str) -> None:
        self.view = RagV2RepositorySelectionView(self)
        self.rag_provider = RagV2Provider(working_directory)
        self._cached_repositories: list[RagV2Repository] | None = None

    def show(self) -> None:
        self.view.show()

    def get_repositories(self) -> list[str] | None:
        """Return the list of valid repository IDs for display (+ cache)."""
        repositories = self.rag_provider.get_repositories()
        if not repositories:
            self._cached_repositories = None
            return None
        self._cached_repositories = list(repositories)
        return [repo.id for repo in self._cached_repositories if repo.id]

    def get_selected_repository(self) -> RagV2Repository | None:
        """Return the user-selected repository (1-based display → 0-based internal).

        Returns None on out-of-bounds / no selection (the documented graceful case).
        """
        if not self._cached_repositories:
            return None
        # The view prompts for a 1-based display index (mirrors v1).
        idx = self.view.get_selected_index() if hasattr(self.view, "get_selected_index") else 0
        candidates = self._cached_repositories
        # 1-based display → 0-based internal; bounds-checked (NOT None on valid).
        if isinstance(idx, int) and 1 <= idx <= len(candidates):
            return candidates[idx - 1]
        return None
