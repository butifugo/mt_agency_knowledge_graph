"""
D3.js Interactive Visualization - Phase 5
Creates advanced interactive network visualizations
"""

import json
from pathlib import Path
from typing import Optional
from collections import defaultdict

from src.network.schema import KnowledgeGraph, NodeType, EdgeType


class D3Visualizer:
    """Creates D3.js interactive visualizations"""
    
    def __init__(self, graph: KnowledgeGraph, output_dir: str = "html"):
        self.graph = graph
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_force_directed_graph(
        self,
        filename: str = "knowledge_network_d3.html",
        max_nodes: Optional[int] = 1000,
        include_edge_types: Optional[list] = None,
        verbose: bool = True
    ) -> str:
        """Generate D3.js force-directed graph visualization"""
        
        if verbose:
            print(f"Generating D3.js visualization: {filename}")
        
        # Sample nodes if too many
        if max_nodes and len(self.graph.nodes) > max_nodes:
            if verbose:
                print(f"  Sampling {max_nodes} most important nodes...")
            
            # Sort by importance (pagerank + in_degree)
            sorted_nodes = sorted(
                self.graph.nodes.items(),
                key=lambda x: (x[1].pagerank_score + x[1].in_degree / 100, x[1].in_degree),
                reverse=True
            )[:max_nodes]
            selected_node_ids = {node_id for node_id, _ in sorted_nodes}
        else:
            selected_node_ids = set(self.graph.nodes.keys())
        
        # Prepare nodes data
        nodes_data = []
        node_index = {}  # Map node_id to index for edges
        
        for idx, node_id in enumerate(selected_node_ids):
            node = self.graph.nodes[node_id]
            node_index[node_id] = idx
            
            # Determine size based on node type and importance
            if node.node_type.value == "agency_root":
                # Agency nodes are much larger
                doc_count = node.custom_properties.get("document_count", 0)
                size = min(60 + (doc_count * 2), 150)
            else:
                # Regular document nodes
                size = min(20 + (node.in_degree * 2), 50)
            
            nodes_data.append({
                "id": node_id,
                "index": idx,
                "title": node.title,
                "agency": node.agency,
                "type": node.node_type.value,
                "size": size,
                "topics": node.topics[:5],
                "keywords": node.keywords[:5],
                "url": node.source_url,
                "in_degree": node.in_degree,
                "out_degree": node.out_degree,
                "word_count": node.word_count,
                "is_agency": node.node_type.value == "agency_root",
                "document_count": node.custom_properties.get("document_count", 0) if node.node_type.value == "agency_root" else 0
            })
        
        # Prepare edges data
        edges_data = []
        edge_type_counts = defaultdict(int)
        
        for edge in self.graph.edges:
            # Filter by edge type if specified
            if include_edge_types and edge.edge_type not in include_edge_types:
                continue
            
            # Only include if both nodes are in selection
            if edge.source_id in selected_node_ids and edge.target_id in selected_node_ids:
                edges_data.append({
                    "source": node_index[edge.source_id],
                    "target": node_index[edge.target_id],
                    "type": edge.edge_type.value,
                    "weight": edge.weight,
                    "anchor_text": edge.anchor_text or ""
                })
                edge_type_counts[edge.edge_type.value] += 1
        
        if verbose:
            print(f"  Selected {len(nodes_data)} nodes and {len(edges_data)} edges")
        
        # Calculate statistics
        agency_counts = defaultdict(int)
        type_counts = defaultdict(int)
        for node_data in nodes_data:
            agency_counts[node_data['agency']] += 1
            type_counts[node_data['type']] += 1
        
        # Generate HTML with D3.js
        html_content = self._generate_d3_html(
            nodes_data, 
            edges_data, 
            agency_counts,
            type_counts,
            edge_type_counts
        )
        
        # Write to file
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if verbose:
            print(f"✓ Saved D3.js visualization to {filepath}")
        
        return str(filepath)
    
    def _generate_d3_html(
        self,
        nodes_data: list,
        edges_data: list,
        agency_counts: dict,
        type_counts: dict,
        edge_type_counts: dict
    ) -> str:
        """Generate the complete HTML with D3.js code"""
        
        # Color schemes
        agency_colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#6C5CE7", "#FDCB6E", "#E17055", "#74B9FF", "#A29BFE"
        ]
        
        type_colors = {
            "html_page": "#4ECDC4",
            "pdf_document": "#FF6B6B",
            "docx_document": "#FFA07A",
            "index_page": "#6C5CE7",
            "policy_page": "#45B7D1",
            "program_page": "#FDCB6E",
            "agency_root": "#2D3436"
        }
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Montana Knowledge Network - Interactive Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #1a1a1a;
            color: #ffffff;
            overflow: hidden;
        }}
        
        #header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }}
        
        #header h1 {{
            font-size: 24px;
            font-weight: 600;
        }}
        
        #header .stats {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        #controls {{
            position: fixed;
            top: 90px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            border-radius: 10px;
            max-width: 300px;
            max-height: calc(100vh - 120px);
            overflow-y: auto;
            z-index: 100;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }}
        
        #controls h3 {{
            margin-bottom: 10px;
            font-size: 16px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 5px;
        }}
        
        #controls label {{
            display: block;
            margin: 10px 0 5px 0;
            font-size: 14px;
        }}
        
        #controls select, #controls input {{
            width: 100%;
            padding: 8px;
            background: #2a2a2a;
            border: 1px solid #444;
            color: #fff;
            border-radius: 5px;
            font-size: 14px;
        }}
        
        #controls button {{
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            background: #667eea;
            border: none;
            border-radius: 5px;
            color: white;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        #controls button:hover {{
            background: #764ba2;
        }}
        
        .filter-group {{
            margin: 15px 0;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 13px;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            margin-right: 8px;
        }}
        
        #tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.95);
            padding: 15px;
            border-radius: 8px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 350px;
            font-size: 13px;
            line-height: 1.5;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            border: 1px solid #667eea;
            z-index: 1001;
        }}
        
        #tooltip h4 {{
            margin: 0 0 8px 0;
            font-size: 15px;
            color: #667eea;
        }}
        
        #tooltip .info {{
            margin: 4px 0;
            color: #ccc;
        }}
        
        #tooltip .url {{
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #444;
            font-size: 11px;
            opacity: 0.8;
            word-break: break-all;
        }}
        
        #search-box {{
            margin-bottom: 15px;
        }}
        
        #search-input {{
            width: 100%;
            padding: 10px;
            background: #2a2a2a;
            border: 1px solid #444;
            color: #fff;
            border-radius: 5px;
        }}
        
        .node {{
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        
        .node:hover {{
            stroke: #fff;
            stroke-width: 3px;
        }}
        
        .link {{
            stroke-opacity: 0.3;
            transition: stroke-opacity 0.2s;
        }}
        
        .link:hover {{
            stroke-opacity: 0.8;
        }}
        
        .link.hyperlink {{ stroke: #4ECDC4; }}
        .link.parent_child {{ stroke: #FFA07A; }}
        .link.same_agency {{ stroke: #98D8C8; }}
        .link.belongs_to_agency {{ stroke: #6C5CE7; stroke-width: 2px; }}
        .link.topic_related {{ stroke: #FDCB6E; }}
        .link.semantic_similar {{ stroke: #E17055; }}
        
        .node.agency-node {{
            stroke: #FFD700;
            stroke-width: 3px;
            filter: drop-shadow(0px 0px 8px rgba(255, 215, 0, 0.6));
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🗺️ Montana State Government Knowledge Network</h1>
        <div class="stats">
            {len(nodes_data)} Documents • {len(edges_data)} Connections • {len(agency_counts)} Agencies
        </div>
    </div>
    
    <div id="controls">
        <div id="search-box">
            <label>Search Documents:</label>
            <input type="text" id="search-input" placeholder="Type to search...">
        </div>
        
        <div class="filter-group">
            <h3>Filter by Agency</h3>
            <select id="agency-filter">
                <option value="all">All Agencies</option>
                {self._generate_options_with_default(sorted(agency_counts.keys()))}
            </select>
        </div>
        
        <div class="filter-group">
            <h3>Filter by Type</h3>
            <select id="type-filter">
                <option value="all">All Types</option>
                {self._generate_options(sorted(type_counts.keys()))}
            </select>
        </div>
        
        <div class="filter-group">
            <h3>Color Nodes By</h3>
            <select id="color-by">
                <option value="agency">Agency</option>
                <option value="type">Document Type</option>
            </select>
        </div>
        
        <button onclick="resetZoom()">Reset View</button>
        <button onclick="togglePhysics()">Toggle Physics</button>
        
        <div class="filter-group">
            <h3>Statistics</h3>
            <div class="legend-item">
                <span>Total Nodes: {len(nodes_data)}</span>
            </div>
            <div class="legend-item">
                <span>Total Edges: {len(edges_data)}</span>
            </div>
        </div>
        
        <div class="filter-group">
            <h3>Document Types</h3>
            {self._generate_legend_items(type_counts, type_colors)}
        </div>
    </div>
    
    <div id="tooltip"></div>
    <svg id="network"></svg>
    
    <script>
        // Data
        const nodesData = {json.dumps(nodes_data)};
        const linksData = {json.dumps(edges_data)};
        
        // Setup
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        const svg = d3.select("#network")
            .attr("width", width)
            .attr("height", height);
        
        const g = svg.append("g");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        // Tooltip
        const tooltip = d3.select("#tooltip");
        
        // Color scales
        const agencyColor = d3.scaleOrdinal()
            .domain([...new Set(nodesData.map(d => d.agency))])
            .range({json.dumps(agency_colors)});
        
        const typeColorMap = {json.dumps(type_colors)};
        
        // Force simulation
        let simulation = d3.forceSimulation(nodesData)
            .force("link", d3.forceLink(linksData).id(d => d.index).distance(d => {{
                // Agency nodes attract their documents
                return d.type === "belongs_to_agency" ? 80 : 120;
            }}))
            .force("charge", d3.forceManyBody().strength(d => {{
                // Agency nodes have stronger gravity
                return d.is_agency ? -800 : -300;
            }}))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 5))
            .force("radial", d3.forceRadial(d => {{
                // Agency nodes stay more central
                return d.is_agency ? 0 : 200;
            }}, width / 2, height / 2).strength(0.1));
        
        // Draw links
        const link = g.append("g")
            .selectAll("line")
            .data(linksData)
            .join("line")
            .attr("class", d => "link " + d.type)
            .attr("stroke-width", d => Math.sqrt(d.weight) * 1.5);
        
        // Draw nodes
        const node = g.append("g")
            .selectAll("circle")
            .data(nodesData)
            .join("circle")
            .attr("class", d => d.is_agency ? "node agency-node" : "node")
            .attr("r", d => d.size)
            .attr("fill", d => agencyColor(d.agency))
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("mouseover", showTooltip)
            .on("mouseout", hideTooltip)
            .on("click", nodeClicked);
        
        // Simulation tick
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
        
        // Event handlers
        function showTooltip(event, d) {{
            const tooltipContent = d.is_agency ? `
                <h4>🏛️ ${{d.title}} Agency</h4>
                <div class="info"><strong>Total Documents:</strong> ${{d.document_count}}</div>
                <div class="info"><strong>Total Words:</strong> ${{d.word_count.toLocaleString()}}</div>
                <div class="info"><strong>Connections:</strong> ${{d.in_degree}} in, ${{d.out_degree}} out</div>
            ` : `
                <h4>${{d.title}}</h4>
                <div class="info"><strong>Agency:</strong> ${{d.agency}}</div>
                <div class="info"><strong>Type:</strong> ${{d.type}}</div>
                <div class="info"><strong>Connections:</strong> ${{d.in_degree}} in, ${{d.out_degree}} out</div>
                <div class="info"><strong>Words:</strong> ${{d.word_count.toLocaleString()}}</div>
                ${{d.topics.length > 0 ? '<div class="info"><strong>Topics:</strong> ' + d.topics.join(', ') + '</div>' : ''}}
                <div class="url">${{d.url}}</div>
            `;
            
            tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px")
                .html(tooltipContent);
        }}
        
        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}
        
        function nodeClicked(event, d) {{
            if (d.is_agency) {{
                // For agency nodes, highlight all connected documents
                const connectedNodeIds = new Set();
                linksData.forEach(link => {{
                    if (link.source.id === d.id) connectedNodeIds.add(link.target.id);
                    if (link.target.id === d.id) connectedNodeIds.add(link.source.id);
                }});
                
                node.style("opacity", n => n.id === d.id || connectedNodeIds.has(n.id) ? 1 : 0.1);
                link.style("opacity", l => l.source.id === d.id || l.target.id === d.id ? 0.6 : 0.05);
            }} else if (d.url) {{
                window.open(d.url, '_blank');
            }}
        }}
        
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        // Controls
        function resetZoom() {{
            svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
        }}
        
        function togglePhysics() {{
            if (simulation.alpha() < 0.1) {{
                simulation.alpha(0.3).restart();
            }} else {{
                simulation.stop();
            }}
        }}
        
        // Filters
        function applyAgencyFilter(selected) {{
            if (selected === "all") {{
                node.style("display", "block").style("opacity", 1);
                link.style("display", "block").style("opacity", 0.3);
            }} else {{
                // Get nodes that belong to the selected agency
                const filteredNodes = new Set();
                nodesData.forEach(d => {{
                    if (d.agency === selected) {{
                        filteredNodes.add(d.index);
                    }}
                }});
                
                // Get links connected to filtered nodes
                const filteredLinks = new Set();
                linksData.forEach((l, i) => {{
                    if (filteredNodes.has(l.source.index) && filteredNodes.has(l.target.index)) {{
                        filteredLinks.add(i);
                    }}
                }});
                
                // Hide unassociated nodes and links for performance
                node.style("display", (d, i) => filteredNodes.has(i) ? "block" : "none")
                    .style("opacity", (d, i) => filteredNodes.has(i) ? 1 : 0);
                    
                link.style("display", (d, i) => filteredLinks.has(i) ? "block" : "none")
                    .style("opacity", (d, i) => filteredLinks.has(i) ? 0.3 : 0);
            }}
        }}
        
        d3.select("#agency-filter").on("change", function() {{
            applyAgencyFilter(this.value);
        }});
        
        d3.select("#type-filter").on("change", function() {{
            const selected = this.value;
            const agencyFilter = d3.select("#agency-filter").property("value");
            
            if (selected === "all") {{
                // Reapply agency filter
                applyAgencyFilter(agencyFilter);
            }} else {{
                // Get nodes from current agency filter
                let baseNodes = new Set();
                if (agencyFilter === "all") {{
                    nodesData.forEach((d, i) => baseNodes.add(i));
                }} else {{
                    nodesData.forEach((d, i) => {{
                        if (d.agency === agencyFilter) baseNodes.add(i);
                    }});
                }}
                
                // Filter by type within agency filter
                const filteredNodes = new Set();
                baseNodes.forEach(i => {{
                    if (nodesData[i].type === selected) {{
                        filteredNodes.add(i);
                    }}
                }});
                
                // Get links connected to filtered nodes
                const filteredLinks = new Set();
                linksData.forEach((l, i) => {{
                    if (filteredNodes.has(l.source.index) && filteredNodes.has(l.target.index)) {{
                        filteredLinks.add(i);
                    }}
                }});
                
                // Hide unassociated nodes and links for performance
                node.style("display", (d, i) => filteredNodes.has(i) ? "block" : "none")
                    .style("opacity", (d, i) => filteredNodes.has(i) ? 1 : 0);
                    
                link.style("display", (d, i) => filteredLinks.has(i) ? "block" : "none")
                    .style("opacity", (d, i) => filteredLinks.has(i) ? 0.3 : 0);
            }}
        }});
        
        d3.select("#color-by").on("change", function() {{
            const colorBy = this.value;
            node.attr("fill", d => {{
                return colorBy === "agency" ? agencyColor(d.agency) : typeColorMap[d.type];
            }});
        }});
        
        // Search
        d3.select("#search-input").on("input", function() {{
            const searchTerm = this.value.toLowerCase();
            const agencyFilter = d3.select("#agency-filter").property("value");
            const typeFilter = d3.select("#type-filter").property("value");
            
            if (!searchTerm) {{
                // Reapply current filters
                if (typeFilter !== "all") {{
                    d3.select("#type-filter").dispatch("change");
                }} else {{
                    applyAgencyFilter(agencyFilter);
                }}
                return;
            }}
            
            // Get nodes from current filters
            let baseNodes = new Set();
            if (agencyFilter === "all") {{
                nodesData.forEach((d, i) => baseNodes.add(i));
            }} else {{
                nodesData.forEach((d, i) => {{
                    if (d.agency === agencyFilter) baseNodes.add(i);
                }});
            }}
            
            if (typeFilter !== "all") {{
                const tempNodes = new Set();
                baseNodes.forEach(i => {{
                    if (nodesData[i].type === typeFilter) tempNodes.add(i);
                }});
                baseNodes = tempNodes;
            }}
            
            // Filter by search term within existing filters
            const filteredNodes = new Set();
            baseNodes.forEach(i => {{
                const d = nodesData[i];
                if (d.title.toLowerCase().includes(searchTerm) || 
                    d.topics.some(t => t.toLowerCase().includes(searchTerm)) ||
                    d.keywords.some(k => k.toLowerCase().includes(searchTerm))) {{
                    filteredNodes.add(i);
                }}
            }});
            
            // Get links connected to filtered nodes
            const filteredLinks = new Set();
            linksData.forEach((l, i) => {{
                if (filteredNodes.has(l.source.index) && filteredNodes.has(l.target.index)) {{
                    filteredLinks.add(i);
                }}
            }});
            
            // Hide unassociated nodes and links for performance
            node.style("display", (d, i) => filteredNodes.has(i) ? "block" : "none")
                .style("opacity", (d, i) => filteredNodes.has(i) ? 1 : 0);
                
            link.style("display", (d, i) => filteredLinks.has(i) ? "block" : "none")
                .style("opacity", (d, i) => filteredLinks.has(i) ? 0.3 : 0);
        }});
        
        // Apply default filter (first agency) on page load for performance
        setTimeout(() => {{
            const firstAgency = d3.select("#agency-filter option:nth-child(2)").property("value");
            if (firstAgency) {{
                d3.select("#agency-filter").property("value", firstAgency);
                applyAgencyFilter(firstAgency);
            }}
        }}, 100);
        
        // Initial zoom to fit
        setTimeout(() => {{
            const bounds = g.node().getBBox();
            const fullWidth = bounds.width;
            const fullHeight = bounds.height;
            const midX = bounds.x + fullWidth / 2;
            const midY = bounds.y + fullHeight / 2;
            const scale = 0.8 / Math.max(fullWidth / width, fullHeight / height);
            const translate = [width / 2 - scale * midX, height / 2 - scale * midY];
            
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
            );
        }}, 500);
    </script>
</body>
</html>'''
    
    def _generate_options(self, items: list) -> str:
        """Generate HTML option elements"""
        return "\n".join([f'<option value="{item}">{item}</option>' for item in items])
    
    def _generate_options_with_default(self, items: list) -> str:
        """Generate HTML option elements with first one selected by default"""
        if not items:
            return ""
        options = []
        for i, item in enumerate(items):
            selected = ' selected' if i == 0 else ''
            options.append(f'<option value="{item}"{selected}>{item}</option>')
        return "\n".join(options)
    
    def _generate_legend_items(self, counts: dict, colors: dict) -> str:
        """Generate legend items HTML"""
        items = []
        for key, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            color = colors.get(key, "#888")
            items.append(f'''
            <div class="legend-item">
                <div class="legend-color" style="background-color: {color};"></div>
                <span>{key}: {count}</span>
            </div>
            ''')
        return "\n".join(items)


def main():
    """Generate D3.js visualization"""
    from src.network.persistence import GraphPersistence
    
    print("Loading knowledge graph...")
    persistence = GraphPersistence(output_dir="src/network/exports")
    graph = persistence.load_pickle("montana_knowledge.pkl", verbose=False)
    
    if not graph:
        print("✗ Could not load graph.")
        return
    
    print(f"Loaded graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges\n")
    
    # Create visualization
    visualizer = D3Visualizer(graph, output_dir="html")
    
    filepath = visualizer.generate_force_directed_graph(
        filename="montana_network_interactive.html",
        max_nodes=1000,  # Limit for performance
        include_edge_types=None,  # Include all edge types
        verbose=True
    )
    
    print(f"\n✓ Visualization complete!")
    print(f"\nOpen in browser: {filepath}")


if __name__ == "__main__":
    main()
