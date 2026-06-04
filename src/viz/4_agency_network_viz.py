#!/usr/bin/env python
"""
Agency Network Visualization
Creates interactive network graph for Montana state agencies with on-demand loading

Usage:
    python src/viz/4_agency_network_viz.py
    python src/viz/4_agency_network_viz.py --output-dir custom/
    python src/viz/4_agency_network_viz.py --max-nodes 500
"""

import argparse
import json
import sys
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
        """Load graph with module name fixes"""
        import sys
        
        # Create module alias
        if 'network' not in sys.modules:
            import src.network as network
            sys.modules['network'] = network
            sys.modules['network.schema'] = sys.modules['src.network.schema']
        
        try:
            with open(filepath, 'rb') as f:
                graph = pickle.load(f)
            return graph
        except Exception as e:
            print(f"Error loading pickle: {e}")
            return None


class AgencyNetworkVisualizer:
    """Creates interactive D3.js visualization with agency selector and on-demand loading"""
    
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
        """
        Load navigation_network.json for the agency
        
        Args:
            agency_name: Agency folder name
            
        Returns:
            Navigation data dict or None if not found
        """
        nav_path = self.knowledge_dir / agency_name / "navigation_network.json"
        
        if not nav_path.exists():
            return None
        
        try:
            with open(nav_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠ Error loading navigation network for {agency_name}: {e}")
            return None
    
    def extract_agency_data(self, agency_name: str, include_cross_agency: bool = True) -> Dict:
        """
        Extract and prepare data for a specific agency (on-demand)
        
        Args:
            agency_name: Agency folder name
            include_cross_agency: Include edges to other agencies
            
        Returns:
            Dict with 'nodes' and 'edges' ready for visualization
        """
        # Check cache first
        cache_key = f"{agency_name}_{include_cross_agency}_{self.max_nodes}"
        if cache_key in self.agency_data_cache:
            return self.agency_data_cache[cache_key]
        
        # Load navigation network
        navigation_data = self.load_navigation_network(agency_name)
        navigation_nodes = set()
        
        if navigation_data and 'nodes' in navigation_data:
            for url, node_info in navigation_data['nodes'].items():
                if node_info.get('type') == 'html_page':
                    navigation_nodes.add(url)
        
        # Filter nodes for this agency
        agency_nodes_dict = {}
        navigation_priority_nodes = {}
        secondary_nodes = {}
        
        for node_id, node in self.graph.nodes.items():
            if node.agency == agency_name:
                is_navigation = (
                    node.source_url in navigation_nodes or
                    node.node_type.value in ['html_page', 'index_page']
                )
                
                if is_navigation:
                    navigation_priority_nodes[node_id] = node
                else:
                    secondary_nodes[node_id] = node
        
        # Always include all navigation nodes
        agency_nodes_dict.update(navigation_priority_nodes)
        
        # Add secondary nodes up to limit
        if self.max_nodes:
            remaining_slots = self.max_nodes - len(navigation_priority_nodes)
            if remaining_slots > 0 and secondary_nodes:
                sorted_secondary = sorted(
                    secondary_nodes.items(),
                    key=lambda x: (x[1].pagerank_score + x[1].in_degree / 100, x[1].in_degree),
                    reverse=True
                )[:remaining_slots]
                agency_nodes_dict.update(dict(sorted_secondary))
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
                    external_node_id = edge.target_id if edge.source_id in selected_node_ids else edge.source_id
                    if external_node_id in self.graph.nodes and external_node_id not in agency_nodes_dict:
                        external_node = self.graph.nodes[external_node_id]
                        if external_node.pagerank_score > 0.0001:
                            agency_nodes_dict[external_node_id] = external_node
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
        """
        Prepare data structures for D3.js visualization
        
        Args:
            agency_nodes: Filtered nodes for this agency
            agency_edges: Filtered edges for this agency
            navigation_nodes: Set of navigation node URLs
            agency_name: Name of the agency
            
        Returns:
            (nodes_data, edges_data) as JSON-serializable lists
        """
        nodes_data = []
        node_index = {}
        
        # Prepare nodes
        for idx, (node_id, node) in enumerate(agency_nodes.items()):
            node_index[node_id] = idx
            
            # Check if this is a navigation node
            is_navigation_node = (
                node.source_url in navigation_nodes or
                node.node_type.value in ['html_page', 'index_page']
            )
            
            # Determine size based on type and importance
            if node.node_type.value == "agency_root":
                doc_count = node.custom_properties.get("document_count", 0)
                size = min(60 + (doc_count * 2), 150)
            elif is_navigation_node:
                size = min(25 + (node.in_degree * 3) + (node.pagerank_score * 150), 70)
            else:
                size = min(12 + (node.in_degree * 1.5) + (node.pagerank_score * 80), 45)
            
            # Get content preview from chunks
            content_preview = ""
            if node.chunk_ids and len(node.chunk_ids) > 0:
                first_chunk_id = node.chunk_ids[0]
                if first_chunk_id in self.graph.chunks:
                    first_chunk = self.graph.chunks[first_chunk_id]
                    content = first_chunk.content if hasattr(first_chunk, 'content') else str(first_chunk)
                    content_preview = content[:200] + "..." if len(content) > 200 else content
            
            nodes_data.append({
                "id": node_id,
                "index": idx,
                "title": node.title,
                "agency": node.agency,
                "type": node.node_type.value,
                "size": size,
                "topics": node.topics[:5] if node.topics else [],
                "keywords": node.keywords[:5] if node.keywords else [],
                "url": node.source_url or "",
                "in_degree": node.in_degree,
                "out_degree": node.out_degree,
                "word_count": node.word_count,
                "pagerank": round(node.pagerank_score, 6),
                "is_agency": node.node_type.value == "agency_root",
                "is_navigation": is_navigation_node,
                "is_external": node.agency != agency_name,
                "content_preview": content_preview,
                "crawled_date": node.crawled_date.strftime("%Y-%m-%d") if node.crawled_date else "",
            })
        
        # Prepare edges
        edges_data = []
        for edge in agency_edges:
            if edge.source_id in node_index and edge.target_id in node_index:
                edges_data.append({
                    "source": node_index[edge.source_id],
                    "target": node_index[edge.target_id],
                    "type": edge.edge_type.value,
                    "weight": edge.weight,
                    "anchor_text": edge.anchor_text or ""
                })
        
        return nodes_data, edges_data
    
    
    def generate_agency_selector_html_dynamic(self) -> str:
        """
        Generate self-contained HTML with agency selector and 3D visualization
        
        Returns:
            Complete HTML string with 3D agency selector interface that loads JSON files
        """
        # Generate agency metadata (stats only, not full data)
        agency_metadata = {}
        for agency_key, agency_display in self.AGENCIES.items():
            node_count = sum(1 for n in self.graph.nodes.values() if n.agency == agency_key)
            agency_metadata[agency_key] = {
                'display_name': agency_display,
                'node_count': node_count
            }
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Montana State Government - Agency Navigation Network</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
        }}
        
        #container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        #header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 100;
        }}
        
        #header h1 {{
            font-size: 24px;
            color: #2d3748;
            margin-bottom: 5px;
        }}
        
        #header .subtitle {{
            font-size: 14px;
            color: #718096;
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
            color: #2d3748;
        }}
        
        #agency-selector select {{
            padding: 8px 12px;
            border: 2px solid #cbd5e0;
            border-radius: 6px;
            font-size: 14px;
            background: white;
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
            color: #4a5568;
        }}
        
        .stat strong {{
            color: #2d3748;
            font-weight: 600;
        }}
        
        #main {{
            flex: 1;
            display: flex;
            position: relative;
            overflow: hidden;
        }}
        
        #visualization {{
            flex: 1;
            background: white;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        #loading-screen {{
            text-align: center;
            color: #4a5568;
        }}
        
        #loading-screen h2 {{
            font-size: 28px;
            color: #2d3748;
            margin-bottom: 10px;
        }}
        
        #loading-screen p {{
            font-size: 16px;
        }}
        
        .spinner {{
            border: 4px solid #e2e8f0;
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
        
        .error-message {{
            color: #e53e3e;
            background: #fff5f5;
            border: 2px solid #fc8181;
            border-radius: 8px;
            padding: 20px;
            margin: 20px;
            max-width: 500px;
        }}
        
        .error-message h3 {{
            margin-bottom: 10px;
        }}
        
        svg {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        
        svg:active {{
            cursor: grabbing;
        }}
        
        .node {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .node:hover {{
            stroke: #ff6b6b;
            stroke-width: 3px;
        }}
        
        .node.agency-node {{
            stroke: #ffd700;
            stroke-width: 4px;
        }}
        
        .node.navigation-node {{
            stroke: #4299e1;
            stroke-width: 3px;
            filter: brightness(1.1);
        }}
        
        .node.secondary-node {{
            opacity: 0.85;
        }}
        
        .node.external-node {{
            opacity: 0.5;
            stroke-dasharray: 4;
        }}
        
        .node.selected {{
            stroke: #ff0080 !important;
            stroke-width: 5px !important;
            filter: drop-shadow(0 0 8px #ff0080);
        }}
        
        .node.dimmed {{
            opacity: 0.2;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.3;
            fill: none;
            transition: all 0.3s;
        }}
        
        .link.highlighted {{
            stroke: #ff0080;
            stroke-opacity: 0.8;
            stroke-width: 3px;
        }}
        
        .link.dimmed {{
            stroke-opacity: 0.1;
        }}
        
        .link.hyperlink {{ stroke: #3b82f6; }}
        .link.semantic_similar {{ stroke: #10b981; }}
        .link.topic_related {{ stroke: #f59e0b; }}
        .link.belongs_to_agency {{ stroke: #8b5cf6; }}
        
        .label {{
            font-size: 10px;
            font-weight: 600;
            fill: #2d3748;
            pointer-events: none;
            user-select: none;
            text-shadow: 1px 1px 2px rgba(255,255,255,0.9), -1px -1px 2px rgba(255,255,255,0.9);
        }}
        
        .label.important {{
            font-size: 12px;
            font-weight: 700;
            fill: #1a202c;
        }}
        
        .label.secondary {{
            font-size: 9px;
            font-weight: 500;
            fill: #4a5568;
            opacity: 0.85;
        }}
        
        #controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 10;
            min-width: 200px;
            display: none;
        }}
        
        #controls.visible {{
            display: block;
        }}
        
        #controls h3 {{
            font-size: 14px;
            margin-bottom: 10px;
            color: #2d3748;
        }}
        
        #controls button {{
            width: 100%;
            padding: 8px 12px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            background: #4299e1;
            color: white;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }}
        
        #controls button:hover {{
            background: #3182ce;
        }}
        
        #controls label {{
            display: block;
            margin: 10px 0 5px 0;
            font-size: 12px;
            color: #4a5568;
        }}
        
        #controls select {{
            width: 100%;
            padding: 6px;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        #controls input[type="checkbox"] {{
            margin-right: 5px;
        }}
        
        #metadata-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 400px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 20;
            display: none;
        }}
        
        #metadata-panel.visible {{
            display: block;
        }}
        
        .panel-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        
        .panel-header h3 {{
            font-size: 18px;
            margin-bottom: 5px;
        }}
        
        .panel-header .close-btn {{
            position: absolute;
            top: 10px;
            right: 15px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            line-height: 1;
        }}
        
        .panel-header .close-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        .panel-content {{
            padding: 20px;
        }}
        
        .info-group {{
            margin-bottom: 15px;
        }}
        
        .info-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: #718096;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-size: 14px;
            color: #2d3748;
            line-height: 1.5;
        }}
        
        .info-value.preview {{
            font-size: 13px;
            color: #4a5568;
            font-style: italic;
            background: #f7fafc;
            padding: 10px;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}
        
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 5px;
        }}
        
        .tag {{
            background: #e2e8f0;
            color: #2d3748;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
        }}
        
        .primary-action {{
            background: #48bb78;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            text-align: center;
            font-weight: 600;
            cursor: pointer;
            margin: 15px 0;
            display: block;
            text-decoration: none;
            transition: background 0.2s;
        }}
        
        .primary-action:hover {{
            background: #38a169;
        }}
        
        .secondary-action {{
            background: #edf2f7;
            color: #2d3748;
            padding: 8px 15px;
            border-radius: 4px;
            text-align: center;
            font-size: 12px;
            cursor: pointer;
            margin: 5px 0;
            display: block;
            text-decoration: none;
            border: 1px solid #cbd5e0;
            transition: all 0.2s;
        }}
        
        .secondary-action:hover {{
            background: #e2e8f0;
            border-color: #a0aec0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .stat-box {{
            background: #f7fafc;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .stat-box .value {{
            font-size: 18px;
            font-weight: 700;
            color: #667eea;
        }}
        
        .stat-box .label {{
            font-size: 10px;
            text-transform: uppercase;
            color: #718096;
            margin-top: 3px;
        }}
        
        #tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="header">
            <h1>🏛️ Montana State Government - Agency Navigation Network</h1>
            <div class="subtitle">Interactive knowledge graph visualization • Select an agency to explore</div>
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
        
        <div id="main">
            <div id="visualization">
                <div id="loading-screen">
                    <h2>👋 Welcome</h2>
                    <p>Select an agency from the dropdown above to view its knowledge network.</p>
                </div>
            </div>
            
            <div id="controls">
                <h3>Controls</h3>
                <button onclick="resetView()">Reset View</button>
                <button onclick="togglePhysics()">Toggle Physics</button>
                <button onclick="toggleLabels()">Toggle Labels</button>
                
                <label>
                    <input type="checkbox" id="show-external" checked onchange="applyFilters()">
                    Show External Links
                </label>
                
                <label for="type-filter">Document Type:</label>
                <select id="type-filter" onchange="applyFilters()">
                    <option value="all">All Types</option>
                </select>
            </div>
            
            <div id="metadata-panel">
                <div class="panel-header">
                    <h3 id="panel-title">Node Information</h3>
                    <button class="close-btn" onclick="closePanel()">&times;</button>
                </div>
                <div class="panel-content" id="panel-content">
                    <!-- Dynamic content -->
                </div>
            </div>
            
            <div id="tooltip"></div>
        </div>
    </div>
    
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        // Wait for DOM to be ready
        document.addEventListener('DOMContentLoaded', function() {{
        
        // Agency data cache (loaded from JSON files)
        const AGENCY_DATA_CACHE = {{}};
        
        // Current state
        let currentAgency = null;
        let simulation = null;
        let svg = null;
        let g = null;
        let labelsVisible = true;
        let physicsEnabled = true;
        
        // UI elements
        const agencySelect = document.getElementById('agency-select');
        const statsDiv = document.getElementById('stats');
        const visualization = document.getElementById('visualization');
        const controls = document.getElementById('controls');
        const tooltip = d3.select("#tooltip");
        
        // Color schemes
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
        
        // Truncate text to fit within circle
        function truncateText(text, radius, scale = 1) {{
            const charsPerPixel = 0.15 * scale;
            const maxChars = Math.floor(radius * 2 * charsPerPixel);
            if (text.length <= maxChars) return text;
            return text.substring(0, Math.max(3, maxChars - 3)) + '...';
        }}
        
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
                // Check cache first
                let data = AGENCY_DATA_CACHE[agencyKey];
                
                if (!data) {{
                    // Fetch from JSON file
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
                
                // Check if this is a CORS/file protocol error
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
                        <p><strong>Likely Cause:</strong> Browser security restrictions prevent loading files directly.</p>
                        <p><strong>Solution:</strong> Serve this HTML file using a local web server:</p>
                        <pre style="background: #2d3748; color: #e2e8f0; padding: 12px; border-radius: 4px; margin: 10px 0; font-size: 12px; overflow-x: auto;">cd html
python3 -m http.server 8000</pre>
                        <p>Then open: <a href="http://localhost:8000/agency-navigation.html" target="_blank" style="color: #4299e1;">http://localhost:8000/agency-navigation.html</a></p>
                    `;
                }} else {{
                    errorHtml += `
                        <p>Make sure the agency data files are in the correct location:</p>
                        <p><code>html/agency-data/${{agencyKey}}.json</code></p>
                    `;
                }}
                
                errorHtml += `</div>`;
                visualization.innerHTML = errorHtml;
            }}
        }}
        
        function clearVisualization() {{
            visualization.innerHTML = '<div id="loading-screen"><h2>👋 Welcome</h2><p>Select an agency from the dropdown above to view its knowledge network.</p></div>';
            statsDiv.style.display = 'none';
            controls.classList.remove('visible');
            currentAgency = null;
        }}
        
        function updateStats(data) {{
            document.getElementById('nav-count').textContent = data.navigation_count;
            document.getElementById('doc-count').textContent = data.secondary_count;
            document.getElementById('edge-count').textContent = data.edges.length;
            document.getElementById('word-count').textContent = data.total_words.toLocaleString();
            
            // Update type filter
            const typeFilter = document.getElementById('type-filter');
            const types = new Set(data.nodes.map(n => n.type));
            typeFilter.innerHTML = '<option value="all">All Types</option>';
            types.forEach(type => {{
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type.replace('_', ' ').toUpperCase();
                typeFilter.appendChild(option);
            }});
        }}
        
        function renderVisualization(data) {{
            const nodesData = data.nodes;
            const linksData = data.edges;
            
            // Clear visualization area
            visualization.innerHTML = '';
            
            // Get container dimensions
            const width = visualization.clientWidth;
            const height = visualization.clientHeight;
            
            // Create SVG
            const svg = d3.select("#visualization")
                .append("svg")
                .attr("width", "100%")
                .attr("height", "100%")
                .attr("viewBox", `0 0 ${{width}} ${{height}}`);
            
            const g = svg.append("g");
            
            // Add zoom behavior
            const zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                }});
            
            svg.call(zoom);
            
            // Organize nodes into layers
            const agencyNodes = nodesData.filter(d => d.is_agency);
            const navigationNodes = nodesData.filter(d => !d.is_agency && d.is_navigation);
            const secondaryNodes = nodesData.filter(d => !d.is_agency && !d.is_navigation);
            
            // Use D3 force simulation with collision detection
            const simulation = d3.forceSimulation(nodesData)
                .force("link", d3.forceLink(linksData)
                    .id(d => d.index)
                    .distance(d => {{
                        // Shorter links between connected nodes
                        if (d.type === 'hyperlink') return 80;
                        if (d.type === 'semantic_similar') return 120;
                        return 100;
                    }})
                    .strength(0.3))
                .force("charge", d3.forceManyBody()
                    .strength(-300)
                    .distanceMax(500))
                .force("collision", d3.forceCollide()
                    .radius(d => d.size + 5)
                    .strength(0.9))
                .force("x", d3.forceX(d => {{
                    if (d.is_agency) return width / 2;
                    if (d.is_navigation) return width / 2;
                    return width / 2;
                }}).strength(0.05))
                .force("y", d3.forceY(d => {{
                    if (d.is_agency) return height * 0.2;
                    if (d.is_navigation) return height * 0.5;
                    return height * 0.75;
                }}).strength(0.3))
                .alphaDecay(0.02)
                .velocityDecay(0.3);
            
            // Draw links first (so they appear behind nodes)
            const link = g.append("g")
                .attr("class", "links")
                .selectAll("line")
                .data(linksData)
                .join("line")
                .attr("class", d => "link " + d.type)
                .attr("stroke-width", d => Math.sqrt(d.weight) * 1.5);
            
            // Draw nodes
            const node = g.append("g")
                .attr("class", "nodes")
                .selectAll("circle")
                .data(nodesData)
                .join("circle")
                .attr("class", d => {{
                    let classes = "node";
                    if (d.is_agency) classes += " agency-node";
                    if (d.is_navigation) classes += " navigation-node";
                    if (d.is_external) classes += " external-node";
                    if (!d.is_navigation && !d.is_agency) classes += " secondary-node";
                    return classes;
                }})
                .attr("r", d => d.size)
                .attr("fill", d => typeColors[d.type] || "#999")
                .on("mouseover", showTooltip)
                .on("mouseout", hideTooltip)
                .on("click", showMetadataPanel)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            // Draw labels
            const label = g.append("g")
                .attr("class", "labels")
                .selectAll("text")
                .data(nodesData)
                .join("text")
                .attr("class", d => {{
                    if (d.is_navigation || d.is_agency) return "label important";
                    return d.pagerank > 0.001 ? "label" : "label secondary";
                }})
                .attr("text-anchor", "middle")
                .attr("dominant-baseline", "middle")
                .text(d => {{
                    const maxLen = 20;
                    return d.title.length > maxLen ? d.title.substring(0, maxLen) + '...' : d.title;
                }})
                .style("font-size", d => {{
                    const baseFontSize = d.is_agency ? 11 : (d.is_navigation ? 10 : 9);
                    return baseFontSize + "px";
                }});
            
            // Update positions on each tick
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
                
                label
                    .attr("x", d => d.x)
                    .attr("y", d => d.y + d.size + 12);
            }});
            
            // Store for global access
            window.currentElements = {{ node, link, label, svg, g }};
            window.currentSimulation = simulation;
            
            // Store data globally
            window.currentVisualizationData = {{
                nodes: nodesData,
                edges: linksData,
                metadata: {{
                    navigation_count: data.navigation_count,
                    secondary_count: data.secondary_count,
                    total_words: data.total_words
                }}
            }};
            
            console.log('Visualization rendered:', {{
                nodes: nodesData.length,
                edges: linksData.length,
                navigation: data.navigation_count,
                secondary: data.secondary_count
            }});
        }}
        
        // Event handlers
        function highlightNode(d) {{
            if (!window.currentElements) return;
            
            const {{ node, link }} = window.currentElements;
            
            // Clear previous highlights
            node.classed("selected", false).classed("dimmed", false);
            link.classed("highlighted", false).classed("dimmed", false);
            
            if (!d) return; // If null, just clear highlights
            
            // Highlight selected node
            node.filter(n => n === d).classed("selected", true);
            
            // Find connected nodes
            const connectedNodes = new Set();
            connectedNodes.add(d);
            
            // Highlight connected links and collect connected nodes
            link.each(function(l) {{
                if (l.source === d || l.target === d) {{
                    d3.select(this).classed("highlighted", true);
                    connectedNodes.add(l.source);
                    connectedNodes.add(l.target);
                }}
            }});
            
            // Dim non-connected nodes and links
            node.filter(n => !connectedNodes.has(n)).classed("dimmed", true);
            link.filter(l => l.source !== d && l.target !== d).classed("dimmed", true);
        }}
        
        function showTooltip(event, d) {{
            const content = `
                <strong>${{d.title}}</strong><br>
                Type: ${{d.type}}<br>
                Connections: ${{d.in_degree}} in, ${{d.out_degree}} out<br>
                Words: ${{d.word_count.toLocaleString()}}
            `;
            
            tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px")
                .html(content);
        }}
        
        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}
        
        function showMetadataPanel(event, d) {{
            event.stopPropagation();
            
            // Highlight the clicked node and its connections
            highlightNode(d);
            
            const panel = document.getElementById("metadata-panel");
            const title = document.getElementById("panel-title");
            const content = document.getElementById("panel-content");
            
            title.textContent = d.title;
            
            let html = `
                <div class="info-group">
                    <div class="info-label">Document Type</div>
                    <div class="info-value">${{d.type.replace('_', ' ').toUpperCase()}}</div>
                </div>
                
                <div class="info-group">
                    <div class="info-label">Agency</div>
                    <div class="info-value">${{d.agency.replace('-', ' ').toUpperCase()}}</div>
                </div>
            `;
            
            if (d.url) {{
                html += `
                    <a href="${{d.url}}" target="_blank" class="primary-action">
                        📄 View Source Document
                    </a>
                    <button class="secondary-action" onclick="copyUrl('${{d.url}}')">
                        📋 Copy URL
                    </button>
                `;
            }}
            
            html += `
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="value">${{d.in_degree}}</div>
                        <div class="label">Incoming</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.out_degree}}</div>
                        <div class="label">Outgoing</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.word_count.toLocaleString()}}</div>
                        <div class="label">Words</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.pagerank.toFixed(4)}}</div>
                        <div class="label">PageRank</div>
                    </div>
                </div>
            `;
            
            if (d.topics && d.topics.length > 0) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Topics</div>
                        <div class="tags">
                            ${{d.topics.map(t => '<span class="tag">' + t + '</span>').join('')}}
                        </div>
                    </div>
                `;
            }}
            
            if (d.keywords && d.keywords.length > 0) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Keywords</div>
                        <div class="tags">
                            ${{d.keywords.map(k => '<span class="tag">' + k + '</span>').join('')}}
                        </div>
                    </div>
                `;
            }}
            
            if (d.content_preview) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Content Preview</div>
                        <div class="info-value preview">${{d.content_preview}}</div>
                    </div>
                `;
            }}
            
            if (d.crawled_date) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Crawled Date</div>
                        <div class="info-value">${{d.crawled_date}}</div>
                    </div>
                `;
            }}
            
            content.innerHTML = html;
            panel.classList.add("visible");
        }}
        
        function closePanel() {{
            document.getElementById("metadata-panel").classList.remove("visible");
            highlightNode(null); // Clear highlights
        }}
        
        function copyUrl(url) {{
            navigator.clipboard.writeText(url).then(() => {{
                alert("URL copied to clipboard!");
            }});
        }}
        
        function dragstarted(event, d) {{
            if (!event.active && window.currentSimulation) {{
                window.currentSimulation.alphaTarget(0.3).restart();
            }}
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active && window.currentSimulation) {{
                window.currentSimulation.alphaTarget(0);
            }}
            d.fx = null;
            d.fy = null;
        }}
        
        function resetView() {{
            if (window.currentElements && window.currentElements.svg) {{
                window.currentElements.svg
                    .transition()
                    .duration(750)
                    .call(d3.zoom().transform, d3.zoomIdentity);
            }}
        }}
        
        function togglePhysics() {{
            if (window.currentSimulation) {{
                const alpha = window.currentSimulation.alpha();
                if (alpha > 0) {{
                    window.currentSimulation.stop();
                    console.log('Physics paused');
                }} else {{
                    window.currentSimulation.alpha(0.3).restart();
                    console.log('Physics resumed');
                }}
            }}
        }}
        
        function toggleLabels() {{
            labelsVisible = !labelsVisible;
            if (window.currentElements && window.currentElements.label) {{
                window.currentElements.label
                    .transition()
                    .duration(300)
                    .style("opacity", labelsVisible ? 1 : 0);
            }}
        }}
        
        function updateLabelVisibility(scale) {{
            if (!labelsVisible || !window.currentElements || !window.currentElements.label) return;
            
            window.currentElements.label.style("opacity", d => {{
                if (d.is_agency || d.is_navigation) return 1;
                return scale > 1.5 ? 1 : 0.5;
            }});
        }}
        
        function applyFilters() {{
            if (!window.currentElements) return;
            
            const showExternal = document.getElementById("show-external").checked;
            const typeFilter = document.getElementById("type-filter").value;
            
            const {{ node, link, label }} = window.currentElements;
            
            // Filter nodes
            node.style("display", d => {{
                if (!showExternal && d.is_external) return "none";
                if (typeFilter !== "all" && d.type !== typeFilter) return "none";
                return "block";
            }});
            
            // Filter labels
            label.style("display", d => {{
                if (!showExternal && d.is_external) return "none";
                if (typeFilter !== "all" && d.type !== typeFilter) return "none";
                return "block";
            }});
            
            // Filter links (only show if both source and target are visible)
            link.style("display", l => {{
                const sourceVisible = (!showExternal || !l.source.is_external) && 
                                    (typeFilter === "all" || l.source.type === typeFilter);
                const targetVisible = (!showExternal || !l.target.is_external) && 
                                    (typeFilter === "all" || l.target.type === typeFilter);
                return (sourceVisible && targetVisible) ? "block" : "none";
            }});
        }}
        
        // Close panel when clicking outside
        document.addEventListener("click", (e) => {{
            const panel = document.getElementById("metadata-panel");
            if (panel.classList.contains("visible") && !panel.contains(e.target)) {{
                closePanel();
            }}
        }});
        
        // Clear highlights when clicking on SVG background
        svg.on("click", () => {{
            highlightNode(null);
        }});
        
        }}); // End DOMContentLoaded
    </script>
</body>
</html>'''
        
        return html
    
    def generate_agency_selector_html(self) -> str:
        """
        Generate self-contained HTML with agency selector and on-demand loading
        
        Returns:
            Complete HTML string with agency selector interface
        """
        # Generate agency data metadata (stats only, not full data)
        agency_metadata = {}
        for agency_key, agency_display in self.AGENCIES.items():
            node_count = sum(1 for n in self.graph.nodes.values() if n.agency == agency_key)
            agency_metadata[agency_key] = {
                'display_name': agency_display,
                'node_count': node_count
            }
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Montana State Government - Agency Navigation Network</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
        }}
        
        #container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        #header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 100;
        }}
        
        #header h1 {{
            font-size: 24px;
            color: #2d3748;
            margin-bottom: 5px;
        }}
        
        #header .subtitle {{
            font-size: 14px;
            color: #718096;
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
            color: #2d3748;
        }}
        
        #agency-selector select {{
            padding: 8px 12px;
            border: 2px solid #cbd5e0;
            border-radius: 6px;
            font-size: 14px;
            background: white;
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
            color: #4a5568;
        }}
        
        .stat strong {{
            color: #2d3748;
            font-weight: 600;
        }}
        
        #main {{
            flex: 1;
            display: flex;
            position: relative;
            overflow: hidden;
        }}
        
        #visualization {{
            flex: 1;
            background: white;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        #loading-screen {{
            text-align: center;
            color: #4a5568;
        }}
        
        #loading-screen h2 {{
            font-size: 28px;
            color: #2d3748;
            margin-bottom: 10px;
        }}
        
        #loading-screen p {{
            font-size: 16px;
        }}
        
        .spinner {{
            border: 4px solid #e2e8f0;
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
        
        svg {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        
        svg:active {{
            cursor: grabbing;
        }}
        
        .node {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .node:hover {{
            stroke: #ff6b6b;
            stroke-width: 3px;
        }}
        
        .node.agency-node {{
            stroke: #ffd700;
            stroke-width: 4px;
        }}
        
        .node.navigation-node {{
            stroke: #4299e1;
            stroke-width: 3px;
            filter: brightness(1.1);
        }}
        
        .node.secondary-node {{
            opacity: 0.85;
        }}
        
        .node.external-node {{
            opacity: 0.5;
            stroke-dasharray: 4;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.3;
            fill: none;
        }}
        
        .link.hyperlink {{ stroke: #3b82f6; }}
        .link.semantic_similar {{ stroke: #10b981; }}
        .link.topic_related {{ stroke: #f59e0b; }}
        .link.belongs_to_agency {{ stroke: #8b5cf6; }}
        
        .label {{
            font-size: 11px;
            font-weight: 500;
            fill: #2d3748;
            pointer-events: none;
            user-select: none;
            text-shadow: 1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white;
        }}
        
        .label.important {{
            font-size: 13px;
            font-weight: 600;
            fill: #1a202c;
        }}
        
        .label.secondary {{
            font-size: 10px;
            font-weight: 400;
            fill: #4a5568;
            opacity: 0.7;
        }}
        
        #controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 10;
            min-width: 200px;
            display: none;
        }}
        
        #controls.visible {{
            display: block;
        }}
        
        #controls h3 {{
            font-size: 14px;
            margin-bottom: 10px;
            color: #2d3748;
        }}
        
        #controls button {{
            width: 100%;
            padding: 8px 12px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            background: #4299e1;
            color: white;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }}
        
        #controls button:hover {{
            background: #3182ce;
        }}
        
        #controls label {{
            display: block;
            margin: 10px 0 5px 0;
            font-size: 12px;
            color: #4a5568;
        }}
        
        #controls select {{
            width: 100%;
            padding: 6px;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        #controls input[type="checkbox"] {{
            margin-right: 5px;
        }}
        
        #metadata-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 400px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 20;
            display: none;
        }}
        
        #metadata-panel.visible {{
            display: block;
        }}
        
        .panel-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        
        .panel-header h3 {{
            font-size: 18px;
            margin-bottom: 5px;
        }}
        
        .panel-header .close-btn {{
            position: absolute;
            top: 10px;
            right: 15px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            line-height: 1;
        }}
        
        .panel-header .close-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        .panel-content {{
            padding: 20px;
        }}
        
        .info-group {{
            margin-bottom: 15px;
        }}
        
        .info-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: #718096;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-size: 14px;
            color: #2d3748;
            line-height: 1.5;
        }}
        
        .info-value.preview {{
            font-size: 13px;
            color: #4a5568;
            font-style: italic;
            background: #f7fafc;
            padding: 10px;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}
        
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 5px;
        }}
        
        .tag {{
            background: #e2e8f0;
            color: #2d3748;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
        }}
        
        .primary-action {{
            background: #48bb78;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            text-align: center;
            font-weight: 600;
            cursor: pointer;
            margin: 15px 0;
            display: block;
            text-decoration: none;
            transition: background 0.2s;
        }}
        
        .primary-action:hover {{
            background: #38a169;
        }}
        
        .secondary-action {{
            background: #edf2f7;
            color: #2d3748;
            padding: 8px 15px;
            border-radius: 4px;
            text-align: center;
            font-size: 12px;
            cursor: pointer;
            margin: 5px 0;
            display: block;
            text-decoration: none;
            border: 1px solid #cbd5e0;
            transition: all 0.2s;
        }}
        
        .secondary-action:hover {{
            background: #e2e8f0;
            border-color: #a0aec0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .stat-box {{
            background: #f7fafc;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .stat-box .value {{
            font-size: 18px;
            font-weight: 700;
            color: #667eea;
        }}
        
        .stat-box .label {{
            font-size: 10px;
            text-transform: uppercase;
            color: #718096;
            margin-top: 3px;
        }}
        
        #tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="header">
            <h1>🏛️ Montana State Government - Agency Navigation Network</h1>
            <div class="subtitle">Interactive knowledge graph visualization • Select an agency to explore</div>
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
        
        <div id="main">
            <div id="visualization">
                <div id="loading-screen">
                    <h2>👋 Welcome</h2>
                    <p>Select an agency from the dropdown above to view its knowledge network.</p>
                </div>
            </div>
            
            <div id="controls">
                <h3>Controls</h3>
                <button onclick="resetView()">Reset View</button>
                <button onclick="togglePhysics()">Toggle Physics</button>
                <button onclick="toggleLabels()">Toggle Labels</button>
                
                <label>
                    <input type="checkbox" id="show-external" checked onchange="applyFilters()">
                    Show External Links
                </label>
                
                <label for="type-filter">Document Type:</label>
                <select id="type-filter" onchange="applyFilters()">
                    <option value="all">All Types</option>
                </select>
            </div>
            
            <div id="metadata-panel">
                <div class="panel-header">
                    <h3 id="panel-title">Node Information</h3>
                    <button class="close-btn" onclick="closePanel()">&times;</button>
                </div>
                <div class="panel-content" id="panel-content">
                    <!-- Dynamic content -->
                </div>
            </div>
            
            <div id="tooltip"></div>
        </div>
    </div>
    
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        // Embedded agency data (loaded on-demand)
        const AGENCY_DATA = {json.dumps({k: self.extract_agency_data(k) for k in self.AGENCIES.keys()}, indent=8)};
        
        // Current state
        let currentAgency = null;
        let simulation = null;
        let svg = null;
        let g = null;
        let labelsVisible = true;
        let physicsEnabled = true;
        
        // UI elements
        const agencySelect = document.getElementById('agency-select');
        const statsDiv = document.getElementById('stats');
        const visualization = document.getElementById('visualization');
        const controls = document.getElementById('controls');
        const tooltip = d3.select("#tooltip");
        
        // Color schemes
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
        
        // Truncate text to fit within circle
        function truncateText(text, radius, scale = 1) {{
            const charsPerPixel = 0.15 * scale;
            const maxChars = Math.floor(radius * 2 * charsPerPixel);
            if (text.length <= maxChars) return text;
            return text.substring(0, Math.max(3, maxChars - 3)) + '...';
        }}
        
        // Agency selection handler
        agencySelect.addEventListener('change', (e) => {{
            const agency = e.target.value;
            if (agency) {{
                loadAgency(agency);
            }} else {{
                clearVisualization();
            }}
        }});
        
        function loadAgency(agencyKey) {{
            currentAgency = agencyKey;
            
            // Show loading
            visualization.innerHTML = '<div id="loading-screen"><h2>Loading...</h2><div class="spinner"></div></div>';
            
            // Simulate async loading (data is already embedded)
            setTimeout(() => {{
                const data = AGENCY_DATA[agencyKey];
                if (data) {{
                    renderVisualization(data);
                    updateStats(data);
                    statsDiv.style.display = 'flex';
                    controls.classList.add('visible');
                }}
            }}, 100);
        }}
        
        function clearVisualization() {{
            visualization.innerHTML = '<div id="loading-screen"><h2>👋 Welcome</h2><p>Select an agency from the dropdown above to view its knowledge network.</p></div>';
            statsDiv.style.display = 'none';
            controls.classList.remove('visible');
            currentAgency = null;
        }}
        
        function updateStats(data) {{
            document.getElementById('nav-count').textContent = data.navigation_count;
            document.getElementById('doc-count').textContent = data.secondary_count;
            document.getElementById('edge-count').textContent = data.edges.length;
            document.getElementById('word-count').textContent = data.total_words.toLocaleString();
            
            // Update type filter
            const typeFilter = document.getElementById('type-filter');
            const types = new Set(data.nodes.map(n => n.type));
            typeFilter.innerHTML = '<option value="all">All Types</option>';
            types.forEach(type => {{
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type.replace('_', ' ').toUpperCase();
                typeFilter.appendChild(option);
            }});
        }}
        
        function renderVisualization(data) {{
            const nodesData = data.nodes;
            const linksData = data.edges;
            
            // Clear and setup SVG
            visualization.innerHTML = '';
            const width = visualization.clientWidth;
            const height = visualization.clientHeight;
            
            svg = d3.select("#visualization")
                .append("svg")
                .attr("width", "100%")
                .attr("height", "100%");
            
            g = svg.append("g");
            
            // Zoom behavior
            const zoom = d3.zoom()
                .scaleExtent([0.1, 10])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                    updateLabelVisibility(event.transform.k);
                }});
            
            svg.call(zoom);
            
            // Force simulation
            simulation = d3.forceSimulation(nodesData)
                .force("link", d3.forceLink(linksData)
                    .id(d => d.index)
                    .distance(d => {{
                        if (d.type === "hyperlink") return 80;
                        if (d.type === "belongs_to_agency") return 50;
                        return 120;
                    }})
                    .strength(d => {{
                        const sourceNode = nodesData[d.source.index || d.source];
                        const targetNode = nodesData[d.target.index || d.target];
                        if (sourceNode && targetNode) {{
                            if (sourceNode.is_navigation && targetNode.is_navigation) return 1.0;
                            if (sourceNode.is_navigation || targetNode.is_navigation) return 0.7;
                        }}
                        return 0.5;
                    }})
                )
                .force("charge", d3.forceManyBody()
                    .strength(d => {{
                        if (d.is_agency) return -1200;
                        if (d.is_navigation) return -500;
                        return -200;
                    }})
                )
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide()
                    .radius(d => d.size + 8)
                )
                .force("radial", d3.forceRadial(
                    d => {{
                        if (d.is_agency) return 0;
                        if (d.is_navigation) return 150;
                        return 350;
                    }},
                    width / 2,
                    height / 2
                ).strength(d => d.is_navigation ? 0.15 : 0.05));
            
            // Draw links
            const link = g.append("g")
                .attr("class", "links")
                .selectAll("line")
                .data(linksData)
                .join("line")
                .attr("class", d => "link " + d.type)
                .attr("stroke-width", d => Math.sqrt(d.weight) * 1.5);
            
            // Draw nodes
            const node = g.append("g")
                .attr("class", "nodes")
                .selectAll("circle")
                .data(nodesData)
                .join("circle")
                .attr("class", d => {{
                    let classes = "node";
                    if (d.is_agency) classes += " agency-node";
                    if (d.is_navigation) classes += " navigation-node";
                    if (d.is_external) classes += " external-node";
                    if (!d.is_navigation && !d.is_agency) classes += " secondary-node";
                    return classes;
                }})
                .attr("r", d => d.size)
                .attr("fill", d => typeColors[d.type] || "#999")
                .attr("stroke-width", d => {{
                    if (d.is_agency) return 4;
                    if (d.is_navigation) return 3;
                    return 2;
                }})
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended))
                .on("mouseover", showTooltip)
                .on("mouseout", hideTooltip)
                .on("click", showMetadataPanel);
            
            // Draw labels
            const label = g.append("g")
                .attr("class", "labels")
                .selectAll("text")
                .data(nodesData)
                .join("text")
                .attr("class", d => {{
                    if (d.is_navigation || d.is_agency) return "label important";
                    return d.pagerank > 0.001 ? "label" : "label secondary";
                }})
                .text(d => d.title.length > 30 ? d.title.substring(0, 30) + "..." : d.title)
                .attr("dx", d => d.size + 5)
                .attr("dy", 4);
            
            // Store for global access
            window.currentElements = {{ node, link, label }};
            
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
                
                label
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
            }});
        }}
        
        // Event handlers
        function showTooltip(event, d) {{
            const content = `
                <strong>${{d.title}}</strong><br>
                Type: ${{d.type}}<br>
                Connections: ${{d.in_degree}} in, ${{d.out_degree}} out<br>
                Words: ${{d.word_count.toLocaleString()}}
            `;
            
            tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px")
                .html(content);
        }}
        
        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}
        
        function showMetadataPanel(event, d) {{
            event.stopPropagation();
            
            const panel = document.getElementById("metadata-panel");
            const title = document.getElementById("panel-title");
            const content = document.getElementById("panel-content");
            
            title.textContent = d.title;
            
            let html = `
                <div class="info-group">
                    <div class="info-label">Document Type</div>
                    <div class="info-value">${{d.type.replace('_', ' ').toUpperCase()}}</div>
                </div>
                
                <div class="info-group">
                    <div class="info-label">Agency</div>
                    <div class="info-value">${{d.agency.replace('-', ' ').toUpperCase()}}</div>
                </div>
            `;
            
            if (d.url) {{
                html += `
                    <a href="${{d.url}}" target="_blank" class="primary-action">
                        📄 View Source Document
                    </a>
                    <button class="secondary-action" onclick="copyUrl('${{d.url}}')">
                        📋 Copy URL
                    </button>
                `;
            }}
            
            html += `
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="value">${{d.in_degree}}</div>
                        <div class="label">Incoming</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.out_degree}}</div>
                        <div class="label">Outgoing</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.word_count.toLocaleString()}}</div>
                        <div class="label">Words</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.pagerank.toFixed(4)}}</div>
                        <div class="label">PageRank</div>
                    </div>
                </div>
            `;
            
            if (d.topics && d.topics.length > 0) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Topics</div>
                        <div class="tags">
                            ${{d.topics.map(t => '<span class="tag">' + t + '</span>').join('')}}
                        </div>
                    </div>
                `;
            }}
            
            if (d.keywords && d.keywords.length > 0) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Keywords</div>
                        <div class="tags">
                            ${{d.keywords.map(k => '<span class="tag">' + k + '</span>').join('')}}
                        </div>
                    </div>
                `;
            }}
            
            if (d.content_preview) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Content Preview</div>
                        <div class="info-value preview">${{d.content_preview}}</div>
                    </div>
                `;
            }}
            
            if (d.crawled_date) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Crawled Date</div>
                        <div class="info-value">${{d.crawled_date}}</div>
                    </div>
                `;
            }}
            
            content.innerHTML = html;
            panel.classList.add("visible");
        }}
        
        function closePanel() {{
            document.getElementById("metadata-panel").classList.remove("visible");
        }}
        
        function copyUrl(url) {{
            navigator.clipboard.writeText(url).then(() => {{
                alert("URL copied to clipboard!");
            }});
        }}
        
        function dragstarted(event, d) {{
            if (!event.active && physicsEnabled) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active && physicsEnabled) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        function resetView() {{
            if (svg) {{
                svg.transition().duration(750).call(d3.zoom().transform, d3.zoomIdentity);
            }}
        }}
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            if (simulation) {{
                if (physicsEnabled) {{
                    simulation.alphaTarget(0.3).restart();
                }} else {{
                    simulation.stop();
                }}
            }}
        }}
        
        function toggleLabels() {{
            labelsVisible = !labelsVisible;
            if (window.currentElements && window.currentElements.label) {{
                window.currentElements.label.style("opacity", labelsVisible ? 1 : 0);
            }}
        }}
        
        function updateLabelVisibility(scale) {{
            if (!labelsVisible || !window.currentElements || !window.currentElements.label) return;
            
            window.currentElements.label.style("opacity", d => {{
                if (d.is_agency || d.pagerank > 0.001) return 1;
                return scale > 1 ? 1 : 0.3;
            }});
        }}
        
        function applyFilters() {{
            if (!window.currentElements) return;
            
            const showExternal = document.getElementById("show-external").checked;
            const typeFilter = document.getElementById("type-filter").value;
            
            const {{ node, link, label }} = window.currentElements;
            
            node.style("display", d => {{
                if (!showExternal && d.is_external) return "none";
                if (typeFilter !== "all" && d.type !== typeFilter) return "none";
                return "block";
            }});
            
            label.style("display", d => {{
                if (!showExternal && d.is_external) return "none";
                if (typeFilter !== "all" && d.type !== typeFilter) return "none";
                return "block";
            }});
            
            link.style("display", l => {{
                const sourceVisible = (!showExternal || !l.source.is_external) && 
                                    (typeFilter === "all" || l.source.type === typeFilter);
                const targetVisible = (!showExternal || !l.target.is_external) && 
                                    (typeFilter === "all" || l.target.type === typeFilter);
                return (sourceVisible && targetVisible) ? "block" : "none";
            }});
        }}
        
        // Close panel when clicking outside
        document.addEventListener("click", (e) => {{
            const panel = document.getElementById("metadata-panel");
            if (panel.classList.contains("visible") && !panel.contains(e.target)) {{
                closePanel();
            }}
        }});
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_agency_options(self, agency_metadata: Dict[str, Dict]) -> str:
        """Generate HTML options for agency selector"""
        options = []
        for agency_key in sorted(self.AGENCIES.keys()):
            meta = agency_metadata.get(agency_key, {})
            display_name = meta.get('display_name', agency_key)
            node_count = meta.get('node_count', 0)
            options.append(f'<option value="{agency_key}">{display_name} ({node_count} documents)</option>')
        return '\n                    '.join(options)
        """
        Generate self-contained HTML with D3.js visualization
        
        Args:
            nodes_data: Node data for visualization
            edges_data: Edge data for visualization
            
        Returns:
            Complete HTML string
        """
        # Calculate statistics
        type_counts = defaultdict(int)
        total_words = 0
        navigation_count = 0
        secondary_count = 0
        
        for node in nodes_data:
            type_counts[node['type']] += 1
            total_words += node['word_count']
            if node.get('is_navigation'):
                navigation_count += 1
            elif not node.get('is_external'):
                secondary_count += 1
        
        # Agency display name
        agency_display = self.agency_name.replace('-', ' ').title()
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agency_display} - Navigation Network</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
        }}
        
        #container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        #header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 100;
        }}
        
        #header h1 {{
            font-size: 24px;
            color: #2d3748;
            margin-bottom: 5px;
        }}
        
        #header .subtitle {{
            font-size: 14px;
            color: #718096;
        }}
        
        #stats {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }}
        
        .stat {{
            font-size: 12px;
            color: #4a5568;
        }}
        
        .stat strong {{
            color: #2d3748;
            font-weight: 600;
        }}
        
        #main {{
            flex: 1;
            display: flex;
            position: relative;
            overflow: hidden;
        }}
        
        #visualization {{
            flex: 1;
            background: white;
            position: relative;
        }}
        
        svg {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        
        svg:active {{
            cursor: grabbing;
        }}
        
        .node {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .node:hover {{
            stroke: #ff6b6b;
            stroke-width: 3px;
        }}
        
        .node.agency-node {{
            stroke: #ffd700;
            stroke-width: 4px;
        }}
        
        .node.navigation-node {{
            stroke: #4299e1;
            stroke-width: 3px;
            filter: brightness(1.1);
        }}
        
        .node.secondary-node {{
            opacity: 0.85;
        }}
        
        .node.external-node {{
            opacity: 0.5;
            stroke-dasharray: 4;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.3;
            fill: none;
        }}
        
        .link.hyperlink {{ stroke: #3b82f6; }}
        .link.semantic_similar {{ stroke: #10b981; }}
        .link.topic_related {{ stroke: #f59e0b; }}
        .link.belongs_to_agency {{ stroke: #8b5cf6; }}
        
        .label {{
            font-size: 11px;
            font-weight: 500;
            fill: #2d3748;
            pointer-events: none;
            user-select: none;
            text-shadow: 1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white;
        }}
        
        .label.important {{
            font-size: 13px;
            font-weight: 600;
            fill: #1a202c;
        }}
        
        .label.secondary {{
            font-size: 10px;
            font-weight: 400;
            fill: #4a5568;
            opacity: 0.7;
        }}
        
        #controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 10;
            min-width: 200px;
        }}
        
        #controls h3 {{
            font-size: 14px;
            margin-bottom: 10px;
            color: #2d3748;
        }}
        
        #controls button {{
            width: 100%;
            padding: 8px 12px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            background: #4299e1;
            color: white;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }}
        
        #controls button:hover {{
            background: #3182ce;
        }}
        
        #controls label {{
            display: block;
            margin: 10px 0 5px 0;
            font-size: 12px;
            color: #4a5568;
        }}
        
        #controls select {{
            width: 100%;
            padding: 6px;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        #controls input[type="checkbox"] {{
            margin-right: 5px;
        }}
        
        #metadata-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 400px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 20;
            display: none;
        }}
        
        #metadata-panel.visible {{
            display: block;
        }}
        
        .panel-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        
        .panel-header h3 {{
            font-size: 18px;
            margin-bottom: 5px;
        }}
        
        .panel-header .close-btn {{
            position: absolute;
            top: 10px;
            right: 15px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            line-height: 1;
        }}
        
        .panel-header .close-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        .panel-content {{
            padding: 20px;
        }}
        
        .info-group {{
            margin-bottom: 15px;
        }}
        
        .info-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: #718096;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-size: 14px;
            color: #2d3748;
            line-height: 1.5;
        }}
        
        .info-value.preview {{
            font-size: 13px;
            color: #4a5568;
            font-style: italic;
            background: #f7fafc;
            padding: 10px;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}
        
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 5px;
        }}
        
        .tag {{
            background: #e2e8f0;
            color: #2d3748;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
        }}
        
        .primary-action {{
            background: #48bb78;
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            text-align: center;
            font-weight: 600;
            cursor: pointer;
            margin: 15px 0;
            display: block;
            text-decoration: none;
            transition: background 0.2s;
        }}
        
        .primary-action:hover {{
            background: #38a169;
        }}
        
        .secondary-action {{
            background: #edf2f7;
            color: #2d3748;
            padding: 8px 15px;
            border-radius: 4px;
            text-align: center;
            font-size: 12px;
            cursor: pointer;
            margin: 5px 0;
            display: block;
            text-decoration: none;
            border: 1px solid #cbd5e0;
            transition: all 0.2s;
        }}
        
        .secondary-action:hover {{
            background: #e2e8f0;
            border-color: #a0aec0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .stat-box {{
            background: #f7fafc;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .stat-box .value {{
            font-size: 18px;
            font-weight: 700;
            color: #667eea;
        }}
        
        .stat-box .label {{
            font-size: 10px;
            text-transform: uppercase;
            color: #718096;
            margin-top: 3px;
        }}
        
        #tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="header">
            <h1>🏛️ {agency_display} - Navigation Network</h1>
            <div class="subtitle">Interactive knowledge graph visualization • Navigation pages (blue border) form the core structure</div>
            <div id="stats">
                <div class="stat"><strong>{navigation_count}</strong> Navigation Pages</div>
                <div class="stat"><strong>{secondary_count}</strong> Documents</div>
                <div class="stat"><strong>{len(edges_data)}</strong> Connections</div>
                <div class="stat"><strong>{total_words:,}</strong> Words</div>
            </div>
        </div>
        
        <div id="main">
            <div id="visualization"></div>
            
            <div id="controls">
                <h3>Controls</h3>
                <button onclick="resetView()">Reset View</button>
                <button onclick="togglePhysics()">Toggle Physics</button>
                <button onclick="toggleLabels()">Toggle Labels</button>
                
                <label>
                    <input type="checkbox" id="show-external" checked onchange="applyFilters()">
                    Show External Links
                </label>
                
                <label for="type-filter">Document Type:</label>
                <select id="type-filter" onchange="applyFilters()">
                    <option value="all">All Types</option>
                    {self._generate_type_options(type_counts)}
                </select>
            </div>
            
            <div id="metadata-panel">
                <div class="panel-header">
                    <h3 id="panel-title">Node Information</h3>
                    <button class="close-btn" onclick="closePanel()">&times;</button>
                </div>
                <div class="panel-content" id="panel-content">
                    <!-- Dynamic content -->
                </div>
            </div>
            
            <div id="tooltip"></div>
        </div>
    </div>
    
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        // Data
        const nodesData = {json.dumps(nodes_data, indent=8)};
        const linksData = {json.dumps(edges_data, indent=8)};
        
        // Configuration
        const width = window.innerWidth;
        const height = window.innerHeight - 100;
        let labelsVisible = true;
        let physicsEnabled = true;
        
        // Color schemes
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
        
        // SVG setup
        const svg = d3.select("#visualization")
            .append("svg")
            .attr("width", "100%")
            .attr("height", "100%");
        
        const g = svg.append("g");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
                updateLabelVisibility(event.transform.k);
            }});
        
        svg.call(zoom);
        
        // Tooltip
        const tooltip = d3.select("#tooltip");
        
        // Force simulation
        // Navigation nodes form the core structure, secondary nodes hang off them
        let simulation = d3.forceSimulation(nodesData)
            .force("link", d3.forceLink(linksData)
                .id(d => d.index)
                .distance(d => {{
                    // Shorter distances for navigation links
                    if (d.type === "hyperlink") return 80;
                    if (d.type === "belongs_to_agency") return 50;
                    // Longer distances for secondary documents
                    return 120;
                }})
                .strength(d => {{
                    // Stronger links between navigation nodes
                    const sourceNode = nodesData[d.source.index || d.source];
                    const targetNode = nodesData[d.target.index || d.target];
                    if (sourceNode && targetNode) {{
                        if (sourceNode.is_navigation && targetNode.is_navigation) return 1.0;
                        if (sourceNode.is_navigation || targetNode.is_navigation) return 0.7;
                    }}
                    return 0.5;
                }})
            )
            .force("charge", d3.forceManyBody()
                .strength(d => {{
                    if (d.is_agency) return -1200;
                    if (d.is_navigation) return -500;  // Navigation nodes repel more
                    return -200;  // Secondary nodes repel less (cluster near navigation)
                }})
            )
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide()
                .radius(d => d.size + 8)
            )
            .force("radial", d3.forceRadial(
                d => {{
                    if (d.is_agency) return 0;
                    if (d.is_navigation) return 150;  // Navigation nodes closer to center
                    return 350;  // Secondary nodes further out
                }},
                width / 2,
                height / 2
            ).strength(d => d.is_navigation ? 0.15 : 0.05));  // Stronger pull for navigation;
        
        // Draw links
        const link = g.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(linksData)
            .join("line")
            .attr("class", d => "link " + d.type)
            .attr("stroke-width", d => Math.sqrt(d.weight) * 1.5);
        
        // Draw nodes
        const node = g.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodesData)
            .join("circle")
            .attr("class", d => {{
                let classes = "node";
                if (d.is_agency) classes += " agency-node";
                if (d.is_navigation) classes += " navigation-node";  // Navigation nodes
                if (d.is_external) classes += " external-node";
                if (!d.is_navigation && !d.is_agency) classes += " secondary-node";  // PDFs, etc.
                return classes;
            }})
            .attr("r", d => d.size)
            .attr("fill", d => typeColors[d.type] || "#999")
            .attr("stroke-width", d => {{
                if (d.is_agency) return 4;
                if (d.is_navigation) return 3;  // Thicker border for navigation
                return 2;
            }})
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("mouseover", showTooltip)
            .on("mouseout", hideTooltip)
            .on("click", showMetadataPanel);
        
        // Draw labels
        const label = g.append("g")
            .attr("class", "labels")
            .selectAll("text")
            .data(nodesData)
            .join("text")
            .attr("class", d => {{
                // Navigation nodes and important nodes get emphasized labels
                if (d.is_navigation || d.is_agency) return "label important";
                return d.pagerank > 0.001 ? "label" : "label secondary";
            }})
            .text(d => d.title.length > 30 ? d.title.substring(0, 30) + "..." : d.title)
            .attr("dx", d => d.size + 5)
            .attr("dy", 4);
        
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
            
            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});
        
        // Event handlers
        function showTooltip(event, d) {{
            const content = `
                <strong>${{d.title}}</strong><br>
                Type: ${{d.type}}<br>
                Connections: ${{d.in_degree}} in, ${{d.out_degree}} out<br>
                Words: ${{d.word_count.toLocaleString()}}
            `;
            
            tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px")
                .html(content);
        }}
        
        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}
        
        function showMetadataPanel(event, d) {{
            event.stopPropagation();
            
            const panel = document.getElementById("metadata-panel");
            const title = document.getElementById("panel-title");
            const content = document.getElementById("panel-content");
            
            title.textContent = d.title;
            
            let html = `
                <div class="info-group">
                    <div class="info-label">Document Type</div>
                    <div class="info-value">${{d.type.replace('_', ' ').toUpperCase()}}</div>
                </div>
                
                <div class="info-group">
                    <div class="info-label">Agency</div>
                    <div class="info-value">${{d.agency.replace('-', ' ').toUpperCase()}}</div>
                </div>
            `;
            
            if (d.url) {{
                html += `
                    <a href="${{d.url}}" target="_blank" class="primary-action">
                        📄 View Source Document
                    </a>
                    <button class="secondary-action" onclick="copyUrl('${{d.url}}')">
                        📋 Copy URL
                    </button>
                `;
            }}
            
            html += `
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="value">${{d.in_degree}}</div>
                        <div class="label">Incoming</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.out_degree}}</div>
                        <div class="label">Outgoing</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.word_count.toLocaleString()}}</div>
                        <div class="label">Words</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${{d.pagerank.toFixed(4)}}</div>
                        <div class="label">PageRank</div>
                    </div>
                </div>
            `;
            
            if (d.topics && d.topics.length > 0) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Topics</div>
                        <div class="tags">
                            ${{d.topics.map(t => '<span class="tag">' + t + '</span>').join('')}}
                        </div>
                    </div>
                `;
            }}
            
            if (d.keywords && d.keywords.length > 0) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Keywords</div>
                        <div class="tags">
                            ${{d.keywords.map(k => '<span class="tag">' + k + '</span>').join('')}}
                        </div>
                    </div>
                `;
            }}
            
            if (d.content_preview) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Content Preview</div>
                        <div class="info-value preview">${{d.content_preview}}</div>
                    </div>
                `;
            }}
            
            if (d.crawled_date) {{
                html += `
                    <div class="info-group">
                        <div class="info-label">Crawled Date</div>
                        <div class="info-value">${{d.crawled_date}}</div>
                    </div>
                `;
            }}
            
            content.innerHTML = html;
            panel.classList.add("visible");
        }}
        
        function closePanel() {{
            document.getElementById("metadata-panel").classList.remove("visible");
        }}
        
        function copyUrl(url) {{
            navigator.clipboard.writeText(url).then(() => {{
                alert("URL copied to clipboard!");
            }});
        }}
        
        function dragstarted(event, d) {{
            if (!event.active && physicsEnabled) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active && physicsEnabled) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        function resetView() {{
            svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
        }}
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            if (physicsEnabled) {{
                simulation.alphaTarget(0.3).restart();
            }} else {{
                simulation.stop();
            }}
        }}
        
        function toggleLabels() {{
            labelsVisible = !labelsVisible;
            label.style("opacity", labelsVisible ? 1 : 0);
        }}
        
        function updateLabelVisibility(scale) {{
            if (!labelsVisible) return;
            
            // Show more labels when zoomed in
            label.style("opacity", d => {{
                if (d.is_agency || d.pagerank > 0.001) return 1;
                return scale > 1 ? 1 : 0.3;
            }});
        }}
        
        function applyFilters() {{
            const showExternal = document.getElementById("show-external").checked;
            const typeFilter = document.getElementById("type-filter").value;
            
            node.style("display", d => {{
                if (!showExternal && d.is_external) return "none";
                if (typeFilter !== "all" && d.type !== typeFilter) return "none";
                return "block";
            }});
            
            label.style("display", d => {{
                if (!showExternal && d.is_external) return "none";
                if (typeFilter !== "all" && d.type !== typeFilter) return "none";
                return "block";
            }});
            
            link.style("display", l => {{
                const sourceVisible = (!showExternal || !l.source.is_external) && 
                                    (typeFilter === "all" || l.source.type === typeFilter);
                const targetVisible = (!showExternal || !l.target.is_external) && 
                                    (typeFilter === "all" || l.target.type === typeFilter);
                return (sourceVisible && targetVisible) ? "block" : "none";
            }});
        }}
        
        // Close panel when clicking outside
        document.addEventListener("click", (e) => {{
            const panel = document.getElementById("metadata-panel");
            if (panel.classList.contains("visible") && !panel.contains(e.target)) {{
                closePanel();
            }}
        }});
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_type_options(self, type_counts: Dict[str, int]) -> str:
        """Generate HTML options for document type filter"""
        options = []
        for doc_type, count in sorted(type_counts.items()):
            display_name = doc_type.replace('_', ' ').title()
            options.append(f'<option value="{doc_type}">{display_name} ({count})</option>')
        return '\n                    '.join(options)
    
    def save_agency_data_files(self) -> Dict[str, Path]:
        """
        Save each agency's data as a separate JSON file
        
        Returns:
            Dict mapping agency keys to their data file paths
        """
        data_dir = self.output_dir / "agency-data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        print("Generating agency data files...")
        for agency_key in self.AGENCIES.keys():
            data = self.extract_agency_data(agency_key)
            filename = f"{agency_key}.json"
            filepath = data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            file_size_kb = filepath.stat().st_size / 1024
            print(f"  ✓ {agency_key}: {file_size_kb:.1f} KB")
            saved_files[agency_key] = filepath
        
        return saved_files
    
    def save_visualization(self) -> Path:
        """
        Save visualization HTML and separate agency data files
        
        Returns:
            Path to saved HTML file
        """
        # Save agency data files
        data_files = self.save_agency_data_files()
        
        # Generate HTML with dynamic loading
        filename = "agency-navigation.html"
        filepath = self.output_dir / filename
        
        print("\nGenerating agency selector HTML...")
        html_content = self.generate_agency_selector_html_dynamic()
        file_size_kb = len(html_content) / 1024
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Generated agency selector HTML ({file_size_kb:.1f} KB)")
        print(f"\nSaved to: {filepath}")
        print(f"✓ Agency data files: {self.output_dir / 'agency-data'}/")
        print("✓ Complete! Open in browser to view.")
        print(f"✓ All {len(self.AGENCIES)} agencies load on-demand from separate JSON files")
        
        return filepath


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate interactive network visualization with agency selector for Montana state government",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/viz/agency_network_viz.py
  python src/viz/agency_network_viz.py --output-dir custom/
  python src/viz/agency_network_viz.py --max-nodes 500

