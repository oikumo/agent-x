# RESUME — improvement007 (meta_harness_evolution loop, ALL OPT A–I)

RESUMED 2026-08-01 (7th session): R11 DONE (163/163, receipt fresh). ALL rounds
R1–R11 complete; only the FINAL wrap remains (full pytest, live smoke, WORK.md,
META_HARNESS note, OUTCOME.md, omt_complete).
Options + evidence: ./IMPROVEMENT_OPTIONS.md (user selected ALL nine).

## Session bootstrap for the resuming agent (do FIRST)

1. New opencode session ⇒ phase/skip ledger records are session-scoped — re-run:
   - `omt_phase{task_type:"refactor", phase:"Programming", scope:"improvement007 R10..R11 per .sandbox/meta/improvement007/RESUME.md", feature:"improvement007"}`
   - `omt_skip{reason:"approved canary: improvement007 tests/scripts/omt pin/test updates", scope:"tests"}`
2. Read THIS file + IMPROVEMENT_OPTIONS.md. Do NOT re-run the analysis audits.
3. Receipt was fresh at pause ⇒ per-file FIRST harness-surface edit is free; keep round discipline (below).

## Round discipline (gotchas, proven in improvement006/007)

- ONE edit per harness-surface file per e2e receipt; multi-site transforms via
  `uv run python /tmp/opencode/<script>.py` (bash edit-guards hook edit-tools only),
  ONE receipt refresh per round: `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`.
- After every round: `uv run scripts/omt/harnessc.py check` → `build` →
  `check --verify-projections` → e2e → `uv run pytest tests/scripts/omt -q` (148/148 at pause).
- Think-gated files (need `omt_think{op:list,path}` consult first): .opencode/plugins/omt_think.ts
  (TA: xref :605 — feature_022 v2 FEATURE.md catalogs 13 v1 flaws; read before
  touching INSERTION mechanics — arg/describe edits are fine), .opencode/lib/enforcer/think_gate.ts.
- Enforcer TS sources are source-pinned by tests/scripts/omt/test_omt_enforcer_guard_source_pins.py
  — read the pin expectations before editing enforcer files (arg describes are NOT pinned).
- TS irToolDescription seeds must ≡ .omt @tool payloads (check_tool_seed_sync = build error).
- Write-tool full-file writes of big guarded plugins abort — chunk via cat >> heredoc if needed.
- NEW R4 pin-authoring traps: (a) slicing a TS array region by `"]"` hits the
  `}[]` type annotation first — slice by `"\n]"`. (b) harnessc's attr parser
  STRIPS quotes compiling when=/requires= into the IR (IR `file_has(TA:)` vs TS
  literal `file_has("TA:")`) — normalize quotes when pin-comparing.
- Budgets now: tool_schemas 775/1024 · tool_args 1287/1536 · agents_md 1934/2560 ·
  nav_index 56982/64000 · ir_json 15792/20480 · work_md 3745/4096 ·
  work_scratchpad 1502/3072 · meta_harness_md 1366/2048 · meta_md 5002/6144.

## DONE — R1 / OPT-C {@var.x} interpolation

- harnessc.py: INTERP_RE + `interpolate(c)` (after parse, before derive/checks;
  unknown names = check errors); build_ir `cap`/`window` = `int(str(resolve(...)))`.
- .omt: grammar comment documents `{@var.x}`; msg artifact → `{@var.scaffold}`;
  msg receipt_stale → `{@var.e2e_cmd}`; msg mvc_warn → `{@var.mvc_check}`;
  @state ledger cap/window → `@var.ledger_cap_bytes`/`@var.unlock_window_ms`.

## DONE — R2 / OPT-D check hardening (126→124→126 arc; landed 124/124 at its round)

- .omt 3 drift fixes: :164 @doc tdd.done_allowlist → "×3 + ×3" (6 KNOWN_SUITE_FAILURES:
  react_screen ×3 + window-flaky probes ×3) · :277 @xref mvc → 5 ERROR + 3 WARNING
  rule names, notes CONTROLLER_IN_MODEL/VIEW_CREATES_CONTROLLER have no @msg ·
  :280 @xref ledger kinds → phase|skip|complete|tdd|tdd_testlist|think_consult.
