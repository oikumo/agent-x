# Analysis 001: Net-driven WORK.md render/parse/propose contract

> **Phase:** Analysis
> **Feature:** feature_045.work_md_net_driven (minor_feature, core 4/4 per D17)
> **Design basis:** IDEA-005 + `ideas/WORK.md.net-driven-example` + PROJECT.md D16/D17/D19
> **Live net:** rev 43, drift-free, 5/5 resources capacity_ok, enabled 6 starts (f001/f002/f042/f043/f044/f045)

## Problem statement

WORK.md Tasks/Projects are hand-maintained prose; the net bundle
(`META_NET.petri.json` + sidecar + overlay, rev 43) is the D16 state SSOT.
No mechanical link exists: checkbox edits never validate against the net,
resource conflicts stay invisible, drift is silent. IDEA-005 + D19 require
WORK.md to become a deterministic net projection + proposal surface, and
the 045 render *is* the session-start menu (NEXT + enabled + blocked +
resources, rev-stamped).

## Current implementation (verified on disk)

- `scripts/omt/net/state.py` (1203 lines): `sync()` bootstraps supervisor
  skeleton (feature_ready=1, resource_token=1, goal_satisfied=0, 5-place
  catalog all M0=1) then scans reality (feature dirs + WORK.md Tasks
  checkboxes + Projects table) and emits proposal-only
  `{add_subnets, disable_subnets, add_resource_places}` — never auto-applied
  (D4). No md render/parse exists. `_scan_reality` already parses Tasks
  checkboxes (`_TASK_ROW_RE` + `_CHECKBOX_M0`) and Projects rows — the md→net
  parse half is partially built.
- `scripts/omt/net/cli.py`: `sync` op takes only `--reasoning/--session`;
  no md directions. `probe` gives marking/enabled/advice; `invariant`
  gives resources[]/conflicts[] + drift envelope. `RESERVED_OPS=("synthesize",)`.
- Live probe rev 43: `agent_attention=1` free, all resources 1/1, 6 pending
  starts enabled, `f046_done=1` (archived pattern), `archive_pool=39`.
  invariant green, drift false (net rev == ledger rev 43).
- TA consults done: state.py:58 (R1-R8 catalog cap=1, sketch 2/3 rejected),
  state.py:297 (REBUILD-remove + derived overlay P10), cli.py:36/37
  (additive resources/conflicts, splice/sync contract). KB nav: no TIER_CORE
  hit — no src/ contract to reuse; sync.py is green-field in `scripts/omt/net/`.

## Substrate inventory

| Substrate | Path | 045 use |
|---|---|---|
| Net bundle (state) | `.meta/.omt/META_NET.petri.json` + sidecar + overlay (git-ignored, D15) | render source; parse target |
| `sync()` scan | `state.py:_scan_reality/_subnet_mutation` | reuse checkbox/projects parse; extend with render |
| `probe`/`invariant` | `cli.py:_probe/_invariant` + `resource_report` | menu data: enabled[], holders, conflicts[] |
| WORK.md live | `WORK.md` ## Tasks / ## Projects | render target (tasks/projects blocks only; CONV_* stays) |
| Target sketch | `ideas/WORK.md.net-driven-example` | template basis (rev-stamp, Net Status, Tasks, Resources, Blocked, Scratchpad) |
| Ledger audit | `.meta/.omt/ledger.jsonl` `kind:"net_sync"` | render/propose audit; D7 drift hook unchanged |

## Constraints discovered

- **D4 proposal-only:** md→net never writes state; returns fire/splice
  proposals validated by analyzer (`is_enabled_at`), agent fires explicitly.
  Stale rev (`R != probe revision`) refuses fire, re-renders first.
- **D16 SSOT:** net owns state; WORK.md blocks are renders, ledger is audit.
  Only Tasks/Projects blocks become renders; Convention/Scratchpad keep
  existing authority.
- **P10 derived overlay:** render reads `derive_overlay` output; never
  persists membership by hand.
- **Conformance gate:** structure-changing sync applications go through
  splice path (9-vector gate pre-save); render itself is read-only.
- **F5 zero churn:** no new tool — `sync` gains md directions
  (`--direction net_to_md | md_to_net_propose`, `--dry-run`); no new ops,
  budgets, gates, hooks, ledger kinds (D19: menu needs none).
- **D1/D2/D3:** harness-only (`scripts/omt/net/` + WORK.md); no `src/` edits;
  no engine change; no gate/FSM change.
- **Determinism:** same marking → byte-identical block (sorted subnets,
  fixed template, rev-stamp header `<!-- net_rev:R | sync_ts -->`).
- **D19 menu contract:** `NEXT` = smallest pending core/phase-2 start
  (recommend 045 until done, then 042→044); `Blocked` with structural reason
  (holder/conflict pair); `Resources` one line with capacity_ok flags.

## Recommendation

Proceed to Design with the locked surface:

- **New module `scripts/omt/net/sync_md.py`** (pure functions, stdlib only):
  `render_work_md(net, marking, overlay, resources, conflicts, revision)` →
  Tasks/Projects block text; `parse_work_md(text)` → desired marking diff;
  `propose_diff(net, marking, diff)` → fire/splice proposals (analyzer-validated).
- **`sync` extension:** `--direction net_to_md` (render+write-if-changed,
  ledger `net_sync` with `md_rev`) and `md_to_net_propose` (parse+propose,
  drift-log on blocked, never apply). Default direction keeps current
  proposal behavior (backward compat with `test_net_sync.py` pins).
- **Test bar:** round-trip vector (marking→render→parse→same enabled set);
  proposal-validity (every proposal analyzer-enabled); drift (hand-edit →
  logged, not applied); resource-block (over-capacity → blocked);
  D19 menu vector (6 starts ordered, NEXT + resources line, stale-rev refuse).
- **Migration:** one-time `sync --direction net_to_md --bootstrap-render`
  initializes blocks from rev 43; no hand migration.
