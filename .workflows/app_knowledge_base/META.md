# .workflows/app_knowledge_base/ — Application Knowledge Base Workflows

> Subject manifest for the **app_knowledge_base** subject. **Status: active — 1 loop** (the empty reserved stub was populated 2026-08-08). Workflows here operate on the application knowledge base — the curated concept/contract/dependency index built by the `feature_kb_akb` project. See `../META.md` §4 for the full discovery & trigger contract.

---

## Subject scope

This subject covers workflows that operate on the **application knowledge base** — the curated concept/contract/dependency index built by the `feature_kb_akb` project (`kb_ast_extract.py`, `kb_compiler.py build`, `omt_kb_nav.ts` cap=25+truncate), the `g.kb` gate, and the `kb_bootstrap` injection that powers it. When the user triggers a workflow about updating, re-tiling, auditing, or fixing the application knowledge base, this is the matched subject.

Trigger keywords for subject-scoping: "knowledge base", "AKB", "app-knowledge-base", "kb", "kb_compiler", "kb_ast_extract", "concept-altitude index", "g.kb gate".

All AKB workflows authored in this subject **follow OMT methodology** by convention (the KB is the canonical consumer of `omt_kb_nav`, opposing it would be self-defeating — a workflow that polishes the KB passes the same `g.kb` consult gate it maintains). Confirm the stance in each workflow file's own `# Rules` line 1; this manifest echoes it.

---

## Loops

**1 loop.** The `loops/` directory under this subject holds the AKB smart population / update procedure — the recurring pass that rebuilds the AST skeleton, diagnoses coverage gaps + drift + curation debt, proposes fixes, and applies the user-approved subset.

| Workflow | Purpose | Trigger keywords | Output path | OMT gate stance |
|---|---|---|---|---|
| `loops/akb_smart_population_and_update.md` | Drive a smart population / update pass on the AKB — rebuild the AST skeleton, measure baseline (total / per-kind / orphans / dups / style-lint), diagnose coverage gaps + drift + auto-text curation debt + gate/lint sanity, propose prioritised fix alternatives, apply the user-approved subset. Large-effort because the AKB is unbounded (ALL public classes, ~270+ records + deps + curated docs) and drift accrues continuously as `src/` moves. | "AKB", "knowledge base", "kb", "populate the KB", "update the KB", "re-tile the KB", "rebuild the index", "audit the AKB", "concept-altitude drift", "curate overlay text", "kb_compiler", "kb_ast_extract", "g.kb gate", "fix the knowledge base" | nested round — `./sandbox/akb_smart_population_and_update/round_<NNN>_<brief>.md` | **follow** omt methodology |

### When to trigger this loop

Trigger this workflow when the user asks (in any wording) for a smart pass on the AKB: populating missing skeleton records, updating curated overlay `text` for un-curated records, reconciling drift after a `src/` rename/removal, auditing the concept-altitude index, fixing `g.kb` consult-gate / `omt_kb_nav` result-bound / `@inject kb_bootstrap` behaviour, or generally "the knowledge base is stale, fix it". It is a recurring loop — not a one-shot — because the AKB accrues drift continuously and the curation queue (records still on auto-text) is peeled in subsystem-sized rounds across sessions.

---

## Top-level one-shots

None. A AKB-specific one-shot (e.g. a single-purpose "wipe-and-rebuild" utility) is plausible future work — author it at the subject root only after confirming it is genuinely single-pass and not just one round of this loop.

---

## History (was future/reserved stub, now active)

This subject was created on 2026-08-08 as a **future — reserved stub** with empty `loops/` (decision: keep the directory and let the manifest declare the state honestly, rather than delete the namespace). The reserved-stub period ended the same day with the first loop (`akb_smart_population_and_update.md`) dropping into `loops/`. The reasons for keeping the namespace reservation through the empty period remain valid for any future empty subject:

- The application knowledge base is a real, active subsystem (the `feature_kb_akb` project shipped it on 2026-08-08). Workflows that operate on it are natural recurring work — the reservation anticipated this loop.
- Empty `loops/` was never a hidden stub because the subject manifest declared it empty; the agent read this manifest, learned the state, and did not invent an AKB workflow.
- Keeping the name in `../META.md` §2's tree through the empty period meant the first AKB workflow only needed to update one row above — no re-declaration.

---

## Notes for future maintainers

- To add a second AKB loop: copy the authoring template from `../META.md` §6, drop the file under `loops/`, add a row to the Loops table above, and (if the loop adds a new output-path pattern not covered by `../META.md` §5.1) extend §5.1 of the root manifest.
- The completion of this subject (`future` → `active`) means `../META.md` §2 (subject list and tree) now shows **active — 1 loop** for `app_knowledge_base`. Keep the two manifests in agreement; the workflow file is the source of truth on its own content, the manifests stay in agreement on state.
- A AKB workflow that opts out of OMT methodology would be the exception, not the norm — add it only with a defended reason in `# Rules` line 1, and prefer still using `omt_think` to embed knowledge (invariant rule #2 preserved in `../META.md` §7).
