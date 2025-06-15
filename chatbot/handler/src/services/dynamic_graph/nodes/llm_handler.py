"""
LLM Node Handler

Handles LLM nodes in the dynamic graph system with configurable
models, prompts, and parameters.
"""

import logging
from typing import Dict, Any, Callable, List
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage
from langchain_aws import ChatBedrockConverse

from database.models import GraphNode
from .base_handler import BaseNodeHandler
from ..engine.state_manager import DynamicState
from config.config import config

logger = logging.getLogger(__name__)


class LLMNodeHandler(BaseNodeHandler):
    """
    Handler for LLM nodes in the dynamic graph.

    Supports configurable models, system prompts, temperature,
    and other LLM parameters.
    """

    def create_handler(self, node: GraphNode) -> Callable:
        """
        Create a LangGraph node handler function for LLM nodes.

        Args:
            node: GraphNode instance with LLM configuration

        Returns:
            Callable: Function that can be used as a LangGraph node
        """

        def llm_handler(
            state: DynamicState, runnable_config: RunnableConfig
        ) -> Command:
            try:
                # Get node configuration
                node_config = self.get_node_config(node)

                # Log execution start
                self.log_node_execution(
                    node.node_id,
                    "running",
                    input_tokens=len(state.messages) if state.messages else 0,
                )

                # Create LLM with custom configuration
                llm = self._create_custom_llm(node_config)

                # Get tools for this node
                tools = self.config_manager.get_node_tools(node)
                if tools:
                    model = llm.bind_tools(tools)
                else:
                    model = llm

                # Prepare messages with system prompt
                messages = self._prepare_messages(state.messages, node_config)

                # Execute LLM
                response = model.invoke(messages, runnable_config)

                # Log successful execution
                self.log_node_execution(
                    node.node_id,
                    "completed",
                    output_tokens=(
                        len(response.content) if hasattr(response, "content") else 0
                    ),
                )

                return Command(update={"messages": [response]})

            except Exception as e:
                error_msg = f"LLM node execution failed: {str(e)}"
                self.log_node_execution(node.node_id, "failed", error_message=error_msg)
                return self.create_error_command(error_msg)

        return llm_handler

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate LLM node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            bool: True if configuration is valid
        """
        required_fields = ["system_prompt"]

        for field in required_fields:
            if field not in config:
                logger.warning(f"Missing required field in LLM config: {field}")
                return False

        # Validate temperature
        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                logger.warning(f"Invalid temperature value: {temp}")
                return False

        # Validate max_tokens
        if "max_tokens" in config:
            max_tokens = config["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                logger.warning(f"Invalid max_tokens value: {max_tokens}")
                return False

        return True

    def _create_custom_llm(self, node_config: Dict[str, Any]) -> ChatBedrockConverse:
        """
        Create a custom LLM instance based on node configuration.

        Args:
            node_config: Validated node configuration

        Returns:
            ChatBedrockConverse: Configured LLM instance
        """
        # Extract configuration
        model_id = node_config.get("model", config.AWS_BEDROCK_MODEL_ID)
        temperature = node_config.get("temperature", 0.7)
        max_tokens = node_config.get("max_tokens", 1000)
        top_p = node_config.get("top_p", 1.0)
        frequency_penalty = node_config.get("frequency_penalty", 0.0)
        presence_penalty = node_config.get("presence_penalty", 0.0)

        # Create LLM with custom parameters
        llm = ChatBedrockConverse(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            region_name=config.AWS_REGION,
        )

        logger.debug(f"Created LLM with config: model={model_id}, temp={temperature}")
        return llm

    def _prepare_messages(self, messages: List, node_config: Dict[str, Any]) -> List:
        """
        Prepare messages for LLM execution, including system prompt.

        Args:
            messages: Current conversation messages
            node_config: Node configuration with system prompt

        Returns:
            List: Messages with system prompt prepended
        """
        system_prompt = node_config.get("system_prompt", "You are a helpful assistant.")

        # Create system message
        system_message = SystemMessage(content=system_prompt)

        # Prepend system message to existing messages
        prepared_messages = [system_message] + messages

        logger.debug(f"Prepared {len(prepared_messages)} messages with system prompt")
        return prepared_messages
