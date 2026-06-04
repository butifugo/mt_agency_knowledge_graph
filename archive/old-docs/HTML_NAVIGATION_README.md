# HTML Navigation Extraction & Visualization

A focused tool for extracting and visualizing the **pure HTML navigation structure** of government websites. Unlike knowledge graphs that represent conceptual relationships, this creates a simple navigational map showing how web pages link to each other.

## Purpose

This tool extracts the actual HTML navigation links from crawled websites and creates an interactive force-directed visualization where:

- **Domain Root** = Largest circle (50px) - The homepage/root of the site
- **HTML Pages** = Medium circles (20px) - Web pages that form the navigation structure  
- **Documents** = Smallest circles (6-8px) - PDF, DOCX, and other linked files

## Key Differences from Knowledge Graphs

| Feature | HTML Navigation | Knowledge Graph |
|---------|----------------|-----------------|
| **Focus** | How pages link together | What concepts are related |
| **Structure** | Webpage hierarchy | Topic relationships |
| **Nodes** | URLs and documents | Concepts and entities |
| **Edges** | Hyperlinks | Semantic relationships |
| **Use Case** | Understanding site structure | Understanding content connections |

## Architecture

```
src/phase3_navigation/
  ├── html_navigation_extractor.py    # Extracts HTML navigation from markdown
  ├── html_nav_cli.py                 # Command-line interface
  
src/phase5_viz_navigation/
  ├── html_navigation_viz.py          # Generates D3.js force-directed viz

data/graphs/navigation/
  └── {agency}_html_navigation.json   # Extracted navigation data

html/
  └── {agency}-html-navigation.html   # Interactive visualization
```

## Features

### Extraction (`html_navigation_extractor.py`)

- ✅ Extracts all hyperlinks from markdown content
- ✅ Resolves relative URLs to absolute URLs
- ✅ Classifies nodes by MIME type (HTML, PDF, DOCX, etc.)
- ✅ Identifies root domain automatically
- ✅ Exports to JSON format
- ✅ Filters out image links and anchors

### Visualization (`html_navigation_viz.py`)

- ✅ Force-directed network layout
- ✅ MIME-type based node sizing
- ✅ Color-coded by document type
- ✅ Interactive controls (zoom, pan, drag)
- ✅ Filter by type (all, HTML only, documents only)
- ✅ Tooltip with node details
- ✅ Click to open URL in new tab
- ✅ Toggle labels on/off
- ✅ Reset view

## Usage

### Command-Line Interface

```bash
# Extract and visualize for one agency
python -m src.phase3_navigation.html_nav_cli --agency agriculture

# Extract only (no visualization)
python -m src.phase3_navigation.html_nav_cli --agency agriculture --extract-only

# Visualize from existing data (no extraction)
python -m src.phase3_navigation.html_nav_cli --agency agriculture --viz-only

# Process all agencies
python -m src.phase3_navigation.html_nav_cli --all

# Quiet mode
python -m src.phase3_navigation.html_nav_cli --agency agriculture --quiet
```

### Python API

**Extract navigation:**
```python
from src.phase3_navigation.html_navigation_extractor import HTMLNavigationExtractor

extractor = HTMLNavigationExtractor()
data = extractor.extract_navigation('agriculture', verbose=True)

# Access nodes
for node_id, node in data['nodes'].items():
    print(f"{node['title']}: {node['url']} ({node['type']})")

# Access edges
for edge in data['edges']:
    print(f"{edge['source']} -> {edge['target']}: {edge['link_text']}")
```

**Generate visualization:**
```python
from src.phase5_viz_navigation.html_navigation_viz import HTMLNavigationVisualizer

viz = HTMLNavigationVisualizer()
output_path = viz.generate_visualization('agriculture')
print(f"Visualization: {output_path}")
```

## Output Format

### Navigation JSON

```json
{
  "agency": "agriculture",
  "created": "2025-12-09T13:00:52.112786",
  "base_domain": "https://agr.mt.gov",
  "statistics": {
    "total_nodes": 3310,
    "html_pages": 2091,
    "pdf_documents": 1165,
    "docx_documents": 40,
    "other_documents": 14,
    "total_edges": 4217
  },
  "nodes": {
    "node_id": {
      "id": "abc123",
      "url": "https://agr.mt.gov/page",
      "title": "Page Title",
      "mime_type": "text/html",
      "type": "html_page",
      "is_root": false,
      "file_path": "agriculture/page.md"
    }
  },
  "edges": [
    {
      "source": "node_id_1",
      "target": "node_id_2",
      "link_text": "Click Here"
    }
  ]
}
```

## Visualization Controls

