# AGENTS.md — System Rules (compressed)

> **STARTUP:** Read `WORK.md` (only) at session start; summarize current state in ≤ 15 lines (in-progress / blocked / next). All other docs on demand via nav tools (`omt_nav`, `omt_list_sections`, `omt_cross_ref`, `omt_quick_ref`).
> **RUNTIME:** `uv` only (no bare `python`/`pip`/`pytest`). `src/` edits → `omt_phase` first.

## Enforcement
**ENF:** mechanical via `.opencode/plugins/omt_enforcer.ts` + `opencode.jsonc`  
**REF:** `.meta/META_HARNESS.md` (R1–R3, RIGOR, ERR, WRN, PROT, ESC, EXT, TREE, CMDS)

## NEVER (blocked by gate)
`git commit|push`, `.env*`, deps w/o approval, `tests/` w/o canary, `README.md|uv.lock|LICENSE`, `src/` w/o `omt_phase`

## ALWAYS
`git log/status` → `META.md` per dir → `omt_phase{tt,ph,sc}` → artifacts per §12 → tests pass

## Phase Artifacts (per META_HARNESS.md §12 / guide §12)
| Task Type | Artifact Required |
|-----------|-------------------|
| `bug_fix` `minor_feature` `refactor` `test` | Phase declaration only |
| `major_feature` `new_screen` | Phase + **design doc on disk** (`new_feature.py`) |
| `docs` | None |

## TDD (feature_016)
`major_feature`/`new_screen` in **Programming** → auto-activates:
```
omt_testlist → omt_red → omt_green → omt_refactor → omt_done
```
**Two-hats gate:**
- `RED` state → `tests/` edits only
- `GREEN`/`REFACTOR` state → `src/` edits only (auto-revert if tests break)

## Tools
| Category | Tools |
|----------|-------|
| Phase | `omt_phase`, `omt_skip`, `omt_complete` |
| TDD | `omt_testlist`, `omt_red`, `omt_green`, `omt_refactor`, `omt_done` |
| Lint/Scaffold | `mvc_check.py`, `new_feature.py`, `tdd_check.py` |
| Status | `omt_status` |
| **Navigation** | `omt_nav`, `omt_list_sections`, `omt_cross_ref`, `omt_quick_ref` |
| **Think Anywhere** | `omt_think`, `omt_think_list`, `omt_think_remove`, `omt_think_verify`, `omt_think_suggest` |

## Navigation Enforcement (feature_020)
**MANDATORY:** Before answering ANY question about the project (classes, components, features, architecture, codebase structure, workflows, etc.), agents MUST:
1. Use `omt_nav` / `omt_list_sections` / `omt_cross_ref` / `omt_quick_ref` to search META HARNESS documentation
2. Only fall back to `grep`/`glob` if navigation tools return no results
3. Cite documentation sections found via navigation tools in responses

**Scope of the mechanical gate:** the gate blocks `grep`/`glob` scoped to **doc paths** (`.meta/`, `AGENTS.md`, `WORK.md`) until a nav tool is used. It does **not** block:
- `read` (targeted file access — e.g. `WORK.md` at startup, or a file the user named)
- searches scoped to `src/` or other non-doc paths (nav indexes docs, not code)

**Escape hatch:** `omt_skip{reason:"...", scope:"nav"}` (logged) bypasses the nav gate for the session.

## Think Anywhere (feature_021)
Persistent `TA:` thought-tags inline in any non-protected file — hard-won context (gotchas, why, risks, xrefs) survives sessions. Retrieval O(hits) via `grep`/`omt_think_list`, never whole-file reads.

**Tools:**
- `omt_think{path, thought, line?, category?}` — insert a language-aware `TA:` comment (annotation; bypasses phase/canary gates). Denied on `.env*`, `README.md`, `uv.lock`, `LICENSE`, `.json`.
- `omt_think_list{path?, category?, query?}` — grep-backed retrieval; **marks the session consulted** (clears the think-gate).
- `omt_think_remove{path, line}` — remove a `TA:` line + append a remove-tombstone (R6: index is append-only).
- `omt_think_verify{path, line}` — re-check a thought's placement integrity (drift → stale).
- `omt_think_suggest{path, top?}` — rank candidate TA: insertion sites (.py).

**Tag format:** `<comment> TA: [<category>: ] <thought>` — e.g. `# TA: gotcha: mutates history`, `// TA: why: legacy compat`, `<!-- TA: risk: breaks if x -->`.

**Think-gate (blocking):** editing a file that carries `TA:` thoughts is **blocked** until the session consults via `omt_think_list`. The block surfaces the file's own thoughts. **NOT bypassable by `omt_skip`** — thoughts are safety-relevant; only `omt_think_list` (active consult) clears it.

**Session digest:** the first tool result of each session carries a compact TA: digest (counts + per-file counts + stale ⚠️ + pointer; full texts via `omt_think_list` and per-file injection on read). Emitted on `tool.execute.after` (R6: the inert `session.start` hook was deleted). The index is append-only (add/verify/remove-tombstone).

## Quick Reference
- **Declare phase:** `omt_phase{task_type:"bug_fix|minor_feature|major_feature|new_screen|refactor|test|docs", phase:"Analysis|Design|Programming|Testing", scope:"done definition"}`
- **Major/new needs design:** `uv run scripts/omt/new_feature.py "<name>" --type major_feature`
- **Escape hatch:** `omt_skip{reason:"...", scope:"src|tests|nav|all"}` (logged)
- **Complete phase:** `omt_complete{feature:"feature_XXX", advance_to:"Design|Programming|Testing|Done"}`
- **Architecture check:** `uv run scripts/omt/mvc_check.py [path]`
