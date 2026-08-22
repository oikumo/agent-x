# CURRENT_STATE: project_lifecycle

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-22 (auto — project.py log)

- shipped: major_feature · test report @ 6.testing/features/feature_030.project_lifecycle/test_report.md — 20/20 goldens, omt_tdd{op:done} ✅ (manual trigger: this session's plugins predate R3/R4 — GOTCHA_TS_NO_RELOAD; the omt_complete auto-sync fires from next session)

---

## 2026-08-22 (iter 1 — feature_030 BUILD COMPLETE: 20/20 goldens, done gate ✅, backfill landed)

### Done

- **Full build executed same-day** (Analysis → Design → Programming → Testing → Done, one session):
  - **Analysis** — `analysis_001_anchor_verification.md`: 13 anchors re-verified in-tree (A1–A13); 9 findings (F1 full-fold gap is the one substrate extension; F2 additive envelope tolerance; F7 manifest-writer=project.py).
  - **Design** — `design_001` + `operation_spec_001`: record shapes, module layout (project_state.py self-contained, lazy env), CLI contract (9 subcommands), 5 harnessc checks, TS deltas, 16-behavior testlist, R1–R5 receipt-round plan.
  - **R1** — templates + `project_state.py` + `project.py` (TestProjectPy 6/6).
  - **R2** — 3 `@var` + 3 doc payloads in the .omt; 5 `check_projects_*` in harnessc.py; `new_feature.py --project`; **real backfill in the same round** (checks flag every pre-mechanic home by design — a round never ends red): 7 homes adopted, 9 origin:backfill links, 7 baseline blocks, manifest generated, `.bak` removed, workflows/ stub, 6 headers normalized + 5 Quick-Start blocks added (resume-check convergence).
  - **R3** — `readLedgerAll` (omt_shared) + `maybeLinkProjectFromDesignDoc` / `syncProjectLogFromLedger` (phase_gate.ts, exported for hermetic bun probes) (17/17).
  - **R4** — `foldProjectDrift` (omt_q, additive `project_drift`) + `deriveActiveProject` (omt_status line + metadata) (20/20).
  - **Post-done correctness fix** — ship-sync guarded to terminal completions (Testing/Done) after catching that an Analysis-complete would write a premature "Done" block; stale-log fold + close guard aligned to terminal-phase semantics. 20/20 + 232/0 re-run green.
- **Gates:** `omt_tdd{op:done}` ✅ (2 KNOWN_SUITE_FAILURES tolerated; 0 regressions vs the 0-failure baseline) · `harnessc check` 0 errors (250 records) · build OK · e2e receipt fresh.
- **Test report:** `6.testing/features/feature_030.project_lifecycle/test_report.md`.

### Locked decisions (do not re-litigate without new evidence)

- D1–D8 (PROJECT.md) hold. Build-time additions: project_state.py self-contained (lazy env per call — tdd.state import-time env unusable for in-process goldens); phase_gate hooks exported standalone (probe without `$`-shelling); checks+backfill in ONE round (never end red); terminal-only ship semantics.

### In progress / Blocked

- _(nothing)_

### Next

- **Nothing pending in this project.** The mechanic is live: `project.py new|link|log|status|close|reopen|archive|sync|backfill`; `new_feature.py --project`; checks run on every `harnessc check`. Project stays **active** (user closes).
- Watch items (v1.1 candidates, not scheduled): iteration-log golden (git-in-probe); link-after-close fold precision; `new_feature.py` env-redirectability for a real-path --project golden; the `skip`-shadows-`phase` unlock quirk observed live this session (omt_status showed the canary skip as the active unlock, shadowing the tdd_mode phase record — same class as the meta_harness_3 noted candidate finding).

### Notes / context

- Live omt_q/omt_status/omt_complete surfaces activate next session (no TS hot-reload); this session's proof = 20 bun-probe goldens.
- WORK.md row flipped to [x] manually — `syncWorkMdFromLedger` only flips `[ ]` rows, and this feature tracked as `[~]`. Convention note for future `[~]` usage.
- Receipt round-robin honored: 4 e2e refreshes mid-build; multi-site TS insertions via sanctioned bash transforms (GOTCHA_RECEIPT_ROUND_ROBIN).

---

## 2026-08-22 (iter 0 — investigation → options → user-locked design → home + feature_030 created)

### Done

- **Investigation of how "project" exists in the harness today.** Convention documented at `META_HARNESS.omt:184/185/208` (PROJECT.md canonical + CURRENT_STATE.md log; non-gated); 6 homes exist; only 5 thin mechanical touchpoints (root_allowlist, 3 nav doc records, AGENTS.md line, unvalidated design_doc bridge at phase_gate.ts:128, think-gate on TA: files). Everything else manual.
- **Measured the real entity model (1 : 0..N)** — see PROJECT.md §Entity model table: meta_harness_2↔{020–023,026}, meta_harness_3↔{028,+B/C}, rag_v2↔{027,029,+2 bug fixes}, petri_net_library↔{}, workflows↔{}, ~20 features with no home.
- **Found 6 live drift instances** (PROJECT.md §Evidence): workflows/ missing CURRENT_STATE.md · feature_kb_akb `.bak` · rag_v2 stale-log (3 ships missing) · meta_harness_3 status drift (caught by hand at iter-4) · stale workflow path (`./projects/meta/project_<ID>/`) · no manifest/scaffolder/resume-rule/omt_q surface.
- **Presented tiered options (A→D)**; user directed deeper analysis under the 0..N constraint, then set the lifecycle model: **create → iterate → spawn features (for it or another) → close; omt phases are for features only.**
- **Locked the design in 4 user decisions** (PROJECT.md D1–D8): facts-not-verdicts write scope · full honest backfill · all four optional components (manifest projection, `log`, reopen, physical archive).
- **Created this home** (`.projects/meta/project_lifecycle/`) by hand — the mechanic didn't exist yet; the feature backfilled its own link (origin:backfill, dogfood note in PROJECT.md §Backfill).

### Locked decisions (do not re-litigate without new evidence)

- D1–D8 per PROJECT.md §Decisions log. Key forks already rejected: optional `project=` phase arg (decay evidence: 21 empty `feature:` records, meta_harness_2 U8) · name-derived links (feature_028↔meta_harness_3 share no substring) · edit-gating `.projects/` (chicken-egg bootstrap) · grandfathering the 6 homes (two classes forever) · fabricated retro-logging (poisons resume trust).

### Notes / context

- `project.py` is deliberately a bash CLI, not an omt_* tool (D5 — tool_schemas budget is zero-sum at 1094/1280).
