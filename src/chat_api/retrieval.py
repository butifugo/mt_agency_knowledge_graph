"""Shared retrieval core: load the knowledge graph once and expose a retriever.

Both the chat API and the MCP server import ``get_retriever()`` so retrieval is
defined in exactly one place (over ``src/network``), never reimplemented.
"""
from functools import lru_cache

from src.network.persistence import GraphPersistence
from src.network.rag_retriever import GraphRAGRetriever

GRAPH_DIR = "src/network/exports"
GRAPH_FILE = "montana_knowledge.pkl"


@lru_cache(maxsize=1)
def get_retriever() -> GraphRAGRetriever:
    """Return a process-wide singleton retriever over the built graph."""
    graph = GraphPersistence(output_dir=GRAPH_DIR).load_pickle(GRAPH_FILE, verbose=False)
    if not graph:
        raise RuntimeError(
            f"Knowledge graph not found at {GRAPH_DIR}/{GRAPH_FILE}. "
            "Build it with: python src/network/3_build_network.py --quick"
        )
    return GraphRAGRetriever(graph)
