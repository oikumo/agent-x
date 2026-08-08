from dataclasses import dataclass
from enum import IntEnum

class UIMessageType(IntEnum):
    INFO = 0
    SUCCESS = 1
    WARNING = 2
    ERROR = 3
    HEADER = 4


@dataclass
class UIMessage:
    message: str
    message_type: UIMessageType = UIMessageType.INFO


class UIConsoleColors:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class UIPrompt:
    base: str
    parts: list[str]

    def __init__(self, base: str, parts: list[str] | None = None) -> None:
        self.base = base or ""
        self.parts = list(parts or [])

    def prompt(self) -> str:
        suffix = "/" + "/".join(self.parts) if self.parts else ""
        return f"({self.base}{suffix}) "

    def reset_prompt(self) -> None:
        self.parts.clear()

class UIConsole:
    def __init__(self, prompt: str = ""):
        super().__init__()
        self.ui_prompt = prompt

    def reset_prompt(self) -> None:
        self.ui_prompt = ""

    def set_prompt_additional(self, part: str):
        self.ui_prompt += part

    def capture_input(self) -> str | None:
        """Capture one line of user input.

        Returns:
            The stripped input string ('' for a bare Enter), or ``None`` when
            the user interrupts (Ctrl+C) or sends EOF (Ctrl+D). The empty-vs-
            ``None`` distinction lets REPLs re-prompt on a bare Enter while
            still exiting on a real interrupt (feature_024 fix: react module
            empty input must re-prompt, not return to the main menu).
        """
        try:
            user_input = input(f"{self.ui_prompt} ").strip()
            return user_input
        except KeyboardInterrupt:
            self.error("received interrupt, exiting...")
        except EOFError:
            self.error("EOF received, exiting...")
        return None

    def partial_info(self, message: str) -> None:
        print(f"{UIConsoleColors.DARKCYAN}{message}{UIConsoleColors.END}", end="", flush=True)

    def info(self, message: str) -> None:
        print(f"{UIConsoleColors.DARKCYAN}{message}{UIConsoleColors.END}")

    def success(self, message: str) -> None:
        print(f"{UIConsoleColors.GREEN}{message}{UIConsoleColors.END}")

    def waning(self, message: str) -> None:
        print(f"{UIConsoleColors.YELLOW}{message}{UIConsoleColors.END}")

    def error(self, message: str) -> None:
        print(f"{UIConsoleColors.RED}❌ {message}{UIConsoleColors.END}")

    def header(self, message: str) -> None:
        print(f"\n{UIConsoleColors.BOLD}{UIConsoleColors.PURPLE}{'=' * 60}{UIConsoleColors.END}")
        print(f"{UIConsoleColors.BOLD}{UIConsoleColors.PURPLE}{message}{UIConsoleColors.END}")
        print(f"{UIConsoleColors.BOLD}{UIConsoleColors.PURPLE}{'=' * 60}{UIConsoleColors.END}\n")

    def stream_write(self, text: str) -> None:
        """Write text to stdout without newline, flushing immediately for token streaming."""
        print(text, end="", flush=True)







