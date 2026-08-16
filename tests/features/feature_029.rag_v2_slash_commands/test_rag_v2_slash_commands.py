"""RED tests for feature_029.rag_v2_slash_commands — hybrid slash-command grammar.

Pins the design_001 command surface:

  * ``/help`` prints the command table; an unknown ``/cmd`` errors with a
    ``/help`` hint — NEITHER reaches ``send_message`` (the slash branch is
    deterministic, no-LLM by design).
  * ``/search <query>`` is the explicit chat route; bare ``/search`` is a
    usage error.
  * Bare text stays the chat default; ``q``/``quit``/``exit``/``/quit`` exit;
    empty input re-prompts.
  * Menu-collision regression: bare ``"1"``/``"s"`` reach ``send_message``
    (the feature_027 ``_MENU_ACTIONS`` digit map is deleted).
  * ``/repos`` ``/use`` ``/create`` ``/ingest`` ``/status`` ``/reset`` route
    to the new deterministic controller operations.
  * Streaming surfaces tool activity: AI ``tool_calls`` → ``on_tool_call``,
    tool messages → ``on_tool_result`` (≤120-char previews), answer stream +
    summarization filter intact.
  * Tools renamed ``search_documents``/``ingestion_status`` (no
    ``repository_path`` in schemas); ``show_chat`` removed from the v2
    partner ABC + controller.

All v2 symbol imports are deferred inside test bodies (feature_027 pattern)
so RED failures surface as test failures, NOT collection errors.
"""

from __future__ import annotations

import importlib
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, patch


def _load_symbol(module_path: str, name: str) -> Any:
    module = importlib.import_module(module_path)
    return getattr(module, name)


def _make_view(inputs: list[str | None]):
    """Build a RagV2View with a scripted input feed + a MagicMock controller.

    Returns (view, controller, console_mock) — ``console_mock.info`` /
    ``.error`` capture every printed line for assertions.
    """
    view_cls = _load_symbol("agentx.ui.screens.rag_v2.rag_v2_view", "RagV2View")
    controller = MagicMock()
    controller.send_message.return_value = True
    view = view_cls(controller)
    console = MagicMock()
    feed = iter(inputs)
    console.capture_input.side_effect = lambda: next(feed, "q")
    view.console = console
    # The REPL joins the worker thread after send_message; the mock controller
    # has a MagicMock _worker_thread — make join a no-op.
    controller._worker_thread = None
    return view, controller, console


def _printed(console: MagicMock) -> str:
    """Every line the view printed (info + error), joined."""
    lines: list[str] = []
    for call in console.info.call_args_list + console.error.call_args_list:
        lines.append(str(call.args[0]) if call.args else "")
    return "\n".join(lines)


# ── b1 — /help + unknown command ──────────────────────────────────────────────


class TestSlashHelpAndUnknown(TestCase):
    """The slash branch is deterministic: /help + unknown commands never
    reach the LLM (design_001 §Command surface)."""

    def test_help_prints_command_table_without_send_message(self) -> None:
        view, controller, console = _make_view(["/help", "q"])
        view.show()
        out = _printed(console)
        for cmd in ("/search", "/repos", "/use", "/create", "/ingest", "/status", "/reset", "/quit"):
            assert cmd in out, f"/help must list {cmd}"
        controller.send_message.assert_not_called()

    def test_unknown_slash_command_errors_with_help_hint(self) -> None:
        view, controller, console = _make_view(["/frobnicate", "q"])
        view.show()
        out = _printed(console)
        assert "unknown" in out.lower() or "frobnicate" in out, (
            "unknown /cmd must surface an error naming the command"
        )
        assert "/help" in out, "unknown /cmd must point at /help"
        controller.send_message.assert_not_called()

    def test_bare_help_word_is_chat_not_command(self) -> None:
        """Only the `/` prefix is a command — bare 'help' is a question."""
        view, controller, _ = _make_view(["help", "q"])
        view.show()
        controller.send_message.assert_called_once_with("help")


# ── b2 — /search routing ──────────────────────────────────────────────────────


