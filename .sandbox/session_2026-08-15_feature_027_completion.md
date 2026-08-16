# Session Log — 2026-08-15 — feature_027.rag_v2 completion (resume → done)

> Purpose: an objective post-mortem of one session running the OMT++ meta harness end-to-end,
> to capture workflow evolution and feed concrete improvement signals back into the harness.
> Bias disclaimer: I am `gpt-5-codex` working in harness; this is written from inside the loop
> it critiques. I have tried to label friction that was genuinely the harness's fault vs. my own
> misuse of it. The headline question is: **what about this workflow compounds at scale (hundreds
> of features, many agents) and what is one-time cost?**
>
> Scope: a single major_feature (feature_027.rag_v2) resumed from "~80% GREEN, 6 failing tests"
> (per `.sandbox/pause_2026-08-15_l.md`), driven to `omt_tdd{op:done}` + `omt_complete{advance_to:Done}`
> in one session. Actual wall-clock: ~90 minutes; ~269 ledger records; 31/31 v2 tests green; 4
> collateral infra fixes shipped; Feature Health 100%.

---

## 1. Session shape (what actually happened)

1. **Start** — read `WORK.md` (15-line summary per STARTUP), loaded `.sandbox/pause_2026-08-15_l.md` (the iter-l resume anchor). The pause doc gave me:
   - the EXACT three fixes (TUIProvider stubs, lazy ConsoleProvider import, sys.modules poison) with file:line anchors,
   - the EXACT order to apply them (RED hat first for the test edit, then GREEN hat for src),
   - the exact 5 file-level node IDs and the node-granularity caveat,
   - the resume protocol as one paragraph.
   - **Cost saved:** zero rediscovery. The pause doc paid the "narrative is paid every session startup" (CONV_WORK_DONE) debt forward.
