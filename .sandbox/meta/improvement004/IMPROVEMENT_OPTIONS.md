# improvement004 — IMPROVEMENT_OPTIONS

> Rules honored: fresh start · token-consumption minimization first · agent performance over
> human-readable artifacts (DSL wherever possible) · refactors considered · flexibility for change.
> Estimates: ~4 bytes/token. All options end with `.meta/META_HARNESS.md` stub state-note update.

---

## OPT-A — AGENTS.md diet, round 2: tables → nav pointers  ★ RECOMMENDED (small+safe)
Extend the proven 001/OPT-A pattern to the last duplicated blocks in the every-turn projection:
§12 Phase-Artifacts table → `RULE_RIGOR` pointer; TDD paragraph → `RULE_R3` pointer;
Quick Reference (8 rows) → one `omt_quick_ref` line; NAV/THINK paragraphs → tag pointers.
NEVER/ALWAYS/ENF core stays inline.
- **Token win:** 2941 → ~1900 B ≈ **~260 tok saved EVERY TURN**; budget pin 5120→2560 (build error on bloat)
- **Risk:** low (001 precedent, harnessc render_agents edit + pins + e2e) · **Effort:** small
- **Flexibility:** content lives once in .omt; projection auto-follows

## OPT-B — Tool consolidation: 18 tools → ~8 (namespaced ops)
`omt_tdd{op:testlist|red|green|refactor|done}` (5→1), `omt_nav{op:...}` (4→1),
`omt_think{op:add|list|remove|verify|suggest}` (5→1); keep phase/skip/complete/status.
Each tool = fixed JSON-schema header in the system prompt beyond the 1484 B descriptions.
- **Token win:** −10 schema headers ≈ **~1000–2000 tok EVERY TURN** (largest available win)
- **Risk:** HIGH — 4 plugins + enforcer + 116 harness tests + perms + docs · **Effort:** large
- **Flexibility:** fewer tools, one schema per domain; new ops = data, not new schemas

## OPT-C — WORK.md DONE rotation (bounded startup file)
DONE list grows forever (~40 lines now). Convention + enforcement: keep pending + last 5 DONE
inline; older rotate to `WORK_ARCHIVE.md` (never auto-read; pointer kept) — `mode=rotate` for
WORK.md, mirroring the ledger. New `@doc conv.work_rotate` + compile/lint pin
(done_max_lines) so bloat = build error.
- **Token win:** 5899 → ~3.2 KB ≈ **~650 tok saved EVERY SESSION STARTUP**, structurally bounded
- **Risk:** low · **Effort:** small-medium (one-time archive + convention + pin)

## OPT-D — HDL-2: data-driven gate interpreter (DSL frontier)
Today `@gate` is data but LOGIC is hand-written TS ×7. Make the TS a generic evaluator over
compiled `when=`/`requires=` @pred expressions → gate changes become .omt-only edits
(no TS, no receipt round-robin ×7, no hot-reload gotcha).
- **Token win:** indirect (cheaper harness evolution; fewer re-paid gotchas)
- **Risk:** HIGH (core enforcement rewrite; guard-order pins + SDK contracts must hold) · **Effort:** largest
- **Flexibility:** maximal — new gates = declarations; the "suggest a DSL" rule's next increment

## OPT-E — Token telemetry: harness.report → cost model + per-turn budget
Extend the existing report: per-turn cost (AGENTS.md + full schema overhead + resident injects)
and per-session cost (WORK.md + status), tok estimates, printed by `harnessc check`;
new `@budget per_turn_bytes` so aggregate prompt-riding regressions are build errors.
- **Token win:** 0 direct — but makes every future loop data-driven and locks in 001–004 gains
- **Risk:** low · **Effort:** small · **Flexibility:** the F32/F33 knob becomes measurable

## OPT-F — omt_status compact default
Routine calls need phase/unlock/next only (~8 lines); verbose behind `include_ledger`/flag.
- **Token win:** ~300–500 tok per status call · **Risk:** low · **Effort:** small

## OPT-G — Single-shot session bootstrap (`omt_start`)
Merge startup reads (WORK.md + nav tip + TA digest + status) into one tool emission;
STARTUP rule becomes "call omt_start, summarize ≤15 lines".
- **Token win:** fewer round trips + no double-paid context (~200–400 tok/session)
- **Risk:** medium (changes STARTUP convention + WORK.md contract) · **Effort:** medium

---

### Suggested batching
- **Small-safe batch:** A + C + E (+F) — one session, ~900 tok/turn+session combined, all low risk
- **Big-win track:** B (or D) alone, dedicated session with full TDD/e2e round-robin
