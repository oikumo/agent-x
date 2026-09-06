# Test report — feature_059.harness_tiered_template (Wave 5 D1+D2+D3)

> major_feature · Testing 2026-09-06 · TDD testlist (10 behaviors → 12 tests)

## TDD cycle

- `testlist`: 10 behaviors (tier T1/T2/T3+net filter, template_vars,
  init fs, init refuse, onboarding content, mvc none/ts, budget pins).
- RED-1: `test_tier_filter.py::test_tier1_...` true-RED (missing
  `filter_corpus_for_tier`) → GREEN-1 (R1 .omt vars, R2 filter+vars).
- RED-2: init/onboarding/mvc/budget files true-RED (missing `cmd_init`,
  `check_tree`) → GREEN-2 (R3 mega-round, R4 esc+collect fixes, R5 seed sync).
- Same-node red/green pairs kept (gotcha pin); batch warnings accepted
  (4-file RED-2 batch, one GREEN covering the slice — documented).

## Results

- New suite: **12/12 green**
  (`tests/features/feature_059.harness_tiered_template/`: tier_filter 4,
  init_fs 4, mvc_profile 3, budget_pins 1).
- Full suite: **1979 passed / 0 failed** (1967 pre-existing + 12 new),
  empty allowlist, `uv run pytest -q` 177s.
- `harnessc check`: 0 errors, 263 records. `build`: OK (5 projections +
  GETTING_STARTED.md 2176 B, gitignored). All 12 budgets green —
  tightest unchanged (tool_args 2278/2304, schemas 1770/1792,
  nav_index 63923/64000, agents_md 2918/2944, gates 10/12).
- e2e `test_omt_harness_e2e.py`: green incl. new **check 19**
  (template vars + 6 harnessc pins + mvc profile pins + gitignore pin);
  receipt refreshed after every harness round (R1–R5).
- Live template proof (in-process, hermetic tmp dirs): `init --tier 1`
  tree checks green via `check_tree` (gates exactly
  g.phase/g.protect/g.tdd_after/g.tests); `--tier 3` + receipt, net
  excluded by default / included with `--with-net`; non-empty dir refused
  with and without `--force`; Tier-1 onboarding names core gates only and
  carries no nav/think/kb/net tokens; Tier-3-full lists all 10 gates.
- `mvc_check --profile none` exits 0; `mvc_ts` flags TS
  view-creates-controller; `mvc_py` byte-identical (existing
  `test_mvc_check.py` green untouched).

## Coverage gaps / follow-ups (non-blocking)

1. Per-tier runtime manifests (T1 ships inert T3 scripts — documented).
2. Measure-then-set budget re-baseline at init (caps kept loose, green).
3. TS scope-arg validation stays source-wide (T1 nav skip logs noise only).
4. Cross-repo execution (target `pytest`, target `opencode` boot) not run
   here — no target venv/opencode in this env; in-process `check_tree`
   is the hermetic equivalent.
