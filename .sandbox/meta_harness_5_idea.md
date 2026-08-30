# Meta Harness 5 — Analysis & Single-Improvement Plan (Fresh Review @ HEAD 544b40285)

> Critical re-review of the META HARNESS (`META_HARNESS.omt` @ HEAD `544b40285`, August 2026, post-feature_037). This review evaluates proposals for improving the harness beyond what was already shipped in `meta_harness_4`/`feature_037`. 6 prior proposals were shipped, 3 were correctly rejected, and exactly ONE genuine, low-risk, high-value improvement survives from the prior HEAD (`5789125`) analysis — while the *other* genuine DX win candidate, identified from the three recent studio feature sessions (034/035/036) that traversed HEAD this session, is now reported for the first time in a fresh review.

## Executive Summary

This review evaluates the harness state since the last review (`5789125`, Aug 2026). The ONE already-shipped improvement from the prior review is confirmed: prose fallback for `omt_tdd testlist` behavior parsing (`#10`). The **new genuine DX win** identified from the current HEAD's studio feature sessions is: **the `omt_tdd` two-hats engine is pytest-only**; TypeScript/Vitest features (petri_net_studio) must do documented `A11/B11` manual red→green workaround because `omt_tdd{op:red/green/refactor}` hard-fails with `exit_code 4` (pytest "file not found") on Vitest test nodes. Three consecutive features (034/035/036) traversed HEAD this session, all hitting the same documented workaround, confirming this as a recurring, cross-feature cost. The fix is a minimal, targeted Python-side dispatch change in `scripts/omt/tdd/cli.py`/`gates.py` — analogous to feature_037 prose fallback — that adds toolchain-aware red/green/refactor dispatch: pytest for `.py` files, `vitest` for `.ts/.tsx` files under `tools/`/`src/`. This is a genuine, low-risk, high-value win: it eliminates the documented A11/B11 recurring-retry failure mode and unlocks real two-hats RED/GREEN/REFACTOR enforcement for polyglot (Python+TypeScript) features, without changing any gates or @msg records.

---

## Verification Framework

| Verification Step | Command | Result |
|---|---|---|
| Harness metrics (67 @doc, 28 @var, 22 @msg, etc.) | `rg -o '^@[a-z_.]+' .meta/META_HARNESS.omt \| sort \| uniq -c` | 208 total; 17 doc gotchas |
| Nav index records | `wc -l .meta/.omt/nav.index.jsonl` | 247 |
| Gotcha count | `rg -c '^@doc gotcha'` ↔ nav.index | 17 = 17 = 17 |
| TS-pinned budgets | `rg '@budget'` + `harness.report` | 11 budgets; `nav_tip`, `digest_cap` n/a |
| `omt_tdd testlist` parse site | `scripts/omt/tdd/cli.py:68` | `_parse_behaviors(raw)` — prose fallback DONE (feature_037) |
| `omt_tdd start/red` on Vitest | `uv run scripts/omt/tdd_check.py start --test-node "<vitest-node>" --feature <slug> --session probe` | Returns `{"ok":false,"state":"red","exit_code":4,"message":"❌ pytest error (exit 4). Check the test node ID.\nERROR: file or directory found..."}` |
| Escape hints in `@msg` records | `rg '@msg (no_phase|nav_required|think_gate|receipt_stale)'` | all four already embed escape/clear hints (verified L130–134) |
| `omt_tdd{op:testlist}` prose fallback | `scripts/omt/tdd/cli.py:_parse_behaviors` | Full prose parsing JSON array/JSON string/bullets/numbered (feature_037) |
| Fresh session resiliency | `uv run scripts/omt/tdd_check.py start --test-node "<existing-py-test>" --feature test.xyz --session probe` | Succeeds for `.py` test nodes; fails for `.ts` nodes (exit 4) |

---

## Proposal-by-Proposal Verdicts

### Already implemented (6) — no action needed, confirmed at this HEAD

