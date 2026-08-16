# CURRENT_STATE: petri_net_library

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-16 (iter 0 — project home created; no feature work)

### Done

- **Project home created** at `.projects/meta/petri_net_library/` per user request: "create a new project for a petri net library for agentx, follow this doc as a requirement starting point" — with explicit constraints "do not implement anything, just create the project" and "project, no feature yet".
- **PROJECT.md v1 written** (canonical design doc). Requirement anchor = `.meta/doc/petri_nets/petri_net_python_coding_agents.md` (41 sections, read in full). Contains: Summary, Purpose (what/not/requirement anchor/recurring principles), Vision + standing principle + main objectives (draft), Scope & success criteria (**draft — explicitly NOT locked, awaiting user approval**), Status checklist, Out-of-scope reminders, Decisions log D1–D9 (draft), Iteration log, References.
- **CURRENT_STATE.md iter-0 created** (this file).

### Facts verified before writing

- Next free feature slot is **030** (`feature_029.rag_v2_slash_commands` is last in `2.requirements/features/`).
- `src/agentx/model/petri_net/` **does not exist**; `tests/model/petri_net/test_petri_net.py` exists as a June placeholder stub (`self.assertTrue(True)`) — the library's real tests will replace it.
- `src/agentx/model/` uses flat packages with empty `__init__.py` (e.g. `session/`, `rag_v2/`).
- `pyproject.toml` has `numpy>=2.5.1`, **no sympy** — drives open decision D4 (exact arithmetic for invariants: add sympy vs pure-Python nullspace).

### Locked decisions (do not re-litigate without new evidence)

- **(user) Project only, no feature yet** — no `new_feature.py` scaffolding, no `omt_phase`, no `src/` edits, no tests.
- **(draft, unconfirmed)** D1–D9 in PROJECT.md — all pending user approval/revision, especially the scope boundary and D4 (sympy dependency).

### In progress / Blocked

- _(nothing — project definition delivered, awaiting user response)_

### Next

- **User approval of scope & decisions (D1–D9)** — approve as-is or revise (especially: scope boundary, sympy-vs-pure-Python for invariants, edge-case policy D7).
- After approval: lock scope in PROJECT.md (v1.1), then (only on user go) scaffold `feature_030.petri_net_library` via `uv run scripts/omt/new_feature.py "petri net library" --type major_feature` and declare the first phase.

### Notes / context

- The requirement doc's Definition of Done (§40, items 1–19) and minimum analysis toolkit (§36) are encoded as the success-criteria draft — they are the acceptance contract when implementation starts.
- Existing placeholder test `tests/model/petri_net/test_petri_net.py` is not touched by this project home; its fate (replace with real tests) belongs to the future feature phases.