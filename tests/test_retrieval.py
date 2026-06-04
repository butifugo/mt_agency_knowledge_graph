"""Slice 1 — retrieval smoke tests against the real knowledge graph.

Verifies the ``RAGResult`` contract and that results are *citation-ready*
(carry a source URL + chunk text), which is the foundation the chat API and the
MCP server both build on.
"""
from src.network.schema import RAGResult

COMMON_QUERY = "employee leave and vacation policies"


def test_retrieve_returns_ragresult_contract(retriever):
    r = retriever.retrieve(COMMON_QUERY, top_k=5, return_chunks=True)
    assert isinstance(r, RAGResult)
    assert r.query == COMMON_QUERY
    assert isinstance(r.results, list)
    assert r.total_found == len(r.results)
    assert isinstance(r.search_strategy, str) and r.search_strategy
    assert isinstance(r.execution_time_ms, float)
    assert isinstance(r.expanded_nodes, list)


def test_results_are_citation_ready(retriever):
    r = retriever.retrieve(COMMON_QUERY, top_k=8, return_chunks=True)
    assert r.results, "expected at least one result for a common query"
    for doc in r.results:
        assert doc.get("title")
        assert "source_url" in doc
        assert doc.get("agency")
    # at least one result has a real URL to cite ...
    assert any((doc.get("source_url") or "").startswith("http") for doc in r.results)
    # ... and at least one carries chunk text to ground an answer
    assert any(
        doc.get("chunks") and doc["chunks"][0].get("content")
        for doc in r.results
    )


def test_search_by_agency_scopes_to_agency(retriever):
    # signature is search_by_agency(agency, query=None, top_k)
    rows = retriever.search_by_agency("human-resources", query="leave", top_k=5)
    assert isinstance(rows, list)
    for row in rows:
        node = retriever.graph.nodes.get(row["node_id"])
        assert node is not None and node.agency == "human-resources"
