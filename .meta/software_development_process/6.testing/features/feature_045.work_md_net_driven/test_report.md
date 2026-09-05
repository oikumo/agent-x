# Test report — feature_045.work_md_net_driven (minor_feature, core 4/4)

> Phase: Programming → Testing. Design:
> `4.design/features/feature_045.work_md_net_driven/design_001_sync_md_spec.md`.

## New tests (RED→GREEN, manual — minor_feature, tdd_mode:false)

`tests/scripts/omt/test_net_sync_md.py` ×6 — RED confirmed pre-impl
(6 failed: no `net.sync_md`, no `--direction`); GREEN post-impl (6 passed):

- round-trip same-enabled · proposals-are-enabled · hand-edit-blocked-logs-drift
- resource-block over-capacity (serial-mirror: 1 fire + rest blocked)
- menu order NEXT/resources · cli net_to_md dry-run

## Regression

- Net suite (sync/splice/cli/resources/state/engine/conformance/plugin_args):
  92 passed; + sync_md 6 = 98 net green.
- Pins: `test_omt_net_plugin_args.py` 6/6 (direction ⊆ CLI flags; session rules hold).
- e2e receipt refreshed post-harness-edits: 1 passed.
- Dogfood real SSOT rev 43 (dry-run, no state write): `NEXT: f001_start`,
  6 pending ordered, 046 done, `Resources: 5/5 free`, proposal empty.
- Full sentinel: **1767 passed, 1 failed**
  (`test_nav_reminder_deferred_after_nav_first`) — flake, not 045:
  passes in isolation (1 passed) and the guards file is green standalone
  (2 passed). Unrelated substrate (nav reminder vs net sync_md).

## Files

- new: `scripts/omt/net/sync_md.py`, `tests/.../test_net_sync_md.py`
- edit: `scripts/omt/net/state.py` (sync direction/dry_run + md branches +
  `_write_md_section`), `scripts/omt/net/cli.py` (--direction/--dry-run/--work-md
  + envelope), `.opencode/plugins/omt_net.ts` (sync direction whitelist + dry-run flag)
