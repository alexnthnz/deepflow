import logging
from typing import Optional, Dict, Any, List, Tuple
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_postgres import PostgresChatMessageHistory
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command

from database import database
from database.models import Graph, GraphNode, GraphEdge, AvailableTool, NodeTool
from repositories.graph import GraphRepository, ToolRepository, GraphExecutionRepository
from .llm import llm
from .tools import TOOLS
from .state import State
from .utils import format_response_message, format_tool_message

logger = logging.getLogger(__name__)


class DynamicGraphExecutor:
    """
    Executes graphs dynamically based on database configuration.
    """
    
    def __init__(self, graph_id: uuid.UUID, session_id: Optional[str] = None):
        self.graph_id = graph_id
        self.session_id = session_id or str(uuid.uuid4())
        self.thread_id = self.session_id
        
        # Initialize repositories
        self.graph_repo = GraphRepository(database.get_session())
        self.tool_repo = ToolRepository(database.get_session())
        self.execution_repo = GraphExecutionRepository(database.get_session())
        
        # Load graph configuration
        self.graph_config = self._load_graph_config()
        if not self.graph_config:
            raise ValueError(f"Graph {graph_id} not found or not active")
        
        # Initialize conversation history
        self.conversation_history = PostgresChatMessageHistory(
            "chat_history",
            self.session_id,
            sync_connection=database.sync_connection,
        )
        
        # Build the dynamic graph
        self.compiled_graph = self._build_graph()
        
    def _load_graph_config(self) -> Optional[Graph]:
        """Load graph configuration from database."""
        graph = self.graph_repo.get_graph_with_details(self.graph_id)
        if not graph or not graph.is_active:
            return None
        return graph
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph from database configuration."""
        workflow = StateGraph(State)
        
        # Add nodes
        for node in self.graph_config.nodes:
            if node.node_type == "start":
                workflow.add_edge(START, node.node_id)
            elif node.node_type == "end":
                workflow.add_edge(node.node_id, END)
            else:
                workflow.add_node(node.node_id, self._create_node_function(node))
        
        # Add edges
        for edge in self.graph_config.edges:
            if edge.condition_type == "conditional":
                # Add conditional edge
                workflow.add_conditional_edges(
                    edge.from_node_id,
                    self._create_condition_function(edge),
                    edge.condition_config.get("conditions", {})
                )
            else:
                # Add regular edge
                workflow.add_edge(edge.from_node_id, edge.to_node_id)
        
        return workflow.compile()
    
    def _create_node_function(self, node: GraphNode):
        """Create a function for executing a specific node type."""
        
        def node_executor(state: State, config: RunnableConfig):
            logger.info(f"Executing node: {node.node_id} ({node.node_type})")
            
            try:
                if node.node_type == "llm":
                    return self._execute_llm_node(node, state, config)
                elif node.node_type == "tool":
                    return self._execute_tool_node(node, state, config)
                elif node.node_type == "condition":
                    return self._execute_condition_node(node, state, config)
                elif node.node_type == "human":
                    return self._execute_human_node(node, state, config)
                else:
                    logger.warning(f"Unknown node type: {node.node_type}")
                    return Command(update={"messages": []})
                    
            except Exception as e:
                logger.error(f"Error executing node {node.node_id}: {e}")
                error_message = AIMessage(
                    content=f"Error in {node.name}: {str(e)}"
                )
                return Command(update={"messages": [error_message]})
        
        return node_executor
    
    def _execute_llm_node(self, node: GraphNode, state: State, config: RunnableConfig):
        """Execute an LLM node."""
        node_config = node.configuration
        
        # Get model configuration
        model_name = node_config.get("model", "default")
        temperature = node_config.get("temperature", 0.7)
        max_tokens = node_config.get("max_tokens", 1000)
        system_prompt = node_config.get("system_prompt")
        
        # Configure the model
        model = llm
        if hasattr(model, 'temperature'):
            model.temperature = temperature
        if hasattr(model, 'max_tokens'):
            model.max_tokens = max_tokens
        
        # Add system prompt if specified
        messages = state["messages"]
        if system_prompt and not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
        
        # Get available tools for this node
        node_tools = self._get_node_tools(node)
        if node_tools:
            model = model.bind_tools(node_tools)
        
        # Execute the model
        response = model.invoke(messages, config)
        
        return Command(update={"messages": [response]})
    
    def _execute_tool_node(self, node: GraphNode, state: State, config: RunnableConfig):
        """Execute a tool node."""
        outputs = []
        tools_by_name = {tool.name: tool for tool in self._get_node_tools(node)}
        
        # Get the last message which should contain tool calls
        last_message = state["messages"][-1]
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            logger.warning(f"No tool calls found for tool node {node.node_id}")
            return Command(update={"messages": []})
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name not in tools_by_name:
                logger.error(f"Tool {tool_name} not available in node {node.node_id}")
                outputs.append(
                    ToolMessage(
                        content=f"Error: Tool {tool_name} not available",
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                continue
            
            try:
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
        
        return Command(update={"messages": outputs})
    
    def _execute_condition_node(self, node: GraphNode, state: State, config: RunnableConfig):
        """Execute a condition node."""
        # This is a placeholder - condition logic would be implemented based on node configuration
        node_config = node.configuration
        condition_type = node_config.get("condition_type", "simple")
        condition = node_config.get("condition", "")
        
        # For now, just pass through - actual condition evaluation would be implemented here
        logger.info(f"Condition node {node.node_id}: {condition}")
        
        return Command(update={"messages": []})
    
    def _execute_human_node(self, node: GraphNode, state: State, config: RunnableConfig):
        """Execute a human intervention node."""
        from langgraph.types import interrupt
        
        node_config = node.configuration
        prompt = node_config.get("prompt", "Human assistance required")
        timeout = node_config.get("timeout_seconds", 300)
        
        # Request human intervention
        human_response = interrupt({
            "query": prompt,
            "timeout": timeout,
            "node_id": node.node_id
        })
        
        # Convert human response to message
        response_message = HumanMessage(content=human_response.get("data", ""))
        
        return Command(update={"messages": [response_message]})
    
    def _get_node_tools(self, node: GraphNode) -> List:
        """Get available tools for a specific node."""
        node_tools = []
        
        for node_tool in node.tools:
            if not node_tool.is_enabled:
                continue
                
            tool = node_tool.tool
            if not tool.is_enabled:
                continue
            
            # Find the corresponding tool in TOOLS
            for available_tool in TOOLS:
                if available_tool.name == tool.name:
                    node_tools.append(available_tool)
                    break
        
        return node_tools
    
    def _create_condition_function(self, edge: GraphEdge):
        """Create a condition function for conditional edges."""
        
        def condition_evaluator(state: State):
            # Implement condition logic based on edge configuration
            condition_config = edge.condition_config
            condition_type = edge.condition_type
            
            # This is a placeholder - actual condition evaluation would be implemented here
            # For now, return the default path
            return condition_config.get("default", "continue")
        
        return condition_evaluator
    
    async def execute_message(
        self, 
        message: str, 
        chat_id: Optional[uuid.UUID] = None,
        attachments: Optional[List[dict]] = None
    ) -> Tuple[str, List[str], List[str], str]:
        """
        Execute a message through the dynamic graph.
        
        Args:
            message: The user's message
            chat_id: Optional chat ID for tracking
            attachments: Optional attachments
            
        Returns:
            Tuple of (response, message_ids, tool_call_ids, title)
        """
        
        # Create execution record
        execution = self.execution_repo.create_execution(
            self.graph_id,
            {"chat_id": chat_id, "session_id": self.session_id}
        )
        
        try:
            # Get conversation history
            history_messages = self.conversation_history.get_messages()
            last_10_messages = (
                history_messages[-10:] if len(history_messages) > 10 else history_messages
            )
            
            # Create system message based on graph configuration
            system_content = self.graph_config.description or "You are a helpful assistant."
            system_message = SystemMessage(content=system_content)
            
            # Prepare messages
            context_messages = [system_message] + last_10_messages
            human_message = HumanMessage(content=message.strip())
            
            # Execute the graph
            result = await self.compiled_graph.ainvoke(
                {
                    "messages": context_messages + [human_message],
                },
                {"configurable": {"thread_id": self.thread_id}}
            )
            
            # Filter new messages
            filtered_messages = [
                msg for msg in result["messages"] 
                if msg not in context_messages
            ]
            
            # Save to conversation history
            self.conversation_history.add_messages(filtered_messages)
            
            # Update execution status
            self.execution_repo.update_execution_status(execution.id, "completed")
            
            # Format response
            response_text = ""
            message_ids = []
            tool_call_ids = []
            
            for msg in filtered_messages:
                if isinstance(msg, AIMessage):
                    response_text += msg.content + "\n"
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_call_ids.extend([tc["id"] for tc in msg.tool_calls])
                elif isinstance(msg, ToolMessage):
                    response_text += f"Tool result: {msg.content}\n"
            
            # Generate title (simplified)
            title = f"Chat with {self.graph_config.name}"
            
            return response_text.strip(), message_ids, tool_call_ids, title
            
        except Exception as e:
            logger.error(f"Error executing graph {self.graph_id}: {e}")
            self.execution_repo.update_execution_status(
                execution.id, 
                "failed", 
                str(e)
            )
            raise


class DynamicGraphManager:
    """
    Manages dynamic graph instances and provides a factory for creating executors.
    """
    
    def __init__(self):
        self.graph_repo = GraphRepository(database.get_session())
    
    def get_default_graph_executor(self, session_id: Optional[str] = None) -> DynamicGraphExecutor:
        """Get an executor for the default graph."""
        default_graph = self.graph_repo.get_default_graph()
        if not default_graph:
            raise ValueError("No default graph configured")
        
        return DynamicGraphExecutor(default_graph.id, session_id)
    
    def get_graph_executor(self, graph_id: uuid.UUID, session_id: Optional[str] = None) -> DynamicGraphExecutor:
        """Get an executor for a specific graph."""
        return DynamicGraphExecutor(graph_id, session_id)
    
    def validate_graph(self, graph_id: uuid.UUID) -> Dict[str, Any]:
        """Validate a graph configuration."""
        graph = self.graph_repo.get_graph_with_details(graph_id)
        if not graph:
            return {"valid": False, "errors": ["Graph not found"]}
        
        errors = []
        warnings = []
        
        # Check for start and end nodes
        has_start = any(node.node_type == "start" for node in graph.nodes)
        has_end = any(node.node_type == "end" for node in graph.nodes)
        
        if not has_start:
            errors.append("Graph must have at least one start node")
        if not has_end:
            errors.append("Graph must have at least one end node")
        
        # Check for orphaned nodes
        node_ids = {node.node_id for node in graph.nodes}
        connected_nodes = set()
        
        for edge in graph.edges:
            connected_nodes.add(edge.from_node_id)
            connected_nodes.add(edge.to_node_id)
        
        orphaned_nodes = node_ids - connected_nodes
        if orphaned_nodes:
            warnings.append(f"Orphaned nodes found: {', '.join(orphaned_nodes)}")
        
        # Check for invalid edges
        for edge in graph.edges:
            if edge.from_node_id not in node_ids:
                errors.append(f"Edge references non-existent from_node: {edge.from_node_id}")
            if edge.to_node_id not in node_ids:
                errors.append(f"Edge references non-existent to_node: {edge.to_node_id}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        } 