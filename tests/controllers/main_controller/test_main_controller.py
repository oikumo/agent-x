"""
Unit tests for MainController new provider-backed show_* methods.

Follows OMT++ §11:
  - Stage 1: Unit test Controller with mocked Provider + mocked View
  - Stage 2: Integration test Controller + real View with mocked Provider
"""

from __future__ import annotations

from unittest import TestCase
from unittest.mock import MagicMock, patch

from agentx.ui.screens.main.main_controller import MainController
from agentx.ui.interfaces import IUIProvider


class TestMainControllerShowReact(TestCase):
    """Unit tests for MainController.show_react() using provider."""

    def setUp(self) -> None:
        self.mock_provider = MagicMock(spec=IUIProvider)
        self.mock_react_view = MagicMock()
        self.mock_provider.create_react_view.return_value = self.mock_react_view
        self.controller = MainController(provider=self.mock_provider)

    def test_show_react_calls_provider_create_react_view(self) -> None:
        """show_react() should call provider.create_react_view(controller)."""
        # Act
        self.controller.show_react()

        # Assert
        self.mock_provider.create_react_view.assert_called_once()
        call_args = self.mock_provider.create_react_view.call_args[0]
        assert isinstance(call_args[0], object)  # controller passed

    def test_show_react_stores_controller_and_view(self) -> None:
        """show_react() should store ReactController and view for later retrieval."""
        self.controller.show_react()

        assert self.controller._react_controller is not None
        assert self.controller._react_view is self.mock_react_view

    def test_show_react_wires_controller_to_view(self) -> None:
        """Created controller should have its view attribute set."""
        self.controller.show_react()

        react_controller = self.controller._react_controller
        assert react_controller is not None
        assert react_controller.view is self.mock_react_view

    def test_show_react_does_not_call_view_show(self) -> None:
        """show_react() should NOT call view.show() — that's for TUI screens."""
        self.controller.show_react()
        self.mock_react_view.show.assert_not_called()


class TestMainControllerShowCoding(TestCase):
    """Unit tests for MainController.show_coding() using provider."""

    def setUp(self) -> None:
        self.mock_provider = MagicMock(spec=IUIProvider)
        self.mock_coding_view = MagicMock()
        self.mock_provider.create_coding_view.return_value = self.mock_coding_view
        self.controller = MainController(provider=self.mock_provider)

    def test_show_coding_calls_provider_create_coding_view(self) -> None:
        self.controller.show_coding()
        self.mock_provider.create_coding_view.assert_called_once()

    def test_show_coding_stores_controller_and_view(self) -> None:
        self.controller.show_coding()
        assert self.controller._coding_controller is not None
        assert self.controller._coding_view is self.mock_coding_view


class TestMainControllerShowModels(TestCase):
    """Unit tests for MainController.show_models() using provider."""

    def setUp(self) -> None:
        self.mock_provider = MagicMock(spec=IUIProvider)
        self.mock_models_view = MagicMock()
        self.mock_provider.create_models_view.return_value = self.mock_models_view
        self.controller = MainController(provider=self.mock_provider)

    def test_show_models_calls_provider_create_models_view(self) -> None:
        self.controller.show_models()
        self.mock_provider.create_models_view.assert_called_once()

    def test_show_models_stores_controller_and_view(self) -> None:
        self.controller.show_models()
        assert self.controller._models_controller is not None
        assert self.controller._models_view is self.mock_models_view


class TestMainControllerShowAgent(TestCase):
    """Unit tests for MainController.show_agent() using provider."""

    def setUp(self) -> None:
        self.mock_provider = MagicMock(spec=IUIProvider)
        self.mock_agent_view = MagicMock()
        self.mock_provider.create_agent_view.return_value = self.mock_agent_view
        self.controller = MainController(provider=self.mock_provider)

    def test_show_agent_calls_provider_create_agent_view(self) -> None:
        self.controller.show_agent()
        self.mock_provider.create_agent_view.assert_called_once()

    def test_show_agent_stores_controller_and_view(self) -> None:
        self.controller.show_agent()
        assert self.controller._agent_controller is not None
        assert self.controller._agent_view is self.mock_agent_view


class TestMainControllerShowFastAgent(TestCase):
    """Unit tests for MainController.show_fast_agent() using provider."""

    def setUp(self) -> None:
        self.mock_provider = MagicMock(spec=IUIProvider)
        self.mock_fast_agent_view = MagicMock()
        self.mock_provider.create_fast_agent_view.return_value = self.mock_fast_agent_view
        self.controller = MainController(provider=self.mock_provider)

    def test_show_fast_agent_calls_provider_create_fast_agent_view(self) -> None:
        self.controller.show_fast_agent()
        self.mock_provider.create_fast_agent_view.assert_called_once()

    def test_show_fast_agent_stores_controller_and_view(self) -> None:
        self.controller.show_fast_agent()
        assert self.controller._fast_agent_controller is not None
        assert self.controller._fast_agent_view is self.mock_fast_agent_view