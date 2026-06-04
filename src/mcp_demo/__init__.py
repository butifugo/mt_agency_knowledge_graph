"""MCP demo bridge — a thin HTTP shim so a browser can demonstrate the MCP server.

A browser can't speak MCP (JSON-RPC over stdio/streamable-HTTP), so this small FastAPI
service acts as a real MCP *client* to the MCP server and exposes its tool list and tool
calls over plain HTTP for the demo page. It is ADDITIVE — separate process/port from the
chat API; nothing in the working chat path changes.
"""
