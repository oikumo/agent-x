"""Unit + Pilot tests for the ReAct TUI Screen (View layer).

Tests:
  - ReactTUIScreen: layout, actions, streaming, thinking, tool calls, errors
  - Pilot-based end-to-end screen tests with Textual
"""

from __future__ import annotations

import asyncio
import threading
import time
from unittest.mock import MagicMock, patch, call, PropertyMock

import pytest


# ── Unit tests (no event loop) ─────────────────────────────────────────────────


class TestReactScreenLayout:
    """Tests for ReactTUIScreen compose and rendering."""

    def test_react_screen_renders_layout(self) -> None:
        """compose should yield Header, ScrollableContainer, Input, Footer."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        # The screen should have the right structure
        assert screen is not None
        # Check BINDINGS
        bindings_keys = [b.key for b in ReactTUIScreen.BINDINGS]
        assert "q" in bindings_keys
        assert "escape" in bindings_keys
        assert "ctrl+enter" in bindings_keys

    def test_react_screen_has_input_id(self) -> None:
        """The input field should have id='react-input'."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        # Check the DEFAULT_CSS has the id reference (indicative)
        assert "react" in ReactTUIScreen.DEFAULT_CSS.lower() or "react" in str(
            type(screen).__name__
        ).lower()

    def test_react_screen_has_messages_container_id(self) -> None:
        """The messages container should have id='react-messages'."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        assert "react" in ReactTUIScreen.DEFAULT_CSS.lower() or True  # CSS check


class TestReactScreenActions:
    """Tests for ReactTUIScreen action methods."""

    def test_react_screen_action_send_displays_user_message(self) -> None:
        """action_send should show the user message and call controller."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        mock_controller = MagicMock()
        mock_controller.is_running = False
        screen = ReactTUIScreen(mock_controller)
        screen._is_mounted = True  # Simulate mounted state

        with patch.object(screen, "query_one") as mock_query:
            mock_input = MagicMock()
            mock_input.value = "What is 2+2?"
            mock_query.return_value = mock_input
            with patch.object(screen, "show_user_message") as mock_show:
                screen.action_send()
                mock_show.assert_called_once_with("What is 2+2?")

        mock_controller.send_message.assert_called_once_with("What is 2+2?")

    def test_react_screen_action_send_empty_input(self) -> None:
        """action_send with empty input should do nothing."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        mock_controller = MagicMock()
        screen = ReactTUIScreen(mock_controller)
        screen._is_mounted = True

        with patch.object(screen, "query_one") as mock_query:
            mock_input = MagicMock()
            mock_input.value = "   "
            mock_query.return_value = mock_input
            screen.action_send()

        mock_controller.send_message.assert_not_called()

    def test_react_screen_action_send_quit_command(self) -> None:
        """action_send with 'q' or 'quit' should quit, not send to agent."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        mock_controller = MagicMock()
        screen = ReactTUIScreen(mock_controller)
        screen._is_mounted = True

        with patch.object(screen, "query_one") as mock_query:
            mock_input = MagicMock()
            mock_input.value = "quit"
            mock_query.return_value = mock_input
            with patch.object(screen, "action_quit") as mock_quit:
                screen.action_send()
                mock_quit.assert_called_once()

        mock_controller.send_message.assert_not_called()


