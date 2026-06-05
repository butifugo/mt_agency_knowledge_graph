"""Unified deployable app — everything on one origin (for Railway / single-service hosting).

Serves:
  GET  /                 → the static front-end (web/: page, widget, graph + MCP tabs)
  POST /chat             → grounded, cited answer (Perplexity/Claude per CHAT_PROVIDER)
  GET  /health           → ok
  GET  /api/mcp/tools    → MCP tool list (browser demo bridge)
  POST /api/mcp/call     → invoke an MCP tool (browser demo bridge)
  /mcp                   → real MCP streamable-HTTP endpoint (for AI clients / Claude Desktop)

Run (local or hosted):
    uvicorn src.web_app:app --host 0.0.0.0 --port ${PORT:-8000}
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastmcp import Client
from pydantic import BaseModel

from src.chat_api.answer import MissingAPIKey, synthesize
from src.chat_api.retrieval import get_retriever
from src.mcp_server.server import mcp

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# Real MCP endpoint (streamable-HTTP) mounted into this app for AI clients.
_mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_retriever()  # warm the graph (downloads via GRAPH_URL on a fresh host)
    async with _mcp_app.lifespan(app):  # start the MCP session manager
        yield


app = FastAPI(title="Montana Agency Answer Engine", version="1.0.0", lifespan=lifespan)


# ---- chat (same origin as the page) ----------------------------------------
class ChatRequest(BaseModel):
    question: str
    agency: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    try:
        return synthesize(req.question.strip(), req.agency)
    except MissingAPIKey as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ---- MCP browser bridge (powers the "MCP server" tab) -----------------------
class CallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


@app.get("/api/mcp/tools")
async def mcp_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    return {
        "server": mcp.name,
        "tools": [
            {"name": t.name, "description": (t.description or "").strip()} for t in tools
        ],
    }


@app.post("/api/mcp/call")
async def mcp_call(req: CallRequest):
    try:
        async with Client(mcp) as client:
            result = await client.call_tool(req.tool, req.arguments)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{type(exc).__name__}: {exc}")
    data = getattr(result, "structured_content", None) or getattr(result, "data", None)
    return {"server": mcp.name, "request": {"tool": req.tool, "arguments": req.arguments}, "result": data}


# ---- real MCP endpoint for AI clients, then static front-end (catch-all) ----
app.mount("/mcp", _mcp_app)
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
