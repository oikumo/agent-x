# Design 001: Console Parity — No-TUI Full Features

> **Phase:** Design — `omt_agent_guide.md §2`, §5–§10  
> **Feature:** feature_024.no_tui_full_features

## Summary
Enable console (non-TUI) mode to access **all** TUI features — ReAct, Coding, Models, Agent, Fast Agent — via CLI menus/commands with parity to TUI keyboard shortcuts and screen navigation. Currently only Main, Chat, and RAG work in console mode; React, Coding, Models, Agent, and Fast Agent are TUI-only.

## Components / Screens Affected
| Console Screen | TUI Counterpart | Status |
|----------------|-----------------|--------|
| `ConsoleReactView` | `ReactTUIScreen` | **New** |
| `ConsoleCodingView` | `CodingTUIScreen` | **New** |
| `ConsoleModelsView` | `ModelsTUIScreen` | **New** |
| `ConsoleAgentView` | `AgentTUIScreen` | **New** |
| `ConsoleFastAgentView` | `FastAgentTUIScreen` | **New** |
| `MainView` (extend commands) | `MainTUIScreen` (actions) | **Extend** |
| `IUIProvider` interface | `TUIProvider` | **Extend + Implement** |

## Static Structure (Classes & Files)

| File | Layer | Responsibility |
|------|-------|----------------|
| `agentx/ui/interfaces.py` | Interface | Extend `IUIProvider` with `create_react_view`, `create_coding_view`, `create_models_view`, `create_agent_view`, `create_fast_agent_view` |
| `agentx/ui/providers.py` | Provider | `ConsoleProvider` implements the 5 new factory methods |
| `agentx/ui/screens/react/react_view.py` | View | `ConsoleReactView` implements `IReactView` |
| `agentx/ui/screens/react/react_controller.py` | Controller | `ReactController` implements `IReactViewPartner` |
| `agentx/ui/screens/coding/coding_view.py` | View | `ConsoleCodingView` implements `ICodingView` |
| `agentx/ui/screens/coding/coding_controller.py` | Controller | `CodingController` implements `ICodingViewPartner` |
| `agentx/ui/screens/models/models_view.py` | View | `ConsoleModelsView` implements `IModelsView` |
| `agentx/ui/screens/models/models_controller.py` | Controller | `ModelsController` implements `IModelsViewPartner` |
| `agentx/ui/screens/agent/agent_view.py` | View | `ConsoleAgentView` implements `IAgentView` |
| `agentx/ui/screens/agent/agent_controller.py` | Controller | `AgentController` implements `IAgentViewPartner` |
| `agentx/ui/screens/fast_agent/fast_agent_view.py` | View | `ConsoleFastAgentView` implements `IFastAgentView` |
| `agentx/ui/screens/fast_agent/fast_agent_controller.py` | Controller | `FastAgentController` implements `IFastAgentViewPartner` |
| `agentx/ui/screens/main/main_controller.py` | Controller | Add commands: `react`, `coding`, `models`, `agent`, `fast-agent` |
| `agentx/ui/screens/main/commands/commands.py` | Controller | New `Command` subclasses for each |
| `agentx/ui/interfaces.py` | Interface | New `IModelsView`, `IModelsViewPartner`, `IAgentView`, `IAgentViewPartner`, `IFastAgentView`, `IFastAgentViewPartner` |
| `agentx/model/session/session_manager.py` | Model | Reuse existing session for persistence |

## Abstract Partner Interfaces (new in `interfaces.py`)

```python
class IModelsViewPartner(ABC):
    @abstractmethod
    def select_model(self, provider: str, model: str) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

class IAgentViewPartner(ABC):
    @abstractmethod
    def send_message(self, user_message: str) -> bool: ...

    @abstractmethod
    def cancel(self) -> None: ...

    @property
    @abstractmethod
    def is_running(self) -> bool: ...

    @abstractmethod
    def get_history(self) -> list: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def start_new_conversation(self) -> None: ...

class IFastAgentViewPartner(ABC):
    @abstractmethod
    def send_message(self, user_message: str) -> bool: ...

    @abstractmethod
    def cancel(self) -> None: ...

    @property
    @abstractmethod
    def is_running(self) -> bool: ...

    @abstractmethod
    def get_cycle_summary(self) -> dict: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def start_new_conversation(self) -> None: ...
```

