# Analysis 001: RAG v2 Console UX Gaps — Slash Commands

> **Phase:** Analysis — `omt_agent_guide.md §2`
> **Feature:** feature_029.rag_v2_slash_commands
> **Trigger:** user feedback 2026-08-16 — "chat option is unclear (no TUI); must allow the user to execute commands; option `rag_search` is not clear; make commands like `/<command>`".

## Summary

The feature_027 console REPL works but its interaction model is ambiguous: a numeric
menu that is *not* a mode switch, an implicit chat fallback, and zero visibility into
what the agent is doing. This analysis pins the four concrete UX gaps with file:line
evidence and records the chosen direction (hybrid slash commands + tool-activity
surfacing + tool rename) from the three options presented to the user.

## Gap matrix (evidence per HEAD)

| # | Gap | Evidence | Impact |
|---|-----|----------|--------|
| U1 | `[3] chat` is a fake mode — it only pre-builds the agent service; the real chat is "type anything else" | `rag_v2_controller.py:141-155` (`show_chat` primes only), `rag_v2_view.py:63-66` (fallback → `send_message`) | User presses 3, sees "Chat ready", doesn't understand chat was *already* available |
| U2 | Menu keys eat questions — any input equal to `1`–`6`/`s`/`q` is swallowed by the menu | `rag_v2_view.py:25-33` (`_MENU_ACTIONS`), `:52-62` (token dispatch) | One-char questions impossible; `s`/`q` collide with real words |
| U3 | No explicit command surface — every non-menu input goes to the LLM; no deterministic local actions (list repos, status, reset) | `rag_v2_view.py:63-66` | User can't operate the REPL without talking to the model |
| U4 | `rag_search` is invisible + jargon — the console wires only `on_answer`; `on_tool_call`/`on_tool_result` exist but are unused; the tool name is LLM-facing | `rag_v2_controller.py:232-238` (only `on_answer`/`on_done`/`on_error` wired), `rag_v2_agent_service.py:253-282` (`_dispatch_stream_delta` never routes tool events) | User sees a pause, then an answer — retrieval "happens" invisibly under an unclear name |

## Options considered

| Option | Shape | Verdict |
|---|---|---|
| **A — Hybrid** | bare text = chat; `/cmd` = deterministic local commands | **CHOSEN** — kills U1/U2/U3, keeps chat zero-friction; classic REPL/IRC convention |
| B — Strict | questions require `/search <q>`; bare text rejected | Rejected — heavier for the common case |
| C — Slash + keep menu | add `/cmd`, keep `[1]–[6]/s` | Rejected — keeps the U2 collision and two ways to do everything |

Cross-cutting fixes **both chosen**: (a) surface tool activity via the existing
`on_tool_call`/`on_tool_result` callbacks (closes U4-visibility); (b) rename
`rag_search` → `search_documents`, `rag_ingest_status` → `ingestion_status`
(closes U4-jargon; supersedes feature_027's name-freeze note in
`rag_v2_tools.py:191-197` — a conscious, user-directed tradeoff).

## Rename blast radius (pre-measured)

- src: `rag_v2_tools.py` (22 mentions), `rag_v2_agent_service.py` (5, incl. 2 prompt sites), `rag_v2_retriever.py` (1 docstring)
- tests: `test_rag_v2_retrieval_tool.py` (11), `test_rag_v2_console_repl_regression.py` (8)
- No other consumers (v2 is console-only; v1 tree untouched).

## Existing seams to reuse (no new infrastructure)

- `RagV2Provider.get_repositories()` / `.get_repository(id)` (`rag_v2_provider.py:18-35`) → `/repos`, `/use <id>`.
- Sub-controllers' thin `ingest_url/ingest_path` (`rag_v2_web_ingestion_controller.py:20-23` et al.) → direct `/ingest <kind> <target>` bypassing sub-screen prompts.
- `RagV2AgentService.reset_conversation()` (`rag_v2_agent_service.py:178-181`) → `/reset`.
- `RagV2MainController.get_rag_state()` (`rag_v2_controller.py:275-298`) → `/status`.
- Interactive picker (`select_repository`) + prompt-create (`create_repository`) stay as the no-arg fallbacks of `/use` / `/create`.
