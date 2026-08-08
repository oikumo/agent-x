# PROJECT: workflows

> Status: **draft v1 — purpose only**. Scope, vision, architecture, and tasks pending.

---

## Summary

Project **workflows** — a system for handling **user-triggered workflows**: reusable, human-authored operational procedures that the coding agent executes on demand. 
The workflow definitions live in `.workflows/` as self-contained markdown documents; 
this project gives that catalog a purpose, a structure, and a clear contract between the user (who triggers) and the agent (who executes).

---

## Purpose (draft v1)

### What this project is

The **workflows** project owns the `.workflows/` directory — a catalog of operational playbooks the human user can trigger. Each workflow is a natural-language recipe: a one-line problem statement, a set of rules, and a numbered execution strategy with a mandatory user-approval gate. When the user says "feature X doesn't work, fix it" or "pause my work for resume later", the agent loads the corresponding file and follows its steps.

Today that catalog exists but is **informal**: a de-facto shape repeated by hand across four markdown files, an empty root `META.md`, an empty `app_knowledge_base/loops/` stub, path typos, and no runtime to discover or dispatch workflows. The agent picks the right file only because a human pastes its name into chat.

This project's purpose is to turn that informal catalog into a **defined system**: a manifest, an authoring schema, naming conventions, and a clear integration with the harness so the agent knows how to discover a workflow, how to trigger it, and how to decide whether the OMT gates apply.

### What a workflow is (concept)

A workflow is **not** executable orchestration (not a LangGraph state machine, not a Python pipeline). It is a **triggered procedure**:

- **Trigger** — the user invokes a workflow by name or by describing a situation the workflow covers.
- **Recipe** — a markdown document states the problem, the rules, and a numbered strategy the agent executes step by step.
- **Approval gate** — every multi-step workflow stops mid-flow to ask the user which proposed alternative to apply; workflows never auto-execute a fix without explicit user approval.
- **Result** — the agent records what it did in a sandbox or project artifact, so the workflow is resumable and auditable.

### What this project should establish

1. **A manifest and structure for `.workflows/`** — fill the empty `META.md` root so the catalog describes itself: what `.workflows/` is, how subjects (`agentx/`, `meta_harness/`, `app_knowledge_base/`) namespace the catalog, the distinction between `loops/` (repeatable procedures) and top-level `.md` (one-shot tasks), and the file schema every workflow follows.
2. **An authoring schema** — formalize the de-facto shape already in use (problem line → `# Rules` → `# <Strategy>`) into a reusable template, so new workflows are consistent and discoverable rather than hand-imitated.
3. **A discovery and trigger contract** — define how the user triggers a workflow, how the agent finds the right file without a human pasting its name, and how the workflow result is recorded back to the sandbox/project artifacts (resuming the inconsistent path conventions today).
4. **A clear stance on OMT gates** — each workflow already declares whether it follows OMT methodology or overrides it. This project should make that declaration first-class and explicit, so a triggered workflow knows up front whether `omt_phase` / `g.kb` / think-gates apply to its execution.
5. **Resolution of the current open gaps** — the empty `app_knowledge_base/loops/` stub, the `consitency_enforcement` typo, and the inconsistent sandbox-output conventions (`./sandbox/feature_*.md` flat vs `./sandbox/consistency_enforcement/round_*.md` in a folder).

### What this project is **not**

- Not a workflow **runtime engine** (no DAG executor, no event bus) — workflows are agent-read procedures, not machine-parsed graphs.
- Not a replacement for OMT — workflows sit *above* OMT and decide when to invoke it; several workflows explicitly opt out.
- Not a new source-code module — the workflow definitions themselves are markdown, not Python in `src/`. (A discovery/dispatch helper *may* emerge as code, but that is a later design decision, not the purpose.)

### Recurring principles observed (to be preserved)

Every existing workflow converges on the same five principles — the project should treat these as invariants:

