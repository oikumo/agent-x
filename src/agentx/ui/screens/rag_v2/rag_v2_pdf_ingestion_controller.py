"""RagV2PdfIngestionController — console PDF ingestion (feature_027 G4 new)."""

from __future__ import annotations

from agentx.ui.screens.rag_v2.rag_v2_pdf_ingestion_view import (
    RagV2PdfIngestionView,
)


class RagV2PdfIngestionController:
    """Console PDF-ingestion sub-controller (G4 new)."""

    def __init__(self, repository) -> None:
        self._repository = repository
        self._view = RagV2PdfIngestionView(self)

    def show(self) -> None:
        self._view.show()

    def ingest_path(self, pdf_path: str) -> int:
        from agentx.model.rag_v2.pdf_ingestion.pdf_ingest import ingest_pdf

        return ingest_pdf(pdf_path, repository_path=self._repository.path)
