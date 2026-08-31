# Test report — feature_041.resource_places_concurrency (meta_harness_concurrent core 3/3)

> Date: 2026-08-30 · minor_feature (declaration-only artifact; tests live in `tests/scripts/omt/test_net_resources.py` + `test_net_sync.py` + sentinel `tests/features/feature_041.resource_places_concurrency/`) · PROJECT.md D1–D18, IDEA-002 v4 §2.2/§5.1 · Resumed from `.sandbox/pause_2026-08-30e.md` → GREEN + dogfood per `.sandbox/pause_2026-08-30f.md` (design R1–R8 locked @ `.sandbox/pause_2026-08-30d.md`)

## Verdict

**COMPLETED.** The five complement/resource places (`agent_attention`, `src_edit_capacity`, `tests_capacity`, `harness_surface_round`, `e2e_receipt` — all capacity 1 per IDEA-002 v4 §2.2) are now first-class in the single supervisor net: the bootstrap skeleton materializes them (R1), every subnet template wires `agent_attention` claim/release arcs (R2 — `f{N}_start` claims, `f{N}_complete` releases, serial-mirror conflict trap per IDEA-002 §2.3), the derived overlay refines `ports.resources = sorted((entry ∪ exit) ∩ RESOURCE_PLACES)` (R3 — P10 pure), `resource_report()` + the additive `resources[]`/`conflicts[]` invariant-envelope keys surface capacity violations and pending-blocked subnets with `blocked_by` (R4), resync of pre-041 bundles emits exactly ONE deterministic `add_resource_places` proposal entry with retrofit arcs (R5 — never auto-applied, D4), and lifecycle events (`project.py` new/link/close/archive/reopen + `new_feature.py --project` link) auto-propose re-sync via the fail-open `lifecycle_sync_hook` (R6). Dogfooded on the REAL SSOT: **rev 0 → rev 1** (catalog applied via `sync`→`splice{mode:add}`, invariant green via CLI). No op-enum/TS/budget churn (R8); full sentinel **1756 passed, 0 failed**; harnessc build+check 0 errors; drift pins 12/12; e2e 1/1.

## Red→green cycles (manual; minor_feature → tdd_mode:false)

| Cycle | Target | Tests | Evidence |
|-------|--------|-------|----------|
| 1 | R1/R3 bootstrap + overlay: `TestBootstrapResourceCatalog` | 1 | RED (no `RESOURCE_PLACES`, skeleton lacks catalog) → GREEN: bootstrap materializes 5 places M0=1 in net + live_marking + overlay atomically |
| 2 | R2/R4 attention wiring + conflict surfacing: `TestSubnetAgentAttentionWiring` | 7 | RED → GREEN: template wires claim/release; **two-feature conflict blocks second start** (the ≥2-concurrent-feature success criterion); conservation law `agent_attention` + actives; invariant envelope reports conflict + holder; legacy (pre-041) bundle → empty report; seeded active without claim → `capacity_ok:false` violation; multi-resource fire conserves each pair |
| 3 | R5 resync proposal: `TestResyncResourceProposal` | 4 | RED → GREEN: resync proposes ONE `add_resource_places` entry; retrofit arcs for unwired subnets; no entry when catalog present; applied entry refines `ports.resources` |
| 4 | R6 lifecycle hooks: `TestLifecycleSyncHook` | 6 | RED → GREEN: hook calls sync + prints one line; silent when proposal empty; fail-open on net error; skips when unbootstrapped; `project.py new` triggers hook (`net_sync` ledger record); `new_feature.py --project` link triggers hook (also pins the hermetic-`FEATURES_DIR` print fix, rc==0) |
| 5 | R5 sync-suite evolved pins: `test_net_sync.py` | 9 (3 evolved + 6 untouched) | RED 3 → GREEN 9/9; the 6 pre-existing pins stayed green throughout (no regression in the feature_040 sync contract) |

RED total: **21 pins failed** for the right reasons (absent catalog/helper/hook) → GREEN **27/27** in one implementation round.

## Implementation round (one bash transform round, 17 exact-match replacements, receipt round-robin honored — ONE e2e refresh after ALL edits, R8)

