import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from repositories.graph import (
    GraphRepository, ToolRepository, GraphExecutionRepository,
    get_graph_repository, get_tool_repository, get_graph_execution_repository
)
from schemas.requests.graph import (
    GraphCreate, GraphUpdate, GraphNodeCreate, GraphNodeUpdate,
    GraphEdgeCreate, GraphEdgeUpdate, AvailableToolCreate, AvailableToolUpdate,
    NodeToolCreate, NodeToolUpdate, GraphBulkCreate, GraphExecutionCreate
)
from schemas.responses.graph import (
    GraphInDB, GraphDetailInDB, GraphNodeInDB, GraphNodeDetailInDB,
    GraphEdgeInDB, AvailableToolInDB, NodeToolInDB, GraphExecutionInDB,
    GraphExecutionDetailInDB, GraphStats, NodeTypeInfo, GraphValidationResult
)
from schemas.responses.common import CommonResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# Graph Management Routes
@router.post("/", response_model=CommonResponse, status_code=status.HTTP_201_CREATED)
async def create_graph(
    graph_data: GraphCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Create a new graph."""
    try:
        db_graph = graph_repo.create_graph(graph_data)
        return CommonResponse(
            message="Graph created successfully",
            status_code=status.HTTP_201_CREATED,
            data=GraphInDB.from_orm(db_graph).dict(),
            error=None
        )
    except Exception as e:
        logger.error(f"Error creating graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create graph"
        )


@router.get("/", response_model=CommonResponse)
async def list_graphs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_active: Optional[bool] = Query(None),
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """List all graphs with pagination."""
    try:
        graphs = graph_repo.get_graphs(limit=limit, offset=offset, is_active=is_active)
        
        return CommonResponse(
            message="Graphs retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[GraphInDB.from_orm(graph).dict() for graph in graphs],
            error=None,
            meta={
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": len(graphs)
                }
            }
        )
    except Exception as e:
        logger.error(f"Error listing graphs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve graphs"
        )


@router.get("/{graph_id}", response_model=CommonResponse)
async def get_graph(
    graph_id: uuid.UUID,
    include_details: bool = Query(False),
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Get a specific graph by ID."""
    try:
        if include_details:
            db_graph = graph_repo.get_graph_with_details(graph_id)
            if not db_graph:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Graph not found"
                )
            return CommonResponse(
                message="Graph details retrieved successfully",
                status_code=status.HTTP_200_OK,
                data=GraphDetailInDB.from_orm(db_graph).dict(),
                error=None
            )
        else:
            db_graph = graph_repo.get_graph_by_id(graph_id)
            if not db_graph:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Graph not found"
                )
            return CommonResponse(
                message="Graph retrieved successfully",
                status_code=status.HTTP_200_OK,
                data=GraphInDB.from_orm(db_graph).dict(),
                error=None
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve graph"
        )


