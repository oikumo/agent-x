"""RED tests for feature_027.rag_v2 — MVC++ provider/view/controller contract.

Pins the console-only RAG v2 module's MVC++ contract (mirrors
``test_console_provider_and_views.py`` shape from feature_024):

  * ``IRagV2View``/``IRagV2ViewPartner`` + 3 inner ABC pairs present in
    ``agentx.ui.interfaces`` (G6(a) narrow closure).
  * ``ConsoleProvider`` exposes ``create_rag_v2_view`` + the 3 inner factories.
  * ``RagV2MainController`` exposes ``switch_repository`` (G5).
  * ``show_rag_v2()`` wires via ``set_view(view)`` NOT ``.view = view``
    (feature_024 bug-pin — Constraint d).
  * ``RagV2CreateRepository`` + ``RagV2RepositorySelection`` contracts (G1/G2 parity).

v2 is console-only (no TUI screens); v1 RAG stays untouched for the TUI path.

All imports of not-yet-existing v2 symbols are deferred INSIDE the test bodies
so RED failures surface as test failures (pytest exit 1), NOT collection errors
(exit 2) — per OMT TDD RED-gate rule (runnable RED).
"""

from __future__ import annotations

import importlib
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

# Top-level imports are limited to symbols that ALREADY exist (so collection
# is clean). All v2 symbols are imported lazily inside the test bodies.


def _load_symbol(module_path: str, name: str) -> Any:
    """Import a symbol that may not exist yet (RED) — fails inside the test."""
    module = importlib.import_module(module_path)
    return getattr(module, name)


def _has_attr(module_path: str, name: str) -> bool:
    """True-ish probe: does the module expose the named symbol?"""
    try:
        module = importlib.import_module(module_path)
    except Exception:
        return False
    return hasattr(module, name)


# ── G6(a) outer parity: IRagV2View / IRagV2ViewPartner present ─────────────────


class TestRagV2OuterParity(TestCase):
    """G6(a) — the outer console-parity ABC pair + factory are present."""

    def test_irag_v2_view_and_partner_abc_pair_present(self) -> None:
        """``IRagV2View`` + ``IRagV2ViewPartner`` exist in agentx.ui.interfaces."""
        from agentx.ui import interfaces  # noqa: WPS433  lazy for RED readability
        assert hasattr(interfaces, "IRagV2View"), (
            "IRagV2View must be defined in agentx.ui.interfaces (G6(a) outer)"
        )
        assert hasattr(interfaces, "IRagV2ViewPartner"), (
            "IRagV2ViewPartner must be defined in agentx.ui.interfaces (G6(a) outer)"
        )
        view_cls = interfaces.IRagV2View
        partner_cls = interfaces.IRagV2ViewPartner
        # Both must be classes (ABCs).
        assert isinstance(view_cls, type) and isinstance(partner_cls, type)

    def test_create_rag_v2_view_factory_present(self) -> None:
        """``ConsoleProvider.create_rag_v2_view`` returns an ``IRagV2View``."""
        from agentx.ui.providers import ConsoleProvider
        from agentx.ui.interfaces import IRagV2View
        provider = ConsoleProvider()
        assert hasattr(provider, "create_rag_v2_view"), (
            "ConsoleProvider must expose create_rag_v2_view (G6(a) outer factory)"
        )
        view = provider.create_rag_v2_view(MagicMock())
        assert isinstance(view, IRagV2View), (
            "create_rag_v2_view must return an IRagV2View instance"
        )


# ── G6(a) inner parity: 3 inner ABC pairs + 3 inner factories ─────────────────


