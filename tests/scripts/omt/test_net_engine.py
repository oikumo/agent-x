"""Harness net engine sanity — feature_039.adaptive_net_engine.

Spot-checks the clone's core semantics (fire/enabled/errors/io) plus golden
canonical-bytes io round-trip over `shared/petri-net/examples/`. The deep
semantic proof is the 9-vector conformance suite (test_net_conformance.py);
these tests pin the engine's API shape + the D2 no-`src/`-import rule.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "omt"
sys.path.insert(0, str(SCRIPTS_DIR))

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "shared" / "petri-net" / "examples"


def _engine():
    """Lazy imports — runnable RED (GOTCHA_RED_RUNNABLE)."""
    from net import errors, io, model  # noqa: PLC0415

    return errors, io, model


def _hello_net(model):
    net = model.PetriNet()
    net.add_place("p1", tokens=1)
    net.add_place("p2", tokens=0)
    net.add_transition("t1")
    net.add_input("p1", "t1", weight=1)
    net.add_output("t1", "p2", weight=1)
    return net


class TestModelClone:
    def test_fire_and_enabled(self) -> None:
        _errors, _io, model = _engine()
        net = _hello_net(model)
        assert net.is_enabled_at(net.current_marking(), "t1")
        net.fire("t1")
        assert net.current_marking() == (0, 1)
        assert not net.is_enabled_at(net.current_marking(), "t1")

    def test_disabled_fire_raises_and_does_not_mutate(self) -> None:
        errors, _io, model = _engine()
        net = _hello_net(model)
        net.fire("t1")
        with pytest.raises(errors.TransitionNotEnabledError):
            net.fire("t1")
        assert net.current_marking() == (0, 1)

    def test_place_order_is_sorted_and_derived(self) -> None:
        _errors, _io, model = _engine()
        net = model.PetriNet()
        net.add_place("zz", tokens=1)
        net.add_place("aa", tokens=2)
        assert net.place_order == ("aa", "zz")
        assert net.current_marking() == (2, 1)

    def test_duplicate_arc_rejected(self) -> None:
        errors, _io, model = _engine()
        net = _hello_net(model)
        with pytest.raises(errors.DuplicateArcError):
            net.add_input("p1", "t1", weight=2)


class TestIoClone:
    @pytest.mark.parametrize(
        "example", sorted(EXAMPLES_DIR.glob("*.json")), ids=lambda p: p.stem
    )
    def test_golden_bytes_round_trip(self, example: Path) -> None:
        """net_to_json(document_from_json(golden)) == golden bytes (D7)."""
        _errors, io, _model = _engine()
        text = example.read_text(encoding="utf-8")
        doc = io.document_from_json(text)
        assert io.net_to_json(doc.net, layout=doc.layout) == text


class TestNoSrcImport:
    def test_engine_modules_do_not_import_agentx(self) -> None:
        """D2: the harness engine never imports `src/agentx` — static scan of
        the package sources for `agentx` imports (runtime import would defeat
        the independence rule even if tests pass)."""
        import net  # noqa: PLC0415

        assert net.__file__ is not None
        pkg_dir = Path(net.__file__).resolve().parent
        offenders: list[str] = []
        for py in sorted(pkg_dir.glob("*.py")):
            for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "import agentx" in stripped or "from agentx" in stripped:
                    offenders.append(f"{py.name}:{lineno}")
        assert not offenders, f"D2 violation — agentx imports at: {offenders}"