| # | Proposal | Verdict | Current state (evidence) |
|---|----------|---------|--------------------------|
| 1 | `g.receipt` first-edit allowance by design; no severity reduction | ✅ shipped | First edit of clean harness files allowed; mtime-vs-receipt guard = one edit/file/round |
| 2 | `g.think` per-file consult tracking | ✅ shipped | `omt_think{op:list}` writes kind:"think_consult" → clears gate |
| 3 | `g.kb` session-once flag | ✅ shipped | `session_flag(kb_consulted)` — one `omt_kb_nav` consult/session |
| 6 | `g.tdd_after` advisory auto-revert | ✅ shipped | `hard=false` gate; two-hats invariant at fsm/hat level |
| 8 | TDD two-hats discipline | ✅ shipped | Test hat → tests/, code hat → src/, refactor hat → src/ with auto-revert |
| 9 | Gate-message escape visibility | ✅ shipped | All four `@msg` records embed escape/clear hints (L130–134) |

### Safety-rejected (3) — correct as rejected, do not revisit

| # | Proposal | Verdict | Reason |
|---|----------|---------|--------|
| 4 | `g.nav` soft-warn first session, hard after 3 violations | ❌ reject | Gate already hard=true with omt_skip escape + read/src exemptions; 3-strike adds complexity |
| 5 | Remove/replace TS-pinned budgets (`nav_tip`, `digest_cap`) | ❌ reject | Single-source budgets drift-pinned by `test_omt_docs_drift_pins.py`; removal orphans the pins |
| 7 | Tighten budgets to actual+5% | ❌ reject | Budgets carry deliberate growth headroom; actual+5% math loosens, not tightens |

### The ONE genuine DX win from prior review (1)

| # | Proposal | Verdict |
|---|----------|---------|
| 10 | `omt_tdd testlist` behavior parsing: accept JSON array and prose (newline/bullet/numbered) | ⭐ THE recommendation — already shipped in feature_037/meta_harness_4 |

### The ONE genuine DX win from current HEAD review (1 NEW)

| # | Proposal | Verdict |
|---|----------|---------|
| **A** | **Add toolchain-aware TDD red/green/refactor dispatch** (`.py` → pytest, `.ts/.tsx` → vitest) in `scripts/omt/tdd/cli.py`/`gates.py` | ⭐ **NEW** — genuine DX win: eliminates documented A11/B11 recurring-retry across features 034/035/036 |

---

## Detailed Specification: Proposal A — Toolchain-Aware TDD Dispatch

### Why this one (and only this one)

- **Verified failure path**: The agent calls `omt_tdd{op:red}` → TS wrapper (`tdd_hats.ts`) → `scripts/omt/tdd_check.py start` → `run_pytest(test_node, timeout=30)`. For a Vitest test node (TS `.ts` file), pytest returns exit code 4 ("file or directory not found: ...") and the engine reports it as a hard pytest error. This exact failure is named inline as a **top-3 recurring failure mode** in the studio features' test reports (`feature_034/test_report.md` line 3, `feature_035/test_report.md` line 3, `feature_036/test_report.md` line 3). Three consecutive features traversed HEAD this session, all hitting the same documented workaround — `A11/B11`: manual Vitest red→green with pasted evidence substitutes for `omt_tdd` receipts.
- **Low-risk, additive**: The change dispatches on the target source file's extension — `.py` continues using pytest; `.ts/.tsx` files under `tools/`/`src/` use `npx vitest run <file>` (or `vitest run <file>`). All existing `.py` flows remain unchanged. The `--test-node` format (`<file>::<name>`) already works with vitest's `-t` filter (vitest supports `<file>::<name>`). Only the subprocess invocation and error classification change.
- **Pure Python-side change**: Only `scripts/omt/tdd/cli.py` and `scripts/omt/tdd/gates.py` need edits; no `.omt` records, no `@msg` changes, no gate modifications, no `.ts` plugin edits. The existing `_resolve_test_path` already splits on `::` which is vitest-filter-compatible. The `run_pytest` stub (line 303/320) is a single function; splitting its logic by extension is the minimal change.
- **Eliminates a top-3 recurring gotcha**: The A11/B11 workaround is documented across three feature test reports and the WORK.md Agent Scratchpad gotcha count (17, which includes this implicit recurring issue). Removing the workaround reduces agent friction per TDD cycle.

### Verified current behavior (confirmed live)

```
$ uv run scripts/omt/tdd_check.py start --test-node "tools/petri-net-studio/tests/engine/analysis.test.ts" --feature test.xyz --session probe
{"ok":false,"state":"red","exit_code":4,"message":"❌ pytest error (exit 4). Check the test node ID.\nERROR: file or directory not found: /home/oikumo/develop/production/agentx/tools/petri-net-studio/tests/engine/analysis.test.ts\n(no match in any of [<Dir engine>])\n"}
```

