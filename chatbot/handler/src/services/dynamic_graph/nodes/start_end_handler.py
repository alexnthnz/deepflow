"""
Start/End Node Handler

Handles start and end nodes in the dynamic graph system.
These nodes are typically used for flow control and don't
perform any actual processing.
"""

import logging
from typing import Dict, Any, Callable
from langgraph.types import Command

from database.models import GraphNode
from .base_handler import BaseNodeHandler
from ..engine.state_manager import DynamicState

logger = logging.getLogger(__name__)


class StartEndNodeHandler(BaseNodeHandler):
    """
    Handler for start and end nodes in the dynamic graph.

    Start nodes initialize the execution flow, while end nodes
    terminate the execution.
    """

    def create_handler(self, node: GraphNode) -> Callable:
        """
        Create a LangGraph node handler function for start/end nodes.

        Args:
            node: GraphNode instance

        Returns:
            Callable: Function that can be used as a LangGraph node
        """

        def start_end_handler(state: DynamicState) -> Command:
            try:
                node_type = node.node_type
                
                logger.info(f"Start/End Handler executing for node {node.node_id} (type: {node_type})")
                logger.info(f"Current state messages: {len(state.get('messages', [])) if state.get('messages') else 0}")

                # Log execution
                self.log_node_execution(
                    node.node_id, "running", 
                    execution_id=state.get("execution_id"),
                    node_type=node_type
                )

                if node_type == "start":
                    # Start node - just pass through
                    self.log_node_execution(
                        node.node_id, "completed", 
                        execution_id=state.get("execution_id"),
                        message="Start node executed"
                    )
                    return Command(update={})  # No state changes

                elif node_type == "end":
                    # End node - mark as last step
                    self.log_node_execution(
                        node.node_id, "completed", 
                        execution_id=state.get("execution_id"),
                        message="End node executed"
                    )
                    return Command(update={"is_last_step": True})

                else:
                    error_msg = f"Unknown node type: {node_type}"
                    self.log_node_execution(
                        node.node_id, "failed", 
                        execution_id=state.get("execution_id"),
                        error_message=error_msg
                    )
                    return self.create_error_command(error_msg)

            except Exception as e:
                error_msg = f"Start/End node execution failed: {str(e)}"
                self.log_node_execution(
                    node.node_id, "failed", 
                    execution_id=state.get("execution_id"),
                    error_message=error_msg
                )
                return self.create_error_command(error_msg)

        return start_end_handler

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate start/end node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            bool: True if configuration is valid
        """
        # Start/end nodes typically don't need configuration
        # but we can validate if any is provided
        return True
