# Analysis 001: Console Gap — Missing TUI Features in --no-tui Mode

> **Phase:** Analysis  
> **Feature:** feature_024.no_tui_full_features  
> **Date:** 2026-07-26

## Current State

The codebase has a clean Dependency Inversion architecture:
- `IUIProvider` (abstract factory) creates `IMainView`, `IRagView`, `IChatView`.
- `ProviderRegistry` holds two providers: `console` (fallback) and `tui` (default).
- `main.py` detects `--no-tui` or non-TTY → selects `console` provider.
- `MainController` calls `provider.create_*_view()` for Chat and RAG, then wires controller ↔ view.

### Working in Console Mode (via `ConsoleProvider`)
| Feature | Console View | Controller | Entry |
|---------|--------------|------------|-------|
| Main menu | `MainView` (REPL) | `MainController` | `main_view.show()` |
| Chat | `ChatView` | `ChatController` | `chat` command / `show_chat()` |
| RAG + sub-screens | `RagView` + rag sub-views | `RagController` + sub-controllers | `rag` command / `show_rag()` |

### Missing in Console Mode (TUI-only)
| Feature | TUI Screen | Controller | TUI Entry (binding) |
|---------|------------|------------|---------------------|
| ReAct agent | `ReactTUIScreen` | `ReactController` | `t` / `action_open_react` |
| Coding agent | `CodingTUIScreen` | `CodingController` | `d` / `action_open_coding` |
| Models selector | `ModelsTUIScreen` | `ModelsController` | `m` / `action_open_models` |
| Advanced Agent | `AgentTUIScreen` | `AgentController` | `a` / `action_open_agent` |
| Fast Agent | `FastAgentTUIScreen` | `AgentController` (reuse) | `f` / `action_open_fast_agent` |

**Controllers already exist** for React, Coding, Models — only views missing.
**Agent / Fast Agent** controllers exist in `agentx/agent/controller/` and reuse `AgentController`.

## Root Cause
`IUIProvider` only declares factory methods for `create_main_view`, `create_rag_view`, `create_chat_view`.  
`ConsoleProvider` only implements those three.  
`MainController.show_react()`, `show_coding()`, `show_models()`, `show_agent()`, `show_fast_agent()` **do not call the provider** — they only create controllers and rely on TUI's `navigate_to_child()` to push the screen. No console `view.show()` is invoked.

## Dependency Inversion Gap
```
IUIProvider (interface)
  ├─ create_main_view()
  ├─ create_rag_view()
  ├─ create_chat_view()
  └─ [MISSING] create_react_view(), create_coding_view(), create_models_view(),
                create_agent_view(), create_fast_agent_view()

ConsoleProvider (concrete)
  ├─ implements first three
  └─ [MISSING] implements last five

TUIProvider (concrete)
  ├─ implements first three (returns TUIAdapter)
  └─ [BYPASS] TUI uses Textual screens directly, not provider
```

## Required Interfaces (new)
| Interface | Purpose | Partner |
|-----------|---------|---------|
| `IModelsView` | Models selector UI | `IModelsViewPartner` (select_model, close) |
| `IReactView` | ReAct chat UI | `IReactViewPartner` (process_user_message, close, get_history, is_running, start_new_conversation) |
| `ICodingView` | Coding agent UI | `ICodingViewPartner` (same shape as IReactViewPartner) |
| `IAgentView` | Advanced agent UI | `IAgentViewPartner` (same shape) |
| `IFastAgentView` | Fast agent modal UI | `IFastAgentViewPartner` (send_message, cancel, is_running, get_cycle_summary, close, start_new_conversation) |

## Streaming Requirements
`IChatView` already defines:
- `show_partial_message(message: str)` — streaming token
- `show_stream_message(message: str)` — typing effect

Console views must implement these via `UIConsole.stream_write()` (new method) for token-by-token output.

## Command Surface (MainController)
Current commands: `sum`, `quit`, `clear`, `help`, `history`, `chat`, `new`, `ls`, `rag`, `version`.

**Add 5 commands:** `react`, `coding`, `models`, `agent`, `fast-agent`.

Each follows the `AIChat` pattern: create/wire controller+view via provider, then `view.show()`.

## Acceptance Criteria (Analysis Done)
1. Gap documented: 5 TUI features missing in console mode.
2. Root cause identified: `IUIProvider` + `ConsoleProvider` missing 5 factory methods; `MainController` missing 5 `show_*()` implementations that wire provider views.
3. All required new interfaces, views, controllers, commands listed.
4. No TUI code changes required.
5. Streaming tokens must work in console views (new `UIConsole.stream_write()`).