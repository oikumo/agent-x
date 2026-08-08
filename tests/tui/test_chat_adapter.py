"""TUIChatAdapter (chat_adapter.py) — full mock-based unit tests.

Covers:
  - Construction and initial state
  - ``show()`` — currently a placeholder (no-op)
  - ``show_initial_message`` — delegates to screen.show_initial_message()
  - ``show_message`` — delegates to screen.show_message()
  - ``show_partial_message`` — delegates to screen.show_partial_message()
  - ``show_stream_message`` — delegates to screen.show_stream_message()
  - ``show_message_chat_error`` — delegates to screen.show_message_chat_error()
  - IChatView ABC compliance
  - Edge cases: None screen, None controller
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentx.ui.interfaces import IChatView
from agentx.ui.tui.adapters.chat_adapter import TUIChatAdapter


# ---------------------------------------------------------------------------
# IChatView ABC compliance
# ---------------------------------------------------------------------------

class TestIChatViewABC:
    """Verify IChatView cannot be instantiated."""

    def test_interface_is_abstract(self):
        with pytest.raises(TypeError, match="show"):
            IChatView()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestTUIChatAdapterConstruction:
    """Verify clean initial state."""

    def test_construction_stores_controller_and_none_screen(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        assert adapter._controller is mock_chat_controller
        assert adapter._screen is None

    def test_implements_ichatview(self, mock_chat_controller):
        """Concrete check: every abstract method from IChatView is present."""
        from agentx.ui.interfaces import IChatView

        for method in ("show", "show_initial_message", "show_message",
                       "show_partial_message", "show_stream_message",
                       "show_message_chat_error"):
            assert hasattr(TUIChatAdapter, method), f"Missing {method}"
            assert callable(getattr(TUIChatAdapter, method)), f"{method} not callable"

    def test_accepts_none_controller(self):
        """Should accept None (duck typing)."""
        adapter = TUIChatAdapter(None)  # type: ignore[arg-type]
        assert adapter._controller is None
        assert adapter._screen is None

    def test_set_screen_stores_screen(self, mock_chat_controller):
        """set_screen should store the screen reference."""
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        assert adapter._screen is mock_screen


# ---------------------------------------------------------------------------
# show() — placeholder
# ---------------------------------------------------------------------------

class TestTUIChatAdapterShow:
    """show() is currently a no-op placeholder."""

    def test_show_is_noop(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        result = adapter.show()
        assert result is None

    def test_show_with_none_controller(self):
        adapter = TUIChatAdapter(None)  # type: ignore[arg-type]
        result = adapter.show()
        assert result is None


# ---------------------------------------------------------------------------
# show_initial_message — delegates to screen.show_initial_message()
# ---------------------------------------------------------------------------

class TestTUIChatAdapterInitialMessage:
    """show_initial_message delegates to screen.show_initial_message()."""

    def test_show_initial_message_delegates_to_screen(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_initial_message()
        
        mock_screen.show_initial_message.assert_called_once()

    def test_show_initial_message_no_screen_does_not_raise(self, mock_chat_controller):
        """Should not raise when no screen is set."""
        adapter = TUIChatAdapter(mock_chat_controller)
        adapter.show_initial_message()  # Should not raise


# ---------------------------------------------------------------------------
# show_message — delegates to screen.show_message()
# ---------------------------------------------------------------------------

class TestTUIChatAdapterMessage:
    """show_message delegates to screen.show_message()."""

    def test_show_message_delegates_to_screen(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_message("Hello world")
        
        mock_screen.show_message.assert_called_once_with("Hello world", "assistant")

    def test_show_message_empty_string(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_message("")  # should not raise
        mock_screen.show_message.assert_called_once_with("", "assistant")

    def test_show_message_unicode(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_message("🎉 Unicode ✓")
        mock_screen.show_message.assert_called_once_with("🎉 Unicode ✓", "assistant")

    def test_show_message_multiple_calls(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_message("first")
        adapter.show_message("second")
        
        assert mock_screen.show_message.call_count == 2
        mock_screen.show_message.assert_any_call("first", "assistant")
        mock_screen.show_message.assert_any_call("second", "assistant")


# ---------------------------------------------------------------------------
# show_partial_message — delegates to screen.show_partial_message()
# ---------------------------------------------------------------------------

class TestTUIChatAdapterPartialMessage:
    """show_partial_message delegates to screen.show_partial_message()."""

    def test_partial_message_delegates_to_screen(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_partial_message("streaming")
        
        mock_screen.show_partial_message.assert_called_once_with("streaming")

    def test_partial_message_no_screen_does_not_raise(self, mock_chat_controller):
        """Should not raise when no screen is set."""
        adapter = TUIChatAdapter(mock_chat_controller)
        adapter.show_partial_message("streaming")  # Should not raise

    def test_partial_message_multiple_calls(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_partial_message("first")
        adapter.show_partial_message("second")
        
        assert mock_screen.show_partial_message.call_count == 2

    def test_partial_message_unicode(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_partial_message("流")
        mock_screen.show_partial_message.assert_called_once_with("流")


# ---------------------------------------------------------------------------
# show_stream_message — delegates to screen.show_stream_message()
# ---------------------------------------------------------------------------

class TestTUIChatAdapterStreamMessage:
    """show_stream_message delegates to screen.show_stream_message()."""

    def test_stream_message_delegates_to_screen(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_stream_message("stream")
        
        mock_screen.show_stream_message.assert_called_once_with("stream")

    def test_stream_message_no_screen_does_not_raise(self, mock_chat_controller):
        """Should not raise when no screen is set."""
        adapter = TUIChatAdapter(mock_chat_controller)
        adapter.show_stream_message("data")  # Should not raise


# ---------------------------------------------------------------------------
# show_message_chat_error — delegates to screen.show_message_chat_error()
# ---------------------------------------------------------------------------

class TestTUIChatAdapterError:
    """show_message_chat_error delegates to screen.show_message_chat_error()."""

    def test_show_message_chat_error_delegates_to_screen(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_message_chat_error()
        
        mock_screen.show_message_chat_error.assert_called_once()

    def test_show_message_chat_error_no_screen_does_not_raise(self, mock_chat_controller):
        """Should not raise when no screen is set."""
        adapter = TUIChatAdapter(mock_chat_controller)
        adapter.show_message_chat_error()  # Should not raise

    def test_show_message_chat_error_ignores_args(self, mock_chat_controller):
        """The method accepts the optional ``message`` arg (feature_024 chat
        error surfacing: the controller now passes an actionable provider/credential
        text; a no-arg call forwards ``None``, which the screen resolves to its
        own generic banner)."""
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)

        adapter.show_message_chat_error()  # should not raise TypeError
        mock_screen.show_message_chat_error.assert_called_once_with(None)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestTUIChatAdapterEdgeCases:
    """Boundary conditions for all message types."""

    def test_mixed_message_types(self, mock_chat_controller):
        """All message types can be called in sequence without errors."""
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_initial_message()
        adapter.show_message("msg")
        adapter.show_partial_message("partial")
        adapter.show_stream_message("stream")
        adapter.show_message_chat_error()
        
        mock_screen.show_initial_message.assert_called_once()
        mock_screen.show_message.assert_called_once_with("msg", "assistant")
        mock_screen.show_partial_message.assert_called_once_with("partial")
        mock_screen.show_stream_message.assert_called_once_with("stream")
        mock_screen.show_message_chat_error.assert_called_once()

    def test_very_long_message(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        long_msg = "x" * 10000
        adapter.show_message(long_msg)
        
        mock_screen.show_message.assert_called_once_with(long_msg, "assistant")

    def test_message_with_newlines(self, mock_chat_controller):
        adapter = TUIChatAdapter(mock_chat_controller)
        mock_screen = MagicMock()
        adapter.set_screen(mock_screen)
        
        adapter.show_message("line1\nline2\nline3")
        
        mock_screen.show_message.assert_called_once_with("line1\nline2\nline3", "assistant")