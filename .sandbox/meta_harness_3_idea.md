# Meta Harness 3 — Analysis & Single-Improvement Plan

> Critical review of the META HARNESS (`.meta/META_HARNESS.omt` @ HEAD `5789125`, August 2026). Every count and claim below was verified live against the source; the single recommendation is backed by an executed repro and an executed parser.

## Executive Summary

This review evaluates 10 proposals for improving the harness. **6 are already implemented, 3 were correctly rejected as safety/complexity losses, and exactly ONE genuine, low-risk, high-value improvement survives:**

> **Add a prose fallback to `omt_tdd testlist` behavior parsing in `scripts/omt/tdd/cli.py` (line 68) — hardened to also accept JSON strings and numbered-list prose.**

That is the *single* recommendation. It is a **Python-script change (not an opencode plugin change)** — the agent-facing call chain (`omt_tdd` TS tool → `scripts/omt/tdd_check.py` shim → `tdd/cli.py:68`) passes prose through verbatim, so the Python parser is the only place that can accept it. It eliminates a **top-3 recurring agent failure mode** (`GOTCHA_TESTLIST_JSON`, named inline in `WORK.md`), and it is purely additive: JSON-array syntax keeps working unchanged.

Guiding principle preserved throughout: *make existing escapes discoverable rather than changing gates*. The review found the escapes are already discoverable — the only remaining win is accepting the input forms agents actually emit.

