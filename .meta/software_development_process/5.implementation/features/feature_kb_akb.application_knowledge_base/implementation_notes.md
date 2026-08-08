# Implementation Notes — feature_kb_akb.application_knowledge_base

> Date: 2026-08-08 (session 12) | Phase: Programming → Testing | Feature: feature_kb_akb
> Design doc: `.projects/meta/feature_kb_akb/PROJECT.md` v2.1

## Overview

The Application Knowledge Base (AKB) delivers a unified concept-altitude index of the agentx source code, queryable by coding agents via `omt_kb_nav` before `src/` edits. Sessions 8-11 implemented the data path (AST skeleton extractor, build CLI, overlay merge, budget removal, `@inject kb_bootstrap`, per-query cap); session 12 closed out the implementation (stopword fix → real build → live validation → B7 Agent overlay) and then caught & fixed a silent gate-wiring gap (`g.kb` consult gate declared in IR but never implemented in code).

## Session-12 deliverables

### Code-tier finalization (non-gated)
- **`subsystems.kb.omt:33` stopword fix**: reworded `is_directory_allowed_to_deletion`→`dir-deletion predicate`, `is_valid_url`→`url validation` (snake_case identifiers split by the `[a-zA-Z]+` regex tripped the `'is'` stopword).
- **`kb_compiler.py build` functional**: 437 records (class=239, contract=32, dep=104, doc=39, feature=12, flow=9, xref=2), 0 errors, 4 dup warnings (legacy splits).
- **B7 acceptance (Agent facade overlay)**: added `@class Agent tier=code refs=...` to `code.kb.omt`. `nav CLASS_AGENT` now returns full curated concept text instead of skeleton auto-text.

### g.kb consult-gate wiring follow-up (harness-surface — 3 files, one e2e round)

**Silent gap discovered via B6 verification**: `g.kb` (gate_driver.ts:228) declared `requires: "session_flag(kb_consulted)"`, `skip_ok: false`, `hard: true`, but:
- `SESSION_FLAGS` registered only `nav_used` — no `kb_consulted` impl.
- `omt_kb_nav.ts` wrote no session-state flag.
- Net effect: any agent editing `src/agentx/**` was permanently hard-blocked; consult gate wired in IR but unimplemented in code.

**Wiring fix (mirror the `nav_used`/`omt_nav` pattern):**

```
session_state.ts   + kb: Map<session, {consulted: boolean}>      (new state field)
nav_gate.ts        + KB_TOOLS = new Set(["omt_kb_nav"])          (mirror NAV_TOOLS)
                   + kbTrack(env, session, input)               (mirror navTrack:
                       sets state.kb.get(session).consulted = true
                       when input.tool === "omt_kb_nav")
gate_driver.ts     + SESSION_FLAGS["kb_consulted"]: (ctx) =>     (mirror nav_used pred:
                       !!ctx.env.state.kb.get(ctx.session)?.consulted)
omt_enforcer.ts    + import { kbTrack }                          (compose into before-hook)
                   + await kbTrack(env, session, input)          (line next to navTrack call)
```

Behavior post-fix:
1. Agent calls `omt_kb_nav{op:nav, query:"CLASS_..."}` → before-hook runs `kbTrack` → `state.kb.get(sessionId).consulted = true`.
2. Agent attempts `write`/`edit`/`patch` on `src/agentx/...` → before-hook runs `g.kb` gate → `requires: "session_flag(kb_consulted)"` evaluates `SESSION_FLAGS["kb_consulted"](ctx)` → reads `state.kb.get(session).consulted` → `true` → gate passes.
3. Without prior consult, `state.kb.get(session)?.consulted` is `undefined` → `false` → gate hard-blocks with `gateMsg("kb_required")` → `@msg kb_required` text displayed ("Run omt_kb_nav{op:nav, query} before editing src/") — the agent is told exactly what to consult.

### Test changes (tests/ — receipt-exempt)

1. **`tests/scripts/omt/test_omt_harness_e2e.py`**:
   - Added `omt_kb_nav.ts` to `HARNESS_FILES` list (drift fix — it was already covered by `@var harness_paths` in `META_HARNESS.omt` but missing from the e2e file's list; second-edits to it weren't receipt-guarded).
   - Added §12 structural-wiring block asserting: `SESSION_FLAGS[kb_consulted]` in gate_driver, `kbTrack` exported by nav_gate + imported+called by omt_enforcer, `state.kb` Map in session_state, `KB_TOOLS` set in nav_gate.

2. **`tests/scripts/omt/test_tdd_check.py::test_gate_returns_allowed_when_no_tdd`**:
   - Stale `assert data["allowed"] is False` (commit `0bdbbf0`) expected the python `tdd_check.py gate` to enforce `g.kb`; `g.kb` actually lives in TS gate_driver.ts. Rewrote assertion to validate the structural `state ∈ {valid set}` (the python gate's job is TDD two-hats only, not consult).

## Tests (verified)

```bash
# All KB-specific tests
uv run pytest tests/scripts/omt/test_kb_*.py -q
# 21 passed in 0.60s

# Harness e2e + drift pins + tdd_check (post-wiring)
uv run pytest tests/scripts/omt/test_omt_harness_e2e.py \
  tests/scripts/omt/test_omt_docs_drift_pins.py \
  tests/scripts/omt/test_tdd_check.py -q
# 46 passed

# Full suite: 1141 passed, 7 baseline failures (see test_report.md §4)
uv run pytest
# 7 failed, 1141 passed in ~2 min
# (2× feature_007 MVC god-controller regression from feature_024 paused work;
#  3× feature_018 react_screen textual+py3.14 mock __name__ interaction;
#  2× feature_016 test_tdd_enforcement leftover-done-state assertion fragility.
#  All 7 verified pre-existing via `git stash`.)
```

## Live consult gate verification (caveats)

The TS-side gate (gate_driver.ts) executes inside the opencode host process, which loads plugins at session start. Mid-session edits to `.opencode/plugins/*` and `.opencode/lib/enforcer/*` are NOT picked up until the host restarts. Therefore the live consult-then-edit-allowed cycle is verified by the structural e2e pins (above) AND by manual exploration on a fresh session. The Python-side companion gate (`tdd_check.py gate`) is unrelated — it enforces TDD two-hats only, never consult.

## Files touched this session (session 12)

**Code-tier finalization (non-gated):**
- `.meta/doc/omt++/subsystems.kb.omt` — line 33 stopword fix.
- `.meta/doc/omt++/code.kb.omt` — added `@class Agent` overlay record (B7).
- `.meta/.omt/kb.index.jsonl` + `.meta/.omt/kb.ir.json` — regenerated by `kb_compiler.py build` (gitignored outputs).

**g.kb wiring (harness-surface — gated: 1st edit free, 2nd needs e2e receipt round-robin):**
- `.opencode/lib/enforcer/session_state.ts` — added `kb: Map<string, {consulted: boolean}>` field.
- `.opencode/lib/enforcer/nav_gate.ts` — added `KB_TOOLS` set + `kbTrack` export.
- `.opencode/lib/enforcer/gate_driver.ts` — added `SESSION_FLAGS["kb_consulted"]` impl.
- `.opencode/plugins/omt_enforcer.ts` — added `kbTrack` import + before-hook call.

**Tests (receipt-exempt):**
- `tests/scripts/omt/test_omt_harness_e2e.py` — HARNESS_FILES list + §12 wiring block.
- `tests/scripts/omt/test_tdd_check.py` — stale-assertion rewrite.

**Docs:** `CURRENT_STATE.md` session-12 entry + `test_report.md` §8 follow-up.
