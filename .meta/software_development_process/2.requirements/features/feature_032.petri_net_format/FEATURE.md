# Feature 032: Petri Net Format

> **Status:** [x] Done (2026-08-23)
> **Created:** 2026-08-23
> **WORK.md task:** `- [x] **feature_032.petri_net_format** — DONE 2026-08-23: …` (WORK.md §Tasks)
> **Project:** `.projects/meta/petri_net_studio/PROJECT.md` — roadmap feature #1 (scope LOCKED v1.1)

---

## Summary

Defines `petri-net-json` v1 — the versioned JSON exchange format for weighted P/T
Petri nets that is the ONLY coupling between the agentx Python library and the
planned Petri Net Studio web app (project decision D5). Ships the spec
(`FORMAT.md`: document shape, naming/validation rules V1–V6, semantics by
reference to the tested library, canonical-serialization rules, versioning
policy), the JSON Schema (Draft 2020-12), and three canonical-form example nets —
all under `shared/petri-net/`, plus a `shared/META.md` dir manifest. Format is
stricter than the library (names unique across places ∪ transitions — D6) and
pins byte-identical canonical serialization for git-friendly diffs (D7).

## Scope (one sentence — what "done" looks like)

Done when `shared/petri-net/` contains the FORMAT.md spec, JSON Schema v1, and
≥3 example nets, the schema validates all examples, and the examples are
canonical bytes per the spec's serialization rules.

## Task type

minor_feature (declaration-only artifacts per §12; validation evidence below)

---

## Phase artifacts (traceability)

Per `omt_agent_guide.md §12`, fill only the rows your task type requires. Link each
artifact as it is produced so WORK.md → this file → every phase doc stays navigable.

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_032.petri_net_format/` (this file) | [x] |
| Analysis | Analysis doc | not required (minor_feature, §12) | [x] |
| Design | Design doc | not required (minor_feature, §12) — format design pinned in `shared/petri-net/FORMAT.md` itself | [x] |
| Implementation | Impl notes | deliverables: `shared/petri-net/{FORMAT.md, petri-net-json-v1.schema.json, examples/{hello,producer_consumer,weighted_reaction}.json}` + `shared/META.md` | [x] |
| Testing | Test report | validation run 2026-08-23: 32/32 checks — schema Draft 2020-12 self-valid; 3/3 examples schema-valid + V1–V4 clean + on-disk bytes canonical + canonicalize idempotent; 9 schema-negative + 4 semantic-negative docs rejected; 3/3 examples construct real `PetriNet` via the FORMAT.md §7 algorithm (hello: enabled=[t1]; producer_consumer: enabled=[produce]; weighted_reaction: enabled=[react]) | [x] |

**Naming convention (enforced by `new_feature.py`):** phase docs are
`analysis_NNN_<topic>.md`, `design_NNN_<topic>.md` — incrementing `NNN`, lower_snake topic.
Do **not** create ad-hoc `*_PROOF.md` / `*_SUMMARY.md` files; fold proofs into the test report.
