"""Chat TUI Screen — Simple, clean chat interface.

Refactored (feature_012.tui_framework) to inherit from
:class:`BaseAgentXScreen` and import :class:`ChatMessage`
from ``agentx.ui.tui.framework.widgets``.

Simplified (feature_018):
- Removed conversation sidebar and related complexity
- Removed timestamps from messages
- Clear visual separation between user and agent messages
- Minimal key bindings for focused chat experience
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.widgets import Footer, Header, Input, Static

from agentx.ui.tui.framework import BaseAgentXScreen, ChatMessage

if TYPE_CHECKING:
    from agentx.ui.interfaces import IChatViewPartner


__all__ = ["ChatTUIScreen", "ChatMessage"]


class ChatTUIScreen(BaseAgentXScreen):
    """Simple chat screen with message history and input.
    
    Features:
    - Clean message display with clear user/agent separation
    - Input field for user messages
    - Streaming response from LLM (non-blocking)
    - Minimal, focused UI
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("escape", "back", "Back", show=True),
        Binding("ctrl+enter", "send", "Send", show=True),
    ]

    DEFAULT_CSS = """
    ChatTUIScreen {
        layout: vertical;
    }

    ChatTUIScreen #chat-container {
        height: 1fr;
        padding: 1;
    }

    ChatTUIScreen #main-chat-area {
        width: 1fr;
        height: 1fr;
        layout: vertical;
    }

    ChatTUIScreen #messages {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    ChatTUIScreen #input-section {
        height: auto;
        dock: bottom;
    }

    ChatTUIScreen #input-section Input {
        width: 100%;
    }
    """

    def __init__(self, controller: "IChatViewPartner | None" = None) -> None:
        """Initialize chat screen.

        Args:
            controller: Optional IChatViewPartner for message processing
        """
        super().__init__(controller)
        self.history: list = []
        self._streaming_message: str = ""
        self._is_streaming: bool = False
        self._streaming_widget: ChatMessage | None = None
        # LLM attribute — initialized to None; actual LLM creation is deferred
        # to on_mount() to avoid blocking screen construction (provider
        # factories may validate API keys / network). The controller also
        # holds its own LLM; this attribute is for fallback / inspection.
        self.llm = None

    # action_quit / action_back are inherited from BaseAgentXScreen.

    def compose(self) -> ComposeResult:
        """Compose chat screen layout."""
        yield Header(show_clock=True)

        with Container(id="chat-container"):
            # Main chat area (full width, no sidebar)
            with Vertical(id="main-chat-area"):
                yield ScrollableContainer(id="messages")

                with Horizontal(id="input-section"):
                    yield Input(
                        placeholder="Type your message... (Ctrl+Enter to send, Esc to go back)",
                        id="chat-input",
                    )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Initialize controller if provided — start a new conversation so
        # that (a) history is initialised with the system prompt and
        # (b) DB persistence is active (start_new_conversation sets
        # current_conversation_id, which _save_messages requires).
        if self._controller:
            try:
                self._controller.start_new_conversation()
            except Exception:
                # Fall back to in-memory-only history if DB is unavailable.
                self._controller.start_interactive_streaming(
                    system_prompt="You are a helpful assistant."
                )

        # Focus input
        try:
            self.query_one("#chat-input", Input).focus()
        except Exception:
            pass

    def _add_message(self, message: str, role: str = "user") -> None:
        """Add a message to the chat display.

        Args:
            message: Message content
            role: 'user' or 'assistant'
        """
        try:
            messages_container = self.query_one("#messages", ScrollableContainer)
            chat_message = ChatMessage(message, role)
            messages_container.mount(chat_message)

            # Scroll to bottom
            self.call_later(messages_container.scroll_end, animate=False)
        except Exception:
            pass

    # View methods for IChatView interface (used by controller)
    def show_initial_message(self) -> None:
        """Show welcome message."""
        self._add_message("Welcome to AgentX Chat! Ask me anything.", "assistant")

    def show_message(self, message: str, role: str = "assistant") -> None:
        """Show a complete message."""
        self._add_message(message, role)

    def show_partial_message(self, message: str) -> None:
        """Show partial (streaming) message."""
        try:
            messages_container = self.query_one("#messages", ScrollableContainer)

            if not self._is_streaming:
                # Start new streaming message
                self._is_streaming = True
                self._streaming_message = message
                chat_message = ChatMessage(message, "assistant")
                messages_container.mount(chat_message)
                self._streaming_widget = chat_message
            else:
                # Append to existing streaming message
                self._streaming_message += message
                if self._streaming_widget:
                    self._streaming_widget.update(self._streaming_message)
                else:
                    # Widget lost (shouldn't happen), recreate
                    self._is_streaming = False
                    return self.show_partial_message(message)

            # Scroll to bottom
            self.call_later(messages_container.scroll_end, animate=False)
        except Exception as e:
            # Log error for debugging - don't silently fail
            import logging
            logging.getLogger(__name__).error(f"show_partial_message failed: {e}")
            raise

    def show_stream_message(self, message: str) -> None:
        """Stream message with typing effect (alias for show_partial_message)."""
        self.show_partial_message(message)

    def show_message_chat_error(self, message: str | None = None) -> None:
        """Show chat error.

        Args:
            message: When supplied, surfaced verbatim in the chat feed so the
                user sees *which* provider failed and *what* credential to
                check (e.g. ``"[chat error] NVIDIA NIM: [403] Forbidden —
                check NVIDIA_API_KEY"``).  ``None`` falls back to a generic
                banner for backward-compatible no-arg callers.
        """
        text = message if message else "Error: Failed to get response from assistant."
        self._add_message(text, "assistant")

    def _on_streaming_complete(self) -> None:
        """Called when streaming is complete."""
        self._is_streaming = False
        self._streaming_message = ""
        self._streaming_widget = None

    def action_send(self) -> None:
        """Send current message."""
        try:
            input_widget = self.query_one("#chat-input", Input)
            if input_widget.value.strip():
                # Call handler directly
                event = type('InputSubmitted', (), {'value': input_widget.value, 'input': input_widget})()
                self.on_input_submitted(event)  # type: ignore[arg-type]
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[override]
        """Handle message submission."""
        if event.input.id != "chat-input":
            return

        message = event.value.strip()

        if not message:
            return

        # Clear input
        event.input.value = ""

        # Check for quit command
        if message.lower() in ("quit", "exit"):
            self.action_quit()
            return

        # Add user message to UI
        self._add_message(message, "user")

        # Process through controller if available
        if self._controller:
            try:
                # Run LLM processing on background thread to avoid UI freeze
                self._run_llm_async(message)
            except Exception as e:
                self._add_message(f"Error: {str(e)}", "assistant")
        else:
            # Fallback: show placeholder
            self._add_message("(No controller connected)", "assistant")

    def _run_llm_async(self, user_message: str) -> None:
        """Run the LLM call on a background thread with streaming via call_from_thread.

        Uses the controller's accumulated ``history`` list so the LLM receives
        the full conversation context (system prompt + all prior human/AI turns).

        This avoids blocking the UI thread while preserving streaming UX.
        """
        # Reset streaming state — _is_streaming must be False so the first
        # call to show_partial_message creates the widget.
        self._is_streaming = False
        self._streaming_message = ""
        self._streaming_widget = None

        def worker() -> None:
            """Background worker: calls LLM and streams chunks via call_from_thread."""
            try:
                from langchain_core.messages import HumanMessage, AIMessage
                from agentx.model.ai.service import AIService

                llm = AIService().get_current_llm()

                # Use the controller's accumulated history — this preserves
                # conversation context across turns (system prompt + all prior
                # human/AI messages).  The controller's history was initialised
                # in on_mount() via start_interactive_streaming().
                history = self._controller.history
                history.append(HumanMessage(content=user_message))

                full_response_parts = []

                for chunk in llm.stream(history):
                    content = self._extract_chunk_content(chunk)
                    if content:
                        full_response_parts.append(content)
                        # Stream to UI via app.call_from_thread (safe from any thread).
                        # NOTE: Screen does NOT have call_from_thread — only App does.
                        # Using self.call_from_thread raises AttributeError, which was
                        # silently swallowed by the except block (which also called
                        # self.call_from_thread), so NO assistant message ever appeared.
                        self.app.call_from_thread(self.show_partial_message, content)

                # Append the assistant response to the controller's history so
                # it is available for the next turn.
                full_response = "".join(full_response_parts)
                history.append(AIMessage(content=full_response))

                # Persist if conversation is active
                if self._controller and hasattr(self._controller, '_save_messages'):
                    # We need to save messages via controller
                    self.app.call_from_thread(self._save_via_controller, user_message, full_response)

            except Exception as e:
                # On error, remove the HumanMessage we appended so the
                # controller's history stays consistent (mirrors the
                # controller's own process_user_message error handling).
                try:
                    self._controller.history.pop()
                except (IndexError, AttributeError):
                    pass
                # Report error on UI thread
                self.app.call_from_thread(self._add_message, f"Error: {str(e)}", "assistant")
            finally:
                # Reset streaming state on UI thread
                self.app.call_from_thread(self._on_streaming_complete)

        # Start background thread
        thread = threading.Thread(target=worker, daemon=True, name="AgentX-Chat-LLM")
        thread.start()

    def _extract_chunk_content(self, chunk) -> str:
        """Extract text content from a LangChain chunk (mirrors controller logic)."""
        if hasattr(chunk, "text"):
            return str(chunk.text)
        if chunk.content is None:
            return ""
        if isinstance(chunk.content, list):
            return " ".join(str(item) for item in chunk.content if item is not None)
        return str(chunk.content)

    def _save_via_controller(self, user_message: str, assistant_response: str) -> None:
        """Call controller's save method if available."""
        if self._controller and hasattr(self._controller, '_save_messages'):
            self._controller._save_messages(user_message, assistant_response)