This script generates a single HTML file with an agency selector dropdown.
All agency data is embedded in the file for on-demand loading (no preloading).

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
        default='src/network/exports/montana_knowledge.pkl',
        help='Path to knowledge graph pickle file'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 60)
    print("Agency Network Visualizer - Multi-Agency Selector")
    print("=" * 60)
    
    # Load graph
    graph_path = Path(args.graph_path)
    if not graph_path.exists():
        print(f"\n❌ Error: Graph file not found: {graph_path}")
        print("Please run 'python src/network/build_network.py' first to create the knowledge graph.")
        return 1
    
    print(f"Loading knowledge graph from: {graph_path}")
    
    # Try to load with pickle compatibility fix
    graph = PickleModuleFix.load_graph(graph_path)
    
    if not graph:
        print("❌ Error: Failed to load graph")
        return 1
    
    print(f"✓ Graph loaded: {len(graph.nodes):,} nodes, {len(graph.edges):,} edges")
    
    # Determine knowledge_dir based on where we're running from
    if Path("knowledge").exists():
        knowledge_dir = "knowledge"
    else:
        knowledge_dir = "../knowledge"
    
    # Create visualizer
    print(f"\nPreparing visualization for all agencies...")
    visualizer = AgencyNetworkVisualizer(
        graph,
        output_dir=args.output_dir,
        knowledge_dir=knowledge_dir,
        max_nodes=args.max_nodes
    )
    
    # Generate and save
    output_path = visualizer.save_visualization()
    
    print(f"\n{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
