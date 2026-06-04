"""
Integrated CLI for complete pipeline: Extract + Visualize
Combines HTML navigation extraction with dashboard generation
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.phase3_navigation.html_navigation_extractor import HTMLNavigationExtractor
from src.phase5_viz_navigation.html_navigation_viz import HTMLNavigationVisualizer

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Complete pipeline: Extract HTML navigation and generate visualizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single agency (extract + visualize)
  python -m src.phase6_viz_interactive.integrated_cli --agency agriculture
  
  # Process all agencies
  python -m src.phase6_viz_interactive.integrated_cli --all
  
  # Extract only
  python -m src.phase6_viz_interactive.integrated_cli --agency agriculture --extract-only
  
  # Visualize only (requires existing data)
  python -m src.phase6_viz_interactive.integrated_cli --agency agriculture --viz-only
        """
    )
    
    parser.add_argument(
        '--agency',
        type=str,
        help='Agency name to process (e.g., agriculture, human-resources)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all agencies found in knowledge directory'
    )
    
    parser.add_argument(
        '--extract-only',
        action='store_true',
        help='Only extract navigation data, do not visualize'
    )
    
    parser.add_argument(
        '--viz-only',
        action='store_true',
        help='Only visualize existing navigation data'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.agency and not args.all:
        parser.error('Either --agency or --all must be specified')
    
    if args.agency and args.all:
        parser.error('Cannot specify both --agency and --all')
    
    # Get list of agencies to process
    if args.all:
        knowledge_dir = Path('knowledge')
        if not knowledge_dir.exists():
            logger.error(f"Knowledge directory not found: {knowledge_dir}")
            return 1
        
        agencies = [d.name for d in knowledge_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if not agencies:
            logger.error("No agencies found in knowledge directory")
            return 1
        
        if not args.quiet:
            logger.info(f"Found {len(agencies)} agencies: {', '.join(agencies)}")
    else:
        agencies = [args.agency]
    
    # Initialize tools
    extractor = HTMLNavigationExtractor()
    visualizer = HTMLNavigationVisualizer()
    
    # Track results
    successful = []
    failed = []
    
    # Process each agency
    for agency in agencies:
        if not args.quiet:
            print(f"\n{'='*80}")
            print(f"Processing: {agency}")
            print(f"{'='*80}\n")
        
        try:
            # Extract navigation data
            if not args.viz_only:
                extractor.extract_navigation(agency, verbose=not args.quiet)
            
            # Generate visualization
            if not args.extract_only:
                output_path = visualizer.generate_visualization(agency)
                
                if not args.quiet:
                    logger.info(f"✓ Visualization: {output_path}")
            
            successful.append(agency)
        
        except Exception as e:
            logger.error(f"✗ Error processing {agency}: {e}")
            failed.append(agency)
            continue
    
    # Summary
    if not args.quiet:
        print(f"\n{'='*80}")
        print("Processing Summary")
        print(f"{'='*80}")
        print(f"✓ Successful: {len(successful)}/{len(agencies)}")
        if successful:
            print(f"  {', '.join(successful)}")
        if failed:
            print(f"✗ Failed: {len(failed)}/{len(agencies)}")
            print(f"  {', '.join(failed)}")
        print(f"{'='*80}\n")
        print("Visualizations are in: html/")
        print("To view, run: cd html && python3 -m http.server 8001")
    
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())
