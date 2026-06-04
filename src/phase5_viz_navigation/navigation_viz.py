"""
Navigation Visualization Generator

Creates interactive D3.js tree and radial layout visualizations
from navigation graphs built in Phase 3.

Supports:
- Collapsible tree layouts
- Radial (circular) layouts
- MIME type color coding
- Interactive expand/collapse
- Breadcrumb highlighting
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

logger = logging.getLogger(__name__)


class NavigationVisualizer:
    """Generate interactive navigation visualizations using D3.js"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize visualizer
        
        Args:
            config_path: Path to config.yaml (optional)
        """
        self.config_path = config_path
        self.config = self._load_config() if config_path and config_path.exists() else {}
        
        # Default paths
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data" / "graphs" / "navigation"
        self.output_dir = self.project_root / "html"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML"""
        try:
            import yaml
            if self.config_path:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {}
    
    def load_navigation_graph(self, agency: str) -> Dict[str, Any]:
        """
        Load navigation graph from JSON
        
        Args:
            agency: Agency name
            
        Returns:
            Navigation graph dict with nodes and edges
        """
        graph_file = self.data_dir / f"{agency}_navigation.json"
        
        if not graph_file.exists():
            raise FileNotFoundError(f"Navigation graph not found: {graph_file}")
        
        with open(graph_file, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded navigation graph for {agency}: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
        return data
    
    def build_hierarchy(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert flat graph to hierarchical tree structure
        
        Args:
            graph: Navigation graph with nodes and edges
            
        Returns:
            Root node of tree with children
        """
        # Handle both dict and list format for nodes
        nodes_raw = graph.get('nodes', {})
        if isinstance(nodes_raw, dict):
            nodes = nodes_raw
        else:
            nodes = {n['id']: n for n in nodes_raw}
        
        edges = graph.get('edges', [])
        
        # Build parent-child relationships
        children_map: Dict[str, List[str]] = {}
        parents_map: Dict[str, str] = {}
        
        for edge in edges:
            source = edge['source']
            target = edge['target']
            
            if source not in children_map:
                children_map[source] = []
            children_map[source].append(target)
            parents_map[target] = source
        
        # Find root nodes (no parents)
        roots = [nid for nid in nodes if nid not in parents_map]
        
        # If multiple roots, create synthetic root
        if len(roots) > 1:
            root = {
                'id': '__root__',
                'name': 'Navigation',
                'url': '',
                'mime_type': 'directory',
                'depth': 0,
                'is_root': True,
                'children': []
            }
            for root_id in roots:
                root['children'].append(self._build_tree_node(root_id, nodes, children_map))
            return root
        elif len(roots) == 1:
            return self._build_tree_node(roots[0], nodes, children_map)
        else:
            # No roots found, pick first node
            first_id = list(nodes.keys())[0] if nodes else '__empty__'
            if first_id == '__empty__':
                return {'id': '__empty__', 'name': 'Empty', 'children': []}
            return self._build_tree_node(first_id, nodes, children_map)
    
    def _build_tree_node(self, node_id: str, nodes: Dict[str, Any], 
                         children_map: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Recursively build tree node with children
        
        Args:
            node_id: Current node ID
            nodes: All nodes by ID
            children_map: Parent to children mapping
            
        Returns:
            Tree node dict
        """
        node = nodes.get(node_id, {})
        tree_node = {
            'id': node.get('id', node_id),
            'name': node.get('title', node.get('id', 'Untitled')),
            'url': node.get('url', ''),
            'mime_type': node.get('mime_type', 'unknown'),
            'depth': node.get('depth', 0),
            'is_root': node.get('is_root', False),
            'is_leaf': node.get('is_leaf', False),
            'breadcrumb': node.get('breadcrumb', [])
        }
        
        # Add children recursively
        child_ids = children_map.get(node_id, [])
        if child_ids:
            tree_node['children'] = [
                self._build_tree_node(cid, nodes, children_map) 
                for cid in child_ids
            ]
        
        return tree_node
    
    def generate_tree_visualization(self, agency: str, graph: Dict[str, Any],
                                    hierarchy: Dict[str, Any]) -> str:
        """
        Generate HTML with D3.js collapsible tree layout
        
        Args:
            agency: Agency name
            graph: Navigation graph
            hierarchy: Hierarchical tree structure
            
        Returns:
            Path to generated HTML file
        """
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agency_title} - Navigation Tree</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        
        .stats {{
            color: #666;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        
        .controls {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
        }}
        
        .controls button {{
            margin-right: 10px;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .controls button:hover {{
            background: #5568d3;
        }}
        
        #tree {{
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: auto;
            background: #fafafa;
        }}
        
        .node circle {{
            cursor: pointer;
            stroke: #666;
            stroke-width: 2px;
        }}
        
        .node text {{
            font-size: 12px;
            font-family: 'Segoe UI', sans-serif;
        }}
        
        .link {{
            fill: none;
            stroke: #999;
            stroke-width: 1.5px;
        }}
        
        .node.root circle {{
            fill: #ff6b6b;
        }}
        
        .node.leaf circle {{
            fill: #51cf66;
        }}
        
        .node.html circle {{
            fill: #4dabf7;
        }}
        
        .node.pdf circle {{
            fill: #ff6b6b;
        }}
        
        .node.docx circle {{
            fill: #7950f2;
        }}
        
        .node.unknown circle {{
            fill: #adb5bd;
        }}
        
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
        }}
        
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            font-size: 13px;
        }}
        
        .legend-color {{
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{agency_title} Navigation Tree</h1>
        <div class="stats">
            <strong>Nodes:</strong> {node_count} | 
            <strong>Edges:</strong> {edge_count} |
            <strong>Max Depth:</strong> {max_depth}
        </div>
        
        <div class="controls">
            <button onclick="expandAll()">Expand All</button>
            <button onclick="collapseAll()">Collapse All</button>
            <button onclick="resetZoom()">Reset View</button>
        </div>
        
        <div id="tree"></div>
        
        <div class="legend">
            <strong>Legend:</strong>
            <div class="legend-item">
                <span class="legend-color" style="background: #ff6b6b;"></span>
                Root / PDF
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #4dabf7;"></span>
                HTML
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #7950f2;"></span>
                DOCX
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #51cf66;"></span>
                Leaf Node
            </div>
        </div>
    </div>
    
    <script>
        const treeData = {tree_data};
        
        const width = 1340;
        const height = 800;
        const margin = {{top: 20, right: 120, bottom: 20, left: 120}};
        
        let i = 0;
        const duration = 750;
        let root;
        
        const tree = d3.tree()
            .size([height - margin.top - margin.bottom, width - margin.left - margin.right]);
        
        const svg = d3.select("#tree")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(d3.zoom()
                .scaleExtent([0.1, 3])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                }}));
        
        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);
        
        root = d3.hierarchy(treeData);
        root.x0 = height / 2;
        root.y0 = 0;
        
        // Collapse all nodes initially except root
        root.children.forEach(collapse);
        
        update(root);
        
        function collapse(d) {{
            if (d.children) {{
                d._children = d.children;
                d._children.forEach(collapse);
                d.children = null;
            }}
        }}
        
        function expand(d) {{
            if (d._children) {{
                d.children = d._children;
                d.children.forEach(expand);
                d._children = null;
            }}
        }}
        
        function expandAll() {{
            expand(root);
            update(root);
        }}
        
        function collapseAll() {{
            root.children.forEach(collapse);
            update(root);
        }}
        
        function resetZoom() {{
            svg.transition()
                .duration(750)
                .call(d3.zoom().transform, d3.zoomIdentity);
        }}
        
        function update(source) {{
            const treeData = tree(root);
            const nodes = treeData.descendants();
            const links = treeData.descendants().slice(1);
            
            nodes.forEach(d => d.y = d.depth * 180);
            
            const node = g.selectAll("g.node")
                .data(nodes, d => d.id || (d.id = ++i));
            
            const nodeEnter = node.enter().append("g")
                .attr("class", d => {{
                    let classes = "node";
                    if (d.data.is_root) classes += " root";
                    if (d.data.is_leaf) classes += " leaf";
                    classes += " " + (d.data.mime_type || "unknown");
                    return classes;
                }})
                .attr("transform", d => `translate(${{source.y0}},${{source.x0}})`)
                .on("click", (event, d) => {{
                    if (d.children) {{
                        d._children = d.children;
                        d.children = null;
                    }} else {{
                        d.children = d._children;
                        d._children = null;
                    }}
                    update(d);
                }});
            
            nodeEnter.append("circle")
                .attr("r", 6);
            
            nodeEnter.append("text")
                .attr("dy", ".35em")
                .attr("x", d => d.children || d._children ? -13 : 13)
                .attr("text-anchor", d => d.children || d._children ? "end" : "start")
                .text(d => d.data.name.length > 40 ? d.data.name.substring(0, 37) + "..." : d.data.name)
                .style("fill-opacity", 1e-6);
            
            nodeEnter.append("title")
                .text(d => {{
                    let title = d.data.name;
                    if (d.data.url) title += "\\nURL: " + d.data.url;
                    title += "\\nType: " + (d.data.mime_type || "unknown");
                    title += "\\nDepth: " + (d.data.depth || 0);
                    return title;
                }});
            
            const nodeUpdate = nodeEnter.merge(node);
            
            nodeUpdate.transition()
                .duration(duration)
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`);
            
            nodeUpdate.select("text")
                .style("fill-opacity", 1);
            
            const nodeExit = node.exit().transition()
                .duration(duration)
                .attr("transform", d => `translate(${{source.y}},${{source.x}})`)
                .remove();
            
            nodeExit.select("circle")
                .attr("r", 1e-6);
            
            nodeExit.select("text")
                .style("fill-opacity", 1e-6);
            
            const link = g.selectAll("path.link")
                .data(links, d => d.id);
            
            const linkEnter = link.enter().insert("path", "g")
                .attr("class", "link")
                .attr("d", d => {{
                    const o = {{x: source.x0, y: source.y0}};
                    return diagonal(o, o);
                }});
            
            const linkUpdate = linkEnter.merge(link);
            
            linkUpdate.transition()
                .duration(duration)
                .attr("d", d => diagonal(d, d.parent));
            
            link.exit().transition()
                .duration(duration)
                .attr("d", d => {{
                    const o = {{x: source.x, y: source.y}};
                    return diagonal(o, o);
                }})
                .remove();
            
            nodes.forEach(d => {{
                d.x0 = d.x;
                d.y0 = d.y;
            }});
        }}
        
        function diagonal(s, d) {{
            return `M ${{s.y}} ${{s.x}}
                    C ${{(s.y + d.y) / 2}} ${{s.x}},
                      ${{(s.y + d.y) / 2}} ${{d.x}},
                      ${{d.y}} ${{d.x}}`;
        }}
    </script>
</body>
</html>'''
        
        # Calculate stats
        nodes_raw = graph.get('nodes', {})
        if isinstance(nodes_raw, dict):
            node_count = len(nodes_raw)
            max_depth = max([n.get('level', 0) for n in nodes_raw.values()], default=0)
        else:
            node_count = len(nodes_raw)
            max_depth = max([n.get('depth', 0) for n in nodes_raw], default=0)
        edge_count = len(graph.get('edges', []))
        
        html = html_template.format(
            agency_title=agency.replace('-', ' ').title(),
            node_count=node_count,
            edge_count=edge_count,
            max_depth=max_depth,
            tree_data=json.dumps(hierarchy, indent=2)
        )
        
        output_file = self.output_dir / f"{agency}-navigation-tree.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Generated tree visualization: {output_file} ({len(html)} bytes)")
        return str(output_file)
    
    def generate_radial_visualization(self, agency: str, graph: Dict[str, Any],
                                      hierarchy: Dict[str, Any]) -> str:
        """
        Generate HTML with D3.js radial (circular) layout
        
        Args:
            agency: Agency name
            graph: Navigation graph
            hierarchy: Hierarchical tree structure
            
        Returns:
            Path to generated HTML file
        """
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agency_title} - Navigation Radial</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
            text-align: center;
        }}
        
        .stats {{
            color: #666;
            margin-bottom: 20px;
            font-size: 14px;
            text-align: center;
        }}
        
        #radial {{
            width: 100%;
            height: 900px;
            border-radius: 5px;
            overflow: hidden;
        }}
        
        .node circle {{
            cursor: pointer;
            stroke: #666;
            stroke-width: 2px;
        }}
        
        .node text {{
            font-size: 11px;
            font-family: 'Segoe UI', sans-serif;
        }}
        
        .link {{
            fill: none;
            stroke: #999;
            stroke-width: 1.5px;
        }}
        
        .node.root circle {{
            fill: #ff6b6b;
        }}
        
        .node.leaf circle {{
            fill: #51cf66;
        }}
        
        .node.html circle {{
            fill: #4dabf7;
        }}
        
        .node.pdf circle {{
            fill: #ff6b6b;
        }}
        
        .node.docx circle {{
            fill: #7950f2;
        }}
        
        .node.unknown circle {{
            fill: #adb5bd;
        }}
        
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
            text-align: center;
        }}
        
        .legend-item {{
            display: inline-block;
            margin: 0 15px;
            font-size: 13px;
        }}
        
        .legend-color {{
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{agency_title} Navigation Radial</h1>
        <div class="stats">
            <strong>Nodes:</strong> {node_count} | 
            <strong>Edges:</strong> {edge_count} |
            <strong>Max Depth:</strong> {max_depth}
        </div>
        
        <div id="radial"></div>
        
        <div class="legend">
            <strong>Legend:</strong>
            <div class="legend-item">
                <span class="legend-color" style="background: #ff6b6b;"></span>
                Root / PDF
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #4dabf7;"></span>
                HTML
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #7950f2;"></span>
                DOCX
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #51cf66;"></span>
                Leaf Node
            </div>
        </div>
    </div>
    
    <script>
        const treeData = {tree_data};
        
        const width = 1140;
        const height = 900;
        const radius = Math.min(width, height) / 2 - 60;
        
        const tree = d3.tree()
            .size([2 * Math.PI, radius])
            .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);
        
        const svg = d3.select("#radial")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", `translate(${{width / 2}},${{height / 2}})`);
        
        const root = d3.hierarchy(treeData);
        tree(root);
        
        const link = svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.4)
            .attr("stroke-width", 1.5)
            .selectAll("path")
            .data(root.links())
            .join("path")
            .attr("d", d3.linkRadial()
                .angle(d => d.x)
                .radius(d => d.y));
        
        const node = svg.append("g")
            .selectAll("g")
            .data(root.descendants())
            .join("g")
            .attr("class", d => {{
                let classes = "node";
                if (d.data.is_root) classes += " root";
                if (d.data.is_leaf) classes += " leaf";
                classes += " " + (d.data.mime_type || "unknown");
                return classes;
            }})
            .attr("transform", d => `
                rotate(${{d.x * 180 / Math.PI - 90}})
                translate(${{d.y}},0)
            `);
        
        node.append("circle")
            .attr("r", 5);
        
        node.append("text")
            .attr("dy", "0.31em")
            .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
            .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
            .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)
            .text(d => d.data.name.length > 30 ? d.data.name.substring(0, 27) + "..." : d.data.name)
            .clone(true).lower()
            .attr("stroke", "white")
            .attr("stroke-width", 3);
        
        node.append("title")
            .text(d => {{
                let title = d.data.name;
                if (d.data.url) title += "\\nURL: " + d.data.url;
                title += "\\nType: " + (d.data.mime_type || "unknown");
                title += "\\nDepth: " + (d.data.depth || 0);
                return title;
            }});
    </script>
</body>
</html>'''
        
        # Calculate stats
        nodes_raw = graph.get('nodes', {})
        if isinstance(nodes_raw, dict):
            node_count = len(nodes_raw)
            max_depth = max([n.get('level', 0) for n in nodes_raw.values()], default=0)
        else:
            node_count = len(nodes_raw)
            max_depth = max([n.get('depth', 0) for n in nodes_raw], default=0)
        edge_count = len(graph.get('edges', []))
        
        html = html_template.format(
            agency_title=agency.replace('-', ' ').title(),
            node_count=node_count,
            edge_count=edge_count,
            max_depth=max_depth,
            tree_data=json.dumps(hierarchy, indent=2)
        )
        
        output_file = self.output_dir / f"{agency}-navigation-radial.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Generated radial visualization: {output_file} ({len(html)} bytes)")
        return str(output_file)
    
    def generate_selector_page(self, agencies: List[str]) -> str:
        """
        Generate agency selector landing page
        
        Args:
            agencies: List of agency names
            
        Returns:
            Path to selector HTML file
        """
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Montana State Navigation Explorer</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .container {{
            max-width: 900px;
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
            text-align: center;
        }}
        
        .subtitle {{
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        
        .layout-selector {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-bottom: 40px;
        }}
        
        .layout-btn {{
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: 2px solid transparent;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }}
        
        .layout-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
        }}
        
        .layout-btn.active {{
            background: white;
            color: #667eea;
            border-color: #667eea;
        }}
        
        .agency-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }}
        
        .agency-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
            border: 2px solid transparent;
        }}
        
        .agency-card:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .agency-card h3 {{
            margin: 0 0 10px 0;
            font-size: 18px;
        }}
        
        .agency-card .layout-links {{
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 15px;
        }}
        
        .agency-card .layout-link {{
            padding: 6px 12px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 4px;
            font-size: 12px;
            text-decoration: none;
            color: #667eea;
            transition: all 0.3s;
        }}
        
        .agency-card:hover .layout-link {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗺️ Montana State Navigation Explorer</h1>
        <p class="subtitle">Explore agency website structures with interactive visualizations</p>
        
        <div class="agency-grid">
{agency_cards}
        </div>
    </div>
</body>
</html>'''
        
        # Generate agency cards
        cards = []
        for agency in sorted(agencies):
            agency_title = agency.replace('-', ' ').title()
            card = f'''            <div class="agency-card">
                <h3>{agency_title}</h3>
                <div class="layout-links">
                    <a href="{agency}-navigation-tree.html" class="layout-link">🌳 Tree</a>
                    <a href="{agency}-navigation-radial.html" class="layout-link">⭕ Radial</a>
                </div>
            </div>'''
            cards.append(card)
        
        html = html_template.format(agency_cards='\n'.join(cards))
        
        output_file = self.output_dir / "navigation-selector.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Generated selector page: {output_file}")
        return str(output_file)
