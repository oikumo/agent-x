from __future__ import annotations
from typing import TYPE_CHECKING
from agentx.ui.common.ui_console import UIConsole

if TYPE_CHECKING:
    from agentx.ui.screens.rag.rag_chat_controller import RagChatController

class RagChatView:
    def __init__(self, controller: RagChatController):
        self.controller = controller
        self.console = UIConsole("(rag/chat)")

    def show(self):
        self.show_initial_message()

        while True:
            user_input = self.console.capture_input()
            if user_input and user_input == "quit":
                self.controller.close()
                return
            if not user_input: return
            if not self.controller.process_user_message(user_input): return

    def show_partial_text(self, message: str):
        self.console.partial_info(message)

    def show_initial_message(self):
        self.console.info("""Starting interactive chat (type 'quit' or 'exit' to end):""")

    def show_message(self, message):
        self.console.info(message)

    def show_message_chat_error(self, message: str | None = None):
        if message:
            self.console.error(message)
        else:
            self.console.error("chat error")

    def show_stream_message(self, message: str):
        self.console.info(message)