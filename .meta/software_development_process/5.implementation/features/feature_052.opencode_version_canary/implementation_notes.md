# Implementation Notes — feature_052.opencode_version_canary (F1)

> meta_harness_6 Wave 1 / F1 · Programming 2026-09-06 · minor_feature (decl-only)

## What

Fail-loud canary for live-binary drift: the audited opencode line lives in
ONE place (`.omt @var opencode_version_range` → `ir.vars`), session start
warns once per session when the observed binary falls outside it, and a
cheap always-run canary suite fails loudly until the range is deliberately
re-baselined.

## Changes (receipt round 1 — 3 files, 1 logical edit each, 1 e2e refresh)

1. `.meta/META_HARNESS.omt`
   - `@var opencode_version_range : >=1.18.29,<1.19` (floor = live binary
     1.18.29 audited today; ceiling = next minor line).
   - `@msg wrn_opencode_version sev=warn` — text uses `{rel}` for the
     observed version (gateMsg ctx carries only {rel,tt,feature}; documented
     at the call site) + `{@var.opencode_version_range}` baked at build
     (OPT-C). Wired via TS `gateMsg("wrn_opencode_version")` → passes
     `check_msg_orphans`.
2. `.opencode/lib/enforcer/nav_gate.ts`
   - `versionRange()` — IR var with `FALLBACK_OPENCODE_VERSION_RANGE`
     literal (posture: pinned vs IR by source-pins test).
   - `versionInRange(ver, range)` (exported) — minimal grammar:
     comma-separated `>=V|<=V|>V|<V|=V|V(exact)`, V dotted-numeric, ALL hold;
     null on unparsable input (fail-open).
   - `liveBinaryVersion()` (exported) — `opencode --version`, first token;
     null when unobservable (absence ≠ drift, never warns).
   - `opencodeVersionWarn()` appended to the `sessionBootstrap` firstEver
     branch (the ONE per-session emission site) — WRN only, never a block.
3. `tests/scripts/omt/test_omt_enforcer_guard_source_pins.py`
   - `test_version_range_fallback_matches_ir` (fallback pin, NAV_GATE style).
4. `tests/features/feature_052.opencode_version_canary/test_version_canary.py`
   (new, under tests-canary skip): IR var/msg wiring pins, 9-case + 5-case
   grammar matrix (Python mirror), and THE canary —
   `test_live_binary_inside_audited_range` (`opencode --version` in range,
   skipif binary absent).

## Round-discipline note

The .omt + nav_gate.ts multi-region changes ran as ONE `uv run python`
script (single execution, each file written once — no intermediate state
was ever observed/tested), i.e. one logical round-1 edit; the pins-file
addition is a different file (parallel-OK). ONE e2e refresh covers all
three (receipt fresh, `1 passed`).

## Probe evidence (R6 recipe, real implementation, no LLM cost)

- `bun /tmp/opencode/f52_probe.ts` (repo root, live binary 1.18.29):
  versionInRange matrix 9/9 incl. null-on-unparsable; liveBinaryVersion() =
  1.18.29; in-range bootstrap emits NO version WRN while the TA digest
  still fires.
- `PATH=/tmp/opencode/fakebin:$PATH bun /tmp/opencode/f52_probe2.ts`
  (fake `opencode` → "9.9.9"): bootstrap output carries
  "⚠️ opencode binary 9.9.9 is outside the audited range
  (>=1.18.29,<1.19) — …" + digest intact. WRN branch proven end-to-end.
- GOTCHA (Bun quirk, future probes): `execFileSync` ignores RUNTIME
  `process.env.PATH` mutation (startup snapshot) — fake-binary probes must
  set PATH at bun launch, not inside the script.

## Non-goals honored

g.think / g.protect untouched (no TA:-carrying file edited — nav_gate.ts
and META_HARNESS.omt verified anchored-`TA:`-free before editing, so no
think consult was required); no gate added (B1 net-zero policy safe);
steady-state token cost zero (WRN fires only out-of-range; no budget
records touched — nav_tip/digest_cap untouched).
