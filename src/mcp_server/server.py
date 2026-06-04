"""FastMCP server exposing Montana agency knowledge to AI clients.

Run (stdio) with the dedicated 3.12 venv:
    .venv/bin/python -m src.mcp_server.server

Register with an MCP client (e.g. Claude Desktop) — example config:
    {
      "mcpServers": {
        "montana-agency-knowledge": {
          "command": "/abs/path/to/.venv/bin/python",
          "args": ["-m", "src.mcp_server.server"],
          "cwd": "/abs/path/to/mt_agency_knowledge_graph"
        }
      }
    }
"""
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from src.chat_api.retrieval import get_retriever

SNIPPET_CHARS = 500


# ---- core logic (plain functions, independently testable) -------------------
def _clean_result(doc: Dict[str, Any]) -> Dict[str, Any]:
    chunks = doc.get("chunks") or []
    content = " ".join(c["content"] for c in chunks if c.get("content"))
    return {
        "node_id": doc.get("node_id"),
        "title": doc.get("title"),
        "agency": doc.get("agency"),
        "type": doc.get("type"),
        "source_url": doc.get("source_url"),
        "snippet": " ".join(content.split())[:SNIPPET_CHARS],
    }


def _search(query: str, top_k: int = 6, agency: Optional[str] = None) -> Dict[str, Any]:
    retriever = get_retriever()
    r = retriever.retrieve(query, top_k=top_k * 3 if agency else top_k, return_chunks=True)
    results = r.results
    if agency:
        results = [d for d in results if d.get("agency") == agency] or r.results
    results = results[:top_k]
    return {
        "query": r.query,
        "total_found": len(results),
        "search_strategy": r.search_strategy,
        "execution_time_ms": round(r.execution_time_ms, 1),
        "results": [_clean_result(d) for d in results],
    }


def _agency(agency: str, query: Optional[str], top_k: int = 10) -> Dict[str, Any]:
    rows = get_retriever().search_by_agency(agency, query=query, top_k=top_k)
    return {"agency": agency, "query": query, "total_found": len(rows), "results": rows}


def _context(node_id: str, context_hops: int = 1) -> Dict[str, Any]:
    return get_retriever().get_document_context(node_id, context_hops=context_hops)


# ---- MCP server + tools -----------------------------------------------------
mcp = FastMCP(
    "Montana Agency Knowledge",
    instructions=(
        "Answers questions from the public websites of Montana state agencies. "
        "Use search_agency_knowledge for general questions, search_by_agency to scope to one "
        "agency, and get_document_context to explore around a specific document. Every result "
        "includes a source_url — cite it when you answer."
    ),
)


@mcp.tool
def search_agency_knowledge(query: str, top_k: int = 6) -> Dict[str, Any]:
    """Search across all Montana state agencies for content relevant to a question.

    Returns ranked results, each with title, agency, source_url, and a content snippet
    to ground and cite an answer.
    """
    return _search(query, top_k)


@mcp.tool
def search_by_agency(agency: str, query: str = "", top_k: int = 10) -> Dict[str, Any]:
    """Search within a single agency (folder name, e.g. 'agriculture', 'human-resources').

    With no query, returns the agency's most important documents by graph importance.
    """
    return _agency(agency, query or None, top_k)


@mcp.tool
def get_document_context(node_id: str, context_hops: int = 1) -> Dict[str, Any]:
    """Return the graph neighborhood of a document (related-by-link/topic/agency)."""
    return _context(node_id, context_hops)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Montana Agency Knowledge MCP server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="run as a standing streamable-HTTP service (deployable) instead of stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()

    if args.http:
        # Networked service — clients (the demo bridge, Claude Desktop remote, etc.)
        # connect at http://<host>:<port>/mcp
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()  # stdio (default) — for local AI clients
