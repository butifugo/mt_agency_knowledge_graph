#!/usr/bin/env python
"""
3D Agency Network Visualization
Creates interactive 3D network graph for Montana state agencies with physics-based clustering

Usage:
    python src/viz/agency_network_viz_3d.py
    python src/viz/agency_network_viz_3d.py --output-dir custom/
    python src/viz/agency_network_viz_3d.py --max-nodes 500
"""

import sys
import json
import argparse
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.network.schema import KnowledgeGraph, NodeMetadata, EdgeMetadata
from src.network.persistence import GraphPersistence


# Pickle compatibility fix for loading old graphs
class PickleModuleFix:
    """Helper to fix module import issues when unpickling"""
    @staticmethod
    def load_graph(filepath: Path) -> Optional[KnowledgeGraph]:
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except (ModuleNotFoundError, AttributeError) as e:
            print(f"⚠️  Pickle compatibility issue: {e}")
            print("Attempting to load with module remapping...")
            
            import sys
            from types import ModuleType
            
            # Create fake modules for common pickle paths
            for module_name in ['build_network', 'network', 'src.network']:
                fake_module = ModuleType(module_name)
                fake_module.KnowledgeGraph = KnowledgeGraph  # type: ignore
                fake_module.NodeMetadata = NodeMetadata  # type: ignore
                fake_module.EdgeMetadata = EdgeMetadata  # type: ignore
                sys.modules[module_name] = fake_module
            
            try:
                with open(filepath, 'rb') as f:
                    return pickle.load(f)
            except Exception as e2:
                print(f"❌ Failed to load graph: {e2}")
                return None