class TestSlashSearch(TestCase):
    """``/search <query>`` is the explicit chat route (design_001 §Command
    surface); bare ``/search`` is a usage error that never reaches the LLM."""

    def test_search_routes_query_to_send_message(self) -> None:
        view, controller, _ = _make_view(["/search what is chunk 3 about?", "q"])
        view.show()
        controller.send_message.assert_called_once_with("what is chunk 3 about?")

    def test_search_query_is_not_requoted_or_trimmed_to_pieces(self) -> None:
        """Multi-word queries arrive intact (single string, spaces preserved)."""
        view, controller, _ = _make_view(["/search   spaced   out query  ", "q"])
        view.show()
        args = controller.send_message.call_args.args[0]
        assert "spaced" in args and "out query" in args

    def test_bare_search_is_usage_error_no_send(self) -> None:
        view, controller, console = _make_view(["/search", "q"])
        view.show()
        out = _printed(console)
        assert "usage" in out.lower() or "/search <" in out, (
            "bare /search must print a usage line"
        )
        controller.send_message.assert_not_called()


# ── b3+b4 — chat default, exits, menu-collision regression ────────────────────


class TestChatDefaultExitsAndCollisions(TestCase):
    """Bare text is chat (unchanged default); exit tokens work; the old
    numeric menu no longer eats questions (feature_029 design_001)."""

    def test_bare_text_routes_to_send_message(self) -> None:
        view, controller, _ = _make_view(["what does the doc say about X?", "q"])
        view.show()
        controller.send_message.assert_called_once_with(
            "what does the doc say about X?"
        )

    def test_exit_tokens_quit(self) -> None:
        for token in ("q", "quit", "exit", "/quit"):
            view, controller, _ = _make_view([token])
            # feed exhausted after the token; default "q" would loop forever
            # only if the token failed to exit — the mock feed returns "q".
            view.show()
            controller.send_message.assert_not_called()

    def test_empty_input_reprompts_without_send(self) -> None:
        view, controller, _ = _make_view(["", "   ", "q"])
        view.show()
        controller.send_message.assert_not_called()

    def test_menu_collision_regression_digits_are_chat(self) -> None:
        """feature_027 bug class: '1' selected a repository; 's' switched.
        Both must now reach the agent as ordinary questions."""
        for token in ("1", "s", "6"):
            view, controller, _ = _make_view([token, "q"])
            view.show()
            controller.send_message.assert_called_once_with(token)

    def test_interrupt_returns_cleanly(self) -> None:
        view, controller, _ = _make_view([None])
        view.show()
        controller.send_message.assert_not_called()


# ── b5 — /repos ───────────────────────────────────────────────────────────────


class TestSlashRepos(TestCase):
    """``/repos`` → ``list_repositories()``: lists on-disk repositories,
    marks the active one, refreshes the session registry (op spec)."""

    def test_repos_routes_to_list_repositories(self) -> None:
        view, controller, _ = _make_view(["/repos", "q"])
        view.show()
        controller.list_repositories.assert_called_once_with()

    def test_list_repositories_real_controller(self) -> None:
        import tempfile
        from pathlib import Path

        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "alpha").mkdir()
            Path(tmp, "beta").mkdir()
            controller.rag_working_directory = tmp
            controller.current_repository = repo_cls(
                id="alpha", path=str(Path(tmp, "alpha"))
            )
            controller.list_repositories()
            printed = "\n".join(
                str(c.args[0]) for c in view.print_message.call_args_list
            )
            assert "alpha" in printed and "beta" in printed, (
                "/repos must list every on-disk repository"
            )
            assert "(active)" in printed, "/repos must mark the active repository"
            assert set(controller.repositories) == {"alpha", "beta"}, (
                "/repos must refresh the session registry from disk"
            )

    def test_list_repositories_empty_hints_create(self) -> None:
        import tempfile

        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        with tempfile.TemporaryDirectory() as tmp:
            controller.rag_working_directory = tmp
            controller.list_repositories()
            printed = "\n".join(
                str(c.args[0]) for c in view.print_message.call_args_list
            )
            assert "/create" in printed, "empty /repos must hint at /create"


# ── b6 — /use ─────────────────────────────────────────────────────────────────


