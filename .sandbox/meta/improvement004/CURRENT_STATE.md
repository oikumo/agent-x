# improvement004 — CURRENT_STATE (fresh-start analysis, 2026-08-01)

> Method: META HARNESS artifacts + toolbox only (omt_status, omt_list_sections, omt_nav,
> harnessc check, .omt source read). No application source-code search.

## 1. What the META HARNESS is

OMT-HDL v1 DSL (`.meta/META_HARNESS.omt`, 324 lines, **243 records**, check OK 0 errors)
= single source of truth. Compiler `harnessc.py` projects it to:

| Projection | Size | Consumer |
|---|---|---|
| `AGENTS.md` (GENERATED) | 2941 B (budget 5120) | LLM system prompt — **every turn** |
| `opencode.jsonc` harnessc blocks | — | opencode permission engine (deny rules) |
| `.meta/.omt/harness.ir.json` | 17.4 KB | opencode plugins (enforcer libs) |
| `.meta/.omt/nav.index.jsonl` | 59 KB / 252 records | omt_nav toolbox (on demand) |
| `harness.report` | 10 lines | sizes vs budgets (self-maintaining) |

## 2. Record vocabulary (the DSL grammar)

`@var`(21) · `@deny`(10: git/python/pip/pytest/env/webfetch) · `@protect`(5) · `@always`(5)
· `@phase`(3)+`@fsm phase` · `@fsm tdd`+`@hat`(5) · `@pred`(8 closed builtins, TS-owned)
· `@gate`(8: nav/protect/receipt/tests/phase/think/tdd_after/mvc — data only, LOGIC in TS)
· `@msg`(21) · `@state`(3: ledger rotate 64 KB, thoughts append-only, receipt rewrite)
· `@inject`(2: session_bootstrap, file_thoughts) · `@doc`(101: rules/components/nav/think/
paths/tree/phases/tt/sections/**gotcha×16**/conv) · `@budget`(6, compile-enforced)
· `@tool`(18) · `@flow`(11 QUICK_) · `@xref`(9)

## 3. Enforcement architecture

Composition root `.opencode/plugins/omt_enforcer.ts` + `lib/enforcer/`×7
(phase_gate, tdd_hats, think_gate, nav_gate, receipt_guard, mvc_after, session_state)
+ 3 more plugins (omt_status, omt_nav, omt_think) + shared `omt_shared.ts`.
Guard order pinned (0 nav → 10 protect → 20 receipt → 30 tests → 40 phase → 50 think
→ 60 mvc → 70 tdd_after). Escape: omt_skip (logged); think-gate NOT skip-bypassable.

## 4. Token cost map (F32 ×N-turn / F33 system-prompt)

| Cost | Bytes | Paid | Headroom |
|---|---|---|---|
| AGENTS.md | 2941 | **every turn** | 2941/5120 |
| 18 tool schemas (descriptions) | 1484 | **every turn** (+ JSON-schema overhead not budgeted) | 1484/2560 |
| nav tip inject | ≤512 | conversation-resident → re-paid/turn | TS-pinned |
| TA digest inject | ≤1024 | conversation-resident → re-paid/turn | TS-pinned |
| file_thoughts inject | ≤1024/file | on first read of TA: files | — |
| WORK.md | 5899 (scratchpad 1342) | **every session startup** | 5899/8192 |
| omt_status / nav answers | on demand | per call | — |

WORK.md DONE list: ~40 one-liners, grows unbounded (convention = 1 line + pointer, no rotation).

## 5. Recent loop outcomes (stub state notes — sizing context only)

- 001/OPT-A: AGENTS.md tools-table → pointer, 4273→2941 B (~330 tok/turn saved)
- 002/OPT-B: 16 gotchas WORK.md→@doc nav-indexed (WORK.md 12117→7767 B)
- 003/OPT-M: WORK.md DONE diet + work_md budget 14336→8192 (7767→5899 B)

## 6. Structural observations (fresh)

1. AGENTS.md still carries tables duplicated in nav records: §12 phase-artifact matrix
   (RULE_RIGOR), TDD block (RULE_R3), Quick Reference ×8 rows (@flow QUICK_* via omt_quick_ref),
   NAV/THINK paragraphs (NAV_ENFORCEMENT/THINK_GATE) — precedent 001 says: pointer-ize.
2. 18 tools = 18 fixed JSON-schema headers in the system prompt; description budget counts
   only payload text — true per-turn schema cost is larger and unmeasured.
3. `@gate` is data, but gate LOGIC is hand-written TS ×7 — adding/changing a gate means
   TS edits + receipt round-robin + no hot-reload (GOTCHA_TS_NO_RELOAD). DSL frontier.
4. WORK.md DONE entries have no rotation (ledger has mode=rotate; WORK.md doesn't).
5. harness.report measures sizes but not a per-turn/per-session token model; no
   aggregate "cost of riding the prompt" budget → regressions only caught per-projection.
6. omt_status emits ~35 lines incl. feature-health + ledger even for routine checks.