2. **Declared `omt_phase{phase:Programming}`** — this RESET the TDD state from "stranded-red across 5 nodes, GREEN at 2" to "TESTLIST, cycles:0" and blocked ALL edits with "planning hat" (see §3.1). The single most disorienting moment of the session.
3. **Re-cycled manually** — RED at `test_rag_v2_agent_service.py` (test fails → valid RED) → applied Fix 3 (test edit) → GREEN → unblocked src. Then GREEN still → applied Fix 1+2 (TUIProvider stubs + lazy import).
4. **5th failure was a test defect** — `test_show_rag_v2_calls_set_view_not_dot_view` sliced the `show_rag_v2` body by top-level `\ndef ` but MainController methods are 4-space-indented → over-captured into `show_models`'s legacy `models_controller.view = models_view` (matched the `.view = ` literal). Fixed the slice to `\n    def ` and reworded the TA: comment that also contained the literal.
5. **Stranded-red closure** — the other 3 nodes (`commands_and_views`, `gaps_closure_matrix`, `retrieval_tool`) were already passing; the engine refused RED ("already passes") so I declared GREEN directly at each to close them.
6. **REFACTOR** — 1 DRY tightening of `RagSearchResult` docstring; auto-revert guard verified tests stayed green.
7. **`omt_tdd{op:done}` blocked 6 times** on infra failures unrelated to feature_027's content (harnessc projections, kb pin drift, u13 date-drift). Fixed 4 collateral issues (see §3.6–3.9). Declared done.
8. **Testing phase** — wrote test_report.md + implementation_notes.md at the harness-canonical `.meta/software_development_process/<phase>/features/feature_XXX/` path (after first mis-creating them at repo root; see §3.10).
9. **Phase exit coverage gate** — required a `scope:all` skip to override prior-feature coverage gaps. (See §3.7 — the gate's skip-scope contract is hidden.)
10. **Done** — WORK.md flipped `[~]` → `[x]`; harnessc clean; Feature Health 100%.

---

## 2. What the harness did well (genuine protections that paid off)

| # | Protection | Where in session | Saved me from |
|---|------------|------------------|--------------|
| 2.1 | **Resume discipline (`WORK.md`→pause doc→`omt_q state`)** | Start | Re-reading 22 new src files + 4 existing-file edits to reconstruct where I was. The pause doc gave exact fixes; `omt_q{op:state}` confirmed `stranded_red` + `known_suite_failures` so I could distinguish my regressions from baseline. |
| 2.2 | **TDD node-granularity gotcha (nav-indexed)** | RED/GREEN declarations | Declaring red/green/refactor at the SAME test_node. I declared GREEN at the exact file-level node IDs the RED cycle used — `omt_tdd{op:done}` checked this. A classic "red at `f.py::C::t` + green at `f.py` strands latest=red" break did NOT happen because the gotcha is in `omt_nav` and I read it. |
| 2.3 | **g.think consult gate** | Before editing `main_controller.py` | Surfaced the TA: thought at line 136 — "show_rag_v2 wires the v2 controller via `set_view(view)` NOT `.view = view`". The set_view contract IS the Constraint-d I was pinning. I would have missed this without the consult. |
| 2.4 | **REFACTOR auto-revert guard** | After the `RagSearchResult` docstring tighten | If my refactor had broken the retrieval test, `cmd_after_edit` (gates.py:111) would have reverted via `refactorSnapshots`. Genuine safety — I did NOT break it, but the guard is the reason I could refactor without anxiety. |
| 2.5 | **`harnessc check` hygiene budget** | At `done` gate | Caught WORK.md at 6507 B > 5120 B budget and a stray untracked `sandbox/` dir outside `@var root_allowlist`. Both were real hygiene debt accumulating from prior sessions. This is enforceable hygiene that scales — a human reviewer wouldn't catch the byte budget. |
| 2.6 | **Genuine RED verification (`cmd_start`)** | When I tried `omt_tdd{op:red}` at already-passing nodes | The engine refused with "test already passes. Fix the test to fail, or remove this cycle." This PREVENTED me from declaring false RED on green tests and corrupting the cycle ledger. Protective, correct. |
| 2.7 | **`omt_q` interrogative layer** | Mid-session — `op:state` | Gave me the live `stranded_red`, `known_suite_failures` (so I could bench-separate react_screen/tdd_enforcement baseline from my regressions), `consult_needed` (auto-list of files needing KB consult). The "ask the harness" affordance worked as designed; this is the v1.3 thesis demonstrated live. |
| 2.8 | **Two-hats enforcement overall** | RED→GREEN→REFACTOR→done cycle | The test-hat/code-hat swap forced a 1-test:1-min-impl loop. I could NOT write src code while wearing the test hat — the gate threw `OmtBlock`. This excludes the entire class of "wrote tests AND src in one blind batch" failures. The friction (§3.3) is the cost; the value (this row) is the payoff. |

**Verdict on §2:** the harness's protections are NOT theoretical — at least 4 of them (2.1, 2.3, 2.5, 2.6) caught real mistakes or saved concrete rediscovery this session alone. The rest are lower-impact but compound across many sessions.

---

## 3. Friction encountered — with severity and verdict

I classify each friction event by **scale impact**: **COMPOUNDS** (hits every feature / every session-resume; cumulative), **FIXED** (one-time per developer; bounded), or **LOCAL** (this session only; my misuse).

### 3.1 `omt_phase` reset the in-flight TDD cycle — **COMPOUNDS** (harness)
- **What happened:** I called `omt_phase{phase:Programming, tdd:true, feature:"feature_027.rag_v2", task_type:"major_feature"}` at session start to unlock src. The phase declaration recorded, THEN `omt_status` showed "cycles: 0" and all edits blocked with "wearing the planning hat."
- **Root cause:** the phase ledger records a fresh `phase` entry, and the TDD state machine reset to `testlist` on the new phase-record (state.py treats a new phase decree as a cycle reset). This is correct for a *fresh* feature but WRONG for a *resume* — feature_027 was mid-GREEN (5 RED declared, 2 GREEN declared, 31/31 was on track).
- **Cost:** 3–4 confusing minutes + manual re-cycling at each of the 5 file-level nodes to "close" what was already closed. The stranded-red list then showed 5 nodes I had to re-close, even though the tests passed.
- **Verdict:** the phase declaration should be **idempotent on an in-flight feature**: if a green/refactor/closed cycle exists for the same `feature` slug within the unlock window, preserve the TDD state rather than reset to `testlist`. At minimum, `omt_phase` should warn "this will reset the in-flight TDD cycle — continue?" The current behavior is silent reset.
- **Scale impact:** hits EVERY resume of EVERY mid-flight feature. At scale this is a per-session-confusion tax that discourages multi-session major features.

### 3.2 `stranded_red` closure is manual busywork — **COMPOUNDS** (harness)
- **What happened:** nodes `commands_and_views`, `gaps_closure_matrix`, `retrieval_tool` were declared RED in a prior session and the src had passed since; the engine knew they passed but refused `red` ("already passes") AND didn't auto-close them. I had to `omt_tdd{op:green}` at each to close the cycle the engine saw as "stranded."
- **Root cause:** the engine has no op for "the test has started passing; auto-promote the stranded RED to GREEN." `omt_q{op:state}` surfaces stranded_red but no tool consumes it.
- **Suggested:** add `omt_tdd{op:sync}` (or have `cmd_green` auto-detect: if the prior cycle is `red`+`verified` and the test now passes, promote without requiring a fresh `red`→`green` dance). Galvanize the "RED that has since started passing" pattern.
- **Scale impact:** every multi-session TDD feature accrues stranded nodes if the prior session paused mid-red. Compounds with §3.1.

### 3.3 Two-hats error message is misleading under TESTLIST — **FIXED** (harness bug)
- **What happened:** after the §3.1 reset, edits were blocked with "wearing the planning hat. Only src/ edits allowed." But the actual state was `testlist`, under which NOTHING is editable (rules: `{src:False, tests:False}`). The message said "only src" when the truth was "nothing." I had to read `scripts/omt/tdd/gates.py:99-107` to find the `hat = {"testlist": "planning"}` mapping and realize that "planning hat" means both blocked.
- **Suggested:** when state is `testlist`, emit "testlist blocks both src/ and tests/ — declare `omt_tdd{op:red}` at a failing test to enter the test hat." The current "Only src/ edits allowed" phrasing is true for the `green` and `refactor` hats but FALSE for `testlist`/`done`; the ternary on line 101 only flips the noun but the verb "Only X allowed" is wrong when both are blocked.
- **Scale impact:** FIXED — one wording fix in `gates.py:101`. Cheap.

### 3.4 KB consult gate (g.kb) fired mid-GREEN on a file I had just read — **LOCAL** (harness, my omission)
- **What happened:** applying Fix 1 (TUIProvider stubs) + Fix 2 (lazy import), the KB gate blocked: "run `omt_kb_nav` before editing src." I had read both files in the same turn just above. I ran `omt_kb_nav` for the three symbols, confirmed the contracts (TUIProvider/ConsoleProvider/MainController, all `IUIProvider` realizations), reapplied — succeeded.
- **Verdict:** the gate is protective for blind edits but redundant when I read the file in the same turn. The harness has no "recent read of this file in this session" exemption (cf. g.think consult dedup U13 — `recent_consults` has an 8h window, but the KB gate doesn't consult it). Cross-feature: `omt_kb_nav` itself is great; the issue is the GATE re-firing without checking consultation recency.
- **Suggested:** g.kb should accept a recent-read exemption: if the file was Read in the current session (or within N minutes), consider the consult satisfied. The `recent_consults` substrate already exists for g.think; mirror it.
- **Scale impact:** LOCAL — I could have declared `omt_kb_nav` proactively before reading. But at scale, mid-session round-trips compound; the gate + the consult-recency substrate should be unified.

### 3.5 Harness e2e receipt round-robin blocked mid-fix — **LOCAL** (harness, correct hygiene)
- **What happened:** editing `tests/scripts/omt/test_omt_q.py` a second time tripped "part of the META HARNESS surface and already has unverified changes — run the harness e2e before editing again." I ran `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`, refreshed the receipt (`omt_harness_e2e_last_run.json`), reapplied.
- **Verdict:** the guard is CORRECT (per-file second-edit on harness surface needs a fresh e2e — prevents drift). But it fires mid-logical-fix and breaks my train. Could the harness AUTO-trigger the receipt refresh when the gate trips, then proceed (rather than block-then-rerun)?
- **Scale impact:** LOCAL — affects only harness-surface edits (`scripts/omt/`, `.opencode/`, `.meta/*.omt`). Low frequency but noticeable.

### 3.6 `done` checklist gates on FULL suite pass, not FEATURE suite — **COMPOUNDS** (harness design)
- **What happened:** `omt_tdd{op:done}` blocked 6 times on infra failures UNRELATED to feature_027's content: `harnessc` projection drift + `test_kb_compiler_build_runs_clean` count drift + `test_u13_op_state_consult_dedup` date-drift. Two were genuinely pre-existing (feature_025/026 touched test files), one was feature_027's collateral (kb counts bumped because I added src).
- **Root cause:** `cmd_validate_exit` (gates.py:156) checks `suite_passes=true` which runs the FULL pytest suite. A feature's done-gate then entangles with the union of all prior features' drift.
- **Verdict:** at scale, this is the single worst design smell in the session: every feature's done-blocks-on-all-prior-drift. A new feature ship becomes a worldwide-drift triage session. The natural gate is "feature's own test files pass + repo hygiene check passes" — SEPARATE concerns, not coupled.
- **Suggested:** split `suite_passes` into `feature_suite_passes` (the feature's test dir only) + `repo_hygiene_passes` (`harnessc check` + known-suite-failures allowlist). A feature is `done` when its own content is green and hygiene is clean — NOT when every prior feature's tests still pass (prior drift is a separate, repo-level triage task).
- **Scale impact:** COMPOUNDS — dominantly. At 50+ features, this gate makes features essentially blockable by any random test anywhere in the suite. The `known_suite_failures` allowlist is a band-aid that requires hand-maintenance every time a baseline shifts.

### 3.7 Phase-exit coverage gate requires `scope:all` (not `scope:tests`) — **COMPOUNDS** (hidden contract)
- **What happened:** validate-exit reported coverage gaps across 3 files (interfaces.py, providers.py, main_controller.py) — counting pre-existing feature_024 untested methods AND v2 view-plumbing methods exercised indirectly. The gate's error said "call `omt_skip{reason:...}` to override." I called `omt_skip{scope:"tests"}` (logged, correct per my semantic intent: I'm overriding a test coverage gate). The phase exit STILL blocked — the gate only honors `scope:"all"` (gates.py:166-171).
- **Root cause:** the skip-scope vocabulary is misaligned with the override's natural scope. `scope:all` is the "heavy override" (unlocks everything hard — src/tests/nav, even README/LICENSE permissiveness); `scope:tests` is "test-only override." A coverage gap override is naturally a `tests` concept but the gate keys on `all`.
- **Suggested:** gates.py:168 should accept `scope:tests` for coverage-gate overrides (keep `scope:all` for dangling-reds and broader overrides). OR rename the override contract so the gate's error message says "call `omt_skip{scope:'all', reason:...}`" explicitly.
- **Scale impact:** COMPOUNDS — every feature whose edits collide with a prior feature's untested surface hits this. Required me to read the gate source to discover the scope requirement. Hidden contract.

### 3.8 Coverage gate re-opens prior finalized features' test surface — **COMPOUNDS** (design)
- **What happened:** the coverage gate listed pre-existing feature_024 methods as "uncovered": `IMainView.print_message`, `IUIProvider.create_main_view`, `ConsoleProvider.create_chat_view`, `MainController.show_chat`, etc. These were NEVER covered (feature_024 shipped via bug_fix phase; its TA: thoughts record the virtual-subclass gaps). Feature_027 additively edited those files but did NOT change those methods.
- **Root cause:** `cmd_validate_exit` scans ALL public methods of files in the feature's `target_src` set, irrespective of which feature originally owned them. A feature that additively edits a file inherits ALL of that file's coverage debt.
- **Suggested:** scope the coverage check to methods ADDED or MODIFIED by THIS feature's diff (the `diff_snapshots` mechanism at gates.py:130 already exists for the per-edit `green` hat; promote it to validate-exit). Don't gate feature_027's Testing exit on feature_024's finalized-but-untested surface.
- **Scale impact:** COMPOUNDS — entangled with §3.6. Together they make additive edits to a file-with-prior-debt a trap.

### 3.9 KB compiler count pins = anti-scale (forced re-pin tax) — **COMPOUNDS** (harness test design)
- **What happened:** `test_kb_compiler_build_runs_clean` pinned exact AST counts (`class=240/contract=32/dep=105`). feature_025 added 2 classes (forced a re-pin, per a comment in the test itself). feature_027 added 55 records (classes + ABC pairs + deps). Each feature ship owes a mechanical kb re-pin tax.
- **Verdict:** the user explicitly flagged this ("it does not make sense"). Volatile AST-scraped counts drift on every feature that adds src; pinning exact counts turns every ship into a re-pin with zero contract value. The corrective pattern (which I applied): pin the STRUCTURE (build exits 0 + all expected record KINDS present + index/IR artifacts written), not the counts. Well-formedness is separately pinned in `test_kb_index_jsonl_well_formed_and_comprehensive`.
- **Suggested:** bake the structural-pin pattern as a harness convention — document "magic-number pins on AST-scraped counts are smell; pin kinds + presence + artifact files. Regression tests for compilers output streams should assert the contract, not volatile counts." Put this in `omt_nav{query:"GOTCHA_"}` (the recurring-gotchas index) so future test authors see it.
- **Scale impact:** COMPOUNDS — was already compounding (feature_025 paid it once, feature_027 would have paid it again). The pattern is scale-breaking; fixing it once + documenting removes the tax.

### 3.10 Temporal-window test pins an absolute date — **COMPOUNDS** (harness test design)
- **What happened:** `test_u13_op_state_consult_dedup` hardcoded `fresh_ts = "2026-08-09T18:00:00Z"` with a comment "today is 2026-08-09". Today is 2026-08-15; the consult went stale past the 8h UNLOCK_WINDOW_MS → `recent_consults=[]` → false-fail.
- **Root cause:** a test that asserts a temporal-window contract (consult within 8h) CANNOT pin an absolute timestamp + a hardcoded "today." Any test using a window-vs-now contract must compute now or use a frozen clock.
- **Suggested:** add a lint rule (or a `omt_nav` gotcha entry) flagging any `ts = "20\d\d-\d\d-\d\dT"` literal in a test file as a candidate for date-drift. The dynamic `now - timedelta` is the pattern; advertise it.
- **Scale impact:** COMPOUNDS — silent time-bombs. This one took 6 days to fire; the next one could take 30. The harness should catch this class before it fires.

### 3.11 Artifact path confusion (`.meta/software_development_process/<phase>/...` vs repo root) — **FIXED** (ONE-TIME)
- **What happened:** I created `6.testing/features/feature_027.rag_v2/test_report.md` and `5.implementation/...` at the REPO ROOT, then had to move them to `.meta/software_development_process/<phase>/features/feature_027.rag_v2/`. The §12 matrix in `META.md` says "6.testing/features/feature_XXX/test_report.md" without making the repo-root vs .meta-root split explicit; I resolved it by `ls`-ing sibling dirs.
- **Suggested:** provide a scaffold command for each phase artifact (`uv run scripts/omt/new_feature.py testing --feature feature_027.rag_v2` creates the correct path + a stub). Eliminates the one-time confusion for every new developer.
- **Scale impact:** FIXED — one-time per developer (and per feature-type per developer). Low; but multiplying by the number of developers who touch the harness, the scaffold would prevent repeated first-time errors.

### 3.12 LSP errors reported on every edit flood the signal with pre-existing noise — **FIXED** (filter)
- **What happened:** every edit to `main_controller.py` or `tui/provider.py` re-reported the same 4-9 pre-existing LSP errors (AgentController→IConsoleAgentViewPartner unassignable, `models_controller.view` unknown attr, tui adapter imports unresolved, `langchain.tools` unresolved stub). None were from my edits; all were feature_024 virtual-subclass / runtime-lazy-import issues known-but-unfixed (TA: thoughts record them).
- **Cost:** I had to mentally filter every LSP report to distinguish "new error from my edit" (rare) from "the usual background noise" (frequent). The post-edit report bundled them, drowning real signal.
- **Suggested:** maintain an allowlist of known LSP errors (file:line:message) — the obverse of `known_suite_failures`. Suppress the allowlisted ones in the post-edit report; surface only NEW errors.
- **Scale impact:** FIXED — one-time investment to publish the allowlist; permanent signal-de-noising after.

---

## 4. Workflow evolution — patterns that emerged this session

### 4.1 The "collateral-re-pin as feature responsibility" question
feature_027 added src that bumped kb counts. Was re-pinning the count assertion feature_027's job? My take after fixing it: **NO** — the pin was the anti-pattern, not the drift. The drift is correct behavior (src was added; counts went up). The corrective is to remove the volatile-pin pattern, not to tax every ship. The user's reaction ("it does not make sense") agrees. **Harness implication:** a feature's responsibility should be "don't break the contract," not "re-pin the volatile magic numbers." The harness should make structural pins the default recommendation, and flag volatile counts as a test-smell at authorship time (a `tdd_check` lint).

### 4.2 The green-after-passing auto-promote gap
Section 3.2 surfaced a real gap: the engine recognizes RED, GREEN, REFACTOR, DONE as discrete states but has no transitive "the test started passing → auto-promote stranded RED to GREEN." This is the ONLY manual busywork step in an otherwise mechanical cycle. **Harness implication:** add `op:sync` (or promote in-place on detected pass).

### 4.3 The phase-declaration-vs-cycle-preservation tension
Section 3.1 is the deepest issue: `omt_phase` is the right tool to (re-)unlock src at session resume, but it resets the in-flight TDD state as a side effect. The harness conflates "declare phase" with "start a fresh TDD cycle." These should be separable. **Harness implication:** `omt_phase` on an in-flight feature should be a no-op on TDD state (or a guarded confirm). The phase ledger is for decree/provenance, not for resetting the cycle.

### 4.4 "Done" as feature-scoped vs repo-scoped
Sections 3.6 and 3.8 together: `done` should mean "this feature's content is green + hygiene is clean," NOT "the whole repo's tests still pass." Coupling them makes the harness brittle to prior drift. **Harness implication:** split `suite_passes` into `feature_suite_passes` + `repo_hygiene_passes`; gate feature-done on the former, gate repo-hygiene on a SEPARATE concern (e.g. a new `omt_q{op:hygiene}` fold, or a pre-merge check, not the per-feature lifecycle gate).

### 4.5 The skip-scope vocabulary
Section 3.7: `scope:src` / `scope:tests` / `scope:nav` / `scope:all` is the vocabulary, but the coverage-gate override keys specifically on `all`, not on the natural `tests`. My correct-by-intent `scope:tests` skip did not satisfy it. **Harness implication:** align each gate's override with the gate's natural scope (coverage-gate → `scope:tests`), or document the override-contract in the gate's error message (emit "call `omt_skip{scope:'all'...}`" if that's what's required, instead of the generic "call `omt_skip`").

### 4.6 The recurring-gotcha index is doing real work
`omt_nav{query:"GOTCHA_"}` surfaced the TDD node-granularity rule at the right moment. I did NOT strand a GREEN at the wrong node ID because the gotcha was nav-indexed and I read it pre-edit. **Harness implication:** keep investing in the gotcha index — it's one of the highest-leverage surfaces (zero-cost prevention vs. expensive recovery). Add the §3.9 volatile-pin and §3.10 absolute-date gotchas to it.

### 4.7 The omt_q interrogative layer earned its keep
I used `omt_q{op:state}` twice with real intent: once to confirm stranded_red (so I knew what to close), once to separate my regressions from `known_suite_failures` baseline. This is the v1.3 thesis demonstrated live — a feature_026 ship paying off in a feature_027 session. **Harness implication:** omt_q is a positive example of a ship that compounds (retroactive value across sessions); treat it as the model for future interrogative surfaces.

---

## 5. Suggested harness improvements — prioritized by scale × cost

| # | Improvement | Addresses | Cost | Scale benefit |
|---|-------------|-----------|------|---------------|
| P1 | Make `omt_phase` idempotent on in-flight features (preserve TDD state; warn before reset) | §3.1, §4.3 | low (state.py branch on existing feature-slug) | COMPOUNDS — every resume of every mid-flight major feature |
| P1 | Split `suite_passes` into `feature_suite_passes` + `repo_hygiene_passes`; gate feature-done on the former only | §3.6, §4.4 | medium (gates.py + cli.py) | COMPOUNDS — the single worst design smell at scale |
| P1 | Scope coverage-gate (validate-exit) to methods added/modified by THIS feature's diff (use `diff_snapshots`) | §3.8 | medium (gates.py + ast_checks) | COMPOUNDS — entangled with §3.6 |
| P2 | Add `omt_tdd{op:sync}` or auto-promote on detected pass (RED+verified + now-passing → GREEN) | §3.2, §4.2 | low (gates.py) | COMPOUNDS — busywork every multi-session feature |
| P2 | Bake the structural-pin-not-count-pin convention; add to recurring gotchas (nav) | §3.9, §4.6 | low (docs) | COMPOUNDS — re-pin tax every feature |
| P2 | Lint for absolute-date literals in temporal-window tests; add to recurring gotchas | §3.10 | low (one regex lint) | COMPOUNDS — silent time-bombs |
| P2 | Align skip-scope with override-natural scope (coverage-gate → `scope:tests`); OR make the error message name the required scope explicitly | §3.7, §4.5 | low (gates.py:168 + msg) | COMPOUNDS — hidden contract |
| P3 | Fix two-hats error message for `testlist`/`done` states (say "nothing editable," not "only src") | §3.3 | trivial (gates.py:101) | FIXED |
| P3 | g.kb consult gate accepts a recent-read exemption (mirror `recent_consults`) | §3.4 | medium (gate_driver + consult substrate) | LOCAL but compounds across mid-session round-trips |
| P3 | Scaffold commands for phase artifacts (`new_feature.py testing/implementation`) | §3.11 | low (one script per phase) | FIXED — one-time per developer |
| P3 | Allowlist of known LSP errors; suppressed in post-edit reports | §3.12 | medium (collect + filter) | FIXED — permanent signal-de-noise |
| P3 | Auto-trigger harness-e2e receipt refresh when the receipt-guard trips | §3.5 | low (enforcer hook) | LOCAL |

**Headline:** the three P1 items are the workflow-evolution signal — they all share a common shape: **feature-scoped gating beats repo-scoped gating**. The phase lifecycle should gate on the FEATURE's content + hygiene, not on the union of all prior features' drift. That principle applied to phase declaration (3.1), done-checklist (3.6), and coverage-gate (3.8) would remove the bulk of session friction and make the harness scale to many features / many agents cleanly.

---

## 6. One-paragraph verdict

The OMT++ meta harness's protective layers earned their keep in this session — at least four caught real mistakes (think-gate surfaced the set_view contract; `harnessc` caught WORK.md bloat; `cmd_start` refused false-RED; node-granularity prevented cycle breakage). The pause-doc + `omt_q state` resume discipline gave zero-rediscovery continuity across the iter-l pause. The dominant friction is **entanglement**: `omt_phase` resets in-flight cycles, `done` gates on the full suite, and the coverage gate re-opens prior features' untested surface — three design choices that all share the shape "feature-scoped action gated by repo-scoped state." At big scale (hundreds of features, many agents) these three compound into a per-session tax that discourages multi-session major features and makes any new ship blockable by any random prior drift. The single most leveraged fix is to make feature lifecycle gates feature-scoped: `feature_suite_passes` and coverage-on-diff rather than `suite_passes` and coverage-on-full-file. The structural patterns the harness already has (gotchas-in-nav, `omt_q` interrogative layer, REFACTOR auto-revert, two-hats 1-test:1-impl loop) demonstrate that the protective infrastructure is mature; the lifecycle-gate scoping is the next refactor.
