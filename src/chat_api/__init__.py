"""Chat API (Workstream 2) — a thin FastAPI service over the shared graph RAG core.

Retrieves passages from the knowledge graph and asks Claude to synthesize a grounded,
cited answer. The MCP server (a sibling surface) reuses the same retrieval core.
"""
