"""
Command-line interface for Phase 5: Navigation Visualization

Usage:
    python -m src.phase5_viz_navigation.cli --agency agriculture --layout tree
    python -m src.phase5_viz_navigation.cli --all --layout radial
    python -m src.phase5_viz_navigation.cli --all --layout both
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from .navigation_viz import NavigationVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def get_available_agencies(data_dir: Path) -> List[str]:
    """
    Get list of agencies with navigation graphs
    
    Args:
        data_dir: Directory containing navigation JSON files
        
    Returns:
        List of agency names
    """
    if not data_dir.exists():
        return []
    
    agencies = []
    for file in data_dir.glob("*_navigation.json"):
        agency = file.stem.replace("_navigation", "")
        agencies.append(agency)
    
    return sorted(agencies)


def build_visualization(agency: str, layout: str, visualizer: NavigationVisualizer,
                       quiet: bool = False) -> bool:
    """
    Build navigation visualization for one agency
    
    Args:
        agency: Agency name
        layout: Layout type ('tree', 'radial', or 'both')
        visualizer: NavigationVisualizer instance
        quiet: Suppress output
        
    Returns:
        True if successful
    """
    try:
        # Load navigation graph
        graph = visualizer.load_navigation_graph(agency)
        
        if not quiet:
            logger.info(f"Building {layout} visualization for {agency}...")
        
        # Build hierarchy
        hierarchy = visualizer.build_hierarchy(graph)
        
        # Generate visualizations based on layout
        outputs = []
        
        if layout in ('tree', 'both'):
            output_file = visualizer.generate_tree_visualization(agency, graph, hierarchy)
            outputs.append(output_file)
            if not quiet:
                logger.info(f"✓ Tree visualization: {output_file}")
        
        if layout in ('radial', 'both'):
            output_file = visualizer.generate_radial_visualization(agency, graph, hierarchy)
            outputs.append(output_file)
            if not quiet:
                logger.info(f"✓ Radial visualization: {output_file}")
        
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Navigation graph not found for {agency}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error building visualization for {agency}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate interactive navigation visualizations from Phase 3 graphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate tree layout for one agency
  python -m src.phase5_viz_navigation.cli --agency agriculture --layout tree
  
  # Generate radial layout for one agency
  python -m src.phase5_viz_navigation.cli --agency commerce --layout radial
  
  # Generate both layouts for one agency
  python -m src.phase5_viz_navigation.cli --agency human-resources --layout both
  
  # Generate all agencies with tree layout
  python -m src.phase5_viz_navigation.cli --all --layout tree
  
  # Generate all agencies with both layouts
  python -m src.phase5_viz_navigation.cli --all --layout both
        """
    )
    
    parser.add_argument(
        '--agency',
        type=str,
        help='Agency name (e.g., agriculture, commerce)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate visualizations for all agencies'
    )
    
    parser.add_argument(
        '--layout',
        type=str,
        choices=['tree', 'radial', 'both'],
        default='tree',
        help='Visualization layout type (default: tree)'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=None,
        help='Path to config.yaml (optional)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress informational output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.agency and not args.all:
        parser.error("Must specify either --agency or --all")
    
    if args.agency and args.all:
        parser.error("Cannot specify both --agency and --all")
    
    # Initialize visualizer
    visualizer = NavigationVisualizer(config_path=args.config)
    
    # Get agencies to process
    if args.all:
        agencies = get_available_agencies(visualizer.data_dir)
        if not agencies:
            logger.error(f"No navigation graphs found in {visualizer.data_dir}")
            return 1
        if not args.quiet:
            logger.info(f"Found {len(agencies)} agencies: {', '.join(agencies)}")
    else:
        agencies = [args.agency]
    
    # Build visualizations
    success_count = 0
    for agency in agencies:
        if build_visualization(agency, args.layout, visualizer, args.quiet):
            success_count += 1
    
    # Generate selector page if processing multiple agencies
    if len(agencies) > 1:
        selector_file = visualizer.generate_selector_page(agencies)
        if not args.quiet:
            logger.info(f"✓ Selector page: {selector_file}")
    
    # Summary
    if not args.quiet:
        logger.info(f"\n{'='*60}")
        logger.info(f"Completed: {success_count}/{len(agencies)} agencies")
        logger.info(f"Layout: {args.layout}")
        logger.info(f"Output directory: {visualizer.output_dir}")
        logger.info(f"{'='*60}")
    
    return 0 if success_count == len(agencies) else 1


if __name__ == '__main__':
    sys.exit(main())
