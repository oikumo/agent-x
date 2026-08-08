# .workflows/meta_harness/ — META Harness Workflows

> Subject manifest for workflows that operate on the **OMT++ META harness** itself — the methodology tooling, the harness's own evolution, and session-level housekeeping like pause/resume. See `../META.md` §4 for the full discovery & trigger contract.

---

## Subject scope

This subject covers workflows whose `# <Strategy>` operates on the META harness artifacts (`.meta/`, `META_HARNESS.omt`, `AGENTS.md`, the enforcer, `omt_*` tools) and on session-level work state (`WORK.md`, `.sandbox/meta/`). Two recurring loops live under `loops/`, and one **top-level one-shot** (`pause_dev_for_resume_later.md`) lives at the subject root.

OMT gate stance varies per workflow — read each workflow's `# Rules` line 1 before invoking. The meta harness evolution loop explicitly opts out of OMT methodology in its own `# Rules` line 1; the project loop also opts out; the pause/resume one-shot does not modify `src/` so the harness gates do not come into play.

---

## Loops

| Workflow | Purpose | Trigger keywords | Output path | OMT gate stance |
|---|---|---|---|---|
| `loops/meta_harness_evolution.md` | Find and apply improvement options for the META harness itself — fresh start each iteration, focus on future agent token consumption, prefer machine-readable artifacts (DSL for META HARNESS when possible). | "harness", "improve", "improvement", "evolution", "optimize the harness", "the methodology could be faster", "META HARNESS" | nested — `./sandbox/meta/improvement<NNN>/<artifact>.md` (CURRENT_STATE.md, IMPROVEMENT_OPTIONS.md, then OUTCOME.md/EXECUTION.md written post-approval) | **do not follow** omt methodology |
| `loops/meta_harness_project.md` | Run a structured project on the META harness with explicit phase discipline (project idea → alternatives → user approval → plan → execution). | "project", "new project", "structured project", "plan a harness project" | nested — `.projects/meta/<project_id>/PROJECT.md` (the current project you are resuming lives here at `.projects/meta/workflows/PROJECT.md`) | **do not follow** omt methodology |

### How to pick between the two

Both loops talk about META HARNESS improvement, but:

- The **evolution** loop runs **fresh, no previous-iteration history** (`# Rules` line 1) — it is the "tune the harness right now" workflow for opportunistic improvements. Use it when the user says "improve the harness" / "look for inefficiency" / "META HARNESS evolution".
- The **project** loop **does consider previous iterations history** (`# Rules` line 1) and explicitly produces a structured `PROJECT.md` artifact and a user-approved plan. Use it when the user says "new project", "structured project", "plan a project", or wants the multi-phase proposal-approve-execute flow.

---

## Top-level one-shots

| Workflow | Purpose | Trigger keywords | Output path | Type |
|---|---|---|---|---|
| `pause_dev_for_resume_later.md` | Pause the current in-progress development work so it can be resumed cleanly in a new opencode session — update `WORK.md`, save resumption artifacts, hand off. | "pause", "resume later", "stop for now", "I'm done for today", "save state", "session hand-off" | flat — `./sandbox/pause_<YYYY-MM-DD>.md` (resumption notes) | **one-shot** (follows the full schema — `# Rules` + `# Strategy` — even though it is single-pass; see the workflow's own file) |

### Why `pause_dev_for_resume_later.md` is one-shot

Pause is a **session housekeeping action**, not a recurring analysis loop — every invocation runs the same short pass (read `WORK.md`'s current task → write the resumption notes → update `WORK.md`'s DONE/`[~]` state). It lives at the subject root rather than under `loops/` to flag this. It was brought up to the full schema (`# Rules` + `# Strategy`) in the workflows-project iteration so its shape matches the other workflows, but its execution is single-pass.

---

## Notes for future maintainers

- All three meta_harness workflows honour the five recurring invariants in `../META.md` §7 — including the approval gate (mandatory) and `omt_think` (used in source where they touch it).
- The two loops opt out of OMT methodology (`# Rules` line 1: `Do not consider previous iterations history` / `Consider previous project iterations history`) because they operate on the harness from above — opting in would make the harness gate itself. They still use `omt_think` for any `src/` changes per invariant rule #2.
- To add a new meta_harness loop: copy the authoring template from `../META.md` §6, drop the file under `loops/`, and add a row to the Loops table. To add another one-shot, drop the file at the subject root and add a row to the Top-level one-shots table.
