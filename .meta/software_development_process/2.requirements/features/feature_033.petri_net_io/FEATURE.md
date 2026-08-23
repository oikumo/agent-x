# Feature 033: Petri Net Io

> **Status:** [x] Done (2026-08-23)
> **Created:** 2026-08-23
> **WORK.md task:** `- [x] **feature_033.petri_net_io** — DONE 2026-08-23: …` (WORK.md §Tasks)
> **Project:** `.projects/meta/petri_net_studio/PROJECT.md` — roadmap feature #2 (scope LOCKED v1.1); the only `src/`-touching feature.

---

## Summary

Ships `src/agentx/model/petri_net/io.py` — the agentx-side implementation of the
`petri-net-json` v1 contract (feature_032). Public API: `net_to_json(net, *,
layout=None)` (canonical bytes per FORMAT.md §8), `net_from_json(text)`,
`document_from_json(text)` (net + verbatim layout for §5 byte-preserving
round-trips). Loading validates level-1 (shape/types/integer domains,
duplicate-key rejection) then level-2 (semantic rules V1–V6) with typed errors
subclassing the library's `PetriNetError` (errors.py untouched — additive
`PetriNetFormatError` hierarchy with pinned precedence syntax → format →
version → L1 → L2). Serialization is M0-only (`initial_marking`, never the live
marking). Stdlib-only (library D4) — `pyproject.toml` unchanged; all existing
library modules untouched. Fulfills the library's deferred v2 "JSON export"
backlog item.

## Scope (one sentence — what "done" looks like)

Done when `io.py` round-trips the shared examples byte-identically, enforces
FORMAT.md §6 levels 1–2 with typed errors, emits canonical §8 bytes, and the
full agentx suite stays green with 0 regressions.

## Task type

minor_feature (declaration-only artifacts per §12; tests are the deliverable evidence)

---

## Phase artifacts (traceability)

| Phase | Artifact | Path | Status |
|-------|----------|------|--------|
| Requirements | Use case | `2.requirements/.../feature_033.petri_net_io/` (this file) | [x] |
| Analysis | Analysis doc | not required (minor_feature, §12) — semantics anchored in `shared/petri-net/FORMAT.md` §6–§8 | [x] |
| Design | Design doc | not required (minor_feature, §12) | [x] |
| Implementation | Impl notes | `src/agentx/model/petri_net/io.py` | [x] |
| Testing | Test report | `tests/model/petri_net/test_io.py` — **59 tests, all green**; full suite 1639 passed, 0 regressions (1580→1639) | [x] |

Test coverage: canonical dump (ordering, explicit weights/tokens, raw UTF-8,
minimal escaping, empty net, M0-not-live, trailing LF) · load happy path +
document byte-identity round-trip · shared examples as golden canonical bytes ·
layout verbatim incl. extension members + V6 unknown-node tolerance · integral-
float normalization · re-canonicalization of non-canonical input · typed-error
precedence + rule-id messages (V1–V4) · JSON Schema cross-checks
(jsonschema-gated, importorskip).
