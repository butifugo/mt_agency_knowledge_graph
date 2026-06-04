"""Fast knowledge-graph build for retrieval.

Builds the document graph + content chunks + topic/hyperlink edges and saves
montana_knowledge.pkl — SKIPPING the expensive Phase-3 network analytics
(betweenness centrality / community detection) that the RAG retriever doesn't need.
Use when the full build (3_build_network.py) is too slow on a large corpus.

    PYTHONPATH=. .venv/bin/python scripts/build_graph_fast.py
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.network.graph_builder import GraphBuilder
from src.network.persistence import GraphPersistence
from src.network.semantic_layer import SemanticEnhancer

# Cap chunks per document so huge PDFs (financial reports, full rule sets) don't bloat the
# graph. Keeps every doc represented by its lead content while bounding total size.
MAX_CHUNKS_PER_DOC = 6


def main() -> None:
    t = time.time()
    print("PHASE 1/3: building document graph from knowledge/ ...", flush=True)
    graph = GraphBuilder(knowledge_dir="knowledge").build_graph(verbose=True)
    print(f"  nodes={len(graph.nodes):,}  ({time.time()-t:.0f}s)", flush=True)

    print(f"PHASE 2/3: chunks (max {MAX_CHUNKS_PER_DOC}/doc) + topic edges, no analytics ...", flush=True)
    enh = SemanticEnhancer(graph, knowledge_dir="knowledge")
    enh.create_chunks(verbose=True, max_chunks_per_doc=MAX_CHUNKS_PER_DOC)
    enh.add_topic_edges(verbose=True)
    graph.update_statistics()

    print("PHASE 3/3: saving exports ...", flush=True)
    saved = GraphPersistence(output_dir="src/network/exports").save_all(
        graph, prefix="montana_knowledge", verbose=True
    )

    print(
        f"\nDONE in {time.time()-t:.0f}s  "
        f"docs={graph.total_documents:,}  edges={len(graph.edges):,}  "
        f"chunks={graph.total_chunks:,}",
        flush=True,
    )
    print("saved:", saved, flush=True)


if __name__ == "__main__":
    main()
