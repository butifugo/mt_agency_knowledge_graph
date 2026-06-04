"""
HTML Navigation Visualizer
Creates force-directed network visualization with MIME-type based node sizing
"""

import json
from pathlib import Path
from typing import Dict, Optional


class HTMLNavigationVisualizer:
    """
    Generate force-directed D3.js visualization of HTML navigation
    with node size based on MIME type hierarchy:
    - Domain (root): Largest
    - HTML pages: Medium
    - Documents (PDF/DOCX): Smallest
    """
    
    def __init__(self, data_dir: str = "data/graphs/navigation", output_dir: str = "html"):
        """
        Initialize visualizer
        
        Args:
            data_dir: Directory containing navigation JSON files
            output_dir: Directory for HTML output
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / data_dir
        self.output_dir = self.project_root / output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def load_navigation_data(self, agency: str) -> Dict:
        """Load HTML navigation data for agency"""
        data_file = self.data_dir / f"{agency}_html_navigation.json"
        
        if not data_file.exists():
            raise FileNotFoundError(f"Navigation data not found: {data_file}")
        
        with open(data_file, 'r') as f:
            return json.load(f)
    
    def generate_visualization(self, agency: str, output_file: Optional[str] = None) -> Path:
        """
        Generate force-directed visualization
        
        Args:
            agency: Agency name
            output_file: Optional custom output filename
            
        Returns:
            Path to generated HTML file
        """
        # Load data
        data = self.load_navigation_data(agency)
        
        # Prepare output file
        if not output_file:
            output_file = f"{agency}-html-navigation.html"
        output_path = self.output_dir / output_file
        
        # Get statistics
        stats = data.get('statistics', {})
        base_domain = data.get('base_domain', '')
        
        # Convert to D3 format
        nodes = []
        node_map = {}
        
        for idx, (node_id, node_data) in enumerate(data['nodes'].items()):
            # Determine node size based on type
            if node_data['is_root']:
                size = 50  # Largest for domain root
                group = 'root'
            elif node_data['type'] == 'html_page':
                size = 20  # Medium for HTML pages
                group = 'html'
            elif node_data['type'] == 'pdf_document':
                size = 8  # Small for PDFs
                group = 'pdf'
            elif node_data['type'] == 'docx_document':
                size = 8  # Small for DOCX
                group = 'docx'
            else:
                size = 6  # Smallest for other docs
                group = 'other'
            
            nodes.append({
                'id': node_id,
                'name': node_data['title'],
                'url': node_data['url'],
                'type': node_data['type'],
                'mime_type': node_data['mime_type'],
                'is_root': node_data['is_root'],
                'size': size,
                'group': group
            })
            node_map[node_id] = idx
        
        # Convert edges (links)
        links = []
        for edge in data['edges']:
            source = edge['source']
            target = edge['target']
            
            # Only include edges where both nodes exist
            if source in node_map and target in node_map:
                links.append({
                    'source': source,
                    'target': target,
                    'label': edge.get('link_text', '')
                })
        
        # Generate HTML
        html_content = self._generate_html(
            agency=agency,
            nodes=nodes,
            links=links,
            stats=stats,
            base_domain=base_domain
        )
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Generated visualization: {output_path}")
        return output_path
    
    def _generate_html(self, agency: str, nodes: list, links: list, stats: dict, base_domain: str) -> str:
        """Generate complete HTML with embedded D3.js visualization"""
        
        nodes_json = json.dumps(nodes, indent=2)
        links_json = json.dumps(links, indent=2)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agency.title()} - HTML Navigation Map</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #333;
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 20px;
        }}
        
        header {{
            background: white;
            padding: 20px 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            margin-bottom: 20px;
        }}
        
        h1 {{
            font-size: 28px;
            color: #1e3c72;
            margin-bottom: 8px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        
        .stats {{
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
            font-size: 13px;
        }}
        
        .stat {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .stat-label {{
            color: #888;
        }}
        
        .stat-value {{
            font-weight: 600;
            color: #1e3c72;
        }}
        
        .controls {{
            background: white;
            padding: 15px 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .controls button {{
            padding: 8px 16px;
            background: #1e3c72;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .controls button:hover {{
            background: #2a5298;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        
        .controls button:active {{
            transform: translateY(0);
        }}
        
        #graph {{
            flex: 1;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            position: relative;
            overflow: hidden;
        }}
        
        .legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-size: 12px;
            z-index: 10;
        }}
        
        .legend h3 {{
            font-size: 13px;
            margin-bottom: 10px;
            color: #333;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }}
        
        .legend-circle {{
            border-radius: 50%;
            border: 2px solid #666;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 10px 15px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 300px;
            z-index: 100;
        }}
        
        .tooltip.visible {{
            opacity: 1;
        }}
        
        .tooltip-title {{
            font-weight: 600;
            margin-bottom: 5px;
            color: #fff;
        }}
        
        .tooltip-info {{
            color: #ccc;
            font-size: 11px;
        }}
        
        .node {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .node:hover {{
            stroke: #000;
            stroke-width: 3px;
        }}
        
        .node.root {{
            fill: #e53935;
        }}
        
        .node.html {{
            fill: #1e88e5;
        }}
        
        .node.pdf {{
            fill: #fb8c00;
        }}
        
        .node.docx {{
            fill: #8e24aa;
        }}
        
        .node.other {{
            fill: #43a047;
        }}
        
        .node.connected {{
            stroke: #ff9800 !important;
            stroke-width: 4px !important;
        }}
        
        .node.dimmed {{
            opacity: 0.15;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.3;
            stroke-width: 1px;
        }}
        
        .link.highlighted {{
            stroke: #ff9800;
            stroke-opacity: 1;
            stroke-width: 3px;
        }}
        
        .link.dimmed {{
            opacity: 0.05;
        }}
        
        .node-label {{
            font-size: 10px;
            fill: #333;
            pointer-events: none;
            text-anchor: middle;
            opacity: 0;
        }}
        
        .node-label.visible {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{agency.title()} Department</h1>
            <div class="subtitle">HTML Navigation Structure · {base_domain}</div>
            <div class="stats">
                <div class="stat">
                    <span class="stat-label">Total Pages:</span>
                    <span class="stat-value">{stats.get('total_nodes', 0):,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">HTML Pages:</span>
                    <span class="stat-value">{stats.get('html_pages', 0):,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">PDF Documents:</span>
                    <span class="stat-value">{stats.get('pdf_documents', 0):,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">DOCX Documents:</span>
                    <span class="stat-value">{stats.get('docx_documents', 0):,}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Links:</span>
                    <span class="stat-value">{stats.get('total_edges', 0):,}</span>
                </div>
            </div>
        </header>
        
        <div class="controls">
            <button onclick="resetSimulation()">Reset View</button>
            <button onclick="toggleLabels()">Toggle Labels</button>
            <button onclick="clearHighlight()">Clear Highlight</button>
            <button onclick="filterByType('all')">Show All</button>
            <button onclick="filterByType('html')">HTML Only</button>
            <button onclick="filterByType('documents')">Documents Only</button>
        </div>
        
        <div id="graph">
            <div class="legend">
                <h3>Node Types</h3>
                <div class="legend-item">
                    <div class="legend-circle" style="width: 50px; height: 50px; background: #e53935;"></div>
                    <span>Domain Root</span>
                </div>
                <div class="legend-item">
                    <div class="legend-circle" style="width: 20px; height: 20px; background: #1e88e5;"></div>
                    <span>HTML Page</span>
                </div>
                <div class="legend-item">
                    <div class="legend-circle" style="width: 8px; height: 8px; background: #fb8c00;"></div>
                    <span>PDF Document</span>
                </div>
                <div class="legend-item">
                    <div class="legend-circle" style="width: 8px; height: 8px; background: #8e24aa;"></div>
                    <span>DOCX Document</span>
                </div>
                <div class="legend-item">
                    <div class="legend-circle" style="width: 6px; height: 6px; background: #43a047;"></div>
                    <span>Other</span>
                </div>
            </div>
        </div>
        
        <div class="tooltip" id="tooltip"></div>
    </div>
    
    <script>
        // Data
        const graphData = {{
            nodes: {nodes_json},
            links: {links_json}
        }};
        
        // Dimensions
        const container = document.getElementById('graph');
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        // Create SVG
        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Add zoom behavior
        const g = svg.append('g');
        
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {{
                g.attr('transform', event.transform);
            }});
        
        svg.call(zoom);
        
        // Create force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force('link', d3.forceLink(graphData.links)
                .id(d => d.id)
                .distance(d => {{
                    // Shorter connection lines based on node types
                    const source = graphData.nodes.find(n => n.id === d.source.id || n.id === d.source);
                    const target = graphData.nodes.find(n => n.id === d.target.id || n.id === d.target);
                    if (source && target) {{
                        // Very short for HTML to HTML
                        if (source.type === 'html_page' && target.type === 'html_page') {{
                            return 50;
                        }}
                        // Short for HTML to documents
                        if (source.type === 'html_page' || target.type === 'html_page') {{
                            return 60;
                        }}
                    }}
                    return 70;
                }}))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => d.size + 5));
        
        // Create links
        const link = g.append('g')
            .selectAll('line')
            .data(graphData.links)
            .join('line')
            .attr('class', 'link');
        
        // Create nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(graphData.nodes)
            .join('circle')
            .attr('class', d => `node ${{d.group}}`)
            .attr('r', d => d.size)
            .call(drag(simulation))
            .on('mouseover', showTooltip)
            .on('mouseout', hideTooltip)
            .on('click', handleNodeClick);
        
        // Create labels (hidden by default)
        const labels = g.append('g')
            .selectAll('text')
            .data(graphData.nodes)
            .join('text')
            .attr('class', 'node-label')
            .attr('dy', d => d.size + 12)
            .text(d => d.name.length > 30 ? d.name.substring(0, 30) + '...' : d.name);
        
        // Update positions on tick
        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }});
        
        // Drag behavior
        function drag(simulation) {{
            function dragstarted(event) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }}
            
            function dragged(event) {{
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }}
            
            function dragended(event) {{
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }}
            
            return d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended);
        }}
        
        // Tooltip functions
        const tooltip = document.getElementById('tooltip');
        
        // State for highlighting
        let highlightedNode = null;
        
        function showTooltip(event, d) {{
            const mimeType = d.mime_type === 'text/html' ? 'HTML Page' : 
                           d.mime_type === 'application/pdf' ? 'PDF Document' :
                           d.mime_type.includes('word') ? 'Word Document' : 'Document';
            
            tooltip.innerHTML = `
                <div class="tooltip-title">${{d.name}}</div>
                <div class="tooltip-info">Type: ${{mimeType}}</div>
                <div class="tooltip-info">${{d.url.substring(0, 60)}}...</div>
            `;
            tooltip.classList.add('visible');
            
            // Only highlight on hover if no node is clicked
            if (!highlightedNode) {{
                link.classed('highlighted', l => l.source.id === d.id || l.target.id === d.id);
            }}
        }}
        
        function hideTooltip() {{
            tooltip.classList.remove('visible');
            // Only remove highlight if no node is clicked
            if (!highlightedNode) {{
                link.classed('highlighted', false);
            }}
        }}
        
        function handleNodeClick(event, d) {{
            event.stopPropagation();
            
            // If clicking the same node, clear highlight and open URL
            if (highlightedNode && highlightedNode.id === d.id) {{
                clearHighlight();
                window.open(d.url, '_blank');
                return;
            }}
            
            // Clear previous highlight
            clearHighlight();
            
            // Set new highlighted node
            highlightedNode = d;
            
            // Find all connected nodes (direct connections only)
            const connectedNodes = new Set([d.id]);
            const connectedLinks = new Set();
            
            graphData.links.forEach(l => {{
                if (l.source.id === d.id || l.source === d.id) {{
                    connectedNodes.add(l.target.id || l.target);
                    connectedLinks.add(l);
                }}
                if (l.target.id === d.id || l.target === d.id) {{
                    connectedNodes.add(l.source.id || l.source);
                    connectedLinks.add(l);
                }}
            }});
            
            // Apply highlighting
            node.classed('connected', n => connectedNodes.has(n.id))
                .classed('dimmed', n => !connectedNodes.has(n.id));
            
            link.classed('highlighted', l => connectedLinks.has(l))
                .classed('dimmed', l => !connectedLinks.has(l));
            
            // Show labels for connected nodes
            labels.classed('visible', n => connectedNodes.has(n.id));
        }}
        
        function clearHighlight() {{
            highlightedNode = null;
            node.classed('connected', false)
                .classed('dimmed', false);
            link.classed('highlighted', false)
                .classed('dimmed', false);
            labels.classed('visible', labelsVisible);
        }}
        
        // Click on background to clear highlight
        svg.on('click', () => {{
            clearHighlight();
        }});
        
        // Move tooltip with mouse
        document.addEventListener('mousemove', (e) => {{
            tooltip.style.left = (e.pageX + 15) + 'px';
            tooltip.style.top = (e.pageY + 15) + 'px';
        }});
        
        // Control functions
        let labelsVisible = false;
        
        function toggleLabels() {{
            labelsVisible = !labelsVisible;
            labels.classed('visible', labelsVisible);
        }}
        
        function resetSimulation() {{
            clearHighlight();
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity);
            simulation.alpha(1).restart();
        }}
        
        function filterByType(type) {{
            clearHighlight();
            if (type === 'all') {{
                node.style('opacity', 1);
                link.style('opacity', 0.3);
            }} else if (type === 'html') {{
                node.style('opacity', d => d.type === 'html_page' || d.is_root ? 1 : 0.1);
                link.style('opacity', l => {{
                    const source = l.source.type === 'html_page' || l.source.is_root;
                    const target = l.target.type === 'html_page' || l.target.is_root;
                    return source && target ? 0.6 : 0.05;
                }});
            }} else if (type === 'documents') {{
                node.style('opacity', d => d.type !== 'html_page' ? 1 : 0.1);
                link.style('opacity', l => {{
                    const source = l.source.type !== 'html_page';
                    const target = l.target.type !== 'html_page';
                    return source || target ? 0.6 : 0.05;
                }});
            }}
        }}
        
        // Initial zoom to fit
        setTimeout(() => {{
            const bounds = g.node().getBBox();
            const fullWidth = bounds.width;
            const fullHeight = bounds.height;
            const midX = bounds.x + fullWidth / 2;
            const midY = bounds.y + fullHeight / 2;
            
            const scale = 0.8 / Math.max(fullWidth / width, fullHeight / height);
            const translate = [width / 2 - scale * midX, height / 2 - scale * midY];
            
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        }}, 1000);
    </script>
</body>
</html>"""
    
    def generate_all(self, agencies: list) -> list:
        """Generate visualizations for multiple agencies"""
        generated = []
        
        for agency in agencies:
            try:
                output = self.generate_visualization(agency)
                generated.append(output)
            except FileNotFoundError as e:
                print(f"⚠ Skipping {agency}: {e}")
        
        return generated


if __name__ == '__main__':
    # DEPRECATED: This script now generates standalone files
    # For the unified interactive dashboard, use:
    #   python -m src.phase6_viz_interactive.cli
    
    import sys
    print("=" * 70)
    print("NOTE: Standalone navigation visualizations are deprecated.")
    print("For the best experience, use the unified interactive dashboard:")
    print("  python -m src.phase6_viz_interactive.cli --agencies agriculture")
    print("=" * 70)
    print()
    
    response = input("Generate standalone navigation viz anyway? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled. Use the unified dashboard instead.")
        sys.exit(0)
    
    # Test visualization
    viz = HTMLNavigationVisualizer()
    result = viz.generate_visualization('agriculture')
    print(f"\nGenerated: {result}")

