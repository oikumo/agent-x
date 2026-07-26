# Meta Harness Refactor — Plan

> **Status:** PROPOSED — awaiting execution approval (deep-checked FOUR times 2026-07-25, see §0 audit incl. round-2 §0.4 + round-3 §0.5 + round-4 §0.6)
> **Date:** 2026-07-25 (revised same day after deep-check audit; round-2 adds F14–F22 + new R6 think-anywhere simplification workstream; round-3 adds F24–F31, R6 extensions S1b/S6/S7, new R7 token-optimization workstream + Appendix C; round-4 adds F32–F36, R7 T7/T8, new R8 machine-native harness-language workstream + Appendix D)
> **Baseline commit anchor:** `a7163df` (`[WIP] Refactor META HARNESS`, current HEAD — supersedes original anchor `d497dce`; see §0.1)
> **Task type:** `refactor` (per RULE_RIGOR: phase declaration only, no design doc required)

---

## 0. Deep-Check Audit (2026-07-25)

Every load-bearing claim in the original plan was verified against the live repo. Verdicts:

### 0.1 Tree state (STALE assumption in original plan — CORRECTED)

- Original plan assumed "30 uncommitted paths … do NOT commit; refactor proceeds on top of this tree state".
- **Reality:** those paths were committed as `a7163df [WIP] Refactor META HARNESS` (2026-07-25 18:38, 31 files, +918/−5041). `git status --porcelain` is **empty** — tree is CLEAN.
- **Consequence:** baseline anchor moves `d497dce` → `a7163df`. §5 risk "Mixing with 30 uncommitted paths" is obsolete. WORK.md scratchpad line "Uncommitted (per directive) … Commit on explicit user request only" is now stale history.
- **ROUND-2 UPDATE (F15):** tree is dirty again — see §0.4 F15 (probe-marker duplication in `omt_status.ts`, uncommitted). Baseline anchor `a7163df` still correct.

### 0.2 Verified ACCURATE claims (no change needed)

| Claim | Evidence |
|---|---|
| enforcer 1184 / think 819 / status 368 / nav 276 / tdd_check 825 / mvc+new_feature 366 lines | `wc -l` exact match |
| tdd_check.py = 9 subcommands | testlist, start, green, refactor, done, gate, after-edit, status, validate-exit |
| ledger.jsonl ~108 KB, unbounded | 109,181 B, no rotation logic found anywhere |
| tests/scripts/omt/ = 6 files, 68 static + 17 live | `pytest tests/scripts/omt -m "not opencode_live"` → **68 passed, 17 deselected (1.34s)** |
| P5: process-lifetime session Maps in enforcer | 3 confirmed in `OmtEnforcer` closure: `sessionNavState` :328, `injectedThisSession` :333, F14c nav-reminder Map ~:340 (the :283 `latest` Map is function-local inside `staleLinesFor` — NOT session state) |
| omt_done strict full-suite | `cmd_done` (tdd_check.py:571) → `run_full_suite` :385 (full `pytest -q`, timeout=120, no allowlist) |
| 8h window shared enforcer ↔ tdd_check | `UNLOCK_WINDOW_MS` enforcer:48, tdd_check.py:41 |
| TA: pins at enforcer:1070, omt_think.ts:819 | both confirmed on disk, both files think-gated |
| Baseline d497dce exists | but superseded (§0.1) |

### 0.3 Corrected / NEW findings (plan updated to absorb them)

- **F1 — P1 duplication evidence was wrong for the enforcer.** Grep for `REPO_ROOT|LEDGER_PATH|isProtectedPath|PROTECTED_FILES` in enforcer = **0 hits**. The enforcer uses the hook's `directory` param, not `process.cwd()`. The accurate duplication map is in §2 P1 (rewritten).
- **F2 — `process.cwd()` vs `directory` divergence (latent bug, NEW).** nav:10 / status:10 / think:28 resolve repo paths from `process.cwd()`; enforcer uses SDK `directory`. If opencode is launched from a subdirectory, the three tool-plugins resolve `.meta/…` against the wrong root while the enforcer gates against the right one. R1's shared lib must standardize on `directory` (injected at plugin-init), not `process.cwd()`.
- **F3 — R0's META_HARNESS.md fix list was incomplete.** Singular `.opencode/plugin/` occurs on **10 lines**, not 9: 44, 45, 46, 47, 99, **108 (`THINK_TOOLS:` — was missing from the list)**, 201, 202, 203, 204.
- **F4 — AGENTS.md drift missed entirely.** AGENTS.md:7 (ENF line) says `.opencode/plugin/omt_enforcer.ts` (singular). Added to R0.
- **F5 — feature_016 test file carries the same singular-path bug (4 tests failing NOW).** `tests/features/feature_016.tdd_enforcement/test_tdd_enforcement.py` lines 97/105/112/116 read `.opencode/plugin/…`. Verified: all asserted strings exist in current sources (5/12/1/3 grep hits) → path fix alone turns them green. **This is a live P2 instance the plan missed** — added to R0 (tests/ edit → canary protocol applies, see §4).
- **F6 — P3's omt_done blocker list was incomplete.** Full static suite TODAY (`-m "not opencode_live"`): **7 failed, 973 passed (40s)** = 3 × feature_018 react_screen (known) + **4 × feature_016 path drift (F5)**. The "2 tdd_check ledger-window tests" currently PASS (no TDD session in-window) — they are *window-flaky*, not *broken*. After R0 fixes F5, remaining static blockers: 3 react_screen + 2 window-flaky.
- **F7 — NEW omt_done blocker: the 120 s timeout.** `run_full_suite(timeout=120)` runs the WHOLE suite including `opencode_live` tests when the binary is present — and the binary IS present (`opencode 1.18.5`). Full suite with live tests exceeded **180 s** in audit (timed out). Even with zero failures, `omt_done` returns −1 "pytest timed out". R4 must add: `-m "not opencode_live"` in `run_full_suite` (or a parameterized timeout). This is a more deterministic blocker than the allowlist.
- **F8 — opencode version drift: docs say 1.18.3, binary is 1.18.5.** The F14c workaround + multiple doc/comment claims rest on a 1.18.3 binary audit ("never dispatches session.start"). Live suite was last run GREEN on 1.18.3 (2026-07-20). R0 must re-baseline: run the 17 live tests on 1.18.5 before touching anything, and annotate version-pinned claims as "audited on 1.18.3, re-verified on 1.18.5" (or re-audit).
- **F9 — e2e receipt `covered_files` omits `omt_nav.ts` (coverage gap).** Enforcer `isOmtHarness` (:496–503) guards `.opencode/plugins/omt_` **prefix** → nav IS receipt-guarded, but the e2e test's covered_files/sha256 list (10 files) omits it (also omits `.meta/templates/`, feature_006 dir — both in isOmtHarness). Impact is doc-level only (enforcer uses passed_at + mtime + git-dirty, never the hashes), but R0/R2 should align the list with `isOmtHarness`.
- **F10 — THOUGHT_PATTERN sync contract is now unenforced.** omt_think.ts:31 says "keep in sync with omt_enforcer.ts (byte-identical; **structural test asserts**)" — that structural test was DELETED in `a7163df` (grep `THOUGHT_PATTERN` over tests/ = 0 hits). The byte-identical pair (enforcer:254 ↔ think:38) currently drifts unprotected. Interim: add a cheap source-pin test in R0; R1 eliminates the duplication for real.
- **F11 — Committed junk at repo root (digest pollution).** `test_think_gate.py` (2 lines: `x=1` + `# TA: test123`) and `test_think_gate_probe2.py` (2 lines + `# TA: gotcha: …test thought`) are live-test probe leftovers, committed in `a7163df`, both think-gated, both polluting every session digest. Also `omt_status.ts:367` ends with `// OMT_LIVE_PROBE_MARKER safe to remove` (dead probe marker, committed). And `REFACTOR_PLAN.md` + `REFACTOR_PLAN_v2.md` at root are the SUPERSEDED plans for the already-executed test consolidation — not this refactor; they confuse planning. All → R0 hygiene (delete probes + marker; archive or delete the two stale plans — decision point, default: delete, they are preserved in git history).
- **F12 — reindex over-prune mechanism narrowed down.** Code read (omt_think.ts:714–739): keep requires `cur.text === r.thought && (cur.cat||null) === recCat` (:724); repair requires EXACTLY ONE line where `p.text === r.thought && cat equal` (:731); else dropped as "vanished/ambiguous" (:738). So the criterion is **exact text+category equality between insert-time record and re-parse** — any normalization asymmetry (whitespace collapse, category casing/null-vs-empty) silently drops. The 3 known victims' add-records are NOT in git (`.meta/.omt/thoughts.jsonl` is untracked → **no backup exists; a bad reindex is destructive**). Repro must be rebuilt from the live on-disk comments (still present at omt_think.ts:819, enforcer:1070). R4 updated: (a) failing unit test reconstructing the record from a live comment, (b) normalize both sides identically, (c) backup `thoughts.jsonl` before rewrite (cheap insurance for an untracked file).
- **F13 — R1 loader-constraint evidence gap (confirmed, plan stance kept).** No doc in `.meta/` proves opencode's plugin glob; the dist/ experiment only proves `.opencode/plugins/*.ts` is loaded. `.opencode/lib/` sits outside the plugin dirs by convention, but the R1 live-verification step stays MANDATORY as written. **ROUND-2: downgraded by F19 — official docs now support the constraint.**

### 0.4 Second-pass audit (round 2, same day) — official opencode plugin docs + full drift census

