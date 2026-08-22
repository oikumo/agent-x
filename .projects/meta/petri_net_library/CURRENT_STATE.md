# CURRENT_STATE: petri_net_library

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-22 (iter 6 — review patch applied; no feature work)

### Done

- **Applied the review patch to `PROJECT.md`** (findings a–e) per user "apply patch": (a) named excluded DoD §40-18 = Coverability for unbounded nets (v2, already out of scope via D5 + `coverability.py` stub); (b) pinned `max_states` as required (no implicit default) in D9 and added model-API semantics — `reset()` restores `M0`, `fire_marking(M,t)` raises `TransitionNotEnabledError` when disabled — in In-scope #1; (c) added a per-function test-coverage matrix (happy + "unknown" for every analysis fn) to In-scope #5; (d) added feature_001 runtime-mutation cross-ref to D11 (confirm add-only vs add+remove before lock); (e) added a "Lock sign-off checklist" (single-action approval) + "Design-phase must-pin checklist". No `src/`, no feature, no `omt_phase` — pure project-home markdown.
- **Scope & decisions remain draft, awaiting the lock sign-off** (new checklist makes approval a single action).

### Next

- **User ticks the Lock sign-off checklist** → flip Status to locked (v1.1) → (on user go) scaffold `feature_030.petri_net_library` and declare the first phase.
- backfill baseline: no linked features (draft); log continuity starts here

---

## 2026-08-22 (iter 5 — review-driven doc fixes; no feature work)

### Done

- **Applied the review findings to `PROJECT.md`** (N, A, C, D, E, F, G, B, J, K) + iteration-log entry; and updated `CURRENT_STATE.md` iter-0 decision references (D1–D11, D4 locked). No `src/`, no feature, no `omt_phase` — pure project-home markdown.
- **Scope & decisions remain draft, awaiting user approval** — these edits only sharpen/derisk the draft; they do not lock it.

### Next

- **User approval of scope & decisions (D1–D11)** — then (on user go) scaffold `feature_030.petri_net_library` and declare the first phase.

---

## 2026-08-16 (iter 3 — requirement-doc feasibility review; no feature work)

### Done

- **Reviewed `.meta/doc/petri_nets/petri_net_python_coding_agents.md`** for feasibility & simplicity per user request ("improve the project itself, do not implement anything more") and improved the doc directly. Highlights: §30 example nets now buildable (explicit arcs), §18/§19 pure-Python exact-nullspace reference implementation (D4 fully specified), §20–§22 liveness/home return `AnalysisResult` (doc §27 rule restored), §32 liveness signatures pinned, §28 `max_states` semantics pinned, empty-net policy decided (§38), v1/v2 section map added, module layouts aligned to v1. Full list in PROJECT.md iter 3.
- **PROJECT.md updated**: D5 clarified (liveness returns `AnalysisResult`, not bare bool), in-scope item 2 wording, iter-3 log entry.
- **No implementation, no feature scaffolding, no `src/` edits** — per standing user constraint.

### In progress / Blocked

- _(nothing — still awaiting user approval of scope & decisions)_

### Next

- **User approval of scope & decisions (D1–D11)** — unchanged; the anchor doc is now internally consistent with the locked project decisions (D4 locked: pure-Python nullspace, no sympy; D5/D7/D8/D9 also locked).

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
- **(draft, unconfirmed)** D1–D11 in PROJECT.md — all pending user approval/revision (D4 is already **locked**: pure-Python exact nullspace, no sympy; remaining draft items are the scope boundary, D7 edge-case policy, and D1 feature slug).

### In progress / Blocked

- _(nothing — project definition delivered, awaiting user response)_

### Next

- **User approval of scope & decisions (D1–D11)** — approve as-is or revise (especially: scope boundary and edge-case policy D7; note D4 is already locked to pure-Python exact nullspace with sympy rejected).
- After approval: lock scope in PROJECT.md (v1.1), then (only on user go) scaffold `feature_030.petri_net_library` via `uv run scripts/omt/new_feature.py "petri net library" --type major_feature` and declare the first phase.

### Notes / context

- The requirement doc's Definition of Done (§40, items 1–19) and minimum analysis toolkit (§36) are encoded as the success-criteria draft — they are the acceptance contract when implementation starts.
- Existing placeholder test `tests/model/petri_net/test_petri_net.py` is not touched by this project home; its fate (replace with real tests) belongs to the future feature phases.