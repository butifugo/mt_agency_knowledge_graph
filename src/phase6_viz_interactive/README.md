# Phase 6: Interactive Multi-Agency Dashboard

Unified interactive dashboard combining knowledge graphs and navigation trees with advanced filtering, search, and export capabilities.

## Overview

This is the capstone phase that integrates all previous work into a single, powerful visualization platform. It provides a dual-pane interface showing both knowledge relationships and navigation hierarchies simultaneously.

## Features

✅ **Multi-Agency Selection**
- Dropdown selector for all available agencies
- Automatic detection of agencies with complete data
- Dynamic loading of graph data

✅ **Dual-View Layout**
- Left pane: Knowledge graph (force-directed network)
- Right pane: Navigation tree (hierarchical list)
- Synchronized data loading

✅ **Network Complexity Controls**
- Node limit slider (50-500 nodes)
- Real-time graph filtering
- Performance optimization

✅ **Search Functionality**
- Live search across all nodes
- Visual highlighting of matches
- Case-insensitive filtering

✅ **Export Capabilities**
- PNG export of entire dashboard
- High-quality screenshots
- Timestamped filenames

✅ **Interactive Controls**
- Zoom and pan on knowledge graph
- Drag nodes to reposition
- Reset views button
- Hover tooltips with metadata

## Architecture

```
src/phase6_viz_interactive/
├── __init__.py          # Module initialization
├── dashboard_viz.py     # Dashboard generator
├── cli.py               # Command-line interface
└── README.md            # This file
```

### Key Components

**DashboardGenerator** (`dashboard_viz.py`)
- Loads knowledge and navigation graphs
- Combines data from Phases 2-5
- Generates self-contained HTML dashboard
- Embeds all data and JavaScript

**CLI** (`cli.py`)
- Simple command-line interface
- Agency selection
- Configuration support

## Usage

### Generate Dashboard (All Agencies)
```bash
python -m src.phase6_viz_interactive.cli
```

### Generate Dashboard (Specific Agencies)
```bash
python -m src.phase6_viz_interactive.cli --agencies agriculture,commerce
```

### With Custom Config
```bash
python -m src.phase6_viz_interactive.cli --config config.yaml
```

### Quiet Mode
```bash
python -m src.phase6_viz_interactive.cli --quiet
```

## Input

**Knowledge Graphs** (from Phase 2/4)
- Location: `data/graphs/knowledge/{agency}_knowledge.json`
- Format: JSON with nodes and edges
- Used for force-directed network visualization

**Navigation Graphs** (from Phase 3/5)
- Location: `data/graphs/navigation/{agency}_navigation.json`
- Format: JSON with nodes and edges
- Used for hierarchical tree display

## Output

**Interactive Dashboard**
- Location: `html/interactive-dashboard.html`
- Format: Self-contained HTML with embedded data
- Size: Varies by number of agencies (typically 2-10 MB)

**Features:**
- Agency dropdown selector
- Dual-pane visualization
- Node limit slider (50-500)
- Search box
- Export PNG button
- Reset views button
- Legends for both views

## Dashboard Interface

### Header
- Title: "Montana State Knowledge Network Dashboard"
- Controls: Reset Views, Export PNG

### Toolbar
- Agency selector dropdown
- Max nodes slider with live counter
- Search box

### Content Panels

**Left: Knowledge Graph**
- Force-directed network layout
- Color-coded nodes:
  - Blue (#4dabf7): Documents
  - Green (#51cf66): Keywords
  - Red (#ff6b6b): Topics
- Interactive features:
  - Drag nodes to reposition
  - Zoom and pan
  - Tooltips on hover

**Right: Navigation Tree**
- Hierarchical list view
- Color-coded by MIME type:
  - Blue (#4dabf7): HTML pages
  - Red (#ff6b6b): PDFs
  - Purple (#7950f2): DOCX files
- Shows first 100 nodes for performance

## Integration with Other Phases

**Consumes:**
- Phase 2: Knowledge graphs (semantic relationships)
- Phase 3: Navigation graphs (page hierarchies)
- Phase 4: Knowledge visualization patterns
- Phase 5: Navigation visualization patterns

**Produces:**
- Unified visualization platform
- End-user facing dashboard
- Final deliverable for project

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Max Agencies | Unlimited | Data embedded in HTML |
| Recommended Nodes | 200 | Adjustable 50-500 |
| Load Time | 2-5s | Depends on data size |
| Dashboard Size | 2-10 MB | Varies by agencies |
| Browser Support | Modern | Chrome, Firefox, Safari, Edge |

**Optimizations:**
- Lazy loading of agency data
- Node limit controls
- Simplified navigation view (list vs full tree)
- Efficient D3.js rendering

## Dependencies

- D3.js v7 (CDN)
- html2canvas v1.4.1 (CDN for PNG export)
- Python 3.9+
- Modern web browser

## Examples

### View Agriculture Data
1. Open `html/interactive-dashboard.html`
2. Select "Agriculture" from dropdown
3. Adjust node limit as needed
4. Explore both visualizations

### Search for Content
1. Load any agency
2. Type search term in search box
3. Matching nodes highlight in red

### Export Visualization
1. Set up desired view
2. Click "Export PNG"
3. PNG saved with agency name

## Troubleshooting

**No agencies available**
- Run Phase 2: `python -m src.phase2_knowledge.cli --build-all`
- Run Phase 3: `python -m src.phase3_navigation.cli --build-all`
- Ensure both knowledge and navigation graphs exist

**Dashboard won't load**
- Check browser console for errors
- Verify JSON data is valid
- Try reducing node limit

**Performance issues**
- Reduce node limit slider
- Use fewer agencies
- Close other browser tabs

**Search not working**
- Ensure agency is loaded
- Check spelling
- Search is case-insensitive

## Future Enhancements

- [ ] Full tree visualization in navigation panel
- [ ] Node filtering by type
- [ ] Edge filtering by relationship
- [ ] SVG export option
- [ ] JSON export of filtered data
- [ ] Synchronized zoom/pan between panels
- [ ] Node selection synchronization
- [ ] Advanced search with regex
- [ ] Comparison mode (2 agencies side-by-side)
- [ ] Timeline view of document updates

## See Also

- Phase 2: Knowledge graph building
- Phase 3: Navigation graph building
- Phase 4: Knowledge visualizations
- Phase 5: Navigation visualizations
- Master script: `scripts/run_all.py`

## Credits

Built with D3.js by Mike Bostock
PNG export via html2canvas
Part of Montana State HR Knowledge Network Project
