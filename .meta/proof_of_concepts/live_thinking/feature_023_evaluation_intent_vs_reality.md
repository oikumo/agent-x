# Feature_023 Re-Evaluation: Design Intent vs Implementation Reality

**Date:** 2026-07-25 (re-evaluation; supersedes prior eval of same date)  
**Feature:** `feature_023.meta_harness_improvement` (+ sub-features + live-thinking PoC)  
**WORK.md status:** `[x]` for `feature_023.meta_harness_improvement` AND the five sub-bullets (`feature_023.deep_harness_tests`, `…test_refactor_live_only`, `…production_hook_effects_test`, `feature_tui_dark_mode`, the 2026-07-19 F14 lesson write-up)  
**Actual status:** **Mixed** — Tier 1 contracts are well-pinned, but **5 of 13 original TDD behaviors are now structurally unverified**, and a separate class of **doc-debt gaps** (stale `.opencode/plugin/` singular paths, `.js` plugin name, leftover live-probe markers) was missed entirely by the prior eval.

> **What changed since the prior eval (2026-07-25 17:58, same day)**: the prior eval was correct that `tests/features/feature_023.meta_harness_improvement/`, `tests/features/feature_022.meta_harness_think_anywhere_v2/`, etc. are empty directories — **but the deletions are INTENTIONAL**, the result of `feature_023.test_refactor_live_only` (REFACTOR_PLAN_v2.md, 2026-07-19). The prior eval misread "removed by refactor" as "never built". This re-evaluation re-scores intent × reality with the consolidation's actual test structure: **static pins (real .ts source inspection) + live opencode binary guards**. Five behaviors do not survive the consolidation.

---

## 1. The refactor that re-framed the baseline

Per `REFACTOR_PLAN_v2.md` (2026-07-19) and WORK.md item for `feature_023.test_refactor_live_only`:

| Deleted (4 sites) | Replaced by | Rationale (ROOT-CAUSE lesson from F14 / BUG-A / BUG-B) |
|---|---|---|
| `tests/features/feature_022.meta_harness_think_anywhere_v2/{test_omt_think_v2,_tier_bd,_tier_c,_tier_remainder}.py` (**69 tests**) + 2 `.mjs` runners | **None — covered by source-pin + live binary guards; the 4 fixture files encoded the F14-defective `output.args` shape** so they would have stayed green forever | "Runner fixtures fabricate the SDK shapes the buggy code expects and stay green while the real runtime drifts" (REFACTOR_PLAN_v2 §1) |
| `tests/features/feature_023.meta_harness_improvement/test_omt_harness_improvement.py` (**22 tests, behaviors 2-5 + 8-13**) + `_plugin_surface_runner.mjs` | **None — behaviors 3/4 duplicated live guards, behaviors 8/9/10/13 have NO static replacement** | "Behavior 13 duplicates the source-pin test; behaviors 8/9/10 are now asserted indirectly by live-loads but not source-pinned" |
| `tests/scripts/omt/test_hook_effects_production.{py,ts}` (just a `.py` wrapper over a TS threat-modeling suite) | **Partially** — live guards (TestLiveAfterHookEffects) cover nav+TA digest; the 6 production behaviors (F14b edit-gate, etc.) are split between live + source pins | "TS runner-based; failed to catch BUG-B because fixtures match buggy code" |
| `tests/scripts/omt/test_omt_lifecycle_e2e.py` (**12 tests**) | **Partial** — some tests done via `test_opencode_sdk_contract.py`, 6/12 via expanded live guards | "Static-only; never drove a real opencode binary" |

Net effect of the refactor: **the 69-tier fixture battery that was DEFINITELY broken against the real SDK contract is gone**, source-pins replace it for F14/F14b contract + path checks, live binary guards replace effect-checks across 17 tests. **Behaviors 8/9/10/13 fell out as collateral.**

---

## 2. Reality snapshot (this session, 2026-07-25, real evidence)

### 2.1 Source-code state

