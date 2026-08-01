# Feature 024: No TUI Full Features

> **Status:** [ ] Not started  
> **Created:** 2026-07-26  
> **WORK.md task:** feature_001.session_user_objectives_driven_by_Petri_Net (no direct match — new feature)

---

## Summary
Enable console (non-TUI) mode to access **all** TUI features — ReAct agent, Coding agent, Models selector, Advanced Agent, Fast Agent — via CLI menus and commands with full parity to TUI keyboard shortcuts and screen navigation. Currently only Main, Chat, and RAG work in console mode; the agentic and advanced screens are TUI-only.

## Scope (one sentence — what "done" looks like)
`agentx --no-tui` (or running without a TTY) provides interactive console menus to launch ReAct, Coding, Models, Agent, and Fast Agent screens, each with streaming output, command input, and full agent capabilities identical to their TUI counterparts.

## Task type
major_feature

---

## Phase Artifacts (traceability)

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `4.design/features/feature_024.no_tui_full_features/use_case.md` | [x] |
| Analysis | Analysis doc | `4.design/features/feature_024.no_tui_full_features/analysis_001_console_gap.md` | [x] |
| Design | Design doc | `4.design/features/feature_024.no_tui_full_features/design_001_console_parity.md` | [x] |
| Design | Operation specs | `4.design/features/feature_024.no_tui_full_features/operation_spec_001_console_commands.md` | [x] |
| Implementation | Impl notes | `5.implementation/features/feature_024.no_tui_full_features/` | [ ] |
| Testing | Test report | `6.testing/features/feature_024.no_tui_full_features/` | [ ] |

**Naming convention (enforced by `new_feature.py`):** phase docs are `analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic. Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.