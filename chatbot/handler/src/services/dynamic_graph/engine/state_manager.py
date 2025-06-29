"""
Dynamic State Manager

Manages the state for dynamic graph execution, extending the base state
with execution tracking and metadata.
"""

import uuid
from typing import Dict, Any, Optional, List

from dataclasses import dataclass
from langgraph.graph import MessagesState
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage

from database import database


@dataclass
class DynamicState(MessagesState):
    """
    State for dynamic graph execution - inherits from MessagesState.
    """

    # Additional fields for dynamic graph tracking
    execution_id: Optional[str] = None
    session_id: Optional[str] = None
    chat_id: Optional[str] = None
    condition_result: Optional[str] = None


class DynamicStateManager:
    """
    Manages the creation and manipulation of dynamic state with conversation history.
    """

    @staticmethod
    def create_initial_state(
        input_message: str,
        execution_id: uuid.UUID,
        session_id: str,
        chat_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create initial state for graph execution with conversation history.

        Args:
            input_message: The user's input message
            execution_id: The graph execution ID
            session_id: The session ID
            chat_id: Optional chat ID
            **kwargs: Additional state metadata

        Returns:
            Dict[str, Any]: Initialized state with conversation history
        """
        # Initialize conversation history (same as static graph)
        conversation_history = PostgresChatMessageHistory(
            "chat_history",
            session_id,
            sync_connection=database.sync_connection,
        )

        # Get existing conversation history
        history_messages = conversation_history.get_messages()

        # Get the last 10 messages, or all if fewer than 10 (same logic as static graph)
        last_10_messages = (
            history_messages[-10:] if len(history_messages) > 10 else history_messages
        )

        # Create system message for context (similar to static graph)
        system_message_content = """You are a helpful assistant designed to provide accurate and relevant answers. Follow these guidelines:
        1. Answer the user's question to the best of your ability in a clear, concise, and conversational tone.
        2. If you don't know the answer, respond with "I don't know" and suggest how the user can find the information.
        3. If the question is unclear, ask the user to clarify or provide more details.
        4. Use the provided conversation history to give contextually relevant answers.
        5. If more context is needed, ask the user for additional details.
        The user's question follows the history."""

        # Build context messages with history
        context_messages = [
            SystemMessage(content=system_message_content.strip()),
            *last_10_messages,
        ]

        # Add the new user message
        new_user_message = HumanMessage(content=input_message.strip())

        # Combine context and new message
        all_messages = context_messages + [new_user_message]

        # Store only the context messages for filtering (NOT the new user message)
        # This way the new user message and AI response will be processed and returned

        # Create state as dictionary (LangGraph expects dict-like access)
        state = {
            "messages": all_messages,
            "execution_id": str(execution_id),
            "session_id": session_id,
            "chat_id": str(chat_id) if chat_id else None,
            "condition_result": None,
            "_conversation_history": conversation_history,  # Store for later use
            "_context_messages": context_messages,  # Store only context, NOT the new user message
            "_original_message_count": len(
                all_messages
            ),  # Track original count for filtering
        }

        return state

    @staticmethod
    def save_conversation_history(
        state: Dict[str, Any], filtered_messages: List[Any]
    ) -> None:
        """
        Save new messages to conversation history.

        Args:
            state: The execution state containing conversation history
            filtered_messages: Already filtered new messages to save
        """
        conversation_history = state.get("_conversation_history")

        if conversation_history and filtered_messages:
            # Save the already filtered messages to conversation history
            conversation_history.add_messages(filtered_messages)
