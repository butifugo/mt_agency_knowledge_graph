"""MCP server (Workstream 5) — exposes the shared graph RAG core to AI clients.

Thin FastMCP wrapper over ``src.chat_api.retrieval.get_retriever`` (the same core the
chat API uses). Tools return retrieval results with source URLs for citation; retrieval
is never reimplemented here.

Requires Python >= 3.10 (FastMCP); the project uses a single Python 3.12 venv (.venv).
"""
