import logging
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from repositories.graph import get_graph_repository, GraphRepository
from schemas.requests.graph import (
    GraphNodeCreate,
    GraphNodeUpdate,
    GraphEdgeCreate,
    GraphEdgeUpdate,
)
from schemas.responses.common import CommonResponse
from schemas.responses.graph import (
    GraphNodeDetailInDB,
    GraphEdgeInDB,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Graph Overview Endpoint
@router.get("/", response_model=CommonResponse)
async def get_graph_overview(
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Get the complete graph structure with all nodes and edges."""
    try:
        nodes = graph_repo.get_all_nodes()
        edges = graph_repo.get_all_edges()

        return CommonResponse(
            message="Graph overview retrieved successfully",
            status_code=status.HTTP_200_OK,
            data={
                "nodes": [
                    GraphNodeDetailInDB.model_validate(n).model_dump() for n in nodes
                ],
                "edges": [GraphEdgeInDB.model_validate(e).model_dump() for e in edges],
            },
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving graph overview: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve graph overview",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


# Node Endpoints
@router.get("/nodes", response_model=CommonResponse)
async def list_nodes(
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """List all nodes in the graph."""
    try:
        nodes = graph_repo.get_all_nodes()
        return CommonResponse(
            message="Nodes retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[GraphNodeDetailInDB.model_validate(n).model_dump() for n in nodes],
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving nodes: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve nodes",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.post(
    "/nodes", response_model=CommonResponse, status_code=status.HTTP_201_CREATED
)
async def create_node(
    node: GraphNodeCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Create a new node in the graph."""
    try:
        db_node = graph_repo.create_node(node)
        return CommonResponse(
            message="Node created successfully",
            status_code=status.HTTP_201_CREATED,
            data=GraphNodeDetailInDB.model_validate(db_node).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to create node",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.get("/nodes/{node_id}", response_model=CommonResponse)
async def get_node(
    node_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Get a specific node by ID."""
    try:
        db_node = graph_repo.get_node_by_id(node_id)
        if not db_node:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Node not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Node does not exist",
                ).model_dump(),
            )
        return CommonResponse(
            message="Node retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=GraphNodeDetailInDB.model_validate(db_node).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving node: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve node",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.get("/nodes/by-node-id/{node_id}", response_model=CommonResponse)
async def get_node_by_node_id(
    node_id: str,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Get a specific node by its node_id string."""
    try:
        db_node = graph_repo.get_node_by_node_id(node_id)
        if not db_node:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Node not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Node does not exist",
                ).model_dump(),
            )
        return CommonResponse(
            message="Node retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=GraphNodeDetailInDB.model_validate(db_node).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving node: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve node",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.put("/nodes/{node_id}", response_model=CommonResponse)
async def update_node(
    node_id: uuid.UUID,
    node_update: GraphNodeUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Update a node."""
    try:
        db_node = graph_repo.get_node_by_id(node_id)
        if not db_node:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Node not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Node does not exist",
                ).model_dump(),
            )
        updated_node = graph_repo.update_node(node_id, node_update)
        return CommonResponse(
            message="Node updated successfully",
            status_code=status.HTTP_200_OK,
            data=GraphNodeDetailInDB.model_validate(updated_node).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error updating node: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to update node",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Delete a node."""
    try:
        db_node = graph_repo.get_node_by_id(node_id)
        if not db_node:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Node not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Node does not exist",
                ).model_dump(),
            )
        graph_repo.delete_node(node_id)
        return CommonResponse(
            message="Node deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
            data=None,
            error=None,
        )
    except Exception as e:
        logger.error(f"Error deleting node: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to delete node",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


# Edge Endpoints
@router.get("/edges", response_model=CommonResponse)
async def list_edges(
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """List all edges in the graph."""
    try:
        edges = graph_repo.get_all_edges()
        return CommonResponse(
            message="Edges retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[GraphEdgeInDB.model_validate(e).model_dump() for e in edges],
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving edges: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve edges",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.post(
    "/edges", response_model=CommonResponse, status_code=status.HTTP_201_CREATED
)
async def create_edge(
    edge: GraphEdgeCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Create a new edge in the graph."""
    try:
        db_edge = graph_repo.create_edge(edge)
        return CommonResponse(
            message="Edge created successfully",
            status_code=status.HTTP_201_CREATED,
            data=GraphEdgeInDB.model_validate(db_edge).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error creating edge: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to create edge",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.get("/edges/{edge_id}", response_model=CommonResponse)
async def get_edge(
    edge_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Get a specific edge by ID."""
    try:
        db_edge = graph_repo.get_edge_by_id(edge_id)
        if not db_edge:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Edge not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Edge does not exist",
                ).model_dump(),
            )
        return CommonResponse(
            message="Edge retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=GraphEdgeInDB.model_validate(db_edge).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving edge: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve edge",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.put("/edges/{edge_id}", response_model=CommonResponse)
async def update_edge(
    edge_id: uuid.UUID,
    edge_update: GraphEdgeUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Update an edge."""
    try:
        db_edge = graph_repo.get_edge_by_id(edge_id)
        if not db_edge:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Edge not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Edge does not exist",
                ).model_dump(),
            )
        updated_edge = graph_repo.update_edge(edge_id, edge_update)
        return CommonResponse(
            message="Edge updated successfully",
            status_code=status.HTTP_200_OK,
            data=GraphEdgeInDB.model_validate(updated_edge).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error updating edge: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to update edge",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(
    edge_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Delete an edge."""
    try:
        db_edge = graph_repo.get_edge_by_id(edge_id)
        if not db_edge:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Edge not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Edge does not exist",
                ).model_dump(),
            )
        graph_repo.delete_edge(edge_id)
        return CommonResponse(
            message="Edge deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
            data=None,
            error=None,
        )
    except Exception as e:
        logger.error(f"Error deleting edge: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to delete edge",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )
