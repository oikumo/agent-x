"""UI Interfaces - Abstract Base Classes for dependency inversion.

This module defines the abstract interfaces that all UI implementations must follow.
Controllers depend on these abstractions, not concrete implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Use TYPE_CHECKING to avoid circular imports
    # RagState is defined in rag_controller.py
    pass


class IMainView(ABC):
    """Abstract interface for Main Screen View."""

    @abstractmethod
    def show(self) -> None:
        """Display main screen."""
        pass

    @abstractmethod
    def print_message(self, message: str) -> None:
        """Show info message."""
        pass

    @abstractmethod
    def print_error_message(self, message: str) -> None:
        """Show error message."""
        pass

    @abstractmethod
    def print_warring_message(self, message: str) -> None:
        """Show warning message."""
        pass

    @abstractmethod
    def print_response(self, message: str) -> None:
        """Show response."""
        pass

    @abstractmethod
    def print_response_error(self, message: str) -> None:
        """Show error response."""
        pass


class IRagView(ABC):
    """Abstract interface for RAG Screen View."""

    @abstractmethod
    def show(self) -> None:
        """Display RAG screen."""
        pass

    @abstractmethod
    def print_message(self, message: str) -> None:
        """Show info message."""
        pass

    @abstractmethod
    def print_message_error(self, message: str) -> None:
        """Show error message."""
        pass

    @abstractmethod
    def show_repository_state(self, state: object) -> None:
        """Display repository information."""
        pass

    @abstractmethod
    def show_menu(self) -> None:
        """Display menu options."""
        pass


class IChatView(ABC):
    """Abstract interface for Chat Screen View."""

    @abstractmethod
    def show(self) -> None:
        """Display chat screen."""
        pass

    @abstractmethod
    def show_initial_message(self) -> None:
        """Show welcome message."""
        pass

    @abstractmethod
    def show_message(self, message: str, role: str = "assistant") -> None:
        """Show message.

        Args:
            message: The message content.
            role: Either "user" or "assistant" (default: "assistant").
        """
        pass

    @abstractmethod
    def show_partial_message(self, message: str) -> None:
        """Show partial (streaming) message."""
        pass

    @abstractmethod
    def show_stream_message(self, message: str) -> None:
        """Stream message with typing effect."""
        pass

    @abstractmethod
    def show_message_chat_error(self, message: str | None = None) -> None:
        """Show chat error.

        Args:
            message: Optional actionable error text (e.g. provider name +
                credential hint).  When ``None`` the view uses its own
                generic "chat error" string (backward compatibility).
        """
        pass


class IUIProvider(ABC):
    """Abstract factory for UI components.
    
    This is the main dependency inversion interface.
    Controllers request views through this provider, never creating them directly.
    """

    @abstractmethod
    def create_main_view(self, controller: "IMainViewPartner") -> IMainView:
        """Create main view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            IMainView implementation
        """
        pass

    @abstractmethod
    def create_rag_view(self, controller: "IRagViewPartner") -> IRagView:
        """Create RAG view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            IRagView implementation
        """
        pass

    # --- RAG v2 (feature_027) — console-only sibling factories ---

    @abstractmethod
    def create_rag_v2_view(self, controller: "IRagV2ViewPartner") -> "IRagV2View":
        """Create the console RAG v2 outer view implementation."""
        pass

    @abstractmethod
    def create_rag_v2_create_repository_view(self, controller) -> "IRagV2CreateRepositoryView":
        """Create the console RAG v2 create-repository sub-screen view."""
        pass

    @abstractmethod
    def create_rag_v2_repository_selection_view(self, controller) -> "IRagV2RepositorySelectionView":
        """Create the console RAG v2 repository-selection sub-screen view."""
        pass

    @abstractmethod
    def create_rag_v2_web_ingestion_view(self, controller) -> "IRagV2WebIngestionView":
        """Create the console RAG v2 web-ingestion sub-screen view."""
        pass

    @abstractmethod
    def create_rag_v2_pdf_ingestion_view(self, controller) -> "IRagV2PdfIngestionView":
        """Create the console RAG v2 PDF-ingestion sub-screen view."""
        pass

    @abstractmethod
    def create_rag_v2_md_ingestion_view(self, controller) -> "IRagV2MdIngestionView":
        """Create the console RAG v2 MD-ingestion sub-screen view."""
        pass
    @abstractmethod
    def create_chat_view(self, controller: "IChatViewPartner") -> IChatView:
        """Create chat view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            IChatView implementation
        """
        pass

    # --- New methods for console parity (feature_024) ---

    @abstractmethod
    def create_react_view(self, controller: "IReactViewPartner") -> "IReactView":
        """Create ReAct view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            IReactView implementation
        """
        pass

    @abstractmethod
    def create_coding_view(self, controller: "ICodingViewPartner") -> "ICodingView":
        """Create Coding view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            ICodingView implementation
        """
        pass

    @abstractmethod
    def create_models_view(self, controller: "IModelsViewPartner") -> "IModelsView":
        """Create Models selector view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            IModelsView implementation
        """
        pass

    @abstractmethod
    def create_agent_view(self, controller: "IConsoleAgentViewPartner") -> "IAgentView":
        """Create Advanced Agent view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            IAgentView implementation
        """
        pass

    @abstractmethod
    def create_fast_agent_view(self, controller: "IConsoleFastAgentViewPartner") -> "IFastAgentView":
        """Create Fast Agent view implementation.
        
        Args:
            controller: The controller that will use this view
            
        Returns:
            IFastAgentView implementation
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize UI framework."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup UI resources."""
        pass


