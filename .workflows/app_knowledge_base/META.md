# .workflows/app_knowledge_base/ — Application Knowledge Base Workflows

> Subject manifest for the **app_knowledge_base** subject. **Status: future — reserved stub.** No workflows have been authored for this subject yet. See `../META.md` §4 for the full discovery & trigger contract.

---

## Subject scope

This subject is reserved for workflows that operate on the **application knowledge base** — the curated concept/contract/dependency index built by the `feature_kb_akb` project (`kb_ast_extract.py`, `kb_compiler.py build`, `omt_kb_nav.ts` cap=25+truncate), the `g.kb` gate, and the `kb_bootstrap` injection that powers it. When the user triggers a workflow about updating, re-tiling, auditing, or fixing the application knowledge base, this is the matched subject.

Trigger keywords for subject-scoping: "knowledge base", "AKB", "app-knowledge-base", "kb", "kb_compiler", "kb_ast_extract", "concept-altitude index", "g.kb gate".

---

## Loops

**None authored yet.** The `loops/` directory under this subject is an empty reserved stub — it exists so a future project can drop the first AKB workflow into it without re-creating the directory or re-declaring the subject in `../META.md` §2.

| Workflow | Purpose | Trigger keywords | Output path | OMT gate stance |
|---|---|---|---|---|
| — | (none — `loops/` is empty) | — | — | — |

---

## Top-level one-shots

None. All AKB workflows authored in future projects should land under `loops/` until proven one-shot.

---

## Why this subject is reserved, not deleted

The workflows-project scope decision was to **keep** the `app_knowledge_base/` tree with `loops/` empty and let its subject manifest declare the state honestly, rather than delete the directory and drop the namespace. Reasons:

- The application knowledge base is a real, active subsystem (the `feature_kb_akb` project shipped it on 2026-08-08). Workflows that operate on it are plausible future work — a "re-tile the KB", "audit the concept-altitude index for drift", or "rebuild curated overlay" workflow would naturally live here.
- Empty `loops/` is not a hidden stub if the subject manifest declares it empty. The audit cost of "scan every `.md` to find an AKB workflow" is avoided because the agent reads this manifest, learns the subject is empty, and replies to the user with the catalog-wide list instead of inventing an AKB workflow.
- Re-adding a deleted namespace later requires touching `../META.md` §2 (the subject list and the tree) again; keeping the name in the tree means a future AKB workflow only updates one row above.

---

## Notes for future maintainers

- When the first AKB workflow is authored, replace the table row above and update `../META.md` §2 to change this subject's state from `future` to `active`.
- A future AKB workflow's `# Rules` line 1 should note that it follows OMT methodology (the KB is the canonical consumer of `omt_kb_nav`, opposing it would be self-defeating — the workflow likely *uses* the AKB it modifies) — confirm the stance in the workflow file itself, with this manifest echoing it.
- The authoring template lives in `../META.md` §6 — copy it, fill it, drop the file in `loops/`, then add the row here.
