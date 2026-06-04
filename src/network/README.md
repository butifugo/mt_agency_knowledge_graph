# Network Directory - Knowledge Graph System

A comprehensive document network system for AI RAG (Retrieval-Augmented Generation) and interactive visualization of Montana State Government knowledge base.

## 📋 Overview

The `src/network/` directory contains all components for building, analyzing, and querying the Montana State Government knowledge graph. This system transforms thousands of government documents into an intelligent, interconnected network optimized for AI applications.

### Purpose
- **AI/RAG Systems**: Graph-enhanced retrieval with semantic search and context expansion
- **Interactive Visualization**: D3.js-powered network exploration
- **Network Analysis**: PageRank, centrality metrics, and community detection
- **Multi-Format Export**: JSON, GraphML, and Pickle formats for external tools

### Key Statistics
- **Documents**: 7,586+ nodes (HTML pages, PDFs, DOCX files)
- **Relationships**: 140,526+ edges (hyperlinks, semantic similarity, topics, hierarchy)
- **Content Chunks**: 330,484+ semantic chunks for RAG
- **Agencies**: 9+ Montana state agencies
- **Network Density**: Highly connected with avg clustering coefficient of 0.65

## 📁 Directory Structure

```
network/
├── README.md                          # This file (network system documentation)
├── __init__.py                        # Package initialization
│
├── schema.py                          # Data model definitions
├── graph_builder.py                   # Phase 1: Build document graph
├── semantic_layer.py                  # Phase 2: Add semantic similarity
├── persistence.py                     # Phase 3: Save/load graph
├── analyzer.py                        # Phase 4: Network analysis
├── rag_retriever.py                   # Phase 5: RAG retrieval system
│
└── exports/                           # Generated graph files
    ├── montana_knowledge.pkl          # Full graph (pickle format)
    ├── montana_knowledge.json         # Graph data (JSON format)
    ├── montana_knowledge.graphml      # Graph (GraphML format)
    ├── content_chunks.json            # RAG chunks
    └── analysis_results.json          # Network metrics
```

## 🚀 Quick Start

### Build the Complete Network

```bash
# From project root directory
# Full build (includes all phases)
python src/network/build_network.py

# Quick build (skip expensive semantic similarity)
python src/network/build_network.py --quick

# Load existing graph and visualize
python src/network/build_network.py --load-existing
```

### View the Interactive Visualization

```bash
# Open in default browser
open html/montana_network_interactive.html
```

## 📊 System Architecture

## 📊 System Architecture

### Pipeline Overview

The knowledge graph is built through a 5-phase pipeline orchestrated by `src/network/3_build_network.py`:

```
Phase 1: Graph Builder      → Build base document graph
Phase 2: Semantic Layer      → Add semantic relationships
Phase 3: Persistence         → Save graph to disk
Phase 4: Network Analysis    → Compute metrics
Phase 5: RAG Retriever       → Setup retrieval system
```

Note: Interactive visualizations are generated separately using `src/viz/agency_network_viz.py`

### Phase Details

### 1. **Data Model** (`src/network/schema.py`)

Defines the complete graph structure:

- **Nodes**: Documents with metadata (title, agency, type, keywords, topics)
- **Edges**: Relationships (hyperlinks, semantic similarity, topics, hierarchy)
- **Chunks**: Content chunks for RAG retrieval
- **Metrics**: PageRank, betweenness centrality, degree statistics

### 2. **Graph Builder** (`src/network/graph_builder.py`)

**Phase 1**: Core network construction

- Discovers all markdown files dynamically (no hardcoding)
- Extracts metadata, links, keywords, and topics
- Creates multiple relationship layers:
  - **Hyperlinks**: Direct links between documents
  - **Hierarchy**: Parent-child relationships
  - **Agency**: Co-membership within agencies

**Output**: Base graph with ~48,000 relationships

### 3. **Semantic Layer** (`network/semantic_layer.py`)

**Phase 2**: Semantic enhancement

