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
from agentx.model.rag_v2.rag_v2_provider import RagV2Provider
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

    # --- Slash-command operations (feature_029 design_001 §Command surface) --

    def list_repositories(self) -> None:
        """``/repos`` — list on-disk repositories, mark active, refresh registry.

        Deterministic (no LLM): reads via ``RagV2Provider`` over the RAG
        working directory; the session registry is refreshed from disk so
        ``/use <id>`` can resolve repos created in earlier sessions.
        """
        if self._view is None:
            return
        repos = RagV2Provider(self.rag_working_directory).get_repositories()
        self.repositories = {repo.id: repo for repo in repos}
        if not repos:
            self._view.print_message(
                "No repositories yet — /create <name> to make one."
            )
            return
        active_id = (
            self.current_repository.id if self.current_repository is not None else None
        )
        lines = ["Repositories:"]
        for repo in repos:
            marker = " (active)" if repo.id == active_id else ""
            lines.append(f"  {repo.id}{marker}")
        self._view.print_message("\n".join(lines))

    def use_repository(self, repo_id: str | None) -> None:
        """``/use [id]`` — activate a repository directly (no LLM).

        Bare ``/use`` falls back to the interactive picker
        (``select_repository``). With an id: session registry first, then
        on-disk via ``RagV2Provider`` (registering it), else an error. Any
        successful swap invalidates the bound agent service (G5 closure).
        """
        if self._view is None:
            return
        if repo_id is None or not str(repo_id).strip():
            self.select_repository()
            return
        repo_id = str(repo_id).strip()
        repo = self.repositories.get(repo_id)
        if repo is None:
            repo = RagV2Provider(self.rag_working_directory).get_repository(repo_id)
            if repo is not None:
                self.repositories[repo.id] = repo
        if repo is None:
            self._view.print_message_error(f"Unknown repository: {repo_id}")
            return
        self.current_repository = repo
        # Repo swap invalidates the agent service (bound to the old path).
        self._agent_service = None
        self._view.print_message(f"Active repository: {repo.id}")

    def create_repository_named(self, name: str | None) -> RagV2Repository | None:
        """``/create [name]`` — direct create (no LLM, no prompt).

        Bare ``/create`` falls back to the prompt flow (``create_repository``).
        With a name: same validation as the prompt flow (``_create_repository``);
        success activates + registers the repo and invalidates the agent service.
        """
        if self._view is None:
            return None
        if name is None or not str(name).strip():
            return self.create_repository()
        repo = self._create_repository(str(name).strip())
        if repo is None:
            self._view.print_message_error(
                f"Invalid repository name: {name!r} "
                "(letters, digits, '_' and '-' only)."
            )
            return None
        self.current_repository = repo
        self.repositories[repo.id] = repo
        # Repo swap invalidates the agent service (bound to the old path).
        self._agent_service = None
        self._view.print_message(f"Repository '{repo.id}' created successfully!")
        return repo

    def ingest(self, kind: str | None, target: str | None) -> None:
        """``/ingest <web|pdf|md> <target>`` — direct ingestion (no LLM).

        Calls the same ``ingest_web``/``ingest_pdf``/``ingest_md`` functions
        the sub-screen controllers use, bound to the ACTIVE repository path.
        Guards (in order): active repository, kind enum, non-empty target.
        """
        if self._view is None:
            return
        if self.current_repository is None:
            self._view.print_message_error(
                "No repository selected — /use <id> or /create <name> first."
            )
            return
        if kind is None or kind not in self._INGEST_KINDS:
            self._view.print_message_error(
                "Usage: /ingest <web|pdf|md> <url|path>"
            )
            return
        if target is None or not str(target).strip():
            self._view.print_message_error(f"Usage: /ingest {kind} <url|path>")
            return
        try:
            loader, fn_name = self._INGEST_KINDS[kind]
            module = __import__(loader, fromlist=[fn_name])
            chunks = getattr(module, fn_name)(
                str(target).strip(),
                repository_path=self.current_repository.path,
            )
            self._view.print_message(
                f"Ingested {chunks} chunks into '{self.current_repository.id}'."
            )
        except Exception as exc:
            # The REPL must survive ingestion failures (network, parse, etc.).
            self._view.print_message_error(f"Ingestion failed: {exc}")

    def show_status(self) -> None:
        """``/status`` — active repo + ``RagV2State`` + thread id (no LLM)."""
        if self._view is None:
            return
        if self.current_repository is None:
            self._view.print_message(
                "No active repository — /use <id> or /create <name> first."
            )
            return
        state = self.get_rag_state()
        lines = [
            f"Repository: {self.current_repository.id}",
            f"Path: {self.current_repository.path}",
            f"URL: {(state.url if state else None) or '<none>'}",
            "Database: "
            f"{(state.data_base_location if state else None) or '<none>'}",
            "Documents: "
            f"{(state.documents_location if state else None) or '<none>'}",
        ]
        if self._agent_service is not None:
            lines.append(f"Thread: {self._agent_service.thread_id}")
        else:
            lines.append("Thread: <no active conversation>")
        self._view.print_message("\n".join(lines))

    def reset_chat(self) -> None:
        """``/reset`` — start a new conversation thread (no LLM)."""
        if self._view is None:
            return
        if self._agent_service is None:
            self._view.print_message("No active conversation — nothing to reset.")
            return
        self._agent_service.reset_conversation()
        self._view.print_message("Conversation reset — next question starts fresh.")

    # feature_029: friendly labels for streamed tool activity (» / « lines).
    _TOOL_LABELS = {
        "search_documents": "search",
        "ingestion_status": "status",
        "task": "analyst",
    }

    _INGEST_KINDS = {
        "web": ("agentx.model.rag_v2.web_ingestion.web_ingest", "ingest_web"),
        "pdf": ("agentx.model.rag_v2.pdf_ingestion.pdf_ingest", "ingest_pdf"),
        "md": ("agentx.model.rag_v2.md_ingestion.md_ingest", "ingest_md"),
    }

    # feature_029: show_chat() removed — the [3] chat menu entry was a fake
    # mode (chat is the REPL's bare-text default; the agent service builds
    # lazily on the first question via send_message/_ensure_agent_service).

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
                # feature_029: surface retrieval/delegation as it happens —
                # » labels map tool names to user-friendly verbs.
                on_tool_call=lambda name, args: view.print_message(
                    f"» {self._TOOL_LABELS.get(name, name)}: {args}"
                ),
                on_tool_result=lambda name, preview: view.print_message(
                    f"« {self._TOOL_LABELS.get(name, name)}: {preview}"
                ),
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
