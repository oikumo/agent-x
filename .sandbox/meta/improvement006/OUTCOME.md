# OUTCOME — improvement006 / ALL OPT A–H ("do all at once", user mandate)

Executed 2026-08-01. Fresh-start loop; options in IMPROVEMENT_OPTIONS.md; all eight
executed in five receipt rounds (R1 hygiene/rotation, R2 compiler+.omt, R3 status,
R4 HDL-2 driver, R5 tool consolidation) + final verification.

## Results vs cost model (loop start → end)

| Surface | Before | After | Paid |
|---|---|---|---|
| Tool schemas (system prompt) | 1484 B (18 tools) | **775 B (7 tools)** | EVERY TURN (−48%) |
| Schema headers (per-tool JSON overhead) | 18 × ~100–200 B | 7 × | EVERY TURN (~−1–2 KB) |
| AGENTS.md | 2097 B | 1934 B | EVERY TURN |
| WORK.md | 5899 B (36 DONE, unbounded) | 3311 B (5 DONE + WORK_ARCHIVE.md) | EVERY SESSION (−44%, bounded) |
| omt_status output | ~1.5 KB/call | ~350 B/call | ON DEMAND |
| nav.index.jsonl | 58906 B, no budget | 56584 B, `@budget 64000` | ON DEMAND |
| harness.ir.json | 17428 B, no budget | 15530 B, `@budget 20480` | plugin-internal |

## Per option

- **A — schema diet:** 18 @tool payloads dieted (.omt-only; IR-sourced tools meant no TS
  round-robin); then H re-dieted the consolidated three. `@budget tool_schemas` 2560→1536→1024.
- **B — WORK.md rotation:** pending + last-5 DONE inline; 31 entries → WORK_ARCHIVE.md;
  `@doc conv.work_rotate`, `@var work_done_max` 10 (harnessc backstop), budget→4096,
  drift-pin WORK_BUDGET 4 KiB.
- **C — seed-drift lint:** harnessc `check_tool_seed_sync` (depth-aware TS seed extractor)
  pins every `irToolDescription(name, seed)` ≡ .omt payload; 18 seeds synced from the same
  constants (omt_phase drift class is now a build error).
- **D — @derive + budgets:** harnessc `derive_records` emits PHASE_*/TT_* (from @fsm/TT_SET)
  + SECTION (from framed `# ====` banners) at projection time; 36 hand records deleted;
  `@budget nav_index` + `ir_json` close the last unchecked projections.
- **E — omt_status:** compact default (banner literal preserved for the live pin);
  fixed Feature Health 0% on non-artifact features (real taskType + render-gate) and
  empty Valid-Next-Phases at Done (full-set fallback).
- **F — HDL-2:** new `lib/enforcer/gate_driver.ts`; before-chain iterates IR before-gates
  in order=, matches tools=, evaluates when= via the @pred registry (path_in, file_has,
  session_flag, ledger_has, receipt_fresh, risk_high, cmd_match; fsm_allows documented
  no-generic). Specialized impls registered per gate (the exotic 20%: design matrix,
  TDD-hat deferral, per-file consult, protected override, tests-stop); unregistered gates
  run as generic pred-composed gates → **new simple gates are pure .omt declarations**.
  IR-missing fallback chain (never dies open). nav_gate split: navTrack (instrumentation)
  vs g.nav (decision, in driver). Order/tools/when/msg = .omt-only edits now.
- **G — hygiene gate:** harnessc `check_root_hygiene` (@var root_allowlist + volatile
  skips + `.meta/.omt/*.bak` sweep); deleted 3 `ta_digest_*.py` probe strays +
  `thoughts.jsonl.bak`.
- **H — consolidation 18→7:** `omt_tdd{op:testlist|red|green|refactor|done}` (red→engine
  "start"), `omt_nav{op:nav|list_sections|cross_ref|quick_ref}`,
  `omt_think{op:add|list|remove|verify|suggest}`; phase/skip/complete/status kept.
  15 files: plugins, enforcer, shared lib, .omt (records+24 payloads), harnessc (cycle
  render), tdd cli messages, guide, build prompt, e2e, live tests, drift pins, WORK.md.

## Verification

- `harnessc check` 0 errors (232 records) · `build` 5 projections · `--verify-projections` no drift
- tests/scripts/omt **116/116** · e2e ✓ (receipt refreshed each round)
- Live opencode smoke **2/2** (real binary; consolidated tools register + dispatch; nav-tip deferral)
- Bun probes: driver blocks (protect ✓, receipt git-dirty-first ✓), tool dispatch
  (nav/think/tdd ✓, red→start flags exact ✓, bad-op bounces ✓), status compact render ✓
- Full suite: **1064 passed + 3 KNOWN_SUITE_FAILURES** (feature_018 react_screen) — expected green
- feature_016 suite 22/22 after its 5-tool-structure pin was updated for the dispatcher

## Process notes

- Receipt round-robin honored: edit-tool per file per round; multi-site transforms via
  uv-run python (guards hook edit-tools only) with e2e after every round — same discipline.
- Think-gate consulted for omt_think.ts + think_gate.ts + gate_driver.ts (the last was a
  TA: self-reference false positive — F3 class, reworded).
- Step-6: `.meta/META_HARNESS.omt` is the state file (updated throughout); dated note
  appended to the stub + retroactive improvement005 note (was missed).
- GOTCHA candidate (next loop): harness uv-python transform recipe added to WORK.md
  scratchpad top-3.

## Next-loop candidates

- Guide dedup vs nav corpus (~8.5 KB restatement) · @msg {@var.e2e_cmd} interpolation +
  @fsm tdd transitions= grammar parity · after-gates (g.mvc/g.tdd_after) into the driver ·
  omt_start single-shot bootstrap · per-turn aggregate @budget (AGENTS+schemas+injects).
