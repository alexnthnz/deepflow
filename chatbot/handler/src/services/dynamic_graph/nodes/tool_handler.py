"""
Tool Node Handler

Handles tool nodes in the dynamic graph system with configurable
tool execution and error handling.
"""

import logging
from typing import Dict, Any, Callable, List
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from database.models import GraphNode
from .base_handler import BaseNodeHandler
from ..engine.state_manager import DynamicState
from ..utils.tool_converter import ToolConverter

logger = logging.getLogger(__name__)


class ToolNodeHandler(BaseNodeHandler):
    """
    Handler for tool nodes in the dynamic graph.

    Supports configurable tool execution, timeout handling,
    and error recovery.
    """

    def create_handler(self, node: GraphNode) -> Callable:
        """
        Create a LangGraph node handler function for tool nodes.

        Args:
            node: GraphNode instance with tool configuration

        Returns:
            Callable: Function that can be used as a LangGraph node
        """

        def tool_handler(state: DynamicState) -> Command:
            try:
                # Get node configuration
                node_config = self.get_node_config(node)

                # Log execution start
                self.log_node_execution(
                    node.node_id,
                    "running",
                    input_tools=(
                        len(state.messages[-1].tool_calls)
                        if state.messages and hasattr(state.messages[-1], "tool_calls")
                        else 0
                    ),
                )

                # Get tools for this node
                available_tools = self.config_manager.get_node_tools(node)

                # Convert to LangChain tools
                langchain_tools = ToolConverter.convert_tools_list(available_tools)
                tools_by_name = {tool.name: tool for tool in langchain_tools}

                # Execute tools
                outputs = self._execute_tools(
                    state.messages[-1], tools_by_name, node_config
                )

                # Log successful execution
                self.log_node_execution(
                    node.node_id, "completed", output_tools=len(outputs)
                )

                return Command(update={"messages": outputs})

            except Exception as e:
                error_msg = f"Tool node execution failed: {str(e)}"
                self.log_node_execution(node.node_id, "failed", error_message=error_msg)
                return self.create_error_command(error_msg)

        return tool_handler

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate tool node configuration.

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

        # Validate retry attempts
        if "retry_attempts" in config:
            retries = config["retry_attempts"]
            if not isinstance(retries, int) or retries < 0:
                logger.warning(f"Invalid retry_attempts value: {retries}")
                return False

        return True

    def _execute_tools(
        self,
        last_message,
        tools_by_name: Dict[str, BaseTool],
        node_config: Dict[str, Any],
    ) -> List[ToolMessage]:
        """
        Execute tools based on the last message's tool calls.

        Args:
            last_message: Last message with tool calls
            tools_by_name: Dictionary of available tools
            node_config: Node configuration

        Returns:
            List[ToolMessage]: Tool execution results
        """
        outputs = []

        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            logger.warning("No tool calls found in last message")
            return outputs

        timeout_seconds = node_config.get("timeout_seconds", 300)
        retry_attempts = node_config.get("retry_attempts", 3)
        continue_on_error = node_config.get("continue_on_error", True)

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")

            try:
                # Get tool
                if tool_name not in tools_by_name:
                    error_msg = f"Tool not found: {tool_name}"
                    logger.error(error_msg)
                    if not continue_on_error:
                        raise ValueError(error_msg)

                    outputs.append(
                        ToolMessage(
                            content=f"Error: {error_msg}",
                            name=tool_name,
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue

                tool = tools_by_name[tool_name]

                # Execute tool with retry logic
                tool_result = self._execute_tool_with_retry(
                    tool, tool_args, retry_attempts, timeout_seconds
                )

                # Format result
                formatted_result = self._format_tool_result(tool_call, tool_result)

                outputs.append(
                    ToolMessage(
                        content=formatted_result,
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )

            except Exception as e:
                error_msg = f"Failed to execute tool {tool_name}: {str(e)}"
                logger.error(error_msg)

                if not continue_on_error:
                    raise

                outputs.append(
                    ToolMessage(
                        content=f"Error: {error_msg}",
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )

        return outputs

    def _execute_tool_with_retry(
        self,
        tool: BaseTool,
        tool_args: Dict[str, Any],
        max_retries: int,
        timeout_seconds: int,
    ) -> Any:
        """
        Execute a tool with retry logic and timeout.

        Args:
            tool: Tool to execute
            tool_args: Tool arguments
            max_retries: Maximum number of retry attempts
            timeout_seconds: Timeout in seconds

        Returns:
            Any: Tool execution result
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Execute tool with timeout
                if hasattr(tool, "ainvoke"):
                    # Async tool
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            tool.ainvoke(tool_args), timeout=timeout_seconds
                        )
                    )
                else:
                    # Sync tool
                    result = tool.invoke(tool_args)

                logger.debug(f"Tool executed successfully on attempt {attempt + 1}")
                return result

            except asyncio.TimeoutError:
                last_exception = TimeoutError(
                    f"Tool execution timed out after {timeout_seconds} seconds"
                )
                logger.warning(f"Tool execution timed out on attempt {attempt + 1}")

            except Exception as e:
                last_exception = e
                logger.warning(f"Tool execution failed on attempt {attempt + 1}: {e}")

                if attempt < max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = 2**attempt
                    logger.debug(f"Waiting {wait_time} seconds before retry")
                    asyncio.sleep(wait_time)

        # All retries failed
        raise last_exception or Exception("Tool execution failed")

    def _format_tool_result(self, tool_call: Dict[str, Any], result: Any) -> str:
        """
        Format tool execution result.

        Args:
            tool_call: Original tool call
            result: Tool execution result

        Returns:
            str: Formatted result
        """
        if isinstance(result, str):
            return result

        # Try to convert to string
        try:
            return str(result)
        except Exception:
            return f"Tool executed successfully. Result type: {type(result).__name__}"
