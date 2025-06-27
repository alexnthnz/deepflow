"""
Dynamic Graph Execution Engine

Orchestrates execution of the dynamic graph, manages state, and tracks node executions.
"""

import logging
import asyncio
from typing import Any, Dict
from sqlalchemy.orm import Session

from .graph_builder import DynamicGraphBuilder
from .state_manager import DynamicStateManager, DynamicState
from ..execution.tracker import ExecutionTracker

logger = logging.getLogger(__name__)


class DynamicGraphExecutionEngine:
    """
    Orchestrates execution of the dynamic graph, manages state, and tracks node executions.
    """

    def __init__(self, db_session: Session, max_retries: int = 3, timeout_seconds: int = 300):
        self.db = db_session
        self.tracker = ExecutionTracker(db_session)
        self.builder = DynamicGraphBuilder(db_session, self.tracker)
        self.state_manager = DynamicStateManager()
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    async def execute_graph(
        self,
        chat_id: str,
        session_id: str,
        input_message: str,
        graph_name: str = "default",
    ) -> Dict[str, Any]:
        """
        Execute the dynamic graph workflow with enhanced error handling and retries.
        
        Args:
            chat_id: Chat session ID
            session_id: Session ID
            input_message: User input message
            graph_name: Name of the graph (future extension)
        Returns:
            Dict[str, Any]: Execution result including messages and node executions
        """
        execution = None
        
        for attempt in range(self.max_retries):
            try:
                # 1. Start execution tracking
                if execution is None:
                    execution = self.tracker.start_execution(chat_id, session_id)
                
                # 2. Build graph from database (with caching)
                try:
                    graph = self.builder.build_graph_from_database()
                except Exception as build_error:
                    logger.error(f"Graph building failed on attempt {attempt + 1}: {build_error}")
                    if attempt == self.max_retries - 1:
                        raise build_error
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue

                # 3. Initialize state
                state = self.state_manager.create_initial_state(
                    input_message, execution.id, session_id, chat_id=chat_id
                )

                # 4. Execute graph with timeout and node tracking
                try:
                    result = await asyncio.wait_for(
                        self._execute_with_node_tracking(graph, state, execution.id, session_id),
                        timeout=self.timeout_seconds
                    )
                    
                    # 5. Save conversation history and get filtered messages (using static graph approach)
                    context_messages = state.get("_context_messages", [])
                    all_messages = result.get("messages", [])
                    
                    # Filter messages using the same logic as static graph
                    # This filters out context messages but keeps new user input and AI responses
                    filtered_messages = [
                        message
                        for message in all_messages
                        if message not in context_messages
                    ]
                    
                    # Save filtered messages to conversation history
                    self.state_manager.save_conversation_history(state, filtered_messages)
                    
                    # For API response: return only AI and tool responses (exclude user input)
                    filtered_messages_for_response = []
                    for message in filtered_messages:
                        msg_type = getattr(message, 'type', type(message).__name__)
                        # Include only AI and tool messages, exclude human and system messages
                        if msg_type not in ['human', 'system']:
                            filtered_messages_for_response.append(message)
                    
                    # 6. Record successful execution
                    self.tracker.complete_execution(execution.id, "completed")
                    
                    return {
                        "execution_id": execution.id,
                        "messages": filtered_messages_for_response,  # Return only new AI/tool responses
                        "node_executions": self.tracker.get_node_executions(execution.id),
                        "status": "completed",
                        "attempts": attempt + 1,
                    }
                    
                except asyncio.TimeoutError:
                    error_msg = f"Graph execution timed out after {self.timeout_seconds} seconds"
                    logger.error(error_msg)
                    if attempt == self.max_retries - 1:
                        self.tracker.fail_execution(execution.id, error_msg)
                        return {
                            "execution_id": execution.id,
                            "messages": [],
                            "node_executions": self.tracker.get_node_executions(execution.id),
                            "status": "failed",
                            "error": error_msg,
                            "attempts": attempt + 1,
                        }
                    await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                    continue
                    
            except Exception as e:
                error_msg = f"Dynamic graph execution failed on attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                if attempt == self.max_retries - 1:
                    # Final attempt failed
                    if execution:
                        self.tracker.fail_execution(execution.id, str(e))
                    return {
                        "execution_id": execution.id if execution else None,
                        "messages": [],
                        "node_executions": self.tracker.get_node_executions(execution.id) if execution else [],
                        "status": "failed",
                        "error": str(e),
                        "attempts": attempt + 1,
                    }
                
                # Wait before retry with exponential backoff
                await asyncio.sleep(1 * (attempt + 1))
        
        # Should not reach here, but safety fallback
        return {
            "execution_id": execution.id if execution else None,
            "messages": [],
            "node_executions": [],
            "status": "failed",
            "error": "Maximum retries exceeded",
            "attempts": self.max_retries,
        }

    async def _execute_with_node_tracking(
        self, graph, state: DynamicState, execution_id, session_id: str
    ) -> Dict[str, Any]:
        """
        Execute graph with individual node execution tracking.

        Args:
            graph: Compiled LangGraph
            state: Initial state
            execution_id: Execution ID for tracking
            session_id: Session ID

        Returns:
            Dict[str, Any]: Final execution result
        """
        try:
            # Execute the graph with proper configuration
            result = await graph.ainvoke(
                state, 
                config={
                    "configurable": {"thread_id": session_id},
                    "recursion_limit": 100,  # Prevent infinite loops
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Graph execution failed: {e}", exc_info=True)
            raise

    def validate_graph_before_execution(self) -> Dict[str, Any]:
        """
        Validate graph structure before execution.
        
        Returns:
            Dict[str, Any]: Validation result with errors/warnings
        """
        try:
            graph = self.builder.build_graph_from_database()
            return {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "graph_info": {
                    "nodes_count": len(graph.nodes),
                    "edges_count": len(graph.edges) if hasattr(graph, 'edges') else 0,
                }
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [str(e)],
                "warnings": [],
                "graph_info": None
            }
