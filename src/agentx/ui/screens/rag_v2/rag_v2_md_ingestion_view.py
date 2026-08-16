"""RagV2MdIngestionView — console MD ingestion view (feature_027 G4 new)."""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IRagV2MdIngestionView


class RagV2MdIngestionView(IRagV2MdIngestionView):
    """Console MD-ingestion sub-screen view (G4 new)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(rag-v2-md)")

    def show(self) -> None:
        self.console.info("MD ingestion — enter a path (q/quit to cancel):")
        path = self.console.capture_input()
        if path is None or path.strip().lower() in {"q", "quit", "exit"}:
            return
        count = self.controller.ingest_path(path.strip())
        self.console.info(f"Ingested {count} chunks from {path.strip()}")

    def show_error(self, message: str) -> None:
        self.console.error(message)
