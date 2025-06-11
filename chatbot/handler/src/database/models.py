import enum
import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    ForeignKey,
    Enum,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


# Enum for message sender types
class SenderType(enum.Enum):
    USER = "user"
    AGENT = "agent"


class Chat(Base):
    __tablename__ = "chats"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=True)  # Optional title for the chat
    is_pinned = Column(Boolean, default=False)  # For pinning important chats
    last_read_at = Column(DateTime, nullable=True)  # For read/unread status
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    messages = relationship("Message", back_populates="chat")
    tags = relationship("Tag", secondary="chat_tags", back_populates="chats")


class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(
        UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False, index=True
    )
    sender = Column(Enum(SenderType), nullable=False)  # Enum for user, agent, or core
    content = Column(String, nullable=True)  # Text content, nullable if only a file
    file_id = Column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=True, index=True
    )
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    file = relationship("File", foreign_keys=[file_id])


class File(Base):
    __tablename__ = "files"  # Renamed from "attachments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_url = Column(String, nullable=False)  # URL to the file in external storage
    file_type = Column(String, nullable=True)  # e.g., "image/jpeg", "application/pdf"
    file_size = Column(Integer, nullable=True)  # Size in bytes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Tag(Base):
    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # Tag name (e.g., "work", "personal")

    # Relationships
    chats = relationship("Chat", secondary="chat_tags", back_populates="tags")


class ChatTag(Base):
    __tablename__ = "chat_tags"
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True)


# Dynamic Graph Configuration Models
# Removed Graph table since app only has 1 graph at a time

class GraphNode(Base):
    __tablename__ = "graph_nodes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    node_id = Column(String(100), nullable=False, unique=True)  # unique globally now
    node_type = Column(
        String(50), nullable=False
    )  # 'llm', 'tool', 'condition', 'human', 'start', 'end'
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    configuration = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    tools = relationship(
        "NodeTool", back_populates="node", cascade="all, delete-orphan"
    )


class GraphEdge(Base):
    __tablename__ = "graph_edges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    from_node_id = Column(String(100), nullable=False)
    to_node_id = Column(String(100), nullable=False)
    condition_type = Column(
        String(50), nullable=True
    )  # 'always', 'conditional', 'tool_result'
    condition_config = Column(JSON, default={})
    label = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint to prevent duplicate edges
    __table_args__ = (
        Index("ix_edge_unique", "from_node_id", "to_node_id", unique=True),
    )


class AvailableTool(Base):
    __tablename__ = "available_tools"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    tool_type = Column(
        String(50), nullable=False
    )  # 'search', 'api', 'function', 'human'
    schema = Column(JSON, nullable=False)  # tool input/output schema
    configuration = Column(JSON, default={})  # default config
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    node_tools = relationship("NodeTool", back_populates="tool")


class NodeTool(Base):
    __tablename__ = "node_tools"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    node_id = Column(UUID(as_uuid=True), ForeignKey("graph_nodes.id"), nullable=False)
    tool_id = Column(
        UUID(as_uuid=True), ForeignKey("available_tools.id"), nullable=False
    )
    tool_config = Column(JSON, default={})  # node-specific tool config
    is_enabled = Column(Boolean, default=True)

    # Relationships
    node = relationship("GraphNode", back_populates="tools")
    tool = relationship("AvailableTool", back_populates="node_tools")

    # Unique constraint
    __table_args__ = (Index("ix_node_tool_unique", "node_id", "tool_id", unique=True),)


class GraphExecution(Base):
    __tablename__ = "graph_executions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(
        UUID(as_uuid=True), ForeignKey("chats.id"), nullable=True, index=True
    )
    session_id = Column(String(255), nullable=True)
    status = Column(
        String(50), default="running"
    )  # 'running', 'completed', 'failed', 'interrupted'
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    execution_metadata = Column(JSON, default={})

    # Relationships
    chat = relationship("Chat")
    node_executions = relationship(
        "NodeExecution", back_populates="execution", cascade="all, delete-orphan"
    )


class NodeExecution(Base):
    __tablename__ = "node_executions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("graph_executions.id"),
        nullable=False,
        index=True,
    )
    node_id = Column(String(100), nullable=False)
    status = Column(
        String(50), default="pending"
    )  # 'pending', 'running', 'completed', 'failed', 'skipped'
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(
        Integer, default=0
    )  # Store as cents to avoid decimal precision issues

    # Relationships
    execution = relationship("GraphExecution", back_populates="node_executions")
