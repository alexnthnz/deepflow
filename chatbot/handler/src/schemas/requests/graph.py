from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class NodePosition(BaseModel):
    x: int = Field(default=0)
    y: int = Field(default=0)


class GraphNodeCreate(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=100)
    node_type: Literal["llm", "tool", "condition", "human", "start", "end"]
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    position: Optional[NodePosition] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class GraphNodeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    position: Optional[NodePosition] = None
    configuration: Optional[Dict[str, Any]] = None


class GraphEdgeCreate(BaseModel):
    from_node_id: str = Field(..., min_length=1, max_length=100)
    to_node_id: str = Field(..., min_length=1, max_length=100)
    condition_type: Optional[Literal["always", "conditional", "tool_result"]] = None
    condition_config: Dict[str, Any] = Field(default_factory=dict)
    label: Optional[str] = Field(None, max_length=255)


class GraphEdgeUpdate(BaseModel):
    condition_type: Optional[Literal["always", "conditional", "tool_result"]] = None
    condition_config: Optional[Dict[str, Any]] = None
    label: Optional[str] = Field(None, max_length=255)


class AvailableToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tool_type: Literal["search", "api", "function", "human"]
    schema_: Dict[str, Any] = Field(
        ...,
        alias="schema",
        description="JSON schema for tool input/output",
    )
    configuration: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class AvailableToolUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    schema_: Optional[Dict[str, Any]] = Field(None, alias="schema")
    configuration: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None

    class Config:
        populate_by_name = True


class NodeToolCreate(BaseModel):
    tool_id: uuid.UUID
    tool_config: Dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = Field(default=True)


class NodeToolUpdate(BaseModel):
    tool_config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class GraphExecutionCreate(BaseModel):
    chat_id: Optional[uuid.UUID] = None
    session_id: Optional[str] = None
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeExecutionCreate(BaseModel):
    node_id: uuid.UUID
    status: str = Field(default="pending")
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    tokens_used: int = Field(default=0)
    cost_usd: int = Field(default=0)


class NodeExecutionUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[int] = None
