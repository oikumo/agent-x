# Feature 025: Coding Context Window Optimization

> **Status:** [~] In progress
> **Created:** 2026-08-08
> **WORK.md task:** feature_025.coding_context_window_optimization

---

## Summary

The console coding module (delivered under feature_024 console parity) reaches the model's context window too quickly because every `file_read` / `file_search` / `file_list` tool result accumulates verbatim in the LangGraph checkpointer history with no compression or offloading. This feature wires the LangChain deepagents full stack (`create_deep_agent` with `FilesystemMiddleware`, `SummarizationMiddleware`, `MemoryMiddleware`, `SkillsMiddleware` and an on-demand `compact_conversation` tool) into `CodingAgentService` so multi-file coding sessions stay inside a single context window — large tool outputs are offloaded to a virtual filesystem, older turns are auto-summarized at 85% of `max_input_tokens`, skills are progressively disclosed, and an `AGENTS.md`-style memory file is always loaded.

## Scope (one sentence — what "done" looks like)

`CodingAgentService` constructs its agent via `create_deep_agent` with the full middleware stack, large tool outputs are offloaded instead of bloating history, conversations that would overflow the window are auto-summarized (and recoverable via `ContextOverflowError` retry), all existing public methods (`thread_id`, `is_running`, `cancel`, `get_history`, `reset_conversation`, `stream_agent`) remain API-compatible, the existing MVC pin (`test_coding_mvc.py`) still passes, and a new `tests/features/feature_025.coding_context_window_optimization/` suite is green.

## Task type

major_feature

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_025.coding_context_window_optimization/` | [x] |
| Analysis | Analysis doc | `3.analysis/features/feature_025.coding_context_window_optimization/analysis_001_*.md` | [ ] (folded into design_001 — context-engineering analysis is in design) |
| Design | Design doc | `4.design/features/feature_025.coding_context_window_optimization/design_001_deepagent_context_optimization.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_025.coding_context_window_optimization/` | [ ] |
| Testing | Test report | `6.testing/features/feature_025.coding_context_window_optimization/` | [ ] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
