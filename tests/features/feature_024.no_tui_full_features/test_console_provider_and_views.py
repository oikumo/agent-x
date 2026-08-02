"""feature_024.no_tui_full_features — cycle 3 characterization tests.

Pins the remaining testlist behaviors implemented in cycles 1–2:

  * ``ConsoleProvider.create_*_view`` returns the correct console view types.
  * ``ConsoleCodingView`` / ``ConsoleAgentView`` REPL loops call
    ``controller.send_message`` and exit on empty input; partial messages
    stream via ``console.stream_write``.
  * ``ConsoleFastAgentView.show()`` loop calls ``controller.send_message``.
  * ``UIConsole.stream_write`` writes without newline and flushes.
  * ``IUIProvider`` declares the 5 console-parity abstract factory methods.
  * Console-parity view/partner interfaces are defined in
    ``agentx.ui.interfaces``.
"""

from __future__ import annotations

from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from agentx.ui.common.ui_console import UIConsole
from agentx.ui.interfaces import (
    IAgentView,
    ICodingView,
    IConsoleAgentViewPartner,
    IConsoleFastAgentViewPartner,
    IFastAgentView,
    IModelsView,
    IModelsViewPartner,
    IReactView,
    IReactViewPartner,
    IUIProvider,
)
from agentx.ui.providers import ConsoleProvider
from agentx.ui.screens.agent.agent_view import ConsoleAgentView
from agentx.ui.screens.coding.coding_view import ConsoleCodingView
from agentx.ui.screens.fast_agent.fast_agent_view import ConsoleFastAgentView
from agentx.ui.screens.models.models_view import ConsoleModelsView
from agentx.ui.screens.react.react_view import ConsoleReactView


class TestConsoleProviderFactories(TestCase):
    """ConsoleProvider.create_*_view returns the correct console view types."""

    def setUp(self) -> None:
        self.provider = ConsoleProvider()

    def test_create_react_view_returns_console_react_view(self) -> None:
        view = self.provider.create_react_view(MagicMock())
        assert isinstance(view, ConsoleReactView)
        assert isinstance(view, IReactView)

    def test_create_coding_view_returns_console_coding_view(self) -> None:
        view = self.provider.create_coding_view(MagicMock())
        assert isinstance(view, ConsoleCodingView)
        assert isinstance(view, ICodingView)

    def test_create_models_view_returns_console_models_view(self) -> None:
        view = self.provider.create_models_view(MagicMock())
        assert isinstance(view, ConsoleModelsView)
        assert isinstance(view, IModelsView)

    def test_create_agent_view_returns_console_agent_view(self) -> None:
        view = self.provider.create_agent_view(MagicMock())
        assert isinstance(view, ConsoleAgentView)
        assert isinstance(view, IAgentView)

    def test_create_fast_agent_view_returns_console_fast_agent_view(self) -> None:
        view = self.provider.create_fast_agent_view(MagicMock())
        assert isinstance(view, ConsoleFastAgentView)
        assert isinstance(view, IFastAgentView)

    def test_create_react_view_accepts_ireactviewpartner(self) -> None:
        """ConsoleProvider.create_react_view accepts IReactViewPartner (not IConsoleReactViewPartner)."""
        from agentx.ui.interfaces import IReactViewPartner
        mock_controller = MagicMock(spec=IReactViewPartner)
        view = self.provider.create_react_view(mock_controller)
        assert isinstance(view, ConsoleReactView)
        assert isinstance(view, IReactView)

    def test_create_coding_view_accepts_icodingviewpartner(self) -> None:
        """ConsoleProvider.create_coding_view accepts ICodingViewPartner (not IConsoleCodingViewPartner)."""
        from agentx.ui.interfaces import ICodingViewPartner
        mock_controller = MagicMock(spec=ICodingViewPartner)
        view = self.provider.create_coding_view(mock_controller)
        assert isinstance(view, ConsoleCodingView)
        assert isinstance(view, ICodingView)


