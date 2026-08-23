# Analysis 001 — feature_031.petri_net_library: anchor verification + spec reconciliation

> Date: 2026-08-22 · Phase: Analysis · Sources: `.projects/meta/petri_net_library/PROJECT.md` v1.1 (LOCKED) + requirement anchor `.meta/doc/petri_nets/petri_net_python_coding_agents.md` (41 §§, re-extracted from the working tree by 3 parallel research passes: §1–16+§38, §17–35, §36–41+conventions). Findings F1–F10 feed design_001.

---

## 1. Anchor verification (all confirmed)

| # | Anchor | Verified | Notes for design |
|---|---|---|---|
| A1 | PROJECT.md v1.1 locked (D1–D11, sign-off checklist all ticked) | ✅ | Canonical scope; doc §31 code is subordinate where they conflict (F1–F4). |
| A2 | §31 authority clause (doc line 1814) | ✅ | "This is the single authoritative `analysis.py` for v1. All standalone function forms in §12–§16 and §20–§21 are retained for semantic clarity only" — the tiebreaker for every doc-internal conflict. |
| A3 | §10 canonical engine (doc lines 713–869) | ✅ | Complete model-layer reference: `PetriNet` dataclass, 6 fields, full error hierarchy, 16 methods/properties. Implementable as-is. |
| A4 | §38 empty-net liveness literal vs §31 uniform rule (doc lines 2405 vs 1395/2080) | ✅ conflict | §38 says `AnalysisResult(True, True, 0)` for the empty net but `AnalysisResult(True, True, 1)` for places-no-transitions; §31 computes `len(graph.states)` uniformly (= 1 for both single-state graphs). Resolved F1. |
| A5 | `src/agentx/model/` conventions | ✅ | Flat packages; most recent (`rag_v2/`) `__init__.py` is docstring-only, no re-exports → matches locked D2/must-pin #7. Mixed older styles (chat/react re-export) are legacy. |
| A6 | `tests/model/petri_net/test_petri_net.py` placeholder | ✅ | June stub `assertTrue(True)` quoted; deleted when real tests land (locked in-scope #5). Test layout `tests/model/<pkg>/` mirrors src. |
| A7 | `pyproject.toml` | ✅ | `requires-python >=3.14`, `numpy>=2.5.1` present, **sympy absent** (uv.lock grep: 0 matches) → D4 pure-Python nullspace stays zero-dep; pyproject unchanged. pytest 9.1.1, `testpaths=["tests"]`, `pythonpath=["src"]`. |
| A8 | `src/agentx/model/petri_net/` absent | ✅ | Greenfield package; no existing callers. |
| A9 | §30 example nets buildable | ✅ | `TWO_WAY_CYCLE` (p1–t1→p2–t2→p1; CONSERVATION_M0 (1,1), LIVE_BOUNDED_M0 (1,0)), `UNBOUNDED_NET` (p –1→t–2→ p, M0 (1,)), `DEADLOCK_NET` (p=0, consuming t) + `make_net(defn, initial_marking=None)` helper. These are the test fixtures. |
| A10 | §36 v1 checklist / §40 DoD items 1–17,19 | ✅ | 11 v1 toolkit items; DoD 18 (coverability) = v2 stub. Verified verbatim. |
| A11 | feature_001 FEATURE.md (10 lines) | ✅ | "structure must be updated if the crc of the file changes" → add-only API sufficient via rebuild (D11 resolution, PROJECT.md iter 8). |
| A12 | Harness gates on the path ahead | ✅ | tests/ canary (F8), src/ KB consult (F9), TDD node-granularity + JSON testlist gotchas (WORK.md scratchpad). |

## 2. Reconciliation findings (locked spec vs anchor doc → design_001 pins)

- **F1 — Empty-net `is_live` explored_states: §31 wins (pin `AnalysisResult(True, True, 1)`).** §38's literal `AnalysisResult(True, True, 0)` is inconsistent with its own places-no-transitions case (`…, 1`, line 2409) and with §31's uniform `AnalysisResult(True, True, len(graph.states))` (lines 1395/2080); the empty net's graph has exactly one state `()`. §31 is the declared single authority (A2) → no special-case; test asserts `AnalysisResult(True, True, 1)` for the empty net and §38's other literals unchanged.
- **F2 — `max_states`: required keyword, `int | None`, NO default; `None` = explicitly unlimited.** Locked D9 says "required, no implicit default"; §31's reference code shows `int | None = None`. Reconciliation (satisfies both): every exploration signature is `def f(self, *, max_states: int | None) -> …` — the caller must pass it explicitly (no hidden limit), and `None` is the explicit unlimited choice (§28's semantics preserved). Applies to `reachable_markings`, `reachability_graph`, `deadlocks`, `bounds`, `_explore`.
- **F3 — Result dataclass fields: §31 exact (authority clause).** `AnalysisResult(value, complete, explored_states, reason=None)`; `ReachabilityResult(markings, predecessors, complete, explored_states)` — no `reason`; `ReachabilityGraph(states, edges, complete)` — neither; `BoundResult(bounded, bounds, complete, reason=None)` — no `explored_states`; `DeadlockResult(deadlocks, complete, explored_states, reason=None)`. §28's "provide a reason" is carried by the three types that have the field; for the two that don't, `complete=False` + `explored_states == max_states` is the truncation signal. Do NOT add fields beyond §31 (tests pin shapes).
- **F4 — §10 duplicate-name error asymmetry: preserve exactly.** `add_place` duplicate → `DuplicatePlaceError(InvalidModelError)`; `add_transition` duplicate → plain `ValueError`. Four doc-review iterations kept this asymmetry → intentional; tests pin both branches.
- **F5 — Structural queries live on the MODEL (locked in-scope #1), generic-dispatch form.** §24 lists helpers (transition-centric), §10's engine has none; PROJECT.md places `pre_set`/`post_set` in the model layer. Pin: `PetriNet.pre_set(name) -> frozenset[str]` / `post_set(name) -> frozenset[str]` — transition ⇒ inputs/outputs; place ⇒ producers/consumers (§2.1 place-notation); name in BOTH sets (possible — §10 never enforces P∩T=∅) ⇒ `InvalidModelError` (ambiguous); unknown name ⇒ `PetriNetError`.
- **F6 — `place_index` as a property.** DoD wants it "precomputed", §10 builds it locally in `fire_marking`. Pin: `place_index` property `{p: i for i, p in enumerate(self.place_order)}` (same recompute-per-access idiom as `place_order`; net is add-only so no cache-staleness); consumed by `fire_marking` and `incidence_matrix` (§33 basics allow it).
- **F7 — Degenerate-net invariant basis via explicit `n_cols`.** places-no-transitions ⇒ `nullspace(Cᵀ=0×P, n_cols=P)` ⇒ identity basis; transitions-no-places ⇒ `nullspace(C=0×T, n_cols=T)` ⇒ identity basis; empty net ⇒ early-return `[]` in both (§31 guards `n_places==0`/`n_trans==0`). The `n_cols` parameter is mandatory (iter-4 zero-row fix).
- **F8 — tests/ canary at Programming (from feature_030 analysis F6).** First test-file creation under TDD needs `omt_skip{scope:"tests"}` (TDD_BOOTSTRAP doc); subsequent tests/ edits are covered by the red hat. Placeholder `test_petri_net.py` is deleted in the same phase.
- **F9 — `omt_kb_nav` consult (g.kb) required before first src/ edit** at Programming (AGENTS.md NEVER list).
- **F10 — TDD operational gotchas (WORK.md scratchpad, confirmed live).** red/green/refactor at the SAME `test_node`; `omt_tdd{op:testlist}` behaviors MUST be a JSON array; suite currently ~1343 passing (bug_fix.help_command_deepcopy_thread report).

## 3. Confirmed v1 spec surface (extracted; design_001 pins final form)

### 3a. Model layer — `model.py` + `errors.py` (§10 canonical, per A3)

`PetriNet` dataclass fields: `places: set[str]`, `transitions: set[str]`, `inputs: dict[str, dict[str,int]]` (t → {place: weight}), `outputs: dict[str, dict[str,int]]`, `marking: dict[str,int]`, `initial_marking: dict[str,int]`.
Methods/properties: `add_place(name, tokens=0)`, `add_transition(name)`, `add_input(place, transition, weight=1)`, `add_output(transition, place, weight=1)` (**swapped arg order — follow arc direction; call by keyword**), `is_enabled_at(marking, transition)`, `enabled_transitions_at(marking) -> list[str]` (sorted order), `fire_marking(marking, transition) -> tuple[int,...]` (pure; `UnknownTransitionError` → `ValueError` on malformed marking → `TransitionNotEnabledError`), `fire(transition)` (mutable convenience = re-validate + write back), `current_marking() -> tuple[int,...]`, `initial_marking_tuple()`, `marking_to_dict(marking)` (length + non-negativity validated), `reset()` (restores M0, copies), `place_order`/`transition_order` properties (sorted tuples), plus F5 `pre_set`/`post_set` and F6 `place_index`. No convenience wrappers `is_enabled()`/`enabled_transitions()` (D8); no `remove_*` (build-once, §34).
Errors (`errors.py`): `PetriNetError` base; `InvalidModelError`, `UnknownPlaceError`, `UnknownTransitionError`, `TransitionNotEnabledError`, `DuplicatePlaceError(InvalidModelError)`, `DuplicateArcError(InvalidModelError)`.

### 3b. Analysis layer — `analysis.py` (§31 canonical, per A2)

`Marking: TypeAlias = tuple[int, ...]`; constructor-bound `PetriNetAnalyzer(net)` (lock checklist resolution). Shared `_explore(*, max_states)` BFS core (deque, visited set, predecessor map + edge map, truncation finishes the current state's edges then stops; `explored_states` = distinct visited incl. initial). Public: `reachable_markings`, `reachability_graph`, `deadlocks`, `bounds` (all wrap `_explore`, F2 signature); `firing_sequence_to(result, target) -> list[str] | None` (predecessor back-walk, no exploration); `incidence_matrix() -> list[list[int]]` (`C[p][t] = W(t,p) − W(p,t)`, rows=places × cols=transitions, sorted orders); `place_invariants()` / `transition_invariants()` (module-level `nullspace(matrix, n_cols=None)` — Fraction Gauss–Jordan full RREF, free-variable basis — + `_coprime_int_vector` with LCM-scale → content-divide → first-nonzero-positive sign normalization; F7); `transition_liveness(transition, graph)` / `is_live(graph)` (reverse multi-source BFS on the supplied graph; incomplete graph ⇒ `value=None, complete=False, reason=…`; never bare bool); `strongly_connected_components(graph)` (recursive Tarjan on graph states/edges). `coverability.py` = `coverability_tree` stub raising `NotImplementedError` (v2 Karp–Miller).

### 3c. Completeness + no-overclaim contracts (§27–28, §39, D5)

Tri-state everywhere: `True` proven / `False` disproven / `None` unknown. Truncated search ⇒ `complete=False` (+ `reason` where the field exists, F3); NEVER "deadlock-free"/`bounded=True`/"unbounded" from a truncated BFS. `bounds` truncated ⇒ `bounded=None` with observed maxima only. `firing_sequence_to` ⇒ `None` is a proof of unreachability ONLY when `result.complete is True`.

### 3d. Edge-case contracts (§8, §38, D7 — with F1 applied)

Self-loops (net effect `M−1+1` applied via the general equation), no-input sources (always enabled), no-output sinks (consume-and-vanish), parallel transitions (distinct by name), zero-token places legal, empty net allowed (`()` marking; reachable `{()}` complete; deadlocks `((),)`; bounds `bounded=True, {}`; invariants `[]`; `is_live` `AnalysisResult(True, True, 1)` per F1; SCC `[frozenset({()})]`), places-no-transitions (P×0 matrix; P-invariant identity basis; T-invariants `[]`; `is_live` `(True, True, 1)`), transitions-no-places (0×T matrix; P-invariants `[]`; T-invariant identity basis; all transitions always enabled; `is_live` `True` on the single-state graph), duplicate arcs rejected (`DuplicateArcError`; weight change = remove+re-add — n/a in v1 since no remove API; re-adding raises).

### 3e. Module layout (§35, D2 — locked)

`src/agentx/model/petri_net/{__init__.py (docstring-only, no re-exports — A5), model.py, analysis.py, coverability.py, errors.py}`; tests `tests/model/petri_net/{test_model.py, test_analysis.py, test_coverability.py}` replacing the placeholder. NO `graph.py`, NO `simulator.py` (v2).

## 4. DoD mapping (§40 → test plan)

| §40 item | Test coverage (test file) |
|---|---|
| 1–3 places/transitions/weighted arcs | `test_model.py` build + duplicate/validation errors |
| 4–5 enabledness + firing (incl. self-loop, sources, sinks, parallel) | `test_model.py` enabledness/firing/purity/atomicity |
| 6 invalid models raise typed errors | `test_model.py` error matrix (F4 branches) |
| 7 reachability finite | `test_analysis.py` TWO_WAY_CYCLE + §30 a→b net (2 markings, complete) |
| 8 reachability graph | `test_analysis.py` graph states+edges; truncated edges-to-unvisited targets |
| 9 firing sequences | `test_analysis.py` shortest path; `None` on complete vs truncated |
| 10 deadlocks | `test_analysis.py` DEADLOCK_NET `((0,),)` complete; empty net |
| 11 bounds complete finite | `test_analysis.py` LIVE_BOUNDED_M0 `{p1:1, p2:1}` |
| 12 `complete=False` on truncation | every truncated test (matrix below) |
| 13 incidence matrix | `test_analysis.py` known C incl. degenerate shapes |
| 14–15 P/T invariants exact | `test_analysis.py` TWO_WAY_CYCLE `(1,1)` / `(1,1)` + conservation assertions; degenerate identity bases (F7) |
| 16 liveness on complete graphs | `test_analysis.py` live cyclic net vs fire-once-then-dead; incomplete ⇒ `None` |
| 17 SCC | `test_analysis.py` cyclic single-SCC vs deadlocked two-SCC; empty net |
| 18 coverability | **v2** — `test_coverability.py` asserts stub raises `NotImplementedError` |
| 19 positive + "unknown" cases | the per-function matrix (§5 below) |

## 5. Per-function test matrix (locked in-scope #5 — confirmed, feeds omt_tdd testlist)

| Function | Happy | "Unknown"/truncated (`complete=False`, reason where F3 allows) |
|---|---|---|
| `reachable_markings` | TWO_WAY_CYCLE 2-state set | `max_states=1` ⇒ `{M0}` only, `complete=False`, `explored_states=1` |
| `reachability_graph` | known 2-state graph edges | truncated ⇒ edges recorded, targets unvisited, `complete=False` |
| `firing_sequence_to` | shortest `["t1"]` to (0,1) | absent target: `None`; proof only when complete |
| `deadlocks` | DEADLOCK_NET `((0,),)` | truncated ⇒ partial list, never "deadlock-free" claim |
| `bounds` | `{p1:1, p2:1}` proven | UNBOUNDED_NET small `max_states` ⇒ `bounded=None`, `complete=False` (§30 mandate) |
| `incidence_matrix` | exact known C | degenerate 0-col / 0-row shapes (structural, no truncation) |
| `place_invariants`/`transition_invariants` | `(1,1)` bases | degenerate identity bases (F7) |
| `transition_liveness`/`is_live` | live cyclic net `True`; fire-once net `False` | incomplete graph ⇒ `value=None`, `complete=False` |
| `strongly_connected_components` | 1-SCC cyclic, 2-SCC with deadlock | inherited `complete` from supplied graph |
| `coverability_tree` (stub) | raises `NotImplementedError` | — |

## 6. What Analysis does NOT fix (deferred to design_001)

- Exact module-internal structure beyond §31 (docstrings, helper names), `__init__.py` docstring text, test-file class/function names, the omt_tdd testlist JSON node list, per-test assertion details beyond §4–§5, implementation-plan step order within the TDD cycles.

## 7. Conclusion

All 12 anchors verified in the working tree. Ten reconciliations recorded (F1–F10); none reopens locked scope — F1/F2/F3/F4 apply the locked documents' own precedence rules (PROJECT.md canonical; §31 the doc's declared authority), F5/F6 are pins the lock checklist delegated to design. **Ready for Design.**
