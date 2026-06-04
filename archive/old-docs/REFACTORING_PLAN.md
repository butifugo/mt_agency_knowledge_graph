# Montana State Government Knowledge Network - Refactoring Plan

**Date:** December 8, 2025  
**Purpose:** Restructure project into modular, maintainable components with clear execution pipelines

---

## 📋 Executive Summary

This refactoring plan reorganizes the Montana State Government Knowledge Network project into 6 distinct phases, each with dedicated scripts and clear interfaces. The goal is to create a modular, maintainable system where each component can run independently or as part of a complete pipeline.

### Current State Analysis

**Strengths:**
- Comprehensive crawling system with PDF/DOCX support
- Robust knowledge graph building with semantic analysis
- Working visualization components
- Good documentation structure

**Issues:**
- Mixed concerns (crawler has both extraction and navigation network logic)
- Unclear separation between knowledge graph and navigation graph
- No unified CLI for running all agencies
- Visualization scripts scattered and not clearly numbered
- Missing final comprehensive visualization with filters

---

## 🎯 Target Architecture

```
hr knowledge/
├── src/
│   ├── 1_crawl/              # Phase 1: Web Crawling & Extraction
│   ├── 2_knowledge/          # Phase 2: Knowledge Document Network
│   ├── 3_navigation/         # Phase 3: Webpage Navigation Network
│   ├── 4_viz_knowledge/      # Phase 4: Knowledge Network Visualization
│   ├── 5_viz_navigation/     # Phase 5: Navigation Visualization
│   ├── 6_viz_interactive/    # Phase 6: Interactive Multi-Agency Viz
│   └── shared/               # Shared utilities and schemas
├── data/
│   ├── knowledge/            # Crawled markdown content
│   ├── graphs/               # Generated network graphs
│   ├── navigation/           # Navigation network data
│   └── html/                 # Generated visualizations
├── scripts/
│   ├── run_all.py           # Master orchestrator
│   ├── run_phase.py         # Individual phase runner
│   └── config.yaml          # Configuration
└── docs/
    ├── ARCHITECTURE.md       # System architecture
    ├── API.md               # API documentation
    └── USAGE.md             # Usage guide
```

---

## 📦 Phase Breakdown

### Phase 1: Web Crawling & Content Extraction
**Location:** `src/1_crawl/`  
**Purpose:** Extract and convert website content to markdown

#### Components:
```
src/1_crawl/
├── __init__.py
├── crawler.py              # Core crawler engine (from crawler_1.py)
├── extractors/
│   ├── __init__.py
│   ├── html_extractor.py   # HTML to markdown conversion
│   ├── pdf_extractor.py    # PDF text extraction
│   └── docx_extractor.py   # DOCX text extraction
├── cli.py                  # Command-line interface
└── README.md
```

#### Functionality:
- **Input:** `agencies.md` file with agency list
- **Output:** 
  - Markdown files in `data/knowledge/{agency}/`
  - Basic metadata (source URL, title, timestamp, type)
  - Content type classification (HTML, PDF, DOCX)

#### CLI Interface:
```bash
# Run all agencies
python -m src.1_crawl.cli --all

# Run specific agency
python -m src.1_crawl.cli --agency agriculture

# Run multiple agencies
python -m src.1_crawl.cli --agency agriculture,commerce,human-resources

# Dry run (show what would be crawled)
python -m src.1_crawl.cli --all --dry-run

# Update only (skip existing files)
python -m src.1_crawl.cli --all --update-only
```

#### Key Features:
- Respect robots.txt
- Rate limiting (configurable delay)
- Resume capability (track visited URLs)
- Error handling and retry logic
- Progress reporting
- **NO navigation network building** (moved to Phase 3)

---

### Phase 2: Knowledge Document Network
**Location:** `src/2_knowledge/`  
**Purpose:** Build recursive document knowledge graph with semantic relationships

