# Operation Spec 001 — feature_059.harness_tiered_template: public operation contracts

> Phase: Design companion to design_001_tiered_template.md. Each operation:
> signature · pre · post/effects · errors. `harnessc.py` stays stdlib-only;
> `mvc_check.py` stays stdlib-only. No new MCP tools (no tool_args/schema cost).

## scripts/omt/harnessc.py — tier filter (design §3.1)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `filter_corpus_for_tier(c: Corpus, tier: int, with_net: bool = False) -> Corpus` | `c` = parsed+interpolated full corpus; `tier` in {1,2,3}; `with_net` only meaningful at tier 3 | NEW Corpus with records filtered per TIERS allowlists (T1: core kinds+gates+tools+preds; T2: +nav/think/kb/q; T3: +receipt/think-hard/MVC; net records iff tier==3 and with_net). PURE (no fs). Deterministic: same corpus+tier+flag → identical record id list. | `ValueError` on tier not in {1,2,3}; `with_net=True` at tier<3 is ignored (no error, documented) |
| `check_template_vars(c: Corpus) -> None` | `c` = corpus (post-interpolate) | Appends to `c.errors` iff `@var template_default_tier` payload not in {1,2,3} or `@var stack_profile` payload not in {mvc_py,mvc_ts,none}. Silent when both valid / when vars absent (absent = pre-feature corpus, checked by ref-closure elsewhere). | none (warning-free; error strings name the var + allowed set) |
| `TIERS: dict[int, dict]` | module-level constant | Keys {1,2,3}; each value has `desc: str`, `keep_kinds: set[str]`, `gates: set[str]`, `tools: set[str]`, `preds: set[str]`. Tier N superset of Tier N-1 except net (gated by with_net). Pinned by test asserting exact gate/tool sets per tier. | n/a (data) |

## scripts/omt/harnessc.py — init subcommand (design §3.2)

| Op | Contract |
|---|---|
| `cmd_init(argv: list[str]) -> int` | `harnessc init --tier {1,2,3} [--with-net] [--profile {mvc_py,mvc_ts,none}] [--force] <dir>`. Pre: `<dir>` missing-or-empty (else exit 1, never clobber; `--force` still refuses non-empty). Effects: writes `<dir>/.meta/META_HARNESS.omt` (filtered+restamped), `<dir>/WORK.md` (minimal skeleton), `<dir>/.meta/.omt/{ledger,thoughts}.jsonl` (empty), `<dir>/GETTING_STARTED.md` (tier render), `<dir>/tests/scripts/omt/test_template_e2e.py` (minimal e2e). Sets stack_profile/template_default_tier payloads per flags (defaults: T1→none, T2/T3→mvc_py). Fresh budget baseline via measure-then-set (deterministic rounding). Exit 0 ok / 1 fs-precondition / 2 usage. |
| `main()` dispatch | Accepts `init` alongside check/build. `init` path: parse init flags → load corpus → filter → write tree → print summary (`tier N → <dir>: M records, GETTING_STARTED.md`). Does NOT run this-repo budget loop on the filtered corpus (budgets belong to the TARGET repo's first check). |

## scripts/omt/harnessc.py — onboarding render (design §3.3)

| Op | Pre | Post / returns | Errors |
|---|---|---|---|
| `render_getting_started(c: Corpus, tier: int) -> str` | `c` = TIER-FILTERED corpus (call filter first); `tier` in {1,2,3} | Markdown string: `# Getting started (Tier N)` + tier desc + `## Gates` (rid — payload, order-sorted) + `## Tools` (rid — perm) + `## Flows` (rids) + `## Next steps` (phase→work→complete; T1 has no T2/T3 concepts). PURE. Tier-1 output contains no `nav`/`think`/`kb`/`net` tokens (pinned). | `ValueError` on bad tier |
| `build` emission | existing `build` flow, after the 5 projections | ALSO writes `GETTING_STARTED.md` at repo root from the FULL corpus as tier-3-full (calls filter tier 3 with_net=True then render). This repo's copy is gitignored (not committed). Build output line gains `projection GETTING_STARTED.md: N B`. | IO errors propagate as today (no new handling) |

## scripts/omt/mvc_check.py — profiles (design §4)

| Op | Contract |
|---|---|
| `--profile {mvc_py,mvc_ts,none}` flag | Default: repo `.omt` `@var stack_profile` payload when CWD is inside a repo containing `.meta/META_HARNESS.omt`, else `mvc_py` (backwards compatible; explicit flag beats .omt). |
| `profile=none` | Print `✅ MVC++ disabled (profile=none)`, scan 0 files, exit 0. No findings. |
| `profile=mvc_ts` | Scan `**/*.{ts,tsx}` (excluding node_modules/__pycache__): text/regex mirrors VIEW_IMPORTS_MODEL (view imports model), MODEL_IMPORTS_UI, VIEW_CREATES_CONTROLLER (`new XController(`), GOD_CONTROLLER (>300 lines), SQL_OUTSIDE_DP (same regexes). AST rules skipped (documented: no TS parser in stdlib). JSON shape identical (`files_scanned/errors/warnings/findings`). |
| `profile=mvc_py` | Current behavior byte-identical (all existing `test_mvc_check.py` green untouched). |

## tests/features/feature_059.harness_tiered_template/ — suite (design §5)

| Op | Contract |
|---|---|
| `test_tier_filter.py` | Pure filter vectors: T1/T2/T3 gate+tool sets exact; net excluded default / included with flag+warning path; unknown tier raises. |
| `test_template_vars.py` | check_template_vars matrices: valid/invalid payloads per var; absent vars silent. |
| `test_init_fs.py` | Tmp-dir init T1: files exist; emitted .omt parses and `run_all_checks` green on the FILTERED corpus; GETTING_STARTED Tier-1 has no nav/think/kb/net tokens. Non-empty dir → exit 1; --force still refuses non-empty. |
| `test_mvc_profile.py` | none → exit 0 clean; mvc_ts flags TS view-creates-controller fixture; mvc_py existing behavior (imports current check_file). |
| `test_onboarding.py` | render_getting_started Tier-1/3 content pins; build-emission smoke (render from full corpus contains all 10 gates). |
| `test_budget_pins.py` | This-repo sizes unchanged: nav_index/tool_args/tool_schemas/agents_md equal pre-feature values (hard pins — any growth fails). |

## Global invariants

- **Stdlib-only** — no new deps (harnessc + mvc_check stay stdlib-only by design).
- **Budgets green** — exactly 2 new `@var` (nav-free); 0 new doc/tool/msg; ir_json +~60B only.
- **Never clobber** — init refuses non-empty dirs, with or without --force.
- **Net excluded by default** — Tier 3 without --with-net has no g.net/net_marking/net_paths (DG3).
- **Receipt discipline** — R1 .omt → check → e2e refresh; R2 harnessc.py → check+build → refresh; R3 mvc_check+.gitignore → suite → refresh. One edit per file per round.
