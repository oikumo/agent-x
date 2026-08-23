# CURRENT_STATE: petri_net_library

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-23 (auto — feature_031.petri_net_library Done)

- shipped: major_feature · test report @ 6.testing/features/feature_031.petri_net_library/test_report.md
- logged by omt_complete; expand by hand if resume needs more.

### Session detail (expanded by hand)

- **v1 SHIPPED** — the full locked v1.1 scope landed in one session: `src/agentx/model/petri_net/{__init__.py (docstring-only), errors.py, model.py, analysis.py, coverability.py}` + `tests/model/petri_net/{test_model,test_analysis,test_coverability}.py` (June placeholder deleted). 3 TDD cycles (testlist 26 behaviors → red→green→refactor at same file-level node), closed via `omt_tdd{op:done}` (all checklist green), 99 canonical tests + sentinel re-export, full suite 1577 passed, 0 regressions vs baseline.
- **Prior phases (2026-08-22, prev session):** feature scaffolded via `new_feature.py --project petri_net_library`; analysis_001 (anchors A1–A12, findings F1–F10) and design_001 + operation_spec_001 produced; Programming declared but no code written before session end (only a TDD_BOOTSTRAP skip + phase records in the ledger).
- **Build decisions worth remembering:** (1) deferred imports in ALL test files — a top-level import of the cycle's not-yet-existing module aborts collection (pytest exit 2) and `cmd_start` rejects it as a red; (2) placeholder deleted at bootstrap (two-hats blocks tests/ during green hat); (3) SCC restricted to the graph vertex set (no phantom components from truncated graphs); (4) empty-net `is_live` = `(True, True, 1)` per F1/§31; (5) sentinel + conftest fixture bridge for the `tests/features/<feature>/` omt_complete pattern.
- **Project status:** the library objective is COMPLETE for v1. feature_001 (the future consumer) remains a separate feature; v2 backlog (coverability Karp–Miller, siphons/traps, home markings, simulator, DOT/JSON, optimization) unscheduled.

---


## 2026-08-22 (iter 8 — scope LOCKED v1.1; feature scaffolding underway)

### Done

- **Scope LOCKED v1.1** — user said "execute the project" (the single-action lock approval). All Lock sign-off checklist boxes ticked in `PROJECT.md`: v1/v2 section split, D7 edge-case policy, D1 slug policy approved as drafted; `PetriNetAnalyzer` binding resolved to **constructor binding** `PetriNetAnalyzer(net)`; D11 feature_001 runtime-mutation need resolved — **add-only is sufficient** (FEATURE.md: structure updates on `USER_OBJECTIVES.md` CRC change ⇒ rebuild a fresh `PetriNet` instance; in-place removal is a non-breaking v2 addition if ever needed). PROJECT.md header + Scope section flipped to locked v1.1; iter-8 log entry added.
- **D11 evidence check** — read `feature_001.../FEATURE.md` (10 lines): "The Petri Net structure must be updated if the crc of the file changes" — no in-place-removal requirement; rebuild strategy satisfies it.

### In progress

- **Feature scaffolding + phase pipeline** — `new_feature.py "petri net library" --type major_feature --project petri_net_library` → Analysis (requirement-anchor extraction via parallel sub-agents) → Design → TDD Programming → Testing.

---

## 2026-08-22 (iter 7 — review fixes applied; no feature work)

### Done

- **Applied the full 2026-08-22 project-home review fix set** (all findings) to `PROJECT.md` + `CURRENT_STATE.md`: stale feature slug (030 taken by `feature_030.project_lifecycle` → number auto-assigned by `new_feature.py` at scaffold, next free 031; all refs updated), iter-3 lock overclaim corrected (only D4 is locked), session-log backfill (iter-2 + iter-4 blocks added; iter-0 ≡ PROJECT.md iter-1 offset noted), `--project petri_net_library` on all scaffold commands, `__init__.py` aligned to the verified model/ convention (docstring-only, no re-exports), section-map gaps closed (§35 v1, §26 v2, §36 split, §41 principle), iter-5 lettering H/I/L/M disposition recorded (not adopted, no outstanding action), TA format normalized, PROJECT.md header bumped to iter 7. No `src/`, no feature, no `omt_phase` — pure project-home markdown.

### Next

- **User ticks the Lock sign-off checklist** → flip Status to locked (v1.1) → (on user go) scaffold via `uv run scripts/omt/new_feature.py "petri net library" --type major_feature --project petri_net_library` (feature number auto-assigned, currently 031) and declare the first phase.

---

## 2026-08-22 (iter 6 — review patch applied; no feature work)

### Done

- **Applied the review patch to `PROJECT.md`** (findings a–e) per user "apply patch": (a) named excluded DoD §40-18 = Coverability for unbounded nets (v2, already out of scope via D5 + `coverability.py` stub); (b) pinned `max_states` as required (no implicit default) in D9 and added model-API semantics — `reset()` restores `M0`, `fire_marking(M,t)` raises `TransitionNotEnabledError` when disabled — in In-scope #1; (c) added a per-function test-coverage matrix (happy + "unknown" for every analysis fn) to In-scope #5; (d) added feature_001 runtime-mutation cross-ref to D11 (confirm add-only vs add+remove before lock); (e) added a "Lock sign-off checklist" (single-action approval) + "Design-phase must-pin checklist". No `src/`, no feature, no `omt_phase` — pure project-home markdown.
- **Scope & decisions remain draft, awaiting the lock sign-off** (new checklist makes approval a single action).

