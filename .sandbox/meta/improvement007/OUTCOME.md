# OUTCOME — improvement007.meta_harness_evolution (ALL OPT A–I)

Status: **DONE** (2026-08-01) · 7 sessions · 11 rounds (R1–R11) + FINAL wrap.
Working log + per-round details: ./RESUME.md · option analysis: ./IMPROVEMENT_OPTIONS.md.

## Verification at close

- `harnessc check` — 234 records, 0 errors
- `harnessc build` + `check --verify-projections` — no drift (5 projections)
- `uv run pytest tests/scripts/omt -q` — **163/163** (loop start: 126)
- e2e receipt fresh · live opencode smoke **2/2** · bun driver/IR probes green
- Full suite: **1109 passed + 3 failed** = the allowlisted feature_018
  react_screen ×3 (KNOWN_SUITE_FAILURES; unchanged since loop start)

## What landed (per option)

| OPT | Round | Result |
|-----|-------|--------|
| C {@var.x} interpolation | R1 | 4 literal classes single-sourced; unknown names = check errors |
| D check hardening | R2 | check_grammar_vocab (fsm/hat/inject/gate arity+order); 3 drift fixes |
| A arg-describe diet | R3 | live dispatcher describes 1609→1285 B/turn; `tool_args` budget 1536 |
| E TS consumes IR | R4 | omt_shared IR-accessor layer; 7 hand-mirrors deleted; fallback value-pins |
| E py consumes IR | R5 | @hat → tdd engine (HAT_RULES/REVERT_ON derived; literals = no-IR fallback) |
| leftovers | R6 | gate_driver protect die-open fix; e2e path accessors; write-only counters deleted |
| F after-gates in driver | R7 | runAfterGates + AFTER_IMPLS; enforcer after-hook slim; edit-tools filter → IR tools= |
| G IR gate msgs | R8 | gateMsg() resolver; ~8 inline string sites deleted; check_msg_orphans |
| I derive round 2 + prune | R9 | 14 hand records → 13 derived + 2 dead pruned; drift-kill (byte-neutral) |
| B on-demand doc diet | R10 | META_HARNESS 5526→1366 B stub-rotation; META 6754→5002 B; 2 budgets |
| H guide dedup | R11 | guide 27471→23936 B; §2/§11.4/§16 restatements → pointers; §15 drift fixed; @xref guide 6→16 routes |

## Deviations (honest-cut record, R3 precedent)

- **R3:** "≤900 B arg describes" unreachable without dropping valid-value enums
  (error round-trips = net token loss) → landed 1285 B, capped 1536.
- **R9:** "nav_index 88%→~80%" → landed byte-neutral (+43 B); audit's byte model
  predated R5/R8 wiring. Win was drift-kill, not bytes.
- **R11:** "−20+ KB guide" → landed −3.5 KB. Audit found 11/16 guide sections
  are unique methodology the corpus never carried; §12/§16 are load-bearing
  authority (e2e step-5, mvc_check §16.N citations, 6 live templates).
  render_guide projection rejected (would force ~22 KB into .omt records vs
  ~7 KB nav headroom, zero dedup gain). Win: 3 restatements killed, 2 drift
  sites fixed, nav routing completed, 4 anti-regrowth pins.

## Open carry-overs (future loop)

- e2eCommand() accessor has no live consumer (kept as IR-resolver for the
  pinned const) — delete candidate.
- mvc_check.py rule texts hand-mirrored vs @msg err_*/wrn_* catalog —
  future loop could wire mvc_check --json to ir.msgs.
- doc.sts.out overlaps @tool omt_status payload (~70%) but carries unique
  fields (TDD state, pending items) — kept.

## Test growth

tests/scripts/omt: 126 → **163** (+37 pins/tests across R1–R11):
interpolation, grammar vocab, tool_args budget, IR-accessor fallback sync ×9,
hat fallback sync ×4, gate-driver protect probe, after-gate driver ×3 +
fallback-after pin, msg orphan ×3 + IR-render probe + 13 gateMsg pins,
derive round 2 ×7, doc-diet ×4, guide-dedup ×4.

## Process notes

- Round discipline held throughout: ONE edit per harness-surface file per e2e
  receipt; multi-site transforms via uv-run python scripts; ONE receipt
  refresh per round; e2e test file receipt-exempt.
- New gotchas harvested: TS array slicing (`"\n]"` not `"]"`), harnessc attr
  parser strips quotes (normalize when pin-comparing), transform-script
  anchors must not carry stray indent (0x-match abort-safe).
- NO commit made — dirty tree is intentional per loop rules.
