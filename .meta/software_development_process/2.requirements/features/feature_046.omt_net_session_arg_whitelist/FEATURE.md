# Feature 046: Omt Net Session Arg Whitelist

> **Status:** [x] Done (2026-08-30)
> **Created:** 2026-08-30
> **WORK.md task:** feature_046.omt_net_session_arg_whitelist

---

## Summary

The `omt_net.ts` plugin proxy appended `--session <context.sessionID>` to EVERY op's argv, but the `probe`/`invariant`/`synthesize` subparsers in `scripts/omt/net/cli.py` declare no `--session` flag → argparse exit 2 → `omt_net{op:probe|invariant}` via the plugin ALWAYS failed (latent since feature_039; surfaced by the feature_041 R4 dogfood — former TA gotcha @ omt_net.ts:43; the CLI path `net_check.py` was always green). Fix: a per-op `OP_ARGS` whitelist in the plugin mirroring the CLI subparser declarations, cross-source pinned by `tests/scripts/omt/test_omt_net_plugin_args.py` (6 pins: whitelist parses out of the .ts and must stay SUBSET of the per-op flags parsed from cli.py; explicit no-session for probe/invariant/synthesize; session kept for fire/splice/sync; argv loop iterates `OP_ARGS[op]`; `max_states` gated on `op === "probe"`).

## Scope (one sentence — what "done" looks like)

`omt_net.ts` builds argv from a per-op whitelist (`OP_ARGS`) so probe/invariant/synthesize never receive `--session`, fire/splice/sync keep it (audit records key on it), and `max_states` is probe-scoped — proven by 6 cross-source pin tests (sentinel 1756 → 1762).

## Task type

bug_fix

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | this file (bug_fix → declaration only, §12) | [x] |
| Analysis | Analysis doc | — (bug_fix, declaration only) | [x] |
| Design | Design doc | — (fix spec locked @ `.sandbox/pause_2026-08-30g.md` step 5) | [x] |
| Implementation | Impl notes | `.opencode/plugins/omt_net.ts` (OP_ARGS whitelist) | [x] |
| Testing | Test report | `tests/scripts/omt/test_omt_net_plugin_args.py` (6 cross-source pins; sentinel 1762) | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
