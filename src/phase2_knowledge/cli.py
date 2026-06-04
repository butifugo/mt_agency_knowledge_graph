"""
Phase 2 CLI - Knowledge Network Builder Interface
Command-line interface for building knowledge graphs
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.phase2_knowledge.knowledge_builder import KnowledgeBuilder
from src.phase2_knowledge.semantic_analyzer import SemanticAnalyzer


def build_knowledge(args):
    """Build knowledge network for agency/agencies"""
    config = Config(args.config if Path(args.config).exists() else None)
    
    builder = KnowledgeBuilder(
        knowledge_dir=str(config.knowledge_dir),
        output_dir=str(config.graphs_dir / "knowledge")
    )
    
    if args.all:
        # Build for all agencies
        results = builder.build_all_agencies(verbose=not args.quiet)
        
        print(f"\n{'='*80}")
        print(f"✓ Built knowledge graphs for {len(results)} agencies")
        print(f"{'='*80}\n")
        
    elif args.agency:
        # Build for specific agency
        knowledge_data = builder.build_knowledge_graph(args.agency, verbose=not args.quiet)
        
        if not knowledge_data:
            print(f"✗ Failed to build knowledge graph for {args.agency}")
            return 1
        
        print(f"\n✓ Knowledge graph built successfully")
        
    return 0


def enhance_knowledge(args):
    """Add semantic relationships to knowledge graph"""
    config = Config(args.config if Path(args.config).exists() else None)
    
    knowledge_file = config.graphs_dir / "knowledge" / f"{args.agency}_knowledge.json"
    
    if not knowledge_file.exists():
        print(f"✗ Knowledge graph not found: {knowledge_file}")
        print(f"  Run with --build first to create the graph")
        return 1
    
    print(f"\n{'='*80}")
    print(f"Enhancing Knowledge Graph: {args.agency}")
    print(f"{'='*80}\n")
    
    analyzer = SemanticAnalyzer(str(knowledge_file))
    
    # Add semantic similarity edges
    if not args.skip_semantic:
        threshold = args.threshold if hasattr(args, 'threshold') else 0.3
        analyzer.add_semantic_edges(threshold=threshold, verbose=not args.quiet)
    
    # Add topic clustering edges
    if not args.skip_topics:
        analyzer.add_topic_edges(verbose=not args.quiet)
    
    # Save enhanced graph
    output_file = analyzer.save_enhanced_graph()
    
    print(f"\n✓ Enhanced knowledge graph saved: {output_file}")
    print(f"{'='*80}\n")
    
    return 0


def analyze_knowledge(args):
    """Analyze knowledge graph structure"""
    import json
    
    config = Config(args.config if Path(args.config).exists() else None)
    knowledge_file = config.graphs_dir / "knowledge" / f"{args.agency}_knowledge.json"
    
    if not knowledge_file.exists():
        print(f"✗ Knowledge graph not found: {knowledge_file}")
        return 1
    
    # Load knowledge data
    with open(knowledge_file, 'r') as f:
        knowledge_data = json.load(f)
    
    nodes = knowledge_data.get('nodes', {})
    edges = knowledge_data.get('edges', [])
    stats = knowledge_data.get('statistics', {})
    
    print(f"\n{'='*80}")
    print(f"Knowledge Graph Analysis: {args.agency}")
    print(f"{'='*80}\n")
    
    print("Graph Statistics:")
    print(f"  Total nodes: {len(nodes)}")
    print(f"  Total edges: {len(edges)}")
    
    if 'document_types' in stats:
        print("\nDocument Types:")
        for doc_type, count in stats['document_types'].items():
            print(f"  {doc_type}: {count}")
    
    # Edge type distribution
    edge_types = {}
    for edge in edges:
        edge_type = edge.get('type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    if edge_types:
        print("\nEdge Types:")
        for edge_type, count in edge_types.items():
            print(f"  {edge_type}: {count}")
    
    # Keyword statistics
    all_keywords = []
    for node in nodes.values():
        all_keywords.extend(node.get('keywords', []))
    
    if all_keywords:
        from collections import Counter
        top_keywords = Counter(all_keywords).most_common(10)
        print("\nTop Keywords:")
        for keyword, count in top_keywords:
            print(f"  {keyword}: {count}")
    
    print(f"\n{'='*80}\n")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Phase 2: Build Knowledge Network',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build knowledge graph for all agencies
  python -m src.phase2_knowledge.cli --build-all
  
  # Build for specific agency
  python -m src.phase2_knowledge.cli --build --agency agriculture
  
  # Add semantic relationships
  python -m src.phase2_knowledge.cli --enhance --agency agriculture
  
  # Analyze knowledge graph
  python -m src.phase2_knowledge.cli --analyze --agency agriculture
  
  # Build and enhance in one step
  python -m src.phase2_knowledge.cli --build --agency agriculture --enhance
        """
    )
    
    parser.add_argument(
        '--build',
        action='store_true',
        help='Build knowledge network for agency'
    )
    
    parser.add_argument(
        '--build-all',
        dest='all',
        action='store_true',
        help='Build knowledge networks for all agencies'
    )
    
    parser.add_argument(
        '--enhance',
        action='store_true',
        help='Add semantic relationships to existing graph'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze knowledge graph structure'
    )
    
    parser.add_argument(
        '--agency',
        type=str,
        help='Agency folder name'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.3,
        help='Semantic similarity threshold (default: 0.3)'
    )
    
    parser.add_argument(
        '--skip-semantic',
        action='store_true',
        help='Skip semantic similarity edges when enhancing'
    )
    
    parser.add_argument(
        '--skip-topics',
        action='store_true',
        help='Skip topic clustering edges when enhancing'
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
        result = build_knowledge(args)
        
        # If --enhance flag is also provided, enhance immediately
        if args.enhance and args.agency and result == 0:
            return enhance_knowledge(args)
        
        return result
    
    elif args.enhance:
        if not args.agency:
            parser.error('--enhance requires --agency')
        return enhance_knowledge(args)
    
    elif args.analyze:
        if not args.agency:
            parser.error('--analyze requires --agency')
        return analyze_knowledge(args)
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
