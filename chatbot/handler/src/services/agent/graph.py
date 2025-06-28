import logging
from typing import Optional, List, Tuple
import json

from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_postgres import PostgresChatMessageHistory
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command

from database import database
from config.redis_client import redis_client

from .llm import llm
from .tools import TOOLS
from .state import State
from .utils import format_response_message, format_tool_message

logger = logging.getLogger(__name__)


class Graph:
    def __init__(self, session_id=None):
        self.thread_id = session_id
        self._initialized = False  # Track initialization state
        self.mcp_configs = self._get_cached_mcp_configs()
        logger.info(f"Graph initialized with {len(self.mcp_configs)} MCP configurations")

        # Defer async initialization (client and tools) to async initialize method
        self.client = None
        self.model = None
        self.graph = None
        self.conversation_history = None

    async def initialize(self):
        """Asynchronous initializer for setting up MCP client, tools, and graph."""
        if self._initialized:
            logger.debug("Graph already initialized, skipping")
            return

        # Initialize MCP client and fetch tools
        self.client = MultiServerMCPClient(self.mcp_configs)
        try:
            mcp_tools = await self.client.get_tools()
            logger.info(f"Retrieved {len(mcp_tools)} tools from MCP client")
        except Exception as e:
            logger.error(f"Failed to retrieve tools from MCP client: {e}")
            raise

        # Initialize conversation history
        self.conversation_history = PostgresChatMessageHistory(
            "chat_history",
            self.thread_id,
            sync_connection=database.sync_connection,
        )

        # Bind tools to the model
        self.model = llm.bind_tools(TOOLS + mcp_tools)

        # Set up the workflow
        workflow = StateGraph(State)
        workflow.add_edge(START, "llm")
        workflow.add_node("llm", self.__call_model)
        workflow.add_node("tools", self.__call_tools)
        workflow.add_conditional_edges(
            "llm",
            self.__should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )
        workflow.add_edge("tools", "llm")
        self.graph = workflow.compile()

        self._initialized = True
        logger.info("Graph async initialization completed")

    @staticmethod
    def _get_cached_mcp_configs():
        """Retrieve all cached MCP configurations from Redis in dictionary format."""
        try:
            keys = redis_client.keys("mcp_config:*")
            configs = {}
            for key in keys:
                try:
                    config_json = redis_client.get(key)
                    if config_json:
                        config_data = json.loads(config_json)
                        server_name = config_data.get("name") or key.replace("mcp_config:", "")
                        clean_config = {
                            "transport": config_data.get("transport"),
                        }
                        if config_data.get("command"):
                            clean_config["command"] = config_data["command"]
                        if config_data.get("args"):
                            clean_config["args"] = config_data["args"]
                        if config_data.get("url"):
                            clean_config["url"] = config_data["url"]
                        if config_data.get("env"):
                            clean_config["env"] = config_data["env"]
                        if config_data.get("timeout_seconds") and config_data["timeout_seconds"] != 60:
                            clean_config["timeout_seconds"] = config_data["timeout_seconds"]
                        configs[server_name] = clean_config
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Failed to parse cached config {key}: {e}")
                    continue
            logger.info(f"Retrieved {len(configs)} cached MCP configurations for Graph: {list(configs.keys())}")
            return configs
        except Exception as e:
            logger.error(f"Failed to retrieve cached MCP configs from Redis: {e}")
            return {}

    def __call_model(self, state: State, config: RunnableConfig):
        if not self._initialized:
            raise RuntimeError("Graph not initialized. Call initialize() first.")
        response = self.model.invoke(state["messages"], config)
        return Command(update={"messages": [response]})

    @staticmethod
    def __call_tools(state: State):
        outputs = []
        tools_by_name = {tool.name: tool for tool in TOOLS}
        for tool_call in state["messages"][-1].tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            logger.debug(f"Tool call: {tool_name}, args: {tool_args}")
            try:
                if tool_name == "tavily_search":
                    if isinstance(tool_args, str):
                        tool_args = {"query": tool_args}
                    elif not isinstance(tool_args, dict):
                        logger.warning(
                            f"Invalid tool args for {tool_name}: {tool_args}, converting to dict"
                        )
                        tool_args = {"query": str(tool_args)}
                    tool_result = tools_by_name[tool_name].invoke(tool_args)
                else:
                    tool_result = tools_by_name[tool_name].invoke(tool_args)
                logger.info(f"Tool {tool_name} invoked successfully with result: {tool_result}")
                formatted_result = format_tool_message(tool_call, tool_result)
                outputs.append(
                    ToolMessage(
                        content=formatted_result,
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
            except Exception as e:
                logger.error(f"Error invoking tool {tool_name}: {e}")
                outputs.append(
                    ToolMessage(
                        content=f"Error: Failed to invoke tool {tool_name}: {str(e)}",
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
        return Command(
            update={
                "messages": outputs,
                "is_last_step": state["is_last_step"],
            }
        )

    @staticmethod
    def __should_continue(state: State):
        messages = state["messages"]
        if not messages[-1].tool_calls:
            return "end"
        return "continue"

    async def get_message(
            self, question: str, attachments: Optional[List[dict]] = None
    ) -> Tuple[str, List[str], List[str], str]:
        """
        Invoke the graph to process a question and return all new messages in a structured format.
        """
        if not self._initialized:
            await self.initialize()  # Ensure initialization before processing

        history_messages = self.conversation_history.get_messages()
        last_10_messages = (
            history_messages[-10:] if len(history_messages) > 10 else history_messages
        )

        if len(last_10_messages) > 0 and isinstance(last_10_messages[0], ToolMessage):
            for i in range(len(history_messages) - 1, -1, -1):
                if isinstance(history_messages[i], HumanMessage):
                    start_index = max(0, i)
                    end_index = min(len(history_messages), start_index + 10)
                    last_10_messages = history_messages[start_index:end_index]
                    break
            else:
                last_10_messages = (
                    history_messages[-10:]
                    if len(history_messages) > 10
                    else history_messages
                )

        system_message_content = """You are a helpful assistant designed to provide accurate and relevant answers. Follow these guidelines:
        1. Answer the user's question to the best of your ability in a clear, concise, and conversational tone.
        2. If you don't know the answer, respond with "I don't know" and suggest how the user can find the information.
        3. If the question is unclear, ask the user to clarify or provide more details.
        4. Use the provided conversation history (the last 10 messages) to give contextually relevant answers.
        5. You have access to tools to retrieve external information. Use them when the question requires up-to-date data, specific facts, or information beyond your knowledge.
        6. If more context is needed, ask the user for additional details.
        The user's question follows the history."""

        old_context_messages = [
            SystemMessage(content=system_message_content.strip()),
            *last_10_messages,
        ]

        last_message = last_10_messages[-1] if last_10_messages else None
        human_assistance_tool_call_id = None
        human_assistance_tool_args = None
        if (
                last_message
                and isinstance(last_message, AIMessage)
                and hasattr(last_message, "tool_calls")
                and last_message.tool_calls
        ):
            for tool_call in last_message.tool_calls:
                if tool_call["name"] == "human_assistance":
                    human_assistance_tool_call_id = tool_call["id"]
                    human_assistance_tool_args = tool_call["args"]
                    break

        if human_assistance_tool_call_id:
            query = human_assistance_tool_args.get("query")
            if not query or not isinstance(query, str):
                raise ValueError("Invalid or missing query for human_assistance")

            human_message = ToolMessage(
                content=question,
                name="human_assistance",
                tool_call_id=human_assistance_tool_call_id,
            )
        else:
            human_message = HumanMessage(content=question.strip())

        try:
            result = await self.graph.ainvoke(
                {
                    "messages": [*old_context_messages, human_message],
                },
                {"configurable": {"thread_id": self.thread_id}},
            )

            filtered_messages = [
                message
                for message in result["messages"]
                if message not in old_context_messages
            ]

            self.conversation_history.add_messages(filtered_messages)

            message, resources, images = format_response_message(filtered_messages)

            return message, resources, images, "Untitled Conversation"

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return (
                f"Error: Failed to process message: {str(e)}",
                [],
                [],
                "Error Conversation",
            )