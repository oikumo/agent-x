# Design 001 — feature_030.project_lifecycle: mechanical project management

> Date: 2026-08-22 · Phase: Design · Canonical design: `.projects/meta/project_lifecycle/PROJECT.md` v1.0 (D1–D8) · Analysis: `3.analysis/.../analysis_001_anchor_verification.md` (anchors A1–A13, findings F1–F9)
> This doc fixes the contracts analysis deferred: record shapes, module layout, CLI, checks, templates, manifest, TS deltas, testlist, round plan.

---

## 1. Module layout (new code is 2 Python modules + TS deltas)

| File | Role | New? |
|---|---|---|
| `scripts/omt/project_state.py` | Self-contained state layer: lazy env-redirectable paths, full-fold ledger reader, `write_record`, project/link derivations, manifest rows | NEW |
| `scripts/omt/project.py` | CLI: `new|link|log|status|close|reopen|archive|sync` (argparse, new_feature.py idiom) | NEW |
| `.meta/templates/project.md` / `current_state.md` | Home templates (`{{SLUG}}/{{TITLE}}/{{DATE}}` idiom) | NEW |
| `scripts/omt/harnessc.py` | +5 checks (§4) registered in the check pipeline | EDIT (R2) |
| `.meta/META_HARNESS.omt` | +3 `@var`, 3 `@doc` payload updates (§6) | EDIT (R2) |
| `.opencode/lib/omt_shared.ts` | +`readLedgerAll()` (full fold: all archives + hot) | EDIT (R3) |
| `.opencode/lib/enforcer/phase_gate.ts` | design_doc inference in `omt_phase`; `syncProjectLogFromLedger` in `omt_complete` | EDIT (R3) |
| `.opencode/plugins/omt_q.ts` | +`foldProjectDrift()`, additive `project_drift` envelope field | EDIT (R4) |
| `.opencode/plugins/omt_status.ts` | active-project line + `metadata.project` | EDIT (R4) |
| `tests/scripts/omt/test_project_lifecycle.py` | all goldens (hermetic) | NEW (canary) |

**Why project_state.py is self-contained (not `tdd.state` reuse):** `tdd/state.py:34-37` reads `OMT_LEDGER_PATH` at **import time**; harnessc/pytest import order would freeze the wrong path. project_state.py reads env **per call** (~15 lines of jsonl IO duplicated deliberately). No `tdd` package coupling; harnessc stays stdlib-only at module scope (imports project_state lazily inside check functions... no — top-level `import project_state` is fine since project_state has no import-time env reads; the env is read per call).

## 2. Ledger records (truth; everything else projects)

```json
{"ts":"auto","kind":"project","op":"create|close|reopen|archive","project":"<slug>","session":"…","note":"…","archived_to":".projects/archive/<slug>"}
{"ts":"auto","kind":"project_link","project":"<slug>","feature":"<feature-slug>","origin":"scaffold|inferred|backfill|manual","session":"…"}
```

**Derivations (project_state.py):**
- `read_ledger_all()` — glob `ledger-[0-9]{6}.jsonl` (all archives, sorted) + hot, chronological (fixes F1: latest+hot insufficient for month-spanning links).
- `derive_links(records)` — latest-wins per feature: `{feature: {project, origin, ts}}`; reverse index `{project: [features]}`.
- `derive_state(slug, records, links)` — fold `project` records: last op `close`→`complete` · `archive`→`archived` · `create|reopen`→`active` if ≥1 link else `draft`. No events → `unknown`.
- `project_of(feature)` — latest link for the feature.
- `manifest_rows()` — per project: `(slug, state, features sorted, created ts, last-event ts)`; archived in a separate section with `archived_to`.

## 3. `project.py` CLI contract

| Cmd | Effect | Exit codes |
|---|---|---|
| `new "<name>" [--slug s]` | slugify; create `.projects/meta/<slug>/{PROJECT.md,CURRENT_STATE.md}` from templates; `create` record; sync manifest | 0 ok · 2 exists/empty-slug |
| `link <feature> <project> [--origin manual]` | `project_link` record; **idempotent** (same project+feature latest → no-op message) | 0 · 2 unknown project home |
| `log <slug> "<note>"` | append to today's `## <date>` CURRENT_STATE block (create `(auto — project.py log)` block if absent) | 0 · 2 unknown slug |
| `status [slug]` | print derived table (one or all) | 0 |
| `close <slug> [--force]` | refuse (exit 3) if any linked feature has no `complete` record, unless --force; `close` record; Status header → `**complete**`; sync | 0 · 2 · 3 in-flight |
| `archive <slug>` | move dir → `.projects/archive/<slug>/`; `archive` record w/ `archived_to`; sync | 0 · 2 not complete (close first) |
| `reopen <slug>` | move back if archived; `reopen` record; header → derived; sync | 0 · 2 not closed |
| `sync` | regenerate `.projects/meta/META.md`; reconcile every Status header with derived state (report flips) | 0 |

`close --archive` = close + archive in one run. All writes via project_state (env-redirectable → hermetic goldens).

**Status header literal (template-guaranteed):** line 3 of PROJECT.md is `> Status: **draft** · ...`. The sync/flip rewrites only the `**<state>**` span via regex `(> Status: \*\*)([a-z]+)(\*\*)`; unparseable → skip + stderr note (never corrupt prose).

## 4. harnessc checks (build errors; registered beside check_work_done_max)

