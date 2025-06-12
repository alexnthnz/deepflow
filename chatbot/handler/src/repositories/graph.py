from typing import List, Optional, Dict, Any
import uuid

from fastapi import Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc

from database.database import get_db
from database.models import (
    GraphNode,
    GraphEdge,
    AvailableTool,
    NodeTool,
    GraphExecution,
    NodeExecution,
)
from schemas.requests.graph import (
    GraphNodeCreate,
    GraphNodeUpdate,
    GraphEdgeCreate,
    GraphEdgeUpdate,
    AvailableToolCreate,
    AvailableToolUpdate,
    NodeToolCreate,
    NodeToolUpdate,
    GraphExecutionCreate,
)


class GraphRepository:
    def __init__(self, db: Session):
        self.db = db

    # Node CRUD operations
    def get_all_nodes(self) -> List[GraphNode]:
        """Get all nodes in the graph."""
        return (
            self.db.query(GraphNode)
            .options(joinedload(GraphNode.tools).joinedload(NodeTool.tool))
            .all()
        )

    def create_node(self, node_data: GraphNodeCreate) -> GraphNode:
        """Create a new node in the graph."""
        db_node = GraphNode(
            node_id=node_data.node_id,
            node_type=node_data.node_type,
            name=node_data.name,
            description=node_data.description,
            position_x=node_data.position.x if node_data.position else 0,
            position_y=node_data.position.y if node_data.position else 0,
            configuration=node_data.configuration,
        )

        self.db.add(db_node)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def get_node_by_id(self, node_id: uuid.UUID) -> Optional[GraphNode]:
        """Get a node by its UUID."""
        return (
            self.db.query(GraphNode)
            .options(joinedload(GraphNode.tools).joinedload(NodeTool.tool))
            .filter(GraphNode.id == node_id)
            .first()
        )

    def get_node_by_node_id(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by its node_id string."""
        return (
            self.db.query(GraphNode)
            .options(joinedload(GraphNode.tools).joinedload(NodeTool.tool))
            .filter(GraphNode.node_id == node_id)
            .first()
        )

    def update_node(
        self, node_id: uuid.UUID, node_data: GraphNodeUpdate
    ) -> Optional[GraphNode]:
        """Update a node."""
        db_node = self.get_node_by_id(node_id)
        if not db_node:
            return None

        update_data = node_data.dict(exclude_unset=True)
        if "position" in update_data and update_data["position"]:
            update_data["position_x"] = update_data["position"]["x"]
            update_data["position_y"] = update_data["position"]["y"]
            del update_data["position"]

        for field, value in update_data.items():
            setattr(db_node, field, value)

        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def delete_node(self, node_id: uuid.UUID) -> bool:
        """Delete a node."""
        db_node = self.get_node_by_id(node_id)
        if not db_node:
            return False

        self.db.delete(db_node)
        self.db.commit()
        return True

    # Edge CRUD operations
    def get_all_edges(self) -> List[GraphEdge]:
        """Get all edges in the graph."""
        return self.db.query(GraphEdge).all()

    def create_edge(self, edge_data: GraphEdgeCreate) -> Optional[GraphEdge]:
        """Create a new edge in the graph."""
        # Check if nodes exist
        from_node = self.get_node_by_node_id(edge_data.from_node_id)
        to_node = self.get_node_by_node_id(edge_data.to_node_id)

        if not from_node or not to_node:
            return None

        db_edge = GraphEdge(**edge_data.dict())

        self.db.add(db_edge)
        self.db.commit()
        self.db.refresh(db_edge)
        return db_edge

    def get_edge_by_id(self, edge_id: uuid.UUID) -> Optional[GraphEdge]:
        """Get an edge by its UUID."""
        return self.db.query(GraphEdge).filter(GraphEdge.id == edge_id).first()

    def update_edge(
        self, edge_id: uuid.UUID, edge_data: GraphEdgeUpdate
    ) -> Optional[GraphEdge]:
        """Update an edge."""
        db_edge = self.get_edge_by_id(edge_id)
        if not db_edge:
            return None

        update_data = edge_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_edge, field, value)

        self.db.commit()
        self.db.refresh(db_edge)
        return db_edge

    def delete_edge(self, edge_id: uuid.UUID) -> bool:
        """Delete an edge."""
        db_edge = self.get_edge_by_id(edge_id)
        if not db_edge:
            return False

        self.db.delete(db_edge)
        self.db.commit()
        return True


class ToolRepository:
    def __init__(self, db: Session):
        self.db = db

    # Available Tool CRUD operations
    def create_tool(self, tool_data: AvailableToolCreate) -> AvailableTool:
        db_tool = AvailableTool(**tool_data.dict(by_alias=True))
        self.db.add(db_tool)
        self.db.commit()
        self.db.refresh(db_tool)
        return db_tool

    def get_tool_by_id(self, tool_id: uuid.UUID) -> Optional[AvailableTool]:
        return self.db.query(AvailableTool).filter(AvailableTool.id == tool_id).first()

    def get_tool_by_name(self, name: str) -> Optional[AvailableTool]:
        return self.db.query(AvailableTool).filter(AvailableTool.name == name).first()

    def get_tools(
        self, limit: int = 50, offset: int = 0, is_enabled: Optional[bool] = None
    ) -> List[AvailableTool]:
        query = self.db.query(AvailableTool)
        if is_enabled is not None:
            query = query.filter(AvailableTool.is_enabled == is_enabled)
        return query.offset(offset).limit(limit).all()

    def update_tool(
        self, tool_id: uuid.UUID, tool_data: AvailableToolUpdate
    ) -> Optional[AvailableTool]:
        db_tool = self.get_tool_by_id(tool_id)
        if not db_tool:
            return None

        update_data = tool_data.dict(exclude_unset=True, by_alias=True)
        for field, value in update_data.items():
            setattr(db_tool, field, value)

        self.db.commit()
        self.db.refresh(db_tool)
        return db_tool

    def delete_tool(self, tool_id: uuid.UUID) -> bool:
        db_tool = self.get_tool_by_id(tool_id)
        if not db_tool:
            return False

        self.db.delete(db_tool)
        self.db.commit()
        return True

    # Node Tool CRUD operations
    def add_tool_to_node(
        self, node_id: uuid.UUID, tool_data: NodeToolCreate
    ) -> Optional[NodeTool]:
        # Check if node and tool exist
        node_repo = GraphRepository(self.db)
        if not node_repo.get_node_by_id(node_id):
            return None

        if not self.get_tool_by_id(tool_data.tool_id):
            return None

        db_node_tool = NodeTool(node_id=node_id, **tool_data.dict())

        self.db.add(db_node_tool)
        self.db.commit()
        self.db.refresh(db_node_tool)
        return db_node_tool

    def get_node_tool_by_id(self, node_tool_id: uuid.UUID) -> Optional[NodeTool]:
        return (
            self.db.query(NodeTool)
            .options(joinedload(NodeTool.tool))
            .filter(NodeTool.id == node_tool_id)
            .first()
        )

    def get_tools_by_node(self, node_id: uuid.UUID) -> List[NodeTool]:
        return (
            self.db.query(NodeTool)
            .options(joinedload(NodeTool.tool))
            .filter(NodeTool.node_id == node_id)
            .all()
        )

    def update_node_tool(
        self, node_tool_id: uuid.UUID, tool_data: NodeToolUpdate
    ) -> Optional[NodeTool]:
        db_node_tool = self.get_node_tool_by_id(node_tool_id)
        if not db_node_tool:
            return None

        update_data = tool_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_node_tool, field, value)

        self.db.commit()
        self.db.refresh(db_node_tool)
        return db_node_tool

    def remove_tool_from_node(self, node_tool_id: uuid.UUID) -> bool:
        db_node_tool = self.get_node_tool_by_id(node_tool_id)
        if not db_node_tool:
            return False

        self.db.delete(db_node_tool)
        self.db.commit()
        return True


class GraphExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_execution(self, execution_data: GraphExecutionCreate) -> GraphExecution:
        """Create a new graph execution (without graph_id since there's only one graph)."""
        db_execution = GraphExecution(**execution_data.dict())

        self.db.add(db_execution)
        self.db.commit()
        self.db.refresh(db_execution)
        return db_execution

    def get_execution_by_id(self, execution_id: uuid.UUID) -> Optional[GraphExecution]:
        """Get an execution by its UUID."""
        return (
            self.db.query(GraphExecution)
            .options(joinedload(GraphExecution.node_executions))
            .filter(GraphExecution.id == execution_id)
            .first()
        )

    def get_all_executions(
        self, limit: int = 50, offset: int = 0
    ) -> List[GraphExecution]:
        """Get all graph executions."""
        return (
            self.db.query(GraphExecution)
            .order_by(desc(GraphExecution.started_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_executions_by_chat(
        self, chat_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[GraphExecution]:
        """Get executions for a specific chat."""
        return (
            self.db.query(GraphExecution)
            .filter(GraphExecution.chat_id == chat_id)
            .order_by(desc(GraphExecution.started_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_execution_status(
        self, execution_id: uuid.UUID, status: str, error_message: Optional[str] = None
    ) -> Optional[GraphExecution]:
        """Update execution status."""
        db_execution = (
            self.db.query(GraphExecution)
            .filter(GraphExecution.id == execution_id)
            .first()
        )
        if not db_execution:
            return None

        db_execution.status = status
        if error_message:
            db_execution.error_message = error_message
        if status in ["completed", "failed"]:
            db_execution.completed_at = func.now()

        self.db.commit()
        self.db.refresh(db_execution)
        return db_execution


# Dependency injection functions
def get_graph_repository(db: Session = Depends(get_db)) -> GraphRepository:
    """Provide GraphRepository with a request-scoped DB session."""
    return GraphRepository(db)


def get_tool_repository(db: Session = Depends(get_db)) -> ToolRepository:
    """Provide ToolRepository with a request-scoped DB session."""
    return ToolRepository(db)


def get_graph_execution_repository(
    db: Session = Depends(get_db),
) -> GraphExecutionRepository:
    """Provide GraphExecutionRepository with a request-scoped DB session."""
    return GraphExecutionRepository(db)
