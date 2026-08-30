# CURRENT_STATE: meta_harness_concurrent

> Session-by-session log + resume point. Companion to `PROJECT.md` (canonical).
> Newest entry on top. One `## <date>` block per session.

---

## 2026-08-30 (iter 7 — PROJECT.md v0.5: SSOT refinement per user directive + IDEA-005 renumber)

### Done

- **User directive locked as D16** — "the meta harness work must allow concurrency with state management driven by a single petri net; the net, in complement with other files, is the global state single source of truth":
  - **PROJECT.md v0.5** — header/Quick-Start/Summary/Purpose reframed from "additive observability/guidance layer" to **single-Petri-net concurrency state management + global state SSOT**; new "SSOT = net + complement files" map (net file + sidecar + overlay = state · ledger = audit · WORK.md = projection · drift log = reconciliation)
  - **Authority split (amends D3 wording, IDEA-003 §2.1):** the net owns **state**, gates keep **enforcement**, the ledger keeps **audit** — approval ≠ state. All D3/D5–D15 mechanics unchanged (no gate removed, analyzer blocks fires, drift check at every `omt_complete` exit). IDEA-003's category-error caution honored: enforcement never moves into the net; only state ownership does
  - **D17 — WORK.md as deterministic projection** (IDEA-005 adopted): rendered net→md via `omt_net{op:sync}`; hand edits = proposals (md→net); phase-2 **feature_045**, first phase-2 pick, promote-to-core candidate at the feature_041 exit review
  - **D18 — idea numbering collision fixed:** `git mv idea-004-work-md-net-driven-concurrency.md → idea-005-...` (duplicate IDEA-004 vs ledger-mined; both had also claimed slot feature_044 — WORK.md idea now feature_045); internal tags IDEA-004.D* → IDEA-005.D*, three feature_044 refs → feature_045, header renumber note added
  - Roadmap table extended: 3 core (feature_039–041) + **4 optional phase-2** (feature_042 synthesis, feature_043 dashboard, feature_044 mined, feature_045 work-md); success criteria + in-scope updated for SSOT discipline + WORK.md projection surface
  - Op-list conformance to IDEA-002 v4 canonical set (probe/fire/splice/sync/synthesize/invariant) in PROJECT.md summary/purpose/feasibility + `drift`→`invariant` in the WORK.md sketch (idea §3.1 + example file)
- **No `src/` touch; no gate/FSM change** — D1/D2 intact; D3–D15 mechanics intact (authority labels only)

### In progress / Blocked

- _(nothing)_ — roadmap (3 core + 4 optional phase-2) pending user approval (draft → active flip)

### Next

- User approval of the **3-feature core roadmap** (feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency), then scaffold:
  `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`
- Open decision point deferred by design: promote feature_045 (WORK.md projection) into the core at the feature_041 exit review (D17)

### Notes / context

- The refinement is an **authority reframing, not a mechanics change**: every v0.4 design element (sidecar, overlay, ops, conformance, drift, sync hooks) carries over unchanged; what changed is *who owns state* — the net bundle is now declared the single state store, with WORK.md/ledger as projection/audit complements instead of competing state
- `.projects/` changes uncommitted; the idea-file rename is staged (`git mv`), content edits unstaged

---

## 2026-08-30 (iter 6 — IDEA-004 refined to v2, source-verified against the real ledger corpus)

### Done

- **IDEA-004 refined to v2** — `.projects/meta/meta_harness_concurrent/ideas/idea-004-ledger-mined-behavioral-net.md` aligned with the locked architecture (PROJECT.md v0.4 D1–D15, IDEA-002 v4, IDEA-003):
  - **Ledger = rotated STORE, not one file** — measured this session: `ledger.jsonl` (88) + `ledger-202608.jsonl` (934) + `ledger-202607.jsonl` (628) = 1,650 records, 9 kinds. EXTRACT globs the store; mining window ≠ gate truth window (`@state ledger`: "hot + latest archive")
  - **Correlation is sparse → attribution is the miner's key design decision** — 62% of records lack `feature`; **skips carry `feature` on 0 of 229 records**; 13 features with full 5-phase flows, median trace 3. Open item #1 → RESOLVED (design): case = feature + session-context attribution (`attributed` flag), session = secondary friction view
  - **`mine` positioned on the v4 canonical ops taxonomy** (IDEA-002 §5.0, closed at feature_039) as the *single gated extension point* at feature_044: one enum value + one `miner.py` + one switch case, still ONE `omt_net` registration (F5)
  - **Open items #1–#7 all RESOLVED (design, v2)** — incl. new evidence-backed #7 (rotation + seed-ts tolerance); decision log extended D7–D12; draft-artifact scheme (`META_NET.mined.petri.json` + mined sidecar + `mine.draft.manifest.json`, runtime state per D14); two conformance pins (9 engine vectors guard serialization + 10th golden miner case)
  - Phase-revisit loops + duplicate `complete` (feature_022 ×16) confirmed as **measured** phenomena, folded into the α-variant honest limits
