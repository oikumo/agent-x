# petri-net-json — Format Specification v1

> **Status:** LOCKED (petri_net_studio scope v1.1, 2026-08-23) · **Version:** 1 · **Schema:** `petri-net-json-v1.schema.json`
> **Contract role:** the ONLY coupling between the agentx Python library (`src/agentx/model/petri_net/`) and Petri Net Studio (`tools/petri-net-studio/`) — project decision D5. No code crosses this boundary; only documents in this format do.

---

## 1. Purpose

`petri-net-json` is the exchange format for weighted Place/Transition Petri nets
`N = (P, T, F, W, M0)`. It is:

- **the contract** — one spec, one schema, versioned from day one; both implementations
  (Python `io.py`, TypeScript engine) validate against it (D5);
- **stricter than the library** — the runtime model tolerates ambiguity the format
  forbids (D6), because a file format must never need disambiguation;
- **canonical** — one deterministic serialization, byte-identical across
  implementations, git-friendly to diff (D7).

The format describes **structure + initial marking only**. It carries no analysis
results, no current-marking snapshots, no semantics definitions — semantics are
inherited by reference from the Python library (§7).

## 2. Conformance vocabulary

The key words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are to be interpreted
as in RFC 2119. "Implementation" = any loader or writer of this format
(Python `agentx.model.petri_net.io`, the Studio TS engine, or a third party).

## 3. Document shape

A document is a single JSON object (RFC 8259) with these top-level members, in this
order in canonical form (§8):

| Member | Type | Required | Meaning |
|---|---|---|---|
| `format` | string | **yes** | Constant `"petri-net-json"`. Identifies the format family. |
| `version` | integer | **yes** | Constant `1` for this version. Versioning policy: §9. |
| `places` | array of Place | **yes** (may be empty) | The place set P with initial tokens. |
| `transitions` | array of Transition | **yes** (may be empty) | The transition set T. |
| `arcs` | array of Arc | **yes** (may be empty) | The flow relation F with weights W. |
| `layout` | object | no | Optional, UI-namespaced visual state (§5). Semantically inert. |

No other top-level members are allowed (schema: `additionalProperties: false`).
Extensions require a version bump (§9).

## 4. Structural core

### 4.1 Place

| Member | Type | Required | Rule |
|---|---|---|---|
| `name` | string | yes | `minLength: 1`. See naming rules below. |
| `tokens` | integer | yes | `≥ 0`. The initial marking M0 at this place. |

### 4.2 Transition

| Member | Type | Required | Rule |
|---|---|---|---|
| `name` | string | yes | `minLength: 1`. |

### 4.3 Arc

An arc connects exactly one place and one transition, in either direction.

| Member | Type | Required | Rule |
|---|---|---|---|
| `source` | string | yes | Name of an existing node (§6 V2). |
| `target` | string | yes | Name of an existing node (§6 V2). |
| `weight` | integer | yes | `≥ 1`. Explicit always — there is no default weight (D7). |

- `source` ∈ P, `target` ∈ T → **input arc** (consumes `weight` tokens on firing).
- `source` ∈ T, `target` ∈ P → **output arc** (produces `weight` tokens on firing).
- place→place and transition→transition arcs are **invalid** (§6 V3).

### 4.4 Naming rules (stricter than the library — D6)

- Names are arbitrary non-empty JSON strings; implementations MUST NOT impose a
  charset beyond well-formed JSON text. (Identifier-friendly names are RECOMMENDED
  for readability but not enforced.)
- Names MUST be unique across **places ∪ transitions** (§6 V1). The library permits
  a name to be both a place and a transition; the format forbids it — a document
  must never be ambiguous.

### 4.5 Legal edge cases (inherited from the library)

The following are all valid and MUST round-trip losslessly:

- the **empty net** (all three arrays empty);
- **self-loops** (place → t and t → same place, as two distinct arcs);
- **source transitions** (no input arcs — always enabled) and **sink transitions**
  (no output arcs — consume-and-vanish);
- **parallel transitions** (identical pre/post sets, distinct names);
- **zero-token places**; isolated places (no arcs).

## 5. `layout` (optional, UI-namespaced)

`layout` holds visual state owned by UI tools. It is **semantically inert**: it
MUST NOT influence any net semantics, and the Python implementation ignores it
for computation. Shape in v1:

```json
"layout": {
  "nodes": {
    "<node name>": { "x": <integer>, "y": <integer> }
  }
}
```

- `layout.nodes` maps node names to integer coordinates. v1 pins **integer**
  coordinates (snapped grid); fractional layout is a future format revision.
  (This also keeps canonical number serialization trivially portable — §8.5.)
- Unknown members inside `layout` (e.g. a future `viewport`) are allowed by the
  schema (`additionalProperties: true` at the `layout` level) and MUST be preserved
  verbatim on load→save round-trips. Position objects themselves are strict
  (`{x, y}` only).
- `layout.nodes` entries naming nonexistent nodes SHOULD be ignored by loaders
  (UI state may lag behind edits); they are not validation errors (§6 V6).
- **Round-trip rule:** implementations MUST preserve `layout` verbatim. Dropping it
  on save is a conformance violation — canonical byte-identity (§8) applies to the
  whole document, layout included.

## 6. Validation

Validation has two levels. **Loaders MUST enforce both** and MUST reject
non-conforming documents with an error identifying the violated rule.

**Level 1 — schema.** The document validates against
`petri-net-json-v1.schema.json` (shape, types, integer domains, required members,
no unknown top-level members). Additionally, loaders MUST reject documents
containing **duplicate JSON object keys** (RFC 8259 leaves this unpredictable;
this format forbids it).

