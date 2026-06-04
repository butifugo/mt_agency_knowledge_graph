"""
Knowledge Graph Visualizer
Creates interactive D3.js network visualizations
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class KnowledgeVisualizer:
    """Creates interactive D3.js visualization from knowledge graphs"""
    
    # Agency display names
    AGENCIES = {
        'administration': 'Department of Administration',
        'agriculture': 'Department of Agriculture',
        'arts-council': 'Montana Arts Council',
        'auditor': 'State Auditor',
        'commerce': 'Department of Commerce',
        'corrections': 'Department of Corrections',
        'environmental-quality': 'Department of Environmental Quality',
        'human-resources': 'State Human Resources Division',
        'labor-industry': 'Department of Labor & Industry'
    }
    
    def __init__(self, knowledge_dir: str = "data/graphs/knowledge", output_dir: str = "html"):
        """
        Initialize visualizer
        
        Args:
            knowledge_dir: Directory containing knowledge graph JSONs
            output_dir: Output directory for HTML visualizations
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_knowledge_graph(self, agency: str) -> Optional[Dict]:
        """Load knowledge graph JSON for agency"""
        graph_file = self.knowledge_dir / f"{agency}_knowledge.json"
        
        if not graph_file.exists():
            return None
        
        with open(graph_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def prepare_viz_data(self, graph_data: Dict, max_nodes: Optional[int] = 500) -> Dict:
        """
        Prepare graph data for visualization
        
        Args:
            graph_data: Knowledge graph data
            max_nodes: Maximum nodes to include
            
        Returns:
            Dict with nodes and edges for D3.js
        """
        nodes = graph_data.get('nodes', {})
        edges = graph_data.get('edges', [])
        
        # Filter to most important nodes if needed
        if max_nodes and len(nodes) > max_nodes:
            # Sort by keyword count and edge count
            node_items = list(nodes.items())
            node_items.sort(
                key=lambda x: (len(x[1].get('keywords', [])), len([e for e in edges if e['source'] == x[0] or e['target'] == x[0]])),
                reverse=True
            )
            selected_nodes = dict(node_items[:max_nodes])
            selected_node_ids = set(selected_nodes.keys())
            
            # Filter edges to only include selected nodes
            filtered_edges = [
                e for e in edges 
                if e['source'] in selected_node_ids and e['target'] in selected_node_ids
            ]
        else:
            selected_nodes = nodes
            filtered_edges = edges
            selected_node_ids = set(nodes.keys())
        
        # Create node index mapping
        node_list = []
        node_index = {}
        
        for idx, (node_id, node_data) in enumerate(selected_nodes.items()):
            node_index[node_id] = idx
            
            # Calculate node size based on connections
            in_degree = len([e for e in filtered_edges if e['target'] == node_id])
            out_degree = len([e for e in filtered_edges if e['source'] == node_id])
            
            node_type = node_data.get('type', 'html_page')
            if node_type == 'html_page':
                size = min(20 + in_degree * 2, 50)
            else:
                size = min(10 + in_degree, 30)
            
            node_list.append({
                'id': node_id,
                'index': idx,
                'title': node_data.get('title', 'Untitled'),
                'type': node_type,
                'agency': node_data.get('agency', ''),
                'url': node_data.get('url', ''),
                'keywords': node_data.get('keywords', [])[:5],
                'size': size,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'word_count': node_data.get('word_count', 0)
            })
        
        # Create edge list with indices
        edge_list = []
        for edge in filtered_edges:
            source_id = edge['source']
            target_id = edge['target']
            
            if source_id in node_index and target_id in node_index:
                edge_list.append({
                    'source': node_index[source_id],
                    'target': node_index[target_id],
                    'type': edge.get('type', 'hyperlink'),
                    'weight': edge.get('weight', 1.0)
                })
        
        return {
            'nodes': node_list,
            'edges': edge_list,
            'stats': {
                'total_nodes': len(node_list),
                'total_edges': len(edge_list),
                'total_words': sum(n['word_count'] for n in node_list)
            }
        }
    
    def generate_html(self, viz_data: Dict, agency: str, title: str) -> str:
        """Generate interactive HTML visualization"""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #0a0e27;
            color: #e0e0e0;
            overflow: hidden;
        }}
        
        #container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        
        #stats {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(20, 25, 45, 0.9);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid rgba(100, 150, 255, 0.3);
            min-width: 200px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }}
        
        #stats h2 {{
            margin: 0 0 15px 0;
            font-size: 18px;
            color: #6495ed;
        }}
        
        #stats .stat-row {{
            margin: 8px 0;
            font-size: 14px;
        }}
        
        #stats .stat-label {{
            color: #888;
        }}
        
        #stats .stat-value {{
            color: #fff;
            font-weight: bold;
        }}
        
        #legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(20, 25, 45, 0.9);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid rgba(100, 150, 255, 0.3);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }}
        
        #legend h3 {{
            margin: 0 0 15px 0;
            font-size: 16px;
            color: #6495ed;
        }}
        
        .legend-item {{
            margin: 10px 0;
            display: flex;
            align-items: center;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        
        #tooltip {{
            position: absolute;
            background: rgba(20, 25, 45, 0.95);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(100, 150, 255, 0.5);
            pointer-events: none;
            display: none;
            max-width: 300px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.7);
        }}
        
        #tooltip .title {{
            font-weight: bold;
            color: #6495ed;
            margin-bottom: 8px;
        }}
        
        #tooltip .detail {{
            font-size: 12px;
            margin: 4px 0;
            color: #ccc;
        }}
        
        /* Modal styles */
        #modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            animation: fadeIn 0.3s;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        #modal-content {{
            position: relative;
            background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%);
            margin: 5% auto;
            padding: 0;
            border: 2px solid rgba(100, 150, 255, 0.5);
            border-radius: 12px;
            width: 90%;
            max-width: 700px;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 10px 50px rgba(0, 0, 0, 0.9);
            animation: slideIn 0.3s;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateY(-50px);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}
        
        #modal-header {{
            background: linear-gradient(135deg, #2d3561 0%, #3d4571 100%);
            padding: 25px;
            border-bottom: 2px solid rgba(100, 150, 255, 0.3);
            border-radius: 10px 10px 0 0;
        }}
        
        #modal-header h2 {{
            margin: 0;
            color: #6495ed;
            font-size: 22px;
            word-wrap: break-word;
        }}
        
        #modal-header .node-type {{
            display: inline-block;
            margin-top: 8px;
            padding: 4px 12px;
            background: rgba(100, 150, 255, 0.2);
            border-radius: 12px;
            font-size: 12px;
            color: #9bb3ff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .close-modal {{
            position: absolute;
            top: 20px;
            right: 20px;
            color: #aaa;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.2s;
            line-height: 1;
        }}
        
        .close-modal:hover {{
            color: #fff;
        }}
        
        #modal-body {{
            padding: 25px;
        }}
        
        .info-section {{
            margin-bottom: 25px;
        }}
        
        .info-section h3 {{
            color: #6495ed;
            font-size: 16px;
            margin: 0 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(100, 150, 255, 0.2);
        }}
        
        .info-row {{
            display: grid;
            grid-template-columns: 140px 1fr;
            gap: 10px;
            margin: 8px 0;
            font-size: 14px;
        }}
        
        .info-label {{
            color: #9bb3ff;
            font-weight: 500;
        }}
        
        .info-value {{
            color: #ddd;
            word-wrap: break-word;
        }}
        
        .keywords-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }}
        
        .keyword-tag {{
            display: inline-block;
            padding: 4px 10px;
            background: rgba(100, 150, 255, 0.2);
            border-radius: 12px;
            font-size: 12px;
            color: #9bb3ff;
        }}
        
        .url-link {{
            color: #6495ed;
            text-decoration: none;
            word-break: break-all;
            transition: color 0.2s;
        }}
        
        .url-link:hover {{
            color: #8bb3ff;
            text-decoration: underline;
        }}
        
        .connections-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }}
        
        .connection-card {{
            background: rgba(100, 150, 255, 0.1);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(100, 150, 255, 0.2);
        }}
        
        .connection-title {{
            font-size: 12px;
            color: #9bb3ff;
            margin-bottom: 6px;
            font-weight: 500;
        }}
        
        .connection-value {{
            font-size: 20px;
            color: #fff;
            font-weight: bold;
        }}
        
        .node {{
            stroke: #fff;
            stroke-width: 1.5px;
            cursor: pointer;
        }}
        
        .link {{
            stroke: rgba(100, 150, 255, 0.2);
            stroke-width: 1px;
        }}
        
        .link.semantic {{
            stroke: rgba(255, 100, 150, 0.3);
            stroke-dasharray: 3, 3;
        }}
    </style>
