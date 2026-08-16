"""RagV2MdIngestionController — console MD ingestion (feature_027 G4 new)."""

from __future__ import annotations

from agentx.ui.screens.rag_v2.rag_v2_md_ingestion_view import (
    RagV2MdIngestionView,
)


class RagV2MdIngestionController:
    """Console MD-ingestion sub-controller (G4 new)."""

    def __init__(self, repository) -> None:
        self._repository = repository
        self._view = RagV2MdIngestionView(self)

    def show(self) -> None:
        self._view.show()

    def ingest_path(self, md_path: str) -> int:
        from agentx.model.rag_v2.md_ingestion.md_ingest import ingest_md

        return ingest_md(md_path, repository_path=self._repository.path)
