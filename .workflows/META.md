# .workflows/ — Operational Workflow Catalog

> The catalog of human-authored triggered procedures the coding agent loads and executes on demand. Read this file first on every trigger — it is the manifest and the entry point.

---

## 1. What this catalog is

`.workflows/` is a **catalog of triggered procedures**, not a runtime engine and not machine-parsed graphs. Each workflow is a self-contained markdown document that states a problem, the rules the execution must obey, and a numbered strategy the agent follows step by step. The agent loads the file when the user triggers a workflow by name or by describing a situation the workflow covers, and follows its steps in order.

A workflow is **resumable and auditable**: every multi-step workflow writes what it did into a sandbox artifact under `./sandbox/`, so a later session can pick up the work or review what was decided. A workflow is also **approval-gated**: no multi-step workflow auto-applies a fix — at the proposed-alternatives step the agent stops and asks the user which alternative to perform.

Workflows sit *above* OMT methodology: each workflow declares in its own `# Rules` line 1 whether it follows the OMT harness (`omt_phase` / `g.kb` / think-gates) or overrides it. This catalog and its manifest do not enforce the stance — they make it first-class and discoverable so the agent knows up front which gates apply.

### What this catalog is NOT

- **Not a workflow runtime engine** — no DAG executor, no event bus, no Python module in `src/`. The catalog is symbol-discoverable markdown; the agent reads a file and walks its steps.
- **Not a replacement for OMT** — several workflows explicitly opt out of OMT in their `# Rules` line 1; the catalog just records the stance, it does not impose one.
- **Not a discovery helper** — there is no `omt_workflow` tool, no `.workflows/manifest.json` index, no parser. Discovery is "agent reads the manifest each trigger" (see §4). A discovery helper may emerge as a later project; this manifest is what that helper would consume.

---

## 2. Layout and namespaces

The catalog is namespaced by **subject** — the area of the codebase the workflow operates on. Each subject is a top-level directory.

```
.workflows/
├── META.md                      # THIS FILE — root manifest (read first)
├── agentx/                      # subject: the agentx application source
│   ├── META.md                  # subject manifest (read when trigger is agentx-scoped)
│   └── loops/
│       ├── consistency_enforcement.md
│       └── feature_fix.md
├── meta_harness/                # subject: the OMT++ harness itself
│   ├── META.md                  # subject manifest
│   ├── pause_dev_for_resume_later.md   # one-shot (top-level, not under loops/)
│   └── loops/
│       ├── meta_harness_evolution.md
│       └── meta_harness_project.md
└── app_knowledge_base/          # subject: the application knowledge base (ACTIVE — 1 loop)
    ├── META.md                  # subject manifest
    └── loops/
        └── akb_smart_population_and_update.md   # smart pop/update pass
```

### Subject list

| Subject | Path | State | Reads when the trigger is… |
|---|---|---|---|
| `agentx` | `.workflows/agentx/` | active — 2 workflows | about an agentx feature or the agentx application as a whole |
| `meta_harness` | `.workflows/meta_harness/` | active — 3 workflows (2 loops + 1 top-level one-shot) | about the OMT++ harness, harness development, or session pause/resume |
| `app_knowledge_base` | `.workflows/app_knowledge_base/` | **active** — 1 workflow (smart population / update loop; was `future` reserved-stub until 2026-08-08) | about the application knowledge base — populate, update, audit, re-tile, drift-fix, curate overlay `text`, fix `g.kb` consult-gate / `kb_compiler` / `kb_ast_extract` / `omt_kb_nav` behaviour |

### `loops/` vs top-level `.md`

- **`loops/<workflow>.md`** — **repeatable procedures.** A workflow that is invoked every time a class of situation recurs (a feature breaks, the harness needs improvement, consistency drifts). The file's `# <Strategy>` is a loop body: each invocation starts at step 1 and runs to the approval gate. Most workflows are loops.
- **Top-level `<workflow>.md` (no `loops/`)** — **one-shot / utility playbooks.** A workflow that is short, single-pass, or admin-shaped (e.g. pause-dev-for-resume-later is a session housekeeping action, not a recurring analysis loop). A top-level `.md` may still follow the full schema, but its Strategy may be a single short pass instead of an iterative procedure.

The split is **organizational, not behavioural** — the file schema in §3 applies to both. The marker that a workflow is a one-shot lives in its subject `META.md` (and optionally in its own `# Rules`), not in the directory layout.

---

## 3. File schema (the authoring contract)

