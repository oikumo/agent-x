"""petri-net-json v1 io (shared/petri-net/FORMAT.md; petri_net_studio roadmap #2).

The format is the ONLY coupling to external tools (D5); semantics stay with
:mod:`.model` — this module translates documents to nets and back, nothing
more. Stdlib-only (library D4; ``pyproject.toml`` unchanged).

- Load (:func:`document_from_json` / :func:`net_from_json`): JSON syntax with
  duplicate-key rejection, then level-1 shape/types/domains, then level-2
  semantic rules V1–V6 (FORMAT.md §6), then net construction per §7.
  Error precedence: :class:`FormatSyntaxError` → :class:`UnknownFormatError`
  → :class:`UnsupportedVersionError` → :class:`SchemaValidationError`
  → :class:`SemanticValidationError`.
- Dump (:func:`net_to_json`): canonical bytes per FORMAT.md §8 — pinned member
  order, code-point-sorted arrays, integer-only numbers, minimal escaping,
  trailing LF. Round-trip byte-identity is a tested property (D7).
- ``tokens`` is the initial marking M0 (``initial_marking``), never the live
  marking; v1 has no current-marking snapshots. ``layout`` is UI-namespaced:
  ignored for computation, preserved verbatim on document round-trips (§5).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .errors import PetriNetError
from .model import PetriNet

FORMAT_ID = "petri-net-json"
FORMAT_VERSION = 1

__all__ = [
    "FORMAT_ID",
    "FORMAT_VERSION",
    "PetriNetDocument",
    "PetriNetFormatError",
    "FormatSyntaxError",
    "UnknownFormatError",
    "UnsupportedVersionError",
    "SchemaValidationError",
    "SemanticValidationError",
    "net_to_json",
    "net_from_json",
    "document_from_json",
]

_TOP_LEVEL_KEYS = frozenset({"format", "version", "places", "transitions", "arcs", "layout"})


# ---------------------------------------------------------------------------
# Typed errors (additive — errors.py stays untouched; all subclass its base)
# ---------------------------------------------------------------------------

class PetriNetFormatError(PetriNetError):
    """Base class for petri-net-json load/dump failures."""


class FormatSyntaxError(PetriNetFormatError):
    """Not well-formed JSON, or a duplicate object key (FORMAT.md §6)."""


class UnknownFormatError(PetriNetFormatError):
    """Top-level ``format`` is not ``"petri-net-json"``."""


class UnsupportedVersionError(PetriNetFormatError):
    """``version`` is not implemented here (this implementation speaks v1)."""


class SchemaValidationError(PetriNetFormatError):
    """Level-1 violation: document shape, types, or integer domains (§6)."""


class SemanticValidationError(PetriNetFormatError):
    """Level-2 violation: semantic rules V1–V6 (§6); message carries the rule id."""


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PetriNetDocument:
    """A loaded document: the net plus the verbatim ``layout`` member (§5).

    ``layout`` is exactly the parsed JSON value (or None when absent) so a
    load→dump round-trip preserves it byte-identically (canonical form).
    """

    net: PetriNet
    layout: dict[str, Any] | None


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------

def _parse_no_dup_keys(text: str) -> Any:
    """json.loads with duplicate-key rejection (FORMAT.md §6 level 1)."""
    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for key, value in pairs:
            if key in obj:
                raise FormatSyntaxError(f"Duplicate object key: {key!r}")
            obj[key] = value
        return obj

    try:
        return json.loads(text, object_pairs_hook=hook)
    except json.JSONDecodeError as exc:
        raise FormatSyntaxError(f"Invalid JSON: {exc}") from exc


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise SchemaValidationError(message)


def _as_int(value: Any, what: str, minimum: int) -> int:
    """Schema-`integer` semantics: int (never bool) or integral float → int."""
    if isinstance(value, bool):
        raise SchemaValidationError(f"{what} must be an integer, got boolean {value!r}")
    if isinstance(value, int):
        result = value
    elif isinstance(value, float) and value.is_integer():
        result = int(value)
    else:
        raise SchemaValidationError(f"{what} must be an integer, got {value!r}")
    if result < minimum:
        raise SchemaValidationError(f"{what} must be >= {minimum}, got {result}")
    return result


def _as_name(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaValidationError(f"{what} must be a non-empty string, got {value!r}")
    return value


def _exact_keys(obj: Any, keys: frozenset[str], what: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise SchemaValidationError(f"{what} must be an object, got {obj!r}")
    unknown = set(obj) - keys
    _require(not unknown, f"{what} has unknown member(s): {sorted(unknown)}")
    return obj


def _validate_layout_shape(layout: Any) -> dict[str, Any]:
    """§5: layout is an object; `nodes` maps names to strict {x, y} int pairs.

    Unknown members are allowed and preserved verbatim (extensions within a
    version, §9). Returns the layout unchanged (shape is validated in place).
    """
    if not isinstance(layout, dict):
        raise SchemaValidationError(f"'layout' must be an object, got {layout!r}")
    nodes = layout.get("nodes")
    if nodes is not None:
        if not isinstance(nodes, dict):
            raise SchemaValidationError(f"'layout.nodes' must be an object, got {nodes!r}")
        for node_name, pos in nodes.items():
            pos = _exact_keys(pos, frozenset({"x", "y"}), f"layout.nodes[{node_name!r}]")
            _require("x" in pos and "y" in pos,
                     f"layout.nodes[{node_name!r}] requires members 'x' and 'y'")
            _as_int(pos["x"], f"layout.nodes[{node_name!r}].x", minimum=-10**15)
            _as_int(pos["y"], f"layout.nodes[{node_name!r}].y", minimum=-10**15)
    return layout


def _validate(doc: Any) -> tuple[list[dict], list[dict], list[dict], dict | None]:
    """Levels 1+2 (FORMAT.md §6). Returns normalized (places, transitions,
    arcs, layout) — integral floats normalized to int; layout verbatim."""
    if not isinstance(doc, dict):
        raise FormatSyntaxError(f"Document must be a JSON object, got {doc!r}")

    # format family first, then version (error precedence per module docstring).
    if "format" not in doc:
        raise SchemaValidationError("Missing required member 'format'")
    if not isinstance(doc["format"], str):
        raise SchemaValidationError(f"'format' must be a string, got {doc['format']!r}")
    if doc["format"] != FORMAT_ID:
        raise UnknownFormatError(f"Unknown format: {doc['format']!r} (expected {FORMAT_ID!r})")
    if "version" not in doc:
        raise SchemaValidationError("Missing required member 'version'")
    version = doc["version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise SchemaValidationError(f"'version' must be an integer, got {version!r}")
    if version != FORMAT_VERSION:
        raise UnsupportedVersionError(f"Unsupported version: {version} (this loader speaks v{FORMAT_VERSION})")

    unknown = set(doc) - _TOP_LEVEL_KEYS
    _require(not unknown, f"Unknown top-level member(s): {sorted(unknown)}")
    for key in ("places", "transitions", "arcs"):
        _require(key in doc, f"Missing required member {key!r}")
        _require(isinstance(doc[key], list), f"{key!r} must be an array, got {doc[key]!r}")

    places = []
    for i, raw in enumerate(doc["places"]):
        p = _exact_keys(raw, frozenset({"name", "tokens"}), f"places[{i}]")
        _require("name" in p and "tokens" in p, f"places[{i}] requires members 'name' and 'tokens'")
        places.append({
            "name": _as_name(p["name"], f"places[{i}].name"),
            "tokens": _as_int(p["tokens"], f"places[{i}].tokens", minimum=0),
        })
    transitions = []
    for i, raw in enumerate(doc["transitions"]):
        t = _exact_keys(raw, frozenset({"name"}), f"transitions[{i}]")
        _require("name" in t, f"transitions[{i}] requires member 'name'")
        transitions.append({"name": _as_name(t["name"], f"transitions[{i}].name")})
    arcs = []
    for i, raw in enumerate(doc["arcs"]):
        a = _exact_keys(raw, frozenset({"source", "target", "weight"}), f"arcs[{i}]")
        _require(all(k in a for k in ("source", "target", "weight")),
                 f"arcs[{i}] requires members 'source', 'target', 'weight'")
        arcs.append({
            "source": _as_name(a["source"], f"arcs[{i}].source"),
            "target": _as_name(a["target"], f"arcs[{i}].target"),
            "weight": _as_int(a["weight"], f"arcs[{i}].weight", minimum=1),
        })
    layout = _validate_layout_shape(doc["layout"]) if "layout" in doc else None

    place_names = [p["name"] for p in places]
    transition_names = [t["name"] for t in transitions]
    pset, tset = set(place_names), set(transition_names)
    if len(place_names) != len(pset) or len(transition_names) != len(tset) or pset & tset:
        raise SemanticValidationError(
            "V1: names must be unique across places ∪ transitions"
            f" (duplicate place(s): {sorted(n for n in pset if place_names.count(n) > 1)},"
            f" duplicate transition(s): {sorted(n for n in tset if transition_names.count(n) > 1)},"
            f" in both: {sorted(pset & tset)})")
    for i, a in enumerate(arcs):
        if a["source"] not in pset | tset or a["target"] not in pset | tset:
            raise SemanticValidationError(
                f"V2: arcs[{i}] endpoint(s) do not name an existing node:"
                f" {a['source']!r} -> {a['target']!r}")
        s_is_p, t_is_p = a["source"] in pset, a["target"] in pset
        s_is_t, t_is_t = a["source"] in tset, a["target"] in tset
        if not ((s_is_p and t_is_t) or (s_is_t and t_is_p)):
            raise SemanticValidationError(
                f"V3: arcs[{i}] must connect a place and a transition:"
                f" {a['source']!r} -> {a['target']!r}")
    pairs = [(a["source"], a["target"]) for a in arcs]
    if len(pairs) != len(set(pairs)):
        dupes = sorted(pair for pair in set(pairs) if pairs.count(pair) > 1)
        raise SemanticValidationError(f"V4: duplicate arc(s) (source, target): {dupes}")
    # V6: unknown layout.nodes names are ignored, not errors (no check).
    return places, transitions, arcs, layout


def _build_net(places: list[dict], transitions: list[dict], arcs: list[dict]) -> PetriNet:
    """FORMAT.md §7 construction algorithm."""
    net = PetriNet()
    for p in places:
        net.add_place(p["name"], p["tokens"])
    for t in transitions:
        net.add_transition(t["name"])
    for a in arcs:
        if a["source"] in net.places:
            net.add_input(a["source"], a["target"], a["weight"])
        else:
            net.add_output(transition=a["source"], place=a["target"], weight=a["weight"])
    return net


# ---------------------------------------------------------------------------
# Public load API
# ---------------------------------------------------------------------------

def document_from_json(text: str) -> PetriNetDocument:
    """Parse + validate a petri-net-json v1 document (levels 1–2, §6).

    Returns the net (built per §7) and the verbatim ``layout`` member for
    byte-preserving round-trips (§5). Raises the typed errors above with the
    precedence pinned in the module docstring.
    """
    if not isinstance(text, str):
        raise FormatSyntaxError(f"Expected JSON text (str), got {type(text).__name__}")
    places, transitions, arcs, layout = _validate(_parse_no_dup_keys(text))
    return PetriNetDocument(net=_build_net(places, transitions, arcs), layout=layout)


def net_from_json(text: str) -> PetriNet:
    """Like :func:`document_from_json` but returns only the net (layout dropped)."""
    return document_from_json(text).net


# ---------------------------------------------------------------------------
# Dump (canonical serialization, FORMAT.md §8)
# ---------------------------------------------------------------------------

def _canonical_layout(layout: dict[str, Any]) -> dict[str, Any]:
    """§8.4: layout members sorted (code point); nodes sorted by name; x,y order."""
    out: dict[str, Any] = {}
    for key in sorted(layout):
        value = layout[key]
        if key == "nodes" and isinstance(value, dict):
            out[key] = {
                name: {"x": pos["x"], "y": pos["y"]} if isinstance(pos, dict) and "x" in pos and "y" in pos else pos
                for name, pos in sorted(value.items())
            }
        else:
            out[key] = value  # extension members: verbatim parsed value
    return out


def net_to_json(net: PetriNet, *, layout: dict[str, Any] | None = None) -> str:
# TA: xref: TS-port parity (feature_034+): the TypeScript engine must match this module exactly — error precedence syntax→format→version→L1→L2, V-rule ids in messages, integral-float→int normalization, bool rejection, layout verbatim/extensions/V6, canonical §8 bytes (JSON.stringify(d,null,2)+"\n" ≡ json.dumps(indent=2,ensure_ascii=False)+"\n"; code-point sort ≡ JS default sort for well-formed strings). Reference matrix: tests/model/petri_net/test_io.py (59 tests); golden canonical bytes: shared/petri-net/examples/.
    """Serialize ``net`` (+ optional ``layout``) to canonical bytes (§8).

    ``tokens`` come from ``initial_marking`` (M0 — the live marking is never
    serialized). ``layout`` is shape-validated (§5) and emitted in canonical
    member order; extension members pass through verbatim.
    """
    doc: dict[str, Any] = {"format": FORMAT_ID, "version": FORMAT_VERSION}
    doc["places"] = [
        {"name": p, "tokens": net.initial_marking[p]} for p in sorted(net.places)
    ]
    doc["transitions"] = [{"name": t} for t in sorted(net.transitions)]
    arcs = []
    for t in net.transitions:
        arcs.extend({"source": p, "target": t, "weight": w} for p, w in net.inputs[t].items())
        arcs.extend({"source": t, "target": p, "weight": w} for p, w in net.outputs[t].items())
    arcs.sort(key=lambda a: (a["source"], a["target"]))
    doc["arcs"] = arcs
    if layout is not None:
        doc["layout"] = _canonical_layout(_validate_layout_shape(layout))
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