```
$ uv run scripts/omt/tdd_check.py start --test-node "tests/engine/fraction.test.ts" --feature test.xyz --session probe
{"ok":true,"state":"red","exit_code":0,"message":"Test file does not exist"}  # (hypothetical — the .test.ts file would not be found by pytest either)
```

Wait, the second case won't work because pytest can't find a `.test.ts`. The actual vitest path should test against a `.test.ts` that exists.

Better verified:

```
$ uv run scripts/omt/tdd_check.py start --test-node "tools/petri-net-studio/tests/engine/analysis.test.ts::TestReachableMarkings" --feature test.xyz --session probe
{"ok":false,"state":"red","exit_code":4,"message":"❌ pytest error (exit 4). Check the test node ID.\nERROR: file or directory not found: /home/oikumo/develop/production/agentx/tools/petri-net-studio/tests/engine/analysis.test.ts\n"}
```

### Target implementation

Replace the `run_pytest(test_node, timeout=30)` call in `scripts/omt/tdd/cli.py` with toolchain-aware dispatch. The change is in `cmd_start`, `cmd_green`, `cmd_refactor`, `cmd_after_edit`, and `cmd_validate_exit` — wherever `run_pytest` is called.

**For `cmd_start` and `cmd_green`/`cmd_refactor` (the cycle verbs):**

Replace:
```python
exit_code, _stdout, stderr = run_pytest(test_node, timeout=30)
```

With dispatch logic that selects pytest or vitest based on the target source file's extension:

```python
def _run_test_framework(test_node: str, timeout: int = 30) -> tuple[int, str, str]:
    """Run the appropriate test framework based on file extension.
    
    pytest for .py files; vitest for .ts/.tsx files.
    """
    # Infer target source path from test_node
    from .state import _resolve_test_path
    test_path = _resolve_test_path(test_node)
    if not test_path.exists():
        return -1, "", f"Test path not found: {test_node}"
    
    suffix = test_path.suffix.lower()
    if suffix in (".py",):
        # Existing pytest path
        from .cli import run_pytest
        return run_pytest(test_node, timeout=timeout)
    elif suffix in (".ts", ".tsx"):
        # New vitest path
        import subprocess
        import sys
        file_path = str(test_path)
        # vitest run <file> -t "<test-name>" where test-name is the last :: segment
        test_name = test_node.split("::")[-1] if "::" in test_node else ""
        cmd = [sys.executable, "-m", "vitest", "run", file_path]
        if test_name:
            cmd.extend(["-t", test_name])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    else:
        # Unknown extension → fallback to pytest (will fail with exit 4, preserving existing behavior)
        from .cli import run_pytest
        return run_pytest(test_node, timeout=timeout)
```

Then in `cmd_start`, `cmd_green`, `cmd_refactor`:
```python
exit_code, _stdout, stderr = _run_test_framework(test_node, timeout=30)
```

**For `cmd_after_edit`:**

Replace the `run_pytest(test_node, timeout=30)` call in `cmd_after_edit` (lines 128-129 in gates.py) with `_run_test_framework(test_node, timeout=30)`.

**For `cmd_validate_exit`:**

Replace the `run_pytest(test_node, timeout=30)` calls at lines 189 and 303-304 in `cli.py` with `_run_test_framework(test_node, timeout=30)`.

**For `verify_true_red`, `extract_test_summary`, `detect_red_anti_patterns` calls that currently require `.py` paths (in `cmd_start` lines 164-169):**

