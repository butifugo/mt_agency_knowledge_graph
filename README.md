# Montana State Government Knowledge Network

An AI-powered knowledge base system that crawls, processes, and visualizes content from Montana State Government agencies. The system creates interconnected knowledge graphs optimized for AI/RAG systems with interactive visualizations.

## 🎯 What It Does

This 6-phase pipeline transforms Montana state government websites into an AI-ready knowledge network:

1. **Web Crawling** - Extract content from 37+ state agencies (HTML, PDF, DOCX)
2. **Knowledge Network** - Build document graphs with semantic relationships
3. **Navigation Network** - Create webpage hierarchy structures  
4. **Knowledge Visualization** - Generate interactive knowledge graphs
5. **Navigation Visualization** - Display hierarchical website trees
6. **Interactive Dashboard** - Unified multi-agency visualization with dynamic data loading

**Project Stats:**
- 9 agency data exports • 2,602 agriculture documents • Interactive dashboard • Archived legacy visualizations

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage

**1. Crawl an agency:**
```bash
python -m src.phase1_crawl.cli --agency agriculture
```

**2. Build knowledge graph:**
```bash
python src/network/3_build_network.py --quick
```

**3. Generate interactive dashboard:**
```bash
# Generate for all available agencies
python -m src.phase6_viz_interactive.cli

# Start web server
python serve_dashboard.py

# Open: http://localhost:8000/interactive-dashboard.html
```

**4. Run complete pipeline:**
```bash
# Process specific agencies through all phases
python scripts/run_all.py --agencies agriculture,commerce --quick

# Process all agencies
python scripts/run_all.py --all-agencies
```

## 📁 Project Structure

```
hr knowledge/
├── config.yaml                   # Configuration settings
├── requirements.txt              # Python dependencies
├── agencies.md                   # List of Montana agencies
├── serve_dashboard.py            # Web server for visualizations
├── activate.sh                   # Virtual environment activation
├── serve_visualization.sh        # Dashboard launch script
│
├── src/                          # Source code (modular architecture)
│   ├── shared/                   # Shared utilities
│   │   ├── schemas.py            # Data models
│   │   ├── config.py             # Config management
│   │   └── utils.py              # Common functions
│   │
│   ├── phase1_crawl/             # ✅ Web crawling
│   │   ├── cli.py                # Command interface
│   │   ├── crawler.py            # Main crawler
│   │   └── extractors/           # HTML, PDF, DOCX extractors
│   │
│   ├── phase2_knowledge/         # ✅ Knowledge graphs
│   │   ├── cli.py                # Command interface
│   │   ├── knowledge_builder.py  # Graph builder
│   │   └── semantic_analyzer.py  # Semantic analysis
│   │
│   ├── phase3_navigation/        # ✅ Navigation graphs
│   │   ├── html_nav_cli.py       # Command interface
│   │   └── html_navigation_extractor.py  # Navigation builder
│   │
│   ├── phase4_viz_knowledge/     # ✅ Knowledge visualization
│   │   ├── cli.py                # Command interface
│   │   └── knowledge_viz.py      # D3.js visualizer
│   │
│   ├── phase5_viz_navigation/    # ✅ Navigation visualization
│   │   └── html_navigation_viz.py  # Tree visualizer
│   │
│   ├── phase6_viz_interactive/   # ✅ Unified dashboard
│   │   ├── cli.py                # Command interface
│   │   ├── dashboard_viz.py      # Dashboard generator
│   │   └── integrated_cli.py     # Integrated commands
│   │
│   ├── network/                  # Advanced network analysis
│   │   ├── 3_build_network.py    # Network builder
│   │   ├── graph_builder.py      # Graph construction
│   │   ├── semantic_layer.py     # Semantic relationships
│   │   ├── rag_retriever.py      # RAG system
│   │   ├── analyzer.py           # Network analytics
│   │   └── persistence.py        # Data persistence
│   │
│   ├── viz/                      # Legacy visualization tools
│   │   └── 4_agency_network_viz.py
│   │
│   └── extract/                  # Legacy extraction tools
│       ├── 2_refresh.py          # Content refresh
│       └── crawler_1.py          # Legacy crawler
│
├── scripts/
│   └── run_all.py                # Master pipeline orchestrator
│
├── data/graphs/                  # Generated graphs
│   ├── knowledge/                # Knowledge graph exports (.pkl)
│   └── navigation/               # Navigation graph exports (.json)
│
├── knowledge/                    # Crawled content by agency
│   ├── README.md                 # Knowledge folder documentation
│   └── agriculture/              # 2,602 markdown documents
│
├── html/                         # Active visualizations
│   ├── interactive-dashboard.html  # Main unified dashboard
│   ├── agency-data/              # Agency JSON exports (9 agencies)
│   │   ├── administration.json   # 392KB
│   │   ├── agriculture.json      # 141MB
│   │   ├── arts-council.json     # 968KB
│   │   ├── auditor.json          # 2.4MB
│   │   ├── commerce.json         # 8.2MB
│   │   ├── corrections.json      # 3.2MB
│   │   ├── environmental-quality.json  # 4.2MB
│   │   ├── human-resources.json  # 282KB
│   │   └── labor-industry.json   # 3.0MB
│   └── js/                       # JavaScript libraries
│       ├── d3.v7.min.js          # D3.js visualization
│       └── html2canvas.min.js    # Export functionality
│
├── presentations/                # Generated presentations
│   └── human-resources/
│       └── human-resources_presentation.md
│
└── archive/                      # Archived content
    ├── html/                     # Legacy HTML visualizations
    │   ├── agriculture-html-navigation.html  # 1.4MB
    │   ├── agriculture-knowledge-viz.html    # 838KB
    │   ├── human-resources-html-navigation.html  # 140KB
    │   ├── knowledge-network-selector.html
    │   ├── knowledge_network.html
    │   ├── knowledge_network.png  # 2.3MB
    │   └── montana_network_interactive.html  # 2.4MB
    │
    └── old-docs/                 # Legacy documentation
        └── [historical markdown files]
```