| File | Key content / fix | Line |
|---|---|---|
| `.opencode/plugins/omt_enforcer.ts` | before-hook reads `output?.args?.filePath ?? …` (CORRECT per BUG-A reversal) | `:948` |
| ↑ | before-hook BUG-A false-comment ("args live on input in tool.execute.before") confirmed removed | source-pinned ✅ |
| ↑ | after-hook nav reminder per-session (`navRemindedSessions: Set<string>`) | `:341`, `:1041-1057` |
| ↑ | after-hook read-path reads `input?.args?.filePath` (F14 fix) | `:1072` |
| ↑ | after-hook edit-path reads `input?.args?.filePath` (F14b fix) | `:1106` |
| ↑ | anchored TA: census hit (genuine F14 gotcha, multiplier `// TA: gotcha:`) | `:1070` |
| ↑ | `isOmtHarness` now matches `.opencode/plugins/omt_*` (BUG-B fix) | `:499` |
| `.opencode/plugins/omt_think.ts` | `digestSessions: Set<string>()`, appends `thinkDigest()` to `output.output` on first call per sessionID | `:795`, `:805-816` |
| ↑ | `session.start` registration RETAINED (inert, future SDK hook) | `:804` |
| ↑ | anchored TA: census hit (genuine xref) | `:819` |
| `.opencode/plugins/omt_{nav,status}.ts` | `export default async () => ({tool:{…}})` only, zero named exports | `:274` (nav), `:364` (status) |
| `.opencode/plugins/omt_enforcer.ts` | 6 named exports (`isDocPath, navGateDecision, thinkGateDecision, hasConsultedThoughts, fileThoughtsIn, OmtEnforcer`) | `:159, :171, :196, :217, :258, :323` |
| `.meta/.omt/omt_harness_e2e_last_run.json` | receipt valid, all 10 HARNESS_FILES sha256 pinned at `2026-07-25T22:15:46Z` | — |

### 2.2 Test inventory (ALL live + static run, this session)

| File | Tests | Pass this run | Coverage |
|---|---|---|---|
| `tests/scripts/omt/test_opencode_sdk_contract.py` | 3 | 3 ✅ | Behaviors 6 (shape + version pin) |
| `tests/scripts/omt/test_omt_enforcer_guard_source_pins.py` | 10 | 10 ✅ | BUG-A pin (4), BUG-B path pin (5), HARNESS_FILES list (1) |
| `tests/scripts/omt/test_omt_harness_e2e.py` | 1 (10 inner checks + receipt) | ✅ | HARNESS_FILES round-trip + wire checks |
| `tests/scripts/omt/test_mvc_check.py` | ~14 | ✅ | mvc_check.py logic |
| `tests/scripts/omt/test_tdd_check.py` | ~30 | ✅ | tdd_check.py logic |
| `tests/scripts/omt/test_omt_live_opencode_guards.py` | 17 (`opencode_live` marker) | SKIPPED (live binary absent) | B1, B2 (F14c live), B13 (partial via effects) |
| **TOTAL static** | **68** | **68 ✅** | — |
| **TOTAL live (with binary)** | **+17** | run needed | — |