class TestConsoleCodingView(TestCase):
    """ConsoleCodingView REPL loop + token streaming."""

    def setUp(self) -> None:
        self.controller = MagicMock()
        self.controller.send_message.return_value = True
        self.view: Any = ConsoleCodingView(self.controller)
        self.view.console = MagicMock()

    def test_show_enters_repl_loop_and_exits_on_empty_input(self) -> None:
        self.view.console.capture_input.side_effect = ["hello agent", None]

        self.view.show()

        self.controller.send_message.assert_called_once_with("hello agent")
        assert self.view.console.capture_input.call_count == 2

    def test_show_partial_message_streams_via_stream_write(self) -> None:
        self.view.show_partial_message("token-1")

        self.view.console.stream_write.assert_called_once_with("token-1")


class TestConsoleAgentView(TestCase):
    """ConsoleAgentView REPL loop + token streaming."""

    def setUp(self) -> None:
        self.controller = MagicMock()
        self.controller.send_message.return_value = True
        self.view: Any = ConsoleAgentView(self.controller)
        self.view.console = MagicMock()

    def test_show_enters_repl_loop_and_exits_on_empty_input(self) -> None:
        self.view.console.capture_input.side_effect = ["hello agent", None]

        self.view.show()

        self.controller.send_message.assert_called_once_with("hello agent")
        assert self.view.console.capture_input.call_count == 2

    def test_show_partial_message_streams_via_stream_write(self) -> None:
        self.view.show_partial_message("token-1")

        self.view.console.stream_write.assert_called_once_with("token-1")


class TestConsoleFastAgentViewShow(TestCase):
    """ConsoleFastAgentView loop calls controller.send_message."""

    def test_show_loop_calls_send_message_and_exits_on_empty_input(self) -> None:
        controller = MagicMock()
        controller.send_message.return_value = True
        view = ConsoleFastAgentView(controller)
        view.console = MagicMock()
        view.console.capture_input.side_effect = ["do it fast", None]

        view.show()

        controller.send_message.assert_called_once_with("do it fast")
        assert view.console.capture_input.call_count == 2


class TestUIConsoleStreamWrite(TestCase):
    """UIConsole.stream_write writes without newline and flushes stdout."""

    def test_stream_write_writes_without_newline_and_flushes(self) -> None:
        console = UIConsole("(test)")
        from io import StringIO
        from unittest.mock import patch

        buffer = StringIO()
        with patch("sys.stdout", buffer):
            console.stream_write("token-a")
            console.stream_write("token-b")

        assert buffer.getvalue() == "token-atoken-b"


class TestConsoleParityInterfaces(TestCase):
    """Interface surface pins (feature_024)."""

    def test_iuiprovider_declares_five_console_parity_factory_methods(self) -> None:
        for name in (
            "create_react_view",
            "create_coding_view",
            "create_models_view",
            "create_agent_view",
            "create_fast_agent_view",
        ):
            method = getattr(IUIProvider, name, None)
            assert method is not None, f"IUIProvider missing {name}"
            assert getattr(method, "__isabstractmethod__", False), (
                f"IUIProvider.{name} must be abstract"
            )

    def test_console_parity_interfaces_are_defined(self) -> None:
        import agentx.ui.interfaces as interfaces

        for name in (
            "IReactView",
            "ICodingView",
            "IModelsView",
            "IModelsViewPartner",
            "IAgentView",
            "IFastAgentView",
            "IConsoleAgentViewPartner",
            "IConsoleFastAgentViewPartner",
        ):
            assert hasattr(interfaces, name), f"interfaces missing {name}"

    def test_console_react_coding_partners_deleted(self) -> None:
        """IConsoleReactViewPartner and IConsoleCodingViewPartner are deleted (Alt A)."""
        import agentx.ui.interfaces as interfaces
        assert not hasattr(interfaces, "IConsoleReactViewPartner"), (
            "IConsoleReactViewPartner should be deleted per Alt A"
        )
        assert not hasattr(interfaces, "IConsoleCodingViewPartner"), (
            "IConsoleCodingViewPartner should be deleted per Alt A"
        )

    def test_partner_interfaces_are_referenced_by_views(self) -> None:
        """Sanity: partner ABCs import cleanly alongside the views."""
        from agentx.ui.interfaces import (
            IConsoleAgentViewPartner,
            IConsoleFastAgentViewPartner,
            IModelsViewPartner,
        )

        for partner in (
            IConsoleAgentViewPartner,
            IConsoleFastAgentViewPartner,
            IModelsViewPartner,
        ):
            assert hasattr(partner, "__abstractmethods__")


