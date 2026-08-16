"""RagV2 — the active repository aggregate (feature_027).

Mirrors v1 ``Rag`` (``agentx.model.rag.rag``) shape, pprint-free (surprise #1
from analysis_001: ``rag_query.py:40`` ``pprint.pprint`` polluted stdout in
the model layer — v2 keeps pprint out of ``model/rag_v2/``). Owns the active
repository's DB + docs + ingestion-URL state queries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from agentx.model.rag_v2.rag_v2_db import RagV2Database


class RagV2:
    """Aggregate over one repository's RAG state (DB + docs + ingestion URL)."""

    def __init__(self, working_directory: str) -> None:
        self._working_directory = Path(working_directory)
        # v1 layout: vector_db_path + documents_path under the working dir.
        self.vector_db_path: str = str(self._working_directory / "chroma")
        self.documents_path: str = str(self._working_directory / "documents")
        self._db = RagV2Database(str(self._working_directory / "rag_v2.db"))

    def database_exists(self) -> bool:
        return Path(self.vector_db_path).exists()

    def documents_exist(self) -> bool:
        return Path(self.documents_path).exists()

    def get_ingested_url(self) -> Optional[str]:
        """Return the last-ingested web URL for this repository, or None."""
        try:
            return self._db.get_ingested_url()
        except Exception:
            return None

    def record_ingestion(self, url: str | None = None, kind: str = "web") -> None:
        """Record a completed ingestion (URL for web; path for pdf/md)."""
        self._db.record_ingestion(url=url, kind=kind)