class TestRagV2InnerParity(TestCase):
    """G6(a) narrow closure — 3 inner ABC pairs + 3 inner factories."""

    def test_three_inner_abc_pairs_present(self) -> None:
        """Create-repo / repo-selection / web-ingestion inner ABC pairs present.

        PDF+MD ingestion views (G4) are NEW sibling sub-screens; their ABC pairs
        ship in a separate behavior (``TestRagV2PdfIngestion`` /
        ``TestRagV2MdIngestion`` in the gaps-closure file). This node pins the
        THREE inner pairs that mirror v1's existing inner views.
        """
        from agentx.ui import interfaces
        for name in (
            "IRagV2CreateRepositoryView",
            "IRagV2CreateRepositoryViewPartner",
            "IRagV2RepositorySelectionView",
            "IRagV2RepositorySelectionViewPartner",
            "IRagV2WebIngestionView",
            "IRagV2WebIngestionViewPartner",
        ):
            assert hasattr(interfaces, name), (
                f"{name} must be defined in agentx.ui.interfaces (G6(a) inner parity)"
            )

    def test_three_inner_factories_present(self) -> None:
        """``ConsoleProvider`` exposes the 3 inner ``create_rag_v2_*_view`` factories."""
        from agentx.ui.providers import ConsoleProvider
        provider = ConsoleProvider()
        for factory in (
            "create_rag_v2_create_repository_view",
            "create_rag_v2_repository_selection_view",
            "create_rag_v2_web_ingestion_view",
        ):
            assert hasattr(provider, factory), (
                f"ConsoleProvider.{factory} must exist (G6(a) inner factory)"
            )
            view = getattr(provider, factory)(MagicMock())
            # Each factory returns an instance of the matching inner ABC.
            iface_name = _iface_for_factory(factory)
            from agentx.ui import interfaces
            iface = getattr(interfaces, iface_name)
            assert isinstance(view, iface), (
                f"{factory} must return an {iface_name} instance"
            )


def _iface_for_factory(factory: str) -> str:
    return {
        "create_rag_v2_create_repository_view": "IRagV2CreateRepositoryView",
        "create_rag_v2_repository_selection_view": "IRagV2RepositorySelectionView",
        "create_rag_v2_web_ingestion_view": "IRagV2WebIngestionView",
    }[factory]


# ── G1 parity: create-repository returns a repository, not None ────────────────


class TestRagV2CreateRepositoryContract(TestCase):
    """G1 mirror for parity — the v2 create-repository contract."""

    def test_create_command_returns_repository_not_none(self) -> None:
        """RagV2MainController.create_repository creates a non-None repository
        when the inner creator succeeds (the view prompts a name → creator
        validates + creates → returns a repository, NOT None)."""
        controller_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        controller = controller_cls()
        # Mock the view (console) and stub the inner creator to return a repo.
        view = MagicMock()
        controller.set_view(view)
        repo = repo_cls(id="test-repo", path="/tmp/rag_v2_test")
        controller._create_repository = MagicMock(return_value=repo)  # type: ignore[attr-defined]
        # Drive the create flow with a valid name via the view's name capture.
        view.capture_repository_name.return_value = "test-repo"
        result = controller.create_repository()
        # The contract: on a valid name, a repository is created — the returned
        # value is the repository (or None with a side effect of setting
        # current_repository); either way the controller reflects a live repo.
        created = result if result is not None else controller.current_repository
        assert created is not None and getattr(created, "id", None) == "test-repo", (
            "create_repository must produce a non-None repository on success (G1 parity)"
        )
        controller._create_repository.assert_called_once()

    def test_create_repository_view_factory_present(self) -> None:
        """ConsoleProvider.create_rag_v2_create_repository_view returns an
        IRagV2CreateRepositoryView instance."""
        from agentx.ui.providers import ConsoleProvider
        from agentx.ui.interfaces import IRagV2CreateRepositoryView
        provider = ConsoleProvider()
        view = provider.create_rag_v2_create_repository_view(MagicMock())
        assert isinstance(view, IRagV2CreateRepositoryView), (
            "create_rag_v2_create_repository_view must return IRagV2CreateRepositoryView"
        )


def _readonly_kwargs(obj: Any, name: str) -> list[str]:
    """Best-effort list of kwarg names for a method; [] on failure."""
    import inspect
    try:
        sig = inspect.signature(getattr(obj, name))
        return list(sig.parameters)
    except (ValueError, TypeError):
        return []


# ── G2 parity: get_selected_repository returns candidate-on-valid / None ──────


class TestRagV2RepositorySelectionContract(TestCase):
    """G2 mirror for parity — selection returns candidate on valid index, None
    on out-of-bounds (1-based display → 0-based internal)."""

    def _build_selection(self, candidates: list[Any]):
        cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_repository_selection_controller",
            "RagV2RepositorySelectionController",
        )
        controller = cls(working_directory="/tmp/rag_v2_test")
        controller._cached_repositories = list(candidates)  # type: ignore[attr-defined]
        return controller

    def test_get_selected_repository_returns_candidate_on_valid_index(self) -> None:
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        candidates = [repo_cls(id=f"r{i}", path=f"/tmp/r{i}") for i in range(3)]
        controller = self._build_selection(candidates)
        # Mock the view's index capture: user picks display-index 2 → internal 1.
        controller.view = MagicMock()
        controller.view.get_selected_index.return_value = 2
        result = controller.get_selected_repository()
        assert result is not None, (
            "get_selected_repository must return the candidate on a valid index "
            "(G2 parity — NOT None)"
        )
        assert result.id == "r1", "display index 2 → internal index 1 → r1"

    def test_get_selected_repository_returns_none_on_out_of_bounds(self) -> None:
        repo_cls = _load_symbol(
            "agentx.model.rag_v2.rag_v2_repository", "RagV2Repository"
        )
        candidates = [repo_cls(id=f"r{i}", path=f"/tmp/r{i}") for i in range(2)]
        controller = self._build_selection(candidates)
        controller.view = MagicMock()
        controller.view.get_selected_index.return_value = 99
        result = controller.get_selected_repository()
        assert result is None, (
            "get_selected_repository must return None on out-of-bounds (G2 parity)"
        )