class Agency3DNetworkVisualizer:
    """Creates interactive 3D Three.js visualization with physics-based clustering"""
    
    # Available agencies with display names
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
    
    def __init__(self, graph: KnowledgeGraph, output_dir: str = "html", knowledge_dir: str = "knowledge", max_nodes: Optional[int] = None):
        """
        Initialize visualizer
        
        Args:
            graph: Complete knowledge graph
            output_dir: Output directory for HTML file
            knowledge_dir: Path to knowledge directory for navigation_network.json
            max_nodes: Maximum nodes per agency (optional)
        """
        self.graph = graph
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir = Path(knowledge_dir)
        self.max_nodes = max_nodes
        
        # Cache for agency data (loaded on demand)
        self.agency_data_cache: Dict[str, Dict] = {}
        
    def load_navigation_network(self, agency_name: str) -> Optional[Dict]:
        """Load navigation_network.json for the agency"""
        nav_path = self.knowledge_dir / agency_name / "navigation_network.json"
        
        if not nav_path.exists():
            return None
        
        try:
            with open(nav_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading navigation for {agency_name}: {e}")
            return None
    
    def extract_agency_data(self, agency_name: str, include_cross_agency: bool = True) -> Dict:
        """Extract and prepare data for a specific agency"""
        # Check cache first
        cache_key = f"{agency_name}_{include_cross_agency}_{self.max_nodes}"
        if cache_key in self.agency_data_cache:
            return self.agency_data_cache[cache_key]
        
        # Load navigation network
        navigation_data = self.load_navigation_network(agency_name)
        navigation_nodes = set()
        
        if navigation_data and isinstance(navigation_data, dict) and 'nodes' in navigation_data:
            for node in navigation_data['nodes']:
                if isinstance(node, dict) and 'url' in node:
                    navigation_nodes.add(node['url'])
        
        # Filter nodes for this agency
        agency_nodes_dict = {}
        navigation_priority_nodes = {}
        secondary_nodes = {}
        
        for node_id, node in self.graph.nodes.items():
            if node.agency == agency_name:
                if node_id in navigation_nodes:
                    navigation_priority_nodes[node_id] = node
                else:
                    secondary_nodes[node_id] = node
        
        # Always include all navigation nodes
        agency_nodes_dict.update(navigation_priority_nodes)
        
        # Add secondary nodes up to limit
        if self.max_nodes:
            remaining_slots = self.max_nodes - len(navigation_priority_nodes)
            if remaining_slots > 0:
                sorted_secondary = sorted(
                    secondary_nodes.items(),
                    key=lambda x: x[1].pagerank if hasattr(x[1], 'pagerank') else 0,
                    reverse=True
                )
                agency_nodes_dict.update(dict(sorted_secondary[:remaining_slots]))
        else:
            agency_nodes_dict.update(secondary_nodes)
        
        selected_node_ids = set(agency_nodes_dict.keys())
        
        # Get edges
        agency_edges = []
        for edge in self.graph.edges:
            if edge.source_id in selected_node_ids and edge.target_id in selected_node_ids:
                agency_edges.append(edge)
            elif include_cross_agency:
                if edge.source_id in selected_node_ids or edge.target_id in selected_node_ids:
                    agency_edges.append(edge)
        
        # Prepare visualization data
        nodes_data, edges_data = self._prepare_visualization_data(
            agency_nodes_dict, agency_edges, navigation_nodes, agency_name
        )
        
        result = {
            'nodes': nodes_data,
            'edges': edges_data,
            'navigation_count': len(navigation_priority_nodes),
            'secondary_count': len(agency_nodes_dict) - len(navigation_priority_nodes),
            'total_words': sum(n['word_count'] for n in nodes_data)
        }
        
        # Cache the result
        self.agency_data_cache[cache_key] = result
        return result
    
    def _prepare_visualization_data(
        self, 
        agency_nodes: Dict[str, NodeMetadata], 
        agency_edges: List[EdgeMetadata],
        navigation_nodes: Set[str],
        agency_name: str
    ) -> tuple[List[Dict], List[Dict]]:
        """Prepare data structures for 3D visualization"""
        nodes_data = []
        node_index = {}
        
        # Prepare nodes
        for idx, (node_id, node) in enumerate(agency_nodes.items()):
            node_index[node_id] = idx
            
            # Determine node properties
            is_navigation = node_id in navigation_nodes
            is_agency = str(node.node_type.value) == 'agency_root' or node_id == f"https://{agency_name}.mt.gov"
            
            # Calculate node size based on importance
            base_size = 5
            if is_agency:
                size = base_size * 3
            elif is_navigation:
                size = base_size * 2
            else:
                # Size by PageRank or word count
                pagerank = getattr(node, 'pagerank', 0)
                size = base_size + (pagerank * 100)
            
            size = max(3, min(size, 20))  # Clamp between 3 and 20
            
            # Get node attributes
            content_preview = getattr(node, 'content', '')[:200] if hasattr(node, 'content') else ''
            
            nodes_data.append({
                'id': node_id,
                'index': idx,
                'title': node.title,
                'type': str(node.node_type.value),
                'agency': node.agency,
                'url': node_id,
                'size': size,
                'word_count': getattr(node, 'word_count', 0),
                'pagerank': getattr(node, 'pagerank', 0),
                'in_degree': getattr(node, 'in_degree', 0),
                'out_degree': getattr(node, 'out_degree', 0),
                'topics': getattr(node, 'topics', []),
                'keywords': getattr(node, 'keywords', []),
                'crawled_date': str(getattr(node, 'crawled_date', '')),
                'content_preview': content_preview,
                'is_navigation': is_navigation,
                'is_agency': is_agency,
                'is_external': node.agency != agency_name
            })
        
        # Prepare edges
        edges_data = []
        for edge in agency_edges:
            if edge.source_id in node_index and edge.target_id in node_index:
                edges_data.append({
                    'source': node_index[edge.source_id],
                    'target': node_index[edge.target_id],
                    'type': str(edge.edge_type.value),
                    'weight': edge.weight
                })
        
        return nodes_data, edges_data
    
    def generate_3d_html(self) -> str:
        """Generate self-contained 3D HTML visualization"""
        # Generate agency metadata
        agency_metadata = {}
        for agency_key, agency_display in self.AGENCIES.items():
            data = self.extract_agency_data(agency_key)
            agency_metadata[agency_key] = {
                'display_name': agency_display,
                'navigation_count': data['navigation_count'],
                'secondary_count': data['secondary_count'],
                'total_words': data['total_words']
            }
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Montana State Government - 3D Agency Network</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #1a202c;
            overflow: hidden;
            color: white;
        }}
        
        #container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        #header {{
            background: rgba(45, 55, 72, 0.95);
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 100;
            border-bottom: 2px solid #667eea;
        }}
        
        #header h1 {{
            font-size: 22px;
            color: #e2e8f0;
            margin-bottom: 5px;
        }}
        
        #header .subtitle {{
            font-size: 13px;
            color: #a0aec0;
        }}
        
        #agency-selector {{
            margin-top: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        #agency-selector label {{
            font-size: 14px;
            font-weight: 600;
            color: #e2e8f0;
        }}
        
        #agency-selector select {{
            padding: 8px 12px;
            border: 2px solid #4a5568;
            border-radius: 6px;
            font-size: 14px;
            background: #2d3748;
            color: #e2e8f0;
            cursor: pointer;
            min-width: 300px;
        }}
        
        #agency-selector select:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        #stats {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }}
        
        .stat {{
            font-size: 12px;
            color: #cbd5e0;
        }}
        
        .stat strong {{
            color: #e2e8f0;
            font-weight: 600;
        }}
        
        #visualization {{
            flex: 1;
            position: relative;
        }}
        
        #loading-screen {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #cbd5e0;
        }}
        
        #loading-screen h2 {{
            font-size: 28px;
            color: #e2e8f0;
            margin-bottom: 10px;
        }}
        
        #loading-screen p {{
            font-size: 16px;
        }}
        
        .spinner {{
            border: 4px solid #2d3748;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        #controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(45, 55, 72, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            z-index: 10;
            min-width: 220px;
            display: none;
            border: 1px solid #4a5568;
        }}
        
        #controls.visible {{
            display: block;
        }}
        
        #controls h3 {{
            font-size: 14px;
            margin-bottom: 12px;
            color: #e2e8f0;
            border-bottom: 1px solid #4a5568;
            padding-bottom: 8px;
        }}
        
        #controls button {{
            width: 100%;
            padding: 8px 12px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            background: #667eea;
            color: white;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }}
        
        #controls button:hover {{
            background: #5a67d8;
        }}
        
        #controls label {{
            display: flex;
            align-items: center;
            margin: 10px 0 5px 0;
            font-size: 12px;
            color: #cbd5e0;
            cursor: pointer;
        }}
        
        #controls input[type="checkbox"] {{
            margin-right: 8px;
            cursor: pointer;
        }}
        
        #controls input[type="range"] {{
            width: 100%;
            margin: 8px 0;
        }}
        
        .control-group {{
            margin: 15px 0;
            padding: 10px 0;
            border-top: 1px solid #4a5568;
        }}
        
        .control-group:first-child {{
            border-top: none;
        }}
        
        .control-label {{
            font-size: 11px;
            color: #a0aec0;
            margin-bottom: 5px;
        }}
        
        #info-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(45, 55, 72, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            z-index: 10;
            max-width: 300px;
            display: none;
            border: 1px solid #4a5568;
        }}
        
        #info-panel.visible {{
            display: block;
        }}
        
        #info-panel h4 {{
            font-size: 14px;
            color: #e2e8f0;
            margin-bottom: 8px;
        }}
        
        #info-panel .info-text {{
            font-size: 12px;
            color: #cbd5e0;
            line-height: 1.5;
        }}
        
        #info-panel .close-btn {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255,255,255,0.1);
            border: none;
            color: #e2e8f0;
            font-size: 18px;
            cursor: pointer;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            line-height: 1;
        }}
        
        #info-panel .close-btn:hover {{
            background: rgba(255,255,255,0.2);
        }}
        
        .error-message {{
            color: #fc8181;
            background: rgba(254, 178, 178, 0.1);
            border: 2px solid #fc8181;
            border-radius: 8px;
            padding: 20px;
            margin: 20px;
            max-width: 500px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="header">
            <h1>🏛️ Montana State Government - 3D Agency Network</h1>
            <div class="subtitle">Interactive 3D knowledge graph • Physics-based clustering by content type</div>
            <div id="agency-selector">
                <label for="agency-select">Select Agency:</label>
                <select id="agency-select">
                    <option value="">-- Choose an agency --</option>
                    {self._generate_agency_options(agency_metadata)}
                </select>
            </div>
            <div id="stats" style="display:none;">
                <div class="stat"><strong id="nav-count">0</strong> Navigation Pages</div>
                <div class="stat"><strong id="doc-count">0</strong> Documents</div>
                <div class="stat"><strong id="edge-count">0</strong> Connections</div>
                <div class="stat"><strong id="word-count">0</strong> Words</div>
            </div>
        </div>
        
        <div id="visualization">
            <div id="loading-screen">
                <h2>👋 Welcome</h2>
                <p>Select an agency to explore its 3D knowledge network.</p>
            </div>
        </div>
        
        <div id="controls">
            <h3>⚙️ Controls</h3>
            
            <div class="control-group">
                <button onclick="resetView()">🔄 Reset View</button>
                <button onclick="togglePhysics()">⚡ Toggle Physics</button>
            </div>
            
            <div class="control-group">
                <div class="control-label">Physics Strength</div>
                <input type="range" id="physics-strength" min="0" max="100" value="50" onchange="updatePhysics()">
            </div>
            
            <div class="control-group">
                <label>
                    <input type="checkbox" id="show-labels" checked onchange="toggleLabels()">
                    Show Labels
                </label>
                <label>
                    <input type="checkbox" id="cluster-by-type" checked onchange="toggleClustering()">
                    Cluster by Type
                </label>
            </div>
        </div>
        
        <div id="info-panel">
            <button class="close-btn" onclick="closeInfo()">&times;</button>
            <h4 id="info-title">Node Info</h4>
            <div class="info-text" id="info-content"></div>
        </div>
    </div>
    
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://unpkg.com/d3-force-3d@3"></script>
    <script src="https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js"></script>
    <script>
        // Wait for DOM to be ready
        document.addEventListener('DOMContentLoaded', function() {{
        
        const AGENCY_DATA_CACHE = {{}};
        let currentAgency = null;
        let graph3d = null;
        let physicsEnabled = true;
        let clusterByType = true;
        
        // UI elements
        const agencySelect = document.getElementById('agency-select');
        const statsDiv = document.getElementById('stats');
        const visualization = document.getElementById('visualization');
        const controls = document.getElementById('controls');
        const infoPanel = document.getElementById('info-panel');
        
        // Color schemes by content type
        const typeColors = {{
            "html_page": "#4ECDC4",
            "pdf_document": "#FF6B6B",
            "docx_document": "#FFD93D",
            "index_page": "#95E1D3",
            "policy_page": "#A8E6CF",
            "program_page": "#FECA57",
            "agency_root": "#FFD700",
            "topic_cluster": "#DDA15E"
        }};
        
        // Agency selection handler
        agencySelect.addEventListener('change', (e) => {{
            const agency = e.target.value;
            if (agency) {{
                loadAgency(agency);
            }} else {{
                clearVisualization();
            }}
        }});
        
        async function loadAgency(agencyKey) {{
            currentAgency = agencyKey;
            
            // Show loading
            visualization.innerHTML = '<div id="loading-screen"><h2>Loading...</h2><div class="spinner"></div></div>';
            
            try {{
                let data = AGENCY_DATA_CACHE[agencyKey];
                
                if (!data) {{
                    const response = await fetch(`agency-data/${{agencyKey}}.json`);
                    if (!response.ok) {{
                        throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                    }}
                    data = await response.json();
                    AGENCY_DATA_CACHE[agencyKey] = data;
                }}
                
                renderVisualization(data);
                updateStats(data);
                statsDiv.style.display = 'flex';
                controls.classList.add('visible');
            }} catch (error) {{
                console.error('Error loading agency data:', error);
                
                const isCorsError = error.message.includes('Failed to fetch') || 
                                  error.message.includes('Load failed') ||
                                  window.location.protocol === 'file:';
                
                let errorHtml = `
                    <div class="error-message">
                        <h3>⚠️ Error Loading Data</h3>
                        <p><strong>Error:</strong> ${{error.message}}</p>
                `;
                
                if (isCorsError) {{
                    errorHtml += `
                        <p><strong>Solution:</strong> Serve this HTML file using a local web server:</p>
                        <pre style="background: #2d3748; color: #e2e8f0; padding: 12px; border-radius: 4px; margin: 10px 0; font-size: 12px;">cd html
python3 -m http.server 8000</pre>
                        <p>Then open: <a href="http://localhost:8000/agency-navigation.html" target="_blank" style="color: #667eea;">http://localhost:8000/agency-navigation.html</a></p>
                    `;
                }}
                
                errorHtml += `</div>`;
                visualization.innerHTML = errorHtml;
            }}
        }}
        
        function clearVisualization() {{
            visualization.innerHTML = '<div id="loading-screen"><h2>👋 Welcome</h2><p>Select an agency to explore its 3D knowledge network.</p></div>';
            statsDiv.style.display = 'none';
            controls.classList.remove('visible');
            currentAgency = null;
            if (graph3d) {{
                graph3d._destructor();
                graph3d = null;
            }}
        }}
        
        function updateStats(data) {{
            document.getElementById('nav-count').textContent = data.navigation_count;
            document.getElementById('doc-count').textContent = data.secondary_count;
            document.getElementById('edge-count').textContent = data.edges.length;
            document.getElementById('word-count').textContent = data.total_words.toLocaleString();
        }}
        
        function renderVisualization(data) {{
            // Clear visualization
            visualization.innerHTML = '';
            
            // Prepare graph data with type-based clustering positions
            const graphData = {{
                nodes: data.nodes.map(n => ({{
                    ...n,
                    group: n.type,
                    val: n.size * 2,
                    color: typeColors[n.type] || "#999999"
                }})),
                links: data.edges.map(e => ({{
                    source: e.source,
                    target: e.target,
                    value: e.weight
                }}))
            }};
            
            // Initialize 3D force graph
            graph3d = ForceGraph3D()
                (visualization)
                .graphData(graphData)
                .backgroundColor('#1a202c')
                .nodeLabel(node => `
                    <div style="background: rgba(0,0,0,0.9); padding: 8px; border-radius: 4px; color: white; font-size: 12px; max-width: 200px;">
                        <strong>${{node.title}}</strong><br/>
                        Type: ${{node.type}}<br/>
                        Connections: ${{node.in_degree}} in, ${{node.out_degree}} out
                    </div>
                `)
                .nodeColor(node => node.color)
                .nodeVal(node => node.val)
                .nodeOpacity(0.9)
                .linkWidth(link => Math.sqrt(link.value) * 0.5)
                .linkColor(() => 'rgba(160, 174, 192, 0.3)')
                .linkOpacity(0.3)
                .linkDirectionalParticles(link => link.value > 2 ? 2 : 0)
                .linkDirectionalParticleWidth(2)
                .linkDirectionalParticleSpeed(0.006)
                .onNodeClick(handleNodeClick)
                .onNodeDragEnd(node => {{
                    node.fx = node.x;
                    node.fy = node.y;
                    node.fz = node.z;
                }})
                .d3Force('charge', null)  // Remove default charge
                .d3Force('link', d3.forceLink().distance(50).strength(1))
                .enableNodeDrag(true)
                .enableNavigationControls(true);
            
            // Apply clustering if enabled
            if (clusterByType) {{
                applyClustering();
            }}
            
            // Configure physics
            updatePhysics();
        }}
        
        function applyClustering() {{
            if (!graph3d) return;
            
            // Group nodes by type for clustering
            const types = [...new Set(graph3d.graphData().nodes.map(n => n.type))];
            const numTypes = types.length;
            
            // Position cluster centers in a sphere
            const clusterPositions = {{}};
            types.forEach((type, i) => {{
                const phi = Math.acos(-1 + (2 * i) / numTypes);
                const theta = Math.sqrt(numTypes * Math.PI) * phi;
                const radius = 200;
                
                clusterPositions[type] = {{
                    x: radius * Math.cos(theta) * Math.sin(phi),
                    y: radius * Math.sin(theta) * Math.sin(phi),
                    z: radius * Math.cos(phi)
                }};
            }});
            
            // Add clustering force
            graph3d.d3Force('cluster', alpha => {{
                const strength = 0.5 * alpha;
                graph3d.graphData().nodes.forEach(node => {{
                    const cluster = clusterPositions[node.type];
                    if (cluster) {{
                        node.vx -= (node.x - cluster.x) * strength * 0.1;
                        node.vy -= (node.y - cluster.y) * strength * 0.1;
                        node.vz -= (node.z - cluster.z) * strength * 0.1;
                    }}
                }});
            }});
            
            // Add collision force
            graph3d.d3Force('collision', d3.forceCollide().radius(node => node.val + 5).strength(0.8));
        }}
        
        function handleNodeClick(node) {{
            const panel = document.getElementById('info-panel');
            const title = document.getElementById('info-title');
            const content = document.getElementById('info-content');
            
            title.textContent = node.title;
            
            let html = `
                <p><strong>Type:</strong> ${{node.type.replace('_', ' ').toUpperCase()}}</p>
                <p><strong>Agency:</strong> ${{node.agency.replace('-', ' ').toUpperCase()}}</p>
                <p><strong>Words:</strong> ${{node.word_count.toLocaleString()}}</p>
                <p><strong>Connections:</strong> ${{node.in_degree}} in, ${{node.out_degree}} out</p>
                <p><strong>PageRank:</strong> ${{node.pagerank.toFixed(4)}}</p>
            `;
            
            if (node.url) {{
                html += `<p><a href="${{node.url}}" target="_blank" style="color: #667eea;">View Source →</a></p>`;
            }}
            
            content.innerHTML = html;
            panel.classList.add('visible');
            
            // Focus camera on node
            const distance = 200;
            const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
            graph3d.cameraPosition(
                {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
                node,
                1000
            );
        }}
        
        function closeInfo() {{
            document.getElementById('info-panel').classList.remove('visible');
        }}
        
        function resetView() {{
            if (graph3d) {{
                graph3d.cameraPosition({{ x: 0, y: 0, z: 1000 }}, {{ x: 0, y: 0, z: 0 }}, 1000);
            }}
        }}
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            if (graph3d) {{
                if (physicsEnabled) {{
                    graph3d.resumeAnimation();
                }} else {{
                    graph3d.pauseAnimation();
                }}
            }}
        }}
        
        function toggleLabels() {{
            // Labels are handled via nodeLabel in the graph configuration
            // This would require re-rendering, so we'll just show a message
            alert('Labels are shown on hover');
        }}
        
        function toggleClustering() {{
            clusterByType = document.getElementById('cluster-by-type').checked;
            if (graph3d) {{
                if (clusterByType) {{
                    applyClustering();
                }} else {{
                    graph3d.d3Force('cluster', null);
                    graph3d.d3Force('collision', null);
                }}
            }}
        }}
        
        function updatePhysics() {{
            if (!graph3d) return;
            
            const strength = document.getElementById('physics-strength').value / 50;
            
            // Update link force strength
            graph3d.d3Force('link').strength(strength);
            
            // Reheat simulation
            if (physicsEnabled) {{
                graph3d.d3ReheatSimulation();
            }}
        }}
        
        }}); // End DOMContentLoaded
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_agency_options(self, agency_metadata: Dict[str, Dict]) -> str:
        """Generate HTML option elements for agency selector"""
        options = []
        for agency_key in sorted(self.AGENCIES.keys()):
            display_name = self.AGENCIES[agency_key]
            meta = agency_metadata.get(agency_key, {})
            nav_count = meta.get('navigation_count', 0)
            sec_count = meta.get('secondary_count', 0)
            total = nav_count + sec_count
            
            option = f'<option value="{agency_key}">{display_name} ({total} nodes)</option>'
            options.append(option)
        return '\n'.join(options)
    
    def save_agency_data_files(self) -> Dict[str, Path]:
        """Save individual JSON files for each agency"""
        data_dir = self.output_dir / "agency-data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        for agency_key in self.AGENCIES.keys():
            print(f"  Generating data for: {agency_key}")
            data = self.extract_agency_data(agency_key)
            
            file_path = data_dir / f"{agency_key}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            saved_files[agency_key] = file_path
            print(f"    ✓ Saved: {file_path} ({len(data['nodes'])} nodes, {len(data['edges'])} edges)")
        
        return saved_files
    
    def save_visualization(self) -> Path:
        """Save HTML visualization file"""
        print("Generating 3D visualization HTML...")
        html_content = self.generate_3d_html()
        
        output_path = self.output_dir / "agency-navigation-3d.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Saved: {output_path}")
        
        print("\nSaving agency data files...")
        self.save_agency_data_files()
        
        return output_path


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate interactive 3D network visualization for Montana state government",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/viz/agency_network_viz_3d.py
  python src/viz/agency_network_viz_3d.py --output-dir custom/
  python src/viz/agency_network_viz_3d.py --max-nodes 500

