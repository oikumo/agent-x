# PLAN — feature_033: Petri Net Io

> Task type: **minor_feature** · See `omt_agent_guide.md §12` for the required artifacts.

## Objective

`src/agentx/model/petri_net/io.py` + `tests/model/petri_net/test_io.py` implement petri-net-json v1 (FORMAT.md §6–§8) with byte-identity round-trips on the shared examples — stdlib-only, existing library modules untouched, full suite green.

## Steps

- [x] Analysis — FORMAT.md (feature_032) is the contract; library conventions verified (errors.py hierarchy, add-only mutation API, `initial_marking` = M0, test conventions from test_model.py); `pyproject.toml` has no jsonschema → hand-rolled level-1 validation (stdlib-only, D4).
- [x] Design — API `net_to_json`/`net_from_json`/`document_from_json` + `PetriNetDocument`; typed-error hierarchy subclassing `PetriNetError` with pinned precedence; schema-`integer` semantics (integral floats normalized); layout verbatim passthrough with shape validation on both load and dump.
- [x] Implementation — io.py (~290 LOC); existing modules untouched (`__init__.py` included — import via `agentx.model.petri_net.io` directly).
- [x] Testing — 59 tests green; full suite 1639 passed, 0 regressions.

## Artifacts produced

- Requirements: `feature_033.petri_net_io/FEATURE.md`
- Analysis/Design: not required (minor_feature, §12) — contract is `shared/petri-net/FORMAT.md`
- Implementation: `src/agentx/model/petri_net/io.py`
- Testing: `tests/model/petri_net/test_io.py` (evidence in FEATURE.md test row)
