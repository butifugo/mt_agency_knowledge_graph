"""Shared retrieval core: load the knowledge graph once and expose a retriever.

Both the chat API and the MCP server import ``get_retriever()`` so retrieval is
defined in exactly one place (over ``src/network``), never reimplemented.
"""
import os
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

from src.network.persistence import GraphPersistence
from src.network.rag_retriever import GraphRAGRetriever

GRAPH_DIR = "src/network/exports"
GRAPH_FILE = "montana_knowledge.pkl"


def build_node_filter(
    agency: Optional[str] = None, url_contains: Optional[str] = None
) -> Optional[Callable[[object], bool]]:
    """A retriever ``node_filter`` predicate for scoping to an agency and/or a URL section.

    Returns ``None`` when no scope is requested, so the retriever ranks the whole graph.
    Used by both surfaces (chat API personas, MCP persona tool) so scoping is defined once.
    """
    agency = (agency or "").strip() or None
    uc = (url_contains or "").strip().lower() or None
    if not agency and not uc:
        return None

    def predicate(node: object) -> bool:
        if agency and (getattr(node, "agency", "") or "") != agency:
            return False
        if uc and uc not in (getattr(node, "source_url", "") or "").lower():
            return False
        return True

    return predicate


def _ensure_graph_file() -> None:
    """If the pickle is absent and GRAPH_URL is set, download it (for hosted deploys).

    Locally the file already exists, so this is a no-op. On a fresh host (Railway), set
    GRAPH_URL to a downloadable .pkl; optionally GRAPH_URL_TOKEN for an Authorization
    bearer token (e.g. a private GitHub release asset).
    """
    path = Path(GRAPH_DIR) / GRAPH_FILE
    if path.exists():
        return
    url = os.getenv("GRAPH_URL", "").strip()
    if not url:
        return  # nothing to fetch; load() will raise a clear error
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url)
    token = os.getenv("GRAPH_URL_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/octet-stream")
    tmp = path.with_suffix(".pkl.partial")
    with urllib.request.urlopen(req) as resp, open(tmp, "wb") as out:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
    tmp.replace(path)


@lru_cache(maxsize=1)
def get_retriever() -> GraphRAGRetriever:
    """Return a process-wide singleton retriever over the built graph."""
    _ensure_graph_file()
    graph = GraphPersistence(output_dir=GRAPH_DIR).load_pickle(GRAPH_FILE, verbose=False)
    if not graph:
        raise RuntimeError(
            f"Knowledge graph not found at {GRAPH_DIR}/{GRAPH_FILE} and no GRAPH_URL set. "
            "Build it (scripts/build_graph_fast.py) or set GRAPH_URL to a downloadable .pkl."
        )
    return GraphRAGRetriever(graph)
