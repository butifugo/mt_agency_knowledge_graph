# Architecture — Montana Agency Knowledge Network

A technical walkthrough of how the system turns 37+ Montana state-agency websites into a
queryable knowledge graph, and serves it to AI clients and citizens. For a semi-technical
audience (engineers, technical PMs, stakeholders who read diagrams). Every box maps to a real
module; the diagrams were written against the code in `src/`, not just the high-level docs.

Core principle: **the `KnowledgeGraph` is the single source of truth.** Crawling produces it;
visualizations, navigation, and retrieval all read *from* it. Nothing downstream recomputes
relationships independently.

---

## 1. End-to-end pipeline (data flow)

Six phases turn raw agency websites into visualizations and a retrieval-ready graph. Each box
is a real module under `src/`; cylinders are generated artifacts (mostly gitignored).

```mermaid
flowchart TD
    REG[("agencies.md<br/><i>agency → URL → folder registry</i>")]
    CFG[("config.yaml<br/><i>crawl · chunk_size/overlap · viz</i>")]

    subgraph P1["Phase 1 · Crawl  (src/phase1_crawl)"]
        CR["crawler.py + extractors/<br/>html · pdf · docx"]
    end
    MD[("knowledge/{agency}/*.md<br/>markdown + frontmatter")]

    subgraph P2["Phase 2 · Knowledge  (src/phase2_knowledge)"]
        KB["knowledge_builder.py<br/>semantic_analyzer.py"]
    end

    BLD{{"src/network/3_build_network.py<br/><b>graph build orchestrator</b><br/>(see §2)"}}
    PKL[("src/network/exports/<br/>montana_knowledge.pkl + .json/.graphml<br/><b>KnowledgeGraph</b>")]

    subgraph P3["Phase 3 · Navigation  (src/phase3_navigation)"]
        NV["navigation_builder.py<br/>hierarchy_analyzer · mime_classifier"]
    end
    NAVJSON[("data/graphs/navigation/*.json")]

    subgraph VIZ["Phases 4–6 · Visualize  (src/phase4/5/6_viz_*)"]
        D3["knowledge_viz · navigation_viz<br/>dashboard_viz"]
    end
    HTML[("html/interactive-dashboard.html<br/>html/agency-data/{agency}.json")]

    REG --> CR
    CFG --> CR
    CR -->|"crawl + extract<br/>(.mt.gov only · rate-limited)"| MD
    MD --> KB --> BLD
    BLD --> PKL
    PKL --> NV --> NAVJSON
    PKL --> D3
    NAVJSON --> D3
    D3 --> HTML

    style PKL fill:#2d6cdf,color:#fff,stroke:#1a4ba0,stroke-width:3px
    style BLD fill:#fff4e6,stroke:#f59e0b,stroke-width:2px
```

**Data model (one agency → one graph):** one agency yields many markdown docs; those become a
single `KnowledgeGraph` where **nodes = documents** (`NodeMetadata`), **edges = relationships**
(`EdgeMetadata`), and **chunks = retrieval units** (`ContentChunk`).

---

## 2. The graph build orchestrator (`3_build_network.py`)

