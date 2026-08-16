# Thoughts — reflection on the meta_harness_3 idea

> Companion reflection to `PROJECT.md` (canonical plan) and `CURRENT_STATE.md` (session log).
> This file is deliberately subjective: my honest reaction to the idea after a deep,
> code-grounded review of the three P1 "core problems." Not a spec, not a decision —
> a thinking document.

---

## The idea, in one line

**Feature-scoped gating beats repo-scoped gating** — a feature's lifecycle should gate
on the feature's own content + hygiene, not on the union of all prior features' drift.

I think this is right. After tracing the actual code, I think it is *more* right than
the project document itself claims — and the reasons are more interesting.

---

## What the deep review changed for me

I did not start out trusting the evaluation. It is a post-mortem written by the agent
that ran the session — written from inside the loop it critiques. That is a bias
problem: the friction it reports is real, but the *priorities* it assigns (which items
are P1 vs P3) are one agent's pain ranking.

So I verified the anchors myself. The line numbers hold. Then I kept tracing, and the
tracing changed the picture:

### 1. The §3.1 "phase reset" is not a reset — it's a visibility bug

The evaluation says `omt_phase` "resets the in-flight TDD cycle." It does not. It just
appends a phase record to the ledger. What actually happens: the whole read layer keys
on `session`, and a new session's phase record switches the read path from
window-mode to session-mode, shadowing the prior session's TDD records.

The telling detail: **the harness's own interrogative layer (`omt_q`) already does this
correctly.** `omt_q{op:state}` derives `tdd_position` feature-scoped, across sessions,
and it works. So in the failing scenario, the agent could ask `omt_q state` and get
"red/green in flight, 5 stranded nodes" while the *gate* simultaneously said "testlist,
nothing editable." Two contradictory readings of the same ledger. That is the
disorientation, precisely.