### Next

- **User ticks the Lock sign-off checklist** → flip Status to locked (v1.1) → (on user go) scaffold the feature via `new_feature.py` (number auto-assigned, see PROJECT.md D1) and declare the first phase.
- backfill baseline: no linked features (draft); log continuity starts here

---

## 2026-08-22 (iter 5 — review-driven doc fixes; no feature work)

### Done

- **Applied the review findings to `PROJECT.md`** (N, A, C, D, E, F, G, B, J, K) + iteration-log entry; and updated `CURRENT_STATE.md` iter-0 decision references (D1–D11, D4 locked). No `src/`, no feature, no `omt_phase` — pure project-home markdown.
- **Scope & decisions remain draft, awaiting user approval** — these edits only sharpen/derisk the draft; they do not lock it.

### Next

- **User approval of scope & decisions (D1–D11)** — then (on user go) scaffold the feature via `new_feature.py` (number auto-assigned, see PROJECT.md D1) and declare the first phase.

---

## 2026-08-16 (iter 4 — anchor-doc second pass; no feature work)

### Done

- **Second feasibility/simplicity pass on the requirement doc** (doc-only; block backfilled in iter 7): `nullspace()` zero-row `n_cols` fix (degenerate-net invariants), `_coprime_int_vector` sign normalization, `marking_to_dict` non-negativity validation, §11/§35 module-tree cleanup, §8.5 diagram removed, §9 `add_input`/`add_output` arg-order gotcha, §31 duplication note, §38 degenerate-net edge cases. Full list: PROJECT.md iter 4.

### Next

- **User approval of scope & decisions (D1–D11)** — unchanged.

---

## 2026-08-16 (iter 3 — requirement-doc feasibility review; no feature work)

### Done

- **Reviewed `.meta/doc/petri_nets/petri_net_python_coding_agents.md`** for feasibility & simplicity per user request ("improve the project itself, do not implement anything more") and improved the doc directly. Highlights: §30 example nets now buildable (explicit arcs), §18/§19 pure-Python exact-nullspace reference implementation (D4 fully specified), §20–§22 liveness/home return `AnalysisResult` (doc §27 rule restored), §32 liveness signatures pinned, §28 `max_states` semantics pinned, empty-net policy decided (§38), v1/v2 section map added, module layouts aligned to v1. Full list in PROJECT.md iter 3.
- **PROJECT.md updated**: D5 clarified (liveness returns `AnalysisResult`, not bare bool), in-scope item 2 wording, iter-3 log entry.
- **No implementation, no feature scaffolding, no `src/` edits** — per standing user constraint.

### In progress / Blocked

- _(nothing — still awaiting user approval of scope & decisions)_

### Next

- **User approval of scope & decisions (D1–D11)** — unchanged; the anchor doc is now internally consistent with the project decisions (D4 locked: pure-Python nullspace, no sympy; D5–D11 remain **draft**, pending approval — corrected iter 7: this entry previously mislabeled D5/D7/D8/D9 as locked).

---

## 2026-08-16 (iter 2 — scope refinement; no feature work)

### Done

- **Scope refinement for feasibility & simplicity** (block backfilled in iter 7): v1-only extraction from the 41-section doc; D4 locked to pure-Python rational nullspace (zero deps); `simulator.py`/`graph.py` removed from v1; `coverability.py` stub-only; `max_states`-only limits; convenience wrappers dropped; explicit empty-net policy; "unknown"-case test matrix; decisions updated to D1–D11. Full list: PROJECT.md iter 2.

### Next

- **User approval of scope & decisions (D1–D11)** — unchanged.

---

## 2026-08-16 (iter 0 — project home created; no feature work · ≡ PROJECT.md iteration-log iter 1)

### Done

- **Project home created** at `.projects/meta/petri_net_library/` per user request: "create a new project for a petri net library for agentx, follow this doc as a requirement starting point" — with explicit constraints "do not implement anything, just create the project" and "project, no feature yet".
- **PROJECT.md v1 written** (canonical design doc). Requirement anchor = `.meta/doc/petri_nets/petri_net_python_coding_agents.md` (41 sections, read in full). Contains: Summary, Purpose (what/not/requirement anchor/recurring principles), Vision + standing principle + main objectives (draft), Scope & success criteria (**draft — explicitly NOT locked, awaiting user approval**), Status checklist, Out-of-scope reminders, Decisions log D1–D9 (draft), Iteration log, References.
- **CURRENT_STATE.md iter-0 created** (this file).

### Facts verified before writing

- Next free feature slot is **030** (`feature_029.rag_v2_slash_commands` is last in `2.requirements/features/`). *(True at iter-0; stale since 2026-08-22 — `feature_030.project_lifecycle` took 030; next free is 031. See PROJECT.md D1.)*
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
- After approval: lock scope in PROJECT.md (v1.1), then (only on user go) scaffold via `uv run scripts/omt/new_feature.py "petri net library" --type major_feature --project petri_net_library` (feature number auto-assigned, see PROJECT.md D1) and declare the first phase.

### Notes / context

- The requirement doc's Definition of Done (§40, items 1–19) and minimum analysis toolkit (§36) are encoded as the success-criteria draft — they are the acceptance contract when implementation starts.
- Existing placeholder test `tests/model/petri_net/test_petri_net.py` is not touched by this project home; its fate (replace with real tests) belongs to the future feature phases.