#### Components:
```
src/2_knowledge/
├── __init__.py
├── graph_builder.py        # Core graph construction
├── semantic_analyzer.py    # Semantic similarity & clustering
├── topic_extractor.py      # Topic/keyword extraction
├── rag_chunker.py         # Content chunking for RAG
├── persistence.py         # Save/load graph
├── cli.py                 # Command-line interface
└── README.md
```

#### Functionality:
- **Input:** Markdown files from `data/knowledge/`
- **Output:**
  - Knowledge graph (pickle, JSON, GraphML)
  - Content chunks for RAG
  - Network analysis metrics
  - Topic clusters

#### Graph Structure:
- **Nodes:** All documents (HTML, PDF, DOCX)
- **Edges:**
  - Document citations/references
  - Semantic similarity
  - Topic relationships
  - Agency relationships
  - Hierarchical relationships (inferred from content)

#### CLI Interface:
```bash
# Build complete knowledge network
python -m src.2_knowledge.cli --build

# Quick build (skip expensive operations)
python -m src.2_knowledge.cli --build --quick

# Build for specific agencies
python -m src.2_knowledge.cli --build --agencies agriculture,commerce

# Load and analyze existing graph
python -m src.2_knowledge.cli --analyze

# Export to specific format
python -m src.2_knowledge.cli --export --format graphml
```

#### Key Features:
- Semantic similarity using TF-IDF or embeddings
- Topic modeling (LDA, keyword extraction)
- PageRank and centrality metrics
- Community detection
- RAG-optimized content chunking
- Incremental updates (add new documents without rebuild)

---

### Phase 3: Webpage Navigation Network
**Location:** `src/3_navigation/`  
**Purpose:** Build webpage-centric navigation graph with MIME type hierarchy

#### Components:
```
src/3_navigation/
├── __init__.py
├── navigation_builder.py   # Build navigation graph
├── hierarchy_analyzer.py   # Detect page hierarchies
├── mime_classifier.py      # Classify by MIME type
├── cli.py                 # Command-line interface
└── README.md
```

#### Functionality:
- **Input:** 
  - Markdown files from `data/knowledge/`
  - Link data extracted during crawling
- **Output:**
  - Navigation graph (JSON per agency)
  - Hierarchical structure with MIME types
  - Page navigation paths

#### Graph Structure:
- **Primary Nodes:** HTML pages (mime: text/html)
- **Child Nodes:** PDF and DOCX files linked from HTML pages
- **Edges:**
  - Hyperlinks (HTML → HTML)
  - Document links (HTML → PDF/DOCX)
  - Parent-child relationships
  - Breadcrumb paths

#### Hierarchy Rules:
1. **Root:** Agency homepage (index.html)
2. **Level 1:** Main section pages (directly linked from homepage)
3. **Level 2+:** Subsection pages
4. **Leaf Nodes:** PDF/DOCX documents (children of HTML pages)

#### CLI Interface:
```bash
# Build navigation network for all agencies
python -m src.3_navigation.cli --build-all

# Build for specific agency
python -m src.3_navigation.cli --build --agency agriculture

# Analyze navigation structure
python -m src.3_navigation.cli --analyze --agency agriculture

# Export navigation graph
python -m src.3_navigation.cli --export --agency agriculture --format json
```

#### Output Format (per agency):
```json
{
  "agency": "agriculture",
  "metadata": {
    "total_pages": 150,
    "total_documents": 75,
    "max_depth": 5
  },
  "nodes": {
    "url_hash": {
      "url": "https://agr.mt.gov/...",
      "title": "Page Title",
      "type": "html_page|pdf_document|docx_document",
      "mime_type": "text/html|application/pdf|application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "level": 0,
      "file_path": "knowledge/agriculture/page.md",
      "parent": "parent_url_hash"
    }
  },
  "edges": [
    {
      "source": "source_url_hash",
      "target": "target_url_hash",
      "link_text": "Click here",
      "type": "hyperlink|document_link"
    }
  ]
}
```

---

### Phase 4: Knowledge Network Visualization
**Location:** `src/4_viz_knowledge/`  
**Purpose:** Interactive visualization of knowledge graph

