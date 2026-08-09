# CURRENT_STATE: rag_v2

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

> **Resume entry point:** read `PROJECT.md` §New Session Quick Start (the v1.2 block at the top of PROJECT.md), then run the three commands in it.
> The locked v1.1 project definition (Summary → Purpose → Vision → §Scope G1–G6 closure matrix → Decisions D1–D8 → References) sits below the Quick Start block in PROJECT.md — read once on first contact, then act.

---

## 2026-08-09 (iter 0 — project definition locked + Quick Start block)

### Done (this iter)

- **`PROJECT.md` v1.1 → v1.2** (this round's only project-home edit, no `src/` edit, no feature dir scaffold — both intentionally deferred per the v1.1 lock).
  - **§New Session Quick Start** block prepended to the document (between the H1+v1.2 status line and the v1.1 Status preamble). The block has five named sub-sections:
    1. **What's locked** — a 5-row table mapping each locked v1.1 § to what a fresh session needs from it (Summary / Purpose-v1-gaps / Vision-standing-principle "retrieval is a tool" / Scope G1–G6 closure matrix / Decisions D1–D8).
    2. **The three exact next commands** (verbatim, runnable, in order):
       - `uv run scripts/omt/new_feature.py "rag v2" --type major_feature`  →  scaffolds `.meta/software_development_process/.../features/feature_027.rag_v2/` (free slot confirmed: 025=coding context window, 026=omt_q per `2.requirements/features/` listing).
       - `omt_phase{task_type:"major_feature", scope:"rag v2 — Analysis: ...", feature:"feature_027.rag_v2"}`  →  declares the Analysis phase (feature_016 TDD enforces at *Programming*, Analysis is TDD-free).
       - Run the four Analysis substrate reads in parallel + write `analysis_001_*.md` under `3.analysis/features/feature_027.rag_v2/` (sources: v1 RAG surface, feature_025 deepagents stack, feature_024 console MVC++ contract, LangChain deepagents-RAG docs).
    3. **What NOT to do** — seven ❌ items, each citing the locked decision it would re-litigate: don't scaffold from PROJECT.md / don't edit v1 (D3) / don't pick a different RAG pattern (D5) / don't add a TUI (D2) / don't modify the deepagents stack (D4) / don't add a new vector store / don't close TDD via skip (D7).
    4. **Resume entry point** — points back here to CURRENT_STATE.md.
  - **Status checklist bumped**: header status → v1.2; new row `[x] New Session Quick Start block (v1.2 — ...)` between the four v1.1-locked items and the four design-phase-pending items. Architecture, Tasks, feature dir scaffold, phase declared stay `[ ]`.
  - **Iteration log** appended with the v1.2 entry naming all three moves + gestalt. Three TA: thoughts from v1.1 preserved unchanged (the gotcha / todo / risk on retrieve-offload-delegate + v1 cutover + D5 lock — all still valid).
- **`CURRENT_STATE.md` iter-0** (this file) created per the meta_harness_2 convention (`PROJECT.md` = canonical design_doc, `CURRENT_STATE.md` = session log + resume point; sibling reference: `.projects/meta/meta_harness_2/{PROJECT.md,CURRENT_STATE.md}`).

### Test results

- _(none — project-home markdown only; no pytest run for docs work per `task_type:"docs"` convention.)_
- Sanity: `2.requirements/features/` listing re-verified (only up to feature_026) + no existing `feature_027` dir → step 1 of Quick Start is safe to run.

### Locked decisions (do not re-litigate without new evidence)

- **Quick Start block is navigational, not definitional** — no scope axis was changed by v1.2. The block writes the *path to start* over the *definition of the project* (which remains the locked v1.1 body in PROJECT.md). Editing the Quick Start block (e.g., renaming commands, re-ordering steps) is allowed without a new iteration; editing the v1.1 locked sections (Summary / Purpose / Vision / Scope / Decisions D1–D8) requires the v1.1 boundary-vs-content rules (changing an axis boundary = new iteration; sharpening within an axis = design-phase work).

- **CURRENT_STATE.md iter-0 is the resume anchor** — a fresh session reads CURRENT_STATE.md first, lands on iter-0, follows the resume_entry_point to PROJECT.md §New Session Quick Start, runs the three commands. Subsequent sessions add iter-1, iter-2, … blocks above iter-0; iter-0 stays as the historical origin point (do NOT rotation-delete iter-0 — it's the only entry that documents the pre-feature-dir definition state). Older iter blocks follow the WORK.md rotation rule (last N inline, older rotated to a future `CURRENT_STATE_ARCHIVE.md` if one is ever needed; N follows the same default as WORK.md, 5).

### Next

- **Run the three commands.** (iter 1 = Analysis phase begin)
  1. `uv run scripts/omt/new_feature.py "rag v2" --type major_feature`
  2. `omt_phase{task_type:"major_feature", scope:"rag v2 — Analysis: scaffold substrate reads + write analysis_001_*.md", feature:"feature_027.rag_v2"}`
  3. Parallel substrate reads → `analysis_001_*.md` under `3.analysis/features/feature_027.rag_v2/`.

- **After Analysis → Design phase**, write the deferred Architecture + Tasks into PROJECT.md (or, more likely, into `feature_027.rag_v2/design_001_*.md` per the feature dir's ownership of design-phase sharpening — the v1.1 PROJECT.md body explicitly defers both to the feature dir, so the next iter of THIS file's Status checklist only flips Architecture `[x]` once `design_001_*.md` is committed; the PROJECT.md may not need editing at design time at all, unless a §Standing principle extension arises (e.g., composing rubric-checked grounding on top of retrieve-offload-delegate per the TA: risk note at line ~210)).
