"""
Dynamic State Manager

Manages the state for dynamic graph execution, extending the base state
with execution tracking and metadata.
"""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from langgraph.graph import MessagesState

from database.models import NodeExecution


@dataclass
class DynamicState(MessagesState):
    """
    Extended state for dynamic graph execution.

    Extends the base MessagesState with additional fields for tracking
    execution progress, metadata, and node execution history.
    """

    # Dynamic graph specific fields
    current_node_id: Optional[str] = None
    execution_id: Optional[uuid.UUID] = None
    session_id: Optional[str] = None
    chat_id: Optional[uuid.UUID] = None

    # Execution tracking
    node_executions: List[NodeExecution] = field(default_factory=list)
    graph_metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance tracking
    start_time: Optional[datetime] = None
    current_node_start_time: Optional[datetime] = None

    # Condition result for conditional edges
    condition_result: Optional[str] = None


class DynamicStateManager:
    """
    Manages the creation and manipulation of dynamic state.
    """

    @staticmethod
    def create_initial_state(
        input_message: str,
        execution_id: uuid.UUID,
        session_id: str,
        chat_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> DynamicState:
        """
        Create initial state for graph execution.

        Args:
            input_message: The user's input message
            execution_id: The graph execution ID
            session_id: The session ID
            chat_id: Optional chat ID
            **kwargs: Additional state metadata

        Returns:
            DynamicState: Initialized state
        """
        from langchain_core.messages import HumanMessage

        # Create initial messages
        messages = [HumanMessage(content=input_message)]

        # Create state
        state = DynamicState(
            messages=messages,
            execution_id=execution_id,
            session_id=session_id,
            chat_id=chat_id,
            start_time=datetime.utcnow(),
            graph_metadata=kwargs,
        )

        return state

    @staticmethod
    def update_current_node(state: DynamicState, node_id: str) -> DynamicState:
        """
        Update the current node in the state.

        Args:
            state: Current state
            node_id: New current node ID

        Returns:
            DynamicState: Updated state
        """
        state.current_node_id = node_id
        state.current_node_start_time = datetime.utcnow()
        return state

    @staticmethod
    def add_node_execution(
        state: DynamicState, node_execution: NodeExecution
    ) -> DynamicState:
        """
        Add a node execution to the state.

        Args:
            state: Current state
            node_execution: Node execution record

        Returns:
            DynamicState: Updated state
        """
        state.node_executions.append(node_execution)
        return state

    @staticmethod
    def update_metadata(state: DynamicState, key: str, value: Any) -> DynamicState:
        """
        Update graph metadata.

        Args:
            state: Current state
            key: Metadata key
            value: Metadata value

        Returns:
            DynamicState: Updated state
        """
        state.graph_metadata[key] = value
        return state
