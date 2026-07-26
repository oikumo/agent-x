# AGENTS.md — System Rules

> GENERATED FROM `.meta/META_HARNESS.omt` — DO NOT EDIT. Edit the source, then `uv run scripts/omt/harnessc.py build`. Drift test: `uv run scripts/omt/harnessc.py check --verify-projections`.

> **STARTUP:** Read `WORK.md` (only) at session start; summarize current state in ≤ 15 lines (in-progress / blocked / next). All other docs on demand via nav tools (`omt_nav`, `omt_list_sections`, `omt_cross_ref`, `omt_quick_ref`).
> **RUNTIME:** `uv` only (no bare `python`/`pip`/`pytest`). `src/` edits → `omt_phase` first.

## Enforcement
**ENF:** enforcement is mechanical via .opencode/plugins/omt_enforcer.ts (composition root) + .opencode/lib/enforcer/ ×7 + opencode.jsonc; reference = THIS file (.meta/META_HARNESS.omt) queried via omt_nav

## NEVER (blocked by gate)
- bash deny: `git commit *` `git push *` `python *` `python3 *` `pip *` `pip3 *` `pytest *`
- read deny: `*.env` `*.env.*`; toplevel deny: `webfetch`
- protected: `.env` `.env.*` (hard — no override) · `README.md` `uv.lock` `LICENSE` (`omt_skip{scope:"all"}` only)
- edit gates: harness-surface 2nd edit w/o fresh e2e receipt · `tests/` w/o canary approval · `src/` w/o `omt_phase` · TA:-carrying files w/o `omt_think_list` consult

## ALWAYS
`git status` → `META.md` per dir → `omt_phase` → `omt_complete` → `uv run pytest`

## Phase Artifacts (§12)
| Task Type | Artifact Required |
|---|---|
| `bug_fix` `minor_feature` `refactor` `test` | Phase declaration only |
| `major_feature` `new_screen` | Phase + **design doc on disk** (`new_feature.py`) |
| `docs` | None |

## TDD (feature_016)
`major_feature`/`new_screen` in **Programming** → auto-activates: `omt_testlist → omt_red → omt_green → omt_refactor → omt_done`.
**Two-hats:** `RED` → tests/ edits only · `GREEN`/`REFACTOR` → src/ edits only (auto-revert if tests break).

## Tools
| Tool | Purpose |
|---|---|
| `omt_complete` | Verify the current phase's artifacts, then optionally advance… |
| `omt_cross_ref` | Resolve an XREF_ cross-reference to related doc sections. |
| `omt_done` | Declare TDD completion; runs full suite + checklist; state DONE. |
| `omt_green` | Declare a passing test (verified); state GREEN — src/ edits… |
| `omt_list_sections` | List all SECTION: headers across the META HARNESS corpus. |
| `omt_nav` | Navigate META HARNESS docs by structured tag… |
| `omt_phase` | Declare your OMT++ phase before editing src/… |
| `omt_quick_ref` | Get QUICK_ workflow patterns for common agent tasks. |
| `omt_red` | Declare a failing test (verified true RED); state RED — tests/… |
| `omt_refactor` | Declare refactor state (tests verified green); src/ only,… |
| `omt_skip` | Logged escape hatch: unlock edits/nav without a phase… |
| `omt_status` | OMT++ process context: phase, unlock, artifacts, lint baseline,… |
| `omt_testlist` | Record the TDD behavior list (JSON array); sets state TESTLIST. |
| `omt_think` | Add a persistent inline TA: thought-tag (language-valid… |
| `omt_think_list` | List TA: thought-tags (grep is truth); records the consult that… |
| `omt_think_remove` | Remove a TA: line; appends a remove-tombstone (index… |
| `omt_think_suggest` | Rank candidate TA: insertion sites in a .py file. |
| `omt_think_verify` | Re-check a TA: thought's placement integrity (drift → stale). |

## Navigation Enforcement (feature_020)
**MANDATORY:** scoped gate in lib/enforcer/nav_gate.ts — blocks grep/glob on doc paths until nav used; read & src/non-doc exempt; omt_skip{scope:nav} escape

## Think Anywhere (feature_021)
feature_021.meta_harness_think_anywhere — persistent inline TA: thought-tags think-gate NOT bypassable by omt_skip (safety-relevant); only omt_think_list clears it

## Quick Reference
- **start_bug:** omt_phase{tt:bug_fix,ph:Programming,sc:"..."} → fix → test → omt_complete{advance_to:Testing}
- **start_major:** omt_phase{tt:major_feature,ph:Analysis,sc:"..."} → new_feature.py → design → omt_complete{advance_to:Design} → omt_phase{ph:Programming} → TDD cycle
- **skip_src:** omt_skip{reason:"emergency",scope:"src"} (logged)
- **status:** omt_status → phase, unlock, artifacts, lint, next phases, WORK.md next
- **lint:** uv run scripts/omt/mvc_check.py [file|dir]
