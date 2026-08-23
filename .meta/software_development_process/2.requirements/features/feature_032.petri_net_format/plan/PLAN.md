# PLAN — feature_032: Petri Net Format

> Task type: **minor_feature** · See `omt_agent_guide.md §12` for the required artifacts.

## Objective

`shared/petri-net/` ships the petri-net-json v1 contract: FORMAT.md spec + JSON Schema + ≥3 canonical examples — schema validates all examples; examples are canonical bytes per spec §8.

## Steps

- [x] Analysis — semantics anchored to `src/agentx/model/petri_net/model.py` (places/transitions/arcs/M0, edge-case policy); locked project decisions D5–D7 applied.
- [x] Design — document shape (format/version/places/transitions/arcs + optional UI-namespaced layout), validation split (schema level 1 + semantic rules V1–V6 level 2), canonical serialization rules §8 (pinned member order, code-point sorting, integer-only numbers, minimal escaping), versioning policy §9.
- [x] Implementation — `shared/petri-net/FORMAT.md`, `petri-net-json-v1.schema.json`, `examples/{hello,producer_consumer,weighted_reaction}.json`, `shared/META.md`.
- [x] Testing — 32/32 validation checks (schema self-valid; examples valid + canonical + idempotent; 13 negative docs rejected; examples construct real PetriNets with expected M0/enabled sets).

## Artifacts produced

- Requirements: `feature_032.petri_net_format/FEATURE.md`
- Analysis: not required (minor_feature, §12)
- Design: `shared/petri-net/FORMAT.md` (the format design IS the spec)
- Testing: validation evidence recorded in FEATURE.md test-report row (one-off script, /tmp — pytest coverage arrives with `.petri_net_io`, Vitest conformance with `.studio_v3_graph`)
