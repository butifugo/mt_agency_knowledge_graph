"""MCP demo bridge (FastAPI). Lets the browser demo the MCP server.

Run (separate from the chat API):
    .venv/bin/uvicorn src.mcp_demo.app:app --host 127.0.0.1 --port 8002

Endpoints:
    GET  /health      — bridge + MCP server name
    GET  /mcp/tools   — list the MCP server's tools (what an AI client would see)
    POST /mcp/call    — invoke an MCP tool and return the raw result
"""
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Client
from pydantic import BaseModel

from src.chat_api.retrieval import get_retriever
from src.mcp_server.server import mcp

# If set, connect to a STANDING networked MCP service over HTTP (the deployable path),
# e.g. MCP_SERVER_URL=http://127.0.0.1:8003/mcp. Otherwise fall back to an in-process
# client against the imported server object (zero-dependency local demo).
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "").strip()


def _client() -> Client:
    return Client(MCP_SERVER_URL) if MCP_SERVER_URL else Client(mcp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only the in-process mode needs the graph warmed here; in HTTP mode the standing
    # MCP service owns the graph.
    if not MCP_SERVER_URL:
        get_retriever()
    yield


app = FastAPI(title="MCP Demo Bridge", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def _input_schema(tool) -> Any:
    return getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "server": mcp.name,
        "mode": "http" if MCP_SERVER_URL else "in-process",
        "target": MCP_SERVER_URL or "in-process",
    }


@app.get("/mcp/tools")
async def list_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    return {
        "server": mcp.name,
        "tools": [
            {
                "name": t.name,
                "description": (t.description or "").strip(),
                "input_schema": _input_schema(t),
            }
            for t in tools
        ],
    }


class CallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


@app.post("/mcp/call")
async def call_tool(req: CallRequest):
    try:
        async with _client() as client:
            result = await client.call_tool(req.tool, req.arguments)
    except Exception as exc:  # surface tool/validation errors to the demo UI
        raise HTTPException(status_code=400, detail=f"{type(exc).__name__}: {exc}")
    data = getattr(result, "structured_content", None) or getattr(result, "data", None)
    return {
        "server": mcp.name,
        "request": {"tool": req.tool, "arguments": req.arguments},
        "result": data,
    }
