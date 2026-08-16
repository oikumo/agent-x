"""RagV2WebIngestionController — console web-ingestion (feature_027 G4)."""

from __future__ import annotations

from agentx.ui.screens.rag_v2.rag_v2_web_ingestion_view import (
    RagV2WebIngestionView,
)


class RagV2WebIngestionController:
    """Console web-ingestion sub-controller (G4 web path, v1 asyncio ported)."""

    def __init__(self, repository) -> None:
        self._repository = repository
        self._view = RagV2WebIngestionView(self)

    def show(self) -> None:
        self._view.show()

    def ingest_url(self, url: str) -> int:
        from agentx.model.rag_v2.web_ingestion.web_ingest import ingest_web

        return ingest_web(url, repository_path=self._repository.path)
