---
name: knowledge-query
description: Load the built knowledge graph and query/reason over it (or inspect RAG output) during development. Use to answer questions from agency content, debug retrieval, or check what's in the graph — without standing up the MCP server.
---

# Knowledge query

A fast path to query the knowledge graph and inspect `RAGResult` output directly in Python — for development, debugging retrieval, and building Círdan's gold-question evaluations. Same engine the MCP server wraps; no server needed.

## Load the graph and retrieve

```python
# from repo root, with .venv active
from src.network.persistence import GraphPersistence
from src.network.rag_retriever import GraphRAGRetriever

graph = GraphPersistence(output_dir="src/network/exports").load()   # montana_knowledge.pkl
retriever = GraphRAGRetriever(graph)

result = retriever.retrieve("What are Montana employee leave policies?")
# result is a RAGResult: query, results[], total_found, search_strategy, execution_time_ms, expanded_nodes
for r in result.results:
    print(r)            # inspect the matched chunk/document + its source for citation
```

(Confirm exact constructor/method signatures in `src/network/rag_retriever.py` and `persistence.py` — treat `schema.py` as the source of truth for field names.)

## Common queries

- **Scoped to one agency:** `retriever.search_by_agency(query, agency="agriculture")`.
- **Follow-up context:** `retriever.get_document_context(node_id)` for neighbors of a known document.
- **Inspect the graph itself:** the `KnowledgeGraph` holds nodes (documents), edges (relationships), and chunks (RAG units); `src/network/analyzer.py` offers PageRank/centrality/communities.

## Reading a `RAGResult`

- `results[]` — the retrieved units; each should carry enough source info to **cite**. A result without a usable citation is a quality failure (Círdan).
- `search_strategy` / `expanded_nodes` — how the answer was found (keyword + graph BFS today, not embeddings); useful when diagnosing thin or off-target results.
- `total_found`, `execution_time_ms` — coverage and latency signals.

## Guardrails

- **Read-only.** This queries an already-built graph; it does not crawl or rebuild. If results look wrong or empty, suspect a **stale graph** — rebuild with `python src/network/3_build_network.py --quick` rather than hand-editing exports.
- Don't reimplement retrieval here; if you need new behavior, add it in `src/network/` so the CLIs and MCP server share it.
