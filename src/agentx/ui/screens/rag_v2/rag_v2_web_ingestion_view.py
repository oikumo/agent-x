"""RagV2WebIngestionView — console web-ingestion view (feature_027 G4)."""

from __future__ import annotations

from typing import Any

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import IRagV2WebIngestionView


class RagV2WebIngestionView(IRagV2WebIngestionView):
    """Console web-ingestion sub-screen view (G6(a) inner parity)."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.console = UIConsole("(rag-v2-web)")

    def show(self) -> None:
        self.console.info("Web ingestion (q/quit to cancel):")
        url = self.console.capture_input()
        if url is None or url.strip().lower() in {"q", "quit", "exit"}:
            return
        count = self.controller.ingest_url(url.strip())
        self.console.info(f"Ingested {count} chunks from {url.strip()}")

    def show_error(self, message: str) -> None:
        self.console.error(message)