# Forward declarations for type hints
# These interfaces are defined in controller files to avoid circular imports
class IMainViewPartner(ABC):
    """Abstract partner for Main View (implemented by MainController)."""

    @abstractmethod
    def run_command(self, user_input: str) -> None:
        """Execute a user command."""
        pass

    @abstractmethod
    def error(self) -> None:
        """Handle error state."""
        pass

    @abstractmethod
    def print(self) -> None:
        """Print output."""
        pass

    @abstractmethod
    def show_chat(self) -> None:
        """Show chat screen."""
        pass

    @abstractmethod
    def show_rag(self) -> None:
        """Show RAG screen."""
        pass


class IRagViewPartner(ABC):
    """Abstract partner for RAG View (implemented by RagController)."""

    @abstractmethod
    def select_repository(self) -> None:
        """Select a repository."""
        pass

    @abstractmethod
    def create_repository(self) -> None:
        """Create a new repository."""
        pass

    @abstractmethod
    def show_chat(self) -> None:
        """Show chat screen."""
        pass

    @abstractmethod
    def show_web_ingestion(self) -> None:
        """Show web ingestion screen."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the view."""
        pass

    @abstractmethod
    def get_rag_state(self) -> object:
        """Get RAG repository state."""
        pass


class IChatViewPartner(ABC):
    """Abstract partner for Chat View (implemented by ChatController)."""

    @abstractmethod
    def process_user_message(self, user_message: str) -> bool:
        """Process a user message."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the view."""
        pass

    @abstractmethod
    def start_interactive_streaming(self, system_prompt: str) -> None:
        """Start interactive streaming with system prompt."""
        pass


class IReactViewPartner(ABC):
    """Abstract partner for ReAct View (implemented by ReactController).

    This is the interface the TUI View calls to interact with the Controller.
    The View receives this via constructor injection and should type-hint it
    as ``Any`` (duck-typed) to avoid a metaclass conflict with Textual's
    Screen.  ``register_partner`` virtually registers the screen as a
    subclass of this ABC.
    """

    @abstractmethod
    def send_message(self, user_message: str) -> bool:
        """Send a user message to the ReAct agent.

        Args:
            user_message: The user's input text.

        Returns:
            True if the message was accepted (agent started), False if the
            agent is already running.
        """
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel an in-progress agent run."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the agent is currently running."""
        pass

    @abstractmethod
    def get_history(self) -> list:
        """Get the conversation message history."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the controller and cancel any running agent."""
        pass

    @abstractmethod
    def start_new_conversation(self) -> None:
        """Start a new conversation (reset thread)."""
        pass


class ICodingViewPartner(ABC):
    """Abstract partner for Coding View (implemented by CodingController).

    This is the interface the TUI View calls to interact with the Controller.
    The View receives this via constructor injection and should type-hint it
    as ``Any`` (duck-typed) to avoid a metaclass conflict with Textual's
    Screen. ``register_partner`` virtually registers the screen as a
    subclass of this ABC.
    """

    @abstractmethod
    def send_message(self, user_message: str) -> bool:
        """Send a user message to the Coding agent.

        Args:
            user_message: The user's input text.

        Returns:
            True if the message was accepted (agent started), False if the
            agent is already running.
        """
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel an in-progress agent run."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the agent is currently running."""
        pass

    @abstractmethod
    def get_history(self) -> list:
        """Get the conversation message history."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the controller and cancel any running agent."""
        pass

    @abstractmethod
    def start_new_conversation(self) -> None:
        """Start a new conversation (reset thread)."""
        pass


