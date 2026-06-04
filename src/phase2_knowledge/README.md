# Phase 2: Knowledge Network Builder

Builds document knowledge graphs with semantic relationships.

## Features

- ✅ Document graph building from markdown files
- ✅ Link extraction and edge creation
- ✅ Keyword extraction
- ✅ Semantic similarity edges
- ✅ Topic clustering
- ✅ CLI for single or all agencies
- ✅ Graph analysis tools

## Usage

### Build Knowledge Graph

```bash
# Build for all agencies
python -m src.phase2_knowledge.cli --build-all

# Build for specific agency
python -m src.phase2_knowledge.cli --build --agency agriculture
```

### Enhance with Semantic Relationships

```bash
# Add semantic and topic edges
python -m src.phase2_knowledge.cli --enhance --agency agriculture

# Customize similarity threshold
python -m src.phase2_knowledge.cli --enhance --agency agriculture --threshold 0.4

# Skip semantic edges (topics only)
python -m src.phase2_knowledge.cli --enhance --agency agriculture --skip-semantic
```

### Analyze Knowledge Graph

```bash
python -m src.phase2_knowledge.cli --analyze --agency agriculture
```

### Build and Enhance Together

```bash
python -m src.phase2_knowledge.cli --build --agency agriculture --enhance
```

## Output

Creates JSON files in `data/graphs/knowledge/{agency}_knowledge.json` with:

```json
{
  "agency": "agriculture",
  "created": "2025-12-09T...",
  "statistics": {
    "total_nodes": 1476,
    "total_edges": 89,
    "document_types": {
      "html_page": 357,
      "pdf_document": 1082,
      "docx_document": 37
    },
    "semantic_edges": 245,
    "topic_edges": 156,
    "topic_clusters": 42
  },
  "nodes": {
    "node_id": {
      "id": "agriculture/page",
      "title": "Page Title",
      "url": "https://...",
      "type": "html_page",
      "agency": "agriculture",
      "keywords": ["farming", "livestock", "crops"],
      "file_path": "knowledge/agriculture/page.md",
      "word_count": 1234
    }
  },
  "edges": [
    {
      "source": "node1",
      "target": "node2",
      "type": "hyperlink",
      "link_text": "Click here",
      "context": "..."
    },
    {
      "source": "node1",
      "target": "node3",
      "type": "semantic_similar",
      "weight": 0.45
    }
  ]
}
```

## Components

- `knowledge_builder.py` - Main graph builder
- `semantic_analyzer.py` - Semantic relationship analyzer
- `cli.py` - Command-line interface

## Edge Types

1. **hyperlink** - Direct links between documents
2. **semantic_similar** - Documents with similar keywords (Jaccard similarity)
3. **topic_related** - Documents in same topic cluster

## Configuration

Settings in `config.yaml`:

```yaml
knowledge:
  semantic_similarity:
    enabled: true
    threshold: 0.3
    method: "tfidf"
  topic_modeling:
    enabled: true
    num_topics: 20
```