- Source facts verified: ledger schema XREF_LEDGER line (under-specifies real kinds — omits q/project/project_link); `.meta/.omt/*` git-ignored (D14 confirmed; META_NET.petri.json would be ignored)

### In progress / Blocked

- _(nothing)_ — idea docs mature; core roadmap (feature_039–041) still unapproved (draft → active flip pending)

### Next

- User approval of the **3-feature core roadmap** (feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency)
- Scaffold first feature: `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`
- Optional: one-line candidate note for `feature_044.mined_behavioral_net` in PROJECT.md's roadmap table (currently lists only feature_042/043 as phase-2; IDEA-004 stays a candidate until core proves valuable)

### Notes / context

- All changes in `.projects/` (IDEA-004 v2 rewritten + CURRENT_STATE.md) — no `src/` touch, D1/D2 intact
- v2 verdict: feasible — mostly reuse + α-miner + attribution; the corpus is young/sparse (13 full flows), so v1 observed net is small-but-real and compounds as the ledger grows

---

## 2026-08-30 (iter 6 — evaluation & doc audit)

### Done

- **Evaluated the project doc against the repo** — audited PROJECT.md + ideas/ claims vs on-disk facts:
  - Library test count corrected **99 → 158** (`uv run pytest tests/model/petri_net -q` → 158 passed) in PROJECT.md (feasibility table + references), this log, and IDEA-001.
  - Roadmap/per-roadmap slugs aligned to the `feature_0xx.` convention (`feature_039.adaptive_net_engine` … `feature_043.meta_net_dashboard`) — quick-start + D9 already used it; the tables had leading-dot style.
  - **IDEA-003 added to PROJECT.md References** — body cites it (additive observability layer, §6 re-scope) but References listed only IDEA-001/002.
  - Scope line now names all three idea docs as design basis (not just the pause file).
  - Sentinel-bridge claim sharpened to concrete examples (feature_031/034/035/036) — feature_037/038 carry no `tests/features/` dir.
  - Tool-surface row updated to match D10 (single `omt_net` tool with ops, not 4 registrations).
  - Idea-003 header date fixed 2026-08-31 → 2026-08-30 (file mtime + session date).
- **No `src/` touch; no gate/FSM change** — D1/D2/D3 intact.

### In progress / Blocked

- _(nothing)_ — same as iter 5: architecture decisions locked; roadmap (3 core + 2 optional) pending user approval.

### Next

- User approval of the **3-feature core roadmap** (feature_039/040/041), then scaffold:
  `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`.

### Notes / context

- Audit corrected only *facts + consistency* in the v0.4 doc (99→158, slug style, IDEA-003 reference, sentinel examples); no design decisions changed.
- `.projects/` + `opencode.jsonc` remain uncommitted; `ideas/` untracked (incl. idea-003).

---

## 2026-08-30 (iter 5 — idea-001 refined + PROJECT.md locked to resolved architecture)

### Done

- **IDEA-001 refined** — all four open items resolved with concrete decisions:
  1. **Live-marking persistence** → sidecar (`net_state.sidecar.json`), NOT v2 format (avoids ripple to proven v1 io/conformance/studio)
  2. **Net-vs-gates reconciliation** → drift check at every `omt_complete` exit; ledger primary, net blocks fires; `harness.net.drift.jsonl`
  3. **Analysis authority** → locked: in-repo parity engine only (PIPE/TINA cannot read `petri-net-json`)
  4. **Roadmap scoped** → 3-feature core (feature_039/040/041) + 2 optional phase-2 (feature_042/043)
- **PROJECT.md updated to v0.4** — locked all decisions:
  - Summary/Purpose reframed: "additive observability/guidance layer" (not "control plane")
  - Roadmap table: 3 core + 2 optional with correct deliverables/dependencies
  - Decisions log extended D5–D15 (11 new locked decisions from IDEA-001/002)
  - References updated to include both idea docs + source-verified assets
  - In/out of scope sharpened (no v2 format, no free-form synthesis, no live dashboard, net artifacts = runtime state git-ignored)
