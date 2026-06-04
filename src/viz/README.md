# Visualizations Directory

Standalone visualization and presentation generation tools for Montana State Government knowledge base.

## 📋 Overview

The `src/visualizations/` directory contains tools for creating visual representations and presentations from the Montana government knowledge base. These are **standalone scripts** that work independently of the main knowledge graph system.

### Tools Included
- **Agency Network Visualization** - Multi-agency interactive network with on-demand loading (UPDATED)
- **Network Visualization** - Generate static network graphs
- **Presentation Generator** - Create PowerPoint presentations for agencies

## 📁 Directory Structure

```
viz/
├── README.md                     # This file
├── agency_network_viz.py         # Multi-agency interactive visualization (UPDATED)
├── agency_network_viz_3d.py      # 3D network visualization
├── visualize_network.py          # Network graph visualization generator
└── presentation_generator.py     # PowerPoint presentation generator
```

## 🌐 Agency Network Visualization (UPDATED)

### Purpose
Creates a single interactive, self-contained HTML visualization with a dropdown selector for all Montana state agencies. Agency data is stored in separate JSON files and loaded on-demand for optimal performance.

### Script: `4_agency_network_viz.py`

**Features**:
- **Agency Selector**: Dropdown menu to choose any agency
- **Dynamic Loading**: Data fetched from JSON files only when agency is selected
- **Separate Data Files**: Each agency's data in its own JSON file (no preloading)
- **Minimal HTML Size**: Main HTML file is only ~32 KB
- Always-visible node labels
- Interactive metadata panel on click
- Direct links to source documents
- Force-directed D3.js layout
- Real-time filters and controls

**Usage**:
```bash
# Basic usage (run from project root)
python src/viz/agency_network_viz.py

# Limit nodes per agency for performance
python src/viz/agency_network_viz.py --max-nodes 500

# Custom output directory
python src/viz/agency_network_viz.py --output-dir /custom/path/
```

**Available Agencies** (via dropdown):
- Department of Administration (~392 KB)
- Department of Agriculture (~4.9 MB)
- Montana Arts Council (~968 KB)
- State Auditor (~2.4 MB)
- Department of Commerce (~8.2 MB)
- Department of Corrections (~3.2 MB)
- Department of Environmental Quality (~4.2 MB)
- State Human Resources Division (~600 KB)
- Department of Labor & Industry (~3.0 MB)

**Output Files**:
- `html/agency-navigation.html` - Main HTML file (~32 KB)
- `html/agency-data/*.json` - Individual agency data files (9 files, ~28 MB total)

**Viewing the Visualization**:

Due to browser security restrictions (CORS), the visualization must be served via HTTP:

```bash
# Option 1: Use the provided helper script (from project root)
./serve_visualization.sh

# Option 2: Manually start Python's HTTP server
cd html
python3 -m http.server 8000

# Then open in your browser:
# http://localhost:8000/agency-navigation.html
```

