import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


async def _get_tools_from_client_session(
    client_context_manager: Any, timeout_seconds: int = 10
) -> List:
    """
    Helper function to get tools from a client session.

    Args:
        client_context_manager: A context manager that returns (read, write) functions
        timeout_seconds: Timeout in seconds for the read operation

    Returns:
        List of available tools from the MCP server

    Raises:
        Exception: If there's an error during the process
    """
    try:
        async with client_context_manager as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=timeout_seconds)
            ) as session:
                # Initialize the connection
                await session.initialize()
                # List available tools
                listed_tools = await session.list_tools()
                
                # Validate that tools were returned
                if not hasattr(listed_tools, 'tools'):
                    logger.warning("MCP server response missing 'tools' attribute")
                    return []
                
                tools = listed_tools.tools
                logger.debug(f"Retrieved {len(tools)} tools from MCP server")
                return tools
                
    except Exception as e:
        logger.error(f"Error in MCP client session: {e}")
        raise


async def load_mcp_tools(
    server_type: str,
    command: Optional[str] = None,
    args: Optional[List[str]] = None,
    url: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout_seconds: int = 60,  # Longer default timeout for first-time executions
) -> List:
    """
    Load tools from an MCP server.

    Args:
        server_type: The type of MCP server connection (stdio or sse)
        command: The command to execute (for stdio type)
        args: Command arguments (for stdio type)
        url: The URL of the SSE server (for sse type)
        env: Environment variables
        timeout_seconds: Timeout in seconds (default: 60 for first-time executions)

    Returns:
        List of available tools from the MCP server

    Raises:
        HTTPException: If there's an error loading the tools
    """
    # Input validation
    if not server_type or server_type not in ["stdio", "sse"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid server_type: {server_type}. Must be 'stdio' or 'sse'"
        )
    
    if timeout_seconds <= 0:
        raise HTTPException(
            status_code=400, 
            detail="timeout_seconds must be positive"
        )

    try:
        if server_type == "stdio":
            if not command:
                raise HTTPException(
                    status_code=400, detail="Command is required for stdio type"
                )

            logger.debug(f"Setting up stdio MCP server: command='{command}', args={args}")
            server_params = StdioServerParameters(
                command=command,  # Executable
                args=args or [],  # Optional command line arguments (ensure it's a list)
                env=env or {},  # Optional environment variables (ensure it's a dict)
            )

            return await _get_tools_from_client_session(
                stdio_client(server_params), timeout_seconds
            )

        elif server_type == "sse":
            if not url:
                raise HTTPException(
                    status_code=400, detail="URL is required for sse type"
                )

            logger.debug(f"Setting up SSE MCP server: url='{url}'")
            return await _get_tools_from_client_session(
                sse_client(url=url), timeout_seconds
            )

        else:
            # This should not be reachable due to earlier validation, but keeping for safety
            raise HTTPException(
                status_code=400, detail=f"Unsupported server type: {server_type}"
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception(f"Error loading MCP tools from {server_type} server: {str(e)}")
        # Convert other exceptions to HTTP exceptions with appropriate error message
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504, 
                detail=f"Timeout connecting to MCP server: {error_msg}"
            )
        elif "connection" in error_msg.lower():
            raise HTTPException(
                status_code=503, 
                detail=f"Connection error to MCP server: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to load tools from MCP server: {error_msg}"
            ) 