1. `check_projects_structure` — each `.projects/meta/<slug>/`: PROJECT.md + CURRENT_STATE.md exist · no `*.bak` anywhere under `.projects/` · CURRENT_STATE dates newest-on-top (first two `## YYYY-MM-DD` headers non-increasing). Archive root exempt.
2. `check_projects_links` — full fold: link→project home exists (or archived) · link→feature dir exists in `2.requirements/features/` when feature matches `^feature_\d+\.` · no duplicate (project,feature) pairs · no link with ts > close ts on complete/archived projects.
3. `check_projects_resume` — PROJECT.md bytes > `@var project_resume_threshold_bytes` (16384) ⇒ `^## (New Session Quick Start|Resume)` within first 80 lines.
4. `check_projects_status` — header state ∈ {draft,active,complete,archived} ∧ == derived state; error text ends `→ run: uv run scripts/omt/project.py sync`.
5. `check_projects_manifest` — `.projects/meta/META.md` exists; its rows == `manifest_rows()` projection (state + feature lists).

## 5. TS deltas

- **`omt_shared.ts`:** `readLedgerAll(root?)` — glob all `ledger-*.jsonl` + hot (mirrors py fold).
- **`phase_gate.ts` `omt_phase`:** after the phase record write, resolve the artifact path (existing resolveArtifact); if it matches `^\.projects/meta/([^/]+)/` and `project_of(feature)` is null → `appendLedger({kind:"project_link", project, feature, origin:"inferred", session})`; response line `Project: linked → <slug> (inferred from design_doc)`.
- **`phase_gate.ts` `omt_complete`:** after `syncWorkMdFromLedger`, `syncProjectLogFromLedger(feature)`: link? none → result note `no project link — project.py link if this work belongs to a project home`. Linked → CURRENT_STATE.md of the owning home: if no block matching `feature.*Done` → insert after the header `---` divider:
  ```
  ## <YYYY-MM-DD> (auto — <feature> Done)
  - shipped: <task_type> · test report @ 6.testing/features/<feature>/test_report.md
  - logged by omt_complete; expand by hand if resume needs more.
  ```
  Fail-open try/catch (syncWorkMdFromLedger precedent).
- **`omt_q.ts`:** `foldProjectDrift()` → additive `project_drift: [...]` in the drift envelope (F2: existing pins untouched). Classes: `stale-log` (linked complete-record ts > top CURRENT_STATE date) · `status-drift` (header ≠ derived) · `phantom-link` · `unlinked-project-backed` (phase.design_doc under `.projects/meta/<slug>/`, no link) · `iteration-log` (`git log -1 --format=%cs -- PROJECT.md` > top CURRENT_STATE date) · `aging-draft` (create > 21d, zero links).
- **`omt_status.ts`:** derive `project_of(active_unlock.feature)` (readLedgerAll) → line `Project: <slug> (<state>) · last log <date>` + `metadata.project`.

## 6. `.omt` deltas (R2)

```
@var projects_root : .projects/meta
@var projects_archive : .projects/archive
@var project_resume_threshold_bytes : 16384
```
Payload updates: `@doc comp.projects` (mechanic: project.py + checks + manifest), `@doc pth.projects` (unchanged paths), `@doc projects_home` (AGENTS.md line — watch `agents_md` budget: 2626+~120 ≤ 2816, F9). No new `@budget` (D7: resume-block check instead). No `@gate` (D8: non-gated). `@msg` additions for the 5 check error texts are NOT needed (harnessc errors are compiler output, not gate messages).

## 7. Testlist (TDD behaviors JSON — 16)

R1: ❶ new creates home+record+manifest ❷ link idempotent ❸ derive FSM (draft→active→complete→archived→reopen) ❹ log new-block + same-day merge ❺ close in-flight guard + --force + header flip ❻ sync regenerates manifest + reconciles headers.
R2: ❼ structure (missing pair/.bak/bad order) ❽ links (phantom/link-after-close; backfill-shaped ledger passes) ❾ resume-block ❿ status mismatch + hint ⓫ manifest staleness; docs-drift pins green after .omt build.
R3: ⓬ omt_phase inference writes origin:inferred once ⓭ omt_complete inserts auto-block idempotently; unlinked → note.
R4: ⓮ op=drift project_drift classes + U3 pins intact ⓯ omt_status project line present/absent.
R5: ⓰ backfill: 6 homes pass all checks; origin:backfill links; baseline blocks; .bak removed.

## 8. Round plan (receipt round-robin: one edit per file per e2e receipt)

- **R1** — 2 templates + project_state.py + project.py + test file (new files: first-edit OK; test-file creation under `omt_skip{scope:"tests"}` canary, then red hat) → e2e → receipt.
- **R2** — META_HARNESS.omt + harnessc.py + test file → `harnessc build` (regenerates AGENTS.md/nav.index/jsonc via bash — build output, not edit-tools) → e2e → receipt.
- **R3** — omt_shared.ts + phase_gate.ts + test file → e2e → receipt.
- **R4** — omt_q.ts + omt_status.ts + test file → e2e → receipt.
- **R5** — backfill (bash project.py runs; `.projects/` non-gated) + `.workflows/meta_harness/loops/meta_harness_project.md` stale-path fix (non-gated) + `5.implementation/` notes + e2e → receipt.

## 9. Risks / decisions taken at design

- **Full-fold cost** — ledger archives total ~1.1 MB (meta_harness_2 evidence); folding all per call is fine for CLI/status cadence (omt_q state already folds latest+hot per call; full fold is one glob more). No caching in v1.
- **iteration-log via git** — `execSync git log` in omt_q (as_of_commit precedent); if git fails → class omitted (fail-open).
- **Duplicate-link policy** — writers idempotent; check errors on dupes so a buggy writer surfaces at build, not silently.
- **Non-numbered slugs** (`feature_kb_akb`, `improvement00X`) — linkable; the feature-dir existence rule applies only to `^feature_\d+\.`.
