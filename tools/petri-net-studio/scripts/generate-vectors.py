#!/usr/bin/env python3
"""Conformance-vector generator — feature_035.studio_v2_analysis (design_001 §6/§7).

Dev-time script (never bundled): run from the repo root via

    uv run python tools/petri-net-studio/scripts/generate-vectors.py

Uses the TESTED Python library as the executable spec: builds the corpus
(analysis-test fixtures + shared examples), runs `PetriNetAnalyzer`, and
serializes deterministic `{net, expected}` vectors into
`shared/petri-net/conformance/analysis-v1/<id>.json` (B8/B9).

Determinism: `json.dumps(doc, indent=2, ensure_ascii=False) + "\\n"` with pinned
member order; markings as sorted arrays (numeric lexicographic — Python tuple
order); predecessors/edges/bounds/firing_sequences as sorted ARRAYS of
pairs/triples (B9 — no objects keyed by markings); reason strings verbatim;
truncated vectors carry complete:false + reasons (the no-overclaim corpus).
Re-run = byte-identical (doubles as a stability check).

Resolution note (design-gap, recorded in implementation_001): design §6 lists
`two_way_cycle` at `max_states: null` AND `max_states: 1` while §3 lists 8
files. Emitted: `two_way_cycle.json` (null, complete — the §7 example) PLUS
`two_way_cycle_truncated.json` (1, truncated) = 9 vectors — a strict superset
of the §3 plan.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentx.model.petri_net.analysis import PetriNetAnalyzer
from agentx.model.petri_net.io import document_from_json, net_to_json
from agentx.model.petri_net.model import PetriNet

OUT_DIR = REPO_ROOT / "shared" / "petri-net" / "conformance" / "analysis-v1"
EXAMPLES_DIR = REPO_ROOT / "shared" / "petri-net" / "examples"


# ---------------------------------------------------------------------------
# Fixtures (mirror of tests/model/petri_net/test_analysis.py §30)
# ---------------------------------------------------------------------------

def make_net(defn, initial_marking=None):
    net = PetriNet()
    m0 = initial_marking or {}
    for p in defn["places"]:
        net.add_place(p, tokens=m0.get(p, 0))
    for t in defn["transitions"]:
        net.add_transition(t)
    for src, dst, w in defn["arcs"]:
        if src in defn["places"]:
            net.add_input(src, dst, weight=w)
        else:
            net.add_output(src, dst, weight=w)
    return net


TWO_WAY_CYCLE = {
    "places": ["p1", "p2"],
    "transitions": ["t1", "t2"],
    "arcs": [("p1", "t1", 1), ("t1", "p2", 1), ("p2", "t2", 1), ("t2", "p1", 1)],
}
UNBOUNDED_NET = {
    "places": ["p"],
    "transitions": ["t"],
    "arcs": [("p", "t", 1), ("t", "p", 2)],
}
DEADLOCK_NET = {
    "places": ["p"],
    "transitions": ["t"],
    "arcs": [("p", "t", 1)],
}  # M0 p=0 -> t never enabled
TOKEN_DRAIN_NET = {
    "places": ["p1", "p2"],
    "transitions": ["t"],
    "arcs": [("p1", "t", 1), ("t", "p2", 1)],
}
TWO_DEADLOCKS_NET = {
    "places": ["p1", "p2"],
    "transitions": ["t1", "t2"],
    "arcs": [("p1", "t1", 1), ("t1", "p2", 1), ("p1", "t2", 1)],
}


# ---------------------------------------------------------------------------
# Deterministic serialization (B9)
# ---------------------------------------------------------------------------

def ser_markings(markings):
    return sorted([list(m) for m in markings], key=lambda x: tuple(x))


def ser_predecessors(reach):
    items = []
    for m, (prev, trans) in reach.predecessors.items():
        items.append([list(m), list(prev) if prev is not None else None, trans])
    items.sort(key=lambda item: tuple(item[0]))
    return items


def ser_edges(graph):
    items = []
    for m in graph.edges:
        edges = [[t, list(s)] for t, s in graph.edges[m]]
        items.append([",".join(str(x) for x in m), edges])
    items.sort(key=lambda item: item[0])
    return items


def ser_firing_sequences(analyzer, reach):
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


def ser_liveness(analyzer, graph):
    is_live = analyzer.is_live(graph)
    transitions = []
    for t in analyzer.net.transition_order:
        r = analyzer.transition_liveness(t, graph)
        transitions.append([t, r.value, r.complete, r.explored_states, r.reason])
    return {
        "is_live": [is_live.value, is_live.complete, is_live.explored_states, is_live.reason],
        "transitions": transitions,
    }


def ser_sccs(components):
    return [sorted([list(m) for m in comp], key=lambda x: tuple(x)) for comp in components]


def compute_expected(analyzer, max_states):
    reach = analyzer.reachable_markings(max_states=max_states)
    graph = analyzer.reachability_graph(max_states=max_states)
    dead = analyzer.deadlocks(max_states=max_states)
    bounds = analyzer.bounds(max_states=max_states)
    return {
        "reachable_markings": {
            "markings": ser_markings(reach.markings),
            "predecessors": ser_predecessors(reach),
            "complete": reach.complete,
            "explored_states": reach.explored_states,
        },
        "reachability_graph": {
            "states": ser_markings(graph.states),
            "edges": ser_edges(graph),
            "complete": graph.complete,
        },
        "deadlocks": {
            "deadlocks": ser_markings(dead.deadlocks),
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
        "firing_sequences": ser_firing_sequences(analyzer, reach),
        "liveness": ser_liveness(analyzer, graph),
        "sccs": ser_sccs(analyzer.strongly_connected_components(graph)),
    }


# ---------------------------------------------------------------------------
# Corpus: (id, net, max_states, net_doc | None) — net_doc None ⇒ net_to_json
# ---------------------------------------------------------------------------

def load_example(name):
    text = (EXAMPLES_DIR / name).read_text(encoding="utf-8")
    net = document_from_json(text).net
    return net, json.loads(text)


def build_corpus():
    corpus = [
        ("two_way_cycle", make_net(TWO_WAY_CYCLE, {"p1": 1, "p2": 0}), None, None),
        ("two_way_cycle_truncated", make_net(TWO_WAY_CYCLE, {"p1": 1, "p2": 0}), 1, None),
        ("unbounded_net", make_net(UNBOUNDED_NET, {"p": 1}), 5, None),
        ("deadlock_net", make_net(DEADLOCK_NET), None, None),
        ("token_drain_net", make_net(TOKEN_DRAIN_NET, {"p1": 1}), None, None),
        ("two_deadlocks_net", make_net(TWO_DEADLOCKS_NET, {"p1": 1}), None, None),
    ]
    for name in ("weighted_reaction", "producer_consumer", "hello"):
        net, doc = load_example(f"{name}.json")
        corpus.append((name, net, None, doc))
    return corpus


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for vid, net, max_states, net_doc in build_corpus():
        if net_doc is None:
            net_doc = json.loads(net_to_json(net))
        vector = {
            "format": "petri-net-conformance",
            "version": 1,
            "id": vid,
            "max_states": max_states,
            "net": net_doc,
            "expected": compute_expected(PetriNetAnalyzer(net), max_states),
        }
        text = json.dumps(vector, indent=2, ensure_ascii=False) + "\n"
        (OUT_DIR / f"{vid}.json").write_text(text, encoding="utf-8")
        written.append(vid)
    print(f"wrote {len(written)} vectors to {OUT_DIR}")
    for vid in written:
        print(f"  {vid}.json")


if __name__ == "__main__":
    main()