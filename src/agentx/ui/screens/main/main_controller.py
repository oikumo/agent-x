from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agentx.ui.screens.chat.chat_controller import ChatController
from agentx.ui.screens.main.commands.commands import SumCommand, QuitCommand, ClearCommand, HelpCommand, \
    AIChat, HistoryCommand, NewSessionCommand, LSCommand, RagShowCommand, RagV2ShowCommand, VersionCommand, \
    ReactCommand, CodingCommand, ModelsCommand, AgentCommand, FastAgentCommand
from agentx.ui.screens.main.commands.commands_base import Command
from agentx.ui.screens.main.commands.commands_parser import CommandParser
from agentx.model.session.session_manager import SessionManager
from agentx.ui.screens.main.main_view import MainView
from agentx.ui.interfaces import IMainViewPartner, IChatView, IRagView, IMainView
from agentx.ui.screens.rag.rag_controller import RagController
from agentx.ui.interfaces import (
    IReactView,
    ICodingView,
    IModelsView,
    IAgentView,
    IFastAgentView,
)

if TYPE_CHECKING:
    from agentx.ui.interfaces import IUIProvider
    from agentx.agent.controller.agent_controller import AgentController
    from agentx.agent.interfaces import IAgentViewPartner
    from agentx.ui.screens.models.models_controller import ModelsController
    from agentx.ui.screens.react.react_controller import ReactController
    from agentx.ui.tui.screens.coding.coding_controller import CodingController
    # Console parity interfaces (feature_024)
    from agentx.ui.interfaces import (
        IReactViewPartner,
        ICodingViewPartner,
        IModelsViewPartner,
    )
    # RAG v2 (feature_027)
    from agentx.ui.interfaces import IRagV2View
    from agentx.ui.screens.rag_v2.rag_v2_controller import RagV2MainController
    from agentx.ui.providers import ConsoleProvider


class MainController(IMainViewPartner):
    def __init__(self, view: IMainView | None = None, provider: "IUIProvider | None" = None):
        self.commands: dict[str, Command] = {}
        self.parser = CommandParser()
        self.view: IMainView = view if view else MainView(self)
        self._provider = provider
        self.session_controller = SessionManager()
        # Store sub-controllers and views for screen connection
        self._chat_controller: ChatController | None = None
        self._chat_view: IChatView | None = None
        self._rag_controller: RagController | None = None
        self._rag_view: IRagView | None = None
        # RAG v2 (feature_027) — console-only sibling of v1. v1's _rag_* stay
        # for the TUI path; the console `rag` command repoints to v2 below.
        self._rag_v2_controller: "RagV2MainController | None" = None
        self._rag_v2_view: "IRagV2View | None" = None
        self._agent_controller: AgentController | None = None
        self._fast_agent_controller: AgentController | None = None
        self._models_controller: "ModelsController | None" = None
        self._react_controller: "ReactController | None" = None
        self._coding_controller: "CodingController | None" = None
        # Console parity views (feature_024)
        self._react_view: IReactView | None = None
        self._coding_view: ICodingView | None = None
        self._models_view: IModelsView | None = None
        self._agent_view: IAgentView | None = None
        self._fast_agent_view: IFastAgentView | None = None
        self.load_commands()

    def load_commands(self):
        self.add_command(SumCommand("sum", self))
        self.add_command(QuitCommand("quit", self))
        self.add_command(ClearCommand("clear", self))
        self.add_command(HelpCommand("help", self))
        self.add_command(HistoryCommand("history", self))
        self.add_command(AIChat("chat", self))
        self.add_command(NewSessionCommand("new", self))
        self.add_command(LSCommand("ls", self))
        # feature_027: console `rag` repoints to v2 (console-only); the TUI path
        # keeps v1's RagShowCommand. When a console provider (ConsoleProvider)
        # supplied v2, RagV2ShowCommand routes `rag` → show_rag_v2; otherwise
        # register v1's RagShowCommand for the TUI path. v2 is console-only.
        # Lazy runtime import (circular-safe): ConsoleProvider is only in
        # TYPE_CHECKING above, so `isinstance` needs the real class at runtime.
        # Importing inside load_commands avoids an unbound name (NameError) while
        # keeping the top-level import cycle-free (pause_2026-08-15_l §Fix 2,
        # option A — distinguishes the real ConsoleProvider from a TUIProvider/
        # mock by class identity, which a hasattr capability check could NOT).
        from agentx.ui.providers import ConsoleProvider
        if isinstance(self._provider, ConsoleProvider):
            self.add_command(RagV2ShowCommand("rag", self))
        else:
            self.add_command(RagShowCommand("rag", self))
        self.add_command(VersionCommand("version", self))
        # Console parity commands (feature_024)
        self.add_command(ReactCommand("react", self))
        self.add_command(CodingCommand("coding", self))
        self.add_command(ModelsCommand("models", self))
        self.add_command(AgentCommand("agent", self))
        self.add_command(FastAgentCommand("fast-agent", self))

    def get_session_manager(self):
        return self.session_controller

    def show_chat(self):
