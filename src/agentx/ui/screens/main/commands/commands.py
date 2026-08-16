from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentx.ui.screens.main.main_controller import MainController

import os

from agentx.ui.screens.main.commands.commands_base import Command

from agentx.utils.utils import clear_console, safe_int
from agentx.utils.constants import APP_VERSION


class QuitCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Exit Agent-X")
        self.controller = controller

    def run(self, arguments: list[str]):
        self.controller.print_message("QUIT COMMAND")
        self.controller.close()


class ClearCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Clear the output screen")
        self.controller = controller

    def run(self, arguments: list[str]):
        clear_console()

class HistoryCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Show commands history")
        self.controller = controller

    def run(self, arguments: list[str]):
        for command in self.controller.commands_history()[:-1]:
            self.controller.print_message(f"    {command}")

class HelpCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Show available commands")
        self.controller = controller

    def run(self, arguments: list[str]):
        for command in self.controller.get_commands():
            self.controller.print_message(f"{command.key} - {command.description}")


class RagShowCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Open RAG")
        self.controller = controller

    def run(self, arguments: list[str]):
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return

        self.controller.show_rag()
        if self.controller._rag_view is not None:
            self.controller._rag_view.show()


class RagV2ShowCommand(Command):
    """Console RAG v2 entry command (feature_027).

    Repoints the console ``rag`` key to the v2 surface: calls
    ``controller.show_rag_v2()`` (which wires the v2 controller + view via
    ``set_view()``) then ``controller._rag_v2_view.show()`` to enter the REPL.
    v1's ``RagShowCommand`` stays for the TUI path (feature_024 parity wiring).
    """

    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Open RAG v2")
        self.controller = controller

    def run(self, arguments: list[str]):
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return

        self.controller.show_rag_v2()
        if self.controller._rag_v2_view is not None:
            self.controller._rag_v2_view.show()

class SumCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Add two integers: sum <a> <b>")
        self.controller = controller

    def run(self, arguments: list[str]):
        match arguments:
            case (x, y):
                if safe_int(x) is not None and safe_int(y) is not None:
                    self.controller.print_message(str(int(x) + int(y)))
                else:
                    self.controller.print_warring_message("invalid params for sum command")
            case _:
                self.controller.print_warring_message("invalid command")

        return None


class AIChat(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(
            key,
            description="Start an AI chat session: chat <query>, chat --model <model> <query>, or chat (interactive loop)",
        )
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return

        self.controller.show_chat()
        if self.controller._chat_view is not None:
            self.controller._chat_view.show()


class NewSessionCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Create a new session: new [name]")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        try:
            session_controller = self.controller.get_session_manager()
            new_session = session_controller.create_new_session()
            self.controller.print_message(f"New session created: {new_session.name}")

        except Exception as e:
            self.controller.print_error_message(f"Failed to create new session: {str(e)}")


class LSCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="List files in directory: ls [path]")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        if arguments:
            path = arguments[0]
        else:
            path = os.getcwd()

        try:
            if os.path.exists(path) and os.path.isdir(path):
                files = sorted(os.listdir(path))
                self.print(files, path)
            else:
                self.controller.print_error_message(f"Path does not exist or is not a directory: {path}")
                return
        except PermissionError:
            self.controller.print_error_message(f"Permission denied: {path}")
            return
        except Exception as e:
            self.controller.print_error_message(f"Error listing directory: {str(e)}")

    def print(self, files: list[str], path: str):
        if files:
            self.controller.print_message(f"Directory: {path}")
            for file in files:
                self.controller.print_message(f"  {file}")
        else:
            self.controller.print_message(f"Directory {path} is empty")


class VersionCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Show application version")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        self.controller.print_message(f"Agent-X version {APP_VERSION}")


# --- Console parity commands (feature_024) ---
#
# KEY DESIGN: ``MainController.show_*()`` wires controller+view via the
# provider but must NOT call ``view.show()`` (TUI pushes screens instead).
# Console commands therefore call ``show_*()`` first, then enter the view
# REPL via ``view.show()``.


class ReactCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Open ReAct (reasoning + acting) chat session")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return
        self.controller.show_react()
        if self.controller._react_view is not None:
            self.controller._react_view.show()


class CodingCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Open Coding agent (file operations + chat)")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return
        self.controller.show_coding()
        if self.controller._coding_view is not None:
            self.controller._coding_view.show()


class ModelsCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Select AI model provider (OpenRouter, Ollama, etc.)")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return
        self.controller.show_models()
        if self.controller._models_view is not None:
            self.controller._models_view.show()


class AgentCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Open Advanced Agent (full workspace, persistent memory)")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return
        self.controller.show_agent()
        if self.controller._agent_view is not None:
            self.controller._agent_view.show()


class FastAgentCommand(Command):
    def __init__(self, key: str, controller: MainController):
        super().__init__(key, description="Open Fast Agent (single-turn UX)")
        self.controller = controller

    def run(self, arguments: list[str]) -> None:
        if len(arguments) != 0:
            self.controller.print_warring_message("invalid command")
            return
        self.controller.show_fast_agent()
        if self.controller._fast_agent_view is not None:
            self.controller._fast_agent_view.show()