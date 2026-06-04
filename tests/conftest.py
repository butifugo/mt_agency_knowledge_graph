"""Shared test fixtures.

The retrieval fixtures load the real built graph (``montana_knowledge.pkl``) once per
session. It is large (~390MB), so this is an integration-style harness, not a unit micro-test.
A smaller sampled fixture can replace it later if load time becomes a problem.
"""
import pytest

from src.network.persistence import GraphPersistence
from src.network.rag_retriever import GraphRAGRetriever

GRAPH_DIR = "src/network/exports"
GRAPH_FILE = "montana_knowledge.pkl"


@pytest.fixture(scope="session")
def graph():
    g = GraphPersistence(output_dir=GRAPH_DIR).load_pickle(GRAPH_FILE, verbose=False)
    if not g:
        pytest.skip(f"{GRAPH_DIR}/{GRAPH_FILE} not available — build the graph first")
    return g


@pytest.fixture(scope="session")
def retriever(graph):
    return GraphRAGRetriever(graph)
