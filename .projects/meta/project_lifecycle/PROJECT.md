# PROJECT: project_lifecycle — Mechanical project management for the meta harness

> Status: **active** · **v1.0 (2026-08-22)** — design locked via full investigation + 4 user decisions (D1–D8, §Decisions). Companion feature: **feature_030.project_lifecycle** — **SHIPPED same-session (DONE 2026-08-22; test report @ `6.testing/features/feature_030.project_lifecycle/test_report.md`)**: the 8 components below are now the running mechanic. This home was created by hand pre-mechanic and adopted via `origin:backfill` (dogfood); future homes are one command (`project.py new`).

---

## New Session Quick Start

> Read this block first. The v1.0 design below is **locked** — do NOT re-derive the entity model, re-pick the link mechanism, or re-litigate D1–D8 without new evidence.

**One line:** `.projects/` becomes mechanically managed — a project is a first-class entity (`create → iterate → spawn features (for it or another) → close → archive`), linked **1 : 0..N** to features, with ledger records as truth, `harnessc check` as the compile-time enforcer, `omt_complete` log-sync, and `omt_q` drift surfacing. `.projects/` stays **non-gated**; OMT phases stay **feature-only**.

| If you need… | Read |
|---|---|
| The entity model + measured evidence | §Entity model (0..N) |
| What gets built | §Components (8) + §Build rounds |
| What `omt_complete` may write | §Write scope (facts, not verdicts) |
| Backfill of the 6 existing homes | §Backfill (full honest) |
| Archive semantics | §Physical archive |

**Next commands:** Analysis per §12 → `3.analysis/features/feature_030.project_lifecycle/analysis_001_*.md` re-verifying the anchors: `phase_gate.ts:99-132` (resolveArtifact — the design_doc bridge), `phase_gate.ts:367-414` (syncWorkMdFromLedger — the markdown-sync precedent), `harnessc.py:705-715` (check_work_done_max — the check idiom), `harnessc.py:783-790` (render_agents required-docs), `new_feature.py` (scaffolder idiom), `omt_q.ts` (drift op), `omt_status.ts`. Then design_001.

---

## Summary (one line)

**Ship the missing "project" entity in the meta harness**: today `.projects/meta/<slug>/{PROJECT.md, CURRENT_STATE.md}` is a documented convention with zero mechanics — creation, linking, logging, status, and closure are all manual and already drifting (6 live instances, §Evidence). This project adds the mechanics: a bash lifecycle CLI (`project.py`), spawn-time feature links recorded in the ledger, compile-time structure/link/status checks in `harnessc check`, an `omt_complete` ship-sync into the owning project's log, a generated manifest projection, and `omt_q` project-drift classes — while keeping `.projects/` non-gated and OMT phases feature-only (D1, D8).

---

## Entity model (0..N) — measured, not assumed

Investigation 2026-08-22 over the real repo state:

