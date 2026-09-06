# Test Report — feature_052.opencode_version_canary (F1)

> meta_harness_6 Wave 1 / F1 · Testing 2026-09-06 · HEAD = feature_052 WIP (uncommitted)

## Acceptance criteria → results

| Criterion (evaluation §5 F1) | Result |
|---|---|
| `@var opencode_version_range` declared | ✅ `.omt` → `ir.vars.opencode_version_range = ">=1.18.29,<1.19"`; pinned by canary `test_range_present_and_parses` + source-pins `test_version_range_fallback_matches_ir` |
| Session start emits WRN when out of range | ✅ `sessionBootstrap` firstEver branch appends `gateMsg("wrn_opencode_version")` (range baked, observed version in `{rel}` slot); proven end-to-end by fake-binary (9.9.9) bun probe — WRN text exact, digest intact |
| Live-binary probes become a fail-loud canary suite (GOTCHA_LIVE_BINARY recipe) | ✅ `test_live_binary_inside_audited_range` runs `opencode --version` (no LLM, ~ms) and FAILS with a re-baseline recipe on drift; the 2-trip LLM live smoke stays the deep layer (unchanged) |
| A gate that stops firing without notice is worse than no gate | ✅ version change now fails in 2 places at once: pytest canary (CI/local) + session-start WRN (live sessions) |
| Full suite green, budgets green, receipt fresh | ✅ **1866 passed, 0 failed** (empty allowlist); `harnessc check` 0 errors (258 records); build OK, all 12 budgets green; e2e receipt refreshed (round 1) |

## Runs

| Command | Result |
|---|---|
| `uv run pytest tests/features/feature_052.opencode_version_canary/ tests/scripts/omt/test_omt_enforcer_guard_source_pins.py -q -k "version or ..."` | 18 passed |
| `bun /tmp/opencode/f52_probe.ts` (real impl: range matrix + live 1.18.29 + in-range bootstrap silence) | 14/14 (4 fake-PATH checks N/A by Bun quirk — covered by probe2) |
| `PATH=/tmp/opencode/fakebin:$PATH bun /tmp/opencode/f52_probe2.ts` (9.9.9 → WRN branch) | 5/5 |
| `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` (receipt refresh, round 1) | 1 passed |
| `uv run scripts/omt/harnessc.py check` | OK — 258 records, 0 errors |
| `uv run scripts/omt/harnessc.py build` | OK — 5 projections, all 12 budgets green (nav_index 63582/64000 — tight but green; Wave 3/B1 owns budget policy) |
| `uv run pytest -q` (full) | **1866 passed, 0 failed** |

## Mechanical failure seen and fixed (not a regression)

- `feature_043::test_live_replay_matches_bundle`: committed dashboard
  snapshot rev 54 vs live rev 56 (my `work_start` 55→56 — same mechanical
  class as A1's session-start trio). Fixed via the prescribed
  `uv run scripts/omt/net_snapshot.py` regen → 3 passed; full suite green
  after.

## Notes

- RED evidence: pre-change, `test_range_present_and_parses` /
  `test_msg_wired_with_baked_range` / the fallback pin failed (no var, no
  msg, no TS consumer); all flipped green only after the round-1 edits +
  rebuild in the same session.
- Re-baseline contract (deliberate act on WRN/canary red): live smoke +
  full suite on the new binary → bump `.omt @var` → rebuild (fallback +
  pins follow) → commit.
- Non-goal honored: no new gate; g.net/g.think/g.protect untouched.
