# Design 001 — harness_tiered_template (feature_059)

> meta_harness_6 Wave 5 D1+D2+D3 · 2026-09-06 · major_feature (Design)
> Analysis: `3.analysis/features/feature_059.harness_tiered_template/analysis_001_tiered_template.md`

## 1. Goal (one sentence)

`harnessc init --tier 1|2|3 [--with-net] [--profile mvc_py|mvc_ts|none] <dir>`
scaffolds a working tiered harness; `mvc_check --profile` honors the stack;
`harnessc build` emits `GETTING_STARTED.md` for the active tier.

## 2. `.omt` changes (exactly 2 new `@var`, 0 nav-indexed records)

```omt
# D1 (feature_059): tiered-template pointer — tier table lives in harnessc.py TIERS (code, not records); this var names the default tier for init/build onboarding
@var template_default_tier : 1
# D2 (feature_059): stack profile — mvc_py (current Python/TUI rules) | mvc_ts (TS text-mode rules) | none (mvc_check disabled, exit 0)
@var stack_profile : mvc_py
```

- Placement: after `@var skip_override_warn_per_week` (Wave 5 block), with
  `# D1:`/`# D2:` comments (0 nav cost).
- Cost: ir_json +~60B (headroom 568B). nav_index/tool_args/tool_schemas/
  agents_md/gates untouched. No diet, no deliberate bump.
- Validation: `check_` fn `check_template_vars` — default_tier in {1,2,3},
  stack_profile in {mvc_py,mvc_ts,none}; error otherwise (fail-closed, same
  shape as existing `check_` fns).

## 3. `harnessc.py` changes

### 3.1 `TIERS` table (code, ~60 lines)

```python
TIER_1_KEEP_KINDS = {"version","var","deny","protect","always","phase","fsm","hat","budget","tool","state"}
# Tier 1 gate/tool allowlists (by rid):
TIER_1_GATES = {"g.protect","g.phase","g.tests","g.tdd_red","g.tdd_green","g.tdd_after"}
TIER_1_TOOLS = {"omt_phase","omt_skip","omt_tdd","omt_complete","omt_status"}
TIER_1_PREDS = {"path_in","cmd_match","ledger_has","session_flag","file_has","fsm_allows"}
TIERS = {
  1: {"desc": "core: deny/protect/phase/TDD/ledger", ...},
  2: {"desc": "tier1 + nav/thoughts/KB/budgets/projects/workflows", ...},
  3: {"desc": "tier2 + receipt/think-hard/MVC (+net iff --with-net)", ...},
}
```

- `filter_corpus_for_tier(c, tier, with_net=False) -> Corpus`: keep records
  per tier rules (kind filter + rid allowlists for gate/tool/pred; drop
  net_paths var entries at T1/T2; Tier 3 drops net-gate/records unless
  with_net, emitting a warning). Pure function — unit-testable without fs.
- Tier 2 = Tier 1 + nav/think/kb/q tools+docs+flows+vars+gates.
- Tier 3 = Tier 2 + receipt/think-hard/MVC + budgets full. Net excluded
  unless `with_net=True` (DG3), which keeps g.net + @pred net_marking +
  net_paths and prints an experimental warning.

### 3.2 `init` subcommand

```
harnessc init --tier {1,2,3} [--with-net] [--profile {mvc_py,mvc_ts,none}] [--force] <dir>
```

- Semantics: `<dir>` must not exist or must be empty (else error 1, unless
  `--force` with empty-only still enforced — never clobber non-empty).
- Writes into `<dir>`: `.meta/META_HARNESS.omt` (filtered records, header
  rewritten with tier stamp + `template_tier` marker comment), `WORK.md`
  (minimal canonical Tasks skeleton), `.meta/.omt/` (empty ledger.jsonl,
  thoughts.jsonl), `GETTING_STARTED.md` (rendered for the tier, §5),
  `tests/scripts/omt/test_template_e2e.py` (minimal tier e2e, §6).
- Sets `@var stack_profile` payload to `--profile` (default: tier1→none,
  tier2/3→mvc_py) and `@var template_default_tier` to the tier.
- Fresh budget baseline: `@budget` max values scaled to the tier corpus
  (measure-then-set: compute sizes on the filtered corpus, set max = size
  rounded up to a sane step — deterministic, recorded in implementation notes).
- Exit codes: 0 ok, 1 fs/precondition error, 2 usage error (matches main()).
- `main()` dispatch grows `"init"` (check/build untouched). Budget loop
  unaffected (init does not measure THIS repo).

### 3.3 `GETTING_STARTED.md` emission (D3)

- `render_getting_started(c, tier) -> str`: `# Getting started (Tier N)` +
  tier description + gate list (rid + payload, ordered by `order`) + tool
  list (rid + perm) + flow list + next-steps (declare phase → work →
  complete; pointer to full guide for T2/T3). Pure render, stdlib-only.
