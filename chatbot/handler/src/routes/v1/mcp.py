import logging
import json
from datetime import datetime

from fastapi import APIRouter, status

from schemas.requests.mcp import MCPServerMetadataRequest
from schemas.responses.mcp import MCPServerMetadataResponse
from schemas.responses.common import CommonResponse
from services.mcp.utils import load_mcp_tools
from config.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


def _generate_mcp_name(request: MCPServerMetadataRequest) -> str:
    """Generate a meaningful name for MCP server if not provided"""
    if request.name:
        return request.name
    
    if request.transport == "stdio" and request.command:
        if request.args:
            # Extract meaningful part from args (e.g., "@modelcontextprotocol/server-filesystem" -> "filesystem")
            for arg in request.args:
                if "/" in arg and not arg.startswith("-"):
                    package_name = arg.split("/")[-1]
                    # Remove common prefixes/suffixes
                    name = package_name.replace("mcp-server-", "").replace("server-", "").replace("mcp-", "")
                    return name
            # Fallback to first non-flag arg
            for arg in request.args:
                if not arg.startswith("-"):
                    return arg
        # Use command name
        return request.command
    elif request.transport == "sse" and request.url:
        # Extract meaningful part from URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(request.url)
            domain = parsed.netloc.replace("www.", "").split(".")[0]
            return domain if domain else "sse-server"
        except:
            return "sse-server"
    
    return "unknown-server"


def _save_mcp_config_to_redis(request: MCPServerMetadataRequest, tools_count: int):
    """Save successful MCP configuration to Redis cache using name as key"""
    try:
        # Generate or use provided name
        server_name = _generate_mcp_name(request)
        
        # Use simple name-based key to prevent duplication
        cache_key = f"mcp_config:{server_name}"
        
        # Prepare the config data to cache
        config_data = {
            "name": server_name,
            "transport": request.transport,
            "command": request.command,
            "args": request.args,
            "url": request.url,
            "env": request.env,
            "timeout_seconds": request.timeout_seconds or 60,
            "tools_count": tools_count,
            "discovered_at": datetime.utcnow().isoformat(),
            "status": "working"
        }
        
        # Save to Redis with TTL of 24 hours (86400 seconds)
        # This will overwrite any existing config with the same name
        redis_client.setex(
            cache_key,
            86400,  # 24 hours
            json.dumps(config_data)
        )
        
        logger.info(f"Successfully cached MCP config '{server_name}': {cache_key}")
        return cache_key
        
    except Exception as e:
        logger.warning(f"Failed to cache MCP config to Redis: {e}")
        return None


@router.post("/server/metadata", response_model=CommonResponse)
async def get_mcp_server_metadata(
    request: MCPServerMetadataRequest,
):
    """
    Get metadata and available tools from an MCP server and automatically save to database.
    
    Args:
        request: MCP server connection details
        server_manager: MCP server manager dependency
        
    Returns:
        CommonResponse containing MCP server metadata, tools, and database save status
    """
    try:
        # Discover tools and automatically save server + tools to database
        
        # Use tools from sync result to avoid redundant database query
        # sync_result now includes "tools" key with validated tools
        tools = await load_mcp_tools(
            server_type=request.transport,
            command=request.command,
            args=request.args,
            url=request.url,
            env=request.env,
            timeout_seconds=request.timeout_seconds or 60,
        )
        
        # Save successful MCP config to Redis cache
        cache_key = _save_mcp_config_to_redis(request, len(tools))
        server_name = _generate_mcp_name(request)
        
        response_data = MCPServerMetadataResponse(
            transport=request.transport,
            command=request.command,
            args=request.args,
            url=request.url,
            env=request.env,
            tools=tools,
        )
        
        # Include cache information in response meta
        response_meta = {
            "server_name": server_name,
            "tools_discovered": len(tools),
            "cached": cache_key is not None,
            "cache_key": cache_key
        }
        
        return CommonResponse(
            message=f"MCP server '{server_name}' metadata retrieved and saved successfully",
            status_code=status.HTTP_200_OK,
            data=response_data.model_dump(),
            error=None,
            meta=response_meta,
        )
        
    except Exception as e:
        logger.error(f"Error getting MCP server metadata: {e}", exc_info=True)
        return CommonResponse(
            message="Failed to retrieve MCP server metadata",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=None,
            error=str(e),
            meta=None,
        )


def _get_cached_mcp_configs():
    """Retrieve all cached MCP configurations from Redis"""
    try:
        # Get all MCP config keys (they now use name-based format)
        keys = redis_client.keys("mcp_config:*")
        configs = []
        
        for key in keys:
            try:
                config_json = redis_client.get(key)
                if config_json:
                    config_data = json.loads(config_json)
                    config_data["cache_key"] = key
                    # Extract server name from key for convenience
                    server_name = key.replace("mcp_config:", "")
                    config_data["server_name"] = server_name
                    configs.append(config_data)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse cached config {key}: {e}")
                continue
        
        logger.info(f"Retrieved {len(configs)} cached MCP configurations")
        return configs
        
    except Exception as e:
        logger.error(f"Failed to retrieve cached MCP configs from Redis: {e}")
        return []


@router.get("/cached-configs", response_model=CommonResponse)
async def get_cached_mcp_configs():
    """
    Get all cached MCP configurations from Redis.
    
    Returns:
        CommonResponse containing list of cached MCP configurations
    """
    try:
        cached_configs = _get_cached_mcp_configs()
        
        return CommonResponse(
            message=f"Retrieved {len(cached_configs)} cached MCP configurations",
            status_code=status.HTTP_200_OK,
            data=cached_configs,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Error retrieving cached MCP configs: {e}", exc_info=True)
        return CommonResponse(
            message="Failed to retrieve cached MCP configurations",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=None,
            error=str(e),
        )


@router.delete("/cached-configs/{server_name}", response_model=CommonResponse)
async def delete_cached_mcp_config(server_name: str):
    """
    Delete a cached MCP configuration from Redis.
    
    Args:
        server_name: The name/identifier of the MCP server to delete
        
    Returns:
        CommonResponse indicating success or failure
    """
    try:
        # Construct the cache key
        cache_key = f"mcp_config:{server_name}"
        
        # Check if the config exists
        config_exists = redis_client.exists(cache_key)
        
        if not config_exists:
            return CommonResponse(
                message=f"MCP server '{server_name}' not found in cache",
                status_code=status.HTTP_404_NOT_FOUND,
                data=None,
                error="Configuration not found",
            )
        
        # Delete the config from Redis
        deleted_count = redis_client.delete(cache_key)
        
        if deleted_count > 0:
            logger.info(f"Successfully deleted MCP config '{server_name}': {cache_key}")
            return CommonResponse(
                message=f"MCP server '{server_name}' deleted successfully",
                status_code=status.HTTP_200_OK,
                data={"deleted_server_name": server_name, "cache_key": cache_key},
                error=None,
            )
        else:
            return CommonResponse(
                message=f"Failed to delete MCP server '{server_name}'",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error="Delete operation failed",
            )
        
    except Exception as e:
        logger.error(f"Error deleting cached MCP config '{server_name}': {e}", exc_info=True)
        return CommonResponse(
            message="Failed to delete MCP configuration",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=None,
            error=str(e),
        )