#### Components:
```
src/4_viz_knowledge/
├── __init__.py
├── graph_renderer.py       # D3.js graph generation
├── templates/
│   └── knowledge_graph.html # HTML template
├── cli.py                 # Command-line interface
└── README.md
```

#### Functionality:
- **Input:** Knowledge graph from Phase 2
- **Output:** Interactive HTML visualization

#### Features:
- Force-directed graph layout
- Node coloring by:
  - Agency
  - Document type (HTML, PDF, DOCX)
  - Topic cluster
  - PageRank score
- Edge visualization:
  - Hyperlinks
  - Semantic similarity
  - Topic relationships
- Interactive controls:
  - Zoom/pan
  - Node filtering
  - Search
  - Tooltip with metadata

#### CLI Interface:
```bash
# Generate knowledge graph visualization
python -m src.4_viz_knowledge.cli --generate

# Generate for specific agencies
python -m src.4_viz_knowledge.cli --generate --agencies agriculture,commerce

# Custom output location
python -m src.4_viz_knowledge.cli --generate --output data/html/knowledge.html
```

---

### Phase 5: Navigation Visualization
**Location:** `src/5_viz_navigation/`  
**Purpose:** Website navigation tree visualization

#### Components:
```
src/5_viz_navigation/
├── __init__.py
├── tree_renderer.py        # Tree layout generation
├── templates/
│   └── navigation_tree.html # HTML template
├── cli.py                 # Command-line interface
└── README.md
```

#### Functionality:
- **Input:** Navigation graph from Phase 3
- **Output:** Interactive HTML tree visualization

#### Features:
- Hierarchical tree layout (top-down or radial)
- Node styling:
  - HTML pages: Blue border/fill
  - PDF documents: Red icon
  - DOCX documents: Green icon
- Interactive controls:
  - Expand/collapse branches
  - Zoom/pan
  - Breadcrumb navigation
  - Search by page title
- MIME type filtering:
  - Show only HTML pages
  - Show all documents

#### CLI Interface:
```bash
# Generate navigation visualization
python -m src.5_viz_navigation.cli --generate --agency agriculture

# Generate for all agencies
python -m src.5_viz_navigation.cli --generate-all

# Custom layout (tree vs radial)
python -m src.5_viz_navigation.cli --generate --agency agriculture --layout radial
```

---

### Phase 6: Interactive Multi-Agency Visualization
**Location:** `src/6_viz_interactive/`  
**Purpose:** Comprehensive interactive visualization with agency selection and network filtering

#### Components:
```
src/6_viz_interactive/
├── __init__.py
├── multi_agency_renderer.py # Multi-agency graph renderer
├── network_simplifier.py    # Network complexity reduction
├── templates/
│   └── interactive_network.html # HTML template
├── cli.py                   # Command-line interface
└── README.md
```

#### Functionality:
- **Input:** 
  - Knowledge graphs from Phase 2
  - Navigation graphs from Phase 3
- **Output:** Unified interactive HTML visualization

#### Features:

##### 1. Agency Selection
- Dropdown menu to select agencies
- Multi-select capability (show multiple agencies)
- "Select All" / "Deselect All" buttons
- Agency statistics display

##### 2. Network Filters
- **Document Type Filter:**
  - HTML pages only
  - Include PDFs
  - Include DOCX
  - All types

- **Relationship Filter:**
  - Hyperlinks only
  - Semantic relationships
  - Topic relationships
  - All relationships

- **Complexity Reduction:**
  - Slider: Show top N% nodes by PageRank
  - Slider: Minimum edge weight threshold
  - Toggle: Hide isolated nodes
  - Button: Show only navigation backbone (HTML pages with high betweenness)

##### 3. Visual Controls
- **Layout:**
  - Force-directed
  - Hierarchical
  - Circular
  - Grid

- **Coloring:**
  - By agency
  - By document type
  - By topic cluster
  - By PageRank score

- **Node Sizing:**
  - Uniform
  - By PageRank
  - By in-degree
  - By out-degree

##### 4. Interactive Features
- Click node → Show metadata panel
- Double-click node → Open document
- Hover → Show tooltip with title and metrics
- Right-click → Context menu (expand neighbors, focus, hide)
- Search bar with autocomplete
- Breadcrumb trail for navigation

