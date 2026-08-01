# Operation Spec 001: Console Commands & Controller Methods

> **Phase:** Design — `omt_agent_guide.md §10`  
> **Feature:** feature_024.no_tui_full_features

---

## New Commands in `MainController`

### `react` — `ReactCommand`
```python
class ReactCommand(Command):
    key = "react"
    description = "Open ReAct (reasoning + acting) chat session"
```
**Pre:** `MainController._provider` is set (not None)  
**Post:** `ConsoleReactView.show()` entered; `MainController._react_controller` stored  
**Exc:** `RuntimeError` if provider not set

### `coding` — `CodingCommand`
```python
class CodingCommand(Command):
    key = "coding"
    description = "Open Coding agent (file operations + chat)"
```
**Pre:** provider set  
**Post:** `ConsoleCodingView.show()` entered; `_coding_controller` stored  
**Exc:** `RuntimeError` if provider not set

### `models` — `ModelsCommand`
```python
class ModelsCommand(Command):
    key = "models"
    description = "Select AI model provider (OpenRouter, Ollama, etc.)"
```
**Pre:** provider set  
**Post:** `ConsoleModelsView.show()` entered; `_models_controller` stored  
**Exc:** `RuntimeError` if provider not set

### `agent` — `AgentCommand`
```python
class AgentCommand(Command):
    key = "agent"
    description = "Open Advanced Agent (full workspace, persistent memory)"
```
**Pre:** provider set; session directory available  
**Post:** `AgentAdapter.create_agent()` called (resume=True); `ConsoleAgentView.show()` entered; `_agent_controller` stored  
**Exc:** `RuntimeError` if provider not set; `AgentError` if agent creation fails

### `fast-agent` — `FastAgentCommand`
```python
class FastAgentCommand(Command):
    key = "fast-agent"
    description = "Open Fast Agent (modal, single-turn UX)"
```
**Pre:** provider set  
**Post:** `AgentAdapter.create_agent()` called; `FastAgentTUIView` wired as partner; `ConsoleFastAgentView.show()` entered; `_fast_agent_controller` stored  
**Exc:** `RuntimeError` if provider not set

---

## New Controller Methods (on `MainController`)

| Method | Pre | Post | Exceptions |
|--------|-----|------|------------|
| `show_react()` | `_provider` set | `_react_controller`, `_react_view` stored; `view.show()` called | `RuntimeError` |
| `show_coding()` | `_provider` set | `_coding_controller`, `_coding_view` stored; `view.show()` called | `RuntimeError` |
| `show_models()` | `_provider` set | `_models_controller`, `_models_view` stored; `view.show()` called | `RuntimeError` |
| `show_agent()` | `_provider` set | `_agent_controller` created/wired via `AgentAdapter`; `view.show()` called | `RuntimeError`, `AgentError` |
| `show_fast_agent()` | `_provider` set | `_fast_agent_controller` created/wired; `view.show()` called | `RuntimeError`, `AgentError` |

---

## Sub-Controller Method Specs

### `ReactController.process_user_message(user_message: str) -> bool`
**Pre:** `self.view` set (via provider); agent wired  
**Post:** Returns `True` if agent cycle started; `self.view.show_partial_message()` called for each token; `self.view.show_message()` for final  
**Exc:** `ValueError` if empty message; `RuntimeError` if agent not ready

### `CodingController.process_user_message(user_message: str) -> bool`
**Pre:** `self.view` set; agent wired  
**Post:** Same as ReactController  
**Exc:** Same as ReactController

### `ModelsController.select_model(provider: str, model: str) -> None`
**Pre:** `self.view` set; provider known  
**Post:** Selection persisted to config; `self.view.show_message()` confirms  
**Exc:** `ValueError` if unknown provider/model

### `AgentController.send_message(user_message: str) -> bool`
**Pre:** Agent created (via `AgentAdapter`), `self.view` set  
**Post:** Returns `True` if accepted; streaming via `self.view.show_partial_message()`  
**Exc:** `RuntimeError` if agent not ready; `ValueError` if empty

### `FastAgentController.send_message(user_message: str) -> bool`
**Pre:** Agent created, `FastAgentTUIView` wired as partner  
**Post:** Returns `True` if cycle started; `self.view.show_cycle_summary()` or similar  
**Exc:** `RuntimeError` if agent busy; `ValueError` if empty

---

## View Interface Methods (implemented by Console views)

| Interface | Method | Purpose |
|-----------|--------|---------|
| `IReactView` | `show()` | Enter REPL loop |
| `IReactView` | `show_message(msg: str, role: str)` | Print complete message |
| `IReactView` | `show_partial_message(msg: str)` | Print streaming token |
| `IReactView` | `print_error(msg: str)` | Print error in red |
| `ICodingView` | (same as IReactView) | — |
| `IModelsView` | `show()` | Enter model selection menu |
| `IModelsView` | `show_available_providers(providers: list)` | List providers |
| `IModelsView` | `show_models_for_provider(provider: str, models: list)` | List models |
| `IModelsView` | `show_message(msg: str)` | Info message |
| `IModelsView` | `print_error(msg: str)` | Error message |
| `IAgentView` | `show()` | Enter agent REPL |
| `IAgentView` | `show_message(msg: str, role: str)` | Complete message |
| `IAgentView` | `show_partial_message(msg: str)` | Streaming token |
| `IAgentView` | `print_error(msg: str)` | Error |
| `IFastAgentView` | `show()` | Enter fast-agent modal loop |
| `IFastAgentView` | `show_cycle_summary(summary: dict)` | Print cycle result |
| `IFastAgentView` | `print_error(msg: str)` | Error |

---

## Streaming Implementation Note
`agentx.ui.common.ui_console.UIConsole` will get a new method:
```python
def stream_write(self, text: str) -> None:
    """Write text without newline, flush immediately for token streaming."""
    sys.stdout.write(text)
    sys.stdout.flush()
```
Console views call `self.console.stream_write(token)` in `show_partial_message()`.

---

## Acceptance Criteria (Operation Spec Done)
1. All 5 new `Command` classes defined with pre/post/exc.
2. All 5 `MainController.show_*()` methods specified.
3. All sub-controller interaction methods specified.
4. View interface method tables complete.
5. Streaming console UX defined.