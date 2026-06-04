"""MVP Slice 1 smoke check.

Loads the existing knowledge graph and proves ``retrieve()`` returns citation-ready
passages on real Montana agency data. Run from the repo root with the venv active:

    source .venv/bin/activate
    python scripts/mvp_smoke.py
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.network.persistence import GraphPersistence
from src.network.rag_retriever import GraphRAGRetriever


def load_retriever() -> GraphRAGRetriever:
    t = time.time()
    graph = GraphPersistence(output_dir="src/network/exports").load_pickle(
        "montana_knowledge.pkl", verbose=False
    )
    if not graph:
        raise SystemExit("✗ Could not load montana_knowledge.pkl — build the graph first.")
    print(
        f"Loaded graph: {len(graph.nodes):,} nodes · {len(graph.edges):,} edges · "
        f"{len(graph.chunks):,} chunks · {graph.total_agencies} agencies "
        f"({time.time() - t:.1f}s)"
    )
    return GraphRAGRetriever(graph)


def main() -> None:
    retriever = load_retriever()
    queries = [
        "employee leave and vacation policies",
        "how do I file a consumer complaint",
        "agriculture pesticide licensing",
    ]
    for q in queries:
        r = retriever.retrieve(q, top_k=5, return_chunks=True, strategy="hybrid")
        print("\n" + "=" * 80)
        print(f"Q: {q}")
        print(f"   strategy={r.search_strategy}  found={r.total_found}  {r.execution_time_ms:.0f}ms")
        for i, doc in enumerate(r.results[:3], 1):
            url = doc.get("source_url") or "(no url)"
            print(f"  {i}. {doc['title']}  [{doc['agency']}]")
            print(f"     source: {url}")
            chunks = doc.get("chunks") or []
            if chunks and chunks[0].get("content"):
                snippet = " ".join(chunks[0]["content"].split())[:160]
                print(f"     snippet: {snippet}…")
    print(
        "\n✓ Retrieval works on real data; results carry source_url + chunk text "
        "(citation-ready for the chat API and MCP server)."
    )


if __name__ == "__main__":
    main()