##### 5. Network Statistics Panel
- Total nodes/edges
- Average degree
- Clustering coefficient
- Network diameter
- Top 10 nodes by PageRank
- Top 10 nodes by centrality

#### CLI Interface:
```bash
# Generate interactive visualization
python -m src.6_viz_interactive.cli --generate

# Include specific agencies
python -m src.6_viz_interactive.cli --generate --agencies agriculture,commerce,human-resources

# Custom output
python -m src.6_viz_interactive.cli --generate --output data/html/interactive.html

# With network simplification preset
python -m src.6_viz_interactive.cli --generate --preset minimal  # Top 100 nodes only
```

---

## 🔧 Shared Components

### Location: `src/shared/`

#### Components:
```
src/shared/
├── __init__.py
├── schemas.py             # Data models (NodeMetadata, EdgeMetadata, etc.)
├── constants.py           # Constants and enums
├── utils.py              # Common utilities
├── config.py             # Configuration management
└── logging.py            # Logging setup
```

#### Key Schemas:

##### Document Schema
```python
@dataclass
class Document:
    id: str                    # Unique identifier
    url: str                   # Source URL
    title: str                 # Document title
    content: str               # Full text content
    mime_type: str             # MIME type
    file_path: str             # Local file path
    agency: str                # Agency name
    crawled_date: datetime     # When crawled
    word_count: int            # Word count
    metadata: Dict[str, Any]   # Additional metadata
```

##### Knowledge Graph Schema
```python
@dataclass
class KnowledgeNode:
    id: str
    document: Document
    topics: List[str]
    keywords: List[str]
    embeddings: Optional[np.ndarray]
    pagerank: float
    centrality: float
    in_degree: int
    out_degree: int

@dataclass
class KnowledgeEdge:
    source: str
    target: str
    type: EdgeType  # HYPERLINK, SEMANTIC, TOPIC, etc.
    weight: float
    confidence: float
    metadata: Dict[str, Any]
```

##### Navigation Graph Schema
```python
@dataclass
class NavigationNode:
    id: str
    url: str
    title: str
    type: str  # html_page, pdf_document, docx_document
    mime_type: str
    level: int  # Depth in hierarchy
    parent: Optional[str]
    children: List[str]
    file_path: str

@dataclass
class NavigationEdge:
    source: str
    target: str
    link_text: str
    type: str  # hyperlink, document_link
```

---

## 🚀 Master Orchestration Scripts

### Script: `scripts/run_all.py`
**Purpose:** Run complete pipeline from crawling to visualization

```python
#!/usr/bin/env python3
"""
Master Orchestration Script
Runs complete pipeline: crawl → knowledge → navigation → visualizations
"""

import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Run complete pipeline')
    parser.add_argument('--agencies', type=str, help='Comma-separated agency list')
    parser.add_argument('--all-agencies', action='store_true', help='Run all agencies')
    parser.add_argument('--skip-crawl', action='store_true', help='Skip crawling phase')
    parser.add_argument('--quick', action='store_true', help='Quick mode (skip expensive ops)')
    parser.add_argument('--phases', type=str, default='1,2,3,4,5,6', help='Phases to run')
    
    args = parser.parse_args()
    
    phases = [int(p) for p in args.phases.split(',')]
    
    # Phase 1: Crawl
    if 1 in phases and not args.skip_crawl:
        print("\n=== PHASE 1: Web Crawling ===")
        # Run crawling logic
    
    # Phase 2: Knowledge Network
    if 2 in phases:
        print("\n=== PHASE 2: Knowledge Network ===")
        # Run knowledge graph building
    
    # Phase 3: Navigation Network
    if 3 in phases:
        print("\n=== PHASE 3: Navigation Network ===")
        # Run navigation graph building
    
    # Phase 4: Knowledge Visualization
    if 4 in phases:
        print("\n=== PHASE 4: Knowledge Visualization ===")
        # Generate knowledge graph viz
    
    # Phase 5: Navigation Visualization
    if 5 in phases:
        print("\n=== PHASE 5: Navigation Visualization ===")
        # Generate navigation tree viz
    
    # Phase 6: Interactive Visualization
    if 6 in phases:
        print("\n=== PHASE 6: Interactive Multi-Agency Viz ===")
        # Generate interactive viz

if __name__ == '__main__':
    main()
```

