# Operation Spec 001 — feature_030.project_lifecycle operations

> Date: 2026-08-22 · Companion to design_001. Contract per operation: responsibility, inputs, effects, failures. Goldens in `tests/scripts/omt/test_project_lifecycle.py` pin these behaviors (testlist ❶–⓰).

---

## A. `project_state.py` (state layer — no CLI)

| Operation | Contract |
|---|---|
| `ledger_paths()` | Lazy: `$OMT_LEDGER_PATH` or `.meta/.omt/ledger.jsonl`; archives = sorted `ledger-YYYYMM.jsonl` siblings. Env read **per call**. |
| `read_ledger_all()` | All archives (oldest first) + hot, chronological; unparseable lines skipped. |
| `write_record(rec)` | Append `{ts: now-utc, **rec}` to hot ledger; rotate per cap (delegates to the same 64KB convention). |
| `derive_links(records)` | Latest-wins per feature → `{feature: Link(project, origin, ts)}`; dupes preserved for the check to flag. |
| `derive_state(slug, records, links)` | `unknown|draft|active|complete|archived` per §2 fold. |
| `project_of(feature)` | Latest link's project or None. |
| `manifest_rows()` | Rows for the GENERATED manifest (active table + archived table). |
| `sync_status_header(path, state)` | Regex-flip `> Status: **<state>**` span only; unparseable → return False, never corrupt. |

## B. `project.py` (CLI — bash entry, mirrors new_feature.py)

Pre/post use exit codes per design_001 §3. All commands end with `sync` side-effects (manifest + headers) except `status`/`log`.

1. **`new "<name>" [--slug s]`** — pre: home absent; post: dir + 2 template files + `create` record + manifest row. Failure: 2 (exists/empty slug).
2. **`link <feature> <project>`** — pre: project home exists; post: `project_link` (origin arg) unless identical latest link (no-op, prints "already linked"). Failure: 2.
3. **`log <slug> "<note>"`** — post: bullet appended under today's block (created as `(auto — project.py log)` if absent). Never reorders existing blocks.
4. **`status [slug]`** — read-only print: slug · state · features · created · last event.
5. **`close <slug> [--force]`** — pre: state active/draft; guard: any linked feature without a `complete` ledger record → exit 3 listing them; post: `close` record + header `**complete**` + sync.
6. **`archive <slug>`** — pre: state complete; post: dir moved to `.projects/archive/<slug>/` + `archive` record (`archived_to`) + sync. Failure: 2 with "close first".
7. **`reopen <slug>`** — pre: state complete/archived; post: move back if archived + `reopen` record + header to derived + sync.
8. **`sync`** — post: `.projects/meta/META.md` regenerated (GENERATED header); every Status header reconciled to derived; prints flip list.

## C. `phase_gate.ts` hooks (TS)

1. **design_doc inference (`omt_phase`)** — trigger: resolved artifact path matches `^\.projects/meta/([^/]+)/`; effect: exactly one `project_link{origin:"inferred"}` per feature (fold-checked); response gains `Project: linked → <slug>`. Never blocks the phase call (best-effort).
2. **ship-sync (`omt_complete`)** — trigger: `complete` record written; effect: idempotent auto-block inserted newest-on-top in the owning project's CURRENT_STATE.md (`## <date> (auto — <feature> Done)` + 2 bullets per design_001 §5); unlinked feature → output note only. Fail-open.

## D. harnessc checks (build errors — design_001 §4 1–5)

`check_projects_structure` · `check_projects_links` · `check_projects_resume` · `check_projects_status` · `check_projects_manifest` — each appends actionable `c.errors` (the status check ends with the `project.py sync` hint); archive root exempt from structure; non-numbered feature slugs exempt from feature-dir existence.

## E. omt_q / omt_status surfaces (read-only)

- `foldProjectDrift()` → `project_drift[]` additive field; classes: stale-log · status-drift · phantom-link · unlinked-project-backed · iteration-log (git; fail-open) · aging-draft (21d).
- `omt_status`: `Project: <slug> (<state>) · last log <date>` line + `metadata.project` when the active feature is linked; absent otherwise.
</content>