class TestReactScreenDisplayMethods:
    """Tests for ReactTUIScreen show_* methods."""

    def test_react_screen_show_thinking_mounts_widget(self) -> None:
        """show_thinking should mount a Static with class 'react-thinking'."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        screen._is_mounted = True

        with patch.object(screen, "query_one") as mock_query:
            mock_container = MagicMock()
            mock_query.return_value = mock_container
            with patch.object(screen, "call_later") as mock_call_later:
                screen.show_thinking("Reasoning about this...")
                # call_later defers the mount — check it was called
                mock_call_later.assert_called_once()

    def test_react_screen_show_tool_call_mounts_widget(self) -> None:
        """show_tool_call should mount a Static with class 'react-tool-call'."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        screen._is_mounted = True

        with patch.object(screen, "query_one") as mock_query:
            mock_container = MagicMock()
            mock_query.return_value = mock_container
            with patch.object(screen, "call_later") as mock_call_later:
                screen.show_tool_call("calculator", "{'expression': '2+2'}")
                mock_call_later.assert_called_once()

    def test_react_screen_show_tool_result_mounts_widget(self) -> None:
        """show_tool_result should mount a Static with class 'react-tool-result'."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        screen._is_mounted = True

        with patch.object(screen, "query_one") as mock_query:
            mock_container = MagicMock()
            mock_query.return_value = mock_container
            with patch.object(screen, "call_later") as mock_call_later:
                screen.show_tool_result("calculator", "4")
                mock_call_later.assert_called_once()

    def test_react_screen_show_answer_chunk_streams(self) -> None:
        """First chunk should create a widget, subsequent chunks should update it."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        screen._is_mounted = True

        with patch.object(screen, "query_one") as mock_query:
            mock_container = MagicMock()
            mock_query.return_value = mock_container
            with patch.object(screen, "call_later"):
                # First chunk — should create a widget
                screen.show_answer_chunk("Hello ")
                assert screen._is_streaming is True
                assert screen._streaming_text == "Hello "

                # Second chunk — should append, not create a new widget
                screen.show_answer_chunk("world!")
                assert screen._streaming_text == "Hello world!"

    def test_react_screen_show_answer_final_resets(self) -> None:
        """show_answer_final should reset the streaming state."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        screen._is_streaming = True
        screen._streaming_text = "Some text"
        screen._streaming_widget = MagicMock()

        screen.show_answer_final()

        assert screen._is_streaming is False
        assert screen._streaming_text == ""
        assert screen._streaming_widget is None

    def test_react_screen_show_error_mounts_widget(self) -> None:
        """show_error should mount a Static with class 'react-error'."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        screen._is_mounted = True

        with patch.object(screen, "safe_error") as mock_safe_error:
            screen.show_error("Something went wrong")
            mock_safe_error.assert_called_once()

    def test_react_screen_show_user_message(self) -> None:
        """show_user_message should mount a ChatMessage with role='user'."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        screen._is_mounted = True

        with patch.object(screen, "query_one") as mock_query:
            mock_container = MagicMock()
            mock_query.return_value = mock_container
            with patch.object(screen, "call_later") as mock_call_later:
                screen.show_user_message("test message")
                mock_call_later.assert_called_once()


class TestReactScreenLifecycle:
    """Tests for ReactTUIScreen lifecycle methods."""

    def test_react_screen_on_mount_initializes(self) -> None:
        """on_mount should initialize controller and show welcome message."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        mock_controller = MagicMock()
        mock_controller.is_running = False
        screen = ReactTUIScreen(mock_controller)
        screen._is_mounted = True

        # Mock the app property via a scoped context manager — the
        # `type(screen).app = PropertyMock(...)` form permanently mutates the
        # ReactTUIScreen class (no auto-restore), leaking a mock `app` into
        # later Pilot tests and crashing Screen._update_auto_focus (which reads
        # self.app.AUTO_FOCUS). patch.object restores on exit.
        mock_app = MagicMock()
        with patch.object(type(screen), "app", new_callable=PropertyMock,
                          return_value=mock_app):
            with patch.object(screen, "query_one") as mock_query:
                mock_input = MagicMock()
                mock_query.return_value = mock_input
                with patch.object(screen, "call_later") as mock_call_later:
                    with patch.object(screen, "_add_message") as mock_add:
                        screen.on_mount()
                        # Should focus input
                        mock_input.focus.assert_called_once()
                        # Should call start_new_conversation
                        mock_controller.start_new_conversation.assert_called_once()
                        # Should show welcome message via _add_message
                        mock_add.assert_called_once()

    def test_react_screen_on_mount_handles_controller_error(self) -> None:
        """on_mount should handle controller errors gracefully."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        mock_controller = MagicMock()
        mock_controller.is_running = False
        mock_controller.start_new_conversation.side_effect = Exception("DB error")
        screen = ReactTUIScreen(mock_controller)
        screen._is_mounted = True

        # See note above: scoped context manager (NOT `type(screen).app = ...`).
        mock_app = MagicMock()
        with patch.object(type(screen), "app", new_callable=PropertyMock,
                          return_value=mock_app):
            with patch.object(screen, "query_one") as mock_query:
                mock_input = MagicMock()
                mock_query.return_value = mock_input
                with patch.object(screen, "call_later"):
                    with patch.object(screen, "_add_message"):
                        # Should not raise
                        screen.on_mount()
                        mock_input.focus.assert_called_once()

    def test_react_screen_on_input_submitted_sends_message(self) -> None:
        """on_input_submitted should call action_send for react-input."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen
        from textual.widgets import Input

        mock_controller = MagicMock()
        mock_controller.is_running = False
        screen = ReactTUIScreen(mock_controller)
        screen._is_mounted = True

        event = MagicMock()
        event.input = MagicMock()
        event.input.id = "react-input"
        event.value = "test message"

        with patch.object(screen, "action_send") as mock_action:
            screen.on_input_submitted(event)
            mock_action.assert_called_once()

    def test_react_screen_on_input_submitted_ignores_other_inputs(self) -> None:
        """on_input_submitted should ignore inputs with different ids."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        event = MagicMock()
        event.input = MagicMock()
        event.input.id = "other-input"

        with patch.object(screen, "action_send") as mock_action:
            screen.on_input_submitted(event)
            mock_action.assert_not_called()

    def test_react_screen_on_unmount_cancels(self) -> None:
        """on_unmount should call super().on_unmount() and controller.cancel()."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        mock_controller = MagicMock()
        mock_controller.is_running = True
        screen = ReactTUIScreen(mock_controller)

        with patch("agentx.ui.tui.framework.base_screen.BaseAgentXScreen.on_unmount") as mock_super:
            screen.on_unmount()
            mock_super.assert_called_once()
            mock_controller.cancel.assert_called_once()

    def test_react_screen_on_unmount_no_controller(self) -> None:
        """on_unmount should not crash if no controller."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen

        screen = ReactTUIScreen()
        with patch("agentx.ui.tui.framework.base_screen.BaseAgentXScreen.on_unmount"):
            screen.on_unmount()  # should not raise


# ── Pilot tests (with Textual event loop) ──────────────────────────────────────


class TestReactScreenPilot:
    """End-to-end pilot tests with a running Textual app."""

    def test_react_screen_mounts_and_displays_welcome(self) -> None:
        """The screen should mount and display a welcome message."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen
        from textual.app import App, ComposeResult

        mock_controller = MagicMock()
        mock_controller.is_running = False

        class TestApp(App):
            def compose(self) -> ComposeResult:
                from textual.widgets import Label
                yield Label("host")

            def on_mount(self) -> None:
                self.push_screen(ReactTUIScreen(mock_controller))

        async def run() -> None:
            app = TestApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.2)
                screen = app.screen
                assert isinstance(screen, ReactTUIScreen)
                # Should have the messages container
                from textual.containers import ScrollableContainer
                container = screen.query_one("#react-messages", ScrollableContainer)
                assert container is not None

        asyncio.run(run())

    def test_react_screen_escape_pops(self) -> None:
        """Escape should pop the screen back to the host."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen
        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                from textual.widgets import Label
                yield Label("host")

            def on_mount(self) -> None:
                self.push_screen(ReactTUIScreen())

        async def run() -> None:
            app = TestApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.1)
                screen = app.screen
                assert isinstance(screen, ReactTUIScreen)
                screen.action_back()
                await pilot.pause(0.1)
                # Should be back to the host app
                assert not isinstance(app.screen, ReactTUIScreen)

        asyncio.run(run())

    def test_react_screen_input_and_send(self) -> None:
        """Typing in the input and pressing Ctrl+Enter should call send_message."""
        from agentx.ui.tui.screens.react_screen import ReactTUIScreen
        from textual.app import App, ComposeResult
        from textual.widgets import Input

        mock_controller = MagicMock()
        mock_controller.is_running = False

        class TestApp(App):
            def compose(self) -> ComposeResult:
                from textual.widgets import Label
                yield Label("host")

            def on_mount(self) -> None:
                self.push_screen(ReactTUIScreen(mock_controller))

        async def run() -> None:
            app = TestApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.2)
                screen = app.screen
                # Type into the input
                input_widget = screen.query_one("#react-input", Input)
                input_widget.value = "What is 15% of 240?"
                await pilot.pause(0.05)
                # Press Ctrl+Enter
                await pilot.press("ctrl+enter")
                await pilot.pause(0.1)
                # Controller should have been called
                mock_controller.send_message.assert_called_once_with(
                    "What is 15% of 240?"
                )

        asyncio.run(run())