#### Usage Examples:
```bash
# Complete pipeline (all agencies, all phases)
python scripts/run_all.py --all-agencies

# Specific agencies
python scripts/run_all.py --agencies agriculture,commerce,human-resources

# Skip crawling (use existing data)
python scripts/run_all.py --all-agencies --skip-crawl

# Only run phases 2-6 (skip crawling)
python scripts/run_all.py --all-agencies --phases 2,3,4,5,6

# Quick mode (skip expensive semantic operations)
python scripts/run_all.py --all-agencies --quick

# Only generate visualizations (phases 4-6)
python scripts/run_all.py --agencies agriculture --phases 4,5,6
```

---

### Script: `scripts/run_phase.py`
**Purpose:** Run a single phase with full control

```bash
# Run specific phase
python scripts/run_phase.py 1 --agencies agriculture,commerce  # Phase 1: Crawl
python scripts/run_phase.py 2 --all-agencies                   # Phase 2: Knowledge
python scripts/run_phase.py 3 --agencies agriculture           # Phase 3: Navigation
python scripts/run_phase.py 4                                  # Phase 4: Knowledge Viz
python scripts/run_phase.py 5 --agencies agriculture           # Phase 5: Navigation Viz
python scripts/run_phase.py 6                                  # Phase 6: Interactive Viz
```

---

## 📊 Data Directory Structure

```
data/
├── knowledge/                      # Crawled markdown content
│   ├── administration/
│   │   ├── index.md
│   │   ├── page1.md
│   │   └── pdf_document.md
│   ├── agriculture/
│   └── ...
│
├── graphs/                         # Generated network graphs
│   ├── knowledge/
│   │   ├── full_graph.pkl          # Complete knowledge graph
│   │   ├── full_graph.json
│   │   ├── full_graph.graphml
│   │   ├── content_chunks.json     # RAG chunks
│   │   └── analysis_metrics.json
│   │
│   └── navigation/
│       ├── administration_nav.json
│       ├── agriculture_nav.json
│       └── ...
│
└── html/                           # Generated visualizations
    ├── knowledge_graph.html        # Phase 4 output
    ├── navigation/
    │   ├── administration_tree.html
    │   ├── agriculture_tree.html
    │   └── ...
    └── interactive_network.html    # Phase 6 output
```

---

## 🔄 Migration Strategy

### Step 1: Create New Structure (Week 1)
1. Create new directory structure
2. Move shared components to `src/shared/`
3. Create placeholder directories for phases 1-6
4. Set up configuration system

### Step 2: Refactor Phase 1 - Crawling (Week 1-2)
1. Extract crawler logic from `crawler_1.py`
2. Separate extractors (HTML, PDF, DOCX)
3. Create CLI interface
4. **IMPORTANT:** Remove navigation network building from crawler
5. Test with 1-2 agencies

### Step 3: Refactor Phase 2 - Knowledge Network (Week 2)
1. Move graph building from `src/network/` to `src/2_knowledge/`
2. Simplify to focus on document relationships
3. Create CLI interface
4. Test with existing data

### Step 4: Build Phase 3 - Navigation Network (Week 2-3)
1. Extract navigation network logic from crawler
2. Build separate navigation graph builder
3. Implement MIME type hierarchy
4. Create CLI interface
5. Test with 1-2 agencies

### Step 5: Refactor Visualizations (Week 3-4)
1. **Phase 4:** Extract/refactor knowledge graph viz
2. **Phase 5:** Create navigation tree viz (new)
3. **Phase 6:** Build comprehensive interactive viz (new)
4. Test all visualizations

### Step 6: Build Orchestration (Week 4)
1. Create `run_all.py` master script
2. Create `run_phase.py` individual runner
3. Add configuration file support
4. Write comprehensive documentation

