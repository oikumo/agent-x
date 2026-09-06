Petri net today advises while the enforcer blocks — agents can ship `src/` via `omt_phase→edit→pytest` without ever firing the net. This proposal makes the net (rev 51) the controlling/guarding layer for harness usage.

# Rules
1. Do not follow the omt methodology, focus on harness improvement proposal (meta_harness evolution/project loop stance — advisory for this run; `omt_think` still used if `src/` touched).
2. Use omt think everywhere omt feature to put knowledge in the source code itself
3. Create automated unit tests whenever is possible, use mocks
4. Try to use sub agents for parallel analysis whenever is possible and useful
5. Minimize future agent token consumption; no auto-execute past approval gate.

# Deep analysis (toolbox + 3 parallel sub-agents, 2026-09-05)

## 1. Current enforcement (who blocks?)
Enforcer order pinned (`.meta/META_HARNESS.omt:108 GATE`, driver `.opencode/lib/enforcer/gate_driver.ts:227-350`):
`g.nav:0 BLOCK` grep/glob on docs needs nav_used · `g.protect:10 BLOCK` .env hard / README+lock via scope:all · `g.receipt:20 BLOCK skip_ok=false` 2nd harness-surface edit needs fresh e2e · `g.tests:30 BLOCK` tests/ needs skip · `g.phase:40 BLOCK` src/ needs ledger phase + design-doc for major/new_screen · `g.think:50 BLOCK skip_ok=false` TA-files need think consult · `g.kb:55 BLOCK skip_ok=false` src/ needs kb_consulted · `g.mvc:60 AFTER` NEW BLOCK / SQL-god WARN · `g.tdd_after:70 AFTER` revert+advise. DENY→opencode.jsonc: git commit/push, bare python/pip/pytest, *.env read, toplevel webfetch.
Result: `src/` is gated by ledger/skip flags, NOT by net marking.

## 2. Current net power (what CAN it do? rev 51)
`scripts/omt/net/cli.py`: `probe` marking+enabled+[work_start]+advice · `fire` marking-only + stale-rev refuse · `splice add|remove|disable|undo|repair` + conformance 9-vector + 15-place cap · `sync proposal|net_to_md|md_to_net_propose --dry-run` · `synthesize --goal` template fragment · `mine` ledger→observed net + drift · `invariant` drift+resources+conflicts→harness.net.drift.jsonl.
Formal (`scripts/omt/net/analysis.py`, `state.py:57-97`): deadlocks(max 1000)+complete, bounds/bounded, 10 place-invariants exact rational, RESOURCE cap=1 (agent_attention/src_edit_capacity/tests_capacity/harness_surface_round/e2e_receipt) + resource_report live/capacity_ok/holders + conflicts[blocked_by], POOL (pending/active/done + work_start/complete), MAX_PLACES=15 hard, 3-file atomic save+rollback, sidecar↔overlay rev-mismatch refuse.
Live: `probe rev51 work_pending:3 active:0 done:4`, `invariant drift:false rev51==51 resources 5/5 ok conflicts:[]`, `bounded:true` + 1 deadlock vector (expected idle-end).
D16 doctrine (PROJECT.md:27): net owns STATE, gates own ENFORCEMENT — i.e. split by design.

## 3. Gap table (the core finding)
| Enforcer rule | Net backing? |
|---|---|
| g.nav/protect/receipt/tests/phase/think/kb/mvc/tdd_after, DENY, TDD hats, §12 artifacts | NONE — net has no edit hook |
| Net place/capacity | Enforcer backing? |
| agent_attention/src_edit/harness_round/e2e_receipt cap=1, work_* pool, conflicts[] | NONE — advisory only, fire optional, splice voluntary, sync dry-run, drift logged-not-blocking |
Slogan: **enforcer blocks, net advises (D4 proposal-only)**. `omt_net.ts` is proxy-only; no opencode.jsonc deny requires `fire(work_start)` before edit; WORK.md hand-edits not blocked (md→net propose only).