**Verdict rollup (10 proposals):** 5 already implemented (#1 receipt, #2 think, #3 kb, #6 tdd_after, #8 two-hats) · #9 (gate-message escape visibility) already implemented, previously mislabeled as pending · 3 correctly rejected (#4 nav soft/hard, #5 budget removal, #7 tighten-to-actual) · **#10 → the ONE genuine DX win (prose fallback)** — now the sole recommendation.

---

## Verification Framework

| Verification Step | Command | Result |
|---|---|---|
| Record counts by kind | `rg -o '^@[a-z_.]+' .meta/META_HARNESS.omt \| sort \| uniq -c` | 208 total; see breakdown below |
| Nav index records | `wc -l .meta/.omt/nav.index.jsonl` | 247 |
| Gate categories + orders | `rg '@gate' .meta/META_HARNESS.omt` | 9 gates; orders 0,10,20,30,40,50,55,60,70 |
| Budget categories | `rg '@budget' .meta/META_HARNESS.omt` + `harness.report` | 11 budgets; report confirms sizes |
| Gotcha count | `rg -c '^@doc gotcha'` ↔ nav.index `doc.gotcha.*` ids ↔ `GOTCHA_` tags | 17 = 17 = 17 |
| TS-pinned budgets | `harness.report` + `test_omt_docs_drift_pins.py` + `omt_shared.ts` | 2 "n/a (TS-pinned)": `nav_tip`, `digest_cap`; `DIGEST_CAP_BYTES=1024` |
| TDD behaviors parse site | `scripts/omt/tdd/cli.py:68` | `behaviors = json.loads(args.behaviors) if args.behaviors else []` |
| `@msg` escape-hint presence | `rg '@msg (no_phase|nav_required|think_gate|receipt_stale)'` | all four already embed escape/clear hints |
| Failure repro | `uv run scripts/omt/tdd_check.py testlist --behaviors "Write a test" --feature test.xyz` | `{"ok": false, "error": "Expecting value: line 1 column 1 (char 0)"}` |

---

## Current State Metrics

| Metric | Actual (verified) |
|---|---|
| `@`-records in `.meta/META_HARNESS.omt` | **208** (67 @doc, 28 @var, 22 @msg, 12 @xref, 11 @budget, 10 @deny, 9 @tool, 9 @gate, 8 @pred, 5 @protect, 5 @hat, 5 @flow, 5 @always, 3 @state, 3 @phase, 3 @inject, 2 @fsm, 1 @version) |
| Nav index records | **247** |
| Gate categories | 9 (orders 0,10,20,30,40,50,55,60,70) |
| Budget categories | 11 |
| Documented gotchas | **17** (nav-indexed `doc.gotcha.*` = 17) — note: live `WORK.md` Agent Scratchpad still says "16 nav-indexed" (stale, see companion update #3) |
| TS-pinned budgets "n/a" | 2 (`nav_tip`, `digest_cap`) — `DIGEST_CAP_BYTES=1024` in `omt_shared.ts:553` |
| `omt_tdd testlist` parse | `json.loads` at `tdd/cli.py:68`; `--behaviors` default `"[]"` (`cli.py:411`); `--feature` required (`cli.py:412`); errors serialized to JSON by `main()`'s try/except (`cli.py:465–471`) |
| Escape hints in `@msg` records | Already present in all four records (`.omt` L130–134) |
| `AGENTS.md` budget pressure | 2771/2816 bytes (slack 45B; the 2560→2816 bump was a conscious `.projects/`-line addition, `.omt` L245) |

---

## Proposal-by-Proposal Verdicts

### Already implemented (6) — no action needed

| # | Proposal | Verdict | Current state (evidence) |
|---|----------|---------|--------------------------|
| 1 | `g.receipt` first-edit allowance by design; no severity reduction | ✅ implemented | First edit of clean harness files allowed by design; mtime-vs-receipt guard = one edit/file/round (`GOTCHA_RECEIPT_SECOND_EDIT`, `GOTCHA_RECEIPT_ROUND_ROBIN`) |
| 2 | `g.think` per-file consult tracking | ✅ implemented | `omt_think{op:list}` writes `kind:"think_consult"` → clears gate; `risk_high` drops cross-session window |
| 3 | `g.kb` session-once flag | ✅ implemented | `session_flag(kb_consulted)` — one `omt_kb_nav` consult/session; 256B `kb_bootstrap` injection |
| 6 | `g.tdd_after` advisory auto-revert | ✅ implemented | `hard=false` gate; two-hats invariant in `@fsm tdd` / `@hat tdd.refactor` |
| 8 | TDD two-hats discipline | ✅ implemented | Test hat → tests/, code hat → src/, refactor hat → src/ with auto-revert |
| 9 | Gate-message escape visibility (`nav_required`, `think_gate`, `receipt_stale`, `no_phase`) | ✅ implemented | All four `@msg` records already embed the escape/clear hints (`no_phase` → `omt_skip{reason:"…"}`, `nav_required` → `omt_skip{scope:"nav"}`, `think_gate` → `omt_think{op:"list"}`, `receipt_stale` → `{@var.e2e_cmd}`; verified `.omt` L130–134). `navReminderMsg()` in `nav_gate.ts` already shows the skip escape. **No opencode-plugin or `.omt` message change needed.** |

### Safety-rejected (3) — correct as rejected, do not revisit

| # | Proposal | Verdict | Reason |
|---|----------|---------|--------|
| 4 | `g.nav` soft-warn first session, hard after 3 violations | ❌ reject | Gate already `hard=true skip_ok=true` with `omt_skip{scope:"nav"}` escape + read/src exemptions; 3-strike session state adds complexity for marginal benefit |
| 5 | Remove/replace TS-pinned budgets (`nav_tip`, `digest_cap`) | ❌ reject | Single-source budgets, drift-pinned by `test_omt_docs_drift_pins.py`; removal orphans the pins |
| 7 | Tighten budgets to actual+5% | ❌ reject | Budgets carry **deliberate, review-gated growth headroom** — `agents_md` is 2771/2816 today (slack 45B; the 2560→2816 bump was a conscious `.projects/`-line addition, `.omt` L245). Actual+5% math *loosens* the budget (2771×1.05≈2909 > 2816), not tightens it. Micro-tightening erodes the headroom mechanism for no quality gain. |

### The ONE genuine DX win (1)

| # | Proposal | Verdict |
|---|----------|---------|
| 10 | `omt_tdd testlist` behavior parsing: accept JSON array **and** prose (newline/bullet/numbered) | ⭐ **THE recommendation** — see full spec below |

---

## The Single Improvement: Prose Fallback for `omt_tdd testlist` (`#10`)

### Why this one (and only this one)

- **Verified failure path (the call chain matters):** the agent calls the `omt_tdd` tool → TS wrapper (`.opencode/lib/enforcer/tdd_hats.ts`) runs `uv run scripts/omt/tdd_check.py testlist …` → the compat shim delegates to `scripts/omt/tdd/cli.py:68`, which does `json.loads(args.behaviors) if args.behaviors else []`. Two facts make this Python line the **only** place a fix can land:
  1. The SDK array-coercion guard (`tdd_hats.ts:44-47`) re-serializes JSON-array input back to valid JSON — so the canonical form always arrives parseable.
  2. Prose arrives **verbatim** (`String(v)`, no guard) — it is exactly the input that dies at `json.loads`.
  This exact failure is named inline as a **top-3 recurring gotcha** in `WORK.md` (`GOTCHA_TESTLIST_JSON`).
- **Additive, low-risk:** JSON-array syntax keeps working unchanged; prose becomes a graceful input form. Pure Python-side change — **no opencode plugin edits, no gate changes, no `.ts` edits** (the shim and the TS wrapper need no modification; one wrinkle is the arg-level hint, see "Companion updates").
- **Removes a recurring retry at every TDD session:** `omt_tdd testlist` runs at least once per TDD cycle (auto-on for every `major_feature`/`new_screen` at Programming). Each prose slip today forces a stop, a GOTCHA re-read, a JSON re-format, and a retry round-trip. Accepting the forms agents actually emit (JSON array, JSON string, bullets, **numbered lists**) removes that whole class.

### Verified current behavior

The CLI does **not** surface a raw traceback: `main()` in `cli.py` catches the exception (try/except at `cli.py:465–471`) and prints a JSON object, which the TS wrapper returns to the agent. `--feature` is required (`cli.py:412`). Verified live:

```
$ uv run scripts/omt/tdd_check.py testlist --behaviors "Write a test" --feature test.xyz
{"ok": false, "error": "Expecting value: line 1 column 1 (char 0)"}
```

(That `error` string is `str(JSONDecodeError)` from `cli.py:68`, serialized by `main()`'s handler catch.)

### Target implementation

Replace the single parse line in `cmd_testlist` (`cli.py:68`); keep `--behaviors` default `"[]"` (`cli.py:411`):

```python
import re

_BULLET_RE = re.compile(r"^\s*(?:[-•*]|\d+[.)])\s*(.*)$")

def _parse_behaviors(raw: str | None) -> list[str]:
    """Behaviors from a JSON array, a JSON string, or line-separated prose.

    Accepts:
        omt_tdd testlist --behaviors '["Write a test", "Fix bug"]'
        omt_tdd testlist --behaviors '"Write a test"'
        omt_tdd testlist --behaviors "Write a test\n- Fix bug"
        omt_tdd testlist --behaviors "1. Write a test\n2. Fix bug"
    Empty input => [] (same as today; argparse default is "[]").
    """
    if not raw or not raw.strip():
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, str):
            return [parsed]          # '"Write a test"' -> ["Write a test"]
    except (json.JSONDecodeError, ValueError):
        pass
    behaviors = []
    for line in raw.splitlines():
        m = _BULLET_RE.match(line)
        stripped = (m.group(1) if m else line).strip()
        if stripped:
            behaviors.append(stripped)
    return behaviors
```

In `cmd_testlist`:

```python
behaviors = _parse_behaviors(args.behaviors)
```

Every row in the Before/After table below was **executed against this exact parser** (Python 3, `uv run python3`); all rows match their cells.

**Design decisions (hardened beyond a naive fallback):**

- **JSON strings are handled.** A naive list-guard-only fallback would send `"Write a test"` (a valid JSON string) down the prose path and keep the quotes → `['"Write a test"']`. The `isinstance(parsed, str) → [parsed]` branch parses it correctly.
- **Numbered lists are handled.** Stripping only `-`/`•`/`*` markers leaves `1.`/`2.` prefixes inside behavior text. `_BULLET_RE` strips `-`/`•`/`*` and `1.`/`1)`-style markers — the format agents actually emit. Verified: `'1. Write a test\n2. Fix bug'` → `["Write a test", "Fix bug"]`.
- **Empty behavior lines are skipped** (`"-"`, `"1. "` → no phantom entries).
- **Honest list-guard rationale:** `behaviors`/`remaining` are written to the ledger (`tdd_testlist` record) but **never read anywhere** — grep across `tdd/*.py` and `.opencode/` finds no consumer of `remaining`. A `str` therefore would not crash `write_ledger`/`len()`; it would be **silent ledger type-drift** plus a wrong `behaviors_count`. The list guard is still correct defense — but the crash framing is overstated.
- **Scalar JSON falls to prose:** `123` → `["123"]` (a JSON scalar is neither list nor string; treated as prose text).
- **Placeholder-behavior removal:** there is no fake `["[please add behaviors ...]"]` placeholder; `[]` matches today's empty default.

### Before vs After

| Input | Before (`json.loads` only) | After (`_parse_behaviors`) |
|---|---|---|
| `["Write a test", "Fix bug"]` (JSON array) | ✅ list | ✅ unchanged |
| `Write a test` (bare prose) | ❌ `{"ok":false,"error":"Expecting value…"}` | ✅ `["Write a test"]` |
| `- Write a test\n- Fix bug` | ❌ error | ✅ `["Write a test", "Fix bug"]` |
| `• Task 1\n• Task 2` | ❌ error | ✅ `["Task 1", "Task 2"]` |
| `1. Write a test\n2. Fix bug` | ❌ error | ✅ `["Write a test", "Fix bug"]` |
| `"Write a test"` (JSON string) | ❌ `str` drifts into ledger (silent) | ✅ `["Write a test"]` |
| `123` (JSON scalar) | ❌ `int` drifts into ledger (silent) | ✅ `["123"]` (scalar falls to prose) |
| empty / omitted / `[]` (default) | ✅ `[]` | ✅ `[]` unchanged |

### Companion doc updates (the GOTCHA must change, not stay)

Once prose parses, `GOTCHA_TESTLIST_JSON` ("prose fails …") is stale — landing the change requires **updating** it (same session, harness-surface round-robin discipline). The wording states a canonical form, not a mandate:

1. `.meta/META_HARNESS.omt` `@doc gotcha.testlist_json` (L221): reword to *"behaviors: JSON array is canonical; newline/bullet prose is auto-split by tdd/cli.py `_parse_behaviors` — no re-format required"*.
2. `.meta/META_HARNESS.omt` `@hat tdd.testlist` (L89): "behavior list only (JSON array)" → "behavior list (JSON array canonical; prose auto-split)".
3. `WORK.md` Agent Scratchpad gotcha line — same rewording, **and** fix the stale count: the header line says "16 nav-indexed" while 17 `doc.gotcha.*` ids are actually nav-indexed (verified: 17 = 17 = 17).
4. `@tool omt_tdd` description (`.omt` L264) can note "behaviors: JSON array or prose". **Scope honesty:** this propagates only to the *tool-level* description via `irToolDescription`; the *arg-level* hint `tdd_hats.ts:28` ("testlist: JSON array of behaviors") is hardcoded in the plugin and stays JSON-only unless a plugin edit is made — which is out of scope. Acceptable: the hint describes the canonical form; prose is a graceful fallback.

These are `harness_paths` edits → one edit per file per round, then `uv run scripts/omt/harnessc.py build` + e2e receipt refresh (see `GOTCHA_RECEIPT_ROUND_ROBIN`).

### Verification

- Unit test: extend `tests/scripts/omt/test_tdd_check.py` (the existing suite imports the `tdd_check` shim; `from tdd.cli import _parse_behaviors` is importable) with the table above → assert outputs. Keep the existing `test_testlist_blocks_all` / JSON-array fixtures untouched (regression).
- Manual: `uv run scripts/omt/tdd_check.py testlist --behaviors "Write a test" --feature <slug>` must return `"ok": true, "behaviors_count": 1` (note: `--feature` is required) and no `error` field.
- Through the tool: `omt_tdd{op:"testlist", behaviors:"- Write a test\n- Fix bug", feature:"<slug>"}` must return `behaviors_count=2`.
- Regression: existing JSON-array calls in tests/ledger fixtures pass unchanged; `uv run pytest tests/scripts/omt/ -k "tdd"`.

---

## Action Plan (single session, single improvement)

| Priority | Action | Effort | Impact | Files touched |
|----------|--------|--------|--------|---------------|
| **High (only)** | Add `_parse_behaviors` prose fallback to `omt_tdd testlist` (JSON array, JSON string, bullets, numbered lists) | Low (~45–60 min incl. tests + doc sync) | **High** — removes a top-3 recurring agent failure mode; eliminates the `Expecting value…` retry in every TDD session; accepts the prose formats agents actually emit | `scripts/omt/tdd/cli.py` (edit) → `tests/scripts/omt/test_tdd_check.py` (unit tests) → then `.omt` ×2 records + `WORK.md` gotcha + 16→17 count fix (same-session doc sync) → `harnessc.py build` + e2e |
| — | Rejected items #4/#5/#7 | none | — | — |
| — | #9 gate-message escapes | **none — already implemented** | — | — |

**Do NOT do (explicitly):** soften `g.receipt` to warn (#1), remove TS-pinned budgets (#5), tighten budgets to actual+5% (#7), soft/hard nav strikes (#4), or re-add escape hints to `@msg` records (#9 — they are present today).

---

## Key Files (unchanged single-source → projections pipeline)

- `.meta/META_HARNESS.omt` — single source of truth (edit, then `uv run scripts/omt/harnessc.py build`)
- `scripts/omt/tdd/cli.py` — the only runtime file this plan modifies (line 68)
- `scripts/omt/harnessc.py` — compiler; rebuild after `.omt` edits
- `opencode.jsonc`, `AGENTS.md`, `.meta/.omt/*` — generated projections (auto-rebuild)
- `.sandbox/meta_harness_3_idea.md` — this analysis document (non-gated)