### Step 7: Testing & Documentation (Week 4-5)
1. Integration testing with all agencies
2. Performance optimization
3. Write API documentation
4. Create usage guide
5. Update README.md

### Step 8: Deployment (Week 5)
1. Archive old code to `_archive/` directory
2. Update all documentation
3. Create migration guide for existing users
4. Final testing

---

## ✅ Success Criteria

### Functional Requirements
- ✅ Single command to run complete pipeline
- ✅ Individual phases can run independently
- ✅ CLI support for single or multiple agencies
- ✅ Clear separation between knowledge and navigation graphs
- ✅ MIME type hierarchy in navigation graph
- ✅ Interactive visualization with filters and agency selection
- ✅ Network complexity reduction controls
- ✅ All existing features preserved

### Technical Requirements
- ✅ Modular architecture with clear interfaces
- ✅ Consistent error handling and logging
- ✅ Configuration-based (not hardcoded)
- ✅ Incremental updates supported
- ✅ Resume capability for long-running operations
- ✅ Performance: Process 1000 documents in < 5 minutes
- ✅ Memory efficient (< 2GB for full pipeline)

### Documentation Requirements
- ✅ Architecture documentation
- ✅ API documentation for each phase
- ✅ Usage guide with examples
- ✅ Migration guide
- ✅ Inline code documentation (docstrings)

---

## 📝 Configuration Example

### File: `config.yaml`

```yaml
# Montana State Government Knowledge Network Configuration

# Data paths
paths:
  knowledge_dir: "data/knowledge"
  graphs_dir: "data/graphs"
  html_dir: "data/html"
  agencies_file: "agencies.md"

# Phase 1: Crawling
crawling:
  rate_limit_delay: 1.0  # seconds between requests
  timeout: 30  # request timeout
  max_retries: 3
  allowed_extensions:
    - .html
    - .htm
    - .pdf
    - .docx
  user_agent: "Mozilla/5.0 (Montana Knowledge Crawler)"

# Phase 2: Knowledge Network
knowledge:
  semantic_similarity:
    enabled: true
    threshold: 0.3
    method: "tfidf"  # or "embeddings"
  topic_modeling:
    enabled: true
    num_topics: 20
  rag:
    chunk_size: 512
    chunk_overlap: 50

# Phase 3: Navigation Network
navigation:
  max_depth: 10
  mime_types:
    html: ["text/html"]
    pdf: ["application/pdf"]
    docx: ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

# Phase 4-6: Visualizations
visualization:
  knowledge_graph:
    max_nodes: 1000
    layout: "force-directed"
  navigation_tree:
    layout: "tree"  # or "radial"
  interactive:
    default_agencies: ["agriculture", "commerce", "human-resources"]
    max_nodes: 500
    enable_filters: true

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "pipeline.log"

# Performance
performance:
  parallel_processing: true
  max_workers: 4
  cache_enabled: true
  cache_dir: ".cache"
```

---

## 🎯 Key Differentiators

### What's New/Different:

1. **Separation of Concerns:**
   - Crawler does ONLY crawling (no navigation network building)
   - Navigation network is a separate phase with its own logic
   - Knowledge network focuses on semantic relationships

2. **MIME Type Hierarchy:**
   - HTML pages are primary nodes (blue border)
   - PDF/DOCX are children of HTML pages they're linked from
   - Clear parent-child relationships

3. **Unified CLI:**
   - Consistent interface across all phases
   - Single command to run everything
   - Easy to run specific agencies or phases

4. **Advanced Visualization (Phase 6):**
   - Multi-agency selection
   - Network complexity reduction (essential for large graphs)
   - Multiple filtering options
   - Real-time statistics
   - Interactive controls

5. **Modular Architecture:**
   - Each phase is self-contained
   - Clear data contracts between phases
   - Easy to extend or replace components

6. **Configuration-Driven:**
   - All parameters in config file
   - No hardcoded values
   - Easy to customize per environment

---

## 📈 Performance Considerations

