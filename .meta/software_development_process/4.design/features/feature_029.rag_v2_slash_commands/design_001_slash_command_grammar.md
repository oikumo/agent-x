# Design 001: Hybrid Slash-Command Grammar for the RAG v2 Console REPL

> **Phase:** Design — `omt_agent_guide.md §2`, §5–§10
> **Feature:** feature_029.rag_v2_slash_commands
> **Parent context:** `3.analysis/features/feature_029.rag_v2_slash_commands/analysis_001_console_ux_gaps.md` (gap matrix U1–U4 + options A/B/C; Option A + both cross-cutting fixes chosen by the user).
> **Shape:** Summary → Problem → Components → Static Structure → Flow → Operation Specs → Risks → Test plan (mirrors feature_027 design_001 template, proportionate size).

## Summary

Rework the `RagV2View` REPL from a numeric-menu-plus-implicit-chat model to a
**hybrid slash-command grammar**: bare text is a chat question (unchanged default),
and `/…` prefixes deterministic, no-LLM local commands. Delete the `_MENU_ACTIONS`
digit map (U2 collision), delete the fake `[3] chat` mode (U1), wire the existing
`on_tool_call`/`on_tool_result` streaming callbacks so retrieval is *visible* (U4),
and rename the tools `rag_search` → `search_documents` / `rag_ingest_status` →
`ingestion_status` across code + prompts + test pins (U4 jargon). v1 untouched.

## Problem Analysis

Per analysis_001: the menu is not a mode switch (`show_chat` only primes), menu keys
collide with real questions, no deterministic command surface exists, and retrieval is
invisible under a jargon name. Root cause: the REPL's dispatch has exactly two
buckets — "menu token" and "everything else is chat" — so anything operational must
either steal a token from the chat namespace or round-trip through the LLM.

The fix is a third bucket: the `/` prefix, which is unambiguous because no natural
question starts with `/` at position 0 in this REPL (and if one does, `/search <that
text>` is the documented escape hatch).

## Components

### Command surface (view-level dispatch)

| Command | Args | Routes to | Notes |
|---|---|---|---|
| `/help` | — | view-local | prints the command table (`RAG_V2_HELP` constant) |
| `/search <query…>` | required | `controller.send_message(query)` | explicit chat; empty → usage error, no send |
| `/repos` | — | `controller.list_repositories()` | lists on-disk repos (`RagV2Provider`), marks active, refreshes the registry |
| `/use [id]` | optional | no-arg → `select_repository()` (interactive picker); `<id>` → `controller.use_repository(id)` | direct activation: session registry → on-disk → error |
| `/create [name]` | optional | no-arg → `create_repository()` (prompt flow); `<name>` → `controller.create_repository_named(name)` | same validation as interactive (`_create_repository`) |
| `/ingest <web\|pdf\|md> <target>` | required | `controller.ingest(kind, target)` | direct ingestion on the active repo, bypassing sub-screen prompts; bad kind → usage error |
| `/status` | — | `controller.show_status()` | active repo id/path + `RagV2State` fields + thread id (no LLM) |
| `/reset` | — | `controller.reset_chat()` | `reset_conversation()` when the service is built; confirms either way |
| `/quit` | — | view-local exit | aliases `q`/`quit`/`exit` (bare) unchanged |
| unknown `/x` | — | view-local | error + "try /help" hint; never reaches the LLM |

Dispatch rule (single, total): `input.startswith("/")` → command branch; else
exit-token check; else empty re-prompt; else `send_message`. Menu map **deleted**.

### Tool-activity surfacing

`_dispatch_stream_delta` (`rag_v2_agent_service.py`) gains two routes:

- AI message with non-empty `tool_calls` → `on_tool_call(name, args_str)` per call.
- tool-type message → `on_tool_result(name, content_preview)` (preview truncated ~120 chars — tool content carries full chunk text).

`RagV2MainController._run_agent` wires both callbacks, mapping tool names to friendly
labels (`search_documents` → `search`, `ingestion_status` → `status`, `task` →
`analyst`, fallback the raw name) and printing `» <label>: <args>` lines via
`print_message`. Answer deltas keep streaming via `show_partial_message` — the `»`
lines interleave before/between answer lines in stream order.

### Tool rename (clean cut, no aliases)

- `rag_v2_tools.py`: `rag_search` → `search_documents`, `_rag_search_impl` →
  `_search_documents_impl`, `RagSearchResult` → `SearchDocumentsResult`,
  `rag_ingest_status` → `ingestion_status` (+ its impl/result mirrors),
  `RAG_V2_TOOLS` + `build_rag_v2_tools` `@tool("…")` names updated; the
  name-freeze comment (`:191-197`) replaced by the new canonical names.
- `rag_v2_agent_service.py`: both prompt sites (`DEFAULT_RAG_V2_SYSTEM_PROMPT`,
  path-binding suffix) reference the new names.
- `rag_v2_retriever.py`: docstring mention updated.
- Tests: 19 pins across `test_rag_v2_retrieval_tool.py` + `test_rag_v2_console_repl_regression.py` updated to the new names.

### Interface + dead-mode cut