`scripts/run_all.py` and the per-phase CLIs drive things, but the graph itself is assembled by
`src/network/3_build_network.py`, which runs six internal steps (not to be confused with the
pipeline's phase1–6). `--quick` skips the expensive pairwise semantic-similarity edges.

```mermaid
flowchart LR
    A["knowledge/{agency}/*.md"]
    B["1 · GraphBuilder<br/>graph_builder.py<br/><i>markdown → nodes/edges/chunks</i>"]
    C["2 · SemanticEnhancer<br/>semantic_layer.py<br/><i>chunks + topic edges;<br/>similarity edges (skip if --quick)</i>"]
    D["3 · NetworkAnalyzer<br/>analyzer.py<br/><i>PageRank · centrality · communities</i>"]
    E["4 · GraphPersistence<br/>persistence.py<br/><i>save .pkl/.json/.graphml/chunks</i>"]
    F["5 · viz note (separate step)"]
    G["6 · RAG self-test<br/>GraphRAGRetriever.retrieve()"]
    PKL[("montana_knowledge.pkl")]

    A --> B --> C --> D --> E --> F --> G
    E --> PKL
    style PKL fill:#2d6cdf,color:#fff,stroke:#1a4ba0,stroke-width:2px
```

Node types and edge types come straight from `schema.py`:

- **`NodeType`** — `HTML_PAGE`, `PDF_DOCUMENT`, `DOCX_DOCUMENT`, `INDEX_PAGE`, `POLICY_PAGE`,
  `PROGRAM_PAGE`, `AGENCY_ROOT`, `TOPIC_CLUSTER`.
- **`EdgeType`** — `HYPERLINK`, `CITATION`, `PARENT_CHILD`, `SEMANTIC_SIMILAR`, `TOPIC_RELATED`,
  `SAME_AGENCY`, `BELONGS_TO_AGENCY`, `TEMPORAL`.

---

## 3. The data contract (`schema.py`)

`schema.py` is **the contract** — change a field here and the builder, retriever, visualizer,
and every consumer change with it. Note that the three retriever methods do **not** return the
same type.

```mermaid
classDiagram
    class KnowledgeGraph {
        +nodes: Dict[str, NodeMetadata]
        +edges: List[EdgeMetadata]
        +chunks: Dict[str, ContentChunk]
        +agency_index / type_index / topic_index
        +get_neighbors() get_by_agency() get_by_topic()
    }
    class NodeMetadata {
        +node_id (relative file path)
        +title, source_url, agency
        +NodeType node_type
        +topics, keywords, entities
        +pagerank_score, in_degree, out_degree
        +chunk_ids: List[str]
    }
    class EdgeMetadata {
        +source_id, target_id
        +EdgeType edge_type
        +weight, confidence
        +anchor_text, context
    }
    class ContentChunk {
        +chunk_id, document_id
        +content, chunk_index
        +section_title, chunk_type
        +embedding (optional, unused by retriever)
    }
    class RAGResult {
        +query, results: List[Dict]
        +total_found, search_strategy
        +execution_time_ms
        +expanded_nodes, path_to_results
    }

    KnowledgeGraph "1" *-- "many" NodeMetadata
    KnowledgeGraph "1" *-- "many" EdgeMetadata
    KnowledgeGraph "1" *-- "many" ContentChunk
    NodeMetadata "1" o-- "many" ContentChunk : chunk_ids
```

---

## 4. How retrieval actually works

`GraphRAGRetriever` (in `rag_retriever.py`) is **keyword + graph**, not vector search. At
construction it builds an inverted index over each node's keywords, topics, and title words.
A `retrieve()` call then:

```mermaid
flowchart TD
    Q["query string"]
    KW["keyword_search()<br/>inverted index → seed node_ids<br/>(normalized match counts)"]
    EX["expand_via_graph()<br/>BFS ≤ max_hops from seeds<br/>edge types: HYPERLINK,<br/>SEMANTIC_SIMILAR, TOPIC_RELATED<br/>score = parent · edge.weight · 0.5^hop"]
    COMB["combine scores<br/><b>0.7·keyword + 0.3·graph</b><br/>rank → top_k"]
    CH["get_chunks_for_nodes()<br/>attach ≤N chunks per doc"]
    R["RAGResult<br/>(search_strategy = hybrid_keyword_graph)"]

    Q --> KW --> EX --> COMB --> CH --> R
    style COMB fill:#fff4e6,stroke:#f59e0b
```

`strategy` can be `"keyword"`, `"graph"`, or `"hybrid"` (default). The three public methods:

| Method | Returns | Used by |
|--------|---------|---------|
| `retrieve(query, top_k, strategy=…)` | **`RAGResult`** | `search_agency_knowledge` (MCP), chat `synthesize()` |
| `search_by_agency(agency, query)` | **`List[Dict]`** | `search_by_agency` (MCP) |
| `get_document_context(node_id, hops)` | **`Dict`** (related-by-link/topic/agency) | `get_document_context` (MCP) |

---

## 5. Two surfaces, one retrieval core

Both surfaces import the same `get_retriever()` singleton (`src/chat_api/retrieval.py`), an
`@lru_cache(maxsize=1)` that loads `montana_knowledge.pkl` once and wraps it in a
`GraphRAGRetriever`. Retrieval logic lives only in `src/network/`. The **LLM is called in
exactly one place** — `src/chat_api/providers.py` — for synthesis only; the MCP server never
calls an LLM (it returns structured results for the *client's* model to use).

```mermaid
flowchart LR
    AICLIENT["🤖 AI client<br/>(Claude Desktop, …)"]
    BROWSER["🧑 Citizen browser"]

    subgraph MCP["MCP Server · src/mcp_server/server.py<br/>FastMCP over stdio (no LLM)"]
        T1["search_agency_knowledge"]
        T2["search_by_agency"]
        T3["get_document_context"]
    end

    subgraph CHAT["Chat API · src/chat_api (FastAPI :8001)"]
        EP["app.py<br/>POST /chat · GET /health<br/>(warms retriever on startup)"]
        ANS["answer.synthesize()"]
        PROV["providers.py<br/>CHAT_PROVIDER: perplexity(default) | anthropic"]
    end

    subgraph CORE["Shared retrieval core (src/network)"]
        GET["retrieval.get_retriever()<br/><i>lru_cache singleton</i>"]
        RET["GraphRAGRetriever"]
        PKL[("montana_knowledge.pkl")]
    end

    LLM["☁️ LLM provider<br/>(Perplexity Sonar / Claude)<br/><b>synthesis only</b>"]
    WIDGET["web/widget.js<br/>embeddable widget (data-api)"]

    AICLIENT -->|stdio| MCP
    BROWSER --> WIDGET -->|HTTP POST| EP --> ANS
    T1 & T2 & T3 --> GET
    ANS --> GET
    GET --> RET --> PKL
    RET -->|RAGResult / List / Dict| T1
    RET -->|RAGResult| ANS
    ANS --> PROV --> LLM -->|cited Markdown answer| ANS

    style CORE fill:#ecfdf5,stroke:#10b981
    style GET fill:#2d6cdf,color:#fff,stroke:#1a4ba0,stroke-width:2px
    style LLM fill:#faf5ff,stroke:#8b5cf6
```

| | MCP Server | Chat API |
|---|---|---|
| Transport | stdio (launched per AI client) | HTTP / FastAPI on :8001 |
| Consumer | AI assistants | Browser widget → citizens |
| LLM synthesis? | **No** — returns structured results | **Yes** — `providers.py` |
| Shared core | `get_retriever()` → `GraphRAGRetriever` over `montana_knowledge.pkl` | same |

---

## 6. Request lifecycle — a citizen question (`/chat`)

The chat path does real post-processing around the LLM call: it caps each source's text,
extracts a `<<FOLLOWUPS>>` block, strips citation markers that point past the source list, and
returns only the sources actually cited.

```mermaid
sequenceDiagram
    actor User as Citizen
    participant W as widget.js
    participant API as FastAPI /chat
    participant A as answer.synthesize()
    participant R as GraphRAGRetriever
    participant P as provider (LLM)

    User->>W: types a question
    W->>API: POST /chat {question, agency?}
    API->>A: synthesize(question, agency)
    A->>R: retrieve(question, return_chunks=True)
    R-->>A: RAGResult (ranked docs + chunks)
    Note over A: format_sources() — cap to top_k,<br/>≤1500 chars each, drop empty
    alt no usable sources
        A-->>API: honest "couldn't find" (no LLM call)
    else has sources
        A->>P: complete(system, grounded sources + question)
        P-->>A: Markdown answer + [n] cites + followups
        Note over A: split_followups() ·<br/>strip_invalid_citations() ·<br/>extract_cited()
        A-->>API: answer, citations, sources, followups
    end
    API-->>W: JSON
    W-->>User: rendered answer with citations
```

---

## Invariants worth remembering

- **Graph is source of truth** — change relationships in `graph_builder`/`semantic_layer`, then
  rebuild; never hand-patch downstream JSON/PKL.
- **`schema.py` is the contract** — change a field and all consumers together.
- **Two surfaces, one core** — never reimplement retrieval in a surface; keep it in `src/network/`.
- **Retrieval is keyword + graph BFS**, not embeddings — `ContentChunk.embedding` exists but the
  retriever doesn't use it. (A future vector layer would slot in here.)
- **One place calls the LLM** — `src/chat_api/providers.py`, synthesis only; swap via `CHAT_PROVIDER`.
- **Crawl safety** — `.mt.gov` hosts only, honor `config.yaml` rate limits; prefer `--dry-run` / `--update-only`.
