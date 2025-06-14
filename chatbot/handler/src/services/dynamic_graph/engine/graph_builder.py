"""
Dynamic Graph Builder

Builds a LangGraph StateGraph from database nodes, edges, and handlers.
"""

import logging
from langgraph.graph import StateGraph, END, START
from sqlalchemy.orm import Session

from database.models import GraphNode
from repositories.graph import GraphRepository
from ..nodes.handler_registry import NodeHandlerRegistry
from .config_manager import ConfigManager
from .state_manager import DynamicState
from .graph_cache import GraphCache

logger = logging.getLogger(__name__)


class DynamicGraphBuilder:
    """
    Builds a LangGraph StateGraph from database configuration.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.graph_repo = GraphRepository(db_session)
        self.config_manager = ConfigManager(db_session)
        self.node_handlers = NodeHandlerRegistry(self.config_manager)
        self.cache = GraphCache()

    def build_graph_from_database(self) -> StateGraph:
        """
        Build a LangGraph StateGraph from database nodes and edges.
        Returns:
            StateGraph: Compiled LangGraph graph
        """
        nodes = self.graph_repo.get_all_nodes()
        edges = self.graph_repo.get_all_edges()

        # Check cache first
        nodes_hash = self.cache.get_nodes_hash(nodes)
        edges_hash = self.cache.get_edges_hash(edges)
        cache_key = self.cache.get_cache_key("default", nodes_hash, edges_hash)

        cached_graph = self.cache.get(cache_key)
        if cached_graph:
            logger.info(
                f"Using cached graph with {len(nodes)} nodes and {len(edges)} edges"
            )
            return cached_graph

        logger.info(
            f"Building new dynamic graph with {len(nodes)} nodes and {len(edges)} edges"
        )

        workflow = StateGraph(DynamicState)
        node_id_map = {node.node_id: node for node in nodes}

        # Add nodes
        for node in nodes:
            handler = self.node_handlers.get_handler(node.node_type)
            if not handler:
                logger.warning(
                    f"No handler for node type: {node.node_type}, skipping node {node.node_id}"
                )
                continue
            workflow.add_node(node.node_id, handler.create_handler(node))

        # Add edges
        for edge in edges:
            # For conditional edges, use add_conditional_edges
            if edge.condition_type == "conditional":
                # The handler for the from_node must return a key for the condition
                # The edge's condition_config["conditions"] maps keys to next node_ids
                conditions = edge.condition_config.get("conditions", {})
                default_node = edge.condition_config.get("default", "end")

                # Create condition function with proper closure
                def create_condition_func(default=default_node):
                    return lambda state: state.get("condition_result", default)

                workflow.add_conditional_edges(
                    edge.from_node_id, create_condition_func(), conditions
                )
            else:
                workflow.add_edge(edge.from_node_id, edge.to_node_id)

        # Add start and end if not present
        if "start" not in node_id_map:
            logger.warning("No 'start' node found in graph. Adding default start node.")
            workflow.add_node(START, lambda state: state)
        if "end" not in node_id_map:
            logger.warning("No 'end' node found in graph. Adding default end node.")
            workflow.add_node(END, lambda state: state)

        # Compile and cache the graph
        compiled_graph = workflow.compile()
        self.cache.put(cache_key, compiled_graph)

        return compiled_graph