- **Content Chunking**: Splits documents into 512-char semantic chunks (330K+ chunks)
- **Topic Extraction**: Identifies shared topics (employment, benefits, policy, etc.)
- **Topic Relationships**: Connects documents with shared topics (~92K edges)
- **Semantic Similarity**: (Optional) Embedding-based similarity edges

**Output**: Enhanced graph with ~140K relationships

### 4. **Network Analysis** (`network/analyzer.py`)

**Phase 3**: Compute graph metrics

- **PageRank**: Document importance scoring
- **Betweenness Centrality**: Bridge documents in the network
- **Community Detection**: Topic/agency clusters
- **Hubs & Authorities**: HITS algorithm
- **Agency Statistics**: Per-agency analytics

**Insights**:
- Most important docs: Index pages, policy documents
- Key hubs: Cross-agency reference documents
- Communities: Topic-based clusters

### 5. **Persistence** (`network/persistence.py`)

**Phase 4**: Multi-format export

- **JSON**: Human-readable, for web visualization (44 MB)
- **GraphML**: For Gephi, Cytoscape analysis (23 MB)
- **Pickle**: Complete Python object with all data (365 MB)
- **Chunks JSON**: Content chunks for RAG (388 MB)

### 6. **RAG Retrieval** (`network/rag_retriever.py`)

**Phase 5**: Graph-enhanced retrieval

**Retrieval Strategies**:
1. **Keyword Search**: Inverted index on titles, topics, keywords
2. **Graph Expansion**: BFS traversal from matched documents (1-2 hops)
3. **Hybrid**: Combine keyword + graph scores

**Features**:
- Context window optimization
- Multi-hop reasoning
- Agency-filtered search
- Document context retrieval

**Example**:
```python
from network.rag_retriever import GraphRAGRetriever
from network.persistence import GraphPersistence

# Load graph
persistence = GraphPersistence()
graph = persistence.load_pickle("network/exports/montana_knowledge.pkl")

# Create retriever
retriever = GraphRAGRetriever(graph)

# Search
result = retriever.retrieve(
    query="employee benefits and health insurance",
    top_k=10,
    expand_graph=True,
    max_hops=2,
    return_chunks=True,
    strategy="hybrid"
)

# Access results
for doc in result.results:
    print(f"{doc['title']} ({doc['agency']})")
    for chunk in doc['chunks']:
        print(f"  - {chunk['content'][:100]}...")
```

---

## 📊 Interactive Visualizations

For interactive D3.js network visualizations, use the separate visualization tool:

```bash
# Generate agency network visualization
python src/viz/agency_network_viz.py
```

**Features**:
- Agency selector with on-demand data loading
- Force-directed graph layout
- Zoom, pan, drag nodes
- Navigation pages highlighted
- Color-coded by document type
- Click nodes to view details
- External agency connections
- Responsive design

See `src/viz/README.md` for more details.

---

## 🔧 Module Reference

### 1. schema.py - Data Model Definitions

Defines the complete knowledge graph data structure.

**Key Classes**:
- `KnowledgeGraph`: Main graph container
- `NodeMetadata`: Document node properties
- `EdgeMetadata`: Relationship properties
- `ContentChunk`: RAG content chunks
- `NodeType`: Enum (DOCUMENT, TOPIC, AGENCY)
- `EdgeType`: Enum (HYPERLINK, SEMANTIC, TOPIC, HIERARCHY, AGENCY)

**Usage**:
```python
from network.schema import KnowledgeGraph, NodeType, EdgeType

graph = KnowledgeGraph()
# Access nodes, edges, chunks, metrics
```

### 2. graph_builder.py - Phase 1: Document Graph

Builds the base knowledge graph from markdown files.

**Features**:
- Auto-discovers all markdown files in `knowledge/`
- Extracts metadata from YAML frontmatter
- Creates hyperlink edges between documents
- Builds hierarchy and agency relationships
- Extracts keywords and topics