class IModelsView(ABC):
    """Abstract interface for Models Selector View (console parity)."""

    @abstractmethod
    def show(self) -> None:
        """Display models selector screen."""
        pass

    @abstractmethod
    def show_available_providers(self, providers: list[str]) -> None:
        """Show list of available AI providers."""
        pass

    @abstractmethod
    def show_models_for_provider(self, provider: str, models: list[str]) -> None:
        """Show models available for a specific provider."""
        pass

    @abstractmethod
    def show_message(self, message: str) -> None:
        """Show info message."""
        pass

    @abstractmethod
    def print_error(self, message: str) -> None:
        """Show error message."""
        pass


class IModelsViewPartner(ABC):
    """Abstract partner for Models View (implemented by ModelsController)."""

    @abstractmethod
    def select_model(self, provider: str, model: str) -> None:
        """Select a model from a provider."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the view."""
        pass


class IReactView(ABC):
    """Abstract interface for ReAct View (console parity)."""

    @abstractmethod
    def show(self) -> None:
        """Display ReAct chat screen."""
        pass

    @abstractmethod
    def show_message(self, message: str, role: str = "assistant") -> None:
        """Show complete message."""
        pass

    @abstractmethod
    def show_partial_message(self, message: str) -> None:
        """Show partial (streaming) message."""
        pass

    @abstractmethod
    def show_stream_message(self, message: str) -> None:
        """Stream message with typing effect."""
        pass

    @abstractmethod
    def print_error(self, message: str) -> None:
        """Show error message."""
        pass


class ICodingView(ABC):
    """Abstract interface for Coding View (console parity)."""

    @abstractmethod
    def show(self) -> None:
        """Display Coding agent screen."""
        pass

    @abstractmethod
    def show_message(self, message: str, role: str = "assistant") -> None:
        """Show complete message."""
        pass

    @abstractmethod
    def show_partial_message(self, message: str) -> None:
        """Show partial (streaming) message."""
        pass

    @abstractmethod
    def show_stream_message(self, message: str) -> None:
        """Stream message with typing effect."""
        pass

    @abstractmethod
    def print_error(self, message: str) -> None:
        """Show error message."""
        pass


class IAgentView(ABC):
    """Abstract interface for Advanced Agent View (console parity)."""

    @abstractmethod
    def show(self) -> None:
        """Display Advanced Agent screen."""
        pass

    @abstractmethod
    def show_message(self, message: str, role: str = "assistant") -> None:
        """Show complete message."""
        pass

    @abstractmethod
    def show_partial_message(self, message: str) -> None:
        """Show partial (streaming) message."""
        pass

    @abstractmethod
    def show_stream_message(self, message: str) -> None:
        """Stream message with typing effect."""
        pass

    @abstractmethod
    def print_error(self, message: str) -> None:
        """Show error message."""
        pass


class IConsoleAgentViewPartner(ABC):
    """Abstract partner for Advanced Agent View (implemented by AgentController) — console mode."""

    @abstractmethod
    def send_message(self, user_message: str) -> bool:
        """Send a user message to the Agent."""
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel an in-progress agent run."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the agent is currently running."""
        pass

    @abstractmethod
    def get_history(self) -> list:
        """Get the conversation message history."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the controller and cancel any running agent."""
        pass

    @abstractmethod
    def start_new_conversation(self) -> None:
        """Start a new conversation (reset thread)."""
        pass


class IFastAgentView(ABC):
    """Abstract interface for Fast Agent View (console parity)."""

    @abstractmethod
    def show(self) -> None:
        """Display Fast Agent modal screen."""
        pass

    @abstractmethod
    def show_cycle_summary(self, summary: dict) -> None:
        """Show cycle summary result."""
        pass

    @abstractmethod
    def print_error(self, message: str) -> None:
        """Show error message."""
        pass


