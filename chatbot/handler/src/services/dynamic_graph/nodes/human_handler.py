"""
Human Node Handler

Handles human interaction nodes in the dynamic graph system.
These nodes pause execution and wait for human input.
"""

import logging
from typing import Dict, Any, Callable
from langgraph.types import Command, interrupt
from langchain_core.messages import HumanMessage

from database.models import GraphNode
from .base_handler import BaseNodeHandler
from ..engine.state_manager import DynamicState

logger = logging.getLogger(__name__)


class HumanNodeHandler(BaseNodeHandler):
    """
    Handler for human interaction nodes in the dynamic graph.

    Supports configurable prompts and timeout handling for
    human assistance requests.
    """

    def create_handler(self, node: GraphNode) -> Callable:
        """
        Create a LangGraph node handler function for human nodes.

        Args:
            node: GraphNode instance with human interaction configuration

        Returns:
            Callable: Function that can be used as a LangGraph node
        """

        def human_handler(state: DynamicState) -> Command:
            try:
                # Get node configuration
                node_config = self.get_node_config(node)

                # Log execution start
                self.log_node_execution(
                    node.node_id,
                    "running",
                    timeout_seconds=node_config.get("timeout_seconds", 3600),
                )

                # Prepare human assistance request
                query = self._prepare_human_query(state, node_config)

                # Request human assistance
                human_response = interrupt({"query": query})

                # Create human message from response
                human_message = HumanMessage(content=human_response["data"])

                # Log successful execution
                self.log_node_execution(
                    node.node_id,
                    "completed",
                    response_length=len(human_response["data"]),
                )

                return Command(update={"messages": [human_message]})

            except Exception as e:
                error_msg = f"Human node execution failed: {str(e)}"
                self.log_node_execution(node.node_id, "failed", error_message=error_msg)
                return self.create_error_command(error_msg)

        return human_handler

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate human node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            bool: True if configuration is valid
        """
        # Validate timeout
        if "timeout_seconds" in config:
            timeout = config["timeout_seconds"]
            if not isinstance(timeout, int) or timeout <= 0:
                logger.warning(f"Invalid timeout value: {timeout}")
                return False

        # Validate prompt template
        if "prompt_template" in config:
            prompt = config["prompt_template"]
            if not isinstance(prompt, str):
                logger.warning("prompt_template must be a string")
                return False

        return True

    def _prepare_human_query(
        self, state: DynamicState, node_config: Dict[str, Any]
    ) -> str:
        """
        Prepare the query for human assistance.

        Args:
            state: Current execution state
            node_config: Node configuration

        Returns:
            str: Formatted query for human assistance
        """
        prompt_template = node_config.get(
            "prompt_template", "Please provide assistance for: {query}"
        )

        # Extract context from state
        context = self._extract_context(state)

        # Format the prompt
        try:
            query = prompt_template.format(
                query=context,
                session_id=state.session_id or "unknown",
                execution_id=(
                    str(state.execution_id) if state.execution_id else "unknown"
                ),
            )
        except KeyError as e:
            logger.warning(f"Invalid placeholder in prompt template: {e}")
            query = f"Please provide assistance for: {context}"

        return query

    def _extract_context(self, state: DynamicState) -> str:
        """
        Extract relevant context from the current state.

        Args:
            state: Current execution state

        Returns:
            str: Context information
        """
        context_parts = []

        # Add last message content
        if state.messages:
            last_message = state.messages[-1]
            content = getattr(last_message, "content", "")
            if content:
                context_parts.append(f"Last message: {content}")

        # Add current node information
        if state.current_node_id:
            context_parts.append(f"Current node: {state.current_node_id}")

        # Add execution metadata
        if state.graph_metadata:
            metadata_str = ", ".join(
                [f"{k}: {v}" for k, v in state.graph_metadata.items()]
            )
            context_parts.append(f"Metadata: {metadata_str}")

        return (
            " | ".join(context_parts)
            if context_parts
            else "No specific context available"
        )
