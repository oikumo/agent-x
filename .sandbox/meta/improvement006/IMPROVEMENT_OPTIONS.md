# IMPROVEMENT_OPTIONS — improvement006 (fresh-start loop, 2026-08-01)

> Rules honored: fresh start · future token-consumption minimization first · agent
> performance over human-readable artifacts (DSL wherever possible) · refactors
> considered · flexibility for future changes · subagents considered (skipped:
> analysis completed from harness artifacts + 3 targeted greps; parallel agents
> would add tokens without new information).

## Cost model (measured 2026-08-01, harness.report + artifact audit, post-improvement005)

| Surface | Bytes | Paid | Budget |
|---|---|---|---|
| AGENTS.md (system prompt) | 1962 | EVERY TURN | 1962/2560 OK |
| Tool schemas (18 × @tool one-liner, IR-sourced) | 1484 | EVERY TURN | 1484/2560 OK |
| Nav tip (session-bootstrap inject, resident) | ~155 | EVERY TURN | ≤512 |
| TA digest (session-bootstrap inject, resident) | ~230 | EVERY TURN | ≤1024 |
| omt_status output | ~1500/call | ON DEMAND (frequent) | none |
| WORK.md (80 lines, ~36 DONE entries) | 5899 | EVERY SESSION STARTUP | 5899/8192 OK |
| nav.index.jsonl (252 records) | 58906 | ON DEMAND (per nav answer) | **NO BUDGET** |
| harness.ir.json | 17428 | plugin-internal | **NO BUDGET** |
| omt_agent_guide.md | 27422 | ON DEMAND (rare) | n/a |
| .meta/META_HARNESS.md stub (state notes) | 3319 | never auto-read | none (grows/loop) |

Dominant lever remains per-turn (~3.8 KB/turn); per-session = WORK.md (unbounded DONE growth);
on-demand = nav answers (a GOTCHA_ query ≈ 4 KB), omt_status, guide.

## Confirmed findings this loop (drive the options)

1. **Schema single-source holds, fallback seeds drifted.** All 18 tools resolve descriptions
   via `irToolDescription(name, <fallback>)` (10 in plugins/, 3 in phase_gate.ts, 5 in
   tdd_hats.ts). System-prompt cost = `.omt` @tool payloads (1484 B, accurately budgeted).
   But the TS fallback seeds are stale duplicates (e.g. omt_phase seed "…Records
   task_type/phase/scope to the …" ≠ .omt "…→ ledger; unlocks per the §12 matrix").
2. **omt_status display bugs (live, this session):** "Feature Health: overall 0%
   (R:0 A:0 D:0 I:0 T:0)" shown for a feature already at phase Done; "Valid Next
   Phases:" empty at Done. ~1.5 KB default output with box-drawing + ledger tail.
3. **Repo hygiene drift on disk NOW:** 3 × `ta_digest_*.py` probe leftovers at repo root
   (2026-07-19), `.meta/.omt/thoughts.jsonl.bak` (2026-07-25). Nothing guards against it.
4. **WORK.md DONE list unbounded:** ~36 DONE one-liners ≈ 3.3 KB of the 5.9 KB startup
   read; budget 8192 will eventually hard-fail builds instead of bounding growth.
5. **nav.index.jsonl + harness.ir.json have no @budget** — the two largest projections
   are the only unchecked ones; ~30/252 nav records are derivable (@doc ph.*/tt.*/sec.*).

## Options (select ONE)

### OPT-A — @tool schema description diet (.omt-only) ★ RECOMMENDED
18 one-liners 1484 → ~1050 B. Top-6 = 714 B: omt_think 180, omt_skip 114, omt_phase 110,
omt_think_list 105, omt_complete 103, omt_status 102. Keep constraint clauses
(e.g. "line | after | symbol (at most one)") — misuse blocks cost more than saved bytes.
- **Saving:** ~430 B/turn (≈21 KB per 50-turn session). **Risk:** LOW · **Effort:** S.
- **Change:** .omt @tool payloads only → harnessc check/build (all 18 tools confirmed
  IR-sourced — NO TS edits, no receipt round-robin); shrink @budget tool_schemas
  2560→1536 to lock it. Update the one TS-pinned budget test alongside (round-robin OK).

### OPT-B — WORK.md DONE rotation (structural per-session bound)
Convention + enforcement: keep pending + last 5 DONE inline; older rotate to
`WORK_ARCHIVE.md` (never auto-read; pointer kept) — `mode=rotate` for WORK.md,
mirroring the ledger. New @doc conv.work_rotate + harnessc pin (done_max_lines)
so bloat = build error. One-time migration of ~31 DONE entries.
- **Saving:** 5899 → ~2.8 KB ≈ ~750 tok saved EVERY SESSION STARTUP, structurally bounded
  forever. **Risk:** LOW · **Effort:** S-M (WORK.md is not harness-surface; convention +
  pin are).
- **Note:** subsumes the still-pending "narrative DONE diet" — current DONE entries are
  already one-liners; the leak is COUNT, not verbosity.

### OPT-C — Schema fallback-seed drift lint (single-source integrity)
harnessc check gains a pin: each TS `irToolDescription(name, seed)` seed ≡ .omt @tool
payload (or seeds dropped → IR mandatory at plugin load, fail-fast). Fixes the confirmed
omt_phase drift + 17 un audited siblings; pins the single-source invariant the DSL promises.
- **Saving:** drift prevention (future tokens + wrong-tool-selection risk); ~0 B/turn.
  **Risk:** LOW-MODERATE (harnessc change + 18 TS one-line edits under receipt
  round-robin). **Effort:** M.

### OPT-D — @derive compiler pass + nav/IR budgets
Delete derivable records: 12 @doc ph.*/tt.* (one-word payloads), 18 @doc sec.* (section
catalog implicit in tag prefixes), @doc rule.rigor (3rd copy of §12 matrix),
@doc prot.files + esc.* (prose copies of @protect/@gate fields). harnessc gains a
projection-time @derive expansion emitting PHASE_/TT_/SECTION/PROT_/ESC_ nav records
from @fsm/@phase/@protect/@gate. Add @budget nav_index + ir_json (58.9 KB/252 rec,
17.4 KB — currently the ONLY unchecked projections).
- **Saving:** ~30 source lines / ~2.4 KB .omt; ~30/252 index records; self-enforcing via
  new budgets. **Risk:** MODERATE (compiler change; budget pins + e2e). **Effort:** L.
- **Flexibility win (rule 5):** new phase/task_type/rule costs 1 record, not 4.

### OPT-E — omt_status compact default + 2 display-bug fixes
Compact default block (phase/unlock/next-task/budgets one-liner), verbose behind
include_ledger. Fixes confirmed bugs: Feature Health "overall 0%" on Done features;
empty "Valid Next Phases" at Done.
- **Saving:** ~0.5–1 KB per status call (most frequent on-demand tool). **Risk:**
  MODERATE (primary orientation tool — over-compression backfires; keep the 5 key
  fields). **Effort:** S-M (TS-only: omt_status.ts, receipt-guarded, one edit/round).

### OPT-F — HDL-2: data-driven gate interpreter (DSL frontier)
@gate rows are data but guard LOGIC is hand-written TS ×7 (~57 KB: phase_gate 19.5,
think_gate 9.4, nav_gate 8.2, session_state 6.4, tdd_hats 5.4, mvc_after 4.7,
receipt_guard 3.8). Make the TS a generic evaluator over compiled when=/requires=
@pred expressions → gate changes become .omt-only edits (no TS round-robin ×7, no
TS-no-reload gotcha).
- **Saving:** indirect (cheaper harness evolution; fewer re-paid gotchas). **Risk:**
  HIGH (core enforcement rewrite; guard-order pins + SDK contracts must hold).
  **Effort:** LARGEST. **Flexibility:** maximal — new gates = declarations.

### OPT-G — Repo-hygiene gate: root allowlist + state-dir sweep
harnessc check gains a repo-root allowlist (fails on `ta_digest_*.py`-class strays)
+ `.meta/.omt/` sweep for `*.bak`. One-time cleanup included (3 root strays +
thoughts.jsonl.bak, all confirmed junk from Jul probes).
- **Saving:** prevents agent confusion/mis-reads + silent junk accumulation; ~0 B/turn.
  **Risk:** LOW · **Effort:** S.

### OPT-H — Tool consolidation: 18 tools → ~8 (namespaced ops)
`omt_tdd{op:testlist|red|green|refactor|done}` (5→1), `omt_nav{op:...}` (4→1),
`omt_think{op:add|list|remove|verify|suggest}` (5→1); keep phase/skip/complete/status.
Each eliminated tool removes its fixed JSON-schema header from EVERY system prompt
(beyond the 1484 B descriptions).
- **Saving:** ~1–2 KB/turn (largest per-turn win available). **Risk:** HIGH (4 plugins
  + enforcer + 116 harness tests + perms + docs). **Effort:** L.

## Token-ROI ranking (50-turn session)

OPT-H ≈ 50–100 KB > **OPT-A ≈ 21 KB** > OPT-E ≈ 5–10 KB > OPT-B ≈ 3 KB + structural
> OPT-D/C/G (integrity/future) > OPT-F (evolution cost, indirect).

## Notes

- Step-6 target interpretation (carried from improvement004/005): `./meta/META_HARNESS.md`
  is a GENERATED stub (retired corpus); the harness single source of truth is
  `.meta/META_HARNESS.omt` (AGENTS.md is its generated projection). "Update the META
  HARNESS state file" ⇒ edit `.meta/META_HARNESS.omt` + rebuild projections via
  harnessc + append the dated state note to the stub.
- OPT-A composes with OPT-B/E/G (disjoint surfaces). OPT-C is prerequisite-grade
  hygiene for any future schema work.