class TestSlashUse(TestCase):
    """``/use [id]`` — direct activation (registry → disk → error); bare
    ``/use`` falls back to the interactive picker (op spec)."""

    def test_use_with_id_routes_argument(self) -> None:
        view, controller, _ = _make_view(["/use alpha", "q"])
        view.show()
        controller.use_repository.assert_called_once_with("alpha")

    def test_bare_use_routes_none(self) -> None:
        view, controller, _ = _make_view(["/use", "q"])
        view.show()
        controller.use_repository.assert_called_once_with(None)

    def _real_controller(self):
        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        return controller, view, repo_cls

    def test_use_repository_from_registry(self) -> None:
        controller, view, repo_cls = self._real_controller()
        controller.repositories["beta"] = repo_cls(id="beta", path="/tmp/beta")
        controller._agent_service = object()  # stale service must invalidate
        controller.use_repository("beta")
        assert controller.current_repository is not None
        assert controller.current_repository.id == "beta"
        assert controller._agent_service is None, (
            "repo swap must invalidate the bound agent service"
        )

    def test_use_repository_from_disk(self) -> None:
        import tempfile
        from pathlib import Path

        controller, view, _ = self._real_controller()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "gamma").mkdir()
            controller.rag_working_directory = tmp
            controller.use_repository("gamma")
            assert controller.current_repository is not None
            assert controller.current_repository.id == "gamma"
            assert "gamma" in controller.repositories, (
                "disk-resolved repo must enter the session registry"
            )

    def test_use_repository_unknown_errors(self) -> None:
        import tempfile

        controller, view, _ = self._real_controller()
        with tempfile.TemporaryDirectory() as tmp:
            controller.rag_working_directory = tmp
            controller.use_repository("nope")
            view.print_message_error.assert_called()
            assert controller.current_repository is None

    def test_bare_use_falls_back_to_interactive_picker(self) -> None:
        controller, view, _ = self._real_controller()
        with patch.object(controller, "select_repository") as picker:
            controller.use_repository(None)
            picker.assert_called_once_with()


# ── b7 — /create ──────────────────────────────────────────────────────────────


class TestSlashCreate(TestCase):
    """``/create [name]`` — direct create (same validation as the prompt
    flow); bare ``/create`` falls back to the prompt (op spec)."""

    def test_create_with_name_routes_argument(self) -> None:
        view, controller, _ = _make_view(["/create myrepo", "q"])
        view.show()
        controller.create_repository_named.assert_called_once_with("myrepo")

    def test_bare_create_routes_none(self) -> None:
        view, controller, _ = _make_view(["/create", "q"])
        view.show()
        controller.create_repository_named.assert_called_once_with(None)

    def _real_controller(self):
        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        return controller, view

    def test_create_named_creates_and_activates(self) -> None:
        import tempfile
        from pathlib import Path

        controller, view = self._real_controller()
        with tempfile.TemporaryDirectory() as tmp:
            controller.rag_working_directory = tmp
            repo = controller.create_repository_named("myrepo")
            assert repo is not None, "valid name must return the repository"
            assert Path(tmp, "myrepo").is_dir(), "repository dir must exist"
            assert controller.current_repository is not None
            assert controller.current_repository.id == "myrepo"
            assert "myrepo" in controller.repositories
            assert controller._agent_service is None

    def test_create_named_invalid_name_errors(self) -> None:
        import tempfile
        from pathlib import Path

        controller, view = self._real_controller()
        with tempfile.TemporaryDirectory() as tmp:
            controller.rag_working_directory = tmp
            repo = controller.create_repository_named("bad name!")
            assert repo is None, "invalid name must not create"
            view.print_message_error.assert_called()
            assert list(Path(tmp).iterdir()) == [], "no dir on invalid name"

    def test_bare_create_falls_back_to_prompt_flow(self) -> None:
        controller, view = self._real_controller()
        with patch.object(controller, "create_repository") as prompt_flow:
            controller.create_repository_named(None)
            prompt_flow.assert_called_once_with()


# ── b8 — /ingest ──────────────────────────────────────────────────────────────