Round-1 verdicts re-verified, ALL HOLD:
- **F6 re-run, exact match:** `uv run pytest tests/ -m "not opencode_live"` → **7 failed (4× feature_016 + 3× feature_018), 973 passed, 17 deselected, 38 s**.
- **F5 form precision:** the feature_016 drift is in **Path-parts form** — `(REPO_ROOT / ".opencode" / "plugin" / "omt_enforcer.ts")` (lines 97/105/112/116) — NOT the literal `.opencode/plugin/` string. A naive `grep '\.opencode/plugin/'` MISSES it. Sweeps and the R5 drift-pin must match both forms.
- **F9 confirmed:** receipt `covered_files` = 10 entries, omits `omt_nav.ts` (also `.meta/templates/`); `passed_at` 2026-07-25T22:50Z (fresh today).
- **F10 confirmed + sharpened:** THOUGHT_PATTERN byte-identical (enforcer:254 ↔ think:38), **0 hits in tests/**. Both sync comments still claim "structural test asserts it" — these comments now LIE; R0's pin test must also fix both comment texts.
- **F12 confirmed + refined:** the ONLY reader of index add-record anchors is `omt_think_verify` (omt_think.ts:546–556, basis anchor|exists). The reindex header comment itself declares "**grep stays the gate's source of truth**; the index carries B1 anchors + C1 [verify records]" (omt_think.ts:659) — the rewrite-by-filter reindex is an architectural anomaly, which motivates deletion over repair (R6 S1).

New findings:

- **F14 — opencode.jsonc `plugin` array is npm-only per official docs (changes R0).** Official plugin documentation: two load paths — local files placed in `.opencode/plugins/` are **auto-loaded at startup**; the config `plugin` array lists **npm packages**. The 4 `omt_*` entries are local plugins → the array entries are redundant; `"omt_nav.js"` (explicit extension) is not even a valid npm package name. R0's planned `"omt_nav.js" → "omt_nav"` normalization treats the symptom; the correct fix is **removing all 4 `omt_*` entries** (live-verify tool registration on 1.18.5; fallback = bare names if verification regresses). This DELETES the whole config-drift class (the WORK.md pending-approval follow-up) instead of normalizing it — and aligns with the user's directive that plugins are plural/directory-loaded.
- **F15 — §0.1 "CLEAN tree" is stale.** `git status` NOW: `omt_status.ts` modified (+2 lines: the `OMT_LIVE_PROBE_MARKER` is **duplicated** at :368–369 — file is 370 lines, not 368) and this plan doc modified (the round-1 §0 audit itself, expected). A BUG-B-recipe probe evidently left the duplication behind. R0 hygiene: `git checkout -- .opencode/plugins/omt_status.ts` (revert, don't hand-edit — receipt-covered file; refresh receipt after). The F11 "delete the marker line" item becomes moot via the revert.
- **F16 — singular-path drift census: 77 hits repo-wide, not 12 (expands R0 scope).** Live (non-historical) sites beyond round-1's list: `.meta/doc/omt++/architecture.md`:117,128 · `.meta/doc/omt++/features.md`:47,78,85 · `.meta/software_development_process/4.design/structure/STRUCTURE.md`:67 · `scripts/omt/new_feature.py`:13 · plugin header comments `omt_status.ts`:361 and `omt_nav.ts`:259 (guarded files — receipt cycle). The **enforcer itself has 0 hits** (the feature_023 eval doc's enforcer :336/:1043/:1070 claim is stale). The remaining ~50 hits are historical per-feature docs (2.requirements → 6.testing feature dirs + the PoC eval doc, which itself catalogued this as G6 "cosmetic" in its §4.2). **Decision point, default: fix LIVE docs + sources only; declare historical per-feature docs frozen point-in-time records** (rewriting them falsifies history; R5's drift-pin guards the live set going forward).
- **F17 — `worktree` is the correct repo-root anchor, not `directory` (upgrades F2/R1).** Official plugin context: `{project, client, $, directory, worktree}` — `directory` = current working directory (so a subdir launch breaks it EXACTLY like `process.cwd()` — F2's fix as written does **not** fix the subdir case), while `worktree` = git worktree path. R1's shared lib must resolve repo paths from `worktree ?? directory` (live-verify `worktree` is always populated by the plugin factory).
- **F18 — digest can move to the documented `event` hook (enables R6 S3).** The official event list contains NO `session.start` (definitively explains the F14c-inert finding) but documents a generic `event` hook and a `session.created` event. `omt_think.ts` currently carries BOTH the inert `"session.start"` hook (:804) and the Tier 1c first-tool-result path (`digestSessions` Set :795 + check :810–813). An `event`-hook digest on `session.created` deletes both. **Gate:** live-verify `session.created` fires under headless `opencode run` on 1.18.5; fallback keeps Tier 1c (delete only the dead hook).
- **F19 — R1 loader constraint now doc-supported (downgrades F13).** Official doc: a plugin module "exports one or more plugin **functions**"; every named-export example is a function; imports are documented (npm deps via `.opencode/package.json`, Bun resolution). Named non-function exports living OUTSIDE the plugin dirs (`.opencode/lib/`) are standard module resolution — risk class drops from unknown to low. Live verification stays in R1 (cheap) but is no longer a go/no-go unknown.
- **F20 — P5 undercount: FIVE process-lifetime state containers in the enforcer, not 3 (correction).** `sessionNavState` :328, `injectedThisSession` :333, `navRemindedSessions` :341, **plus `hardSnapshot` :472 and `refactorSnapshots` :473**. R2's `session_state.ts` scope = all 5 (minus any deleted by R6).
- **F21 — think-gate consult read is O(ledger size) per gated edit (ties R4 rotation to gate latency).** `hasConsultedThoughts` (enforcer:217–247) JSON.parses every ledger line on every gated edit; the ledger is unbounded (109 KB today). R4's rotation keeps the hot file small → think-gate latency stays flat. Not a separate fix; recorded as an R4 benefit and as a hard upper-bound argument for the 64 KB cap.
- **F22 — reindex deletion is receipt-pinned (R6 wiring cost).** The e2e test source-pins the 6-tool map (`test_omt_harness_e2e.py`:190) and the `"omt_think_reindex": "allow"` permission (:200; opencode.jsonc:77). Deleting the tool = e2e pin update (tests/ canary) + config edit (receipt cycle). Mechanical, but must be planned in R6, not discovered mid-edit.
- **F23 — ALL of `.meta/.omt/` is untracked, not just thoughts.jsonl.** `git ls-files .meta/.omt/` → empty: `ledger.jsonl` (the omt_skip/phase audit trail!), `thoughts.jsonl`, `tdd_snapshots/`, and the e2e receipt are ALL local-only. F12's "no backup" therefore extends to the process ledger; R4's rotation archives are likewise local. Acceptable solo-dev posture — recorded explicitly so it stops surprising audits.

### 0.5 Third-pass audit (round 3, same day) — full re-verification + token-consumption census

Round-1/round-2 verdicts re-verified, ALL HOLD:

- **Line counts exact:** enforcer 1184 / nav 276 / status 370 / think 819 / tdd_check 825 (`wc -l`).
- **F6 exact match (3rd consecutive run):** `uv run pytest tests/ -m "not opencode_live"` → **7 failed (4× feature_016 + 3× feature_018), 973 passed, 17 deselected, 39 s**.
- **F15 confirmed with line precision:** the marker is duplicated at **:368 and :370** (diff adds blank :369 + marker :370; plan said ":368–369" — cosmetic precision fix only, the revert recipe `git checkout -- .opencode/plugins/omt_status.ts` is unchanged).
- **F9 confirmed:** receipt `covered_files` = 10 entries, omits `omt_nav.ts`; `passed_at` refreshed to **2026-07-25T23:09Z** (receipt was re-run after round 2 — content still omits nav).
- **F14/F22 confirmed on disk:** opencode.jsonc `plugin` array = `["omt_enforcer", "omt_nav.js", "omt_status", "omt_think"]`, line-3 comment singular, `"omt_think_reindex": "allow"` at :77. Live tool census (this session): **19 `omt_*` tools** registered — B6's "19 (18 post-R6)" is exact.
- **F20 exact:** enforcer state containers at :328/:333/:341/:472/:473 (5, all process-lifetime).
- **F21 confirmed by direct read:** `hasConsultedThoughts` (enforcer:226–230) reads + JSON.parses EVERY ledger line per gated edit; ledger now **109,329 B** (grew 148 B since round 1).
- **META_HARNESS.md 10 singular lines exact:** 44–47, 99, 108, 201–204. AGENTS.md:7 singular confirmed. e2e pins at `test_omt_harness_e2e.py`:190/:200 confirmed (F22 wiring cost stands).
- **R6 deletion targets confirmed:** `reconcileIndex` rewrite :100–110, `reindexRecords` :657–760 + `writeFileSync(THOUGHTS_INDEX…)` at :751, `digestSessions` :795, `"session.start"` hook :804, Tier 1c :810–813, tool map :801, grep-is-truth declaration :659. `omt_think_reindex` wiring: e2e :190 tool map + :200 permission + opencode.jsonc:77.

New findings:

- **F24 — test-file singular hits are intentional history, do NOT "fix".** `tests/scripts/omt/test_omt_enforcer_guard_source_pins.py`:22–23 mentions `.opencode/plugin/` inside a docstring describing the PRE-rename state (the bug the test pins). Suite passes 10/10. Recorded so no future auditor breaks the docstring's historical accuracy; R5's drift-pin must EXCLUDE docstrings/comments that quote the old path for history (pin the Path-parts construction + literal in NON-comment tokens, or whitelist this file with a comment).
- **F25 — README.md carries 5 LIVE singular-path hits (:69–72, :84) — missed by F16, and it is NEVER-edit protected.** AGENTS.md blocks README.md edits. **Decision point, default: (a) drift-pin excludes README.md with a pointer comment + (b) user hand-edits at leisure** (the table is user-facing documentation, not agent-consumed; zero mechanical impact). Option (c) one-time `omt_skip` fix is recorded but NOT default (README never-list exists to force human authorship).
- **F26 — WORK.md carries both a singular path AND two stale entries (missed by F16/R0).** WORK.md:86's FOLLOW-UP note quotes `.opencode/plugin/omt_enforcer.ts` and proposes the `"omt_nav.js" → "omt_nav"` normalization — **fully superseded by F14's plugin-array removal**; R0 closes the follow-up by editing WORK.md:86, not the config normalization. WORK.md:57's task summary is stale (anchor `d497dce`, workstreams "R0–R5", no R6/R7) → R0 updates it (anchor `a7163df`, R0–R8).
- **F27 — Root clutter beyond F11's list: `OMT_SESSION_STATE_feature_023.md` + `OMT_SESSION_STATE_feature_023_deep_tests.md`** (12 KB, both completed work, both quote the singular path historically). F11 missed them. → R0 hygiene deletions (git history preserves; same default as REFACTOR_PLAN*.md).
- **F28 — Verify-record misassociation on line drift (sharpens R6 S1's digest join).** Live evidence in thoughts.jsonl: the verify record keyed `main_screen.py:79` carries the thought TEXT of live `:81` (todo) — recorded pre-drift. The digest's stale-join keys verdicts by `path:line` only → after ANY insertion/removal above a thought, verdicts silently re-attach to the WRONG thought. R6 S1's "JOIN verify verdicts against live grep hits" must **match on normalized thought TEXT (verify records already store full text), not `path:line` alone**; `path:line` remains the display key. Also noted: of 4 live add-records, ONE has `"anchor":null` and THREE carry `repaired_from` but **no `anchor` field at all** — the B1 anchor machinery has produced zero usable anchors in 9 days of production (feeds S1b below).
- **F29 — R6 S1's no-rewrite pin is imprecise as written (would be false-red).** "`writeFileSync` appears 0 times in omt_think.ts" can never pass: `omt_think` (:405) and `omt_think_remove` (:489) legitimately `writeFileSync` the TARGET file — that IS the tool's function. Correct pin: **`writeFileSync(THOUGHTS_INDEX` appears 0 times** (today 2: :108 reconcile, :751 reindex). R6 S1 corrected below.
- **F30 — Startup-directive contradiction.** AGENTS.md:3 STARTUP says read 4 docs (`WORK.md → AGENTS.md → META_HARNESS.md → omt_agent_guide.md` ≈ 58 KB ≈ ~15k tok); the ACTUAL build-agent system prompt `.agents_prompts/build.md` says "Read `WORK.md`" ONLY. The 4-doc directive also contradicts the feature_020 nav-tool philosophy (docs searchable on demand via omt_nav/omt_list_sections). Followed literally it burns ~10–11k tok/session on META_HARNESS.md+guide (WORK.md is needed regardless; AGENTS.md is already in the system prompt). → R7 T1 makes WORK.md-only startup authoritative in AGENTS.md too.
- **F31 — Nav reminder fires unconditionally on the first tool result, even when the session's FIRST tool was a nav tool (already compliant).** Enforcer :1049–1054 gates only on `navRemindedSessions`. Cheap deferral: if `input.tool` is a nav tool, skip WITHOUT marking the Set — the reminder then lands on the first NON-nav tool result instead. Saves ~120 tok in nav-first sessions; more importantly stops teaching the already-taught. → R7 T3.

### 0.6 Fourth-pass audit (round 4, same day) — token-model completion + plan precision fixes

Round-1/2/3 verdicts re-verified, ALL HOLD (4th consecutive data point):

- **Tree:** HEAD still `a7163df`; dirty = `omt_status.ts` (F15 marker dup — `git diff` shows committed :368 + added blank :369 + dup :370; revert recipe unchanged) + this plan doc (round-3 audit edit). Baseline anchor unchanged.
- **Line counts exact:** enforcer 1184 / think 819 / status 370 / nav 276 / tdd_check 825 (`wc -l`).
- **F6 exact match (4th run):** `uv run pytest tests/ -m "not opencode_live"` → **7 failed (4× feature_016 + 3× feature_018), 973 passed, 17 deselected, 38 s**.
- **Sizes:** ledger **109,901 B** (+572 since round 3 — unbounded growth continues, R4); AGENTS.md 4,766 B; WORK.md 12,835 B; META_HARNESS.md 13,179 B; guide **27,422 B / 718 lines at `.meta/software_development_process/omt_agent_guide.md`** (full path recorded for the first time — NOT under `.meta/doc/omt++/`); build.md 337 B.
- **On-disk spot-checks, all exact:** state containers enforcer:328/:333/:341/:472/:473 (F20); THOUGHT_PATTERN enforcer:254 ↔ think:38 byte-identical (F10); digestSessions :795 / `"session.start"` :804 / Tier 1c :810–811 (R6 S3 targets); navRemindedSessions gate :1049–1050 (F31); singular comments status:361, nav:259, AGENTS.md:7 (F16/F4); opencode.jsonc `plugin` array + line-3 singular + reindex permission :77 (F14/F22). WORK.md:57/:86 stale entries unchanged (F26 stands).
- **Receipt:** re-run again since round 3, `passed_at` **2026-07-25T23:33Z**; `covered_files` still 10, still omits `omt_nav.ts` (F9 stands).
- **opencode run census (C2): claim HOLDS, method note corrected.** The literal string `opencode run` appears on only 2 lines (prose) — round-3's "`grep -c` → 22 sites" was method-imprecise. True count ≈ 20–22 invocation sites: 19 `_run_opencode(...)` call sites (helper :65 wraps `[OPENCODE_BIN, "run", …]`) + ≥1 direct `OPENCODE_BIN run` (:110). Conclusion (C2 magnitude) unchanged.
- **This session as live evidence:** 19 `omt_*` tools registered (B6 exact); session digest = 8 thoughts across 6 files ≈ 1.4 KB full-text dump incl. BOTH probe files (F11 pollution live-costing every session); nav tip ≈ 0.45 KB — matches C4/C5.
- **Executor safety note:** the 4 `TA:` substrings in this plan doc are prose; 0 hits against THOUGHT_PATTERN — the doc is NOT think-gated.

New findings:

- **F32 — Appendix C's per-session figures are first-turn-only; conversation-resident injections are re-paid EVERY model turn (the missing multiplier).** Agentic-loop APIs resend full conversation history on every model call, so anything appended to a tool result (nav tip C5, TA digest C4, D1 per-file injections C6, gate blocks C8, omt_status output C9) is re-paid on each subsequent turn: turn-adjusted cost ≈ size × (N − t₀). At N≈30 turns: C4's ~350 tok digest → up to ~10k tok/session; C5's ~120 tok tip → ~3.5k; one D1 injection (~150 tok) → ~4.5k. Consequences: (a) S7's compact digest + T3's deferral are worth ~10–14k tok/session, not ~500 — both defaults STRENGTHENED; (b) terse TA: thought texts pay off (they persist); (c) the harness is markedly more expensive than Appendix C showed. Caveats: prompt caching attenuates input re-reads (cache-read ≈ 0.1× on supported providers → still ~1–1.4k for C4+C5); opencode compaction (B4 `session.compacted`) eventually truncates; N is an assumption, not a measurement (R8's budget report should capture real per-session usage). → Appendix C C12.
- **F33 — The 19 `omt_*` tool schemas ride the system prompt EVERY turn and were never censused (largest uncensused harness cost; supersedes F30's "largest single token finding" claim — T1's fix stands regardless).** Tool schemas are part of the system-prompt prefix on every model call, including sessions that never touch the harness. Census of the live schemas (this session): ≈ 4.5–6 KB ≈ **1.1–1.5k tok/turn** marginal for the omt set (omt_think alone ≈ 0.9 KB, the longest description). At N≈30 turns ≈ 33–45k tok/session input-side before caching (≈3–4.5k cache-attenuated). Mitigations: (a) tighten descriptions, single-sourced + budget-pinned (R7 T8 → R8 `@tool`); (b) decision point: consolidate 19 → ~7 tools (`omt_tdd{op:…}`, `omt_think{op:…}`) — changes B5 permission keys + e2e pins, mega-tool usability must be live-verified. → Appendix C C11 + R7 T8 + R8/D6(a).
- **F34 — build.md:5 "Display to the user the current state of the WORK" costs OUTPUT tokens (~3.2k if literal).** Literal compliance echoes WORK.md (12.8 KB) into the assistant turn; output tokens typically price ~3–5× input. Fix: build.md specifies "summarize current state in ≤ 15 lines". → R7 T7 (rides R0 doc edits). The round-4 session complies with the summarized form as prior art.
- **F35 — opencode.jsonc permission block covers only 10 of 19 `omt_*` tools.** Present: 4 nav + 6 think (incl. reindex). Missing, running on the implicit permissive default: **omt_phase, omt_complete, omt_skip, omt_status, omt_testlist, omt_red, omt_green, omt_refactor, omt_done** — all 9 phase/TDD tools. Harmless today (opencode.jsonc:31–32 "defaults stay permissive"), but it is the F14/F22 implicit-drift class: a future default flip would silently gate the process tools. → R0 makes the 9 explicit in the same config edit (receipt cycle already planned); R8's `@tool perm=` projection makes the block generated, killing the class.
- **F36 — The executor's plan-reading cost is unbudgeted (~13k tok for this 342-line doc).** §4 sends an executing agent into the full plan; only the §3 R<n> block + §4 + Appendix B are execution input (~3–4k tok). → §4 step 0 added.

Precision fixes applied this round (not findings):

- **F30 line ref:** "AGENTS.md:10 STARTUP" → **AGENTS.md:3** (on-disk verified; R7 T1 carried the same wrong ref — fixed there too).
- **Header:** round-3 summary said "R6 extensions S1b/S6/S7/S8" — there is no S8 (R6 ends at S7). Header corrected.

---

## 1. Current State Inventory

| Layer | Component | Lines | Issues |
|---|---|---|---|
| Plugins (TS) | `.opencode/plugins/omt_enforcer.ts` | 1184 | Monolith: 8 concerns in one hook body (phase gate, TDD two-hats, think-gate, nav-gate, e2e-receipt guard, protected files, MVC++ after-hook, digest/nav-reminder emission) |
| | `.opencode/plugins/omt_think.ts` | 819 | 6 tools + all helpers in one file |
| | `.opencode/plugins/omt_status.ts` | 370 | Duplicates ledger/path logic; dead probe marker DUPLICATED at :368 and :370 (F11+F15, round-3 precision) |
| | `.opencode/plugins/omt_nav.ts` | 276 | Duplicates doc-path logic; missing from e2e covered_files (F9) |
| Scripts (Py) | `scripts/omt/tdd_check.py` | 825 | 9 subcommands in one file; `run_full_suite` 120 s timeout too small when live tests run (F7) |
| | `scripts/omt/mvc_check.py`, `new_feature.py` | 366 | OK — leave as-is |
| State | `.meta/.omt/ledger.jsonl` | ~109 KB | Unbounded growth, no rotation |
| | `.meta/.omt/thoughts.jsonl` | untracked | No backup; destructive reindex risk (F12). ROUND-2: **ALL of `.meta/.omt/` is untracked** — ledger, receipt, snapshots too (F23) |
| Docs | META_HARNESS.md (209) / AGENTS.md (74) / omt_agent_guide.md (718) | ~1000 | Hand-synced; drift present in BOTH META_HARNESS.md (10 lines) AND AGENTS.md:7 (F3/F4) |
| Tests | `tests/scripts/omt/` (6 files) + feature dirs | — | Source-pin tests grep enforcer content; brittle under refactor by design. feature_016 file carries singular-path bug (F5) |
| Root clutter | REFACTOR_PLAN.md, REFACTOR_PLAN_v2.md, test_think_gate*.py, OMT_SESSION_STATE_feature_023*.md | — | Superseded plans + committed probe leftovers (F11) + stale session-state files (F27) |

## 2. Problems (evidence-based)

- **P1 — Cross-plugin duplication (map corrected by audit F1).** Actual duplicates:
  - `REPO_ROOT = process.cwd()` ×3 (nav:10, status:10, think:28) — enforcer diverges via `directory` (F2).
  - `LEDGER_PATH` byte-identical ×2 (status:11, think:30) + enforcer's own `ledgerPath` (:327).
  - `THOUGHT_PATTERN` byte-identical ×2 (enforcer:254, think:38) — sync contract now unenforced (F10).
  - `resolveFeatureDir` duplicated ×2 (enforcer:80, status:87).
  - `UNLOCK_WINDOW_MS` ×3 across languages: enforcer:48 (named), tdd_check.py:41 (named), omt_status.ts:59+244 (**inline magic numbers**).
  - Ledger read/append helpers re-implemented per plugin (status:39–41, think:144–153, enforcer internal).
  Cross-cutting changes must be applied N times — the F14 MIRRORED bug happened precisely this way.
- **P2 — Doc/config drift (expanded by audit F3/F4/F5/F9/F10/F11, census completed by round-2 F14/F15/F16, refined by round-3 F24/F25/F26/F27).** META_HARNESS.md `.opencode/plugin/` singular ×10 lines (44–47, 99, 108, 201–204); AGENTS.md:7 same bug; `opencode.jsonc` line-3 comment singular AND `plugin` array misused for local plugins (npm-only per official docs — F14); live docs `.meta/doc/omt++/architecture.md`:117,128, `features.md`:47,78,85, `STRUCTURE.md`:67, `new_feature.py`:13, plugin comments `omt_status.ts`:361/`omt_nav.ts`:259 (F16); **round-3 adds: README.md ×5 (NEVER-edit protected — F25), WORK.md:86 (F26)**; feature_016 test file same bug in **Path-parts form** (4 live failures); test_omt_enforcer_guard_source_pins.py:22–23 hits are intentional historical prose (F24 — excluded); e2e covered_files ≠ isOmtHarness set; THOUGHT_PATTERN sync test deleted AND both sync comments lie about it; stale root plans + probe leftovers (incl. uncommitted duplicated marker — F15) **+ OMT_SESSION_STATE_feature_023*.md ×2 (F27)**; WORK.md:57 task summary stale (F26). Repo-wide census 99 hits (round 3); ~50 historical per-feature docs + ~26 historical design-doc hits declared OUT OF SCOPE (frozen records, F16 default).
- **P3 — Known latent bugs (list corrected by audit F6/F7, reframed by round-2).** `omt_think_reindex` over-prunes — root cause is the **rewrite-by-filter pattern itself** (`reconcileIndex` omt_think.ts:100–110 + `reindexRecords` :657–760), not merely normalization asymmetry → fix by DELETING the rewrite class (R6 S1), not patching comparisons; `omt_done` unreachable via THREE independent causes: (a) 3 pre-existing feature_018 failures, (b) 2 window-flaky tdd_check tests, (c) **120 s timeout < live-included suite runtime (F7)**; TESTLIST two-hats chicken-and-egg on tests/ creation.
- **P4 — Brittle test anchors.** Source-pin tests grep enforcer *content/lines*; any refactor breaks anchors by design and needs a planned pin rewrite.
- **P5 — Session-state fragmentation (count corrected by round-2 F20).** **5** process-lifetime containers inside the enforcer closure: `sessionNavState` :328, `injectedThisSession` :333, `navRemindedSessions` :341, `hardSnapshot` :472, `refactorSnapshots` :473 — no shared abstraction.
- **P6 — opencode version drift 1.18.3→1.18.5 (F8).** Binary-audit claims (session.start inert, F14c live path) pinned to 1.18.3; live suite not re-baselined since the upgrade. ROUND-2: the official event list (no `session.start`, generic `event` hook documented) independently confirms the F14c analysis (F18).
- **P7 — Config/plugin-model mismatch (round-2 F14).** `opencode.jsonc` lists local directory-loaded plugins in the npm-only `plugin` array — redundant, misleading, and the source of the recurring `"omt_nav.js"` drift. Removal is a simplification, not just a normalization.
- **P8 — Think-anywhere carries a destructive-rewrite subsystem (round-2 reframe of F12).** The index is declared grep-is-truth (omt_think.ts:659), yet two rewrite paths (`reconcileIndex`, `reindexRecords`) can silently destroy untracked state. Append-only + tombstones delivers the same semantics (incl. C1 "re-added starts unverified") with zero rewrites. Round-3 F28 adds: verdict keying by `path:line` misassociates on drift — the join must match normalized text.
- **P9 — Harness token overhead is unbudgeted and partly contradictory (round-3, F30/F31 + Appendix C census).** (a) Startup directive contradicts itself across AGENTS.md (4 docs ≈ 15k tok) vs build.md (WORK.md only ≈ 3.5k tok); (b) per-session injections (nav tip ~120 tok + TA digest ~300–400 tok growing to ~1.1k at cap) duplicate what D1 re-injects point-of-use; (c) WORK.md scratchpad carries ~5 KB of DONE-feature history into every session; (d) the live suite is 22 full `opencode run` agent sessions per execution (the dominant harness-driven token consumer); (e) no mechanical pin bounds any of these. Every wasted token is paid EVERY session, so small leaks dominate one-time costs. **Round-4 completion (F32–F35):** (f) Appendix C's per-session numbers are first-turn-only — conversation-resident injections re-pay per model turn (F32, the missing multiplier: digest + nav tip ≈ 10–14k tok/session turn-adjusted at N≈30); (g) the 19 omt_* tool schemas ride the system prompt EVERY turn (~1.1–1.5k tok/turn — the largest uncensused cost, F33); (h) build.md's "Display … WORK" costs ~3.2k OUTPUT tok if literal (F34); (i) 9 of 19 omt_* tools run on implicit permission defaults (F35). F32/F33 re-rank the optimization order: **per-turn costs dominate per-session costs** — this is the argument for R8's language-level fix (Appendix D).

## 3. Workstreams (ordered low → high risk; each independently shippable)

### R0 — Drift & hygiene fixes (~1 h, zero code-risk) — EXPANDED by audit (rounds 1 + 2 + 3 + 4)
- META_HARNESS.md: `.opencode/plugin/` → `.opencode/plugins/` — **all 10 lines** (44–47, 99, 108, 201–204) (F3).
- AGENTS.md:7 ENF line: same fix (F4).
- Remaining LIVE singular sites (F16): `.meta/doc/omt++/architecture.md`:117,128 · `.meta/doc/omt++/features.md`:47,78,85 · `4.design/structure/STRUCTURE.md`:67 · `scripts/omt/new_feature.py`:13 · guarded plugin comments `omt_status.ts`:361, `omt_nav.ts`:259 (receipt cycle applies). Historical per-feature docs: **out of scope** (frozen records, F16 default decision).
- `opencode.jsonc` (F14, supersedes the round-1 `"omt_nav.js" → "omt_nav"` normalization): **remove all 4 `omt_*` entries from the `plugin` array** — per Appendix B1 local plugins auto-load from `.opencode/plugins/`; the array is npm-only. Live-verify all 19 `omt_*` tools register + 17 live tests GREEN on 1.18.5; fallback on regression: restore with bare names. Fix line-3 comment to `plugins/` plural. Also drop `"omt_think_reindex": "allow"` (:77) IF R6 S1 is executed in the same cycle (F22). Round-4 F35: also add explicit `"allow"` keys for the 9 uncovered phase/TDD tools (omt_phase, omt_complete, omt_skip, omt_status, omt_testlist, omt_red, omt_green, omt_refactor, omt_done) — permissive defaults today, but the implicit-drift class dies here (generated block post-R8). *(Clears the WORK.md pending-approval follow-up — this plan constitutes the approval record.)*
- Revert probe pollution (F15): `git checkout -- .opencode/plugins/omt_status.ts` — drops the duplicated marker at :368/:370 (receipt-covered file: refresh receipt after; this makes F11's "delete the marker line" item moot).
- feature_016 test file: `".opencode" / "plugin"` → `".opencode" / "plugins"` (**Path-parts form**) at 4 sites (97/105/112/116) → 4 red tests green (F5). **tests/ canary: `omt_skip{reason:"fix feature_016 path drift", scope:"tests"}` per §4.**
- e2e `covered_files` += `omt_nav.ts` (align with isOmtHarness; note `.meta/templates/` + feature_006 dir intentionally doc-only) (F9).
- Add THOUGHT_PATTERN source-pin test (byte-identical enforcer:254 ↔ think:38) — interim guard until R1 (F10). **Also fix both lying "structural test asserts it" comments** (enforcer:253, think:37) to reference the new pin.
- Hygiene deletions (F11 + round-3 F27): `test_think_gate.py`, `test_think_gate_probe2.py` (+ `omt_think_reindex` to reconcile TA index — or just verify the digest goes clean, since grep is truth), REFACTOR_PLAN.md + REFACTOR_PLAN_v2.md, **`OMT_SESSION_STATE_feature_023.md` + `OMT_SESSION_STATE_feature_023_deep_tests.md`** (decision point: delete, default; git history preserves).
- **WORK.md updates (F26):** :57 task summary → anchor `a7163df`, workstreams R0–R7; :86 FOLLOW-UP note → mark CLOSED by this plan (F14 plugin-array removal supersedes the `"omt_nav.js"` normalization it proposed).
- **README.md ×5 singular hits (F25):** decision point, default = do NOT edit (NEVER-edit protected); R5 drift-pin excludes it with a pointer comment; user hand-edits at leisure.
- **Re-baseline on opencode 1.18.5 (F8):** run 17 live tests BEFORE any edit; annotate version-pinned comments ("audited 1.18.3, re-verified 1.18.5") where the suite confirms behavior; escalate if behavior changed.
- Refresh e2e receipt: `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`.
- **Verify:** 68 harness static + feature_016 suite GREEN; receipt fresh; live-suite baseline recorded in WORK.md.

### R1 — Shared TS lib: `.opencode/lib/omt_shared.ts` (~1.5 h)
- **Build every touched plugin per Appendix B** (B1 placement/loading, B2 module shape, B3 repo-root): `.opencode/lib/` is NOT a plugin dir → named non-function exports are legal there (B2); plugin files in `plugins/` keep ONLY the default-export function.
- Extract: repo-root resolution, `LEDGER_PATH`/state paths, `THOUGHT_PATTERN`, `resolveFeatureDir`, ledger read/append, e2e-receipt status check, glob→regex.
- **Standardize on SDK `worktree ?? directory`, NOT `process.cwd()` and NOT bare `directory`** (F2 upgraded by F17): `directory` is the current working directory, so a subdir launch breaks it exactly like `process.cwd()`; `worktree` is the git worktree path. Lib exports an init (`initOmtShared(worktree ?? directory)`) or per-call param; the 4 plugins close over the plugin-factory ctx value. Live-verify `worktree` is always populated; fall back to `directory`.
- 4 plugins import from it; delete in-file copies (incl. enforcer's `directory`-based variants — converge on ONE implementation).
- Note: enforcer session-state containers are deliberately NOT extracted here — they are enforcer-internal and move to `lib/enforcer/session_state.ts` in R2 (all 5, F20).
- `UNLOCK_WINDOW_MS`: dedupe across the TS plugins here; tdd_check.py keeps its own copy (cross-language — add a comment pin both sides; optionally a cheap test asserting the two constants agree).
- **Constraint (round-2 F19: now doc-supported, low risk):** official docs say a plugin module exports plugin FUNCTIONS only (named-export examples are all functions) — matching the WORK.md loader gotcha. A `lib/` dir outside the plugin dirs + plain imports is standard Bun module resolution. **Live verification after extraction stays MANDATORY** (cheap; no longer a go/no-go unknown).
- **Verify:** live `opencode run` + one call per tool (phase, status, nav, think); 17 live tests GREEN; e2e receipt refresh between guarded edits (receipt-rebuild cycles per gotcha). THOUGHT_PATTERN pin test from R0 now asserts the single source (update pin target).

### R2 — Split the enforcer monolith (~3 h)
- `omt_enforcer.ts` → thin composition root (~200 lines): hook registration + dispatch only. **Must still satisfy Appendix B2 exactly**: single default-export async function receiving ctx, returning the hooks object; zero named non-function exports; all gate logic imported from `.opencode/lib/enforcer/`.
- New modules under `.opencode/lib/enforcer/`: `phase_gate.ts`, `tdd_hats.ts`, `think_gate.ts`, `nav_gate.ts`, `receipt_guard.ts`, `mvc_after.ts`, `session_state.ts` (shared abstraction over all **5** confirmed state containers — `sessionNavState`, `injectedThisSession`, `navRemindedSessions`, `hardSnapshot`, `refactorSnapshots`; fixes P5/F20; minus any deleted by R6).
- Rewrite source-pin tests as coarser contract pins (hook names, guard order, error-message prefixes) — accept planned pin breakage (P4).
- `omt_enforcer.ts` is think-gated (TA: at :1070, confirmed present) → `omt_think_list` consult before editing; re-anchor the TA: comment into the appropriate lib module (`mvc_after.ts`).
- **Verify:** 17 live tests GREEN; rewritten pins GREEN; full harness suite; receipt cycles between chunks (batch edits per Write-tool gotcha).

### R3 — Split `tdd_check.py` (~1 h)
- 825 lines → `scripts/omt/tdd/` package: `cli.py` (arg dispatch), `state.py` (ledger/state IO), `gates.py` (two-hats, validate-exit), `ast_checks.py` (true-RED, coverage gaps).
- Keep `scripts/omt/tdd_check.py` as a thin compat shim — enforcer and docs call `tdd_check.py <subcommand>`; no call-site changes.
- **Verify:** `tests/scripts/omt/test_tdd_check.py` + harness suite GREEN.

### R4 — State hygiene + latent bugs (~1 h, shrank — reindex item moved to R6 as a deletion)
- `ledger.jsonl` rotation: size-cap (e.g. 64 KB) → archive to `ledger-YYYYMM.jsonl`; readers scan current + latest archive (8 h window — verified shared across all 3 readers — makes this safe). Note: ledger is already 109 KB → rotation triggers on first run. **Round-2 F21: rotation is also the think-gate latency fix** — `hasConsultedThoughts` parses the whole ledger per gated edit; a capped hot file keeps gate cost flat.
- ~~Fix `omt_think_reindex` over-prune~~ → **MOVED to R6 S1 as a DELETION** (round-2 P8: the bug class is the rewrite-by-filter pattern itself; grep-is-truth makes reindex redundant — deleting beats repairing, and the F12 "untracked, backup-less, destructive" risk disappears with the rewrite path).
- `omt_done` fixes (F6/F7): (1) `-m "not opencode_live"` in `run_full_suite` (or parameterized timeout) — deterministic blocker; (2) known-failure allowlist (feature_018 ×3, ledger-window ×2) OR formally document the `omt_complete{advance_to:Testing→Done}` exit as the supported path — **decision point, default: (1)+(2) allowlist**.
- TESTLIST chicken-and-egg (P3): tests/ creation is blocked by the two-hats gate before any RED exists → **decision point**: (a) auto-unlock tests/ *new-file creation* during TESTLIST state, or (b) formally document the `omt_skip{scope:tests}` bootstrap as the supported path — **default: (b) document** (auto-unlock weakens the canary model; feature_021/022 prior art uses the logged skip).
- **Verify:** rotation unit test (window readers scan current + latest archive); `omt_done` dry-run completes < timeout; harness suite GREEN.

### R5 — Docs single-source (~30 min; +R7 ride-alongs)
- Re-sync AGENTS.md ↔ META_HARNESS.md tables (components, tools, phases).
- Add a drift-pin test: assert AGENTS.md component paths match META_HARNESS.md COMP_* entries and both match on-disk reality (prevents P2 recurrence — would have caught F3/F4/F5). **Round-2 extension: also pin ZERO singular `.opencode/plugin/` hits (literal AND Path-parts forms, F5 precision) across the LIVE doc set (F16 list), and pin the `plugin` array absent of local plugin names (F14). Round-3 exclusions (F24/F25): the pin must EXCLUDE (a) README.md — NEVER-edit protected, user hand-edits (F25 default), with a pointer comment so the exclusion is intentional, and (b) the historical docstring in test_omt_enforcer_guard_source_pins.py:22–23, which quotes the pre-rename path BY DESIGN.**
- **Round-3 ride-alongs (R7):** pin AGENTS.md STARTUP section == `.agents_prompts/build.md` startup section (T1 single-source); token budget pins (T5): AGENTS.md ≤ 5 KB, digest builder cap ≤ 1 KB (post-S7 constant), nav tip ≤ 0.5 KB, WORK.md ≤ 14 KB with scratchpad ≤ 6 KB.
- **Verify:** new pin tests GREEN; nav tools (`omt_list_sections`) still resolve all SECTION: headers.

### R6 — Think-anywhere mechanical simplification: grep-is-truth, append-only state (~1.5 h, NEW round 2)

**Goal:** every think-anywhere feature keeps working mechanically, but state is either (a) derived by live grep, or (b) append-only events. No harness state file is ever rewritten. The inline comment is already the declared source of truth (omt_think.ts:659) — R6 makes the code match the declaration.

- **S1 — Index becomes append-only; the rewrite class is DELETED (replaces R4's reindex repair; fixes P8/F12 by construction).**
  - DELETE `omt_think_reindex` (omt_think.ts:657–760 + registration :801) — grep-is-truth makes reconciliation redundant: list/digest/gate already read live comments; add-record line drift is only cosmetic (verify re-resolves anchors live, :546–556). **Decision point, default: delete** (alternative: reduce to a read-only drift REPORT that never writes).
  - DELETE `reconcileIndex` rewrite (:100–110): `omt_think_remove` appends a tombstone `{kind:"remove", path, line}` instead. One shared reader folds events latest-wins per `path:line`; a tombstoned slot reads as absent; a re-added thought (newer add-record) starts unverified — **C1 semantics preserved exactly, with zero rewrites**. Unit test: remove → re-add → verify starts unverified.
  - Digest stale-count must JOIN verify verdicts against live grep hits (defensive: file deletions like R0's probe cleanup must not leave phantom stale entries). **Round-3 F28 precision: the join must match on NORMALIZED THOUGHT TEXT (verify records already store full text), not `path:line` alone** — live evidence (verify record keyed `main_screen.py:79` carrying live `:81`'s text) shows drift silently re-attaches verdicts to the wrong thought; `path:line` stays the display key only.
  - Wiring cost (F22, planned not discovered): e2e pin update (`test_omt_harness_e2e.py`:190 tool map, :200 permission — tests/ canary per §4) + `opencode.jsonc:77` permission removal (folds into R0's config edit + receipt cycle).
  - New mechanical pin (**round-3 F29 correction**): **`writeFileSync(THOUGHTS_INDEX` appears 0 times** in omt_think.ts (today 2: :108, :751) — NOT "`writeFileSync` 0 times", which would be false-red forever: `omt_think` (:405) and `omt_think_remove` (:489) legitimately `writeFileSync` the TARGET file (that IS the tool's function). The no-rewrite invariant becomes self-enforcing on the index, where it belongs.
  - The F12 "no backup of an untracked index" risk is **moot**: append-only files are never destroyed in-place; a one-time `.bak` snapshot of the current index is taken anyway for the historical record.
- **S1b — Radical index reduction (round-3 decision point, default: DEFER, keep S1's tombstone model).** Post-S1 the index's only consumers are (i) verify verdicts, (ii) add-record anchors read solely by `omt_think_verify` (:546–556). Production evidence (F28): 4 live add-records, 1 with `"anchor":null`, 3 with `repaired_from` and NO anchor field — the B1 anchor machinery has produced zero usable anchors in 9 days. Option: reduce the index to verify-events only (drop add-records AND tombstones; verify falls back to `basis:"exists"` — already the behavior for anchor-null records), deleting ~80–120 more lines (recordAdd path, latest-wins fold). Trade-off: loses anchor-based drift re-resolution (deliberate feature_022 B1 design — omt_think{symbol/after} anchors exist for FUTURE drift repair). **Default: keep S1 as written; revisit S1b with anchor-usage evidence after R6 ships.** If ever taken: existence stays grep-derived, so removing tombstones changes no observable semantics — that is what makes the option cheap.
- **S2 — THOUGHT_PATTERN single source** — unchanged, lives in R1 (shared lib); R0's interim pin guards until then.
- **S3 — Digest moves to the documented `event` hook on `session.created` (F18).**
  - Replaces BOTH the inert `"session.start"` hook (:804 — dead code; official event list contains no `session.start`, B4) AND the Tier 1c first-tool-result path (`digestSessions` Set :795 + per-call check :810–813) with `event: async ({event}) => … if (event.type === "session.created")` (B4 signature). Same digest content (live grep + verdict join), one semantic trigger, two state mechanisms deleted.
  - **GATE (hard):** live-verify on 1.18.5 that `session.created` reaches the `event` hook in headless `opencode run` (digest must appear in `opencode run --format json` output) AND interactively. Fallback: keep Tier 1c, delete only the dead `session.start` hook; record the outcome in WORK.md.
- **S4 — Consult path: DO NOT TOUCH (verified already-optimal, round 2).** `recordConsult` (omt_think.ts:144–153) already appends `think_consult` to `ledger.jsonl`; `hasConsultedThoughts` (enforcer:217–247) already reads it with session-match + 8 h-window fallback + risk-carrier window-drop. No new consult store, no Map — R2's `session_state.ts` must NOT absorb this file-backed state. Recorded as an explicit guardrail against over-extraction.
- **S5 — D1 read-time injection: NO CHANGE** (per-read `fileThoughtsIn` grep + `injectedThisSession` dedup; the dedup Map moves to R2's `session_state.ts` mechanically).
- **S6 — Single session-bootstrap injector (round-3 addition; rides R2, not R6).** Today TWO plugins each keep a process-lifetime "first tool result" Set and each append to the same first result (enforcer nav-reminder :1049–1054 via `navRemindedSessions`; think digest :810–813 via `digestSessions`). After R2's `session_state.ts` exists, consolidate into ONE bootstrap branch in the enforcer's after-hook (thinkDigest imported from the shared lib): one Set, one emission site, load-order-independent. Do NOT do this in R6 — the digest's home is moving in S3 and its container in R2; consolidating before both moves = triple port. **Verify:** live test asserting the first tool result carries nav tip + digest exactly once still passes.
- **S7 — Compact digest (round-3 token item, P9/Appendix C C4; decision point, default: compact).** Digest currently dumps full thought texts (cap 30) on the first tool result — content D1 re-injects point-of-use anyway when the file is read. Compact form: count + per-file counts + stale ⚠️ list (text-matched per F28) + pointer (`omt_think_list` for full texts). ~300–400 tok → ~80–100 tok/session today; caps the worst case (30 thoughts ≈ 1.1k tok) to ~150 tok. **Round-4 F32: turn-adjusted the digest costs up to ~10k tok/session (350 tok × ~30 turns, history resend) — compaction's true saving is ~8–9k tok/session, not ~300.** Trade-off: loses the session-start repo-wide thought preview (the probe-thought pollution was noticed this way) — mitigated because the stale/count header survives and R0 deletes the pollution. If rejected, keep full texts but truncate each to ~120 chars.
- **Verify:** 17 live tests GREEN (they cover digest presence, think-gate block/clear, per-file consult — the full mechanical chain); tombstone unit test (remove → re-add → verify starts unverified); **text-matched stale-join unit test (F28: verdict recorded at old line must NOT attach to a different thought that drifted into that line)**; no-rewrite source-pin GREEN (F29 form); e2e receipt refreshed per guarded chunk; digest shows correct count after R0's probe-file deletions. **Round-3 hardening (optional):** add ONE live test for the tombstone lifecycle (think → remove → re-think → digest count + gate behavior) — the only think-anywhere mechanic with no live pin today.

**Why R6 runs BEFORE R1:** R1 extracts shared helpers from the think plugin — extracting from the already-slimmed file (reindex + rewrite helpers + dead hook gone, ~180 lines lighter) is less to port and avoids extracting code that R6 deletes. R6 needs only R0's 1.18.5 re-baseline as its live-test contract.

### R7 — Token-consumption optimization (~1 h, NEW round 3; fixes P9; census in Appendix C)

**Principle:** the harness is paid for in EVERY session — recurring per-session/per-edit costs dominate one-time refactor costs, so budget them mechanically. All items are tagged with their natural ride-along; none requires a standalone pass.

- **T1 — Startup contract: WORK.md-only, authoritative everywhere [rides R0 doc edits + R5 drift-pin].** AGENTS.md:3 STARTUP currently orders 4 doc reads (~15k tok literal); the live build-agent prompt (`.agents_prompts/build.md`) already says WORK.md-only (~3.5k tok). Fix AGENTS.md to match build.md and explicitly route META_HARNESS.md/guide through nav tools ON DEMAND (feature_020's raison d'être — the directive as written contradicts it). **Saves ~10–11k tok/session** vs AGENTS.md-literal. AGENTS.md is receipt-covered → receipt cycle. R5's drift-pin asserts AGENTS.md STARTUP == build.md STARTUP (single-source).
- **T2 — WORK.md diet [rides R0].** Scratchpad carries ~5 KB of DONE-feature debug history (feature_023 entries ×4, all `[x]`) into every session read. Prune rule: scratchpad keeps CURRENT/RECURRING content only; DONE-feature narratives live in their feature dirs (already true — scratchpad is the duplicate). **Saves ~1.5–2k tok/session.** Decision point, default: prune (history is in git + feature docs).
- **T3 — Nav-reminder deferral (F31) [rides R2's session_state or standalone 5-line edit].** If the first tool result belongs to a NAV tool, skip the reminder WITHOUT marking `navRemindedSessions` — it lands on the first non-nav result instead. Saves ~120 tok in nav-first sessions; stops teaching the already-taught.
- **T4 — Live-suite model pin (decision point, default: DEFER).** 22 `opencode run` invocations per live-suite execution = 22 full agent sessions (system prompt + AGENTS.md + tool schemas + harness injections + model loop ≈ 25–40 KB context each before output — Appendix C). `--model <cheap/fast>` on the test invocation would cut cost, but a weak model may never attempt the guarded edit → false-green risk (tests assert FILE STATE, which requires the attempt). The `--pure` A/B control + imperative prompts mitigate but don't eliminate. Recorded as an option for when the suite runs in CI; NOT default for local re-baselines (fidelity first — F14-mirrored was caught by real behavior).
- **T5 — Mechanical token budget pins [rides R5].** Static test: AGENTS.md ≤ 5 KB; digest builder output ≤ 1 KB (source-pin the cap constant post-S7); nav tip ≤ 0.5 KB; WORK.md ≤ 14 KB with a scratchpad ≤ 6 KB sub-budget. Prevents silent re-inflation — the P9 class becomes self-enforcing.
- **T6 — Documented, deliberately UNCHANGED:** gate ⛔ block messages stay verbose (fire on violation only; teaching value > token cost); e2e receipt pytest output per guarded-edit chunk (~200–400 tok + 30–60 s wall) is mitigated by the existing batch-edits gotcha, not by weakening the receipt; mvc_check subprocess per src edit is latency, not tokens.
- **T7 — WORK.md display = summary, not echo (F34) [rides R0 doc edits].** build.md:5 "Display to the user the current state of the WORK" invites a literal ~12.8 KB echo ≈ ~3.2k OUTPUT tok/session (output prices ~3–5× input). Fix: build.md specifies "summarize current state in ≤ 15 lines (in-progress / blocked / next)"; post-T2 diet makes the summary cheaper still. **Saves ~3k output tok/session.** Round-4 session used the summarized form as prior art.
- **T8 — Tool-schema diet (F33) [default: defer to R8's `@tool` single-source; standalone option recorded].** Tighten the 19 omt_* schema descriptions to one line each, detail moved into @doc/nav corpus (~40–60% cut ≈ 500–900 tok/turn). Standalone = edit 4 guarded plugin files (receipt cycles) — default: let R8 generate them budget-pinned instead. Consolidation 19 → ~7 tools is a separate decision point (R8/D6(a)), NOT default.
- **Verify:** T1/T2 doc edits green under R5's drift-pin; T3: live nav-reminder test adjusted (reminder absent after nav-first result, present after first non-nav result); T5 budget-pin test GREEN; Appendix C table re-measured and recorded in WORK.md.

### R8 — Machine-native harness language: OMT-HDL (~3–4 h, NEW round 4; full spec in Appendix D)

**Premise (user directive, round 4):** the harness's only consumers are the opencode plugins (mechanical enforcement) and an LLM agent (on-demand guidance) — **no human-readable artifact is required**. Today the source of truth is hand-synced Markdown (the P2 drift class: six audit rounds of path/singular drift) plus hardcoded TS tables (P1 duplication), both paid in tokens every session AND every turn (P9/F32/F33). R8 replaces the doc layer + enforcer tables with ONE dense line-oriented source — `.meta/META_HARNESS.omt` — compiled by `harnessc` (stdlib-only Python, ~250–300 LoC, `uv run`, no deps approval) into mechanical projections.

- **HDL-1 (this workstream):** language v1 + compiler + projections: (1) `.meta/.omt/harness.ir.json` — plugins load once at init; (2) GENERATED AGENTS.md ≤ 5 KB (dense, banner-marked, receipt-covered); (3) nav index for the 4 nav tools; (4) generated opencode.jsonc permission block (F35's class dies); (5) budget report that makes Appendix C self-maintaining. Plugins read IR for DATA (paths, patterns, windows, messages, tool descriptions); **gate LOGIC stays in TS**. R5's drift-pin zoo collapses into one test: `harnessc check --verify-projections`.
- **HDL-2 (R8b, ~2–3 h, separate approval):** `@gate`/`@pred` interpreter — the enforcer evaluates gates declaratively from IR, one gate at a time, 17 live tests GREEN per gate. Side-effect: gate semantics become unit-testable OUTSIDE opencode → live suite shrinks to thin-shim smoke (T4's real fix, C2 relief).
- **Every harness feature works mechanically from data:** NEVER/ALWAYS, phase gate, TDD two-hats, think-gate (`skip_ok=false` declarative), nav-gate, e2e receipt, MVC++ after-hook, think-anywhere (append-only/grep-truth — R6's semantics ARE the language's state model), navigation, budgets (compile-time), status, injections, escape hatch — map in Appendix D4.
- **Token wins:** AGENTS.md 4.8 → ~1.8 KB (per-turn, F33); schemas tightened + budget-pinned (T8); nav results are single ~40–80 tok records instead of 200–500 tok markdown sections; `@inject` budgets make C4/C5 compile-visible (F32 turns budget cuts into ×N-turn savings); the R0 singular-path census class becomes unrepresentable (paths are `@var`, single-sourced).
- **Sequencing:** after R2 (the module split is the interpreter seam); R5 still runs as the cheap interim. R8 absorbs F2/F17 root resolution (`@var` + ctx init) and makes R5/T5 pins compile-time.
- **Verify:** `harnessc check` green in CI; generated AGENTS.md diff-reviewed once then receipt-covered; 17 live tests GREEN; one live query per nav tool answered from the index; budget report recorded in WORK.md.
- **Decision points:** (a) tool consolidation 19 → ~7 (F33; permission/e2e churn vs mega-tool usability — live-verify with a tool-call success probe; **default: NO consolidation in HDL-1, descriptions only**); (b) gate-message short + `see=@doc` form vs C8's verbose teaching default (default: keep verbose first-offense, short on repeat — needs offense counting, defer to HDL-2); (c) AGENTS.md projection density (**default: dense tables, no prose** — per the no-human-readable-artifacts directive).

### Non-goals (explicit — do not let scope grow)
- No split of `omt_think.ts` beyond R6's deletions (post-R6 ~640 lines but cohesive: 5 tools over shared helpers; R1's shared-lib extraction is the only reuse win).
- No changes to `mvc_check.py` / `new_feature.py` (healthy, §1 — except new_feature.py:13's one-word comment fix in R0).
- No new dependencies, no opencode version change, no `dist/` reintroduction (deleted 2026-07-20, proven unused).
- No gate/rule semantics changes — refactor preserves behaviour; the ONLY intentional behaviour changes are: R4's fixes (rotation, omt_done, decision-point outcomes), R6's deletions (reindex tool removed — user-visible, decision point default delete; digest trigger moved `session.start`/first-result → `session.created` event; **round-3: digest CONTENT compacted per S7 — same trigger, smaller payload, decision point**), R1's `worktree`-based root resolution (F2/F17 — a latent-bug fix, not a semantic gate change), **R7's startup-directive narrowing (AGENTS.md 4-doc → WORK.md-only, matching the live build prompt — an instruction change, not a gate change) and T3 nav-reminder deferral**, and R0's doc/config/test drift corrections (incl. `plugin`-array removal, F14 — registration behaviour preserved, verified live).
- No rewrite of historical per-feature docs' `.opencode/plugin/` mentions (F16: frozen point-in-time records). **Round-3 precision: same freeze applies to the historical docstring in test_omt_enforcer_guard_source_pins.py:22–23 (F24) and, by NEVER-edit protection, to README.md (F25 — user hand-edits at leisure, drift-pin excludes it).**
- **R8 changes REPRESENTATION, not gate semantics** — HDL is data + projections; HDL-1 keeps all gate logic in TS (HDL-2 is separately approved and gated).
- **No hand-editing of generated projections** (AGENTS.md, opencode.jsonc permission block, nav index) — the compiler owns them; drift becomes a compile error, not a test failure. META_HARNESS.md / guide retirement is the LAST step of HDL-1, only after nav-from-index is live-verified.

## 4. Execution Protocol (per workstream)

0. **Executor reading budget (F36):** read ONLY the §3 R<n> block for your workstream + this §4 + Appendix B (~3–4k tok). §0 is the review record; §5/§6/Appendices A/C/D are context-on-demand. The full plan is ~13k tok and is NOT execution input.
1. `omt_phase{task_type:"refactor", phase:"Analysis", scope:"R<n> done definition", feature:"meta_harness_refactor"}`
2. Work in receipt-rebuild cycles for guarded files (`.opencode/plugins/*.ts`, `opencode.jsonc`): batch edits → `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q` → next batch. **Every plugin edit must conform to Appendix B** (module shape B2, hook signatures B4, tool definition B5); every structural plugin change closes with the B6 acceptance smoke.
3. tests/ edits (R0's feature_016 fix, R2's pin rewrite, R4's new tests) go through the canary: `omt_skip{reason:"...", scope:"tests"}` (logged; feature_021/022 prior art).
4. `omt_complete{feature:"meta_harness_refactor", advance_to:"Done"}` per workstream; update WORK.md line per completed R.
5. No `git commit` without explicit user request (NEVER rule); diff against baseline anchor **`a7163df`** for review.

## 5. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Plugin loader rejects lib imports or named exports | R1 first live check: `opencode run` + tool call per plugin before proceeding to R2 (F13: no doc evidence — live only) |
| Source-pin tests break under R2 (by design) | Planned pin rewrite to coarser contract anchors; count as R2 deliverable |
| e2e-receipt second-edit guard stalls multi-edit refactors | Receipt-rebuild cycles; batch each plugin's changes into minimal writes (Write-tool large-payload gotcha) |
| Think-gate on `omt_enforcer.ts` / `omt_think.ts` | `omt_think_list{path}` consult before each edit session; re-anchor TA: comments post-move |
| Behaviour drift under refactor | 17 live tests are the contract; they must stay GREEN per workstream, not only at the end |
| ~~Mixing with 30 uncommitted paths~~ | OBSOLETE (F/§0.1): committed as `a7163df`; baseline moved. ROUND-2 F15: tree dirty again (probe-marker duplication) — R0 reverts `omt_status.ts` via `git checkout`, plan-doc edit is this audit |
| opencode 1.18.5 behaves differently than audited 1.18.3 (F8) | R0 re-baselines live suite BEFORE any edit; diff failures against 2026-07-20 GREEN run; escalate on behavior change |
| Reindex fix touches an untracked, backup-less index (F12) | RISK DELETED (R6 S1): the rewrite path is removed, not repaired; one-time `.bak` snapshot taken for the historical record |
| `plugin`-array removal breaks tool registration (F14) | Official docs: local dir auto-loads, array is npm-only. R0 live-verifies all 19 `omt_*` tools + 17 live tests on 1.18.5 BEFORE the next edit; fallback = restore array with bare names |
| `event` hook doesn't fire headless (F18/R6 S3) | Hard live-verify gate in R6; fallback keeps the Tier 1c first-result digest (deletes only the dead `session.start` hook) |
| Tombstone model regresses C1 "re-added starts unverified" (R6 S1) | Latest-event-wins fold preserves C1 exactly (newer add-record beats tombstone; verdict reset); dedicated unit test remove → re-add → verify |
| Digest stale-count goes phantom after probe-file deletions (R6 S1) | Stale-count joins verdicts to LIVE grep hits only, **matched on normalized text not path:line (F28)**; verified in R6's digest check after R0 deletions + dedicated drift-misassociation unit test |
| Startup narrowing (R7 T1) makes an agent under-read process docs | Nav tools are the documented on-demand path (feature_020, already MANDATORY); the live build prompt already runs WORK.md-only today with no observed process failures — T1 aligns docs to proven reality, R5 pins the two startup sections equal |
| Compact digest (R6 S7) hides a thought the agent needed at start | Stale ⚠️ + per-file counts survive; D1 re-injects full texts point-of-use on first read of each file (the moment of need); `omt_think_list` one call away; decision point with keep-full-texts fallback recorded |
| Token budget pins (R7 T5) false-red on legitimate growth | Budgets set with ≥30% headroom over post-R7 measurements; pin failure message says "grow budget deliberately in the same commit" — the pin forces a conscious edit, not a hard ceiling |
| Verify verdicts misassociate after line drift (F28) | R6 S1 join on normalized text + drift-misassociation unit test; `path:line` demoted to display key |
| HDL compiler/projection bug silently weakens a gate (R8) | HDL-1 keeps gate LOGIC in TS (data-only extraction); `harnessc check` validates schema/refs/budgets; 17 live tests + receipt stay the contract per chunk; HDL-2 migrates one gate at a time |
| Generated AGENTS.md too dense for the agent to follow (R8 decision point c) | @doc/@msg payloads stay natural language; AGENTS.md keeps NEVER/ALWAYS + pointers; first generated diff is human-reviewed before adoption; fallback = raise density budget |
| Tool consolidation degrades agent tool-use (F33/R8 decision point a) | Default is descriptions-only tightening (T8); consolidation requires a live tool-call success probe (one call per tool + 17 live tests) before adoption |

## 6. Effort Summary

R0 ~1h (expanded ×2: round-2 config removal, round-3 WORK.md/README/hygiene items) · **R6 ~1.5h (think-anywhere simplification; S7 digest compaction rides it)** · R1 ~1.5h · R2 ~3h (S6 bootstrap consolidation rides it) · R3 ~1h · R4 ~1h (shrank — reindex moved to R6 as deletion) · R5 ~30m (grew slightly: R7 T1/T5 drift+budget pins ride it) · **R7 ~1h (NEW round 3 — token budget; mostly ride-alongs, standalone residue ≈ T3 + measurement; round-4 T7/T8 ride R0/R8)** · **R8 ~3–4 h (NEW round 4 — OMT-HDL-1 machine-native language, Appendix D; HDL-2/R8b ~2–3 h separately approved)** → **~13.5 h total** (+4 h round 4 — the language workstream; buys the per-turn floor cuts F32/F33 and deletes the P2 drift class by construction).

Sequencing: **R0 → R6 → R1 → R2 → (R3 ∥ R4 ∥ R5) → R7-residue**. R6 before R1 so the shared lib extracts from the already-slimmed think plugin; R3/R4 mutually independent and both independent of R2; R6 needs only R0's 1.18.5 re-baseline as its live-test contract; R7's doc items (T1/T2) ride R0/R5, its digest item (S7) rides R6, its injector consolidation (S6) rides R2 — only T3 (5-line enforcer edit + live-test adjust), T5 measurement, and the Appendix C re-census run as a small standalone tail after R2 (they touch files R2 has just settled). **R8 after R2 settles** (the module split is the interpreter seam; HDL-1 reads data from R2's lib modules, HDL-2 replaces their internals one gate at a time); R8b gated on R8 live-green + separate approval.

---

## Appendix A — Audit method (2026-07-25)

**Round 1:** Reproducible commands used for every verdict above: `git status/log/show`, `wc -l` on all 7 source files, targeted greps (duplication map, singular-path refs, THOUGHT_PATTERN, UNLOCK_WINDOW, isOmtHarness), full static suite (`uv run pytest tests/ -m "not opencode_live"` → 7 failed/973 passed/40 s), harness subset (→ 68 passed/17 deselected), feature_016 failure root-cause run, e2e receipt JSON inspection, `omt_think.ts:657–760` reindex source read, `git log` on `thoughts.jsonl` (untracked), `opencode --version` (1.18.5).

**Round 2 (same day):** full-drift census `grep -rn '\.opencode/plugin/'` over `.meta/` (77 hits; live-vs-historical split per F16) + both plugin sources (enforcer 0 hits; status :361, nav :259) + `new_feature.py`:13; feature_016 test read directly (Path-parts form, lines 97/105/112/116); `THOUGHT_PATTERN` grep over `tests/` (0 hits) + line reads enforcer:252–257 / think:34–41; e2e receipt JSON re-read (covered_files=10, passed_at 22:50Z); full static suite re-run (7 failed/973 passed/17 deselected/38 s — exact F6 match); `git ls-files .meta/.omt/` (empty → F23); `git diff` on the dirty tree (F15 duplicated marker); enforcer state-container grep (:328/:333/:341/:472/:473 → F20); think-plugin structure grep (`recordConsult` :144 ledger-backed, `reconcileIndex` :100 rewrite, `digestSessions` :795, `session.start` :804, tool map :801, verify anchor-basis :546–556, grep-is-truth declaration :659); e2e pin lines (`test_omt_harness_e2e.py`:190/:200 → F22); official opencode plugin documentation (user-provided — distilled into Appendix B): plugins dir plural + auto-load, `plugin` array npm-only (F14), ctx `{project, client, $, directory, worktree}` (F17), event list without `session.start` + generic `event` hook + `session.created` (F18), plugin-functions-only export model (F19), before-hook `output.args` example (confirms F14-MIRRORED fix).

**Round 3 (same day):** repo-wide singular census `grep -rn '\.opencode/plugin/'` (99 hits incl. README ×5, WORK.md:86, test docstring ×2 — F24/F25/F26); per-file live-set breakdown via `awk|uniq -c`; `git diff` F15 line precision (markers at :368/:370); e2e receipt re-read (passed_at now 23:09Z — re-run between rounds, covered_files unchanged); full static suite 3rd run (7 failed/973 passed/17 deselected/39 s — exact F6 match); `hasConsultedThoughts` direct read (enforcer:217–247 — F21 confirmed); `fileThoughtsIn`/`thinkGateDecision` reads (think-gate NOT skip-bypassable — AGENTS.md claim structurally confirmed, block at :1032 consults no skip state); after-hook emission-site reads (:1041–1099 — nav reminder unconditional-first-result → F31; D1 dedup per file); `writeFileSync` census in omt_think.ts (:24 import, :108/:751 index rewrites, :405/:489 legitimate target-file writes → F29 pin correction); `thoughts.jsonl` full read (verify record keyed `main_screen.py:79` carrying live `:81`'s text → F28; 4 add-records, 0 usable anchors → S1b evidence); `.agents_prompts/build.md` read (startup = WORK.md-only, contradicting AGENTS.md:10 → F30); live-test invocation census (`grep -c` → 22 `opencode run` sites, no `--model` flag → R7 T4); byte-size census `wc -c` on AGENTS.md/WORK.md/META_HARNESS.md/guide/build.md (4.8/12.8/13.2/27.4/0.3 KB → Appendix C); root listing (`OMT_SESSION_STATE_feature_023*.md` ×2 → F27); ledger re-measure (109,329 B).

---

## Appendix B — Official opencode plugin build contract (authoritative; user-provided doc, 2026-07-25)

Binding build rules for every plugin edit in R0/R1/R2/R6. Items marked **[repo-pinned]** are harness-specific facts pinned by the live suite, consistent with (not from) the doc.

### B1. Placement & loading
- **Project plugins:** `.opencode/plugins/*.ts|js` (PLURAL) — auto-loaded at startup. **Global:** `~/.config/opencode/plugins/`. No config entry required for either.
- The config `plugin` array lists **npm packages only** (installed via Bun at startup, cached in `~/.cache/opencode/node_modules/`). Local directory plugins MUST NOT be listed there (F14).
- Load order: global config → project config → global plugin dir → project plugin dir. Duplicate npm name+version loads once; a local plugin and an npm plugin with similar names load **separately**.
- Local-plugin npm deps: `.opencode/package.json` at the config dir root; opencode runs `bun install` at startup. **[repo-pinned: already present]**

### B2. Module shape (the loader contract)
- A plugin module exports **one or more plugin FUNCTIONS**. Each function receives the plugin context and returns a hooks object:
  ```ts
  import type { Plugin } from "@opencode-ai/plugin"
  export const MyPlugin: Plugin = async ({ project, client, $, directory, worktree }) => {
    return { /* hooks + optional tool map */ }
  }
  ```
- **[repo-pinned]** Harness convention: `export default async () => ({...})` and **ALL named exports must be functions** — non-function named exports break the loader (WORK.md gotcha, consistent with the doc's "plugin functions" model; guarded by `test_no_named_exports_except_default`).
- Shared constants/helpers live OUTSIDE `plugins/` (e.g. `.opencode/lib/`) and are imported — plain Bun module resolution. **This is what makes R1/R2 legal.**

### B3. Plugin context & repo-root
- ctx = `{ project, client, $, directory, worktree }`: `directory` = current working directory; `worktree` = git worktree path; `$` = Bun shell API; `client` = opencode SDK client.
- Harness repo-root resolution: **`worktree ?? directory`** (F17) — never `process.cwd()`, never bare `directory`.

### B4. Hooks used by the harness (signatures)
- `"tool.execute.before": async (input, output) => …` — `input = {tool, sessionID, callID}`; tool args on **`output.args`** (doc's env-protection example). **[repo-pinned: F14-MIRRORED]** Throwing blocks the call (hard gate).
- `"tool.execute.after": async (input, output) => …` — tool args on **`input.args`**; `output = {title, output, metadata}` only. **[repo-pinned: F14]** Mutating `output.output` appends to the tool result (digest/injection path).
- `event: async ({ event }) => …` — generic subscription. Doc event list: `command.executed`; `file.edited`, `file.watcher.updated`; `installation.updated`; `lsp.client.diagnostics`, `lsp.updated`; `message.part.removed/updated`, `message.removed/updated`; `permission.asked/replied`; `server.connected`; **`session.created`**, `session.compacted/deleted/diff/error/idle/status/updated`; `todo.updated`; `shell.env`; `tool.execute.after/before`; `tui.prompt.append/command.execute/toast.show`; `experimental.session.compacting`.
- There is **NO `session.start` event** — a `"session.start"` hook is dead code (F18; omt_think.ts:804 is the instance R6 deletes).
- Logging: `await client.app.log({body:{service, level, message, extra}})` — NOT `console.log`.

### B5. Custom tools
- `import { type Plugin, tool } from "@opencode-ai/plugin"`; define with `tool({ description, args: { k: tool.schema.string() /* Zod */ }, async execute(args, context) { … } })`; return the map as `{ tool: { name: def } }` from the plugin function.
- `execute` returns a **plain string** **[repo-pinned: DEFECT-D]**; `context` exposes `directory`/`worktree`.
- Name collision: a plugin tool **overrides** the built-in tool of the same name.
- **[repo-pinned]** opencode.jsonc `permission` keys are the tool names (`"omt_think": "allow"`, …); adding/removing a tool = config edit (receipt cycle) + e2e pin update (canary).

### B6. Acceptance smoke (mechanical, after ANY plugin-structure change)
1. `opencode run --format json "<prompt invoking one tool per plugin>"` → all 19 `omt_*` tools (18 post-R6) register and execute.
2. 17 live tests GREEN (`uv run pytest tests/scripts/omt -m opencode_live`).
3. E2e receipt refresh: `uv run pytest tests/scripts/omt/test_omt_harness_e2e.py -q`.

---

## Appendix C — Token-consumption census (round 3, 2026-07-25; ~4 chars/token estimate)

The harness pays these costs EVERY session (or per event). Ordered by avoidable magnitude.

| # | Cost item | Mechanism / evidence | Size today | Post-R7 target | Disposition |
|---|---|---|---|---|---|
| C1 | Startup doc reads | AGENTS.md:10 STARTUP = 4 docs (WORK 12.8 KB + AGENTS 4.8 + META_HARNESS 13.2 + guide 27.4 ≈ 58 KB ≈ ~15k tok); build.md says WORK.md-only (F30 contradiction) | ~10–11k tok avoidable (META+guide; WORK needed, AGENTS already in system prompt) | ~3.5k tok (WORK.md only; docs on-demand via nav tools) | R7 T1 — fix AGENTS.md; R5 pins equality |
| C2 | Live suite execution | 22 `opencode run` invocations (`test_omt_live_opencode_guards.py`), each a full agent session ≈ 25–40 KB context before output; no `--model` pin | ~0.6–0.9 MB context processed per full live run | unchanged (fidelity) or cheap-model pin | R7 T4 — DEFERRED (false-green risk); scope runs to guarded changes (already the receipt practice) |
| C3 | WORK.md scratchpad bloat | ~5 KB of DONE-feature debug history (feature_023 ×4 entries) read every session | ~1.5–2k tok/session | ≤ 6 KB scratchpad budget | R7 T2 prune rule + T5 budget pin |
| C4 | TA session digest | Full thought texts (cap 30) on first tool result (omt_think.ts:764–787); today 8 thoughts ≈ 1.4 KB | ~300–400 tok/session, worst case ~1.1k | ~80–150 tok (compact: counts + stale + pointer) | R6 S7 — decision point, default compact; D1 covers point-of-use |
| C5 | Nav reminder | ~0.45 KB appended to FIRST tool result unconditionally (enforcer:1049–1054) — fires even nav-first (F31) | ~120 tok/session | 0 in nav-first sessions (deferred, not dropped) | R7 T3 |
| C6 | D1 per-file thought injection | ~0.4–0.6 KB per thought-carrying file, once per file per session (enforcer:1076–1093) | ~120–160 tok × files read | unchanged | KEEP — this is the feature working as designed (point-of-use > digest) |
| C7 | E2e receipt refresh per guarded-edit chunk | `pytest -q` output ~200–400 tok + 30–60 s wall per cycle; a 4-plugin refactor ≈ 8–12 cycles | ~2–4k tok + ~10 min per refactor | unchanged (batch edits — existing gotcha) | KEEP — documented, T6 |
| C8 | Gate ⛔ block messages | Verbose multi-line remediation text, on violation only | ~150–400 tok per violation | unchanged | KEEP — teaching value > token cost, T6 |
| C9 | omt_status tool output | Phase/unlock/artifact/TDD/WORK next-task JSON-ish blob | ~1–2 KB per call | unchanged | KEEP — called on demand only |
| C10 | Process (non-token) costs, recorded for completeness | `hasConsultedThoughts` full-ledger parse per gated edit (F21, 109 KB); `fileThoughtsIn` grep per edit; `mvc_check` subprocess per src edit (~0.5–1.5 s); digest full-repo grep per session | latency, not tokens | ledger 64 KB cap (R4) bounds the worst of it | R4 already; no R7 item |
| C11 | omt_* tool schemas in system prompt (F33) | 19 schemas ≈ 4.5–6 KB, paid EVERY model turn incl. sessions that never touch the harness (omt_think alone ≈ 0.9 KB) | ~1.1–1.5k tok/turn ≈ 33–45k tok/session at 30 turns (≈3–4.5k cache-attenuated) | ≤ 0.6k tok/turn (tightened, budget-pinned); ~0.4k if consolidated | R7 T8 / R8 `@tool`; decision point: 19→7 consolidation |
| C12 | History-residency multiplier (F32) | conversation-resident injections (C4/C5/C6/C8/C9) re-paid every subsequent turn: cost ≈ size × (N − t₀), N≈30 assumed | turns C4's ~350 tok into up to ~10k tok/session; C5's ~120 into ~3.5k | multiplier is API reality — SHRINK THE PAYLOADS (true saving ~10–14k tok/session) | R6 S7 + R7 T3 (strengthened); terse TA: texts |
| C13 | WORK.md display at startup (F34) | build.md:5 "Display … current state of the WORK" — literal echo = 12.8 KB assistant output | ~3.2k OUTPUT tok/session (output ≈ 3–5× input price) | ≤ 15-line summary ≈ ~300 output tok | R7 T7 |

**Net today (typical session, AGENTS.md-literal):** ≈ 12–15k tok of harness overhead before the first line of work — **round-4 correction: that was the first-turn figure. Turn-adjusted (N≈30, cache-attenuated) ≈ 20–35k tok/session incl. C11/C12/C13.**
**Post-R7 (same session):** ≈ 4–5.5k tok first-turn, ≈ 8–12k turn-adjusted — a ~60–65% cut, with C6/C8/C9 (the costs that BUY safety) untouched.
**Post-R8:** the per-turn floor (AGENTS.md projection + schema layer) roughly halves again; nav queries drop to single records. R8's budget report re-measures this table mechanically — the census becomes self-maintaining.
**Budget pins (T5/T8):** AGENTS.md ≤ 5 KB · digest ≤ 1 KB · nav tip ≤ 0.5 KB · WORK.md ≤ 14 KB (scratchpad ≤ 6 KB) · **tool-schema set ≤ 2.5 KB (compile-enforced post-R8)** — the P9 class becomes self-enforcing.

---

## Appendix D — OMT-HDL v0: a machine-native language for the meta harness (round-4 proposal, R8)

### D0. Premise & design goals

The meta harness serves exactly two consumers: the opencode plugins (mechanical enforcement) and an LLM agent (on-demand guidance). **Neither requires human-readable artifacts.** The Markdown sources (META_HARNESS.md 13.2 KB + guide 27.4 KB + AGENTS.md 4.8 KB ≈ 45 KB) are the root of both remaining disease classes: P2 hand-sync drift (F3/F4/F5/F9/F14/F16/F25/F26 — four audit rounds of path drift) and P9 token overhead (C1/C11). OMT-HDL replaces them with ONE dense line-oriented source, compiled to projections. Human readability becomes a compile target (the AGENTS.md projection), never a source property.

Goals: (1) **one fact, one line, one place**; (2) **grep-native** — `grep '^@gate '` lists all gates (the feature_020/021 retrieval philosophy applied to the harness itself); (3) **closed kind vocabulary**, mechanically validated; (4) every harness feature expressible as **data**, so it works mechanically; (5) **token budgets enforced at compile time**; (6) stdlib-only tooling (`uv run scripts/omt/harnessc.py` — no deps approval).

### D1. Grammar (complete)

```
line    := blank | comment | record
comment := '#' … EOL
record  := '@' kind SP id (SP attr)* (SP ' : ' payload)? EOL
attr    := key '=' (bare_token | "quoted string")
id      := [a-z][a-z0-9_]* ('.' [a-z0-9_]+)*        # globally unique, immutable, grep-addressable
kind    := version | var | deny | protect | always | phase | fsm | hat | pred | gate
         | msg | state | inject | doc | budget | tool | flow | xref
