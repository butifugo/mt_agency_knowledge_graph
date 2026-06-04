"""
Phase 4 CLI - Knowledge Visualization Interface
Command-line interface for creating knowledge network visualizations
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.config import Config
from src.phase4_viz_knowledge.knowledge_viz import KnowledgeVisualizer


def create_viz(args):
    """Create knowledge network visualization"""
    config = Config(args.config if Path(args.config).exists() else None)
    
    visualizer = KnowledgeVisualizer(
        knowledge_dir=str(config.graphs_dir / "knowledge"),
        output_dir=str(config.html_dir)
    )
    
    if args.all:
        # Create visualizations for all agencies
        agencies = [
            'administration', 'agriculture', 'arts-council', 'auditor',
            'commerce', 'corrections', 'environmental-quality',
            'human-resources', 'labor-industry'
        ]
        
        created_files = []
        for agency in agencies:
            output_file = visualizer.create_visualization(
                agency,
                max_nodes=args.max_nodes,
                verbose=not args.quiet
            )
            if output_file:
                created_files.append(agency)
        
        # Create selector page
        if created_files and not args.no_selector:
            visualizer.create_multi_agency_selector(created_files, verbose=not args.quiet)
        
        print(f"\n✓ Created visualizations for {len(created_files)} agencies")
        
    elif args.agency:
        # Create visualization for specific agency
        output_file = visualizer.create_visualization(
            args.agency,
            max_nodes=args.max_nodes,
            verbose=not args.quiet
        )
        
        if output_file:
            print(f"\n✓ Visualization created successfully")
            print(f"  Open in browser: {output_file}")
        else:
            print(f"\n✗ Failed to create visualization for {args.agency}")
            return 1
    
    return 0


def main():
    print("=" * 80)
    print("DEPRECATED: Phase 4 standalone knowledge visualizations are deprecated.")
    print("For the best experience, use the unified interactive dashboard:")
    print()
    print("  # Generate dashboard for all agencies:")
    print("  python -m src.phase6_viz_interactive.cli")
    print()
    print("  # Generate dashboard for specific agencies:")
    print("  python -m src.phase6_viz_interactive.cli --agencies agriculture,commerce")
    print()
    print("The unified dashboard provides:")
    print("  ✓ Knowledge graphs AND navigation trees side-by-side")
    print("  ✓ Dynamic data loading (no 140MB HTML files)")
    print("  ✓ Better performance and user experience")
    print("  ✓ Consistent look and feel")
    print("=" * 80)
    print()
    
    response = input("Generate standalone knowledge viz anyway? (y/N): ")
    if response.lower() != 'y':
        print("\nCancelled. Use the unified dashboard instead:")
        print("  python -m src.phase6_viz_interactive.cli")
        return 0
    
    print("\nProceeding with legacy visualization...\n")
    
    parser = argparse.ArgumentParser(
        description='Phase 4: Create Knowledge Network Visualizations (DEPRECATED)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create visualization for all agencies
  python -m src.phase4_viz_knowledge.cli --all
  
  # Create for specific agency
  python -m src.phase4_viz_knowledge.cli --agency agriculture
  
  # Limit nodes for better performance
  python -m src.phase4_viz_knowledge.cli --agency agriculture --max-nodes 300
  
  # Create all without selector page
  python -m src.phase4_viz_knowledge.cli --all --no-selector
        """
    )
    
    parser.add_argument(
        '--agency',
        type=str,
        help='Agency folder name'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Create visualizations for all agencies'
    )
    
    parser.add_argument(
        '--max-nodes',
        type=int,
        default=500,
        help='Maximum nodes to include in visualization (default: 500)'
    )
    
    parser.add_argument(
        '--no-selector',
        action='store_true',
        help='Skip creating multi-agency selector page'
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
    if not args.all and not args.agency:
        parser.error('Either --all or --agency is required')
    
    return create_viz(args)


if __name__ == '__main__':
    sys.exit(main())
