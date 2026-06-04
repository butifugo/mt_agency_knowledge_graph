"""
Phase 3 CLI - Navigation Network Builder Interface
Command-line interface for building navigation graphs
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.phase3_navigation.navigation_builder import NavigationBuilder
from src.phase3_navigation.hierarchy_analyzer import HierarchyAnalyzer
from src.phase3_navigation.mime_classifier import MimeClassifier


def build_navigation(args):
    """Build navigation network for agency/agencies"""
    config = Config(args.config if Path(args.config).exists() else None)
    
    builder = NavigationBuilder(
        knowledge_dir=str(config.knowledge_dir),
        output_dir=str(config.graphs_dir / "navigation")
    )
    
    if args.all:
        # Build for all agencies
        results = builder.build_all_agencies(verbose=not args.quiet)
        
        print(f"\n{'='*80}")
        print(f"✓ Built navigation graphs for {len(results)} agencies")
        print(f"{'='*80}\n")
        
    elif args.agency:
        # Build for specific agency
        nav_data = builder.build_navigation_graph(args.agency, verbose=not args.quiet)
        
        if not nav_data:
            print(f"✗ Failed to build navigation graph for {args.agency}")
            return 1
        
        print(f"\n✓ Navigation graph built successfully")
        
    return 0


def analyze_navigation(args):
    """Analyze navigation structure"""
    import json
    
    config = Config(args.config if Path(args.config).exists() else None)
    nav_file = config.graphs_dir / "navigation" / f"{args.agency}_navigation.json"
    
    if not nav_file.exists():
        print(f"✗ Navigation graph not found: {nav_file}")
        print(f"  Run with --build first to create the graph")
        return 1
    
    # Load navigation data
    with open(nav_file, 'r') as f:
        nav_data = json.load(f)
    
    nodes = nav_data.get('nodes', {})
    edges = nav_data.get('edges', [])
    
    # Analyze hierarchy
    print(f"\n{'='*80}")
    print(f"Navigation Analysis: {args.agency}")
    print(f"{'='*80}\n")
    
    analyzer = HierarchyAnalyzer(nodes, edges)
    structure = analyzer.analyze_structure()
    
    print("Structure Analysis:")
    print(f"  Total nodes: {structure['total_nodes']}")
    print(f"  Total edges: {structure['total_edges']}")
    print(f"  Root nodes: {structure['root_nodes']}")
    print(f"  Leaf nodes: {structure['leaf_nodes']}")
    print(f"  Maximum depth: {structure['max_depth']}")
    print(f"  Avg branching factor: {structure['avg_branching_factor']}")
    
    print("\nType Distribution:")
    for node_type, count in structure['type_distribution'].items():
        print(f"  {node_type}: {count}")
    
    # MIME type classification
    classifier = MimeClassifier(nodes)
    mime_stats = classifier.get_statistics()
    
    print("\nMIME Type Statistics:")
    print(f"  HTML pages: {mime_stats['html_pages']}")
    print(f"  PDF documents: {mime_stats['pdf_documents']}")
    print(f"  DOCX documents: {mime_stats['docx_documents']}")
    
    print(f"\n{'='*80}\n")
    
    return 0


def export_navigation(args):
    """Export navigation graph in different formats"""
    import json
    
    config = Config(args.config if Path(args.config).exists() else None)
    nav_file = config.graphs_dir / "navigation" / f"{args.agency}_navigation.json"
    
    if not nav_file.exists():
        print(f"✗ Navigation graph not found: {nav_file}")
        return 1
    
    # Load navigation data
    with open(nav_file, 'r') as f:
        nav_data = json.load(f)
    
    output_file = Path(args.output) if args.output else nav_file.with_suffix(f'.{args.format}')
    
    if args.format == 'json':
        # Already in JSON, just copy
        with open(output_file, 'w') as f:
            json.dump(nav_data, f, indent=2, ensure_ascii=False)
    
    elif args.format == 'graphml':
        # Export to GraphML format
        import xml.etree.ElementTree as ET
        
        root = ET.Element('graphml')
        graph = ET.SubElement(root, 'graph', id=args.agency, edgedefault='directed')
        
        # Add nodes
        for node_id, node in nav_data['nodes'].items():
            node_elem = ET.SubElement(graph, 'node', id=node_id)
            
            # Add data elements
            data_title = ET.SubElement(node_elem, 'data', key='title')
            data_title.text = node.get('title', '')
            
            data_type = ET.SubElement(node_elem, 'data', key='type')
            data_type.text = node.get('type', '')
        
        # Add edges
        for i, edge in enumerate(nav_data['edges']):
            ET.SubElement(graph, 'edge',
                         id=f"e{i}",
                         source=edge['source'],
                         target=edge['target'])
        
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f"✓ Exported to: {output_file}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Phase 3: Build Navigation Network',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build navigation network for all agencies
  python -m src.phase3_navigation.cli --build-all
  
  # Build for specific agency
  python -m src.phase3_navigation.cli --build --agency agriculture
  
  # Analyze navigation structure
  python -m src.phase3_navigation.cli --analyze --agency agriculture
  
  # Export navigation graph
  python -m src.phase3_navigation.cli --export --agency agriculture --format graphml
        """
    )
    
    parser.add_argument(
        '--build',
        action='store_true',
        help='Build navigation network for agency'
    )
    
    parser.add_argument(
        '--build-all',
        dest='all',
        action='store_true',
        help='Build navigation networks for all agencies'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze navigation structure'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export navigation graph'
    )
    
    parser.add_argument(
        '--agency',
        type=str,
        help='Agency folder name'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'graphml'],
        default='json',
        help='Export format'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.build or args.all:
        if not args.all and not args.agency:
            parser.error('--build requires --agency')
        return build_navigation(args)
    
    elif args.analyze:
        if not args.agency:
            parser.error('--analyze requires --agency')
        return analyze_navigation(args)
    
    elif args.export:
        if not args.agency:
            parser.error('--export requires --agency')
        return export_navigation(args)
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
