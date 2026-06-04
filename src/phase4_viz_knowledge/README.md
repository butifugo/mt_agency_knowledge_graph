# Phase 4: Knowledge Visualization

Creates interactive D3.js network visualizations from knowledge graphs.

## Features

- ✅ Interactive force-directed network graphs
- ✅ Node coloring by document type
- ✅ Dynamic tooltips with metadata
- ✅ Click to open source URLs
- ✅ Multi-agency selector page
- ✅ Drag-and-drop node repositioning
- ✅ Automatic node filtering by importance

## Usage

### Create Visualization for Single Agency

```bash
python -m src.phase4_viz_knowledge.cli --agency agriculture
```

### Create for All Agencies

```bash
python -m src.phase4_viz_knowledge.cli --all
```

### Limit Nodes for Performance

```bash
python -m src.phase4_viz_knowledge.cli --agency agriculture --max-nodes 300
```

### Skip Selector Page

```bash
python -m src.phase4_viz_knowledge.cli --all --no-selector
```

## Output

Creates HTML files in `html/` directory:
- `{agency}-knowledge-viz.html` - Individual agency visualization
- `knowledge-network-selector.html` - Multi-agency selector (if --all used)

## Visualization Features

### Node Types
- **Blue (HTML Pages)**: Web pages, primary navigation
- **Orange (PDF Documents)**: PDF files
- **Purple (DOCX Documents)**: Word documents

### Node Size
- Sized by importance (connections + keywords)
- Larger nodes = more connected/important

### Edge Types
- **Solid lines**: Direct hyperlinks
- **Dashed lines**: Semantic similarity

### Interactions
- **Hover**: Show tooltip with metadata
- **Click**: Open source URL in new tab
- **Drag**: Reposition nodes
- **Zoom/Pan**: Mouse wheel and drag background

## Configuration

Settings in `config.yaml`:

```yaml
visualization:
  knowledge_graph:
    max_nodes: 500
    layout: "force-directed"
```

## Components

- `knowledge_viz.py` - Main visualizer class
- `cli.py` - Command-line interface

## Technical Details

- Uses D3.js v7 for visualization
- Force-directed graph layout
- Responsive design
- Dark theme optimized for readability
- No external dependencies (self-contained HTML)

## Example Output

Opening `agriculture-knowledge-viz.html`:
- Displays ~500 most important nodes
- Shows hyperlink and semantic edges
- Interactive exploration of document relationships
