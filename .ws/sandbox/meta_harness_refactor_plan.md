# Meta Harness Refactor — Plan

> **Status:** PROPOSED — awaiting execution approval
> **Date:** 2026-07-25
> **Baseline commit anchor:** `d497dce30817ca93a057592b625c1a1bce9c7bf5` (`d497dce`, "feature_023")
> **Task type:** `refactor` (per RULE_RIGOR: phase declaration only, no design doc required)
> **Uncommitted state at planning time:** 30 changed paths (test-consolidation deletions from feature_023.test_refactor_live_only, `M .opencode/plugins/omt_status.ts`, `M WORK.md`, `M pyproject.toml`). Decision: do NOT commit; refactor proceeds on top of this tree state, anchored to the commit above for diff/revert reference.

---

## 1. Current State Inventory

| Layer | Component | Lines | Issues |
|---|---|---|---|
| Plugins (TS) | `.opencode/plugins/omt_enforcer.ts` | 1184 | Monolith: 8 concerns in one hook body (phase gate, TDD two-hats, think-gate, nav-gate, e2e-receipt guard, protected files, MVC++ after-hook, digest/nav-reminder emission) |
| | `.opencode/plugins/omt_think.ts` | 819 | 6 tools + all helpers in one file |
| | `.opencode/plugins/omt_status.ts` | 368 | Duplicates ledger/path logic |
| | `.opencode/plugins/omt_nav.ts` | 276 | Duplicates doc-path logic |
| Scripts (Py) | `scripts/omt/tdd_check.py` | 825 | 9 subcommands in one file |
| | `scripts/omt/mvc_check.py`, `new_feature.py` | 366 | OK — leave as-is |
| State | `.meta/.omt/ledger.jsonl` | ~108 KB | Unbounded growth, no rotation |
| Docs | META_HARNESS.md (209) / AGENTS.md (74) / omt_agent_guide.md (718) | ~1000 | Hand-synced; drift already present (see P2) |
| Tests | `tests/scripts/omt/` (6 files) + feature dirs | — | Source-pin tests grep enforcer content; brittle under refactor by design |

## 2. Problems (evidence-based)

- **P1 — Mass duplication across the 4 TS plugins.** `REPO_ROOT`, `LEDGER_PATH`, `isProtectedPath`, `PROTECTED_FILES`, ledger read/append, e2e-receipt logic: 7–17 grep hits *per file*. Cross-cutting changes must be applied N times — the F14 MIRRORED bug (before-hook fix applied with after-hook semantics) happened precisely this way.
- **P2 — Doc drift.** META_HARNESS.md `COMP_ENF`/`COMP_STS`/`COMP_NAV`/`COMP_THINK` still say `.opencode/plugin/` (singular); actual dir is `plugins/` since the BUG-B rename. `opencode.jsonc` references `omt_nav.js` (explicit `.js`; works only via resolver fallback — flagged in WORK.md as pending approval) and its line-3 comment references the singular path.
- **P3 — Known latent bugs** (WORK.md scratchpad): `omt_think_reindex` over-prunes anchor-less records (dropped 3 valid live records); `omt_done` strict full-suite unreachable (3 pre-existing feature_018 failures + 2 ledger-window-sensitive tests); TESTLIST two-hats chicken-and-egg on tests/ creation.
- **P4 — Brittle test anchors.** Source-pin tests grep enforcer *content/lines*; any refactor breaks anchors by design and needs a planned pin rewrite.
- **P5 — Session-state fragmentation.** Process-lifetime `Map`s inside the enforcer (nav state, injected paths, reminder state) with no shared abstraction.

## 3. Workstreams (ordered low → high risk; each independently shippable)

### R0 — Drift & hygiene fixes (~30 min, zero code risk)
- META_HARNESS.md: `.opencode/plugin/` → `.opencode/plugins/` (COMP_ENF, COMP_STS, COMP_NAV, COMP_THINK, NAV_FILES, XREF_NAV, XREF_NAV_ENF, XREF_THINK, XREF_THINK_GATE).
- `opencode.jsonc`: `"omt_nav.js"` → `"omt_nav"`; fix line-3 comment to `plugins/` plural. *(Clears the WORK.md pending-approval follow-up — this plan constitutes the approval record.)*
- Refresh e2e receipt: `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`.
- **Verify:** 68 static tests GREEN + receipt fresh.

### R1 — Shared TS lib: `.opencode/lib/omt_shared.ts` (~1.5 h)
- Extract: repo-root resolution, `LEDGER_PATH`/state paths, `isProtectedPath`/`PROTECTED_FILES`, ledger read/append, e2e-receipt status check, glob→regex.
- 4 plugins import from it; delete in-file copies.
- Note: enforcer session-state `Map`s are deliberately NOT extracted here — they are enforcer-internal and move to `lib/enforcer/session_state.ts` in R2.
- **Constraint:** opencode loader requires plugin files (`plugins/*.ts`) to export ONLY `export default async () => ({tool:{...}})`. A `lib/` dir is not a plugin glob target, so named exports are safe — **must verify loader only globs `plugins/*.ts`** (live test after extraction).
- **Verify:** live `opencode run` + one call per tool (phase, status, nav, think); 17 live tests GREEN; e2e receipt refresh between guarded edits (receipt-rebuild cycles per gotcha).

