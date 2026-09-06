# Analysis 001 — Tiered template + stack profiles + onboarding (feature_059)

> meta_harness_6 Wave 5 D1+D2+D3 · 2026-09-06 · major_feature (Analysis)

## 1. Live state (measured 2026-09-06, net rev 57, HEAD clean)

- `.omt`: 261 records, check 0 errors. Budgets: agents_md 2918/2944 (26B),
  tool_args 2278/2304 (26B), tool_schemas 1770/1792 (22B),
  nav_index 63920/64000 (80B), ir_json 19912/20480 (568B),
  gates 10/12. All green — tightest headrooms are tool_args/schemas/nav/agents.
- `harnessc.py` (1615 lines): subcommands **check|build only** — no `init`.
  `main()` rejects anything else with usage (exit 2). Projections: IR JSON,
  AGENTS.md, nav.index.jsonl, opencode.jsonc blocks, harness.report.
- `mvc_check.py` (245 lines): Python-only, AST+regex, scans `src/agentx`
  by default. No `--profile`, no TS mode, no disable flag.
- `.meta/templates/` (8 files): analysis/design/feature/operation_spec/
  project/test_plan/use_case/current_state — process-doc templates only,
  no harness scaffold template.
- Eval spec: `.sandbox/meta_harness_6_evaluation.md` §5 D1–D3 + PROJECT.md
  §The program Wave 5 + DG3 (Tier 3 excludes net until multi-session proven).

## 2. What D1+D2+D3 must deliver (from eval §5)

| Item | Eval text | Acceptance (PROJECT.md §Scope) |
|---|---|---|
| D1 `harness_tiered_template` | `harnessc init --tier 1\|2\|3`: T1 deny/protect/phase(decl-only)/TDD-majors/ledger+skip (~80% value, stack-agnostic); T2 +nav/thoughts/KB/budgets/projects/workflows; T3 +net/receipt/think-hard/MVC (experimental). Init = `@var` re-pointing + state reset + fresh budget baseline. | `harnessc init --tier 1` produces WORKING Tier-1 harness in fresh tmp repo (deny/protect/phase/TDD-majors/ledger live; e2e of the template passes). |
| D2 `stack_profiles` | `@profile mvc_py\|mvc_ts\|none`; mvc_check TS mode or disabled under `none` (current rules Python/TUI-specific). Rides D1. | mvc_check honors profile: `none` disables (exit 0 clean), `mvc_ts` runs TS-mode checks (or documented stub), default `mvc_py` = current behavior. |
| D3 `generated_onboarding` | `harnessc build` emits GETTING_STARTED.md per tier from active @gate/@tool/@flow. Rides D1. | Fresh-repo `build` emits GETTING_STARTED.md naming the tier's gates/tools/flows; Tier-1 file is short (no T2/T3 concepts). |

DG1/DG3 constraint: Tier 3 EXCLUDES net artefacts by default (051 deferred;
C1 predicate is the shipped net story). Tier 3 ships net/receipt/think-hard/
MVC as opt-in experimental flags, documented as such.

## 3. Budget strategy (the tight-budget design driver)

- `render_nav_index` indexes ONLY doc/flow/xref/tool/msg. **`@var` records
  are nav-free** (precedent: feature_057 B1 `@budget` nav-free note).
- `render_agents` renders docs/flows/deny/protect/gates/tool-count only —
  new `@var` costs **0 agents_md, 0 tool_args, 0 tool_schemas**.
- Only cost of a `@var`: ir_json payload bytes (~50–80B each; headroom 568B).
- KINDS is a closed set without `profile` — adding a `@profile` kind means
  touching SCHEMA + check_schema + build_ir + e2e shape pins. **Rejected:**
  D2 rides a `@var stack_profile` (values in payload, validated in
  mvc_check + a `check_` function), zero compiler-kind churn.
- D1 tier table lives in **Python code** (`TIERS` dict in harnessc.py) +
  `# D1:` comments in the .omt (parser-ignored → 0 nav cost, E1 precedent).
  New `.omt` records: exactly two `@var` (template tiers pointer +
  stack_profile) — both nav-free. No new @doc/@tool/@msg → nav_index,
  tool_args, tool_schemas, agents_md untouched.
- D3 `GETTING_STARTED.md` is a **new projection file** (like harness.report),
  rendered from the already-loaded Corpus — no new records, no budget impact
  on this repo (the emitted file lives in the TARGET repo, and in this repo
  is gitignored-or-test-tmp only).

## 4. Tier contents (concrete record sets)

Tier 1 (stack-agnostic core, ~80% value):
deny.* (all 10) · protect.* (5) · always.* (5) · phase decl_only/design_req/
docs_none · fsm phase + fsm tdd + hat.* (5) · pred path_in/cmd_match/
ledger_has/session_flag/file_has/fsm_allows (subset — no receipt_fresh,
no net_marking, no risk_high) · gates: g.protect/g.phase/g.tests/g.tdd_*
(deny/phase/tests/TDD only — no g.nav/g.think/g.kb/g.net/g.receipt/g.mvcc)
· state ledger/thoughts? (ledger yes, thoughts minimal) · tool omt_phase/
omt_skip/omt_tdd/omt_complete/omt_status (5 — no nav/think/kb/net/q) ·
budget ledger/unlock/tdd_core subset (fresh baseline, small caps) · var
ledger_path/thoughts_path/unlock_window/scaffold/harnessc/edit_tools/
stack_profile=none default.

Tier 2 (+ long-lived repo knowledge): + pred receipt_fresh? (no — receipt is
T3) + g.nav/g.think(soft?)/g.kb · tools omt_nav/omt_think/omt_kb_nav/omt_q ·
doc nav.*/think.*/kb.* · flow search/consult chains · budgets nav_index/
tool_args/tool_schemas · vars doc_paths/thought_pattern/nav paths · workflows
+ projects_home docs.

Tier 3 (+ experimental, opt-in, net EXCLUDED by default per DG3): + g.receipt
+ think-hard + MVC (mvc_check) + net artefacts ONLY behind `--with-net`
(explicit opt-in, warns it needs multi-session proof). Receipt-guard +
think-hard ship as experimental flags.

## 5. Risks / open questions for Design

1. e2e of the template: the existing e2e (`test_omt_harness_e2e.py`) pins
   THIS repo's shape (261 records, 18 checks). The Tier-1 template needs its
   OWN minimal e2e (fresh tmp repo: init → check green → build green →
   deny fires → phase gate fires → TDD RED/GREEN cycle). Where does that
   e2e live — new test file (canary!) vs `harnessc init --self-test`?
2. `init` target semantics: existing non-empty dir = error (never clobber);
   `--force`? (Rejected by default — init is for FRESH repos; document it.)
3. GETTING_STARTED.md per-tier rendering: derive from Corpus (gates/tools/
   flows present in the FILTERED tier corpus, not the full one) — build the
   tier corpus first, then render. Same code path serves `init` (target repo)
   and `build` (current repo, Tier-3-full).
4. mvc TS mode depth: full TS AST checks (needs tree-sitter — NOT stdlib,
   violates harnessc stdlib-only rule) vs regex/text checks mirroring the
   Python text rules (stdlib-safe). **Decision for Design: text/regex mode.**