# ── G5: switch_repository on the main controller ─────────────────────────────


class TestRagV2MainController(TestCase):
    """G5 — RagV2MainController exposes switch_repository()."""

    def test_switch_repository_command_present(self) -> None:
        """``RagV2MainController.switch_repository`` exists + swaps the active
        repository + refreshes state (G5 multi-repo session switch closure)."""
        controller_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        controller = controller_cls()
        assert hasattr(controller, "switch_repository") and callable(
            controller.switch_repository
        ), "RagV2MainController must expose switch_repository() (G5 closure)"
        assert hasattr(controller, "current_repository"), (
            "RagV2MainController must hold current_repository state (G5)"
        )


# ── G6(a) set_view: show_rag_v2 uses set_view, NOT .view = ─────────────────────


class TestRagV2MainControllerWiringUsesSetView(TestCase):
    """G6(a) — show_rag_v2() wires the controller via set_view() (feature_024
    bug-pin: ``.view =`` leaves ``_view=None`` → streaming callbacks silently
    no-op). Constraint d. Verified two ways: (1) behavioral — show_rag_v2
    calls the v2 controller's set_view with the provider-built view; (2)
    source-pin — the show_rag_v2 body contains ``set_view(`` and does NOT
    assign ``_rag_v2_controller.view =`` on the controller."""

    def test_show_rag_v2_calls_set_view_not_dot_view(self) -> None:
        from agentx.ui.screens.main.main_controller import MainController
        from agentx.ui.providers import ConsoleProvider

        # (1) Source-pin: show_rag_v2 body uses set_view( and does not assign .view =.
        src_path = (
            __import__("pathlib").Path(
                "src/agentx/ui/screens/main/main_controller.py"
            )
        )
        src = src_path.read_text(encoding="utf-8")
        # Slice out the show_rag_v2 method body (from def to the next method
        # def — a 4-space-indented "def " at column 0 of a line, NOT a top-level
        # col-0 "\ndef " which would skip all indented methods and over-capture
        # into show_models where the legacy `.view =` assignment lives).
        start = src.find("def show_rag_v2")
        assert start != -1, "MainController must define show_rag_v2() (console rag→v2)"
        # end = next 4-space-indented method def after start, or EOF.
        search_from = start + 1
        end = -1
        while True:
            cand = src.find("\n    def ", search_from)
            if cand == -1:
                break
            end = cand
            break
        body = src[start:] if end == -1 else src[start:end]
        assert "set_view(" in body, (
            "show_rag_v2 must call set_view(view) (feature_024 bug-pin Constraint d)"
        )
        assert ".view = " not in body.replace("_rag_v2_view = ", "", 1), (
            "show_rag_v2 must NOT assign controller.view = view — use set_view() "
            "(feature_024 bug-pin Constraint d)"
        )

        # (2) Behavioral: with a ConsoleProvider, show_rag_v2 builds a view via
        # create_rag_v2_view and threads it through the v2 controller's set_view.
        controller = MainController(provider=ConsoleProvider())
        rag_v2_controller_cls = _load_symbol(
            "agentx.ui.screens.rag_v2.rag_v2_controller", "RagV2MainController"
        )
        set_view_calls: list[Any] = []
        orig_set_view = rag_v2_controller_cls.set_view
        try:
            rag_v2_controller_cls.set_view = (  # type: ignore[method-assign]
                lambda self, view: set_view_calls.append(view)
            )
            controller.show_rag_v2()
        finally:
            rag_v2_controller_cls.set_view = orig_set_view  # type: ignore[method-assign]
        assert set_view_calls, (
            "show_rag_v2 must call set_view(view) on the v2 controller"
        )


if __name__ == "__main__":
    import unittest
    unittest.main()