- **IDEA-002 v3 already mature** — all 9 open items resolved in design (§11), composition overlay (§1.4), sync hooks, derived ordering rebase, subnet lifecycle, net artifacts as runtime state

### In progress / Blocked

- _(nothing)_ — architecture decisions locked; idea docs mature; roadmap proposal updated in PROJECT.md

### Next

- User approval of the **3-feature core roadmap** (feature_039.adaptive_net_engine, feature_040.net_composition_supervisor, feature_041.resource_places_concurrency)
- Scaffold first feature: `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`

### Notes / context

- All changes in `.projects/` (PROJECT.md, CURRENT_STATE.md, ideas/) — no `src/` touch, D1/D2 intact
- IDEA-001 now has concrete resolutions (was 4 open blockers); IDEA-002 v3 has all 9 items resolved in design
- The 3-feature core is the minimal shippable increment; phase-2 items gated on core value proof

---

## 2026-08-30 (iter 4 — idea-002 v3, source-verified hardening)

### Done

- **IDEA-002 refined to v3** — second refinement pass, source-verified this time. Open items 6–9 → **RESOLVED (design)**:
  - **#6 Net↔reality sync** — `omt_net_sync` op; bootstrap + re-sync hooked to `project.py` lifecycle (`new|link|log|status|close|archive|reopen|backfill|sync` — verified CLI) + `new_feature.py --project` link; sync = deterministic proposal through the splice path, never silent (D4).
  - **#7 `place_order` stability** — order is *derived* (verified `place_order = tuple(sorted(...))` in `model.py`); tuple → name map at load; structure-changing splices rebase by name in-transaction; revision mismatch → refuse + `--repair` replay from ledger mutation.
  - **#8 Subnet lifecycle** — library has **no disable primitive** (verified); `disable` ≡ remove-with-policy + `kind:"net_disable"` record; undo = inverse splice replay; `project.py close/archive` triggers subnet disable.
  - **#9 Composition overlay persistence (NEW)** — gap found: where subnet membership/ports/disabled live → new §1.4 `supervisor.overlay.json` beside the v1 union net (v1 stays pure flat union; three-file atomic transaction).
- **Source facts verified & fixed:** `analysis.ts` = 509 lines (doc said 510); 9 conformance vectors re-confirmed by file listing; ledger example conformed to the real `.meta/.omt/ledger.jsonl` (flat `kind`-discriminated; verified kinds: phase/complete/skip/q/think_consult/project*); `.meta/.omt/*` git-ignored → net artifacts = runtime state (D14); "control-plane" wording removed from §5/§8.1.

### In progress / Blocked

- _(nothing)_ — idea doc mature; still candidate (roadmap feature_039–043 unapproved).

### Next

