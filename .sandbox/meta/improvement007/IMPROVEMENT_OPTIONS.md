# IMPROVEMENT_OPTIONS — improvement007 (fresh-start loop, 2026-08-01)

Method: harness-artifact deep-read (.meta/META_HARNESS.omt full corpus, toolbox
omt_status/omt_nav) + 2 parallel subagent audits (token-cost surfaces; DSL corpus
vs compiler vs TS runtime). No src/ searched. Evidence refs: `.omt:N` = corpus
line; A# = token-audit finding; B# = DSL-audit finding.

## Cost model baseline (measured)

| Surface | Bytes | Paid | Budget |
|---|---|---|---|
| Tool arg `describe()` strings | 1611 | EVERY TURN | NONE (uncounted) |
| Schema JSON boilerplate | ~2200 | EVERY TURN | NONE |
| AGENTS.md | 1934 | EVERY TURN | 2560 (626 headroom) |
| WORK.md | 3857 | EVERY STARTUP | 4096 (239 headroom, 94% used) |
| Bootstrap injection | 396 | RESIDENT | 1536 (healthy) |
| .meta/META.md | 6754 | ON-DEMAND (ALWAYS rule) | NONE |
| .meta/META_HARNESS.md (stub) | 5526 | ON-DEMAND | NONE |
| omt_agent_guide.md | 27471 | ON-DEMAND (latent dup) | NONE |
| nav.index.jsonl | 56584 | ON-DEMAND | 64000 (88% used) |
| harness.ir.json | 15530 | plugin-internal | 20480 |

---

