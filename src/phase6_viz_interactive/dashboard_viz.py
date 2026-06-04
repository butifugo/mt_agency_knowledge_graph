"""
Interactive Multi-Agency Dashboard Generator

Creates a unified dashboard combining knowledge graphs and navigation trees
with advanced filtering, search, and export capabilities.

Features:
- Multi-agency selection
- Dual-view layout (knowledge + navigation)
- Network complexity controls
- Search functionality
- Export to PNG/SVG/JSON
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Generate interactive multi-agency dashboard"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize dashboard generator
        
        Args:
            config_path: Path to config.yaml (optional)
        """
        self.config_path = config_path
        self.config = self._load_config() if config_path and config_path.exists() else {}
        
        # Default paths
        self.project_root = Path(__file__).parent.parent.parent
        self.knowledge_dir = self.project_root / "data" / "graphs" / "knowledge"
        self.navigation_dir = self.project_root / "data" / "graphs" / "navigation"
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
    
    def get_available_agencies(self) -> List[str]:
        """
        Get list of agencies with both knowledge and HTML navigation graphs
        
        Returns:
            List of agency names
        """
        knowledge_agencies = set()
        navigation_agencies = set()
        
        if self.knowledge_dir.exists():
            for file in self.knowledge_dir.glob("*_knowledge.json"):
                agency = file.stem.replace("_knowledge", "")
                knowledge_agencies.add(agency)
        
        if self.navigation_dir.exists():
            # Look for HTML navigation files
            for file in self.navigation_dir.glob("*_html_navigation.json"):
                agency = file.stem.replace("_html_navigation", "")
                navigation_agencies.add(agency)
        
        # Return agencies that have both graphs
        common = knowledge_agencies & navigation_agencies
        return sorted(list(common))
    
    def load_knowledge_graph(self, agency: str) -> Optional[Dict[str, Any]]:
        """Load knowledge graph for agency"""
        graph_file = self.knowledge_dir / f"{agency}_knowledge.json"
        if not graph_file.exists():
            return None
        
        with open(graph_file, 'r') as f:
            return json.load(f)
    
    def load_navigation_graph(self, agency: str) -> Optional[Dict[str, Any]]:
        """Load HTML navigation graph for agency"""
        graph_file = self.navigation_dir / f"{agency}_html_navigation.json"
        if not graph_file.exists():
            return None
        
        with open(graph_file, 'r') as f:
            return json.load(f)
    
    def generate_dashboard(self, agencies: Optional[List[str]] = None) -> str:
        """
        Generate interactive dashboard HTML
        
        Args:
            agencies: List of agencies to include (None = all)
            
        Returns:
            Path to generated HTML file
        """
        if agencies is None:
            agencies = self.get_available_agencies()
        
        if not agencies:
            raise ValueError("No agencies with both knowledge and navigation graphs found")
        
        # Create agency-data directory
        agency_data_dir = self.output_dir / "agency-data"
        agency_data_dir.mkdir(exist_ok=True, parents=True)
        
        # Export each agency's data as separate JSON file
        available_agencies = []
        for agency in agencies:
            knowledge = self.load_knowledge_graph(agency)
            navigation = self.load_navigation_graph(agency)
            
            if knowledge and navigation:
                agency_json = {
                    'knowledge': knowledge,
                    'navigation': navigation
                }
                
                # Write to separate file
                json_file = agency_data_dir / f"{agency}.json"
                with open(json_file, 'w') as f:
                    json.dump(agency_json, f)
                
                available_agencies.append(agency)
                logger.info(f"Exported {agency} data: {json_file.stat().st_size / 1024:.1f} KB")
        
        # Generate dashboard HTML (loads data dynamically)
        html = self._generate_dashboard_html(available_agencies)
        
        output_file = self.output_dir / "interactive-dashboard.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Generated dashboard: {output_file} ({len(html) / 1024:.1f} KB)")
        return str(output_file)
    
    def _generate_dashboard_html(self, agencies: List[str]) -> str:
        """Generate complete dashboard HTML that loads agency data dynamically"""
        
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Montana State Knowledge Network - Interactive Dashboard</title>
    <script src="js/d3.v7.min.js"></script>
    <script src="js/html2canvas.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            overflow: hidden;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-rows: 60px 50px 1fr;
            height: 100vh;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 0 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
        }}
        
        .header-controls {{
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        .btn {{
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s;
        }}
        
        .btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        .btn-primary {{
            background: white;
            color: #1e3c72;
            border-color: white;
        }}
        
        .btn-primary:hover {{
            background: #f0f0f0;
        }}
        
        /* Toolbar */
        .toolbar {{
            background: white;
            border-bottom: 1px solid #ddd;
            padding: 0 30px;
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .agency-select {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            min-width: 200px;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .control-group label {{
            font-size: 13px;
            color: #666;
            font-weight: 500;
        }}
        
        .slider {{
            width: 150px;
        }}
        
        .search-box {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
            width: 250px;
        }}
        
        /* Main Content */
        .content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px 30px;
            overflow: hidden;
        }}
        
        .panel {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .panel-header {{
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .panel-header h2 {{
            font-size: 18px;
            font-weight: 600;
            color: #1e3c72;
        }}
        
        .panel-stats {{
            font-size: 12px;
            color: #666;
        }}
        
        .panel-body {{
            flex: 1;
            overflow: hidden;
            position: relative;
        }}
        
        #knowledge-graph, #navigation-tree {{
            width: 100%;
            height: 100%;
        }}
        
        /* Nodes and Links */
        .node circle {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}
        
        .node text {{
            font-size: 11px;
            pointer-events: none;
        }}
        
        .link {{
            fill: none;
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 1.5px;
        }}
        
        .node.selected circle {{
            stroke: #ff6b6b;
            stroke-width: 3px;
        }}
        
        /* Tooltips */
        .tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            max-width: 300px;
        }}
        
        /* Legend */
        .legend {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: white;
            padding: 10px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 11px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        /* Loading */
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #999;
        }}
        
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #1e3c72;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Node Details Panel */
        #node-details {{
            position: absolute;
            top: 0;
            right: 0;
            width: 350px;
            height: 100%;
            background: white;
            border-left: 2px solid #1e3c72;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            overflow-y: auto;
            z-index: 10;
            box-shadow: -2px 0 10px rgba(0,0,0,0.1);
        }}
        
        #node-details.active {{
            transform: translateX(0);
        }}
        
        #node-details-header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px;
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        
        #node-details-header h3 {{
            margin: 0 0 10px 0;
            font-size: 18px;
            word-wrap: break-word;
        }}
        
        .node-type-badge {{
            display: inline-block;
            padding: 4px 10px;
            background: rgba(255,255,255,0.2);
            border-radius: 12px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .close-details {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            line-height: 1;
            transition: background 0.2s;
        }}
        
        .close-details:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        #node-details-body {{
            padding: 20px;
        }}
        
        .detail-section {{
            margin-bottom: 25px;
        }}
        
        .detail-section h4 {{
            color: #1e3c72;
            font-size: 14px;
            margin: 0 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #f0f0f0;
            font-weight: 600;
        }}
        
        .detail-row {{
            display: grid;
            grid-template-columns: 110px 1fr;
            gap: 10px;
            margin: 8px 0;
            font-size: 13px;
        }}
        
        .detail-label {{
            color: #666;
            font-weight: 500;
        }}
        
        .detail-value {{
            color: #333;
            word-wrap: break-word;
        }}
        
        .detail-value a {{
            color: #1e3c72;
            text-decoration: none;
            word-break: break-all;
        }}
        
        .detail-value a:hover {{
            text-decoration: underline;
        }}
        
        .keywords-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }}
        
        .keyword-badge {{
            display: inline-block;
            padding: 4px 10px;
            background: #e3f2fd;
            color: #1e3c72;
            border-radius: 12px;
            font-size: 11px;
            border: 1px solid #bbdefb;
        }}
        
        .stat-card {{
            background: #e3f2fd;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #bbdefb;
            margin-bottom: 8px;
        }}
        
        .stat-card-label {{
            font-size: 11px;
            color: #666;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .stat-card-value {{
            font-size: 24px;
            font-weight: bold;
            color: #1e3c72;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🗺️ Montana State Knowledge Network Dashboard</h1>
            <div class="header-controls">
                <button class="btn" onclick="resetViews()">Reset Views</button>
                <button class="btn btn-primary" onclick="exportDashboard()">Export PNG</button>
            </div>
        </div>
        
        <div class="toolbar">
            <div class="control-group">
                <label>Agency:</label>
                <select class="agency-select" id="agency-select" onchange="loadAgency()">
                    <option value="">Select an agency...</option>
{agency_options}
                </select>
            </div>
            
            <div class="control-group">
                <label>Max Nodes:</label>
                <input type="range" class="slider" id="node-limit" min="50" max="500" value="200" step="50">
                <span id="node-limit-value">200</span>
            </div>
            
            <div class="control-group">
                <label>Search:</label>
                <input type="text" class="search-box" id="search-box" placeholder="Search nodes...">
            </div>
        </div>
        
        <div class="content">
            <div class="panel">
                <div class="panel-header">
                    <h2>Knowledge Graph</h2>
                    <div class="panel-stats" id="knowledge-stats">
                        0 nodes, 0 edges
                    </div>
                </div>
                <div class="panel-body">
                    <div id="knowledge-graph">
                        <div class="loading">
                            <div class="spinner"></div>
                            <div>Select an agency to view knowledge graph</div>
                        </div>
                    </div>
                    <div class="legend">
                        <div class="legend-item">
                            <div class="legend-color" style="background: #4dabf7;"></div>
                            <span>Document</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #51cf66;"></div>
                            <span>Keyword</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #ff6b6b;"></div>
                            <span>Topic</span>
                        </div>
                    </div>
                    <!-- Node Details Panel -->
                    <div id="node-details">
                        <div id="node-details-header">
                            <button class="close-details" onclick="closeNodeDetails()">&times;</button>
                            <h3 id="detail-node-title">Node Details</h3>
                            <span class="node-type-badge" id="detail-node-type"></span>
                        </div>
                        <div id="node-details-body">
                            <div class="detail-section">
                                <h4>📄 Information</h4>
                                <div id="detail-info-content"></div>
                            </div>
                            <div class="detail-section">
                                <h4>🔗 Connections</h4>
                                <div id="detail-connections-content"></div>
                            </div>
                            <div class="detail-section">
                                <h4>🏷️ Keywords</h4>
                                <div id="detail-keywords-content"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <h2>Navigation Tree</h2>
                    <div class="panel-stats" id="navigation-stats">
                        0 nodes, 0 edges
                    </div>
                </div>
                <div class="panel-body">
                    <div id="navigation-tree">
                        <div class="loading">
                            <div class="spinner"></div>
                            <div>Select an agency to view navigation tree</div>
                        </div>
                    </div>
                    <div class="legend">
                        <div class="legend-item">
                            <div class="legend-color" style="background: #4dabf7;"></div>
                            <span>HTML Pages</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #ff6b6b;"></div>
                            <span>PDF Documents</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #7950f2;"></div>
                            <span>DOCX Documents</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #51cf66; height: 2px; margin-top: 8px;"></div>
                            <span>Page Links</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #ff6b6b; height: 2px; margin-top: 8px;"></div>
                            <span>Doc Links</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #868e96; height: 2px; margin-top: 8px; border-top: 1px dashed #868e96;"></div>
                            <span>Hierarchy</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        // Available agencies (loaded dynamically)
        const availableAgencies = {agency_list_json};
        let agencyDataCache = {{}};
        
        let currentAgency = null;
        let knowledgeGraph = null;
        let navigationTree = null;
        
        // Initialize
        document.getElementById('node-limit').addEventListener('input', function() {{
            document.getElementById('node-limit-value').textContent = this.value;
            if (currentAgency) {{
                renderKnowledgeGraph(currentAgency, parseInt(this.value));
            }}
        }});
        
        document.getElementById('search-box').addEventListener('input', function() {{
            searchNodes(this.value);
        }});
        
        async function loadAgencyData(agency) {{
            // Check cache first
            if (agencyDataCache[agency]) {{
                return agencyDataCache[agency];
            }}
            
            // Load from file
            try {{
                const response = await fetch(`agency-data/${{agency}}.json`);
                if (!response.ok) {{
                    throw new Error(`Failed to load ${{agency}} data`);
                }}
                const data = await response.json();
                agencyDataCache[agency] = data;
                return data;
            }} catch (error) {{
                console.error('Error loading agency data:', error);
                alert(`Failed to load data for ${{agency}}`);
                return null;
            }}
        }}
        
        async function loadAgency() {{
            const select = document.getElementById('agency-select');
            const agency = select.value;
            
            if (!agency) return;
            
            // Show loading
            d3.select('#knowledge-graph').html('<div class="loading"><div class="spinner"></div><div>Loading knowledge graph...</div></div>');
            d3.select('#navigation-tree').html('<div class="loading"><div class="spinner"></div><div>Loading navigation tree...</div></div>');
            
            // Load data
            const data = await loadAgencyData(agency);
            if (!data) return;
            
            currentAgency = agency;
            const nodeLimit = parseInt(document.getElementById('node-limit').value);
            
            renderKnowledgeGraph(agency, nodeLimit);
            renderNavigationTree(agency);
        }}
        
        function renderKnowledgeGraph(agency, maxNodes = 200) {{
            const data = agencyDataCache[agency].knowledge;
            if (!data) return;
            
            // Clear previous
            d3.select('#knowledge-graph').html('');
            
            // Extract nodes and edges
            let nodes = [];
            let edges = [];
            
            if (Array.isArray(data.nodes)) {{
                nodes = data.nodes.slice(0, maxNodes);
            }} else {{
                nodes = Object.values(data.nodes).slice(0, maxNodes);
            }}
            
            if (Array.isArray(data.edges)) {{
                const nodeIds = new Set(nodes.map(n => n.id));
                edges = data.edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
            }}
            
            // Calculate in_degree and out_degree for each node
            const degreeMap = {{}};
            nodes.forEach(n => {{
                degreeMap[n.id] = {{ in: 0, out: 0 }};
            }});
            
            edges.forEach(e => {{
                const sourceId = typeof e.source === 'object' ? e.source.id : e.source;
                const targetId = typeof e.target === 'object' ? e.target.id : e.target;
                
                if (degreeMap[sourceId]) degreeMap[sourceId].out++;
                if (degreeMap[targetId]) degreeMap[targetId].in++;
            }});
            
            // Apply degrees to nodes
            nodes.forEach(n => {{
                n.in_degree = degreeMap[n.id]?.in || 0;
                n.out_degree = degreeMap[n.id]?.out || 0;
            }});
            
            // Update stats
            document.getElementById('knowledge-stats').textContent = 
                `${{nodes.length}} nodes, ${{edges.length}} edges`;
            
            // Create force simulation
            const width = document.getElementById('knowledge-graph').clientWidth;
            const height = document.getElementById('knowledge-graph').clientHeight;
            
            const svg = d3.select('#knowledge-graph')
                .append('svg')
                .attr('width', width)
                .attr('height', height)
                .call(d3.zoom()
                    .scaleExtent([0.1, 4])
                    .on('zoom', (event) => {{
                        g.attr('transform', event.transform);
                    }}));
            
            const g = svg.append('g');
            
            const simulation = d3.forceSimulation(nodes)
                .force('link', d3.forceLink(edges).id(d => d.id).distance(50))
                .force('charge', d3.forceManyBody().strength(-100))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(20));
            
            const link = g.append('g')
                .selectAll('line')
                .data(edges)
                .join('line')
                .attr('class', 'link')
                .attr('stroke-width', 1.5);
            
            const node = g.append('g')
                .selectAll('g')
                .data(nodes)
                .join('g')
                .attr('class', 'node')
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            node.append('circle')
                .attr('r', 6)
                .attr('fill', d => {{
                    const type = d.type || d.node_type || 'document';
                    if (type.includes('document')) return '#4dabf7';
                    if (type.includes('keyword')) return '#51cf66';
                    if (type.includes('topic')) return '#ff6b6b';
                    return '#adb5bd';
                }})
                .on('click', function(event, d) {{
                    event.stopPropagation();
                    showNodeDetails(d);
                    
                    // Highlight selected node
                    d3.selectAll('.node circle').attr('stroke', 'white').attr('stroke-width', 1.5);
                    d3.select(this).attr('stroke', '#ff6b6b').attr('stroke-width', 3);
                }});
            
            node.append('title')
                .text(d => d.title || d.name || d.id);
            
            simulation.on('tick', () => {{
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
            }});
            
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
            
            knowledgeGraph = {{ svg, simulation, nodes, edges }};
        }}
        
        function renderNavigationTree(agency) {{
            const data = agencyDataCache[agency].navigation;
            if (!data) return;
            
            // Clear previous
            d3.select('#navigation-tree').html('');
            
            // Extract nodes and edges
            let allNodes = data.nodes;
            if (!Array.isArray(allNodes)) {{
                allNodes = Object.values(allNodes);
            }}
            
            let edges = data.edges || [];
            if (!Array.isArray(edges)) {{
                edges = Object.values(edges);
            }}
            
            console.log('Navigation data:', {{
                totalNodes: allNodes.length,
                totalEdges: edges.length
            }});
            
            // Separate by type
            const htmlPages = allNodes.filter(n => (n.type || '').toLowerCase().includes('html'));
            const pdfDocs = allNodes.filter(n => (n.type || '').toLowerCase().includes('pdf'));
            const docDocs = allNodes.filter(n => (n.type || '').toLowerCase().includes('doc'));
            
            console.log('Content distribution:', {{
                html: htmlPages.length,
                pdf: pdfDocs.length,
                doc: docDocs.length
            }});
            
            // Extract URL hierarchy for HTML pages
            htmlPages.forEach(page => {{
                const url = page.url || '';
                if (url.includes('agr.mt.gov')) {{
                    const path = url.split('agr.mt.gov')[1] || '';
                    page.urlDepth = path.split('/').filter(p => p).length;
                    page.urlPath = path;
                }} else {{
                    page.urlDepth = 0;
                    page.urlPath = '';
                }}
            }});
            
            // Sort HTML pages by depth (shallow to deep)
            htmlPages.sort((a, b) => a.urlDepth - b.urlDepth);
            
            // Build node map for edge validation
            const nodeMap = new Map(allNodes.map(n => [n.id, n]));
            
            // Filter edges to only include valid connections
            const validEdges = edges.filter(edge => {{
                const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                const tgtId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                return nodeMap.has(srcId) && nodeMap.has(tgtId);
            }});
            
            // Get nodes that are part of the link structure (have incoming or outgoing edges)
            const connectedNodeIds = new Set();
            validEdges.forEach(edge => {{
                const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                const tgtId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                connectedNodeIds.add(srcId);
                connectedNodeIds.add(tgtId);
            }});
            
            // Include ALL HTML pages + only connected documents
            const displayNodes = [
                ...htmlPages,
                ...pdfDocs.filter(n => connectedNodeIds.has(n.id)),
                ...docDocs.filter(n => connectedNodeIds.has(n.id))
            ];
            
            console.log('Display nodes:', {{
                total: displayNodes.length,
                html: htmlPages.length,
                connectedDocs: displayNodes.length - htmlPages.length
            }});
            
            // Update stats
            document.getElementById('navigation-stats').textContent = 
                `${{displayNodes.length}} nodes (${{htmlPages.length}} HTML, ${{displayNodes.length - htmlPages.length}} linked docs), ${{validEdges.length}} links`;
            
            // Create visualization
            const width = document.getElementById('navigation-tree').clientWidth;
            const height = document.getElementById('navigation-tree').clientHeight;
            
            const svg = d3.select('#navigation-tree')
                .append('svg')
                .attr('width', width)
                .attr('height', height)
                .call(d3.zoom()
                    .scaleExtent([0.1, 4])
                    .on('zoom', (event) => {{
                        g.attr('transform', event.transform);
                    }}));
            
            const g = svg.append('g');
            
            // Prepare graph data
            const graphNodes = displayNodes.map(node => {{
                const type = (node.type || '').toLowerCase();
                return {{
                    id: node.id,
                    title: node.title || node.name || node.id,
                    type: node.type,
                    url: node.url,
                    isHtml: type.includes('html'),
                    isPdf: type.includes('pdf'),
                    isDoc: type.includes('doc'),
                    urlDepth: node.urlDepth || 0
                }};
            }});
            
            // Prepare edges
            const graphEdges = [];
            validEdges.forEach(edge => {{
                const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                const tgtId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                
                // Only include edges where both nodes are in display set
                const srcInDisplay = displayNodes.find(n => n.id === srcId);
                const tgtInDisplay = displayNodes.find(n => n.id === tgtId);
                
                if (srcInDisplay && tgtInDisplay) {{
                    graphEdges.push({{
                        source: srcId,
                        target: tgtId,
                        linkText: edge.link_text || '',
                        linkType: edge.type || 'unknown'
                    }});
                }}
            }});
            
            console.log('Graph:', {{
                nodes: graphNodes.length,
                edges: graphEdges.length
            }});
            
            // Create force simulation - emphasize hierarchy by URL depth
            const simulation = d3.forceSimulation(graphNodes)
                .force('link', d3.forceLink(graphEdges)
                    .id(d => d.id)
                    .distance(d => {{
                        // Variable distance based on node types
                        if (d.source.isHtml && d.target.isHtml) return 100;
                        if (d.source.isHtml) return 80;  // HTML to document
                        return 60;
                    }})
                    .strength(0.7))
                .force('charge', d3.forceManyBody()
                    .strength(d => {{
                        // Stronger repulsion for HTML to spread them out
                        if (d.isHtml) return -200;
                        return -100;
                    }}))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide()
                    .radius(d => d.isHtml ? 20 : 12))
                .force('x', d3.forceX()
                    .x(d => {{
                        // Spread horizontally by URL depth
                        if (d.isHtml) {{
                            const maxDepth = 6;
                            const depthRatio = d.urlDepth / maxDepth;
                            return width * 0.1 + (width * 0.8 * depthRatio);
                        }}
                        return width / 2;
                    }})
                    .strength(d => d.isHtml ? 0.2 : 0.05))
                .force('y', d3.forceY()
                    .y(d => {{
                        // Vertical separation by content type
                        if (d.isHtml) return height * 0.3;
                        if (d.isPdf) return height * 0.6;
                        if (d.isDoc) return height * 0.75;
                        return height * 0.5;
                    }})
                    .strength(d => d.isHtml ? 0.1 : 0.3));
            
            // Create links
            const link = g.append('g')
                .attr('class', 'links')
                .selectAll('line')
                .data(graphEdges)
                .join('line')
                .attr('stroke', d => {{
                    // Different colors for different link types
                    if (d.linkType === 'hierarchy') return '#868e96';  // Gray for hierarchy
                    if (d.linkType === 'hyperlink') return '#51cf66';  // Green for page links
                    if (d.linkType === 'document_link') return '#ff6b6b';  // Red for doc links
                    return '#4dabf7';  // Blue default
                }})
                .attr('stroke-opacity', d => {{
                    // More subtle hierarchy edges
                    if (d.linkType === 'hierarchy') return 0.3;
                    return 0.6;
                }})
                .attr('stroke-width', d => {{
                    // Thinner hierarchy edges
                    if (d.linkType === 'hierarchy') return 1;
                    return 1.5;
                }})
                .attr('stroke-dasharray', d => {{
                    // Dashed hierarchy edges
                    if (d.linkType === 'hierarchy') return '2,2';
                    return null;
                }});
            
            // Add tooltips to links
            link.append('title')
                .text(d => {{
                    const linkType = d.linkType === 'hyperlink' ? 'Page Link' : 'Document Link';
                    return `${{linkType}}: ${{d.linkText || 'Link'}}`;
                }});
            
            // Create nodes
            const node = g.append('g')
                .attr('class', 'nodes')
                .selectAll('g')
                .data(graphNodes)
                .join('g')
                .attr('class', 'nav-node')
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            // Add circles
            node.append('circle')
                .attr('r', d => {{
                    if (d.isHtml) return 7;
                    return 5;
                }})
                .attr('fill', d => {{
                    if (d.isHtml) return '#4dabf7';   // Blue
                    if (d.isPdf) return '#ff6b6b';    // Red
                    if (d.isDoc) return '#7950f2';    // Purple
                    return '#adb5bd';
                }})
                .attr('stroke', '#fff')
                .attr('stroke-width', 1.5)
                .style('cursor', 'pointer');
            
            // Add labels for HTML pages only (to reduce clutter)
            node.filter(d => d.isHtml)
                .append('text')
                .attr('dx', 10)
                .attr('dy', 3)
                .attr('font-size', '10px')
                .attr('fill', '#e0e0e0')
                .style('pointer-events', 'none')
                .text(d => {{
                    const title = d.title || d.id;
                    return title.length > 25 ? title.substring(0, 22) + '...' : title;
                }});
            
            // Add tooltips
            node.append('title')
                .text(d => {{
                    let text = d.title || d.id;
                    text += '\\nType: ' + (d.type || 'unknown');
                    if (d.url) text += '\\nURL: ' + d.url;
                    if (d.urlDepth) text += '\\nDepth: ' + d.urlDepth;
                    return text;
                }});
            
            // Update positions on tick
            simulation.on('tick', () => {{
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
            }});
            
            // Drag functions
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
            
            navigationTree = {{ svg, simulation, nodes: graphNodes, edges: graphEdges }};
        }}
        
        function resetViews() {{
            if (currentAgency) {{
                loadAgency();
            }}
        }}
        
        function searchNodes(query) {{
            if (!query || !knowledgeGraph) return;
            
            const lowerQuery = query.toLowerCase();
            
            d3.selectAll('.node')
                .classed('selected', function(d) {{
                    const text = (d.title || d.name || d.id || '').toLowerCase();
                    return text.includes(lowerQuery);
                }});
        }}
        
        function exportDashboard() {{
            if (typeof html2canvas === 'undefined') {{
                alert('Export to PNG is not available. Please disable tracking prevention for this page or use a different browser.');
                return;
            }}
            
            html2canvas(document.querySelector('.dashboard')).then(canvas => {{
                const link = document.createElement('a');
                link.download = 'dashboard-' + (currentAgency || 'export') + '.png';
                link.href = canvas.toDataURL();
                link.click();
            }}).catch(err => {{
                console.error('Export failed:', err);
                alert('Export failed. Please check browser console for details.');
            }});
        }}
        
        function showNodeDetails(node) {{
            const panel = document.getElementById('node-details');
            const titleEl = document.getElementById('detail-node-title');
            const typeEl = document.getElementById('detail-node-type');
            const infoEl = document.getElementById('detail-info-content');
            const connectionsEl = document.getElementById('detail-connections-content');
            const keywordsEl = document.getElementById('detail-keywords-content');
            
            // Set header
            titleEl.textContent = node.title || node.name || node.id || 'Untitled';
            const nodeType = (node.type || node.node_type || 'unknown').replace('_', ' ');
            typeEl.textContent = nodeType;
            
            // Build information section
            let infoHTML = '';
            infoHTML += `<div class="detail-row">`;
            infoHTML += `<span class="detail-label">ID:</span>`;
            infoHTML += `<span class="detail-value">${{node.id || 'N/A'}}</span>`;
            infoHTML += `</div>`;
            
            infoHTML += `<div class="detail-row">`;
            infoHTML += `<span class="detail-label">Type:</span>`;
            infoHTML += `<span class="detail-value">${{nodeType}}</span>`;
            infoHTML += `</div>`;
            
            if (node.word_count !== undefined) {{
                infoHTML += `<div class="detail-row">`;
                infoHTML += `<span class="detail-label">Words:</span>`;
                infoHTML += `<span class="detail-value">${{node.word_count.toLocaleString()}}</span>`;
                infoHTML += `</div>`;
            }}
            
            if (node.url) {{
                infoHTML += `<div class="detail-row">`;
                infoHTML += `<span class="detail-label">URL:</span>`;
                infoHTML += `<span class="detail-value"><a href="${{node.url}}" target="_blank">${{node.url}}</a></span>`;
                infoHTML += `</div>`;
            }}
            
            infoEl.innerHTML = infoHTML;
            
            // Build connections section
            let connectHTML = '';
            const inDegree = node.in_degree || 0;
            const outDegree = node.out_degree || 0;
            
            connectHTML += `<div class="stat-card">`;
            connectHTML += `<div class="stat-card-label">Incoming Links</div>`;
            connectHTML += `<div class="stat-card-value">${{inDegree}}</div>`;
            connectHTML += `</div>`;
            
            connectHTML += `<div class="stat-card">`;
            connectHTML += `<div class="stat-card-label">Outgoing Links</div>`;
            connectHTML += `<div class="stat-card-value">${{outDegree}}</div>`;
            connectHTML += `</div>`;
            
            connectHTML += `<div class="stat-card">`;
            connectHTML += `<div class="stat-card-label">Total Connections</div>`;
            connectHTML += `<div class="stat-card-value">${{inDegree + outDegree}}</div>`;
            connectHTML += `</div>`;
            
            connectionsEl.innerHTML = connectHTML;
            
            // Build keywords section
            let keywordsHTML = '';
            if (node.keywords && node.keywords.length > 0) {{
                keywordsHTML += `<div class="keywords-container">`;
                node.keywords.forEach(kw => {{
                    keywordsHTML += `<span class="keyword-badge">${{kw}}</span>`;
                }});
                keywordsHTML += `</div>`;
            }} else {{
                keywordsHTML = `<div class="detail-value">No keywords available</div>`;
            }}
            
            keywordsEl.innerHTML = keywordsHTML;
            
            // Show panel
            panel.classList.add('active');
        }}
        
        function closeNodeDetails() {{
            const panel = document.getElementById('node-details');
            panel.classList.remove('active');
            
            // Remove node highlighting
            d3.selectAll('.node circle').attr('stroke', 'white').attr('stroke-width', 1.5);
        }}
    </script>
</body>
</html>'''
        
        # Generate agency options
        agency_options = []
        for agency in sorted(agencies):
            title = agency.replace('-', ' ').title()
            agency_options.append(f'                    <option value="{agency}">{title}</option>')
        
        html = html_template.format(
            agency_options='\n'.join(agency_options),
            agency_list_json=json.dumps(agencies)
        )
        
        return html
