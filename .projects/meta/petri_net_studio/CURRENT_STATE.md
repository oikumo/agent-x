# CURRENT_STATE: petri_net_studio

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-29 (auto — feature_035.studio_v2_analysis Done)

- shipped: major_feature · test report @ 6.testing/features/feature_035.studio_v2_analysis/test_report.md
- logged by omt_complete; expand by hand if resume needs more.

---


## 2026-08-29 (resumed + shipped — roadmap feature #4 DONE: feature_035.studio_v2_analysis · ≡ PROJECT.md iteration-log iter 8)

### Done

- **Resumed** from `.sandbox/pause_2026-08-29b.md` — found **stale** (claimed Cycle 2 stub; the tree had cycles 1–3 DONE + Cycle 4 partially wired). Reconstructed true state from `implementation_001_manual_cycles.md`, git status, and a green 245/245 Vitest run.
- **Cycle 4 completed** (the actual remaining work): `App.tsx` imported `AnalysisPanel` but never rendered it (TS6133) and `styles.css` lacked the design §9 analysis styles. Fixed: `{analysisVisible && <AnalysisPanel />}` below the canvas + full analysis CSS section (badges green/red/amber via `--enabled`/`--danger`/`--warn`). Store additions (`maxStates`/`analysisVisible`/`setMaxStates`/`toggleAnalysis`) + 5 additive tests were already green.
- **Verified all gates**: Vitest **245/245** (8 files) · `tsc --noEmit` clean · `npm run build` green · `check-independence` OK (15 files/43 imports) · `vite preview` smoke 200×3.
- **Sentinel**: `tests/features/feature_035.studio_v2_analysis/test_studio_v2_analysis_sentinel.py` (executes `npx vitest run`; env-skip; structural floor incl. generator + vectors dir; canary-approval skip logged) → `uv run pytest -q` **1638 passed, 5 failed**: 2 = known TDD-ledger probes (in-window); 3 = ONE root cause — WORK.md 5644 B > 5120 B budget — cleared by DONE-rotation (feature_032/033 → WORK_ARCHIVE.md, scratchpad compacted; WORK.md now 3787 B).
- **Bookkeeping**: implementation_001 updated (Cycle 4 + verification evidence), test_report.md written, FEATURE.md/PLAN.md filled, WORK.md feature_035 DONE, PROJECT.md iter 8 + status + Quick Start (next = feature #5 scaffold on user go), `omt_complete` Programming → Testing → Done.

### In progress / Blocked

- _(nothing)_ — project v2 analysis shipped.

### Next

- **Roadmap feature #5 `.studio_v3_graph`** (major_feature): reachability-graph explorer (auto-layout), firing-sequence animation, liveness/SCC views, conformance-suite runner wired into Vitest, example gallery — scaffold via `new_feature.py "studio v3 graph" --type major_feature --project petri_net_studio` on user go.

### Notes / context

- Pause-bookkeeping lesson: the pause doc described Cycle 2 while the implementation report + tree were 2 cycles ahead — resume docs must be re-verified against git status / test runs, not trusted blindly.
- `-0` parity bug fixed in Cycle 3 (Fraction ctor + `_coprimeIntVector`); TA-pinned both sites; caught by conformance vector `weighted_reaction` place_invariants.
- 9th vector emitted (two_way_cycle_truncated) — strict superset of the §3 8-file plan; strengthens the no-overclaim corpus.

---

## 2026-08-23 (bookkeeping sync — feature_035 already scaffolded; docs caught up)

- `feature_035.studio_v2_analysis` (roadmap #4, major_feature) was scaffolded after the feature_034 bookkeeping — the manifest already listed it, but PROJECT.md / CURRENT_STATE.md / WORK.md still pointed at "scaffold #4 on user go". Synced: PROJECT.md iter 6 (Quick Start + status checklist + iteration log), WORK.md task row, feature_035 FEATURE.md WORK.md-task link.
- No feature work, no phases declared, no `src/` edits; scope unchanged (LOCKED v1.1).
- **D8 re-lock recorded (PROJECT.md iter 7, user directive)**: feature #2 shipped io.py without the conformance-vector generator (locked D8 said "feature 2 provides the generator"). Amendment: generator deliverable moved to feature #4 (`.studio_v2_analysis` — vectors are the TDD targets for the TS analysis port); runner wiring stays #5; generator placement is a #4-Analysis decision. Scope remains LOCKED v1.1 with this single amendment.
- **Next**: feature_035 **Analysis** on user go → design doc (§12) → Programming (TDD pipeline auto-activates). TA:gotcha applies to the port: exact rational invariants (no float nullspace) + `_explore` truncation order must match Python or truncated-case vectors diverge.

---

## 2026-08-23 (auto — feature_034.studio_v1_editor Done)

- shipped: major_feature · test report @ 6.testing/features/feature_034.studio_v1_editor/test_report.md
- logged by omt_complete; expand by hand if resume needs more.

### Detail (manual expansion, same session — roadmap feature #3 DONE → **project v1 COMPLETE**)

- Resumed from `.sandbox/pause_2026-08-23c.md` (late-Programming: build+report remaining) — consumed. Remaining sequence executed: tree re-verified (Vitest **170/170**, `tsc --noEmit` clean, independence OK 12 files/36 imports) → `npm run build` (= `tsc --noEmit && vite build`) green → `dist/` verified (`index.html` + hashed css/js) → `vite preview` smoke: `/` + both assets 200; shared examples bundled via `?raw` (no runtime fs).
- **Artifacts**: `implementation_001_manual_cycles.md` + `test_report.md` written (all 4 cycles' RED/GREEN evidence, build/independence/tsc outputs, design-gap resolutions); FEATURE.md/PLAN.md filled; `omt_complete` Programming → Testing → **Done**.
- **Gate fix of note**: Programming-exit requires `tests/features/<feature>/test_*.py` (pytest-shaped, same family as the A11 `omt_tdd` mismatch) → sentinel `tests/features/feature_034.studio_v1_editor/test_studio_v1_editor_sentinel.py` executes `npx vitest run` (env-skip without node, structural floor always-on; feature_031 sentinel precedent; canary-approval skip logged). Agentx suite: **1637 passed + 2 KNOWN_SUITE_FAILURES** (feature_031 TDD-ledger probes still in the 8h window — pass when it clears; zero `src/` edits ⇒ no regressions).
- **Design-gap resolutions recorded** (test_report): `addArc` op (op-spec omission; §7 gesture pinned), import ⇒ edit mode, store-level simulate lock (A9 in every mutating action).
- **Next**: roadmap feature #4 `.studio_v2_analysis` (major_feature — TS analysis port + no-overclaim dashboard D10; TA:gotcha on exact rational invariants + truncation order) on user go.

---


## 2026-08-23 (PAUSED #3 late-Programming — resume via `.sandbox/pause_2026-08-23c.md`)

### State

- **State layer + UI + independence tooling COMPLETE**: `src/state/{document,store}.ts` + `src/examples.ts` + `src/ui/{flow,PlaceNode,TransitionNode,Inspector,App}` + `main.tsx`/`styles.css` + `scripts/check-independence.mjs`. Vitest **170/170** (122 engine + 47 store + 1 independence) · `tsc --noEmit` clean · independence OK (12 files, 36 imports) — tree verified working at pause.
- Cycles 3 (store: RED 46F/1P → GREEN 169) + 4 (independence: RED 1F → GREEN 170) done manual red→green (A11); evidence in pause doc (for the test report, with cycles 1–2 from pause_2026-08-23b).
- Build breakers fixed (first tsc run): io.ts JsonObject return, store.ts Point→JsonObject literal, @types/node + tsconfig types, `**/`-in-comment SyntaxError (TA-pinned).
- Design-gap resolutions (record in test report): addArc op added (op-spec omission; §7 gesture pinned); import ⇒ edit mode; store-level simulate lock.
- **Remaining**: `npm run build` → dist verify → test report → FEATURE/PLAN checkboxes → `omt_complete` (Testing).
- TA: 5 thoughts pinned this session (check-independence.mjs, document.ts, store.ts, independence.test.ts, App.tsx).

---

## 2026-08-23 (PAUSED #2 mid-Programming — resume via `.sandbox/pause_2026-08-23b.md`)

### State

- **Engine port COMPLETE, GREEN**: `tools/petri-net-studio/src/engine/{errors,model,io}.ts` — Vitest **122/122** (60 model + 59 io + 3 golden-example bytes); two manual red→green cycles, evidence in the pause doc (for the test report). Golden byte-identity vs `shared/petri-net/examples/` verified cross-impl without Python.
- Phases: Analysis ✅ · Design ✅ (+operation_spec_001) · Programming ⏸ declared (Vitest/omt_tdd mismatch declared in scope — A11).
- Harness: `tools` in root_allowlist (check 0 errors). Scaffold + npm install done (incl. ajv dev-only).
- **Remaining**: document.ts → store.ts (+store tests) → React Flow UI → check-independence.mjs → `npm run build` → test report → `omt_complete`.
- TA-pinned: io.ts (unary-`**`/integral-float caveats), model.ts (code-point sort), io.test.ts (node-env docblock).
- Budgets tight (work_md ~5015/5120, scratchpad full) — prefer WORK_ARCHIVE rotation over growth on next bookkeeping.

---

## 2026-08-23 (RESUMED feature_034 — Analysis+Design DONE; next Programming)

### State

- feature_034.studio_v1_editor un-paused (resume doc `.sandbox/pause_2026-08-23.md` consumed).
- **Analysis DONE**: `3.analysis/features/feature_034.studio_v1_editor/analysis_001_port_sources.md` — port matrices (62 model + 59 io behaviors; 3 golden-bytes examples), findings A1–A12 (dup-key parser, code-point sort vs UTF-16 erratum, add_output arg order, document-model-first UI, Edit/Simulate modes, root_allowlist +tools, omt_tdd/Vitest mismatch resolution).
- **Design DONE**: `4.design/features/feature_034.studio_v1_editor/design_001_studio_v1_editor.md` — repo layout, errors/model/io API pins, store/UI pin, independence check, test plan + RED/GREEN evidence protocol, programming sequence. `omt_phase{major_feature, Design}` recorded.
- No code yet; no `src/` edits (this feature never touches src/).

### Next

1. Add `tools` to `@var root_allowlist` (META_HARNESS.omt + `harnessc.py build`; receipt discipline) — A10.
2. `omt_phase` Programming (scope declares Vitest/omt_tdd mismatch — A11).
3. Scaffold `tools/petri-net-studio/` (hand-written package.json; npm install — network OK), then RED cycle 1 (model).

---

## 2026-08-23 (PAUSED mid-feature-#3 — resume via `.sandbox/pause_2026-08-23.md`)

### State

- Features #1 (format) + #2 (io) DONE, omt_complete'd, suite 1639 green (re-verified at pause: petri_net subset 158 green).
- **feature_034.studio_v1_editor scaffolded only** (FEATURE.md/PLAN.md stubs, linked). No design doc, no `omt_phase`, no code.
- Paused via `pause_dev_for_resume_later` workflow. **Resume: read `WORK.md` `[~]` row → `.sandbox/pause_2026-08-23.md`** (next step = design doc + `omt_phase`, then Vite scaffold; network confirmed OK; open decision: `omt_tdd` is pytest-shaped vs Vitest — manual red-green likely, recorded in pause doc).

---

## 2026-08-23 (auto — feature_033.petri_net_io Done)

- shipped: minor_feature (declaration-only §12) · test evidence @ `tests/model/petri_net/test_io.py` (59 green) + FEATURE.md test row
- logged by omt_complete; details in the iter-3 entry below.

---


## 2026-08-23 (iter 3 — roadmap feature #2 DONE: feature_033.petri_net_io · ≡ PROJECT.md iteration-log iter 4)

### Done

- **Roadmap feature #2 shipped** (continued "execute the project" go): scaffolded `feature_033.petri_net_io` (minor_feature, origin: scaffold) → `omt_phase` Programming → KB consult (no petri_net records — library postdates KB compile; consult recorded) → TA consult (errors.py: 0 thoughts).
- **`src/agentx/model/petri_net/io.py`** (~290 LOC, stdlib-only, D4): `net_to_json(net, *, layout=None)` canonical §8 bytes · `net_from_json` · `document_from_json` (net + verbatim layout). Validation: level-1 (shape/types/integer domains + duplicate-key rejection via `object_pairs_hook`) → level-2 (V1–V6, rule ids in messages); typed errors subclass `PetriNetError` with pinned precedence (syntax → format → version → L1 → L2). Schema-`integer` semantics honored (integral floats normalized). M0-only serialization (`initial_marking`). Existing library modules + `pyproject.toml` untouched.
- **59 tests green** (`tests/model/petri_net/test_io.py`; canary-approval skip logged — roadmap #2 is locked-scope): canonical dump, byte-identity round-trips, shared examples as golden bytes, layout verbatim/extensions/V6, typed-error matrix, JSON Schema cross-checks. **Full suite 1639 passed, 0 regressions.**
- Bookkeeping: FEATURE.md/PLAN.md filled, WORK.md (feature_031 task line rotated to WORK_ARCHIVE.md — budget), CURRENT_STATE.md, PROJECT.md iter 4.

### In progress / Blocked

- _(nothing)_

### Next

- **Roadmap feature #3 `.studio_v1_editor`** (major_feature, depends on #1 ✅): `tools/petri-net-studio/` scaffold (Vite+React+TS+React Flow+Vitest per D2) — visual editor, token/weight editing, **TS model-layer port**, click-to-fire simulation with enabled highlighting, JSON import/export with validation, static build, independence lint check (no agentx/harness imports). Scaffold via `new_feature.py "studio v1 editor" --type major_feature --project petri_net_studio` on user go — **major_feature ⇒ design doc (§12) + TDD pipeline auto-activates at Programming**; npm install requires network.

### Notes / context

- io.py gotchas pinned for future features: `add_output` called by keyword (§9 argument-order gotcha); `object_pairs_hook` for duplicate-key rejection; `bool` excluded before `int` checks everywhere; layout extension members pass through with parsed key order (canonical ordering pinned only for v1 members).
- The TS io port (feature #3) must match these exact behaviors — `tests/model/petri_net/test_io.py` is the reference matrix to port.

---

## 2026-08-23 (auto — feature_032.petri_net_format Done)

- shipped: minor_feature (declaration-only §12) · validation evidence @ `2.requirements/features/feature_032.petri_net_format/FEATURE.md` test row (32/32 checks)
- logged by omt_complete; details in the iter-2 entry below.

---


## 2026-08-23 (iter 2 — roadmap feature #1 DONE: feature_032.petri_net_format · ≡ PROJECT.md iteration-log iter 3)

### Done

- **User go received** ("execute project") → scaffolded roadmap feature #1 via `new_feature.py "petri net format" --type minor_feature --project petri_net_studio` → auto-numbered **feature_032** (D9), linked origin: scaffold; manifest flipped **draft → active** mechanically.
- **`shared/petri-net/` shipped** (the contract, D5): `FORMAT.md` spec v1 (document shape; naming stricter-than-library per D6 — names unique across P ∪ T; two-level validation: schema + semantic rules V1–V6; semantics by reference to the tested library §7; canonical serialization §8 per D7; versioning §9; conformance-vectors plan §10), `petri-net-json-v1.schema.json` (Draft 2020-12), 3 canonical examples (`hello`, `producer_consumer` with layout, `weighted_reaction`), plus `shared/META.md` (dir manifest, contract-only rule).
- **Validated**: 32/32 one-off checks — schema Draft 2020-12 self-valid; 3/3 examples schema-valid + V1–V4 clean + on-disk bytes already canonical + canonicalize idempotent; 9 schema-negative + 4 semantic-negative docs rejected; 3/3 examples construct real `PetriNet` objects via the FORMAT.md §7 algorithm with expected enabled sets. No `src/` edits (src-gate never fires for this feature — features 1,3,4,5 live outside `src/`).
- **Bookkeeping**: FEATURE.md + PLAN.md filled (declaration-only, §12), WORK.md task + scratchpad entries, PROJECT.md status/iteration-log iter 3.

### In progress / Blocked

- _(nothing)_

### Next

- **Roadmap feature #2 `.petri_net_io`** (minor_feature, depends on #1 ✅): `src/agentx/model/petri_net/io.py` + `tests/model/petri_net/test_io.py` — `net_to_json`/`net_from_json`, schema + V1–V6 validation, typed errors, canonical bytes, byte-identity round-trip tests; fulfills the library's deferred v2 "JSON export" backlog item. Scaffold via `new_feature.py "petri net io" --type minor_feature --project petri_net_studio` on user go. **Only `src/`-touching feature → needs `omt_phase` + KB consult before edits; stdlib-only (library D4, `pyproject.toml` unchanged).**

### Notes / context

- Format design choices pinned in v1 (re-litigating = scope re-lock): flat `arcs` array with source/target (React Flow-friendly); `tokens`/`weight` always explicit (no defaults); integer-only layout coordinates (kills Python/JS float-serialization divergence in canonical bytes); duplicate JSON keys MUST be rejected by loaders; `layout` round-trip preserved verbatim (byte-identity includes layout).
- Validation script was one-off (/tmp); permanent test coverage lands with feature #2 (pytest) and the conformance runner (feature #5, Vitest).

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
