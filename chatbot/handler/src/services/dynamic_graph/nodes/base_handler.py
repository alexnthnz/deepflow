"""
Base Node Handler

Abstract base class for all node handlers in the dynamic graph system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
from langgraph.types import Command

from database.models import GraphNode
from ..engine.state_manager import DynamicState

logger = logging.getLogger(__name__)


class BaseNodeHandler(ABC):
    """
    Abstract base class for node handlers.

    All node handlers must implement this interface to be used
    in the dynamic graph system.
    """

    def __init__(self, config_manager, execution_tracker=None):
        self.config_manager = config_manager
        self.execution_tracker = execution_tracker

    @abstractmethod
    def create_handler(self, node: GraphNode) -> Callable:
        """
        Create a LangGraph node handler function.

        Args:
            node: GraphNode instance with configuration

        Returns:
            Callable: Function that can be used as a LangGraph node
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            bool: True if configuration is valid
        """
        pass

    def get_node_config(self, node: GraphNode) -> Dict[str, Any]:
        """
        Get validated configuration for a node.

        Args:
            node: GraphNode instance

        Returns:
            Dict[str, Any]: Validated configuration
        """
        return self.config_manager.get_node_config(node)

    def log_node_execution(
        self, node_id: str, status: str, error_message: Optional[str] = None, **kwargs
    ):
        """
        Log node execution for debugging and monitoring.
        Also record execution in database if tracker is available.

        Args:
            node_id: Node identifier
            status: Execution status
            error_message: Optional error message
            **kwargs: Additional execution data
        """
        log_data = {"node_id": node_id, "status": status, **kwargs}

        if error_message:
            log_data["error"] = error_message
            logger.error(f"Node execution failed: {log_data}")
        else:
            logger.info(f"Node execution: {log_data}")

        # Record in database if tracker is available and execution_id is provided
        if self.execution_tracker and "execution_id" in kwargs:
            try:
                self.execution_tracker.record_node_execution(
                    execution_id=kwargs["execution_id"],
                    node_id=node_id,
                    status=status,
                    error_message=error_message,
                    execution_metadata=kwargs,
                )
            except Exception as e:
                logger.error(f"Failed to record node execution in database: {e}")

    def create_command(self, **updates) -> Command:
        """
        Create a LangGraph Command with updates.

        Args:
            **updates: State updates to apply

        Returns:
            Command: LangGraph command
        """
        return Command(update=updates)

    def create_error_command(self, error_message: str) -> Command:
        """
        Create a Command that represents an error state.

        Args:
            error_message: Error message

        Returns:
            Command: Error command
        """
        return Command(update={"error_message": error_message, "status": "failed"})