# TA: gotcha: BUG (feature_024 console parity): show_chat/show_rag must NOT call view.show() — the TUI path uses them as setup callbacks then pushes a screen; the console (no-TUI) path relies on AIChat/RagShowCommand calling view.show() afterwards to enter the REPL (feature_024 parity pattern). The OLD fallback `if self._provider: ... else: chat_controller.show()` violated parity (console never entered the REPL).
        # C5: reuse an already-wired controller (no fresh chat on every open).
        if self._chat_controller is not None:
            return
        chat_controller = ChatController()
        if self._provider is not None:
            chat_view = self._provider.create_chat_view(chat_controller)
            chat_controller.view = chat_view
            # Store for screen connection (TUI pushes a screen; the console
            # command enters the REPL via view.show() — feature_024 parity).
            self._chat_view = chat_view
        self._chat_controller = chat_controller

    def show_rag(self):
        # C5: reuse an already-wired controller (no fresh rag on every open).
        if self._rag_controller is not None:
            return
        rag_controller = RagController()
        if self._provider is not None:
            rag_view = self._provider.create_rag_view(rag_controller)
            rag_controller.view = rag_view
            # Store for screen connection (TUI pushes a screen; the console
            # command enters the REPL via view.show() — feature_024 parity).
            self._rag_view = rag_view
        self._rag_controller = rag_controller

    def get_chat_controller(self) -> tuple[ChatController | None, IChatView | None]:
        """Get the chat controller and view for screen connection."""
        return self._chat_controller, self._chat_view

    def get_rag_controller(self) -> tuple[RagController | None, IRagView | None]:
        """Get the RAG controller and view for screen connection."""
        return self._rag_controller, self._rag_view

    def show_rag_v2(self):
        # TA: gotcha: FIX (feature_024, Constraint d): show_rag_v2 wires the v2
        # controller via set_view(view) rather than the legacy direct-attribute
        # assignment (the OLD pattern, which v1's show_rag at line 106 still
        # uses) — that left _view=None so streaming callbacks silently no-op.
        # v2 mirrors the FIXED show_react/show_coding pattern (lines 251/273),
        # NOT v1's buggy show_rag.
        # C5: reuse an already-wired controller (no fresh rag on every open).
        # NOTE: show_rag_v2 must NOT call view.show() — the TUI path uses it as
        # a setup callback then pushes a screen; the console (no-TUI) path
        # relies on RagV2ShowCommand calling view.show() afterwards (feature_024
        # parity). v2 is console-only.
        if self._rag_v2_controller is not None:
            return
        from agentx.ui.screens.rag_v2.rag_v2_controller import RagV2MainController
        rag_v2_controller = RagV2MainController()
        if self._provider is not None:
            rag_v2_view = self._provider.create_rag_v2_view(rag_v2_controller)
            rag_v2_controller.set_view(rag_v2_view)   # set_view (Constraint d), NOT the legacy dot-view assignment
            self._rag_v2_view = rag_v2_view
        self._rag_v2_controller = rag_v2_controller

    def get_rag_v2_controller(self) -> tuple["RagV2MainController | None", "IRagV2View | None"]:
        """Get the RAG v2 controller and view for screen connection."""
        return self._rag_v2_controller, self._rag_v2_view

    def show_agent(self) -> None:
        """Create and wire an Agent + AgentController for the TUI agent screen.

        C5: reuses an already-wired controller (no fresh agent on every open).
        I1/I4: the :class:`AgentAdapter` owns AI-service wiring and resumes the
        latest persisted snapshot so state survives a close/reopen.
        """
        # C5: reuse the existing agent controller if already wired this session.
        if self._agent_controller is not None:
            return

        from agentx.agent.adapter import AgentAdapter
        from agentx.agent.types import AgentConfig, AutonomyLevel, MemoryConfig

        # Use the session working directory for persistence + sandbox.
        session_dir = "."
        try:
            session = self.session_controller.get_current_session()
            if session and session.directory:
                session_dir = session.directory
        except Exception:
            pass

        import os
        agent_id = f"agent_{os.getpid()}"
        config = AgentConfig(
            id=agent_id,
            name="AgentX Agent",
            autonomy_level=AutonomyLevel.SUPERVISED,
            memory_config=MemoryConfig(persistent_path=session_dir),
            sandbox_root=session_dir,
        )
        _agent, controller = AgentAdapter.create_agent(config, resume=True)
        agent_view = self._provider.create_agent_view(controller) if self._provider else None
        if agent_view is not None:
            controller.set_view(cast("IAgentViewPartner", agent_view))
        self._agent_controller = controller
        self._agent_view = agent_view

    def get_agent_controller(self) -> AgentController | None:
        """Get the agent controller for screen connection."""
        return self._agent_controller

    def show_fast_agent(self) -> None:
        """Create and wire a Fast Agent (feature_011) — modal-dialog UX.

        Builds an :class:`Agent` + :class:`AgentController` (reusing the same
        engine as the Advanced Agent) and wires a no-op
        :class:`FastAgentTUIView` as the controller's partner.  The Fast Agent
        screen is pushed by :meth:`MainTUIScreen.action_open_fast_agent`.

        C5: reuses an already-wired controller (no fresh agent on every open).
        """
        if self._fast_agent_controller is not None:
            return

        from agentx.agent.adapter import AgentAdapter
        from agentx.agent.types import AgentConfig, AutonomyLevel, MemoryConfig

        session_dir = "."
        try:
            session = self.session_controller.get_current_session()
            if session and session.directory:
                session_dir = session.directory
        except Exception:
            pass

        import os
        agent_id = f"fast_agent_{os.getpid()}"
        config = AgentConfig(
            id=agent_id,
            name="AgentX Fast Agent",
            autonomy_level=AutonomyLevel.SUPERVISED,
            memory_config=MemoryConfig(persistent_path=session_dir),
            sandbox_root=session_dir,
        )
        _agent, controller = AgentAdapter.create_agent(config, resume=True)

        fast_agent_view = self._provider.create_fast_agent_view(controller) if self._provider else None
        if fast_agent_view is not None:
            # ConsoleFastAgentView acts as the controller's partner (no-op
            # wiring acceptable for console parity).
            controller.set_view(cast("IAgentViewPartner", fast_agent_view))
        self._fast_agent_controller = controller
        self._fast_agent_view = fast_agent_view

    def get_fast_agent_controller(self) -> AgentController | None:
        """Get the Fast Agent controller for screen connection."""
        return self._fast_agent_controller

    def show_models(self) -> None:
        """Create and wire a ModelsController for the Models screen via provider.

        Uses the provider pattern (create_models_view) for console parity.
        Reuses an already-wired controller (C5 pattern).
        """
        if self._models_controller is not None:
            return
        from agentx.ui.screens.models.models_controller import ModelsController

        models_controller = ModelsController()
        if self._provider is not None:
            models_view = self._provider.create_models_view(models_controller)
            models_controller.view = models_view
            self._models_view = models_view
        self._models_controller = models_controller

    def get_models_controller(self) -> "ModelsController | None":
        """Get the Models controller for screen connection."""
        return self._models_controller

    def show_react(self) -> None:
        """Create and wire a ReactController for the ReAct screen via provider.

        Uses the provider pattern (create_react_view) for console parity.
        Reuses an already-wired controller (C5 pattern).
        """
        if self._react_controller is not None:
            return
        from agentx.ui.screens.react.react_controller import ReactController

        react_controller = ReactController()
        if self._provider is not None:
            react_view = self._provider.create_react_view(react_controller)
            react_controller.set_view(react_view)
            self._react_view = react_view
        self._react_controller = react_controller

    def get_react_controller(self) -> "ReactController | None":
        """Get the ReAct controller for screen connection."""
        return self._react_controller