Which means P1-1 is not "add a preserve branch to `omt_phase`" — it is *align the gate
path with the feature-scoped derivation the rest of the system already uses.* The
substrate exists. This is a consistency fix, not a feature. That feels much better to
build, and it is much easier to verify (the golden is "the gate answers what omt_q
answers").

### 2. The coverage-on-diff fix has a hole the doc doesn't see

The PROJECT.md says "promote `diff_snapshots` to validate-exit." I traced it:
`snapshot_source` *overwrites* the per-file snapshot on every edit, and there is no
pre-feature baseline anywhere. The diff mechanism works in the GREEN hat only because
it compares the immediately-prior edit. At phase exit, "diff-scoped coverage" would
compute *the last edit's* new methods and silently drop the middle of the feature's
work — worse than today's over-broad full-file scan.

The real deliverable needs a feature-start baseline snapshot. That is new substrate the
project definition doesn't mention. This is the biggest gap I found.

### 3. Two definitions of "stranded" disagree

`omt_q`'s `stranded_red` and `gates.py`'s dangling-red are the same concept with
different membership rules (one counts unverified reds, the other doesn't). Before
`op:sync` can exist, these must be unified — otherwise sync closes a different set than
the interrogative layer reports.

### 4. The `scope:tests` option would weaken a protection

The PROJECT.md offers two fixes for the skip-scope problem; one of them (honoring
`scope:tests` for the coverage gate) widens the escape hatch for a gate whose failure
mode is "code is untested," not "tests are broken." The project's own D5 says no
protection regression. The message-clarity option is the honest one.

---

## The meta-finding

The 12-item table presents P1/P2/P3 as independent fixes. The deep trace says
otherwise: **four of the items (phase reset, coverage-on-diff, sync, skip-scope) all
root in the same session-vs-feature read-axis conflation.** Phase-A is not "three
independent P1 fixes." It is one architectural change (feature-scoped, temporal read
axis) plus one new mechanism (feature-start baseline) plus one done-checklist re-scope.

That is a reframe, not a criticism of the thesis. The thesis survives contact with the
code — it gets *stronger*, because the correct pattern already exists in the codebase
and the work is alignment.

---

## What I'm genuinely unsure about

- **The repo-hygiene note has no owner.** P1-2 removes the full-suite *block* and keeps
  the full-suite *signal* as a note. But nothing reads that note. Prior drift can
  accumulate silently. I keep coming back to this — it is the one place where the
  "protections stay byte-identical" claim is doing quiet work it doesn't deserve.
- **The coverage check matches by bare method name**, not per-class. A test calling
  `.show_chat` on anything covers `MainController.show_chat`. Diff-scoping fixes scope,
  not identity. This is a latent correctness issue the project doesn't mention at all.
- **The evaluation's priorities are one agent's pain ranking.** The three P1 items are
  load-bearing and I agree with them. The P2/P3 ordering I'd treat as negotiable — cheap
  enough to reorder if Phase-A reveals a different dominant friction.
- **12 items across 3 phases in one feature_028 is a lot.** A multi-week monolithic
  feature is the drift-accumulation mode this project exists to fix. Shipping Phase-A
  alone as feature_028 would already be a clean, shippable unit.

---

## Bottom line (what I'd want to see)

The idea is right and the ground is solid. Before Phase-A I'd want the project
definition corrected in four places:

1. P1-1 reframed as read-axis alignment (the omt_q pattern is the spec).
2. P1-3 given an explicit feature-start baseline mechanism.
3. P2-4 given a single unified stranded-red derivation + re-verify-before-promote.
4. P2-7 narrowed to the message-clarity option.

And I'd want Phase-A sized as one feature, not three-plus. The rest is build order.

---

*Written 2026-08-16, after the deep code review. Companion to PROJECT.md v1.0 and the
session evaluation `.sandbox/session_2026-08-15_feature_027_completion.md`.*

---

## Follow-up pass — independent review (second pair of eyes, before Phase-A)

A second reviewer re-verified the anchors independently and pushed on the edges the
first pass left open. Nothing here overturns the thesis; where the two passes overlap
(baseline substrate, skip-scope narrowing, one-feature sizing) it is confirmation, not
repetition.

### The anchors hold — verified, not trusted

I re-checked every cited line against the working tree before writing this:

- `state.py:157-169` (session shadowing → `testlist`) — real; the §3.1 diagnosis is accurate.
- `cli.py:233-262` (`cmd_done` full-suite gate + allowlist as the only net) — real.
- `gates.py:185-197` (full-file coverage scan) + `gates.py:129-131` (`diff_snapshots`
  already used in the GREEN hat) — real; the "promote the same mechanism" story is honest.
- `gates.py:166-171` (`skip_override` honors only `scope:"all"`) + `phase_gate.ts:307`
  (generic "call omt_skip") — real; the hidden contract is confirmed.

### Where I'd push harder (new findings, not in the first pass)

1. **P1-2 wants a baseline-diff, not just a note.** The "repo-hygiene note has no owner"
   doubt gets a concrete mechanism: record suite failures at feature start (or read the
   last `complete` record from the ledger) and block `done` only on failures NOT in that
   baseline. That keeps "done is cheap" while still catching *this feature broke someone
   else's tests* — a different failure class from pre-existing drift, and the hand-maintained
   allowlist alone cannot distinguish the two (the evaluation itself calls the allowlist a
   band-aid; the project keeps it as the only net).
2. **P1-1 needs a negative golden.** The fix must key on feature slug + the 8 h window —
   it must NOT relax session isolation. In-window + same feature + TDD records → preserve
   + warn; outside window → fresh. A golden pinning that boundary stops the fix from
   merging two concurrent agents' work on the same feature. The first pass's read-axis
   reframe is right; this is the boundary test that keeps it honest.
3. **P1-3's snapshot lifecycle has two holes the project doc doesn't name.** (a)
   `diff_snapshots` returns only methods ADDED since the last snapshot — a MODIFIED method
   keeps its `(class, method)` key and is invisible, so "added/modified" over-promises.
   (b) `snapshot_source` overwrites per-file snapshots on every edit and `cmd_done` DELETES
   them (`cli.py:274-289`) — so at validate-exit, "diff-scoped" can silently mean "last
   edit only," or fall back to a full-file scan when no snapshot exists. The no-snapshot
   fallback must be defined and pinned in a golden, not left to implementation judgment.
   (This extends the first pass's feature-start-baseline finding rather than repeating it.)
4. **P2-4 sync must re-verify before promoting.** Run the node's test (`run_pytest`)
   before RED→GREEN. A stranded node whose test now fails for a *different* reason (deleted
   file, changed assertion) must not auto-promote — this preserves the genuine-RED spirit
   (§2.6) the harness earned.

### Open decisions I'd put on the table

- **feature_028 task_type:** lean `major_feature` — the build is golden-test-first and
  TDD auto-on matches that shape; the design-doc artifact requirement is a natural home
  for the Phase-A design. `refactor` is lighter §12-wise. Either is defensible; it should
  be a decision, not a default.
- **A success metric:** log feature_028's own session costs (done retries, `omt_skip`
  calls, resume friction) vs feature_027's baseline (6 done-blocks, 1 `scope:all` skip).
  Makes "the tax is gone" measurable instead of vibes.
- **P3 deferral permission:** if Phase-C drags, an explicit carve-out to defer a P3 item
  to feature_029 is sequencing, not re-scoping — D1 survives.

### Bottom line of the second pass

The project definition is buildable as-is for Phase-A with three corrections: P1-2 gains
a baseline-diff row, P1-1 gains the window-boundary negative golden, P1-3 gains an
explicit no-snapshot fallback + a "modified methods" admission. The rest is build order.

---

*Second-pass entry, 2026-08-16, after independent anchor re-verification against the
working tree. Companion to the first-pass entry above, PROJECT.md v1.0, and the session
evaluation `.sandbox/session_2026-08-15_feature_027_completion.md`.*