**Usage**:
```python
from network.graph_builder import GraphBuilder

builder = GraphBuilder(knowledge_dir="knowledge")
graph = builder.build_graph(verbose=True)
```

**Output**: Base graph with ~48,000 relationships

### 3. semantic_layer.py - Phase 2: Semantic Enhancement

Adds semantic relationships and content chunking.

**Features**:
- **Content Chunking**: Splits documents into 512-char semantic chunks
- **Topic Extraction**: Identifies shared topics across documents
- **Topic Relationships**: Connects documents with shared topics
- **Semantic Similarity**: (Optional) Embedding-based similarity edges

**Usage**:
```python
from network.semantic_layer import SemanticEnhancer

enhancer = SemanticEnhancer(graph, knowledge_dir="knowledge")
graph = enhancer.enhance_graph(
    create_chunks_flag=True,
    add_topic_edges_flag=True,
    add_semantic_edges_flag=False  # Expensive
)
```

**Output**: Enhanced graph with ~140,526 relationships, 330,484+ chunks

### 4. analyzer.py - Phase 4: Network Analysis

Computes graph metrics and statistics.

**Metrics Computed**:
- PageRank (document importance)
- Betweenness centrality (bridge documents)
- Degree centrality (connectivity)
- HITS algorithm (hubs & authorities)
- Community detection (topic clusters)
- Agency statistics

**Usage**:
```python
from network.analyzer import NetworkAnalyzer

analyzer = NetworkAnalyzer(graph)
results = analyzer.analyze_all(verbose=True)

# Get important documents
important_docs = analyzer.get_most_important_documents(top_n=20)

# Get agency statistics
agency_stats = analyzer.get_agency_statistics()

# Get communities
communities = analyzer.detect_communities()
```

**Output**: Analysis results stored in graph metrics

### 5. persistence.py - Phase 3: Save/Load Graph

Multi-format export and import.

**Formats**:
- **Pickle**: Complete Python object (365 MB)
- **JSON**: Human-readable, web-friendly (44 MB)
- **GraphML**: For Gephi/Cytoscape (23 MB)
- **Chunks JSON**: RAG content chunks (388 MB)

**Usage**:
```python
from network.persistence import GraphPersistence

persistence = GraphPersistence(output_dir="network/exports")

# Save all formats
persistence.save_all(graph, prefix="montana_knowledge")

# Load specific format
graph = persistence.load_pickle("montana_knowledge.pkl")
json_data = persistence.load_json("montana_knowledge.json")
```

**Output**: Files in `network/exports/`

### 6. rag_retriever.py - Phase 6: RAG Retrieval System

Graph-enhanced document retrieval for AI/RAG.

**Retrieval Strategies**:
1. **Keyword Search**: Inverted index on titles, topics, keywords
2. **Graph Expansion**: BFS traversal from matched documents (1-2 hops)
3. **Hybrid**: Combine keyword + graph scores

**Features**:
- Context window optimization
- Multi-hop reasoning
- Agency-filtered search
- Document context retrieval
- Chunk-level retrieval

**Usage**:
```python
from network.rag_retriever import GraphRAGRetriever

retriever = GraphRAGRetriever(graph)

# Basic search
result = retriever.retrieve(
    query="employee benefits health insurance",
    top_k=10,
    expand_graph=True,
    max_hops=2,
    return_chunks=True,
    strategy="hybrid"
)

# Agency-specific search
agency_results = retriever.search_by_agency(
    agency="human-resources",
    query="hiring policies",
    top_k=5
)

# Get document context
context = retriever.get_document_context(
    node_id="human-resources/index",
    context_hops=2,
    include_chunks=True
)
```

**Output**: Ranked documents with chunks, scores, and metadata

---

## 📈 Network Properties

### Node Statistics
- **Total Documents**: 7,586+
- **HTML Pages**: ~1,064
- **PDF Documents**: ~5,872
- **DOCX Documents**: ~285
- **Index Pages**: ~123
- **Policy Pages**: ~5
- **Program Pages**: ~237