This script generates a 3D HTML file with physics-based clustering by content type.

Available agencies:
  administration, agriculture, arts-council, auditor, commerce,
  corrections, environmental-quality, human-resources, labor-industry
        """
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='html',
        help='Output directory for HTML file (default: html/)'
    )
    
    parser.add_argument(
        '--max-nodes',
        type=int,
        default=None,
        help='Maximum nodes per agency (uses importance ranking)'
    )
    
    parser.add_argument(
        '--graph-path',
        type=str,
        default='src/network/exports/montana_knowledge.json',
        help='Path to knowledge graph JSON file'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 60)
    print("3D Agency Network Visualizer - Physics-Based Clustering")
    print("=" * 60)
    
    # Load graph using GraphPersistence
    graph_path = Path(args.graph_path)
    if not graph_path.exists():
        print(f"❌ Graph file not found: {graph_path}")
        return 1
    
    print(f"Loading knowledge graph from: {graph_path}")
    
    # Use the persistence module to load
    persistence = GraphPersistence(output_dir=str(graph_path.parent))
    
    # Try JSON first (more reliable), fallback to pickle
    if graph_path.suffix == '.json':
        json_data = persistence.load_json(filename=graph_path.name, verbose=True)
        if not json_data:
            print("❌ Failed to load graph from JSON")
            return 1
        # Reconstruct KnowledgeGraph from JSON
        graph = KnowledgeGraph()
        # Simple reconstruction - the JSON already has the data we need for visualization
        # We'll use the JSON data directly in extract_agency_data
        graph._json_data = json_data  # Store for later use
        # Create minimal node entries for compatibility
        for node_data in json_data.get('nodes', []):
            # Create a simple object to hold the data
            class NodeProxy:
                def __init__(self, data):
                    self.node_id = data['id']
                    self.title = data['title']
                    self.agency = data['agency']
                    self.node_type = type('obj', (object,), {'value': data['type']})()
                    self.pagerank = data.get('pagerank', 0)
                    self.word_count = data.get('word_count', 0)
                    self.in_degree = data.get('in_degree', 0)
                    self.out_degree = data.get('out_degree', 0)
                    self.topics = data.get('topics', [])
                    self.keywords = data.get('keywords', [])
            graph.nodes[node_data['id']] = NodeProxy(node_data)
        # Create minimal edge entries  
        for edge_data in json_data.get('edges', []):
            class EdgeProxy:
                def __init__(self, data):
                    self.source_id = data['source']
                    self.target_id = data['target']
                    self.edge_type = type('obj', (object,), {'value': data.get('type', 'hyperlink')})()
                    self.weight = data.get('weight', 1.0)
            graph.edges.append(EdgeProxy(edge_data))
    else:
        graph = persistence.load_pickle(filename=graph_path.name, verbose=True)
    
    if not graph:
        print("❌ Failed to load graph")
        return 1
    
    print(f"✓ Graph loaded: {len(graph.nodes):,} nodes, {len(graph.edges):,} edges")
    
    # Determine knowledge_dir based on where we're running from
    if Path("knowledge").exists():
        knowledge_dir = "knowledge"
    else:
        knowledge_dir = "../knowledge"
    
    # Create visualizer
    print(f"\nPreparing 3D visualization for all agencies...")
    visualizer = Agency3DNetworkVisualizer(
        graph,
        output_dir=args.output_dir,
        knowledge_dir=knowledge_dir,
        max_nodes=args.max_nodes
    )
    
    # Generate and save
    output_path = visualizer.save_visualization()
    
    print(f"\n{'=' * 60}")
    print("✅ 3D Visualization generated successfully!")
    print(f"\n📁 Output: {output_path}")
    print(f"\n🚀 To view, run:")
    print(f"   cd {args.output_dir}")
    print(f"   python3 -m http.server 8000")
    print(f"   Then open: http://localhost:8000/agency-navigation-3d.html")
    print(f"{'=' * 60}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