## 4. Bypass / incentive analysis
Logged: all omt_skip→ledger; phase/complete/tdd; .sandbox proposals+#Result. Silent/by-design: read+src-exempt nav bypass; docs/.projects/ edits need nothing; `.workflows #Rules:1=Do not follow` treats phase/kb as advisory; bash `uv-run python` multi-edit evades edit-hook (manual round discipline); cached TS plugin no hot-reload (GOTCHA_TS_NO_RELOAD, feat_046 session-whitelist bug class); `omt_q plan` dry-run never blocks; drift kb:515 + 11 unlinked-project-backed accumulates until queried.
Incentive: nav+kb+think+phase+complete+TDD+e2e per src/edit costs tokens vs one-line omt_skip; net consult (probe/graph/slider/52 snaps/rev-stamp) heavy with zero src-block → agents rationally skip net → debt.

## 5. What "proper" would mean
Net as SSOT for permission-to-act: no src/tests/harness edit without enabled-transition + successful fire + fresh revision; no close without work_complete fire; drift/conflict = block, not log; every synthesize/mine/sync proposal carries splice-obligation or explicit debt-accept with expiry; dashboard + WORK.md render become read-projections of net, not hand-edited sources.

# Proposal alternatives (pick ONE at approval gate)

## Alt A — Net-as-Gate (hard, recommended for control)
Enforcer pre-tool hook queries net: `probe` must show transition enabled + `fire --expected-revision HEAD` must succeed before `edit/write` to src/tests/harness-surface; `invariant conflicts!=[] or drifted` → BLOCK; `splice/sync` conformance-fail → BLOCK; WORK.md Tasks block writable only via `omt_net sync net_to_md`. Add `g.net:35 BLOCK skip_ok=false` (between tests and phase) + `DENY fire-bypass`. Stale-rev check on ALL ops. Tests: enforcer+net e2e ×N, stale-rev, drift-block, receipt-round interaction. Cost: new failure modes (net down = all blocked → need fail-closed vs fail-open policy + break-glass `omt_skip{scope:all}` with expiry + audit), token +1 tool call per edit, TS hot-reload fix required. Power: FULL — net truly controls.

## Alt B — Net-as-Guide + obligations (soft, recommended for adoption)
Keep enforcer as blocker; add consult-obligations: `omt_kb_nav`-style `net_consulted` session flag required for src/ (probe or invariant within window, like nav_used); `synthesize/mine/sync propose` creates splice-obligation ledger entry that must be spliced or debt-accepted with expiry before `omt_complete→Done`; `sync_md` render becomes canonical check in `harnessc check` (WORK.md drift = error, not silent); dashboard link in STARTUP menu. No fire-required. Cost: low, no availability risk, ~2 files + enforcer flag + harnessc rule. Power: MEDIUM — net guides, debt visible, still bypassable via skip (logged).

## Alt C — Hybrid phased (balanced, recommended overall)
Phase 1 now = Alt B (guide + obligations + WORK.md check + dashboard). Phase 2 after 2-week dogfood + TS-reload fix = Alt A gate on `work_start/work_complete` + resource places only (minimal blast radius), then expand to full splice/drift block. Links to `feature_001.session_user_objectives_driven_by_Petri_Net` (user tasks get net fragments via synthesize) so harness-control and task-execution converge. Cost: phased review points, needs project home (project.py new) + CURRENT_STATE tracking. Power: grows MEDIUM→FULL, lowest regret.

## Alt D — Do nothing (baseline)
Keep D4 proposal-only + advisory dashboard. Cost zero. Power stays as-is: correct formal net, zero control.

# Strategy (post-approval)
1. User picks A/B/C/D (this run stops here per §4.3).
2. If C (expected): `uv run scripts/omt/project.py new "net_enforced_harness"` → PROJECT.md + CURRENT_STATE.md → `new_feature.py` per phase → implement → e2e receipts → `omt_complete`.
3. Record outcome in `# Result` below + close or resume.

# Result
Selected 2026-09-05: **Alt A Net-as-Gate**. Project home `.projects/meta/net_enforced_harness/` (draft) created. Next: approve implementation plan below, then spawn `major_feature` + design doc + TDD.
