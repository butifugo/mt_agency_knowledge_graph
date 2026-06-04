---
name: mcp-server
description: Build and extend the project's MCP server (Python / FastMCP) that exposes the graph-enhanced RAG retriever so AI clients can answer questions from Montana agency public content. Use when designing, adding, or changing MCP tools.
---

# MCP server

The mission: an **MCP server that answers people's questions from Montana agency public content.** The server is a thin Python/**FastMCP** layer whose tools **wrap the existing `GraphRAGRetriever`** and return the existing `RAGResult` shape. It is a driver around the graph engine — never a place to reimplement retrieval.

## Core principle

> The graph engine in `src/network/` is the durable API. MCP tools call its methods and return its contracts. If a tool needs new retrieval behavior, add it to `src/network/` (reusable from the CLIs too), then wrap it — do not write retrieval logic in the server.

## The retriever surface to wrap

`src/network/rag_retriever.py` → `GraphRAGRetriever`:

| Method | MCP tool intent |
|--------|-----------------|
| `retrieve(query, ...)` | General question → cited passages across all loaded agencies |
| `search_by_agency(query, agency, ...)` | Same, scoped to one agency |
| `get_document_context(node_id, ...)` | Follow-up: neighbors/context for a known document |

All return the **`RAGResult`** contract (`src/network/schema.py`): `query`, `results[]`, `total_found`, `search_strategy`, `execution_time_ms`, `expanded_nodes`. MCP tool outputs must preserve this shape (serialize, don't reshape).

## Building a tool (pattern)

1. Load the graph once at startup via `GraphPersistence(output_dir="src/network/exports")` → `montana_knowledge.pkl`; construct a `GraphRAGRetriever` over it. Reuse across calls.
2. Register a FastMCP tool with a **clear name + description** (the calling model reads these to choose it — coordinate naming with Galadriel). Map args to the retriever method.
3. In the tool body: call the retriever, return the `RAGResult` (as a dict/JSON). No re-ranking or re-querying outside `src/network/`.
4. Surface citations: each `results[]` item should carry its source so the client can attribute the answer (trust is the product).

## Decisions to make explicitly

- **Transport**: stdio (local/embedded clients) vs. HTTP (embeddable on agency websites). Start stdio for development.
- **Freshness**: the server reads a built `.pkl`; document how/when it reloads after a rebuild (Treebeard owns freshness).
- **Scope/safety**: read-only retrieval only; no crawling or graph mutation from the server; never leak secrets in tool output.

## Gates before shipping a tool (see `CLAUDE.md`)

- Server starts clean; a live tool call returns a valid `RAGResult` with non-empty, cited `results` (Gimli).
- `schema.py`/`RAGResult` unchanged or rippled to all consumers (Faramir).
- Answer relevance + citation accuracy meet the gold-set bar (Círdan) — the builder does not self-certify this.
- pytest covers the tool wrapping (Samwise).

FastMCP is not yet in `requirements.txt`; add it when the first tool lands.
