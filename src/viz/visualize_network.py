#!/bin/sh
''''exec "$(dirname "$0")/../../.venv/bin/python" "$0" "$@" # '''
"""
Knowledge Network Visualization
Creates an interactive network graph of the Montana HR website structure
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches


def extract_metadata(md_file):
    """Extract metadata from markdown file"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML frontmatter
    metadata = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            for line in frontmatter.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
    
    return metadata


def extract_links_from_markdown(md_file):
    """Extract links from markdown content"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all markdown links [text](url)
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = re.findall(link_pattern, content)
    
    return [url for text, url in links if url.startswith('http') or url.startswith('..')]


def build_network_graph(knowledge_dir):
    """Build network graph from markdown files"""
    knowledge_path = Path(knowledge_dir)
    
    # Graph data structures
    nodes = {}
    edges = defaultdict(list)
    node_types = {}
    
    # Process all markdown files recursively from all subdirectories
    for md_file in knowledge_path.rglob('*.md'):
        metadata = extract_metadata(md_file)
        source_url = metadata.get('source', '')
        title = metadata.get('title', md_file.stem)
        file_type = metadata.get('type', 'HTML')
        
        # Determine node type
        if md_file.name.startswith('pdf_'):
            node_type = 'PDF'
        elif 'index' in md_file.name.lower():
            node_type = 'Index'
        elif 'Policy' in title or 'policy' in md_file.name.lower():
            node_type = 'Policy'
        elif 'Program' in title or 'program' in md_file.name.lower():
            node_type = 'Program'
        else:
            node_type = 'Page'
        
        # Add node
        node_id = str(md_file.relative_to(knowledge_path).with_suffix(''))
        nodes[node_id] = {
            'title': title,
            'type': node_type,
            'source': source_url,
            'file': md_file.name,
            'folder': md_file.parent.name
        }
        node_types[node_id] = node_type
        
        # Extract links to other pages
        links = extract_links_from_markdown(md_file)
        for link in links:
            # Try to match link to another file
            if link.startswith('..'):
                # It's a relative link, try to find matching file
                link_filename = Path(link).stem
                # Look for PDF files across all subdirectories
                for target_file in knowledge_path.rglob('pdf_*.md'):
                    if link_filename in target_file.stem:
                        target_id = str(target_file.relative_to(knowledge_path).with_suffix(''))
                        if target_id in nodes or any(f.stem == target_file.stem for f in knowledge_path.rglob('*.md')):
                            edges[node_id].append(target_id)
                        break
    
    return nodes, edges, node_types


def create_visualization(nodes, edges, node_types, output_file='html/knowledge_network.png'):
    """Create network visualization using NetworkX and Matplotlib"""
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for node_id, node_data in nodes.items():
        G.add_node(node_id, **node_data)
    
    # Add edges
    for source, targets in edges.items():
        for target in targets:
            if target in nodes:  # Only add edge if target exists
                G.add_edge(source, target)
    
    # Calculate layout
    print("Calculating network layout...")
    
    # Group nodes by type for better layout
    node_groups = defaultdict(list)
    for node_id, node_type in node_types.items():
        node_groups[node_type].append(node_id)
    
    # Use spring layout for overall structure
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(20, 16))
    
    # Color scheme
    colors = {
        'Index': '#FF6B6B',      # Red
        'Policy': '#4ECDC4',     # Teal
        'Program': '#45B7D1',    # Blue
        'PDF': '#FFA07A',        # Light Salmon
        'Page': '#95E1D3',       # Mint
    }
    
    # Draw nodes by type
    for node_type, color in colors.items():
        nodelist = [n for n in G.nodes() if node_types.get(n) == node_type]
        if nodelist:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=nodelist,
                node_color=color,
                node_size=800,
                alpha=0.9,
                ax=ax,
                label=f'{node_type} ({len(nodelist)})'
            )
    
    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        edge_color='gray',
        alpha=0.3,
        arrows=True,
        arrowsize=10,
        width=0.5,
        ax=ax
    )
    
    # Draw labels (only for important nodes to avoid clutter)
    important_nodes = [n for n in G.nodes() if node_types.get(n) in ['Index', 'Policy']]
    labels = {n: nodes[n]['title'][:20] + '...' if len(nodes[n]['title']) > 20 else nodes[n]['title'] 
              for n in important_nodes}
    
    nx.draw_networkx_labels(
        G, pos,
        labels,
        font_size=6,
        font_weight='bold',
        ax=ax
    )
    
    # Title and legend
    ax.set_title('Montana HR Website Knowledge Network\n(hr.mt.gov)', 
                 fontsize=18, fontweight='bold', pad=20)
    
    # Create custom legend
    legend_elements = [mpatches.Patch(facecolor=color, label=f'{node_type} ({len([n for n in node_types.values() if n == node_type])})') 
                      for node_type, color in colors.items() 
                      if any(t == node_type for t in node_types.values())]
    
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10, 
             title='Node Types', framealpha=0.9)
    
    # Add statistics box
    stats_text = f"""Network Statistics:
Total Nodes: {len(G.nodes())}
Total Connections: {len(G.edges())}
Avg Connections: {len(G.edges())/len(G.nodes()):.1f}
Most Connected: {nodes[max(dict(G.degree()).items(), key=lambda x: x[1])[0]]['title'][:30]}"""
    
    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.axis('off')
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Network visualization saved to: {output_file}")
    
    return G


def create_html_interactive(nodes, edges, node_types, output_file='html/knowledge_network.html'):
    """Create interactive HTML visualization"""
    
    # Prepare data for vis.js
    vis_nodes = []
    for node_id, node_data in nodes.items():
        node_type = node_types.get(node_id, 'Page')
        color_map = {
            'Index': '#FF6B6B',
            'Policy': '#4ECDC4',
            'Program': '#45B7D1',
            'PDF': '#FFA07A',
            'Page': '#95E1D3',
        }
        
        vis_nodes.append({
            'id': node_id,
            'label': node_data['title'][:30],
            'title': f"{node_data['title']}<br>Type: {node_type}<br>Folder: {node_data.get('folder', 'root')}<br>File: {node_data['file']}",
            'color': color_map.get(node_type, '#95E1D3'),
            'shape': 'dot' if node_type == 'PDF' else 'box',
            'size': 30 if node_type == 'Index' else 20
        })
    
    vis_edges = []
    for source, targets in edges.items():
        for target in targets:
            if target in nodes:
                vis_edges.append({
                    'from': source,
                    'to': target,
                    'arrows': 'to'
                })
    
    # Create HTML
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Montana HR Knowledge Network</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        #mynetwork {{
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .legend {{
            background: white;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            vertical-align: middle;
            border-radius: 3px;
        }}
        .stats {{
            background: white;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>🗺️ Montana HR Website Knowledge Network</h1>
    <p style="text-align: center; color: #666;">Interactive visualization of hr.mt.gov content structure</p>
    
    <div id="mynetwork"></div>
    
    <div class="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #FF6B6B;"></span>
            <span>Index Pages</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #4ECDC4;"></span>
            <span>Policy Pages</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #45B7D1;"></span>
            <span>Program Pages</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #FFA07A;"></span>
            <span>PDF Documents</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #95E1D3;"></span>
            <span>Other Pages</span>
        </div>
    </div>
    
    <div class="stats">
        <h3>Network Statistics</h3>
        <p><strong>Total Nodes:</strong> {len(nodes)}</p>
        <p><strong>Total Connections:</strong> {sum(len(targets) for targets in edges.values())}</p>
        <p><strong>PDF Documents:</strong> {sum(1 for t in node_types.values() if t == 'PDF')}</p>
        <p><strong>HTML Pages:</strong> {sum(1 for t in node_types.values() if t != 'PDF')}</p>
    </div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(vis_nodes)});
        var edges = new vis.DataSet({json.dumps(vis_edges)});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        
        var options = {{
            physics: {{
                stabilization: {{
                    iterations: 200
                }},
                barnesHut: {{
                    gravitationalConstant: -8000,
                    springLength: 200,
                    springConstant: 0.04
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100
            }},
            nodes: {{
                font: {{
                    size: 12
                }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                color: {{
                    color: '#848484',
                    opacity: 0.5
                }},
                smooth: {{
                    type: 'continuous'
                }}
            }}
        }};

        var network = new vis.Network(container, data, options);
        
        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                console.log('Clicked node:', nodes.get(nodeId));
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Interactive HTML visualization saved to: {output_file}")


def main():
    print("=" * 60)
    print("Montana HR Knowledge Network Visualization")
    print("=" * 60)
    print()
    
    knowledge_dir = "../knowledge"
    
    print("Analyzing knowledge base...")
    nodes, edges, node_types = build_network_graph(knowledge_dir)
    
    print(f"\nFound {len(nodes)} nodes")
    print(f"Found {sum(len(targets) for targets in edges.values())} connections")
    print()
    
    # Node type breakdown
    type_counts = defaultdict(int)
    for node_type in node_types.values():
        type_counts[node_type] += 1
    
    print("Node Types:")
    for node_type, count in sorted(type_counts.items()):
        print(f"  {node_type}: {count}")
    print()
    
    # Create static visualization
    print("Creating static network visualization...")
    G = create_visualization(nodes, edges, node_types, output_file='html/knowledge_network.png')
    
    # Create interactive visualization
    print("\nCreating interactive HTML visualization...")
    create_html_interactive(nodes, edges, node_types)
    
    print("\n" + "=" * 60)
    print("✓ Visualization complete!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - knowledge_network.png (static image)")
    print("  - knowledge_network.html (interactive, open in browser)")


if __name__ == "__main__":
    main()
