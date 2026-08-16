"""RagV2Database — SQLite journal of v2 ingestion entries (feature_027).

Mirrors v1 ``RagDatabase`` (``agentx.model.rag.rag_db``) schema, cleansed of
stdout pollution (analysis_001 surprise #1). Tracks the last-ingested URL +
the per-source kind (web/pdf/md).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class RagV2Database:
    """SQLite journal of RAG v2 ingestion entries for one repository."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS ingestion (
                       id    INTEGER PRIMARY KEY AUTOINCREMENT,
                       kind  TEXT NOT NULL,
                       url   TEXT,
                       path  TEXT,
                       ts    TEXT NOT NULL DEFAULT (datetime('now'))
                   )"""
            )
            conn.commit()

    def record_ingestion(
        self, *, url: Optional[str] = None, path: Optional[str] = None, kind: str = "web"
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO ingestion (kind, url, path) VALUES (?, ?, ?)",
                (kind, url, path),
            )
            conn.commit()

    def get_ingested_url(self) -> Optional[str]:
        """Return the most-recent web-ingestion URL, or None."""
        try:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT url FROM ingestion WHERE kind='web' AND url IS NOT NULL "
                    "ORDER BY id DESC LIMIT 1"
                ).fetchone()
            return row[0] if row else None
        except sqlite3.Error:
            return None

    @staticmethod
    def create_if_not_exists(db_path: str) -> "RagV2Database":
        db = RagV2Database(db_path)
        db._ensure_schema()
        return db
