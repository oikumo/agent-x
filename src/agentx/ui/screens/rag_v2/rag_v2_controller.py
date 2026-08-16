"""RagV2MainController — the console RAG v2 controller (feature_027).

Implements ``IRagV2ViewPartner``; holds ``current_repository`` + ``repositories``
state (G5 multi-repo session-switch closure). Routes to sub-screens via
``set_view()`` (NOT ``.view =`` — feature_024 bug-pin: ``.view =`` leaves
``_view=None`` so streaming callbacks silently no-op; Constraint d).

Parity mirror of v1 ``RagController`` (``rag/rag_controller.py``): G1 create,
G2 select, G3 get_rag_state — v1 already ships these; v2 mirrors for the
console contract, NOT net-new.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from agentx.model.session.session_manager import SessionManager
from agentx.model.rag_v2.rag_v2_repository import RagV2Repository
from agentx.ui.interfaces import IRagV2View, IRagV2ViewPartner


@dataclass
class RagV2State:
    """Snapshot of the active repository's RAG state (mirrors v1 ``RagState``)."""

    url: str | None
    data_base_location: str | None
    documents_location: str | None


class RagV2MainController(IRagV2ViewPartner):
    """Console RAG v2 orchestrator — owns repository state + routes sub-screens."""

    def __init__(self, view: IRagV2View | None = None) -> None:
        self.session_controller = SessionManager()
        self.rag_working_directory = self.session_controller.get_directory_rag()
        # G5: the active repository + the known-repositories registry (switch closure).
        self.current_repository: RagV2Repository | None = None
        self.repositories: dict[str, RagV2Repository] = {}
        # The view is set ONLY via set_view() (feature_024 bug-pin Constraint d).
        self.view: IRagV2View | None = view
        self._view: IRagV2View | None = view
        # The DeepAgents-backed agent service (built lazily on first chat).
        self._agent_service = None
        # Console chat worker (feature_024 parity with ReactController): the
        # view REPL calls send_message() then joins this thread.
        self._worker_thread: threading.Thread | None = None

    # --- view wiring (feature_024 bug-pin: set_view, NOT .view =) ------------

    def set_view(self, view: IRagV2View) -> None:
        """Wire the console view — sets BOTH ``view`` + ``_view``.

        Constraint d (feature_024): the OLD ``controller.view = view`` pattern
        left ``_view=None`` so streaming callbacks silently no-op; ``set_view``
        sets both so the controller + the agent-service callbacks resolve.
        """
        self.view = view
        self._view = view

    # --- IRagV2ViewPartner (G1/G2/G3/G5 parity) ------------------------------

    def show(self) -> None:
        if self.view is not None:
            self.view.show()

    def select_repository(self) -> None:
        """G2 parity — delegate to the repository-selection sub-controller."""
        from agentx.ui.screens.rag_v2.rag_v2_repository_selection_controller import (
            RagV2RepositorySelectionController,
        )

        selector = RagV2RepositorySelectionController(working_directory=self.rag_working_directory)
        selector.show()
        repo = selector.get_selected_repository()
        if repo is not None:
            self.current_repository = repo
            self.repositories[repo.id] = repo
            # Repo swap invalidates the agent service (bound to the old path).
            self._agent_service = None
            if self.view is not None:
                self.view.print_message(f"Selected repository: {repo.id}")
        else:
            if self.view is not None:
                self.view.print_message("No repository selected.")

    def create_repository(self) -> RagV2Repository | None:
        """G1 parity — prompt a name + create the repository on disk.

        Returns the created ``RagV2Repository`` (NOT None) on a valid name.
        The view captures the name; the inner ``_create_repository`` validates +
        creates the directory + registers it.
        """
        if self.view is None:
            return None
        name = self.view.capture_repository_name() if hasattr(self.view, "capture_repository_name") else ""
        if not name:
            return None
        repo = self._create_repository(name)
        if repo is not None:
            self.current_repository = repo
            self.repositories[repo.id] = repo
            # Repo swap invalidates the agent service (bound to the old path).
            self._agent_service = None
            self.view.print_message(f"Repository '{repo.id}' created successfully!")
            return repo
        self.view.print_message_error("Failed to create repository.")
        return None

    def _create_repository(self, name: str) -> RagV2Repository | None:
        """Validate the name + create the repository directory (G1)."""
        import re
        from pathlib import Path

        if not name or not name.strip():
            return None
        if not re.match(r"^[A-Za-z0-9_\-]+$", name):
            return None
        repo_path = str(Path(self.rag_working_directory) / name)
        Path(repo_path).mkdir(parents=True, exist_ok=True)
        return RagV2Repository(id=name, path=repo_path)

    def switch_repository(self) -> None:
        """G5 — swap the active repository; no leak of the prior repo's state.

        The user picks a repository id from the view; if it is a known
        repository, ``current_repository`` swaps to it (refresh state downstream).
        """
        if self.view is None:
            return
        repo_id = self.view.get_selected_repository_id() if hasattr(self.view, "get_selected_repository_id") else None
        if repo_id and repo_id in self.repositories:
            self.current_repository = self.repositories[repo_id]
            # Repo swap invalidates the agent service (bound to the old path).
            self._agent_service = None
            self.view.print_message(f"Switched to repository: {repo_id}")
        else:
            self.view.print_message_error(f"Unknown repository: {repo_id}")

    def show_chat(self) -> None:
        """Menu [3]: prime the DeepAgents orchestrator for the active repo.

        The console REPL itself is the chat loop (any non-menu input goes to
        ``send_message``); this menu action just pre-builds the service so a
        misconfiguration surfaces immediately, not on the first question.
        """
        if self.current_repository is None:
            if self._view is not None:
                self._view.print_message_error(
                    "No repository selected — create [2] or select [1] one first."
                )
            return
        if self._ensure_agent_service() and self._view is not None:
            self._view.print_message("Chat ready — type your question (q to leave).")

    # --- Console chat (feature_024 parity with ReactController.send_message) --

    def send_message(self, user_message: str) -> bool:
        """Send a user question to the RAG v2 agent (console REPL contract).

        Mirrors ``ReactController.send_message``: rejects with False ONLY when
        the agent is busy (the view then shows "Agent is busy"). Every other
        path is handled inline (error via the view) and returns True. The turn
        runs on ``self._worker_thread``; the view's ``_wait_for_agent`` joins
        it (console mode has no app.call_from_thread — callbacks fire on the
        worker thread and print directly).
        """
        if not user_message or not user_message.strip():
            return True
        if self.current_repository is None:
            if self._view is not None:
                self._view.print_message_error(
                    "No repository selected — create [2] or select [1] one first."
                )
            return True
        if not self._ensure_agent_service():
            return True
        if self._agent_service is not None and self._agent_service.is_running:
            return False
        thread = threading.Thread(
            target=self._run_agent,
            args=(user_message,),
            daemon=True,
            name="AgentX-RagV2-Worker",
        )
        self._worker_thread = thread
        thread.start()
        return True

    def _ensure_agent_service(self) -> bool:
        """Lazily build the ``RagV2AgentService`` for the active repository.

        Returns False (after surfacing an error via the view) when no
        repository is active or the service cannot be built (e.g. no LLM
        configured) — the REPL must survive both.
        """
        if self._agent_service is not None:
            return True
        if self.current_repository is None:
            return False
        try:
            from agentx.model.rag_v2.rag_v2_agent_service import RagV2AgentService

            self._agent_service = RagV2AgentService(
                repository_path=self.current_repository.path
            )
            return True
        except Exception as exc:
            if self._view is not None:
                self._view.print_message_error(
                    f"Failed to start the RAG v2 agent: {exc}"
                )
            return False

    def _run_agent(self, user_message: str) -> None:
        """Worker-thread body: stream one agent turn to the console view.

        Console parity: no Textual app marshalling — the view callbacks print
        directly (same as the ``ReactController._run_agent`` no-app fallback).
        Answer deltas stream via ``show_partial_message`` (no per-delta
        newline); ``on_done`` terminates the answer line.
        """
        view = self._view
        service = self._agent_service
        if view is None or service is None:
            return
        # IRagV2View declares only the menu surface; the streaming sink lives
        # on the console view (RagV2View.show_partial_message). Duck-type it
        # like this controller's other console-only captures.
        show_partial = getattr(view, "show_partial_message", lambda _t: None)
        try:
            service.stream_agent(
                user_message,
                on_answer=show_partial,
                on_done=lambda: show_partial("\n"),
                on_error=lambda e: view.print_message_error(f"RAG v2 agent error: {e}"),
            )
        except Exception as exc:
            view.print_message_error(f"RAG v2 agent error: {exc}")

    def show_web_ingestion(self) -> None:
        if self.current_repository is None:
            return
        from agentx.ui.screens.rag_v2.rag_v2_web_ingestion_controller import (
            RagV2WebIngestionController,
        )

        RagV2WebIngestionController(self.current_repository).show()

    def show_pdf_ingestion(self) -> None:
        if self.current_repository is None:
            return
        from agentx.ui.screens.rag_v2.rag_v2_pdf_ingestion_controller import (
            RagV2PdfIngestionController,
        )

        RagV2PdfIngestionController(self.current_repository).show()

    def show_md_ingestion(self) -> None:
        if self.current_repository is None:
            return
        from agentx.ui.screens.rag_v2.rag_v2_md_ingestion_controller import (
            RagV2MdIngestionController,
        )

        RagV2MdIngestionController(self.current_repository).show()

    def close(self) -> None:
        if self.view is not None:
            self.view.print_message("close")

    # --- G3 — get_rag_state() hygiene ---------------------------------------

    def get_rag_state(self) -> RagV2State | None:
        """Return the active repository's RAG state, or None if none selected.

        Parity with v1 ``rag_controller.py:66-107``: selected repository WITH
        artifacts present → populated ``RagV2State``; no repository → None.
        """
        if self.current_repository is None or not self.current_repository.path:
            return None
        rag = self._rag_for_current()
        if rag is None:
            return None
        data_base_path: str | None = None
        documents_path: str | None = None
        url: str | None = None
        if rag.database_exists():
            data_base_path = rag.vector_db_path
            url = rag.get_ingested_url()
        if rag.documents_exist():
            documents_path = rag.documents_path
        return RagV2State(
            url=url,
            data_base_location=data_base_path,
            documents_location=documents_path,
        )

    def _rag_for_current(self):
        """Build the ``RagV2`` aggregate for the active repository (seam)."""
        from agentx.model.rag_v2.rag_v2 import RagV2

        return RagV2(working_directory=self.current_repository.path)  # type: ignore[union-attr]