`IRagV2ViewPartner`: **remove `show_chat`** (U1 — the fake mode; unreachable once the
menu map is gone) and add the new command methods (`list_repositories`,
`use_repository`, `create_repository_named`, `ingest`, `show_status`, `reset_chat`).
`show_menu()` stays on `IRagV2View` but its body prints the new banner + hint
(constants: `RAG_V2_MENU` rewritten; `RAG_V2_HELP` added — single-source-of-truth
constants rule from feature_027 analysis_001 surprise #3).

## Static Structure

```
RagV2View (ui/screens/rag_v2/rag_v2_view.py)
  show()                REPL: slash-branch → command; else exit/empty/chat
  _dispatch_command()   parse /cmd + args → controller method (or view-local)
  show_menu()           banner + "Type a question, or /help for commands."
RagV2MainController (ui/screens/rag_v2/rag_v2_controller.py)
  list_repositories()   NEW — provider list + active mark + registry refresh
  use_repository(id)    NEW — registry → provider.get_repository → error
  create_repository_named(name)  NEW — direct create via _create_repository
  ingest(kind, target)  NEW — {web,pdf,md} → ingest_* with active repo path
  show_status()         NEW — repo + RagV2State + thread id (no LLM)
  reset_chat()          NEW — service.reset_conversation() if built
  _run_agent()          wires on_tool_call/on_tool_result (» labels)
  show_chat()           REMOVED (dead fake mode)
rag_v2_tools.py         search_documents / ingestion_status (renamed)
rag_v2_agent_service.py _dispatch_stream_delta + tool routing; prompts renamed
interfaces.py           IRagV2ViewPartner ± methods above
constants.py            RAG_V2_MENU rewritten; RAG_V2_HELP added
```

## Flow

```
(rag-v2) input
  ├─ "/help"                → print RAG_V2_HELP
  ├─ "/search q…"           → send_message(q)          → agent turn (» lines + stream)
  ├─ "/repos|/use|/create|  → controller.<cmd>()        → deterministic, no LLM
  │   /ingest|/status|/reset"
  ├─ "/quit" | q/quit/exit  → return to main menu
  ├─ "/<unknown>"           → error + /help hint
  ├─ ""                     → re-prompt
  └─ <bare text>            → send_message(text)        → agent turn
```

Agent turn display: `» search: "query" (k=5)` → `» analyst: <desc>` → streamed answer.

## Operation Specs

- **Dispatch purity:** the slash branch never calls `send_message` except via
  `/search`; the chat branch never interprets tokens. Regression pin: bare `"1"`
  reaches `send_message("1")`.
- **`/ingest` guards:** no active repo → error hint (`/use` or `/create` first);
  unknown kind → usage line. Web ingest is sync-called exactly as the sub-controller
  does today (`ingest_web(url, repository_path=…)`).
- **Streaming truncation:** `on_tool_result` previews truncated to ≤120 chars; args
  in `on_tool_call` stringified + truncated to ≤120 chars.
- **Rename totality:** `rg "rag_search|rag_ingest_status" src/ tests/` → 0 hits at
  green (except this doc + feature_027 historical docs, which are immutable records).
- **ABC honesty:** every command the view calls exists on `IRagV2ViewPartner`;
  `show_chat` removed from ABC + controller + contract tests.

## Risks

| Risk | Mitigation |
|---|---|
| feature_027 pin churn (19 rename + menu-string pins) | run feature_027 suite every TDD cycle; update pins in the same cycle they break |
| Tool-result flood (full chunk text into console) | 120-char preview truncation in the dispatcher |
| `/ingest` bypasses sub-screen validation | replicate the sub-controllers' guards (active repo, kind enum); reuse the same ingest fns |
| `show_chat` removal breaks an unseen consumer | `rg show_chat` before removal; TDD red pins the ABC cut |

## Test plan (TDD behaviors)

1. `/help` prints the command table; unknown `/cmd` → error + hint; neither reaches `send_message`.
2. `/search <q>` → `send_message(q)`; bare `/search` → usage error, no send.
3. Chat default preserved: bare text → `send_message`; `q/quit/exit//quit` exit; empty re-prompts.
4. Menu-collision regression: bare `"1"`, `"s"` → `send_message` (menu map gone).
5. `/repos` lists provider repos, marks the active one, refreshes the registry.
6. `/use <id>`: registry hit, on-disk hit, unknown → error; bare `/use` → interactive picker.
7. `/create <name>` direct create (+ registry + active swap); bare `/create` → prompt flow.
8. `/ingest web|pdf|md <t>` calls the right ingest fn with the active repo path; no repo → error; bad kind → usage.
9. `/status` prints repo + state + thread id; no repo → hint.
10. `/reset` resets the conversation when the service exists; confirms either way.
11. Streaming: AI `tool_calls` → `on_tool_call(name, args)`; tool message → `on_tool_result(name, ≤120 preview)`; answer still streams; summarization filter intact.
12. Rename: `@tool` names are `search_documents`/`ingestion_status`; schemas expose no `repository_path`; prompts use the new names; `rg` totality check.
13. `show_chat` absent from ABC + controller; feature_027 contract/menu pins updated.