View interfaces (`IModelsView`, `IAgentView`, `IFastAgentView`) mirror the TUI view interfaces: `show()`, `show_message()`, `show_partial_message()`, `print_error()`, etc.

## Functional Flow (Sequence)

```
User → MainView.capture_input() → MainController.run_command("react")
     → MainController.show_react()
     → provider.create_react_view(controller)
     → ReactController + ConsoleReactView wired
     → ConsoleReactView.show()  (enters REPL loop)
     → ReactController.process_user_message()
     → Agent.run_cycle() (streaming)
     → ConsoleReactView.show_partial_message() / show_message()
     → User types "exit" → ReactController.close() → back to MainView
```

Same pattern for `coding`, `models`, `agent`, `fast-agent`.

## Operation Specifications (Controller Methods)

| Controller | Method | Pre | Post | Exceptions |
|------------|--------|-----|------|------------|
| `MainController` | `show_react()` | provider set | view shown, controller stored | `RuntimeError` if no provider |
| `MainController` | `show_coding()` | provider set | view shown, controller stored | `RuntimeError` if no provider |
| `MainController` | `show_models()` | provider set | view shown, controller stored | `RuntimeError` if no provider |
| `MainController` | `show_agent()` | provider set | agent created/wired, view shown | `RuntimeError` if no provider |
| `MainController` | `show_fast_agent()` | provider set | agent created/wired, view shown | `RuntimeError` if no provider |
| `ReactController` | `process_user_message(msg)` | view set | returns True if agent started | `ValueError` if empty msg |
| `CodingController` | `process_user_message(msg)` | view set | returns True if agent started | `ValueError` if empty msg |
| `ModelsController` | `select_model(provider, model)` | view set | model persisted, view updated | `ValueError` if unknown provider |
| `AgentController` | `send_message(msg)` | agent wired | returns True if accepted | `RuntimeError` if not ready |
| `FastAgentController` | `send_message(msg)` | agent wired | returns True if accepted | `RuntimeError` if not ready |

## Streaming Support in Console Views
`IChatView` already has `show_partial_message()` and `show_stream_message()`. Console views will implement these using `UIConsole.stream_write()` (to be added to `ui_console.py`) for token-by-token output without buffering.

## MVC++ Self-Check
- [ ] Views do not import Model
- [ ] Models do not import ui
- [ ] Abstract Partners are `ABC` with `@abstractmethod`
- [ ] SQL only in `*_db.py` / `DP_*` (N/A — no new persistence)
- [ ] No `*Controller` under `model/`
- [ ] `uv run scripts/omt/mvc_check.py` passes for touched files

## Integration Points
- `ProviderRegistry` already supports multiple providers; `ConsoleProvider` registered as fallback in `providers.py:138`
- `MainController` already accepts `provider: IUIProvider | None` and uses it in `show_chat()` / `show_rag()` — extend same pattern
- TUI provider (`TUIProvider`) unchanged; TUI continues to use adapters + Textual screens
- Session persistence reuses `SessionManager` (agent memory, working directory)

## Risks / Open Questions
| Risk | Mitigation |
|------|------------|
| `IAgentViewPartner` / `IFastAgentViewPartner` clash with `agentx.agent.interfaces` | Keep in `agentx.ui.interfaces`; TUI adapters already duck-type to these names |
| Console streaming UX differs from TUI (no live region) | Implement `UIConsole.stream_write()` with carriage-return + flush; match token cadence |
| Agent/FastAgent controllers currently import TUI views (`agentx.agent.view.tui.*`) | Console controllers import console views only; adapter pattern keeps them isolated |
| `MainController` command parser needs new command classes | Follow existing `Command` pattern (`HelpCommand`, `AIChat`, etc.) |

## Acceptance Criteria (Design Done)
1. `design_001_console_parity.md` exists and passes self-check.
2. All 5 new console views + controllers + interfaces defined on paper.
3. `MainController` command surface extended with 5 new commands.
4. `ConsoleProvider` implements 5 new factory methods.
5. No TUI code modified; no circular imports introduced.