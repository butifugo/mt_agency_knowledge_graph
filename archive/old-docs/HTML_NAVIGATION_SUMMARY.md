# HTML Navigation Visualization - Summary

## What Was Built

A **pure HTML navigation structure extractor and visualizer** that focuses on how web pages link together, distinct from knowledge graphs that show conceptual relationships.

## Key Features

### 1. Smart Deduplication
- URLs are normalized (removes trailing slashes, fragments, query params)
- Only one node per unique document
- **Result**: 3,203 unique nodes (removed 107 duplicates from initial extraction)

### 2. MIME-Type Based Visual Hierarchy
- **Domain Root**: 50px circles (red) - Homepage/root URL
- **HTML Pages**: 20px circles (blue) - Web pages
- **PDF Documents**: 8px circles (orange) - PDF files  
- **DOCX Documents**: 8px circles (purple) - Word files
- **Other Documents**: 6px circles (green) - Other file types

### 3. Interactive Force-Directed Network
- Zoom and pan with mouse
- Drag nodes to reposition
- Click nodes to open URLs
- Hover for tooltips
- Filter by type (all/HTML only/documents)
- Toggle labels on/off

## Files Created

```
src/phase3_navigation/
  ├── html_navigation_extractor.py  # Extracts navigation from crawled markdown
  └── html_nav_cli.py               # Command-line interface

src/phase5_viz_navigation/
  └── html_navigation_viz.py        # Generates D3.js visualization

data/graphs/navigation/
  └── agriculture_html_navigation.json  # Extracted data (3,203 nodes, 4,168 edges)

html/
  └── agriculture-html-navigation.html  # Interactive visualization

HTML_NAVIGATION_README.md  # Complete documentation
```

## Usage

### Quick Start
```bash
# Extract and visualize for one agency
python -m src.phase3_navigation.html_nav_cli --agency agriculture

# View in browser
open html/agriculture-html-navigation.html

# Or serve with HTTP server
cd html && python3 -m http.server 8001
# Then open: http://localhost:8001/agriculture-html-navigation.html
```

### All Agencies
```bash
# Process all agencies at once
python -m src.phase3_navigation.html_nav_cli --all
```

## Statistics (Agriculture Department)

- **Total Nodes**: 3,203 (deduplicated from 3,310)
- **HTML Pages**: 1,984
- **PDF Documents**: 1,165
- **DOCX Documents**: 40
- **Other Documents**: 14
- **Total Links**: 4,168

## How It Differs from Knowledge Graphs

| Aspect | HTML Navigation | Knowledge Graph |
|--------|----------------|-----------------|
| **Purpose** | Show website structure | Show concept relationships |
| **Nodes** | URLs and files | Topics and entities |
| **Edges** | Hyperlinks | Semantic connections |
| **Layout** | Force-directed | Knowledge-based |
| **Use Case** | Site audit, navigation analysis | Content discovery |

## Interactive Controls

- **Reset View** - Return to initial zoom/position
- **Toggle Labels** - Show/hide node names
- **Show All** - Display all nodes
- **HTML Only** - Filter to just HTML pages
- **Documents Only** - Filter to just documents

## Color Legend

- 🔴 Red: Domain root (homepage)
- 🔵 Blue: HTML pages  
- 🟠 Orange: PDF documents
- 🟣 Purple: DOCX documents
- 🟢 Green: Other file types

## Next Steps

To use with other agencies:
```bash
python -m src.phase3_navigation.html_nav_cli --agency human-resources
python -m src.phase3_navigation.html_nav_cli --agency commerce
python -m src.phase3_navigation.html_nav_cli --agency administration
```

See `HTML_NAVIGATION_README.md` for complete documentation.