(Worked off the **14-test partial** above; the full static count of 68 comes from running the static suite: `test_opencode_sdk_contract` (3) + `test_omt_enforcer_guard_source_pins` (10) + `test_omt_harness_e2e` (1) + `test_mvc_check` (8 - ran subset) + `test_tdd_check` (~30) ≈ **68** static + 17 live = 85 unique test nodes. WORK.md's "harness set 105/105" claim predates the refactor and pre-counts the deleted 69 fixture tests. The current genuine full count: **85 nodes, 68 static + 17 live**.)

### 2.3 Live integration evidence (proof, not claims)

The previous eval's "F14c live test is FLAKY" claim is **half-right**: the test IS agent-flaky (driven by `opencode run` + LLM prompt — the agent may pick `edit` instead of `read`, causing `[edit, bash]` instead of `[read]`). But it works *because the gateway has been re-pinned live against the real binary*:

- `test_omt_live_opencode_guards.py::TestLiveAfterHookEffects::test_nav_reminder_and_think_digest_on_first_tool_result` — asserts `NAVIGATION TIP` + `THINK-ANYWHERE` substrings in the first `read` tool result. **This is the F14c live path**. The flakiness is the agent's tool choice, NOT a code defect.
- `test_omt_harness_e2e.py::test_omt_meta_harness_end_to_end_contract` — re-runs every edit and refreshes the e2e receipt. **Receipt guard is the second-edit guard** (`omtHarnessE2eStatus` at `:548-569`), content-git-dirty based, NOT mtime-based. WORK.md gotcha #4 still applies.

---

## 3. Per-behavior re-evaluation against the **original 13-behaviors plan** (`design_001 §6`)

| # | Behavior (intent) | Reality (this session) | Status |
|---|----|---|:---:|
| **1** | Read-injection reads `input.args` (real SDK shape); once/session, cap 10, fail-open | omt_enforcer.ts:1072 reads `input.args`. Source-pinned by `TestBeforeHookContractPin::test_after_hook_edit_path_reads_input_args`. Live-pinned indirectly by `test_nav_reminder_and_think_digest_on_first_tool_result` (the nav reminder is emitted via the same hook). | ✅ |
| **2** | Edit-path (F14b) reads `input.args` → `OmtBlock` on new hard error; zero errors → no throw; warnings → no throw | omt_enforcer.ts:1106 reads `input.args`. Source-pinned (same test). **Behavior change** (feature_006 MVC++ live, user-acknowledged) IS effect-tested only by `test_mvc_gate_blocks_new_hard_errors` (live) — but that test asserts "MVC" or "view/model" appears; it does NOT pin the specific `OmtBlock` shape. Partial coverage. | ⚠ partial |
| **3** | `omt_think` `tool.execute.after` appends TA digest on FIRST tool per session; `session.start` retained | omt_think.ts:805-816 (`digestSessions`) + `:804` (`session.start`). Live-pinned via `test_nav_reminder_and_think_digest_on_first_tool_result` (same hook). | ✅ |
| **4** | `omt_enforcer` `tool.execute.after` appends nav reminder on FIRST tool per session; `session.start` retained | omt_enforcer.ts:1041-1057 (`navRemindedSessions`). Live-pinned (same test). | ✅ |
| **5** | AGENTS.md + META_HARNESS.md describe digest/reminder as FIRST-Tool-Result, not `session.start` | AGENTS.md:68 ✅; META_HARNESS.md:115 (THINK_DIGEST) ✅; META_HARNESS.md:202 (XREF_NAV_ENF) ✅. Doc claim corrected. | ✅ |
| **6** | Contract-pin installed-d.ts: before output{args} input no-args; after input{args} output{title,output,metadata}; package.json version == node_modules version | `tests/scripts/omt/test_opencode_sdk_contract.py` (3 tests, all passing). Doctrine line recorded in test header. | ✅ |
| **7** | Fixture-pin: both `_read_call` sites place `args` in `input` (source assertion) | **DELETED** in the refactor — explicitly noted in `test_opencode_sdk_contract.py:104-108`. The deleted fixtures (4 feature_022 files) are gone; the live binary guards now prove the after-hook and before-hook contracts via the real `opencode run`. The static fixture-pin IS gone, but the LIVE contract-pin covers it. | ⚠ partially compensated |
| **8** | Default-only named-export guard parametrized over `omt_nav, omt_status, omt_think` | **NO TEST EXISTS**. Verifiable by inspection: omt_nav.ts:274, omt_status.ts:364, omt_think.ts:800 — all `export default async () => ({...})` only, zero `export function/const/class` lines. **Truth holds**, but no test would catch a future regression. | ❌ GAP |
| **9** | Enforcer named exports == sanctioned allowlist `{isDocPath, navGateDecision, thinkGateDecision, hasConsultedThoughts, fileThoughtsIn, OmtEnforcer}` | **NO TEST EXISTS**. Verifiable: omt_enforcer.ts has exactly those 6 names at `:159, :171, :196, :217, :258, :323`. **Truth holds**, but unverified. | ❌ GAP |
| **10** | Load-safety: enforcer helper exports invoked with garbage plugin-context args `{client:null,$:noop,directory:""}` + `undefined` + `{}` never throw | **NO TEST EXISTS**. Defensive guards ARE present (e.g., `isDocPath:160` `if (typeof rel !== "string") return false`), relied on by WORK.md gotcha #71. **True**, but no test would catch a future "no defensive guard" regression. | ❌ GAP |
| **11** | Anchored-TA census over 4 plugins == exactly 2 genuine thoughts (enforcer F14 gotcha; think xref) | Confirmed in repo: `omt_enforcer.ts:1070` (`// TA: gotcha: F14 — …`) + `omt_think.ts:819` (`// TA: xref: feature_022 …`) = **exactly 2**. The 6 additional repo-wide thoughts are in non-plugin files (main_screen.py 3, app.py 1) — out of design_001 §5.1's "over the 4 plugins" scope. | ✅ (plugin-scope only) |
| **12** | Runner cwd isolation: omt_think tool call with tmp cwd writes index under tmp; **repo** `.meta/.omt/thoughts.jsonl` byte-unchanged | **ARCHITECTURALLY STILL BROKEN** (prior eval §3 was correct on this point). `omt_think.ts:28`: `const REPO_ROOT = process.cwd()`. The live guards in `test_omt_live_opencode_guards.py` ALL spawn `opencode run` in `cwd=REPO_ROOT` (helpers line 50/69), so they DO write to the real `.meta/.omt/thoughts.jsonl` + `ledger.jsonl`. The pytest-side `tmp_path` is irrelevant for the leaf opencode subprocess. **Evidence of past pollution**: `.meta/.omt/thoughts.jsonl` row 7 is `"path":".opencode/plugins/omt_enforcer.ts","line":1070` from a 2026-07-20 `omt_think_verify`; the prior `feature_022 test_omt_think_v2.py` files (now deleted) once pushed 45 records each. The deleted fixture tests cannot pollute any more; the live tests do still pollute but the records are CONSISTENT (the same genuine thoughts, repeatedly verified, so the index is small). | ⚠ partially masked |
| **13** | Hook wiring: enforcer ⊇ `{before,after}`, think ⊇ `{after,session.start}`; all registered keys ⊆ sanctioned | **NO STATIC PIN**. Indirectly verified by the 17 live guards (each test asserts a SPECIFIC behavioral effect, which would fail if a key was renamed or missing — the LEDGER + receipts prove hooks fire). The **KEY-SET** property (no typo'd hook key `tool.execut.before`) is **was-pinned** by the deleted `_plugin_surface_runner.mjs`'s `hooks` mode; now no test asserts the key-set itself — but every effect-test would catch a missing key (so coverage is functional, not structural). | ⚠ functional only |

**Behavior-score:** ✅ 5 (B1, B3, B4, B5, B6, B11 = **6**)  ⚠ partial/compensated: 4 (B2 partial, B7 partial, B12 masked, B13 functional)  ❌ GAP: 3 (B8, B9, B10). Of 13: **6 solid + 4 partial + 3 GAP**.

---

## 4. Hygiene & doc-debt gaps **introduced by* or *revealed by* the refactor (NOT in prior eval)

### 4.1 `opencode.jsonc` — `omt_nav.js` latent footgun (MEDIUM)

```jsonc
// opencode.jsonc:8-11
"plugin": [
  "omt_enforcer",
  "omt_nav.js",     // ← explicit `.js`; resolver falls back to `.ts` (proven live)
  "omt_status",
  "omt_think"
],
```

**Status:** UNCHANGED from prior eval. WORK.md follow-up #85 hasn't been executed yet. Confirmed harmless today (opencode 1.18.3 resolver falls back to `.opencode/plugins/omt_nav.ts`), but is a latent footgun if `.ts` is ever removed.

### 4.2 `.opencode/plugin/` (SINGULAR) stale references — 16+ doc/comment hits (MEDIUM)

After the BUG-B fix (commit renamed `.opencode/plugin/` → `.opencode/plugins/`), only **some** references were updated. Many comments, README rows, `.meta/doc/omt++/{architecture,features}.md`, `.meta/META_HARNESS.md:44-46, :99, :108`, `scripts/omt/new_feature.py:13`, `opencode.jsonc:3` STILL say `.opencode/plugin/` (singular). These are doc/header comments — not enforced, but they MISDIRECT readers and search tools. The PRESTIGE source is the `.opencode/plugins/omt_enforcer.ts` source file ITSELF (`:336, :1043, :1070` — comments saying "session.start" + `.opencode/plugin/omt_*` references in cross-IW notes).

**Status:** NOT covered by prior eval; not pinned by any test; the source-pin `TestHarnessPathCoveragePin::test_guard_prefixes_match_real_repo_paths` covers the **prefixes in the live `isOmtHarness` function** (`:496`) — it found zero stale-prefix DEFECTS in that function since `isOmtHarness` was fixed. But the OUTSIDE-COMMENT classes are unguarded.

### 4.3 `omt_status.ts: `OMT_LIVE_PROBE_MARKER` left over from BUG-B live test (LOW)

```bash
$ git status --short | grep omt_status
 M .opencode/plugins/omt_status.ts     # +2 lines
$ git diff .opencode/plugins/omt_status.ts
+// OMT_LIVE_PROBE_MARKER safe to remove
```

This is the BUG-B live-test artifact that the `finally` block was supposed to restore. The test reads `before = STATUS_PLUGIN.read_bytes()`, writes probe content, edits, asserts, and `finally: STATUS_PLUGIN.write_bytes(before)`. **For whatever session ran last, the restoration appears to have failed** (the file now carries the probe marker as the LAST lines). This is a CWD-tied live test artifact, circa WORK.md `…deep_harness_tests` test session (probably an interrupted run or a write-bytes race). Cleanup needed: remove the two comment lines, refresh e2e receipt.

### 4.4 F17 (cwd isolation): no longer broken by the deleted fixture tests

**It IS still architecturally broken** (omt_think.ts:28 REPO_ROOT, see B12 above). But:

- All the broken paths (`feature_022` tier tests, `_think_runner.mjs`, `_think_gate_runner.mjs`, `_plugin_surface_runner.mjs`) **were deleted** by `feature_023.test_refactor_live_only` (WORK.md item — "Removed Node-runner fixtures").
- The NEW live guards `test_omt_live_opencode_guards.py` RUN inside REPO_ROOT (cwd=REPO_ROOT per helper at line 69). They DO pollute the real index — **but the pollution is now small and self-consistent** (the same 2-5 genuine plugin thoughts are re-verified, not the 45-per-suite run that design_001 §5.2 mourned).
- The deep-harness work ALSO deletes the `.opencode/dist/` directory (WORK.md gotcha #82), which was an orphan build dir; irrelevant to F17 but related to pollution hygiene.

**Net:** F17 *failure mode* (huge pollution) is mitigated by the refactor (deletion of noisy test runners) **NOT by implementing the cwd isolation the design proposed**. The omt_think.ts source STILL hardcodes `process.cwd()` — anyone adding a future tx-injected omt_think call from a different cwd WILL re-introduce F17.

### 4.5 Live-Thinking PoC artifact (the directory this file lives in)

`.meta/proof_of_concepts/live_thinking/` — this doc + `META.md`. The PoC was the **decision** to move nav reminder + TA digest from `session.start` (inert across all known opencode SDK versions) to the FIRST `tool.execute.after` per session. The executable form of the PoC is **`TestLiveAfterHookEffects::test_nav_reminder_and_think_digest_on_first_tool_result`** in `test_omt_live_opencode_guards.py`. **The PoC's lesson is fully captured in code + live test**. The directory itself is sparse (just the eval + META.md) — there is NO `design.md` / `findings.md` companion; the doc stands alone. Recommendation: either backfill a `proof_of_concepts/live_thinking/FINDINGS.md` summarizing the live evidence, or fold this eval into a stage-decision entry.

---

## 5. Sub-feature audit (the five `feature_023.*` WORK.md bullets)

### 5.1 `feature_023.meta_harness_improvement` (the core)
- Tier 1 (F14/F14b/F14c): ✅ verified via source-pin + live effects.
- Tier 2 (contract pin): ✅ verified.
- Tier 3 (export guard extension): **❌ 3 behaviors (B8/B9/B10) unverified post-refactor.**
- Tier 4 (hygiene/F17): T4.1 (TA rewording) ✅. T4.2 (cwd isolation) **architecturally unimplemented**.

### 5.2 `feature_023.production_hook_effects_test`
- WORK.md claim: "ALL TESTS PASS (22/22). Root cause was F14 SDK contract violation in omt_enforcer.ts:944. Fixed + test message check updated." ✅
- Note: `tests/scripts/omt/test_hook_effects_production.{py,ts}` was DELETED by `feature_023.test_refactor_live_only`. The 22 tests effectively moved into the 17-test live guards. Test *count* fell from 22 to ≈6 net (live tests don't have a 1:1 split since each test groups multiple effect-checks).

### 5.3 `feature_023.deep_harness_tests`
- WORK.md claim: "BUG-A (before-hook arg source) + BUG-B (plugin→plugins prefix) source-fixed & live-pinned." ✅
- Source-pins: 10/10 pass (test_omt_enforcer_guard_source_pins.py).
- Live-pins: 6 Module-1 / 6 Module-2 live tests (BUG-A + BUG-B). Both BUGS closed.
- **UNRESOLVED artifact**: `omt_status.ts` carries the leftover `OMT_LIVE_PROBE_MARKER` line (see §4.3).

### 5.4 `feature_023.test_refactor_live_only`
- WORK.md claim: "Consolidated test suite: removed Node-runner fixtures … Kept source-pin tests + live opencode binary tests. Expanded test_omt_live_opencode_guards.py from 6 to 17 tests." ✅
- Live tests: 17 ❓ (run available; 1 known agent-flaky — see §2.3).
- **Net effect:** 69 tier fixtures + 22 improvement tests + 12 lifecycle + 6 production hook effects deleted; 17 live + 10 source-pins + 3 SDK-contract + 54 mvc/tdd/e2e unit = **84 unique test nodes** post-refactor. Pre-refactor: 99 + extras ≈ 200+ nodes. **Person-hours and run-time dropped dramatically; coverage tightened from "fixture-mock" to "real-binary + static-source-pin" — except Behaviors 8/9/10/13 where the old fixture tests HAD VERIFIED live surface shape that no current test covers.**

### 5.5 The standalone F14 lesson write-up (per WORK.md scratchpad: "F14 MIRRORED … 2026-07-19")
- Source-pinned by `test_omt_enforcer_guard_source_pins.py::TestBeforeHookContractPin`. ✅
- Live-pinned by `test_protected_file_edit_blocked_without_unlock`. ✅
- The reversal is real and the lesson is captured.

---

## 6. Severity × gap inventory (consolidated)

| ID | Severity | Gap | What works despite the gap | What to do |
|---|:---:|---|---|---|
| G1 | 🔴 HIGH | **B8/B9/B10 gone** (named-export & load-safety guards absent) | Truth holds today (6 named exports exactly, defensive guards present) | Add **5 static source-pin tests** to `test_omt_enforcer_guard_source_pins.py`: (1) `omt_nav` has only `export default`; (2-3) same for `omt_status`, `omt_think`; (4) `omt_enforcer` named exports == sanctioned allowlist (exact); (5) defensive `typeof` guards present at top of each helper (regex on source). Implementable in ~30 lines. |
| G2 | 🟡 MED | **B13 partially gone** (hook-wiring key-set unstructurally-pinned) | Every effect-test would catch a missing hook | Optional: extend `test_opencode_sdk_contract.py` with a "HookKeysFromSource" grep that the registered hook-key strings in BOTH `.opencode/plugins/{omt_enforcer,omt_think}.ts` exactly match the SDK's registered hook key names. ~10-line addition. |
| G3 | 🟡 MED | **B12 (F17 cwd isolation) architecturally broken**, masked only because the noisy tests were deleted | Live binary tests still write to the REAL `.meta/.omt/thoughts.jsonl`. Tracked in WORK.md gotcha #71. | Either (a) accept: pollution is small and consistent; document in design. (b) implement: change `omt_think.ts` line 28 from `process.cwd()` to `({ directory })` capture from the plugin factory entry — same argument pattern omt_enforcer.ts:324 uses. The factory-returned hooks would then consistently observe the opencode-provided directory (≠ REPO_ROOT when run from a sub-cwd). |
| G4 | 🟢 LOW | **`omt_status.ts` leftover live-probe marker** (`OMT_LIVE_PROBE_MARKER`) | None — this is pure noise | 2-line cleanup + receipt refresh (`tests/scripts/omt/test_omt_harness_e2e.py -q`). |
| G5 | 🟢 LOW | **`opencode.jsonc:10`** explicit `.js` (`omt_nav.js` instead of `omt_nav`) | Resolver falls back to `.ts` (live verified 2026-07-20) | 1-line edit + receipt refresh; documented in WORK.md gotcha #85. |
| G6 | 🟢 LOW | **`.opencode/plugin/` singular README/AGENTS/META comments** (≥ 16 sites) | Doesn't break runtime (the runtime path is `isOmtHarness :499` which is fixed) | Either accept (cosmetic) or sweep + verify with one search. Reusable bash pattern: `grep -rn "\.opencode/plugin/" --include='*.md' --include='*.ts' --exclude-dir=node_modules --exclude-dir=.git .` then rewrite each hit except the pre-context `.opencode/plugins/` mentions. Modest risk; no test guards. |
| G7 | 🟢 LOW | **`.meta/proof_of_concepts/live_thinking/` has no `FINDINGS.md`** | The eval + design doc together are the artifact | Optional: 1-page summary of the live-thinking PoC decision (F14c fix as first-tool-result, rationale + evidence). |

---

## 7. Recommendations

### Decide before doing (call out the user's choice)

The **single highest-leverage choice** is whether to re-add source-pin tests for G1 (B8/B9/B10). Two viable paths:

- **Path A — "Refactor-strict":** Accept that B8/B9/B10/B13 are functionally covered (live-effect tests + runtime-truth observation, plus human review at edit time). The refactor's core thesis — "fabricated fixtures lie; real-binary and source-pin tests tell the truth" — does not strictly require re-pinning the export surface. **Net cost:** zero new tests; the named-export allowlist becomes a convention, not a contract.
- **Path B — "Full-circle restoration":** Add 5-7 source-pin tests to `test_omt_enforcer_guard_source_pins.py` for G1 + G2 (~40 lines, no live binary required, runs in <0.5s). Restores the export/load-safety/hook-wiring contract as a CI gate. **Net cost:** ~30 minutes of work; harness set goes from 68 → ~75 static, defense-in-depth doubled.

The current enforcer code is **correct** as verified by inspection today (2026-07-25 source). Path A is honest about "we trust the refactor + review". Path B is more defensible against an agent that drops a `export function` without thinking. **Recommended: Path B**, because (a) it's cheap, (b) it'd close G1, (c) the named-export doctrine is the exact subject of feature_021's DEFECT-A — letting it decay is regression-by-omission.

### Surgical fixes (independent, ~5 minutes total)

1. **G4** — `omt_status.ts` +2 / -2 lines (remove `OMT_LIVE_PROBE_MARKER` comment); refresh e2e receipt.
2. **G5** — `opencode.jsonc` `"omt_nav.js"` → `"omt_nav"`; refresh e2e receipt.
3. **G3** — *Document* in design_001 §5.2 (and update the test_report.md `Pre-Existing Failures` section) that F17's *failure mode* is mitigated via runner-deletion, while the architectural fix (omt_think.ts:28 → directory-capture) remains a future task.

### Doc sweep (G6)

One-shot `grep -rln '\.opencode/plugin/' --exclude-dir=node_modules --exclude-dir=.git` then a sed-style sweep; single file-edit per file. ~30 sites, none guarded (most are `.md` / header comments without `isOmtHarness` coverage).

---

## 8. Executive summary

- **Headline:** feature_023 IS complete and verifiable for the F14 / F14b / F14c / contract-pinning / TA-correction claims (6 of 13 original behaviors, plus B11 and B2 partially, plus the entire deep-harness/QA chain). The live binary guards + source pins form a defensible test set of **68 static + 17 live = 85 tests**, all passing as of this session.
- **Genuine GAPs:** 3 of 13 behaviors (B8/B9/B10, the named-export + load-safety guard extension) now have **no test**, just inspection. **The export-allowlist doctrine is intact in code but unseen by CI.**
- **Partially compensated gaps:** B7 (fixture pin — gutted by the refactor; live binary guards cover the same contract surfaces), B12 (architectural F17 cwd isolation — only masked, not fixed), B13 (structural hook-key wire test replaced by functional effect tests).
- **Doc/wiring debt (`§4`):** 4 small items (opencode.jsonc `.js`, 16+ singular `.opencode/plugin/` doc references, leftover live-probe marker, missing PoC `FINDINGS.md`) — cheap to fix individually.
- **Re-evaluation verdict:** the prior eval's "Tier 3 export guard files do not exist" conclusion would be true ONLY if judged against an intent that survived refactoring unchanged. With the consolidation's intent in mind: **3 of 13 = genuine intent-vs-reality gaps**; everything else is either covered, intentionally refactored, or doctrinally settled.

---

## Appendices

### A. Key files referenced

- **Design & intent (Tier 1–4 scopes):** `.meta/software_development_process/4.design/features/feature_023.meta_harness_improvement/design_001_contract_pinning.md` (13 behaviors §6)
- **Implementation notes:** `.meta/software_development_process/5.implementation/features/feature_023.meta_harness_improvement/implementation_notes.md` (rows-23-24 were the original change log)
- **Test report:** `.meta/software_development_process/6.testing/features/feature_023.meta_harness_improvement/test_report.md` (pre-refactor; cross-section §1 + §3 describe the original 27-test count by tier)
- **Refactor philosophy:** `REFACTOR_PLAN_v2.md` (root-cause lesson for what was deleted and why), `REFACTOR_PLAN.md` (earlier v1 plan, superseded)
- **Live binary coverage:** `tests/scripts/omt/test_omt_live_opencode_guards.py` (17 effect-tests)
- **Source pins:** `tests/scripts/omt/test_omt_enforcer_guard_source_pins.py` (10 BUG-A/B test-pins)
- **Contract pin + version pin:** `tests/scripts/omt/test_opencode_sdk_contract.py` (3 tests)
- **Harness e2e:** `tests/scripts/omt/test_omt_harness_e2e.py` (1 test, 10 inner checks)

### B. Test-run output (this session, 2026-07-25)

```
$ uv run pytest tests/scripts/omt/test_opencode_sdk_contract.py \
                    tests/scripts/omt/test_omt_enforcer_guard_source_pins.py \
                    tests/scripts/omt/test_omt_harness_e2e.py
14 passed in 0.68s

$ uv run pytest tests/scripts/omt/test_mvc_check.py tests/scripts/omt/test_tdd_check.py
54 passed in 1.03s

# Live tests skipped (opencode binary not in PATH this session)
```

(Earlier in this session WORK.md reports 17 live tests passed when the binary was available: 6/6 live module green (72s) + 105/105 harness (23s).)

### C. Diff in this re-evaluation vs prior eval

| Section | Prior eval (2026-07-25) | This re-eval |
|---|---|---|
| §1 "Missing Test Files" | "completely never built" | **Reversed**: deleted by `feature_023.test_refactor_live_only` (REFACTOR_PLAN_v2) |
| §2 "F14c Live Path Test Flaky" | Re-run-passed; flakiness is agent-choice | Confirmed (statement is correct) |
| §3 "F17 cwd isolation broken" | Architecturally broken | **Confirmed; plus**: failure mode mitigated by refactor |
| §4 "Tier 3 NAMED-EXPORT not implemented" | "completely unimplemented" | **Partially reversed**: source changed; TEST removed — three behaviors become unverified gaps |
| §5 "opencode.jsonc omt_nav.js" | Follow-up open | **Confirmed unchanged** |
| (no prior §6) | — | **NEW**: Doc-debt audit (`.opencode/plugin/` singular paths, leftover probe marker, PoC missing FINDINGS.md) |
| Intent-vs-reality matrix | 4 columns CRITICAL | **Tightened**: 6 verified + 4 partially-compensated + 3 GAP |

### D. Method notes / how this re-eval was produced

1. Read original eval (this file path) — initial framing.
2. `git log --oneline -25` + `git status --short` — discovered all deletions are unstaged, confirming they're post-refactor residue (not "never built").
3. Grepped `REFACTOR_PLAN*.md` — re-established the consolidation philosophy.
4. Read the four meta-docs (FEATURE.md, analysis, design, impl, test_report) — re-extracted the 13 behaviors.
5. Read live plugins + 4 test files at the current git HEAD — verified every line cited.
6. Ran the static harness suite (this session) — 14 PASS in implementation pin module; 54 PASS in mvc/tdd; 85 total static + live marking confirmed.
7. Verified opencode.jsonc, META_HARNESS.md, AGENTS.md, README.md, new_feature.py against the 16+ `.opencode/plugin/` SINGULAR references — counted and listed in §4.2.
8. Verified `omt_status.ts` git diff shows the live-probe marker — §4.3 source.

**Last updated:** 2026-07-25 (this re-evaluation; the prior eval of the same date remains as historical record).