### Edge Statistics
- **Total Relationships**: 140,526+
- **Hyperlinks**: ~2,688 (direct links between pages)
- **Parent-Child**: ~7,577 (hierarchical relationships)
- **Same Agency**: ~37,795 (co-membership edges)
- **Topic Related**: ~92,466 (shared topic connections)

### Graph Metrics
- **Density**: 0.0011 (sparse, focused connections)
- **Clustering Coefficient**: 0.65 (highly clustered communities)
- **Connected Components**: 1 (fully connected graph)
- **Average Path Length**: ~8-10 hops (small-world property)
- **PageRank Distribution**: Power law (few highly important docs)

## 🎯 Use Cases

### 1. AI Chatbot with RAG

Build an AI chatbot that answers questions about Montana government services:

```python
from network.rag_retriever import GraphRAGRetriever
from network.persistence import GraphPersistence

# Load graph
persistence = GraphPersistence()
graph = persistence.load_pickle("network/exports/montana_knowledge.pkl")
retriever = GraphRAGRetriever(graph)

# User asks a question
user_question = "What are the employee leave policies in Montana?"

# Retrieve relevant documents + context
result = retriever.retrieve(
    query=user_question,
    top_k=5,
    expand_graph=True,
    return_chunks=True,
    strategy="hybrid"
)

# Extract content chunks for LLM context
context = "\n\n".join([
    f"[{doc['title']}]\n{chunk['content']}"
    for doc in result.results 
    for chunk in doc['chunks'][:3]  # Top 3 chunks per doc
])

# Send to LLM (e.g., GPT-4, Claude)
response = llm.generate(
    f"Context:\n{context}\n\nQuestion: {user_question}\n\nAnswer:"
)
```

### 2. Document Discovery & Exploration

Find related documents and explore connections:

```python
from network.rag_retriever import GraphRAGRetriever

# Find documents similar to a known document
context = retriever.get_document_context(
    node_id="human-resources/employee-handbook",
    context_hops=2,
    include_chunks=False
)

# Access related documents
print(f"Connected via hyperlinks: {len(context['neighbors'])}")
print(f"Related by topic: {len(context['related_by_topic'])}")
print(f"Same agency: {len(context['same_agency'])}")

# Get specific relationships
for neighbor in context['neighbors'][:5]:
    print(f"  → {neighbor['title']} (link: {neighbor['edge_type']})")
```

### 3. Agency-Specific Analysis

Analyze content and structure for a specific agency:

```python
from network.analyzer import NetworkAnalyzer

analyzer = NetworkAnalyzer(graph)

# Get agency statistics
agency_stats = analyzer.get_agency_statistics()
hr_stats = agency_stats['human-resources']

print(f"Human Resources Department:")
print(f"  Documents: {hr_stats['total_documents']}")
print(f"  Average PageRank: {hr_stats['avg_pagerank']:.4f}")
print(f"  Top Topics: {', '.join(hr_stats['top_topics'][:5])}")
print(f"  Most Important Doc: {hr_stats['most_important_doc']['title']}")

# Search within agency only
hr_results = retriever.search_by_agency(
    agency="human-resources",
    query="hiring process recruitment",
    top_k=10
)
```

### 4. Network Visualization & Exploration

Create and explore interactive visualizations:

```bash
# Generate agency network visualization
python src/viz/agency_network_viz.py

# Open in browser
open html/agency-navigation.html
```

See `src/viz/README.md` for visualization options.

# Open in browser
import webbrowser
webbrowser.open(viz_path)
```

**Visualization Features**:
- Click nodes to open source URLs
- Hover for document metadata
- Filter by agency or document type
- Search for specific documents
- Zoom and pan to explore clusters
- Color-coded by agency

### 5. Cross-Agency Research

Find information spanning multiple agencies:

```python
# Search across all agencies
result = retriever.retrieve(
    query="environmental regulations for businesses",
    top_k=15,
    expand_graph=True,
    max_hops=2
)