### Scalability Targets:
- **Agencies:** 50+ (current: 9)
- **Documents:** 20,000+ (current: 7,586)
- **Edges:** 500,000+ (current: 140,526)

### Optimization Strategies:

1. **Phase 1 (Crawling):**
   - Parallel crawling (multiple agencies simultaneously)
   - Async HTTP requests
   - Resume from checkpoint

2. **Phase 2 (Knowledge):**
   - Incremental graph building
   - Cache semantic similarity computations
   - Batch embedding generation
   - Optional quick mode (skip expensive operations)

3. **Phase 3 (Navigation):**
   - Load link data from crawler (don't re-parse)
   - Cache MIME type classifications

4. **Phase 4-6 (Visualizations):**
   - Generate separate files per agency for navigation viz
   - Interactive viz: load data on-demand (not all at once)
   - Network simplification for large graphs
   - WebGL rendering for 1000+ nodes

---

## 🔍 Testing Strategy

### Unit Tests:
- Each extractor (HTML, PDF, DOCX)
- Graph builders (knowledge and navigation)
- Network simplification algorithms
- Visualization renderers

### Integration Tests:
- End-to-end pipeline with test agencies
- Data flow between phases
- CLI interface

### Performance Tests:
- Crawl 100 pages in < 2 minutes
- Build knowledge graph (1000 docs) in < 3 minutes
- Generate visualization in < 30 seconds

### Validation Tests:
- Verify no data loss during migration
- Check graph connectivity
- Validate MIME type hierarchy

---

## 📚 Documentation Plan

### 1. ARCHITECTURE.md
- System overview diagram
- Component descriptions
- Data flow diagrams
- Technology stack

### 2. API.md
- Each phase's API
- Data schemas
- Configuration options
- Examples

### 3. USAGE.md
- Quick start guide
- Common workflows
- Troubleshooting
- FAQ

### 4. MIGRATION.md
- Changes from old structure
- Migration steps
- Breaking changes
- Compatibility notes

### 5. CONTRIBUTING.md
- Code style guide
- How to add new features
- Testing requirements
- PR process

---

## 🗓️ Timeline

### Week 1: Foundation
- ✅ Create refactoring plan (this document)
- Create new directory structure
- Extract shared components
- Set up configuration system

### Week 2: Core Phases
- Refactor Phase 1 (Crawling)
- Refactor Phase 2 (Knowledge)
- Build Phase 3 (Navigation)

### Week 3: Visualizations
- Refactor Phase 4 (Knowledge Viz)
- Build Phase 5 (Navigation Viz)
- Build Phase 6 (Interactive Viz)

### Week 4: Integration
- Build orchestration scripts
- Integration testing
- Performance optimization
- Documentation

### Week 5: Finalization
- Comprehensive testing
- Documentation review
- Migration guide
- Deployment

---

## ✨ Future Enhancements

### Post-Refactoring Features:
1. **Search Interface:**
   - Full-text search across all documents
   - Faceted search (by agency, type, topic)
   - Graph-based query expansion

2. **Change Detection:**
   - Track website changes over time
   - Diff visualization
   - Alert on significant changes

3. **API Server:**
   - REST API for graph queries
   - GraphQL support
   - Real-time updates via WebSocket

4. **AI Integration:**
   - RAG-based question answering
   - Document summarization
   - Topic clustering
   - Relationship prediction

5. **Advanced Analytics:**
   - Temporal analysis (how network evolves)
   - Citation analysis (most referenced docs)
   - Content gap analysis
   - Agency comparison

6. **Export Formats:**
   - Neo4j import format
   - RDF/Turtle for semantic web
   - Gephi format
   - CSV/Excel for analysis

---

## 📞 Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize features** if timeline needs adjustment
3. **Assign resources** to each phase
4. **Create GitHub issues** for tracking
5. **Set up development branch** for refactoring
6. **Begin Week 1 tasks**

---

**Document Version:** 1.0  
**Last Updated:** December 8, 2025  
**Author:** GitHub Copilot  
**Status:** Draft - Awaiting Approval
