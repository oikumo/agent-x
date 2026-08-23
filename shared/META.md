# shared/ — Cross-implementation contracts (grep-friendly)

> **Purpose**: Artifacts shared across the repo's independent implementations (Python library, browser tools). Only *contracts* live here — specs, schemas, examples, golden vectors. Never code: no implementation may import across the boundary (petri_net_studio D5).

---

# SECTION:DIRECTORIES (grep:DIR_)

**DIR_PETRI_NET**: `petri-net/` — the petri-net-json format, the ONLY coupling between `src/agentx/model/petri_net/` (Python) and `tools/petri-net-studio/` (TypeScript). Start at `petri-net/FORMAT.md` (spec v1, canonical-serialization rules §8); schema `petri-net/petri-net-json-v1.schema.json`; `petri-net/examples/` (canonical-form example nets); `petri-net/conformance/` (planned — generated golden vectors, feature `.petri_net_io`).

---

# SECTION:RULES (grep:RULE_)

**RULE_CONTRACT_ONLY**: documents only (spec/schema/examples/vectors) — no buildable code, no imports across implementations.

**RULE_CANONICAL_EXAMPLES**: example/vector JSON files MUST be canonical bytes per `petri-net/FORMAT.md` §8 (they double as golden canonical output).
