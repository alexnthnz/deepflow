import logging
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from repositories.graph import get_graph_repository, GraphRepository
from schemas.requests.graph import (
    GraphCreate,
    GraphUpdate,
    GraphNodeCreate,
    GraphNodeUpdate,
    GraphEdgeCreate,
    GraphEdgeUpdate,
)
from schemas.responses.common import CommonResponse
from schemas.responses.graph import (
    GraphInDB,
    GraphDetailInDB,
    GraphNodeDetailInDB,
    GraphEdgeInDB,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=CommonResponse)
async def list_graphs(
    graph_repo: GraphRepository = Depends(get_graph_repository),
    limit: int = 50,
    offset: int = 0,
    is_active: bool | None = None,
):
    try:
        graphs = graph_repo.get_graphs(limit=limit, offset=offset, is_active=is_active)
        return CommonResponse(
            message="Graphs retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=[GraphInDB.model_validate(g).model_dump() for g in graphs],
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving graphs: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve graphs",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.post("/", response_model=CommonResponse, status_code=status.HTTP_201_CREATED)
async def create_graph(
    graph: GraphCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_graph = graph_repo.create_graph(graph)
        return CommonResponse(
            message="Graph created successfully",
            status_code=status.HTTP_201_CREATED,
            data=GraphInDB.model_validate(db_graph).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error creating graph: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to create graph",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.get("/{graph_id}", response_model=CommonResponse)
async def get_graph(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_graph = graph_repo.get_graph_with_details(graph_id)
        if not db_graph:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Graph not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Graph does not exist",
                ).model_dump(),
            )

        graph_resp = GraphDetailInDB.model_validate(db_graph)
        graph_resp.nodes = [
            GraphNodeDetailInDB.model_validate(n) for n in db_graph.nodes
        ]
        graph_resp.edges = [GraphEdgeInDB.model_validate(e) for e in db_graph.edges]

        return CommonResponse(
            message="Graph retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=graph_resp.model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving graph: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve graph",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.put("/{graph_id}", response_model=CommonResponse)
async def update_graph(
    graph_id: uuid.UUID,
    graph_update: GraphUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_graph = graph_repo.update_graph(graph_id, graph_update)
        if not db_graph:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Graph not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Graph does not exist",
                ).model_dump(),
            )
        return CommonResponse(
            message="Graph updated successfully",
            status_code=status.HTTP_200_OK,
            data=GraphInDB.model_validate(db_graph).model_dump(),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error updating graph: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to update graph",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.delete("/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_graph(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        deleted = graph_repo.delete_graph(graph_id)
        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Graph not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Graph does not exist",
                ).model_dump(),
            )
        return CommonResponse(
            message="Graph deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
            data=None,
            error=None,
        )
    except Exception as e:
        logger.error(f"Error deleting graph: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to delete graph",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.get("/{graph_id}/nodes", response_model=CommonResponse)
async def list_nodes(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        nodes = graph_repo.get_nodes_by_graph(graph_id)
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
    "/{graph_id}/nodes",
    response_model=CommonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_node(
    graph_id: uuid.UUID,
    node: GraphNodeCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_node = graph_repo.create_node(graph_id, node)
        if not db_node:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Graph not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Graph does not exist",
                ).model_dump(),
            )
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


@router.get("/{graph_id}/nodes/{node_id}", response_model=CommonResponse)
async def get_node(
    graph_id: uuid.UUID,
    node_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_node = graph_repo.get_node_by_id(node_id)
        if not db_node or db_node.graph_id != graph_id:
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


@router.put("/{graph_id}/nodes/{node_id}", response_model=CommonResponse)
async def update_node(
    graph_id: uuid.UUID,
    node_id: uuid.UUID,
    node_update: GraphNodeUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_node = graph_repo.get_node_by_id(node_id)
        if not db_node or db_node.graph_id != graph_id:
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


@router.delete("/{graph_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    graph_id: uuid.UUID,
    node_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_node = graph_repo.get_node_by_id(node_id)
        if not db_node or db_node.graph_id != graph_id:
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


@router.get("/{graph_id}/edges", response_model=CommonResponse)
async def list_edges(
    graph_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        edges = graph_repo.get_edges_by_graph(graph_id)
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
    "/{graph_id}/edges",
    response_model=CommonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_edge(
    graph_id: uuid.UUID,
    edge: GraphEdgeCreate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_edge = graph_repo.create_edge(graph_id, edge)
        if not db_edge:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Graph or nodes not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error="Invalid graph or node reference",
                ).model_dump(),
            )
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


@router.get("/{graph_id}/edges/{edge_id}", response_model=CommonResponse)
async def get_edge(
    graph_id: uuid.UUID,
    edge_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_edge = graph_repo.get_edge_by_id(edge_id)
        if not db_edge or db_edge.graph_id != graph_id:
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


@router.put("/{graph_id}/edges/{edge_id}", response_model=CommonResponse)
async def update_edge(
    graph_id: uuid.UUID,
    edge_id: uuid.UUID,
    edge_update: GraphEdgeUpdate,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_edge = graph_repo.get_edge_by_id(edge_id)
        if not db_edge or db_edge.graph_id != graph_id:
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


@router.delete("/{graph_id}/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(
    graph_id: uuid.UUID,
    edge_id: uuid.UUID,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    try:
        db_edge = graph_repo.get_edge_by_id(edge_id)
        if not db_edge or db_edge.graph_id != graph_id:
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
