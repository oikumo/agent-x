# IMPROVEMENT_OPTIONS — improvement005 (fresh-start loop, no prior-iteration input)

## Cost model (measured 2026-08-01, harness.report + artifact audit)

| Surface | Bytes | Paid | Budget |
|---|---|---|---|
| AGENTS.md (system prompt) | 2097 | EVERY TURN | 2097/2560 OK |
| Tool schemas (18 @tool one-liners) | 1484 | EVERY TURN | 1484/2560 OK |
| Nav tip (session-bootstrap inject) | 489 | EVERY TURN (conversation-resident) | ≤512 |
| TA digest (session-bootstrap inject) | 282 | EVERY TURN (conversation-resident) | ≤1024 |
| WORK.md | 5899 | EVERY SESSION STARTUP | 5899/8192 OK |
| nav.index.jsonl (252 records) | 58966 | ON DEMAND (per nav answer) | NO BUDGET |
| harness.ir.json | 17428 | plugin-internal | NO BUDGET |
| omt_agent_guide.md | 27422 | ON DEMAND (rare) | n/a |

Dominant lever = per-turn surfaces (~4.3 KB/turn). Per-session = WORK.md. On-demand = nav answers, guide, omt_status.

## Options (select ONE)

### OPT-A — Per-turn injection diet (RECOMMENDED)
Compress the three conversation-resident/system-prompt texts: nav tip 489→~150 B (one-liner; tool schemas already carry args), TA digest tail fold (~100 B: merge pointer into line 1, keep "omt_think_list"/"think-gate" words), AGENTS.md maintainer boilerplate trim (GENERATED-FROM line + ENF line, 401→~70 B; content already nav-indexed as @doc comp.enf/@doc enforcement).
- Saving: ~700 B/turn (≈35 KB over a 50-turn session). Risk: LOW. Effort: M.
- Change: TS-pinned tip/digest text + .omt @doc payload + harnessc AGENTS.md template; @budget nav_tip/agents_md already enforce. Harness-surface → receipt round-robin rules apply (ONE edit/file/round, e2e between rounds).

### OPT-B — @tool schema description diet
18 one-liners 1484→~1050 B (top-6 = 714 B: omt_think 180, omt_skip 114, omt_phase 110, omt_think_list 105, omt_complete 103, omt_status 102). Keep constraint clauses (e.g. "line | after | symbol (at most one)") — misuse blocks cost more than saved bytes.
- Saving: ~400 B/turn. Risk: MODERATE (tool-selection quality). Effort: S.
- Change: .omt @tool payloads only → harnessc check/build; @budget tool_schemas enforces. Composes cleanly with OPT-A.

### OPT-C — WORK.md startup diet
Enforce CONV_WORK_DONE (7 narrative DONE entries = 1868 B → one-line+pointer), strip dead `<!-- id -->` on completed tasks (~330 B), compress Convention block 530→~150 B, scratchpad top-3 gotcha copies 536→~150 B (verbatim duplicates of nav-indexed @doc gotcha.*; pointer line already exists), FEATURES DONE paragraph 324→~120 B.
- Saving: ~2.5-3 KB/session startup. Risk: LOW (drift correction; convention already mandates it). Effort: S.
- Change: WORK.md data edit only (not in harness_paths → no receipt guard). No DSL/TS change.

### OPT-D — DSL @derive pass (kill derivable records)
Delete 12 trivial @doc ph.*/tt.* (one-word payloads), 18 @doc sec.* (section catalog implicit in tag prefixes), @doc rule.rigor (3rd copy of §12 matrix), @doc prot.files + esc.* (prose copies of @protect/@gate fields). harnessc gains a projection-time @derive expansion emitting PHASE_/TT_/SECTION/PROT_/ESC_ nav records from @fsm/@phase/@protect/@gate. Add @budget nav_index + ir_json (currently unchecked: 58.9 KB/252 rec, 17.4 KB).
- Saving: ~30 source lines / ~2.4 KB .omt, ~30/252 index records, self-enforcing via new budgets. Risk: MODERATE (compiler change; budget pins + e2e). Effort: L.
- Change: .omt + harnessc.py (DSL extension — rule 3). Flexibility win: new phase/task_type/rule costs 1 record, not 4.

### OPT-E — DSL integrity pack (single-source vars)
@state ledger cap/window → @var.ledger_cap_bytes/@var.unlock_window_ms (currently re-hardcoded); @msg {@var.e2e_cmd} interpolation (e2e cmd hardcoded in receipt_stale; new_feature.py ×2; mvc_check.py ×1); g.nav tools=@var.search_tools (dead var) + drop duplicate paths= (derive from path_in arg); fix @msg deny_git see= (points at wrong rule); fix @xref mvc pattern (@msg mvc.* matches nothing); wire or delete unused @pred cmd_match/risk_high; @fsm tdd transitions= (grammar parity with @fsm phase); harnessc warn when gate file-order ≠ order=.
- Saving: drift prevention (future tokens), ~0 B/turn. Risk: LOW-MODERATE. Effort: M.
- Change: .omt + harnessc.py interpolation pass. Flexibility win (rule 5).

### OPT-F — Guide dedup vs nav corpus
omt_agent_guide.md §11.4 TDD (2807 B) + §12–14 (4366 B) + §16 (1293 B) ≈ 8.5 KB substantially restate @doc rule.r3/tdd.*/rule.rigor + @msg err_*/wrn_* → shrink to nav pointers; XREF_GUIDE retargets to unique deep-dive sections.
- Saving: up to ~6-8 KB per full guide read (on-demand only). Risk: MODERATE (verify §13 checklist/§16 unique detail first). Effort: M.
- Change: docs edit; guide IS in harness_paths → receipt-guarded.

### OPT-G — omt_status terse output
Compact default output (single-line/JSON-ish), verbose behind include_ledger. ~200-500 B/call on demand.
- Saving: on-demand only. Risk: MODERATE (primary orientation tool; over-compression backfires). Effort: S. TS-only.

## Notes
- Rule-1 compliance: prior improvement001-004 contents NOT read (ID allocation only).
- Step-6 target interpretation: `./meta/META_HARNESS.md` does not exist; the harness single source of truth is `.meta/META_HARNESS.omt` (AGENTS.md is its generated projection). "Update the META HARNESS state file" ⇒ edit `.meta/META_HARNESS.omt` + rebuild projections via harnessc.
- Token-ROI ranking (50-turn session): OPT-A ≈35 KB > OPT-B ≈20 KB > OPT-C ≈3 KB > OPT-D/E/F/G (on-demand/future).
- OPT-A and OPT-B compose; if both wanted, pick OPT-A now, OPT-B next loop.