class IConsoleFastAgentViewPartner(ABC):
    """Abstract partner for Fast Agent View (implemented by FastAgentController) — console mode."""

    @abstractmethod
    def send_message(self, user_message: str) -> bool:
        """Send a user message to the Fast Agent."""
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel an in-progress agent run."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the agent is currently running."""
        pass

    @abstractmethod
    def get_cycle_summary(self) -> dict:
        """Get the last cycle summary."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the controller and cancel any running agent."""
        pass

    @abstractmethod
    def start_new_conversation(self) -> None:
        """Start a new conversation (reset thread)."""
        pass


# ── RAG v2 (feature_027) — console-only; v1 IRagView/IRagViewPartner locked ──
# v2 is a console sibling of v1. The outer ABC pair + 3 inner ABC pairs (G6(a)
# narrow closure); PDF/MD ingestion views are G4-new ABC pairs. v1's ABCs are
# NOT touched (D3 defer — v1 stays for the TUI path).

class IRagV2View(ABC):
    """Abstract interface for the console RAG v2 outer view."""

    @abstractmethod
    def show(self) -> None:
        """Display the RAG v2 console screen."""
        pass

    @abstractmethod
    def print_message(self, message: str) -> None:
        """Show an info message."""
        pass

    @abstractmethod
    def print_message_error(self, message: str) -> None:
        """Show an error message."""
        pass

    @abstractmethod
    def show_repository_state(self, state: object) -> None:
        """Display repository information."""
        pass

    @abstractmethod
    def show_menu(self) -> None:
        """Display the menu options."""
        pass


class IRagV2ViewPartner(ABC):
    """Abstract partner for the RAG v2 view (implemented by RagV2MainController)."""

    @abstractmethod
    def select_repository(self) -> None:
        """Select a repository."""
        pass

    @abstractmethod
    def create_repository(self) -> None:
        """Create a new repository."""
        pass

    @abstractmethod
    def show_chat(self) -> None:
        """Show the chat session."""
        pass

    @abstractmethod
    def show_web_ingestion(self) -> None:
        """Show the web-ingestion sub-screen."""
        pass

    @abstractmethod
    def show_pdf_ingestion(self) -> None:
        """Show the PDF-ingestion sub-screen (G4)."""
        pass

    @abstractmethod
    def show_md_ingestion(self) -> None:
        """Show the MD-ingestion sub-screen (G4)."""
        pass

    @abstractmethod
    def switch_repository(self) -> None:
        """Switch the active repository (G5)."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the view."""
        pass

    @abstractmethod
    def get_rag_state(self) -> object:
        """Get the RAG repository state."""
        pass


# --- RAG v2 inner ABC pairs (G6(a) narrow closure) ---------------------------

class IRagV2CreateRepositoryView(ABC):
    """Abstract interface for the RAG v2 create-repository sub-screen."""

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        pass

    @abstractmethod
    def show_success(self, repo_id: str, repo_path: str) -> None:
        pass


class IRagV2CreateRepositoryViewPartner(ABC):
    """Abstract partner for the RAG v2 create-repository view."""

    @abstractmethod
    def on_name_entered(self, name: str) -> bool:
        pass

    @abstractmethod
    def get_prompt(self) -> str:
        pass


class IRagV2RepositorySelectionView(ABC):
    """Abstract interface for the RAG v2 repository-selection sub-screen."""

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def get_selected_index(self) -> int:
        pass


class IRagV2RepositorySelectionViewPartner(ABC):
    """Abstract partner for the RAG v2 repository-selection view."""

    @abstractmethod
    def get_repositories(self) -> "list[str] | None":
        pass


class IRagV2WebIngestionView(ABC):
    """Abstract interface for the RAG v2 web-ingestion sub-screen (G4)."""

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        pass


class IRagV2WebIngestionViewPartner(ABC):
    """Abstract partner for the RAG v2 web-ingestion view."""

    @abstractmethod
    def ingest_url(self, url: str) -> int:
        pass


class IRagV2PdfIngestionView(ABC):
    """Abstract interface for the RAG v2 PDF-ingestion sub-screen (G4 new)."""

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        pass


class IRagV2PdfIngestionViewPartner(ABC):
    """Abstract partner for the RAG v2 PDF-ingestion view."""

    @abstractmethod
    def ingest_path(self, pdf_path: str) -> int:
        pass


class IRagV2MdIngestionView(ABC):
    """Abstract interface for the RAG v2 MD-ingestion sub-screen (G4 new)."""

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        pass


class IRagV2MdIngestionViewPartner(ABC):
    """Abstract partner for the RAG v2 MD-ingestion view."""

    @abstractmethod
    def ingest_path(self, md_path: str) -> int:
        pass