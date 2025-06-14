"""
Execution Tracker

Tracks graph executions and node executions in the database.
"""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from database.models import GraphExecution, NodeExecution
from repositories.graph import GraphExecutionRepository
from schemas.requests.graph import GraphExecutionCreate

logger = logging.getLogger(__name__)


class ExecutionTracker:
    """
    Tracks graph executions and node executions in the database.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.repo = GraphExecutionRepository(db_session)

    def start_execution(
        self, chat_id: Optional[str], session_id: str
    ) -> GraphExecution:
        """
        Start a new graph execution.
        """
        execution_data = GraphExecutionCreate(
            chat_id=chat_id, session_id=session_id, execution_metadata={}
        )
        execution = self.repo.create_execution(execution_data)
        logger.info(f"Started graph execution: {execution.id}")
        return execution

    def complete_execution(self, execution_id, status: str = "completed"):
        """
        Mark a graph execution as completed.
        """
        self.repo.update_execution_status(execution_id, status)
        logger.info(f"Completed graph execution: {execution_id}")

    def fail_execution(self, execution_id, error_message: str):
        """
        Mark a graph execution as failed.
        """
        self.repo.update_execution_status(
            execution_id, "failed", error_message=error_message
        )
        logger.warning(f"Failed graph execution: {execution_id} ({error_message})")

    def get_node_executions(self, execution_id) -> List[NodeExecution]:
        """
        Get all node executions for a graph execution.
        """
        return self.repo.get_node_executions_by_execution(execution_id)

    def record_node_execution(
        self, execution_id, node_id, status: str = "running", **kwargs
    ) -> NodeExecution:
        """
        Record a node execution.
        """
        node_execution = self.repo.create_node_execution(
            execution_id=execution_id,
            node_id=node_id,
            status=status,
            started_at=datetime.utcnow() if status == "running" else None,
            completed_at=(
                datetime.utcnow() if status in ["completed", "failed"] else None
            ),
            **kwargs,
        )
        logger.debug(f"Recorded node execution: {node_execution.id} for node {node_id}")
        return node_execution

    def update_node_execution(
        self, node_execution_id, status: str, **kwargs
    ) -> Optional[NodeExecution]:
        """
        Update a node execution.
        """
        update_data = {"status": status, **kwargs}
        if status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.utcnow()

        return self.repo.update_node_execution(node_execution_id, **update_data)
