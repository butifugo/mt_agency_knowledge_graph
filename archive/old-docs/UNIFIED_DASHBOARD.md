# Unified Interactive Dashboard

## Overview

The HR Knowledge project now uses a **unified interactive dashboard** that combines knowledge graphs and navigation trees in a single, efficient interface.

## Key Improvements

### Before (Deprecated Approach)
- ❌ Multiple separate HTML files for each visualization type
- ❌ 140MB single dashboard file with embedded data
- ❌ Inconsistent look and feel across visualizations
- ❌ Difficult to maintain and update

### After (Current Unified Dashboard)
- ✅ Single 41KB dashboard HTML file
- ✅ Agency data loaded dynamically from separate JSON files
- ✅ Consistent modern design with blue gradient theme
- ✅ Side-by-side knowledge graph and navigation tree views
- ✅ Fast loading and responsive performance

## Architecture

```
html/
├── interactive-dashboard.html    # Main dashboard (41KB)
├── agency-data/                  # Dynamic data files
│   ├── agriculture.json          # 141MB
│   ├── commerce.json             # 8.2MB
│   ├── human-resources.json      # 600KB
│   └── ...
└── js/
    ├── d3.v7.min.js
    └── html2canvas.min.js
```

## Usage

### Generate Dashboard

```bash
# Generate dashboard for all available agencies
python -m src.phase6_viz_interactive.cli

# Generate for specific agencies only
python -m src.phase6_viz_interactive.cli --agencies agriculture,commerce

# Generate quietly (minimal output)
python -m src.phase6_viz_interactive.cli --quiet
```

### Open Dashboard

1. Generate the dashboard using one of the commands above
2. **Start the web server** (required for loading agency data):
   ```bash
   python serve_dashboard.py
   ```
3. Open in browser: **http://localhost:8000/interactive-dashboard.html**
4. Select an agency from the dropdown
5. Explore both knowledge graph and navigation tree simultaneously

> **Note:** The dashboard must be served via HTTP (not opened as a local file) because it loads agency data dynamically via `fetch()` API calls.

## Features

### Interactive Controls

- **Agency Selector**: Choose which agency to visualize
- **Max Nodes Slider**: Control knowledge graph complexity (50-500 nodes)
- **Search Box**: Filter nodes by name/keyword
- **Reset Views**: Restore default view
- **Export PNG**: Save dashboard as image

### Knowledge Graph (Left Panel)

- Force-directed network visualization
- Color-coded nodes:
  - 🔵 Blue: Documents
  - 🟢 Green: Keywords
  - 🔴 Red: Topics
- Click nodes for detailed information
- Drag to reposition
- Zoom and pan support

### Navigation Tree (Right Panel)

- HTML page hierarchy visualization
- Color-coded by content type:
  - 🔵 Blue: HTML Pages
  - 🔴 Red: PDF Documents
  - 🟣 Purple: DOCX Documents
- Link types shown with different colors/styles:
  - Green solid: Page links
  - Red solid: Document links
  - Gray dashed: Hierarchy
- Hover for tooltips

### Node Details Panel

- Slides in from right when clicking a node
- Shows:
  - Node metadata (type, URL, word count)
  - Connection statistics
  - Keywords and tags
  - Related content

## Design

The unified dashboard features a modern, professional design:

- **Color Scheme**: Blue gradient (`#1e3c72` → `#2a5298`)
- **Typography**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI)
- **Layout**: Responsive grid with header, toolbar, and dual-panel content
- **Interactions**: Smooth transitions and hover effects

## Migration from Old Scripts

### Deprecated Scripts

The following scripts now show deprecation warnings:

1. `src.phase4_viz_knowledge.cli` - Standalone knowledge visualizations
2. `src.phase5_viz_navigation.html_navigation_viz` - Standalone navigation visualizations

### Migration Path

**Old Command:**
```bash
python -m src.phase4_viz_knowledge.cli --agency agriculture
```

**New Command:**
```bash
python -m src.phase6_viz_interactive.cli --agencies agriculture
```

The old commands will prompt for confirmation before proceeding with legacy generation.

## File Structure

### Dashboard Generator

```
src/phase6_viz_interactive/
├── __init__.py
├── cli.py              # Command-line interface
├── dashboard_viz.py    # Main generator class
└── README.md           # Phase 6 documentation
```

### Key Methods

**DashboardGenerator Class:**
- `get_available_agencies()` - Find agencies with both data types
- `load_knowledge_graph(agency)` - Load knowledge graph JSON
- `load_navigation_graph(agency)` - Load navigation graph JSON
- `generate_dashboard(agencies)` - Create dashboard HTML + export JSON files

## Performance

### Data Loading Strategy

1. Dashboard HTML loads instantly (41KB)
2. Agency data loaded on-demand via `fetch()` API
3. Data cached in memory after first load
4. Only selected agency's data is loaded

### Size Comparison

| File | Old Size | New Size | Reduction |
|------|----------|----------|-----------|
| Dashboard HTML | 140MB | 41KB | 99.97% |
| Agriculture Data | Embedded | 141MB (separate) | - |
| Total Initial Load | 140MB | 41KB | 99.97% |

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (may need tracking prevention disabled for export)

## Troubleshooting

### Dashboard won't load agency data

**Issue:** Clicking agency shows loading spinner forever

**Solution:** 
- **Make sure you're using the web server!** Don't open the HTML file directly
  - Wrong: `file:///Users/.../interactive-dashboard.html`
  - Right: `http://localhost:8000/interactive-dashboard.html`
- Start server: `python serve_dashboard.py`
- Check browser console for CORS errors
- Verify `html/agency-data/` contains JSON files
- Ensure files are named correctly (e.g., `agriculture.json`)

### Export to PNG fails

**Issue:** "Export to PNG is not available" error

**Solution:**
- Disable tracking prevention for the local file
- Or use Chrome/Edge which have better support
- Or take a screenshot manually

### Visualization is too cluttered

**Issue:** Too many nodes make graph hard to read

**Solution:**
- Use the "Max Nodes" slider to reduce complexity
- Try values between 100-200 for clearer visualization
- Use search to filter specific topics

## Future Enhancements

Potential improvements for the unified dashboard:

- [ ] Filtering by node type
- [ ] Highlighting connection paths between selected nodes
- [ ] Timeline view for content publication dates
- [ ] Cross-agency comparison view
- [ ] Export to JSON/CSV for data analysis
- [ ] Bookmarkable URLs with agency/view state
- [ ] Collaborative annotations

## Related Documentation

- [Phase 6 README](src/phase6_viz_interactive/README.md) - Detailed phase documentation
- [Quick Start Guide](QUICK_START.md) - Getting started
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Technical details
