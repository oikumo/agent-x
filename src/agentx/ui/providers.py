"""UI Providers - Dependency injection for UI implementations.

This module provides the provider registry and concrete implementations.
Controllers request views through providers, maintaining dependency inversion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agentx.ui.interfaces import IMainView, IChatView, IRagView, IUIProvider, IModelsView, IReactView, ICodingView, IAgentView, IFastAgentView

if TYPE_CHECKING:
    from agentx.ui.interfaces import IMainViewPartner, IRagViewPartner, IChatViewPartner, IModelsViewPartner, IReactViewPartner, ICodingViewPartner, IConsoleAgentViewPartner, IConsoleFastAgentViewPartner
    from agentx.ui.interfaces import IRagV2View, IRagV2ViewPartner, IRagV2CreateRepositoryView, IRagV2RepositorySelectionView, IRagV2WebIngestionView, IRagV2PdfIngestionView, IRagV2MdIngestionView


class ProviderRegistry:
    """Registry for UI providers.
    
    Allows switching between different UI implementations (TUI, console, etc.)
    without changing controller code.
    """

    _providers: dict[str, IUIProvider] = {}
    _default: str | None = None

    @classmethod
    def register(cls, name: str, provider: IUIProvider, set_default: bool = False) -> None:
        """Register a provider.
        
        Args:
            name: Provider identifier
            provider: Provider instance
            set_default: If True, set as default provider
        """
        cls._providers[name] = provider
        if set_default:
            cls._default = name

    @classmethod
    def get(cls, name: str) -> IUIProvider:
        """Get provider by name.
        
        Args:
            name: Provider identifier
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider not found
        """
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' not found. Available: {list(cls._providers.keys())}")
        return cls._providers[name]

    @classmethod
    def get_default(cls) -> IUIProvider:
        """Get default provider.
        
        Returns:
            Default provider instance
            
        Raises:
            ValueError: If no default set
        """
        if cls._default is None:
            raise ValueError("No default provider set. Register a provider with set_default=True")
        return cls._providers[cls._default]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List registered provider names.
        
        Returns:
            List of provider names
        """
        return list(cls._providers.keys())


class ConsoleProvider(IUIProvider):
    """Fallback provider using existing console-based views.
    
    This provider maintains backward compatibility by using
    the existing ANSI console views.
    """

    def __init__(self) -> None:
        self._initialized = False

    def create_main_view(self, controller: IMainViewPartner) -> IMainView:
        """Create console-based main view.
        
        Args:
            controller: Controller instance
            
        Returns:
            MainView instance
        """
        from agentx.ui.screens.main.main_view import MainView
        return MainView(controller)  # type: ignore

    def create_rag_view(self, controller: IRagViewPartner) -> IRagView:
        """Create console-based RAG view.
        
        Args:
            controller: Controller instance
            
        Returns:
            RagView instance
        """
        from agentx.ui.screens.rag.rag_view import RagView
        return RagView(controller)  # type: ignore

    def create_chat_view(self, controller: IChatViewPartner) -> IChatView:
        """Create console-based chat view.
        
        Args:
            controller: Controller instance
            
        Returns:
            ChatView instance
        """
        from agentx.ui.screens.chat.chat_view import ChatView
        return ChatView(controller)  # type: ignore

    # --- Console parity methods (feature_024) ---

    def create_react_view(self, controller: "IReactViewPartner") -> IReactView:
        """Create console-based ReAct view.
        
        Args:
            controller: Controller instance
            
        Returns:
            ConsoleReactView instance
        """
        from agentx.ui.screens.react.react_view import ConsoleReactView
        return ConsoleReactView(controller)  # type: ignore

    def create_coding_view(self, controller: "ICodingViewPartner") -> ICodingView:
        """Create console-based Coding view.
        
        Args:
            controller: Controller instance
            
        Returns:
            ConsoleCodingView instance
        """
        from agentx.ui.screens.coding.coding_view import ConsoleCodingView
        return ConsoleCodingView(controller)  # type: ignore

    def create_models_view(self, controller: "IModelsViewPartner") -> IModelsView:
        """Create console-based Models view.
        
        Args:
            controller: Controller instance
            
        Returns:
            ConsoleModelsView instance
        """
        from agentx.ui.screens.models.models_view import ConsoleModelsView
        return ConsoleModelsView(controller)  # type: ignore

    def create_agent_view(self, controller: "IConsoleAgentViewPartner") -> IAgentView:
        """Create console-based Advanced Agent view.
        
        Args:
            controller: Controller instance
            
        Returns:
            ConsoleAgentView instance
        """
        from agentx.ui.screens.agent.agent_view import ConsoleAgentView
        return ConsoleAgentView(controller)  # type: ignore

    def create_fast_agent_view(self, controller: "IConsoleFastAgentViewPartner") -> IFastAgentView:
        """Create console-based Fast Agent view.
        
        Args:
            controller: Controller instance
            
        Returns:
            ConsoleFastAgentView instance
        """
        from agentx.ui.screens.fast_agent.fast_agent_view import ConsoleFastAgentView
        return ConsoleFastAgentView(controller)  # type: ignore

    # --- RAG v2 (feature_027) — console-only sibling factories ---

    def create_rag_v2_view(self, controller: "IRagV2ViewPartner") -> "IRagV2View":
        """Create the console RAG v2 outer view."""
        from agentx.ui.screens.rag_v2.rag_v2_view import RagV2View
        return RagV2View(controller)  # type: ignore

    def create_rag_v2_create_repository_view(self, controller):
        """Create the console RAG v2 create-repository sub-screen view."""
        from agentx.ui.screens.rag_v2.rag_v2_create_repository_view import (
            RagV2CreateRepositoryView,
        )
        return RagV2CreateRepositoryView(controller)

    def create_rag_v2_repository_selection_view(self, controller):
        """Create the console RAG v2 repository-selection sub-screen view."""
        from agentx.ui.screens.rag_v2.rag_v2_repository_selection_view import (
            RagV2RepositorySelectionView,
        )
        return RagV2RepositorySelectionView(controller)

    def create_rag_v2_web_ingestion_view(self, controller):
        """Create the console RAG v2 web-ingestion sub-screen view."""
        from agentx.ui.screens.rag_v2.rag_v2_web_ingestion_view import (
            RagV2WebIngestionView,
        )
        return RagV2WebIngestionView(controller)

    def create_rag_v2_pdf_ingestion_view(self, controller):
        """Create the console RAG v2 PDF-ingestion sub-screen view."""
        from agentx.ui.screens.rag_v2.rag_v2_pdf_ingestion_view import (
            RagV2PdfIngestionView,
        )
        return RagV2PdfIngestionView(controller)

    def create_rag_v2_md_ingestion_view(self, controller):
        """Create the console RAG v2 MD-ingestion sub-screen view."""
        from agentx.ui.screens.rag_v2.rag_v2_md_ingestion_view import (
            RagV2MdIngestionView,
        )
        return RagV2MdIngestionView(controller)

    def initialize(self) -> None:
        """Initialize console UI (no-op)."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown console UI (no-op)."""
        self._initialized = False


# Register console provider as fallback
# Note: TUI provider will be added in ui/tui/provider.py
ProviderRegistry.register("console", ConsoleProvider())

# Import TUI provider to register it (if available)
try:
    from agentx.ui.tui import provider as tui_provider_module
    # TUI provider is registered in its module
except ImportError:
    pass  # TUI not available, use console only