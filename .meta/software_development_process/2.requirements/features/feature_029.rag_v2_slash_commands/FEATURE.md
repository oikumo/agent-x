# Feature 029: Rag_V2 Slash Commands

> **Status:** [x] Done (2026-08-16)
> **Created:** 2026-08-16
> **WORK.md task:** feature_029.rag_v2_slash_commands

---

## Summary

The feature_027 console RAG v2 REPL is functional but ambiguous: the numeric menu is
not a mode switch (`[3] chat` only primes the agent), menu keys collide with real
questions, there is no deterministic command surface, and retrieval happens invisibly
under the jargon name `rag_search`. This feature reworks the REPL to a hybrid
slash-command grammar (bare text = chat; `/help /search /repos /use /create /ingest
/status /reset /quit` = deterministic local commands), surfaces tool activity during
streaming (`» search:` / `» analyst:` lines via the existing `on_tool_call` /
`on_tool_result` callbacks), and renames the tools to `search_documents` /
`ingestion_status` across code, prompts, and test pins.

## Scope (one sentence — what "done" looks like)

The `(rag-v2)` REPL dispatches `/`-prefixed commands to deterministic controller
actions and bare text to chat, prints tool-activity lines while the agent retrieves
and delegates, and no `rag_search`/`rag_ingest_status` names remain in src/ or tests/.

## Task type

major_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_029.rag_v2_slash_commands/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_029.rag_v2_slash_commands/analysis_001_console_ux_gaps.md` | [x] |
| Design | Design doc | `4.design/features/feature_029.rag_v2_slash_commands/design_001_slash_command_grammar.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_029.rag_v2_slash_commands/` | [x] (TDD log folded into test report) |
| Testing | Test report | `6.testing/features/feature_029.rag_v2_slash_commands/test_report.md` | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
