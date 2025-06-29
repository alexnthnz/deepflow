import json
import logging
from typing import List, Tuple

from langchain_core.messages import BaseMessage, ToolMessage, AIMessage

logger = logging.getLogger(__name__)


def format_response_message(
        filtered_messages: List[BaseMessage], include_tool_message: bool = False
) -> Tuple[str, List[str], List[str]]:
    """
    Formats a list of messages into a single string for display or logging.

    Args:
        filtered_messages (List[BaseMessage]): The list of messages to format.
        include_tool_message (bool): Whether to include tool messages in the response string.
                                    If False, tool messages are processed for resources but not included
                                    in the response. Defaults to True.

    Returns:
        tuple: A tuple containing:
            - str: The formatted string representation of the messages.
            - List[str]: A list of URLs extracted from search results.
    """
    response_parts = []
    search_resources = []
    images = []
    for message in filtered_messages:
        if isinstance(message, AIMessage):
            if len(message.tool_calls) > 0:
                for ai_message in message.content:
                    if isinstance(ai_message, dict):
                        ai_message_type = ai_message.get("type")
                        ai_message_name = ai_message.get("name")
                        if ai_message_type == "text":
                            text = ai_message.get("text")
                            response_parts.append(f"{text}\n")
                        elif (
                                ai_message_type == "tool_use"
                                and ai_message_name == "human_assistance"
                        ):
                            ai_message_input = ai_message.get("input")
                            query = ai_message_input.get("query")
                            response_parts.append(query)
            else:
                response_parts.append(f"{message.content}\n")
        elif isinstance(message, ToolMessage):
            content = json.loads(message.content)
            match message.name:
                case "tavily_search":
                    tool_images = content.get("images")
                    for result in content.get("results", []):
                        if isinstance(result, dict):
                            url = result.get("url")
                            if url:
                                search_resources.append(url)
                    images.extend(tool_images)

            logger.info(f"Processing ToolMessage: {message.name} with content: {message.content}")
            logger.info(dir(message))

    # Combine all parts into a single response, separated by newlines
    final_response = "\n".join(response_parts)
    return final_response, search_resources, images