- `scripts/omt/net/state.py`: `RESOURCE_PLACES` catalog (5 places, cap=1) · R1 bootstrap skeleton (+5 M0=1 places, live_marking + overlay) · R2 `_subnet_mutation` agent_attention claim/release arcs (9 arcs, appended last → deterministic byte-stable order) · R3 `derive_overlay` `ports.resources` refinement · R4 NEW `resource_report(st)` (resources[] capacity/live/capacity_ok/holders + conflicts[] pending-blocked with `blocked_by` = empty unprefixed start inputs) · R5 `sync()` resync → ONE `add_resource_places` proposal entry (`net_sync` record gains `add_resource_places` + `retrofit_arcs`) · R6 NEW `lifecycle_sync_hook(event)` (lazy import, try/except fail-open, silent when unbootstrapped, proposal-only D4, one-line stdout).
- `scripts/omt/net/cli.py`: `_invariant` envelope gains ADDITIVE `resources`/`conflicts` keys (after `drift`); `RESERVED_OPS` stays `("synthesize",)` — no op-enum churn.
- `scripts/omt/project.py`: `_net_auto_sync(event)` helper (lazy `from net import state`, fail-open) wired after `_sync_all()` in cmd_new/link/close/archive/reopen — deliberately NOT cmd_sync/cmd_backfill.
- `scripts/omt/new_feature.py`: `new_feature_link` hook after successful `--project` link (rc==0, AFTER the link ledger append) + spec-driven fix: created-paths print survives a hermetic `FEATURES_DIR` outside the repo (`relative_to` ValueError → absolute-path fallback).

## Live smoke (dogfood on the REAL SSOT — rev 0 → rev 1, D16)

| Op | Envelope / result |
|----|-------------------|
| `sync` (resync at rev 0) | proposal = 41 `add_subnets` entries (UNAPPLIED — user decision, D4) + **ONE `add_resource_places` entry** (5 catalog places, `retrofit_arcs: []` — no subnets at rev 0), exactly as designed |
| `splice mode:add` (resource-catalog entry only) | **rev 1**; conformance 9/9; marking = 3 boundary + 5 resource places (all 1 except `goal_satisfied`=0) |
| `invariant` (via CLI `net_check.py`) | `ok:true` · 5× `{capacity:1, live:1, capacity_ok:true, holders:[]}` · `conflicts:[]` · drift `net=ledger=1` · `live_marking_invariants_hold:true` |

Re-verified at wrap-up (this session): `invariant` still green — rev 1, drift-free, 5/5 resources capacity_ok, no conflicts. The 41 subnet proposals stay UNAPPLIED by design (D4; sync will keep re-proposing them).

## Suite numbers

- `tests/scripts/omt/test_net_resources.py` (18) + `test_net_sync.py` (9): **27/27** canonical.
- `uv run pytest tests/scripts/omt tests/features/feature_041.resource_places_concurrency`: **344 passed** (041 sentinel bridge 2/2 — structural floor + subprocess re-execution of the canonical suite, feature_039/040 precedent).
- Full sentinel `uv run pytest`: **1756 passed, 0 failed** (exactly the predicted baseline: 1736 + 18 new + 2 sentinel).
- Drift pins **12/12** · e2e **1 passed** (receipt refreshed ONCE, post-transform) · `harnessc build`+`check` **0 errors** (253 records — budgets untouched, R8).

## Finding — omt_net.ts proxy bug (pre-existing, NOT feature_041 scope)

- `omt_net{op:invariant}` and `omt_net{op:probe}` **via the MCP plugin always fail**: `.opencode/plugins/omt_net.ts:42` appends `--session <context.sessionID>` to EVERY op's argv, but the CLI `probe`/`invariant` subparsers declare no `--session` → argparse `unrecognized arguments` (exit 2 → `engine_error` envelope). Latent since feature_039 (dogfoods used the CLI or --session-accepting ops; the D7 `omt_complete` hook calls the CLI in-process, so nothing surfaced it).
- **The Python engine is correct** — this is a proxy arg-whitelist bug. TA gotcha recorded @ `.opencode/plugins/omt_net.ts:43`. No test covers it yet — the fix feature must add one RED-first.
- **Workaround:** use the CLI (`uv run scripts/omt/net_check.py invariant|probe`) or --session-accepting ops.
- **Decision deferred to the user (exit review):** scaffold bug_fix **feature_046** (per-op arg whitelist in omt_net.ts + pin test) or defer. Deliberately NOT folded into feature_041 (R8: no TS churn in scope).

## Deferred (per FEATURE.md)

- `synthesize` op (goal→net templates) → feature_042 (reserved envelope intact).
- WORK.md net-projection render → feature_045 (**D17 promote-to-core decision at this exit review — user call**).
- Mined behavioral net → feature_044 · dashboard → feature_043.
- omt_net.ts `--session` proxy bug → feature_046 (user decision, above).
