# Implementation notes 001 — feature_030.project_lifecycle build rounds

> Date: 2026-08-22 · Phase: Programming · Design: `4.design/features/feature_030.project_lifecycle/design_001_project_lifecycle.md`

## Round log (receipt round-robin honored: one edit per file per e2e receipt)

| Round | Files | Goldens | Result |
|---|---|---|---|
| R1 | `.meta/templates/project.md` + `current_state.md` + `scripts/omt/project_state.py` + `scripts/omt/project.py` + test file (new) | TestProjectPy ❶–❻ | 6/6 GREEN |
| R2 | `.meta/META_HARNESS.omt` (3 @var + 3 doc payloads) + `harnessc.py` (5 checks + registration) + `project_state.py` (IR-var alignment + header normalize) + `project.py` (backfill) + `new_feature.py` (--project) + test file | TestHarnesscChecks ❼–⓫ + TestScaffoldLink + TestBackfill | 13/13 GREEN |
| R2-backfill | real ledger + 7 homes (bash `project.py` runs; `.projects/` non-gated) | 7 backfill creates · 9 origin:backfill links · 7 baseline log blocks · manifest generated · stray `.bak` removed · `workflows/` CURRENT_STATE stub · 6 headers normalized/machine-inserted · 5 Quick-Start blocks added | `harnessc check` 0 errors (250 records) |
| R3 | `omt_shared.ts` (readLedgerAll) + `phase_gate.ts` (2 exported hooks + 2 call sites; multi-site bash transform per GOTCHA_RECEIPT_ROUND_ROBIN) | TestPhaseGateProjectHooks ⓬⓭ (4 bun probes) | 17/17 GREEN |
| R4 | `omt_q.ts` (foldProjectDrift + additive `project_drift`) + `omt_status.ts` (deriveActiveProject + line + metadata) — bash transform | TestOmtQProjectDrift ⓮ + TestOmtStatusProject ⓯ | 20/20 GREEN |

## Decisions taken during the build

- **project_state.py is self-contained** (lazy env-per-call paths; IR @var override with literal fallback — state.py:42-56 idiom). No `tdd.state` import: its env reads are import-time, unusable for hermetic goldens from an already-imported process.
- **The two phase_gate hooks are exported standalone functions** (`maybeLinkProjectFromDesignDoc`, `syncProjectLogFromLedger`) so bun probes test them hermetically without omt_complete's `$`-shelling (tdd validate-exit) in the probe path.
- **R2+R5-merge:** the checks flag every pre-mechanic home by design, so the backfill landed in the SAME round — a round must never end with `harnessc check` red.
- **Header normalization bug caught live:** first normalize pass left a stray `**` after the version span (strip("*") only trims string ends). Fixed by unwrapping the leading `**...**` pair; the 3 affected headers (rag_v2, workflows, petri_net_library) repaired by hand; meta_harness_2/meta_harness_3 same class.
- **feature_kb_akb had no `> Status:` line at all** — machine header inserted by hand (normalize only rewrites existing Status lines).
- **TS plugins don't hot-reload** (GOTCHA_TS_NO_RELOAD): the live omt_q/omt_status surfaces activate in the NEXT session; this session's proof is the 20 bun-probe goldens.

## Verification evidence

- 20/20 feature goldens (TDD: 4 red→green cycles, node-consistent).
- 232 passed, 0 failed in `tests/scripts/omt/` (3 live-binary deselected) after R4.
- `harnessc check` 0 errors (250 records); `harnessc build` OK (5 projections).
- Live: `omt_q{op:drift}` on the real repo — pre-R4 plugin in this session (no hot-reload); golden probes prove the new fold.