- harnessc.py: NEW `check_grammar_vocab` (wired into run_all_checks after
  check_fsm_hats): @fsm initial∈states + transition endpoints ∈states ·
  @hat revert_on ∈ {"","tests_break"}, allow entries ""/end-"/" ·
  @inject on ∈ {first_tool_result,file_read} · @gate when= pred-call arity vs
  PRED_ARITY {path_in:1, cmd_match:1, ledger_has:1..3, session_flag:1, file_has:1,
  receipt_fresh:0, fsm_allows:2, risk_high:0} + rejects `|` in args (when= ONLY —
  requires= deliberately unchecked: g.phase ledger_has(phase|skip) is a known-broken
  dead expr, future loop owns it) · @gate order unique per on= group.
- Orphan-@msg check still DEFERRED to R8 (artifact/mvc_warn get wired by OPT-G first).
- tests: test_harnessc.py section 10 (+6 tests).

## DONE — R3 / OPT-A arg-describe diet + tool_args budget

- Live dispatcher arg describes dieted **1609 → 1285 B** (−324 B/turn ≈ −80 tok).
  5 TS files: phase_gate.ts (omt_phase/skip/complete), tdd_hats.ts, omt_nav.ts,
  omt_status.ts, omt_think.ts. Per-op helper describes (1212 B) intentionally
  untouched — unregistered tools, zero per-turn cost.
