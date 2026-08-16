"""TUI Provider - Textual-based UI implementation.

This module provides the Textual TUI implementation of the UI provider interface.
It is completely isolated from the existing UI module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agentx.ui.interfaces import IUIProvider, IMainView, IRagView, IChatView, IReactView, ICodingView, IModelsView, IAgentView, IFastAgentView
from agentx.ui.providers import ProviderRegistry

if TYPE_CHECKING:
    from agentx.ui.interfaces import IMainViewPartner, IRagViewPartner, IChatViewPartner, IModelsViewPartner, IReactViewPartner, ICodingViewPartner, IConsoleAgentViewPartner, IConsoleFastAgentViewPartner
    from agentx.ui.interfaces import IRagV2View, IRagV2CreateRepositoryView, IRagV2RepositorySelectionView, IRagV2WebIngestionView, IRagV2PdfIngestionView, IRagV2MdIngestionView


class TUIProvider(IUIProvider):
    """Textual TUI provider.
    
    Creates TUI adapters for all screens using the Textual framework.
    This is a completely isolated implementation that doesn't modify existing UI code.
    """

    def __init__(self) -> None:
        self._app: object | None = None
        self._initialized = False

    def create_main_view(self, controller: IMainViewPartner) -> IMainView:
        """Create TUI adapter for main screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUIAdapter instance
        """
        from agentx.ui.tui.adapters.main_adapter import TUIAdapter
        return TUIAdapter(controller)

    def create_rag_view(self, controller: IRagViewPartner) -> IRagView:
        """Create TUI adapter for RAG screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUIRagAdapter instance
        """
        from agentx.ui.tui.adapters.rag_adapter import TUIRagAdapter
        return TUIRagAdapter(controller)

    def create_chat_view(self, controller: IChatViewPartner) -> IChatView:
        """Create TUI adapter for chat screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUIChatAdapter instance
        """
        from agentx.ui.tui.adapters.chat_adapter import TUIChatAdapter
        return TUIChatAdapter(controller)

    # --- Console parity methods (feature_024) ---

    def create_react_view(self, controller: IReactViewPartner) -> IReactView:
        """Create TUI adapter for ReAct screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUIReactAdapter instance
        """
        from agentx.ui.tui.adapters.react_adapter import TUIReactAdapter
        return TUIReactAdapter(controller)

    def create_coding_view(self, controller: ICodingViewPartner) -> ICodingView:
        """Create TUI adapter for Coding screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUICodingAdapter instance
        """
        from agentx.ui.tui.adapters.coding_adapter import TUICodingAdapter
        return TUICodingAdapter(controller)

    def create_models_view(self, controller: IModelsViewPartner) -> IModelsView:
        """Create TUI adapter for Models screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUIModelsAdapter instance
        """
        from agentx.ui.tui.adapters.models_adapter import TUIModelsAdapter
        return TUIModelsAdapter(controller)

    def create_agent_view(self, controller: IConsoleAgentViewPartner) -> IAgentView:
        """Create TUI adapter for Advanced Agent screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUIAgentAdapter instance
        """
        from agentx.ui.tui.adapters.agent_adapter import TUIAgentAdapter
        return TUIAgentAdapter(controller)

    def create_fast_agent_view(self, controller: IConsoleFastAgentViewPartner) -> IFastAgentView:
        """Create TUI adapter for Fast Agent screen.
        
        Args:
            controller: Controller instance
            
        Returns:
            TUIFastAgentAdapter instance
        """
        from agentx.ui.tui.adapters.fast_agent_adapter import TUIFastAgentAdapter
        return TUIFastAgentAdapter(controller)

    # --- RAG v2 (feature_027) — console-only; TUI refuses to host v2 ---
    def create_rag_v2_view(self, controller) -> "IRagV2View":
        raise NotImplementedError("RAG v2 is console-only; use the console provider.")

    def create_rag_v2_create_repository_view(self, controller) -> "IRagV2CreateRepositoryView":
        raise NotImplementedError("RAG v2 is console-only; use the console provider.")

    def create_rag_v2_repository_selection_view(self, controller) -> "IRagV2RepositorySelectionView":
        raise NotImplementedError("RAG v2 is console-only; use the console provider.")

    def create_rag_v2_web_ingestion_view(self, controller) -> "IRagV2WebIngestionView":
        raise NotImplementedError("RAG v2 is console-only; use the console provider.")

    def create_rag_v2_pdf_ingestion_view(self, controller) -> "IRagV2PdfIngestionView":
        raise NotImplementedError("RAG v2 is console-only; use the console provider.")

    def create_rag_v2_md_ingestion_view(self, controller) -> "IRagV2MdIngestionView":
        raise NotImplementedError("RAG v2 is console-only; use the console provider.")

    def initialize(self) -> None:
        """Initialize Textual framework."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown Textual framework."""
        self._initialized = False


# Register TUI provider
ProviderRegistry.register("tui", TUIProvider(), set_default=True)