- **Human approval is mandatory** — no workflow auto-applies a fix; the user picks the alternative.
- **`omt_think` is always used** to embed knowledge in source — even when the workflow overrides OMT methodology.
- **Automated unit tests with mocks** are the preferred verification tool.
- **Sub-agents** are preferred for parallel analysis whenever useful.
- **Future agent token consumption** is the primary cost to minimize.

---

## Scope & success criteria (v1 — locked from sess decisions)

### In scope (this iteration)

The workflows project delivers the **definition layer** for the `.workflows/` catalog. Concretely, this iteration owns five artifacts, **all markdown**:

1. **`.workflows/META.md` (root manifest)** — fill the empty file so the catalog describes itself: what `.workflows/` is, how subjects (`agentx/`, `meta_harness/`, `app_knowledge_base/`) namespace the catalog, the `loops/` (repeatable) vs top-level `.md` (one-shot) split, the file schema, and the trigger contract. This is the entry point the agent reads first on every trigger.
2. **Per-subject `META.md`** — one in each of `agentx/`, `meta_harness/`, `app_knowledge_base/` so the agent can scope a read to one subject instead of the whole catalog when the trigger is clearly namespaced.
3. **Authoring schema + template** — formalize the de-facto shape already in use (problem line → `# Rules` → `# <Strategy>` → optional `# Result`) into a reusable template the user can copy; documented in root `META.md` and enforced only by convention (no parser). Includes the **per-workflow output-path declaration** — each workflow's schema declares its own sandbox-output pattern (flat `./sandbox/<workflow>_<NNN>_<desc>.md` or nested `./sandbox/<workflow>/<NNN>_<desc>.md`), recorded in the manifest.
4. **Discovery & trigger contract** — define (in prose, in root `META.md`) how the user triggers a workflow and how the agent finds the right file: **the agent reads `.workflows/META.md` + the relevant subject `META.md` each trigger and reasons a match from the problem lines**. No index file, no parser, no `src/` code. The contract records the read-order and the human-approval gate as the agent's mandatory procedure.
5. **Resolution of the open gaps** listed in Purpose §5:
   - Fill or remove the empty `app_knowledge_base/loops/` stub (decide intent: populate with a first workflow, or delete the directory and drop it from the subject list in root `META.md`).
   - Fix the `consitency_enforcement` typo in `consistency_enforcement.md` strategy step 3 (path says `./sandbox/consitency_enforcement/`, misspelled; rewrite to match the per-workflow-declared output-path convention).
   - Bring the one-line-only workflow (`pause_dev_for_resume_later.md`) up to the schema — add `# Rules` + `# <Strategy>` consistent with the other loops, or explicitly mark it one-shot in the manifest.

### Out of scope (this iteration — explicit non-goals)

- **No `src/` code** — no discovery helper, no parser, no `omt_workflow` tool, no `.opencode/` plugin. A discovery helper *may* emerge as a later project; this iteration delivers the markdown contract such a helper would consume, but does not build the helper.
- **No harness integration** — workflows sit above the harness; this iteration does not modify `META_HARNESS.omt`, `AGENTS.md`, or the enforcer. The existing `omt_phase` / `g.kb` / think-gates continue to apply (or not) per each workflow's own `# Rules` declaration.
- **No machine-parseable gate-stance field** — the OMT-vs-override declaration stays **informal, in `# Rules` prose** (line 1, as today). The manifest does NOT add a `gates:` field; the agent reads the rules to learn the stance. (A first-class field is a documented future option, not this iteration.)
- **No manifest index file** — discovery is "agent reads the catalog each trigger", so there is no `.workflows/manifest.json`-style index to maintain. Root + subject `META.md` IS the manifest, in markdown.
- **No new workflows authored** — this iteration fixes the catalog's *definition*; authoring new workflow content beyond bringing the gap-files up to schema is out of scope.
- **No workflow runtime** — reaffirmed from Purpose: no DAG executor, no event bus. Workflows are agent-read procedures.

### Success criteria

The iteration is done when **all six** hold:

| # | Criterion | Verified by |
|---|---|---|
| S1 | `.workflows/META.md` is non-empty and documents: catalog purpose, subject namespaces, `loops/` vs top-level split, file schema, trigger contract (read-order + approval gate), per-workflow output-path declaration convention. | Read the file against a checklist derived from this Scope section. |
| S2 | Each subject dir (`agentx/`, `meta_harness/`, `app_knowledge_base/`) has a non-empty `META.md` listing the workflows in that subject with name, one-line purpose, trigger keywords, and the workflow's sandbox-output-path pattern. | Read the three files. |
| S3 | An authoring template exists (either as a `TEMPLATE.md` in `.workflows/` or a fenced block in root `META.md`) showing the problem → `# Rules` → `# <Strategy>` → optional `# Result` shape with the per-workflow output-path field filled. | Copy the template, confirm a new workflow could be authored by filling it. |
| S4 | The three open gaps are resolved: (a) `app_knowledge_base/loops/` is either populated with a first workflow or deleted + dropped from the subject list; (b) the `consitency_enforcement` typo is fixed and the path follows the per-workflow-declared convention; (c) `pause_dev_for_resume_later.md` is brought up to the schema (Rules + Strategy) or marked one-shot in the manifest. | Diff the three sites; grep for the misspelling returns zero hits. |
| S5 | The discovery & trigger contract in root `META.md` is sufficient that **a fresh agent session, given only a natural-language trigger** (e.g. "feature X doesn't work, fix it" / "pause my work for resume later"), can identify the correct `.workflows/` file by reading root `META.md` + the matched subject `META.md` — without a human pasting the filename. | Manual dry-run: simulate two distinct triggers against the manifest, confirm the right file is selected both times. |
| S6 | No `src/`, `.opencode/`, or `META_HARNESS.omt` files were modified by this iteration. | `git diff --stat` shows changes only under `.workflows/` and `.projects/meta/workflows/`. |

### Boundaries restated (one line each)

- **What changes:** `.workflows/` (markdown only) + this PROJECT.md.
- **What does not change:** `src/`, `.opencode/`, `.meta/`, harness, enforcer, gate-stance field, manifest-index file.
- **What is deferred (future projects, not this one):** discovery helper code; first-class `gates:` field; harness integration / `omt_workflow` tool; new workflow content beyond gap-fixes.

---

## Status

- [x] Purpose (draft v1) — this section
- [x] Scope & success criteria (v1) — locked from sess decisions (definition-only, agent-reads-catalog, informal gates, per-workflow output path)
- [ ] Vision / goals — pending (deferred — not required for the definition-layer iteration; future project may draft a vision section)
- [ ] Architecture — pending (deferred — the definition layer's "architecture" is the manifest's discovery contract; a richer architecture section is a future-project concern if/when a discovery helper or `omt_workflow` tool is proposed)
- [x] Tasks — definition-layer iteration executed (see below)

---

## Tasks (definition-layer iteration — DONE 2026-08-08)