# Group results by agency
by_agency = {}
for doc in result.results:
    agency = doc.get('agency', 'unknown')
    if agency not in by_agency:
        by_agency[agency] = []
    by_agency[agency].append(doc)

# Show coverage
for agency, docs in by_agency.items():
    print(f"{agency}: {len(docs)} relevant documents")
```

## ⚡ Performance

### Build Times (7,586 documents)
- **Phase 1** (Graph Build): ~60 seconds
- **Phase 2** (Semantic Layer): ~90 seconds (quick) / ~15 minutes (with embeddings)
- **Phase 3** (Persistence): ~30 seconds
- **Phase 4** (Analysis): ~45 seconds
- **Phase 5** (D3 Visualization): ~5 seconds
- **Phase 6** (RAG Setup): ~10 seconds

**Total Build Time**:
- Quick Mode: ~3-4 minutes
- Full Build (with embeddings): ~20 minutes

### Memory Requirements
- **Graph in Memory**: ~500 MB
- **Peak Memory**: ~2 GB (during embedding computation)
- **Disk Storage**: ~850 MB (all export formats)

### Query Performance
- **Keyword Search**: <100ms for top-10 results
- **Graph Expansion (2 hops)**: <500ms
- **Hybrid Retrieval**: <1 second
- **Document Context**: <200ms

## 🔧 Configuration & Customization

### Adjust Chunk Size

```python
from network.semantic_layer import SemanticEnhancer

enhancer = SemanticEnhancer(graph)
graph = enhancer.enhance_graph(
    create_chunks_flag=True,
    chunk_size=1024  # Larger chunks (default: 512)
)
```

### Filter by Document Type

```python
# Only retrieve PDF documents
result = retriever.retrieve(
    query="safety regulations",
    top_k=10,
    doc_type_filter="pdf_document"
)
```

### Custom Visualization

```bash
# Generate visualization for specific agencies
python src/viz/4_agency_network_viz.py --max-nodes 200

# View generated HTML files
open html/agency-navigation.html
```

### Export for External Tools

```python
# Export to GraphML for Gephi
persistence = GraphPersistence()
persistence.save_graphml(graph, "my_network.graphml")

