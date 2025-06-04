from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class NodePositionInDB(BaseModel):
    x: int
    y: int


class GraphNodeInDB(BaseModel):
    id: uuid.UUID
    graph_id: uuid.UUID
    node_id: str
    node_type: str
    name: str
    description: Optional[str]
    position_x: int
    position_y: int
    configuration: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @property
    def position(self) -> NodePositionInDB:
        return NodePositionInDB(x=self.position_x, y=self.position_y)

    class Config:
        from_attributes = True


class GraphEdgeInDB(BaseModel):
    id: uuid.UUID
    graph_id: uuid.UUID
    from_node_id: str
    to_node_id: str
    condition_type: Optional[str]
    condition_config: Dict[str, Any]
    label: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableToolInDB(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    description: Optional[str]
    tool_type: str
    schema_: Dict[str, Any] = Field(alias="schema")
    configuration: Dict[str, Any]
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class NodeToolInDB(BaseModel):
    id: uuid.UUID
    node_id: uuid.UUID
    tool_id: uuid.UUID
    tool_config: Dict[str, Any]
    is_enabled: bool
    tool: Optional[AvailableToolInDB] = None

    class Config:
        from_attributes = True


class GraphInDB(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    version: str
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphDetailInDB(GraphInDB):
    nodes: List[GraphNodeInDB] = []
    edges: List[GraphEdgeInDB] = []

    class Config:
        from_attributes = True


class GraphNodeDetailInDB(GraphNodeInDB):
    tools: List[NodeToolInDB] = []

    class Config:
        from_attributes = True


class NodeExecutionInDB(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    node_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    tokens_used: int
    cost_usd: int

    class Config:
        from_attributes = True


class GraphExecutionInDB(BaseModel):
    id: uuid.UUID
    graph_id: uuid.UUID
    chat_id: Optional[uuid.UUID]
    session_id: Optional[str]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    execution_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class GraphExecutionDetailInDB(GraphExecutionInDB):
    node_executions: List[NodeExecutionInDB] = []
    graph: Optional[GraphInDB] = None

    class Config:
        from_attributes = True


class GraphStats(BaseModel):
    total_graphs: int
    active_graphs: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_time_ms: Optional[float]
    total_tokens_used: int
    total_cost_usd: float


class NodeTypeInfo(BaseModel):
    node_type: str
    display_name: str
    description: str
    default_configuration: Dict[str, Any]
    required_fields: List[str]
    optional_fields: List[str]


class GraphValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
