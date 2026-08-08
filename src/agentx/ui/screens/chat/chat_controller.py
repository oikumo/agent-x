from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from agentx.model.ai.service import AIService
from agentx.model.chat import ChatHistoryRepository, Conversation
from agentx.ui.interfaces import IChatView, IChatViewPartner


class ChatController(IChatViewPartner):
    def __init__(
        self, 
        view: IChatView | None = None,
        history_repo: ChatHistoryRepository | None = None
    ) -> None:
        self.view = view if view else None  # Will be set by provider if None
        self.history: list[BaseMessage] = []
        self.llm = AIService().get_current_llm()
        self.history_repo = history_repo or ChatHistoryRepository()
        self.current_conversation_id: int | None = None

    def show(self):
        self.start_interactive_streaming(system_prompt="You are a helpful assistant.")
        if self.view:
            self.view.show()

    def close(self) -> None:
        pass

    def start_interactive_streaming(self, system_prompt: str) -> None:
        self.history.clear()
        self.history.append(SystemMessage(content=system_prompt))

    def process_user_message(self, user_message: str) -> bool:
        if user_message.strip().lower() in ("quit", "exit"):
            return False

        stripped = user_message.strip()
        if not stripped:
            return False

        self.history.append(HumanMessage(content=stripped))

        try:
            full_response: list[str] = []

            for chunk_content in self.get_streaming_response(self.llm, self.history):
                if self.view:
                    self.view.show_partial_message(chunk_content)
                full_response.append(chunk_content)

            if self.view:
                self.view.show_partial_message("\n")
            
            response_content = "".join(full_response)
            self.history.append(AIMessage(content=response_content))

            # Persist to database if conversation is active
            if self.current_conversation_id:
                self._save_messages(stripped, response_content)

            return True

        except Exception as e:
            self.history.pop()
            message = self._format_chat_error(e)
            if self.view:
                self.view.show_message_chat_error(message)
            else:
                print(message)

            return True

    # Error-message affordance map for the catalog providers (feature_024 chat
    # error surfacing).  Maps the provider's ``ProviderInfo.id`` to the env var
    # whose value controls that provider's auth — gives the user an actionable
    # hint instead of a bare ``[403] Forbidden``.
    _AUTH_ENV_VARS: dict[str, str] = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "nvidia": "NVIDIA_API_KEY",
        "ollama": "OLLAMA base URL",
        "llamacpp": "local GGUF path",
    }

    def _format_chat_error(self, exc: Exception) -> str:
        """Build a user-facing error message that surfaces *which* provider
        failed and the actionable credential/env-var to check.

        Replaces the pre-fix bare ``print(f"Error: {e}")`` — that swallowed LLM
        exceptions so silently a dead ``NVIDIA_API_KEY`` (e.g. a 403 from a
        revoked key on the NVIDIA API Catalog) looked like "chat silently
        fails" with one bare line on stdout and no UI feedback.
        """
        # Resolve the active provider's display name + id defensively — the
        # selector may be in any state; never raise from an error handler.
        provider_name = "Unknown provider"
        provider_id = ""
        try:
            ai = AIService()
            info = ai.get_current_provider_info()
            provider_name = info.name
            provider_id = info.id
        except Exception:
            pass
        hint = self._AUTH_ENV_VARS.get(provider_id, "API key / config")
        return (
            f"[chat error] {provider_name}: {exc} "
            f"— check {hint}"
        )

    def get_streaming_response(self, llm: BaseChatModel, history: list):
        for chunk in llm.stream(history):
            content = self._extract_chunk_content(chunk)
            if content:
                yield content

    def _extract_chunk_content(self, chunk) -> str:
        if hasattr(chunk, "text"):
            return str(chunk.text)
        if chunk.content is None:
            return ""
        if isinstance(chunk.content, list):
            return " ".join(str(item) for item in chunk.content if item is not None)
        return str(chunk.content)

    # === Persistence Methods ===

    def start_new_conversation(self, title: str | None = None, model_provider: str | None = None) -> int:
        """Create a new conversation and set as current.
        
        Args:
            title: Optional conversation title (auto-generated if not provided)
            model_provider: Optional model provider name
            
        Returns:
            New conversation ID
        """
        if title is None:
            from datetime import datetime
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if model_provider is None:
            model_provider = AIService().get_current_provider_name() or "Unknown"
        
        self.current_conversation_id = self.history_repo.create_conversation(title, model_provider)
        self.start_interactive_streaming(system_prompt="You are a helpful assistant.")
        return self.current_conversation_id

    def load_conversation(self, conversation_id: int) -> bool:
        """Load a conversation from the database.
        
        Args:
            conversation_id: ID of conversation to load
            
        Returns:
            True if loaded successfully, False if not found
        """
        result = self.history_repo.get_conversation_with_messages(conversation_id)
        if not result:
            return False
        
        conv, messages = result
        self.current_conversation_id = conversation_id
        
        # Rebuild history from stored messages
        self.history.clear()
        self.history.append(SystemMessage(content="You are a helpful assistant."))
        
        for msg in messages:
            if msg.role == "user":
                self.history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                self.history.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                self.history.append(SystemMessage(content=msg.content))
        
        # Notify view to refresh
        if self.view:
            self.view.show_initial_message()
            for msg in messages:
                if msg.role != "system":
                    self.view.show_message(msg.content, msg.role)
        
        return True

    def save_conversation(self) -> bool:
        """Save current in-memory history to the database.
        
        Returns:
            True if saved, False if no active conversation
        """
        if self.current_conversation_id is None:
            return False
        
        # Messages are already saved incrementally in process_user_message
        # This method is for explicit saves if needed
        return True

    def list_conversations(self, limit: int = 20) -> list[Conversation]:
        """Get recent conversations for the sidebar.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        return self.history_repo.get_recent_conversations(limit)

    def _save_messages(self, user_message: str, assistant_response: str) -> None:
        """Save user and assistant messages to the database."""
        if self.current_conversation_id is None:
            return
        
        self.history_repo.add_message(
            self.current_conversation_id, 
            "user", 
            user_message
        )
        self.history_repo.add_message(
            self.current_conversation_id, 
            "assistant", 
            assistant_response
        )
    
    def get_current_conversation_id(self) -> int | None:
        """Get the current conversation ID."""
        return self.current_conversation_id
    
    def set_current_conversation_id(self, conversation_id: int) -> None:
        """Set the current conversation ID (for loading existing)."""
        self.current_conversation_id = conversation_id
    
    def delete_current_conversation(self) -> bool:
        """Delete the current conversation."""
        if self.current_conversation_id is None:
            return False
        result = self.history_repo.delete_conversation(self.current_conversation_id)
        if result:
            self.current_conversation_id = None
            self.start_interactive_streaming(system_prompt="You are a helpful assistant.")
        return result
    
    def update_conversation_title(self, title: str) -> bool:
        """Update the current conversation title."""
        if self.current_conversation_id is None:
            return False
        return self.history_repo.update_conversation_title(self.current_conversation_id, title)
    
    def export_current_conversation_json(self) -> dict | None:
        """Export current conversation as JSON."""
        if self.current_conversation_id is None:
            return None
        return self.history_repo.export_conversation_json(self.current_conversation_id)
    
    def export_current_conversation_markdown(self) -> str | None:
        """Export current conversation as Markdown."""
        if self.current_conversation_id is None:
            return None
        return self.history_repo.export_conversation_markdown(self.current_conversation_id)