**Level 2 — semantic rules** (not expressible in JSON Schema):

| ID | Rule |
|---|---|
| **V1** | All place names distinct; all transition names distinct; no name is both a place and a transition. |
| **V2** | Every arc's `source` and `target` names an existing node. |
| **V3** | No arc connects two places or two transitions. |
| **V4** | No two arcs share the same `(source, target)` pair (mirrors the library's `DuplicateArcError`). |
| **V5** | Integer domains — `tokens ≥ 0`, `weight ≥ 1` (schema-enforced; restated for implementers). |
| **V6** | `layout.nodes` keys that name no existing node are ignored, not errors. |

## 7. Semantics (by reference)

The executable specification of net semantics is the tested Python library
(`src/agentx/model/petri_net/model.py`, 99 tests). This format does not redefine
semantics; a document **denotes** the `PetriNet` built by:

```
net = PetriNet()
for p in places:      net.add_place(p.name, p.tokens)      # tokens = M0
for t in transitions: net.add_transition(t.name)
for a in arcs:
    if a.source is a place: net.add_input(a.source, a.target, a.weight)
    else:                   net.add_output(a.source, a.target, a.weight)
```

- `tokens` is the **initial marking M0** (what `reset()` restores). v1 has no
  current-marking snapshot (deferred, see project scope).
- Firing/enabledness/reachability semantics — weighted firing
  `M'(p) = M(p) − W(p,t) + W(t,p)`, AND-enabledness, canonical sorted ordering,
  completeness-explicit analysis results — are exactly the library's, including
  its edge-case policy (§4.5).

## 8. Canonical serialization (D7)

Canonical form is the ONLY form writers produce, and the form against which
round-trip byte-identity is tested. Loaders MUST accept any schema-valid document
(canonical or not); writers MUST emit canonical bytes.

1. **Encoding:** UTF-8, no BOM. Line endings LF. The file ends with exactly one
   trailing LF.
2. **Whitespace:** 2-space indentation, one member per line — exactly
   `JSON.stringify(doc, null, 2) + "\n"` ≡
   `json.dumps(doc, indent=2, ensure_ascii=False) + "\n"`.
3. **Member order (structural core — pinned, never alphabetical):**
   top level `format, version, places, transitions, arcs, layout`;
   Place `name, tokens`; Transition `name`; Arc `source, target, weight`;
   position `x, y`.
4. **Member order (`layout`):** `layout`'s own members in Unicode code-point order;
   `layout.nodes` entries sorted by node name in code-point order.
5. **Array order:** `places` sorted by `name`; `transitions` sorted by `name`;
   `arcs` sorted by `(source, target)` — all lexicographic by Unicode code point
   (equivalently UTF-16 code-unit order; they agree for all well-formed strings).
6. **Numbers:** integers only (schema-enforced for the structural core and v1
   layout coordinates); shortest form — no leading zeros, no `+`, no decimal
   point, no exponent.
7. **Strings:** minimal JSON escaping — escape only `"`, `\`, and control
   characters U+0000–U+001F (short forms `\b \t \n \f \r` where defined, else
   `\u00xx` lowercase hex); all other characters, including non-ASCII, are written
   raw (UTF-8), never `\uXXXX`-escaped.

**Byte-identity contract:** two conforming implementations serializing the same
document produce identical bytes. Round-trip equality (load → save → identical
bytes for canonical input) is a tested property of BOTH implementations
(Python: feature `.petri_net_io`; TS: feature `.studio_v1_editor`).

## 9. Versioning

- `version` is a positive integer; this document defines **1**. `format` +
  `version` together identify the format revision; a loader MUST reject any
  `version` it does not implement (no silent best-effort parsing).
- Adding/removing/repurposing structural members, or relaxing semantic rules
  V1–V4, requires a version bump. `layout` may grow new optional members within
  a version (schema-permitted, §5).
- Reserved future directions (not v1): current-marking snapshots, colored/timed
  nets, hierarchical nets. The version field exists so these can arrive without
  breaking v1 tooling.

## 10. Conformance vectors (planned)

Semantic equivalence of the two engines is proven by golden vectors —
`{net, expected analysis results}` JSON files generated by the tested Python
library (generator: feature `.petri_net_io`) and executed by Vitest against the
TS engine (runner: feature `.studio_v3_graph`), including truncated /
`complete=false` / "unknown" cases (project decision D8). Vectors live in
`shared/petri-net/conformance/` (created by the generator, never hand-written)
and are documents in this format plus an `expected` payload — so the format
itself is exercised by the conformance suite.

## Appendix A — Annotated minimal example (`examples/hello.json`)

```json
{
  "format": "petri-net-json",
  "version": 1,
  "places": [
    { "name": "p1", "tokens": 1 },
    { "name": "p2", "tokens": 0 }
  ],
  "transitions": [
    { "name": "t1" }
  ],
  "arcs": [
    { "source": "p1", "target": "t1", "weight": 1 },
    { "source": "t1", "target": "p2", "weight": 1 }
  ]
}
```

A single token in `p1`; `t1` is enabled; firing it moves the token to `p2`.
(Example files in this repo are shown pretty-printed inline for readability;
on disk they are canonical bytes per §8 — same content, exact whitespace rules.)

## Appendix B — Example files

| File | Demonstrates |
|---|---|
| `examples/hello.json` | Minimal net: 2 places, 1 transition, 1 token. |
| `examples/producer_consumer.json` | Classic bounded producer/consumer (capacity-3 buffer via complementary place), with a `layout` block. |
| `examples/weighted_reaction.json` | Weighted arcs (2 H₂ + O₂ → 2 H₂O), zero-token places, no `layout`. |
