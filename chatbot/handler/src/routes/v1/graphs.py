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
    DynamicGraphExecutionRequest,
    WorkflowSaveRequest,
    WorkflowValidateRequest,
    NodePosition,
)
from schemas.responses.common import CommonResponse
from schemas.responses.graph import (
    GraphNodeDetailInDB,
    GraphEdgeInDB,
)
from services.dynamic_graph.engine.execution_engine import DynamicGraphExecutionEngine
from database.database import get_db
from sqlalchemy.orm import Session

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


# Bulk Operations for Workflow Management
@router.post("/bulk/save", response_model=CommonResponse)
async def save_workflow(
    workflow_data: WorkflowSaveRequest,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """
    Save entire workflow (bulk create/update nodes and edges).
    Expected format: {"nodes": [...], "edges": [...]}
    """
    try:
        nodes_data = workflow_data.nodes
        edges_data = workflow_data.edges
        
        saved_nodes = []
        saved_edges = []
        
        # Save nodes
        for node_data in nodes_data:
            # Convert ReactFlow format to backend format
            backend_node = GraphNodeCreate(
                node_id=node_data.id,
                node_type=node_data.data["nodeType"],
                name=node_data.data["name"],
                description=node_data.data.get("description"),
                position=node_data.position,
                configuration=node_data.data
            )
            
            # Check if node exists, update or create
            existing_node = graph_repo.get_node_by_node_id(node_data.id)
            if existing_node:
                updated_node = graph_repo.update_node(existing_node.id, GraphNodeUpdate(
                    name=backend_node.name,
                    description=backend_node.description,
                    position=backend_node.position,
                    configuration=backend_node.configuration
                ))
                saved_nodes.append(updated_node)
            else:
                created_node = graph_repo.create_node(backend_node)
                saved_nodes.append(created_node)
        
        # Save edges
        for edge_data in edges_data:
            backend_edge = GraphEdgeCreate(
                from_node_id=edge_data.source,
                to_node_id=edge_data.target,
                condition_type=edge_data.condition_type or "always",
                condition_config=edge_data.condition_config or {},
                label=edge_data.label
            )
            
            # For simplicity, always create new edges (delete old ones first)
            created_edge = graph_repo.create_edge(backend_edge)
            saved_edges.append(created_edge)
        
        return CommonResponse(
            message="Workflow saved successfully",
            status_code=status.HTTP_200_OK,
            data={
                "nodes": [GraphNodeDetailInDB.model_validate(n).model_dump() for n in saved_nodes],
                "edges": [GraphEdgeInDB.model_validate(e).model_dump() for e in saved_edges],
            },
            error=None,
        )
    except Exception as e:
        logger.error(f"Error saving workflow: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to save workflow",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.delete("/bulk/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_workflow(
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Clear entire workflow (delete all nodes and edges)."""
    try:
        # Delete all edges first (due to foreign key constraints)
        edges = graph_repo.get_all_edges()
        for edge in edges:
            graph_repo.delete_edge(edge.id)
        
        # Delete all nodes
        nodes = graph_repo.get_all_nodes()
        for node in nodes:
            graph_repo.delete_node(node.id)
        
        return CommonResponse(
            message="Workflow cleared successfully",
            status_code=status.HTTP_204_NO_CONTENT,
            data=None,
            error=None,
        )
    except Exception as e:
        logger.error(f"Error clearing workflow: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to clear workflow",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.get("/workflow/reactflow", response_model=CommonResponse)
async def get_workflow_for_reactflow(
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Get workflow in ReactFlow format for frontend consumption."""
    try:
        nodes = graph_repo.get_all_nodes()
        edges = graph_repo.get_all_edges()
        
        # Convert to ReactFlow format
        reactflow_nodes = []
        for node in nodes:
            reactflow_nodes.append({
                "id": node.node_id,
                "type": "custom",
                "position": {"x": node.position_x, "y": node.position_y},
                "data": {
                    "name": node.name,
                    "description": node.description,
                    "nodeType": node.node_type,
                    **node.configuration  # Spread configuration
                }
            })
        
        reactflow_edges = []
        for edge in edges:
            reactflow_edges.append({
                "id": f"e-{edge.from_node_id}-{edge.to_node_id}",
                "source": edge.from_node_id,
                "target": edge.to_node_id,
                "sourceHandle": "output",
                "targetHandle": "input",
                "type": "smoothstep",
                "animated": True,
                "style": {"stroke": "#6b7280", "strokeWidth": 1},
                "label": edge.label,
                "condition_type": edge.condition_type,
                "condition_config": edge.condition_config
            })
        
        return CommonResponse(
            message="Workflow retrieved successfully",
            status_code=status.HTTP_200_OK,
            data={
                "nodes": reactflow_nodes,
                "edges": reactflow_edges
            },
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving workflow: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve workflow",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.post("/validate", response_model=CommonResponse)
async def validate_workflow(
    workflow_data: WorkflowValidateRequest,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Validate workflow structure and configuration."""
    try:
        from services.dynamic_graph.engine.config_manager import ConfigManager
        
        nodes_data = workflow_data.nodes
        edges_data = workflow_data.edges
        
        errors = []
        warnings = []
        
        # Basic validation
        if not nodes_data:
            errors.append("Workflow must contain at least one node")
        
        # Check for start and end nodes
        node_types = [node.data["nodeType"] for node in nodes_data]
        if "start" not in node_types:
            warnings.append("Workflow should have a start node")
        if "end" not in node_types:
            warnings.append("Workflow should have an end node")
        
        # Validate node IDs are unique
        node_ids = [node.id for node in nodes_data]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Node IDs must be unique")
        
        # Validate edge connections
        for edge in edges_data:
            if edge.source not in node_ids:
                errors.append(f"Edge references non-existent source node: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"Edge references non-existent target node: {edge.target}")
        
        is_valid = len(errors) == 0
        
        return CommonResponse(
            message="Workflow validation completed",
            status_code=status.HTTP_200_OK,
            data={
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings
            },
            error=None,
        )
    except Exception as e:
        logger.error(f"Error validating workflow: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to validate workflow",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


# Dynamic Graph Execution
@router.post("/execute", response_model=CommonResponse)
async def execute_dynamic_graph(
    request: DynamicGraphExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute the dynamic graph workflow with the given input message.
    This endpoint builds the graph from the database and executes it.
    Supports both new chat sessions and continuing existing conversations.
    """
    try:
        # Handle new chat session (same logic as static graph)
        if request.is_new_chat:
            # Generate a new session ID for new chats
            session_id = str(uuid.uuid4())
        else:
            # Use provided session_id for existing chats
            session_id = request.session_id
            if not session_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=CommonResponse(
                        message="session_id is required when is_new_chat is False",
                        status_code=status.HTTP_400_BAD_REQUEST,
                        data=None,
                        error="Missing session_id for existing chat",
                    ).model_dump(),
                )
        
        engine = DynamicGraphExecutionEngine(db)
        
        result = await engine.execute_graph(
            chat_id=request.chat_id,
            session_id=session_id,
            input_message=request.message,
            graph_name=request.graph_name or "default",
        )
        
        # Add session_id to the response data (like static graph)
        result["session_id"] = session_id
        
        return CommonResponse(
            message="Graph executed successfully",
            status_code=status.HTTP_200_OK,
            data=result,
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Dynamic graph execution failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to execute graph",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


# Workflow Templates
@router.get("/templates", response_model=CommonResponse)
async def get_workflow_templates():
    """Get available workflow templates."""
    try:
        templates = [
            {
                "id": "simple-chat",
                "name": "Simple Chat Workflow",
                "description": "Basic chat workflow with LLM node",
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "custom",
                        "position": {"x": 100, "y": 100},
                        "data": {
                            "name": "Start",
                            "description": "Workflow entry point",
                            "nodeType": "start"
                        }
                    },
                    {
                        "id": "llm-1", 
                        "type": "custom",
                        "position": {"x": 300, "y": 100},
                        "data": {
                            "name": "Chat LLM",
                            "description": "Main chat processing",
                            "nodeType": "llm",
                            "system_prompt": "You are a helpful assistant.",
                            "temperature": 0.7
                        }
                    },
                    {
                        "id": "end-1",
                        "type": "custom", 
                        "position": {"x": 500, "y": 100},
                        "data": {
                            "name": "End",
                            "description": "Workflow completion",
                            "nodeType": "end"
                        }
                    }
                ],
                "edges": [
                    {
                        "id": "e-start-1-llm-1",
                        "source": "start-1",
                        "target": "llm-1",
                        "type": "smoothstep"
                    },
                    {
                        "id": "e-llm-1-end-1", 
                        "source": "llm-1",
                        "target": "end-1",
                        "type": "smoothstep"
                    }
                ]
            },
            {
                "id": "tool-workflow",
                "name": "Tool-Enhanced Workflow",
                "description": "Workflow with LLM and tool integration",
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "custom",
                        "position": {"x": 100, "y": 150},
                        "data": {
                            "name": "Start",
                            "description": "Workflow entry point",
                            "nodeType": "start"
                        }
                    },
                    {
                        "id": "llm-1",
                        "type": "custom", 
                        "position": {"x": 300, "y": 150},
                        "data": {
                            "name": "Reasoning LLM",
                            "description": "Initial analysis and tool selection",
                            "nodeType": "llm",
                            "system_prompt": "You are an AI assistant with access to tools. Analyze the user's request and decide if you need to use tools.",
                            "temperature": 0.3
                        }
                    },
                    {
                        "id": "condition-1",
                        "type": "custom",
                        "position": {"x": 500, "y": 150}, 
                        "data": {
                            "name": "Tool Decision",
                            "description": "Decide whether to use tools",
                            "nodeType": "condition"
                        }
                    },
                    {
                        "id": "tool-1",
                        "type": "custom",
                        "position": {"x": 600, "y": 50},
                        "data": {
                            "name": "Search Tool",
                            "description": "Web search capability", 
                            "nodeType": "tool"
                        }
                    },
                    {
                        "id": "llm-2",
                        "type": "custom",
                        "position": {"x": 700, "y": 150},
                        "data": {
                            "name": "Response LLM",
                            "description": "Generate final response",
                            "nodeType": "llm",
                            "system_prompt": "Provide a helpful response based on the conversation and any tool results.",
                            "temperature": 0.7
                        }
                    },
                    {
                        "id": "end-1",
                        "type": "custom",
                        "position": {"x": 900, "y": 150},
                        "data": {
                            "name": "End",
                            "description": "Workflow completion",
                            "nodeType": "end"
                        }
                    }
                ],
                "edges": [
                    {
                        "id": "e-start-1-llm-1",
                        "source": "start-1",
                        "target": "llm-1",
                        "type": "smoothstep"
                    },
                    {
                        "id": "e-llm-1-condition-1",
                        "source": "llm-1", 
                        "target": "condition-1",
                        "type": "smoothstep"
                    },
                    {
                        "id": "e-condition-1-tool-1",
                        "source": "condition-1",
                        "target": "tool-1",
                        "type": "smoothstep",
                        "condition_type": "conditional",
                        "condition_config": {
                            "conditions": {"use_tool": "tool-1"},
                            "default": "llm-2"
                        }
                    },
                    {
                        "id": "e-condition-1-llm-2",
                        "source": "condition-1",
                        "target": "llm-2", 
                        "type": "smoothstep"
                    },
                    {
                        "id": "e-tool-1-llm-2",
                        "source": "tool-1",
                        "target": "llm-2",
                        "type": "smoothstep"
                    },
                    {
                        "id": "e-llm-2-end-1",
                        "source": "llm-2",
                        "target": "end-1",
                        "type": "smoothstep"
                    }
                ]
            }
        ]
        
        return CommonResponse(
            message="Workflow templates retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=templates,
            error=None,
        )
    except Exception as e:
        logger.error(f"Error retrieving templates: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to retrieve templates",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )


@router.post("/templates/{template_id}/apply", response_model=CommonResponse)
async def apply_workflow_template(
    template_id: str,
    graph_repo: GraphRepository = Depends(get_graph_repository),
):
    """Apply a workflow template to create a new workflow."""
    try:
        # Get templates (in a real implementation, this would come from a database)
        templates_response = await get_workflow_templates()
        if not templates_response.data:
            raise ValueError("No templates available")
        
        template = None
        for t in templates_response.data:
            if t["id"] == template_id:
                template = t
                break
        
        if not template:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=CommonResponse(
                    message="Template not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                    data=None,
                    error=f"Template {template_id} does not exist",
                ).model_dump(),
            )
        
        # Clear existing workflow first
        existing_edges = graph_repo.get_all_edges()
        for edge in existing_edges:
            graph_repo.delete_edge(edge.id)
        
        existing_nodes = graph_repo.get_all_nodes()
        for node in existing_nodes:
            graph_repo.delete_node(node.id)
        
        # Apply template
        saved_nodes = []
        saved_edges = []
        
        # Create nodes from template
        for node_data in template["nodes"]:
            backend_node = GraphNodeCreate(
                node_id=node_data["id"],
                node_type=node_data["data"]["nodeType"],
                name=node_data["data"]["name"],
                description=node_data["data"].get("description"),
                position=NodePosition(
                    x=int(node_data["position"]["x"]),
                    y=int(node_data["position"]["y"])
                ),
                configuration=node_data["data"]
            )
            created_node = graph_repo.create_node(backend_node)
            saved_nodes.append(created_node)
        
        # Create edges from template
        for edge_data in template["edges"]:
            backend_edge = GraphEdgeCreate(
                from_node_id=edge_data["source"],
                to_node_id=edge_data["target"],
                condition_type=edge_data.get("condition_type", "always"),
                condition_config=edge_data.get("condition_config", {}),
                label=edge_data.get("label")
            )
            created_edge = graph_repo.create_edge(backend_edge)
            saved_edges.append(created_edge)
        
        return CommonResponse(
            message=f"Template '{template['name']}' applied successfully",
            status_code=status.HTTP_200_OK,
            data={
                "template": template,
                "nodes": [GraphNodeDetailInDB.model_validate(n).model_dump() for n in saved_nodes],
                "edges": [GraphEdgeInDB.model_validate(e).model_dump() for e in saved_edges],
            },
            error=None,
        )
        
    except Exception as e:
        logger.error(f"Error applying template: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=CommonResponse(
                message="Failed to apply template",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=None,
                error=str(e),
            ).model_dump(),
        )