- User review of v3 (esp. §1.4 overlay schema + §11 #6 sync trigger wiring — both flagged "validate at feature_039/040 design").
- Approve roadmap + scaffold `feature_039.adaptive_net_engine`.

### Notes / context

- All verification via read-only source inspection (model.py/analysis.py/io.py/omt_q.ts/project.py/harnessc.py/.gitignore/ledger.jsonl). No commits made; `.projects/` changes remain uncommitted (CURRENT_STATE.md modified + `ideas/` untracked).

---

## 2026-08-30 (iter 3 — idea-002 v2 refinement)

### Done

- **IDEA-002 refined to v2** — `.projects/meta/meta_harness_concurrent/ideas/idea-002-compositional-net-of-nets-architecture.md` aligned with the project's current understanding:
  - **IDEA-003 reframing adopted:** summary/§1/§8 now frame the net-of-nets as an **additive observability/guidance layer** (net informs/guides/blocks via analyzer; `META_HARNESS.omt` + phase FSM + ledger remain PRIMARY approval authority — D3, IDEA-003.D1/D2). Supersedes the v1 "the META HARNESS control plane is a flat Petri net" framing.
  - **IDEA-001 open items carried:** §7 sidecar schema conformed to IDEA-003 §3.1 (`net_state.sidecar.json` `{live_marking, revision, updated_at}` + atomic two-file write with rollback); §8 drift check now "every `omt_complete` exit" with `harness.net.drift.jsonl` records.
  - **Roadmap numbered** per PROJECT.md: feature_039.adaptive_net_engine … feature_043.meta_net_dashboard (§10).
  - **Open items 1–5 marked RESOLVED (design)** per IDEA-003 §4; three genuinely remaining items added (§11): net↔reality sync (#6, High), `place_order` stability (#7, Medium), subnet lifecycle/archive policy (#8, Medium).
  - **Decision log extended** D8–D10 (additive-layer adoption, resolved-in-design items, remaining items deferred to feature_040/041 design).

### In progress / Blocked

- _(nothing new)_ — idea still candidate; roadmap proposal (feature_039–043) still unapproved (draft → active flip pending user go).

### Next

- User review of idea-002 v2 (esp. §11 items 6–8 — net↔reality sync needs a concrete proposal before feature_040).
- Then approve roadmap + scaffold `feature_039.adaptive_net_engine` (`uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`).
- Optionally: fold the additive-layer framing into PROJECT.md Summary/Purpose (currently "control plane" wording, superseded by IDEA-003).

### Notes / context

- Grounded: `FORMAT.md` §1 confirmed the live-marking gap verbatim ("structure + initial marking only"); `git status` shows only `.projects/` changes (CURRENT_STATE.md modified, `ideas/` untracked). No `src/` touch — D1/D2 intact.

---

## 2026-08-30 (iter 2 — idea: file-backed net control)

### Done

- **Critical re-scoping captured** — user clarified (via Q&A) that control is by a **REAL persisted Petri-net FILE** in the repo's own `petri-net-json` v1 format, where the file is the **authority** and analysis feeds back into decisions. This dissolves the prior "in-memory mirror / journal not controller" weakness.
- **Idea doc created** — `.projects/meta/meta_harness_concurrent/ideas/idea-001-file-backed-net-control.md`: intent workflow (observe→decide→fire→re-verify off the file), format decision (repo v1, not PNML), feasibility grounded in the actual `PetriNet`/`PetriNetAnalyzer` API + io/conformance assets, four ranked open items, honest limits.

### In progress / Blocked

- Four open items must be settled before building (ranked in the idea doc): **(1) live-marking persistence** (`petri-net-json` v1 has NO current-marking snapshot — the #1 blocker; v2-snapshot vs sidecar decision), **(2) net-vs-gates reconciliation rule** (ledger/phase-FSM/TDD-FSM still own real approval per D3), **(3) plain statement that "external analysis" = in-repo parity engine, not an external tool** (repo format can't be read by PIPE/TINA), **(4) scope down to a core 3-part build** (file+marking io, fire/probe/invariant ops + parity, ledger/gates reconciliation); synthesis + dashboard are optional phase-2.

### Next

- Resolve open item 1 (live-marking persistence: v2 format extension vs sidecar) — it decides the architecture.
- Then decide whether to promote this idea into a locked project decision + scaffold the core feature (`feature_039.*`).
- Optionally update `PROJECT.md` Summary/Purpose to reflect the file-backed control mechanism (parts superseded by idea-001).

### Notes / context

- Session also verified feasibility claims: library stdlib-only; `PetriNet`+`PetriNetAnalyzer` full API present (158 tests); `petri-net-json` v1 io round-trip + 9 conformance vectors; `omt_q.ts` = 817-line single-tool template; feature slots 039+ free.

---

## 2026-08-30 (iter 1 — project definition)

### Done

- Resumed from `.sandbox/pause_2026-08-30.md` + PROJECT.md (was bare v0.1 scaffold).
- **Project definition written (v0.2)** — filled New Session Quick Start / Summary / Purpose (what it is / NOT) / Scope & success criteria / Status / Decisions log / References.
- **D1 locked (user directive):** meta harness only scope, **not agentx** — no `src/agentx/`, no `internal_state`, no feature_001 work under this project.
- **Feasibility section added (v0.3)** — verdict "feasible", grounded: parity-without-import pattern proven by petri-net-studio (feature_035/036), `omt_q.ts` as the single-tool-with-ops template (F5 mitigation), studio UI assets for the dashboard, risks F1–F7 + mitigations, per-roadmap feasibility table, guardrails (no real concurrency / no library extension / no free-form synthesis).

### In progress / Blocked

- _(nothing)_ — roadmap proposal written but unapproved; first feature not yet scaffolded (draft → active flip pending).

### Next

- User approval of the roadmap proposal (feature_039.adaptive_net_engine … feature_043.meta_net_dashboard).
- Then: `uv run scripts/omt/new_feature.py "adaptive net engine" --type minor_feature --project meta_harness_concurrent`.

### Notes / context

- The pause file claimed PROJECT.md §§1-10 architecture deep-dive was complete — on disk it was NOT (bare template); the deep-dive substance lives in `.sandbox/pause_2026-08-30.md`. Restore deeper architecture iterations later from that file; this iter focused on the definition layer only, per user instruction.
- WORK.md pause line still present (cleared when real feature work starts).
