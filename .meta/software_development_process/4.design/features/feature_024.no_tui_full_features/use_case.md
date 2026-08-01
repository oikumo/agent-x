# Use Case: No-TUI Full Features

> **Feature:** feature_024.no_tui_full_features

## Primary Actor
Developer / power user running `agentx` in a terminal that lacks TUI support (CI, SSH without TTY, Docker, tmux without pane focus, or explicit `--no-tui` flag).

## Preconditions
- `agentx` installed with dependencies.
- `OPENROUTER_API_KEY` set (or entered on first run).
- Terminal supports ANSI escape codes (colors, cursor movement) — standard for all modern terminals.

## Postconditions
User can access **all** AgentX features via console REPL:
- ReAct reasoning+acting chat
- Coding agent (file operations)
- Models selector (provider/model picker)
- Advanced Agent (full workspace)
- Fast Agent (modal quick-task)
- Plus existing Chat, RAG, Main menu

## Main Success Scenario
1. User runs `agentx --no-tui` (or `agentx` in non-TTY).
2. Main menu prints: welcome, command list, prompt `agentx>`.
3. User types `react` → ReAct screen opens:
   - Prints "ReAct Agent — type 'exit' to return"
   - User types task → agent streams reasoning + tool calls + final answer
   - User types `exit` → back to main menu
4. User types `coding` → Coding screen opens:
   - Similar flow, agent has file read/write tools
5. User types `models` → Models selector:
   - Lists providers (OpenRouter, etc.) and models
   - User selects → persisted for session
6. User types `agent` → Advanced Agent:
   - Full workspace agent, persists conversation
7. User types `fast-agent` → Fast Agent modal:
   - Single-task agent, returns summary, exits
8. User types `quit` → clean exit.

## Alternative Flows
- **Streaming interrupt:** User presses `Ctrl+C` during agent streaming → agent cancels, returns to screen prompt.
- **Invalid command:** Unknown command → prints "Unknown command: X. Type 'help' for list."
- **API error:** Network/auth failure → prints error, returns to screen prompt (not main menu).
- **Sub-command help:** `react --help` (if implemented) → prints screen-specific help.

## Error Scenarios
| Trigger | System Response |
|---------|-----------------|
| No API key | Prompt for key on startup (existing behavior) |
| Provider unavailable | Print error, stay in current screen |
| Agent crash | Catch exception, print traceback if `--debug`, return to main menu |
| Terminal too narrow (< 40 cols) | Degrade gracefully: no tables, wrap text |

## Non-Functional Requirements
- **Startup latency** < 500ms (no Textual import in --no-tui path).
- **Streaming latency** token-to-screen < 50ms (flush per token).
- **Memory** < 50MB baseline (no Textual widget tree).
- **Accessibility** works with screen readers (plain text, no TUI escape codes).