## 🎯 Core Features

### 1. Multi-Agency Web Crawler
- Multi-format support (HTML, PDF, DOCX)
- Polite crawling with rate limiting
- Clean markdown conversion
- Metadata tracking (source URLs, titles, timestamps)

**Commands:**
```bash
# Crawl all agencies
python -m src.phase1_crawl.cli --all

# Crawl specific agency
python -m src.phase1_crawl.cli --agency agriculture

# Dry run (preview only)
python -m src.phase1_crawl.cli --agency agriculture --dry-run

# Update only (skip existing)
python -m src.phase1_crawl.cli --all --update-only
```

### 2. Knowledge Graph Network
- Document graphs with semantic relationships
- Topic modeling and clustering
- Network analysis (PageRank, centrality, communities)
- Multi-format export (JSON, GraphML, Pickle)
- Currently: Agriculture dataset with 2,602 documents

**Commands:**
```bash
# Build complete network
python src/network/3_build_network.py

# Quick build (skip expensive operations)
python src/network/3_build_network.py --quick
```

### 3. RAG Retrieval System
- Graph-enhanced search with context expansion
- Semantic chunks (512 chars, 50 overlap)
- Hybrid retrieval (semantic similarity + graph structure)
- Multi-hop queries following relationships
- Citation tracking with source documents

**Location:** `src/network/rag_retriever.py`

### 4. Interactive Visualizations

**Unified Dashboard** (Recommended):
- Side-by-side knowledge graph + navigation tree
- Dynamic data loading (minimal HTML, data in JSON)
- 9 agencies available via dropdown selector
- Modern blue gradient design with search and filters
- PNG export capability
- Responsive zoom/pan controls

**Commands:**
```bash
# Generate dashboard
python -m src.phase6_viz_interactive.cli

# Generate for specific agencies
python -m src.phase6_viz_interactive.cli --agencies agriculture,commerce

# Quiet mode
python -m src.phase6_viz_interactive.cli --quiet

# Start server (required)
python serve_dashboard.py
```

**Features:**
- D3.js force-directed network graphs
- Interactive node dragging and exploration
- Color-coded by document type/agency
- Tooltips with metadata
- Node detail panels

## 🔧 Common Tasks

### Update Agency Content
```bash
# Update all agencies
python src/extract/2_refresh.py

# Update specific agency
python src/extract/2_refresh.py agriculture
```

### Build Knowledge Network
```bash
# Standard build
python -m src.phase2_knowledge.cli --build-all

# Build for single agency
python -m src.phase2_knowledge.cli --build --agency agriculture

# Enhance with semantic similarity
python -m src.phase2_knowledge.cli --enhance --agency agriculture
```

### Generate Visualizations
```bash
# Knowledge graph
python -m src.phase4_viz_knowledge.cli --agency agriculture

# Unified dashboard (all agencies)
python -m src.phase6_viz_interactive.cli
```

### Run Complete Pipeline
```bash
# All phases for specific agencies
python scripts/run_all.py --agencies agriculture,commerce --quick

# All agencies, skip crawling (use existing data)
python scripts/run_all.py --all-agencies --skip-crawl

# Only specific phases (e.g., 2 and 4)
python scripts/run_all.py --agencies agriculture --phases 2,4
```

## 📊 Output Files

| Phase | Output Location | Description |
|-------|----------------|-------------|
| Phase 1 | `knowledge/{agency}/*.md` | Crawled markdown files (2,602 for agriculture) |
| Phase 2 | `data/graphs/knowledge/*.pkl` | Knowledge graph data (pickle format) |
| Phase 3 | `data/graphs/navigation/*.json` | Navigation hierarchy graphs |
| Phase 4 | `archive/html/{agency}-knowledge-viz.html` | Legacy knowledge visualizations |
| Phase 5 | `archive/html/{agency}-html-navigation.html` | Legacy navigation visualizations |
| Phase 6 | `html/interactive-dashboard.html` | Unified interactive dashboard |
| Phase 6 | `html/agency-data/{agency}.json` | Dashboard data files (9 agencies) |