</head>
<body>
    <div id="container">
        <svg id="network"></svg>
        
        <div id="stats">
            <h2>{agency.replace('-', ' ').title()}</h2>
            <div class="stat-row">
                <span class="stat-label">Nodes:</span>
                <span class="stat-value">{viz_data['stats']['total_nodes']}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Edges:</span>
                <span class="stat-value">{viz_data['stats']['total_edges']}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Total Words:</span>
                <span class="stat-value">{viz_data['stats']['total_words']:,}</span>
            </div>
        </div>
        
        <div id="legend">
            <h3>Node Types</h3>
            <div class="legend-item">
                <div class="legend-color" style="background: #6495ed;"></div>
                <span>HTML Pages</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffa500;"></div>
                <span>PDF Documents</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #9370db;"></div>
                <span>DOCX Documents</span>
            </div>
        </div>
        
        <div id="tooltip"></div>
        
        <!-- Modal for node details -->
        <div id="modal">
            <div id="modal-content">
                <div id="modal-header">
                    <span class="close-modal">&times;</span>
                    <h2 id="modal-title"></h2>
                    <span class="node-type" id="modal-type"></span>
                </div>
                <div id="modal-body"></div>
            </div>
        </div>
    </div>
    
    <script>
        const graphData = {json.dumps(viz_data)};
        
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        const svg = d3.select("#network")
            .attr("width", width)
            .attr("height", height);
        
        const tooltip = d3.select("#tooltip");
        
        // Color scale
        const colorScale = {{
            'html_page': '#6495ed',
            'pdf_document': '#ffa500',
            'docx_document': '#9370db'
        }};
        
        // Create force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges)
                .id(d => d.index)
                .distance(d => d.type === 'semantic_similar' ? 150 : 100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 5));
        
        // Create edges
        const link = svg.append("g")
            .selectAll("line")
            .data(graphData.edges)
            .enter()
            .append("line")
            .attr("class", d => `link ${{d.type}}`)
            .attr("stroke-opacity", d => d.type === 'hyperlink' ? 0.6 : 0.3);
        
        // Create nodes
        const node = svg.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter()
            .append("circle")
            .attr("class", "node")
            .attr("r", d => d.size)
            .attr("fill", d => colorScale[d.type] || '#999')
            .call(drag(simulation))
            .on("mouseover", showTooltip)
            .on("mousemove", moveTooltip)
            .on("mouseout", hideTooltip)
            .on("click", nodeClick);
        
        // Update positions on simulation tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
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
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }}
        
        // Tooltip functions
        function showTooltip(event, d) {{
            const keywords = d.keywords.length > 0 ? d.keywords.join(', ') : 'None';
            
            tooltip
                .style("display", "block")
                .html(`
                    <div class="title">${{d.title}}</div>
                    <div class="detail"><strong>Type:</strong> ${{d.type.replace('_', ' ')}}</div>
                    <div class="detail"><strong>Words:</strong> ${{d.word_count.toLocaleString()}}</div>
                    <div class="detail"><strong>Connections:</strong> In: ${{d.in_degree}}, Out: ${{d.out_degree}}</div>
                    <div class="detail"><strong>Keywords:</strong> ${{keywords}}</div>
                `);
        }}
        
        function moveTooltip(event) {{
            tooltip
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY + 15) + "px");
        }}
        
        function hideTooltip() {{
            tooltip.style("display", "none");
        }}
        
        function nodeClick(event, d) {{
            event.stopPropagation();
            showModal(d);
        }}
        
        // Modal functions
        function showModal(node) {{
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modal-title');
            const modalType = document.getElementById('modal-type');
            const modalBody = document.getElementById('modal-body');
            
            // Set header
            modalTitle.textContent = node.title || 'Untitled';
            modalType.textContent = (node.type || 'unknown').replace('_', ' ');
            
            // Build body content
            let bodyHTML = '';
            
            // Basic Information Section
            bodyHTML += `
                <div class="info-section">
                    <h3>📄 Document Information</h3>
                    <div class="info-row">
                        <span class="info-label">Document ID:</span>
                        <span class="info-value">${{node.id || 'N/A'}}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Type:</span>
                        <span class="info-value">${{(node.type || 'unknown').replace('_', ' ')}}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Word Count:</span>
                        <span class="info-value">${{(node.word_count || 0).toLocaleString()}} words</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">URL:</span>
                        <span class="info-value">
                            ${{node.url ? `<a href="${{node.url}}" target="_blank" class="url-link">${{node.url}}</a>` : 'N/A'}}
                        </span>
                    </div>
                </div>
            `;
            
            // Network Connections Section
            bodyHTML += `
                <div class="info-section">
                    <h3>🔗 Network Connections</h3>
                    <div class="connections-grid">
                        <div class="connection-card">
                            <div class="connection-title">Incoming Links</div>
                            <div class="connection-value">${{node.in_degree || 0}}</div>
                        </div>
                        <div class="connection-card">
                            <div class="connection-title">Outgoing Links</div>
                            <div class="connection-value">${{node.out_degree || 0}}</div>
                        </div>
                        <div class="connection-card">
                            <div class="connection-title">Total Connections</div>
                            <div class="connection-value">${{(node.in_degree || 0) + (node.out_degree || 0)}}</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Keywords Section
            if (node.keywords && node.keywords.length > 0) {{
                bodyHTML += `
                    <div class="info-section">
                        <h3>🏷️ Keywords (${{node.keywords.length}})</h3>
                        <div class="keywords-list">
                            ${{node.keywords.map(kw => `<span class="keyword-tag">${{kw}}</span>`).join('')}}
                        </div>
                    </div>
                `;
            }} else {{
                bodyHTML += `
                    <div class="info-section">
                        <h3>🏷️ Keywords</h3>
                        <div class="info-value">No keywords extracted</div>
                    </div>
                `;
            }}
            
            // Additional metadata if available
            if (node.metadata) {{
                bodyHTML += `
                    <div class="info-section">
                        <h3>ℹ️ Additional Metadata</h3>
                `;
                for (const [key, value] of Object.entries(node.metadata)) {{
                    bodyHTML += `
                        <div class="info-row">
                            <span class="info-label">${{key}}:</span>
                            <span class="info-value">${{value}}</span>
                        </div>
                    `;
                }}
                bodyHTML += `</div>`;
            }}
            
            modalBody.innerHTML = bodyHTML;
            modal.style.display = 'block';
            
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
        }}
        
        function closeModal() {{
            const modal = document.getElementById('modal');
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }}
        
        // Close modal when clicking X
        document.querySelector('.close-modal').onclick = closeModal;
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('modal');
            if (event.target === modal) {{
                closeModal();
            }}
        }}
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>"""
        
        return html
    
    def create_visualization(self, agency: str, max_nodes: Optional[int] = 500, verbose: bool = True):
        """
        Create visualization for an agency
        
        Args:
            agency: Agency name
            max_nodes: Maximum nodes to include
            verbose: Print progress
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"Creating Knowledge Visualization: {agency}")
            print(f"{'='*80}\n")
        
        # Load knowledge graph
        graph_data = self.load_knowledge_graph(agency)
        
        if not graph_data:
            if verbose:
                print(f"✗ Knowledge graph not found for {agency}")
            return None
        
        if verbose:
            print(f"Loaded knowledge graph")
            print(f"  Nodes: {len(graph_data.get('nodes', {}))}")
            print(f"  Edges: {len(graph_data.get('edges', []))}")
        
        # Prepare visualization data
        viz_data = self.prepare_viz_data(graph_data, max_nodes=max_nodes)
        
        if verbose:
            print(f"\nFiltered to {viz_data['stats']['total_nodes']} nodes")
            print(f"  {viz_data['stats']['total_edges']} edges")
        
        # Generate HTML
        display_name = self.AGENCIES.get(agency, agency.replace('-', ' ').title())
        title = f"{display_name} - Knowledge Network"
        html_content = self.generate_html(viz_data, agency, title)
        
        # Save to file
        output_file = self.output_dir / f"{agency}-knowledge-viz.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if verbose:
            print(f"\n✓ Visualization saved: {output_file}")
            print(f"{'='*80}\n")
        
        return output_file
    
    def create_multi_agency_selector(self, agencies: List[str], verbose: bool = True):
        """Create a selector page for multiple agencies"""
        if verbose:
            print(f"\n{'='*80}")
            print(f"Creating Multi-Agency Selector")
            print(f"{'='*80}\n")
        
        # Build agency links
        agency_links = []
        for agency in agencies:
            display_name = self.AGENCIES.get(agency, agency.replace('-', ' ').title())
            viz_file = f"{agency}-knowledge-viz.html"
            agency_links.append((display_name, viz_file))
        
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Montana Knowledge Network - Agency Selector</title>
    <style>
        body {
            margin: 0;
            padding: 40px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            color: #6495ed;
            font-size: 36px;
            margin-bottom: 50px;
        }
        
        .agency-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        
        .agency-card {
            background: rgba(20, 25, 45, 0.8);
            padding: 30px;
            border-radius: 12px;
            border: 1px solid rgba(100, 150, 255, 0.3);
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .agency-card:hover {
            transform: translateY(-5px);
            border-color: rgba(100, 150, 255, 0.6);
            box-shadow: 0 8px 30px rgba(100, 150, 255, 0.3);
        }
        
        .agency-card a {
            color: #6495ed;
            text-decoration: none;
            font-size: 18px;
            font-weight: 500;
        }
        
        .agency-card:hover a {
            color: #87ceeb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Montana State Government Knowledge Network</h1>
        <div class="agency-grid">
"""
        
        for display_name, viz_file in agency_links:
            html += f"""
            <div class="agency-card" onclick="window.location.href='{viz_file}'">
                <a href="{viz_file}">{display_name}</a>
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        output_file = self.output_dir / "knowledge-network-selector.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        if verbose:
            print(f"✓ Multi-agency selector saved: {output_file}")
            print(f"{'='*80}\n")
        
        return output_file
