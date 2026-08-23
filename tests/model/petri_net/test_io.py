"""Tests for petri-net-json v1 io (shared/petri-net/FORMAT.md; feature_033).

Covers: canonical serialization (D7/§8), two-level validation (§6: level-1
shape + level-2 V1–V6), typed-error precedence, layout verbatim round-trip
(§5), M0-only serialization, and the shared examples as golden canonical
bytes. Deferred imports inside helpers/test bodies (feature_031 convention).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = REPO_ROOT / "shared" / "petri-net" / "examples"
SCHEMA = REPO_ROOT / "shared" / "petri-net" / "petri-net-json-v1.schema.json"


def _io():
    from agentx.model.petri_net import io
    return io


def _new_net():
    from agentx.model.petri_net.model import PetriNet
    return PetriNet()


def make_hello():
    """FORMAT.md Appendix A net: p1 -t1-> p2, one token in p1."""
    net = _new_net()
    net.add_place("p1", tokens=1)
    net.add_place("p2", tokens=0)
    net.add_transition("t1")
    net.add_input("p1", "t1")
    net.add_output("t1", "p2")
    return net


HELLO_JSON = """{
  "format": "petri-net-json",
  "version": 1,
  "places": [
    {
      "name": "p1",
      "tokens": 1
    },
    {
      "name": "p2",
      "tokens": 0
    }
  ],
  "transitions": [
    {
      "name": "t1"
    }
  ],
  "arcs": [
    {
      "source": "p1",
      "target": "t1",
      "weight": 1
    },
    {
      "source": "t1",
      "target": "p2",
      "weight": 1
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Behavior 1 — canonical dump (§8): bytes, ordering, escaping
# ---------------------------------------------------------------------------

class TestCanonicalDump:
    def test_hello_serializes_to_expected_canonical_bytes(self):
        assert _io().net_to_json(make_hello()) == HELLO_JSON

    def test_places_transitions_arcs_sorted_code_point(self):
        net = _new_net()
        net.add_place("z", tokens=0)
        net.add_place("a", tokens=2)
        net.add_transition("t2")
        net.add_transition("t10")  # code-point: "t10" < "t2"
        net.add_input("z", "t2", weight=3)
        net.add_input("a", "t10")
        net.add_output("t2", "a")
        doc = json.loads(_io().net_to_json(net))
        assert [p["name"] for p in doc["places"]] == ["a", "z"]
        assert [t["name"] for t in doc["transitions"]] == ["t10", "t2"]
        arcs = [(a["source"], a["target"]) for a in doc["arcs"]]
        assert arcs == sorted(arcs)
        assert arcs == [("a", "t10"), ("t2", "a"), ("z", "t2")]

    def test_explicit_weights_and_tokens_always_emitted(self):
        doc = json.loads(_io().net_to_json(make_hello()))
        assert all(set(p) == {"name", "tokens"} for p in doc["places"])
        assert all(set(a) == {"source", "target", "weight"} for a in doc["arcs"])

    def test_non_ascii_names_written_raw_utf8(self):
        net = _new_net()
        net.add_place("plätz", tokens=1)
        net.add_transition("tü")
        net.add_input("plätz", "tü")
        text = _io().net_to_json(net)
        assert "plätz" in text and "tü" in text
        assert "\\u" not in text

    def test_strings_minimally_escaped(self):
        net = _new_net()
        net.add_place('quote"and\nnewline', tokens=0)
        text = _io().net_to_json(net)
        assert '\\"' in text and "\\n" in text

    def test_empty_net_round_trips(self):
        text = _io().net_to_json(_new_net())
        assert _io().net_to_json(_io().net_from_json(text)) == text

    def test_dump_uses_initial_marking_not_live(self):
        net = make_hello()
        net.fire("t1")  # live marking now (0, 1); M0 stays (1, 0)
        assert _io().net_to_json(net) == HELLO_JSON

    def test_trailing_lf_and_indent(self):
        text = _io().net_to_json(make_hello())
        assert text.endswith("\n") and not text.endswith("\n\n")
        assert '\n  "version"' in text


# ---------------------------------------------------------------------------
# Behavior 2 — load: happy path + document round-trip byte-identity (§5/§8)
# ---------------------------------------------------------------------------

class TestLoad:
    def test_hello_loads_to_equivalent_net(self):
        net = _io().net_from_json(HELLO_JSON)
        assert net.places == {"p1", "p2"}
        assert net.transitions == {"t1"}
        assert net.inputs == {"t1": {"p1": 1}}
        assert net.outputs == {"t1": {"p2": 1}}
        assert net.initial_marking == {"p1": 1, "p2": 0}
        assert net.enabled_transitions_at(net.current_marking()) == ["t1"]

    def test_document_round_trip_byte_identical(self):
        doc = _io().document_from_json(HELLO_JSON)
        assert doc.layout is None
        assert _io().net_to_json(doc.net, layout=doc.layout) == HELLO_JSON

    def test_net_to_json_accepts_layout_and_validates_it(self):
        layout = {"nodes": {"p1": {"x": 1, "y": 2}}}
        text = _io().net_to_json(make_hello(), layout=layout)
        assert json.loads(text)["layout"] == layout
        with pytest.raises(_io().SchemaValidationError):
            _io().net_to_json(make_hello(), layout={"nodes": {"p1": {"x": 1.5, "y": 2}}})

    @pytest.mark.parametrize("example", sorted(EXAMPLES.glob("*.json")), ids=lambda p: p.name)
    def test_shared_examples_are_golden_canonical_bytes(self, example):
        """The shipped examples round-trip byte-identically through Python (D7)."""
        text = example.read_text(encoding="utf-8")
        doc = _io().document_from_json(text)
        assert _io().net_to_json(doc.net, layout=doc.layout) == text

    def test_layout_preserved_verbatim_including_extensions(self):
        text = (EXAMPLES / "producer_consumer.json").read_text(encoding="utf-8")
        doc_in = json.loads(text)
        doc_in["layout"]["viewport"] = {"zoom": 1, "x": 0, "y": 0}  # extension member
        doc = _io().document_from_json(json.dumps(doc_in))
        out = json.loads(_io().net_to_json(doc.net, layout=doc.layout))
        assert out["layout"]["viewport"] == {"zoom": 1, "x": 0, "y": 0}

    def test_layout_nodes_for_unknown_nodes_ignored_not_error(self):
        doc_in = json.loads(HELLO_JSON)
        doc_in["layout"] = {"nodes": {"ghost": {"x": 0, "y": 0}, "p1": {"x": 1, "y": 2}}}
        doc = _io().document_from_json(json.dumps(doc_in))  # V6: ignored, not error
        assert set(json.loads(_io().net_to_json(doc.net, layout=doc.layout))["layout"]["nodes"]) == {"ghost", "p1"}

    def test_integral_floats_normalized_to_int(self):
        doc_in = json.loads(HELLO_JSON)
        doc_in["places"][0]["tokens"] = 1.0  # schema-`integer` accepts integral floats
        net = _io().net_from_json(json.dumps(doc_in))
        assert net.initial_marking["p1"] == 1
        # …and re-serialization is canonical integer bytes.
        assert _io().net_to_json(net) == HELLO_JSON

    def test_non_canonical_input_loads_and_recanonicalizes(self):
        messy = json.dumps({"arcs": [{"weight": 1, "target": "t1", "source": "p1"},
                                     {"weight": 1, "target": "p2", "source": "t1"}],
                            "transitions": [{"name": "t1"}],
                            "places": [{"tokens": 0, "name": "p2"}, {"tokens": 1, "name": "p1"}],
                            "version": 1, "format": "petri-net-json"})
        assert _io().net_to_json(_io().net_from_json(messy)) == HELLO_JSON


# ---------------------------------------------------------------------------
# Behavior 3 — typed errors, precedence (syntax → format → version → L1 → L2)
# ---------------------------------------------------------------------------

def _doc(**overrides):
    base = json.loads(HELLO_JSON)
    base.update(overrides)
    return base


class TestTypedErrors:
    def test_syntax_error_on_malformed_json(self):
        with pytest.raises(_io().FormatSyntaxError):
            _io().net_from_json("{not json")

    def test_syntax_error_on_duplicate_keys(self):
        with pytest.raises(_io().FormatSyntaxError, match="Duplicate object key"):
            _io().net_from_json('{"format": "petri-net-json", "format": "petri-net-json"}')

    def test_document_must_be_object(self):
        with pytest.raises(_io().FormatSyntaxError):
            _io().net_from_json('[1, 2]')

    def test_unknown_format(self):
        with pytest.raises(_io().UnknownFormatError):
            _io().net_from_json(json.dumps(_doc(format="other")))

    def test_format_checked_before_version(self):
        with pytest.raises(_io().UnknownFormatError):
            _io().net_from_json(json.dumps(_doc(format="other", version=99)))

    def test_unsupported_version(self):
        with pytest.raises(_io().UnsupportedVersionError, match="99"):
            _io().net_from_json(json.dumps(_doc(version=99)))

    @pytest.mark.parametrize("bad", [
        _doc(format=1),
        _doc(version="1"),
        _doc(places=None),
        _doc(arcs={}),
        _doc(extra=1),
    ])
    def test_schema_level_violations(self, bad):
        with pytest.raises(_io().SchemaValidationError):
            _io().net_from_json(json.dumps(bad))

    @pytest.mark.parametrize("member", ["version", "places", "transitions", "arcs"])
    def test_missing_required_members(self, member):
        bad = json.loads(HELLO_JSON)
        del bad[member]
        with pytest.raises(_io().SchemaValidationError):
            _io().net_from_json(json.dumps(bad))

    def test_missing_format_member(self):
        bad = json.loads(HELLO_JSON)
        del bad["format"]
        with pytest.raises(_io().SchemaValidationError, match="format"):
            _io().net_from_json(json.dumps(bad))

    @pytest.mark.parametrize("place,frag", [
        ({"name": "", "tokens": 0}, "non-empty"),
        ({"name": "p", "tokens": -1}, ">= 0"),
        ({"name": "p", "tokens": True}, "boolean"),
        ({"name": "p", "tokens": 0.5}, "integer"),
        ({"name": "p"}, "requires"),
        ({"name": "p", "tokens": 0, "extra": 1}, "unknown"),
    ])
    def test_bad_places(self, place, frag):
        with pytest.raises(_io().SchemaValidationError, match=frag):
            _io().net_from_json(json.dumps(_doc(places=[place])))

    @pytest.mark.parametrize("arc,frag", [
        ({"source": "p1", "target": "t1", "weight": 0}, ">= 1"),
        ({"source": "p1", "target": "t1", "weight": 1.5}, "integer"),
        ({"source": "", "target": "t1", "weight": 1}, "non-empty"),
        ({"source": "p1", "target": "t1"}, "requires"),
    ])
    def test_bad_arcs(self, arc, frag):
        with pytest.raises(_io().SchemaValidationError, match=frag):
            _io().net_from_json(json.dumps(_doc(arcs=[arc])))

    @pytest.mark.parametrize("layout", [
        "not-an-object",
        {"nodes": ["not-an-object"]},
        {"nodes": {"p1": {"x": 1.5, "y": 0}}},
        {"nodes": {"p1": {"x": 0}}},
        {"nodes": {"p1": {"x": 0, "y": 0, "z": 0}}},
    ])
    def test_bad_layouts(self, layout):
        with pytest.raises(_io().SchemaValidationError):
            _io().net_from_json(json.dumps(_doc(layout=layout)))

    @pytest.mark.parametrize("bad, rule", [
        (_doc(places=[{"name": "p1", "tokens": 0}, {"name": "p1", "tokens": 1}]), "V1"),
        (_doc(transitions=[{"name": "p1"}]), "V1"),  # name in both P and T
        (_doc(arcs=[{"source": "p1", "target": "ghost", "weight": 1}]), "V2"),
        (_doc(arcs=[{"source": "p1", "target": "p2", "weight": 1}]), "V3"),
        (_doc(arcs=[{"source": "p1", "target": "t1", "weight": 1},
                    {"source": "p1", "target": "t1", "weight": 2}]), "V4"),
    ])
    def test_semantic_violations_carry_rule_id(self, bad, rule):
        with pytest.raises(_io().SemanticValidationError, match=rule):
            _io().net_from_json(json.dumps(bad))

    def test_errors_subclass_library_base(self):
        from agentx.model.petri_net.errors import PetriNetError
        for cls in (_io().FormatSyntaxError, _io().UnknownFormatError,
                    _io().UnsupportedVersionError, _io().SchemaValidationError,
                    _io().SemanticValidationError):
            assert issubclass(cls, PetriNetError)


# ---------------------------------------------------------------------------
# Behavior 4 — cross-checks against the JSON Schema (when jsonschema present)
# ---------------------------------------------------------------------------

class TestSchemaCrossCheck:
    @pytest.fixture(autouse=True)
    def _jsonschema(self):
        pytest.importorskip("jsonschema")
        import jsonschema
        self.jsonschema = jsonschema

    @pytest.mark.parametrize("example", sorted(EXAMPLES.glob("*.json")), ids=lambda p: p.name)
    def test_examples_validate_against_schema(self, example):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.jsonschema.validate(json.loads(example.read_text(encoding="utf-8")), schema)

    def test_io_rejects_what_schema_rejects(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = self.jsonschema.Draft202012Validator(schema)
        for bad in (_doc(format="other"), _doc(version=2), _doc(extra=1),
                    _doc(places=[{"name": "p", "tokens": -1}]),
                    _doc(arcs=[{"source": "p1", "target": "t1", "weight": 0}])):
            assert not validator.is_valid(bad)
            with pytest.raises(_io().PetriNetFormatError):
                _io().net_from_json(json.dumps(bad))