### R2 — Split the enforcer monolith (~3 h)
- `omt_enforcer.ts` → thin composition root (~200 lines): hook registration + dispatch only.
- New modules under `.opencode/lib/enforcer/`: `phase_gate.ts`, `tdd_hats.ts`, `think_gate.ts`, `nav_gate.ts`, `receipt_guard.ts`, `mvc_after.ts`, `session_state.ts` (shared Map abstraction, fixes P5).
- Rewrite source-pin tests as coarser contract pins (hook names, guard order, error-message prefixes) — accept planned pin breakage (P4).
- `omt_enforcer.ts` is think-gated (TA: at :1070) → `omt_think_list` consult before editing; re-anchor the TA: comment into the appropriate lib module.
- **Verify:** 17 live tests GREEN; rewritten pins GREEN; full harness suite; receipt cycles between chunks (batch edits per Write-tool gotcha).

### R3 — Split `tdd_check.py` (~1 h)
- 825 lines → `scripts/omt/tdd/` package: `cli.py` (arg dispatch), `state.py` (ledger/state IO), `gates.py` (two-hats, validate-exit), `ast_checks.py` (true-RED, coverage gaps).
- Keep `scripts/omt/tdd_check.py` as a thin compat shim — enforcer and docs call `tdd_check.py <subcommand>`; no call-site changes.
- **Verify:** `tests/scripts/omt/test_tdd_check.py` + feature_023 harness suite GREEN.

### R4 — State hygiene + latent bugs (~1 h)
- `ledger.jsonl` rotation: size-cap (e.g. 64 KB) → archive to `ledger-YYYYMM.jsonl`; readers scan current + latest archive (8 h window makes this safe).
- Fix `omt_think_reindex` over-prune: keep anchor-less records when the literal TA: line still exists on disk (P3).
- `omt_done`: add a known-failure allowlist (feature_018 ×3, ledger-window ×2) OR formally document the `omt_complete{advance_to:Testing→Done}` exit as the supported path — **decision point, default: allowlist**.
- TESTLIST chicken-and-egg (P3): tests/ creation is blocked by the two-hats gate before any RED exists → **decision point**: (a) auto-unlock tests/ *new-file creation* during TESTLIST state, or (b) formally document the `omt_skip{scope:tests}` bootstrap as the supported path — **default: (b) document** (auto-unlock weakens the canary model; feature_021/022 prior art uses the logged skip).
- **Verify:** reindex unit test (3 known live records survive); rotation unit test; live think suite.

### R5 — Docs single-source (~30 min)
- Re-sync AGENTS.md ↔ META_HARNESS.md tables (components, tools, phases).
- Add a drift-pin test: assert AGENTS.md component paths match META_HARNESS.md COMP_* entries and both match on-disk reality (prevents P2 recurrence).
- **Verify:** new pin test GREEN; nav tools (`omt_list_sections`) still resolve all SECTION: headers.

### Non-goals (explicit — do not let scope grow)
- No split of `omt_think.ts` (819 lines but cohesive: 6 tools over shared helpers; R1's shared-lib extraction is the only reuse win).
- No changes to `mvc_check.py` / `new_feature.py` (healthy, §1).
- No new dependencies, no opencode version change, no `dist/` reintroduction (deleted 2026-07-20, proven unused).
- No gate/rule semantics changes — refactor preserves behaviour; the ONLY intentional behaviour changes are R4's fixes (reindex, rotation, decision-point outcomes) and R0's doc/config drift corrections.

## 4. Execution Protocol (per workstream)

1. `omt_phase{task_type:"refactor", phase:"Analysis", scope:"R<n> done definition", feature:"meta_harness_refactor"}`
2. Work in receipt-rebuild cycles for guarded files (`.opencode/plugins/*.ts`, `opencode.jsonc`): batch edits → `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` → next batch.
3. `omt_complete{feature:"meta_harness_refactor", advance_to:"Done"}` per workstream; update WORK.md line per completed R.
4. No `git commit` without explicit user request (NEVER rule); diff against baseline anchor `d497dce` for review.

## 5. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Plugin loader rejects lib imports or named exports | R1 first live check: `opencode run` + tool call per plugin before proceeding to R2 |
| Source-pin tests break under R2 (by design) | Planned pin rewrite to coarser contract anchors; count as R2 deliverable |
| e2e-receipt second-edit guard stalls multi-edit refactors | Receipt-rebuild cycles; batch each plugin's changes into minimal writes (Write-tool large-payload gotcha) |
| Think-gate on `omt_enforcer.ts` / `omt_think.ts` | `omt_think_list{path}` consult before each edit session; re-anchor TA: comments post-move |
| Behaviour drift under refactor | 17 live tests are the contract; they must stay GREEN per workstream, not only at the end |
| Mixing with 30 uncommitted paths | Baseline anchor `d497dce` recorded above; refactor touches disjoint paths except `omt_status.ts` (R1) — review that diff jointly |

## 6. Effort Summary

R0 ~30m · R1 ~1.5h · R2 ~3h · R3 ~1h · R4 ~1h · R5 ~30m → **~7.5 h total**, sequenced R0→R5; R3 and R4 are mutually independent and both independent of R2.