- `build` writes `GETTING_STARTED.md` at repo root (this repo gets the
  Tier-3-full file — gitignored? NO: this repo's file is NOT committed;
  build writes it, tests assert content, `.gitignore` keeps it out. Rationale:
  committing a generated onboarding file for the full harness duplicates
  AGENTS.md; the template's file is what matters).
- Decision: `build` emits the file ALWAYS (all tiers, including this repo),
  because the acceptance says "`harnessc build` emits GETTING_STARTED.md
  per tier". This repo's copy is gitignored.

## 4. `mvc_check.py` changes (D2)

- New flag: `--profile {mvc_py,mvc_ts,none}` (default: read
  `@var stack_profile` from the repo `.omt` when run inside a repo, else
  `mvc_py` — backwards compatible).
- `none`: print `✅ MVC++ disabled (profile=none)` + exit 0, scan nothing.
- `mvc_ts`: text/regex mode over `**/*.{ts,tsx}` (stdlib `pathlib.glob`):
  mirror rules VIEW_IMPORTS_MODEL (view imports model dir), MODEL_IMPORTS_UI,
  VIEW_CREATES_CONTROLLER (`new XController(`), GOD_CONTROLLER (>300 lines),
  SQL_OUTSIDE_DP (same regexes). AST rules skipped (no TS parser in stdlib —
  documented limitation in `--help` + GETTING_STARTED).
- `mvc_py`: current behavior, unchanged (all existing tests green untouched).

## 5. Tests (TDD testlist preview — full list at Programming)

New dir `tests/features/feature_059.harness_tiered_template/` (canary!):

1. tier filter purity: T1 corpus has no g.nav/g.think/g.kb/g.net/g.receipt,
   keeps deny/protect/phase/TDD tools; T2 adds nav/think/kb/q; T3 adds
   receipt (net excluded w/o flag, included with flag + warning).
2. template_vars check: bad default_tier / bad stack_profile = check error.
3. init fs: tmp dir → init --tier 1 → files exist → `check` green on the
   FILTERED omt (parse+run_all_checks on the emitted file) → GETTING_STARTED
   names Tier 1 gates only.
4. init refuses non-empty dir (exit 1); `--force` still refuses non-empty
   (documents never-clobber).
5. mvc profile none exits 0 without scanning; mvc_ts finds a
   view-creates-controller TS fixture; mvc_py unchanged (existing suite).
6. build emits GETTING_STARTED.md containing the tier's gate rids.
7. e2e template check (bundled `test_template_e2e.py` content): Tier-1 tmp
   repo check+build green (runs in-process via functions, not subprocess —
   hermetic, OMT_LEDGER_PATH-style isolation where ledger touched).
8. budgets: this repo check still green (nav_index/tool_args/schemas/agents
   unchanged — assert sizes equal pre-feature values in the pin test).

e2e receipt: `tests/scripts/omt/test_omt_harness_e2e.py` gains check 19
(pins: init subcommand exists, 2 new @var present, GETTING_STARTED render
smoke). The e2e file is receipt-EXEMPT (update pins first, shape-agnostic).

## 6. Receipt / harness-surface discipline

- Touched harness files: `.meta/META_HARNESS.omt` (.omt), `scripts/omt/
  harnessc.py`, `scripts/omt/mvc_check.py`, e2e test file (exempt),
  `.gitignore` (GETTING_STARTED.md — NON-harness? root allowlist includes
  .gitignore; check `harness_paths`: not listed → normal edit, still
  preflight it).
- Round discipline (feature_050 guard): ONE edit per file per round, ONE e2e
  refresh per round. Plan: R1 = .omt (2 vars + comments) → check green →
  e2e refresh; R2 = harnessc.py (TIERS+filter+init+onboarding) →
  check+build green → e2e refresh; R3 = mvc_check.py (profile) + .gitignore
  → full suite → e2e refresh. Transforms via `uv run` python scripts
  (sanctioned bash path), same round discipline manually.
- Gates before each edit: `omt_status{op:preflight}` + `omt_kb_nav` consult
  (src edits) + `omt_think{op:list}` on harnessc.py (TA:-carrying!) + tests
  canary `omt_skip{scope:tests}` (C2 narrowed auto-unlock covers own test
  dir under RED only — new test dir needs the canary until RED is active).

## 7. Acceptance (maps to PROJECT.md §Scope #5 + eval D1–D3)

- [ ] `harnessc init --tier 1 <tmp>` → `check` green in tmp repo; deny fires
  (git commit blocked text), phase gate fires (src edit w/o phase), TDD
  RED→GREEN cycle works on a toy src file.
- [ ] `init --tier 2/3` supersets verified by filter tests; `--with-net`
  includes g.net + warning, default excludes it.
- [ ] `mvc_check --profile none` exit 0; `--profile mvc_ts` flags TS
  view-creates-controller; default unchanged.
- [ ] `build` emits GETTING_STARTED.md with the tier's gates/tools; Tier-1
  file mentions no nav/think/KB/net.
- [ ] Full suite green, all 12 budgets green, e2e receipt refreshed.