# TA: gotcha: FIX (feature_024): use set_view(view) not .view = view inside show_react/show_coding — controllers store self._view (set only via set_view); the old .view= assignment left _view=None so _run_agent silent-no-oped all streaming callbacks (agent ran but nothing displayed).

    def show_coding(self) -> None:
        """Create and wire a CodingController for the Coding screen via provider.

        Uses the provider pattern (create_coding_view) for console parity.
        Reuses an already-wired controller (C5 pattern).
        """
        if self._coding_controller is not None:
            return
        from agentx.ui.tui.screens.coding.coding_controller import CodingController

        coding_controller = CodingController()
        if self._provider is not None:
            coding_view = self._provider.create_coding_view(coding_controller)
            coding_controller.set_view(coding_view)
            self._coding_view = coding_view
        self._coding_controller = coding_controller

    def get_coding_controller(self) -> "CodingController | None":
        """Get the Coding controller for screen connection."""
        return self._coding_controller
# TA: gotcha: FIX (feature_024): same set_view bug as show_react — _view was None, streaming callbacks silent-no-oped.

    def print_message(self, message: str):
        self.view.print_message(message)

    def print_warring_message(self, message: str):
        self.view.print_warring_message(message)

    def print_error_message(self, message: str):
        self.view.print_error_message(message)

    def run(self):
        self.view.show()

    def get_commands(self) -> list[Command]:
        # NOTE: shallow copy only — deepcopy would recurse into every Command's
        # ``controller`` back-reference and copy the whole MainController graph
        # (views, providers, and live rag_v2 worker threads), which crashes with
        # ``TypeError: cannot pickle '_thread.lock' object``. Callers only read
        # ``key``/``description`` (HelpCommand), so a shallow list copy is enough.
        return list(self.commands.values())

    def add_command(self, command: Command):
        self.commands[command.key] = command

    def commands_history(self) -> list[str]:
        history: list[str] = []

        entries = self.session_controller.select_history_entry()
        if entries:
            for entry in entries:
                history.append(entry.command)
        return history


    def close(self):
        exit(0)

    def error(self):
        pass

    def print(self):
        pass

    def run_command(self, user_input: str):
        command_data = self.parser.parse(user_input)
        if not command_data:
            return

        command = self.commands.get(command_data.key)
        if not command:
            self.view.print_response_error(f"Unknown command: {command_data.key}")
            return

        self.session_controller.insert_history_entry(command_data.key)

        try:
            command.run(command_data.arguments)

        except Exception as e:
            self.view.print_response_error(f"Command execution failed")
            print(e)