payload := free text to EOL (natural language allowed; '@id' tokens = cross-refs, compiler-checked)
```

Parse = `shlex.split` per line (stdlib). No nesting; no expressions outside the closed `@pred` vocabulary. A record's meaning is fully determined by `(kind, attrs)`; payloads carry the teaching layer.

### D2. Kind schemas (v1, closed)

| Kind | Attrs | Replaces today |
|---|---|---|
| `@version` | `n` | — |
| `@var` | payload = value | scattered constants: plugin_dir, unlock_window (8h), ledger/state/receipt paths (P1; F2/F17 repo-root = ctx-derived `worktree ?? directory`, set at init, not a var) |
| `@deny` | `match="regex"`, `msg=@msg.*` | NEVER command rules (git commit\|push, pip…) — enforcer regexes AND opencode.jsonc bash denies, single-sourced |
| `@protect` | `path="glob"`, `msg=@msg.*` | NEVER path rules (.env*, README.md, uv.lock, LICENSE) |
| `@always` | `run="cmd"` or `glob="…"` | ALWAYS rules (git log/status, META.md per dir) |
| `@phase` | `applies="tt,…"`, `requires="decl[,design]"` | §12 artifact matrix rows |
| `@fsm` | `states="A,B,…"`, `initial`, `auto_on="tt@phase,…"` | TDD state machine |
| `@hat` | id = `fsm.state`, `allow="glob,…"`, `revert_on` | two-hats cells (RED→tests/, GREEN/REFACTOR→src/) |
| `@pred` | payload = one builtin from the closed set below | gate conditions, currently hand-coded TS |
| `@gate` | `on=before|after|event:<name>`, `tools="a|b"`, `paths="glob"`, `when=@pred.*`, `requires=@pred.*`, `msg=@msg.*`, `hard|soft`, `skip_ok=true|false`, `order=n` | the 7 enforcer concerns as data: phase gate, TDD hats, think-gate (`skip_ok=false` — round-3's structural confirmation becomes declarative), nav-gate, receipt guard, MVC++ after-hook, protected files |
| `@msg` | `sev=block|warn|info`, `see=@doc.*`, payload | ERR_/WRN_ tables + enforcer string literals |
| `@state` | `path=@var.*`, `mode=append|rotate`, `cap`, `window`, `truth` | ledger.jsonl (`rotate`, 64 KB — R4), thoughts.jsonl (`append-only`, `truth="grep TA:"` — R6 S1's semantics ARE the language's state model) |
| `@inject` | `on=first_tool_result|event:session.created|file_read`, `budget`, payload = template | nav tip (C5/T3), TA digest (C4/S7 — F32 makes the budget the ×N control knob), D1 per-file injection (C6); ONE injector per trigger — S6's consolidation is the language default |
| `@doc` | `tags="…"`, payload | META_HARNESS.md sections + guide content — the nav corpus (SECTION_/XREF_/QUICK_ markdown tags die) |
| `@budget` | `target`, `max` | T5/T8 pins — compile-time, not test-time |
| `@tool` | `perm=allow|ask|deny`, `args="k?,…"`, `budget`, payload = one-line description | plugin tool maps + opencode.jsonc permissions (F35's class dies: the block is GENERATED, all 19 explicit) + schema text (F33/T8, budget-pinned) |
| `@flow` | payload = `step; step; …` | QUICK_ workflows (omt_quick_ref corpus) |
| `@xref` | payload = `@id` | XREF_ aliases |

Closed `@pred` vocabulary (each maps 1:1 to an enforcer builtin; NO eval):
`path_in(glob|@var)` · `cmd_match(@deny.*)` · `ledger_has(kind, k=v, window)` · `session_flag(name)` / `!session_flag(name)` · `file_has("lit")` · `receipt_fresh()` · `fsm_allows(@fsm.*, path)` · `risk_high()`

### D3. Compiler & projections (`harnessc`, ~250–300 LoC, stdlib-only)

- `harnessc check` — per-kind attr schema · id uniqueness · ref closure (every `@id` mention resolves) · pred vocabulary · budget feasibility · `--verify-projections` (committed outputs == recompiled) — **the ONE drift test replacing R5's pin zoo; P2 becomes a compile error**.
- `harnessc build` — emits:
  1. `.meta/.omt/harness.ir.json` — plugins load once at init (gates, preds, msgs, state, budgets, tools).
  2. `AGENTS.md` — GENERATED (`# GENERATED FROM .meta/META_HARNESS.omt — do not edit`): dense NEVER/ALWAYS/gates/tools/quickref ≤ budget; receipt-covered.
  3. `.meta/.omt/nav.index.jsonl` — id-keyed @doc/@flow corpus; nav tools answer single records (~40–80 tok vs 200–500 tok markdown sections); omt_nav.ts shrinks to index lookup (markdown tag scraping deleted).
  4. opencode.jsonc permission block between `// harnessc:begin/end` markers (from `@tool perm=` — all 19 explicit; F35 fixed by construction).
  5. `harness.report` — byte sizes vs budgets → Appendix C self-maintaining (round-5 audits stop hand-measuring; feeds F32's real-N measurement).

### D4. Feature-mechanical map (the "all features work mechanically" contract)

| Harness feature | HDL mechanism |
|---|---|
| NEVER / ALWAYS | @deny/@protect/@always → gate `g.protect` eval; opencode.jsonc bash denies GENERATED from the same records |
| Phase gate | @phase rows + `@gate(phase, requires=ledger_has(phase,…,8h))` |
| TDD two-hats | @fsm + @hat cells + `@gate(tdd, requires=fsm_allows)`; tdd_check.py reads the same IR |
| Think-gate | `@gate(think, when=file_has("TA:"), requires=ledger_has(think_consult,…), skip_ok=false)` |
| Nav-gate | `@gate(nav, tools="grep|glob", paths=@var.doc_paths, requires=session_flag(nav_used))` + `@inject` nav tip |
| E2e receipt | `@gate(receipt, requires=receipt_fresh)`; covered_files = @var (F9's alignment-bug class dies) |
| MVC++ after-hook | `@gate(mvc, on=after, run="uv run scripts/omt/mvc_check.py", hard)` |
| Think-anywhere | @state.thoughts(`mode=append`, `truth="grep TA:"`) + `@inject` digest (budget per S7/F32) + D1 = `@inject(on=file_read)` |
| Navigation | @doc/@flow/@xref corpus → compiled index → the 4 nav tools |
| Budgets | @budget compile-enforced (T5/T8 become build errors) |
| omt_status | renders IR + @state files — its duplicated path/ledger logic (P1) dies |
| Escape hatch | omt_skip appends to @state.ledger; gates declare `skip_ok` — ESC_ as data |

### D5. Token model (why this is the lever)

- **Per-turn floor (F33):** AGENTS.md 4.8 KB → ~1.8 KB dense projection; 19 schemas ~4.5–6 KB → ≤ 2.5 KB budget-pinned. Combined ≈ ~1.5k tok/turn saved (× N turns, cache-attenuated).
- **Per-query:** nav results = single records ~40–80 tok vs markdown sections 200–500 tok (~70% cut × queries/session).
- **Per-session (F32):** `@inject` budgets make C4/C5 compile-visible — every budget cut is a ×N-turn saving, not a one-time saving.
- **Drift-tax elimination:** four audit rounds of path/singular drift (P2) cost audit + fix cycles; single-sourced `@var` + generated projections make the class unrepresentable.

### D6. Migration & honesty notes

- **HDL-1 (R8, ~3–4 h):** compiler + `META_HARNESS.omt` v1 (all kinds; @gate/@pred data-only) + projections + plugins READ IR for data (gate logic stays TS) + `check --verify-projections` as the sole drift test + generated AGENTS.md adopted after one human diff-review.
- **HDL-2 (R8b, ~2–3 h, separate approval):** @gate/@pred interpreter in the enforcer, one gate at a time, 17 live tests GREEN per gate; gate semantics become unit-testable OUTSIDE opencode → live suite shrinks to thin-shim smoke (T4's real fix, C2 relief).
- **LLM-comprehension risk: low.** The envelope (`@kind id k=v`) is INI/YAML-adjacent — any LLM parses it; @doc/@msg payloads stay natural language; the agent's normal contact is compiled projections + nav records, never raw source; the agent never hand-writes HDL (the compiler validates).
- **What HDL does NOT do:** change any gate semantics (HDL-1), touch mvc_check/new_feature, add dependencies, or require an opencode version change. META_HARNESS.md/guide retirement is the LAST step of HDL-1 — content migrates to @doc first, retirement only after nav-from-index is live-verified.