**Note**: Opening the HTML file directly (file://) won't work due to browser security that blocks loading JSON files via fetch().

**Interactive Features**:
1. **Agency Selector**: Dropdown menu showing all 9 agencies with document counts
2. **Dynamic Loading**: Agency data fetched asynchronously when selected
3. **Node Labels**: Always-visible titles for all documents
4. **Click Nodes**: Opens detailed metadata panel with:
   - Full document information
   - Topics and keywords (as tags)
   - Network statistics (PageRank, degree, word count)
   - Content preview (first 200 chars)
   - **Primary action button**: "View Source Document"
   - **Copy URL button**: Copy link to clipboard
5. **Controls**: Reset view, toggle physics, filter by type
6. **Tooltips**: Quick info on hover
7. **Zoom/Pan**: Interactive exploration

**Requirements**:
- Pre-built knowledge graph: `src/network/exports/montana_knowledge.pkl`
- Run `python src/network/3_build_network.py` first if needed

**Example Output**:
```
============================================================
Agency Network Visualizer - Multi-Agency Selector
============================================================
Loading knowledge graph from: src/network/exports/montana_knowledge.pkl
✓ Graph loaded: 7,595 nodes, 223,805 edges

Preparing visualization for all agencies...
Generating agency data files...
  ✓ administration: 392.5 KB
  ✓ agriculture: 4976.5 KB
  ✓ arts-council: 968.0 KB
  ✓ auditor: 2412.6 KB
  ✓ commerce: 8434.8 KB
  ✓ corrections: 3263.2 KB
  ✓ environmental-quality: 4348.6 KB
  ✓ human-resources: 600.4 KB
  ✓ labor-industry: 3090.1 KB

Generating agency selector HTML...
✓ Generated agency selector HTML (31.8 KB)

Saved to: html/agency-navigation.html
✓ Agency data files: html/agency-data/
✓ Complete! Open in browser to view.
✓ All 9 agencies load on-demand from separate JSON files
============================================================
```

**Performance Notes**:
- HTML file size: ~32 KB (minimal - just the interface)
- Agency data files: 9 separate JSON files (~28 MB total)
- Loading time: Instant HTML load, fast agency data fetch (~100-500ms per agency)
- Caching: Agency data cached in browser after first load
- No server required: Can be served from any static web server or opened directly

## 🎨 Network Visualization

### Purpose
Creates static network graph visualizations showing the structure and connections within the Montana government knowledge base.

### Script: `visualize_network.py`

**Features**:
- Reads markdown files from `knowledge/` directory
- Extracts links and metadata
- Builds NetworkX graph
- Generates force-directed layout visualization
- Color-codes nodes by document type and agency
- Saves as PNG image

**Usage**:
```bash
# Generate network visualization
python src/viz/visualize_network.py

# Or with shebang
./src/viz/visualize_network.py
```

**Output**:
- `html/knowledge_network.png` - Static network graph image
- `html/knowledge_network.html` - Interactive HTML visualization
- Console output with network statistics

**Visualization Features**:
- **Node Colors**:
  - Blue: HTML pages
  - Red: PDF documents
  - Green: DOCX documents
  - Yellow: Index pages
- **Node Sizes**: Proportional to number of connections
- **Edges**: Gray lines showing hyperlinks
- **Layout**: Force-directed (spring layout)

**Example Output**:
```
Building network graph from knowledge/
  Processing administration/ (245 files)
  Processing human-resources/ (189 files)
  ...
Network Statistics:
  Nodes: 7,586
  Edges: 12,433
  Density: 0.0043
  Components: 3
Visualization saved to html/knowledge_network.png
Interactive visualization saved to html/knowledge_network.html
```

### Technical Details

**Algorithm**: Spring force-directed layout (Fruchterman-Reingold)
- Attractive forces between connected nodes
- Repulsive forces between all nodes
- Iterative optimization for visual clarity

**Performance**:
- Small networks (<500 nodes): <10 seconds
- Medium networks (500-2000 nodes): 30-60 seconds
- Large networks (>2000 nodes): 2-5 minutes

**Dependencies**:
- NetworkX - Graph data structure
- Matplotlib - Visualization rendering
- BeautifulSoup - HTML parsing

## 📊 Presentation Generator

### Purpose
Automatically generates professional PowerPoint presentations describing services provided by each Montana state agency.

### Script: `presentation_generator.py`

**Features**:
- Reads crawled content from `knowledge/` directory
- Analyzes service offerings by category
- Creates 30-minute presentation template
- Professional Montana government styling
- Exports to PowerPoint (.pptx) format

**Usage**:
```bash
# Generate presentations for all agencies
python src/viz/presentation_generator.py

# Generate for specific agency
python src/viz/presentation_generator.py agriculture

# Or with shebang
./src/viz/presentation_generator.py commerce
```

**Output**:
- `presentations/{agency}/{agency}_presentation.pptx` - PowerPoint file
- `presentations/{agency}/{agency}_presentation.md` - Markdown source
- Console output with generation progress

**Presentation Structure**:
1. **Title Slide** - Agency name and logo
2. **Overview Slide** - Mission and scope
3. **Service Category Slides** - By type (Citizen, Business, Government)
4. **Service Detail Slides** - Specific services with descriptions
5. **Contact Slide** - How to reach the agency
6. **Resources Slide** - Additional information

**Example Output**:
```
Generating presentations for Montana State Agencies...

Processing Department of Commerce...
  Found 47 services across 5 categories
  Created 12-slide presentation
  Saved to presentations/commerce/commerce_presentation.pptx

Processing Department of Agriculture...
  Found 32 services across 4 categories
  Created 10-slide presentation
  Saved to presentations/agriculture/agriculture_presentation.pptx

Complete! Generated 9 presentations.
```

### Presentation Features

**Visual Design**:
- **Color Scheme**: Montana government blue and gray palette
  - Primary Blue: #003F87 (titles)
  - Secondary Blue: #4A90E2 (accents)
  - Dark Gray: #333333 (body text)
  - Light Gray: #E5E5E5 (backgrounds)
- **Fonts**: Calibri (sans-serif, professional)
- **Layout**: Clean, modern, government-appropriate

**Content Organization**:
- **Service Categories**:
  - Citizen Services
  - Business Services
  - Government Services
  - Programs & Initiatives
  - Resources & Forms
- **Service Attributes**:
  - Service name
  - Description
  - Access method (Online, In-Person, Phone, Mail)
  - Target audience

**Customization**:
- Edit `presentation_generator.py` to adjust:
  - Color schemes
  - Slide layouts
  - Content extraction rules
  - Service categorization

## 🚀 Quick Start Examples

### Create Network Visualization

```bash
# Navigate to project root
cd "/Users/CMC096/Library/CloudStorage/OneDrive-MT/Documents/dev/hr knowledge"

# Generate visualization
python visualizations/visualize_network.py

# View result
open knowledge_network.png
```

### Generate All Presentations

```bash
# Generate presentations for all agencies
python visualizations/presentation_generator.py

# Open presentations directory
open presentations/
```

### Generate Single Agency Presentation

```bash
# Generate for Human Resources only
python visualizations/presentation_generator.py human-resources

# Open the presentation
open presentations/human-resources/human-resources_presentation.pptx
```

## 🔧 Configuration

### Network Visualization Settings

Edit `visualize_network.py` to customize:

```python
# Line ~50: Adjust figure size
plt.figure(figsize=(20, 20))  # Larger = more detail

# Line ~70: Change layout algorithm
pos = nx.spring_layout(G, k=0.5, iterations=100)

# Line ~80: Adjust node sizes
nx.draw_networkx_nodes(G, pos, node_size=100)

# Line ~90: Customize colors
color_map = {
    'html': '#1f77b4',  # Blue
    'pdf': '#ff7f0e',   # Orange
    'docx': '#2ca02c'   # Green
}
```

### Presentation Customization

Edit `presentation_generator.py` to customize:

```python
# Line ~30: Color scheme
COLORS = {
    'primary': '#003F87',    # Montana blue
    'secondary': '#4A90E2',  # Light blue
    'text': '#333333'        # Dark gray
}

# Line ~100: Service categories
SERVICE_CATEGORIES = [
    'Citizen Services',
    'Business Services',
    'Government Services',
    'Programs',
    'Resources'
]

# Line ~200: Slide layout
SLIDES_PER_PRESENTATION = 15
SERVICES_PER_SLIDE = 4
```

## 📊 Output Files

### Network Visualization Output
- **Location**: Project root (`knowledge_network.png`)
- **Format**: PNG image
- **Resolution**: High-res (20x20 inches, 300 DPI)
- **Size**: 5-15 MB depending on complexity

### Presentation Output
- **Location**: `presentations/{agency}/`
- **Formats**:
  - PowerPoint (.pptx) - Final presentation
  - Markdown (.md) - Source content outline
- **Size**: 100-500 KB per presentation

## 🔍 Comparison with Network System

### `visualizations/` vs `network/`

| Feature | visualizations/ | network/ |
|---------|----------------|----------|
| **Purpose** | Standalone visual tools | Complete knowledge graph system |
| **Complexity** | Simple, single-purpose scripts | Multi-phase pipeline |
| **Dependencies** | Minimal (NetworkX, matplotlib) | Extensive (numpy, scipy, etc.) |
| **Output** | Static images, PowerPoints | Interactive HTML, exports, RAG |
| **Use Case** | Quick visualizations, presentations | AI/RAG, advanced analysis |
| **Execution Time** | <5 minutes | 3-20 minutes |
| **Memory Use** | <500 MB | 2-4 GB |

**When to Use visualizations/**:
- ✅ Need quick static network graph
- ✅ Want PowerPoint presentations
- ✅ Don't need interactive features
- ✅ Simple visualization for reports

**When to Use network/**:
- ✅ Building AI/RAG system
- ✅ Need interactive exploration
- ✅ Advanced network analysis
- ✅ Semantic search and retrieval

## 🐛 Troubleshooting

### Issue: Visualization Too Cluttered

**Problem**: Too many nodes overlap in visualization

**Solution**: Filter nodes before visualizing
```python
# Edit visualize_network.py, add filtering
if len(G.nodes()) > 1000:
    # Keep only highly connected nodes
    degrees = dict(G.degree())
    important_nodes = [n for n, d in degrees.items() if d > 5]
    G = G.subgraph(important_nodes)
```

### Issue: Presentation Missing Content

**Problem**: Generated presentation has few slides

**Solution**: Check if agency content was crawled
```bash
# Verify agency directory exists and has content
ls -la knowledge/{agency-name}/
```

If empty, crawl the agency:
```bash
python src/extract/2_refresh.py {agency-name}
```

### Issue: Font Errors in PowerPoint

**Problem**: "Calibri font not found" error

**Solution**: Presentations use Calibri by default (installed on most systems)
To use different font, edit `presentation_generator.py`:
```python
# Line ~150: Change font
from pptx.util import Pt
font.name = "Arial"  # Or another available font
```

### Issue: Out of Memory

**Problem**: Visualization crashes with large networks

**Solution**: Reduce node count or use network system
```bash
# Use network system for large graphs
python src/network/build_network.py
open network/visualizations/montana_network_interactive.html
```

## 🔗 Related Files

- **`../../README.md`** - Master project documentation
- **`../../knowledge/README.md`** - Source content structure
- **`../network/README.md`** - Advanced network system
- **`../../presentations/README.md`** - Generated presentations
- **`../network/3_build_network.py`** - Main network builder

## 📝 Development Notes

### Adding New Visualization Types

To add a new visualization:

1. Create new script in `visualizations/`
2. Follow naming pattern: `{purpose}_generator.py`
3. Add shebang for direct execution
4. Import from `knowledge/` directory
5. Save output to appropriate location
6. Document in this README

### Extending Presentation Generator

To add features to presentations:

1. Edit `presentation_generator.py`
2. Add new content extraction logic
3. Create new slide templates
4. Update service categorization
5. Test with multiple agencies
6. Document changes

### Performance Optimization

For large networks:
- Sample nodes before visualization
- Use iterative layout algorithms
- Reduce edge rendering complexity
- Export to vector format (SVG) instead of raster (PNG)

## 📄 License & Notes

- Visualizations are generated from public Montana government content
- PowerPoint presentations are for government use
- Scripts are maintained by Montana State IT
- Color schemes follow Montana government brand guidelines

---

**Directory Purpose**: Standalone visualization and presentation tools  
**Primary Use**: Quick visualizations, PowerPoint generation  
**Complementary To**: `network/` system (advanced features)  
**Last Updated**: December 2025