| Control | Action |
|---------|--------|
| **Mouse Wheel** | Zoom in/out |
| **Click + Drag** | Pan around |
| **Drag Node** | Reposition node |
| **Hover Node** | Show tooltip |
| **Click Node** | Open URL in new tab |
| **Reset View** | Return to initial zoom |
| **Toggle Labels** | Show/hide node labels |
| **Show All** | Display all nodes |
| **HTML Only** | Show only HTML pages |
| **Documents Only** | Show only documents |

## Color Scheme

- 🔴 **Red** (#e53935) - Domain root
- 🔵 **Blue** (#1e88e5) - HTML pages
- 🟠 **Orange** (#fb8c00) - PDF documents
- 🟣 **Purple** (#8e24aa) - DOCX documents
- 🟢 **Green** (#43a047) - Other documents

## Node Sizing

Node size is determined by MIME type to show hierarchy:

```python
Domain Root:    50px  # Largest - the website's homepage
HTML Pages:     20px  # Medium - navigable web pages
PDF Documents:   8px  # Small - downloadable PDFs
DOCX Documents:  8px  # Small - downloadable Word docs
Other Docs:      6px  # Smallest - other file types
```

## Example Workflows

### 1. Audit Site Navigation

```bash
# Extract navigation structure
python -m src.phase3_navigation.html_nav_cli --agency agriculture

# Open visualization
open html/agriculture-html-navigation.html

# Use "HTML Only" filter to see page structure
# Use "Documents Only" to see what files are linked
```

### 2. Compare Agency Structures

```bash
# Extract all agencies
python -m src.phase3_navigation.html_nav_cli --all

# Compare visualizations to see organizational differences
```

### 3. Find Orphaned Pages

```python
from src.phase3_navigation.html_navigation_extractor import HTMLNavigationExtractor

extractor = HTMLNavigationExtractor()
data = extractor.extract_navigation('agriculture')

# Find nodes with no incoming edges
incoming = {edge['target'] for edge in data['edges']}
all_nodes = set(data['nodes'].keys())
orphaned = all_nodes - incoming - {next(n for n, d in data['nodes'].items() if d['is_root'])}

print(f"Orphaned pages: {len(orphaned)}")
for node_id in orphaned:
    node = data['nodes'][node_id]
    if node['type'] == 'html_page':
        print(f"  - {node['title']}: {node['url']}")
```

## Performance

- **Agriculture Department**:
  - 2,602 markdown files processed
  - 3,310 nodes extracted
  - 4,217 edges mapped
  - Processing time: ~3 seconds
  - Visualization generates in <1 second

## Technical Details

### Link Extraction

Links are extracted using regex pattern matching on markdown content:

```python
link_pattern = r'\[([^\]]+)\]\(([^\)]+?)(?:\s+"[^"]*")?\)'
```

This captures:
- `[link text](url)` - Standard markdown links
- `[link text](url "title")` - Links with titles

### URL Resolution

Relative URLs are resolved to absolute using the source page URL:

```python
from urllib.parse import urlparse, urljoin

parsed_source = urlparse(source_url)
base = f"{parsed_source.scheme}://{parsed_source.netloc}"
absolute_url = urljoin(base + '/', relative_url)
```

### MIME Type Detection

MIME types are inferred from URL extensions:

```python
'.pdf' -> 'application/pdf'
'.docx' -> 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
'.html' or unknown -> 'text/html'
```

### Force Simulation

The D3.js force simulation uses:

- **Link Force**: Pulls connected nodes together (distance: 100-150px)
- **Charge Force**: Pushes nodes apart (strength: -300)
- **Center Force**: Keeps graph centered
- **Collision Force**: Prevents node overlap (radius: node.size + 5)

## Troubleshooting

### No visualization appears

1. Check that extraction completed successfully
2. Verify JSON file exists: `data/graphs/navigation/{agency}_html_navigation.json`
3. Check browser console for JavaScript errors
4. Try resetting the view with "Reset View" button

### Graph is too dense

1. Use filter buttons to reduce visible nodes:
   - "HTML Only" - Shows just the page structure
   - "Documents Only" - Shows just linked files
2. Zoom in to focus on specific areas
3. Drag nodes to untangle clusters

### Missing links

1. Verify markdown files contain proper markdown links
2. Check that URLs are not filtered (images, anchors)
3. Inspect `_html_navigation.json` to see raw data

## Future Enhancements

Potential improvements:

- [ ] Hierarchical tree layout option
- [ ] Path highlighting between nodes
- [ ] Export to other formats (GraphML, Cytoscape)
- [ ] Link strength based on frequency
- [ ] Clustering by subdomain/section
- [ ] Search/filter functionality
- [ ] Compare two agency structures side-by-side

## Related Tools

- **Phase 2 Knowledge Graph**: Semantic relationships between concepts
- **Phase 3 Navigation Graph**: Original hierarchical navigation builder
- **Phase 5 Viz Navigation**: Tree and radial visualizations

## License

Part of the Montana HR Knowledge Base project.
