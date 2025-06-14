"""
Configuration Manager

Handles loading, parsing, and validating node configurations
from the database.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ValidationError

from database.models import GraphNode, GraphEdge, AvailableTool
from repositories.graph import GraphRepository, ToolRepository

logger = logging.getLogger(__name__)


class LLMNodeConfig(BaseModel):
    """Configuration schema for LLM nodes."""

    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: str = "You are a helpful assistant."
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class ToolNodeConfig(BaseModel):
    """Configuration schema for tool nodes."""

    timeout_seconds: int = 300
    retry_attempts: int = 3
    parallel_execution: bool = False
    continue_on_error: bool = True


class ConditionNodeConfig(BaseModel):
    """Configuration schema for condition nodes."""

    conditions: Dict[str, str]  # condition_name -> next_node_id
    default: str  # default next node
    evaluation_type: str = "message_content"  # message_content, tool_result, custom


class HumanNodeConfig(BaseModel):
    """Configuration schema for human interaction nodes."""

    timeout_seconds: int = 3600  # 1 hour default
    prompt_template: str = "Please provide assistance for: {query}"
    allow_attachments: bool = True


class StartEndNodeConfig(BaseModel):
    """Configuration schema for start/end nodes."""

    pass  # Start/end nodes typically don't need configuration


class ConfigManager:
    """
    Manages configuration loading and validation for dynamic graph nodes.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.graph_repo = GraphRepository(db_session)
        self.tool_repo = ToolRepository(db_session)

        # Configuration schemas by node type
        self.config_schemas = {
            "llm": LLMNodeConfig,
            "tool": ToolNodeConfig,
            "condition": ConditionNodeConfig,
            "human": HumanNodeConfig,
            "start": StartEndNodeConfig,
            "end": StartEndNodeConfig,
        }

    def get_node_config(self, node: GraphNode) -> Dict[str, Any]:
        """
        Get validated configuration for a node.

        Args:
            node: GraphNode instance

        Returns:
            Dict[str, Any]: Validated configuration
        """
        config = node.configuration or {}
        node_type = node.node_type

        # Get schema for node type
        schema_class = self.config_schemas.get(node_type)
        if not schema_class:
            logger.warning(f"No configuration schema for node type: {node_type}")
            return config

        try:
            # Validate and return configuration
            validated_config = schema_class(**config)
            return validated_config.model_dump()
        except ValidationError as e:
            logger.error(
                f"Configuration validation failed for node {node.node_id}: {e}"
            )
            # Return default configuration
            return schema_class().model_dump()

    def get_node_tools(self, node: GraphNode) -> List[AvailableTool]:
        """
        Get tools associated with a node.

        Args:
            node: GraphNode instance

        Returns:
            List[AvailableTool]: List of available tools
        """
        node_tools = self.tool_repo.get_tools_by_node(node.id)
        return [node_tool.tool for node_tool in node_tools if node_tool.is_enabled]

    def validate_graph_structure(
        self, nodes: List[GraphNode], edges: List[GraphEdge]
    ) -> tuple[bool, List[str]]:
        """
        Validate the overall graph structure.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges

        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # Check for required node types
        node_ids = {node.node_id for node in nodes}
        node_types = {node.node_type for node in nodes}

        # Must have start and end nodes
        if "start" not in node_types:
            errors.append("Graph must have a 'start' node")
        if "end" not in node_types:
            errors.append("Graph must have an 'end' node")

        # Check edge validity
        for edge in edges:
            if edge.from_node_id not in node_ids:
                errors.append(f"Edge references non-existent node: {edge.from_node_id}")
            if edge.to_node_id not in node_ids:
                errors.append(f"Edge references non-existent node: {edge.to_node_id}")

        # Check for cycles (basic check)
        if self._has_cycles(nodes, edges):
            errors.append("Graph contains cycles which are not supported")

        # Check connectivity
        if not self._is_connected(nodes, edges):
            errors.append("Graph is not fully connected")

        return len(errors) == 0, errors

    def _has_cycles(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> bool:
        """
        Check if graph has cycles using DFS.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges

        Returns:
            bool: True if cycles detected
        """
        # Build adjacency list
        graph = {}
        for edge in edges:
            if edge.from_node_id not in graph:
                graph[edge.from_node_id] = []
            graph[edge.from_node_id].append(edge.to_node_id)

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node in nodes:
            if node.node_id not in visited:
                if dfs(node.node_id):
                    return True

        return False

    def _is_connected(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> bool:
        """
        Check if graph is connected (all nodes reachable from start).

        Args:
            nodes: List of graph nodes
            edges: List of graph edges

        Returns:
            bool: True if connected
        """
        # Build adjacency list
        graph = {}
        for edge in edges:
            if edge.from_node_id not in graph:
                graph[edge.from_node_id] = []
            graph[edge.from_node_id].append(edge.to_node_id)

        # Find start node
        start_node = None
        for node in nodes:
            if node.node_type == "start":
                start_node = node
                break

        if not start_node:
            return False

        # BFS from start node
        visited = set()
        queue = [start_node.node_id]
        visited.add(start_node.node_id)

        while queue:
            current = queue.pop(0)
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Check if all nodes are reachable
        return len(visited) == len(nodes)
