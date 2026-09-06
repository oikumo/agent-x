# Implementation Notes — feature_056.skip_taxonomy_phase_hygiene (Wave 3/A2+A3)

> meta_harness_6 · minor_feature · 2026-09-06 · Programming→Testing→Done

## What shipped

**A2 skip_purpose_taxonomy** — `omt_skip{reason, scope?, purpose?}` with a closed
`purpose: canary|emergency|break_glass|override` vocabulary (unknown values rejected)
and a scope-aware default (`scope=tests` → `canary`, else `override`), so the 266
opaque historical skips classify meaningfully without re-marking. `omt_status` reports
the 7-day split (friction vs nav-escapes vs evasion); `harnessc check` warns (never
blocks) when 7-day evasion crosses `@var skip_override_warn_per_week` (5).

**A3 phase_hygiene** — phase/skip records auto-expire after `@var unlock_window_ms`
*including session-matched ones* (the stale-shadow hole: an expired phase no longer
shadows a later tests-approval, and stale `scope=all` no longer opens protected
paths). `omt_status` lists expired dangling phases with one-call resume
(`omt_phase` re-declare) / abandon (`omt_phase{phase:"abandoned"}` tombstone).

## Surface (5 harness files, receipt round-robin; tests via documented bash path)

1. **`.meta/META_HARNESS.omt`** (round 1): `@tool omt_skip` args + payload (taxonomy;
   kept the literal `Scopes: a|b` shape — the doc.esc derive regex requires it);
   new `@var skip_override_warn_per_week : 5`; `@state ledger` documents
   purpose/expiry/tombstones; `@xref ledger` gains `purpose,abandons`; `@flow
   skip_src` teaches `purpose:"emergency"` point-of-use. NO new @tool/@doc/@msg.
2. **`.opencode/lib/enforcer/phase_gate.ts`** (round 1): `SKIP_PURPOSES` closed set;
   purpose validation + scope-aware default + ledger field + result echo (seed synced
   byte-exact); `abandonDanglingPhase` + `phase="abandoned"` early-branch (before exit
   validation/TDD-baseline/artifact-link — abandoning must never demand the work it
   retires); tool_args diet trims (design_doc/tdd/advance_to/reason describes).
3. **`.opencode/lib/enforcer/session_state.ts`** (rounds 1–2): `isAliveUnlockRecord`
   (window filter incl. session-matched; tombstones never unlock) +
   `isRetiredByTombstone` (a tombstone retires EARLIER same-feature same-phase
   records; other features/phases unaffected). All-expired sessions resolve to
   no-unlock (fail-closed); sessions owning no records keep the window fallback.
   `hasFastPathUnlock`/`hasNavUnlock` deliberately untouched (C2 owns them).
4. **`.opencode/plugins/omt_status.ts`** (round 1): `skipHygiene()` (read-only — the
   A4 ledger-write-free pin holds) + `Skips 7d:` / `Dangling phases:` lines (cap 10,
   oldest-first) with exact one-call commands; `skip_hygiene` metadata;
   include_ledger describe trim. `CLEARING_ACTIONS` untouched (feature_055 pins).
5. **`.meta/META_HARNESS.omt` → `scripts/omt/harnessc.py`** (round 1): `Corpus.warnings`
   channel (alarm ≠ error, exit stays 0); pure `skip_effective_purpose` /
   `skip_hygiene_counts` / `skip_override_warning` + live-ledger wrapper
   `check_skip_override_alarm` (hot file only — 64 KB cap ≫ a week of skips;
   NOT OMT_LEDGER_PATH-aware: it audits the repo, like the WORK.md checks;
   missing ledger fails open silent). Mirrors the TS `skipHygiene` semantics.
6. **Tests** (`tests/features/feature_056…/`, 32 tests): pure-Python matrices for the
   default rule / 7-day split / warning boundary / wrapper hermeticity (monkeypatched
   REPO_ROOT), static SSOT+diet pins, and bun probes on the REAL TS modules
   (expiry matrix, shadow-kill via the real `guardTestsPath`, purpose+abandon via the
   real tools with ledger read-back, full status-plugin probe, C2 fast-path guardrail).
   Plus e2e check 16 (source-string wiring pins).

## Key design decisions

- **Scope-aware default over required purpose**: requiring purpose would break every
  existing flow/doc/example; defaulting everything to `override` would mislabel the
  canary toll as evasion and chronically trip the alarm. `tests→canary` encodes the
  designed intent of the scope; nav escapes bucket separately (tracked, never
  alarming) so the evasion signal stays about discipline gates (phase/tests/protect/net).
- **One retirement semantic everywhere**: tombstone-retires-earlier-same-phase is
  shared by `getActiveUnlock`, `getActiveFeaturePhase`, the abandon target search,
  and the dangling scan. Round-2 probe catch: without it, abandoning the session's
  current phase resurrected the retired record as the unlock.
- **Warning, not error, for the alarm**: an error would couple `check` (and the
  suites that assert exit 0) to live-ledger behavior. Alarms inform; gates block.
- **`phase:"abandoned"` taught point-of-use, not in the schema**: the phase arg
  describe and `@tool omt_phase` payload are untouched (tool_args/tool_schemas
  headroom); the status printer emits the exact call where it is needed.
- **omt_q left alone**: its U1 fixture's absolute 2026-08-09 dates depended on timeless
  session matching — refreshed to in-window relative timestamps (intent-preserving
  maintenance; the interrogative as-of semantics are E-wave material, not this feature).

## Budget diet (all 12 green)

tool_args 2271/2304 · tool_schemas 1750/1792 · nav_index 63900/64000 ·
ir_json 19875/20480 · agents_md unchanged (render doesn't embed payloads). The 59 B
`purpose` describe was funded by −70 B of redundant-hint trims; the one-liner grew
+33 B net (dropped the redundant `(default all)`); new `@var`/`@state` cost only
ir_json bytes (not nav-indexed); `@xref ledger` +17 B, `@flow skip_src` +21 B.

## Gotchas encountered (session-local)

- **Bun probe factory await**: `(await import(x)).default(args)` returns a Promise —
  the status probe needs `await (await import(x)).default(args)`.
- **Receipt-guard round accounting**: the failed first harnessc.py script (bad anchor
  probe) wrote nothing — a no-op round, not a round touch. The real R1 was the five
  successful per-file transforms.
- **Tool-surface parity gap (process deviation, documented)**: this session's tool
  surface exposes no `omt_skip`, so the tests/ canary skip is unrepresentable here.
  tests/ writes (feature tests, e2e check 16, U1 fixture) went via the sanctioned bash
  path under a declared minor_feature phase, with receipt round discipline kept
  manually and e2e refreshes actually run. No skip record from this session exists in
  the live ledger (verifiable) — the taxonomy is exercised against hermetic ledgers
  in the suite. Recommend B-wave note: agent tool surface should expose omt_skip
  (or document the bash path as the canary equivalent).