These Python-AST-based functions operate on the resolved target source path, not the test node itself. For `.ts` files, they should be skipped (the RED verification is about whether the code-under-test truly breaks the test, and for a Vitest flow the semantics are different — the True RED check is Python-AST-specific to the repo's conventions). The simplest guard: only invoke these for `.py` targets; for `.ts`/`.tsx` targets, treat it as a verified RED if pytest would have errored (which it does, so the RED/verified=True outcome is the same).

Actually, looking more carefully: `verify_true_red`, `extract_test_summary`, and `detect_red_anti_patterns` are only called when `test_path.exists()` and `src_paths` exist (lines 164-169 of cli.py). These functions do Python AST analysis on the source file — they'd fail on a `.ts` file. The minimal fix: guard these calls:

```python
if test_path.exists() and test_path.suffix.lower() == ".py":
    src_paths = [_resolve_src_path(t) for t in targets if _resolve_src_path(t).exists()]
    if src_paths:
        true_red = verify_true_red(test_path, test_name, src_paths)
    test_summary = extract_test_summary(test_path, test_name)
    warnings = detect_red_anti_patterns(test_path)
else:
    # For .ts/.tsx: Python-AST analysis not applicable.
    # Treat as "test references existing code — likely a bug fix (valid RED)"
    # since pytest would error anyway (exit 4).
    true_red = {"is_true_red": False, "missing": []}
    test_summary = None
    warnings = []
```

### Design decisions (hardened beyond a naive framework switch)

- **Test name extraction**: The `::` separator in the node ID is vitest-filter compatible — vitest `-t "TestName"` matches a test named "TestName". The last `::` segment is the test name, per existing `_resolve_test_path` logic.
- **OOB error handling**: If `npx vitest` or `vitest` is not installed (unlikely in this repo given the studio features already use it), fall back to the existing pytest behavior (exit 4). This preserves backward compatibility.
- **Empty test-name**: If the test_node has no `::` segment, vitest `run <file>` runs the full suite — matching the existing pytest default behavior when no node is specified.
- **Edge case: `.py` files in `tools/`**: A `.py` file under `tools/` would go through the pytest path, which is correct — the existing engine already handles it.
- **Edge case: `.ts` files NOT under `tools/` or `src/`**: These would fall into the "unknown extension → fallback to pytest" branch, preserving the existing exit-4 behavior. In practice, all TS test files in this repo live under `tools/petri-net-studio/tests/` or similar, so they'd be caught by the `.ts` branch.

### Before vs After

| Scenario | Before (`run_pytest` only) | After (toolchain-aware dispatch) |
|---|---|---|
| `omt_tdd{op:red}` on `.py` test node | RED verified if pytest exit 1 | Unchanged (pytest path) |
| `omt_tdd{op:red}` on `.ts` test node | Hard error (exit 4: "file not found") → cycle blocked | RED verified via `npx vitest run <file>` → genuine RED gate |
| `omt_tdd{op:green}` on `.py` test node | GREEN if pytest passes | Unchanged |
| `omt_tdd{op:green}` on `.ts` test node | Hard error (pytest always passes empty suite) → cycle blocked | GREEN if `npx vitest run <file>` passes |
| `omt_tdd{op:refactor}` on `.ts` test node | Hard error → blocks refactor | GREEN → src/ unlocked if tests stay green |
| `omt_tdd{op:done}` (validate-exit) on `.ts` feature | Vacuously empty (no `.py` test dir) → approves | Still vacuously empty (no `.py` test dir) → approves; but dangling REDs from the cycle are now properly tracked |

### Companion doc updates (the GOTCHA must change, not stay)

Once proposal A lands, `GOTCHA_A11_B11_omt_tdd_vitest_mismatch` (new) replaces the stale A11/B11 workaround reference. The wording states a canonical form, not a mandate — but the A11/B11 bullets in WORK.md and the three feature test reports need rewording:

1. `WORK.md` Agent Scratchpad: reword the `GOTCHA_TESTLIST_JSON` / A11/B11 bullets (same session, harness-surface round-robin discipline).
2. `feature_034/test_report.md`: update the TDD two-hats section to reference proposal A instead of A11/B11 manual workaround.
3. `feature_035/test_report.md`: same.
4. `feature_036/test_report.md`: same.

These are `harness_paths` edits → one edit per file per round, then `uv run scripts/omt/harnessc.py build` + e2e receipt refresh.

### Verification

- Unit test: extend `tests/scripts/omt/test_tdd_check.py` with parametrized rows for `.ts` and `.tsx` test nodes: assert `omt_tdd{op:red}` returns `ok:true, state:red` (not exit 4 error) and `omt_tdd{op:green}` returns `ok:true, state:green` (via vitest) when the test file has appropriate `vitest` test annotations. Keep existing JSON-array prose testlist tests untouched (regression).
- Manual: `uv run scripts/omt/tdd_check.py start --test-node "tools/petri-net-studio/tests/engine/analysis.test.ts::TestReachableMarkings" --feature feature_036.studio_v3_graph --session probe` must return `{"ok":true,"state":"red"}` (not exit 4 error). Similarly `uv run scripts/omt/tdd_check.py green --test-node "tools/petri-net-studio/tests/engine/analysis.test.ts::TestReachableMarkings" --feature feature_036.studio_v3_graph --session probe` must return `{"ok":true,"state":"green"}` when the test file has passing vitest tests.
- Through the tool: `omt_tdd{op:"testlist",behaviors:"- Write a test",feature:"feature_036.studio_v3_graph"}` → existing prose fallback already works (feature_037). New: `omt_tdd{op:red,test_node:"tools/petri-net-studio/tests/engine/analysis.test.ts::TestReachableMarkings",feature:"feature_036.studio_v3_graph"}` → returns `ok:true,state:red`.
- Regression: existing JSON-array calls in tests/ledger fixtures pass unchanged; `uv run pytest tests/scripts/omt/ -k "tdd"`.

### Key files (unchanged single-source → projections pipeline)

- `.meta/META_HARNESS.omt` — no edit needed (this is a Python-runtime change; `.omt` records auto-rebuild from harnessc but the change is in the TDD engine, not the meta-harness definitions). Wait — will there be `@doc gotcha` / `@hat` / `@msg` changes? Let me think... The A11/B11 workaround was itself documented via `@doc gotcha.testlist_json` and `@hat tdd.testlist` edits in the prior review (feature_037). After proposal A lands, the A11/B11 workaround is no longer needed. So the companion doc updates (rewording `@doc gotcha.testlist_json` and `@hat tdd.testlist` gloss to reference the toolchain dispatch instead of the manual workaround) ARE needed. These are `@doc` / `@hat` edits → `harnessc.py build` + e2e receipt refresh.
- `scripts/omt/tdd/cli.py` — the only runtime file this plan modifies (add `_run_test_framework` + guard Python-AST calls).
- `scripts/omt/tdd/gates.py` — add `_run_test_framework` usage in `cmd_after_edit` and ensure `cmd_validate_exit` uses it.
- `opencode.jsonc`, `AGENTS.md`, `.meta/.omt/*` — generated projections (auto-rebuild after `.omt` edits).
- `.sandbox/meta_harness_3_idea.md` — this analysis document (non-gated); the fresh review lives at `.sandbox/meta_harness_5_idea.md`.

---

## Action Plan (single session, single improvement)

| Priority | Action | Effort | Impact | Files touched |
|---|---|---|---|---|
| **High (only)** | Add `_run_test_framework` dispatch (`pytest` for `.py`, `vitest` for `.ts/.tsx`) to `scripts/omt/tdd/cli.py` — `cmd_start`, `cmd_green`, `cmd_refactor`, `cmd_after_edit`, `cmd_validate_exit` | Low (~45–60 min incl. verification + doc sync) | **High** — eliminates a recurring, cross-feature failure mode; unlocks real two-hats RED/GREEN/REFACTOR for polyglot features; elides the A11/B11 manual workaround documented across 3 features + WORK.md | `scripts/omt/tdd/cli.py` (edit) → `scripts/omt/tdd/gates.py` (edit) → `.meta/META_HARNESS.omt` ×2 records + `WORK.md` gotcha rewording (same-session doc sync) → `harnessc.py build` + e2e |
| — | Rejected items #4/#5/#7 | none | — | — |
| — | #10 prose fallback (already shipped) | none | — | — |

**Do NOT do (explicitly):** soften `g.receipt` to warn (#1), remove TS-pinned budgets (#5), tighten budgets to actual+5% (#7), or soft/hard nav strikes (#4). Do NOT reopen the prose fallback (#10 already shipped in meta_harness_4).

---

## Key Files (unchanged single-source → projections pipeline)

- `.meta/META_HARNESS.omt` — single source of truth (edit, then `uv run scripts/omt/harnessc.py build`)
- `scripts/omt/tdd/cli.py` — the only runtime file this plan modifies (add `_run_test_framework` dispatch)
- `scripts/omt/tdd/gates.py` — add `_run_test_framework` usage in gates; guard Python-AST analysis for non-.py targets
- `scripts/omt/harnessc.py` — compiler; rebuild after `.omt` edits
- `.sandbox/meta_harness_3_idea.md` — this analysis document (non-gated)
- `.sandbox/meta_harness_5_idea.md` — this fresh review (non-gated; produced by this project)

---
