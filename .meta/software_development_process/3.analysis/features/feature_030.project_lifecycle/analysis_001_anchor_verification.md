# Analysis 001 — feature_030.project_lifecycle: anchor verification against the working tree

> Date: 2026-08-22 · Phase: Analysis · Design source: `.projects/meta/project_lifecycle/PROJECT.md` v1.0 (locked, D1–D8)
> Method: every anchor re-read in the working tree (not trusted from the project doc). Findings F1–F9 feed design_001.

---

## 1. Anchor verification (all confirmed)

| # | Anchor | Verified | Notes for design |
|---|---|---|---|
| A1 | `phase_gate.ts:99-132` resolveArtifact / detectDesignArtifact | ✅ | `record.design_doc` + `existsSync` → any existing path accepted (the unvalidated bridge). The design_doc inference hook slots here: path under `.projects/meta/<slug>/` → write `project_link` (origin:inferred). |
| A2 | `phase_gate.ts:367-414` syncWorkMdFromLedger | ✅ | Runs inside `omt_complete` after the `complete` record write (:361, best-effort try/catch). The ship-sync (`syncProjectLogFromLedger`) slots as a sibling call — same failure isolation. |
| A3 | `harnessc.py:705-715` check_work_done_max | ✅ | Check idiom: read file → compare → `c.errors.append(f"...")`. Registered in the check pipeline at :1085. |
| A4 | `harnessc.py:783-790` render_agents required-docs | ✅ | `projects_home` already a required doc — its payload update (R2) automatically re-projects into AGENTS.md. |
| A5 | `harnessc.py:658-666` check_comp_paths / `:685-702` check_root_hygiene | ✅ | Path-exists + allowlist idioms the project checks mirror. |
| A6 | `new_feature.py` scaffolder | ✅ | argparse + slugify + next-number + `render()` `{{VAR}}` substitution + `--dry-run`. `project.py` mirrors this shape; `--project <slug>` flag on new_feature.py writes the link record (origin:scaffold). |
| A7 | `omt_q.ts:650-666` drift op + `:696` dispatch | ✅ | `foldDrift()` → `{as_of_commit, drift_records, count_drift}`; unregistered per-op tools dispatched by the `omt_q` facade. Project drift = new fold + additive envelope field. |
| A8 | `omt_status.ts:290-295` output lines | ✅ | The active-project line slots into `lines[]`; metadata gets a `project` field. Ledger access via `sharedReadLedger()`. |
| A9 | `tdd/state.py:34-37` hermetic redirects | ✅ | `OMT_LEDGER_PATH` / `OMT_SNAPSHOT_DIR` env redirects — the golden-test substrate. `write_ledger` (:102-106) auto-stamps `ts`; no kind validation — new kinds flow. |
| A10 | `omt_shared.ts:174-176` readLedger | ✅ | Latest archive + hot only (see F1). |
| A11 | `receipt_guard.ts` + `omt_shared.ts:409` omtHarnessE2eStatus | ✅ | Second-edit guard; e2e-test-file exemption is **rel-equality** with `@var e2e_test` (comment :216) — only `test_omt_harness_e2e.py` itself is exempt; other `tests/scripts/omt/` files are receipt-guarded (first edit of a clean/non-existent file allowed by design). |
| A12 | `.meta/templates/feature.md` | ✅ | `{{NUM}}/{{TITLE}}/{{SLUG}}/{{DATE}}` substitution idiom for `project.md`/`current_state.md` templates. |
| A13 | `tests/scripts/omt/` landscape | ✅ | 18 test files; `test_omt_harness_e2e.py` (receipt), `test_omt_q.py` + `test_omt_q_state_summary.py` (envelope pins), `test_omt_docs_drift_pins.py` (doc/budget pins), `test_ledger_rotation.py` (rotation + KNOWN_SUITE_FAILURES shape pin). New home: `test_project_lifecycle.py`. |

## 2. New findings (feed design_001)

- **F1 — Latest+hot ledger fold is insufficient for project records.** Both `state.py:93-99 read_ledger()` and `omt_shared.ts:174 readLedger()` read **latest archive + hot only**. Project links/creates are long-lived (a link written in August must resolve in October; rotation cap 64KB rotates roughly monthly). Design needs full-fold readers: py `read_ledger_all()` (fold `_ledger_archives()` all + hot, state.py:85-90) and ts `readLedgerAll()` (sibling in omt_shared.ts); harnessc uses its own small fold (F4).
- **F2 — omt_q drift envelope: additive field is safe.** `test_omt_q.py:204-215` pins `count_drift` presence + `direction_b_only`, not exact envelope equality → add `project_drift: [...]` as a NEW field; do not touch `drift_records`/`count_drift` semantics.
- **F3 — omt_status project surface is derive-only.** Active project = project linked to `active_unlock.feature` (full-fold latest-wins per feature); render one line + `metadata.project = {slug, state, last_log_date} | null`. No stored active-project state (D1).
- **F4 — harnessc.py is stdlib-standalone** (imports: json/re/shlex/sys/dataclasses/pathlib — no local package imports). Project checks get a local ~15-line jsonl fold over `.meta/.omt/ledger*.jsonl` (glob all archives + hot), consistent with its standalone style; do NOT import `tdd/state.py`.
- **F5 — Receipt round-robin applies per file.** R1 touches 4 harness-surface files (2 new templates + `project.py` + new test file) — one edit each, one e2e receipt refresh per round (GOTCHA_RECEIPT_ROUND_ROBIN). New test file creation additionally needs the tests/ canary (F8).
- **F6 — g.tests canary vs TDD red hat.** `guardTestsPath` (receipt_guard.ts:61-74): TDD mode active → two-hats decide (red allows tests/); testlist state allows nothing → first test-file creation needs `omt_skip{scope:"tests"}` (TDD_BOOTSTRAP doc), then red hat covers subsequent tests/ edits.
- **F7 — Manifest writer = project.py, not harnessc.** project.py is the single writer of `.projects/meta/META.md` (tool-maintained file, WORK.md idiom); harnessc CHECKS manifest↔dirs↔ledger consistency (read-only). Avoids harnessc reading archives for generation; keeps the compiler pure over state.
- **F8 — KNOWN_SUITE_FAILURES shape pin.** `test_ledger_rotation.py` pins its shape; project goldens must use hermetic redirects (A9) and never touch the real suite state (feature_028 R10 precedent: hermetic test-dir for planted fixtures).
- **F9 — .omt record deltas (R2).** New `@var projects_root : .projects/meta`, `@var projects_archive : .projects/archive`, `@var project_resume_threshold_bytes : 16384`; payload updates for `@doc comp.projects`/`pth.projects`/`projects_home` (AGENTS.md line re-projects — budget `agents_md` 2816 must still fit: current 2626 B per meta_harness_3 evidence → ~190 B headroom, the projects_home payload grows ~120 B — feasible, verify at build).

## 3. What Analysis does NOT fix (deferred to design_001)

- Exact ledger record field sets (`project` / `project_link`), `project.py` CLI signatures + exit codes, check function signatures + error texts, manifest table format, golden-test list per round (testlist JSON), the draft→active flip literal convention in the template Status header.
- Whether `iteration-log` drift uses git-mtime or content-hash (git is available in harnessc context — `check_root_hygiene` precedent is fs-only; decide at design).

## 4. Conclusion

All 13 anchors verified against the working tree; no design-doc correction needed (contrast: meta_harness_3 needed R1/R2 anchor corrections — here the anchors were drawn from same-session reads). F1 (full-fold) is the one substrate extension; F2/F3/F7 keep every existing envelope/pin intact. **Ready for Design.**
