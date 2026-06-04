"""Build web/graph.json — a SAMPLED, browser-renderable view of the knowledge graph.

The full graph (11k+ nodes / 224k edges) is far too big for the browser, so we sample:
agency "hub" nodes + the top-N documents per agency (by in-degree), plus a capped set of
inter-document edges. Colored by agency in the demo's D3 force view.

    PYTHONPATH=. .venv/bin/python scripts/build_graph_viz.py [--per-agency 30 --max-cross 250]
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
CROSS_EDGE_TYPES = {EdgeType.TOPIC_RELATED, EdgeType.HYPERLINK, EdgeType.SEMANTIC_SIMILAR}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-agency", type=int, default=30)
    ap.add_argument("--max-cross", type=int, default=250)
    args = ap.parse_args()

    graph = GraphPersistence(output_dir="src/network/exports").load_pickle(
        "montana_knowledge.pkl", verbose=False
    )
    if not graph:
        raise SystemExit("montana_knowledge.pkl not found — build the graph first.")

    nodes, links, sampled = [], [], set()
    agencies = []

    SKIP_AGENCIES = {"knowledge"}  # stray buckets from non-agency files (e.g. knowledge/README.md)
    for agency in sorted(graph.agency_index.keys()):
        if agency in SKIP_AGENCIES:
            continue
        docs = [
            n for n in graph.get_by_agency(agency)
            if n.node_type != NodeType.AGENCY_ROOT
        ]
        if not docs:
            continue
        docs.sort(key=lambda n: n.in_degree, reverse=True)
        docs = docs[: args.per_agency]

        agencies.append(agency)
        hub_id = f"agency:{agency}"
        nodes.append({
            "id": hub_id,
            "label": agency.replace("-", " ").title(),
            "agency": agency,
            "kind": "agency",
        })
        for n in docs:
            sampled.add(n.node_id)
            nodes.append({
                "id": n.node_id,
                "label": (n.title or n.node_id)[:60],
                "agency": agency,
                "kind": "doc",
                "url": n.source_url or "",
            })
            links.append({"source": n.node_id, "target": hub_id, "type": "belongs_to_agency"})

    # capped inter-document edges among the sampled nodes, for cross-links
    cross = 0
    for e in graph.edges:
        if cross >= args.max_cross:
            break
        if e.edge_type in CROSS_EDGE_TYPES and e.source_id in sampled and e.target_id in sampled:
            links.append({"source": e.source_id, "target": e.target_id, "type": e.edge_type.value})
            cross += 1

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
          f"({cross} cross-edges) across {len(agencies)} agencies "
          f"(of {len(graph.nodes):,} total nodes)")


if __name__ == "__main__":
    main()
