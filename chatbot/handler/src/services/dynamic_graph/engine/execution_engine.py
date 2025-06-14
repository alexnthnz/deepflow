"""
Dynamic Graph Execution Engine

Orchestrates execution of the dynamic graph, manages state, and tracks node executions.
"""

import logging
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

    def __init__(self, db_session: Session):
        self.db = db_session
        self.builder = DynamicGraphBuilder(db_session)
        self.state_manager = DynamicStateManager()
        self.tracker = ExecutionTracker(db_session)

    async def execute_graph(
        self,
        chat_id: str,
        session_id: str,
        input_message: str,
        graph_name: str = "default",
    ) -> Dict[str, Any]:
        """
        Execute the dynamic graph workflow.
        Args:
            chat_id: Chat session ID
            session_id: Session ID
            input_message: User input message
            graph_name: Name of the graph (future extension)
        Returns:
            Dict[str, Any]: Execution result including messages and node executions
        """
        # 1. Start execution tracking
        execution = self.tracker.start_execution(chat_id, session_id)

        # 2. Build graph from database
        graph = self.builder.build_graph_from_database()

        # 3. Initialize state
        state = self.state_manager.create_initial_state(
            input_message, execution.id, session_id, chat_id=chat_id
        )

        # 4. Execute graph with node tracking
        try:
            result = await self._execute_with_node_tracking(
                graph, state, execution.id, session_id
            )
            # 5. Record successful execution
            self.tracker.complete_execution(execution.id, "completed")
            return {
                "execution_id": execution.id,
                "messages": result["messages"],
                "node_executions": self.tracker.get_node_executions(execution.id),
                "status": "completed",
            }
        except Exception as e:
            # 6. Record failed execution
            self.tracker.fail_execution(execution.id, str(e))
            logger.error(f"Dynamic graph execution failed: {e}", exc_info=True)
            return {
                "execution_id": execution.id,
                "messages": [],
                "node_executions": self.tracker.get_node_executions(execution.id),
                "status": "failed",
                "error": str(e),
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
        # For now, execute normally and let individual node handlers record their executions
        # In the future, this could be enhanced with more granular tracking
        result = await graph.ainvoke(state, {"configurable": {"thread_id": session_id}})
        return result