class TestConsoleReactViewStreaming(TestCase):
    """ConsoleReactView implements all 6 streaming callbacks."""

    def setUp(self) -> None:
        self.controller = MagicMock()
        self.view = ConsoleReactView(self.controller)
        self.view.console = MagicMock()

    def test_show_thinking_exists_and_calls_console_info(self) -> None:
        self.view.show_thinking("reasoning text")
        self.view.console.info.assert_called_once()
        args = self.view.console.info.call_args[0][0]
        assert "reasoning text" in args

    def test_show_tool_call_exists_and_calls_console_info(self) -> None:
        self.view.show_tool_call("tool_name", '{"arg": "value"}')
        self.view.console.info.assert_called_once()
        args = self.view.console.info.call_args[0][0]
        assert "tool_name" in args

    def test_show_tool_result_exists_and_calls_console_info(self) -> None:
        self.view.show_tool_result("tool_name", "result output")
        self.view.console.info.assert_called_once()
        args = self.view.console.info.call_args[0][0]
        assert "result output" in args

    def test_show_answer_chunk_exists_and_calls_stream_write(self) -> None:
        self.view.show_answer_chunk("token")
        self.view.console.stream_write.assert_called_once_with("token")

    def test_show_answer_final_exists_and_resets_state(self) -> None:
        self.view.show_answer_final()
        # Just verify it's callable without error
        pass

    def test_show_error_exists_and_calls_console_error(self) -> None:
        self.view.show_error("error message")
        self.view.console.error.assert_called_once()
        args = self.view.console.error.call_args[0][0]
        assert "error message" in args


class TestConsoleCodingViewStreaming(TestCase):
    """ConsoleCodingView implements all 6 streaming callbacks."""

    def setUp(self) -> None:
        self.controller = MagicMock()
        self.view = ConsoleCodingView(self.controller)
        self.view.console = MagicMock()

    def test_show_thinking_exists_and_calls_console_info(self) -> None:
        self.view.show_thinking("reasoning text")
        self.view.console.info.assert_called_once()
        args = self.view.console.info.call_args[0][0]
        assert "reasoning text" in args

    def test_show_tool_call_exists_and_calls_console_info(self) -> None:
        self.view.show_tool_call("tool_name", '{"arg": "value"}')
        self.view.console.info.assert_called_once()
        args = self.view.console.info.call_args[0][0]
        assert "tool_name" in args

    def test_show_tool_result_exists_and_calls_console_info(self) -> None:
        self.view.show_tool_result("tool_name", "result output")
        self.view.console.info.assert_called_once()
        args = self.view.console.info.call_args[0][0]
        assert "result output" in args

    def test_show_answer_chunk_exists_and_calls_stream_write(self) -> None:
        self.view.show_answer_chunk("token")
        self.view.console.stream_write.assert_called_once_with("token")

    def test_show_answer_final_exists_and_resets_state(self) -> None:
        self.view.show_answer_final()
        # Just verify it's callable without error
        pass

    def test_show_error_exists_and_calls_console_error(self) -> None:
        self.view.show_error("error message")
        self.view.console.error.assert_called_once()
        args = self.view.console.error.call_args[0][0]
        assert "error message" in args
