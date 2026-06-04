# Phase 3: HTML Navigation Extractor

Extracts pure HTML navigation structure from crawled websites, focusing on hyperlinks rather than hierarchical relationships.

## Features

- ✅ Extracts actual hyperlinks from markdown content
- ✅ URL normalization and deduplication
- ✅ MIME type classification (HTML, PDF, DOCX)
- ✅ Domain root identification
- ✅ JSON export for visualization

## Architecture

```
src/phase3_navigation/
├── html_navigation_extractor.py  # Main extractor
└── html_nav_cli.py               # Command-line interface
```

## Usage

### Extract Navigation Data

```bash
# Single agency
python -m src.phase3_navigation.html_nav_cli --agency agriculture

# All agencies
python -m src.phase3_navigation.html_nav_cli --all

# Extract only (no visualization)
python -m src.phase3_navigation.html_nav_cli --agency agriculture --extract-only
```

### Or Use Integrated Pipeline

```bash
# Extract + visualize in one command
python -m src.phase6_viz_interactive.integrated_cli --agency agriculture
```

## Output

Creates JSON files in `data/graphs/navigation/{agency}_html_navigation.json`:

```json
{
  "agency": "agriculture",
  "created": "2025-12-09T...",
  "base_domain": "https://agr.mt.gov",
  "statistics": {
    "total_nodes": 3203,
    "html_pages": 1984,
    "pdf_documents": 1165,
    "docx_documents": 40,
    "other_documents": 14,
    "total_edges": 4168
  },
  "nodes": {
    "node_id": {
      "id": "abc123",
      "url": "https://...",
      "title": "Page Title",
      "mime_type": "text/html",
      "type": "html_page",
      "is_root": false,
      "file_path": "agriculture/page.md"
    }
  },
  "edges": [
    {
      "source": "id1",
      "target": "id2",
      "link_text": "Click Here"
    }
  ]
}
```

## Key Features

### URL Normalization
- Removes trailing slashes
- Removes URL fragments (#anchors)
- Removes query parameters
- Ensures one node per unique document

### MIME Type Detection
- Inferred from URL extensions
- Override from markdown metadata
- Classification: HTML, PDF, DOCX, Excel, Other

### Link Extraction
- Standard markdown links: `[text](url)`
- Links with titles: `[text](url "title")`
- Relative URL resolution
- Filters out images and anchors

## See Also

- **Phase 5**: Visualization (`src/phase5_viz_navigation/`)
- **Phase 6**: Integrated Dashboard (`src/phase6_viz_interactive/`)
- **Complete Documentation**: `HTML_NAVIGATION_README.md`
- **Child Nodes**: Documents
  - PDF documents (`application/pdf`)
  - DOCX documents (`application/vnd.openxmlformats...`)
  - Always children of HTML pages

## Configuration

Settings in `config.yaml`:

```yaml
navigation:
  max_depth: 10
  mime_types:
    html: ["text/html"]
    pdf: ["application/pdf"]
    docx: ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
```
