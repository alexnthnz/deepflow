from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
import uuid

from database.database import get_db
from database.models import (
    Graph,
    GraphNode,
    GraphEdge,
    AvailableTool,
    NodeTool,
    GraphExecution,
    NodeExecution,
)
from schemas.requests.graph import (
    GraphCreate,
    GraphUpdate,
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

    # Graph CRUD operations
    def create_graph(self, graph_data: GraphCreate) -> Graph:
        db_graph = Graph(**graph_data.dict())
        self.db.add(db_graph)
        self.db.commit()
        self.db.refresh(db_graph)
        return db_graph

    def get_graph_by_id(self, graph_id: uuid.UUID) -> Optional[Graph]:
        return self.db.query(Graph).filter(Graph.id == graph_id).first()

    def get_graph_with_details(self, graph_id: uuid.UUID) -> Optional[Graph]:
        return (
            self.db.query(Graph)
            .options(
                joinedload(Graph.nodes)
                .joinedload(GraphNode.tools)
                .joinedload(NodeTool.tool),
                joinedload(Graph.edges),
            )
            .filter(Graph.id == graph_id)
            .first()
        )

    def get_graphs(
        self, limit: int = 50, offset: int = 0, is_active: Optional[bool] = None
    ) -> List[Graph]:
        query = self.db.query(Graph)
        if is_active is not None:
            query = query.filter(Graph.is_active == is_active)
        return query.order_by(desc(Graph.updated_at)).offset(offset).limit(limit).all()

    def update_graph(
        self, graph_id: uuid.UUID, graph_data: GraphUpdate
    ) -> Optional[Graph]:
        db_graph = self.get_graph_by_id(graph_id)
        if not db_graph:
            return None

        update_data = graph_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_graph, field, value)

        self.db.commit()
        self.db.refresh(db_graph)
        return db_graph

    def delete_graph(self, graph_id: uuid.UUID) -> bool:
        db_graph = self.get_graph_by_id(graph_id)
        if not db_graph:
            return False

        self.db.delete(db_graph)
        self.db.commit()
        return True

    def set_default_graph(self, graph_id: uuid.UUID) -> bool:
        # First, unset all other default graphs
        self.db.query(Graph).update({Graph.is_default: False})

        # Set the specified graph as default
        db_graph = self.get_graph_by_id(graph_id)
        if not db_graph:
            return False

        db_graph.is_default = True
        self.db.commit()
        return True

    def get_default_graph(self) -> Optional[Graph]:
        return self.db.query(Graph).filter(Graph.is_default == True).first()

    # Node CRUD operations
    def create_node(
        self, graph_id: uuid.UUID, node_data: GraphNodeCreate
    ) -> Optional[GraphNode]:
        # Check if graph exists
        if not self.get_graph_by_id(graph_id):
            return None

        db_node = GraphNode(
            graph_id=graph_id,
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
        return self.db.query(GraphNode).filter(GraphNode.id == node_id).first()

    def get_node_by_graph_and_node_id(
        self, graph_id: uuid.UUID, node_id: str
    ) -> Optional[GraphNode]:
        return (
            self.db.query(GraphNode)
            .filter(and_(GraphNode.graph_id == graph_id, GraphNode.node_id == node_id))
            .first()
        )

    def get_nodes_by_graph(self, graph_id: uuid.UUID) -> List[GraphNode]:
        return (
            self.db.query(GraphNode)
            .options(joinedload(GraphNode.tools).joinedload(NodeTool.tool))
            .filter(GraphNode.graph_id == graph_id)
            .all()
        )

    def update_node(
        self, node_id: uuid.UUID, node_data: GraphNodeUpdate
    ) -> Optional[GraphNode]:
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
        db_node = self.get_node_by_id(node_id)
        if not db_node:
            return False

        self.db.delete(db_node)
        self.db.commit()
        return True

    # Edge CRUD operations
    def create_edge(
        self, graph_id: uuid.UUID, edge_data: GraphEdgeCreate
    ) -> Optional[GraphEdge]:
        # Check if graph exists and nodes exist
        if not self.get_graph_by_id(graph_id):
            return None

        if not self.get_node_by_graph_and_node_id(graph_id, edge_data.from_node_id):
            return None

        if not self.get_node_by_graph_and_node_id(graph_id, edge_data.to_node_id):
            return None

        db_edge = GraphEdge(graph_id=graph_id, **edge_data.dict())

        self.db.add(db_edge)
        self.db.commit()
        self.db.refresh(db_edge)
        return db_edge

    def get_edge_by_id(self, edge_id: uuid.UUID) -> Optional[GraphEdge]:
        return self.db.query(GraphEdge).filter(GraphEdge.id == edge_id).first()

    def get_edges_by_graph(self, graph_id: uuid.UUID) -> List[GraphEdge]:
        return self.db.query(GraphEdge).filter(GraphEdge.graph_id == graph_id).all()

    def update_edge(
        self, edge_id: uuid.UUID, edge_data: GraphEdgeUpdate
    ) -> Optional[GraphEdge]:
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
        db_tool = AvailableTool(**tool_data.dict())
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

        update_data = tool_data.dict(exclude_unset=True)
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

    def create_execution(
        self, graph_id: uuid.UUID, execution_data: GraphExecutionCreate
    ) -> GraphExecution:
        db_execution = GraphExecution(graph_id=graph_id, **execution_data.dict())

        self.db.add(db_execution)
        self.db.commit()
        self.db.refresh(db_execution)
        return db_execution

    def get_execution_by_id(self, execution_id: uuid.UUID) -> Optional[GraphExecution]:
        return (
            self.db.query(GraphExecution)
            .options(
                joinedload(GraphExecution.node_executions),
                joinedload(GraphExecution.graph),
            )
            .filter(GraphExecution.id == execution_id)
            .first()
        )

    def get_executions_by_graph(
        self, graph_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[GraphExecution]:
        return (
            self.db.query(GraphExecution)
            .filter(GraphExecution.graph_id == graph_id)
            .order_by(desc(GraphExecution.started_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_execution_status(
        self, execution_id: uuid.UUID, status: str, error_message: Optional[str] = None
    ) -> Optional[GraphExecution]:
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
def get_graph_repository(db: Session = next(get_db())) -> GraphRepository:
    return GraphRepository(db)


def get_tool_repository(db: Session = next(get_db())) -> ToolRepository:
    return ToolRepository(db)


def get_graph_execution_repository(
    db: Session = next(get_db()),
) -> GraphExecutionRepository:
    return GraphExecutionRepository(db)
