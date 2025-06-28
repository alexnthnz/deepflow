from fastapi import FastAPI

from .chat import router as chat_router
from .graphs import router as graph_router
from .mcp import router as mcp_router

api_v1 = FastAPI()
api_v1.include_router(chat_router, prefix="/chats")
api_v1.include_router(graph_router, prefix="/graphs", tags=["graphs"])
api_v1.include_router(mcp_router, prefix="/mcp", tags=["mcp"])
