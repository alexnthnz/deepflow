import os
from typing import List, Literal, Optional

from langchain_tavily import TavilySearch
from langchain_core.tools import Tool, BaseTool, StructuredTool, tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from config.config import config

os.environ["SERPER_API_KEY"] = config.SERPER_API_KEY
os.environ["TAVILY_API_KEY"] = config.TAVILY_API_KEY

# Google search instance (unchanged)
search_1 = GoogleSerperAPIWrapper()


def create_tavily_search(
    topic: Literal["general", "news", "finance"] = "general",
    include_images: bool = False,
    time_range: Optional[Literal["day", "week", "month", "year"]] = None,
    search_depth: Literal["basic", "advanced"] = "basic",
    max_results: int = 5,
) -> TavilySearch:
    """Creates and returns a new TavilySearch instance with configured parameters.

    Args:
        topic (Literal["general", "news", "finance"]): The topic for the search, defaults to "general".
        include_images (bool): Whether to include image search results, defaults to False.
        time_range (Optional[Literal["day", "week", "month", "year"]]): Time range for search results, defaults to None (no restriction).
        search_depth (Literal["basic", "advanced"]): Depth of the search, defaults to "basic".
        max_results (int): Maximum number of results to return, defaults to 4.
    Returns:
        TavilySearch: A configured TavilySearch instance.

    Raises:
        ValueError: If an invalid topic, time_range, or search_depth is provided.
    """
    if topic not in ["general", "news", "finance"]:
        raise ValueError("Topic must be one of 'general', 'news', or 'finance'")
    if time_range is not None and time_range not in ["day", "week", "month", "year"]:
        raise ValueError("Time range must be one of 'day', 'week', 'month', or 'year'")
    if search_depth not in ["basic", "advanced"]:
        raise ValueError("Search depth must be one of 'basic' or 'advanced'")
    if not (1 <= max_results <= 10):
        raise ValueError("Maximum results must be between 1 and 10")
    return TavilySearch(
        max_results=4 if include_images else max_results,
        topic=topic,
        include_images=include_images,
        search_depth=search_depth,
    )


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]


# Define the input schema for tavily_search using Pydantic
class TavilySearchInput(BaseModel):
    query: str = Field(..., description="The search query")
    topic: Literal["general", "news", "finance"] = Field(
        default="general", description="The topic for the search"
    )
    include_images: bool = Field(
        default=False, description="Whether to include image search results"
    )
    time_range: Optional[Literal["day", "week", "month", "year"]] = Field(
        default=None, description="Time range for search results"
    )
    search_depth: Literal["basic", "advanced"] = Field(
        default="basic", description="Depth of the search"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of results to return (1-10), default is 5, images are limited to 4",
    )


# Define the tavily_search tool with a structured input schema
def tavily_search_func(
    query: str,
    topic: Literal["general", "news", "finance"] = "general",
    include_images: bool = False,
    time_range: Optional[str] = None,
    search_depth: Literal["basic", "advanced"] = "basic",
) -> str:
    """Run a Tavily search with the specified query, topic, image inclusion, time range, and search depth."""
    if not query:
        raise ValueError("Query cannot be empty")
    # Append time range to query if specified
    if time_range:
        query = f"{query} past {time_range}"
    return create_tavily_search(topic, include_images, time_range, search_depth).run(
        query
    )


tavily_search_tool = StructuredTool.from_function(
    func=tavily_search_func,
    name="tavily_search",
    description="Provides curated, concise web results optimized for AI, ideal for quick, relevant answers or content "
    "generation. Supports topics: general, news, finance. Optionally includes image search results, "
    "time range filtering (day, week, month, year), and search depth (basic, advanced). Limit of 10 results without "
    "images, 4 with images.",
    args_schema=TavilySearchInput,
)

static_tools: List[Tool | BaseTool] = [
    Tool(
        name="serper_search",
        func=search_1.results,
        description="Fetches raw, detailed Google search results (URLs, titles, snippets) for broad web data analysis "
        "or research.",
    ),
    tavily_search_tool,
    human_assistance,
]