## OPT-A — Every-turn schema diet round 2: arg-describe budget + trim
- **What:** Extend `@budget tool_schemas` to cover arg `describe()` strings (1611 B
  currently uncounted; desc-only 775 B is budgeted). Diet the verbose arg texts
  (omt_think `symbol` 76 B, omt_status `include_ledger` 100 B, omt_phase
  `design_doc` 89 B, op dispatchers' per-op arg prose). Target ≤900 B args.
- **Pays:** EVERY TURN (~−700 B ≈ −175 tok/turn) + closes the last unbudgeted
  every-turn surface (A#1).
- **Touches:** .omt (@budget + @tool args), TS seeds (seed-sync lint pins them),
  drift pins. Receipt round-robin applies.

## OPT-B — On-demand doc diet: stub rotation + META.md fix + budgets
- **What:** (1) `.meta/META_HARNESS.md` state-note rotation — 4.8 KB of
  improvement001–006 narrative → git history, keep header + latest note inline
  (~1 KB); loop step-6 updates stay one-liner+pointer. (2) `.meta/META.md`:
  remove stale "READ FIRST → META_HARNESS.md" directive + slim the 2.2 KB
  dir-tree block (duplicates `ls`). (3) New `@budget` pins for both (first
  on-demand docs under budget).
- **Pays:** ON-DEMAND ~−7 KB per doc-read event; kills a stale directive that
  misroutes agents to a retired file (A#6, A#7).
- **Touches:** 2 docs + .omt (@budget ×2) + harnessc measure pins.

## OPT-C — DSL `{@var.x}` interpolation (payloads + numeric attrs)
- **What:** Grammar extension in harnessc: interpolate `{@var.x}` inside
  `: payloads` and msg text; allow `@var` refs in numeric attrs. Single-sources
  e2e_cmd (.omt:24 vs :130 vs omt_shared.ts:194), scaffold (:34 vs :127),
  mvc_check (:32 vs :133), window/cap ×4 (:16-17 vs :144 vs TS vs tdd/state.py).
- **Pays:** flexibility — one-edit constant changes; kills a whole drift class
  (B1.1–1.3, B3.6). Prerequisite synergy with OPT-G.
- **Touches:** harnessc (renderer+resolver), .omt records, e2e. Compiler-side
  only → cheap rounds.

## OPT-D — harnessc check hardening (drift police; 3 live drifts found)
- **What:** New build errors for: fsm transition targets + initial∈states;
  hat allow/revert_on vocab; inject on= vocab; pred arg shapes; gate order
  uniqueness; orphan/unreferenced records (@msg artifact :127, mvc_warn :133
  already orphaned); doc/xref claims vs code truth — **drift already present**:
  tdd.done_allowlist says ×3 but state.py has 6 (.omt:164); xref mvc names vs
  VIEW_IMPORTS_MODEL (.omt:277); xref ledger kinds omit think_consult/tdd
  (.omt:280) (B2.7, B5.1).
- **Pays:** reliability — corpus stays trustworthy as it grows; nav answers
  can't silently lie. Cheap: compiler-only.
- **Touches:** harnessc checks + fix the 3 drifts in .omt + tests.

## OPT-E — TS consumes IR (kill hand-mirrors; HDL-1 completion)
- **What:** TS enforcer reads IR instead of hand-copied literals:
  VALID_TRANSITIONS (phase_gate.ts:27-32 mirrors .omt:80, unchecked), auto_on
  tripled (.omt:85 vs phase_gate.ts:219 vs hc:494), EDIT_TOOLS/SEARCH_TOOLS
  (.omt:36-37 vs omt_enforcer.ts:48, nav_gate.ts:17), FALLBACK_GATES hand-mirror
  (gate_driver.ts:213-220), isProtected/isDocPath fallbacks, dead
  thought_pattern var (.omt:25 never read), @hat dead data (.omt:86-90 vs
  HAT_RULES gates.py:35-42 → engine consumes ir.hats).
- **Pays:** flexibility — order/tools/paths/hats become .omt-only edits; deletes
  ~7 hand-mirror drift surfaces (B1.4-1.5, B2.4-2.6, B3.5).
- **Touches:** TS enforcer ×4 + tdd engine + .omt + e2e. Multi-round.

## OPT-F — HDL-2 after-gates into gate_driver
- **What:** g.mvc + g.tdd_after are declared (.omt:113-114, run= resolved) but
  uninterpreted — after-hook order/logic hardcoded in omt_enforcer.ts:107-119.
  Extend the IR-driven driver chain to after-gates like improvement006 did for
  before-gates.
- **Pays:** flexibility — new after-gates become pure .omt declarations;
  completes the HDL-2 arc (B3.4).
- **Touches:** gate_driver.ts, omt_enforcer.ts, mvc_after.ts, tdd_hats.ts, e2e.

## OPT-G — IR-driven gate messages ({rel}/{tt} interpolation)
- **What:** All six gate msg= attrs are dead — impls throw inline TS strings
  (receipt_guard.ts:22-28, phase_gate.ts:139-149, nav_gate.ts:84-89,
  think_gate.ts:117-131); `{tt}` (.omt:127) interpolated nowhere, `{rel}` only
  in genericImpl. Centralize rendering in the driver/impls from IR msgs.
- **Pays:** flexibility — block/warn text becomes .omt-only edits; ~6 inline
  string sites deleted (B3.3). Synergy: OPT-C gives the interpolation engine.
- **Touches:** gate impls ×5 + driver + .omt + e2e pins.

## OPT-H — Guide dedup vs nav corpus (27.5 KB latent restatement)
- **What:** omt_agent_guide.md (27471 B) hand-restates the .omt corpus;
  drift already present (B2.7). Either convert guide → generated projection
  (harnessc render_guide from records) or slim to section-pointers into
  omt_nav. Keeps §12/§16 authority single-sourced.
- **Pays:** ON-DEMAND when guide is read (−20+ KB) + kills the largest
  double-maintenance surface (A#9 note 6).
- **Touches:** guide + harnessc (if projection) + xref records. Larger effort.

## OPT-I — Corpus derive round 2 + dead-record prune (nav_index headroom)
- **What:** @derive expansion: @flow tdd_*/start_* skeletons (:260-266) from
  @fsm/@phase/@hat; tree.* (:203-205) from @gate; prot.files/esc (:179-180)
  from @protect/@tool. Prune or wire: dead @hat data, orphan @msg artifact /
  mvc_warn. nav.index 88% → ~80% budget; fewer hand records to drift
  (B2.1-2.4).
- **Pays:** ON-DEMAND nav answers smaller; corpus −~15 hand records; budget
  headroom for future knowledge.
- **Touches:** harnessc derive + .omt + nav pins. Agent-visible text changes →
  verify nav e2e.

---

## Selection matrix (strategy-rule weighted)

| OPT | Token/turn | Token/startup | On-demand | DSL/flex | Drift killed | Effort |
|---|---|---|---|---|---|---|
| A | ★★★ | | | ★ (budget) | | S |
| B | | | ★★ | ★ (budget) | stale directive | S |
| C | | | | ★★★ | 4 literals classes | M |
| D | | | | ★★ | 3 live + future | S-M |
| E | | | | ★★★ | 7 mirrors | M-L |
| F | | | | ★★★ | after-gate hardcode | M |
| G | | | | ★★ | 6 string sites | M |
| H | | | ★★★ | ★★ | biggest dup | L |
| I | | | ★★ | ★★ | ~15 records | M |

Recommended first pick (token rule #2): **OPT-A** (only every-turn leak left).
Recommended first pick (DSL rule #3): **OPT-C** (unlocks G, feeds E/F).
User may pick one, several, or ALL (improvement006 precedent).
