"""
Database seeding script for dynamic graph configuration.
This script populates the database with default tools and graph nodes/edges.
Since the app only has one graph, we don't create a graph table - just nodes and edges.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.database import SessionLocal
from database.models import AvailableTool, GraphNode, GraphEdge, NodeTool

logger = logging.getLogger(__name__)


def seed_default_tools(db: Session) -> dict:
    """Seed the database with default available tools."""

    default_tools = [
        {
            "name": "google_search",
            "display_name": "Google Search",
            "description": "Fetches raw, detailed Google search results (URLs, titles, snippets) for broad web data analysis or research.",
            "tool_type": "search",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"],
            },
            "configuration": {},
        },
        {
            "name": "tavily_search",
            "display_name": "Tavily Search",
            "description": "Provides curated, concise web results optimized for AI, ideal for quick, relevant answers or content generation.",
            "tool_type": "search",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "topic": {
                        "type": "string",
                        "enum": ["general", "news", "finance"],
                        "default": "general",
                        "description": "The topic for the search",
                    },
                    "include_images": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to include image search results",
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["day", "week", "month", "year"],
                        "description": "Time range for search results",
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "default": "basic",
                        "description": "Depth of the search",
                    },
                },
                "required": ["query"],
            },
            "configuration": {
                "max_results": 5,
                "topic": "general",
                "include_images": False,
                "search_depth": "basic",
            },
        },
        {
            "name": "human_assistance",
            "display_name": "Human Assistance",
            "description": "Request assistance from a human operator.",
            "tool_type": "human",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or request for human assistance",
                    }
                },
                "required": ["query"],
            },
            "configuration": {"timeout_seconds": 300},
        },
    ]

    created_tools = {}

    for tool_data in default_tools:
        try:
            # Check if tool already exists
            existing_tool = (
                db.query(AvailableTool)
                .filter(AvailableTool.name == tool_data["name"])
                .first()
            )

            if existing_tool:
                logger.info(f"Tool '{tool_data['name']}' already exists, skipping")
                created_tools[tool_data["name"]] = existing_tool
                continue

            # Create new tool
            tool = AvailableTool(**tool_data)
            db.add(tool)
            db.commit()
            db.refresh(tool)

            created_tools[tool_data["name"]] = tool
            logger.info(f"Created tool: {tool_data['name']}")

        except IntegrityError as e:
            db.rollback()
            logger.warning(f"Tool '{tool_data['name']}' already exists: {e}")
            # Get the existing tool
            existing_tool = (
                db.query(AvailableTool)
                .filter(AvailableTool.name == tool_data["name"])
                .first()
            )
            if existing_tool:
                created_tools[tool_data["name"]] = existing_tool

    return created_tools


def seed_default_graph_components(db: Session, tools: dict):
    """Seed the database with default graph nodes and edges."""

    # Check if default nodes already exist
    existing_nodes = db.query(GraphNode).all()
    if existing_nodes:
        logger.info("Graph nodes already exist, skipping graph seeding")
        return True

    try:
        # Create nodes
        nodes_data = [
            {
                "node_id": "start",
                "node_type": "start",
                "name": "Start",
                "description": "Entry point",
                "position_x": 100,
                "position_y": 100,
                "configuration": {},
            },
            {
                "node_id": "llm",
                "node_type": "llm",
                "name": "Main LLM",
                "description": "Primary language model processing",
                "position_x": 300,
                "position_y": 100,
                "configuration": {
                    "model": "default",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "system_prompt": "You are a helpful assistant. Use tools when you need current information or to perform specific tasks.",
                },
            },
            {
                "node_id": "tools",
                "node_type": "tool",
                "name": "Tool Execution",
                "description": "Execute external tools",
                "position_x": 500,
                "position_y": 100,
                "configuration": {},
            },
            {
                "node_id": "end",
                "node_type": "end",
                "name": "End",
                "description": "Exit point",
                "position_x": 700,
                "position_y": 100,
                "configuration": {},
            },
        ]

        created_nodes = {}
        for node_data in nodes_data:
            node = GraphNode(**node_data)
            db.add(node)
            db.commit()
            db.refresh(node)
            created_nodes[node_data["node_id"]] = node
            logger.info(f"Created node: {node_data['node_id']}")

        # Create edges
        edges_data = [
            {
                "from_node_id": "start",
                "to_node_id": "llm",
                "condition_type": "always",
                "label": "Start to LLM",
            },
            {
                "from_node_id": "llm",
                "to_node_id": "tools",
                "condition_type": "conditional",
                "label": "LLM to Tools",
                "condition_config": {
                    "conditions": {"continue": "tools", "end": "end"},
                    "default": "end",
                },
            },
            {
                "from_node_id": "llm",
                "to_node_id": "end",
                "condition_type": "conditional",
                "label": "LLM to End",
            },
            {
                "from_node_id": "tools",
                "to_node_id": "llm",
                "condition_type": "always",
                "label": "Tools back to LLM",
            },
        ]

        for edge_data in edges_data:
            edge = GraphEdge(**edge_data)
            db.add(edge)
            db.commit()
            logger.info(
                f"Created edge: {edge_data['from_node_id']} -> {edge_data['to_node_id']}"
            )

        # Associate tools with nodes
        llm_node = created_nodes["llm"]
        tool_node = created_nodes["tools"]

        # Add tools to LLM node
        for tool_name, tool in tools.items():
            node_tool = NodeTool(
                node_id=llm_node.id, tool_id=tool.id, tool_config={}, is_enabled=True
            )
            db.add(node_tool)

            # Also add to tool node
            node_tool_2 = NodeTool(
                node_id=tool_node.id, tool_id=tool.id, tool_config={}, is_enabled=True
            )
            db.add(node_tool_2)

        db.commit()
        logger.info("Default graph components created successfully")
        return True

    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Default graph components creation failed: {e}")
        return False


def seed_database():
    """Main function to seed the database with default data."""
    logger.info("Starting database seeding...")

    db = SessionLocal()
    try:
        # Seed tools first
        tools = seed_default_tools(db)
        logger.info(f"Seeded {len(tools)} tools")

        # Seed default graph components
        success = seed_default_graph_components(db, tools)
        if success:
            logger.info("Seeded default graph components")

        logger.info("Database seeding completed successfully")
        return {"status": "success", "message": "Database seeded successfully"}

    except Exception as e:
        logger.error(f"Database seeding failed: {e}", exc_info=True)
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )

    result = seed_database()
    print(f"Seeding result: {result}")