# Export to JSON for custom web app
persistence.save_json(graph, "my_network.json")
```

## 🐛 Troubleshooting

### Issue: Out of Memory During Build

**Solution**: Use quick mode to skip semantic embeddings
```bash
python src/network/build_network.py --quick
```

### Issue: Slow RAG Queries

**Solution**: Reduce expansion hops or top_k
```python
result = retriever.retrieve(query, top_k=5, max_hops=1)
```

### Issue: Visualization Too Dense

**Solution**: Reduce max_nodes
```python
visualizer.generate_force_directed_graph(max_nodes=300)
```

### Issue: Missing Exports Directory

**Solution**: Create directory manually
```bash
mkdir -p network/exports network/visualizations
```

## 🔗 Related Documentation

- **`../../README.md`** - Master project documentation
- **`../../knowledge/README.md`** - Source content structure
- **`build_network.py`** - Main pipeline script
- **`../viz/README.md`** - Visualization tools

## 📊 File Formats

### Pickle Format (.pkl)
- **Size**: ~365 MB
- **Use**: Python applications, complete graph with all data
- **Load**: `pickle.load()` or `GraphPersistence.load_pickle()`

### JSON Format (.json)
- **Size**: ~44 MB
- **Use**: Web applications, data inspection, custom tools
- **Load**: `json.load()` or `GraphPersistence.load_json()`

### GraphML Format (.graphml)
- **Size**: ~23 MB
- **Use**: Gephi, Cytoscape, network analysis software
- **Load**: Use external tools (Gephi, NetworkX)

### Chunks JSON (.json)
- **Size**: ~388 MB
- **Use**: RAG systems, search indexes, content analysis
- **Structure**: Array of chunk objects with metadata

## 📝 Development Notes

### Adding New Phases

To add a new processing phase:

1. Create module in `network/` (e.g., `my_phase.py`)
2. Implement processing logic
3. Add to `build_network.py` pipeline
4. Update this README

### Extending Data Model

To add new node/edge types:

1. Update `NodeType` or `EdgeType` enum in `schema.py`
2. Modify `graph_builder.py` to create new types
3. Update visualization colors in `src/viz/4_agency_network_viz.py`
4. Rebuild graph with `python src/network/3_build_network.py`

### Custom Retrieval Strategies

To implement custom retrieval:

1. Subclass or modify `GraphRAGRetriever`
2. Add new strategy to `retrieve()` method
3. Test with sample queries
4. Document in this README

## 📄 License & Attribution

This network system is built on content from Montana State Government websites. All content is public domain. The graph structure and code are maintained by Montana State Government IT.

---

**Directory Purpose**: Knowledge graph construction and analysis  
**Primary Use**: AI/RAG systems, network visualization, document retrieval  
**Maintained By**: Montana State Government  
**Last Updated**: December 2025

### Retrieval Performance
- Keyword search: ~10-20ms
- Hybrid (keyword + graph): ~100-150ms
- Query with chunks: ~200-300ms

### Memory Usage
- Graph in memory: ~400 MB
- With all chunks: ~2 GB
- Visualization: Handles 1,000 nodes smoothly in browser

---

## 🛠️ Advanced Configuration

### Custom Chunking
```python
enhancer = SemanticEnhancer(graph)
chunks = enhancer.chunk_content(
    content=document_text,
    node_id="agency/doc",
    chunk_size=512  # Adjust chunk size
)
```

### Custom Similarity Threshold
```python
enhancer.add_semantic_edges(
    similarity_threshold=0.5,  # Higher = stricter
    max_edges_per_node=5
)
```

### Visualization Customization
```python
visualizer.generate_force_directed_graph(
    max_nodes=500,  # Fewer nodes for faster rendering
    include_edge_types=[EdgeType.HYPERLINK, EdgeType.TOPIC_RELATED]
)
```

---

## 📊 Export to External Tools

### Gephi (Network Analysis)
1. Open `network/exports/montana_knowledge.graphml` in Gephi
2. Run layout algorithms (Force Atlas 2, Fruchterman-Reingold)
3. Color nodes by agency or document type
4. Detect communities (Modularity)
5. Calculate additional centrality metrics

### Cytoscape (Biological Networks Style)
1. Import GraphML file
2. Apply network layouts
3. Style nodes/edges
4. Export publication-quality images

### Neo4j (Graph Database)
```python
# Convert to Cypher queries for Neo4j import
# (Custom export script can be added)
```

---

## 🐛 Troubleshooting

### Out of Memory
- Use `--quick` mode to skip semantic embeddings
- Reduce `max_nodes` in visualization
- Process agencies separately

### Slow Performance
- Ensure scipy is installed for fast PageRank
- Use pickle format (fastest load)
- Limit graph expansion hops to 1-2

### Missing Dependencies
```bash
pip install -r requirements.txt
```

---

## 📝 License

This project is part of the Montana State Government Knowledge Base system.

---

## 🤝 Contributing

The system is designed to be:
- **Fully Dynamic**: No hardcoded paths or agency names
- **Extensible**: Easy to add new relationship types
- **Modular**: Each phase can be run independently

To add new features:
1. Extend `schema.py` for new node/edge types
2. Add processing in appropriate module
3. Update persistence to save new data
4. Enhance visualization if needed

---

## 🔮 Future Enhancements

1. **Real Embeddings**: Replace simple embeddings with OpenAI/sentence-transformers
2. **Temporal Analysis**: Track document changes over time
3. **Entity Recognition**: Extract and link people, places, organizations
4. **Multi-Modal**: Include images, tables as separate nodes
5. **Recommendation Engine**: "Documents you might like"
6. **API Server**: REST API for network queries
7. **Incremental Updates**: Add new documents without full rebuild

---

**Built with ❤️ for Montana State Government**