@router.put("/{graph_id}", response_model=CommonResponse)
async def update_graph(
    graph_id: uuid.UUID,
    graph_data: GraphUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Update a graph."""
    try:
        db_graph = graph_repo.update_graph(graph_id, graph_data)
        if not db_graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found"
            )
        
        return CommonResponse(
            message="Graph updated successfully",
            status_code=status.HTTP_200_OK,
            data=GraphInDB.from_orm(db_graph).dict(),
            error=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update graph"
        )


@router.delete("/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_graph(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Delete a graph."""
    try:
        deleted = graph_repo.delete_graph(graph_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete graph"
        )


@router.post("/{graph_id}/set-default", response_model=CommonResponse)
async def set_default_graph(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Set a graph as the default graph."""
    try:
        success = graph_repo.set_default_graph(graph_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found"
            )
        
        return CommonResponse(
            message="Default graph set successfully",
            status_code=status.HTTP_200_OK,
            data={"graph_id": str(graph_id)},
            error=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set default graph"
        )


@router.post("/{graph_id}/validate", response_model=CommonResponse)
async def validate_graph(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Validate a graph configuration."""
    try:
        from services.agent.dynamic_graph import DynamicGraphManager
        
        graph_manager = DynamicGraphManager()
        validation_result = graph_manager.validate_graph(graph_id)
        
        return CommonResponse(
            message="Graph validation completed",
            status_code=status.HTTP_200_OK,
            data=GraphValidationResult(**validation_result).dict(),
            error=None
        )
    except Exception as e:
        logger.error(f"Error validating graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate graph"
        )


# Node Management Routes
@router.post("/{graph_id}/nodes", response_model=CommonResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    graph_id: uuid.UUID,
    node_data: GraphNodeCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Create a new node in a graph."""
    try:
        db_node = graph_repo.create_node(graph_id, node_data)
        if not db_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found"
            )
        
        return CommonResponse(
            message="Node created successfully",
            status_code=status.HTTP_201_CREATED,
            data=GraphNodeInDB.from_orm(db_node).dict(),
            error=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating node in graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create node"
        )


@router.get("/{graph_id}/nodes", response_model=CommonResponse)
async def list_nodes(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """List all nodes in a graph."""
    try:
        nodes = graph_repo.get_nodes_by_graph(graph_id)
        
        return CommonResponse(
            message="Nodes retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[GraphNodeDetailInDB.from_orm(node).dict() for node in nodes],
            error=None
        )
    except Exception as e:
        logger.error(f"Error listing nodes for graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve nodes"
        )


@router.put("/nodes/{node_id}", response_model=CommonResponse)
async def update_node(
    node_id: uuid.UUID,
    node_data: GraphNodeUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Update a node."""
    try:
        db_node = graph_repo.update_node(node_id, node_data)
        if not db_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        return CommonResponse(
            message="Node updated successfully",
            status_code=status.HTTP_200_OK,
            data=GraphNodeInDB.from_orm(db_node).dict(),
            error=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update node"
        )


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Delete a node."""
    try:
        deleted = graph_repo.delete_node(node_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete node"
        )


# Edge Management Routes
@router.post("/{graph_id}/edges", response_model=CommonResponse, status_code=status.HTTP_201_CREATED)
async def create_edge(
    graph_id: uuid.UUID,
    edge_data: GraphEdgeCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Create a new edge in a graph."""
    try:
        db_edge = graph_repo.create_edge(graph_id, edge_data)
        if not db_edge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid edge: graph or nodes not found"
            )
        
        return CommonResponse(
            message="Edge created successfully",
            status_code=status.HTTP_201_CREATED,
            data=GraphEdgeInDB.from_orm(db_edge).dict(),
            error=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating edge in graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create edge"
        )


@router.get("/{graph_id}/edges", response_model=CommonResponse)
async def list_edges(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """List all edges in a graph."""
    try:
        edges = graph_repo.get_edges_by_graph(graph_id)
        
        return CommonResponse(
            message="Edges retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[GraphEdgeInDB.from_orm(edge).dict() for edge in edges],
            error=None
        )
    except Exception as e:
        logger.error(f"Error listing edges for graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve edges"
        )


@router.put("/edges/{edge_id}", response_model=CommonResponse)
async def update_edge(
    edge_id: uuid.UUID,
    edge_data: GraphEdgeUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Update an edge."""
    try:
        db_edge = graph_repo.update_edge(edge_id, edge_data)
        if not db_edge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Edge not found"
            )
        
        return CommonResponse(
            message="Edge updated successfully",
            status_code=status.HTTP_200_OK,
            data=GraphEdgeInDB.from_orm(db_edge).dict(),
            error=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating edge {edge_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update edge"
        )


@router.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(
    edge_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Delete an edge."""
    try:
        deleted = graph_repo.delete_edge(edge_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Edge not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting edge {edge_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete edge"
        )


# Tool Management Routes
@router.post("/tools", response_model=CommonResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: AvailableToolCreate,
    tool_repo: ToolRepository = Depends(get_tool_repository)
):
    """Create a new available tool."""
    try:
        db_tool = tool_repo.create_tool(tool_data)
        return CommonResponse(
            message="Tool created successfully",
            status_code=status.HTTP_201_CREATED,
            data=AvailableToolInDB.from_orm(db_tool).dict(),
            error=None
        )
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tool"
        )


@router.get("/tools", response_model=CommonResponse)
async def list_tools(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_enabled: Optional[bool] = Query(None),
    tool_repo: ToolRepository = Depends(get_tool_repository)
):
    """List all available tools."""
    try:
        tools = tool_repo.get_tools(limit=limit, offset=offset, is_enabled=is_enabled)
        
        return CommonResponse(
            message="Tools retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[AvailableToolInDB.from_orm(tool).dict() for tool in tools],
            error=None,
            meta={
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": len(tools)
                }
            }
        )
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tools"
        )


# Bulk Operations
@router.post("/bulk", response_model=CommonResponse, status_code=status.HTTP_201_CREATED)
async def create_graph_bulk(
    bulk_data: GraphBulkCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository)
):
    """Create a complete graph with nodes and edges in one operation."""
    try:
        # Create the graph
        db_graph = graph_repo.create_graph(bulk_data.graph)
        
        # Create nodes
        created_nodes = []
        for node_data in bulk_data.nodes:
            db_node = graph_repo.create_node(db_graph.id, node_data)
            if db_node:
                created_nodes.append(db_node)
        
        # Create edges
        created_edges = []
        for edge_data in bulk_data.edges:
            db_edge = graph_repo.create_edge(db_graph.id, edge_data)
            if db_edge:
                created_edges.append(db_edge)
        
        # Return the complete graph
        complete_graph = graph_repo.get_graph_with_details(db_graph.id)
        
        return CommonResponse(
            message="Graph created successfully with all components",
            status_code=status.HTTP_201_CREATED,
            data=GraphDetailInDB.from_orm(complete_graph).dict(),
            error=None,
            meta={
                "created_nodes": len(created_nodes),
                "created_edges": len(created_edges)
            }
        )
    except Exception as e:
        logger.error(f"Error creating bulk graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create graph"
        )


# Utility Routes
@router.get("/node-types", response_model=CommonResponse)
async def get_node_types():
    """Get available node types and their configurations."""
    node_types = [
        NodeTypeInfo(
            node_type="start",
            display_name="Start Node",
            description="Entry point for the graph execution",
            default_configuration={},
            required_fields=[],
            optional_fields=[]
        ),
        NodeTypeInfo(
            node_type="end",
            display_name="End Node", 
            description="Exit point for the graph execution",
            default_configuration={},
            required_fields=[],
            optional_fields=[]
        ),
        NodeTypeInfo(
            node_type="llm",
            display_name="LLM Node",
            description="Large Language Model processing node",
            default_configuration={
                "model": "default",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            required_fields=["model"],
            optional_fields=["temperature", "max_tokens", "system_prompt"]
        ),
        NodeTypeInfo(
            node_type="tool",
            display_name="Tool Node",
            description="External tool execution node",
            default_configuration={},
            required_fields=["tool_name"],
            optional_fields=["tool_config"]
        ),
        NodeTypeInfo(
            node_type="condition",
            display_name="Condition Node",
            description="Conditional branching node",
            default_configuration={
                "condition_type": "simple"
            },
            required_fields=["condition"],
            optional_fields=["condition_type"]
        ),
        NodeTypeInfo(
            node_type="human",
            display_name="Human Input Node",
            description="Node that requires human intervention",
            default_configuration={
                "timeout_seconds": 300
            },
            required_fields=[],
            optional_fields=["timeout_seconds", "prompt"]
        )
    ]
    
    return CommonResponse(
        message="Node types retrieved successfully",
        status_code=status.HTTP_200_OK,
        data=[node_type.dict() for node_type in node_types],
        error=None
    )


@router.post("/seed", response_model=CommonResponse)
async def seed_database():
    """Manually trigger database seeding for default tools and graphs."""
    try:
        from database.seed_data import seed_database
        
        result = seed_database()
        
        if result["status"] == "success":
            return CommonResponse(
                message="Database seeded successfully",
                status_code=status.HTTP_200_OK,
                data=result,
                error=None
            )
        else:
            return CommonResponse(
                message="Database seeding completed with warnings",
                status_code=status.HTTP_200_OK,
                data=result,
                error=result.get("message")
            )
            
    except Exception as e:
        logger.error(f"Manual database seeding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database seeding failed: {str(e)}"
        ) 