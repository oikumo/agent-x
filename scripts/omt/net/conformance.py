"""Conformance-vector runner — feature_039.adaptive_net_engine (D2 parity proof).

Recomputes the ``expected`` section of each shared conformance vector
(`shared/petri-net/conformance/analysis-v1/*.json`) with the HARNESS engine
and deep-compares. The serialization discipline mirrors the generator
(`tools/petri-net-studio/scripts/generate-vectors.py` — B9: sorted arrays,
maps as sorted pair-arrays, marking keys comma-joined) so a vector produced
from the tested library must match this harness clone byte-for-byte in
structure.

Used by `tests/scripts/omt/test_net_conformance.py`; structure-changing ops
(`splice`/`sync`/`synthesize`, feature_040+) re-run it as the regression
gate (IDEA-002 v4 §5.0 trigger matrix).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .analysis import PetriNetAnalyzer
from .io import document_from_json


# ---------------------------------------------------------------------------
# Deterministic serialization (mirror of generate-vectors.py, B9)
# ---------------------------------------------------------------------------

def _ser_markings(markings) -> list[list[int]]:
    return sorted([list(m) for m in markings], key=lambda x: tuple(x))


def _ser_predecessors(reach) -> list[list[Any]]:
    items = []
    for m, (prev, trans) in reach.predecessors.items():
        items.append([list(m), list(prev) if prev is not None else None, trans])
    items.sort(key=lambda item: tuple(item[0]))
    return items


def _ser_edges(graph) -> list[list[Any]]:
    items = []
    for m in graph.edges:
        edges = [[t, list(s)] for t, s in graph.edges[m]]
        items.append([",".join(str(x) for x in m), edges])
    items.sort(key=lambda item: item[0])
    return items


def _ser_firing_sequences(analyzer: PetriNetAnalyzer, reach) -> list[list[Any]]:
    items = []
    for m in sorted(reach.markings):
        items.append([list(m), analyzer.firing_sequence_to(reach, m)])
    # one provably-unreachable (or, on truncation, absent) target -> null:
    # per-place max token count over explored states, +1.
    max_tokens: list[int] = []
    for m in reach.markings:
        while len(max_tokens) < len(m):
            max_tokens.append(0)
        for i, tokens in enumerate(m):
            if tokens > max_tokens[i]:
                max_tokens[i] = tokens
    for m in reach.markings:
        for i, tokens in enumerate(m):
            if tokens > max_tokens[i]:
                max_tokens[i] = tokens
    target = tuple(x + 1 for x in max_tokens)
    items.append([list(target), analyzer.firing_sequence_to(reach, target)])
    return items


def _ser_liveness(analyzer: PetriNetAnalyzer, graph) -> dict[str, Any]:
    is_live = analyzer.is_live(graph)
    transitions = []
    for t in analyzer.net.transition_order:
        r = analyzer.transition_liveness(t, graph)
        transitions.append([t, r.value, r.complete, r.explored_states, r.reason])
    return {
        "is_live": [is_live.value, is_live.complete, is_live.explored_states, is_live.reason],
        "transitions": transitions,
    }


def _ser_sccs(components) -> list[list[list[int]]]:
    return [sorted([list(m) for m in comp], key=lambda x: tuple(x)) for comp in components]


def compute_expected(analyzer: PetriNetAnalyzer, max_states: int | None) -> dict[str, Any]:
    """The full `expected` section of a vector, from the harness engine."""
    reach = analyzer.reachable_markings(max_states=max_states)
    graph = analyzer.reachability_graph(max_states=max_states)
    dead = analyzer.deadlocks(max_states=max_states)
    bounds = analyzer.bounds(max_states=max_states)
    return {
        "reachable_markings": {
            "markings": _ser_markings(reach.markings),
            "predecessors": _ser_predecessors(reach),
            "complete": reach.complete,
            "explored_states": reach.explored_states,
        },
        "reachability_graph": {
            "states": _ser_markings(graph.states),
            "edges": _ser_edges(graph),
            "complete": graph.complete,
        },
        "deadlocks": {
            "deadlocks": _ser_markings(dead.deadlocks),
            "complete": dead.complete,
            "explored_states": dead.explored_states,
            "reason": dead.reason,
        },
        "bounds": {
            "bounded": bounds.bounded,
            "bounds": [[p, bounds.bounds[p]] for p in sorted(bounds.bounds)],
            "complete": bounds.complete,
            "reason": bounds.reason,
        },
        "incidence_matrix": analyzer.incidence_matrix(),
        "place_invariants": [list(v) for v in analyzer.place_invariants()],
        "transition_invariants": [list(v) for v in analyzer.transition_invariants()],
        "firing_sequences": _ser_firing_sequences(analyzer, reach),
        "liveness": _ser_liveness(analyzer, graph),
        "sccs": _ser_sccs(analyzer.strongly_connected_components(graph)),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_vector(vector: dict[str, Any]) -> dict[str, Any]:
    """Deep-compare one vector's `expected` against the harness engine.

    Returns ``{"id", "ok", "mismatches": [section, ...]}`` — never raises on
    a mismatch; engine/validation errors surface as ``mismatches=["<error>"]``.
    """
    vid = vector.get("id", "<unknown>")
    try:
        doc = document_from_json(json.dumps(vector["net"]))
        analyzer = PetriNetAnalyzer(doc.net)
        computed = compute_expected(analyzer, vector.get("max_states"))
    except Exception as exc:  # engine/validation failure = parity failure
        return {"id": vid, "ok": False, "mismatches": [f"<engine error: {exc!r}>"]}
    expected = vector["expected"]
    mismatches = [
        section
        for section in expected
        if section not in computed or computed[section] != expected[section]
    ] + [section for section in computed if section not in expected]
    return {"id": vid, "ok": not mismatches, "mismatches": sorted(set(mismatches))}


def run_vectors(vectors_dir: Path) -> list[dict[str, Any]]:
    """Run every vector file in a directory; sorted by vector id."""
    results = [
        run_vector(json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(vectors_dir.glob("*.json"))
    ]
    return sorted(results, key=lambda r: r["id"])
