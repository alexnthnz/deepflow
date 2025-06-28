from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class MCPServerMetadataRequest(BaseModel):
    """Request model for MCP server metadata."""

    name: Optional[str] = Field(
        None, description="Unique name for this MCP server configuration (auto-generated if not provided)"
    )
    transport: str = Field(
        ..., description="The type of MCP server connection (stdio or sse)"
    )
    command: Optional[str] = Field(
        None, description="The command to execute (for stdio type)"
    )
    args: Optional[List[str]] = Field(
        None, description="Command arguments (for stdio type)"
    )
    url: Optional[str] = Field(
        None, description="The URL of the SSE server (for sse type)"
    )
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    timeout_seconds: Optional[int] = Field(
        None, description="Optional custom timeout in seconds for the operation"
    ) 