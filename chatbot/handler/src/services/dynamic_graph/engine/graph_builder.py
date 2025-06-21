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
            try:
                # For conditional edges, use add_conditional_edges
                if edge.condition_type == "conditional":
                    # The handler for the from_node must return a key for the condition
                    # The edge's condition_config["conditions"] maps keys to next node_ids
                    conditions = edge.condition_config.get("conditions", {})
                    default_node = edge.condition_config.get("default", END)

                    # Create condition function with proper closure - fix the closure issue
                    def create_condition_func(conditions_map, default_target):
                        def condition_router(state):
                            condition_key = state.get("condition_result", "default")
                            return conditions_map.get(condition_key, default_target)
                        return condition_router

                    workflow.add_conditional_edges(
                        edge.from_node_id, 
                        create_condition_func(conditions, default_node),
                        list(conditions.values()) + [default_node]  # All possible destinations
                    )
                elif edge.condition_type == "tool_result":
                    # Handle tool-based conditional routing
                    conditions = edge.condition_config.get("conditions", {})
                    default_node = edge.condition_config.get("default", END)
                    
                    def create_tool_condition_func(conditions_map, default_target):
                        def tool_condition_router(state):
                            # Check tool results or outputs for routing decision
                            tool_result = state.get("tool_result", "")
                            last_message = state.get("messages", [])
                            
                            if last_message and hasattr(last_message[-1], 'content'):
                                content = last_message[-1].content.lower()
                                for condition_key, target_node in conditions_map.items():
                                    if condition_key.lower() in content:
                                        return target_node
                            
                            return default_target
                        return tool_condition_router
                    
                    workflow.add_conditional_edges(
                        edge.from_node_id,
                        create_tool_condition_func(conditions, default_node),
                        list(conditions.values()) + [default_node]
                    )
                else:
                    # Simple direct edge
                    workflow.add_edge(edge.from_node_id, edge.to_node_id)
                    
            except Exception as e:
                logger.error(f"Failed to add edge from {edge.from_node_id} to {edge.to_node_id}: {e}")
                # Continue with other edges even if one fails

        # Set entry point and handle start/end nodes
        start_nodes = [node for node in nodes if node.node_type == "start"]
        end_nodes = [node for node in nodes if node.node_type == "end"]
        
        if start_nodes:
            # If we have start nodes, set the first one as entry point
            workflow.set_entry_point(start_nodes[0].node_id)
        elif nodes:
            # If no start node, use the first node as entry point
            workflow.set_entry_point(nodes[0].node_id)
            logger.warning(f"No start node found. Using {nodes[0].node_id} as entry point.")
        else:
            logger.error("No nodes found in graph. Cannot build workflow.")
            raise ValueError("Cannot build workflow without nodes")
        
        # Ensure we have proper end connections
        if not end_nodes:
            logger.warning("No end nodes found. Workflow may not terminate properly.")

        # Compile and cache the graph
        compiled_graph = workflow.compile()
        self.cache.put(cache_key, compiled_graph)

        return compiled_graph
