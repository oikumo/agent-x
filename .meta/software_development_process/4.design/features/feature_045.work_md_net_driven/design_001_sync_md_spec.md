# Design 001: sync_md render/parse/propose + sync md directions

> **Phase:** Design
> **Feature:** feature_045.work_md_net_driven (minor_feature, core 4/4)
> **Analysis:** `3.analysis/features/feature_045.work_md_net_driven/analysis_001_net_md_contract.md`
> **Basis:** IDEA-005 + `ideas/WORK.md.net-driven-example` + D16/D17/D19

## Summary

Add pure module `scripts/omt/net/sync_md.py` (render/parse/propose, stdlib
only) and extend `omt_net{op:sync}` with `--direction net_to_md |
md_to_net_propose` (+ `--dry-run`, `--work-md` override for tests). No new
tool, op, gate, hook, or ledger kind. The 045 render doubles as the D19
session-start menu block inside `## Tasks`.

## Components / Files Affected

| File | Change |
|---|---|
| `scripts/omt/net/sync_md.py` (new) | Pure render/parse/propose; no net I/O, no ledger |
| `scripts/omt/net/state.py` | `sync()` gains `direction` param; delegates to sync_md; ledger `net_sync` gains `direction/md_rev/proposals` fields (additive) |
| `scripts/omt/net/cli.py` | `sync` parser gains `--direction/--dry-run/--work-md`; envelope gains `rendered/proposals` (additive) |
| `WORK.md` | Tasks/Projects blocks become renders (net_to_md writes them) |
| `tests/scripts/omt/test_net_sync_md.py` (new) | Round-trip + propose + drift + resource-block + menu vectors |
| `.opencode/plugins/omt_net.ts` | Pass-through of new sync args (OP_ARGS whitelist update, same pattern as 046) |

**No changes to:** engine (`model/analysis/io/errors/conformance`), splice/fire/probe/invariant, overlay derivation (P10), gates/FSM, budgets, `src/`.

## Static Structure

```python
# sync_md.py — pure, deterministic, stdlib only
def render_tasks_block(net, live_marking, overlay, resources, conflicts, revision) -> str
def render_projects_block(overlay, projects_map) -> str
def render_net_status(live_marking, resources, conflicts, revision) -> str
def parse_tasks_block(text) -> dict[str, str]   # {N: pending|active|done}
def propose_diff(net, live_marking, desired) -> {"fires": [...], "blocked": [...]}
def menu_lines(enabled, resources, conflicts, revision) -> list[str]
```

- `render_tasks_block`: header `<!-- net_rev:R -->` + `NEXT: fN_start
  (recommended)` + `Other enabled:` + `Blocked:` (with `blocked_by` reason)
  + per-subnet rows `- [ ]/~|x|! **feature_NN.slug**` sorted by N. Same
  marking → byte-identical output (sorted keys, `\n` joins, no timestamps
  inside the block; `sync_ts` lives only in the ledger record).
- `parse_tasks_block`: reuses `_TASK_ROW_RE`/`_CHECKBOX_M0` semantics
  (`" "`→pending, `"~"/"!"`→active, `"x"/"X"`→done); unknown rows ignored.
- `propose_diff`: for each N where desired != actual, propose
  `fN_start` (pending→active) or `fN_complete` (active→done); validate each
  via `net.is_enabled_at(live_tuple, t)`; disabled → `blocked[]` with
  `blocked_by` (empty unprefixed inputs), never applied.
- `menu_lines`: `NEXT` = smallest pending N with enabled start, display
  recommendation `045 until done else 042→044`; `Resources: 5/5 free` or
  `holders`; `(net rev R)` suffix; stale (`R != probe revision`) → caller
  re-renders before fire.

### CLI contract

```
omt_net sync --direction net_to_md|md_to_net_propose|proposal (default proposal)
  --reasoning "" --session "" --dry-run --work-md <path>
```

- `proposal` (default): current behavior, byte-identical envelope (backward
  compat with `test_net_sync.py` pins).
- `net_to_md`: render blocks from live state; `--dry-run` returns text only;
  else writes WORK.md Tasks/Projects sections in place (header/convention/
  scratchpad untouched), ledger `net_sync{direction, md_rev:R}`.
- `md_to_net_propose`: parse WORK.md, diff vs live, return
  `{proposals:{fires[], blocked[]}}`; blocked → drift log row, exit 0.
- Envelope additive keys only (`rendered: str|None`, `proposals`); existing
  `proposal/bootstrap/conformance` keys unchanged.

### WORK.md edit discipline

`net_to_md` replaces text between `## Tasks` and the next `## ` header, and
the `## Projects` body, only. Rotation (`WORK_ARCHIVE.md`), Convention, and
Scratchpad sections are never touched. Hand edits inside the blocks are
inputs to `md_to_net_propose`, never state.

## Testing

`tests/scripts/omt/test_net_sync_md.py` (hermetic: `OMT_NET_DIR` +
`OMT_NET_WORK_MD` tmp dirs):

1. round-trip: marking→render→parse→same enabled set (rev 43 fixture + 2
   synthetic markings).
2. proposal-validity: every proposed fire `is_enabled_at` live.
3. drift: hand-edited checkbox (e.g. activate f043 while attention held) →
   `blocked[]` non-empty, drift row appended, no state write.
4. resource-block: over-capacity propose → analyzer blocks.
5. menu: 6 starts ordered, `NEXT: f045_start`, resources line, stale-rev
   refuse path.
6. backward-compat: default `proposal` envelope shape == current pins.

Sentinel bridge re-export per `Programming→Testing` matcher (thin wrapper,
same pattern as 039–041).

## Risks

- Template churn vs `_scan_reality` regexes: parse and render share one
  row-format constant (`TASK_ROW_FMT`) — single source, tested both ways.
- WORK.md section-header drift: `_md_section` prefix-match reused; unknown
  headers fail closed with `invalid_work_md` envelope, never partial write.
- Receipt guard: WORK.md is not a harness path — no e2e round needed for
  render writes; `omt_net.ts` arg pass-through is the only harness-surface
  touch (one e2e round, same convention as 046).
