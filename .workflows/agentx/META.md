# .workflows/agentx/ — Agentx Application Workflows

> Subject manifest for workflows that operate on the **agentx** application source code. Read this file when the user trigger is clearly about an agentx feature or the agentx codebase as a whole. See `../META.md` §4 for the full discovery & trigger contract.

---

## Subject scope

This subject covers workflows whose `# <Strategy>` operates on the agentx application's source, features, and implementation consistency. The catalog currently holds two loops under this subject, both in `loops/`.

OMT gate stance varies per workflow — read each workflow's `# Rules` line 1 before invoking. The harness gates apply only if the matched workflow declares `Follow omt methodology`.

---

## Loops

| Workflow | Purpose | Trigger keywords | Output path | OMT gate stance |
|---|---|---|---|---|
| `loops/consistency_enforcement.md` | Fix agentx implementation inconsistencies — gaps between the application's core idea and its current implementation, where the implementation drifts from requirements and feature expectations. | "consistency", "consistent", "implementation doesn't match", "drift", "agentx is inconsistent", "fix the implementation", "doesn't follow requirements" | nested round — `./sandbox/consistency_enforcement/round_<NNN>_<brief>.md` | **do not follow** omt methodology, focus on the application as a whole |
| `loops/feature_fix.md` | Inspect and fix a specific agentx feature that does not work as expected — read the feature docs, find the gap between the feature's core idea and its current implementation, propose and apply an approved fix. | "feature", "fix", "doesn't work", "broken", "feature X is wrong", "implement doesn't match spec" | flat — `./sandbox/feature_<NNN>_<brief>.md` | **follow** omt methodology |

### How to pick between the two

If the user's trigger names a specific feature ("feature_024 doesn't work"), pick `feature_fix`. If the user's trigger is about the agentx application as a whole ("the agentx implementation is inconsistent", "implementation doesn't match the requirements", "consistency drift"), pick `consistency_enforcement`. Both are loops — neither auto-applies; the approval gate (step 4 in each strategy) is mandatory.

---

## Top-level one-shots

None. Both agentx workflows are loops under `loops/`.

---

## Notes for future maintainers

- Both agentx loops honour the five recurring invariants in `../META.md` §7: human approval mandatory, `omt_think` everywhere, unit tests with mocks, sub-agents for parallel analysis, minimize future agent token consumption.
- The two output-path patterns are different on purpose: a feature fix is a small doc per invocation (flat), consistency enforcement is a multi-round iteration that groups its rounds under one namespace (nested round).
- To add a new agentx loop: copy the authoring template from `../META.md` §6, drop the file under `loops/`, and add a row to the table above.