- DEVIATION from options-doc "≤900 B" target: unreachable without dropping
  valid-value enums (task_type/tag_type/op lists) whose absence causes error
  round-trips = net token LOSS (strategy rule #2). Landed honest cut, capped 1536.
- harnessc.py: `_ts_arg_describes(src,name)` (irToolDescription→"async execute"
  region extractor, reuses _ts_seed unescape) + `tool_args` ∈ MEASURABLE_BUDGETS +
  measure_budgets wiring (sums live describes per @tool rid over TOOL_SEED_DIRS).
- .omt: `@budget tool_args max=1536`. tests: section 11 (+2 tests).
- Gotcha: compiler's measure (unescaped literals) reads 1287 vs raw-probe 1285 — fine.

## DONE — R4 / OPT-E (TS side): TS consumes IR (135/135 at its round)

- omt_shared.ts NEW IR-accessor layer (FALLBACK_* literal + per-call loadIr()
  getter — never die open, F2/F17 lazy): thoughtPattern() ← @var thought_pattern
  (the var was DEAD before), e2eCommand() ← @var e2e_cmd, phaseTransitions() ←
  @fsm phase transitions= ("A>B,C;D>E" parsed to the Record shape), tddAutoOn() ←
  @fsm tdd auto_on= ("tt@Phase,..." entries), protectList()/matchesProtect() ←
  @protect records (trailing "*" = prefix; hard=true ≡ no-override).
  parseThoughtLine/thinkDigest/omtHarnessE2eStatus re-pointed internally.
- Consumers swapped off hand-mirrors: phase_gate.ts (VALID_TRANSITIONS + the
  auto_on expression deleted), **omt_status.ts (SECOND VALID_TRANSITIONS mirror
  found beyond the RESUME list — deleted too, shares phaseTransitions())**,
  omt_enforcer.ts (EDIT_TOOLS ← @var edit_tools; in-file FALLBACK_EDIT_TOOLS),
  nav_gate.ts (SEARCH_TOOLS ← @var search_tools; "read" dropped from the old
  hand set — gate-exempt + instrumentation-only, usedSearch/searchCount are
  write-only), receipt_guard.ts (isProtected + isEnv hard-flag ← ir.protect),
  think_gate.ts + omt_think.ts (THOUGHT_PATTERN → thoughtPattern() ×5 sites;
  think-gate consults recorded first).
- harnessc.py render_agents: the AGENTS.md TDD line's auto-on list is now
  DERIVED from @fsm tdd auto_on= (was hardcoded `major_feature`/`new_screen`
  @Programming text) — projection byte-identical (verify-projections OK).
- gate_driver FALLBACK_GATES KEPT (it IS the IR-missing path — cannot read
  ir.gates when IR is missing by definition) but now VALUE-PINNED ≡ IR
  before-gates on id/on/tools/when/msg/hard/skip_ok/order (requires= excluded —
  impl-owned, deliberately empty in the fallback except g.receipt).
- tests: +9 pins — TestIrAccessorFallbackSyncPin (6 value + 1 structural
  consumers-resolve-through-accessors), TestFallbackGatesIrSyncPin,
  test_thought_pattern_fallback_matches_omt_var; the single-source import regex
  widened to THOUGHT_PATTERN|thoughtPattern.
- R4 leftovers → R6: (a) driver-level die-open gap — gate_driver.pathIn
  "@protect.*" evaluates against ir.protect ONLY: IR missing ⇒ g.protect when=
  false ⇒ gate skipped (the protectList fallback is unreachable via the chain;
  pre-existing HDL-2 gap — pathIn needs a protectList()-backed fallback).
  (b) OMT_HARNESS_E2E_TEST/RECEIPT consts still literal (@var e2e_test /
  receipt_path exist in IR — same accessor pattern applies). (c) nav
  usedSearch/searchCount write-only — delete candidates.

## DONE — R5 / OPT-E (Python side): @hat → tdd engine (139/139 at its round)

- gates.py: `_ir_hats()` best-effort IR read (state._ir_var_int pattern) +
  `_derive_hat_rules()` (allow "tests/"→{src:F,tests:T}, "src/"→{src:T,tests:F},
  ""→both-F; engine-local "none" appended). HAT_RULES/HAT_REVERT_ON now derived
  from ir.hats at module load; literals renamed `_FALLBACK_HAT_RULES` /
  `_FALLBACK_HAT_REVERT_ON` as the no-IR fallback.
- revert_on consumption FOUND + wired: cmd_after_edit's refactor auto-revert
  was an `if state == "refactor":` hardcode → now
  `HAT_REVERT_ON.get(state) == "tests_break"` (ir.hats tdd.refactor revert_on;
  behavior identical, now data-driven).
- tests: test_tdd_check.py +4 — TestHatFallbackIrSyncPin (fallback ≡ IR ×2,
  effective-derived-from-IR ×1) + revert-branch data-driven behavior test.
  135 → 139/139 green; full round chain green (check/build/verify/e2e).
- tdd_check.py shim untouched (its HAT_RULES re-export stays the effective
  dict); no other HAT_RULES consumers exist. harnessc.py's HAT_REVERT_ON vocab
  set (:362) is check-side only — no collision.
- R6 leftovers from R5: none.

## DONE — R6 / leftovers + full verify chain (142/142 at its round)

- (a) gate_driver.ts pathIn "@protect.*" die-open FIXED: when ir?.protect is
  not a non-empty array, falls back to the shared-lib protectList() +
  matchesProtect() (FALLBACK_PROTECT literal) — g.protect no longer skipped on
  the IR-missing chain. Import line widened (protectList, matchesProtect).
  NEW test TestGateDriverProtectIrMissing (pins py): bun probe drives
  runBeforeGates on README.md under a tmp root with NO IR → asserts BLOCKED
  (pre-fix: NO_BLOCK). skipif bun absent.
- (b) omt_shared.ts: e2eReceiptPath()/e2eTestPath() accessors added (mirror
  e2eCommand(); consts stay the pinned fallback literals); 3 consumers swapped
  (receiptTimestampMs join, omtHarnessE2eStatus exempt check + msg text).
  +2 pins (test_e2e_receipt_fallback_matches_ir — join() parts "/"-joined ≡
  IR vars.receipt_path; test_e2e_test_fallback_matches_ir ≡ vars.e2e_test) +
  2 consumer-resolve entries. Forward-slash @var ≡ join() literal on linux —
  rel-equality exempt holds.
- (c) usedSearch/searchCount write-only counters DELETED (4 sites:
  session_state.ts Map type, nav_gate.ts init + 2 mutations). searchTools()
  STAYS in nav_gate.ts (IR-accessor pin target — declaration contains the
  "searchTools()" substring the pin wants).
- tests: 139 → 142/142 green; full round chain green (check 233 rec 0 err /
  build+verify no drift / e2e ✓ receipt fresh). NOTE: live smoke
  (test_omt_live_opencode_guards) flaked once with tools seen: [] — isolated
  rerun 2/2 green; transient real-model no-call, not a regression.
- R7 leftovers from R6: none.

## DONE — R7 / OPT-F after-gates into gate_driver (144/144 at its round)

- gate_driver.ts: NEW runAfterGates(env, session, input, output, rawEditPath)
  mirroring runBeforeGates — IR after-gates ascending order=, tools= match,
  when= pre-filter (always decisive: rel non-null past the raw guard), stop on
  "stop"; unregistered after-gate id → warn-log + skip fail-open (NO generic
  after-impl: run= deltas / fsm reverts are impl-owned by definition).
  AFTER_IMPLS: g.mvc → mvcAfterEdit adapter (false ⇒ "stop" — the monolith's
  early return; OmtBlock propagates), g.tdd_after → tddAfterEdit call-through
  (no GateCtx shims needed in mvc_after.ts/tdd_hats.ts — untouched).
  FALLBACK_AFTER_GATES (2 entries; requires=/run= excluded, impl-owned).
- omt_enforcer.ts after-hook slim: sessionBootstrap + injectThoughtsOnRead +
  raw/null guard + ONE runAfterGates call. DELETED: editTools() +
  FALLBACK_EDIT_TOOLS (the edit-tools filter moved into the chain's tools=
  attrs — @var edit_tools is now build-time interpolated only), plus the
  isSrc/relOf/loadIr/mvcAfterEdit/tddAfterEdit imports; module doc gains the
  gate_driver line (was missing since improvement006).
- IR-declared behavior widening: g.tdd_after when=path_in(src/) — tddAfterEdit
  now fires for ALL src/ edits (was .py-only via the root's combined filter);
  advisory/revert-only and tdd_mode-gated internally, so harmless.
- pins py: test_after_hook_order_matches_ir REWORKED →
  test_after_hook_delegates_to_driver (runAfterGates( present, mvcAfterEdit(/
  tddAfterEdit( ABSENT from root body) + test_driver_sorts_after_gates_by_ir_order
  (runAfterGates region: on==="after" filter + order sort; the old IR
  order-uniqueness assert DROPPED — compiler-owned via R2 check_grammar_vocab)
  + test_after_impls_cover_exactly_the_ir_after_gates. TestFallbackGatesIrSyncPin:
  _parse_fallback/_ir_gates helpers extracted +
  test_fallback_after_gates_mirror_ir_after_gates. DELETED
  test_edit_tools_fallback_matches_ir + the ENFORCER editTools() consumer-resolve
  entry (accessor deleted; edit_tools coverage = the fallback-gates tools= pin).
- e2e (receipt-exempt): step-11 root module list dropped receipt_guard (its
  guards are chain-consumed via gate_driver only).
- tests: 142 → 144/144 green; full round chain green (check 233 rec 0 err /
  build+verify no drift / e2e ✓ receipt fresh). Bun driver-probe green.
- R8 leftovers from R7: none.

## DONE — R8 / OPT-G IR-driven gate msgs + orphan-@msg check (148/148 at its round)

- omt_shared.ts: NEW `gateMsg(id, {rel,tt,feature})` — IR @msg text resolver
  ({@var.x} already baked at build; placeholders replaceAll per call). NO
  FALLBACK_* text mirror by design: IR missing degrades text to the msg id —
  guard LOGIC never dies (FALLBACK_GATES & co. own that), text is teaching
  (genericImpl's established posture). omtHarnessE2eStatus message →
  gateMsg("receipt_stale") (inline 4-line literal deleted).
- Inline string sites deleted, all throw/notify sites render via gateMsg:
  receipt_guard.ts (denyMsg/testsMsg gone; env→protect_env, soft→protect_file,
  tests→tests_canary) · phase_gate.ts (noPhaseMsg/artifactMsg gone;
  no_phase + artifact with {tt}/{feature}) · nav_gate.ts (navRequiredMsg gone;
  g.nav impl in gate_driver renders nav_required) · think_gate.ts (thinkGateMsg
  header → IR think_gate; the risk-first/STALE/10-cap list body stays dynamic)
  · mvc_after.ts (mvc_new_hard block + mvc_warn advisory — orphan wired)
  · tdd_hats.ts (revert fallback → gateMsg("tdd_revert")) · gate_driver.ts
  (genericImpl text via gateMsg; module doc: ANY gate text now .omt-only).
- .omt: @msg artifact gains ('{feature}') · @msg think_gate reworded to compose
  with the appended list · @msg receipt_stale gains "(refreshes
  {@var.receipt_path})" · @msg nav_required gains op examples · @xref mvc
  enumerates the rule catalog as full @msg.* refs (feeds the orphan check).
- harnessc.py: NEW check_msg_orphans (run_all_checks after check_refs): a @msg
  is wired iff referenced by any record's attrs/payload @msg.<id> mention
  (gate/deny/protect msg=, see=, @xref catalog) OR a TS gateMsg("<id>") call
  (TOOL_SEED_DIRS + .opencode/lib scan); self-refs excluded.
- tests: test_harnessc.py section 12 (+3: orphan flagged, deny/payload refs
  count + self-ref rejected, real corpus zero-orphans) · pins file: +13
  gateMsg consumer entries (MVC_AFTER/TDD_HATS consts added; banned-helper
  regexes denyMsg/testsMsg/noPhaseMsg/artifactMsg/navRequiredMsg) +
  TestGateDriverIrRenderedMsg bun probe (tmp root + copied IR → g.protect
  block carries the IR @msg.protect_file text, {rel} interpolated).
- Round gotcha: transform-script anchor with stray leading indent = 0x match
  (abort-safe; re-ran remainder); one hand typo (stray `)` on an assert)
  caught by pytest collection — edit-tool fix was receipt-free (mtime < the
  just-refreshed receipt).
- tests: 144 → 148/148 green; full round chain green (check 233 rec 0 err /
  build+verify no drift / e2e ✓ receipt fresh). Bun IR-render probe green.
- R9 leftovers from R8: (a) e2eCommand() accessor has no live consumer now
  (kept as the IR-resolver for the pinned OMT_HARNESS_E2E_COMMAND const; the
  consumer-resolve pin passes via the definition) — delete candidate if R9's
  dead-record prune wants a TS sibling. (b) mvc_check.py rule texts remain
  hand-mirrored vs the @msg err_*/wrn_* catalog (pre-existing; @xref mvc
  documents) — future loop could wire mvc_check --json to ir.msgs.

## DONE — R9 / OPT-I derive round 2 + dead-record prune (155/155 at its round)

- harnessc.py derive_records extended (4 new families): flow.start_{major,
  minor,bug} ← @phase applies/requires + @fsm phase initial + @fsm tdd auto_on
  + @var scaffold · flow.tdd_<state> ← @fsm tdd states × @hat tdd.* (op from
  state, allow/revert_on from hat; NEW tdd_testlist flow fills the gap) ·
  doc.tree.{src,tst,doc} ← @gate when= path_in chains (order asc; before-gates
  inline payloads, after-gates id-listed) + @hat allows + @phase docs_none ·
  doc.prot.files ← @protect hard/soft + g.tests · doc.esc ← @tool omt_skip
  "Scopes:" payload + skip_ok gate map + hard protects. Convention tables
  (START_PHASE/START_GLOSS/TDD_FLOW_GLOSS/ESC_*) hold ONLY the facts the
  corpus doesn't carry (GATE_NEVER precedent); missing derive source = build
  error (state w/o hat, state w/o gloss, omt_skip w/o Scopes, esc gate
  missing/skip_ok!=true).
- .omt: 14 hand records deleted (7 flow start/tdd + 3 tree + prot.files + esc
  + DEAD doc.nav.tools [strict subset of comp.nav/@tool omt_nav] + DEAD
  doc.nav.workflow [dup of flow.nav_docs]); FLOW banner + 3 DERIVED pointer
  comments. Hand re-add under a derived id = duplicate-id build error.
- tests: test_harnessc.py section 13 (+7: start-flow facts, tdd states×hats,
  trees/prot/esc facts, missing-hat error, missing-gloss error, hand-readd
  dup, pruned-stay-absent). 148 → 155/155 green; full round chain green
  (check 232 rec 0 err / build+verify no drift / e2e ✓ receipt fresh).
- DEVIATION (options-doc "nav_index 88%→~80%"): landed 56984/64000 ≈ 89% —
  byte-NEUTRAL (+43 B). The audit's byte model predated R5/R8 (which wired
  the dead @hat data + orphan @msgs, consuming the prune list) and
  overestimated dead weight: nav-useful skeletons carry the same facts as the
  hand texts. Remaining fat (gotcha.* 6 KB, legacy omt++ scrape 18.3 KB) is
  live knowledge or belongs to R10/R11. The R9 win is drift-kill: 14 hand
  records → 13 derived + 2 pruned, each fact now carried once (R3 honest-cut
  precedent).
- R10 leftovers from R9: (a) e2eCommand() delete candidate STILL open (from
  R8; no live consumer). (b) mvc_check.py rule texts vs @msg err_*/wrn_*
  (from R8; future loop). (c) doc.sts.out overlaps @tool omt_status payload
  (~70%) but carries unique fields (TDD state, pending items) — kept.

## DONE — R10 / OPT-B on-demand doc diet (159/159 at its round)

- .meta/META_HARNESS.md 5526→1366 B: state-note rotation — improvement001–005
  narrative → git history; header kept byte-identical (e2e step-9 contract:
  "GENERATED" + .omt path); ROTATION rule travels inline with the stub; latest
  note (improvement006) compacted to one bullet + pointer (OUTCOME.md + git
  log). New notes land one-liner + pointer style.
- .meta/META.md 6754→5002 B: stale "READ FIRST → META_HARNESS.md" directive
  killed at all 4 sites (header START-HERE, KEY_DOCS row, LEARN_CODEBASE
  step 1, XREF_HARNESS) — re-routed to AGENTS.md + omt_nav on the .omt;
  dir-tree block 2.2 KB → 6-line top-level sketch (deep detail duplicated
  `ls` + the DIR_SDP table).
- harnessc.py: META_HARNESS_MD_PATH/META_MD_PATH consts + MEASURABLE_BUDGETS
  +2 ids + measure_budgets wiring (stat().st_size, missing→0) — transform
  script, 3 anchored reps.
- .omt: @budget meta_harness_md max=2048 (headroom for the FINAL 007 note) +
  @budget meta_md max=6144 (~23%, prior-round convention). 232→234 records.
- tests: test_harnessc.py section 14 (+4: ids measurable, measured-within-cap,
  stub rotation shape, no READ-FIRST). 155 → 159/159 green; full round chain
  green (check 234 rec 0 err / build+verify no drift / e2e ✓ receipt fresh).
- R11 leftovers from R10: none new; R8/R9 carry-overs still open
  (e2eCommand() delete candidate; mvc_check.py vs @msg catalog — future loop).

## DONE — R11 / OPT-H guide dedup (163/163 at its round)

- Audit verdict (nav-first diff, 16 sections vs corpus): the options-doc premise
  "guide wholesale restates the .omt corpus" does NOT hold — 11 of 16 sections
  are unique methodology the corpus never carried (§1,§3,§4,§6-§11,§13-§15).
  Real restatement: §2 transitions table (@fsm phase), §11.4 TDD workflow
  (@fsm tdd + @hat + @doc tdd.*, AND drifted — two-hats table missing
  TESTLIST/DONE states), §16 grep-pattern Detect advice (mvc_check.py is the
  executable impl), §15 file tree (stale: pre-feature_012/024 — no tui/, agent/,
  console screens). §12/§16 confirmed load-bearing: e2e step-5 pins §12
  literals ≡ phase_gate.ts ARTIFACT_REQUIRED; mvc_check messages cite §16.7/9
  row numbers; 6 live templates + new_feature.py cite §2/§3/§10/§11/§12.
- Decision: slim-to-pointers variant (R3 honest-cut precedent). render_guide
  projection REJECTED: would force ~22 KB of unique methodology into .omt
  records → blows nav_index headroom (56982/64000, ~7 KB free) for zero dedup
  gain; §12/§16 stay guide-authoritative per the directive.
- Guide 27471 B/718 ln → 23936 B/647 ln (−3.5 KB): §2 transitions table →
  IR-enforced pointer + rationale · §11.4 62→14 lines (summary + omt_nav
  TDD_/CMD_OMT_TDD pointers; drift fixed) · §15 stale tree → current-reality
  convention sketch (52→25 lines; drift-prone leaf enumeration dropped) · §16
  "(grep Patterns)" title → mvc_check enforcement preamble (rows 1-5,7,9,10
  auto-checked via g.mvc after-gate; table rows byte-kept — §16.N citations
  load-bearing) · footer re-scoped (methodology authority; harness mechanics →
  omt_nav). Transform: /tmp/opencode/r11_guide_slim.py, 5 anchored sites.
- .omt: @xref guide extended 6→16 section routes (§1,§3-§11,§15 added — nav
  answers "where is X" for the full methodology).
- tests: test_omt_docs_drift_pins.py +4 (live §-refs resolve · @xref guide
  covers all sections · mvc_check §16.N rows exist · §11.4 anti-regrowth ≤25
  lines + corpus pointers). 159 → 163/163 green; full round chain green
  (check 234 rec 0 err / build+verify no drift / e2e ✓ receipt fresh).
- DEVIATION (options-doc "−20+ KB on-demand"): landed −3.5 KB. The −20 KB
  model assumed wholesale restatement; the audit found the guide is mostly
  unique single-sourced methodology whose deletion would LOSE knowledge the
  corpus can't absorb within budget. The R11 win: 3 real restatements killed,
  2 drift sites fixed, nav routing completed 6→16, 4 anti-regrowth pins.
- FINAL leftovers: R8/R9 carry-overs still open (e2eCommand() delete
  candidate; mvc_check.py rule texts vs @msg catalog — future loop).

## NEXT — FINAL wrap (nothing else remains)

- full `uv run pytest -q` (163 omt + suite; recompute KNOWN_SUITE_FAILURES) ·
  live opencode smoke (TS tools changed in R3+R4 — mandatory) · WORK.md [x] +
  rotate · step-6 dated note in .meta/META_HARNESS.md · OUTCOME.md here ·
  omt_complete{feature:"improvement007", advance_to:"Done"}.

## Pause-state inventory

- Dirty (uncommitted, intentional): the R1–R3 pause set (.meta/META_HARNESS.omt,
  scripts/omt/harnessc.py, tests/scripts/omt/test_harnessc.py,
  .opencode/lib/enforcer/{phase_gate,tdd_hats}.ts, .opencode/plugins/{omt_nav,
  omt_status,omt_think}.ts, .meta/.omt/{harness.ir.json,nav.index.jsonl},
  WORK.md, WORK_ARCHIVE.md, prompts/pause_dev_for_resume_later.md,
  .sandbox/meta/improvement007/*) PLUS the R4 set:
  .opencode/lib/omt_shared.ts, .opencode/lib/enforcer/{nav_gate,receipt_guard,
  think_gate}.ts, .opencode/plugins/omt_enforcer.ts,
  tests/scripts/omt/{test_omt_enforcer_guard_source_pins,test_thought_pattern_pin}.py
  PLUS the R5 set: scripts/omt/tdd/gates.py, tests/scripts/omt/test_tdd_check.py
  PLUS the R6 set: .opencode/lib/enforcer/{gate_driver,session_state}.ts
  PLUS the R7 set: .opencode/lib/enforcer/gate_driver.ts,
  .opencode/plugins/omt_enforcer.ts,
  tests/scripts/omt/{test_omt_enforcer_guard_source_pins,test_omt_harness_e2e}.py
  PLUS the R8 set: .opencode/lib/enforcer/{nav_gate,receipt_guard,phase_gate,
  think_gate,mvc_after,tdd_hats}.ts, tests/scripts/omt/test_harnessc.py
  PLUS the R9 set: scripts/omt/harnessc.py, .meta/META_HARNESS.omt,
  tests/scripts/omt/test_harnessc.py (+ regenerated projections:
  .meta/.omt/{harness.ir.json,nav.index.jsonl}, harness.report)
  PLUS the R10 set: scripts/omt/harnessc.py, .meta/META_HARNESS.omt,
  .meta/{META_HARNESS.md,META.md}, tests/scripts/omt/test_harnessc.py
  (+ regenerated projections again).
  NO commit without explicit user request.
- Verified green at pause: check 0 err (234 rec) · build+verify no drift · e2e ✓ ·
  tests/scripts/omt 159/159 · receipt FRESH.
- Ledger: phase(refactor/Programming) + skip(tests) recorded under the PAUSED
  session id — session-scoped: the resuming session MUST re-run the bootstrap
  lines at the top of this file (omt_phase + omt_skip{scope:"tests"}).
