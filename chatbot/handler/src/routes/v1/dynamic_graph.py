"""
Dynamic Graph API Route

Endpoint for executing the dynamic graph and returning results.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from services.dynamic_graph.engine.execution_engine import DynamicGraphExecutionEngine
from database.database import get_db

router = APIRouter(prefix="/api/v1/dynamic-graph", tags=["Dynamic Graph"])


class DynamicGraphExecutionRequest(BaseModel):
    chat_id: Optional[str]
    session_id: str
    message: str
    graph_name: Optional[str] = "default"


@router.post("/execute")
async def execute_dynamic_graph(
    request: DynamicGraphExecutionRequest, db: Session = Depends(get_db)
):
    """
    Execute the dynamic graph with the given input message.
    """
    engine = DynamicGraphExecutionEngine(db)
    try:
        result = await engine.execute_graph(
            chat_id=request.chat_id,
            session_id=request.session_id,
            input_message=request.message,
            graph_name=request.graph_name or "default",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
