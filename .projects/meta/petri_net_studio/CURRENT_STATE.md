# CURRENT_STATE: petri_net_studio

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-23 (iter 1 — scope LOCKED v1.1; no feature work · ≡ PROJECT.md iteration-log iter 2)

### Done

- **Scope LOCKED v1.1** — user said "lock the scope" (single-action approval of PROJECT.md draft v1). All decisions D1–D10 locked (D1–D4 were user-locked in the same-session Q&A; D5–D10 locked here). PROJECT.md flipped: header status line, scope section heading + lock note, status checklist ticked, decisions-log heading + draft markers removed, iteration-log iter-2 entry added. No `src/`, no feature, no `omt_phase` — pure project-home markdown.

### In progress / Blocked

- _(nothing — awaiting user go to scaffold the first feature)_

### Next

- **User go** → scaffold roadmap feature #1 via `uv run scripts/omt/new_feature.py "petri net format" --type minor_feature --project petri_net_studio` (number auto-assigned, D9) → declare the first phase (`omt_phase`); the format work lives in `shared/petri-net/` (outside `src/`, so no src-gate fires).

### Notes / context

- Manifest state stays **draft** until the first feature is linked (flips to active mechanically at scaffold via the project link).
- Locked scope changes from here on require an explicit re-lock decision recorded in the PROJECT.md iteration log.

---

## 2026-08-23 (iter 0 — project home created; no feature work · ≡ PROJECT.md iteration-log iter 1)

### Done

- **Idea round** (same session, before project creation): user asked for a UI tool that uses the shipped Petri-net library to create nets, run analyses, and define a JSON import/export format — modern HTML UI, TypeScript, modern web framework; constraint added: "independent of agentx and meta harness, but must share the same import export file format. same repo". Presented the Petri Net Studio concept (capability→library-API map, format sketch, 3 architecture options A/B/C, stack options, repo layout, phasing).
- **User Q&A decisions (LOCKED):** D1 architecture = **A, pure browser + TS engine port**; D2 stack = **React + TypeScript + Vite + React Flow**; D3 = **io.py yes, as a follow-up harness feature**. User then directed: "create a project … in meta harness, to develop after defining it, as a feature(s)" (→ D4: harness process, independent runtime).
- **Project home created** via `uv run scripts/omt/project.py new "petri net studio" --slug petri_net_studio` (state: draft; manifest synced by the CLI).
- **PROJECT.md v1 written** (canonical): three deliverables (shared format in `shared/petri-net/`, Studio app in `tools/petri-net-studio/`, agentx `io.py`), 5-feature roadmap (`.petri_net_format` → `.petri_net_io` → `.studio_v1_editor` → `.studio_v2_analysis` → `.studio_v3_graph`), draft scope & success criteria, decisions D1–D10, boundaries.
- **CURRENT_STATE.md iter-0 created** (this file).

### Facts verified before writing

- Library shipped and tested: `src/agentx/model/petri_net/{model,analysis,errors,coverability}.py`, 99 tests; add-only mutation API; `PetriNetAnalyzer(net)` constructor-bound; `max_states` required kw-only (`None` = explicitly unlimited); result dataclasses carry `complete`/`reason`/`value: None` semantics.
- No web-server framework anywhere in `src/` (no fastapi/flask/uvicorn) — consistent with D1 pure-browser choice.
- `pyproject.toml` dependency-free for the library itself (stdlib-only — io.py will keep that, mirroring library D4).
- `.projects/meta/META.md` manifest listed 7 homes before this one; CLI `new` scaffolds both files from templates and syncs the manifest mechanically.

### Locked decisions (do not re-litigate without new evidence)

- **(user-locked)** D1 pure-browser TS port · D2 React+TS+Vite+React Flow · D3 io.py as follow-up feature · D4 harness process / independent runtime.
- **(draft, unconfirmed)** D5–D10 in PROJECT.md (format-only coupling, format strictness, canonical serialization, conformance vectors, roadmap/numbering, no-overclaim UI) — pending user approval.

### In progress / Blocked

- _(nothing — project definition delivered, awaiting user response)_

### Next

- **User approves scope & decisions (D1–D10)** — approve as-is or revise (esp. D6 format strictness, D8 conformance vectors, roadmap order/types).
- After approval: lock scope in PROJECT.md (v1.1), then (only on user go) scaffold the first feature via `uv run scripts/omt/new_feature.py "petri net format" --type minor_feature --project petri_net_studio` (number auto-assigned, never hard-coded — D9) and declare the first phase.

### Notes / context

- The tool's independence is a **runtime** property (D4): the harness feature pipeline still governs development; only roadmap feature #2 (`.petri_net_io`) touches `src/` and therefore needs `omt_phase`; features 3–5 are major_feature (design doc + TDD pipeline) even though their code lives outside `src/`.
- Resume entry point: `PROJECT.md` §New Session Quick Start → this entry → §Next.
