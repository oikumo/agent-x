"""feature_024.no_tui_full_features — chat error surfacing (bug_fix).

Regression guard for the "swallowed NVIDIA 403" UX bug:

    ChatController.process_user_message used to catch every LLM exception,
    ``print(f"Error: {e}")`` to raw stdout, and continue the REPL with no UI
    feedback.  A dead ``NVIDIA_API_KEY`` therefore looked like "chat silently
    fails" in console mode — the user saw one bare line and could not tell it
    was an auth failure on the NVIDIA provider.

The fix routes the exception through ``view.show_message_chat_error()`` with a
message that carries the **selected provider name** (so the user knows which
provider blew up) and an actionable key hint.

Behaviors:

  1. ``process_user_message`` calls ``view.show_message_chat_error(message)``
     on LLM exception, where ``message`` contains the provider name AND a
     hint about the relevant env var / config.
  2. Existing pre-error behaviors preserved:
     - the failed ``HumanMessage`` is popped from ``self.history``.
     - the REPL continues (returns ``True``).
  3. When ``view is None`` the controller must still not crash (it falls
     back to printing the error).
"""

from __future__ import annotations

from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from langchain_core.messages import SystemMessage


def _make_controller_with_raising_llm(provider_name: str = "NVIDIA NIM") -> Any:
    """Build a ChatController whose ``llm.stream`` raises, with a stub view.

    Construction bypasses the real ``AIService`` (no network / env), so the
    RED/GREEN cycle is hermetic.  The module-level ``AIService`` attribute
    inside ``chat_controller`` is patched so the fix can resolve the provider
    name without hitting the real registry / config file.
    """
    from agentx.ui.screens.chat.chat_controller import ChatController

    ctl = ChatController.__new__(ChatController)
    ctl.view = MagicMock()
    ctl.history = [SystemMessage(content="You are a helpful assistant.")]
    ctl.history_repo = MagicMock()
    ctl.current_conversation_id = None

    raising_llm = MagicMock()
    raising_llm.stream.side_effect = Exception("[403] Forbidden\nAuthorization failed")
    ctl.llm = raising_llm

    fake_ai = MagicMock()
    fake_ai.get_current_provider_info().name = provider_name
    fake_ai.get_current_provider_info().id = "nvidia"
    fake_ai.get_current_provider_id.return_value = "nvidia"
    import agentx.ui.screens.chat.chat_controller as mod

    mod.AIService = lambda: fake_ai  # type: ignore[assignment]
    return ctl


class TestChatErrorSurfacing(TestCase):
    """LLM exceptions during streaming must surface through the view, not stdout."""

    def test_view_show_message_chat_error_called_with_provider_name_and_hint(self) -> None:
        ctl = _make_controller_with_raising_llm(provider_name="NVIDIA NIM")
        ok = ctl.process_user_message("hi")

        # The view's chat-error hook must be invoked exactly once.
        ctl.view.show_message_chat_error.assert_called_once()
        msg = ctl.view.show_message_chat_error.call_args.args[0]
        # Provider identity surfaces so the user knows which provider failed.
        self.assertIn("NVIDIA NIM", msg)
        # Actionable hint about the API key (env var name appears).
        self.assertIn("NVIDIA_API_KEY", msg)
        # The original error text is preserved for diagnosis.
        self.assertIn("403", msg)

    def test_failed_human_message_popped_from_history(self) -> None:
        ctl = _make_controller_with_raising_llm()
        history_len_before = len(ctl.history)
        ctl.process_user_message("hi")
        # The HumanMessage added for "hi" must be popped on failure (existing
        # behavior — preserves history integrity for retry).
        self.assertEqual(len(ctl.history), history_len_before)

    def test_returns_true_so_repl_continues(self) -> None:
        ctl = _make_controller_with_raising_llm()
        self.assertTrue(ctl.process_user_message("hi"))

    def test_no_view_does_not_crash(self) -> None:
        """With ``view is None`` the controller must fall back to print, not raise."""
        ctl = _make_controller_with_raising_llm()
        ctl.view = None  # no view attached — must degrade to stdout
        # Should not raise.
        ok = ctl.process_user_message("hi")
        self.assertTrue(ok)
