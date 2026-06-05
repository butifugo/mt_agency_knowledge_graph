"""Build web/graph.json — a SAMPLED, browser-renderable view of the knowledge graph.

The full graph (11k+ nodes / 224k edges) is too big for the browser, so we sample agency
"hub" nodes + the top-N documents per agency (by in-degree), enrich each node with its
keywords/topics/type/degree, and include the meaningful relationship edges among the
sampled nodes. The demo's graph tab renders this with an agency filter and a click-to-detail
panel. (Connections shown are from this sample, not the full graph.)

    PYTHONPATH=. .venv/bin/python scripts/build_graph_viz.py [--per-agency 30 --max-edges 1200]
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.network.persistence import GraphPersistence
from src.network.schema import EdgeType, NodeType

OUT = ROOT / "web" / "graph.json"
# Meaningful relationship edges to show (exclude the dense same_agency / belongs_to_agency).
REL_EDGE_TYPES = {
    EdgeType.TOPIC_RELATED,
    EdgeType.HYPERLINK,
    EdgeType.SEMANTIC_SIMILAR,
    EdgeType.CITATION,
    EdgeType.PARENT_CHILD,
}
SKIP_AGENCIES = {"knowledge"}  # stray bucket from non-agency files (e.g. knowledge/README.md)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-agency", type=int, default=30)
    ap.add_argument("--max-edges", type=int, default=1200)
    args = ap.parse_args()

    graph = GraphPersistence(output_dir="src/network/exports").load_pickle(
        "montana_knowledge.pkl", verbose=False
    )
    if not graph:
        raise SystemExit("montana_knowledge.pkl not found — build the graph first.")

    nodes, links, sampled = [], [], set()
    agencies = []

    for agency in sorted(graph.agency_index.keys()):
        if agency in SKIP_AGENCIES:
            continue
        docs = [n for n in graph.get_by_agency(agency) if n.node_type != NodeType.AGENCY_ROOT]
        if not docs:
            continue
        docs.sort(key=lambda n: n.in_degree, reverse=True)
        docs = docs[: args.per_agency]

        agencies.append(agency)
        hub_id = f"agency:{agency}"
        nodes.append({
            "id": hub_id, "label": agency.replace("-", " ").title(),
            "agency": agency, "kind": "agency", "doc_count": len(docs),
        })
        for n in docs:
            sampled.add(n.node_id)
            nodes.append({
                "id": n.node_id,
                "label": (n.title or n.node_id)[:70],
                "agency": agency,
                "kind": "doc",
                "type": n.node_type.value,
                "url": n.source_url or "",
                "keywords": (n.keywords or [])[:8],
                "topics": (n.topics or [])[:8],
                "in_degree": n.in_degree,
                "out_degree": n.out_degree,
            })
            links.append({"source": n.node_id, "target": hub_id, "type": "belongs_to_agency"})

    # relationship edges among sampled docs (so nodes have neighbors to explore)
    rel = 0
    for e in graph.edges:
        if rel >= args.max_edges:
            break
        if e.edge_type in REL_EDGE_TYPES and e.source_id in sampled and e.target_id in sampled:
            links.append({
                "source": e.source_id, "target": e.target_id, "type": e.edge_type.value,
            })
            rel += 1

    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "total_nodes": len(graph.nodes),
        "total_edges": len(graph.edges),
        "agencies": agencies,
        "nodes": nodes,
        "links": links,
    }
    OUT.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(nodes)} nodes, {len(links)} links "
          f"({rel} relationship edges) across {len(agencies)} agencies "
          f"(of {len(graph.nodes):,} total nodes)")


if __name__ == "__main__":
    main()
