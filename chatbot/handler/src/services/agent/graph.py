import logging
from typing import Optional, List, Tuple

from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_postgres import PostgresChatMessageHistory
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command

from database import database

from .llm import llm
from .tools import TOOLS
from .state import State
from .utils import format_response_message, format_tool_message

logger = logging.getLogger(__name__)


class Graph:
    def __init__(self, session_id=None):
        self.thread_id = session_id

        self.conversation_history = PostgresChatMessageHistory(
            "chat_history",
            session_id,
            sync_connection=database.sync_connection,
        )
        self.model = llm.bind_tools(TOOLS)
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

    def __call_model(self, state: State, config: RunnableConfig):
        response = self.model.invoke(state["messages"], config)
        return Command(
            update={
                "messages": [response]
            }
        )

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
                    # Ensure args is a dict with expected structure
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

        Args:
            question (str): The user's question or message.
            attachments (Optional[List[dict]]): Optional attachments related to the question.

        Returns:
            Tuple[str, List[str], List[str], str]: A tuple containing:
                - A structured string of all new messages.
                - List of message IDs.
                - List of tool call IDs.
                - The conversation title.
        """
        history_messages = self.conversation_history.get_messages()

        # Get the last 10 messages, or all if fewer than 10
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
            return f"Error: Failed to process message: {str(e)}", [], [], "Error Conversation"
