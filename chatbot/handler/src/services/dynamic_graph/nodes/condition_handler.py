"""
Condition Node Handler

Handles condition nodes in the dynamic graph system for
conditional logic and branching.
"""

import logging
from typing import Dict, Any, Callable
from langgraph.types import Command

from database.models import GraphNode
from .base_handler import BaseNodeHandler
from ..engine.state_manager import DynamicState

logger = logging.getLogger(__name__)


class ConditionNodeHandler(BaseNodeHandler):
    """
    Handler for condition nodes in the dynamic graph.

    Supports different types of conditional logic based on
    message content, tool results, or custom conditions.
    """

    def create_handler(self, node: GraphNode) -> Callable:
        """
        Create a LangGraph node handler function for condition nodes.

        Args:
            node: GraphNode instance with condition configuration

        Returns:
            Callable: Function that can be used as a LangGraph node
        """

        def condition_handler(state: DynamicState) -> Command:
            try:
                # Get node configuration
                node_config = self.get_node_config(node)

                # Log execution start
                self.log_node_execution(
                    node.node_id,
                    "running",
                    evaluation_type=node_config.get(
                        "evaluation_type", "message_content"
                    ),
                )

                # Evaluate condition
                result = self._evaluate_condition(state, node_config)

                # Log successful execution
                self.log_node_execution(
                    node.node_id, "completed", condition_result=result
                )

                # Return result for conditional edge routing
                return Command(update={"condition_result": result})

            except Exception as e:
                error_msg = f"Condition node execution failed: {str(e)}"
                self.log_node_execution(node.node_id, "failed", error_message=error_msg)
                return self.create_error_command(error_msg)

        return condition_handler

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate condition node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            bool: True if configuration is valid
        """
        # Check for required fields
        if "conditions" not in config:
            logger.warning("Missing 'conditions' in condition node config")
            return False

        if "default" not in config:
            logger.warning("Missing 'default' in condition node config")
            return False

        # Validate conditions structure
        conditions = config.get("conditions", {})
        if not isinstance(conditions, dict):
            logger.warning("'conditions' must be a dictionary")
            return False

        # Validate evaluation type
        evaluation_type = config.get("evaluation_type", "message_content")
        valid_types = ["message_content", "tool_result", "custom"]
        if evaluation_type not in valid_types:
            logger.warning(f"Invalid evaluation_type: {evaluation_type}")
            return False

        return True

    def _evaluate_condition(
        self, state: DynamicState, node_config: Dict[str, Any]
    ) -> str:
        """
        Evaluate condition based on configuration and current state.

        Args:
            state: Current execution state
            node_config: Node configuration

        Returns:
            str: Condition result (should match a key in conditions dict)
        """
        evaluation_type = node_config.get("evaluation_type", "message_content")
        conditions = node_config.get("conditions", {})
        default = node_config.get("default", "end")

        try:
            if evaluation_type == "message_content":
                return self._evaluate_message_content(state, conditions, default)
            elif evaluation_type == "tool_result":
                return self._evaluate_tool_result(state, conditions, default)
            elif evaluation_type == "custom":
                return self._evaluate_custom_condition(state, node_config, default)
            else:
                logger.warning(f"Unknown evaluation type: {evaluation_type}")
                return default

        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return default

    def _evaluate_message_content(
        self, state: DynamicState, conditions: Dict[str, str], default: str
    ) -> str:
        """
        Evaluate condition based on message content.

        Args:
            state: Current execution state
            conditions: Condition mapping
            default: Default result

        Returns:
            str: Condition result
        """
        if not state.messages:
            return default

        last_message = state.messages[-1]
        content = getattr(last_message, "content", "")

        if not content:
            return default

        # Check for tool calls (continue to tools)
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return conditions.get("continue", default)

        # Check for specific content patterns
        content_lower = content.lower()

        for condition_key, next_node in conditions.items():
            # Simple keyword matching (can be enhanced)
            if condition_key.lower() in content_lower:
                return next_node

        return default

    def _evaluate_tool_result(
        self, state: DynamicState, conditions: Dict[str, str], default: str
    ) -> str:
        """
        Evaluate condition based on tool execution results.

        Args:
            state: Current execution state
            conditions: Condition mapping
            default: Default result

        Returns:
            str: Condition result
        """
        if not state.messages:
            return default

        # Look for tool messages
        for message in reversed(state.messages):
            if hasattr(message, "name") and message.name:
                # Check if this tool result matches any conditions
                tool_name = message.name
                for condition_key, next_node in conditions.items():
                    if condition_key.lower() in tool_name.lower():
                        return next_node

        return default

    def _evaluate_custom_condition(
        self, state: DynamicState, node_config: Dict[str, Any], default: str
    ) -> str:
        """
        Evaluate custom condition based on node configuration.

        Args:
            state: Current execution state
            node_config: Node configuration
            default: Default result

        Returns:
            str: Condition result
        """
        # This can be extended with custom evaluation logic
        # For now, return default
        logger.debug("Custom condition evaluation not implemented, using default")
        return default