| Project | Linked work | Ratio |
|---|---|---|
| `meta_harness_2` | feature_020, _021, _022, _023, _026 (+ improvement00X slugs) | 1 : 5+ |
| `meta_harness_3` | feature_028 shipped; Phase-B/C = 2 future features | 1 : 3 |
| `rag_v2` | feature_027 + feature_029 + 2 bug_fixes (ingestion_persist, help_deepcopy) | 1 : 4 |
| `petri_net_library` | none yet (feature_001 is a future *consumer*, not the library's feature) | 1 : 0 |
| `workflows` | none (docs-only) | 1 : 0 |
| `feature_kb_akb` | non-numbered slug, no feature_0NN | 1 : 0-numbered |
| ~20 features (001–025 mostly) | no project home | 0 : 1 |

Consequences: **(1)** name-derivation is impossible (`feature_028.feature_scoped_gating` ↔ `meta_harness_3` share no substring) — links must be explicit records. **(2)** Most features legitimately have no project — the link is optional feature→project, mandatory real project→features. **(3)** Project completion is underivable from feature states (meta_harness_3 stays open with 028 Done) — close is a user verdict executed by command, never inferred.

**Model:** Project `1 : 0..N` Feature (a feature ≤1 project). Truth = ledger records (`{kind:"project", op:create|close|reopen}` · `{kind:"project_link", project, feature, origin:scaffold|inferred|backfill}`) + filesystem dirs. Everything else (manifest, omt_q answers, drift) is projection. Project FSM: `draft → active → complete → archived`.

## Evidence — the drift already accumulating (what the checks must catch)

1. `workflows/` has **no CURRENT_STATE.md** (structure violation, nothing catches it).
2. `feature_kb_akb/` carries a stray `.bak` + loose artifacts (`check_root_hygiene` flags `.bak` in `.meta/.omt`, nothing in `.projects/`).
3. `rag_v2/CURRENT_STATE.md` last entry 2026-08-15 (Design) — feature_027 Done + feature_029 + 2 bug fixes shipped since; **stale-log**.
4. `meta_harness_3` PROJECT.md §Status went stale after feature_028 shipped — caught by hand at iter-4 (**status drift**).
5. `.workflows/meta_harness/loops/meta_harness_project.md` (the manual procedure) has a stale path `./projects/meta/project_<ID>/` ≠ `.projects/meta/<slug>/`.
6. No manifest (`.workflows/META.md` exists; `.projects/meta/META.md` doesn't); no scaffolder (`new_feature.py` only does feature dirs); no budget/resume-block rule (T3: `meta_harness_2/PROJECT.md` re-read 26× ≈ 520KB in one session); `omt_status`/`omt_q` know nothing about projects.

The 5 thin touchpoints that DO exist: `@var root_allowlist` (`.projects`), 3 nav doc records (`comp.projects`/`pth.projects`/`projects_home`), the AGENTS.md projection line, `omt_phase{design_doc=}` accepting any existing path (phase_gate.ts:128 — the unvalidated bridge), and the think-gate on TA:-carrying project files.

## Lifecycle FSM + mechanics (locked by user)

**`create → iterate → spawn features (for it or another) → close → archive`; phases stay feature-only.**

| Step | Mechanic | Writer | Mechanical check |
|---|---|---|---|
| create | `scripts/omt/project.py new "<name>"` → dirs + templates + ledger `create` | bash script (D5: no new omt tool) | harnessc: structure |
| iterate | free non-gated edits; `project.py log "<note>"` appends a formatted CURRENT_STATE block | agent/human | omt_q drift: iteration-log |
| spawn | `new_feature.py --project <slug>` → `project_link` (origin:scaffold); fallback: `omt_phase` infers from `design_doc` inside `.projects/meta/<slug>/` (origin:inferred) | scaffolder / phase_gate.ts | harnessc: links both directions |
| ship | `omt_complete{advance_to:Done}` → dated auto-block in the OWNING project's CURRENT_STATE.md (idempotent) + `draft→active` flip on first link | phase_gate.ts | omt_q drift: stale-log |
| close | `project.py close <slug>` → Status: complete + ledger `close`; warns on in-flight linked features | user-run | harnessc: status consistency |
| archive | `project.py archive <slug>` (or `close --archive`) → moves home to `.projects/archive/<slug>/`, `archived_to` on the record | script | checks skip archive root |
| reopen | `project.py reopen <slug>` → Status flip + ledger record (moves back from archive) | script | — |

**"For it or another project"** (user-set): the ship entry lands in the feature's OWNING project regardless of session context. No active-project state is stored — "active project" is derived from the active feature's link (feature_028 `_active_feature` precedent). A feature made for NO project is legal: no-op + one-line note.

## Components (8)

1. **`scripts/omt/project.py`** — `new|link|log|status|close|reopen|archive` (mirrors `new_feature.py`; bash, not an omt tool — schema budget untouched, D5).
2. **Templates** — `.meta/templates/project.md` (parseable `> Status: **draft**` header + Quick-Start block + Features section) + `current_state.md`.
3. **`new_feature.py --project <slug>`** — link at spawn.
4. **phase_gate.ts** — design_doc inference (resolveArtifact path under `.projects/meta/<slug>/` → `project_link` origin:inferred) + `omt_complete` ship-sync (extends the syncWorkMdFromLedger precedent).
5. **harnessc checks (build errors)** — ① structure (PROJECT.md + CURRENT_STATE.md pair; newest-on-top; no `.bak`) ② links (no phantom features/projects; no dupes; complete projects acquire no links) ③ resume-block (PROJECT.md > threshold ⇒ Quick-Start block near top — D7) ④ status-header consistency (header ⇔ derived state) ⑤ manifest sync.
6. **Manifest projection** — harnessc build emits `.projects/meta/META.md` (GENERATED table: `project | state | features | created | closed`; active + archived sections; never hand-edited).
7. **omt_q / omt_status surface** — `op=drift` gains project classes (stale-log, status-drift, phantom-link, unlinked-project-backed, iteration-log, aging-draft); `op=state{feature}` shows its project; `omt_status` shows derived active project + last log date.
8. **Backfill** — §Backfill (full honest).

## Write scope — facts to log, verdicts stay human (D2)

On `omt_complete{advance_to:Done}` for a linked feature:

- **Always:** insert a dated auto-block at the top of the owning project's `CURRENT_STATE.md` (newest-on-top):
  ```
  ## <date> (auto — feature_0NN.slug Done)
  - shipped: <task_type> · test report @ 6.testing/features/feature_0NN.slug/test_report.md
  - logged by omt_complete; expand by hand if resume needs more.
  ```
  Idempotent (skips if the feature+Done block exists). The auto-block is the *floor*, not the ceiling — rich iter-N narratives stay human.
- **Factual flip only:** `Status: **draft**` → `**active**` on first linked feature (template guarantees the parseable literal; unparseable → skip + note). Never prose Status; never close.
- **Unlinked feature:** no-op + one line in the omt_complete output ("no project link — `project.py link` if this work belongs to a project home").
- Precedent: `syncWorkMdFromLedger` (phase_gate.ts:367-414) already writes WORK.md checkboxes on complete; this extends the same idiom to project logs.

## Backfill — full honest (D3)

- **Structure:** `workflows/` gets its stub CURRENT_STATE.md; `feature_kb_akb/`'s `.bak` flagged + removed. All 6 homes pass structure checks from day one (no grandfathering — two classes of projects forever is the worst outcome).
- **Links:** historical mapping written as `project_link` records with `origin:"backfill"` (append-only, no forged timestamps): meta_harness_2↔{020,021,022,023,026} · meta_harness_3↔{028} · rag_v2↔{027,029} · petri_net_library↔{} · workflows↔{}.
- **Logs:** ONE `(auto — backfill)` baseline block per home: "linked features […]; prior ships: feature_027 (report @…), feature_029 (…); log continuity starts here." Gives the stale-log check a clean baseline ts without fabricating retro-history.
- This project's own home is backfilled too: `project_lifecycle↔{feature_030}` (origin:backfill, since the spawn mechanic doesn't exist at scaffold time — dogfood note).

## Physical archive (D6)

`close --archive` / `archive` moves the home to `.projects/archive/<slug>/`. Accepted consequences: historical `design_doc` ledger pointers dangle harmlessly (resolveArtifact runs only at active-phase time); inline TA: thoughts travel with moved files (thoughts.jsonl sidecar path keys go stale — documented, inline is truth per R6 S1); manifest lists archived projects in a separate section with new paths; harnessc checks skip the archive root; `@var root_allowlist` covers `.projects` wholesale.

## Checks + drift classes

**harnessc check (build errors):** structure · links both directions · resume-block (threshold via `@var project_resume_threshold_bytes`, ~16KB) · status-header consistency · manifest sync. Idioms: `check_work_done_max` (harnessc.py:705), `check_root_hygiene` (:685), `check_comp_paths` (:658).

**omt_q op=drift (warnings):** stale-log (linked Done newer than top CURRENT_STATE entry) · status-drift · phantom-link · unlinked-project-backed (design_doc in `.projects/`, no link record — autofix hint `project.py link`) · iteration-log (PROJECT.md changed since top entry; git-based, warning-level to survive typo edits) · aging-draft (draft > N weeks, prompt-only).

## Build rounds (feature_030, major_feature → TDD auto at Programming)

R1 templates + `project.py` + ledger writers → R2 harnessc checks + `.omt` records (`@var` paths, doc payload updates, manifest projection) → R3 phase_gate.ts (inference + ship-sync) → R4 omt_q.ts + omt_status.ts surfaces → R5 backfill + manifest + e2e + test report. Receipt round-robin per round (GOTCHA_RECEIPT_ROUND_ROBIN); hermetic goldens via `OMT_LEDGER_PATH`/`OMT_SNAPSHOT_DIR` (state.py:34-37 precedent).

## Success criteria (testable)

- All 6 §Evidence drift instances are caught mechanically (golden per class).
- A feature_029-style ship lands in the owning project's log with zero agent effort (golden: omt_complete Done → auto-block present, idempotent on re-run).
- Create/close = one command each; manifest never decays (build-checked); draft→active flip fires exactly once.
- Full regression green; `harnessc check` 0 errors; `.projects/` still non-gated (no gate record added); tool count unchanged (D5).

## Non-goals (locked)

No edit-gating of `.projects/` (D8) · no project phases (D1) · no prose writes into Status beyond draft→active (D2) · no auto-close · no fabricated retro-logging (D3) · no new omt tool (D5) · no slug-name link derivation (§Entity model).

## Decisions log (locked — do not re-litigate without new evidence)

- **D1 — Lifecycle model (user-set 2026-08-22):** create → iterate → spawn features (for it or another) → close (→ archive). OMT phases are for features only; projects never enter the §12 matrix; the link is born at spawn, not at phase declaration.
- **D2 — omt_complete writes facts, not verdicts (user-confirmed):** dated auto-block in the owning project's CURRENT_STATE.md (idempotent) + draft→active flip on first link. Never prose Status; never close.
- **D3 — Full honest backfill (user-confirmed):** structure + origin:backfill links + one baseline block per home; no fabricated history; no grandfathering.
- **D4 — Link born at spawn:** `new_feature.py --project` primary; design_doc inference (origin:inferred) fallback. NO optional `project=` phase arg — optional-arg decay is measured (21 empty `feature:` phase records; meta_harness_2 U8).
- **D5 — No new omt tool:** `project.py` is bash (tool_schemas budget is zero-sum, 1094/1280 — meta_harness_3 D9). Scaffolders-as-scripts is the new_feature.py idiom.
- **D6 — All four optional components in scope (user-confirmed):** generated manifest projection · `project.py log` · reopen · physical archive (consequences §Physical archive accepted).
- **D7 — Resume-block check over raw byte budget:** PROJECT.md > threshold ⇒ Quick-Start block near top (the rag_v2 organic pattern made mechanical; T3 re-read evidence). Preserves doc freedom, guarantees a cheap resume path.
- **D8 — `.projects/` stays non-gated:** edit-time gating creates the chicken-egg bootstrap (the home is where you design BEFORE a feature exists — the TDD_BOOTSTRAP analog). Mechanical management without gates: checks + sync + projections.

## References

- Convention source: `.meta/META_HARNESS.omt:184-185,208` (`@doc comp.projects`/`pth.projects`/`projects_home`)
- Mechanics anchors: `phase_gate.ts:99-132` (resolveArtifact) · `:367-414` (syncWorkMdFromLedger) · `harnessc.py:658-715` (check idioms) · `harnessc.py:783-790` (render_agents required-docs) · `scripts/omt/new_feature.py` · `scripts/omt/tdd/state.py:34-37` (hermetic redirects)
- Analogs: `.workflows/META.md` (manifest model) · WORK.md rotation + `check_work_done_max` (non-gated but mechanically managed file)
- Evidence: §Evidence (6 live drift instances, verified 2026-08-22)
- Feature dir: `.meta/software_development_process/2.requirements/features/feature_030.project_lifecycle/`
</content>