Every workflow file follows the same de-facto shape. The shape is enforced only by **convention** (no parser, no linter) — but authoring new workflows against the template keeps the catalog consistent and lets the agent read any workflow the same way.

### 3.1 Required shape

A workflow file has, top to bottom:

```m центрarkdown
<problem statement>

# Rules
1. <OMT stance — line 1 is always: "Follow omt methodology" OR "Do not follow the omt methodology, focus on <X>">
2. <invariant rules — e.g. use omt_think to embed knowledge in source, unit tests with mocks, sub-agents for parallel analysis>
3. …
N. <rule N>

# <Strategy name>
1. <step 1 — typically: read the documentation/artifacts>
2. <step 2 — typically: understand the current implementation and find gaps>
3. <step 3 — typically: identify issues and propose fix alternatives in <output path>>
4. <step 4 — typically: ask the user which alternative to perform>   ← MANDATORY APPROVAL GATE
5. <step 5 — typically: execute the alternative chosen by the user>
6. <step 6 — typically: update the results in the same file as step 3>

# Result (optional)
<filled in after execution: what was done, what artifacts were created, what is left to resume>
```

### 3.2 Schema field reference

| Section | Required? | Notes |
|---|---|---|
| `<problem statement>` (top of file, before any heading) | **Required** | One to a few lines of prose stating the problem the workflow solves. The agent reads this first to decide if the trigger matches. |
| `# Rules` | **Required** (unless the workflow is explicitly marked one-shot in its subject `META.md` AND it has a single-line purpose; `pause_dev_for_resume_later.md` is brought up to the full schema, so it has `# Rules`). | A numbered list. **Line 1 is always the OMT stance** — either `Follow omt methodology` or `Do not follow the omt methodology, focus on <X>`. Lines 2+ are invariants the project treats as fixed: use `omt_think` to embed knowledge in source, write automated unit tests with mocks when possible, prefer sub-agents for parallel analysis, minimize future agent token consumption. |
| `# <Strategy name>` | **Required** (a workflow without a strategy cannot be executed). Heading is a free-form name; body is a numbered list of steps. Most strategies end at step 4 with an approval gate; some add execution (step 5) and result-recording (step 6). | See §3.3 for the contract every step list must honour. |
| `# Result` | Optional | Filled in after the workflow runs. Lets the workflow be resumable: a later session reads this to know what was already done. |

### 3.3 Strategy contract (the invariants every strategy honours)

Regardless of what an individual workflow's strategy is named or how many steps it has, every strategy list MUST honour these invariants:

- **Approval gate.** A multi-step strategy has at least one step whose action is *"Ask the user to select one of the proposed alternatives."* The agent does not execute the chosen alternative without the user's explicit go-ahead.
- **`omt_think` everywhere a feature exists.** Any workflow that touches source code embeds knowledge in the source itself via `omt_think` — even workflows that opt out of OMT methodology. This is invariant rule #2 in every existing workflow and is preserved here.
- **Write the output back to `.sandbox/`.** The strategy declares its **output-path pattern** (see §5). The proposals step writes to that path, the execute step performs the chosen alternative, and a results step updates the same file with what was done.
- **`# Result` if resumable.** If the workflow's effect is meant to survive the session (most are), the strategy ends with a results step that fills a `# Result` section in the same artifact, so a later session can resume.

---

## 4. Discovery & trigger contract

This is the procedure the agent follows **every time a user trigger lands**, from a cold start.

### 4.1 Read order

1. **`/.workflows/META.md`** (this file) — the agent reads this first to learn the subjects, the file schema, and the read order.
2. **The matched subject's `META.md`** — the agent picks the subject whose trigger keywords best match the user request, then reads that subject's manifest. The subject `META.md` lists every workflow with a one-line purpose, trigger keywords, and the output-path pattern.
3. **The matched workflow file** — only after the subject manifest identifies the right workflow does the agent read the workflow's own markdown to get the rules and the strategy.

The agent never globs `.workflows/` and reads every workflow file — that costs tokens. The two-level read (root → matched subject → matched file) lets the agent scope the read to one subject when the trigger is clearly namespaced, and fall back to scanning all three subjects' manifests only when the trigger namespace is ambiguous.

### 4.2 Match procedure

Given a natural-language user trigger, the agent goes through:

1. Read `/.workflows/META.md`.
2. Compare the trigger against each subject's purpose + trigger keywords (read from each subject `META.md` — but if the trigger explicitly mentions an agentx feature or the application codebase, jump straight to `agentx/META.md`; if it mentions the harness, OMT, or session/process work, jump to `meta_harness/META.md`).
3. Inside the matched subject `META.md`, compare the trigger against each workflow's `trigger_keywords` field and `purpose` line.
4. If one workflow's keywords dominate, load that workflow file and follow its `# <Strategy>`.
5. If no workflow matches, reply to the user with the list of available workflows (from the subject manifests) and ask them to clarify or paste a workflow name.
6. **Never** auto-execute a multi-step workflow past its approval gate.

### 4.3 The approval gate (hard invariant)

Every multi-step workflow stops mid-flow at its **proposed-alternatives step** (typically step 4) and presents the alternatives it drafted in step 3. The agent:

- does NOT call any state-mutating tool (no `edit`, no `write` to source, no commit) on the chosen alternative until the user has explicitly picked one;
- MAY write the proposal itself (the alternatives doc) to `.sandbox/` in step 3 — that is a sandbox artifact describing the proposed alternatives, not an applied change;
- executes the chosen alternative only after the user's go-ahead, and records the result back in the same `.sandbox/` file in a later step.

This invariant is **non-negotiable**: an approval-gated workflow that skips the gate is a bug, not a shortcut.

### 4.4 OMT gate stance (how the harness relates to a triggered workflow)

The catalog does not add a machine-parseable `gates:` field. The stance is declared, as today, in the workflow's `# Rules` line 1:

- `Follow omt methodology` — the workflow respects `omt_phase` (declaring phase before `src/` edits), `g.kb` (the app-knowledge-base gate, `omt_kb_nav` consult before `src/` edits), and the think-gates (`omt_think{op:list}` consult on TA-carrying files). The harness gates apply normally.
- `Do not follow the omt methodology, focus on <X>` — the workflow overrides the OMT harness for its own execution but typically still uses `omt_think` to embed knowledge (invariant rule #2). The agent executing the workflow treats `omt_phase` / `g.kb` as advisory rather than blocking for that workflow's run.

The agent reads line 1 of the matched workflow's `# Rules` to learn the stance before executing the strategy. (A first-class `gates:` field is a documented future option, not this iteration — adding it would force a parser, which this iteration explicitly defers.)

---

## 5. Output-path declaration convention

Every workflow declares in its own file (and the subject manifest records it) the sandbox-output pattern it writes to. This convention removes the ambiguity in the current catalog (flat `./sandbox/feature_*.md` vs nested `./sandbox/meta/improvement<NNN>/{...}.md`).

### 5.1 Two patterns, choose per workflow

| Pattern | Shape | Use when | Examples in the catalog |
|---|---|---|---|
| **flat** | `./sandbox/<workflow>_<NNN>_<brief>.md` | The workflow produces a single document per invocation. | `feature_fix` → `./sandbox/feature_<NNN>_<brief>.md` ; `pause_dev_for_resume_later` → `./sandbox/pause_<YYYY-MM-DD>.md` |
| **nested** | `./sandbox/<workflow>/<NNN>_<brief>/<artifact>.md` | The workflow produces more than one file per invocation (proposal + outcome + supporting docs). | `meta_harness_evolution` → `./sandbox/meta/improvement<NNN>/<artifact>.md` ; `meta_harness_project` → `./sandbox/<workflow>/<artifact>.md` per project |
| **nested round** | `./sandbox/<workflow>/round_<NNN>_<brief>.md` | A loop that iterates rounds within a single workflow namespace and wants the rounds grouped. | `consistency_enforcement` → `./sandbox/consistency_enforcement/round_<NNN>_<brief>.md` |

### 5.2 How to declare it in a workflow file

Inside the strategy's propose step (the step that drafts alternatives), the workflow file states the output path explicitly. This file's `META.md` records the chosen pattern for each workflow in §2's subject tree and each subject's `META.md` repeats it in the workflow's row of the table. **The manifest and the workflow file must agree** — if they drift, the workflow file is the source of truth and the manifest should be corrected to match.

### 5.3 Audit and resume

A triggered workflow's strategy always ends with a results-writing step so the same `.sandbox/` file that holds the proposals later holds the outcome. A later session can resume by reading that `.sandbox/` file's `# Result` section. This is how `.sandbox/` doubles as both an audit log and a resumption point.

---

## 6. Authoring template

Copy this template, fill the `«»` placeholders, drop it under the right subject (in `loops/` if it is a recurring procedure, at the subject root if it is a one-shot). The schema in §3 is informal — this template is the reference shape new workflows should match.

```markdown
«one to three lines: the problem this workflow solves, written so the agent can match a trigger to it»

# Rules
1. «OMT stance — either: "Follow omt methodology" OR "Do not follow the omt methodology, focus on <X>"»
2. Use omt think everywhere omt feature to put knowledge in the source code itself
3. Create automated unit test whenever is possible to verify if part of the implementation is wrong, use mocks
4. Try to use sub agents for parallel analysis whenever is possible and useful
5. «optional: any extra invariants specific to this workflow»

# «Strategy name»
1. Read the «project|feature|subject» documentation and requirements
2. Understand the current «implementation|state» and try to find gaps between the core idea versus the actual state
3. Identify the issues if they exist, and propose fix alternatives in a new document or update one document in «OUTPUT_PATH — flat or nested, see §5.1»
4. Ask the user what alternatives have to perform the «fix|change»
5. Execute the «fix|change» alternative chosen by the user
6. Update the results in the same file of step 3, «OUTPUT_PATH»

# Result (optional)
«filled in after execution: what was done, what artifacts were created, what is left to resume — enables later-session resume»
```

### 6.1 Authoring checklist

Before a new workflow lands in the catalog, confirm:

- [ ] Problem statement at the top of the file (before any heading) — < 3 lines, trigger-matchable.
- [ ] `# Rules` section, line 1 is the OMT stance (`Follow omt methodology` / `Do not follow the omt methodology, focus on <X>`).
- [ ] Invariant rule #2 (`omt_think` for embedding knowledge in source) is present, even when the workflow overrides OMT methodology.
- [ ] The strategy is named (`# <Strategy name>`), numbered steps, and contains an approval gate — a step that asks the user which alternative to perform.
- [ ] The output-path pattern is declared in the strategy's propose step (step that writes to `.sandbox/`), in one of the three patterns from §5.1.
- [ ] The strategy ends with a results step that updates the same `.sandbox/` file as the propose step.
- [ ] The workflow file is dropped under the right subject, in `loops/` (recurring) or at the subject root (one-shot).
- [ ] The subject's `META.md` table is updated to list the new workflow (name, purpose, trigger_keywords, output_path).
- [ ] If the workflow is a one-shot at the subject root, the subject's `META.md` marks it with `type: one-shot` (or notes it under "Top-level one-shots").

---

## 7. Recurring principles (the invariants preserved across every workflow)

Every existing workflow converges on five principles. This manifest treats them as **invariants**: a workflow may add rules of its own but cannot drop these.

1. **Human approval is mandatory** — no workflow auto-applies a fix; the user picks the alternative at the approval gate.
2. **`omt_think` is always used** to embed knowledge in source — even when the workflow overrides OMT methodology.
3. **Automated unit tests with mocks** are the preferred verification tool.
4. **Sub-agents** are preferred for parallel analysis whenever useful.
5. **Future agent token consumption** is the primary cost to minimize — workflow definitions are terse, output paths are explicit, and the two-level read order in §4.1 is the cure for "scan every file to find the right one."

---

## 8. Status & maintenance

- This iteration (`workflows` project, `.projects/meta/workflows/PROJECT.md`) delivered the catalog's **definition layer**: this root manifest, the three subject manifests, the authoring template, and the resolution of three open gaps (the empty `app_knowledge_base/loops/` stub, the misspelled path in `consistency_enforcement.md`, the one-line-only pause workflow).
- **First catalog content added post-definition-layer (2026-08-08, same session):** the `app_knowledge_base` subject moved from `future — reserved stub` to `active — 1 loop` with the `akb_smart_population_and_update.md` workflow (a large-effort, nested-round smart pop/update pass over the AKB). The §2 subject list, the §2 tree, and `.workflows/app_knowledge_base/META.md` were updated together to keep the three manifests in agreement (see "To add a workflow" below).
- **Out of scope (deferred to future projects):** discovery helper code in `src/`; a first-class machine-parseable `gates:` field; harness integration / an `omt_workflow` tool.
- **To add a workflow:** copy the template in §6, fill it, drop it under the right subject, update that subject's `META.md` AND §2's subject-list row + tree above (so the root manifest's state stays in agreement with the subject manifest's count). Keep §3's schema and §4.3's approval gate invariants.
- **To add a subject:** make a new top-level directory, add a `META.md` in it using the other subjects as the shape, add the subject to §2's subject list and the tree above.