| # | Task | Status | Artifact |
|---|---|---|---|
| T1 | Fill `.workflows/META.md` root manifest | [x] DONE | `.workflows/META.md` (catalog purpose, subject namespaces, `loops/` vs top-level split, file schema, trigger contract §4, output-path declaration §5, authoring template §6, recurring invariants §7) |
| T2 | Create per-subject `META.md` (agentx) | [x] DONE | `.workflows/agentx/META.md` |
| T3 | Create per-subject `META.md` (meta_harness) | [x] DONE | `.workflows/meta_harness/META.md` |
| T4 | Create per-subject `META.md` (app_knowledge_base) | [x] DONE | `.workflows/app_knowledge_base/META.md` (declares subject reserved/future, `loops/` is an empty reserved stub) |
| T5 | Gap-S4a resolve empty `app_knowledge_base/loops/` stub | [x] DONE | Decision: Option B — kept the directory, declared it future/reserved in `.workflows/app_knowledge_base/META.md` |
| T6 | Gap-S4b fix the `consitency_enforcement` typo | [x] DONE | `.workflows/agentx/loops/consistency_enforcement.md` step 3 + step 6 rewritten to `./sandbox/consistency_enforcement/round_<NNN>_<BRIEF_DESCRIPTION>.md`; grep for the misspelling returns zero hits across `.workflows/` |
| T7 | Gap-S4c `pause_dev_for_resume_later.md` up to schema | [x] DONE | `.workflows/meta_harness/pause_dev_for_resume_later.md` now has `# Rules` + `# Pause strategy` (6 steps, approval gate at step 4) + optional `# Result`; type one-shot stays declared in `.workflows/meta_harness/META.md` |
| T8 | Authoring template delivered | [x] DONE | `.workflows/META.md` §6 (fenced template + authoring checklist) |
| T9 | Discovery & trigger contract delivered | [x] DONE | `.workflows/META.md` §4 (read order, match procedure, approval gate hard invariant, OMT gate stance) |
| T10 | Verify S5 by manual dry-run | [x] DONE | Two distinct natural-language triggers ("feature X doesn't work, fix it" → `agentx/loops/feature_fix.md`; "pause my work for resume later" → `meta_harness/pause_dev_for_resume_later.md`) — both land on the right file via the two-level read with no human pasting the filename |
| T11 | Verify S6 by `git diff --stat` | [x] DONE | All changes are under `.workflows/` (3 modified + 3 newly-created META files) — no `src/`, `.opencode/`, `.meta/`, `META_HARNESS.omt`, or `AGENTS.md` modifications |

### Success criteria outcome

| # | Success criterion | Result |
|---|---|---|
| S1 | `.workflows/META.md` is non-empty and documents catalog purpose, subject namespaces, `loops/` vs top-level split, file schema, trigger contract (read-order + approval gate), per-workflow output-path declaration convention | ✅ `.workflows/META.md` — 8 sections covering all required content |
| S2 | Each subject dir has non-empty `META.md` listing workflows with name, purpose, trigger keywords, output-path pattern | ✅ Three subject META.md files (agentx: 2 loops, meta_harness: 2 loops + 1 one-shot, app_knowledge_base: future/reserved with zero workflows yet declared) |
| S3 | Authoring template exists showing the problem → `# Rules` → `# <Strategy>` → optional `# Result` shape with the per-workflow output-path field filled | ✅ `.workflows/META.md` §6 — fenced template that can be copied to author a new workflow |
| S4 | Three open gaps resolved | ✅ (a) `app_knowledge_base/loops/` kept as empty reserved stub, declared future in its SUBJECT META.md; (b) the misspelled path is fixed and the path follows the per-workflow-declared nested-round convention; (c) `pause_dev_for_resume_later.md` brought up to the full schema (Rules + Strategy + Result); `consitency` grep returns zero hits |
| S5 | A fresh agent session given only a natural-language trigger can identify the correct `.workflows/` file by reading root + matched subject META.md, without a human pasting the filename | ✅ Manual dry-run with two distinct triggers (one feature-fix, one session-pause) — both correctly selected |
| S6 | No `src/`, `.opencode/`, or `META_HARNESS.omt` files modified | ✅ `git diff --stat` shows changes only under `.workflows/`; untracked additions all under `.workflows/` |

### Out-of-scope reminders (deferred to future projects, not done)

- Discovery helper code in `src/` — this iteration delivered the markdown contract such a helper would consume, but did not build the helper.
- First-class machine-parseable `gates:` field — the OMT-vs-override declaration stays informal, in `# Rules` prose line 1.
- Harness integration (modifying `META_HARNESS.omt`, `AGENTS.md`, enforcer, adding an `omt_workflow` tool) — workflows sit above the harness; this iteration did not modify the harness.
- New workflow content beyond the gap-fixes — the catalog's *definition* was the deliverable; authoring new workflows is a future project.
- Workflow runtime (DAG executor, event bus) — reaffirmed: workflows are agent-read procedures.