**Note:** Legacy single-agency HTML visualizations have been archived to `archive/html/` to streamline the project. The unified dashboard in `html/interactive-dashboard.html` provides all visualization functionality.

## ⚙️ Configuration

Edit `config.yaml` to customize behavior:

```yaml
paths:
  knowledge_dir: "knowledge"
  graphs_dir: "data/graphs"
  html_dir: "html"

crawling:
  rate_limit_delay: 1.0
  timeout: 30
  max_retries: 3
  allowed_extensions: [.html, .htm, .pdf, .docx]

knowledge:
  semantic_similarity:
    enabled: true
    threshold: 0.3
  topic_modeling:
    enabled: true
    num_topics: 20
  rag:
    chunk_size: 512
    chunk_overlap: 50

visualization:
  knowledge_graph:
    max_nodes: 1000
    layout: "force-directed"
```

## 📋 Requirements

**Python:** 3.9+

**Dependencies:** (see `requirements.txt`)
- requests, beautifulsoup4, markdownify
- PyPDF2, python-docx
- networkx, numpy, scipy
- matplotlib, python-pptx
- colorama, pyyaml

## 🎨 Visualization Examples

### Unified Dashboard
- **URL:** `http://localhost:8000/interactive-dashboard.html`
- **Size:** 41KB HTML + dynamic JSON data
- **Features:** Knowledge graph + navigation tree side-by-side
- **Controls:** Agency selector, max nodes slider, search, export PNG

### Knowledge Graph
- Force-directed layout
- Color-coded nodes (documents=blue, keywords=green, topics=red)
- Interactive tooltips and dragging
- Zoom and pan support

### Navigation Tree
- Hierarchical webpage structure
- MIME type color coding (HTML=blue, PDF=red, DOCX=purple)
- Collapsible branches
- Link type visualization

## 📚 Agency Coverage

9 Montana State Agencies with exported dashboard data:
- **Administration** • **Agriculture** (2,602 documents) • **Arts Council** • **Auditor**
- **Commerce** • **Corrections** • **Environmental Quality**
- **Human Resources** • **Labor & Industry**

See `agencies.md` for the complete list of available Montana agencies. Additional agencies can be added by running the crawl and visualization pipeline.

## 🔄 Maintenance

### Monthly Updates
```bash
# Refresh all agency content
python src/extract/2_refresh.py

# Rebuild knowledge network
python src/network/3_build_network.py

# Regenerate visualizations
python -m src.phase6_viz_interactive.cli
```

### Adding New Agencies
1. Edit `agencies.md` and add row:
   ```markdown
   | Agency Name | URL | Folder |
   |------------|-----|--------|
   | New Agency | https://agency.mt.gov/ | agency-folder |
   ```

2. Crawl the new agency:
   ```bash
   python -m src.phase1_crawl.cli --agency agency-folder
   ```

3. Build knowledge graph:
   ```bash
   python src/network/3_build_network.py --quick
   ```

4. Generate dashboard data:
   ```bash
   python -m src.phase6_viz_interactive.cli --agencies agency-folder
   ```

### Cleaning Up Legacy Files
Legacy HTML visualizations are stored in `archive/html/`. These can be safely removed if you only need the unified dashboard. To restore them, regenerate using:
```bash
python -m src.phase4_viz_knowledge.cli --agency agriculture
python -m src.phase5_viz_navigation.cli --agency agriculture
```

## 🐛 Troubleshooting

**Command not found:**
```bash
# Use python3 instead of python
python3 -m src.phase1_crawl.cli --agency agriculture
```

**Module not found:**
```bash
pip install -r requirements.txt
```

**Dashboard not loading agency data:**
- Must serve via HTTP (not file://)
- Start server: `python serve_dashboard.py`
- Open: `http://localhost:8000/interactive-dashboard.html`

**Visualization not generating:**
- Ensure phases 2 & 3 have run first
- Check that agency data exists in `data/graphs/`

## 📖 Documentation

This README provides a comprehensive overview. For detailed phase-specific information, see:
- `knowledge/README.md` - Knowledge folder documentation
- Individual phase folders in `src/` for implementation details
- `archive/old-docs/` - Historical documentation and implementation notes

### Project Organization
- **Active Files**: `html/interactive-dashboard.html` and `html/agency-data/` for current visualizations
- **Archive**: `archive/html/` contains legacy single-agency visualizations
- **Source Code**: Modular architecture in `src/` with 6 phases + network analysis
- **Data Storage**: `data/graphs/` for knowledge and navigation graphs
- **Content**: `knowledge/` for crawled markdown files

---

**Last Updated:** December 9, 2025  
**Project Status:** Production Ready (All 6 phases complete, legacy files archived)  
**Current Dataset:** 9 agencies with interactive dashboard, 2,602 agriculture documents  
**Purpose:** AI-ready knowledge base for Montana government services