class TestSlashIngest(TestCase):
    """``/ingest <web|pdf|md> <target>`` — direct ingestion on the active
    repository, bypassing the sub-screen prompts (op spec)."""

    def test_ingest_routes_kind_and_target(self) -> None:
        view, controller, _ = _make_view(["/ingest web http://example.com", "q"])
        view.show()
        controller.ingest.assert_called_once_with("web", "http://example.com")

    def test_ingest_missing_args_routes_nones(self) -> None:
        view, controller, _ = _make_view(["/ingest", "q"])
        view.show()
        controller.ingest.assert_called_once_with(None, None)

    def _real_controller(self):
        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        return controller, view, repo_cls

    def test_ingest_without_active_repo_errors(self) -> None:
        controller, view, _ = self._real_controller()
        controller.current_repository = None
        controller.ingest("web", "http://example.com")
        view.print_message_error.assert_called()

    def test_ingest_bad_kind_is_usage_error(self) -> None:
        import tempfile

        controller, view, repo_cls = self._real_controller()
        with tempfile.TemporaryDirectory() as tmp:
            controller.current_repository = repo_cls(id="r", path=tmp)
            controller.ingest("stone", "tablet")
            out = "\n".join(
                str(c.args[0]) for c in view.print_message_error.call_args_list
            )
            assert "usage" in out.lower() or "web|pdf|md" in out

    def test_ingest_missing_target_is_usage_error(self) -> None:
        import tempfile

        controller, view, repo_cls = self._real_controller()
        with tempfile.TemporaryDirectory() as tmp:
            controller.current_repository = repo_cls(id="r", path=tmp)
            controller.ingest("pdf", None)
            view.print_message_error.assert_called()

    def test_ingest_dispatches_to_kind_functions(self) -> None:
        import tempfile

        controller, view, repo_cls = self._real_controller()
        cases = [
            ("web", "http://example.com",
             "agentx.model.rag_v2.web_ingestion.web_ingest", "ingest_web"),
            ("pdf", "/tmp/doc.pdf",
             "agentx.model.rag_v2.pdf_ingestion.pdf_ingest", "ingest_pdf"),
            ("md", "/tmp/notes.md",
             "agentx.model.rag_v2.md_ingestion.md_ingest", "ingest_md"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            controller.current_repository = repo_cls(id="r", path=tmp)
            for kind, target, module_path, fn_name in cases:
                view.reset_mock()
                with patch(f"{module_path}.{fn_name}", return_value=7) as fn:
                    controller.ingest(kind, target)
                    fn.assert_called_once_with(target, repository_path=tmp), (
                        f"/ingest {kind} must call {fn_name}(target, "
                        f"repository_path=<active repo>)"
                    )
                printed = "\n".join(
                    str(c.args[0]) for c in view.print_message.call_args_list
                )
                assert "7" in printed, (
                    f"/ingest {kind} must report the ingested chunk count"
                )


# ── b9 — /status ──────────────────────────────────────────────────────────────


class TestSlashStatus(TestCase):
    """``/status`` — active repo + ``RagV2State`` fields + conversation
    thread id; deterministic, no LLM (op spec)."""

    def test_status_routes_to_show_status_no_args(self) -> None:
        view, controller, _ = _make_view(["/status", "q"])
        view.show()
        controller.show_status.assert_called_once_with()

    def _real_controller(self):
        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        return controller, view, repo_cls

    def test_status_without_repo_hints(self) -> None:
        controller, view, _ = self._real_controller()
        controller.current_repository = None
        controller.show_status()
        printed = "\n".join(
            str(c.args[0]) for c in view.print_message.call_args_list
        )
        assert "/use" in printed or "/create" in printed, (
            "no-repo /status must hint how to select one"
        )

    def test_status_prints_repo_state_and_thread(self) -> None:
        import tempfile

        controller, view, repo_cls = self._real_controller()
        with tempfile.TemporaryDirectory() as tmp:
            controller.current_repository = repo_cls(id="r1", path=tmp)
            service = MagicMock()
            service.thread_id = "thread-123"
            controller._agent_service = service
            controller.show_status()
            printed = "\n".join(
                str(c.args[0]) for c in view.print_message.call_args_list
            )
            assert "r1" in printed and tmp in printed, (
                "/status must show the active repo id + path"
            )
            for label in ("url", "database", "documents"):
                assert label in printed.lower(), (
                    f"/status must show the {label} state field"
                )
            assert "thread-123" in printed, (
                "/status must surface the conversation thread id"
            )


# ── b10 — /reset ──────────────────────────────────────────────────────────────


class TestSlashReset(TestCase):
    """``/reset`` — new conversation thread; safe when no service exists
    (op spec: confirms either way)."""

    def test_reset_routes_to_reset_chat_no_args(self) -> None:
        view, controller, _ = _make_view(["/reset", "q"])
        view.show()
        controller.reset_chat.assert_called_once_with()

    def _real_controller(self):
        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        return controller, view

    def test_reset_with_service_resets_conversation(self) -> None:
        controller, view = self._real_controller()
        service = MagicMock()
        controller._agent_service = service
        controller.reset_chat()
        service.reset_conversation.assert_called_once_with()
        printed = "\n".join(
            str(c.args[0]) for c in view.print_message.call_args_list
        )
        assert "reset" in printed.lower()

    def test_reset_without_service_is_graceful(self) -> None:
        controller, view = self._real_controller()
        controller._agent_service = None
        controller.reset_chat()  # must not raise
        printed = "\n".join(
            str(c.args[0]) for c in view.print_message.call_args_list
        )
        assert printed, "/reset with no service must still say something"


# ── b11 — tool-activity streaming ─────────────────────────────────────────────


class TestToolActivityStreaming(TestCase):
    """Retrieval must be VISIBLE: AI ``tool_calls`` → ``on_tool_call``; tool
    messages → ``on_tool_result`` (≤120-char previews); the controller prints
    friendly ``» search:`` / ``» analyst:`` lines (design_001 §surfacing)."""

    def _dispatcher(self):
        return _load_symbol(
            "agentx.model.rag_v2.rag_v2_agent_service", "_dispatch_stream_delta"
        )

    def _ai_msg(self, content: str = "", tool_calls: list | None = None):
        msg = MagicMock()
        msg.type = "ai"
        msg.content = content
        msg.tool_calls = tool_calls or []
        return msg

    def test_tool_calls_route_to_on_tool_call(self) -> None:
        calls: list[tuple[str, str]] = []
        msg = self._ai_msg(tool_calls=[
            {"name": "search_documents", "args": {"query": "chunk 3", "k": 5}}
        ])
        self._dispatcher()(
            "model",
            {"messages": [msg]},
            on_reasoning=None,
            on_tool_call=lambda n, a: calls.append((n, a)),
            on_tool_result=None,
            on_answer=None,
        )
        assert len(calls) == 1 and calls[0][0] == "search_documents", (
            "AI tool_calls must fire on_tool_call with the tool name"
        )
        assert "chunk 3" in calls[0][1], "on_tool_call must carry the args"

    def test_tool_message_routes_to_on_tool_result_truncated(self) -> None:
        results: list[tuple[str, str]] = []
        msg = MagicMock()
        msg.type = "tool"
        msg.name = "search_documents"
        msg.content = "x" * 500
        msg.tool_calls = []
        self._dispatcher()(
            "tools",
            {"messages": [msg]},
            on_reasoning=None,
            on_tool_call=None,
            on_tool_result=lambda n, p: results.append((n, p)),
            on_answer=None,
        )
        assert len(results) == 1 and results[0][0] == "search_documents"
        assert len(results[0][1]) <= 120, (
            "tool-result previews must truncate (chunk text is huge)"
        )

    def test_summarization_filter_precedes_tool_routing(self) -> None:
        fired: list[str] = []
        msg = self._ai_msg(
            content="noise",
            tool_calls=[{"name": "search_documents", "args": {}}],
        )
        self._dispatcher()(
            "model",
            {"lc_source": "summarization", "messages": [msg]},
            on_reasoning=lambda t: fired.append("reasoning"),
            on_tool_call=lambda n, a: fired.append("tool_call"),
            on_tool_result=lambda n, p: fired.append("tool_result"),
            on_answer=lambda t: fired.append("answer"),
        )
        assert fired == [], "summarization noise must not surface anywhere"

    def test_answer_stream_still_fires_without_tool_calls(self) -> None:
        answers: list[str] = []
        msg = self._ai_msg(content="the answer")
        self._dispatcher()(
            "model",
            {"messages": [msg]},
            on_reasoning=None,
            on_tool_call=None,
            on_tool_result=None,
            on_answer=answers.append,
        )
        assert answers == ["the answer"]

    def test_run_agent_wires_friendly_tool_lines(self) -> None:
        """The controller maps tool names to friendly labels and prints
        ``» label: args`` / ``« label: preview`` lines via the view."""
        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        controller = ctrl_cls()
        view = MagicMock()
        controller.set_view(view)
        service = MagicMock()
        controller._agent_service = service
        controller._run_agent("a question")
        kwargs = service.stream_agent.call_args.kwargs
        on_tool_call = kwargs.get("on_tool_call")
        on_tool_result = kwargs.get("on_tool_result")
        assert callable(on_tool_call) and callable(on_tool_result), (
            "_run_agent must wire on_tool_call/on_tool_result"
        )
        on_tool_call("search_documents", "{'query': 'x'}")
        on_tool_call("task", "{'description': 'read chunk_1'}")
        on_tool_result("search_documents", "preview")
        lines = [
            str(c.args[0]) for c in view.print_message.call_args_list
        ]
        assert any(l.startswith("» search:") for l in lines), lines
        assert any(l.startswith("» analyst:") for l in lines), lines
        assert any(l.startswith("« search:") for l in lines), lines


# ── b12 — tool rename (search_documents / ingestion_status) ───────────────────


class TestToolRename(TestCase):
    """feature_029 rename: ``rag_search`` → ``search_documents``,
    ``rag_ingest_status`` → ``ingestion_status`` — clean cut, no aliases
    (user-directed; supersedes feature_027's name-freeze note)."""

    _TOOLS_MOD = "agentx.model.rag_v2.rag_v2_tools"

    def test_module_level_tools_renamed(self) -> None:
        tools = _load_symbol(self._TOOLS_MOD, "RAG_V2_TOOLS")
        names = {t.name for t in tools}
        assert "search_documents" in names
        assert "ingestion_status" in names
        assert "rag_search" not in names, "old name must be gone (clean cut)"
        assert "rag_ingest_status" not in names

    def test_bound_tool_names_renamed(self) -> None:
        build = _load_symbol(self._TOOLS_MOD, "build_rag_v2_tools")
        tools = build("/tmp/feature_029_rename_probe")
        names = {t.name for t in tools}
        assert names == {"search_documents", "ingestion_status"}, names

    def test_bound_schemas_expose_no_repository_path(self) -> None:
        """feature_027 fix preserved through the rename: the path is bound
        server-side; the model cannot hallucinate what it cannot supply."""
        build = _load_symbol(self._TOOLS_MOD, "build_rag_v2_tools")
        tools = build("/tmp/feature_029_rename_probe")
        by_name = {t.name: t for t in tools}
        search_args = set(by_name["search_documents"].args)
        assert search_args <= {"query", "k"}, search_args
        assert "repository_path" not in search_args
        status_args = set(by_name["ingestion_status"].args)
        assert "repository_path" not in status_args

    def test_impl_and_result_symbols_renamed(self) -> None:
        for symbol in (
            "_search_documents_impl",
            "_ingestion_status_impl",
            "SearchDocumentsResult",
        ):
            assert _load_symbol(self._TOOLS_MOD, symbol) is not None, symbol

    def test_system_prompt_uses_new_names(self) -> None:
        prompt = _load_symbol(
            "agentx.model.rag_v2.rag_v2_agent_service",
            "DEFAULT_RAG_V2_SYSTEM_PROMPT",
        )
        assert "search_documents" in prompt
        assert "rag_search" not in prompt, "prompt must not teach old names"
        assert "rag_ingest_status" not in prompt

    def test_no_old_tool_names_remain_in_rag_v2_src(self) -> None:
        """Totality pin: rg-equivalent over the v2 src trees."""
        from pathlib import Path

        root = Path(__file__).resolve().parents[3]
        offenders: list[str] = []
        for tree in (
            root / "src" / "agentx" / "model" / "rag_v2",
            root / "src" / "agentx" / "ui" / "screens" / "rag_v2",
        ):
            for path in tree.rglob("*.py"):
                text = path.read_text(encoding="utf-8")
                if "rag_search" in text or "rag_ingest_status" in text:
                    offenders.append(str(path))
        assert offenders == [], f"old tool names remain in: {offenders}"


# ── b13 — show_chat removal + ABC honesty ─────────────────────────────────────


class TestShowChatRemoved(TestCase):
    """The fake `[3] chat` mode is gone: ``show_chat`` leaves the v2 partner
    ABC + controller; the slash-command operations join the ABC (design_001
    §Interface + dead-mode cut)."""

    def test_partner_abc_has_no_show_chat(self) -> None:
        abc = _load_symbol("agentx.ui.interfaces", "IRagV2ViewPartner")
        assert not hasattr(abc, "show_chat"), (
            "IRagV2ViewPartner.show_chat must be removed (dead fake mode)"
        )

    def test_controller_has_no_show_chat(self) -> None:
        ctrl_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        assert not hasattr(ctrl_cls, "show_chat"), (
            "RagV2MainController.show_chat must be removed (dead fake mode)"
        )

    def test_slash_commands_declared_on_partner_abc(self) -> None:
        abc = _load_symbol("agentx.ui.interfaces", "IRagV2ViewPartner")
        for method in (
            "list_repositories",
            "use_repository",
            "create_repository_named",
            "ingest",
            "show_status",
            "reset_chat",
        ):
            assert callable(getattr(abc, method, None)), (
                f"IRagV2ViewPartner must declare {method} (ABC honesty)"
            )
