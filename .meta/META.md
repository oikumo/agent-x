# .meta — Central Metadata Repository (grep-friendly)

> **Purpose**: Central repository for all development metadata, documentation, and process artifacts following OMT++ methodology.
> **Process enforcement**: `AGENTS.md` (root, generated from `.meta/META_HARNESS.omt`) — query rules on demand via `omt_nav`.

---

# SECTION:STRUCTURE — Directory Tree (grep:STRUCTURE_)
```
.meta/
├── META.md                        # This file — overview
├── META_HARNESS.omt               # OMT-HDL corpus (single source; .md = generated stub)
├── doc/                           # Technical documentation, current-state (index: doc/README.md)
├── software_development_process/  # OMT++ SDLC: phase dirs 1.project…7.integration (META.md each) + omt_agent_guide.md
├── proof_of_concepts/             # Technical feasibility validation
└── prototypes/                    # UI mockups & interaction flows
```

---

# SECTION:DIRECTORIES — Directory Descriptions (grep:DIR_)
**DIR_DOC**: `doc/` — Maintainable technical documentation (current-state reference). Start at `doc/README.md`. Covers: architecture (MVC++), feature catalog, subsystem deep dives, runtime data flows, persistence, extension how-to. Updated on code changes; NOT historical.

**DIR_SDP**: `software_development_process/` — Complete OMT++ methodology implementation. Every feature/bugfix moves through phases with visible artifacts:
| Phase | Dir | Purpose |
|-------|-----|---------|
| 1 | `1.project/` | Feasibility studies - "should we do this?" |
| 2 | `2.requirements/` | WHAT users need (use cases, operations, analysis) |
| 3 | `3.analysis/` | Domain concepts, UI behavior specs |
| 4 | `4.design/` | HOW to implement (architecture, components, interfaces) |
| 5 | `5.implementation/` | Source code following MVC++ + Abstract Partner |
| 6 | `6.testing/` | Three-stage testing (unit → integration → system) |
| 7 | `7.integration/` | End-to-end workflow validation |

**DIR_POC**: `proof_of_concepts/` — Technical feasibility validation before full implementation (LLM providers, DB schemas, architectural patterns, risk reduction).

**DIR_PROTO**: `prototypes/` — Rapid UI mockups & interaction flows (screen layouts, command patterns, UX experiments, Abstract Partner interfaces).

---

# SECTION:KEY_DOCS — Key Entry Points (grep:KEY_)
| File | Role |
|------|------|
| `.meta/META_HARNESS.omt` | OMT-HDL process corpus (single source) — query via `omt_nav`; `.md` is a generated stub |
| `.meta/software_development_process/omt_agent_guide.md` | Complete OMT++ methodology (source of truth) |
| `.meta/doc/README.md` | Technical documentation index + maintenance guide |
| `.meta/software_development_process/1.project/PROJECT_SUMMARY.md` | High-level project overview |

---

# SECTION:WORKFLOW — How to Use (grep:WORKFLOW_)
**WORKFLOW_NEW_FEATURE**:
1. Start in `software_development_process/1.project/` — assess feasibility
2. Move to `2.requirements/` — define use cases and operations
3. Proceed through Analysis → Design → Implementation → Testing
4. Create artifacts in each phase directory before coding

**WORKFLOW_BUG_FIX**:
1. Identify affected component in `5.implementation/`
2. Check `6.testing/` for existing test coverage
3. Follow OMT++: Analysis (root cause) → Design (fix approach) → Implementation → Testing

**WORKFLOW_LEARN_CODEBASE**:
1. Read `AGENTS.md` (root) — process enforcement quick reference (details: `omt_nav` on `.meta/META_HARNESS.omt`)
2. Read `.meta/doc/README.md` — current-state technical docs (arch, features, subsystems)
4. Read `software_development_process/omt_agent_guide.md` — methodology
5. Review `1.project/PROJECT_SUMMARY.md` — high-level overview
6. Explore phase directories for development workflow

---

# SECTION:OMT_QUICK — OMT++ Methodology Quick Ref (grep:OMT_)
**PHASES** (never skip): ANALYSIS → DESIGN → PROGRAMMING → TESTING
**PATHS** (model both): STATIC (classes, components, files) + FUNCTIONAL (use cases, sequences, interactions)
**ARCHITECTURE**: MVC++ (strict layer separation) + Abstract Partner (interface-based View↔Controller) + Command Pattern (top-level dispatch) + Database Partner (all SQL in DP classes)

---

# SECTION:RELATED — Related Root Files (grep:REL_)
| File | Role |
|------|------|
| `WORK.md` (root) | Active task tracking |
| `AGENTS.md` (root) | Agent behavior rules + process enforcement |
| `README.md` (root) | User-facing project overview |

---

# SECTION:XREF — Cross-References (grep:XREF_)
XREF_HARNESS: `.meta/META_HARNESS.omt` — query via `omt_nav` (tag types: SECTION/RULE/ERR/WRN/CMD/QUICK/XREF/TT/PHASE/FEAT)
XREF_GUIDE: `omt_agent_guide.md` — §2(Phase), §11.4(TDD), §12(Artifacts), §13(Checklist), §14(Do/Don't), §16(Mistakes)
XREF_DOC: `.meta/doc/` — architecture.md, features.md, subsystems.md, data_flow.md, persistence.md, extending.md
XREF_SDP: `software_development_process/` — phase dirs 1-7 + META.md each
